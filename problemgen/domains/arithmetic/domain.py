"""Доменный адаптер для арифметических шаблонов."""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from problemgen.core.difficulty import get_difficulty_level
from problemgen.domains.base import MathDomain
from problemgen.russian import count_with_word_ru

from . import templates as tmpl


def _resolve_seed(seed_mode: str, seed: Optional[int]) -> Optional[int]:
    if seed_mode == "random":
        return None
    if seed_mode == "fixed":
        if seed is None:
            raise ValueError("Для режима fixed нужно передать --seed.")
        return seed
    if seed_mode == "today":
        return int(datetime.now().strftime("%Y%m%d"))
    raise ValueError("seed_mode должен быть today, random или fixed.")


class ArithmeticDomain(MathDomain):
    code = "arithmetic"
    label = "Арифметика"
    description = (
        "Классические текстовые задачи с правильным склонением русских слов: "
        "головы и ноги, пропорции, возраст, турниры, окраска куба, оплата."
    )

    def list_templates(self):
        return tmpl.list_templates()

    def available_themes(self) -> Dict[str, str]:
        return {}

    def generate_bundle(
        self,
        *,
        count: int,
        template_name: str,
        difficulty_level: str,
        story_theme: str = "any",
        seed_mode: str = "random",
        seed: Optional[int] = None,
        output_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if count <= 0:
            raise ValueError("Количество задач должно быть положительным.")

        get_difficulty_level(difficulty_level)
        resolved_seed = _resolve_seed(seed_mode, seed)
        rng = random.Random(resolved_seed)

        factories = tmpl.TEMPLATE_FACTORIES
        if template_name != "any" and template_name not in factories:
            raise ValueError(
                f"Шаблон '{template_name}' не найден. "
                f"Доступные: {list(factories)}"
            )

        factory_names = list(factories)
        problems = []
        for i in range(1, count + 1):
            name = template_name if template_name != "any" else rng.choice(factory_names)
            problem = factories[name](
                rng=rng,
                index=i,
                difficulty_level=difficulty_level,
            )
            problems.append(problem)

        if output_path is None:
            output_path = str(
                Path("outputs") / "generated"
                / f"{self.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        bundle = {
            "count": len(problems),
            "count_text": count_with_word_ru(len(problems), ("задача", "задачи", "задач")),
            "domain": self.code,
            "domain_label": self.label,
            "template_name": template_name,
            "difficulty_level": difficulty_level,
            "seed_mode": seed_mode,
            "seed_value": resolved_seed,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "output_path": str(path),
            "problems": [p.to_dict() for p in problems],
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        return bundle
