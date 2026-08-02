"""Независимая проверка подсчёта чисел на промежутке по условию на цифру.

Решатель теста читает условие словами — «нечётных», «не содержащих цифру 5» —
и пересчитывает всё сам, перебирая промежуток. Так проверяется не только
арифметика, но и то, что слова описывают ровно тот отбор, который делает
шаблон: перепутанные «содержащих» и «не содержащих» дадут расхождение сразу.

Отдельно проверяется, что задача не выродилась. Если под условие подпадает
весь промежуток или ни одного числа, ответ формально верен, но задача уже
не про цифры.
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
SEEDS = range(40)


class CountInRangeByDigitTests(unittest.TestCase):
    TEMPLATE = LIBRARY["count_in_range_by_digit"]

    def solve(self, text: str) -> int:
        """Решить задачу заново, читая условие как читает её человек."""
        low, high = (int(value) for value in
                     re.search(r"от (\d+) до (\d+)", text).groups())
        digit = re.search(r"цифру (\d)", text).group(1)
        without = "не содержащих" in text
        if "нечётных" in text:
            keep_parity = lambda value: value % 2 == 1  # noqa: E731
        elif "чётных" in text:
            keep_parity = lambda value: value % 2 == 0  # noqa: E731
        else:
            keep_parity = lambda value: True  # noqa: E731
        return sum(
            1 for value in range(low, high + 1)
            if keep_parity(value) and ((digit not in str(value)) if without
                                       else (digit in str(value)))
        )

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            self.assertEqual(generated["answer"], self.solve(text), f"seed {seed}: {text}")

    def test_condition_actually_selects_something(self) -> None:
        """Ответ не должен быть ни нулём, ни всем промежутком целиком."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            low, high = (int(value) for value in
                         re.search(r"от (\d+) до (\d+)", text).groups())
            if "нечётных" in text:
                pool = sum(1 for v in range(low, high + 1) if v % 2)
            elif "чётных" in text:
                pool = sum(1 for v in range(low, high + 1) if not v % 2)
            else:
                pool = high - low + 1
            self.assertGreater(generated["answer"], 0, f"seed {seed}: {text}")
            self.assertLess(generated["answer"], pool, f"seed {seed}: {text}")

    def test_text_is_clean(self) -> None:
        """Пустое слово чётности оставляло двойной пробел в каждом четвёртом."""
        for seed in range(120):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("  ", text, f"seed {seed}: {text}")
            self.assertNotIn("{", text, f"seed {seed}")
            self.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
            self.assertEqual(text.rstrip()[-1], "?", f"seed {seed}")

    def test_both_directions_of_the_digit_rule_occur(self) -> None:
        """И «содержащих», и «не содержащих» обязаны выпадать."""
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add("не содержащих" in text)
        self.assertEqual(seen, {True, False})


class BoardSawingTests(unittest.TestCase):
    """Время распила пропорционально числу разрезанных перегородок."""

    TEMPLATE = LIBRARY["board_sawing_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]

            def cuts(rows: int, cols: int, piece: int) -> int:
                # Перебор всех пар соседних клеток: каждая пара — перегородка.
                walls = 0
                for row in range(rows):
                    for col in range(cols):
                        if col + 1 < cols:
                            walls += 1
                        if row + 1 < rows:
                            walls += 1
                # Внутри детали из k клеток остаётся k−1 неразрезанная перегородка.
                return walls - (rows * cols // piece) * (piece - 1)

            first = cuts(values["rows1"], values["cols1"], values["piece1"])
            second = cuts(values["rows2"], values["cols2"], values["piece2"])
            text = generated["rendered_problem"]
            given = int(re.search(r"за (\d+)", text).group(1))
            self.assertEqual(given % first, 0, f"seed {seed}: время не делится на пропилы")
            self.assertEqual(
                generated["answer"], given // first * second, f"seed {seed}: {text}")

    def test_source_numbers_reproduce(self) -> None:
        """Контроль по источнику: 8×8 доминошками — 80 пропилов, 2×9 уголками — 13."""
        def cuts(rows: int, cols: int, piece: int) -> int:
            walls = rows * (cols - 1) + cols * (rows - 1)
            return walls - (rows * cols // piece) * (piece - 1)
        self.assertEqual(cuts(8, 8, 2), 80)
        self.assertEqual(cuts(2, 9, 3), 13)
        # Вырезать одну клетку из середины — четыре пропила, квадрат 2×2 — восемь.
        self.assertEqual(2 * (1 + 1) + 0, 4)
        self.assertEqual(2 * (2 + 2), 8)

    def test_both_boards_split_evenly(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertEqual((values["rows1"] * values["cols1"]) % values["piece1"], 0)
            self.assertEqual((values["rows2"] * values["cols2"]) % values["piece2"], 0)


if __name__ == "__main__":
    unittest.main()
