"""Независимо проверяет первый формульный тип в прежде пустых модулях."""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


def numbers(text: str) -> list[int]:
    """Вернуть все целые числа, напечатанные в условии."""
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    """Проверить базовые свойства готового текста задачи."""
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class MissingModulesTests(unittest.TestCase):
    """Решает новые задачи по напечатанным условиям, не по derived_values."""

    def generated(self, template_id: str, seed: int) -> dict:
        """Собрать один вариант указанного шаблона."""
        return generate_active_template(LIBRARY[template_id], random.Random(seed))

    def test_factorial_value(self) -> None:
        """Перемножает множители факториала по одному."""
        for seed in SEEDS:
            generated = self.generated("factorial_value", seed)
            n = numbers(generated["rendered_problem"])[-1]
            product = 1
            for factor in range(1, n + 1):
                product *= factor
            self.assertEqual(generated["answer"], product, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_count_odd_open_interval(self) -> None:
        """Перебирает открытый промежуток и считает нечётные числа."""
        for seed in SEEDS:
            generated = self.generated("count_odd_open_interval", seed)
            low, high = numbers(generated["rendered_problem"])
            expected = sum(value % 2 for value in range(low + 1, high))
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_balls_guaranteed_two_black(self) -> None:
        """Проверяет худший случай: сперва вынуты все белые шары."""
        for seed in SEEDS:
            generated = self.generated("balls_guaranteed_two_black", seed)
            white, black = numbers(generated["rendered_problem"])
            expected = white + 2
            self.assertGreaterEqual(black, 2, f"seed {seed}")
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            self.assertLessEqual(expected, white + black, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_uniform_numbers_parity_sum(self) -> None:
        """Проверяет цифры списка, а не доверяет готовому ответу JSON-пакета."""
        for seed in SEEDS:
            generated = self.generated("uniform_numbers_parity_sum", seed)
            values = numbers(generated["rendered_problem"])

            def uniform(value: int) -> bool:
                digits = [int(digit) for digit in str(value)]
                return any(left % 2 == right % 2 for left, right in zip(digits, digits[1:]))

            predicate = generated["parameters"]["predicate_id"]
            if predicate == "has_same_parity_adjacent_pair":
                expected = sum(value for value in values if uniform(value))
            elif predicate == "all_adjacent_pairs_opposite_parity":
                expected = sum(value for value in values if not uniform(value))
            else:
                self.fail(f"Неизвестный предикат: {predicate}")
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_square_area_from_perimeter(self) -> None:
        """Восстанавливает сторону по периметру и считает площадь."""
        for seed in SEEDS:
            generated = self.generated("square_area_from_perimeter", seed)
            perimeter = numbers(generated["rendered_problem"])[0]
            self.assertEqual(perimeter % 4, 0, f"seed {seed}")
            self.assertEqual(generated["answer"], (perimeter // 4) ** 2, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_grid_square_count(self) -> None:
        """Складывает квадраты каждого размера вместо готовой формулы."""
        for seed in SEEDS:
            generated = self.generated("grid_square_count", seed)
            side = numbers(generated["rendered_problem"])[0]
            expected = sum((side - size + 1) ** 2 for size in range(1, side + 1))
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_cube_paint_surface_scaling(self) -> None:
        """Сравнивает площади шести граней двух кубов."""
        for seed in SEEDS:
            generated = self.generated("cube_paint_surface_scaling", seed)
            _, base_paint, side = numbers(generated["rendered_problem"])
            expected = base_paint * (6 * side * side) // 6
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_line_uniform_points_distance(self) -> None:
        """Считает промежутки между первой и последней точками."""
        for seed in SEEDS:
            generated = self.generated("line_uniform_points_distance", seed)
            _, points, step = numbers(generated["rendered_problem"])
            self.assertEqual(generated["answer"], (points - 1) * step, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_container_weight_with_quarter(self) -> None:
        """Решает уравнение массы обратной подстановкой."""
        for seed in SEEDS:
            generated = self.generated("container_weight_with_quarter", seed)
            known = numbers(generated["rendered_problem"])[0]
            self.assertEqual((known * 4) % 3, 0, f"seed {seed}")
            expected = known * 4 // 3
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_wrong_product_correction(self) -> None:
        """Находит два совпадающих частных и пересчитывает третье произведение."""
        for seed in SEEDS:
            generated = self.generated("wrong_product_correction", seed)
            values = numbers(generated["rendered_problem"])
            factors = values[0::2]
            reports = values[1::2]
            quotients = [report // factor for factor, report in zip(factors, reports) if report % factor == 0]
            number, occurrences = Counter(quotients).most_common(1)[0]
            self.assertEqual(occurrences, 2, f"seed {seed}: {generated['rendered_problem']}")
            wrong_index = next(index for index, (factor, report) in enumerate(zip(factors, reports))
                               if report != factor * number)
            self.assertEqual(generated["answer"], factors[wrong_index] * number, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)


if __name__ == "__main__":
    unittest.main()
