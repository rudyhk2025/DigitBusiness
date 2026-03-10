"""
意图识别：解析达人回复（要样机/问佣金/拒绝/加微信等）。
支持关键词规则 + AI 兜底。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from src.chat.llm_client import chat
from src.chat.prompts.intent import get_intent_prompt

Intent = Literal[
    "WANT_SAMPLE", "ASK_COMMISSION", "REFUSE", "GIVE_WECHAT", "INTERESTED", "UNKNOWN"
]

# 关键词规则（优先）
KEYWORDS = {
    "GIVE_WECHAT": ["微信", "微信号", "vx", "VX", "wx", "加我", "加微信", "私信我"],
    "WANT_SAMPLE": ["样机", "样品", "寄样", "试用"],
    "ASK_COMMISSION": ["佣金", "分成", "比例", "多少", "几个点"],
    "REFUSE": ["不做", "不合作", "算了", "没兴趣", "不用了"],
}


@dataclass
class IntentResult:
    intent: Intent
    confidence: float
    raw: str
    contact_value: str | None = None  # 若 GIVE_WECHAT，提取的微信号/手机号


def _extract_contact(text: str) -> str | None:
    """粗略提取微信号/手机号。"""
    # 微信号常见格式
    m = re.search(r"[a-zA-Z][a-zA-Z0-9_-]{5,20}", text)
    if m:
        return m.group(0)
    m = re.search(r"1[3-9]\d{9}", text)
    if m:
        return m.group(0)
    return None


def _classify_by_keywords(text: str) -> Intent | None:
    for intent, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return intent
    return None


async def parse_intent(text: str, use_llm: bool = True) -> IntentResult:
    """
    解析达人回复意图。优先关键词，无匹配时调用 LLM。
    """
    t = (text or "").strip()
    if not t:
        return IntentResult("UNKNOWN", 0, t)

    kw_intent = _classify_by_keywords(t)
    if kw_intent:
        contact = _extract_contact(t) if kw_intent == "GIVE_WECHAT" else None
        return IntentResult(kw_intent, 0.9, t, contact)

    if use_llm:
        try:
            system, user = get_intent_prompt(t)
            out = await chat(user, system=system, temperature=0)
            intent = out.strip().upper().replace(" ", "_")
            if intent not in ("WANT_SAMPLE", "ASK_COMMISSION", "REFUSE", "GIVE_WECHAT", "INTERESTED"):
                intent = "UNKNOWN"
            contact = _extract_contact(t) if intent == "GIVE_WECHAT" else None
            return IntentResult(intent, 0.7, t, contact)
        except Exception:
            pass
    return IntentResult("UNKNOWN", 0, t)
