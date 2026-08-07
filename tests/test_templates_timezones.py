"""Независимая проверка темы «Часовые пояса и расписания».

Пять шаблонов темы оставались единственными в библиотеке без независимого
решателя: их арифметику никто не пересчитывал по напечатанному тексту.
Обнаружилось это при сплошном просмотре каталога, и сразу же нашёлся дефект,
который не поймала ни одна прежняя проверка: в `olympiad_two_cities_duration`
разница часовых поясов разыгрывалась свободным числом, никак не связанным
с выбранными городами. 187 условий из 200 утверждали географическую неправду
вроде «в Екатеринбурге и в Самаре» с разницей шесть часов вместо одного.

Поэтому здесь две разные проверки:

* арифметика — решатель моделирует поездку или олимпиаду на общей шкале
  времени, а не повторяет формулу шаблона;
* география — заявленная в условии разница поясов сверяется с реестром
  топонимов. Задача обязана быть верной не только внутри себя.
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

from problemgen.russian.toponyms import hours_between  # noqa: E402
from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(30)
SPACE = "[\\s ]+"


def minutes(text: str) -> int:
    hours, mins = text.split(":")
    return int(hours) * 60 + int(mins)


def clocks(text: str) -> list[int]:
    return [minutes(item) for item in re.findall(r"\b(\d{1,2}:\d{2})\b", text)]


class TimezoneGeographyTests(unittest.TestCase):
    """Разница поясов в условии обязана совпадать с настоящей."""

    # Каждая тройка — «город, город, параметр с разницей между ними».
    # Список полный: все пять шаблонов темы, все их пары городов.
    CITY_PAIRS = (
        ("olympiad_two_cities_duration", "city_a", "city_b", "offset"),
        ("timezone_travel_duration", "city_a", "city_b", "offset_hours"),
        ("timezone_offset_round_trip", "city_a", "city_b", "offset_hours"),
        ("turnaround_flight_time", "city_a", "city_b", "offset_hours"),
        ("flight_landing_local_time", "city_a", "city_b", "off_ab"),
        ("flight_landing_local_time", "city_b", "city_c", "off_bc"),
    )

    def test_declared_offset_matches_the_registry(self) -> None:
        checked = 0
        for template_id, first, second, offset_key in self.CITY_PAIRS:
            template = LIBRARY[template_id]
            for seed in SEEDS:
                values = generate_active_template(template, random.Random(seed))["parameters"]
                self.assertEqual(
                    values[offset_key], hours_between(values[first], values[second]),
                    f"{template_id}, seed {seed}: заявленная разница поясов между "
                    f"{values[first].nom} и {values[second].nom} не та, что в реестре",
                )
                checked += 1
        # Иначе опечатка в имени параметра тихо превратила бы проверку в пустую.
        self.assertEqual(checked, len(self.CITY_PAIRS) * len(SEEDS))


class OlympiadDurationTests(unittest.TestCase):
    """Обе олимпиады проигрываются на общей шкале времени."""

    TEMPLATE = LIBRARY["olympiad_two_cities_duration"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start = int(re.search(rf"в (\d+){SPACE}час", text).group(1))
            first, second = text.split("А ", 1)
            gap_a, word = re.search(
                rf"на (\d+){SPACE}час\w*{SPACE}(позже|раньше)", first).groups()
            gap_b = int(re.search(rf"на (\d+){SPACE}час\w*{SPACE}позже", second).group(1))
            offset = generated["parameters"]["offset"]

            # Решение с нуля: перебираем длительность и проверяем оба заявления
            # на общей шкале — города различаются только сдвигом offset.
            fits = []
            for duration in range(1, 13):
                end_a = start + duration
                start_b = start - offset
                end_b = start_b + duration
                said_a = (end_a - start_b) == (int(gap_a) if word == "позже" else -int(gap_a))
                said_b = (end_b - start) == gap_b
                if said_a and said_b:
                    fits.append(duration)
            self.assertEqual(fits, [generated["answer"]], f"seed {seed}: {text}")


class TravelDurationTests(unittest.TestCase):
    """Время в пути считается переводом обоих моментов в один пояс."""

    TEMPLATE = LIBRARY["timezone_travel_duration"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            sample_a, sample_b, departure, arrival = clocks(text)
            offset = (sample_b - sample_a) // 60

            # Приезд «на следующий день», поэтому к прибытию добавляются сутки;
            # обратный перевод в пояс отправления даёт чистое время в пути.
            travel = arrival + 1440 - offset * 60 - departure
            hours = int(re.search(rf"(\d+){SPACE}час", generated["answer_text"]).group(1))
            mins = int(re.search(rf"(\d+){SPACE}минут", generated["answer_text"]).group(1))
            self.assertEqual(travel, hours * 60 + mins, f"seed {seed}: {text}")
            self.assertEqual(offset, generated["parameters"]["offset_hours"], f"seed {seed}")


class LandingTimeTests(unittest.TestCase):
    """Момент посадки строится сложением двух известных сдвигов."""

    TEMPLATE = LIBRARY["flight_landing_local_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            values = clocks(text)
            first_gap = (values[1] - values[0]) // 60
            second_gap = (values[3] - values[2]) // 60
            departure = values[4]
            flight_h, flight_m = re.search(
                rf"летел (\d+){SPACE}час\w*{SPACE}(\d+){SPACE}минут", text).groups()

            # Самолёт летит с востока на запад: местное время посадки — это
            # вылет минус суммарный сдвиг плюс время в полёте.
            total_gap = first_gap + second_gap
            landing = (departure - total_gap * 60 + int(flight_h) * 60 + int(flight_m)) % 1440
            printed = minutes(generated["answer_text"].strip())
            self.assertEqual(landing, printed, f"seed {seed}: {text}")


class RoundTripOffsetTests(unittest.TestCase):
    """Разница поясов восстанавливается из пары симметричных рейсов."""

    TEMPLATE = LIBRARY["timezone_offset_round_trip"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            out_dep, out_arr, back_dep, back_arr = clocks(text)

            # Решение с нуля: перебираем разницу поясов и время в пути,
            # требуя, чтобы оба рейса длились поровну.
            fits = []
            for offset in range(-12, 13):
                there = (out_arr - offset * 60 - out_dep) % 1440
                back = (back_arr + offset * 60 - back_dep) % 1440
                if there == back and there > 0:
                    fits.append(abs(offset))
            printed = int(re.search(rf"(\d+){SPACE}час", generated["answer_text"]).group(1))
            self.assertIn(printed, fits, f"seed {seed}: {text}")


class TurnaroundTests(unittest.TestCase):
    """Момент разворота проверяется делением всего полёта в заданном отношении."""

    TEMPLATE = LIBRARY["turnaround_flight_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            offset = int(re.search(rf"на (\d+){SPACE}час", text).group(1))
            departure, landing = clocks(text)[:2]
            ratio = int(re.search(rf"в (\d+){SPACE}раза дольше", text).group(1))

            # Всё считается в поясе города посадки: вылет переводится туда же.
            # В зеркальной ветке садятся западнее вылета, и разницу поясов
            # нужно вычитать, а не прибавлять — иначе ответ уедет на полсуток.
            eastward = "восточнее, чем" in text
            departure_local = departure + (offset * 60 if eastward else -offset * 60)
            total = (landing - departure_local) % 1440
            east = total * ratio // (ratio + 1)
            self.assertEqual(
                total * ratio % (ratio + 1), 0,
                f"seed {seed}: отношение не делит полёт нацело — {text}",
            )
            turn = (departure_local + east) % 1440
            printed = minutes(generated["answer_text"].strip())
            self.assertEqual(turn, printed, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
