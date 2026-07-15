# users.py
from sqlalchemy import Column, String, Integer
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from datetime import datetime

from .base import MyModel, BaseSchema
from db import Base


# SQLAlchemy 用户模型
class UserModel(Base, MyModel):
    __tablename__ = "users"

    username = Column(String(20), unique=True, index=True, nullable=False)
    password = Column(String(16), nullable=False)
    wx = Column(String(30), index=True)
    phone = Column(String(11), index=True)
    description = Column(String(255), default=True)
    active = Column(Integer, default=1)


# Pydantic 模型
class UserBase(BaseSchema):
    username: str = Field(..., min_length=1, max_length=20, )
    password: str = Field(..., min_length=3, max_length=16,)
    wx: str = Field(..., min_length=3, max_length=30, )
    description: str = Field(..., min_length=3, max_length=255)
    active: Literal[0, 1] = Field(
        default=1, description="用户激活状态，1表示激活，0表示禁用"
    )
