"""
微信小店达人表 (talent_wx) 增删改查。
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from src.config.settings import PROJECT_ROOT
from src.db.models import WechatShopTalent

DB_PATH = PROJECT_ROOT / "data" / "talent.db"
SCHEMA_SQL = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def add(t: WechatShopTalent) -> int:
    """新增或更新达人，以 openId 唯一。已存在则 UPDATE。返回 id。"""
    conn = _ensure_db()
    try:
        conn.execute(
            """
            INSERT INTO talent_wx (
                openId, nickname, avatar, finderUsername, gender, introduction,
                fans_num, topCatList, hasContact, status, wechat, phone, chat_log, contact
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(openId) DO UPDATE SET
                nickname=excluded.nickname,
                avatar=excluded.avatar,
                finderUsername=excluded.finderUsername,
                gender=excluded.gender,
                introduction=COALESCE(excluded.introduction, introduction),
                fans_num=excluded.fans_num,
                topCatList=COALESCE(excluded.topCatList, topCatList),
                hasContact=excluded.hasContact,
                wechat=COALESCE(excluded.wechat, wechat),
                phone=COALESCE(excluded.phone, phone),
                chat_log=COALESCE(excluded.chat_log, chat_log),
                contact=COALESCE(excluded.contact, contact),
                updated_at=datetime('now')
            """,
            (
                t.openId,
                t.nickname,
                t.avatar,
                t.finderUsername,
                t.gender,
                t.introduction,
                t.fans_num,
                t.topCatList,
                t.hasContact,
                t.status,
                t.wechat,
                t.phone,
                t.chat_log,
                t.contact,
            ),
        )
        conn.commit()
        cur = conn.execute("SELECT id FROM talent_wx WHERE openId=?", (t.openId,))
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def get_by_openId(openId: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT * FROM talent_wx WHERE openId=?", (openId,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def update_status(openId: str, status: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "UPDATE talent_wx SET status=?, updated_at=datetime('now') WHERE openId=?",
            (status, openId),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_chat_log(openId: str, chat_log: list[dict]) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "UPDATE talent_wx SET chat_log=?, updated_at=datetime('now') WHERE openId=?",
            (json.dumps(chat_log, ensure_ascii=False), openId),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_contact(openId: str, contact: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "UPDATE talent_wx SET contact=?, updated_at=datetime('now') WHERE openId=?",
            (contact, openId),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_by_status(status: Optional[int] = None, limit: int = 500) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        if status is not None:
            cur = conn.execute(
                "SELECT * FROM talent_wx WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur = conn.execute("SELECT * FROM talent_wx ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()

