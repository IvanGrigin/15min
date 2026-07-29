"""Независимая проверка тем «Уравнения», «Арифметика» и «Доли и проценты».

Уравнения проверяются подстановкой: тест берёт числа из условия, собирает
левую часть заново по порядку действий и сравнивает с правой. Это сильнее
пересчёта по формуле — так проверяется и сам текст, и ответ.

Арифметические суммы складываются по одному члену: приёмы вроде вынесения
общего множителя тест не применяет, в этом и смысл проверки.
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
SEEDS = range(25)


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class EquationSubstitutionTests(unittest.TestCase):
    """Каждое уравнение проверяется подстановкой ответа в левую часть."""

    def check(self, template_id: str, build, seed_range=SEEDS) -> None:
        template = LIBRARY[template_id]
        for seed in seed_range:
            generated = generate_active_template(template, random.Random(seed))
            text = generated["rendered_problem"]
            values = numbers(text)
            answer = generated["answer"]
            left, right = build(values, answer)
            self.assertEqual(
                left, right,
                f"{template_id}, seed {seed}: подстановка не сходится — {text}",
            )
            assert_text_is_clean(self, text, seed)

    def test_multiply_add_divide(self) -> None:
        # left − (x*mul + add) : div = right
        self.check(
            "equation_multiply_add_divide",
            lambda v, x: (v[0] - (x * v[1] + v[2]) // v[3], v[4]),
        )

    def test_divide_by_unknown(self) -> None:
        # left + (inner_left − dividend : x) * mul = right
        self.check(
            "equation_divide_by_unknown",
            lambda v, x: (v[0] + (v[1] - v[2] // x) * v[3], v[4]),
        )

    def test_two_level_nesting(self) -> None:
        # ((left − x) : div1 + add) : div2 = right
        self.check(
            "equation_two_level_nesting",
            lambda v, x: (((v[0] - x) // v[1] + v[2]) // v[3], v[4]),
        )

    def test_sum_divide_subtract(self) -> None:
        # (base + mul*x) : div − sub = right
        self.check(
            "equation_sum_divide_subtract",
            lambda v, x: ((v[0] + v[1] * x) // v[2] - v[3], v[4]),
        )

    def test_subtract_bracket_product(self) -> None:
        # left − (base − x*mul) * factor − sub = right
        self.check(
            "equation_subtract_bracket_product",
            lambda v, x: (v[0] - (v[1] - x * v[2]) * v[3] - v[4], v[5]),
        )

    def test_divisions_are_exact(self) -> None:
        """Ни одно деление в цепочке не должно давать остатка."""
        for template_id, check in (
            ("equation_multiply_add_divide",
             lambda p: (p["x"] * p["mul"] + p["add"]) % p["div"]),
            ("equation_divide_by_unknown", lambda p: p["dividend"] % p["x"]),
            ("equation_two_level_nesting", lambda p: (p["left"] - p["x"]) % p["div1"]),
            ("equation_sum_divide_subtract",
             lambda p: (p["base"] + p["mul"] * p["x"]) % p["div"]),
        ):
            for seed in SEEDS:
                values = generate_active_template(
                    LIBRARY[template_id], random.Random(seed))["parameters"]
                self.assertEqual(check(values), 0, f"{template_id}, seed {seed}")


class CommonFactorTests(unittest.TestCase):
    TEMPLATE = LIBRARY["common_factor_two_products"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, common, second, again = numbers(text)

            self.assertEqual(common, again, f"seed {seed}: множитель не общий — {text}")
            # Считаем в лоб, без вынесения множителя — в этом и проверка.
            self.assertEqual(
                generated["answer"], first * common + second * common,
                f"seed {seed}: {text}",
            )
            assert_text_is_clean(self, text, seed)

    def test_sum_of_multipliers_is_round(self) -> None:
        """Иначе приём не даёт выигрыша и задача теряет смысл."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertEqual((values["a"] + values["b"]) % 10, 0, f"seed {seed}")


class NearMultipliersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_near_multipliers"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, first, base, second, high, third = numbers(text)

            self.assertEqual(base - low, 1, f"seed {seed}: множимые не соседние — {text}")
            self.assertEqual(high - base, 1, f"seed {seed}: множимые не соседние — {text}")
            # Прямое умножение, без вынесения общего множимого.
            self.assertEqual(
                generated["answer"], low * first + base * second + high * third,
                f"seed {seed}: {text}",
            )
            assert_text_is_clean(self, text, seed)


