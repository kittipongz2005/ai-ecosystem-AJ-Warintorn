"""
Inference Router
ทำนายผลด้วย AI Model แบบ real-time
"""
from fastapi import APIRouter
from datetime import datetime
import uuid
import random

from backend.schemas.inference import (
    InferenceRequest,
    InferenceResponse,
    PredictionResult,
)

router = APIRouter()

# ─── Mock Labels ────────────────────────────────────────────────────────────────
_MOCK_LABELS = ["Normal", "Pneumonia", "COVID-19", "Tuberculosis"]


# ─── Endpoint 5: POST /api/v1/inference/predict ───────────────────────────────

@router.post(
    "/predict",
    response_model=InferenceResponse,
    summary="Real-time Inference",
    description="ส่ง input data เข้า AI Model แล้วรับผลการทำนายพร้อม confidence score"
)
async def predict(body: InferenceRequest):
    """
    ทำนายผลแบบ real-time
    - รับ image URL, base64 image, หรือ text input
    - ส่งไปยัง deployed model (mock: random predictions)
    - Normalize confidence scores ให้รวมเป็น 1.0
    - คืนผลพร้อม latency_ms สำหรับ monitoring
    """
    prediction_id = f"pred-{uuid.uuid4().hex[:8]}"
    latency = round(random.uniform(15, 150), 2)

    # Generate normalized confidence scores
    raw_scores = sorted([random.random() for _ in _MOCK_LABELS], reverse=True)
    total = sum(raw_scores)
    normalized = [round(s / total, 4) for s in raw_scores]

    predictions = [
        PredictionResult(
            label=label,
            confidence=conf,
            bounding_box=[10.0, 20.0, 150.0, 180.0] if "detection" in body.model_id else None,
        )
        for label, conf in zip(_MOCK_LABELS, normalized)
    ]

    if not body.return_probabilities:
        predictions = [predictions[0]]  # Top-1 only

    return InferenceResponse(
        prediction_id=prediction_id,
        model_id=body.model_id,
        model_version="1.0.0",
        predictions=predictions,
        raw_output={"logits": [c.confidence for c in predictions]} if body.return_probabilities else None,
        latency_ms=latency,
        timestamp=datetime.utcnow(),
    )
