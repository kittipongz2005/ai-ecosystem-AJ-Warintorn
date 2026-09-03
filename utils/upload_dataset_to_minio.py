"""
Script to download Token Classification (NER) dataset from Hugging Face
and upload it to MinIO bucket.
"""
import os
import io
import json
import argparse
from datasets import load_dataset
from minio import Minio

def upload_dataset_to_minio(
    dataset_name: str = "conll2003",
    bucket_name: str = "datasets",
    minio_endpoint: str = None,
    access_key: str = None,
    secret_key: str = None,
    secure: bool = False
):
    endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT", "localhost:9000")
    ak = access_key or os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    sk = secret_key or os.getenv("MINIO_SECRET_KEY", "minioadmin123")

    client = Minio(
        endpoint=endpoint,
        access_key=ak,
        secret_key=sk,
        secure=secure
    )

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"[MinIO] Created bucket '{bucket_name}'")

    print(f"[HuggingFace] Downloading dataset '{dataset_name}'...")
    ds = load_dataset(dataset_name)

    for split in ds.keys():
        records = [row for row in ds[split]]
        jsonl_data = "\n".join(json.dumps(r) for r in records).encode("utf-8")
        data_stream = io.BytesIO(jsonl_data)
        object_name = f'token-classification/{dataset_name}/{split}.jsonl'
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data_stream,
            length=len(jsonl_data),
            content_type="application/jsonl"
        )
        print(f"[MinIO] Uploaded {split} ({len(records)} items) to '{bucket_name}/{object_name}'")

    print("[SUCCESS] Dataset uploaded to MinIO successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload HuggingFace dataset to MinIO")
    parser.add_argument("--dataset", type=str, default="conll2003", help="Hugging Face dataset name")
    parser.add_argument("--bucket", type=str, default="datasets", help="MinIO bucket name")
    args = parser.parse_args()
    upload_dataset_to_minio(dataset_name=args.dataset, bucket_name=args.bucket)