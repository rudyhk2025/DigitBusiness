"""
初次邀约 Prompt 模板：按平台分层（小红书亲切、京东专业、抖音居中）。
"""
from typing import Literal

Platform = Literal["DY", "JD", "XHS"]

SYSTEM = {
    "XHS": "你是小红书品牌方的商务，语气亲切、活泼，善于用 emoji 和口语化表达。",
    "JD": "你是京东商城的品类运营，语气专业、简洁，突出数据与权益。",
    "DY": "你是抖店品牌方的商务，语气热情但不过分，突出合作共赢。",
}

INVITE_PROMPT = """请为以下达人生成 1 条初次邀约私信，要求：
- 不超过 80 字
- 平台风格：{style}
- 达人信息：昵称「{nickname}」，类目「{category}」，粉丝约 {fans}
- 不要提及具体品牌名，只说「我们品牌」
- 不要出现「私信」「回复」等敏感词，自然结尾

直接输出邀约文案，不要其它解释。"""


def get_invite_prompt(
    platform: Platform,
    nickname: str,
    category: str = "",
    fans: int | None = None,
) -> tuple[str, str]:
    """
    返回 (system, user_prompt) 用于初次邀约生成。
    """
    style = SYSTEM.get(platform, SYSTEM["DY"])
    fans_str = f"{fans}万" if fans and fans >= 10000 else (str(fans or "未知"))
    user = INVITE_PROMPT.format(
        style=style,
        nickname=nickname,
        category=category or "未分类",
        fans=fans_str,
    )
    return style, user
