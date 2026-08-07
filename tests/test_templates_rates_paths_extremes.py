"""Независимая проверка групп А, Б, Д и И каталога приёмов.

Пять шаблонов: система на производительности, банки с равным содержимым,
доля пути при возврате за забытой вещью, крайний случай при фиксированной
сумме баллов и отношение денег к цене мороженого. Плюс ход короля в обход
аварии — единственный, где формулу подтверждает полный перебор.

Решатели устроены иначе, чем шаблоны. Производительности тест находит
перебором обоих времён, а не вычитанием уравнений; банки — перебором
объёма; доля пути — прямым проигрыванием обоих исходов; крайние случаи —
перебором всех допустимых наборов оценок; мороженое — перебором цены
в целых копейках. Ход жука проверяется поиском в ширину на уменьшенном
поле: формула обязана давать тот же прирост, что и настоящий обход.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import deque
from fractions import Fraction
from itertools import combinations_with_replacement
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


class MixedRatesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["mixed_workers_rate_system"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fast_a, slow_a, time_one, fast_b, slow_b, time_two = numbers(text)[:6]

            # Решение с нуля: перебираем оба времени в одиночку и требуем,
            # чтобы обе смеси сошлись. Вычитанием уравнений тест не пользуется.
            fits = []
            for fast in range(10, 400):
                for slow in range(10, 800):
                    if Fraction(fast_a, fast) + Fraction(slow_a, slow) != Fraction(1, time_one):
                        continue
                    if Fraction(fast_b, fast) + Fraction(slow_b, slow) != Fraction(1, time_two):
                        continue
                    fits.append((fast, slow))
            self.assertEqual(len(fits), 1, f"seed {seed}: {text} — {fits[:3]}")
            fast, slow = fits[0]
            # Какую группу спрашивают, видно по слову перед существительным;
            # сами формы слов берём у шаблона, а числа — только из текста.
            asked = re.search(r"одна (\w+) \w+ съест", text).group(1)
            slow_word = generated["parameters"]["slow_word_one"]
            expected = slow if asked == slow_word else fast
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_only_the_fast_group_changes(self) -> None:
        """Иначе вычитание не убирает медленных и задача становится другой."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertEqual(values["slow_a"], values["slow_b"], f"seed {seed}")
            self.assertGreater(values["fast_b"], values["fast_a"], f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 383: 1 и 2 за 60 мин, 4 и 2 за 20 -> 90 минут."""
        self.assertEqual(Fraction(1, 90) * 1 + Fraction(1, 360) * 2, Fraction(1, 60))
        self.assertEqual(Fraction(1, 90) * 4 + Fraction(1, 360) * 2, Fraction(1, 20))


class EqualJarsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["equal_jars_two_gifts"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            big_grams, times, gap = numbers(text)[:3]
            self.assertEqual(big_grams % times, 0, f"seed {seed}: {text}")
            small_grams = big_grams // times

            # Перебираем объём банки и требуем, чтобы оба количества делились
            # нацело и разность банок совпала с условием.
            fits = [
                size for size in range(1, big_grams + 1)
                if big_grams % size == 0 and small_grams % size == 0
                and big_grams // size - small_grams // size == gap
            ]
            self.assertTrue(fits, f"seed {seed}: {text}")
            size = max(fits)
            if "помещается в одну банку" in text:
                expected = size
            elif "вместе" in text:
                expected = big_grams // size + small_grams // size
            else:
                expected = small_grams // size
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 157: 1050 г, в 5 раз меньше, разница 12 банок."""
        self.assertEqual((1050 - 1050 // 5) // 12, 70)


class ForgottenItemTests(unittest.TestCase):
    TEMPLATE = LIBRARY["path_share_forgotten_item"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            trip, early, late = numbers(text)[:3]

            # Проигрываем оба исхода на общей шкале: ищем момент, когда
            # обе фразы условия становятся верными одновременно.
            fits = []
            for walked in range(1, trip):
                for bell in range(1, 200):
                    if trip - walked != bell - early:
                        continue
                    if walked + trip != bell + late:
                        continue
                    fits.append((walked, bell))
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            walked, bell = fits[0]
            expected = bell if "осталось до звонка" in text else walked
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 1570: дорога 20, раньше на 3, опоздание 7 -> 5 минут."""
        self.assertEqual((7 + 3) // 2, 5)
        self.assertEqual(Fraction(5, 20), Fraction(1, 4))


class BestScoresTests(unittest.TestCase):
    TEMPLATE = LIBRARY["best_scores_minimum_total"]

    KEEP = {"три лучшие": 3, "четыре лучшие": 4, "пять лучших": 5, "шесть лучших": 6}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            keep = next(value for word, value in self.KEEP.items() if word in text)
            max_score, works, total = numbers(text)[1], numbers(text)[2], numbers(text)[3]
            self.assertEqual(works, keep + 1, f"seed {seed}: {text}")

            # Полный перебор наборов оценок: они невелики, и это честнее
            # любых рассуждений о крайнем случае.
            best, worst, dropped_best = None, None, None
            for scores in combinations_with_replacement(range(1, max_score + 1), works):
                if sum(scores) != total:
                    continue
                kept = sum(sorted(scores)[1:])
                best = kept if best is None else min(best, kept)
                worst = kept if worst is None else max(worst, kept)
                if best == kept:
                    dropped_best = min(scores)
            self.assertIsNotNone(best, f"seed {seed}: набора не существует — {text}")

            if "наибольший результат" in text:
                expected = worst
            elif "отброшенная работа" in text:
                expected = dropped_best
            else:
                expected = best
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 374: 5 работ, сумма 72, до 20 баллов -> 58."""
        best = min(
            sum(sorted(scores)[1:])
            for scores in combinations_with_replacement(range(1, 21), 5)
            if sum(scores) == 72
        )
        self.assertEqual(best, 58)


class IceCreamTests(unittest.TestCase):
    TEMPLATE = LIBRARY["ice_cream_shortfall_multiple"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first_times, first_count, second_count = numbers(text)[:3]

            # Перебираем цену и деньги в целых единицах: отношение от цены
            # не зависит, и совпадение на всех ценах это подтверждает.
            answers = set()
            for price in range(4, 60):
                for money in range(price, 2 * price):
                    short = 2 * price - money
                    if money + first_times * short != first_count * price:
                        continue
                    need = second_count * price - money
                    if need % short:
                        continue
                    answers.add(need // short)
            self.assertEqual(len(answers), 1, f"seed {seed}: {text} — {answers}")
            self.assertEqual(generated["answer"], answers.pop(), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 472: впятеро больше нехватки -> три мороженых, ответ 9."""
        price, money = 4, 7
        short = 2 * price - money
        self.assertEqual(money + 5 * short, 3 * price)
        self.assertEqual((4 * price - money) // short, 9)


class BugAroundDamageTests(unittest.TestCase):
    TEMPLATE = LIBRARY["bug_king_moves_around_damage"]

    @staticmethod
    def king_steps(side: int, width: int, height: int) -> int:
        """Настоящий обход поиском в ширину — без всякой формулы."""
        centre = side // 2
        x0, x1 = centre - width // 2, centre + width // 2
        y0, y1 = centre - height // 2, centre + height // 2
        dist = {(0, 0): 0}
        queue = deque([(0, 0)])
        while queue:
            x, y = queue.popleft()
            if (x, y) == (side - 1, side - 1):
                return dist[(x, y)]
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < side and 0 <= ny < side):
                        continue
                    if x0 <= nx <= x1 and y0 <= ny <= y1:
                        continue
                    if (nx, ny) in dist:
                        continue
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    queue.append((nx, ny))
        raise AssertionError("школа недостижима")

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            values = generated["parameters"]
            width, height = values["damage_width"], values["damage_height"]
            side = values["side"]

            # Настоящий квадрат — тысячи клеток, перебор там невозможен.
            # Прирост пути от стороны не зависит, поэтому обход считается
            # на уменьшенном поле с той же аварией.
            small = max(width, height) * 2 + 5
            small += 1 - small % 2
            detour = self.king_steps(small, width, height) - (small - 1)
            expected = (side - 1) + detour
            if "На сколько шагов длиннее" in text:
                expected = detour
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_single_cell_damage_costs_one_step(self) -> None:
        """Это сказано в самом условии и служит ключом к задаче."""
        for side in (11, 15, 21):
            self.assertEqual(self.king_steps(side, 1, 1), side)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 64: квадрат 2025, авария 5 × 9 -> 2031 шаг."""
        detour = self.king_steps(23, 5, 9) - 22
        self.assertEqual(detour, 7)
        self.assertEqual(2024 + detour, 2031)


if __name__ == "__main__":
    unittest.main()
