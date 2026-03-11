# 数字员工 · 全平台达人自动化邀约系统

本地部署的智能 RPA 助手：抖音、京东、小红书后台的精准筛选 → 自动邀约 → 意向挖掘 → 信息推送。

详见 [doc/product.md](doc/product.md) 与 [doc/plan.md](doc/plan.md)。

---

## 环境要求

- **Python 3.10+**
- Chromium（由 Playwright 安装）

## 前置准备（Day 0）

### 1. 创建虚拟环境

```bash
cd /Users/rudy/proj/DigitBusiness
python3.10 -m venv venv
# 或
python3 -m venv venv
```

激活：

```bash
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

若报错 `Executable doesn't exist at .../chrome-headless-shell`，说明浏览器未装到本机缓存，请在**本机终端**（非 IDE 内置终端）中执行上述命令，确保下载的是当前系统架构（如 Mac arm64）。

### 4. 验证 Stealth 启动（可选）

在项目根目录执行（需先 `source venv/bin/activate`）：

```bash
python -c "
from src.env.stealth_launcher import launch_stealth_browser, check_stealth
import asyncio
async def main():
    async with launch_stealth_browser(headless=True) as page:
        ok = await check_stealth(page)
        print('navigator.webdriver 已抹除:', ok)
        await page.goto('https://bot.sannysoft.com/')
        await page.screenshot(path='data/stealth_check.png')
        print('Stealth 检查页已截图: data/stealth_check.png')
asyncio.run(main())
"
```

若在 IDE 沙箱中运行浏览器被终止，可在本机终端执行上述命令验证。

---

## 项目结构

```
src/
  env/      多平台环境管理器（BrowserManager、Stealth）
  filter/   精准筛选引擎（抖音/京东/小红书）
  chat/     AI 对话与邀约
  report/   信息上报与通知
  db/       SQLite 与达人数据
  config/   平台配置、频率限制、API Key
data/       运行时数据（user_data_dir、截图等，不入库）
doc/        产品与开发文档
tests/      测试
```

## 第一阶段验收（自动化地基）

1. **首次登录**（每平台一次）：`python scripts/login_once.py DY`（或 JD / XHS），在打开的浏览器中完成扫码登录后关闭。
2. **抓一页并入库**：
   - **抖音**：`python scripts/run_filter_one_page.py DY`，打开精选联盟、按关键词搜索、解析达人并写入 `data/talent.db` 的 `talent_dy` 表。
   - **小红书**：`python scripts/run_filter_one_page.py XHS`，打开蒲公英博主广场，按当前脚本配置抓取并写入 `talent_xhs` 表（见下方「小红书抓取说明」）。
   - **京东**：`python scripts/run_filter_one_page.py JD`（JD 待接入分表）。

三平台选择器为占位，若页面改版需在 `src/filter/douyin.py`、`jd.py`、`xiaohongshu.py` 中更新选择器与筛选逻辑。

### 小红书抓取说明（XHS）

- **入口**：`scripts/run_filter_one_page.py XHS`，内部调用 `src/filter/xiaohongshu.fetch_one_page`。
- **两种模式**（由 `kol_type` 决定）：
  - **笔记博主（note）**：打开 `XHS_NOTE_KOL_URL`（博主广场·笔记），点击页面中含有 `note_contentTag` 的元素（如「健康养生」），监听接口 `api/solar/cooperator/blogger/v2`，解析返回的 `data.kols` 并写入 `talent_xhs`。
  - **直播达人（live）**：打开 `XHS_LIVE_BUYERS_URL`（博主广场·直播），光标移到含有 `live_first_category` 的元素上，随机等待 1～3 秒后点击含有 `live_second_category` 的元素，监听接口 `api/draco/distributor-square/live/buyers`，解析 `data.distributor_info_list` 并写入 `talent_xhs`。
- **脚本当前传参示例**（可在 `run_filter_one_page.py` 中修改）：
  - `kol_type="note"`、`note_contentTag="健康养生"`：笔记页按内容分类筛选；
  - `live_first_category="保健食品/膳食营养补充食品"`、`live_second_category="普通膳食营养食品"`：直播页按一级/二级类目筛选（在 `kol_type="live"` 时生效）。
- **频率**：小红书每小时不超过 10 次动作（见 `doc/product.md`）。

## 第二阶段（AI 逻辑集成）

1. **配置 LLM**：复制 `.env.example` 为 `.env`，填写 `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`、`OPENAI_BASE_URL`。
2. **生成邀约文案**：`python scripts/run_invite.py DY 达人昵称 美食 50000`
3. **测试通知**：配置 SMTP 或 Webhook 后，`python scripts/test_notify.py <uid>` 模拟成交推送。
4. **轮询（占位）**：`scripts/run_poller.py` 需对接各平台私信接口后启用。

## 开发计划

按 [doc/plan.md](doc/plan.md) 分阶段执行：自动化地基 → AI 逻辑集成 → 闭环测试与风控。
