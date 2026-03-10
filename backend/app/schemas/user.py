# app/schemas/user.py
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        # Разрешаем только латинские буквы, цифры, точку, дефис и подчеркивание
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError("Username can only contain letters, numbers, _, ., and -")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserRead(UserBase):
    id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtherUserProfile(UserBase):
    id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_online: bool
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True


class MyUserProfile(UserBase):
    id: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    two_factor_enabled: Optional[bool] = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    avatar_url: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
