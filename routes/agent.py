from core.agent import generate_names
from core.scumbag_agent import evaluate_scumbag, get_scumbag_questions
from schemas import ResultSchema
from schemas.name_schema import NameIn, NamesOut
from schemas.scumbag_schema import ScumbagTestIn, ScumbagTestOut
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


# ---------- 渣男评测 ----------
@router.get("/scumbag/questions")
async def scumbag_get_questions():
    """获取渣男评测题目"""
    return {"code": 200, "message": "获取成功", "data": get_scumbag_questions()}


@router.post("/scumbag/evaluate", response_model=ResultSchema[ScumbagTestOut])
async def scumbag_evaluate(test_in: ScumbagTestIn):
    """提交渣男评测"""
    try:
        result = await evaluate_scumbag(test_in)
        print("result ==>", result)
        if result:
            return {"code": 200, "message": "评测成功", "data": result}
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="评测失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
