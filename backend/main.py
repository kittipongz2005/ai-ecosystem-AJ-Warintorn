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
    train,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    print("[START] AI Ecosystem API starting up...")
    yield
    print("[STOP] AI Ecosystem API shutting down...")


# ─── OpenAPI Tag Metadata ─────────────────────────────────────────────────────
# อ้างอิง: https://fastapi.tiangolo.com/tutorial/metadata/
tags_metadata = [
    {
        "name": "Health",
        "description": (
            "ตรวจสอบสถานะของระบบ AI Ecosystem และ services ที่เกี่ยวข้องทั้งหมด "
            "(API server, PostgreSQL, MinIO, Label Studio, Model Registry)"
        ),
    },
    {
        "name": "Authentication",
        "description": (
            "ลงทะเบียนและเข้าสู่ระบบ AI Ecosystem. "
            "รองรับการสร้างบัญชีใหม่และออก **JWT Bearer Token** สำหรับ authenticate request อื่น ๆ"
        ),
    },
    {
        "name": "Data Ingestion",
        "description": (
            "สร้างและจัดการ Dataset สำหรับเก็บข้อมูล AI. "
            "รองรับหลาย format: `image`, `video`, `text`, `json`, `csv`, `audio`. "
            "Dataset ที่สร้างจะผูกกับ MinIO bucket สำหรับเก็บไฟล์จริงใน production."
        ),
    },
    {
        "name": "Inference",
        "description": (
            "ส่ง input data เข้า AI Model แบบ real-time และรับผลการทำนายพร้อม confidence score. "
            "รองรับ image URL, base64 image และ text input. "
            "คืน `latency_ms` สำหรับ performance monitoring."
        ),
    },
    {
        "name": "Training",
        "description": (
            "จัดการคิวการเทรน AI Model (Token Classification / NER) ด้วย Redis Queue (RQ). "
            "รองรับการตั้งเวลาการเริ่มเทรน (Delayed/Scheduled queue) และดึงสถานะงาน"
        ),
    },
]

app = FastAPI(
    # ─── ข้อมูลพื้นฐานของ API ────────────────────────────────────────────────
    title="AI Ecosystem API",
    summary="REST API หลักสำหรับ AI Ecosystem — FastAPI Assignment 5",
    description="""
## 🤖 AI Ecosystem API

ระบบ Backend API สำหรับ **AI Ecosystem** ที่ประกอบด้วยบริการ AI ครบวงจร:
ตั้งแต่การ **จัดการข้อมูล** (Data Ingestion) ไปถึง **การทำนายผล** (Inference) ด้วย AI Model

### 🏗️ Architecture Components
| Component | คำอธิบาย |
|-----------|----------|
| **FastAPI** | Web framework หลัก พร้อม async support |
| **Pydantic v2** | Data validation ด้วย type hints |
| **PostgreSQL** | Relational database (via Docker) |
| **MinIO** | S3-compatible object storage สำหรับไฟล์ AI |
| **Label Studio** | Data labeling platform สำหรับ annotation |

### 🌐 5 Core Endpoints
| # | Method | Endpoint | คำอธิบาย |
|---|--------|----------|----------|
| 1 | `GET`  | `/api/v1/health` | ตรวจสอบสถานะระบบ |
| 2 | `POST` | `/api/v1/auth/register` | ลงทะเบียนผู้ใช้ใหม่ |
| 3 | `POST` | `/api/v1/auth/login` | เข้าสู่ระบบรับ JWT Token |
| 4 | `POST` | `/api/v1/data/datasets` | สร้าง Dataset container |
| 5 | `POST` | `/api/v1/inference/predict` | ทำนายผลด้วย AI Model |

### 📖 API Documentation
- **Swagger UI** (Interactive): [/docs](/docs)
- **ReDoc** (Readable): [/redoc](/redoc)
- **OpenAPI JSON** (Download): [/openapi.json](/openapi.json)
    """,
    version="1.0.0",

    # ─── ข้อมูลผู้พัฒนา ──────────────────────────────────────────────────────
    contact={
        "name": "AI Ecosystem Team",
        "url": "https://github.com/kittipongz2005/ai-ecosystem-AJ-Warintorn",
        "email": "team@ai-ecosystem.dev",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://github.com/kittipongz2005/ai-ecosystem-AJ-Warintorn",

    # ─── OpenAPI / Swagger Paths ──────────────────────────────────────────────
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc UI
    openapi_url="/openapi.json",  # OpenAPI schema (ดาวน์โหลดเพื่อแปลงเป็น CSV ได้)

    # ─── Tag Metadata (จาก tags_metadata ด้านบน) ─────────────────────────────
    openapi_tags=tags_metadata,

    # ─── Lifespan (startup/shutdown hooks) ───────────────────────────────────
    lifespan=lifespan,
)

# ─── CORS Middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router,         prefix="/api/v1",       tags=["Health"])
app.include_router(auth.router,           prefix="/api/v1/auth",  tags=["Authentication"])
app.include_router(data_ingestion.router, prefix="/api/v1/data",  tags=["Data Ingestion"])
app.include_router(inference.router,      prefix="/api/v1/inference", tags=["Inference"])
app.include_router(train.router,          prefix="/api/v1",       tags=["Training"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🤖 Welcome to AI Ecosystem API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
