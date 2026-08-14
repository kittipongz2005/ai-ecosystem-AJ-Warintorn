# 🚀 Backend — AI Ecosystem FastAPI Server

> **Component หลัก**: FastAPI application server สำหรับ AI Ecosystem  
> **ภาษา**: Python 3.13+  
> **Framework**: FastAPI 0.115+ พร้อม Pydantic v2

---

## 📁 โครงสร้าง Directory

```text
backend/
├── __init__.py              # Package initializer
├── main.py                  # 🏠 FastAPI app entry point (สร้าง app, register routers, middleware)
├── core/
│   └── config.py            # ⚙️  Settings จาก .env ด้วย pydantic-settings
├── routers/                 # 🛣️  Endpoint handlers (รับ HTTP request → ส่งไป service)
│   ├── __init__.py
│   ├── health.py            # GET  /api/v1/health
│   ├── auth.py              # POST /api/v1/auth/register, /api/v1/auth/login
│   ├── data_ingestion.py    # POST /api/v1/data/datasets
│   └── inference.py         # POST /api/v1/inference/predict
├── schemas/                 # 📐 Pydantic models — กำหนด shape ของ request/response
│   ├── __init__.py
│   ├── health.py
│   ├── auth.py
│   ├── data_ingestion.py
│   └── inference.py
└── services/                # 🧠 Business logic layer (แยก logic ออกจาก router)
    ├── __init__.py
    ├── auth_service.py
    ├── data_ingestion_service.py
    └── inference_service.py
```

---

## 📌 รายละเอียดแต่ละ Component

### 1. `main.py` — Application Entry Point
**หน้าที่**: สร้าง FastAPI instance หลัก, กำหนด metadata ของ API (title, description, tags), ลงทะเบียน Router ทั้งหมด และตั้ง Middleware

**สิ่งที่ทำงานในไฟล์นี้**:
- สร้าง `FastAPI()` พร้อม `title`, `description`, `version`, `openapi_tags` สำหรับ Swagger
- ลงทะเบียน `CORSMiddleware` เพื่อให้ Frontend เรียก API ได้
- `include_router()` สำหรับ router แต่ละ domain พร้อม prefix `/api/v1/...`
- `lifespan` context manager: จัดการ startup/shutdown event

---

### 2. `core/config.py` — Configuration Settings
**หน้าที่**: โหลดค่า environment variables จากไฟล์ `.env` ด้วย `pydantic-settings`

**Variables ที่กำหนด**:
| Variable | ค่าเริ่มต้น | คำอธิบาย |
|----------|------------|----------|
| `DATABASE_URL` | (required) | Connection string ของ PostgreSQL |
| `MINIO_ENDPOINT` | `localhost:9000` | URL ของ MinIO S3-compatible storage |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key สำหรับ MinIO |
| `MINIO_SECRET_KEY` | `minioadmin123` | Secret key สำหรับ MinIO |
| `MINIO_BUCKET_NAME` | `my-images` | ชื่อ bucket สำหรับเก็บไฟล์รูปภาพ |
| `MINIO_SECURE` | `False` | เปิด/ปิด HTTPS ต่อ MinIO |

**วิธีใช้ใน module อื่น**:
```python
from backend.core.config import settings
print(settings.MINIO_ENDPOINT)
```

---

### 3. `routers/` — Endpoint Handlers
Router แต่ละไฟล์รับผิดชอบ HTTP endpoint ของตัวเอง ใช้ `APIRouter` จาก FastAPI เพื่อแยก domain ออกจากกัน

#### `health.py`
- **`GET /api/v1/health`** — ตรวจสอบสถานะของระบบ AI Ecosystem ทั้งหมด
- ส่งคืนสถานะของ services: API server, PostgreSQL, MinIO, Label Studio, Model Registry
- ใช้ข้อมูล `platform` และ `sys` เพื่อรายงาน Python version และ OS

#### `auth.py`
- **`POST /api/v1/auth/register`** — ลงทะเบียนผู้ใช้ใหม่
  - รับ `username`, `email`, `password`, `full_name`
  - ตรวจสอบ username ซ้ำ (409 Conflict)
  - Hash password ด้วย SHA-256 ก่อนบันทึก
  - คืน `UserResponse` (ไม่รวม password)
