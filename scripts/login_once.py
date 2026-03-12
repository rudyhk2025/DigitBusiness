#!/usr/bin/env python3
"""
免登录前置：首次为指定平台打开浏览器并进入登录页，人工完成扫码/登录后关闭即可。
之后 BrowserManager 会复用该 user_data_dir 实现免登录启动。

用法:
  python scripts/login_once.py DY     # 抖店
  python scripts/login_once.py JD      # 京麦
  python scripts/login_once.py XHS     # 蒲公英
  python scripts/login_once.py DY JD XHS  # 多个
"""
import asyncio
import sys
from pathlib import Path

# 保证可导入 src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import USER_DATA
from src.env.stealth_launcher import launch_stealth_browser

# 各平台后台登录/首页 URL（需已登录才能看到达人后台）
LOGIN_OR_HOME_URLS = {
    "DY": "https://buyin.jinritemai.com/",      # 抖店精选联盟入口
    "JD": "https://jdd.jd.com/",                 # 京麦/京东达人
    "XHS": "https://pgy.xiaohongshu.com/",   # 蒲公英创作者平台
    "WXSHOP": "https://store.weixin.qq.com/shop?fromScene=6",  # 微信小店
}

PLATFORM_NAMES = {"DY": "抖音/抖店", "JD": "京麦", "XHS": "小红书/蒲公英", "WXSHOP": "微信小店"}


async def login_once(platform: str):
    if platform not in LOGIN_OR_HOME_URLS:
        print(f"未知平台: {platform}，可选: DY, JD, XHS, WXSHOP")
        return
    user_data = USER_DATA[platform]
    user_data.mkdir(parents=True, exist_ok=True)
    url = LOGIN_OR_HOME_URLS[platform]
    name = PLATFORM_NAMES[platform]
    print(f"[{name}] 正在启动浏览器（有头），请在此窗口内完成登录，完成后关闭浏览器即可。")
    async with launch_stealth_browser(headless=False, user_data_dir=user_data) as page:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        # 保持打开，直到用户关闭
        try:
            await page.wait_for_timeout(3600_000)  # 最多等 1 小时
        except Exception:
            pass


def main():
    platforms = [p.strip().upper() for p in sys.argv[1:] if p.strip()]
    if not platforms:
        print("用法: python scripts/login_once.py DY [JD] [XHS] [WXSHOP]")
        sys.exit(1)
    for p in platforms:
        asyncio.run(login_once(p))
        print(f"  {p} 已完成。若已登录可关闭浏览器；若需登录下一平台，将再次打开浏览器。\n")


if __name__ == "__main__":
    main()
