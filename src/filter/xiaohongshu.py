"""
蒲公英 · 博主广场：从 v2 / buyers API 返回数据解析博主列表并入库。
需已登录蒲公英创作者平台；支持笔记博主(v2)与直播达人(buyers)两种列表接口。
"""
from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

from src.db.models import XiaohongshuTalent, TalentCandidate
from src.db import talent_xhs_repo
from src.filter import random_wait as _random_wait

# 博主广场（笔记 KOL）
XHS_NOTE_KOL_URL = "https://pgy.xiaohongshu.com/solar/pre-trade/note/kol"
# 直播达人广场（若后续需要可单独入口）
XHS_LIVE_BUYERS_URL = "https://pgy.xiaohongshu.com/solar/pre-trade/live/kol"

API_URL_V2_PATTERN = "api/solar/cooperator/blogger/v2"
API_URL_BUYERS_PATTERN = "api/draco/distributor-square/live/buyers"
API_URL_KOL_CONTACT_PATTERN = "api/draco/selection-center/contact/info/query"

PAGINATION_PAGE_ITEM_CLASS = "d-pagination-page-content"


async def _wait_list_api(
    page,
    *,
    pattern: str,
    timeout_ms: int = 20000,
    trigger: Callable[[], Awaitable[None]] | None = None,
) -> dict:
    """
    等待列表接口响应（避免“先请求后监听”导致错过）。

    - 若提供 trigger：会先挂上 expect_response，再执行 trigger，从而稳定捕获该次请求响应。
    - 若不提供 trigger：退化为 wait_for_response（仅适用于你确定请求尚未发生的场景）。
    """
    pred = lambda r: pattern in r.url and r.status == 200
    if trigger is None:
        resp = await page.wait_for_response(pred, timeout=timeout_ms)
        return await resp.json()

    async with page.expect_response(pred, timeout=timeout_ms) as resp_info:
        await trigger()
    resp = await resp_info.value
    return await resp.json()


async def _click_pagination_page(page, page_no: int) -> bool:
    """点击分页页码（class 含 d-pagination-page-content），返回是否点击成功。"""
    loc = page.locator(f".{PAGINATION_PAGE_ITEM_CLASS}").filter(has_text=str(page_no)).first
    try:
        await loc.wait_for(state="visible", timeout=3000)
        await loc.click(timeout=5000)
        return True
    except Exception:
        return False


def _parse_v2_kol(item: dict) -> XiaohongshuTalent | None:
    """v2 接口单条：data.kols[]，字段 userId/redId/name/fansNum/personalTags/contentTags/tradeType/headPhoto/gender/location"""
    uid = (item.get("userId") or "").strip()
    if not uid:
        return None
    name = (item.get("name") or "").strip() or "未知"
    fans_num = item.get("fansNum") if item.get("fansNum") is not None else item.get("fansCount")
    personal_tags = item.get("personalTags")
    if personal_tags is not None:
        personal_tags = json.dumps(personal_tags, ensure_ascii=False) if isinstance(personal_tags, list) else str(personal_tags)
    content_tags = item.get("contentTags")
    if content_tags is not None:
        content_tags = json.dumps(content_tags, ensure_ascii=False) if isinstance(content_tags, list) else str(content_tags)
    trade_type = item.get("tradeType") or None
    main_sale_type = trade_type
    return XiaohongshuTalent(
        uid=uid,
        red_id=(item.get("redId") or "").strip() or None,
        nickname=name,
        fans_num=fans_num,
        personal_tags=personal_tags,
        content_tags=content_tags,
        trade_type=trade_type,
        avatar=item.get("headPhoto") or None,
        gender=item.get("gender") or None,
        status=0,
        location=item.get("location") or None,
        main_sale_type=main_sale_type,
        introduction=None,
        wechat=None,
        phone=None,
        chat_log=None,
        contact=None,
    )


