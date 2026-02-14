from pydantic import BaseModel, Field
from typing import List, Annotated


class ScumbagAnswerItem(BaseModel):
    """单题答案"""
    question_id: Annotated[str, Field(..., description="题目ID")]
    answer: Annotated[str, Field(..., description="用户选择的答案", min_length=1, max_length=500)]


class ScumbagTestIn(BaseModel):
    """渣男评测输入"""
    answers: Annotated[List[ScumbagAnswerItem], Field(..., description="用户作答列表", min_length=1)]


class ScumbagTestOut(BaseModel):
    """渣男评测输出"""
    score: Annotated[int, Field(..., description="渣男指数 0-100", ge=0, le=100)]
    level: Annotated[str, Field(..., description="等级标签")]
    analysis: Annotated[str, Field(..., description="详细分析")]
    suggestions: Annotated[List[str], Field(..., description="改进建议")]
