"""Независимая проверка темы «Прямоугольники: стороны, площадь, периметр».

Пять шаблонов батча: диофантово условие «периметр больше площади», кайма
вокруг квадрата, разрез и склейка до квадрата, смешанные единицы площади
и квадрат с тем же периметром. Каталог с оригинальными номерами задач —
`docs/NEXT_TEMPLATE_BATCHES.md`.

Решатели устроены иначе, чем шаблоны. Там, где шаблон печатает готовый
ответ по формуле, тест перебирает все возможные стороны и требует, чтобы
условию отвечал ровно один прямоугольник: в трёх задачах этой темы
источник просит «приведите пример», и вся ценность ключа в том, что
пример на самом деле единственный. Если бы их было два, ребёнок с верным
вторым ответом получил бы крестик.
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

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(30)


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class PerimeterExceedsAreaTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_perimeter_exceeds_area"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            gap = numbers(text)[0]

            # Решение с нуля: перебираем меньшую сторону и находим большую
            # из уравнения. Формулой шаблона не пользуемся вовсе.
            fits = []
            for short in range(1, gap + 3):
                # 2(x + y) − xy = gap  =>  y(2 − x) = gap − 2x
                if short == 2:
                    continue
                numerator, denominator = gap - 2 * short, 2 - short
                if numerator % denominator:
                    continue
                long = numerator // denominator
                if long >= short:
                    fits.append((short, long))
            self.assertEqual(len(fits), 1, f"seed {seed}: примеров не один — {fits}")
            self.assertEqual(list(generated["answer"]), list(fits[0]), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_answer_really_satisfies_the_condition(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            gap = numbers(generated["rendered_problem"])[0]
            short, long = generated["answer"]
            self.assertEqual(2 * (short + long) - short * long, gap, f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 39: разница 2023 -> стороны 1 и 2021."""
        self.assertEqual(2 * (1 + 2021) - 1 * 2021, 2023)


class SquareAreaGrowthTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_side_from_area_growth"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            grow, grow_area = numbers(text)[:2]

            # Перебираем сторону и сравниваем площади двух квадратов честно,
            # не раскрывая разность квадратов.
            fits = [
                side for side in range(1, grow_area + 1)
                if (side + grow) ** 2 - side ** 2 == grow_area
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 183: прирост 15 при шаге 1 -> сторона 7."""
        self.assertEqual((7 + 1) ** 2 - 7 ** 2, 15)


class CutAndGlueToSquareTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_cut_and_glue_to_square"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            cut_perimeter, glue_perimeter = numbers(text)[:2]

            # Решение с нуля: перебираем обе стороны и проверяем периметры
            # отрезаемой и приклеиваемой полос прямым счётом.
            fits = []
            for long in range(2, glue_perimeter):
                for short in range(1, long):
                    strip = long - short
                    if 2 * (strip + short) != cut_perimeter:
                        continue
                    if 2 * (strip + long) != glue_perimeter:
                        continue
                    fits.append((short, long))
            self.assertEqual(len(fits), 1, f"seed {seed}: {text} — {fits}")
            self.assertEqual(list(generated["answer"]), list(fits[0]), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 453: периметры 420 и 660 -> стороны 90 и 210."""
        short, long = 90, 210
        self.assertEqual(2 * ((long - short) + short), 420)
        self.assertEqual(2 * ((long - short) + long), 660)


class MixedUnitsAreaTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_side_from_area_mixed_units"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            length, area_small = numbers(text)[:2]

            # Единицы переводятся явно: в квадратном метре сто квадратных
            # дециметров. Это и есть содержание задачи.
            self.assertEqual(area_small % 100, 0, f"seed {seed}: {text}")
            area_big = area_small // 100
            self.assertEqual(area_big % length, 0, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], area_big // length, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_naive_division_gives_a_different_number(self) -> None:
        """Кто поделил, не переведя единицы, обязан получить не тот ответ."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            length, area_small = numbers(generated["rendered_problem"])[:2]
            self.assertNotEqual(generated["answer"], area_small // length, f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 671: 7500 дм² при длине 15 м -> ширина 5 м."""
        self.assertEqual(7500 // 100 // 15, 5)


class SquareSamePerimeterTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_with_same_perimeter"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            width, length = numbers(text)[:2]

            perimeter = 2 * (width + length)
            self.assertEqual(perimeter % 4, 0, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], perimeter // 4, f"seed {seed}: {text}")
            self.assertNotEqual(width, length, f"seed {seed}: прямоугольник выродился в квадрат")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 670: стороны 6 и 12 -> сторона квадрата 9."""
        self.assertEqual(2 * (6 + 12) // 4, 9)


if __name__ == "__main__":
    unittest.main()
