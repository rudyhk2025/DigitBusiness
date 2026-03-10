#!/usr/bin/env python3
"""
生成初次邀约文案（可接入筛选后的发送流程）。
需配置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY、OPENAI_BASE_URL（国产模型时）。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chat.invite import generate_invite


async def main():
    platform = (sys.argv[1] or "DY").strip().upper()
    nickname = sys.argv[2] if len(sys.argv) > 2 else "测试达人"
    category = sys.argv[3] if len(sys.argv) > 3 else "美食"
    fans = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 50000
    text = await generate_invite(platform, nickname, category=category, fans=fans)
    print(text)


if __name__ == "__main__":
    asyncio.run(main())
