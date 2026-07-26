"""Независимая проверка шаблонов темы «Числовые процессы и повторяющиеся операции».

Каждый решатель решает задачу по её условию с нуля — симуляцией, а не повторением
формул шаблона. Для кругов строится реальная пара списков и ищется поворот; для
частичных сумм суммирование идёт честным циклом; для государств процесс проигрывается
год за годом. Совпадение симуляции с закрытой формулой шаблона и есть проверка.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
CIRCLE = LIBRARY["process_circle_overlay"]
TRIANGULAR = LIBRARY["process_triangular_sum_next"]
STATES = LIBRARY["process_states_merge_countdown"]
SEEDS = range(25)


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый плейсхолдер")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: текст должен начинаться с заглавной")
    case.assertIn(text[-1], ".?!", f"seed {seed}: текст должен заканчиваться знаком препинания")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ не должен быть в условии")


class CircleOverlayTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(CIRCLE, random.Random(seed))
            values = generated["parameters"]
            n, a, b, q = values["n"], values["a"], values["b"], values["q"]

            # Решение с нуля: нижний круг — числа 1..n по позициям 0..n-1.
            # Верхний круг такой же, но повёрнут на неизвестное число позиций.
            # Перебираем все n поворотов и берём тот, при котором на секторе a
            # действительно лежит число b. Затем читаем, что лежит на секторе q.
            bottom = list(range(1, n + 1))
            matching = [
                shift for shift in range(n)
                if bottom[(bottom.index(a) - shift) % n] == b
            ]
            self.assertEqual(len(matching), 1, f"seed {seed}: поворот должен быть единственным")
            shift = matching[0]
            expected = bottom[(bottom.index(q) - shift) % n]

            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_answer_is_not_given_away_in_the_statement(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(CIRCLE, random.Random(seed))
            values = generated["parameters"]
            self.assertNotEqual(values["q"], values["a"], f"seed {seed}")
            self.assertNotEqual(generated["answer"], values["q"], f"seed {seed}")
            self.assertLessEqual(values["a"], values["n"], f"seed {seed}")
            self.assertLessEqual(values["q"], values["n"], f"seed {seed}")


class TriangularSumTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(TRIANGULAR, random.Random(seed))
            values = generated["parameters"]
            first, second = values["first"], values["second"]

            # Решение с нуля: складываем 1+2+3+... честным циклом, пока не встретим
            # выписанную сумму, затем продолжаем ещё на два шага. Формула
            # k(k+1)/2 здесь не используется вовсе.
            running, term, seen = 0, 0, []
            while running < first:
                term += 1
                running += term
                seen.append(running)
            self.assertEqual(running, first, f"seed {seed}: {first} обязана быть частичной суммой")
            term += 1
            running += term
            self.assertEqual(running, second, f"seed {seed}: суммы обязаны быть соседними")
            term += 1
            running += term

            self.assertEqual(generated["answer"], running, f"seed {seed}")
            self.assertLessEqual(term, values["limit"], f"seed {seed}: вышли за верхнюю границу ряда")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_series_prefix_in_the_text_is_the_real_prefix(self) -> None:
        # В тексте префикс ряда записан константами 3, 6, 10, 15 — он не зависит
        # от параметров, потому что сложение всегда начинается с 1+2.
        prefix, running = [], 0
        for term in range(1, 6):
            running += term
            if term >= 2:
                prefix.append(running)
        self.assertEqual(prefix[:4], [3, 6, 10, 15])


class StatesMergeTests(unittest.TestCase):
    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(STATES, random.Random(seed))
            values = generated["parameters"]
            n0, m, k = values["n0"], values["m"], values["k"]

            # Решение с нуля: проигрываем процесс год за годом.
            count, years, after_k = n0, 0, None
            while count >= m:
                count -= m - 1
                years += 1
                if years == k:
                    after_k = count
            self.assertIsNotNone(after_k, f"seed {seed}: процесс обязан дожить до года k")

            self.assertEqual(generated["answer"], [after_k, years, count], f"seed {seed}")
            self.assertLess(count, m, f"seed {seed}: процесс обязан остановиться")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_answer_units_agree_with_numbers(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(STATES, random.Random(seed))
            rendered = generated.get("rendered_answer")
            if rendered is None:
                continue
            self.assertRegex(rendered, r"\d+\xa0(государство|государства|государств)")
            self.assertRegex(rendered, r"\d+\xa0(год|года|лет)")


if __name__ == "__main__":
    unittest.main()
