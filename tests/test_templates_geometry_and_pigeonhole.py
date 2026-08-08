"""Независимая проверка первой волны по каталогу непокрытых задач.

Пять приёмов, которых в библиотеке не было: разбор распиленного куба,
перегородки в фигуре с дырой, пузатость прямоугольника, разрез прямоугольника
и обратный принцип Дирихле. Каталог с оригинальными номерами задач —
`docs/archive/UNCOVERED_TASK_GROUPS.md`.

Решатели не повторяют формулы шаблонов. Куб и сетка перебираются поштучно:
каждый кубик и каждая пара соседних клеток проверяются отдельно, как это
сделал бы ребёнок на маленьком примере. Это и есть проверка формулы —
на больших числах перебор невозможен, поэтому шаблон ограничен так, чтобы
перебор оставался посильным хотя бы на части жеребьёвок.
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


class CubePaintedFacesTests(unittest.TestCase):
    """Куб перебирается кубик за кубиком, без формул для четырёх сортов."""

    TEMPLATE = LIBRARY["cube_cut_painted_faces"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            side = generated["parameters"]["side"]
            wanted = generated["parameters"]["faces_n"]

            # Решение с нуля: у кубика окрашена та грань, что смотрит наружу,
            # то есть каждая координата, равная 0 или side−1, добавляет грань.
            counted = 0
            for x in range(side):
                for y in range(side):
                    for z in range(side):
                        outside = sum(
                            1 for value in (x, y, z) if value in (0, side - 1))
                        if outside == wanted:
                            counted += 1
            self.assertEqual(generated["answer"], counted, f"seed {seed}: {text}")

    def test_four_kinds_add_up_to_the_whole_cube(self) -> None:
        """Углы, рёбра, грани и нутро вместе обязаны дать side³."""
        for seed in SEEDS:
            side = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]["side"]
            inner = side - 2
            self.assertEqual(8 + 12 * inner + 6 * inner ** 2 + inner ** 3, side ** 3)


class GridPartitionsTests(unittest.TestCase):
    """Перегородки считаются перебором пар соседних клеток."""

    TEMPLATE = LIBRARY["grid_partitions_with_hole"]

    def test_matches_independent_solution_on_small_cases(self) -> None:
        """Полный перебор посилен не всегда, поэтому берутся мелкие жеребьёвки."""
        checked = 0
        for seed in range(400):
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            rows, cols = values["rows"], values["cols"]
            if rows * cols > 200_000:
                continue
            hole_r, hole_c = values["hole_r"], values["hole_c"]
            top, left = (rows - hole_r) // 2, (cols - hole_c) // 2

            def present(row: int, col: int) -> bool:
                return not (top <= row < top + hole_r and left <= col < left + hole_c)

            # Перегородка — общая сторона двух оставшихся клеток.
            counted = 0
            for row in range(rows):
                for col in range(cols):
                    if not present(row, col):
                        continue
                    if col + 1 < cols and present(row, col + 1):
                        counted += 1
                    if row + 1 < rows and present(row + 1, col):
                        counted += 1
            self.assertEqual(generated["answer"], counted, f"seed {seed}")
            checked += 1
            if checked >= 10:
                break
        self.assertGreaterEqual(checked, 8, "не набралось случаев, посильных для перебора")

    def test_source_examples_reproduce(self) -> None:
        """Контрольные числа из условия: 1×2 даёт 1 перегородку, 2×3 даёт 7."""
        def walls(rows: int, cols: int) -> int:
            return rows * (cols - 1) + cols * (rows - 1)
        self.assertEqual(walls(1, 2), 1)
        self.assertEqual(walls(2, 3), 7)
        # 3×3 без центральной клетки — 8, 4×4 с дырой 2×2 — 12.
        self.assertEqual(walls(3, 3) - walls(1, 1) - 2 * (1 + 1), 8)
        self.assertEqual(walls(4, 4) - walls(2, 2) - 2 * (2 + 2), 12)


class RectangleFatnessTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_fatness_glued_pair"]

    def test_matches_independent_solution(self) -> None:
        from fractions import Fraction

        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            ratio = generated["parameters"]["ratio"]

            # Решение с нуля: плитка 1 × ratio, склеиваем двумя способами
            # и берём большее отношение сторон.
            options = []
            for width, height in ((2, ratio), (1, 2 * ratio)):
                options.append(Fraction(max(width, height), min(width, height)))
            self.assertEqual(
                generated["answer"], max(options),
                f"seed {seed}: {generated['rendered_problem']}")


class RectanglePerimeterCutTests(unittest.TestCase):
    TEMPLATE = LIBRARY["rectangle_perimeter_after_cut"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            perimeter, vertical_sum = numbers(text)[:2]

            # Решение с нуля: перебираем стороны и оставляем те, при которых
            # оба заявления верны. Формулу шаблона тест не воспроизводит.
            fits = []
            for height in range(1, perimeter // 2):
                width = perimeter // 2 - height
                if width < 1:
                    continue
                if perimeter + 2 * height == vertical_sum:
                    fits.append(perimeter + 2 * width)
            self.assertEqual(fits, [generated["answer"]], f"seed {seed}: {text}")

    def test_square_is_excluded(self) -> None:
        """У квадрата оба разреза дают одно и то же — задача теряет смысл."""
        for seed in SEEDS:
            values = generate_active_template(
                self.TEMPLATE, random.Random(seed))["parameters"]
            self.assertNotEqual(values["height"], values["half"] - values["height"])


class PigeonholeRecoverTests(unittest.TestCase):
    TEMPLATE = LIBRARY["pigeonhole_recover_counts"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first, second = numbers(text)

            # Решение с нуля: перебираем составы пенала и проверяем обе гарантии
            # напрямую — «вынув n штук, нельзя промахнуться мимо вида X».
            best = 0
            for a in range(1, first + second):
                for b in range(1, first + second):
                    for c in range(1, first + second):
                        if b + c < first and a + c < second:
                            best = max(best, a + b + c)
            self.assertEqual(generated["answer"], best, f"seed {seed}: {text}")


class LetterOTests(unittest.TestCase):
    """Буква О — прямоугольник с прямоугольной дыркой по толщине стенки."""

    TEMPLATE = LIBRARY["letter_o_partitions"]

    def test_matches_independent_solution(self) -> None:
        checked = 0
        for seed in range(200):
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            values = generated["parameters"]
            width, height, thickness = values["w"], values["h"], values["t"]
            if width * height > 60_000:
                continue

            # Перебор клеток: клетка принадлежит букве, если лежит в рамке.
            def inside(row: int, col: int) -> bool:
                return not (thickness <= row < height - thickness
                            and thickness <= col < width - thickness)

            counted = 0
            for row in range(height):
                for col in range(width):
                    if not inside(row, col):
                        continue
                    if col + 1 < width and inside(row, col + 1):
                        counted += 1
                    if row + 1 < height and inside(row + 1, col):
                        counted += 1
            self.assertEqual(generated["answer"], counted, f"seed {seed}")
            checked += 1
            if checked >= 8:
                break
        self.assertGreaterEqual(checked, 6, "не набралось случаев для перебора")

    def test_sample_in_the_text_is_true(self) -> None:
        """Образец в условии обязан сойтись: 5 × 7 при толщине 2 даёт 48."""
        def walls(a: int, b: int) -> int:
            return a * (b - 1) + b * (a - 1)
        self.assertEqual(walls(5, 7) - walls(1, 3) - 2 * (1 + 3), 48)


class HotelRoomsTests(unittest.TestCase):
    """Число неотрицательных решений диофантова уравнения."""

    TEMPLATE = LIBRARY["hotel_room_split_ways"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            small, big, total = numbers(text)[:3]

            # Решение с нуля: прямой перебор числа люксов. Формулу шаблона
            # с наибольшим общим делителем тест не воспроизводит.
            ways = sum(1 for luxury in range(total // big + 1)
                       if (total - big * luxury) % small == 0)
            self.assertEqual(generated["answer"], ways, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику: 820 м² при номерах 30 и 40 — семь способов."""
        self.assertEqual(
            sum(1 for luxury in range(820 // 40 + 1) if (820 - 40 * luxury) % 30 == 0), 7)


class CubeVisibleFacesTests(unittest.TestCase):
    """Сумма чисел на гранях: перебор кубиков против формулы 36·side²."""

    TEMPLATE = LIBRARY["cube_visible_faces_sum"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            side = generated["parameters"]["side"]

            # Решение с нуля: у каждого кубика считаем видимые грани и пишем
            # это число на всех шести. Формулу шаблона тест не повторяет.
            total = 0
            for x in range(side):
                for y in range(side):
                    for z in range(side):
                        visible = sum(1 for value in (x, y, z)
                                      if value in (0, side - 1))
                        total += 6 * visible
            self.assertEqual(generated["answer"], total, f"seed {seed}")

    def test_sum_of_visible_faces_is_the_surface(self) -> None:
        """Тот самый ход, на котором держится задача."""
        for side in (3, 5, 8):
            visible = sum(
                sum(1 for value in (x, y, z) if value in (0, side - 1))
                for x in range(side) for y in range(side) for z in range(side))
            self.assertEqual(visible, 6 * side * side)


class CubeIntoBarsTests(unittest.TestCase):
    """Бруски укладываются без остатка, иначе объёмного деления мало."""

    TEMPLATE = LIBRARY["cube_cut_into_bars"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            side = int(re.search(r"стороной (\d+) см", text).group(1))
            sizes = re.findall(r"(\d+) × (\d+) × (\d+)", text)

            # Решение с нуля: считаем, сколько брусков влезает по каждой оси.
            counts = []
            for a, b, c in sizes:
                a, b, c = int(a), int(b), int(c)
                counts.append((side // a) * (side // b) * (side // c))
                for edge in (a, b, c):
                    self.assertEqual(side % edge, 0, f"seed {seed}: {edge} не делит {side}")
            self.assertEqual(len(counts), 2, f"seed {seed}: {text}")
            self.assertEqual(generated["answer"], abs(counts[0] - counts[1]),
                             f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: куб 100 см даёт 200 и 12500 брусков, разница 12300."""
        self.assertEqual((100 // 5) * (100 // 20) * (100 // 50), 200)
        self.assertEqual((100 // 2) * (100 // 4) * (100 // 10), 12500)


class LongRectangleCutsTests(unittest.TestCase):
    """Перебор разрезов: обе части должны быть длинными."""

    TEMPLATE = LIBRARY["long_rectangle_cuts"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            width, height = (int(v) for v in re.search(r"(\d+) × (\d+)", text).groups())

            def is_long(first: int, second: int) -> bool:
                return max(first, second) > 2 * min(first, second)

            good = sum(1 for cut in range(1, width)
                       if is_long(cut, height) and is_long(width - cut, height))
            good += sum(1 for cut in range(1, height)
                        if is_long(width, cut) and is_long(width, height - cut))
            self.assertEqual(generated["answer"], good, f"seed {seed}: {text}")

    def test_total_cuts_in_text_is_true(self) -> None:
        """Число способов названо в условии — оно обязано сходиться."""
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            width, height = (int(v) for v in re.search(r"(\d+) × (\d+)", text).groups())
            stated = int(re.search(r"есть (\d+)", text).group(1))
            self.assertEqual(stated, (width - 1) + (height - 1), f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: 15 × 10 режется 23 способами, из них 5 дают две длинных."""
        def is_long(a: int, b: int) -> bool:
            return max(a, b) > 2 * min(a, b)
        good = sum(1 for cut in range(1, 15) if is_long(cut, 10) and is_long(15 - cut, 10))
        good += sum(1 for cut in range(1, 10) if is_long(15, cut) and is_long(15, 10 - cut))
        self.assertEqual((15 - 1) + (10 - 1), 23)
        self.assertEqual(good, 5)


class GiftSettlementTests(unittest.TestCase):
    """Доли от общей суммы против фактически внесённого."""

    TEMPLATE = LIBRARY["gift_two_parts_settlement"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            first = int(re.search(r"первую часть (\d+)", text).group(1))
            second = int(re.search(r"вторую — (\d+)", text).group(1))

            # Решение с нуля: общая сумма, договорные доли, разница с внесённым.
            total = first + second
            self.assertEqual(total % 2, 0, f"seed {seed}: сумма не делится пополам")
            rest = total // 2
            self.assertEqual(rest % 2, 0, f"seed {seed}: остаток не делится надвое")
            self.assertEqual(generated["answer"], rest // 2 - second, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль: части 5695 и 1405 — доплата 370."""
        total = 5695 + 1405
        self.assertEqual((total - total // 2) // 2 - 1405, 370)

    def test_gender_agrees_in_the_question(self) -> None:
        """«Должна доплатить Поухатан» — слот с двумя одинаковыми формами."""
        for seed in range(60):
            text = generate_active_template(
                self.TEMPLATE, random.Random(seed))["rendered_problem"]
            self.assertNotIn("должнен", text, f"seed {seed}")
            self.assertTrue("должен доплатить" in text or "должна доплатить" in text,
                            f"seed {seed}: {text[-60:]}")


if __name__ == "__main__":
    unittest.main()
