import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.sqlite import VARCHAR
from sqlalchemy.orm import relationship

from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(VARCHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan", order_by="PasswordHistory.created_at.desc()")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(VARCHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(VARCHAR(36), ForeignKey("users.id"), nullable=False, index=True)
    token_jti = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="password_reset_tokens")


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(VARCHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(VARCHAR(36), ForeignKey("users.id"), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="password_history")
