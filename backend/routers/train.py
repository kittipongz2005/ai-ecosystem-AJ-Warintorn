import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status
import redis
from rq import Queue
from rq.job import Job

from backend.schemas.train import (
    TrainJobCreateRequest,
    TrainJobResponse,
    TrainJobStatusResponse
)

TASK_FUNCTION_PATH = "workers.tasks.train_token_classification_job"


router = APIRouter(prefix="/train", tags=["Training"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = "training_queue"

def get_redis_conn():
    return redis.from_url(REDIS_URL)

@router.post(
    "/enqueue",
    response_model=TrainJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a model training job with optional schedule time"
)
async def enqueue_training_job(req: TrainJobCreateRequest):
    """
    Enqueue a Token Classification training job to Redis Queue (RQ).
    Supports scheduling at a specific datetime or after a delay.
    """
    try:
        r_conn = get_redis_conn()
        q = Queue(QUEUE_NAME, connection=r_conn)
        
        job_id = f"job_tc_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)
        
        target_time = now
        if req.scheduled_at:
            # Ensure scheduled_at has timezone
            if req.scheduled_at.tzinfo is None:
                target_time = req.scheduled_at.replace(tzinfo=timezone.utc)
            else:
                target_time = req.scheduled_at
        elif req.delay_seconds and req.delay_seconds > 0:
            target_time = now + timedelta(seconds=req.delay_seconds)
            
        job_kwargs = {
            "job_id": job_id,
            "base_model_name": req.base_model_name,
            "dataset_name": req.dataset_name,
            "dataset_bucket": req.dataset_bucket,
            "model_bucket": req.model_bucket,
            "epochs": req.epochs,
            "batch_size": req.batch_size,
            "learning_rate": req.learning_rate,
            "max_samples": req.max_samples,
        }

        if target_time > now:
            # Scheduled job
            job = q.enqueue_at(
                target_time,
                TASK_FUNCTION_PATH,
                job_id=job_id,
                kwargs=job_kwargs,
                job_timeout="2h"
            )
            msg = f"Job {job_id} scheduled to start at {target_time.isoformat()}"
        else:
            # Immediate job
            job = q.enqueue(
                TASK_FUNCTION_PATH,
                job_id=job_id,
                kwargs=job_kwargs,
                job_timeout="2h"
            )
            msg = f"Job {job_id} enqueued for immediate execution"

        return TrainJobResponse(
            job_id=job.id,
            status=job.get_status() or "queued",
            queue_name=QUEUE_NAME,
            enqueued_at=now.isoformat(),
            scheduled_start_time=target_time.isoformat(),
            message=msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue training job: {str(e)}"
        )

@router.get(
    "/jobs/{job_id}",
    response_model=TrainJobStatusResponse,
    summary="Get status and result of a training job"
)
async def get_training_job_status(job_id: str):
    """
    Check the current status and metrics of a training job.
    """
    try:
        r_conn = get_redis_conn()
        job = Job.fetch(job_id, connection=r_conn)
        
        return TrainJobStatusResponse(
            job_id=job.id,
            status=job.get_status() or "unknown",
            created_at=job.created_at.isoformat() if job.created_at else None,
            enqueued_at=job.enqueued_at.isoformat() if job.enqueued_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            ended_at=job.ended_at.isoformat() if job.ended_at else None,
            result=job.result if isinstance(job.result, dict) else None,
            error=str(job.exc_info) if job.is_failed else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found or error occurred: {str(e)}"
        )
