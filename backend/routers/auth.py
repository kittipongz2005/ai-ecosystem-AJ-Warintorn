"""
Authentication Router
ลงทะเบียนและเข้าสู่ระบบด้วย JWT Token
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import uuid
import hashlib
import secrets

from backend.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()

# ─── Mock Database (In production: use SQLAlchemy + PostgreSQL) ─────────────────
_users_db: dict = {}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id: str) -> str:
    return f"eyJhbGciOiJIUzI1NiJ9.{secrets.token_urlsafe(32)}.{user_id[:8]}"


# ─── Endpoint 2: POST /api/v1/auth/register ────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="สร้างบัญชีผู้ใช้ใหม่ใน AI Ecosystem พร้อม hashed password"
)
async def register(body: UserRegisterRequest):
    """
    ลงทะเบียนผู้ใช้ใหม่
    - ตรวจสอบ username ซ้ำ (409 Conflict)
    - Hash password ด้วย SHA-256
    - คืน UserResponse (ไม่รวม password)
    """
    if body.username in _users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

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


# ─── Endpoint 3: POST /api/v1/auth/login ──────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="เข้าสู่ระบบด้วย username/password รับ JWT Bearer Token"
)
async def login(body: UserLoginRequest):
    """
    ตรวจสอบ credentials และออก access token
    - ตรวจสอบ username/password (401 Unauthorized ถ้าผิด)
    - คืน JWT token พร้อม expires_in
    """
    user = _users_db.get(body.username)
    if not user or user["password_hash"] != _hash_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = _generate_token(user["user_id"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
    )
