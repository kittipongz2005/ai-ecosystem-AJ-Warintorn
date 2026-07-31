"""
Pydantic Schemas for Health Check
"""
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime


class ServiceStatus(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    services: Dict[str, ServiceStatus]
