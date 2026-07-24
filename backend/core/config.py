from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # กำหนดตัวแปรที่ต้องการดึงจากไฟล์ .env
    DATABASE_URL: str

    # ตั้งค่าให้ดึงข้อมูลจากไฟล์ .env (Pydantic v2 style)
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

# ประกาศตัวแปร settings ไว้ให้ไฟล์อื่นเรียกใช้งาน
settings = Settings()   