"""
utils/logger.py
────────────────
Custom Logger สำหรับโปรเจกต์ Friday

การออกแบบ (Design):
─────────────────────
1. Level-based Logging  → รองรับระดับ DEBUG / INFO / WARNING / ERROR / CRITICAL
2. Structured Format    → Timestamp | Level | Module | Message
                          ตัวอย่าง: 2026-07-24 15:30:00,123 | INFO     | backend.main | เริ่มต้นระบบ
3. Multi-Handler        → แสดงบน Console (Terminal) และบันทึกลงไฟล์พร้อมกัน
4. Log Rotation         → ป้องกันไฟล์ Log ใหญ่เกินด้วย RotatingFileHandler
                          แบ่งไฟล์ทุก 5 MB, เก็บสำรองย้อนหลัง 3 ไฟล์
                          (friday.log → friday.log.1 → friday.log.2 → friday.log.3)
5. Singleton Pattern    → ทุกโมดูลใช้ Logger ตัวเดียวกัน (ไม่สร้างซ้ำ)

การใช้งาน:
──────────
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.debug("รายละเอียด Debug")
    logger.info("ข้อความทั่วไป")
    logger.warning("มีบางอย่างน่าสังเกต")
    logger.error("เกิดข้อผิดพลาด")
    logger.critical("ระบบล่ม!")
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# ─────────────────────────────────────────────────────────────────
#  ค่าคงที่ (Constants)
# ─────────────────────────────────────────────────────────────────

# โฟลเดอร์สำหรับเก็บไฟล์ Log (สร้างอัตโนมัติถ้ายังไม่มี)
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "friday.log"

# ─── Principle 2: Structured Format ───
# รูปแบบ: Timestamp | Level | Module | Message
# ตัวอย่าง: 2026-07-24 15:30:00,123 | INFO     | backend.main | เริ่มต้นระบบ
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ─── Principle 4: Log Rotation ───
# แบ่งไฟล์ทุก 5 MB, เก็บสำรองย้อนหลังไว้สูงสุด 3 ไฟล์
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
BACKUP_COUNT = 3                        # friday.log.1, friday.log.2, friday.log.3


# ─────────────────────────────────────────────────────────────────
#  Core Setup Function
# ─────────────────────────────────────────────────────────────────

def _setup_root_logger() -> None:
    """
    ตั้งค่า Root Logger ครั้งแรกครั้งเดียว (Singleton Pattern)

    ─── Principle 5: Singleton Pattern ───
    ตรวจสอบ handlers ก่อน ถ้ามีอยู่แล้วจะไม่สร้างซ้ำ
    ทำให้ทุกโมดูลทั่วทั้งโปรเจกต์ใช้ Logger ตัวเดียวกัน
    """
    root_logger = logging.getLogger("friday")

    # ─── Principle 5: Singleton Guard ───
    # ถ้ามี handlers อยู่แล้ว แสดงว่าเคย setup แล้ว ไม่ต้องทำซ้ำ
    if root_logger.handlers:
        return

    # ─── Principle 1: Level-based Logging ───
    # ตั้งระดับต่ำสุดที่ Root Logger รับ (DEBUG ขึ้นไปทั้งหมด)
    root_logger.setLevel(logging.DEBUG)

    # ─── Principle 2: Structured Format ───
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ─── Principle 3: Multi-Handler ─── Handler 1: Console (stdout) ───
    # แสดงผลใน Terminal เพื่อให้นักพัฒนาดูได้ทันที
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # ─── Principle 3: Multi-Handler ─── Handler 2: RotatingFileHandler ───
    # บันทึกลงไฟล์พร้อมกับ Console
    # ─── Principle 4: Log Rotation ───
    # ถ้าไฟล์เกิน 5 MB จะ rotate เป็นไฟล์ใหม่อัตโนมัติ:
    #   friday.log        ← ไฟล์ปัจจุบัน
    #   friday.log.1      ← สำรองล่าสุด
    #   friday.log.2      ← สำรองกลาง
    #   friday.log.3      ← สำรองเก่าที่สุด (ลบทิ้งเมื่อเกิน)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ลงทะเบียน Handlers ทั้งสองตัวบน Root Logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # ไม่ส่ง Log ต่อไปยัง Root Logger ของ Python เพื่อป้องกัน Log ซ้ำ
    root_logger.propagate = False


# ─────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    ดึง Logger สำหรับโมดูลที่ระบุ

    ─── Principle 5: Singleton Pattern ───
    ทุก Logger จะเป็น child ของ "friday" Root Logger
    รับ Handler และ Level จาก Root Logger โดยอัตโนมัติ
    ไม่ว่าจะเรียก get_logger() กี่ครั้ง จะใช้ Root Logger ตัวเดียวกันเสมอ

    Args:
        name (str): ชื่อโมดูล แนะนำให้ส่ง __name__ เสมอ
                    เช่น get_logger(__name__) → "friday.backend.main"

    Returns:
        logging.Logger: Logger พร้อมใช้งาน รองรับทุก Level

    ตัวอย่าง:
        from utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("โหลดข้อมูลสำเร็จ")
        logger.error("เชื่อมต่อ Database ไม่ได้")
    """
    # เรียก setup ก่อน (Singleton: ครั้งแรกเท่านั้นที่จะสร้าง Handler)
    _setup_root_logger()

    # ─── Principle 5: Singleton ───
    # ใช้ "friday." นำหน้าเพื่อให้เป็น child ของ root logger "friday"
    # Python logging จะ cache Logger ตามชื่อ ไม่สร้างซ้ำ
    return logging.getLogger(f"friday.{name}")


# ─────────────────────────────────────────────────────────────────
#  Demo / Self-Test  (รัน: python utils/logger.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger = get_logger("demo")

    print(f"\n📝 ทดสอบ Custom Logger (ไฟล์ Log บันทึกที่: {LOG_FILE})\n")
    print("─" * 65)

    # ─── Principle 1: Level-based Logging ─── ทดสอบทุก Level ───
    logger.debug("🔍 [DEBUG]    รายละเอียดการ Debug (เห็นเฉพาะ Dev Mode)")
    logger.info("ℹ️  [INFO]     ระบบทำงานปกติ เริ่มต้น Service สำเร็จ")
    logger.warning("⚠️  [WARNING]  ใช้ Config เริ่มต้น ควรตั้งค่า .env ก่อน")
    logger.error("❌ [ERROR]    เชื่อมต่อ Database ไม่ได้ Connection refused")
    logger.critical("🔥 [CRITICAL] ระบบล่ม! ต้องแก้ไขด่วน!")

    print("─" * 65)
    print(f"✅ ดู Log ไฟล์เพิ่มเติมได้ที่: {LOG_FILE}")
    print(f"   (Log Rotation: สูงสุด 5 MB/ไฟล์, เก็บสำรอง {BACKUP_COUNT} ไฟล์)\n")
