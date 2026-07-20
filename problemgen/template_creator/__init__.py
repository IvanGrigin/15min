"""Автоматический провайдерный конвейер «задача → JSON-шаблон»."""

from .provider import MathTemplateGenerationProvider, provider_from_environment
from .service import TemplateCreatorService

__all__ = ("MathTemplateGenerationProvider", "TemplateCreatorService", "provider_from_environment")