class SeriesSumTests(unittest.TestCase):
    TEMPLATE = LIBRARY["arithmetic_series_sum_plain"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start, second, third, last = numbers(text)
            step = second - start

            self.assertEqual(third - second, step, f"seed {seed}: разность непостоянна")
            # Складываем член за членом, без формулы суммы прогрессии.
            total = 0
            value = start
            while value <= last:
                total += value
                value += step
            self.assertEqual(value - step, last, f"seed {seed}: последний член не в ряду")
            self.assertEqual(generated["answer"], total, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class AlternatingSeriesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["alternating_series_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            a1, a2, a3, a4, before_last, last = numbers(text)
            step = a2 - a1

            for previous, current in ((a2, a3), (a3, a4)):
                self.assertEqual(current - previous, step, f"seed {seed}: шаг непостоянен")
            self.assertEqual(last - before_last, step, f"seed {seed}: хвост не в ряду")

            # Проходим ряд по одному члену, чередуя знаки. Группировку в пары,
            # на которой держится формула шаблона, тест не использует.
            total = 0
            sign = 1
            value = a1
            while value <= last:
                total += sign * value
                sign = -sign
                value += step
            self.assertEqual(sign, -1, f"seed {seed}: ряд оборвался на минусе")
            self.assertEqual(generated["answer"], total, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class PlatesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["nuts_on_distinct_plates"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = numbers(text)[0]

            # Решение с нуля: наращиваем тарелки, кладя на каждую минимум
            # на один орех больше предыдущей, пока хватает орехов.
            plates = 0
            used = 0
            while used + plates + 1 <= count:
                plates += 1
                used += plates
            self.assertEqual(generated["answer"], plates, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class ThreeSharesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_shares_candies"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = numbers(text)[0]
            times = int(re.search(r"в (\d+)\s+раза? больше", text).group(1))

            # Решение с нуля: перебираем все три доли и проверяем оба условия
            # буквально, как они написаны в тексте.
            fits = [
                first
                for first in range(1, total)
                for second in range(1, total - first)
                for third in [total - first - second]
                if third > 0 and second + first == third
                and third + first == times * second
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class DoublingTests(unittest.TestCase):
    TEMPLATE = LIBRARY["doubling_reaches_half"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = numbers(text)[0]

            # Решение с нуля: наполняем ёмкость шаг за шагом и смотрим,
            # на каком шаге пройдена половина.
            volume = 1
            full = 2 ** total
            step = 0
            while volume < full // 2:
                volume *= 2
                step += 1
            self.assertEqual(generated["answer"], step, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class ThreeBoxesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_boxes_mutual_difference"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first_gap, second_gap = numbers(text)[:2]

            # Решение с нуля: перебираем общий вес и содержимое ящиков.
            # Ответ обязан не зависеть от общего веса — это и проверяем.
            answers = set()
            # Шаг единица: чётность общего веса определяется разностями,
            # а они могут быть и нечётными.
            for total in range(first_gap + second_gap, first_gap + second_gap + 60):
                if (total - first_gap) % 2 or (total - second_gap) % 2:
                    continue
                first = (total - first_gap) // 2
                second = (total - second_gap) // 2
                third = total - first - second
                if first > 0 and second > 0 and third > 0:
                    answers.add(third)
            self.assertEqual(len(answers), 1, f"seed {seed}: ответ зависит от веса — {text}")
            self.assertEqual(generated["answer"], answers.pop(), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class NewlyMigratedModulesTests(unittest.TestCase):
    """Независимо проверяет первые типы из ещё не подключённых модулей."""

    def test_sum_and_difference_system(self) -> None:
        """Решает напечатанную систему сложением и вычитанием уравнений."""
        template = LIBRARY["system_sum_and_difference"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            total, difference = numbers(generated["rendered_problem"])
            x, y = generated["answer"]
            self.assertEqual(x + y, total, f"seed {seed}")
            self.assertEqual(x - y, difference, f"seed {seed}")
            self.assertEqual(x, (total + difference) // 2, f"seed {seed}")
            self.assertEqual(y, (total - difference) // 2, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_symmetric_products_difference(self) -> None:
        """Вычисляет разность непосредственно из напечатанных множителей."""
        template = LIBRARY["symmetric_products_difference"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            center, step, center_again, step_again, first_center, second_center = numbers(
                generated["rendered_problem"]
            )
            self.assertEqual((center, step), (center_again, step_again), f"seed {seed}")
            self.assertEqual((center, first_center, second_center), (center, center, center), f"seed {seed}")
            direct = abs((center - step) * (center + step) - center * center)
            self.assertEqual(generated["answer"], direct, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_two_linear_equations_system(self) -> None:
        """Решает общую систему правилом Крамера по напечатанным коэффициентам."""
        template = LIBRARY["system_two_linear_equations"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            a, b, first, c, d, second = numbers(generated["rendered_problem"])
            determinant = a * d - b * c
            self.assertNotEqual(determinant, 0, f"seed {seed}")
            expected_x = (first * d - b * second) // determinant
            expected_y = (a * second - first * c) // determinant
            self.assertEqual(generated["answer"], [expected_x, expected_y], f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_crossed_products_difference(self) -> None:
        """Вычитает оба напечатанных произведения напрямую."""
        template = LIBRARY["crossed_products_difference"]
        for seed in SEEDS:
            generated = generate_active_template(template, random.Random(seed))
            left_base, _, right_base, left_again, right_again, _ = numbers(
                generated["rendered_problem"]
            )
            self.assertEqual((left_base, right_base), (left_again, right_again), f"seed {seed}")
            expected = abs((left_base + 1) * right_base - left_base * (right_base + 1))
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)


if __name__ == "__main__":
    unittest.main()
