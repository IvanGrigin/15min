"""Вертикальный срез: морфология в Template Studio + независимая проверка математики.

Проверяется то, чего раньше в проекте не было:
  1) падежи и род персонажей приходят из данных, а не из эвристики;
  2) constraints действительно исполняются (rejection sampling);
  3) ответы шаблонов сходятся с независимым решением задачи по её условию.
"""
from __future__ import annotations

import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.russian.characters import characters_by_universe, load_characters  # noqa: E402
from problemgen.russian.template_engine import render_template as render_russian  # noqa: E402
from problemgen.template_studio.runtime import (  # noqa: E402
    TemplateRuntimeError,
    generate_active_template,
    render_template,
    validate_slots,
)
from problemgen.template_studio.safe_expressions import evaluate_expression  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
BASE_TEMPLATE = LIBRARY["motion_half_path_half_time_ride"]
ADVANCED_TEMPLATE = LIBRARY["motion_third_path_third_time_ride"]


SEEDS = range(25)


class CharacterRegistryTests(unittest.TestCase):
    def test_registry_is_consistent(self) -> None:
        characters = load_characters()
        self.assertGreaterEqual(len(characters), 12)
        for character in characters:
            for case in ("nom", "gen", "dat", "acc", "ins", "pre"):
                self.assertTrue(character.get_case(case).strip())
            self.assertIn(character.gender, {"m", "f", "n"})

    def test_registry_names_match_markdown_source(self) -> None:
        """Реестр падежей не должен разъезжаться со списком имён из Docs/."""
        from problemgen.generation.comparison_templates import load_approved_characters

        from problemgen.russian.characters import COMMON_POOL, canonical_universes

        approved = load_approved_characters()
        canonical = canonical_universes()
        for universe, characters in characters_by_universe().items():
            if universe == COMMON_POOL or universe not in canonical:
                # Обычные имена и расширенные миры (Гравити Фолз, мифы Греции, легенды)
                # в markdown-таблице 25 франшиз отсутствуют по построению.
                continue
            self.assertIn(universe, approved, f"Вселенной {universe} нет в markdown-таблице.")
            markdown_names = {character.name for character in approved[universe]}
            for character in characters:
                self.assertIn(
                    character.nom, markdown_names,
                    f"{character.nom} отсутствует в Docs/approved_dimensions_150_characters.md",
                )

    def test_gender_is_explicit_not_guessed(self) -> None:
        """Эвристика по окончанию ошибается на этих именах — данные должны побеждать."""
        by_name = {character.nom: character for character in load_characters()}
        self.assertEqual(by_name["галчонок Хватайка"].gender, "m")
        self.assertEqual(by_name["Нюша"].gender, "f")
        self.assertEqual(by_name["корова Мурка"].gender, "f")

    def test_indeclinable_names_do_not_change(self) -> None:
        by_name = {character.nom: character for character in load_characters()}
        self.assertEqual(by_name["Фродо"].get_case("gen"), "Фродо")
        self.assertEqual(by_name["Гимли"].get_case("dat"), "Гимли")


class SlotRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.by_name = {character.nom: character for character in load_characters()}

    def test_case_and_gender_slots(self) -> None:
        text = "{hero:nom} {hero:g,пришёл|пришла} к {friend:dat} и {hero:g,ушёл|ушла} с {friend:ins}."
        rendered = render_template(text, {
            "hero": self.by_name["Нюша"],
            "friend": self.by_name["кот Матроскин"],
        })
        self.assertEqual(rendered, "Нюша пришла к коту Матроскину и ушла с котом Матроскиным.")

    def test_lowercase_name_is_capitalized_only_at_sentence_start(self) -> None:
        rendered = render_template("{hero:nom} ушёл. Дома остался {hero:nom}.", {
            "hero": self.by_name["пёс Шарик"],
        })
        self.assertEqual(rendered, "Пёс Шарик ушёл. Дома остался пёс Шарик.")

    def test_noun_agreement_with_integer_and_fraction(self) -> None:
        from problemgen.russian.noun_dict import NOUNS

        context = {"h": NOUNS["час"], "one": 1, "few": 3, "many": 11, "half": 2.5}
        nbsp = " "  # движок ставит неразрывный пробел между числом и словом
        self.assertEqual(render_russian("{h:count,one}", context), f"1{nbsp}час")
        self.assertEqual(render_russian("{h:count,few}", context), f"3{nbsp}часа")
        self.assertEqual(render_russian("{h:count,many}", context), f"11{nbsp}часов")
        self.assertEqual(render_russian("{h:count,half}", context), f"2,5{nbsp}часа")

    def test_broken_slots_are_rejected_with_readable_message(self) -> None:
        for text, fragment in [
            ("{hero:genitive} пришёл.", "Неизвестный падеж"),
            ("{hero:g,купил} пришёл.", "две или три формы"),
            ("{hero:magic,n} пришёл.", "Неизвестная операция"),
        ]:
            with self.assertRaises(TemplateRuntimeError) as error:
                validate_slots(text)
            self.assertIn(fragment, str(error.exception))


