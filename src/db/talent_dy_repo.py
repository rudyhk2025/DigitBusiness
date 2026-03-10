"""
抖音达人表 (talent_dy) 增删改查。
"""
import json
import sqlite3
from pathlib import Path
from typing import Optional

from src.config.settings import PROJECT_ROOT
from src.db.models import DouyinTalent, STATUS_NOT_INVITED

DB_PATH = PROJECT_ROOT / "data" / "talent.db"
SCHEMA_SQL = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def add(t: DouyinTalent) -> int:
    """新增或更新达人，以 uid 唯一。已存在则 UPDATE。返回 id。"""
    conn = _ensure_db()
    try:
        cur = conn.execute(
            """
            INSERT INTO talent_dy (
                uid, did, nickname, fans_num, main_cate, avatar, avatar_big, gender, city,
                author_level, high_reply, no_ad, author_label, status, main_sale_type,
                total_sales_low, total_sales_high, total_sales_settle_low, total_sales_settle_high,
                window_product_num, window_order_low, window_order_high, introduction, wechat, phone
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(uid) DO UPDATE SET
                did=excluded.did, nickname=excluded.nickname, fans_num=excluded.fans_num,
                main_cate=excluded.main_cate, avatar=excluded.avatar, avatar_big=excluded.avatar_big,
                gender=excluded.gender, city=excluded.city, author_level=excluded.author_level,
                high_reply=excluded.high_reply, no_ad=excluded.no_ad, author_label=excluded.author_label,
                main_sale_type=excluded.main_sale_type,
                total_sales_low=excluded.total_sales_low, total_sales_high=excluded.total_sales_high,
                total_sales_settle_low=excluded.total_sales_settle_low, total_sales_settle_high=excluded.total_sales_settle_high,
                window_product_num=excluded.window_product_num,
                window_order_low=excluded.window_order_low, window_order_high=excluded.window_order_high,
                introduction=COALESCE(excluded.introduction, introduction),
                wechat=COALESCE(excluded.wechat, wechat),
                phone=COALESCE(excluded.phone, phone),
                updated_at=datetime('now')
            """,
            (
                t.uid, t.did, t.nickname, t.fans_num, t.main_cate, t.avatar, t.avatar_big,
                t.gender, t.city, t.author_level, t.high_reply, t.no_ad, t.author_label,
                t.status, t.main_sale_type,
                t.total_sales_low, t.total_sales_high, t.total_sales_settle_low, t.total_sales_settle_high,
                t.window_product_num, t.window_order_low, t.window_order_high, t.introduction, t.wechat, t.phone,
            ),
        )
        conn.commit()
        cur = conn.execute("SELECT id FROM talent_dy WHERE uid=?", (t.uid,))
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def get_by_uid(uid: str) -> Optional[dict]:
    """按 uid 查一条。"""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("SELECT * FROM talent_dy WHERE uid=?", (uid,))
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
        cur = conn.execute("UPDATE talent_dy SET status=?, updated_at=datetime('now') WHERE uid=?", (status, uid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_chat_log(uid: str, chat_log: list[dict]) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "UPDATE talent_dy SET chat_log=?, updated_at=datetime('now') WHERE uid=?",
            (json.dumps(chat_log, ensure_ascii=False), uid),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_contact(uid: str, contact: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("UPDATE talent_dy SET contact=?, updated_at=datetime('now') WHERE uid=?", (contact, uid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_by_status(status: Optional[int] = None, limit: int = 500) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    try:
        if status is not None:
            cur = conn.execute(
                "SELECT * FROM talent_dy WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur = conn.execute("SELECT * FROM talent_dy ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()
