"""Независимая проверка гонки половинами, догонялок и города лжецов.

Решатели теста разбирают напечатанное условие и считают заново. Для гонки
половинами тест не повторяет формулу шаблона, а моделирует движение прямо:
берёт конкретную длину пути и конкретную скорость соперника и складывает
время по участкам. Для догонялок — идёт по минутам, пока один не догонит
другого. Так проверка не может «согласиться» с шаблоном из-за общей ошибки
в формуле.
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

# Слова условия — множители скорости. Держим их здесь, а не выводим из чисел
# шаблона: тест обязан читать задачу так же, как её читает ребёнок.
FACTORS = {
    "вдвое быстрее": Fraction(2),
    "втрое быстрее": Fraction(3),
    "в четыре раза быстрее": Fraction(4),
    "в семь раз быстрее": Fraction(7),
    "в полтора раза быстрее": Fraction(3, 2),
    "вдвое медленнее": Fraction(1, 2),
    "втрое медленнее": Fraction(1, 3),
    "в четыре раза медленнее": Fraction(1, 4),
    "в полтора раза медленнее": Fraction(2, 3),
}


class HalfSplitRaceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["half_split_race"]

    def read(self, text: str) -> tuple[Fraction, Fraction, bool]:
        """Два множителя скорости и то, что делится пополам: путь или время."""
        found = [
            (text.index(phrase), factor)
            for phrase, factor in FACTORS.items()
            if phrase in text
        ]
        self.assertEqual(len(found), 2, f"должно быть два множителя: {text}")
        found.sort()
        by_time = "половину времени" in text
        return found[0][1], found[1][1], by_time

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            fast, slow, by_time = self.read(text)

            # Решение с нуля: берём соперника со скоростью 1 и путь длиной 2.
            if by_time:
                # Каждый бежит одно и то же время; сравниваем пройденный путь.
                # Пусть общее время равно 2: соперник пройдёт 2.
                mine = fast + slow
                rival = Fraction(2)
                first_is_hero = mine > rival
            else:
                # Каждый проходит путь 2; сравниваем затраченное время.
                mine = 1 / fast + 1 / slow
                rival = Fraction(2)
                first_is_hero = mine < rival
            self.assertNotEqual(mine, rival, f"seed {seed}: ничья — {text}")

            hero, rival_name = self.names(text)
            self.assertEqual(
                generated["answer_text"].lower(),
                (hero if first_is_hero else rival_name).lower(),
                f"seed {seed}: {text}")

    def names(self, text: str) -> tuple[str, str]:
        """Кто герой, а кто соперник — по первой фразе условия «A и B»."""
        head = re.split(r"\s(?:бежали|спускались|устроили|побежали)\s", text)[0]
        first, second = (part.strip() for part in head.split(" и ", 1))
        return first, second

    def test_both_splits_occur(self) -> None:
        """Оба варианта обязаны выпадать: иначе исчезает вся соль задачи."""
        seen = set()
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add("половину времени" in text)
        self.assertEqual(seen, {True, False})

    def test_source_example_reproduces(self) -> None:
        """Контроль: половина пути вдвое быстрее и вдвое медленнее — проигрыш."""
        mine = 1 / Fraction(2) + 1 / Fraction(1, 2)
        self.assertEqual(mine, Fraction(5, 2))
        self.assertGreater(mine, 2, "Буратино проиграл Пьеро — задача 1157")
        # Та же пара множителей, но пополам делится время, — и уже выигрыш.
        self.assertGreater(Fraction(2) + Fraction(1, 2), 2)


class CatchUpTests(unittest.TestCase):
    TEMPLATE = LIBRARY["catch_up_head_start"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            speeds = [int(value) for value in re.findall(r"(\d+) (?:км/ч|м/с)", text)]
            self.assertEqual(len(speeds), 2, f"seed {seed}: {text}")
            slow, fast = speeds

            head = re.search(r"на (\d+) минут", text)
            if head is not None:
                # Фора по времени: ушедший вперёд успел пройти head · slow.
                gap = int(head.group(1)) * slow
            else:
                gap = int(re.search(r"(?:между ними|было) (\d+) метр", text).group(1))

            # Решение с нуля: шагаем по единице времени, пока не догонит.
            step = 0
            behind = gap
            while behind > 0:
                behind -= fast - slow
                step += 1
            self.assertEqual(behind, 0, f"seed {seed}: догоняет не в целое время")
            self.assertEqual(generated["answer"], step, f"seed {seed}: {text}")

    def test_chaser_is_really_faster(self) -> None:
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            slow, fast = (int(value) for value in re.findall(r"(\d+) (?:км/ч|м/с)", text))
            self.assertGreater(fast, slow, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: фора 105 минут при скоростях 4 и 6 — догонит через 210."""
        self.assertEqual(105 * 4 // (6 - 4), 210)
        self.assertEqual(10 // (7 - 6), 10, "между мальчиками 10 метров — 10 секунд")


class CityOfLiarsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["city_of_liars_and_potters"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            people = int(re.search(r"все\s(\d+)\s?жител", text).group(1))

            # Решение с нуля: перебираем, сколько правдивцев могло быть, и
            # проверяем обе природы отдельно. Фраза «вы все лжецы» истинна
            # ровно тогда, когда среди остальных нет ни одного правдивца.
            fits = []
            for truthful in range(people + 1):
                # Для правдивца остальных правдивцев truthful − 1, и его фраза
                # обязана быть истинной.
                truthful_holds = truthful == 0 or truthful - 1 == 0
                # Для лжеца остальных правдивцев truthful, и его фраза
                # обязана быть ложной — то есть правдивец среди них найдётся.
                liar_holds = truthful == people or truthful > 0
                if truthful_holds and liar_holds:
                    fits.append(truthful)
            self.assertEqual(fits, [1], f"seed {seed}: подходят {fits}")

            liars_asked = "Сколько" in text and re.search(
                r"Сколько (\w+) было", text).group(1) == self.liar_word(text)
            self.assertEqual(
                generated["answer"], people - 1 if liars_asked else 1,
                f"seed {seed}: {text}")

    def liar_word(self, text: str) -> str:
        """Родительный падеж лжецов — из вопроса, а не из параметров шаблона."""
        claim = re.search(r"«Вы все (\w+)!»", text).group(1)
        asked = re.search(r"Сколько (\w+) было", text).group(1)
        # «торговцы» и «торговцев» — одно слово в разных падежах: сравниваем корни.
        return asked if asked[:5] == claim[:5] else ""

    def test_answer_never_depends_on_the_crowd(self) -> None:
        """Правдивец один при любом числе жителей — в этом вся задача."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            people = int(re.search(r"все\s(\d+)\s?жител", text).group(1))
            self.assertIn(generated["answer"], (1, people - 1), f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
