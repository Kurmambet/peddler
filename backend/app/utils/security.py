# app/utils/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.config import get_settings
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password(password: str) -> str:
    # bcrypt ограничен 72 байтами, поэтому обрезаем по байтам
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raw = raw[:72]
    return raw.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    safe = _truncate_password(password)
    return pwd_context.hash(safe)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    safe = _truncate_password(plain_password)
    return pwd_context.verify(safe, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    subject — обычно user_id или username.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload

    # Бросает JWTError, если токен невалиден/истёк.
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id_from_token(token: str) -> int:
    payload = decode_token(token)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return int(sub)
