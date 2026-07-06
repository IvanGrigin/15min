from __future__ import annotations

from typing import Any, Dict, List, Optional

from problemgen.core.models import TemplateDescriptor
from problemgen.domains.base import MathDomain

from . import legacy_engine as legacy

SEGMENT_TEMPLATE_LABELS = {
    "line_two_segments_possible_ac": (
        "Два отрезка и возможные значения третьего",
        "По двум связанным расстояниям определить все возможные значения третьего отрезка.",
    ),
    "line_three_consecutive_segments": (
        "Три последовательных отрезка",
        "Сумма трех последовательных отрезков на одной прямой.",
    ),
    "line_equality_relation": (
        "Равные крайние отрезки",
        "Найти неизвестный отрезок из условия о равных частях на прямой.",
    ),
    "plane_midpoint": (
        "Середина отрезка",
        "Задача о середине отрезка и удвоении известной половины.",
    ),
    "plane_point_inside_segment": (
        "Точка внутри отрезка",
        "Разбиение отрезка на части и поиск неизвестной части.",
    ),
}


class SegmentsDomain(MathDomain):
    code = "segments"
    label = "Отрезки"
    description = "Задачи на прямой и на плоскости с сюжетными вариациями и размерностями."

    def list_templates(self) -> List[TemplateDescriptor]:
        registry = legacy.build_default_registry("medium")
        return [
            TemplateDescriptor(
                code=name,
                label=SEGMENT_TEMPLATE_LABELS.get(name, (legacy.humanize_template_name(name), ""))[0],
                description=SEGMENT_TEMPLATE_LABELS.get(
                    name,
                    ("", "Шаблон задач на отрезки из совместимого сегментного движка."),
                )[1],
            )
            for name in registry.names()
        ]

    def available_themes(self) -> Dict[str, str]:
        return dict(legacy.STORY_THEME_LABELS)

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
        mode = "all"
        if options:
            mode = str(options.get("mode", "all"))

        result = legacy.generate_problem_set(
            count=count,
            mode=mode,
            template_name=template_name,
            difficulty_level=difficulty_level,
            story_theme=story_theme,
            seed_mode=seed_mode,
            seed=seed,
            output_path=None if output_path is None else legacy.Path(output_path),
        )
        result["domain"] = self.code
        result["domain_label"] = self.label
        result["metadata"] = {
            "mode": mode,
            "engine": "legacy_segments",
        }
        return result
