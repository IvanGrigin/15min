from __future__ import annotations

import unittest

from problemgen.generation.clock_templates import generate_clock_problem
from problemgen.generation.age_templates import generate_age_problem
from problemgen.generation.grid_templates import generate_grid_problem
from problemgen.generation.logic_templates import generate_logic_problem
from problemgen.generation.plane_geometry_templates import generate_plane_geometry_problem
from problemgen.generation.ratio_templates import generate_ratio_problem
from problemgen.generation.sets_templates import generate_sets_problem
from problemgen.russian.agreement import count_phrase_ru, count_with_word_ru


class RussianVariableAgreementTests(unittest.TestCase):
    def test_count_helpers_cover_russian_numeral_edges(self) -> None:
        forms = ("минута", "минуты", "минут")
        self.assertEqual(
            [count_with_word_ru(number, forms) for number in (1, 2, 5, 11, 21, 22, 25)],
            ["1 минута", "2 минуты", "5 минут", "11 минут", "21 минута", "22 минуты", "25 минут"],
        )
        self.assertEqual(
            count_phrase_ru(5, ("квадратную дырку", "квадратные дырки", "квадратных дырок")),
            "5 квадратных дырок",
        )

    def test_grid_hole_templates_agree_with_the_generated_count(self) -> None:
        forms = ("непересекающуюся квадратную дырку", "непересекающиеся квадратные дырки", "непересекающихся квадратных дырок")
        for generator, template_id in (
            (generate_plane_geometry_problem, "geometry_012_grid_holes"),
            (generate_grid_problem, "grid_004_inverse_holes"),
        ):
            for seed in range(40):
                problem = generator(template_id, seed=seed)
                count = problem.parameters["hole_count"]
                self.assertIn(count_phrase_ru(count, forms), problem.problem_text)

    def test_clock_offsets_and_ratio_character_verbs_are_agreed(self) -> None:
        for seed in range(40):
            drift = generate_clock_problem("clock_004_drifting_watches", seed=seed)
            self.assertIn(count_with_word_ru(drift.parameters["fast_minutes_per_day"], ("минуту", "минуты", "минут")), drift.problem_text)
            self.assertIn(count_with_word_ru(drift.parameters["slow_minutes_per_day"], ("минуту", "минуты", "минут")), drift.problem_text)

            ratio = generate_ratio_problem("ratios_011_box_conservation", seed=seed)
            characters = ratio.characters or []
            self.assertEqual(len(characters), 2)
            self.assertNotIn("Нюша переложил", ratio.problem_text)
            self.assertNotIn("Нюша проверил", ratio.problem_text)

    def test_people_counts_and_following_people_are_agreed(self) -> None:
        for seed in range(40):
            club = generate_sets_problem("sets_004_club_inclusion_exclusion", seed=seed)
            self.assertIn(
                count_with_word_ru(club.parameters["total_people"], ("человек", "человека", "человек")),
                club.problem_text,
            )
            logic = generate_logic_problem("logic_002_circular_liars", seed=seed)
            self.assertIn(
                count_with_word_ru(logic.parameters["following_count"], ("человек", "человека", "человек")),
                logic.problem_text,
            )

    def test_age_templates_keep_uninflected_character_names_outside_cases(self) -> None:
        for template_id in ("age_002_age_difference", "age_003_future_age", "age_004_family_sum"):
            problem = generate_age_problem(template_id, seed=19)
            self.assertIn("Персонаж", problem.problem_text)
            self.assertNotIn("сейчас", problem.problem_text)


if __name__ == "__main__":
    unittest.main()
