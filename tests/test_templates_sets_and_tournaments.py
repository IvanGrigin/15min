"""Независимая проверка шаблонов темы «Множества, клубы, знакомства и турниры».

Решатели не повторяют формулу шаблона: где шаблон считает по закрытому
выражению, тест перебирает варианты или строит расписание турнира целиком.
Совпадение двух разных способов и есть проверка.
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
SPACE = "[  ]"


def numbers(text: str) -> list[int]:
    """Все целые числа условия по порядку — тест читает то же, что ученик."""
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    """Общие требования к любому сгенерированному условию."""
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class RoundRobinTests(unittest.TestCase):
    TEMPLATE = LIBRARY["tournament_round_robin_games"]

    def test_matches_independent_solution(self) -> None:
        words = {"одному разу": 1, "два раза": 2, "три раза": 3}
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            found = re.search(rf"участвуют (\d+){SPACE}\w+", text)
            self.assertIsNotNone(found, f"seed {seed}: {text}")
            people = int(found.group(1))
            rounds = next(value for phrase, value in words.items() if phrase in text)

            # Решение с нуля: честно перебираем пары участников. Формулу
            # n(n-1)/2 тест не знает.
            played = sum(
                rounds
                for first in range(people)
                for second in range(first + 1, people)
            )
            self.assertEqual(generated["answer"], played, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class KnockoutTests(unittest.TestCase):
    TEMPLATE = LIBRARY["tournament_knockout_games"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            found = re.search(rf"(\d+){SPACE}\w+ на турнир", text)
            self.assertIsNotNone(found, f"seed {seed}: {text}")
            alive = int(found.group(1))

            # Решение с нуля: разыгрываем сетку по турам. При нечётном числе
            # оставшихся один проходит дальше без игры. Формулу n-1 не используем.
            played = 0
            while alive > 1:
                pairs = alive // 2
                played += pairs
                alive -= pairs
            self.assertEqual(generated["answer"], played, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_participant_count_avoids_broken_accusative(self) -> None:
        """«собрал 31 человек» — сломанный винительный, такие числа исключены."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["n"] % 10, 1, f"seed {seed}: n={values['n']}")


class BoardsTotalTimeTests(unittest.TestCase):
    TEMPLATE = LIBRARY["tournament_boards_total_time"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            players = int(re.search(rf"играли (\d+){SPACE}\w+", text).group(1))
            boards = int(re.search(rf"на (\d+){SPACE}доск", text).group(1))
            hours = int(re.search(rf"занял (\d+){SPACE}час", text).group(1))

            # Решение с нуля: строим настоящее расписание кругового турнира
            # методом карусели и убеждаемся, что каждый тур занимает ровно
            # столько досок, сколько объявлено. Только после этого считаем время.
            rotation = list(range(players - 1))
            schedule: list[list[tuple[int, int]]] = []
            for _ in range(players - 1):
                tour = [(rotation[0], players - 1)]
                for offset in range(1, players // 2):
                    tour.append((rotation[offset], rotation[-offset]))
                schedule.append(tour)
                rotation = rotation[1:] + rotation[:1]
            seen = {tuple(sorted(pair)) for tour in schedule for pair in tour}
            self.assertEqual(len(seen), players * (players - 1) // 2, f"seed {seed}")
            for tour in schedule:
                self.assertEqual(len(tour), boards, f"seed {seed}: тур не заполняет доски")

            duration = Fraction(hours, len(schedule))
            on_one_board = duration * len(seen)
            self.assertEqual(on_one_board.denominator, 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], on_one_board.numerator, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class TwoLanguagesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_languages_inclusion_exclusion"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, first, second, neither = numbers(text)

            # Решение с нуля: перебираем размер пересечения и проверяем, что
            # объединение сходится с условием. Формулу включений-исключений
            # тест не применяет.
            fits = [
                both for both in range(0, min(first, second) + 1)
                if (first - both) + (second - both) + both == total - neither
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_two_different_languages(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["lang_a"], values["lang_b"], f"seed {seed}")


class BipartiteFriendshipTests(unittest.TestCase):
    TEMPLATE = LIBRARY["class_friendship_bipartite"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, per_boy, per_girl = numbers(text)

            # Решение с нуля: перебираем число мальчиков и проверяем, что рёбра
            # дружбы считаются одинаково с обеих сторон.
            fits = [
                boys for boys in range(1, total)
                if boys * per_boy == (total - boys) * per_girl
                and per_boy <= total - boys and per_girl <= boys
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            # Вопрос бывает про обе части класса.
            boys = fits[0]
            expected = total - boys if "девочек?" in text else boys
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class HandshakesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["handshakes_between_two_grades"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            per_four, per_five, total = numbers(text)
            asks_fours = "четвероклассников, если" in text

            fits = [
                fours for fours in range(1, total)
                if fours * per_four == (total - fours) * per_five
                and per_four <= total - fours and per_five <= fours
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            expected = fits[0] if asks_fours else total - fits[0]
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_both_questions_appear(self) -> None:
        asked = {
            generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]["asked"]
            for seed in range(60)
        }
        self.assertEqual(asked, {"four", "five"})


class TwoClubsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_clubs_one_shared_girl"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, music, none_, boys = numbers(text)

            # Решение с нуля: перебираем размер литературного клуба так, чтобы
            # объединение двух клубов накрыло ровно тех, кто состоит хоть в одном.
            fits = [
                size for size in range(1, total + 1)
                if music + size - 1 == total - none_
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0] - boys, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class MixedTournamentTests(unittest.TestCase):
    TEMPLATE = LIBRARY["mixed_tournament_win_difference"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            boys, girls, points = numbers(text)[:2] + [numbers(text)[-1]]
            girls_scored = "Девочки вместе набрали" in text

            # Решение с нуля: перебираем все исходы межгрупповых партий.
            # Очки внутри своей группы фиксированы и считаются отдельно.
            inner_girls = girls * (girls - 1)
            inner_boys = boys * (boys - 1)
            cross = boys * girls
            found = set()
            for girl_wins in range(cross + 1):
                for draws in range(cross - girl_wins + 1):
                    boy_wins = cross - girl_wins - draws
                    scored = (
                        inner_girls + 2 * girl_wins + draws if girls_scored
                        else inner_boys + 2 * boy_wins + draws
                    )
                    if scored == points:
                        found.add(girl_wins - boy_wins)
            self.assertIn(generated["answer"], found, f"seed {seed}: {text}")
            self.assertEqual(len(found), 1, f"seed {seed}: перевес неоднозначен — {text}")
            assert_text_is_clean(self, text, seed)


class CoffeeWithMilkTests(unittest.TestCase):
    TEMPLATE = LIBRARY["coffee_with_milk_shares"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            coffee_share, milk_share = [
                int(value) for value in re.findall(r"1/(\d+)", text)
            ]

            # Решение с нуля: перебираем численность клуба и для каждой находим
            # долю кофе в общем объёме, при которой доли президента сходятся.
            # Клуб возможен, только если эта доля строго между 0 и 1.
            # Правило «n строго между знаменателями» тест не знает.
            fits = []
            for people in range(2, 60):
                share = (
                    (Fraction(1, people) - Fraction(1, milk_share))
                    / (Fraction(1, coffee_share) - Fraction(1, milk_share))
                )
                if 0 < share < 1:
                    fits.append(people)
            self.assertEqual(fits, [generated["answer"]], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
