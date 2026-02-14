import os
import sys
from pathlib import Path

# 直接运行本文件时，将项目根目录加入 path，保证 config、schemas 等可导入
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.setting import settings
# from langchain_community.llms import Tongyi # 单轮对话
#
# os.environ["DASHSCOPE_API_KEY"] = settings.OPENAI_API_KEY
# print(Tongyi().invoke("你是谁"))


from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from schemas.agent_schema import NamesResultSchema
from schemas.name_schema import NameIn
import asyncio
import json
import re

os.environ["DASHSCOPE_API_KEY"] = settings.OPENAI_API_KEY

chat_model = ChatTongyi()

system_prompt = """
你是一位精通汉语言文学、音韵学与传统文化的命名专家，擅长为人物创作兼具音律美感、深刻寓意与文化内涵的姓名。请严格遵循以下原则进行命名：

发音优先：名字需平仄协调、声调起伏自然，避免拗口、谐音歧义（如不雅谐音、负面联想），朗朗上口，富有韵律感；
寓意深远：结合用户提供的背景（如姓氏、性别、字数和其他要求等），选取具有积极象征意义的意象（如自然元素、美德品质、经典典故），做到“名以载道”；
内涵厚重：优先从《诗经》《楚辞》《论语》等经典文献，或唐诗宋词、成语典故中汲取灵感，确保名字有出处、有底蕴，避免空洞堆砌；
现代适配：在尊重传统的基础上，兼顾当代语境与审美，避免过度古奥或生僻字（生僻字需附注音与释义），确保实用性与传播性；
个性化定制：根据用户具体需求（如性别倾向、字数限制、风格偏好—儒雅/清丽/大气/灵动等），提供10个候选方案，并按照以下格式输出：
【姓名】姓名
【出处】典籍来源或文化意象
【寓意】字义拆解与整体象征

"""

# user_message = [
#     SystemMessage(content=system_prompt),
#     HumanMessage(content="你是谁")
# ]
#
# response = chat_model.invoke(user_message)  #多轮对话
# print(response.content)


# 使用 with_structured_output 绑定输出格式
structured_llm = chat_model.with_structured_output(NamesResultSchema)


def _parse_json_from_content(content: str) -> NamesResultSchema | None:
    """从模型返回的文本中提取 JSON 并解析为 NamesResultSchema。"""
    if not content or not content.strip(): # 空文本
        return None
    text = content.strip()
    # 先尝试 ```json ... ``` 或 ``` ... ```
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block:
        try:
            data = json.loads(code_block.group(1).strip())
            return NamesResultSchema.model_validate(data)
        except (json.JSONDecodeError, Exception):
            pass
    # 再尝试整段为 JSON 或匹配 {...}
    obj_match = re.search(r"\{[\s\S]*\}", text)
    raw = (obj_match.group(0) if obj_match else text).strip()
    try:
        return NamesResultSchema.model_validate(json.loads(raw))
    except (json.JSONDecodeError, Exception):
        return None


async def generate_names(name_info: NameIn) -> NamesResultSchema | None:
    prompt = f"用户的姓氏是：{name_info.surname}，用户的性别为：{name_info.gender}，算上姓用户的字数要求为：{name_info.length}，用户的其他要求为：{name_info.other}，这些名字不要：{'、'.join(name_info.exclude)}，请为用户生成5个符合要求的姓名。"
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt),
    ]
    result = None
    try:
        result = await structured_llm.ainvoke(messages)
    except Exception as e:
        print("structured_llm.ainvoke error ==>", e)
    # 若结构化输出为 None（部分模型/环境下 function calling 未正确返回），则用原始模型并解析 JSON
    if result is None:
        json_instruction = (
            '请仅输出一个 JSON 对象，不要其他说明，姓名是姓和名的组合。格式为：{"names": [{"name": "姓名", "reference": "出处", "moral": "寓意"}, ...]}，共10个姓名。'
        )
        fallback_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt + "\n\n" + json_instruction),
        ]
        try:
            raw_response = await chat_model.ainvoke(fallback_messages)
            content = getattr(raw_response, "content", None) or str(raw_response)
            result = _parse_json_from_content(content)
        except Exception as e:
            print("fallback chat_model.ainvoke error ==>", e)
    return result

# if __name__ == '__main__':
#     asyncio.run(generate_names(NameIn(surname="张", gender="男", length="单字", other="", exclude=["张三"])))