"""
1、orm模型
2、pydantic 模型
"""
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')

class ResultSchema(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None
