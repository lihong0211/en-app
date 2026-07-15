# words.py
from sqlalchemy import Column, String, JSON
from pydantic import Field, BaseModel
from typing import List
from .base import MyModel, BaseSchema
from db import Base


# SQLAlchemy 用户模型
class WordModel(Base, MyModel):
    __tablename__ = "words"
    word = Column(String(30), unique=True, index=True, nullable=False)
    en_pronunciation = Column(String(30), unique=False, index=False, nullable=True)
    us_pronunciation = Column(String(30), unique=False, index=False, nullable=True)


# 定义含义的子模型
class MeaningItem(BaseModel):
    type: str = Field(..., description="词性类型，如 vt., adj. 等")
    content: str = Field(..., description="含义内容")


# Pydantic 模型
class WordBase(BaseSchema):
    word: str = Field(..., min_length=1, max_length=30)
    en_pronunciation: str = Field(..., min_length=1, max_length=30)
    us_pronunciation: str = Field(..., min_length=1, max_length=30)
    meaning: List[MeaningItem] = Field(..., description="单词含义列表")


# 用于创建和响应的模型
class WordCreate(WordBase):
    pass


class WordResponse(WordBase):
    id: int

    class Config:
        orm_mode = True
