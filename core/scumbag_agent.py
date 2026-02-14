import os
import sys
import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.setting import settings
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from schemas.scumbag_schema import ScumbagTestIn, ScumbagTestOut
from data.scumbag_questions import SCUMBAG_QUESTIONS

os.environ["DASHSCOPE_API_KEY"] = settings.OPENAI_API_KEY

chat_model = ChatTongyi()

system_prompt = """你是一位专业的恋爱关系分析师。渣男指数 0-100，分数越高表示问题行为越多、越渣。

等级与分数对应（必须严格一致）：
- 0-20分：绝世好男人/暖男 → 分析应为正面肯定
- 21-40分：普通直男 → 有小问题可改进
- 41-60分：海王倾向 → 需警惕
- 61-80分：渣男 → 红 flag 较多
- 81-100分：绝世渣男 → 严重问题

你的 level、analysis、suggestions 必须与给定分数完全一致，不得矛盾。请保持客观、幽默但不刻薄。"""


# 选项 A/B/C/D 对应的渣男指数分值（越高越渣）
_OPTION_SCORE = {"A": 0, "B": 25, "C": 60, "D": 100}


def _compute_score(answers: list) -> int:
    """根据作答规则计算渣男指数 0-100，分数越高越渣"""
    if not answers:
        return 0
    total = 0
    for a in answers:
        total += _OPTION_SCORE.get(a.answer.upper(), 50)  # 未知选项取中间值
    return round(total / len(answers))


def _build_answers_text(answers: list) -> str:
    """将作答转为可读文本"""
    q_map = {q["id"]: q for q in SCUMBAG_QUESTIONS}
    lines = []
    for a in answers:
        q = q_map.get(a.question_id, {})
        text = q.get("text", a.question_id)
        opt = q.get("options", {}).get(a.answer, a.answer)
        lines.append(f"Q: {text}\nA: {a.answer} - {opt}")
    return "\n\n".join(lines)


def _parse_json_from_content(content: str) -> ScumbagTestOut | None:
    """从模型返回中解析 JSON"""
    if not content or not content.strip():
        return None
    text = content.strip()
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block:
        try:
            data = json.loads(code_block.group(1).strip())
            return ScumbagTestOut.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass
    obj_match = re.search(r"\{[\s\S]*\}", text)
    raw = (obj_match.group(0) if obj_match else text).strip()
    try:
        return ScumbagTestOut.model_validate(json.loads(raw))
    except (json.JSONDecodeError, Exception):
        return None


# 绑定结构化输出
structured_llm = chat_model.with_structured_output(ScumbagTestOut)


async def evaluate_scumbag(test_in: ScumbagTestIn) -> ScumbagTestOut | None:
    """渣男评测：分数规则计算，分析由 LLM 生成且必须与分数一致"""
    # 1. 规则计算分数（保证与选项一一对应，高分=越渣）
    score = _compute_score(test_in.answers)
    answers_text = _build_answers_text(test_in.answers)

    user_prompt = f"""渣男指数已计算为 {score} 分。请根据以下作答和该分数，生成与之完全一致的 level、analysis、suggestions。

【用户作答】
{answers_text}

【要求】level 与 analysis 必须符合 {score} 分的档次（0-20好/21-40普通/41-60海王/61-80渣/81-100绝世渣），不得矛盾。
请严格按照 JSON 格式返回：{{"score": {score}, "level": "等级", "analysis": "分析", "suggestions": ["建议1", "建议2"]}}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    result = None
    try:
        result = await structured_llm.ainvoke(messages)
    except Exception as e:
        print("scumbag structured_llm.ainvoke error ==>", e)

    if result is None:
        json_instruction = (
            f'请仅输出一个 JSON 对象，格式为：{{"score": {score}, "level": "等级", "analysis": "分析", "suggestions": ["建议1", "建议2"]}}'
        )
        fallback_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt + "\n\n" + json_instruction),
        ]
        try:
            raw_response = await chat_model.ainvoke(fallback_messages)
            content = getattr(raw_response, "content", None) or str(raw_response)
            result = _parse_json_from_content(content)
        except Exception as e:
            print("scumbag fallback error ==>", e)

    # 2. 强制使用规则计算的分数，避免 LLM 返回矛盾值
    if result:
        result = ScumbagTestOut(
            score=score,
            level=result.level,
            analysis=result.analysis,
            suggestions=result.suggestions,
        )
    return result


def get_scumbag_questions():
    """获取评测题目，供前端展示"""
    return SCUMBAG_QUESTIONS
