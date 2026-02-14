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

system_prompt = """你是一位专业的恋爱关系分析师，擅长从行为模式判断一个人是否具备「渣」的特质。请根据用户的作答，给出客观、幽默但不刻薄的评测。

评测标准：
- 渣男指数 0-100：分数越高，表示在恋爱中的问题行为越多、越典型
- 等级标签：从「绝世好男人」「暖男」「普通直男」「海王」「渣男」到「绝世渣男」等，根据分数合理划分
- 分析要结合具体题目和选项，指出哪些行为值得肯定、哪些需要改进
- 建议要具体、可操作，语气友善，目的是帮助对方成为更好的伴侣

请保持轻松幽默的语气，避免人身攻击。"""


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
    """渣男评测"""
    answers_text = _build_answers_text(test_in.answers)
    user_prompt = f"""请根据以下作答，评测该用户的「渣男指数」并给出分析建议。

【用户作答】
{answers_text}

请严格按照 ScumbagTestOut 格式返回 JSON：score(0-100)、level、analysis、suggestions(字符串列表)。"""

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
            '请仅输出一个 JSON 对象，格式为：{{"score": 0-100, "level": "等级", "analysis": "分析", "suggestions": ["建议1", "建议2"]}}'
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

    return result


def get_scumbag_questions():
    """获取评测题目，供前端展示"""
    return SCUMBAG_QUESTIONS
