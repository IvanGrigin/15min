"""Батч Б1: движение по кругу, встречи и погоня.

Решатели не повторяют формул шаблонов. Точки встречи на круге пересчитываются
моделированием: круг делится на мелкие доли, встречи отмечаются одна за другой,
и различные точки складываются в множество — так это проверил бы человек
на бумаге. Всадник с письмом и возврат велосипедиста решаются от расстояний
в точных дробях, а интервал поездов — перебором фаз расписания.
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
SEEDS = range(30)
SPACE = "[\\s ]+"


def meeting_points(first: Fraction, second: Fraction) -> int:
    """Сколько различных точек круга дают встречи при этих скоростях.

    Круг считается единичным. Идущие навстречу сближаются со скоростью
    суммы, поэтому встречи случаются через равные промежутки; место каждой
    отмечается долей круга, пройденной первым. Точки копятся в множестве,
    пока не пойдут повторы.
    """
    step = first / (first + second)
    seen: set[Fraction] = set()
    position = Fraction(0)
    for _ in range(400):
        position = (position + step) % 1
        if position in seen:
            break
        seen.add(position)
    return len(seen)


class CircleMeetingTests(unittest.TestCase):
    TEMPLATE = LIBRARY["circle_meeting_points_speed"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            own = int(re.search(r"со скоростью (\d+) км/ч", text).group(1))
            points = int(re.search(r"в (\d+) разных точках", text).group(1))

            # Решение с нуля: перебираем скорость встречного и оставляем те,
            # при которых моделирование даёт ровно столько точек.
            fits = [
                other for other in range(1, 20 * own + 1)
                if meeting_points(Fraction(own), Fraction(other)) == points
            ]
            self.assertTrue(fits, f"seed {seed}: ни одна скорость не подходит — {text}")

            answer = generated["answer"]
            if isinstance(answer, list):
                self.assertEqual(sorted(answer), sorted(fits), f"seed {seed}: {text}")
            elif "наибольшая" in text:
                self.assertEqual(answer, max(fits), f"seed {seed}: {text}")
            else:
                self.assertEqual(answer, min(fits), f"seed {seed}: {text}")

    def test_all_three_questions_appear(self) -> None:
        """Шаблон обязан спрашивать по-разному, а не только «чему может быть равна»."""
        asked = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            asked.add("наибольшая" in text or "наименьшая" in text)
        self.assertEqual(asked, {True, False}, "встретился только один вид вопроса")

    def test_both_answers_are_printed(self) -> None:
        """Верных ответов два, и ключ обязан назвать оба."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            if isinstance(generated["answer"], list):
                self.assertIn(" или ", generated["answer_text"], f"seed {seed}")
                self.assertEqual(len(generated["answer"]), 2, f"seed {seed}")


class RiderLetterTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rider_carries_letter_back"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            walk = int(re.search(r"скоростью (\d+) км/ч", text).group(1))
            head = int(re.search(rf"на (\d+){SPACE}час", text).group(1))
            there = int(re.search(rf"письмо за (\d+){SPACE}минут", text).group(1))

            # Решение с нуля, в километрах и часах. Скорость всадника
            # не дана — она восстанавливается из первого участка.
            gap = Fraction(walk * head)
            hours_there = Fraction(there, 60)
            rider = gap / hours_there - walk        # сближение навстречу
            if "С какой скоростью" in text:
                self.assertEqual(generated["answer"], rider, f"seed {seed}: {text}")
                continue

            wait = int(re.search(rf"(\d+){SPACE}минут ждал", text).group(1))
            grown = gap + walk * Fraction(wait, 60)  # первый ушёл, второй стоял
            back = grown / (rider - walk) * 60       # догон, в минутах
            expected = back + there + wait if "от найма" in text else back
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_rider_is_faster_than_walkers(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertGreater(values["times"], 1, f"seed {seed}: всадник не догонит")


class CyclistReturnsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["cyclist_returns_before_walker"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            gap = int(re.search(rf"на (\d+){SPACE}минут", text).group(1))
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))

            # Решение с нуля: берём путь за единицу, скорость пешехода за 1.
            # Тогда время пешехода — это сам путь, и всё считается в тех же
            # единицах, а расстояние из ответа уходит.
            meet = Fraction(1, times + 1)      # доля пути до встречи по времени
            walker_total = Fraction(1)
            rider_total = 2 * meet             # туда столько же, сколько обратно
            unit = Fraction(gap) / (walker_total - rider_total)
            if "весь путь" in text:
                expected = walker_total * unit
            elif "в дороге" in text:
                expected = rider_total * unit
            else:
                expected = meet * unit
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")

    def test_cities_differ(self) -> None:
        """«Из Свалки в Свалку» — так было, пока города брались локациями."""
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["p"].nom, values["q"].nom, f"seed {seed}")


class TrainIntervalTests(unittest.TestCase):
    TEMPLATE = LIBRARY["train_interval_from_count"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            window = int(re.search(rf"ровно (\d+){SPACE}минут", text).group(1))
            seen = int(re.search(rf"насчитал[а]? (\d+){SPACE}поезд", text).group(1))

            # Решение с нуля: для каждого промежутка прокручиваем все сдвиги
            # расписания и смотрим, может ли в окно попасть ровно столько поездов.
            fits = []
            for interval in range(1, window + 1):
                counts = set()
                for shift in range(interval):
                    counts.add(len(range(shift, window + 1, interval)))
                if seen in counts:
                    fits.append(interval)
            answer = generated["answer"]
            if isinstance(answer, list):
                self.assertEqual(sorted(answer), sorted(fits), f"seed {seed}: {text}")
            else:
                self.assertEqual(answer, max(fits), f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
