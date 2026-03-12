"""
微信小店 · 达人广场抓取（WXSHOP）。

列表接口返回结构参考：json/wxshop/talentList.json

字段映射（按用户要求）：
- openId: accountList[0].openfinderid
- nickname: finderInfo.nickname
- avatar: finderInfo.headImg
- finderUsername: accountList[0].finderUsername
- gender: finderInfo.finderSexType（1=female, 2=male）
- introduction: finderInfo.introduction
- fans_num: finderInfo.fansNumber（原样字符串保存）
- topCatList: finderInfo.topCatList（JSON）
- hasContact: finderInfo.hasContact
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Iterable

from src.db.models import TalentCandidate, WechatShopTalent
from src.db import talent_wx_repo
from src.filter import random_wait as _random_wait

WXSHOP_KOL_LIST_URL = "https://store.weixin.qq.com/shop/findersquare/find"
API_TALENT_LIST_URL_PATTERN = "shop-faas/mmchannelstradeleague/finderSquare/cgi/getSquareTalentList"

@dataclass
class WxshopFilters:
    """
    微信小店达人广场筛选参数（按页面分组）。

    说明：
    - 这里不强绑定具体 DOM 结构，只按“分组标题 + 选项文案”进行点击。
    - 你可以直接把页面上看到的文案传进来，例如：
      - deliver_categories=["食品饮料", "美妆护肤"]
      - deliver_metrics=["GMV：￥1万以下", "直播场次：0-10"]（以实际文案为准）
      - talent_profile=["女性", "官方认证"]（以实际文案为准）
      - fans_profile=["1万以下", "1万-10万"]（以实际文案为准）
      - others=["有联系方式"]
    """

    deliver_categories: list[str] = field(default_factory=list)  # 带货类目
    deliver_metrics: list[str] = field(default_factory=list)     # 带货数据
    talent_profile: list[str] = field(default_factory=list)      # 达人画像
    fans_profile: list[str] = field(default_factory=list)        # 粉丝画像
    others: list[str] = field(default_factory=list)              # 其他筛选


def _app_root(page):
    """
    达人广场页面主体位于 micro-app(findingsquare) 的 shadow DOM 内。
    Playwright locator 可穿透 open shadow root，因此直接从 micro-app 下找文本即可。
    """
    return page.locator('micro-app[name="findersquare"]').first


async def _is_option_selected(opt) -> bool:
    """
    尝试判断一个筛选项是否处于“已选中”状态。
    兼容常见实现：aria-checked/aria-selected、input.checked、class 包含 active/selected/checked。
    """
    try:
        return await opt.evaluate(
            """(el) => {
              const attr = (n) => (el.getAttribute && el.getAttribute(n)) || null;
              const ariaChecked = attr('aria-checked');
              if (ariaChecked === 'true') return true;
              const ariaSelected = attr('aria-selected');
              if (ariaSelected === 'true') return true;
              // input checkbox/radio
              const input = el.querySelector && el.querySelector('input[type="checkbox"],input[type="radio"]');
              if (input && input.checked) return true;
              const cls = (el.className || '').toString().toLowerCase();
              if (cls.includes('active') || cls.includes('selected') || cls.includes('checked')) return true;
              return false;
            }"""
        )
    except Exception:
        return False


async def _click_and_assert_selected(scope, option_text: str, *, timeout_ms: int = 15000) -> bool:
    """
    在 scope 范围内点击某个选项文案，并校验其最终变为“选中”。
    返回是否成功选中。
    """
    opt = scope.get_by_text(option_text, exact=False).first
    try:
        await opt.wait_for(state="visible", timeout=timeout_ms)
        await opt.click(timeout=timeout_ms)
    except Exception:
        return False

    # 等 UI 状态更新
    for _ in range(20):
        if await _is_option_selected(opt):
            return True
        await scope.page.wait_for_timeout(150)
    return await _is_option_selected(opt)


async def _apply_group_filters(page, *, group_title: str, options: Iterable[str]) -> dict[str, bool]:
    """
    按“分组标题”应用多项筛选，并返回每个选项是否选中成功。
    """
    root = _app_root(page)
    results: dict[str, bool] = {}
    opts = [o for o in options if (o or "").strip()]
    if not opts:
        return results

    # 通过标题定位分组，再在该分组附近点击选项
    # 由于 DOM 可能变化，这里用“标题元素的父容器”作为 scope 做启发式查找。
    title_loc = root.get_by_text(group_title, exact=False).first
    try:
        await title_loc.wait_for(state="visible", timeout=8000)
    except Exception:
        # 找不到该分组就直接标记失败（避免误点别处）
        for o in opts:
            results[o] = False
        return results

    group_scope = title_loc.locator("xpath=ancestor::*[self::div or self::section][1]")
    for o in opts:
        ok = await _click_and_assert_selected(group_scope, o)
        results[o] = ok
        await _random_wait(0.2, 0.6)
    return results


async def apply_filters_and_check(page, filters: WxshopFilters) -> dict[str, dict[str, bool]]:
    """
    应用筛选并校验每项是否生效（被选中）。
    返回结构：{group: {option_text: True/False}}
    """
    # 先确保页面在达人广场（避免 micro-app 尚未挂载）
    await _app_root(page).wait_for(state="attached", timeout=20000)

    # 尝试点开“筛选”面板（如果页面默认已展开，这一步不会报错）
    root = _app_root(page)
    try:
        btn = root.get_by_text("筛选", exact=False).first
        if await btn.is_visible():
            await btn.click(timeout=5000)
            await _random_wait(0.3, 0.8)
    except Exception:
        pass

    return {
        "带货类目": await _apply_group_filters(page, group_title="带货类目", options=filters.deliver_categories),
        "带货数据": await _apply_group_filters(page, group_title="带货数据", options=filters.deliver_metrics),
        "达人画像": await _apply_group_filters(page, group_title="达人画像", options=filters.talent_profile),
        "粉丝画像": await _apply_group_filters(page, group_title="粉丝画像", options=filters.fans_profile),
        "其他筛选": await _apply_group_filters(page, group_title="其他筛选", options=filters.others),
    }


async def _wait_list_api(
    page,
    *,
    pattern: str,
    timeout_ms: int = 30000,
    trigger: Callable[[], Awaitable[None]] | None = None,
) -> dict:
    pred = lambda r: pattern in r.url and r.status == 200
    if trigger is None:
        resp = await page.wait_for_response(pred, timeout=timeout_ms)
        return await resp.json()
    async with page.expect_response(pred, timeout=timeout_ms) as resp_info:
        await trigger()
    resp = await resp_info.value
    return await resp.json()


def _parse_list_response(data: dict) -> list[WechatShopTalent]:
    """
    解析微信小店达人列表响应（见 json/wxshop/talentList.json）。
    """
    if not isinstance(data, dict):
        return []
    if data.get("code") not in (0, "0", None):
        return []

    items = data.get("list") or []
    if not isinstance(items, list):
        return []

    result: list[WechatShopTalent] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        finder_info = it.get("finderInfo") or {}
        account_list = it.get("accountList") or []
        acc0 = account_list[0] if isinstance(account_list, list) and account_list else {}

        open_id = (acc0.get("openfinderid") or "").strip()
        nickname = (finder_info.get("nickname") or acc0.get("nickname") or "").strip()
        if not open_id or not nickname:
            continue

        avatar = finder_info.get("headImg") or acc0.get("headImg")
        finder_username = acc0.get("finderUsername")
        gender = finder_info.get("finderSexType")
        introduction = finder_info.get("introduction")
        fans_num = finder_info.get("fansNumber")
        top_cat_list = finder_info.get("topCatList")
        has_contact = finder_info.get("hasContact")

        top_cat_json = None
        if top_cat_list is not None:
            top_cat_json = (
                json.dumps(top_cat_list, ensure_ascii=False)
                if isinstance(top_cat_list, (list, dict))
                else str(top_cat_list)
            )

        result.append(
            WechatShopTalent(
                openId=open_id,
                nickname=nickname,
                avatar=avatar,
                finderUsername=finder_username,
                gender=gender if isinstance(gender, int) else None,
                introduction=introduction,
                fans_num=str(fans_num) if fans_num is not None else None,
                topCatList=top_cat_json,
                hasContact=int(has_contact) if has_contact is not None else 0,
            )
        )

    return result


async def fetch_one_page(
    page,
    *,
    api_list_pattern: str | None = None,
    filters: WxshopFilters | None = None,
    limit: int = 20,
    on_candidate: Callable[[WechatShopTalent], Awaitable[None]] | None = None,
) -> list[TalentCandidate]:
    """
    打开微信小店达人广场并监听列表接口抓一页。

    使用方式（建议）：
    1) 先执行 `python scripts/login_once.py WXSHOP` 完成登录；
    2) 运行 `python scripts/run_filter_one_page.py WXSHOP`；
    3) 如接口路径变更，可通过 api_list_pattern 覆盖监听 pattern。
    """

    pattern = api_list_pattern or API_TALENT_LIST_URL_PATTERN

    try:
        await page.goto(WXSHOP_KOL_LIST_URL, wait_until="domcontentloaded", timeout=60000)
        await _random_wait(1.5, 3.0)

        if filters is not None:
            check = await apply_filters_and_check(page, filters)
            # 若有明显失败项，打印出来，方便你对照页面文案/DOM 调整
            failed = [(g, o) for g, m in check.items() for o, ok in m.items() if ok is False]
            if failed:
                print(f"[WXSHOP] 筛选未生效项: {failed}")

        # 触发一次列表加载后再监听（通常筛选会自动刷新列表；否则可手动滚动/翻页触发）
        data = await _wait_list_api(page, pattern=pattern, timeout_ms=30000)
    except Exception:
        print("未监听到微信小店达人列表 API：请确认已登录并进入达人广场页")
        return []

    items = _parse_list_response(data)
    all_candidates: list[WechatShopTalent] = []
    for t in items:
        try:
            if talent_wx_repo.get_by_openId(t.openId):
                print(f"已采集，跳过: {t.nickname} ({t.openId})")
                continue
        except Exception:
            pass

        if on_candidate is not None:
            await on_candidate(t)
        else:
            talent_wx_repo.add(t)

        all_candidates.append(t)
        if limit and len(all_candidates) >= limit:
            break

    return [
        TalentCandidate(
            platform="WXSHOP",
            talent_id=t.openId,
            username=t.nickname,
            fans_count=None,
            category=None,
            extra={
                "avatar": t.avatar,
                "finderUsername": t.finderUsername,
                "gender": t.gender,
                "introduction": t.introduction,
                "fans_num": t.fans_num,
                "topCatList": t.topCatList,
                "hasContact": t.hasContact,
            },
            recent_titles=[],
        )
        for t in all_candidates
    ]

