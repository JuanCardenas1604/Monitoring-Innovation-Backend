import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.rate_limiter import check_rate_limit
from app.core.config import settings
from app.models.user import User, UserRole, PasswordResetToken, PasswordHistory
from app.schemas.user import (
    UserCreate,
    UserCreateAdmin,
    UserLogin,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.api.deps import get_current_user, require_admin
from app.services.email_service import send_reset_password_email, send_password_changed_notification

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _as_utc(dt: datetime) -> datetime:
    """SQLite puede devolver datetimes sin tzinfo; normalizar a UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(f"register:{ip}", max_requests=5, window=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados registros desde esta IP. Intenta de nuevo en {retry_after} segundos",
        )

    existing = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email o nombre de usuario ya está registrado",
        )

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=UserRole.VIEWER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register-admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_admin(
    user_data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email o nombre de usuario ya está registrado",
        )

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    allowed, retry_after = check_rate_limit(f"login:{login_data.username}", max_requests=10, window=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos. Intenta de nuevo en {retry_after} segundos",
        )

    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/forgot-password")
def forgot_password(request: Request, data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una cuenta con ese correo electrónico",
        )

    ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(f"forgot-password:{ip}", max_requests=3, window=3600)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiadas solicitudes. Intenta de nuevo en {retry_after} segundos",
        )

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).update({"used": True}, synchronize_session=False)

    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    db_token = PasswordResetToken(
        user_id=user.id,
        token_jti=jti,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    reset_token = create_access_token(
        {"sub": user.id, "type": "reset", "jti": jti},
        expires_delta=timedelta(minutes=10),
    )

    send_reset_password_email(to_email=user.email, reset_token=reset_token)

    response: dict = {
        "message": "Si el correo está registrado, recibirás un enlace de recuperación",
    }
    if settings.DEBUG:
        response["reset_token"] = reset_token
    return response


@router.post("/reset-password")
def reset_password(request: Request, data: ResetPasswordRequest, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(f"reset-password:{ip}", max_requests=5, window=300)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos. Intenta de nuevo en {retry_after} segundos",
        )

    payload = decode_access_token(data.token)
    if not payload or payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado",
        )

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido",
        )

    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_jti == jti,
        PasswordResetToken.used == False,
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este enlace ya ha sido utilizado o ha expirado. Solicita uno nuevo.",
        )

    if datetime.now(timezone.utc) > _as_utc(db_token.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace ha expirado. Solicita uno nuevo.",
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    limit = settings.PASSWORD_HISTORY_LIMIT
    recent_hashes = [
        h.password_hash
        for h in db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
    ]

    for old_hash in recent_hashes:
        if verify_password(data.password, old_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La contraseña ya fue utilizada recientemente. Elige una diferente a las últimas {limit}.",
            )

    db_token.used = True
    user.hashed_password = hash_password(data.password)

    db.add(PasswordHistory(user_id=user.id, password_hash=user.hashed_password))

    excess = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .offset(limit)
        .all()
    )
    for record in excess:
        db.delete(record)

    db.commit()

    send_password_changed_notification(to_email=user.email)

    return {"message": "Contraseña actualizada correctamente"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
