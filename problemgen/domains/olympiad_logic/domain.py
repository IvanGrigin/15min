from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from problemgen.core.difficulty import get_difficulty_level
from problemgen.core.story_worlds import StoryContext
from problemgen.core.themes import THEMES, get_theme_label
from problemgen.domains.base import MathDomain
from problemgen.russian import attach_language_report, count_with_word_ru

from . import templates


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


class OlympiadLogicDomain(MathDomain):
    code = "olympiad_logic"
    label = "Олимпиадная логика"
    description = "Олимпиадные текстовые задачи с отдельной математической логикой и общим сюжетным слоем."

    def list_templates(self):
        return templates.list_templates()

    def available_themes(self) -> Dict[str, str]:
        return {code: theme.label for code, theme in THEMES.items()}

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
        if count <= 0:
            raise ValueError("Количество задач должно быть положительным.")

        difficulty = get_difficulty_level(difficulty_level)
        resolved_seed = _resolve_seed(seed_mode, seed)
        rng = random.Random(resolved_seed)

        factories = dict(templates.TEMPLATE_FACTORIES)
        if template_name != "any" and template_name not in factories:
            raise ValueError(f"Шаблон '{template_name}' не найден для домена '{self.code}'.")

        problems = []
        factory_names = list(factories)
        story_contexts = list((options or {}).get("story_contexts", []))
        for index in range(1, count + 1):
            current_name = template_name if template_name != "any" else rng.choice(factory_names)
            story_context: StoryContext | None = None
            if index - 1 < len(story_contexts):
                story_context = story_contexts[index - 1]
            problem = factories[current_name](
                rng=rng,
                index=index,
                difficulty_level=difficulty_level,
                story_context=story_context,
            )
            problems.append(attach_language_report(problem))

        if output_path is None:
            output_path = str(Path("outputs") / "generated" / f"{self.code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        bundle = {
            "count": len(problems),
            "count_text": count_with_word_ru(len(problems), ("задача", "задачи", "задач")),
            "domain": self.code,
            "domain_label": self.label,
            "template_name": template_name,
            "difficulty_level": difficulty.code,
            "difficulty_label": difficulty.label,
            "difficulty_description": difficulty.description,
            "requested_story_theme": story_theme,
            "requested_story_theme_label": get_theme_label(story_theme),
            "requested_story_world": (options or {}).get("story_world", "any"),
            "seed_mode": seed_mode,
            "seed_value": resolved_seed,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "output_path": str(path),
            "problems": [problem.to_dict() for problem in problems],
            "metadata": {
                "mode": "olympiad_logic",
                "language_summary": {
                    "issues_found": sum(len(problem.metadata.get("language_issues", [])) for problem in problems),
                },
            },
        }

        with path.open("w", encoding="utf-8") as file:
            json.dump(bundle, file, ensure_ascii=False, indent=2)

        return bundle
