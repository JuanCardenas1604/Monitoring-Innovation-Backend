from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole

PASSWORD_RULES = [
    (r".{8,}", "mínimo 8 caracteres"),
    (r"[A-Z]", "debe contener una mayúscula"),
    (r"[a-z]", "debe contener una minúscula"),
    (r"[0-9]", "debe contener un número"),
    (r"[^A-Za-z0-9]", "debe contener un carácter especial"),
]


def _validate_password(v: str) -> str:
    for pattern, msg in PASSWORD_RULES:
        if not __import__("re").search(pattern, v):
            raise ValueError(msg)
    return v


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

    _validate_password = field_validator("password")(_validate_password)


class UserCreateAdmin(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER

    _validate_password = field_validator("password")(_validate_password)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdateRole(BaseModel):
    role: UserRole


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=128)

    _validate_password = field_validator("password")(_validate_password)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
