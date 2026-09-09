"""
Inference Worker Tasks module
- โหลดโมเดลจาก MLflow Registry / MinIO
- รองรับการทำนายผล Token Classification (NER) / Text Inference
- ประมวลผลและส่งผลลัพธ์ผ่าน Redis
"""
import os
import time
import logging
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import mlflow
import mlflow.pyfunc

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("inference_worker")

# Cache loaded models in-memory to avoid reloading on every request
_MODEL_CACHE = {}


def setup_mlflow_env():
    """ตั้งค่า Environment สำหรับเชื่อมต่อกับ MLflow & MinIO S3"""
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}"
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    os.environ["MLFLOW_S3_IGNORE_TLS"] = "true"


def get_inference_pipeline(model_name_or_uri: str):
    """
    โหลด Model และ Tokenizer จาก MLflow Model Registry หรือ Local Path พร้อมทำ In-Memory Cache
    """
    if model_name_or_uri in _MODEL_CACHE:
        return _MODEL_CACHE[model_name_or_uri]

    setup_mlflow_env()
    logger.info(f"[Inference Worker] Loading model from: {model_name_or_uri}")
    
    device = 0 if torch.cuda.is_available() else -1
    
    try:
        if model_name_or_uri.startswith("models:/") or model_name_or_uri.startswith("runs:/"):
            # โหลดผ่าน MLflow
            loaded_model = mlflow.transformers.load_model(model_name_or_uri, device=device)
            nlp_pipe = loaded_model
        else:
            # Fallback โหลด default HuggingFace model
            base_model = os.getenv("DEFAULT_MODEL_NAME", "distilbert-base-cased")
            tokenizer = AutoTokenizer.from_pretrained(base_model)
            model = AutoModelForTokenClassification.from_pretrained(base_model)
            nlp_pipe = pipeline("ner", model=model, tokenizer=tokenizer, device=device)
            
        _MODEL_CACHE[model_name_or_uri] = nlp_pipe
        logger.info(f"[Inference Worker] Successfully loaded model: {model_name_or_uri}")
        return nlp_pipe
    except Exception as e:
        logger.warning(f"Could not load MLflow model '{model_name_or_uri}': {e}. Falling back to default NER pipeline.")
        nlp_pipe = pipeline("ner", model="dslim/bert-base-NER", device=device)
        _MODEL_CACHE[model_name_or_uri] = nlp_pipe
        return nlp_pipe


def run_inference_task(
    job_id: str,
    text: str,
    model_uri: str = "models:/token-classification-model/latest",
    parameters: dict = None
):
    """
    Function สำหรับ Worker ทำการคำนวณ Inference
    """
    logger.info(f"[Inference Worker] Processing Job {job_id} on text: '{text[:50]}...'")
    start_time = time.time()

    parameters = parameters or {}
    confidence_threshold = parameters.get("confidence_threshold", 0.0)

    try:
        pipe = get_inference_pipeline(model_uri)
        results = pipe(text)

        # จัดฟอร์แมตผลลัพธ์
        formatted_predictions = []
        for item in results:
            score = float(item.get("score", 1.0))
            if score >= confidence_threshold:
                formatted_predictions.append({
                    "entity": item.get("entity", item.get("entity_group", "UNKNOWN")),
                    "word": item.get("word", ""),
                    "score": round(score, 4),
                    "start": item.get("start", None),
                    "end": item.get("end", None)
                })

        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        output = {
            "job_id": job_id,
            "status": "completed",
            "model_uri": model_uri,
            "predictions": formatted_predictions,
            "total_entities_found": len(formatted_predictions),
            "latency_ms": latency_ms
        }
        logger.info(f"[Inference Worker] Job {job_id} completed in {latency_ms} ms")
        return output

    except Exception as e:
        logger.error(f"[Inference Worker] Job {job_id} failed: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
