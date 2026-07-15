# word_meanings.py
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from pydantic import Field
from .base import MyModel, BaseSchema
from db import Base


# SQLAlchemy 用户模型
class WordMeaningsModel(Base, MyModel):
    __tablename__ = "word_meanings"
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), nullable=False, comment='单词ID')
    type = Column(String(20), nullable=False, comment='词性')
    content = Column(Text, nullable=False, comment='释义内容')


# Pydantic 模型
class WordMeaningsBase(BaseSchema):
    word_id: int = Field(..., min_length=1, max_length=30)
    type: str = Field(..., min_length=1, max_length=30)
    content: str = Field(..., min_length=1, max_length=100)
