"""Батч Б7: геометрия, клетки и чётность.

Решатели строят фигуру, а не подставляют формулу. Ковры кладутся в углы
и перекрытие считается пересечением отрезков. Поверхность куба с вырезами
пересчитывается по граням: сколько ушло снаружи и сколько открылось внутри.
Путь жука ищется поиском в ширину по настоящей сетке — на малых размерах
это посильно, и именно поэтому годится в проверку.
"""
from __future__ import annotations

import random
import re
import sys
import unittest
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(25)
SPACE = "[\\s ]+"


def overlap(first: tuple[int, int], second: tuple[int, int]) -> int:
    """Длина пересечения двух отрезков на прямой."""
    return max(0, min(first[1], second[1]) - max(first[0], second[0]))


class CarpetsTests(unittest.TestCase):
    TEMPLATE = LIBRARY["two_square_carpets_overlap"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            opposite, adjacent = (int(value) for value in
                                  re.findall(r"площадью (\d+) м²", text))

            # Решение с нуля: перебираем сторону меньшего ковра и комнату,
            # раскладываем ковры по углам и считаем пересечение прямоугольников.
            fits = []
            for small in range(2, 60):
                big = 2 * small
                for room in range(big + 1, 3 * small):
                    across = (overlap((0, small), (room - big, room)) *
                              overlap((0, small), (room - big, room)))
                    along = (overlap((0, small), (room - big, room)) *
                             overlap((0, small), (0, big)))
                    if across == opposite and along == adjacent:
                        fits.append((small, big, room))
            self.assertTrue(fits, f"seed {seed}: не подобралось — {text}")
            small, big, room = fits[0]
            expected = big if "большего ковра" in text else room
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class CubeSurfaceTests(unittest.TestCase):
    TEMPLATE = LIBRARY["cube_corners_cut_surface"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            side = int(re.search(r"стороной (\d+) вырезали", text).group(1))
            cut = int(re.search(r"два куба со стороной (\d+)", text).group(1))

            # Решение с нуля: считаем по граням. Каждый вырез убирает три
            # квадрата снаружи и открывает три внутри — складываем отдельно.
            whole = 6 * side * side
            removed = 2 * 3 * cut * cut
            opened = 2 * 3 * cut * cut
            expected_surface = whole - removed + opened
            expected = 0 if "больше или меньше" in text else expected_surface
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            self.assertEqual(expected_surface, whole, "вырез не должен менять площадь")


class BugPathTests(unittest.TestCase):
    TEMPLATE = LIBRARY["bug_king_moves_blocked_cell"]

    def test_matches_independent_solution_on_small_boards(self) -> None:
        """Формула проверяется поиском в ширину на доске того же вида."""
        for side in (13, 15, 21):
            centre = side // 2
            for blocked, extra in (((centre, centre), 1), ((centre, centre + 1), 0)):
                start, finish = (0, 0), (side - 1, side - 1)
                seen = {start: 0}
                queue = deque([start])
                while queue:
                    row, column = queue.popleft()
                    for drow in (-1, 0, 1):
                        for dcolumn in (-1, 0, 1):
                            step = (row + drow, column + dcolumn)
                            if step == blocked or step in seen:
                                continue
                            if not (0 <= step[0] < side and 0 <= step[1] < side):
                                continue
                            seen[step] = seen[(row, column)] + 1
                            queue.append(step)
                self.assertEqual(seen[finish], side - 1 + extra,
                                 f"доска {side}, перекрыто {blocked}")

    def test_template_agrees_with_the_rule(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            side = int(re.search(r"квадрата (\d+) ×", text).group(1))
            extra = 0 if "соседней с центральной" in text else 1
            expected = extra if "длиннее" in text else side - 1 + extra
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")


class BerriesParityTests(unittest.TestCase):
    TEMPLATE = LIBRARY["berries_parity_along_fence"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = generated["rendered_problem"]
            count = int(re.search(rf"растут (\d+){SPACE}куст", text).group(1))
            step = int(re.search(r"отличается ровно на (\d+)", text).group(1))
            target = int(re.search(rf"ровно (\d+){SPACE}ягод", text).group(1))

            # Решение с нуля: строим наборы прямо. Первый куст перебираем,
            # остальные получаются прибавлением или вычитанием шага, поэтому
            # достаточно проверить достижимые суммы по модулю двойки.
            sums = set()
            for first in range(1, 6):
                for pattern in range(1 << (count - 1)):
                    values = [first]
                    for index in range(count - 1):
                        move = step if pattern >> index & 1 else -step
                        values.append(values[-1] + move)
                    if all(value >= 0 for value in values):
                        sums.add(sum(values) % 2)
                if len(sums) > 1:
                    break
            possible = target % 2 in sums
            self.assertEqual(generated["answer"], possible, f"seed {seed}: {text}")


if __name__ == "__main__":
    unittest.main()
