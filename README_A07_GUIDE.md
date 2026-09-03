# 🚀 WTN-A07: Trainer Worker Implementation Guide & Documentation

คู่มือสรุปสถาปัตยกรรม วิธีการรันระบบ และข้อมูลสำหรับเขียนรายงานส่งงาน WTN-A07

---

## 🏗️ 1. Architecture Diagram & Workflow

```
[ User / Client ]
       │
       ▼ (1) POST /api/v1/train/enqueue (with scheduled_at / delay_seconds)
[ FastAPI Backend ]
       │
       ▼ (2) Enqueue Delayed Job
 [ Redis Queue (RQ) ] ◄── Scheduled / Time-delayed Trigger
       │
       ▼ (3) Worker receives task when timer expires
[ Trainer Worker (GPU) ]
       │
       ├────► (4) Download Dataset ────► [ MinIO: datasets/token-classification/conll2003/ ]
       │
       ├────► (5) Fine-tune Model (Transformers Token Classification) & Write Log (.log)
       │
       └────► (6) Upload Model & Logs ─► [ MinIO: models/token-classification/{job_id}_{timestamp}/ ]
```

---

## 🛠️ 2. คำตอบสำหรับรายงาน (Report Answers)

### 2.1 การโหลด dataset จาก Hugging Face มาลง MinIO ใช้วิธีการอย่างไร?
- **เครื่องมือที่ใช้**: ไลบรารี `datasets` จาก Hugging Face และ `minio` Python SDK
- **กระบวนการ**:
  1. ใช้สคริปต์ `utils/upload_dataset_to_minio.py` เพื่อดาวน์โหลด Token Classification dataset (เช่น `conll2003`) จาก Hugging Face
  2. แปลงแต่ละ split (`train`, `validation`, `test`) ให้เป็น JSON Lines (`.jsonl`) format
  3. สตรีมข้อมูลอัปโหลดขึ้น MinIO bucket `datasets` ที่ path:
     `token-classification/conll2003/train.jsonl`
     `token-classification/conll2003/validation.jsonl`
     `token-classification/conll2003/test.jsonl`

### 2.2 API URL สำหรับการสั่งเพิ่ม train queue
- **Endpoint**: `POST /api/v1/train/enqueue`
- **Request Body ตัวอย่าง**:
```json
{
  "base_model_name": "distilbert-base-cased",
  "dataset_name": "conll2003",
  "dataset_bucket": "datasets",
  "model_bucket": "models",
  "epochs": 1,
  "batch_size": 8,
  "learning_rate": 2e-5,
  "max_samples": 500,
  "delay_seconds": 60
}
```
*(กำหนด `delay_seconds: 60` เพื่อให้คิวรอ 60 วินาทีก่อนเริ่มเทรน หรือส่ง `scheduled_at: "2026-09-03T19:30:00Z"`)*

### 2.3 การ Enqueue ทำอย่างไร ด้วย queue ชื่ออะไร?
- **เครื่องมือ**: ใช้ **Redis Queue (RQ)** ร่วมกับ Redis instance
- **Queue Name**: `training_queue`
- **การทำงาน**: ใช้ฟังก์ชัน `q.enqueue_at(target_time, ...)` สำหรับงานที่กำหนดเวลาล่วงหน้า หรือ `q.enqueue(...)` สำหรับงานทันที

### 2.4 การดึงข้อมูลจาก MinIO โดย Trainer Worker
- เมื่อ Worker ถึงเวลาทำงาน จะเชื่อมต่อไปยัง MinIO S3 API Endpoint (`minio:9000`)
- ดึงไฟล์ Dataset split `.jsonl` จาก bucket `datasets/token-classification/{dataset_name}/`
- โหลดเข้า Hugging Face `DatasetDict` เพื่อเตรียมทำ tokenization และ feature alignment

### 2.5 ตั้งชื่อโมเดลใน MinIO อย่างไร?
- **Bucket**: `models`
- **Path Pattern**: `token-classification/{job_id}_{YYYYMMDD_HHMMSS}/`
- **ภายในโฟลเดอร์ประกอบด้วย**:
  - Model weights (`model.safetensors` หรือ `pytorch_model.bin`)
  - Config (`config.json`)
  - Tokenizer files (`tokenizer_config.json`, `vocab.txt`, `special_tokens_map.json`)
  - Training Log (`training.log`)

---

## 🐳 3. การรันระบบด้วย Docker Compose

```bash
# สั่ง Build และรันทุก Container (FastAPI, Redis, MinIO, Trainer Worker, DB, Label Studio)
docker compose up -d --build
```

**Flags สำคัญสำหรับ GPU ใน compose.yml**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```
