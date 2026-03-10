-- 按平台分表存储，各平台字段不同
-- 抖音达人表 (talent_dy)
CREATE TABLE IF NOT EXISTS talent_dy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL UNIQUE,
    did TEXT,
    nickname TEXT NOT NULL,
    fans_num INTEGER,
    main_cate TEXT,
    avatar TEXT,
    avatar_big TEXT,
    gender INTEGER,
    city TEXT,
    author_level INTEGER,
    high_reply INTEGER DEFAULT 0,
    no_ad INTEGER DEFAULT 0,
    author_label TEXT,
    status INTEGER NOT NULL DEFAULT 0,
    main_sale_type TEXT,
    total_sales_low INTEGER,
    total_sales_high INTEGER,
    total_sales_settle_low INTEGER,
    total_sales_settle_high INTEGER,
    window_product_num INTEGER,
    window_order_low INTEGER,
    window_order_high INTEGER,
    introduction TEXT,
    wechat TEXT,
    phone TEXT,
    chat_log TEXT,
    contact TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_talent_dy_status ON talent_dy(status);
CREATE INDEX IF NOT EXISTS idx_talent_dy_uid ON talent_dy(uid);

-- 京东达人表 (talent_jd) 占位，后续补充字段
CREATE TABLE IF NOT EXISTS talent_jd (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talent_id TEXT NOT NULL UNIQUE,
    nickname TEXT,
    status INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 小红书达人表 (talent_xhs) 占位，后续补充字段
CREATE TABLE IF NOT EXISTS talent_xhs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talent_id TEXT NOT NULL UNIQUE,
    nickname TEXT,
    status INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
