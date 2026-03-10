# 模块2：精准筛选引擎（抖音/京东/小红书）
import asyncio
import random


async def random_wait(min_sec: float = 1, max_sec: float = 3):
    """随机等待，模拟人工操作间隔。"""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


__all__ = ["random_wait"]
