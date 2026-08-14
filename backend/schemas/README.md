# 📐 Schemas — Pydantic Data Models

> **Component**: Data validation layer สำหรับ AI Ecosystem API  
> **หน้าที่**: กำหนด shape, validate และ serialize ข้อมูลที่เข้า/ออก API  
> **Technology**: Pydantic v2 พร้อม type hints

---

## 📁 โครงสร้าง

```text
schemas/
├── __init__.py          # Export ทุก schema
├── health.py            # Health check response models
├── auth.py              # Authentication request/response models
├── data_ingestion.py    # Dataset management models + DataFormat/DataSourceType Enums
└── inference.py         # AI inference request/response models
```

---

## 📌 รายละเอียดแต่ละ Schema

### `health.py`
| Class | ทิศทาง | Fields |
|-------|--------|--------|
| `HealthResponse` | Response | `status`, `timestamp`, `version`, `services` |

---

### `auth.py`
| Class | ทิศทาง | Fields สำคัญ |
|-------|--------|-------------|
| `UserRegisterRequest` | Request | `username` (3-50 chars), `email`, `password` (≥8 chars), `full_name` |
| `UserLoginRequest` | Request | `username`, `password` |
| `TokenResponse` | Response | `access_token`, `token_type="bearer"`, `expires_in=3600` |
| `UserResponse` | Response | `user_id`, `username`, `email`, `full_name`, `role`, `created_at` |

**ข้อสังเกต**: `UserResponse` ไม่มี `password_hash` → ป้องกัน sensitive data รั่วไหล

---

### `data_ingestion.py`
| Class | ทิศทาง | Fields สำคัญ |
|-------|--------|-------------|
| `DatasetCreateRequest` | Request | `name`, `description`, `data_format` (Enum), `tags`, `metadata` |
| `DatasetResponse` | Response | `dataset_id`, `name`, `data_format`, `total_items`, `size_bytes`, `created_at` |

**Enum ที่ใช้**:
```python
class DataFormat(str, Enum):
    IMAGE = "image" | VIDEO = "video" | TEXT = "text"
    JSON = "json"  | CSV = "csv"     | AUDIO = "audio"
```

---

### `inference.py`
| Class | ทิศทาง | Fields สำคัญ |
|-------|--------|-------------|
| `InferenceRequest` | Request | `model_id`, `input_data` (dict), `parameters`, `return_probabilities` |
| `PredictionResult` | Nested | `label`, `confidence` (float), `bounding_box` (Optional) |
| `InferenceResponse` | Response | `prediction_id`, `model_id`, `predictions[]`, `latency_ms`, `timestamp` |

---

## ✅ Best Practices ที่ใช้
- `Field(...)` พร้อม `example` ทุก field → Swagger แสดงตัวอย่างอัตโนมัติ
- `model_config` พร้อม `json_schema_extra` → กำหนด example body สำหรับ Swagger UI
- `EmailStr` validator สำหรับ email format validation
- `min_length`, `max_length`, `ge`, `le` สำหรับ field-level constraints