- **`POST /api/v1/auth/login`** — เข้าสู่ระบบ
  - ตรวจสอบ credentials (401 Unauthorized ถ้าผิด)
  - คืน JWT Bearer Token พร้อม `expires_in: 3600`

#### `data_ingestion.py`
- **`POST /api/v1/data/datasets`** — สร้าง Dataset container
  - รับ `name`, `description`, `data_format` (image/video/text/csv/audio), `tags`
  - Generate `dataset_id` แบบ UUID prefix (`ds-xxxxxxxx`)
  - ใน production: สร้าง MinIO bucket สำหรับเก็บไฟล์จริง

#### `inference.py`
- **`POST /api/v1/inference/predict`** — ทำนายผลแบบ real-time
  - รับ `model_id`, `input_data` (image URL / base64 / text), `parameters`
  - Generate normalized confidence scores สำหรับ 4 labels: Normal, Pneumonia, COVID-19, Tuberculosis
  - รองรับ `return_probabilities` flag — ถ้า `false` คืนเฉพาะ Top-1 prediction
  - วัด `latency_ms` สำหรับ monitoring

---

### 4. `schemas/` — Pydantic Data Models
กำหนด **shape ของข้อมูล** ที่เข้าและออกจาก API ด้วย Pydantic v2 (type validation อัตโนมัติ)

| ไฟล์ | Classes หลัก | หน้าที่ |
|------|-------------|---------|
| `health.py` | `HealthResponse` | Response จาก health endpoint |
| `auth.py` | `UserRegisterRequest`, `UserLoginRequest`, `TokenResponse`, `UserResponse` | Validate auth request/response |
| `data_ingestion.py` | `DatasetCreateRequest`, `DatasetResponse`, `DataFormat` (Enum) | Validate dataset creation |
| `inference.py` | `InferenceRequest`, `InferenceResponse`, `PredictionResult` | Validate inference input/output |

**ตัวอย่าง Enum ที่ใช้**:
```python
class DataFormat(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT  = "text"
    JSON  = "json"
    CSV   = "csv"
    AUDIO = "audio"
```

---

### 5. `services/` — Business Logic Layer
แยก business logic ออกจาก router เพื่อให้ router บาง (thin controller) และ service ทำงานได้อิสระ ทดสอบได้ง่าย

| ไฟล์ | หน้าที่ |
|------|---------|
| `auth_service.py` | จัดการ user store, password hashing, token generation |
| `data_ingestion_service.py` | จัดการ dataset lifecycle, เชื่อมต่อ MinIO bucket |
| `inference_service.py` | จัดการ model loading, preprocessing, prediction pipeline |

---

## 🌐 5 Core Endpoints ที่ expose

| # | Method | Endpoint | Status Code | คำอธิบาย |
|---|--------|----------|-------------|----------|
| 1 | `GET`  | `/api/v1/health` | 200 | Health check ระบบทั้งหมด |
| 2 | `POST` | `/api/v1/auth/register` | 201 | ลงทะเบียนผู้ใช้ใหม่ |
| 3 | `POST` | `/api/v1/auth/login` | 200 | เข้าสู่ระบบ รับ JWT token |
| 4 | `POST` | `/api/v1/data/datasets` | 201 | สร้าง Dataset container |
| 5 | `POST` | `/api/v1/inference/predict` | 200 | ทำนายผลด้วย AI Model |

---

## 🚀 Run the Backend Server

```bash
# จาก root ของโปรเจค
uvicorn backend.main:app --reload --port 8000
```

เปิด API Documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 📦 Dependencies ที่ใช้

| Library | เวอร์ชัน | วัตถุประสงค์ |
|---------|---------|------------|
| `fastapi` | ≥0.115 | Web framework หลัก |
| `uvicorn` | ≥0.30 | ASGI server รัน FastAPI |
| `pydantic` | ≥2.0 | Data validation และ serialization |
| `pydantic-settings` | ≥2.0 | โหลด config จาก .env |
| `python-multipart` | ≥0.0.9 | รองรับ file upload (form-data) |
| `minio` | ≥7.2 | Python client สำหรับ MinIO S3 |
| `httpx` | ≥0.27 | Async HTTP client สำหรับ external calls |
