"""Независимо проверяет первый формульный тип в прежде пустых модулях."""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)


def numbers(text: str) -> list[int]:
    """Вернуть все целые числа, напечатанные в условии."""
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    """Проверить базовые свойства готового текста задачи."""
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class MissingModulesTests(unittest.TestCase):
    """Решает новые задачи по напечатанным условиям, не по derived_values."""

    def generated(self, template_id: str, seed: int) -> dict:
        """Собрать один вариант указанного шаблона."""
        return generate_active_template(LIBRARY[template_id], random.Random(seed))

    def test_factorial_value(self) -> None:
        """Перемножает множители факториала по одному."""
        for seed in SEEDS:
            generated = self.generated("factorial_value", seed)
            n = numbers(generated["rendered_problem"])[-1]
            product = 1
            for factor in range(1, n + 1):
                product *= factor
            self.assertEqual(generated["answer"], product, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_count_odd_open_interval(self) -> None:
        """Перебирает открытый промежуток и считает числа нужной чётности."""
        for seed in SEEDS:
            generated = self.generated("count_odd_open_interval", seed)
            text = generated["rendered_problem"]
            low, high = numbers(text)
            wanted = 0 if "существует чётных" in text else 1
            expected = sum(1 for value in range(low + 1, high) if value % 2 == wanted)
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, text, seed)

    def test_balls_guaranteed_two_black(self) -> None:
        """Проверяет худший случай: сперва вынуты все белые шары."""
        for seed in SEEDS:
            generated = self.generated("balls_guaranteed_two_black", seed)
            white, black = numbers(generated["rendered_problem"])
            expected = white + 2
            self.assertGreaterEqual(black, 2, f"seed {seed}")
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            self.assertLessEqual(expected, white + black, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_uniform_numbers_parity_sum(self) -> None:
        """Решает задачу по напечатанному тексту, не заглядывая в параметры.

        Правило берётся из самого условия — по его словесной формулировке,
        а не по идентификатору из данных. Так проверяется и то, что слова
        описывают ровно ту проверку, которую делает решатель: раньше здесь
        лежали готовые ответы, и рассогласование слов с арифметикой никто
        бы не заметил.
        """
        for seed in SEEDS:
            generated = self.generated("uniform_numbers_parity_sum", seed)
            text = generated["rendered_problem"]
            listed = numbers(text)

            def uniform(value: int) -> bool:
                digits = [int(digit) for digit in str(value)]
                return any(left % 2 == right % 2 for left, right in zip(digits, digits[1:]))

            # Формулировок у правила несколько («одной чётности», «одинаковую
            # чётность», «разную чётность»), поэтому опознаётся смысл, а не
            # точная фраза: совпадает ли требуемая чётность соседних цифр.
            same = re.search(r"(одной|одинаков\w+) чётност", text)
            opposite = re.search(r"разн\w+ чётност", text)
            if bool(same) == bool(opposite):
                self.fail(f"seed {seed}: правило не опознано в тексте — {text}")
            if same:
                keep = uniform
            else:
                def keep(value: int) -> bool:
                    return not uniform(value)

            expected = sum(value for value in listed if keep(value))
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_uniform_numbers_list_is_worth_sorting(self) -> None:
        """В списке всегда есть и подходящие числа, и неподходящие.

        Если подходят все, задача превращается в сложение всего списка;
        если ни одно — ответ ноль. И то и другое выглядит как опечатка,
        поэтому обе квоты гарантируются при генерации.
        """
        for seed in SEEDS:
            generated = self.generated("uniform_numbers_parity_sum", seed)
            listed = numbers(generated["rendered_problem"])
            answer = generated["answer"]
            self.assertGreater(answer, 0, f"seed {seed}: не подошло ни одно число")
            self.assertLess(
                answer, sum(listed),
                f"seed {seed}: подошли все числа списка — отбирать нечего",
            )

    def test_uniform_numbers_are_freshly_drawn(self) -> None:
        """Защита от возврата к готовым пакетам «список + ответ» в JSON.

        Восемь пакетов давали 31 различное условие на всю тему; здесь
        проверяется, что списки действительно разыгрываются.
        """
        distinct = {
            self.generated("uniform_numbers_parity_sum", seed)["rendered_problem"]
            for seed in range(60)
        }
        self.assertGreater(len(distinct), 40, f"всего {len(distinct)} различных условий на 60")

    def test_square_area_from_perimeter(self) -> None:
        """Восстанавливает сторону по периметру и считает площадь."""
        for seed in SEEDS:
            generated = self.generated("square_area_from_perimeter", seed)
            perimeter = numbers(generated["rendered_problem"])[0]
            self.assertEqual(perimeter % 4, 0, f"seed {seed}")
            self.assertEqual(generated["answer"], (perimeter // 4) ** 2, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_grid_square_count(self) -> None:
        """Складывает квадраты каждого размера вместо готовой формулы."""
        for seed in SEEDS:
            generated = self.generated("grid_square_count", seed)
            side = numbers(generated["rendered_problem"])[0]
            expected = sum((side - size + 1) ** 2 for size in range(1, side + 1))
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    FACES_WORD = {"все грани": 6, "пять граней": 5, "четыре грани": 4, "три грани": 3}

    def test_cube_paint_surface_scaling(self) -> None:
        """Пересчитывает расход через одну грань, а не через шесть.

        Известная краска относится не обязательно ко всем граням: сколько
        именно граней покрашено, сказано в условии словом.
        """
        for seed in SEEDS:
            generated = self.generated("cube_paint_surface_scaling", seed)
            text = generated["rendered_problem"]
            _, base_paint, side = numbers(text)
            asked = text.split("понадобится")[0]
            faces = next(count for word, count in self.FACES_WORD.items() if word in asked)
            self.assertEqual(base_paint % faces == 0 or (base_paint * 6) % faces == 0, True,
                             f"seed {seed}: {text}")
            expected = (base_paint * 6 // faces) * side * side
            self.assertEqual(generated["answer"], expected, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    def test_line_uniform_points_distance(self) -> None:
        """Считает промежутки между первой и последней точками."""
        for seed in SEEDS:
            generated = self.generated("line_uniform_points_distance", seed)
            _, points, step = numbers(generated["rendered_problem"])
            self.assertEqual(generated["answer"], (points - 1) * step, f"seed {seed}")
            assert_text_is_clean(self, generated["rendered_problem"], seed)

    PART_SHARE = {
        "четверть": (1, 4),
        "треть": (1, 3),
        "половину": (1, 2),
        "две пятых": (2, 5),
        "три четверти": (3, 4),
        "три пятых": (3, 5),
    }


    def test_train_cars_common_divisor(self) -> None:
        """Подбирает вместимость вагона перебором делителей.

        Решатель не пользуется НОДом: он перебирает все возможные
        вместимости, отбирает те, что делят все три числа и больше
        порога, и требует, чтобы такая вместимость была ровно одна —
        иначе у задачи несколько верных ответов.
        """
        for seed in SEEDS:
            generated = self.generated("train_cars_common_divisor", seed)
            text = generated["rendered_problem"]
            first, second, third, floor = numbers(text)

            fits = [
                size for size in range(floor + 1, min(first, second, third) + 1)
                if first % size == 0 and second % size == 0 and third % size == 0
            ]
            self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
            size = fits[0]
            expected = first // size + second // size + third // size
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_train_source_examples_reproduce(self) -> None:
        """Контроль по источнику: 236, 295, 472 -> 17 вагонов."""
        import math

        self.assertEqual(math.gcd(math.gcd(236, 295), 472), 59)
        self.assertEqual(236 // 59 + 295 // 59 + 472 // 59, 17)
        self.assertEqual(math.gcd(math.gcd(265, 318), 477), 53)
        self.assertEqual(265 // 53 + 318 // 53 + 477 // 53, 20)

    def test_container_weight_with_quarter(self) -> None:
        """Решает уравнение массы перебором, не пользуясь формулой шаблона."""
        for seed in SEEDS:
            generated = self.generated("container_weight_with_quarter", seed)
            text = generated["rendered_problem"]
            printed = numbers(text)

            if "весят столько же" in text:
                # Ветка с несколькими сосудами: full*w = kept*w + extra.
                full, kept, extra = printed
                self.assertGreater(full, kept, f"seed {seed}")
                fits = [
                    weight for weight in range(1, extra + 1)
                    if full * weight == kept * weight + extra
                ]
                self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
                self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            else:
                known = printed[0]
                word = next(w for w in self.PART_SHARE if w in text)
                num, den = self.PART_SHARE[word]
                # Полный вес ищется перебором: known + доля себя = вес.
                fits = [
                    total for total in range(1, 10 * known + 1)
                    if total * den == known * den + num * total
                ]
                self.assertEqual(len(fits), 1, f"seed {seed}: {text}")
                self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_wrong_product_correction(self) -> None:
        """Восстанавливает, какой ответ чей, и пересчитывает ошибочный.

        Соответствие в условии больше не дано — ответы перечислены «в каком-то
        порядке», как в источнике. Решатель перебирает все сопоставления
        и требует, чтобы подходило ровно одно: иначе у задачи несколько
        верных ответов, а ключ печатается один.
        """
        from itertools import permutations

        for seed in SEEDS:
            generated = self.generated("wrong_product_correction", seed)
            text = generated["rendered_problem"]
            factors = [int(value) for value in re.search(
                r"на (\d+), \S+ — на (\d+), а \S+ — на (\d+)", text).groups()]
            shown = [int(value) for value in re.search(
                r"ответы (\d+), (\d+) и (\d+)", text).groups()]

            found = set()
            for order in permutations(shown):
                for wrong in range(3):
                    right = [(factor, value) for index, (factor, value)
                             in enumerate(zip(factors, order)) if index != wrong]
                    if any(value % factor for factor, value in right):
                        continue
                    quotients = {value // factor for factor, value in right}
                    if len(quotients) != 1:
                        continue
                    number = quotients.pop()
                    if order[wrong] == factors[wrong] * number:
                        continue          # тогда никто не ошибся
                    found.add(factors[wrong] * number)
            self.assertEqual(len(found), 1, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], found.pop(), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)


if __name__ == "__main__":
    unittest.main()
