"""
Inference Service
Business logic for real-time and batch AI inference
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, List

from backend.schemas.inference import (
    InferenceRequest,
    InferenceResponse,
    PredictionResult,
    BatchInferenceRequest,
    BatchJobResponse,
)


# ─── In-Memory Storage (In production: use Redis + PostgreSQL) ───────────────────
_predictions_db: dict = {}
_batch_jobs_db: dict = {}

# Simulated model capabilities
_MOCK_LABELS = {
    "image_classification": ["Normal", "Pneumonia", "COVID-19", "Tuberculosis"],
    "object_detection": ["person", "car", "bicycle", "dog", "cat"],
    "nlp_classification": ["positive", "negative", "neutral"],
}


def run_inference(body: InferenceRequest) -> InferenceResponse:
    """
    ทำนายผลแบบ real-time
    - ส่ง input ไปยัง model serving (mock: random predictions)
    - คำนวณ confidence scores
    - บันทึก prediction ลง DB สำหรับ audit trail
    - คืน InferenceResponse พร้อม latency
    """
    prediction_id = f"pred-{uuid.uuid4().hex[:8]}"
    latency = round(random.uniform(15, 150), 2)

    labels = _MOCK_LABELS.get("image_classification", ["Class_A", "Class_B"])
    confidences = sorted([random.random() for _ in labels], reverse=True)
    # Normalize confidences to sum to 1
    total = sum(confidences)
    confidences = [c / total for c in confidences]

    predictions = [
        PredictionResult(
            label=label,
            confidence=round(conf, 4),
            bounding_box=[10.0, 20.0, 150.0, 180.0] if "detection" in body.model_id else None,
        )
        for label, conf in zip(labels, confidences)
    ]

    if not body.return_probabilities:
        predictions = [predictions[0]]  # Top-1 only

    response = InferenceResponse(
        prediction_id=prediction_id,
        model_id=body.model_id,
        model_version="1.0.0",
        predictions=predictions,
        raw_output={"logits": [c.confidence for c in predictions]} if body.return_probabilities else None,
        latency_ms=latency,
        timestamp=datetime.utcnow(),
    )
    _predictions_db[prediction_id] = response
    return response


def create_batch_job(body: BatchInferenceRequest) -> BatchJobResponse:
    """
    สร้าง batch inference job (async)
    - คำนวณจำนวน items
    - Estimate completion time
    - ใน production: ส่งไปยัง Celery/RQ task queue
    """
    job_id = f"batch-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    total_items = len(body.input_items) if body.input_items else 100

    job = BatchJobResponse(
        job_id=job_id,
        model_id=body.model_id,
        status="queued",
        total_items=total_items,
        processed_items=0,
        created_at=now,
        estimated_completion=now + timedelta(minutes=int(total_items / 10) + 1),
        result_path=None,
    )
    _batch_jobs_db[job_id] = job
    return job


def get_batch_job(job_id: str) -> BatchJobResponse:
    """ดูสถานะ batch inference job"""
    if job_id not in _batch_jobs_db:
        raise KeyError(f"Batch job '{job_id}' not found")
    return _batch_jobs_db[job_id]


def get_prediction(prediction_id: str) -> InferenceResponse:
    """ดึงผลการทำนายตาม prediction ID"""
    if prediction_id not in _predictions_db:
        raise KeyError(f"Prediction '{prediction_id}' not found")
    return _predictions_db[prediction_id]


def get_model_inference_metrics(model_id: str) -> dict:
    """
    ดู inference performance metrics
    - ใน production: ดึงจาก Prometheus/Grafana
    """
    return {
        "model_id": model_id,
        "period": "last_24h",
        "total_requests": 15420,
        "avg_latency_ms": 45.2,
        "p95_latency_ms": 120.5,
        "p99_latency_ms": 250.1,
        "throughput_rps": 8.5,
        "error_rate_percent": 0.12,
        "top_predictions": {
            "Normal": 6500,
            "Pneumonia": 5200,
            "COVID-19": 3720,
        },
    }
