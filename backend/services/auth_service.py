"""
Authentication Service
Business logic for user registration, login, and API key management
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from backend.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    APIKeyCreateRequest,
    APIKeyResponse,
    UserResponse,
)


# ─── In-Memory Storage (In production: use SQLAlchemy + PostgreSQL) ─────────────
_users_db: dict = {}
_api_keys_db: dict = {}


def _hash_password(password: str) -> str:
    """Hash password with SHA-256 (In production: use bcrypt)"""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id: str) -> str:
    """Generate mock JWT token (In production: use python-jose)"""
    return f"eyJhbGciOiJIUzI1NiJ9.{secrets.token_urlsafe(32)}.{user_id[:8]}"


def register_user(body: UserRegisterRequest) -> UserResponse:
    """
    ลงทะเบียนผู้ใช้ใหม่
    - ตรวจสอบ username ซ้ำ
    - Hash password ก่อนบันทึก
    - คืน UserResponse (ไม่รวม password)
    """
    if body.username in _users_db:
        raise ValueError("Username already exists")

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    user = {
        "user_id": user_id,
        "username": body.username,
        "email": body.email,
        "full_name": body.full_name,
        "password_hash": _hash_password(body.password),
        "role": "user",
        "created_at": datetime.utcnow(),
    }
    _users_db[body.username] = user

    return UserResponse(
        user_id=user["user_id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=user["created_at"],
    )


def authenticate_user(body: UserLoginRequest) -> TokenResponse:
    """
    ตรวจสอบ credentials และสร้าง access token
    - ตรวจสอบ username/password
    - สร้าง JWT token (mock)
    - คืน token พร้อม expiry
    """
    user = _users_db.get(body.username)
    if not user or user["password_hash"] != _hash_password(body.password):
        raise ValueError("Invalid username or password")

    token = _generate_token(user["user_id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
    )


def create_api_key(body: APIKeyCreateRequest) -> APIKeyResponse:
    """
    สร้าง API Key ใหม่
    - Generate random key ด้วย secrets module
    - Hash key ก่อนบันทึก (แสดง plain key ครั้งเดียว)
    - กำหนด expiry ถ้ามี expires_days
    """
    key_id = f"key-{uuid.uuid4().hex[:8]}"
    api_key = f"ai-eco-{secrets.token_urlsafe(32)}"
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=body.expires_days) if body.expires_days else None

    _api_keys_db[key_id] = {
        "key_id": key_id,
        "name": body.name,
        "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
        "created_at": created_at,
        "expires_at": expires_at,
    }

    return APIKeyResponse(
        key_id=key_id,
        name=body.name,
        api_key=api_key,  # Only shown once!
        created_at=created_at,
        expires_at=expires_at,
    )


def list_api_keys() -> dict:
    """ดึงรายการ API Keys (ไม่แสดง key จริง)"""
    return {
        "keys": [
            {
                "key_id": k["key_id"],
                "name": k["name"],
                "created_at": k["created_at"].isoformat(),
                "expires_at": k["expires_at"].isoformat() if k["expires_at"] else None,
            }
            for k in _api_keys_db.values()
        ],
        "total": len(_api_keys_db),
    }


def revoke_api_key(key_id: str) -> None:
    """ยกเลิก API Key"""
    if key_id not in _api_keys_db:
        raise KeyError(f"API Key '{key_id}' not found")
    del _api_keys_db[key_id]
