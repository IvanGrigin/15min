from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from problemgen.catalog.problem_templates import find_templates, list_modules, load_template_catalog
from problemgen.generation.template_generator import (
    evaluate_formula,
    generate_problem_from_template,
    registered_strategies,
)
from problemgen.worksheet.service import validate_items
from problemgen.worksheet.service import generate_worksheet_artifacts
from datetime import date, timedelta
from itertools import combinations, permutations
from math import factorial
import calendar
import itertools
import math


class TemplateGeneratorTests(unittest.TestCase):
    def test_catalog_has_unique_valid_template_ids(self) -> None:
        templates = load_template_catalog()
        self.assertGreaterEqual(len(templates), 8)
        self.assertEqual(len({template["template_id"] for template in templates}), len(templates))

    def test_every_template_can_generate_an_answer(self) -> None:
        expected = {"number": int, "multi": list, "text": str}
        for index, template in enumerate(load_template_catalog(), start=1):
            problem = generate_problem_from_template(
                template["module"], template["supported_difficulties"][0], rng=random.Random(index)
            )
            self.assertTrue(problem.problem_text)
            self.assertNotIn("{", problem.problem_text)
            self.assertIsInstance(problem.answer, expected[template.get("answer_type", "number")])

    def test_every_template_strategy_is_registered(self) -> None:
        available = registered_strategies()
        for template in load_template_catalog():
            self.assertIn(
                template["number_strategy"], available,
                msg=f"У шаблона {template['template_id']} нет зарегистрированной стратегии чисел.",
            )

    def test_no_template_is_fragile_across_seeds(self) -> None:
        # Страж против рассинхрона стратегии и constraints: каждый шаблон должен
        # генерироваться без ошибок на нескольких сложностях и сидах.
        failures = []
        for template in load_template_catalog():
            diffs = template.get("supported_difficulties", [template["difficulty"]])
            for difficulty in {diffs[0], diffs[len(diffs) // 2], diffs[-1]}:
                for seed in range(6):
                    try:
                        generate_problem_from_template(
                            template["module"], difficulty, rng=random.Random(seed * 131 + difficulty)
                        )
                    except Exception as error:  # noqa: BLE001 — фиксируем любой сбой генерации
                        failures.append(f"{template['template_id']}@d{difficulty}: {error}")
        self.assertEqual(failures, [], msg=f"Хрупкие шаблоны: {failures[:5]}")

    def test_ratio_split_is_never_degenerate(self) -> None:
        templates = find_templates("ages", 5)
        self.assertTrue(templates)
        self.assertTrue(all(template["module"] == "ages" for template in templates))

    def test_a04_product_comparison_matches_direct_calculation(self) -> None:
        """A04 возвращает правильный порядок и разность без округления."""
        for seed in range(100):
            problem = generate_problem_from_template("compare_products", 6, rng=random.Random(seed))
            values = problem.variables
            first = values["a"] * values["mid"] * values["b"]
            second = values["c"] * values["mid"] * values["d"]
            expected_label = "первое" if first > second else ("второе" if second > first else "поровну")
            self.assertEqual(problem.answer, [expected_label, abs(first - second)])

    def test_module_filter_returns_matching_static_templates(self) -> None:
        templates = find_templates("joint_work", 4)
        self.assertTrue(templates)
        self.assertTrue(all(template["module"] == "joint_work" for template in templates))

    def test_formula_evaluator_rejects_function_calls(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("open('bad')", {})

    def test_formula_evaluator_rejects_non_whitelisted_function(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("eval('1')", {})

    def test_formula_evaluator_supports_extended_operators(self) -> None:
        self.assertEqual(evaluate_formula("a // b", {"a": 17, "b": 5}), 3)
        self.assertEqual(evaluate_formula("a % b", {"a": 17, "b": 5}), 2)
        self.assertEqual(evaluate_formula("a ** b", {"a": 2, "b": 10}), 1024)

    def test_formula_evaluator_caps_exponent(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_formula("2 ** n", {"n": 1000})

    def test_formula_evaluator_supports_whitelisted_functions(self) -> None:
        self.assertEqual(evaluate_formula("gcd(a, b)", {"a": 24, "b": 36}), 12)
        self.assertEqual(evaluate_formula("lcm(a, b)", {"a": 4, "b": 6}), 12)
        self.assertEqual(evaluate_formula("comb(n, k)", {"n": 5, "k": 2}), 10)
        self.assertEqual(evaluate_formula("count_digit(7, 1, 100)", {}), 20)
        self.assertEqual(evaluate_formula("digit_sum(n)", {"n": 12345}), 15)
        self.assertEqual(evaluate_formula("first_digit(987654)", {}), 9)
        self.assertEqual(evaluate_formula("inverse_truncated_twice(20, 5, 137)", {}), 137)
        self.assertEqual(evaluate_formula("c_count_digit_sum(3, 4)", {}), 10)
        self.assertEqual(evaluate_formula("factorial(n)", {"n": 5}), 120)
        self.assertEqual(evaluate_formula("perm_multiset(a, b)", {"a": 3, "b": 2}), 10)

    def test_formula_evaluator_supports_multi_and_text_answers(self) -> None:
        self.assertEqual(evaluate_formula("[max(a, b), abs(a - b)]", {"a": 9, "b": 4}), [9, 5])
        self.assertEqual(evaluate_formula("weekday_after(0, 8)", {}), "вторник")

    def test_extended_engine_templates_generate_expected_answer_types(self) -> None:
        cases = ["k01_truth_liars", "k03_elevator_reachability", "k04_domino_parity", "k08_state_reachability"]
        for module in cases:
            problem = generate_problem_from_template(module, 4, rng=random.Random(11))
            self.assertIsInstance(problem.answer, str)
            self.assertNotIn("{", problem.problem_text)

    def test_every_visible_module_accepts_a_valid_item(self) -> None:
        modules = list_modules()
        items = [
            {"module": module["id"], "difficulty": module["available_difficulties"][0]}
            for module in (modules * 5)[:5]
        ]
        self.assertEqual(validate_items(items), items)

    def test_items_require_exactly_five_entries(self) -> None:
        with self.assertRaises(ValueError):
            validate_items([{"module": "ages", "difficulty": 3}])

    def test_items_reject_module_without_matching_difficulty(self) -> None:
        items = [{"module": "Несуществующий модуль", "difficulty": 1} for _ in range(5)]
        with self.assertRaises(ValueError):
            validate_items(items)

    @patch("problemgen.worksheet.service.render_worksheet")
    def test_worksheet_has_exactly_five_template_problems(self, render_worksheet: object) -> None:
        items = [
            {"module": "joint_work", "difficulty": 4},
            {"module": "ages", "difficulty": 3},
            {"module": "compare_products", "difficulty": 4},
            {"module": "linear_equation_chain", "difficulty": 3},
            {"module": "movement", "difficulty": 4},
        ]
        with tempfile.TemporaryDirectory() as directory:
            artifact = generate_worksheet_artifacts(items=items, output_dir=directory, seed=42)
            self.assertEqual(len(artifact.problems), 5)
            self.assertEqual(len(artifact.items), 5)
            self.assertTrue(Path(artifact.student_json_path).exists())
            self.assertTrue(Path(artifact.answers_json_path).exists())
            self.assertEqual(render_worksheet.call_count, 1)



    def test_digits_group_c_answers_match_independent_enumeration(self) -> None:
            """Тридцать seed на семейство: проверяем модель отдельно от formula engine."""
            modules = (
                "c01_interval_parity",
                "c02_contains_digit",
                "c03_avoids_digit",
                "digit_count",
                "c05_alternating_parity",
                "c06_last_digit_power",
                "c07_digit_sum_count",
                "c08_first_digit_gt_last",
                "c09_distinct_digit_numbers",
                "c10_missing_addend_digit",
                "c11_same_suffix_numbers",
                "c12_consecutive_digit_block",
            )
            for module in modules:
                for seed in range(30):
                    problem = generate_problem_from_template(module, 1, rng=random.Random(seed))
                    values = problem.variables
                    if module == "c01_interval_parity":
                        expected = sum(number % 2 == 0 for number in range(values["left"], values["right"] + 1))
                    elif module == "c02_contains_digit":
                        expected = sum(str(values["digit"]) in str(number) for number in range(values["left"], values["right"] + 1))
                    elif module == "c03_avoids_digit":
                        expected = sum(str(values["digit"]) not in str(number) for number in range(values["left"], values["right"] + 1))
                    elif module == "digit_count":
                        expected = "".join(str(number) for number in range(values["lo"], values["hi"] + 1)).count(str(values["digit"]))
                    elif module == "c05_alternating_parity":
                        expected = sum(
                            all((int(left) - int(right)) % 2 for left, right in zip(str(number), str(number)[1:]))
                            for number in range(10 ** (values["length"] - 1), 10 ** values["length"])
                        )
                    elif module == "c06_last_digit_power":
                        expected = pow(values["base"], values["exponent"], 10)
                    elif module == "c07_digit_sum_count":
                        expected = sum(
                            sum(map(int, str(number))) == values["target_sum"]
                            for number in range(10 ** (values["length"] - 1), 10 ** values["length"])
                        )
                    elif module == "c08_first_digit_gt_last":
                        expected = sum(
                            str(number)[0] > str(number)[-1]
                            for number in range(10 ** (values["length"] - 1), 10 ** values["length"])
                        )
                    elif module == "c09_distinct_digit_numbers":
                        expected = len(list(permutations(range(values["available"]), values["length"])))
                    elif module == "c10_missing_addend_digit":
                        expected = values["total"] - values["addend"]
                    elif module == "c11_same_suffix_numbers":
                        expected = [
                            values["first"] * 100 + values["suffix"],
                            values["second"] * 100 + values["suffix"],
                            values["third"] * 100 + values["suffix"],
                        ]
                    else:
                        candidates = [
                            start for start in range(1, 1001)
                            if sum(len(str(number)) for number in range(start, start + values["count"])) == values["total_digits"]
                            and start < 1000 < start + values["count"]
                        ]
                        self.assertEqual(len(candidates), 1)
                        expected = candidates[0]
                    self.assertEqual(problem.answer, expected, msg=f"{module}, seed={seed}")

    def test_combinatorics_group_f_answers_match_independent_enumeration(self) -> None:
            """Тридцать seed на семейство: ответы не доверяются formula движка."""
            modules = (
                "comb_permutations_distinct",
                "comb_permutations_repeated",
                "comb_bounded_words",
                "comb_unknown_alphabet",
                "comb_team_selection",
                "comb_round_robin_pairs",
                "comb_elimination_matches",
                "comb_lattice_paths",
                "comb_weighted_grid_paths",
                "comb_nonattacking_rooks",
                "comb_pigeonhole_target",
            )
            for module in modules:
                for seed in range(30):
                    problem = generate_problem_from_template(module, 5, rng=random.Random(seed))
                    values = problem.variables
                    if module == "comb_permutations_distinct":
                        expected = factorial(values["n"])
                    elif module == "comb_permutations_repeated":
                        letters = "А" * values["first_count"] + "Б" * values["second_count"]
                        expected = len(set(permutations(letters)))
                    elif module == "comb_bounded_words":
                        expected = sum(values["alphabet_size"] ** length for length in range(1, values["max_length"] + 1))
                    elif module == "comb_unknown_alphabet":
                        expected = "".join(list(permutations(values["order"]))[values["target_rank"] - 1])
                    elif module == "comb_team_selection":
                        expected = len(list(combinations(range(values["members"]), values["team_size"])))
                    elif module == "comb_round_robin_pairs":
                        expected = len(list(combinations(range(values["players"]), 2)))
                    elif module == "comb_elimination_matches":
                        expected = values["players"] - 1
                    elif module == "comb_lattice_paths":
                        expected = len(list(combinations(range(values["right_steps"] + values["up_steps"]), values["up_steps"])))
                    elif module == "comb_weighted_grid_paths":
                        weights = [values[f"w{index}"] for index in range(1, 10)]
                        expected = 0
                        for up_steps in combinations(range(4), 2):
                            row = column = 0
                            total = weights[0]
                            for step in range(4):
                                if step in up_steps:
                                    row += 1
                                else:
                                    column += 1
                                total += weights[row * 3 + column]
                            expected += total == values["target"]
                    elif module == "comb_nonattacking_rooks":
                        cells = list(range(values["board_size"] ** 2))
                        expected = sum(
                            white // values["board_size"] != black // values["board_size"]
                            and white % values["board_size"] != black % values["board_size"]
                            for white in cells for black in cells
                        )
                    else:
                        expected = values["non_target"] + 1
                    self.assertEqual(problem.answer, expected, msg=f"{module}, seed={seed}")

    def test_geometry_helpers_match_independent_enumeration(self) -> None:
            # G05: независимый перебор сторон подтверждает подсчёт факторной формулы.
            for value in range(1, 80):
                by_enumeration = sum(
                    1
                    for side_a in range(1, 100)
                    for side_b in range(side_a, 100)
                    if side_a * side_b - 2 * (side_a + side_b) == value
                )
                self.assertEqual(
                    evaluate_formula("count_integer_rectangle_sides(c)", {"c": value}),
                    by_enumeration,
                )

            # G08: перебор положений каждого квадрата, не та же формула, что в helper.
            for rows in range(1, 8):
                for columns in range(1, 8):
                    by_enumeration = sum(
                        1
                        for size in range(1, min(rows, columns) + 1)
                        for _top in range(rows - size + 1)
                        for _left in range(columns - size + 1)
                    )
                    self.assertEqual(
                        evaluate_formula("grid_square_count(r, c)", {"r": rows, "c": columns}),
                        by_enumeration,
                    )

    def test_calendar_functions_match_datetime_and_calendar(self) -> None:
            """Календарные helper'ы сверяются со стандартной библиотекой независимо."""
            weekdays = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
            rng = random.Random(20260715)
            for _ in range(300):
                year = rng.randint(1, 9999)
                month = rng.randint(1, 12)
                days = calendar.monthrange(year, month)[1]
                day = rng.randint(1, days)
                weekday = rng.randint(0, 6)
                variables = {"year": year, "month": month, "day": day, "weekday": weekday}
                self.assertEqual(evaluate_formula("days_in_month(year, month)", variables), days)
                self.assertEqual(
                    evaluate_formula("weekday_of_date(year, month, day)", variables),
                    weekdays[date(year, month, day).weekday()],
                )
                self.assertEqual(
                    evaluate_formula("count_weekday_in_month(year, month, weekday)", variables),
                    sum(1 for week in calendar.monthcalendar(year, month) for value in week if value and date(year, month, value).weekday() == weekday),
                )

    def test_calendar_templates_match_independent_bruteforce(self) -> None:
            """Каждый I01–I03 шаблон проверяется на 30 сидах без helper'ов движка."""
            weekdays = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
            expected_by_module = {
                "calendar_weekday_date": {"i01_weekday_after_real_date_001", "i01_weekday_of_real_date_002"},
                "calendar_weekday_counts": {"i02_count_mondays_february_001", "i02_may_condition_first_monday_002"},
                "calendar_last_weekday_possibilities": {"i03_last_thursday_may_ordinals_001"},
                "calendar_nth_weekday": {"i03_fourth_thursday_may_002"},
            }
            seen: dict[str, int] = {}
            for module, expected_ids in expected_by_module.items():
                for seed in range(2000):
                    problem = generate_problem_from_template(module, 6, rng=random.Random(seed))
                    variables = problem.variables
                    if problem.template_id == "i01_weekday_after_real_date_001":
                        expected = weekdays[(date(variables["year"], variables["month"], variables["day"]) + timedelta(days=variables["days"])).weekday()]
                    elif problem.template_id == "i01_weekday_of_real_date_002":
                        expected = weekdays[date(variables["year"], variables["month"], variables["day"]).weekday()]
                    elif problem.template_id == "i02_count_mondays_february_001":
                        expected = sum(1 for week in calendar.monthcalendar(variables["year"], 2) for value in week if value and date(variables["year"], 2, value).weekday() == 0)
                    elif problem.template_id == "i02_may_condition_first_monday_002":
                        may = calendar.monthcalendar(variables["year"], 5)
                        saturdays = sum(1 for week in may if week[5])
                        fridays = sum(1 for week in may if week[4])
                        self.assertGreater(saturdays, fridays)
                        expected = next(value for week in calendar.monthcalendar(variables["year"], 9) for value in [week[0]] if value)
                    elif problem.template_id == "i03_last_thursday_may_ordinals_001":
                        expected = [date(2025, 5, value).timetuple().tm_yday for value in range(25, 32)]
                    elif problem.template_id == "i03_fourth_thursday_may_002":
                        expected = [value for week in calendar.monthcalendar(variables["year"], 5) for value in [week[3]] if value][3]
                    else:
                        self.fail(f"Неожиданный календарный шаблон: {problem.template_id}")
                    self.assertEqual(problem.answer, expected)
                    seen[problem.template_id] = seen.get(problem.template_id, 0) + 1
                    if all(seen.get(template_id, 0) >= 30 for template_id in expected_ids):
                        break
                else:
                    self.fail(f"Не удалось получить по 30 проверок каждого шаблона {module}: {seen}")
            self.assertEqual(set(seen), {
                "i01_weekday_after_real_date_001", "i01_weekday_of_real_date_002",
                "i02_count_mondays_february_001", "i02_may_condition_first_monday_002",
                "i03_last_thursday_may_ordinals_001", "i03_fourth_thursday_may_002",
            })
            self.assertTrue(all(count >= 30 for count in seen.values()))

    def test_timezone_templates_match_minute_arithmetic(self) -> None:
            """I04–I06 сверяются независимой арифметикой минут на 40 сидах."""
            for module, difficulty in (("time_zone_direct", 5), ("time_zone_multi_leg", 6), ("time_zone_turnaround", 8)):
                for seed in range(40):
                    problem = generate_problem_from_template(module, difficulty, rng=random.Random(seed))
                    values = problem.variables
                    if problem.template_id == "i04_convert_local_time_001":
                        minutes = values["departure_hour"] * 60 + values["departure_minute"] + values["timezone_diff"] * 60
                    elif problem.template_id == "i04_arrival_other_timezone_002":
                        minutes = values["departure_hour"] * 60 + values["departure_minute"] + values["duration_minutes"] + values["timezone_diff"] * 60
                    elif problem.template_id == "i05_two_flights_connection_001":
                        minutes = values["departure_hour"] * 60 + values["departure_minute"] + values["leg_one_minutes"] + values["wait_minutes"] + values["leg_two_minutes"] + (values["ab_diff"] + values["bc_diff"]) * 60
                    elif problem.template_id == "i06_turnaround_eastbound_ratio_001":
                        total = values["arrival_hour"] * 60 + values["arrival_minute"] - values["timezone_diff"] * 60 - values["departure_hour"] * 60 - values["departure_minute"]
                        minutes = values["departure_hour"] * 60 + values["departure_minute"] + total // (values["east_ratio"] + 1) * values["east_ratio"]
                    else:
                        self.fail(f"Неожиданный шаблон часового пояса: {problem.template_id}")
                    hours, minutes = divmod(minutes % 1440, 60)
                    self.assertEqual(problem.answer, f"{hours:02d}:{minutes:02d}")

    def test_group_k_templates_have_independently_verified_answers(self) -> None:
            """Сверяем математику K01--K08 отдельно от answer_formula и helper-ов."""
            modules = {
                "k01_truth_liars": str,
                "k02_one_wrong_equation": int,
                "k03_elevator_reachability": str,
                "k04_domino_parity": str,
                "k05_neighbor_difference": str,
                "k06_guaranteed_draws": list,
                "k07_ordered_clues": str,
                "k08_state_reachability": str,
            }
            for module, expected_type in modules.items():
                for seed in range(40):
                    problem = generate_problem_from_template(
                        module, seed % 10 + 1, rng=random.Random(10_000 + seed)
                    )
                    self.assertIsInstance(problem.answer, expected_type)
                    values = problem.variables
                    if module == "k02_one_wrong_equation":
                        equalities = [
                            values["multiplier_1"] * problem.answer == values["result_1"],
                            values["multiplier_2"] * problem.answer == values["result_2"],
                            values["multiplier_3"] * problem.answer == values["result_3"],
                        ]
                        self.assertEqual(sum(equalities), 2)
                    elif module in {"k03_elevator_reachability", "k08_state_reachability"}:
                        expected = "можно" if values["difference"] % math.gcd(
                            values["up"], values["down"]
                        ) == 0 else "нельзя"
                        self.assertEqual(problem.answer, expected)
                    elif module == "k04_domino_parity":
                        self.assertEqual(
                            problem.answer,
                            "можно" if values["rows"] * values["columns"] % 2 == 0 else "нельзя",
                        )
                    elif module == "k05_neighbor_difference":
                        numerator = 2 * values["total"] - values["count"] * (
                            values["count"] - 1
                        ) * values["step"]
                        expected = "можно" if numerator > 0 and numerator % (
                            2 * values["count"]
                        ) == 0 else "нельзя"
                        self.assertEqual(problem.answer, expected)
                    elif module == "k06_guaranteed_draws":
                        red, blue, green = problem.answer
                        self.assertEqual(red + blue + green, values["total"])
                        self.assertEqual(values["red_draw"], values["total"] - red + 1)
                        self.assertEqual(values["blue_draw"], values["total"] - blue + 1)
                    elif module == "k01_truth_liars":
                        solutions = [
                            roles for roles in itertools.product((False, True), repeat=3)
                            if roles[0] == (not roles[1])
                            and roles[1] == (not roles[2])
                            and roles[2] == (roles[0] and roles[1])
                        ]
                        self.assertEqual(solutions, [(False, True, False)])
                        self.assertEqual(problem.answer, "Борис")
                    else:  # k07_ordered_clues
                        solutions = [
                            places for places in itertools.permutations((1, 2, 3))
                            if places[0] != 1 and places[1] < places[2] and places[2] != 3
                        ]
                        self.assertEqual(solutions, [(3, 1, 2)])
                        self.assertEqual(problem.answer, "Борис")

if __name__ == "__main__":
    unittest.main()
