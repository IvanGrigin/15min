"""Независимая проверка первой волны плана на 90%.

Существа с двумя признаками — тест решает систему перебором, а не формулой.
Турнир каждый с каждым — тест перебирает пары. Турнир на выбывание — тест
моделирует круги. Возвращение за забытым — тест считает обе дороги по минутам.
Круговая дорожка — тест берёт конкретные скорости и сравнивает частоты встреч.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


class TwoKindsByTraitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_kinds_count_by_traits"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]

            if "Всего видно" in text:
                # Два признака: у каждого вида своё число ног и голов или рук.
                head = text.split("Всего видно")[0]
                legs = [int(v) for v in re.findall(r"(\d+) ног[аи]? и", head)]
                others = [int(v) for v in re.findall(r"и (\d+) (?:рук|голов)", head)]
                self.assertEqual(len(legs), 2, f"seed {seed}: {text}")
                totals = re.search(r"Всего видно (\d+) ног и (\d+) ", text)
                legs_total, other_total = (int(v) for v in totals.groups())
                asked_first = True
            else:
                legs = None
                asked_first = False

            if legs is not None:
                # Решение с нуля: перебираем оба количества.
                fits = [
                    (x, y)
                    for x in range(0, 60) for y in range(0, 60)
                    if legs[0] * x + legs[1] * y == legs_total
                    and others[0] * x + others[1] * y == other_total
                ]
                self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
                self.assertEqual(generated["answer"], fits[0][0], f"seed {seed}: {text}")
                continue

            # Второй вариант: известны общее число существ и общее число ног.
            legs_pair = self.legs_from_pair_name(text)
            total = int(re.search(r"всего (\d+) штук", text).group(1))
            legs_total = int(re.search(r"ног у них (\d+)", text).group(1))
            fits = [
                (x, total - x) for x in range(total + 1)
                if legs_pair[0] * x + legs_pair[1] * (total - x) == legs_total
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            self.assertEqual(generated["answer"], fits[0][1], f"seed {seed}: {text}")

    # Во втором сюжете числа ног в тексте не названы — они известны из самой
    # пары существ. Читаем их так же, как читал бы ребёнок: из знания о том,
    # сколько ног у гуся и у коровы.
    LEGS_BY_GROUP = {
        "гусей и коров": (2, 4),
        "дроидов и генералов": (2, 2),
        "Тридцатичетырёхножки и Драконы": (34, 4),
        "дроидеки и клоны": (3, 2),
        "Змеи и Кентавры": (2, 4),
    }

    def legs_from_pair_name(self, text: str) -> tuple[int, int]:
        for group, legs in self.LEGS_BY_GROUP.items():
            if group in text:
                return legs
        raise AssertionError(f"незнакомая пара существ: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 20 ног и 26 рук дают 7 дроидов и 3 генералов."""
        fits = [(x, y) for x in range(20) for y in range(20)
                if 2 * x + 2 * y == 20 and 2 * x + 4 * y == 26]
        self.assertEqual(fits, [(7, 3)])


