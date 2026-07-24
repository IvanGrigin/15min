"""Независимый bounded-аудит критических математических шаблонов."""
from __future__ import annotations

from fractions import Fraction
from math import gcd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from problemgen.generation.clock_templates import generate_clock_problem
from problemgen.generation.cube_templates import generate_cube_problem
from problemgen.generation.motion_templates import generate_motion_problem
from problemgen.generation.quantity_templates import generate_quantity_problem
from problemgen.generation.sets_templates import generate_sets_problem


def main() -> int:
    checked = 0
    for seed in range(100):
        train = generate_motion_problem("motion_004_train_overlap", seed=seed)
        expected = Fraction(sum(train.parameters["lengths"]) * 3600, sum(train.parameters["speeds"]) * 1000)
        assert expected.denominator == 1 and train.answer == expected.numerator
        painted = generate_cube_problem("cube_002_painted_cubes", seed=seed)
        p = painted.parameters
        assert painted.answer == 4 * (p["a"] - 2) + 4 * (p["b"] - 2) + 4 * (p["c"] - 2)
        water = generate_cube_problem("cube_003_water_depth", seed=seed)
        assert water.answer == water.parameters["volume_l"] // (water.parameters["width_m"] * water.parameters["length_m"])
        visible = generate_cube_problem("cube_005_visible_faces_sum", seed=seed)
        assert visible.answer == 6 * visible.parameters["side"] ** 2
        watermelon = generate_quantity_problem("quantity_004_watermelon", seed=seed)
        assert watermelon.answer * 2 == watermelon.parameters["initial_mass"]
        bridge = generate_quantity_problem("quantity_003_bridge", seed=seed)
        assert bridge.answer * (bridge.parameters["denominator"] - 2) == bridge.parameters["river_width"] * bridge.parameters["denominator"]
        drift = generate_clock_problem("clock_004_drifting_watches", seed=seed)
        relative = drift.parameters["fast_minutes_per_day"] + drift.parameters["slow_minutes_per_day"]
        assert drift.answer == 1440 // gcd(relative, 1440)
        fields = generate_sets_problem("sets_001_two_fields", seed=seed)
        assert fields.answer == 6 * fields.parameters["game_hours"]
        checked += 8
    print(f"OK: independently checked {checked} critical instances (100 seeds per template).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
