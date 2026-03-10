"""
统一 LLM 接口：支持 OpenAI 及国产模型（DeepSeek 等）兼容 OpenAI API。
"""
from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

# 支持 python-dotenv 加载 .env（若已安装）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 安全读取 API Key，避免 None.strip() 报错
_API_KEY = (
    os.environ.get("OPENAI_API_KEY")
    or os.environ.get("DEEPSEEK_API_KEY")
    or ""
).strip() or None

# 可选自定义 base_url（用于 DeepSeek 等兼容 OpenAI 服务）
_raw_base = (os.environ.get("OPENAI_BASE_URL") or "").strip()
_BASE_URL: Optional[str] = None
if _raw_base:
    # 支持写成 api.deepseek.com 或 https://api.deepseek.com
    _BASE_URL = _raw_base if _raw_base.startswith("http") else f"https://{_raw_base}"


_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    """获取已配置的 AsyncOpenAI 客户端。"""
    global _client
    if _client is None:
        kwargs: dict = {}
        if _API_KEY:
            kwargs["api_key"] = _API_KEY
        if _BASE_URL:
            kwargs["base_url"] = _BASE_URL
        _client = AsyncOpenAI(**kwargs)
    return _client


def get_model() -> str:
    """获取模型名。"""
    # 默认 OpenAI 小模型，更贴合当前使用场景
    return os.environ.get("MODEL") or "gpt-4o-mini"


async def chat(
    prompt: str,
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """
    统一调用接口：输入 prompt + 可选 system，返回回复文本（异步）。
    :param prompt: 用户输入
    :param system: 系统提示（角色设定）
    :param model: 模型名，如 gpt-4o / deepseek-chat
    :param temperature: 随机度
    """
    client = get_client()
    model = model or get_model()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()

