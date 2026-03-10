"""
成功判定：识别「微信号」或「明确合作意向」，触发 contact 更新与 status 变更。
"""
from __future__ import annotations

import re

from src.chat.intent import parse_intent, IntentResult
from src.db.models import STATUS_DEAL


def _has_wechat_pattern(text: str) -> bool:
    """简单规则：是否包含微信号/手机号模式。"""
    if not text:
        return False
    if re.search(r"[a-zA-Z][a-zA-Z0-9_-]{5,20}", text):
        return True
    if re.search(r"1[3-9]\d{9}", text):
        return True
    if any(k in text for k in ["微信", "vx", "VX", "wx", "加我"]):
        return True
    return False


def is_success(result: IntentResult) -> bool:
    """
    是否可判定为成交（需记录 contact 并更新 status 为成交）。
    """
    if result.intent == "GIVE_WECHAT":
        return True
    if result.intent == "INTERESTED" and result.confidence >= 0.8:
        return True
    if result.contact_value:
        return True
    return False


def extract_contact(text: str) -> str | None:
    """从原文中提取联系方式，供写入 contact 字段。"""
    m = re.search(r"[a-zA-Z][a-zA-Z0-9_-]{5,20}", text)
    if m:
        return f"微信: {m.group(0)}"
    m = re.search(r"1[3-9]\d{9}", text)
    if m:
        return f"手机: {m.group(0)}"
    return None
