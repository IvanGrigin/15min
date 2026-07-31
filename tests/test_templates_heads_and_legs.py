"""Независимая проверка шаблонов темы «Головы, ноги, колёса и подсчёт объектов».

Особенность темы: число ног не написано в условии — ученик знает его из жизни,
а шаблон берёт из словаря. Поэтому решатели тоже не берут его из параметров:
они выцепляют из текста название существа и смотрят его признак в словаре,
как это сделал бы человек. Именно так проверяется, что признак и текст сошлись.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.russian.noun_dict import NOUNS  # noqa: E402
from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)
SPACE = r"[\s\u00a0]+"

# Форма родительного множественного -> число ног. Тест узнаёт существо из
# условия, а не из скрытого параметра генератора.
LEGS_BY_FORM = {
    noun.gen_pl: noun.legs for noun in NOUNS.values() if noun.legs is not None
}


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def creatures_in(text: str) -> list[tuple[str, int]]:
    """Существа, названные в условии, по порядку первого упоминания."""
    found: list[tuple[str, int, int]] = []
    for form, legs in LEGS_BY_FORM.items():
        # Границы слова обязательны: «ос» — родительный множественного осы,
        # и без \b он находится внутри слова «После».
        match = re.search(rf"\b{form}\b", text)
        if match is not None:
            found.append((form, legs, match.start()))
    return [(form, legs) for form, legs, _ in sorted(found, key=lambda item: item[2])]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


def solve_two_species(first_legs: int, second_legs: int, heads: int, legs: int) -> list[int]:
    """Перебором: сколько существ первого вида даёт нужные головы и ноги."""
    return [
        first for first in range(heads + 1)
        if first * first_legs + (heads - first) * second_legs == legs
    ]


class HeadsAndLegsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["heads_and_legs_two_species"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            species = creatures_in(text)
            self.assertEqual(len(species), 2, f"seed {seed}: {text}")
            heads = int(re.search(rf"вышло (\d+){SPACE}голов", text).group(1))
            legs = int(re.search(rf"и (\d+){SPACE}ног", text).group(1))

            fits = solve_two_species(species[0][1], species[1][1], heads, legs)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_species_differ_in_legs(self) -> None:
        """Виды с одинаковым числом ног сделали бы задачу неразрешимой."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["legs_a"], values["legs_b"], f"seed {seed}")


