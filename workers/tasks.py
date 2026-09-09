import os
import io
import json
import logging
import datetime
from pathlib import Path
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)
from minio import Minio
import mlflow
import mlflow.transformers

def setup_logger(log_file_path: str):
    logger = logging.getLogger("trainer_worker")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fh = logging.FileHandler(log_file_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def get_minio_client():
    return Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
    )

def setup_mlflow():
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}"
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    os.environ["MLFLOW_S3_IGNORE_TLS"] = "true"
    mlflow.set_experiment("Token-Classification-NER")

def download_dataset_from_minio(client: Minio, bucket_name: str, dataset_prefix: str, local_dir: str):
    os.makedirs(local_dir, exist_ok=True)
    objects = client.list_objects(bucket_name, prefix=dataset_prefix, recursive=True)
    loaded_splits = {}

    for obj in objects:
        if obj.object_name.endswith(".jsonl"):
            split_name = Path(obj.object_name).stem
            local_file = os.path.join(local_dir, f"{split_name}.jsonl")
            client.fget_object(bucket_name, obj.object_name, local_file)
            
            records = []
            with open(local_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            loaded_splits[split_name] = records
            
    return loaded_splits

def upload_directory_to_minio(client: Minio, bucket_name: str, local_dir: str, minio_prefix: str):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, local_dir).replace("\\", "/")
            object_name = f"{minio_prefix}/{rel_path}".strip("/")
            client.fput_object(bucket_name, object_name, local_path)

def train_token_classification_job(
    job_id: str,
    base_model_name: str = "distilbert-base-cased",
    dataset_name: str = "conll2003",
    dataset_bucket: str = "datasets",
    model_bucket: str = "models",
    epochs: int = 1,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    max_samples: int = 500
):
    work_dir = f"/tmp/training_jobs/{job_id}" if os.name != "nt" else f"./scratch/{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    log_file = os.path.join(work_dir, f"train_{job_id}.log")
    logger = setup_logger(log_file)

    logger.info(f"=== Starting Training Job with MLflow: {job_id} ===")
    logger.info(f"PyTorch Version: {torch.__version__}")
    is_cuda = torch.cuda.is_available()
    logger.info(f"CUDA Available: {is_cuda}")
    if is_cuda:
        logger.info(f"GPU Device: {torch.cuda.get_device_name(0)}")
    else:
        logger.info("Using CPU for training.")

    setup_mlflow()
    minio_client = get_minio_client()

    logger.info(f"Downloading dataset from MinIO: {dataset_bucket}/token-classification/{dataset_name}")
    data_dir = os.path.join(work_dir, "dataset")
    dataset_prefix = f"token-classification/{dataset_name}"
    splits_data = download_dataset_from_minio(minio_client, dataset_bucket, dataset_prefix, data_dir)

    if not splits_data or "train" not in splits_data:
        raise ValueError("Train dataset split not found in MinIO bucket!")

    train_data = splits_data["train"][:max_samples]
    val_data = splits_data.get("validation", splits_data["train"])[:max_samples // 4]

    raw_datasets = DatasetDict({
        "train": Dataset.from_list(train_data),
        "validation": Dataset.from_list(val_data)
    })

    logger.info(f"Loaded train samples: {len(raw_datasets['train'])}")
    logger.info(f"Loaded validation samples: {len(raw_datasets['validation'])}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    num_labels = 9

    model = AutoModelForTokenClassification.from_pretrained(
        base_model_name,
        num_labels=num_labels
    )

    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples["tokens"],
            truncation=True,
            is_split_into_words=True,
            padding=False
        )
        labels = []
        for i, label in enumerate(examples["ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx] if word_idx < len(label) else -100)
                else:
                    label_ids.append(-100)
                previous_word_idx = word_idx
            labels.append(label_ids)
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    tokenized_datasets = raw_datasets.map(
        tokenize_and_align_labels,
        batched=True,
        remove_columns=raw_datasets["train"].column_names
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    output_model_dir = os.path.join(work_dir, "saved_model")

    training_args = TrainingArguments(
        output_dir=os.path.join(work_dir, "checkpoints"),
        eval_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=epochs,
        weight_decay=0.01,
        logging_dir=os.path.join(work_dir, "logs"),
        logging_steps=10,
        save_strategy="epoch",
        report_to="none",
        use_cpu=not is_cuda
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator
    )

    with mlflow.start_run(run_name=f"job_{job_id}") as run:
        mlflow.log_params({
            "base_model": base_model_name,
            "dataset": dataset_name,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_samples": max_samples
        })

        logger.info("Starting Model Training Loop...")
        train_result = trainer.train()
        logger.info(f"Training Finished. Metrics: {train_result.metrics}")

        for k, v in train_result.metrics.items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(k, v)

        logger.info(f"Saving Model and Tokenizer to {output_model_dir}...")
        trainer.save_model(output_model_dir)
        tokenizer.save_pretrained(output_model_dir)

        # Log & Register to MLflow Model Registry
        logger.info("Logging Model to MLflow and Registering to Model Registry...")
        try:
            mlflow.transformers.log_model(
                transformers_model={"model": model, "tokenizer": tokenizer},
                artifact_path="model",
                registered_model_name="token-classification-model"
            )
        except Exception as e:
            logger.warning(f"Could not register to MLflow Registry: {e}")

        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        minio_model_prefix = f"token-classification/{job_id}_{timestamp}"

        upload_directory_to_minio(minio_client, model_bucket, output_model_dir, minio_model_prefix)
        minio_client.fput_object(model_bucket, f"{minio_model_prefix}/training.log", log_file)

        run_id = run.info.run_id

    logger.info(f"=== Job {job_id} Completed Successfully! MLflow Run ID: {run_id} ===")
    return {
        "status": "success",
        "job_id": job_id,
        "mlflow_run_id": run_id,
        "model_path": f"{model_bucket}/{minio_model_prefix}",
        "metrics": train_result.metrics
    }
