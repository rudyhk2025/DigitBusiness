# 统一筛选结果模型由 db 包提供，此处复导出便于 filter 层使用
from src.db.models import TalentCandidate

__all__ = ["TalentCandidate"]
