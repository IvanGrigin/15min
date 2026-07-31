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

from problemgen.template_studio.runtime import generate_active_template, resolve_story_profile  # noqa: E402
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

    def test_heads_and_legs_exists_with_and_without_a_hero(self) -> None:
        """Одна и та же задача живёт в двух оболочках внутри одного шаблона.

        Сюжетная берёт персонажа из вселенной, безличная обходится без него.
        Проверяется, что обе действительно выпадают: если сюжет пропадёт,
        останется безличный конвейер, а если пропадёт безличный вариант —
        задача перестанет собираться под сеттинг без подходящих вселенных.
        """
        seen: dict[str, dict[str, object]] = {}
        for seed in range(40):
            generated = generate_active_template(
                template("heads_and_legs_two_species"), random.Random(seed))
            seen.setdefault(generated["variant_metadata"]["story_variant_id"], generated)
            self.assertNotIn("{", generated["rendered_problem"], f"seed {seed}")
        self.assertEqual(set(seen), {"canonical", "hero_counts"}, "выпал не весь набор оболочек")

        self.assertEqual(seen["hero_counts"]["story_context"]["mode"], "universe")
        self.assertTrue(seen["hero_counts"]["story_context"]["character_ids"])
        self.assertEqual(seen["canonical"]["story_context"]["mode"], "abstract")
        self.assertEqual(seen["canonical"]["story_context"]["character_ids"], [])

    def test_story_variants_do_not_change_the_mathematics(self) -> None:
        """Оболочка меняет текст, но не задачу: ответ обязан сойтись в обеих.

        Ради этого варианты и живут в одном файле — иначе две копии условия
        неизбежно разъедутся по границам чисел или по формуле ответа.
        """
        for template_id in (
            "heads_and_legs_two_species", "box_of_bugs_and_spiders",
            "bicycles_two_and_three_wheels", "coffee_with_milk_shares",
        ):
            for seed in range(30):
                generated = generate_active_template(template(template_id), random.Random(seed))
                values = generated["parameters"]
                self.assertTrue(str(generated["answer"]).strip(), f"{template_id}, seed {seed}")
                self.assertNotIn("{", generated["rendered_problem"], f"{template_id}, seed {seed}")
                # Герой — деталь оболочки: на числа он влиять не должен.
                self.assertNotIn(
                    str(generated["answer"]),
                    [str(value) for name, value in values.items() if name == "hero"],
                    f"{template_id}, seed {seed}",
                )

    def test_tigress_is_forbidden_on_narrow_support(self) -> None:
        tigress = next(item for item in load_characters() if item.character_id == "kfp_tigress")
        self.assertFalse(character_scene_compatible(tigress, "narrow_support"))
        self.assertTrue(character_scene_compatible(tigress, "bridge"))
        self.assertTrue(character_scene_compatible(tigress, "path"))

    def test_ant_is_allowed_on_narrow_support(self) -> None:
        self.assertTrue(noun_scene_compatible(NOUNS["муравей"], "narrow_support"))

    def test_every_library_template_has_a_resolved_story_mode(self) -> None:
        library = PROJECT_ROOT / "data" / "template_studio" / "library"
        for path in library.glob("*.json"):
            source = json.loads(path.read_text(encoding="utf-8"))
            profile = resolve_story_profile(source.get("story_profile"), source["parameter_schema"])
            self.assertIn(profile["mode"], {"universe", "common", "neutral", "abstract"}, path.name)


if __name__ == "__main__":
    unittest.main()
