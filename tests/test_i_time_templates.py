from __future__ import annotations

import random
import unittest

from problemgen.generation.template_generator import generate_problem_from_template


def _format_clock(minutes: int) -> str:
    return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


def _format_clock_seconds(seconds: int) -> str:
    return f"{(seconds // 3600) % 24:02d}:{(seconds // 60) % 60:02d}:{seconds % 60:02d}"


def _next_distinct_display(start_seconds: int, occurrence: int) -> str:
    found = 0
    for moment in range(start_seconds + 1, start_seconds + 2 * 24 * 60 * 60 + 1):
        if len(set(_format_clock_seconds(moment).replace(":", ""))) == 6:
            found += 1
            if found == occurrence:
                return _format_clock_seconds(moment)
    raise AssertionError("Не найдено табло с шестью различными цифрами.")


class ITimeTemplateTests(unittest.TestCase):
    def test_i_templates_answers_match_independent_calculations(self) -> None:
        weekdays = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
        checks = {
            "weekday_after_days": lambda v: weekdays[(v["start_weekday"] + v["days"]) % 7],
            "weekday_counts_month": lambda v: sum((v["start_weekday"] + day) % 7 == v["target_weekday"] for day in range(v["days"])),
            "nth_weekday_month": lambda v: [day + 1 for day in range(v["days"]) if (v["start_weekday"] + day) % 7 == v["target_weekday"]][v["occurrence"] - 1],
            "timezone_direct": lambda v: _format_clock(v["hour"] * 60 + v["minute"] + v["offset"] * 60),
            "timezone_two_leg": lambda v: [
                _format_clock(v["hour"] * 60 + v["minute"] + v["first_flight"] + v["offset"] * 60),
                _format_clock(v["hour"] * 60 + v["minute"] + v["first_flight"] + v["wait"] + v["second_flight"]),
            ],
            "turnaround_timezone": lambda v: _format_clock(v["hour"] * 60 + v["minute"] + v["outward"] + v["returning"] - v["behind_hours"] * 60),
            "clock_drift": lambda v: v["gap"] // (v["fast"] + v["slow"]),
            "digital_clock_display": lambda v: _next_distinct_display(v["start_hour"] * 3600 + v["start_minute"] * 60 + v["start_second"], v["occurrence"]),
        }
        for module, independently_calculated in checks.items():
            for seed in range(12):
                problem = generate_problem_from_template(module, 7, rng=random.Random(seed))
                self.assertEqual(problem.answer, independently_calculated(problem.variables), msg=module)


if __name__ == "__main__":
    unittest.main()
