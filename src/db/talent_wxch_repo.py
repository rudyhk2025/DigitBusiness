"""
微信小店达人表 (talent_wxshop) 增删改查。
"""
import json
import sqlite3
from pathlib import Path
from typing import Optional

from src.config.settings import PROJECT_ROOT
from src.db.models import WechatChannelsTalent

DB_PATH = PROJECT_ROOT / "data" / "talent.db"
SCHEMA_SQL = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def add(t: WechatChannelsTalent) -> int:
    """新增或更新达人，以 uid 唯一。已存在则 UPDATE。返回 id。"""
    conn = _ensure_db()
    try:
        conn.execute(
            """
            INSERT INTO talent_wxshop (
                uid, nickname, fans_num, category, avatar, introduction, status,
                wechat, phone, chat_log, contact
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(uid) DO UPDATE SET
                nickname=excluded.nickname,
                fans_num=excluded.fans_num,
                category=excluded.category,
                avatar=excluded.avatar,
                introduction=COALESCE(excluded.introduction, introduction),
                wechat=COALESCE(excluded.wechat, wechat),
                phone=COALESCE(excluded.phone, phone),
                chat_log=COALESCE(excluded.chat_log, chat_log),
                contact=COALESCE(excluded.contact, contact),
                updated_at=datetime('now')
            """,
            (
                t.uid,
                t.nickname,
                t.fans_num,
                t.category,
                t.avatar,
                t.introduction,
                t.status,
                t.wechat,
                t.phone,
                t.chat_log,
                t.contact,
            ),
        )
        conn.commit()
        cur = conn.execute("SELECT id FROM talent_wxshop WHERE uid=?", (t.uid,))
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def get_by_uid(uid: str) -> Optional[dict]:
    """按 uid 查一条。"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT * FROM talent_wxshop WHERE uid=?", (uid,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def update_status(uid: str, status: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("UPDATE talent_wxshop SET status=?, updated_at=datetime('now') WHERE uid=?", (status, uid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_chat_log(uid: str, chat_log: list[dict]) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "UPDATE talent_wxshop SET chat_log=?, updated_at=datetime('now') WHERE uid=?",
            (json.dumps(chat_log, ensure_ascii=False), uid),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_contact(uid: str, contact: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("UPDATE talent_wxshop SET contact=?, updated_at=datetime('now') WHERE uid=?", (contact, uid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_by_status(status: Optional[int] = None, limit: int = 500) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        if status is not None:
            cur = conn.execute(
                "SELECT * FROM talent_wxshop WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur = conn.execute("SELECT * FROM talent_wxshop ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()

