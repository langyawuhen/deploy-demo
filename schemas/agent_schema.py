from pydantic import BaseModel, Field
from typing import List, Annotated


class NamesSchema(BaseModel):
    name: Annotated[str, Field(..., description="姓名", min_length=1, max_length=50)]
    reference: Annotated[str, Field(..., description="出处")]
    moral: Annotated[str, Field(..., description="寓意")]


class NamesResultSchema(BaseModel):
    names: List[NamesSchema]
