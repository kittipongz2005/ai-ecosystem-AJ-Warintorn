# 🛣️ Routers — HTTP Endpoint Handlers

> **Component**: Endpoint layer ของ AI Ecosystem API  
> **หน้าที่**: รับ HTTP request, validate input (ผ่าน Pydantic Schema), เรียก service, คืน response  
> **Pattern**: Thin Controller → Business Logic อยู่ใน `services/`

---

## 📁 โครงสร้าง

```text
routers/
├── __init__.py          # Export ทุก router
├── health.py            # Endpoint 1: GET /api/v1/health
├── auth.py              # Endpoint 2-3: POST /api/v1/auth/register, /login
├── data_ingestion.py    # Endpoint 4: POST /api/v1/data/datasets
└── inference.py         # Endpoint 5: POST /api/v1/inference/predict
```

---

## 📌 รายละเอียดแต่ละ Router

### `health.py` — Health Check
**Endpoint**: `GET /api/v1/health`  
**หน้าที่**: ตรวจสอบสถานะของทุก service ใน AI Ecosystem

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "api":            { "status": "up", "latency_ms": 0.5  },
    "database":       { "status": "up", "latency_ms": 2.1  },
    "minio_storage":  { "status": "up", "latency_ms": 5.3  },
    "label_studio":   { "status": "up", "latency_ms": 12.0 },
    "model_registry": { "status": "up", "latency_ms": 1.2  }
  }
}
```

---

### `auth.py` — Authentication
**Endpoints**: `POST /api/v1/auth/register` | `POST /api/v1/auth/login`

#### Register (201 Created)
- ตรวจสอบ username ซ้ำ → 409 Conflict
- Hash password ด้วย SHA-256 ก่อนบันทึก (ไม่เก็บ plain text)
- Generate `user_id` แบบ `usr-xxxxxxxx` (UUID prefix)
- คืน `UserResponse` (ไม่มี password)

#### Login (200 OK)
- ตรวจสอบ username/password hash → 401 Unauthorized ถ้าผิด
- Generate pseudo-JWT token (`eyJhbGciOiJIUzI1NiJ9.xxx.xxx`)
- คืน Bearer token พร้อม `expires_in: 3600` วินาที

---

### `data_ingestion.py` — Dataset Management
**Endpoint**: `POST /api/v1/data/datasets` (201 Created)

- รับ `name`, `data_format` (image/video/text/csv/audio/json), `tags`
- Generate `dataset_id` แบบ `ds-xxxxxxxx`
- บันทึก metadata (format, tags, timestamps)
- Production: สร้าง MinIO bucket ชื่อเดียวกับ dataset_id

---

### `inference.py` — AI Inference
**Endpoint**: `POST /api/v1/inference/predict` (200 OK)

- รับ `model_id` และ `input_data` (image_url / base64 / text)
- Generate normalized confidence scores สำหรับ 4 labels
- `return_probabilities=false` → คืนเฉพาะ Top-1 prediction
- คืน `latency_ms` สำหรับ performance monitoring
- Detection model (`model_id` มี "detection") → คืน `bounding_box` ด้วย

---

## ✅ HTTP Status Codes ที่ใช้

| Code | ความหมาย | เกิดเมื่อ |
|------|----------|---------|
| `200 OK` | สำเร็จ | GET health, POST login, POST predict |
| `201 Created` | สร้างสำเร็จ | POST register, POST datasets |
| `401 Unauthorized` | ไม่ได้รับอนุญาต | Login ผิด credentials |
| `409 Conflict` | ข้อมูลซ้ำ | Register username ซ้ำ |

---

## 🔧 วิธี Register Router ใน main.py

```python
app.include_router(health.router,         prefix="/api/v1",          tags=["Health"])
app.include_router(auth.router,           prefix="/api/v1/auth",     tags=["Authentication"])
app.include_router(data_ingestion.router, prefix="/api/v1/data",     tags=["Data Ingestion"])
app.include_router(inference.router,      prefix="/api/v1/inference", tags=["Inference"])
```
