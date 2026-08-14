# ⚙️ Core — Configuration & Settings

> **Component**: Application configuration ของ AI Ecosystem API  
> **หน้าที่**: โหลด environment variables จาก `.env` และ expose ผ่าน `settings` object  
> **Technology**: `pydantic-settings` v2 (BaseSettings)

---

## 📁 โครงสร้าง

```text
core/
└── config.py    # Settings class โหลดค่าจาก .env อัตโนมัติ
```

---

## 📌 Settings ที่กำหนดใน `config.py`

| Variable | ค่าเริ่มต้น | Required | คำอธิบาย |
|----------|------------|----------|----------|
| `DATABASE_URL` | — | ✅ Yes | PostgreSQL connection string เช่น `postgresql://user:pass@localhost:5432/db` |
| `MINIO_ENDPOINT` | `localhost:9000` | ❌ No | URL:Port ของ MinIO S3 API |
| `MINIO_ACCESS_KEY` | `minioadmin` | ❌ No | Access key สำหรับ authenticate MinIO |
| `MINIO_SECRET_KEY` | `minioadmin123` | ❌ No | Secret key สำหรับ authenticate MinIO |
| `MINIO_BUCKET_NAME` | `my-images` | ❌ No | ชื่อ default bucket สำหรับเก็บรูปภาพ |
| `MINIO_SECURE` | `False` | ❌ No | ใช้ HTTPS หรือไม่ (true ใน production) |

---

## 🔧 วิธีใช้งาน

**1. กำหนดค่าใน `.env`**:
```env
DATABASE_URL=postgresql://labelstudio:password123@localhost:5432/labelstudio_data
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=my-images
MINIO_SECURE=false
```

**2. Import `settings` ในไฟล์อื่น**:
```python
from backend.core.config import settings

# ใช้ค่า settings
minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)
```

---

## 🔒 Security Notes
- ไม่ commit ไฟล์ `.env` เข้า Git (ดู `.gitignore`)
- ใน production: ใช้ Docker Secrets หรือ Kubernetes Secrets แทน `.env`
- `MINIO_SECURE=True` เมื่อ deploy จริงเพื่อเข้ารหัส traffic
