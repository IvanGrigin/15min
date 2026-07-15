from __future__ import annotations

import itertools
import random
import unittest

from problemgen.generation.template_generator import (
    _grid_internal_partitions,
    _grid_partitions_with_rectangular_hole,
    generate_problem_from_template,
)


def _brute_grid_partitions(rows: int, cols: int, hole_rows: int = 0, hole_cols: int = 0) -> int:
    """Независимый перебор общих сторон оставшихся клеток."""
    top, left = (rows - hole_rows) // 2, (cols - hole_cols) // 2
    cells = {
        (row, col)
        for row in range(rows)
        for col in range(cols)
        if not (hole_rows and top <= row < top + hole_rows and left <= col < left + hole_cols)
    }
    return sum((row + 1, col) in cells for row, col in cells) + sum(
        (row, col + 1) in cells for row, col in cells
    )


class HGridAndSolidTemplateTests(unittest.TestCase):
    def test_grid_partition_helpers_match_small_grid_enumeration(self) -> None:
        for rows, cols in itertools.product(range(2, 9), repeat=2):
            self.assertEqual(_grid_internal_partitions(rows, cols), _brute_grid_partitions(rows, cols))
            for hole_rows in range(1, rows - 1):
                for hole_cols in range(1, cols - 1):
                    self.assertEqual(
                        _grid_partitions_with_rectangular_hole(rows, cols, hole_rows, hole_cols),
                        _brute_grid_partitions(rows, cols, hole_rows, hole_cols),
                    )

    def test_h_templates_answers_match_independent_calculations(self) -> None:
        checks = {
            "cutting_boards": lambda v: v["pieces"] - 1,
            "cuboid_blocks": lambda v: (v["big_a"] // v["block_a"]) * (v["big_b"] // v["block_b"]) * (v["big_c"] // v["block_c"]),
            "cuboid_cutting_compare": lambda v: abs((v["side"] // v["first_step"]) ** 3 - (v["side"] // v["second_step"]) ** 3),
            "painted_cube_faces": lambda v: 8 + 6 * (v["side"] - 2) ** 2,
            "surface_paint_scale": lambda v: v["base_paint"] * v["scale"] ** 2,
            "grid_partitions": lambda v: _brute_grid_partitions(v["rows"], v["cols"]),
            "grid_partitions_holes": lambda v: _brute_grid_partitions(v["rows"], v["cols"], v["hole_rows"], v["hole_cols"]),
            "polyomino_boundary": lambda v: 2 * v["thickness"] * v["height"] + v["thickness"] * (v["width"] - 2 * v["thickness"]),
            "cube_face_labels": lambda v: 36 * v["side"] ** 2,
        }
        for module, independently_calculated in checks.items():
            for seed in range(12):
                problem = generate_problem_from_template(module, 7, rng=random.Random(seed))
                self.assertEqual(problem.answer, independently_calculated(problem.variables), msg=module)


if __name__ == "__main__":
    unittest.main()
