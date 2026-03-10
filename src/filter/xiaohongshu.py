"""
蒲公英 · 博主广场：抓取博主及最近 3 篇笔记标题，供 AI 个性化邀约。
需已登录蒲公英创作者平台；选择器需随页面改版维护。
"""
from __future__ import annotations

from src.db.models import TalentCandidate

XHS_CREATOR_URL = "https://creator.xiaohongshu.com/"

SELECTORS = {
    "blogger_list": "div.blogger-list .blogger-item",
    "talent_id": "a.blogger-link",
    "username": "span.blogger-name",
    "fans": "span.fans-count",
    "note_titles": "div.recent-notes span.note-title",  # 最近笔记标题，取前 3
}


async def fetch_one_page(page, *, limit: int = 20) -> list[TalentCandidate]:
    """
    进入博主广场（或等价列表页），抓取一页博主及其最近 3 篇笔记标题。
    """
    await page.goto(XHS_CREATOR_URL, wait_until="domcontentloaded", timeout=30000)

    items = await page.query_selector_all(SELECTORS["blogger_list"])
    result: list[TalentCandidate] = []
    for node in items or []:
        if len(result) >= limit:
            break
        try:
            tid_el = await node.query_selector(SELECTORS["talent_id"])
            name_el = await node.query_selector(SELECTORS["username"])
            tid = (await tid_el.get_attribute("href") or "").strip() if tid_el else ""
            username = (await name_el.inner_text()) if name_el else ""
            if not tid:
                tid = f"xhs_placeholder_{len(result)}"
            fans_el = await node.query_selector(SELECTORS["fans"]) if node else None
            fans = _parse_int((await fans_el.inner_text()) if fans_el else None)
            titles_el = await node.query_selector_all(SELECTORS["note_titles"]) if node else []
            recent_titles = []
            for i, t in enumerate(titles_el[:3]):
                if i >= 3:
                    break
                try:
                    recent_titles.append((await t.inner_text()).strip())
                except Exception:
                    pass
            result.append(
                TalentCandidate(
                    platform="XHS",
                    talent_id=tid,
                    username=username or "未知",
                    fans_count=fans,
                    recent_titles=recent_titles,
                )
            )
        except Exception:
            continue
    return result


def _parse_int(s: str | None) -> int | None:
    if not s:
        return None
    s = s.replace(",", "").replace("万", "0000").strip()
    try:
        return int(float(s))
    except ValueError:
        return None
