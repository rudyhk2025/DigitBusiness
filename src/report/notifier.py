"""
通知中心：status 变更为成交时，通过邮件或 Webhook 推送。
"""
from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from src.report.formatter import format_talent_report

# 从环境变量读取
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
DINGTALK_WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")


def send_email(subject: str, body: str) -> bool:
    """通过 SMTP 发送邮件。"""
    if not SMTP_USER or not SMTP_PASS or not NOTIFY_EMAIL:
        return False
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception:
        return False


def send_feishu(text: str) -> bool:
    """飞书 Webhook。"""
    if not FEISHU_WEBHOOK:
        return False
    try:
        r = requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": text}}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def send_dingtalk(text: str) -> bool:
    """钉钉 Webhook。"""
    if not DINGTALK_WEBHOOK:
        return False
    try:
        r = requests.post(DINGTALK_WEBHOOK, json={"msgtype": "text", "text": {"content": text}}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def notify_deal(platform: str, row: dict) -> bool:
    """
    status 变更为成交时调用。按配置选择邮件或 Webhook。
    """
    body = format_talent_report(platform, row)
    subject = f"[数字员工] {platform} 达人成交：{row.get('nickname', '')}"
    ok = False
    if SMTP_USER and NOTIFY_EMAIL:
        ok = send_email(subject, body) or ok
    if FEISHU_WEBHOOK:
        ok = send_feishu(subject + "\n" + body) or ok
    if DINGTALK_WEBHOOK:
        ok = send_dingtalk(subject + "\n" + body) or ok
    return ok
