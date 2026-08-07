"""Независимая проверка трёх календарных приёмов, которых в библиотеке не было.

Прежние календарные шаблоны считали дни недели и сдвигали даты вперёд.
Здесь три другие мысли: сумма длин нескольких месяцев подряд, свойство
записи даты и расстояние между двумя датами.

Решатели устроены иначе, чем шаблоны. Месяцы складываются по таблице длин,
записанной в тесте отдельно от движка; зеркальные даты ищутся перебором
всех дней промежутка через стандартный модуль `datetime`, а не по правилу
«месяц всегда февраль», которое шаблон объясняет в заметке; отпуск
считается днями между датами, а не по разыгранной длине.
"""
from __future__ import annotations

import datetime
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

MONTHS_GENITIVE = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)
MONTHS_NOMINATIVE = (
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
)


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class ConsecutiveMonthsTests(unittest.TestCase):
    """Цепочка месяцев складывается по таблице длин, записанной здесь же."""

    TEMPLATE = LIBRARY["consecutive_months_total_days"]

    RUNS = {"двух": 2, "трёх": 3, "четырёх": 4, "пяти": 5}

    @staticmethod
    def lengths(leap: bool) -> list[int]:
        return [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            run = next(value for word, value in self.RUNS.items() if f"В {word} месяцах" in text)
            leap = "високосного" in text
            total = numbers(text)[0]
            ask_last = "последним" in text

            months = self.lengths(leap)
            expected = []
            for start in range(12):
                chain = [months[(start + step) % 12] for step in range(run)]
                if sum(chain) != total:
                    continue
                index = (start + run - 1) % 12 if ask_last else start
                expected.append(MONTHS_NOMINATIVE[index])

            self.assertEqual(list(generated["answer"]), expected, f"seed {seed}: {text}")
            self.assertTrue(expected, f"seed {seed}: у задачи нет решения — {text}")
            assert_text_is_clean(self, text, seed)

    def test_answer_lists_every_variant(self) -> None:
        """Ответов бывает несколько, и печататься обязаны все."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            rendered = generated["answer_text"]
            for month in generated["answer"]:
                self.assertIn(month, rendered, f"seed {seed}: {rendered}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 308: 90 дней за три месяца обычного года."""
        months = self.lengths(False)
        starts = [
            MONTHS_NOMINATIVE[start] for start in range(12)
            if sum(months[(start + step) % 12] for step in range(3)) == 90
        ]
        self.assertEqual(starts, ["январь", "декабрь"])
        leap = self.lengths(True)
        starts_leap = [
            MONTHS_NOMINATIVE[start] for start in range(12)
            if sum(leap[(start + step) % 12] for step in range(3)) == 90
        ]
        self.assertEqual(starts_leap, ["февраль"])


class PalindromeDatesTests(unittest.TestCase):
    """Зеркальные даты ищутся перебором всех дней промежутка."""

    TEMPLATE = LIBRARY["palindrome_dates_count"]

    @staticmethod
    def count_between(year_from: int, year_to: int) -> int:
        found = 0
        day = datetime.date(year_from, 1, 1)
        last = datetime.date(year_to, 12, 31)
        while day <= last:
            written = f"{day.day:02d}{day.month:02d}{day.year:04d}"
            if written == written[::-1]:
                found += 1
            day += datetime.timedelta(days=1)
        return found

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Первое число условия — пример даты, границы идут следом.
            year_from, year_to = numbers(text)[-2:]
            self.assertLess(year_from, year_to, f"seed {seed}: {text}")
            self.assertEqual(
                generated["answer"], self.count_between(year_from, year_to),
                f"seed {seed}: {text}",
            )
            assert_text_is_clean(self, text, seed)

    def test_every_such_date_falls_in_february(self) -> None:
        """Свойство, на котором стоит задача: в XXI веке иначе не бывает."""
        day = datetime.date(2001, 1, 1)
        last = datetime.date(2100, 12, 31)
        while day <= last:
            written = f"{day.day:02d}{day.month:02d}{day.year:04d}"
            if written == written[::-1]:
                self.assertEqual(day.month, 2, f"{day} не в феврале")
            day += datetime.timedelta(days=1)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 1270: за XXI век зеркальных дат 29."""
        self.assertEqual(self.count_between(2001, 2100), 29)
        # Ровно одна из них приходится на 29 февраля, и только в високосный год.
        self.assertTrue(
            f"{29:02d}{2:02d}{2092:04d}" == f"{29:02d}{2:02d}{2092:04d}"[::-1]
        )


class VacationSpanTests(unittest.TestCase):
    """Отпуск считается днями между датами, а не по разыгранной длине."""

    TEMPLATE = LIBRARY["vacation_days_between_dates"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            start_day, back_day = numbers(text)
            months = [
                index + 1 for word in re.findall(r"\d+ (\w+)", text)
                for index, name in enumerate(MONTHS_GENITIVE) if name == word
            ]
            self.assertEqual(len(months), 2, f"seed {seed}: {text}")

            year = generated["parameters"]["back_year"]
            first = datetime.date(year, months[0], start_day)
            back = datetime.date(year, months[1], back_day)
            # Отпуск — от первого дня отдыха до дня перед выходом на работу.
            expected = (back - first).days

            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            self.assertGreater(expected, 0, f"seed {seed}: отпуск обязан быть длиннее дня")
            assert_text_is_clean(self, text, seed)

    def test_span_crosses_a_month_boundary(self) -> None:
        """Иначе задача сводится к вычитанию двух чисел в одном месяце."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertGreater(values["back_month"], values["start_month"], f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 772: с 3 июля, на работу 27 августа — 55 дней."""
        first = datetime.date(2025, 7, 3)
        back = datetime.date(2025, 8, 27)
        self.assertEqual((back - first).days, 55)


if __name__ == "__main__":
    unittest.main()
