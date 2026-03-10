"""
京麦 · 京东达人平台：按转化率、客单价筛选，抓取一页达人列表。
需已登录京麦；选择器需根据当前页面在下方常量中维护。
"""
from __future__ import annotations

from src.db.models import TalentCandidate

JD_TALENT_URL = "https://jdd.jd.com/"

SELECTORS = {
    "page_list": "div.daren-list .item",
    "talent_id": "a.daren-link",
    "username": "span.daren-name",
    "convert_rate": "span.convert-rate",   # 转化率
    "price": "span.avg-price",             # 客单价
}


async def fetch_one_page(
    page,
    *,
    min_convert_rate: float | None = None,
    min_price: float | None = None,
) -> list[TalentCandidate]:
    """
    进入京东达人平台，应用筛选，抓取当前一页达人。
    """
    await page.goto(JD_TALENT_URL, wait_until="domcontentloaded", timeout=30000)

    # TODO: 操作筛选（转化率、客单价）
    items = await page.query_selector_all(SELECTORS["page_list"])
    result: list[TalentCandidate] = []
    for node in items or []:
        try:
            tid_el = await node.query_selector(SELECTORS["talent_id"])
            name_el = await node.query_selector(SELECTORS["username"])
            tid = (await tid_el.get_attribute("href") or "").strip() if tid_el else ""
            username = (await name_el.inner_text()) if name_el else ""
            if not tid:
                tid = f"jd_placeholder_{len(result)}"
            rate_el = await node.query_selector(SELECTORS["convert_rate"]) if node else None
            price_el = await node.query_selector(SELECTORS["price"]) if node else None
            rate = _parse_float((await rate_el.inner_text()) if rate_el else None)
            price = _parse_float((await price_el.inner_text()) if price_el else None)
            result.append(
                TalentCandidate(
                    platform="JD",
                    talent_id=tid,
                    username=username or "未知",
                    score_or_metric=rate,
                    extra={"avg_price": price} if price is not None else {},
                )
            )
        except Exception:
            continue
    return result


def _parse_float(s: str | None) -> float | None:
    if not s:
        return None
    try:
        return float(s.replace(",", "").replace("%", "").strip())
    except ValueError:
        return None
