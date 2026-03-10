"""
自动回复轮询：每 15 分钟扫描未读消息，意图识别 → 生成回复 → 发送 → 更新 chat_log。
需各平台实现 fetch_unread_messages / send_message 接口。
"""
from __future__ import annotations

import asyncio
from typing import Callable, Awaitable, TypedDict

from src.chat.intent import parse_intent
from src.chat.reply import generate_reply
from src.chat.success import is_success, extract_contact
from src.db.models import STATUS_DEAL, STATUS_IN_TALK
from src.report.notifier import notify_deal

POLL_INTERVAL_SEC = 15 * 60  # 15 分钟


class UnreadMessage(TypedDict):
    talent_id: str
    platform: str
    text: str
    msg_id: str


async def poll_and_reply(
    fetch_unread: Callable[[], Awaitable[list[UnreadMessage]]],
    send_message: Callable[[str, str, str], Awaitable[None]],
    update_contact_and_status: Callable[[str, str, str, int], Awaitable[None]],
    get_talent_row: Callable[[str, str], Awaitable[dict | None]] | None = None,
):
    """
    轮询未读消息并自动回复。
    :param get_talent_row: (platform, talent_id) -> row dict，用于通知时补全信息；None 则用最小 row
    """
    async def _get_row(platform: str, talent_id: str) -> dict:
        if get_talent_row:
            r = await get_talent_row(platform, talent_id)
            if r:
                return r
        return {"uid": talent_id, "talent_id": talent_id, "nickname": "", "fans_num": None, "contact": ""}

    while True:
        try:
            messages = await fetch_unread()
            for msg in messages:
                platform = msg["platform"]
                talent_id = msg["talent_id"]
                text = msg.get("text", "")
                result = await parse_intent(text)
                if is_success(result):
                    contact = result.contact_value or extract_contact(text) or ""
                    await update_contact_and_status(platform, talent_id, contact, STATUS_DEAL)
                    row = await _get_row(platform, talent_id)
                    row["contact"] = contact
                    notify_deal(platform, row)
                    reply = "收到，我们马上联系您～"
                elif result.intent == "REFUSE":
                    reply = "好的，有机会再合作～"
                else:
                    reply = await generate_reply(result.intent, text)
                await send_message(platform, talent_id, reply)
                await asyncio.sleep(2)  # 间隔
        except Exception as e:
            pass  # 日志
        await asyncio.sleep(POLL_INTERVAL_SEC)
