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

from src.config.settings import USER_DATA, USE_CDP_CHROME_PLATFORMS
from src.env.stealth_launcher import launch_stealth_browser
from src.env.chrome_cdp import connect_chrome_cdp

# 各平台后台登录/首页 URL（需已登录才能看到达人后台）
# 微信小店：与抓取脚本同开「达人广场」URL，登录态同源，避免再次打开提示未登录
LOGIN_OR_HOME_URLS = {
    "DY": "https://fxg.jinritemai.com/ffa/mshop/homepage/index ",      # 抖店精选联盟入口
    "JD": "https://passport.shop.jd.com/login/index.action/jdm?ReturnUrl=https%3A%2F%2Fshop.jd.com",                 # 京麦/京东达人
    "XHS": "https://pgy.xiaohongshu.com/",   # 蒲公英创作者平台
    "WX": "https://store.weixin.qq.com/shop/findersquare/find",  # 微信小店·达人广场
}

PLATFORM_NAMES = {"DY": "抖音/抖店", "JD": "京麦", "XHS": "小红书/蒲公英", "WX": "微信小店"}


async def login_once(platform: str):
    if platform not in LOGIN_OR_HOME_URLS:
        print(f"未知平台: {platform}，可选: DY, JD, XHS, WX")
        return
    user_data = USER_DATA[platform]
    user_data.mkdir(parents=True, exist_ok=True)
    url = LOGIN_OR_HOME_URLS[platform]
    name = PLATFORM_NAMES[platform]
    use_cdp = platform in USE_CDP_CHROME_PLATFORMS

    if use_cdp:
        print(f"[{name}] 使用本机 Chrome（CDP 连接），不会被识别为 Playwright，登录态可正常缓存。")
        print(f"  Profile 目录: {user_data.resolve()}")
        print("  完成后请直接关闭 Chrome 窗口；关闭后请勿立即关终端，等待约 3 秒。")
        launcher = connect_chrome_cdp(user_data_dir=user_data)
    else:
        print(f"[{name}] 正在启动浏览器（有头），请在此窗口内完成登录。")
        print(f"  Profile 目录: {user_data.resolve()}")
        print("  完成后请直接关闭浏览器窗口；关闭后请勿立即关终端，等待约 3 秒以保存登录状态。")
        launcher = launch_stealth_browser(headless=False, user_data_dir=user_data)

    async with launcher as page:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        closed = asyncio.get_running_loop().create_future()
        def _on_close():
            if not closed.done():
                closed.set_result(None)
        page.on("close", _on_close)
        try:
            await asyncio.wait(
                [closed, asyncio.create_task(asyncio.sleep(3600_000))],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except Exception:
            pass
        if closed.done():
            print("  浏览器已关闭，保存登录状态中…")
            await asyncio.sleep(3)


def main():
    platforms = [p.strip().upper() for p in sys.argv[1:] if p.strip()]
    if not platforms:
        print("用法: python scripts/login_once.py DY [JD] [XHS] [WX]")
        sys.exit(1)
    for p in platforms:
        asyncio.run(login_once(p))
        print(f"  {p} 已完成。若已登录可关闭浏览器；若需登录下一平台，将再次打开浏览器。\n")


if __name__ == "__main__":
    main()
