"""Проверки изоляции сюжетного контекста у опубликованных JSON-шаблонов."""
from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from problemgen.template_studio.story_compatibility import (  # noqa: E402
    character_scene_compatible,
    noun_scene_compatible,
)
from problemgen.russian.characters import load_characters  # noqa: E402
from problemgen.russian.noun_dict import NOUNS  # noqa: E402


def template(template_id: str) -> dict:
    """Прочитать конкретный шаблон из исходной JSON-библиотеки."""
    path = PROJECT_ROOT / "data" / "template_studio" / "library" / f"{template_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


class StoryContextTests(unittest.TestCase):
    """Контекст должен описывать данные, не попадая в ученический текст."""

    def test_universe_queue_keeps_one_world(self) -> None:
        source = template("queue_of_three_groups")
        for seed in range(20):
            generated = generate_active_template(source, random.Random(seed))
            context = generated["story_context"]
            self.assertEqual(context["mode"], "universe")
            self.assertTrue(context["universe"])
            self.assertEqual(len(context["character_ids"]), 1)
            self.assertIn("single_universe_valid", context["checks"])
            self.assertNotIn("story_context", generated["rendered_problem"])

    def test_common_payment_is_isolated_from_fictional_worlds(self) -> None:
        generated = generate_active_template(template("joint_payment_settlement"), random.Random(4))
        self.assertEqual(generated["story_context"]["mode"], "common")
        self.assertIsNone(generated["story_context"]["universe"])

    def test_heads_and_legs_is_neutral(self) -> None:
        generated = generate_active_template(template("heads_and_legs_two_species"), random.Random(5))
        self.assertEqual(generated["story_context"]["mode"], "neutral")
        self.assertEqual(generated["story_context"]["character_ids"], [])
        self.assertNotIn("{", generated["rendered_problem"])

    def test_tigress_is_forbidden_on_narrow_support(self) -> None:
        tigress = next(item for item in load_characters() if item.character_id == "kfp_tigress")
        self.assertFalse(character_scene_compatible(tigress, "narrow_support"))
        self.assertTrue(character_scene_compatible(tigress, "bridge"))
        self.assertTrue(character_scene_compatible(tigress, "path"))

    def test_ant_is_allowed_on_narrow_support(self) -> None:
        self.assertTrue(noun_scene_compatible(NOUNS["муравей"], "narrow_support"))


if __name__ == "__main__":
    unittest.main()
