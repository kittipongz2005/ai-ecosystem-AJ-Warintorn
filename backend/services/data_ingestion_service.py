"""
Data Ingestion Service
Business logic for dataset and file management
"""
import uuid
from datetime import datetime
from typing import Optional, List

from backend.schemas.data_ingestion import (
    DatasetCreateRequest,
    DatasetResponse,
    IngestionJobResponse,
    URLIngestionRequest,
    DataItemResponse,
    DataFormat,
)


# ─── In-Memory Storage (In production: use SQLAlchemy + PostgreSQL) ─────────────
_datasets_db: dict = {}
_items_db: dict = {}
_jobs_db: dict = {}


def create_dataset(body: DatasetCreateRequest) -> DatasetResponse:
    """
    สร้าง Dataset container ใหม่
    - Generate unique dataset_id
    - บันทึก metadata (name, format, tags)
    - คืน DatasetResponse
    """
    dataset_id = f"ds-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    dataset = {
        "dataset_id": dataset_id,
        "name": body.name,
        "description": body.description,
        "data_format": body.data_format,
        "total_items": 0,
        "size_bytes": 0,
        "tags": body.tags,
        "created_at": now,
        "updated_at": now,
    }
    _datasets_db[dataset_id] = dataset
    return DatasetResponse(**dataset)


def get_dataset(dataset_id: str) -> DatasetResponse:
    """ดึงข้อมูล dataset ตาม ID"""
    if dataset_id not in _datasets_db:
        raise KeyError(f"Dataset '{dataset_id}' not found")
    return DatasetResponse(**_datasets_db[dataset_id])


def list_datasets(
    skip: int = 0,
    limit: int = 20,
    format_filter: Optional[DataFormat] = None,
) -> dict:
    """ดึงรายการ datasets พร้อม pagination และ filter"""
    datasets = list(_datasets_db.values())
    if format_filter:
        datasets = [d for d in datasets if d["data_format"] == format_filter]
    return {
        "datasets": [DatasetResponse(**d) for d in datasets[skip:skip + limit]],
        "total": len(datasets),
        "skip": skip,
        "limit": limit,
    }


def delete_dataset(dataset_id: str) -> None:
    """ลบ dataset และ items ที่เกี่ยวข้อง"""
    if dataset_id not in _datasets_db:
        raise KeyError(f"Dataset '{dataset_id}' not found")
    del _datasets_db[dataset_id]


def ingest_files(dataset_id: str, files_data: List[dict]) -> IngestionJobResponse:
    """
    ประมวลผล file upload
    - สร้าง DataItem สำหรับแต่ละไฟล์
    - อัปเดต dataset stats
    - สร้าง IngestionJob record
    """
    if dataset_id not in _datasets_db:
        raise KeyError(f"Dataset '{dataset_id}' not found")

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    total_size = 0

    for file_data in files_data:
        item_id = f"item-{uuid.uuid4().hex[:8]}"
        total_size += file_data["size_bytes"]
        _items_db[item_id] = {
            "item_id": item_id,
            "dataset_id": dataset_id,
            "filename": file_data["filename"],
            "format": _datasets_db[dataset_id]["data_format"],
            "size_bytes": file_data["size_bytes"],
            "storage_path": f"minio://ai-ecosystem/{dataset_id}/{file_data['filename']}",
            "metadata": {"content_type": file_data.get("content_type")},
            "created_at": now,
        }

    _datasets_db[dataset_id]["total_items"] += len(files_data)
    _datasets_db[dataset_id]["size_bytes"] += total_size
    _datasets_db[dataset_id]["updated_at"] = now

    job = {
        "job_id": job_id,
        "dataset_id": dataset_id,
        "status": "completed",
        "total_files": len(files_data),
        "processed_files": len(files_data),
        "failed_files": 0,
        "started_at": now,
        "completed_at": now,
        "error_message": None,
    }
    _jobs_db[job_id] = job
    return IngestionJobResponse(**job)


def ingest_from_url(dataset_id: str, body: URLIngestionRequest) -> IngestionJobResponse:
    """
    เริ่ม URL ingestion job (async)
    - สร้าง job record ที่ status = 'running'
    - ใน production: ส่งไปยัง Celery/RQ task queue
    """
    if dataset_id not in _datasets_db:
        raise KeyError(f"Dataset '{dataset_id}' not found")

    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    job = {
        "job_id": job_id,
        "dataset_id": dataset_id,
        "status": "running",
        "total_files": len(body.urls),
        "processed_files": 0,
        "failed_files": 0,
        "started_at": now,
        "completed_at": None,
        "error_message": None,
    }
    _jobs_db[job_id] = job
    return IngestionJobResponse(**job)


def get_job(job_id: str) -> IngestionJobResponse:
    """ดูสถานะ ingestion job"""
    if job_id not in _jobs_db:
        raise KeyError(f"Job '{job_id}' not found")
    return IngestionJobResponse(**_jobs_db[job_id])


def list_dataset_items(dataset_id: str, skip: int = 0, limit: int = 20) -> dict:
    """ดึงรายการ items ใน dataset"""
    if dataset_id not in _datasets_db:
        raise KeyError(f"Dataset '{dataset_id}' not found")
    items = [i for i in _items_db.values() if i["dataset_id"] == dataset_id]
    return {
        "items": [DataItemResponse(**i) for i in items[skip:skip + limit]],
        "total": len(items),
    }
