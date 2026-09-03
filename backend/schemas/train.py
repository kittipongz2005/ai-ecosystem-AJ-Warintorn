from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TrainJobCreateRequest(BaseModel):
    base_model_name: str = Field(default="distilbert-base-cased", description="Hugging Face pretrained model name")
    dataset_name: str = Field(default="conll2003", description="Dataset identifier in MinIO")
    dataset_bucket: str = Field(default="datasets", description="MinIO bucket holding the dataset")
    model_bucket: str = Field(default="models", description="MinIO bucket to store output model")
    epochs: int = Field(default=1, ge=1, le=20, description="Number of training epochs")
    batch_size: int = Field(default=8, ge=1, le=128, description="Batch size")
    learning_rate: float = Field(default=2e-5, description="Learning rate")
    max_samples: int = Field(default=500, description="Max training samples (for quick demo/training)")
    
    # Scheduling parameters
    scheduled_at: Optional[datetime] = Field(
        default=None, 
        description="Target UTC datetime to start training job. If None, uses delay_seconds or runs immediately."
    )
    delay_seconds: Optional[int] = Field(
        default=0, 
        ge=0, 
        description="Delay in seconds before the worker starts training"
    )

class TrainJobResponse(BaseModel):
    job_id: str
    status: str
    queue_name: str
    enqueued_at: str
    scheduled_start_time: str
    message: str

class TrainJobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: Optional[str] = None
    enqueued_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
