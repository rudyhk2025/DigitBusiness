"""
初次邀约：生成 3-5 种风格钩子文案，AI 随机选一条。文案随机化防平台判定为垃圾信息。
"""
from __future__ import annotations

import random
from typing import Literal

from src.chat.llm_client import chat
from src.chat.prompts.invite import get_invite_prompt

Platform = Literal["DY", "JD", "XHS"]


async def generate_invite(
    platform: Platform,
    nickname: str,
    *,
    category: str = "",
    fans: int | None = None,
    num_variants: int = 3,
    seed: int | None = None,
) -> str:
    """
    生成 num_variants 种邀约文案，随机选一条返回。
    若 seed 不为 None，用于可复现测试。
    """
    if seed is not None:
        random.seed(seed)
    system, user = get_invite_prompt(platform, nickname, category, fans)
    # 调用 LLM 生成，可要求一次生成多句（用分号分隔），再随机选一
    prompt = user.replace("1 条", f"{num_variants} 条，用「|||」分隔，风格各异")
    text = await chat(prompt, system=system, temperature=0.9)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    return random.choice(parts) if parts else text.strip()
