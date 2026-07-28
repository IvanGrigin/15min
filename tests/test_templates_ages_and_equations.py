"""Независимая проверка шаблонов тем «Возраст и поколения» и «Задачи на уравнения».

Решатели работают перебором или прямым моделированием сюжета: очередь
достраивается человек за человеком, неделя проживается день за днём, цепочка
арифметических действий выполняется вперёд. Формулы шаблона тесты не повторяют.
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
SEEDS = range(25)
SPACE = r"[\s ]+"


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class FriendsSumOfAgesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["friends_sum_of_ages_count"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, years, later = numbers(text)

            # Решение с нуля: перебираем численность компании и прибавляем годы
            # каждому по одному. Деление разности на годы не используется.
            fits = [
                count for count in range(1, 40)
                if total + count * years == later
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class TwoAgesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_ages_sum_and_difference"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            diff, total = numbers(text)

            fits = [
                older for older in range(1, total)
                if older - (total - older) == diff
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_ages_are_plausible(self) -> None:
        """Разница не больше возраста младшего: иначе «сверстникам» 28 и 9 лет."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertLessEqual(values["diff"], values["younger"], f"seed {seed}")
            self.assertGreaterEqual(values["younger"], 5, f"seed {seed}")


class AgePuzzleTests(unittest.TestCase):
    TEMPLATE = LIBRARY["age_puzzle_as_old_as_now"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = numbers(text)[0]
            times = 2 if "вдвое" in text else 3

            # Решение с нуля: перебираем оба возраста и проигрываем условие
            # буквально — отматываем годы назад, пока старший не станет
            # ровесником нынешнего младшего.
            fits = []
            for younger in range(1, total):
                older = total - younger
                back = older - younger
                if back > 0 and older == times * (younger - back):
                    fits.append(younger)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class QueueGenerationsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["queue_of_three_groups"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            # Кто стоит в очереди, зависит от вселенной, поэтому слово не жёсткое.
            total = int(re.search(rf"оказалось (\d+){SPACE}\w+", text).group(1))
            # Ни «похлёбки», ни «молодых» в шаблоне быть не должно: и предмет,
            # и признак групп приходят из данных мира.
            self.assertNotIn("похлёбк", text, f"seed {seed}: предмет зашит в шаблон")

            # Решение с нуля: достраиваем очередь как список и считаем длину.
            fits = []
            for young in range(2, total + 1):
                queue = ["м"] * young
                for mark in ("с", "п"):
                    grown: list[str] = []
                    for index, person in enumerate(queue):
                        if index:
                            grown.append(mark)
                        grown.append(person)
                    queue = grown
                if len(queue) == total:
                    fits.append(young)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class QueueInsertionsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["queue_three_rounds_of_insertions"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(rf"пришло (\d+){SPACE}человек", text).group(1))

            fits = []
            for first in range(2, total + 1):
                length = first
                for added in (1, 2, 3):
                    length += added * (length - 1)
                if length == total:
                    fits.append(first)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class WordsRatioTests(unittest.TestCase):
    TEMPLATE = LIBRARY["words_ratio_and_difference"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))
            diff = int(re.search(rf"на (\d+){SPACE}слов", text).group(1))

            fits = [
                smaller for smaller in range(1, diff + 1)
                if smaller * times - smaller == diff
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class TreesRatioTests(unittest.TestCase):
    TEMPLATE = LIBRARY["trees_ratio_and_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            times = int(re.search(rf"в (\d+){SPACE}раз", text).group(1))
            total = int(re.search(rf"посадили (\d+){SPACE}дерев", text).group(1))

            fits = [
                smaller for smaller in range(1, total)
                if smaller + smaller * times == total
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class SausageTests(unittest.TestCase):
    TEMPLATE = LIBRARY["sausage_two_bites_leftover"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            dog_gap, cat_gap = [
                int(value) for value in re.findall(rf"на (\d+){SPACE}грамм", text)
            ]

            # Решение с нуля: перебираем длину батона и куски. Если ответ
            # действительно не зависит от длины, все варианты дадут одно число.
            leftovers = set()
            for total in range(max(dog_gap, cat_gap) + 2, max(dog_gap, cat_gap) + 400, 2):
                if (total - dog_gap) % 2 or (total - cat_gap) % 2:
                    continue
                dog = (total - dog_gap) // 2
                cat = (total - cat_gap) // 2
                if dog > 0 and cat > 0 and dog + cat < total:
                    leftovers.add(total - dog - cat)
            self.assertEqual(len(leftovers), 1, f"seed {seed}: остаток зависит от батона — {text}")
            self.assertEqual(generated["answer"], leftovers.pop(), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class CandiesTests(unittest.TestCase):
    TEMPLATE = LIBRARY["candies_two_kinds_of_eaters"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total, per_boy, per_girl, people = numbers(text)

            fits = [
                girls for girls in range(0, people + 1)
                if (people - girls) * per_boy + girls * per_girl == total
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class GuessedNumberTests(unittest.TestCase):
    TEMPLATE = LIBRARY["guessed_number_reverse_chain"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            multiplier, addend, divisor, subtrahend, result = numbers(text)

            # Решение с нуля: прогоняем цепочку вперёд для каждого кандидата.
            # Обратный ход, которым пользуется шаблон, тест не повторяет.
            fits = []
            for guess in range(1, 200):
                stepped = guess * multiplier + addend
                if stepped % divisor:
                    continue
                if stepped // divisor - subtrahend == result:
                    fits.append(guess)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_answer_is_not_the_stated_result(self) -> None:
        """Цепочка, возвращающая задуманное число, решается без вычислений."""
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["guessed"], values["result"], f"seed {seed}")


class PillsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["pills_descending_by_one"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            total = int(re.search(rf"друзьям (\d+){SPACE}таблет", text).group(1))

            fits = [
                least for least in range(1, total)
                if sum(least + shift for shift in range(4)) == total
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_five_distinct_characters(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            names = {values[role].character_id for role in ("hero", "a", "b", "c", "d")}
            self.assertEqual(len(names), 5, f"seed {seed}")


class BunsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["buns_between_boys_and_girls"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            boys, girls = numbers(text)

            # Решение с нуля: разыгрываем разные расклады знакомств и в каждом
            # считаем булочки по буквальным правилам условия — сначала отдают
            # девочки знакомым, потом мальчики незнакомым. Ответ обязан
            # совпасть во всех раскладах, включая крайние.
            dice = random.Random(seed)
            counts = set()
            for trial in range(12):
                if trial == 0:
                    knows = [[True] * girls for _ in range(boys)]
                elif trial == 1:
                    knows = [[False] * girls for _ in range(boys)]
                else:
                    knows = [
                        [dice.random() < 0.5 for _ in range(girls)]
                        for _ in range(boys)
                    ]
                from_girls = sum(
                    1 for boy in range(boys) for girl in range(girls) if knows[boy][girl]
                )
                from_boys = sum(
                    1 for boy in range(boys) for girl in range(girls) if not knows[boy][girl]
                )
                counts.add(from_girls + from_boys)
            self.assertEqual(counts, {boys * girls}, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], boys * girls, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class WeeklyTasksTests(unittest.TestCase):
    TEMPLATE = LIBRARY["weekly_growing_tasks"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            step = int(re.search(rf"на (\d+){SPACE}задач", text).group(1))
            times = 3 if "втрое" in text else 4

            # Решение с нуля: проживаем неделю по дням и смотрим, при каком
            # понедельнике воскресенье выходит кратным.
            fits = []
            for monday in range(1, 200):
                week = [monday + day * step for day in range(7)]
                if week[6] == times * week[0]:
                    fits.append(week[4])
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


class ChipmunksTests(unittest.TestCase):
    TEMPLATE = LIBRARY["chipmunks_equal_target"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            done_a, done_b, times = numbers(text)

            fits = [
                target for target in range(max(done_a, done_b) + 1, 2000)
                if target - done_a == times * (target - done_b)
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
