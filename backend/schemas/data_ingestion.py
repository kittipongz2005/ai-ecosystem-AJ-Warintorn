"""
Pydantic Schemas for Data Ingestion
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    FILE_UPLOAD = "file_upload"
    URL = "url"
    S3 = "s3"
    DATABASE = "database"
    STREAM = "stream"


class DataFormat(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    AUDIO = "audio"


class DatasetCreateRequest(BaseModel):
    name: str = Field(..., example="Medical Images Dataset")
    description: Optional[str] = Field(None, example="X-ray images for classification")
    data_format: DataFormat = Field(..., example="image")
    tags: List[str] = Field(default=[], example=["medical", "xray"])
    metadata: Optional[Dict[str, Any]] = Field(default={})

    model_config = {"json_schema_extra": {"example": {
        "name": "Medical Images Dataset",
        "description": "X-ray images for classification",
        "data_format": "image",
        "tags": ["medical", "xray"],
        "metadata": {"source": "hospital_db", "year": 2024}
    }}}


class DatasetResponse(BaseModel):
    dataset_id: str
    name: str
    description: Optional[str]
    data_format: DataFormat
    total_items: int
    size_bytes: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class IngestionJobResponse(BaseModel):
    job_id: str
    dataset_id: str
    status: str  # pending, running, completed, failed
    total_files: int
    processed_files: int
    failed_files: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class URLIngestionRequest(BaseModel):
    dataset_id: str = Field(..., example="ds-001")
    urls: List[str] = Field(..., example=["https://example.com/data.zip"])
    extract_archive: bool = Field(True)


class DataItemResponse(BaseModel):
    item_id: str
    dataset_id: str
    filename: str
    format: DataFormat
    size_bytes: int
    storage_path: str
    metadata: Dict[str, Any]
    created_at: datetime
