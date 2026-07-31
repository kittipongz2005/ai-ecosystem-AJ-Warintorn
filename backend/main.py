"""
AI Ecosystem FastAPI Application
Assignment 5: FastAPI and API for AI Ecosystem
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.routers import (
    health,
    auth,
    data_ingestion,
    inference,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    print("[START] AI Ecosystem API starting up...")
    yield
    print("[STOP] AI Ecosystem API shutting down...")


app = FastAPI(
    title="AI Ecosystem API",
    description="""
## AI Ecosystem API — FastAPI Assignment 5

ระบบ API หลักสำหรับ AI Ecosystem ประกอบด้วย 5 endpoints สำคัญ:

- 🏥 **Health** — ตรวจสอบสถานะระบบ
- 🔐 **Authentication** — ลงทะเบียนและ Login รับ JWT Token
- 📥 **Data Ingestion** — สร้าง Dataset สำหรับเก็บข้อมูล AI
- ⚡ **Inference** — ส่งข้อมูลเข้า Model แล้วรับผลการทำนาย
    """,
    version="1.0.0",
    contact={
        "name": "AI Ecosystem Team",
        "email": "team@ai-ecosystem.dev",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health",         "description": "ตรวจสอบสถานะระบบ"},
        {"name": "Authentication", "description": "ลงทะเบียนและเข้าสู่ระบบ"},
        {"name": "Data Ingestion", "description": "สร้างและจัดการ Dataset"},
        {"name": "Inference",      "description": "ทำนายผลด้วย AI Model"},
    ],
)

# ─── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers (5 endpoints only) ────────────────────────────────────────────────
app.include_router(health.router,         prefix="/api/v1",       tags=["Health"])
app.include_router(auth.router,           prefix="/api/v1/auth",  tags=["Authentication"])
app.include_router(data_ingestion.router, prefix="/api/v1/data",  tags=["Data Ingestion"])
app.include_router(inference.router,      prefix="/api/v1/inference", tags=["Inference"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🤖 Welcome to AI Ecosystem API",
        "version": "1.0.0",
        "endpoints": 5,
        "docs": "/docs",
        "redoc": "/redoc",
    }
