# api_result.py
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    code: int
    msg: str
    data: Optional[T] = None

def success(data=None):
    return ApiResponse(
        code=200,
        data=jsonable_encoder(data),
        msg="success"
    )

def error(msg="系统错误", code=500):
    return ApiResponse(
        code=code,
        msg=msg,
        data=None
    )