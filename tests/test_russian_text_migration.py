"""Регрессии reviewed русских формулировок active templates."""
from __future__ import annotations

import unittest

from problemgen.generation.age_templates import generate_age_problem
from problemgen.generation.calendar_templates import generate_calendar_problem
from problemgen.generation.clock_templates import generate_clock_problem
from problemgen.generation.grid_templates import generate_grid_problem
from problemgen.generation.logic_templates import generate_logic_problem
from problemgen.generation.money_templates import generate_money_problem
from problemgen.generation.parity_templates import generate_parity_problem, has_alternating_adjacent_parity
from problemgen.generation.quantity_templates import generate_quantity_problem


class RussianTextMigrationTests(unittest.TestCase):
    def test_age_templates_use_named_reviewed_cases_and_pronouns(self) -> None:
        for seed in range(100):
            difference = generate_age_problem("age_002_age_difference", seed=seed)
            self.assertNotIn("старший старше младшего", difference.problem_text)
            self.assertNotIn(":", difference.problem_text)
            future = generate_age_problem("age_003_future_age", seed=seed)
            self.assertNotIn("персонажу по имени", future.problem_text)
            self.assertNotIn("ему или ей", future.problem_text)
            self.assertTrue(" ему " in future.problem_text or " ей " in future.problem_text)

    def test_multiplication_cards_are_named_and_use_standard_sign(self) -> None:
        for seed in range(100):
            problem = generate_logic_problem("logic_001_one_wrong_product", seed=seed)
            self.assertIn("Учитель дал трём участникам", problem.problem_text)
            self.assertIn("В трёх карточках записаны решённые примеры", problem.problem_text)
            self.assertEqual(problem.parameters["participant_count"], 3)
            self.assertEqual(problem.problem_text.count("пример "), 3)
            self.assertIn(" × ", problem.problem_text)

    def test_units_and_named_owners_are_rendered(self) -> None:
        for seed in range(100):
            letter_p = generate_grid_problem("grid_003_letter_p_cells", seed=seed)
            self.assertGreaterEqual(letter_p.problem_text.count("клет"), 4)
            tram = generate_calendar_problem("calendar_004_circular_tram_interval", seed=seed)
            self.assertIn("проходит полный круговой маршрут за", tram.problem_text)
            self.assertNotIn("маршруту длиной", tram.problem_text)
            drift = generate_clock_problem("clock_004_drifting_watches", seed=seed)
            self.assertEqual(drift.problem_text.count("Часы "), 1)
            self.assertIn(", а часы ", drift.problem_text)

    def test_split_bill_and_fraction_prose_name_the_subject(self) -> None:
        for seed in range(100):
            bill = generate_money_problem("money_004_split_bill", seed=seed)
            self.assertNotIn("первой доли", bill.problem_text)
            self.assertNotIn("до равной доли", bill.problem_text)
            self.assertGreaterEqual(bill.answer, 1)
            bridge = generate_quantity_problem("quantity_003_bridge", seed=seed)
            self.assertNotIn("одной 3-й", bridge.problem_text)
            self.assertNotIn("одной 4-й", bridge.problem_text)

    def test_alternating_parity_contract_uses_rendered_list(self) -> None:
        for seed in range(100):
            problem = generate_parity_problem("parity_001_adjacent_digit_classification_sum", seed=seed)
            numbers = problem.parameters["candidate_numbers"]
            qualifying = [number for number in numbers if has_alternating_adjacent_parity(number)]
            self.assertEqual(len(numbers), 5)
            self.assertEqual(len(numbers), len(set(numbers)))
            self.assertTrue(2 <= len(qualifying) <= 5)
            self.assertEqual(problem.answer, sum(qualifying))
            self.assertIn("любые две соседние цифры имеют разную чётность", problem.problem_text)


if __name__ == "__main__":
    unittest.main()
