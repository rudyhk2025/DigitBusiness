"""
上报内容格式化：主页链接、粉丝数、联系方式等，便于邮件/Webhook 使用。
"""
from __future__ import annotations

from typing import Any


def format_talent_report(platform: str, row: dict[str, Any]) -> str:
    """
    将达人记录格式化为可读文本，用于邮件正文或 Webhook 消息。
    """
    nickname = row.get("nickname", "")
    fans = row.get("fans_num")
    contact = row.get("contact") or row.get("wechat") or row.get("phone") or ""
    uid = row.get("uid") or row.get("talent_id", "")

    if platform == "DY":
        link = f"https://buyin.jinritemai.com/dashboard/author/detail?uid={uid}" if uid else ""
    else:
        link = ""

    lines = [
        f"【{platform}】达人成交",
        f"昵称：{nickname}",
        f"粉丝数：{fans or '未知'}",
        f"联系方式：{contact or '未知'}",
        f"详情链接：{link}" if link else "",
    ]
    return "\n".join(l for l in lines if l)


def format_talent_report_markdown(platform: str, row: dict[str, Any]) -> str:
    """Markdown 格式，适用于飞书/钉钉。"""
    base = format_talent_report(platform, row)
    return "```\n" + base + "\n```"
