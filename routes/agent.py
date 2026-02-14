from core.agent import generate_names
from schemas import ResultSchema
from schemas.name_schema import NameIn, NamesOut
from fastapi import APIRouter, HTTPException, status
import json

router = APIRouter(prefix="/agent", tags=["生成推荐姓名"])


def is_json_string(s):
    try:
        json.loads(s)
        return True
    except ValueError:
        return False


@router.post("/create", response_model=ResultSchema[NamesOut])
async def get_generate_names(name_info: NameIn):
    try:
        names = await generate_names(name_info)
        if names:
            return {"code": 200, "message": "获取成功", "data": names}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取失败")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