class ConstraintTests(unittest.TestCase):
    def test_comparisons_are_available_in_expressions(self) -> None:
        self.assertTrue(evaluate_expression("a > b and a % 2 == 0", {"a": 4, "b": 3}))
        self.assertEqual(evaluate_expression("a if a > b else b", {"a": 4, "b": 3}), 4)

    def test_constraints_are_enforced_by_resampling(self) -> None:
        template = {
            "candidate_template_text": "Найдите разность {a} и {b}.",
            "parameter_schema": {
                "a": {"type": "integer", "min": 1, "max": 40},
                "b": {"type": "integer", "min": 1, "max": 40},
            },
            "derived_values": {},
            "constraints": ["a > b", "(a - b) % 5 == 0"],
            "answer_expression": "a - b",
        }
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            values = generated["parameters"]
            self.assertGreater(values["a"], values["b"])
            self.assertEqual((values["a"] - values["b"]) % 5, 0)

    def test_impossible_constraints_fail_loudly(self) -> None:
        template = {
            "candidate_template_text": "Число {a}.",
            "parameter_schema": {"a": {"type": "integer", "min": 1, "max": 5}},
            "derived_values": {},
            "constraints": ["a > 100"],
            "answer_expression": "a",
        }
        with self.assertRaises(TemplateRuntimeError):
            generate_active_template(template, random.Random(0))


class MotionTemplateMathTests(unittest.TestCase):
    """Ответы шаблона сверяются с решением задачи «с нуля», по её условию."""

    def test_base_template_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(BASE_TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            v1 = Fraction(values["v1"])
            v2 = Fraction(values["v2"])
            tail = Fraction(values["tail_m"], 1000)
            total_h = Fraction(values["total_min"], 60)

            # Условие: половина пути со скоростью v1, половина ВСЕГО времени со
            # скоростью v2, остаток tail верхом; ищем путь пешком и время верхом.
            run_h = total_h / 2
            run_distance = v2 * run_h
            path = 2 * (run_distance + tail)          # S/2 = run_distance + tail
            walk_h = (path / 2) / v1
            ride_h = total_h - walk_h - run_h

            self.assertGreater(ride_h, 0, f"seed {seed}: время верхом должно быть положительным")
            self.assertEqual(ride_h * 60, values["ride_min"], f"seed {seed}: время верхом")
            self.assertEqual(path - tail, Fraction(str(values["foot_km"])), f"seed {seed}: путь пешком")
            self.assertEqual(
                generated["answer"],
                [values["foot_km"], values["ride_min"]],
                f"seed {seed}: ответ шаблона",
            )
            # Качество условия: лошадь не медленнее пешехода.
            self.assertGreater(tail / ride_h, v1, f"seed {seed}: скорость верхом")

    def test_advanced_template_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(ADVANCED_TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            v1 = Fraction(values["v1"])
            v2 = Fraction(values["v2"])
            v3 = Fraction(values["v3"])
            total_h = Fraction(values["total_min"], 60)

            # Условие: треть пути со скоростью v1, треть ВСЕГО времени со скоростью
            # v2, остаток пути со скоростью v3. Неизвестен весь путь S.
            #   S/3 + v2*(T/3) + v3*(T - S/(3*v1) - T/3) = S
            run_h = total_h / 3
            run_distance = v2 * run_h
            # S/3 + run_distance + v3*(2T/3 - S/(3*v1)) = S
            #   →  S * (2/3 + v3/(3*v1)) = run_distance + v3*(2T/3)
            coefficient = Fraction(2, 3) + v3 / (3 * v1)
            path = (run_distance + v3 * (2 * total_h / 3)) / coefficient
            walk_h = (path / 3) / v1
            ride_h = total_h - walk_h - run_h
            ride_distance = v3 * ride_h

            self.assertEqual(path, Fraction(str(values["path_km"])), f"seed {seed}: весь путь")
            self.assertEqual(ride_distance, Fraction(str(values["ride_km"])), f"seed {seed}: путь верхом")
            self.assertEqual(generated["answer"], [values["path_km"], values["ride_km"]])
            self.assertGreater(v2, v1, f"seed {seed}: бег должен быть быстрее ходьбы")

    def test_texts_are_well_formed(self) -> None:
        for template in (BASE_TEMPLATE, ADVANCED_TEMPLATE):
            for seed in SEEDS:
                text = generate_active_template(template, random.Random(seed))["rendered_problem"]
                self.assertNotIn("{", text)
                self.assertNotIn("  ", text)
                self.assertTrue(text[0].isupper(), text)
                self.assertTrue(text.rstrip().endswith("?"), text)

    def test_hero_and_rider_share_universe_and_differ(self) -> None:
        # Вселенную берём с самого персонажа, а не по имени: одно и то же имя
        # может принадлежать разным мирам («Ёжик» есть и в Смешариках,
        # и в «Ёжике в тумане»), и отображение имя -> вселенная неоднозначно.
        for template in (BASE_TEMPLATE, ADVANCED_TEMPLATE):
            for seed in SEEDS:
                values = generate_active_template(template, random.Random(seed))["parameters"]
                hero, rider = values["hero"], values["rider"]
                self.assertNotEqual(hero.character_id, rider.character_id)
                self.assertEqual(hero.universe, rider.universe)


if __name__ == "__main__":
    unittest.main()
