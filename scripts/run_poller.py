#!/usr/bin/env python3
"""
自动回复轮询入口。需各平台实现 fetch_unread / send_message。
当前为占位：fetch_unread 返回空列表，实际需对接抖店/京麦/蒲公英私信接口。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chat.poller import poll_and_reply
from src.db import talent_dy_repo


async def _fetch_unread_dy() -> list:
    """TODO: 对接抖店私信接口，返回未读消息。"""
    return []


async def _send_message_dy(platform: str, talent_id: str, text: str):
    """TODO: 通过 Playwright 或接口发送私信。"""
    pass


async def _update_dy(platform: str, talent_id: str, contact: str, status: int):
    if platform == "DY":
        talent_dy_repo.update_contact(talent_id, contact)
        talent_dy_repo.update_status(talent_id, status)


async def _get_row(platform: str, talent_id: str):
    if platform == "DY":
        return talent_dy_repo.get_by_uid(talent_id)
    return None


async def main():
    await poll_and_reply(
        fetch_unread=_fetch_unread_dy,
        send_message=_send_message_dy,
        update_contact_and_status=_update_dy,
        get_talent_row=_get_row,
    )


if __name__ == "__main__":
    asyncio.run(main())
