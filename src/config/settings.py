"""
平台配置、频率限制、API 占位。
后续从环境变量或 .env 读取敏感信息，勿提交密钥。
"""
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 各平台独立 user_data_dir（Cookies/登录态隔离）
DATA_DIR = PROJECT_ROOT / "data"
USER_DATA = {
    "DY": DATA_DIR / "user_data_douyin",
    "JD": DATA_DIR / "user_data_jd",
    "XHS": DATA_DIR / "user_data_xiaohongshu",
    "WXSHOP": DATA_DIR / "user_data_wechat_channels",
}

# 频率限制（与 product.md 一致）
RATE_LIMIT = {
    "XHS": 10,   # 小红书 每小时不超过 10 次动作
    "DY": 30,    # 抖音 每小时不超过 30 次
    "JD": 30,    # 京东 每小时不超过 30 次
    "WXSHOP": 30,  # 微信小店 每小时不超过 30 次（先按抖音/京东同级，后续可单独调）
}

# API（占位，实际从环境变量读取）
OPENAI_API_KEY = ""  # 或 os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = ""  # 国产模型兼容时填，如 DeepSeek
DEEPSEEK_API_KEY = ""
