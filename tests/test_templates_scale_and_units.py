"""Независимая проверка темы «Масштаб, единицы площади и вес».

Пять шаблонов батча: вес листа по площади, квадрат из одинаковых квадратов,
перевод квадратных единиц, рамка вокруг картины и два ковра в углах комнаты.
Каталог с оригинальными номерами задач — `docs/NEXT_TEMPLATE_BATCHES.md`.

Общая ловушка темы — квадратные единицы: в метре сто сантиметров, а в
квадратном метре десять тысяч квадратных. Поэтому решатели здесь считают
площади в мелких единицах и переводят их сами, а два теста прямо требуют,
чтобы наивный ответ — тот, что получается без перевода, — отличался от
верного. Задача, где эти числа совпали бы, ничего не проверяет.
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
SEEDS = range(30)


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")


class SheetWeightTests(unittest.TestCase):
    TEMPLATE = LIBRARY["sheet_weight_by_area"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            width, height, sheet_grams, big_area = numbers(text)[:4]

            # Решение с нуля: считаем вес одного квадратного сантиметра как
            # дробь и умножаем на площадь в квадратных сантиметрах. Деления
            # с остатком не допускаем — задача обязана давать целый ответ.
            asked_cm2 = big_area * 10_000
            self.assertEqual(
                sheet_grams * asked_cm2 % (width * height), 0,
                f"seed {seed}: ответ не целый — {text}",
            )
            grams = sheet_grams * asked_cm2 // (width * height)
            self.assertEqual(grams % 1000, 0, f"seed {seed}: ответ не целый в килограммах")
            self.assertEqual(generated["answer"], grams // 1000, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_forgetting_the_square_conversion_gives_another_number(self) -> None:
        """Кто считал по сто сантиметров в метре, обязан ошибиться."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            width, height, sheet_grams, big_area = numbers(generated["rendered_problem"])[:4]
            naive = sheet_grams * big_area * 100 // (width * height)
            self.assertNotEqual(generated["answer"], naive, f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 243: лист 21 × 30 см в 1800 г, 7 м² -> 200 кг."""
        self.assertEqual(1800 * 7 * 10_000 // (21 * 30), 200_000)


class SquareOfSquaresTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_of_equal_squares"]

    COUNTS = {
        "четырёх": 4, "девяти": 9, "шестнадцати": 16, "двадцати пяти": 25,
    }

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = next(value for word, value in self.COUNTS.items() if word in text)
            given = numbers(text)[0]

            # Сторону маленького квадрата достаём тем действием, которое
            # задано условием, а дальше строим большой квадрат по клеткам.
            if "площадью" in text:
                side = round(given ** 0.5)
                self.assertEqual(side * side, given, f"seed {seed}: {text}")
            else:
                self.assertEqual(given % 4, 0, f"seed {seed}: {text}")
                side = given // 4
            rows = round(count ** 0.5)
            self.assertEqual(rows * rows, count, f"seed {seed}: {text}")

            if "периметр большого" in text:
                expected = 4 * rows * side
            else:
                expected = (rows * side) ** 2
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_question_never_repeats_the_given_quantity(self) -> None:
        """Если дана площадь, спрашивают периметр, и наоборот.

        Иначе задача решается умножением на число квадратиков и перестаёт
        быть про то, что площадь растёт как квадрат, а периметр линейно.
        """
        for seed in SEEDS:
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            given_area = "площадью" in text
            asked_area = "площадь большого" in text
            self.assertNotEqual(given_area, asked_area, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 109: девять квадратов по 16 см² -> периметр 48 см."""
        self.assertEqual(4 * 3 * 4, 48)


class SquareUnitsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_units_conversion"]

    COUNTS = {"двух": 2, "трёх": 3, "четырёх": 4, "пяти": 5, "семи": 7}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            ratio = numbers(text)[0]
            count = next(value for word, value in self.COUNTS.items() if word in text)

            # Квадратная единица — это квадрат со стороной в ratio малых,
            # то есть ratio строк по ratio клеток. Считаем клетками.
            cells = sum(ratio for _ in range(ratio))
            self.assertEqual(generated["answer"], count * cells, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_linear_ratio_is_never_the_answer(self) -> None:
        """Ответ обязан отличаться от «количество × линейное отношение»."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            ratio = numbers(text)[0]
            count = next(value for word, value in self.COUNTS.items() if word in text)
            self.assertNotEqual(generated["answer"], count * ratio, f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 713: три квадратных фута -> 432 квадратных дюйма."""
        self.assertEqual(3 * 12 * 12, 432)


class FrameAroundPictureTests(unittest.TestCase):
    TEMPLATE = LIBRARY["square_frame_around_picture"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            frame, perimeter = numbers(text)[:2]

            self.assertEqual(perimeter % 4, 0, f"seed {seed}: {text}")
            side = perimeter // 4
            outer = side + 2 * frame
            self.assertEqual(generated["answer"], outer * outer, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_single_frame_width_is_a_wrong_answer(self) -> None:
        """Кто прибавил ширину рамки один раз вместо двух, обязан ошибиться."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            frame, perimeter = numbers(generated["rendered_problem"])[:2]
            naive = (perimeter // 4 + frame) ** 2
            self.assertNotEqual(generated["answer"], naive, f"seed {seed}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 774: периметр 28, рамка 2 -> 121 см²."""
        self.assertEqual((28 // 4 + 2 * 2) ** 2, 121)


class TwoCarpetsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_carpets_overlap"]

    RATIOS = {"два": 2, "три": 3, "четыре": 4}

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            opposite, adjacent = numbers(text)[:2]
            ratio = next(
                value for word, value in self.RATIOS.items() if f"в {word} раза больше" in text
            )

            # Решение с нуля: перебираем сторону меньшего ковра и комнату
            # и проверяем обе площади наложения прямым счётом. Отношение
            # сторон читается из условия: ковёр бывает вдвое, втрое и вчетверо
            # больше, и формула «три меньших ковра минус выступ» верна только
            # для двойки.
            fits = []
            for small in range(1, adjacent + 1):
                for room in range(ratio * small + 1, (ratio + 1) * small):
                    stick = (ratio + 1) * small - room
                    if stick * stick != opposite:
                        continue
                    if stick * small != adjacent:
                        continue
                    fits.append(room)
            self.assertEqual(len(fits), 1, f"seed {seed}: {text} — {fits}")
            self.assertEqual(generated["answer"], fits[0], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_big_carpet_fits_in_the_room(self) -> None:
        for seed in SEEDS:
            values = generate_active_template(self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertGreater(
                values["room"], values["ratio"] * values["small"], f"seed {seed}")

    def test_all_ratios_actually_appear(self) -> None:
        """Иначе разнообразие только заявлено, а в выдаче одна двойка."""
        seen = set()
        for seed in range(80):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            seen.add(next(word for word in self.RATIOS if f"в {word} раза больше" in text))
        self.assertEqual(seen, set(self.RATIOS), f"выпали не все отношения: {seen}")

    def test_source_examples_reproduce(self) -> None:
        """Контроль по источнику: 4 и 14 -> комната 19 м; 9 и 15 -> 12 м.

        В обеих задачах корпуса ковёр вдвое больше, поэтому множитель три.
        Третья строка — контроль обобщения: при ковре втрое больше та же
        пара площадей даёт другую комнату, и формула для двойки тут врёт.
        """
        for ratio, opposite, adjacent, room in (
            (2, 4, 14, 19), (2, 9, 15, 12), (3, 4, 12, 22),
        ):
            stick = round(opposite ** 0.5)
            small = adjacent // stick
            self.assertEqual((ratio + 1) * small - stick, room)


if __name__ == "__main__":
    unittest.main()
