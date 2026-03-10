# 免登录启动流程说明

各平台（抖音/抖店、京麦、蒲公英）使用独立的 `user_data_dir` 保存登录态，首次需人工登录一次，之后脚本可复用 Session 免扫码启动。

## 1. 目录与平台对应

| 平台 | 代码 | user_data_dir |
|------|------|----------------|
| 抖音/抖店 | DY | `data/user_data_douyin` |
| 京东/京麦 | JD | `data/user_data_jd` |
| 小红书/蒲公英 | XHS | `data/user_data_xiaohongshu` |

## 2. 首次登录（每个平台做一次）

运行「登录辅助脚本」会启动**有头**浏览器并打开对应后台登录页，你手动完成扫码/密码登录即可。关闭浏览器后，Cookie 与 Session 会保存在该平台的 `user_data_dir` 中。

```bash
source venv/bin/activate
# 抖音/抖店
python scripts/login_once.py DY

# 京麦
python scripts/login_once.py JD

# 蒲公英
python scripts/login_once.py JD XHS
```

## 3. 日常使用（免登录）

之后在同一台机器上运行筛选/邀约脚本时，使用 `BrowserManager(platform="DY", use_persistent=True)` 启动即可直接进入已登录状态，无需再次扫码。若平台要求重新登录（如 Session 过期），重新执行一次对应平台的 `login_once.py` 即可。

## 4. 注意

- 不要在多机之间复制 `data/user_data_*` 目录做「共享登录」，可能触发风控。
- 各平台目录相互隔离，抖店、京麦、蒲公英的登录态互不影响。
