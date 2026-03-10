"""
深度谈判回复：根据意图生成回复，支持佣金加码、独家机制等策略。
"""
from __future__ import annotations

from src.chat.llm_client import chat
from src.chat.prompts.reply import get_reply_prompt

# 最高权限配置（可后续从 settings 读取）
MAX_COMMISSION = 20  # 最高佣金 %
CAN_OFFER_EXCLUSIVE = True


async def generate_reply(intent: str, original_text: str) -> str:
    """
    根据意图和原文生成回复。
    """
    system, user = get_reply_prompt(intent, original_text)
    # 注入最高权限到 system
    extra = f"（最高佣金可给到 {MAX_COMMISSION}%，可承诺独家合作）"
    full_system = system + "\n" + extra
    return await chat(user, system=full_system, temperature=0.7)
