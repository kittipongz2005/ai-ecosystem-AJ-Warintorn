from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ========== PostgreSQL ==========
    DATABASE_URL: str

    # ========== MinIO ==========
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_NAME: str = "my-images"
    MINIO_SECURE: bool = False

    # ========== Redis ==========
    REDIS_URL: str = "redis://localhost:6379/0"


    # ตั้งค่าให้ดึงข้อมูลจากไฟล์ .env (Pydantic v2 style)
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

# ประกาศตัวแปร settings ไว้ให้ไฟล์อื่นเรียกใช้งาน
settings = Settings()