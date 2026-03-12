"""
达人表结构与平台专用模型。
按平台分表存储，各平台字段不同。见 schema.sql。
"""
from dataclasses import dataclass, field
from typing import Any, Optional

# 状态码（与 product 一致）
STATUS_NOT_INVITED = 0
STATUS_INVITED = 1
STATUS_IN_TALK = 2
STATUS_DEAL = 3

STATUS_NAMES = {
    STATUS_NOT_INVITED: "未邀约",
    STATUS_INVITED: "已邀约",
    STATUS_IN_TALK: "沟通中",
    STATUS_DEAL: "成交",
}


# main_sale_type 枚举
SALE_TYPE_LIVE = "live"
SALE_TYPE_VIDEO = "video"
SALE_TYPE_IMAGE = "image"
SALE_TYPE_TEXT = "text"


@dataclass
class DouyinTalent:
    """
    抖音达人表 (talent_dy) 对应模型。
    """
    uid: str
    nickname: str
    did: Optional[str] = None
    fans_num: Optional[int] = None
    main_cate: Optional[str] = None
    avatar: Optional[str] = None
    avatar_big: Optional[str] = None
    gender: Optional[int] = None
    city: Optional[str] = None
    author_level: Optional[int] = None
    high_reply: int = 0
    no_ad: int = 0
    author_label: Optional[str] = None
    status: int = STATUS_NOT_INVITED
    main_sale_type: Optional[str] = None
    total_sales_low: Optional[int] = None
    total_sales_high: Optional[int] = None
    total_sales_settle_low: Optional[int] = None
    total_sales_settle_high: Optional[int] = None
    window_product_num: Optional[int] = None
    window_order_low: Optional[int] = None
    window_order_high: Optional[int] = None
    introduction: Optional[str] = None
    wechat: Optional[str] = None
    phone: Optional[str] = None
    chat_log: Optional[str] = None
    contact: Optional[str] = None


@dataclass
class XiaohongshuTalent:
    """
    小红书达人表 (talent_xhs) 对应模型。
    uid: v2 的 userId / buyers 的 distributor_id
    """
    uid: str
    nickname: str
    red_id: Optional[str] = None
    fans_num: Optional[int] = None
    personal_tags: Optional[str] = None  # JSON 或 pipe 分隔
    content_tags: Optional[str] = None   # JSON 或 pipe 分隔
    trade_type: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    status: int = STATUS_NOT_INVITED
    location: Optional[str] = None
    main_sale_type: Optional[str] = None
    introduction: Optional[str] = None
    wechat: Optional[str] = None
    phone: Optional[str] = None
    chat_log: Optional[str] = None
    contact: Optional[str] = None


@dataclass
class WechatChannelsTalent:
    """
    微信小店达人表 (talent_wxshop) 对应模型。
    说明：字段先按最小可用集定义，后续可结合微信小店助手实际 API 扩展。
    """
    uid: str
    nickname: str
    fans_num: Optional[int] = None
    category: Optional[str] = None
    avatar: Optional[str] = None
    introduction: Optional[str] = None
    status: int = STATUS_NOT_INVITED
    wechat: Optional[str] = None
    phone: Optional[str] = None
    chat_log: Optional[str] = None
    contact: Optional[str] = None


@dataclass
class WechatShopTalent:
    """
    微信小店达人表 (talent_wx) 对应模型。
    openId 对应 wxshop 返回的 openfinderid。
    """
    openId: str
    nickname: str
    avatar: Optional[str] = None
    finderUsername: Optional[str] = None
    gender: Optional[int] = None  # 1=female, 2=male
    introduction: Optional[str] = None
    fans_num: Optional[str] = None
    topCatList: Optional[str] = None  # JSON
    hasContact: int = 0
    status: int = STATUS_NOT_INVITED
    wechat: Optional[str] = None
    phone: Optional[str] = None
    chat_log: Optional[str] = None
    contact: Optional[str] = None


@dataclass
class TalentCandidate:
    """
    筛选引擎输出的统一结构，用于跨平台对话等场景。
    入库时映射到各平台专用表。
    """
    platform: str
    talent_id: str
    username: str
    fans_count: Optional[int] = None
    score_or_metric: Optional[float] = None
    category: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    recent_titles: list[str] = field(default_factory=list)
