"""
Pydantic Schemas for Authentication
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john@example.com")
    password: str = Field(..., min_length=8, example="securepassword123")
    full_name: Optional[str] = Field(None, example="John Doe")

    model_config = {"json_schema_extra": {"example": {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "securepassword123",
        "full_name": "John Doe"
    }}}


class UserLoginRequest(BaseModel):
    username: str = Field(..., example="john_doe")
    password: str = Field(..., example="securepassword123")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., example="My API Key")
    description: Optional[str] = Field(None, example="Key for data pipeline")
    expires_days: Optional[int] = Field(30, ge=1, le=365)


class APIKeyResponse(BaseModel):
    key_id: str
    name: str
    api_key: str
    created_at: datetime
    expires_at: Optional[datetime]


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime
