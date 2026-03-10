"""
抖店 · 精选联盟：从 search_feed_author API 返回数据解析达人列表。
需已登录抖店后台，通过页面搜索或初始加载触发 API，再解析响应。
"""
from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable

from src.db.models import (
    DouyinTalent,
    TalentCandidate,
    SALE_TYPE_LIVE,
    SALE_TYPE_VIDEO,
    SALE_TYPE_IMAGE,
    SALE_TYPE_TEXT,
)
from src.db import talent_dy_repo
from src.filter import random_wait as _random_wait

DOUYIN_LEAGUE_URL = "https://buyin.jinritemai.com/dashboard"
DOUYIN_LEAGUE_DAREN_URL = "https://buyin.jinritemai.com/dashboard/servicehall/daren-square"
API_URL_AUTHOR_LIST_PATTERN = "square_pc_api/square/search_feed_author"
API_URL_AUTHOR_PROFILE_PATTERN = "square_pc_api/homePage/author/profile"
API_URL_AUTHOR_CONTACT_PATTERN = "api/contact/contact_info"
API_URL_AUTHOR_DOUYIN_PATTERN = "aweme/v1/web/aweme/post"

async def _fetch_contact_value(page, click_locator, timeout_ms: int = 10000) -> str | None:
    """
    点击后监听 contact API，只处理 contact_value 有值的 response。
    该 API 可能调用两次，需过滤掉空值。
    """
    found: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()

    async def on_response(response):
        if found.done():
            return
        if API_URL_AUTHOR_CONTACT_PATTERN not in response.url or response.status != 200:
            return
        try:
            data = await response.json()
            val = data.get("data", {}).get("contact_info", {}).get("contact_value")
            if val and isinstance(val, str) and val.strip():
                found.set_result(val.strip())
        except Exception:
            pass

    page.on("response", on_response)
    try:
        await asyncio.sleep(random.uniform(0.2, 0.6))
        await click_locator.click()
        return await asyncio.wait_for(asyncio.shield(found), timeout=timeout_ms / 1000)
    except asyncio.TimeoutError:
        return None
    finally:
        page.remove_listener("response", on_response)

MAIN_SALE_TYPE_MAP = {
    "直播为主": SALE_TYPE_LIVE,
    "视频为主": SALE_TYPE_VIDEO,
    "图文为主": SALE_TYPE_IMAGE,
}


def _parse_author(item: dict) -> DouyinTalent | None:
    """
    将 API 单条数据解析为 DouyinTalent，对应 talent_dy 表。
    格式参考 author.json。
    """
    base = item.get("author_base") or {}
    tag = item.get("author_tag") or {}
    sale = item.get("author_sale") or {}
    sale_info = item.get("sale_info") or {}
    contact = item.get("author_contact") or {}
    window = item.get("author_window") or {}

    uid = base.get("uid") or ""
    if not uid:
        return None

    tags = [r.get("reason") for r in (tag.get("author_rec_reasons") or []) if r.get("reason")]
    labels = [r.get("reason") for r in (tag.get("author_label_rec_reasons") or []) if r.get("reason")]
    main_cate = tag.get("main_cate") or []
    main_cate_str = "|".join(main_cate) if main_cate else None
    author_label_str = "|".join(labels) if labels else None

    main_sale_raw = sale.get("main_sale_type") or ""
    main_sale_type = MAIN_SALE_TYPE_MAP.get(main_sale_raw) or (SALE_TYPE_TEXT if main_sale_raw else None)

    total = sale_info.get("total_sales") or {}
    total_settle = sale_info.get("total_sales_settle") or {}
    window_sales = sale_info.get("window_total_sales") or {}

    return DouyinTalent(
        uid=uid,
        did=base.get("aweme_id") or None,
        nickname=(base.get("nickname") or "").strip() or "未知",
        fans_num=base.get("fans_num"),
        main_cate=main_cate_str,
        avatar=base.get("avatar"),
        avatar_big=base.get("avatar_big"),
        gender=base.get("gender"),
        city=base.get("city"),
        author_level=base.get("author_level"),
        high_reply=1 if "回复率高" in tags else 0,
        no_ad=1 if "非投放流量占比高" in tags else 0,
        author_label=author_label_str,
        status=0,
        main_sale_type=main_sale_type,
        total_sales_low=total.get("sale_low"),
        total_sales_high=total.get("sale_high"),
        total_sales_settle_low=total_settle.get("sale_low"),
        total_sales_settle_high=total_settle.get("sale_high"),
        window_product_num=window.get("product_num"),
        window_order_low=window.get("order_low"),
        window_order_high=window.get("order_high"),
        introduction=None,
        wechat=contact.get("wechat") or None,
        phone=contact.get("phone") or None,
    )


async def _process_page_items(
    list_page,
    items: list[dict],
    *,
    min_score: float | None,
    min_fans: int | None,
    category: str | None,
    on_candidate: Callable[[DouyinTalent], Awaitable[None]] | None,
    result: list[DouyinTalent],
) -> None:
    """处理当前页的达人列表：打开详情页、补全信息、筛选并回调/累积。"""
    for item in items:
        c = _parse_author(item)
        if not c:
            continue
        # 已采集过则跳过，避免重复打开详情页
        try:
            if talent_dy_repo.get_by_uid(c.uid):
                print(f"已采集，跳过达人: {c.nickname} ({c.uid})")
                continue
        except Exception:
            # DB 异常时不中断采集，只是不做去重
            pass
        nickname = c.nickname
        # 该达人如果不在列表页面中，则跳过
        if not await list_page.locator("table").get_by_text(nickname, exact=False).first.is_visible():
            print(f"达人不在列表页面中，跳过: {nickname}")
            continue

        await _random_wait(1.5, 3.5)
        print(f"开始解析达人: {nickname}")
        try:
            # 点击打开新 tab，在 popup 上监听 profile 接口（BrowserContext 无 expect_response）
            try:
                async with list_page.expect_popup(timeout=5000) as popup_info:
                    row = list_page.locator("table").get_by_text(nickname, exact=False).first
                    await _random_wait(0.3, 0.8)
                    await row.click(timeout=15000)
                profile_page = await popup_info.value
                async with profile_page.expect_response(
                    lambda r: API_URL_AUTHOR_PROFILE_PATTERN in r.url and r.status == 200
                ) as resp_info:
                    await profile_page.wait_for_load_state("domcontentloaded", timeout=15000)
                response = await resp_info.value
            except Exception:
                await list_page.wait_for_load_state("networkidle", timeout=10000)
                profile_page = list_page
                response = None
            if response is None:
                raise ValueError("未获取到 profile 响应")
            data = await response.json()
            introduction = data.get("data", {}).get("introduction", "")
            c.introduction = introduction or None
            print(f"    简介：{introduction[:50] if introduction else ''}...")
            await _random_wait(2, 4)
            print("    >>检查联系方式 ")
            try:
                await profile_page.locator(".auxo-spin-spinning").first.wait_for(state="hidden", timeout=5000)
            except Exception:
                pass

            if await profile_page.locator("text=达人手机号").first.is_visible():
                await _random_wait(1.5, 3)
                val = await _fetch_contact_value(
                    profile_page,
                    profile_page.locator("text=达人手机号").locator("..").locator("img"),
                )
                if val:
                    c.phone = val
                    print(f"    手机号：{c.phone}")
                await _random_wait(1.5, 3)
            if await profile_page.locator("text=达人微信号").first.is_visible():
                await _random_wait(1.5, 3)
                val = await _fetch_contact_value(
                    profile_page,
                    profile_page.locator("text=达人微信号").locator("..").locator("img"),
                )
                if val:
                    c.wechat = val
                    print(f"    微信号：{c.wechat}")
                await _random_wait(1.5, 3)

            print("    >>获取达人抖音号")
            await _random_wait(1.5, 3)
            try:
                link = profile_page.get_by_text("达人抖音主页", exact=False).first
                await link.wait_for(state="visible", timeout=10000)
                await link.scroll_into_view_if_needed()
                await _random_wait(1.3, 3.8)
                async with profile_page.expect_popup(timeout=20000) as popup_info:
                    await link.click(timeout=30000)
                douyin_page = await popup_info.value
                async with douyin_page.expect_response(
                    lambda r: API_URL_AUTHOR_DOUYIN_PATTERN in r.url and r.status == 200
                ) as resp_info:
                    await douyin_page.wait_for_load_state("domcontentloaded", timeout=15000)
                response = await resp_info.value
                data = await response.json()
                aweme_list = data.get("aweme_list") or []
                for aweme in aweme_list:
                    handle = aweme.get("owner_handle")
                    if handle and isinstance(handle, str) and handle.strip():
                        c.did = handle.strip()
                        break
                print(f"    抖音号：{c.did}")
                await _random_wait(1.5, 3)
                await douyin_page.close()
            except Exception as e:
                print(f"    跳过达人抖音主页：{e}")

            if profile_page != list_page:
                await _random_wait(1.5, 3)
                # print("    关闭达人详情页")
                await profile_page.close()
            await _random_wait(1, 2)  # 下一位达人前间隔

        except Exception as e:
            print(f"跳过 {nickname}：{e}")
            continue

        if min_fans is not None and (c.fans_num is None or c.fans_num < min_fans):
            continue
        score_val = c.total_sales_low or c.total_sales_high
        if min_score is not None and (score_val is None or score_val < min_score):
            continue
        if category and (not c.main_cate or category not in c.main_cate):
            continue
        if on_candidate is not None:
            await on_candidate(c)
        result.append(c)


async def fetch_one_page(
    page,
    *,
    min_score: float | None = None,
    min_fans: int | None = None,
    category: str | None = None,
    search_text: str | None = None,
    on_candidate: Callable[[DouyinTalent], Awaitable[None]] | None = None,
) -> list[TalentCandidate]:
    """
    进入达人广场，通过 API 获取达人列表并解析。
    使用全局 response 监听 `API_URL_AUTHOR_LIST_PATTERN`，避免在局部点击/滚动时漏掉接口。
    """
    loop = asyncio.get_running_loop()
    author_queue: asyncio.Queue[dict] = asyncio.Queue()

    async def _handle_author_list_response(response):
        if API_URL_AUTHOR_LIST_PATTERN not in response.url or response.status != 200:
            return
        try:
            data = await response.json()
            # 测试 打印列表数据
            list = data.get('data', {}).get('list', [])
            print(f"==========获取到列表数据: {len(list)}==========")
            for item in list:
                print(f"\t达人: {item.get('author_base', {}).get('nickname', '')}")
            await author_queue.put(data)
        except Exception:
            pass

    def _on_response(response):
        asyncio.create_task(_handle_author_list_response(response))

    print(f"==========开始获取列表数据==========")
    try:
        if search_text:
            await page.goto(DOUYIN_LEAGUE_DAREN_URL, wait_until="domcontentloaded", timeout=60000)
            await _random_wait(2, 4)
            await page.wait_for_selector('input[type="search"]', timeout=15000)
            await _random_wait(2.5, 6.5)
            await page.fill('input[type="search"]', search_text)
            await _random_wait(1, 5)
            print(f"开始搜索: {search_text}")
            await page.click('button:has-text("搜索")')
        else:
            await page.goto(DOUYIN_LEAGUE_DAREN_URL, wait_until="networkidle", timeout=60000)

        print(f"==========开始监听列表数据==========")
        page.on("response", _on_response)

        # 从全局监听队列中获取首个列表数据
        data = await author_queue.get()
    finally:
        # fetch_one_page 结束前移除监听，避免影响其他流程
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass

    # 解析第一页，并根据 has_more 逐页处理 + 翻页（通过滚动或点击触发相同接口）
    if data.get("code") != 0:
        return []

    list_page = page
    result: list[DouyinTalent] = []
    page_index = 1
    while True:
        page_data = data.get("data") or {}
        raw_list = page_data.get("list") or []
        has_more = bool(page_data.get("has_more"))
        print(f"第 {page_index} 页达人数: {len(raw_list)}")
        # 先处理当前页达人，再考虑翻页
        await _process_page_items(
            list_page,
            raw_list,
            min_score=min_score,
            min_fans=min_fans,
            category=category,
            on_candidate=on_candidate,
            result=result,
        )
        if not has_more:
            break

        # 滚动列表触发下一页接口；若在处理过程中点击已提前触发下一页 API，这里会直接从队列中读取
        try:
            await page.mouse.wheel(0, 2000)
            await _random_wait(0.5, 4.5)
            data = await author_queue.get()
            page_index += 1
            await _random_wait(1, 2)
        except Exception as e:
            print(f"翻页失败，停止继续抓取: {e}")
            break

    await _random_wait(2, 4)
    try:
        await page.locator(".auxo-spin-spinning").first.wait_for(state="hidden", timeout=10000)
    except Exception:
        pass
    await _random_wait(2, 4)
    print(f"共汇总达人: {len(result)}")
    return result