def _parse_buyers_distributor(entry: dict) -> XiaohongshuTalent | None:
    """buyers 接口单条：data.distributor_info_list[].distributor_data_info"""
    d = entry.get("distributor_data_info") or entry
    uid = (d.get("distributor_id") or "").strip()
    if not uid:
        return None
    name = (d.get("distributor_name") or "").strip() or "未知"
    content_categorys = d.get("content_categorys") or d.get("content_category")
    content_tags = None
    if content_categorys is not None:
        content_tags = json.dumps(content_categorys, ensure_ascii=False) if isinstance(content_categorys, list) else str(content_categorys)
    dist_cat = d.get("distribution_category") or []
    main_sale_type = None
    if dist_cat and isinstance(dist_cat, list):
        first = dist_cat[0]
        if isinstance(first, dict):
            main_sale_type = first.get("first_category")
        elif isinstance(first, str):
            main_sale_type = first
    buyer_tag = d.get("buyer_tag") or []
    personal_tags = json.dumps(buyer_tag, ensure_ascii=False) if buyer_tag else None
    return XiaohongshuTalent(
        uid=uid,
        red_id=(d.get("red_id") or "").strip() or None,
        nickname=name,
        fans_num=d.get("fans_num"),
        personal_tags=personal_tags,
        content_tags=content_tags,
        trade_type=main_sale_type,
        avatar=d.get("avatar") or None,
        gender=d.get("sex") or None,
        status=0,
        location=d.get("city") or None,
        main_sale_type=main_sale_type,
        introduction=None,
        wechat=None,
        phone=None,
        chat_log=None,
        contact=None,
    )


def _parse_list_response(data: dict) -> list[XiaohongshuTalent]:
    """根据 data 结构判断是 v2 还是 buyers，解析为 XiaohongshuTalent 列表。"""
    result: list[XiaohongshuTalent] = []
    if data.get("code") != 0:
        return result
    inner = data.get("data") or {}
    kols = inner.get("kols")
    if kols is not None:
        for item in kols:
            c = _parse_v2_kol(item)
            if c:
                result.append(c)
        return result
    distributor_info_list = inner.get("distributor_info_list")
    if distributor_info_list is not None:
        for entry in distributor_info_list:
            c = _parse_buyers_distributor(entry)
            if c:
                result.append(c)
        return result
    return result


def _parse_v2_response(data: dict) -> list[XiaohongshuTalent]:
    """仅解析 v2 接口返回的 data.kols。"""
    if data.get("code") != 0:
        return []
    kols = (data.get("data") or {}).get("kols") or []
    result: list[XiaohongshuTalent] = []
    for item in kols:
        c = _parse_v2_kol(item)
        if c:
            result.append(c)
    return result


def _parse_buyers_response(data: dict) -> list[XiaohongshuTalent]:
    """仅解析 buyers 接口返回的 data.distributor_info_list。"""
    if data.get("code") != 0:
        return []
    distributor_info_list = (data.get("data") or {}).get("distributor_info_list") or []
    result: list[XiaohongshuTalent] = []
    for entry in distributor_info_list:
        c = _parse_buyers_distributor(entry)
        if c:
            result.append(c)
    return result


