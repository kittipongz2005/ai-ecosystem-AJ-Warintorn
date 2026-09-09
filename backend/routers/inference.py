"""
Inference Router
- รองรับ Real-time และ Async Inference ผ่าน Redis Queue & MLflow
- รองรับการขอดูผลการทำงานด้วย job_id (Redis Queue)
"""
import os
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import redis
from rq import Queue
from rq.job import Job

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
INFERENCE_QUEUE_NAME = "inference_queue"
TASK_FUNCTION_PATH = "workers.inference_tasks.run_inference_task"


def get_redis_conn():
    return redis.from_url(REDIS_URL)


# ─── Request & Response Schemas ───────────────────────────────────────────────

class PredictRequest(BaseModel):
    text: str = Field(..., example="Barack Obama was the 44th president of the United States.")
    model_uri: Optional[str] = Field(
        default="models:/token-classification-model/latest",
        example="models:/token-classification-model/latest",
        description="MLflow model URI or name"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default={"confidence_threshold": 0.5},
        example={"confidence_threshold": 0.5}
    )
    async_mode: bool = Field(
        default=False,
        description="Set True to return job_id immediately, or False to wait for result"
    )


class EntityPrediction(BaseModel):
    entity: str
    word: str
    score: float
    start: Optional[int] = None
    end: Optional[int] = None


class PredictResponse(BaseModel):
    job_id: str
    status: str
    model_uri: str
    predictions: Optional[List[EntityPrediction]] = None
    total_entities_found: Optional[int] = 0
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: Optional[str] = None
    enqueued_at: Optional[str] = None
    ended_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict / Inference with MLflow model via Redis Worker",
    description="ส่งข้อมูลเพื่อทำการ Inference ผ่าน Redis Queue และ Inference Worker"
)
async def predict(req: PredictRequest):
    """
    ส่งข้อความเข้าคิว Redis และสั่งให้ Inference Worker ประมวลผล
    - ถ้า `async_mode=False`: รอผลลัพธ์และส่งกลับทันที (Sync wait)
    - ถ้า `async_mode=True`: ส่งคืน job_id ทันที เพื่อนำไปเช็คผลต่อที่ `/jobs/{job_id}`
    """
    try:
        r_conn = get_redis_conn()
        q = Queue(INFERENCE_QUEUE_NAME, connection=r_conn)
        job_id = f"inf_{uuid.uuid4().hex[:8]}"

        job = q.enqueue(
            TASK_FUNCTION_PATH,
            job_id=job_id,
            text=req.text,
            model_uri=req.model_uri,
            parameters=req.parameters,
            job_id=job_id,
            job_timeout="2m"
        )

        if req.async_mode:
            return PredictResponse(
                job_id=job.id,
                status="queued",
                model_uri=req.model_uri,
                message="Job enqueued. Query /api/v1/inference/jobs/{job_id} for results."
            )

        # Sync mode: Wait for result (up to 15 seconds)
        start_wait = time.time()
        while time.time() - start_wait < 15:
            job.refresh()
            if job.is_finished:
                res = job.result
                return PredictResponse(
                    job_id=job.id,
                    status="completed",
                    model_uri=req.model_uri,
                    predictions=res.get("predictions", []),
                    total_entities_found=res.get("total_entities_found", 0),
                    latency_ms=res.get("latency_ms", 0.0),
                    message="Inference completed successfully"
                )
            elif job.is_failed:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Inference job failed: {job.exc_info}"
                )
            time.sleep(0.3)

        # If timeout waiting synchronously, return job_id
        return PredictResponse(
            job_id=job.id,
            status="running",
            model_uri=req.model_uri,
            message="Processing is taking longer than expected. Please check result with job_id."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inference request: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Inference Job Result by job_id",
    description="ตรวจสอบสถานะและผลลัพธ์ของงาน Inference ด้วย job_id จาก Redis"
)
async def get_inference_job_status(job_id: str):
    """
    ดึงผลลัพธ์และสถานะของ Inference Job จาก Redis
    """
    try:
        r_conn = get_redis_conn()
        job = Job.fetch(job_id, connection=r_conn)

        return JobStatusResponse(
            job_id=job.id,
            status=job.get_status() or "unknown",
            created_at=job.created_at.isoformat() if job.created_at else None,
            enqueued_at=job.enqueued_at.isoformat() if job.enqueued_at else None,
            ended_at=job.ended_at.isoformat() if job.ended_at else None,
            result=job.result if isinstance(job.result, dict) else None,
            error=str(job.exc_info) if job.is_failed else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inference Job not found or error occurred: {str(e)}"
        )
