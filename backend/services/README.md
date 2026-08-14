# 🧠 Services — Business Logic Layer

> **Component**: Business logic layer ของ AI Ecosystem API  
> **หน้าที่**: แยก logic ออกจาก router → ทำให้ code ทดสอบได้ง่าย, แก้ไขได้โดยไม่กระทบ endpoint  
> **Pattern**: Service Layer (Separation of Concerns)

---

## 📁 โครงสร้าง

```text
services/
├── __init__.py                  # Export ทุก service
├── auth_service.py              # จัดการ user, password hashing, token
├── data_ingestion_service.py    # จัดการ dataset lifecycle + MinIO
└── inference_service.py         # จัดการ model pipeline + prediction
```

---

## 📌 รายละเอียดแต่ละ Service

### `auth_service.py` — Authentication Service
**หน้าที่**: จัดการ user management และ authentication logic

**ฟังก์ชันหลัก**:
- `create_user(request)` — บันทึก user ใหม่พร้อม hash password
- `authenticate_user(username, password)` — ตรวจสอบ credentials
- `generate_token(user_id)` — สร้าง JWT-like access token
- `get_user_by_username(username)` — ค้นหา user จาก in-memory store

**Storage**: In-memory dict (production: SQLAlchemy + PostgreSQL)

---

### `data_ingestion_service.py` — Data Ingestion Service
**หน้าที่**: จัดการ dataset lifecycle และเชื่อมต่อ MinIO object storage

**ฟังก์ชันหลัก**:
- `create_dataset(request)` — สร้าง dataset พร้อม metadata
- `create_minio_bucket(dataset_id)` — สร้าง bucket ใน MinIO สำหรับเก็บไฟล์
- `upload_file(dataset_id, file)` — อัพโหลดไฟล์เข้า MinIO bucket
- `get_dataset(dataset_id)` — ดึง dataset metadata

**Dependency**: MinIO Python client (`minio>=7.2`)

---

### `inference_service.py` — Inference Service
**หน้าที่**: จัดการ AI model pipeline ตั้งแต่รับ input จนถึงคืน prediction

**ฟังก์ชันหลัก**:
- `run_inference(request)` — รัน model และคืนผลการทำนาย
- `preprocess_input(input_data)` — แปลง input (URL/base64/text) ให้พร้อม inference
- `normalize_scores(raw_scores)` — Normalize confidence scores ให้รวมเป็น 1.0
- `format_response(predictions, latency)` — จัดรูปแบบ response พร้อม metadata

---

## 🔄 Data Flow: Router → Service

```
HTTP Request
    ↓
Router (รับ request, validate ด้วย Pydantic)
    ↓
Service (business logic, ติดต่อ external services)
    ↓
Response (serialize ด้วย Pydantic schema)
    ↓
HTTP Response
```

---

## ✅ ประโยชน์ของ Service Layer
- **Testability**: Unit test service ได้โดยไม่ต้องมี HTTP request
- **Reusability**: หลาย router ใช้ service เดียวกันได้
- **Maintainability**: เปลี่ยน database/storage โดยไม่กระทบ router
- **Single Responsibility**: Router แค่รับ/คืนข้อมูล, Service จัดการ logic
