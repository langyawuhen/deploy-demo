from pydantic import BaseModel, Field
from typing import List, Annotated, Literal

from schemas.agent_schema import NamesSchema


class NameIn(BaseModel):
    surname: Annotated[str, Field(..., min_length=1, max_length=20, description="姓氏")]
    gender: Annotated[Literal["不限", "男生", "女生"], Field(..., description="性别")]
    length: Annotated[Literal["不限", "两字", "三字"], Field(..., description="字数")]
    other: Annotated[str | None, Field("", description="其他要求")]
    exclude: Annotated[List[str], Field([], description="排除的姓名")]


class NamesOut(BaseModel):
    names: List[NamesSchema]
