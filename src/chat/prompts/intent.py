"""
意图识别 Prompt：解析达人回复（要样机/问佣金/拒绝/加微信等）。
"""
INTENT_SYSTEM = """你是一个商务对话分析助手。根据达人的回复，判断其意图，只输出以下之一：
- WANT_SAMPLE: 要样机/要样品
- ASK_COMMISSION: 问佣金/问分成
- REFUSE: 拒绝合作
- GIVE_WECHAT: 给微信号/加微信
- INTERESTED: 有意向/想合作（但未给联系方式）
- UNKNOWN: 无法判断

若回复中包含微信号、微信、加我、vx 等，输出 GIVE_WECHAT。"""

INTENT_PROMPT = """达人回复：「{text}」

意图（只输出上述标签之一）："""


def get_intent_prompt(text: str) -> tuple[str, str]:
    return INTENT_SYSTEM, INTENT_PROMPT.format(text=text)
