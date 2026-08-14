# 🤖 AI Ecosystem — Project Repository


## 1️⃣ รูปแบบและแนวคิดของโปรเจค

โปรเจคนี้เป็น **AI Ecosystem** — ระบบที่รวมทุก component ที่จำเป็นสำหรับ AI pipeline ครบวงจร ตั้งแต่การเก็บข้อมูล (Data Ingestion) ไปจนถึงการทำนายผล (Inference) โดยใช้แนวคิด **Layered Architecture** และ **Microservice-ready Design**

### แนวคิดหลัก: Separation of Concerns
```
HTTP Request
    ↓
Router     (รับ request → validate input)
    ↓
Service    (business logic → เรียก external services)
    ↓
Schema     (serialize response → คืน JSON)
    ↓
HTTP Response
```

### รูปแบบโครงสร้าง: Domain-Driven
แบ่ง code ตาม **domain** ของงาน ไม่ใช่ตาม technical type:
- **Health** → ตรวจสอบสถานะระบบ
- **Auth** → จัดการ user และ token
- **Data Ingestion** → จัดการ dataset และไฟล์
- **Inference** → ทำนายผลด้วย AI Model

---

## 2️⃣ โครงสร้าง Directory และหน้าที่แต่ละส่วน

```text
Friday/                          # Root ของโปรเจค
├── 📄 main.py                   # Entry point: รัน uvicorn server
├── 📄 pyproject.toml            # Project metadata & dependencies (uv/pip)
├── 📄 compose.yml               # Docker Compose: PostgreSQL, Label Studio, MinIO
├── 📄 openapi_to_csv.py         # 🆕 Script แปลง openapi.json → CSV (ข้อ 3e)
├── 📄 .env                      # Environment variables (ไม่ commit ขึ้น Git)
├── 📄 .python-version           # กำหนด Python version (3.13)
│
├── 📁 backend/                  # 🏗️ FastAPI Application
│   ├── 📄 main.py               # FastAPI app, routers, middleware, metadata
│   ├── 📁 core/                 # ⚙️ Configuration (pydantic-settings + .env)
│   ├── 📁 routers/              # 🛣️ HTTP Endpoint handlers (5 endpoints)
│   ├── 📁 schemas/              # 📐 Pydantic models (request/response validation)
│   └── 📁 services/             # 🧠 Business logic layer
│
├── 📁 utils/                    # 🔧 Shared utilities
│   └── logger.py               # Logging configuration
│
├── 📁 workers/                  # ⚡ Background job workers (Celery/ARQ)
│   └── (empty — reserved)
│
├── 📁 sandbox/                  # 🧪 Development & testing scripts
│   ├── enqueue_job.py           # ทดสอบการ enqueue background jobs
│   ├── worker_settings.py       # Worker configuration
│   ├── test_labelstudio.py      # ทดสอบการเชื่อมต่อ Label Studio
│   ├── test_postgres.py         # ทดสอบการเชื่อมต่อ PostgreSQL
│   ├── test_settings.py         # ทดสอบการโหลด environment settings
│   └── minio/                   # ทดสอบการเชื่อมต่อ MinIO
│
├── 📁 diagram/                  # 📊 System Architecture Diagrams
│   ├── overview.drawio          # System overview diagram (source)
│   ├── overview.png             # System overview diagram (exported)
│   ├── postgreSQL.drawio        # Database schema diagram (source)
│   └── postgreSQL.png           # Database schema diagram (exported)
│
└── 📁 storage/                  # 💾 Local storage สำหรับ artifacts และ logs
    ├── artifacts/               # Output files จาก AI pipeline
    └── logs/                    # Application log files
```

---

## 3️⃣ Libraries ที่ติดตั้งและวัตถุประสงค์

| Library | Version | วัตถุประสงค์ |
|---------|---------|------------|
| `fastapi` | ≥0.115 | Web framework หลัก — สร้าง REST API พร้อม auto-generated Swagger |
| `uvicorn[standard]` | ≥0.30 | ASGI server — รัน FastAPI application |
| `pydantic` | ≥2.0 | Data validation และ serialization ด้วย type hints |
| `pydantic-settings` | ≥2.0 | โหลด environment variables จาก `.env` อัตโนมัติ |
| `python-multipart` | ≥0.0.9 | รองรับ file upload ผ่าน `multipart/form-data` |
| `minio` | ≥7.2 | Python client สำหรับ MinIO S3-compatible object storage |
| `httpx` | ≥0.27 | Async HTTP client สำหรับเรียก external services |

**Infrastructure (Docker Compose)**:
| Service | Image | Port | วัตถุประสงค์ |
|---------|-------|------|------------|
| PostgreSQL | `postgres:15` | 5432 | Relational database สำหรับ Label Studio |
| Label Studio | `heartexlabs/label-studio:latest` | 8080 | Data annotation platform |
| MinIO | `minio/minio:latest` | 9000/9001 | Object storage สำหรับเก็บไฟล์ AI |

---

## 4️⃣ 5 Core Endpoints

| # | Method | Endpoint | Status | คำอธิบาย |
|---|--------|----------|--------|----------|
| 1 | `GET`  | `/api/v1/health` | 200 | ตรวจสอบสถานะ API, PostgreSQL, MinIO, Label Studio |
| 2 | `POST` | `/api/v1/auth/register` | 201 | ลงทะเบียนผู้ใช้ใหม่ + SHA-256 hashed password |
| 3 | `POST` | `/api/v1/auth/login` | 200 | เข้าสู่ระบบ + ออก JWT Bearer Token |
| 4 | `POST` | `/api/v1/data/datasets` | 201 | สร้าง Dataset container พร้อม MinIO bucket |
| 5 | `POST` | `/api/v1/inference/predict` | 200 | ทำนายผล AI พร้อม confidence scores + latency |

---

## 🚀 Quick Start

### 1. Start Infrastructure (Docker)
```bash
docker compose up -d
```

### 2. Install Python Dependencies
```bash
# ด้วย uv (แนะนำ)
uv sync

# หรือด้วย pip
pip install -e .
```

### 3. Run FastAPI Server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. ดู API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 📊 แปลง API List เป็น CSV

```bash
# รัน server ก่อน แล้วรัน script
python openapi_to_csv.py

# หรือระบุ options
python openapi_to_csv.py --url http://localhost:8000/openapi.json --output api_list.csv
```

ไฟล์ `api_snapshot.csv` จะถูกสร้างขึ้น — เปิดด้วย Excel หรือ Google Sheets ได้เลย

---

## 📚 README แต่ละ Component

| Component | README |
|-----------|--------|
| Backend (FastAPI app) | [backend/README.md](backend/README.md) |
| Routers (Endpoints) | [backend/routers/README.md](backend/routers/README.md) |
| Schemas (Pydantic models) | [backend/schemas/README.md](backend/schemas/README.md) |
| Services (Business logic) | [backend/services/README.md](backend/services/README.md) |
| Core (Configuration) | [backend/core/README.md](backend/core/README.md) |
