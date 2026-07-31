"""
Health Router
ตรวจสอบสถานะระบบ AI Ecosystem
"""
from fastapi import APIRouter
from datetime import datetime
import platform
import sys

router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description="ตรวจสอบสถานะของระบบ AI Ecosystem และ services ที่เกี่ยวข้อง"
)
async def health_check():
    """
    ตรวจสอบว่าระบบทำงานปกติหรือไม่
    - ตรวจสอบ API server
    - ตรวจสอบ database connection (mock)
    - ตรวจสอบ MinIO storage (mock)
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api":            {"status": "up", "latency_ms": 0.5},
            "database":       {"status": "up", "latency_ms": 2.1},
            "minio_storage":  {"status": "up", "latency_ms": 5.3},
            "label_studio":   {"status": "up", "latency_ms": 12.0},
            "model_registry": {"status": "up", "latency_ms": 1.2},
        },
        "system": {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
        },
    }