class CaravanTests(unittest.TestCase):
    TEMPLATE = LIBRARY["caravan_dwarves_and_pack_animals"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Числа читаются по словам «ног» и «голов», а не по обороту вокруг
            # них: формулировка может меняться, арифметика — нет.
            legs = int(re.search(rf"(\d+){SPACE}ног", text).group(1))
            heads = int(re.search(rf"(\d+){SPACE}голов", text).group(1))
            beast_legs = next(
                value for form, value in LEGS_BY_FORM.items()
                if form != "гномов" and f"на {form}" in text
            )

            fits = solve_two_species(2, beast_legs, heads, legs)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_pack_animals_can_actually_carry(self) -> None:
        """Тег pack: поклажу навьючивают на лошадь, а не на комара."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertIn("pack", values["beast"].tags, f"seed {seed}: {values['beast'].lemma}")


class HypnotistTests(unittest.TestCase):
    TEMPLATE = LIBRARY["hypnotist_false_animal_reports"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            species = creatures_in(text)
            self.assertEqual(len(species), 2, f"seed {seed}: {text}")
            claims = re.findall(rf"них (\d+){SPACE}голов\S* и (\d+){SPACE}ног", text)
            self.assertEqual(len(claims), 2, f"seed {seed}: {text}")
            (heads_a, legs_a), (heads_b, legs_b) = [
                (int(head), int(leg)) for head, leg in claims
            ]
            said_legs = int(re.search(rf"вышло (\d+){SPACE}ног", text).group(1))
            said_heads = int(re.search(rf"и (\d+){SPACE}голов\S*\.", text).group(1))

            # Решение с нуля: перебираем поголовье первого вида и проверяем,
            # что оба заявленных итога сходятся. Определитель системы тест
            # не считает — он просто ищет согласованный ответ.
            fits = [
                (first, second)
                for first in range(0, said_heads // max(heads_a, 1) + 1)
                for second in [
                    (said_heads - first * heads_a) // heads_b
                    if (said_heads - first * heads_a) % heads_b == 0 else -1
                ]
                if second >= 0 and first * legs_a + second * legs_b == said_legs
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            first, second = fits[0]
            real = first * species[0][1] + second * species[1][1]
            self.assertEqual(generated["answer"], real, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_reports_are_actually_false(self) -> None:
        """Если бы животные говорили правду, задача теряла бы смысл."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["leg_a"], values["legs_a"], f"seed {seed}")
            self.assertNotEqual(values["leg_b"], values["legs_b"], f"seed {seed}")
            self.assertGreater(values["head_a"], 1, f"seed {seed}")
            self.assertGreater(values["head_b"], 1, f"seed {seed}")


class BugsAndSpidersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["box_of_bugs_and_spiders"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            species = creatures_in(text)
            # Оболочек у задачи две — безличная и с героем, — поэтому счётные
            # числа ищутся по смыслу: «всего N» существ и «N ног».
            total = int(re.search(rf"всего (\d+)", text).group(1))
            legs = int(re.search(rf"(\d+){SPACE}ног", text).group(1))

            fits = solve_two_species(species[0][1], species[1][1], total, legs)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], total - fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class EqualLegsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["equal_legs_two_species"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            species = creatures_in(text)
            total = int(re.search(rf"всего (\d+){SPACE}штук", text).group(1))

            # Решение с нуля: перебираем состав стада и требуем равенства ног.
            fits = [
                total - first for first in range(1, total)
                if first * species[0][1] == (total - first) * species[1][1]
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class BicyclesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["bicycles_two_and_three_wheels"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, wheels = numbers(text)[:2]

            fits = solve_two_species(2, 3, total, wheels)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], total - fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class TreatsSplitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["treats_shared_unique_split"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            per_boy = int(re.search(r"мальчику по (\d+)", text).group(1))
            per_girl = int(re.search(r"девочке по (\d+)", text).group(1))
            total = int(re.search(rf"{SPACE}?(\d+){SPACE}\S+\. Известно", text).group(1))

            # Решение с нуля: перебираем всех гостей. Теория диофантовых
            # уравнений здесь не нужна — важно, что решение ровно одно.
            fits = [
                boys for boys in range(1, total // per_boy + 1)
                for girls in [(total - boys * per_boy) // per_girl]
                if girls >= 1 and boys * per_boy + girls * per_girl == total
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: решений {fits} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class InsectsChainTests(unittest.TestCase):
    TEMPLATE = LIBRARY["insects_in_the_room_chain"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(r"в (\d+)\s+раза больше", text).group(1))
            bee_pairs = int(re.search(rf"влетело (\d+){SPACE}пар", text).group(1))
            gap = int(re.search(rf"на (\d+){SPACE}пар\w* больше", text).group(1))
            diff = int(re.search(r"на (\d+)\s+меньше", text).group(1))

            # Решение с нуля: перебираем все четвёрки, а не разматываем цепочку.
            bees = 2 * bee_pairs
            wasps = 2 * (bee_pairs - gap)
            fits = [
                gnats
                for flies in range(0, bees + wasps + 1)
                for gnats in [flies - diff]
                if gnats >= 0 and flies + gnats == (bees + wasps) // times
                and (bees + wasps) % times == 0
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class ReserveAnimalsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["reserve_predators_and_herbivores"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # «раз» или «раза» — форма согласуется с числом счётным слотом,
            # поэтому тест не вправе ждать одну из них.
            times = int(re.search(rf"в (\d+){SPACE}раза? больше", text).group(1))
            gap = int(re.search(r"на (\d+)\s+больше", text).group(1))
            predators = int(re.search(r"заповеднике (\d+), и это вдвое", text).group(1))

            # Решение с нуля: перебираем поголовье тигров и косуль.
            tigers = [
                count for count in range(1, predators + 1)
                if count + count * times == predators
            ]
            self.assertEqual(len(tigers), 1, f"seed {seed}: {text}")
            herbivores = 2 * predators
            deers = [
                count for count in range(0, herbivores + 1)
                if count + count + gap == herbivores
            ]
            self.assertEqual(len(deers), 1, f"seed {seed}: {text}")
            expected = deers[0] + tigers[0] * times
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
