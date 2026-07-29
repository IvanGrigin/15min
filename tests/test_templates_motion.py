"""Независимая проверка темы «Движение, скорость и расстояние».

Решатели моделируют движение по шагам: лифт едет этаж за этажом, собака
бежит вперёд и назад по минутам, пешеходы расходятся от своих домиков.
Формулы шаблонов тесты не повторяют — они проигрывают сюжет.
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


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class UphillTests(unittest.TestCase):
    TEMPLATE = LIBRARY["uphill_and_back_distance"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            up, down, hours = numbers(text)

            # Решение с нуля: перебираем расстояние и проверяем сумму времён
            # точными дробями. Формулу d = T*v1*v2/(v1+v2) тест не применяет.
            fits = [
                distance for distance in range(1, hours * down + 1)
                if Fraction(distance, up) + Fraction(distance, down) == hours
            ]
            self.assertEqual(fits, [generated["answer"]], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_uphill_is_slower_than_downhill(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertLess(values["up"], values["down"], f"seed {seed}")


class CompetitionTests(unittest.TestCase):
    TEMPLATE = LIBRARY["competition_three_legs"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(r"дистанцию за (\d+)", text).group(1))
            saves = [int(value) for value in re.findall(r"на (\d+)\s+минут\w*\s+раньше", text)]
            saves += [int(value) for value in re.findall(r"— на (\d+)", text)]
            first, second = saves[0], saves[-1]

            # Решение с нуля: перебираем длительности трёх этапов и проверяем,
            # что обе объявленные экономии сходятся.
            fits = []
            for leg1 in range(2, total, 2):
                for leg2 in range(2, total - leg1, 2):
                    leg3 = total - leg1 - leg2
                    if leg3 <= 0 or leg3 % 2:
                        continue
                    if leg1 // 2 == first and leg2 // 2 == second:
                        fits.append(total - leg3 // 2)
            self.assertEqual(fits, [generated["answer"]], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_three_different_legs(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            legs = {values["leg1"], values["leg2"], values["leg3"]}
            self.assertEqual(len(legs), 3, f"seed {seed}")


class TwoDriversTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_drivers_before_meeting"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, second, minutes = numbers(text)

            # Решение с нуля: ставим машины на расстоянии ответа и проверяем,
            # что они встретятся ровно через объявленное время.
            distance = generated["answer"]
            self.assertEqual(
                Fraction(distance, first + second) * 60, minutes,
                f"seed {seed}: {text}",
            )
            assert_text_is_clean(self, text, seed)

    def test_both_drive(self) -> None:
        """Скорость и единица берутся из способа передвижения — оба на колёсах."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertEqual(values["a"].motion, "drive", f"seed {seed}")
            self.assertEqual(values["b"].motion, "drive", f"seed {seed}")


class DogTests(unittest.TestCase):
    TEMPLATE = LIBRARY["dog_runs_there_and_back"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fast, slow, owner, minutes = numbers(text)

            # Решение с нуля: ищем момент разворота перебором долей минуты
            # и проверяем, что собака и хозяин оказались в одной точке.
            span = Fraction(minutes, 60)
            # Шаг сетки подобран так, чтобы момент разворота на неё попадал
            # при любых скоростях: он всегда кратен 1/(60*(fast+slow)) часа.
            grid = 60 * (fast + slow)
            turn = None
            for numerator in range(1, minutes * grid):
                candidate = Fraction(numerator, grid)
                if candidate >= span:
                    break
                dog_ahead = fast * candidate - slow * (span - candidate)
                if dog_ahead == owner * span:
                    turn = candidate
                    break
            self.assertIsNotNone(turn, f"seed {seed}: момент разворота не найден — {text}")
            path = fast * turn + slow * (span - turn)
            self.assertEqual(path * 1000, generated["answer"], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class ElevatorTests(unittest.TestCase):
    TEMPLATE = LIBRARY["elevator_ride_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # «на 8-м —» идёт без слова «этаже», поэтому его в шаблоне нет.
            floors = [int(value) for value in re.findall(r"(\d+)-(?:го|м)\b", text)]
            times = [int(value) for value in re.findall(r"(\d+)\s+секунд", text)]
            top, mid1, mid2, mid3 = floors
            time_top, time_mid2 = times[0], times[1]

            # Решение с нуля: перебираем скорость лифта и время остановки,
            # моделируя поездку этаж за этажом.
            fits = []
            for per_floor in range(1, 30):
                for per_stop in range(1, 30):
                    ride_top = (top - 1) * per_floor + 3 * per_stop
                    ride_mid2 = (mid2 - 1) * per_floor + 1 * per_stop
                    if ride_top == time_top and ride_mid2 == time_mid2:
                        fits.append((mid1 - 1) * per_floor + 2 * per_stop)
            self.assertEqual(len(set(fits)), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_floors_go_down_in_order(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            order = [values["top"], values["mid1"], values["mid2"], values["mid3"]]
            self.assertEqual(order, sorted(order, reverse=True), f"seed {seed}")
            self.assertGreater(values["mid3"], 1, f"seed {seed}")


class ThreeWalkersTests(unittest.TestCase):
    TEMPLATE = LIBRARY["three_walkers_catch_up"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first_speed = int(re.search(r"направо со скоростью (\d+)", text).group(1))
            second_speed, third_speed = [
                int(value) for value in
                re.search(r"со скоростью (\d+) и (\d+)", text).groups()
            ]
            meet_second, meet_third = [
                int(value) for value in re.findall(r"через (\d+)\s+минут", text)
            ]

            # Решение с нуля: расставляем домики по временам встреч и ведём
            # всех троих по минутам, пока третий не поравняется со вторым.
            house_second = (first_speed + second_speed) * meet_second
            house_third = (first_speed + third_speed) * meet_third
            minute = 0
            while True:
                minute += 1
                second_at = house_second - second_speed * minute
                third_at = house_third - third_speed * minute
                if third_at <= second_at:
                    break
                self.assertLess(minute, 100_000, f"seed {seed}: не догнал")
            self.assertEqual(third_at, second_at, f"seed {seed}: догнал не ровно — {text}")
            self.assertEqual(generated["answer"], minute - meet_third, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
