# users.py
from sqlalchemy import Column, String, Boolean
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import bcrypt

from .base import MyModel
from db import Base


# 密码工具类
class PasswordUtil:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )


# SQLAlchemy 用户模型
class UserModel(Base, MyModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), index=True)
    is_active = Column(Boolean, default=True)

    @classmethod
    def loads(cls, json_data):
        item = cls()
        for key, value in json_data.items():
            if hasattr(cls, key) and value is not None:
                # 特殊处理密码字段
                if key == "password":
                    setattr(item, "hashed_password", PasswordUtil.hash_password(value))
                else:
                    setattr(item, key, value)
        return item


# Pydantic 模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    email: EmailStr = Field(..., example="john@example.com")
    full_name: Optional[str] = Field(None, max_length=100, example="John Doe")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, example="securepassword123")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True


class UserOut(UserInDB):
    pass