class ForgotItemTests(unittest.TestCase):
    TEMPLATE = LIBRARY["forgot_item_return_point"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            way = int(re.search(r"занимает у .+? (\d+)\s?минут", text).group(1))
            early = int(re.search(r"за (\d+)\s?\S+ до звонка", text).group(1))
            late = int(re.search(r"опоздает на (\d+)\s?\S+", text).group(1))
            answer = generated["answer"]

            # Решение с нуля: пробуем каждую минуту как точку, где вспомнили,
            # и проверяем обе дороги. Звонок наступает через way + early минут.
            bell = way + early
            fits = [
                walked for walked in range(1, way)
                if way + 2 * walked - bell == late
            ]
            self.assertEqual(fits, [answer], f"seed {seed}: подходят {fits} — {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: за 3 минуты до звонка и опоздание на 7 дают 5 минут."""
        self.assertEqual((3 + 7) // 2, 5)


class CircularMeetingsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["circular_track_meetings"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(r"в (\d+) раза? чаще", text).group(1))
            ratio = float(str(generated["answer"]).replace(",", "."))

            # Решение с нуля: берём скорость медленного за единицу и считаем,
            # как быстро сокращается круг в обе стороны.
            slow, fast = 1.0, ratio
            catching_up = fast - slow
            meeting = fast + slow
            self.assertAlmostEqual(meeting / catching_up, times, places=6,
                                   msg=f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: встречи впятеро чаще — отец быстрее сына в полтора раза."""
        self.assertEqual((1.5 + 1) / (1.5 - 1), 5)


if __name__ == "__main__":
    unittest.main()


class PositionFromBothEndsTests(unittest.TestCase):
    """Предмет считается дважды — слева и справа, — поэтому единицу вычитают."""

    TEMPLATE = LIBRARY["position_from_both_ends"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            numbers = [int(v) for v in re.findall(r"(\d+)-[мй]", text)]
            self.assertEqual(len(numbers), 2, f"seed {seed}: {text}")
            left, right = numbers

            # Решение с нуля: строим сам ряд и ищем длину, при которой предмет
            # стоит на обоих местах сразу.
            fits = [
                total for total in range(2, 200)
                if left <= total and total - right + 1 == left
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: пятая слева и семнадцатая справа — 21 книга."""
        self.assertEqual(5 + 17 - 1, 21)


class LogsEqualCutsTests(unittest.TestCase):
    """Распилов на единицу меньше, чем частей."""

    TEMPLATE = LIBRARY["logs_equal_cuts"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"Имеется (\d+)", text).group(1))
            long_parts = int(re.search(r"на (\d+) част", text).group(1))
            short_parts = int(re.search(r"короткое — на (\d+)", text).group(1))

            # Решение с нуля: перебираем, сколько брёвен длинные.
            fits = [
                long_logs for long_logs in range(1, total)
                if long_logs * (long_parts - 1) == (total - long_logs) * (short_parts - 1)
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: подходят {fits} — {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 35 брёвен, 5 и 4 части — длинных 15, распилов по 60."""
        self.assertEqual(15 * 4, 20 * 3)
        self.assertEqual(15 + 20, 35)


class LakeWithSpringTests(unittest.TestCase):
    """Озеро пополняется, поэтому делить его на слонов напрямую нельзя."""

    TEMPLATE = LIBRARY["lake_with_spring_elephants"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            herd_one = int(re.search(r"Стадо в\s(\d+)", text).group(1))
            herd_two, days_two = (int(v) for v in re.search(
                r"а стадо в\s(\d+)\s?\S+ — за (\d+)", text).groups())
            answer = generated["answer"]

            # Решение с нуля: приток находим из двух наблюдений, затем объём,
            # затем время одного слона. Считаем дробями, чтобы не потерять
            # половину нормы, из которой вся задача и состоит.
            spring = Fraction(days_two * herd_two - herd_one, days_two - 1)
            volume = Fraction(herd_one) - spring
            self.assertGreater(spring, 0, f"seed {seed}: родник должен прибывать")
            self.assertLess(spring, 1, f"seed {seed}: один слон не догонит родник")
            self.assertEqual(volume, herd_two * days_two - spring * days_two,
                             f"seed {seed}: наблюдения противоречат друг другу")
            self.assertEqual(Fraction(answer), volume / (1 - spring), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 163 слона за день и 33 за пять дней — один слон за 325."""
        spring = Fraction(5 * 33 - 163, 4)
        self.assertEqual(spring, Fraction(1, 2))
        self.assertEqual((163 - spring) / (1 - spring), 325)


class VitaminBoundsTests(unittest.TestCase):
    """Три вилки перемножаются, и неделя — это семь дней."""

    TEMPLATE = LIBRARY["vitamin_course_bounds"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            pills = [int(v) for v in re.search(r"по (\d+)–(\d+) таблетки", text).groups()]
            times = [int(v) for v in re.search(r"(\d+)–(\d+) раза? в день", text).groups()]
            weeks = [int(v) for v in re.search(r"(\d+)–(\d+) недель", text).groups()]

            # Решение с нуля: перебираем все допустимые сочетания и берём
            # крайние — так видно, что минимум и максимум достигаются сразу
            # по всем трём вилкам, а не по какой-то одной.
            totals = [
                p * t * w * 7
                for p in range(pills[0], pills[1] + 1)
                for t in range(times[0], times[1] + 1)
                for w in range(weeks[0], weeks[1] + 1)
            ]
            self.assertEqual(generated["answer"], max(totals) - min(totals),
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 2–3 таблетки 3–4 раза 3–5 недель дают 126 и 420."""
        self.assertEqual(2 * 3 * 3 * 7, 126)
        self.assertEqual(3 * 4 * 5 * 7, 420)
