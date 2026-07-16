# users.py
from sqlalchemy import Column, String, Integer, DateTime
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

from .base import MyModel, BaseSchema
from db import Base


# SQLAlchemy 用户模型
class UserModel(Base, MyModel):
    __tablename__ = "users"

    username = Column(String(20), unique=True, index=True, nullable=True)
    password = Column(String(255), nullable=True)
    wx = Column(String(64), unique=True, index=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(255), nullable=True)
    phone = Column(String(11), index=True)
    description = Column(String(255))
    active = Column(Integer, default=1)
    token = Column(String(64), unique=True, index=True, nullable=True)
    token_expires_at = Column(DateTime(), nullable=True)


# 对外输出用，绝不包含 password/token
class UserPublic(BaseSchema):
    username: Optional[str] = None
    wx: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    active: Literal[0, 1] = 1


# 原有的增删改查接口输入用（仍然保留，供 /users/* 使用）
class UserBase(BaseSchema):
    username: Optional[str] = Field(None, min_length=1, max_length=20)
    password: Optional[str] = Field(None, min_length=3, max_length=100)
    wx: Optional[str] = Field(None, min_length=3, max_length=64)
    description: Optional[str] = Field(None, min_length=3, max_length=255)
    active: Literal[0, 1] = Field(
        default=1, description="用户激活状态，1表示激活，0表示禁用"
    )
