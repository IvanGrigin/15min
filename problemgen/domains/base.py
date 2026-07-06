from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from problemgen.core.models import TemplateDescriptor


class MathDomain(ABC):
    code: str
    label: str
    description: str

    @abstractmethod
    def list_templates(self) -> List[TemplateDescriptor]:
        raise NotImplementedError

    @abstractmethod
    def available_themes(self) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def generate_bundle(
        self,
        *,
        count: int,
        template_name: str,
        difficulty_level: str,
        story_theme: str,
        seed_mode: str,
        seed: Optional[int],
        output_path: Optional[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError
