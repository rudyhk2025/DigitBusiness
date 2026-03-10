#!/usr/bin/env python3
"""
测试邮件/Webhook 通知。可传入 uid 模拟达人成交推送。
需配置 SMTP_* 或 FEISHU_WEBHOOK / DINGTALK_WEBHOOK。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.report.notifier import notify_deal
from src.db import talent_dy_repo


def main():
    uid = sys.argv[1] if len(sys.argv) > 1 else None
    if uid:
        row = talent_dy_repo.get_by_uid(uid)
        if row:
            notify_deal("DY", row)
            print("已发送通知")
        else:
            print(f"未找到 uid={uid}")
    else:
        row = {"uid": "test", "nickname": "测试达人", "fans_num": 10000, "contact": "微信: test123"}
        notify_deal("DY", row)
        print("已发送测试通知")


if __name__ == "__main__":
    main()
