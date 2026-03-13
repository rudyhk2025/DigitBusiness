#!/usr/bin/env python3
"""
第一阶段验收：一键选择平台 → 启动浏览器 → 抓取一页达人 → 写入/更新 SQLite。

用法:
  python scripts/run_filter_one_page.py DY
  python scripts/run_filter_one_page.py JD
  python scripts/run_filter_one_page.py XHS
  python scripts/run_filter_one_page.py WX

需已对本平台执行过 scripts/login_once.py 完成首次登录（或 use_persistent=False 临时不读缓存）。
"""
import asyncio
import sys
from pathlib import Path



sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.env.browser_manager import BrowserManager
from src.db import talent_dy_repo, talent_xhs_repo, talent_wx_repo

PLATFORM_MODULES = {
    "DY": ("src.filter.douyin", "fetch_one_page"),
    "JD": ("src.filter.jd", "fetch_one_page"),
    "XHS": ("src.filter.xiaohongshu", "fetch_one_page"),
    "WX": ("src.filter.wxshop", "fetch_one_page"),
}


async def main(platform: str, use_persistent: bool = True):
    if platform not in PLATFORM_MODULES:
        print("平台可选: DY, JD, XHS, WX")
        return
    mod_name, fn_name = PLATFORM_MODULES[platform]
    import importlib
    mod = importlib.import_module(mod_name)
    fetch_one_page = getattr(mod, fn_name)

    manager = BrowserManager(platform, headless=False, use_persistent=use_persistent)
    async with manager.start() as page:
        print(f"[{platform}] 正在打开页面并抓取一页达人…")
        if platform == "DY":
            async def _on_candidate(c):
                talent_dy_repo.add(c)
                print(f"  add db: {c.nickname} ({c.uid}), phone: {c.phone}, wechat: {c.wechat}")

            candidates = await fetch_one_page(page, search_text="保健品", on_candidate=_on_candidate)
            print(f"  本次共解析到 {len(candidates)} 条，已写入 talent_dy")
        elif platform == "XHS":
            async def _on_candidate(c):
                talent_xhs_repo.add(c)
                print(f"  add db: {c.nickname} ({c.uid}), phone: {c.phone}, wechat: {c.wechat}")

            candidates = await fetch_one_page(page, kol_type="live", note_contentTag="健康养生", live_first_category="保健食品/膳食营养补充食品", live_second_category="普通膳食营养食品", limit=20, on_candidate=_on_candidate)
            print(f"  本次共解析到 {len(candidates)} 条，已写入 talent_xhs")
        elif platform == "WX":
            from src.filter.wxshop import WxshopFilters

            filters = WxshopFilters(
                deliver_categories=["食品饮料", "美妆护肤"], #带货类目
                deliver_metrics=[{"带货销售总额": ["￥1万以下", "￥1万-5万"]}], #带货数据
                talent_profile=[{"粉丝量": ["小于1万", "1万-10万"]}], #达人画像
                # fans_profile=[{"粉丝年龄": ["25-39岁"]}], #粉丝画像
                # others=["有联系方式"],  #其他筛选
            )

            async def _on_candidate(t):
                talent_wx_repo.add(t)
                print(f"  add db: {t.nickname} ({t.openId}), hasContact: {t.hasContact}")

            candidates = await fetch_one_page(page, filters=filters, limit=20, on_candidate=_on_candidate)
            print(f"  本次共解析到 {len(candidates)} 条，已写入 talent_wx")
        else:
            candidates = await fetch_one_page(page)
            print(f"  本页解析到 {len(candidates)} 条（JD 待接入分表）")

        # 保持窗口一段时间，方便你打开 DevTools 查看实际 DOM 和选择器；
        # 想立即结束可直接关闭浏览器窗口。
        try:
            print("浏览器将在前台保持 5 分钟，方便你调试选择器…")
            await page.wait_for_timeout(5 * 60 * 1000)
        except Exception:
            # 若用户手动关闭窗口会触发异常，这里忽略即可
            pass


if __name__ == "__main__":
    platform = (sys.argv[1] or "").strip().upper()
    if not platform:
        print("用法: python scripts/run_filter_one_page.py DY|JD|XHS|WX")
        sys.exit(1)
    asyncio.run(main(platform))
