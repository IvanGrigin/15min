"""Безопасное административное создание параметрических шаблонов.

Пакет не изменяет production-шаблоны напрямую: до явной активации все записи
живут в изолированном хранилище Template Studio.
"""

from .analyzer import TemplateAnalyzer
from .service import TemplateStudioService

__all__ = ("TemplateAnalyzer", "TemplateStudioService")