async def fetch_one_page(
    page,
    *,
    kol_type: str = "note",
    note_contentTag: str | None = None,
    live_first_category: str | None = None,
    live_second_category: str | None = None,
    search_text: str | None = None,
    limit: int = 20,
    on_candidate: Callable[[XiaohongshuTalent], Awaitable[None]] | None = None,
) -> list[TalentCandidate]:
    """
    1) 不使用全局监听；监听动作放在点击页面元素之后（若无筛选参数，则在打开页面后等待）。
    2) 列表分页：点击 class 含 d-pagination-page-content 的元素跳页，然后等待 API，抓取该页数据。
    """
    try:
        pattern = API_URL_BUYERS_PATTERN if kol_type == "live" else API_URL_V2_PATTERN
        parse_fn = _parse_buyers_response if kol_type == "live" else _parse_v2_response

        first_data = None
        if kol_type == "live":
            if live_first_category:
                try:
                    await page.goto(XHS_LIVE_BUYERS_URL, wait_until="domcontentloaded", timeout=60000)
                    await _random_wait(3, 5)
                    loc = page.get_by_text(live_first_category, exact=False).first
                    await loc.hover(timeout=8000)
                    await _random_wait(1, 3)
                except Exception:
                    pass
                if live_second_category:
                    try:
                        first_data = await _wait_list_api(
                            page,
                            pattern=pattern,
                            timeout_ms=30000,
                            trigger=lambda: page.get_by_text(live_second_category, exact=False).first.click(timeout=6000),
                        )
                        await _random_wait(1, 3)
                    except Exception:
                        pass

                # filter
                await page.get_by_text("可查看联系方式").first.click(timeout=8000)
                await _random_wait(2, 5)
            else:
                first_data = await _wait_list_api(
                    page,
                    pattern=pattern,
                    timeout_ms=30000,
                    trigger=lambda: page.goto(XHS_LIVE_BUYERS_URL, wait_until="domcontentloaded", timeout=60000),
                )
        else:
            if note_contentTag:
                try:
                    await page.goto(XHS_NOTE_KOL_URL, wait_until="domcontentloaded", timeout=60000)
                    await _random_wait(3, 5)
                    first_data = await _wait_list_api(
                        page,
                        pattern=pattern,
                        timeout_ms=30000,
                        trigger=lambda: page.get_by_text(note_contentTag, exact=False).first.click(timeout=8000),
                    )
                    await _random_wait(0.5, 1.5)
                except Exception:
                    pass
            else:
                first_data = await _wait_list_api(
                    page,
                    pattern=pattern,
                    timeout_ms=30000,
                    trigger=lambda: page.goto(XHS_NOTE_KOL_URL, wait_until="domcontentloaded", timeout=60000),
                )
        if first_data is None:
            print("未监听到列表 API，请确认已登录蒲公英并打开对应博主广场")
            return []

        all_candidates: list[XiaohongshuTalent] = []
        seen_uids: set[str] = set()
        page_data = first_data
        page_no = 1
        while True:
            items = parse_fn(page_data)
            for c in items:
                if c.uid in seen_uids:
                    continue
                seen_uids.add(c.uid)
                try:
                    if talent_xhs_repo.get_by_uid(c.uid):
                        print(f"已采集，跳过: {c.nickname} ({c.uid})")
                        continue
                except Exception:
                    pass
                # 点击达人名称采集更多信息
                kol_page = page
                try:
                    async with page.expect_popup(timeout=5000) as pinfo:
                        await page.get_by_text(c.nickname, exact=False).first.click(timeout=8000)
                    kol_page = await pinfo.value
                    await kol_page.wait_for_load_state("domcontentloaded", timeout=20000)
                except Exception:
                    # 有些场景会在当前页打开详情（不弹新 tab）
                    try:
                        await page.get_by_text(c.nickname, exact=False).first.click(timeout=8000)
                    except Exception:
                        pass

                await _random_wait(2, 5)
                await kol_page.get_by_text("邀约TA").first.click(timeout=8000)
                await _random_wait(1, 3)
                await kol_page.get_by_text("直播合作").first.click(timeout=8000)
                await _random_wait(1, 2)
                await kol_page.get_by_text("微信/电话联系").first.click(timeout=8000)
                await _random_wait(1, 2)
                # 点击小眼睛触发查询达人电话 API，监听 API_URL_KOL_CONTACT_PATTERN 并解析 phone/wechat
                # 返回json数据：json/xiaohongshu/query_contact.json
                try:
                    async with kol_page.expect_response(
                        lambda r: API_URL_KOL_CONTACT_PATTERN in r.url and r.status == 200,
                        timeout=15000,
                    ) as resp_info:
                        await kol_page.locator("div.info-tel span.d-icon").first.click(timeout=8000)
                    resp = await resp_info.value
                    data = await resp.json()
                    # 参考 json/xiaohongshu/query_contact.json:
                    # {"data":{"contact_info":{"tel":"...","wechat":"..."}},"code":0,"success":true}
                    inner = (data.get("data") or {}) if isinstance(data, dict) else {}
                    contact_info = (inner.get("contact_info") or {}) if isinstance(inner, dict) else {}
                    phone = contact_info.get("tel")
                    wechat = contact_info.get("wechat")
                    if phone is not None:
                        c.phone = (phone.strip() or None) if isinstance(phone, str) else phone
                    if wechat is not None:
                        c.wechat = (wechat.strip() or None) if isinstance(wechat, str) else wechat
                except Exception:
                    pass
                await _random_wait(1, 2)

                if kol_page is not None:
                    try:
                        await kol_page.close()
                    except Exception:
                        pass
                
                
                if on_candidate is not None:
                    await on_candidate(c)
                all_candidates.append(c)
                if limit and len(all_candidates) >= limit:
                    break
            if limit and len(all_candidates) >= limit:
                break

            # 翻到下一页：点击分页按钮，再等待该页接口
            next_page = page_no + 1
            try:
                async def _trigger_next_page() -> None:
                    clicked = await _click_pagination_page(page, next_page)
                    if not clicked:
                        raise RuntimeError("no next page")

                page_data = await _wait_list_api(
                    page,
                    pattern=pattern,
                    timeout_ms=20000,
                    trigger=_trigger_next_page,
                )
            except Exception:
                break
            page_no = next_page

        print(f"本次共解析到 {len(all_candidates)} 条小红书达人")
        return [
            TalentCandidate(
                platform="XHS",
                talent_id=c.uid,
                username=c.nickname,
                fans_count=c.fans_num,
                category=c.main_sale_type or c.trade_type,
                extra={"red_id": c.red_id, "location": c.location},
            )
            for c in all_candidates
        ]
    finally:
        pass
