"""
Pydantic Schemas for Inference
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class InferenceRequest(BaseModel):
    model_id: str = Field(..., example="mdl-001")
    input_data: Dict[str, Any] = Field(
        ...,
        example={"image_url": "https://example.com/image.jpg"}
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default={},
        example={"confidence_threshold": 0.8}
    )
    return_probabilities: bool = Field(False)


class PredictionResult(BaseModel):
    label: str
    confidence: float
    bounding_box: Optional[List[float]] = None


class InferenceResponse(BaseModel):
    prediction_id: str
    model_id: str
    model_version: str
    predictions: List[PredictionResult]
    raw_output: Optional[Dict[str, Any]]
    latency_ms: float
    timestamp: datetime


class BatchInferenceRequest(BaseModel):
    model_id: str = Field(..., example="mdl-001")
    dataset_id: Optional[str] = Field(None, example="ds-001")
    input_items: Optional[List[Dict[str, Any]]] = Field(None)
    parameters: Optional[Dict[str, Any]] = Field(default={})
    output_format: str = Field("json", example="json")
    callback_url: Optional[str] = Field(None, example="https://myapp.com/webhook")

    model_config = {"json_schema_extra": {"example": {
        "model_id": "mdl-001",
        "dataset_id": "ds-001",
        "parameters": {"confidence_threshold": 0.7},
        "output_format": "json",
        "callback_url": "https://myapp.com/webhook/results"
    }}}


class BatchJobResponse(BaseModel):
    job_id: str
    model_id: str
    status: str  # queued, running, completed, failed
    total_items: int
    processed_items: int
    created_at: datetime
    estimated_completion: Optional[datetime]
    result_path: Optional[str]
