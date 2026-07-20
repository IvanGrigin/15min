from __future__ import annotations

import html
import hmac
import json
import mimetypes
import random
import secrets
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from problemgen.template_studio.catalogue import active_template_metadata, active_templates
from problemgen.template_studio.runtime import generate_active_template, normalize_value
from problemgen.template_studio.service import TemplateStudioService

from problemgen.generation.arithmetic_templates import (
    arithmetic_template_metadata,
    generate_arithmetic_problem,
    generate_arithmetic_worksheet,
    load_arithmetic_templates,
)
from problemgen.generation.comparison_templates import (
    comparison_template_metadata,
    generate_comparison_problem_from_module,
)
from problemgen.generation.equation_templates import (
    equation_template_metadata,
    generate_equation_problem_from_module,
)
from problemgen.generation.system_equation_templates import (
    generate_system_equation_problem_from_module,
    system_equation_template_metadata,
)
from problemgen.generation.sequence_templates import (
    generate_sequence_problem_from_module,
    sequence_template_metadata,
)
from problemgen.generation.integer_interval_templates import (
    generate_integer_interval_problem_from_module,
    integer_interval_template_metadata,
)
from problemgen.generation.divisibility_templates import generate_divisibility_problem_from_module, divisibility_template_metadata
from problemgen.generation.digits_templates import (
    digits_template_metadata,
    generate_digits_problem_from_module,
)
from problemgen.generation.ratio_templates import generate_ratio_problem_from_module, ratio_template_metadata
from problemgen.generation.factor_product_templates import (
    factor_product_template_metadata,
    generate_factor_product_problem_from_module,
)
from problemgen.generation.combinatorics_templates import combinatorics_template_metadata, generate_combinatorics_problem_from_module
from problemgen.generation.pigeonhole_templates import pigeonhole_template_metadata, generate_pigeonhole_problem_from_module
from problemgen.generation.parity_templates import parity_template_metadata, generate_parity_problem_from_module
from problemgen.generation.process_templates import process_template_metadata, generate_process_problem_from_module
from problemgen.generation.calendar_templates import calendar_template_metadata, generate_calendar_problem_from_module
from problemgen.generation.clock_templates import clock_template_metadata, generate_clock_problem_from_module
from problemgen.generation.time_zone_templates import time_zone_template_metadata, generate_time_zone_problem_from_module
from problemgen.generation.motion_templates import motion_template_metadata, generate_motion_problem_from_module
from problemgen.generation.work_templates import work_template_metadata, generate_work_problem_from_module
from problemgen.generation.money_templates import money_template_metadata, generate_money_problem_from_module
from problemgen.generation.age_templates import age_template_metadata, generate_age_problem_from_module
from problemgen.generation.counting_objects_templates import counting_template_metadata, generate_counting_problem_from_module
from problemgen.generation.sets_templates import generate_sets_problem_from_module, sets_template_metadata
from problemgen.generation.plane_geometry_templates import generate_plane_geometry_problem_from_module, plane_geometry_template_metadata
from problemgen.generation.grid_templates import generate_grid_problem_from_module, grid_template_metadata
from problemgen.generation.cube_templates import cube_template_metadata, generate_cube_problem_from_module
from problemgen.generation.quantity_templates import generate_quantity_problem_from_module, quantity_template_metadata
from problemgen.generation.line_templates import generate_line_problem_from_module, line_template_metadata
from problemgen.generation.logic_templates import generate_logic_problem_from_module, logic_template_metadata
from problemgen.generation.equation_word_templates import generate_equation_word_problem_from_module, equation_word_template_metadata
from problemgen.generation.alphabetic_order_templates import generate_alphabetic_order_problem_from_module, alphabetic_order_template_metadata
from problemgen.worksheet.all_tasks_site import (
    generate_problem_instance,
    recovered_templates,
    recovery_stats,
    unverified_templates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "generated"
ASSETS_ROOT = PROJECT_ROOT / "assets"
MIN_TASK_COUNT = 1
MAX_TASK_COUNT = 20
VERIFIED_MODULE_IDS = (
    "arithmetic",
    "equations",
    "systems_of_equations",
    "comparison_of_numbers_and_expressions",
    "sequences_progressions_and_sums",
    "ratios_fractions_proportions_and_percentages",
    "factors_products_and_factorials",
    "combinatorics_and_counting_variants",
    "pigeonhole_and_guaranteed_selection",
    "parity_invariants_strategies_and_moves",
    "number_processes_and_repeated_operations",
    "calendar_and_weekdays",
    "clocks_dials_and_electronic_displays",
    "time_zones_and_travel_schedules",
    "motion_speed_and_distance",
    "work_productivity_and_joint_actions",
    "money_purchases_prices_and_calculations",
    "ages_and_generations",
    "heads_legs_wheels_and_object_counts",
    "sets_clubs_acquaintances_and_tournaments",
    "plane_geometry_rectangles_squares_and_areas",
    "grid_figures_cuts_and_routes",
    "cubes_volume_and_spatial_geometry",
    "points_segments_and_positions_on_a_line",
    "quantities_units_weight_and_scaling",
    "logic_problems_and_condition_analysis",
    "word_problems_for_equation_setup",
    "alphabetic_order",
)
ARCHIVE_MODULE_ID = "all_tasks_archive"
RECOVERED_ARCHIVE_MODULE_ID = "all_tasks_recovered"
TEMPLATE_STUDIO_MAX_REQUEST_BYTES = 65_536
_TEMPLATE_STUDIO_CSRF_TOKEN = secrets.token_urlsafe(32)
_template_studio_service = TemplateStudioService()


def _validate_task_count(count: int) -> int:
    if not isinstance(count, int) or isinstance(count, bool) or not MIN_TASK_COUNT <= count <= MAX_TASK_COUNT:
        raise ValueError(f"Количество задач должно быть целым числом от {MIN_TASK_COUNT} до {MAX_TASK_COUNT}.")
    return count


def _combined_template_metadata() -> dict[str, Any]:
    arithmetic = arithmetic_template_metadata()
    equations = equation_template_metadata()
    systems = system_equation_template_metadata()
    comparisons = comparison_template_metadata()
    sequences = sequence_template_metadata()
    intervals = integer_interval_template_metadata()
    divisibility = divisibility_template_metadata()
    digits = digits_template_metadata()
    ratios = ratio_template_metadata()
    factors = factor_product_template_metadata()
    combinatorics = combinatorics_template_metadata()
    pigeonhole = pigeonhole_template_metadata()
    parity = parity_template_metadata()
    processes = process_template_metadata()
    calendars = calendar_template_metadata()
    clocks = clock_template_metadata()
    zones = time_zone_template_metadata()
    motions = motion_template_metadata()
    works = work_template_metadata()
    money = money_template_metadata()
    ages = age_template_metadata()
    counts = counting_template_metadata()
    sets = sets_template_metadata()
    geometry = plane_geometry_template_metadata()
    grids = grid_template_metadata()
    cubes = cube_template_metadata()
    quantities = quantity_template_metadata()
    lines = line_template_metadata()
    logic = logic_template_metadata()
    equation_words = equation_word_template_metadata()
    alphabetic = alphabetic_order_template_metadata()
    modules = list(arithmetic.get("modules", [])) + list(equations.get("modules", [])) + list(systems.get("modules", [])) + list(comparisons.get("modules", [])) + list(sequences.get("modules", [])) + list(intervals.get("modules", [])) + list(divisibility.get("modules", [])) + list(digits.get("modules", [])) + list(factors.get("modules", [])) + list(ratios.get("modules", [])) + list(combinatorics.get("modules", [])) + list(pigeonhole.get("modules", [])) + list(parity.get("modules", [])) + list(processes.get("modules", [])) + list(calendars.get("modules", [])) + list(clocks.get("modules", [])) + list(zones.get("modules", [])) + list(motions.get("modules", [])) + list(works.get("modules", [])) + list(money.get("modules", [])) + list(ages.get("modules", [])) + list(counts.get("modules", [])) + list(sets.get("modules", [])) + list(geometry.get("modules", [])) + list(grids.get("modules", [])) + list(cubes.get("modules", [])) + list(lines.get("modules", []))
    templates = list(arithmetic.get("templates", [])) + list(equations.get("templates", [])) + list(systems.get("templates", [])) + list(comparisons.get("templates", [])) + list(sequences.get("templates", [])) + list(intervals.get("templates", [])) + list(divisibility.get("templates", [])) + list(digits.get("templates", [])) + list(factors.get("templates", [])) + list(ratios.get("templates", [])) + list(combinatorics.get("templates", [])) + list(pigeonhole.get("templates", [])) + list(parity.get("templates", [])) + list(processes.get("templates", [])) + list(calendars.get("templates", [])) + list(clocks.get("templates", [])) + list(zones.get("templates", [])) + list(motions.get("templates", [])) + list(works.get("templates", [])) + list(money.get("templates", [])) + list(ages.get("templates", [])) + list(counts.get("templates", [])) + list(sets.get("templates", [])) + list(geometry.get("templates", [])) + list(grids.get("templates", [])) + list(cubes.get("templates", [])) + list(lines.get("templates", []))
    modules += list(quantities.get("modules", []))
    templates += list(quantities.get("templates", []))
    modules += list(logic.get("modules", []))
    templates += list(logic.get("templates", []))
    modules += list(equation_words.get("modules", []))
    templates += list(equation_words.get("templates", []))
    modules += list(alphabetic.get("modules", []))
    templates += list(alphabetic.get("templates", []))
    studio_templates = active_templates()
    studio_counts: dict[str, int] = {}
    for studio_template in studio_templates:
        module_id = studio_template.get("module_id")
        if isinstance(module_id, str):
            studio_counts[module_id] = studio_counts.get(module_id, 0) + 1
    modules = [
        {**module, "template_count": int(module.get("template_count", 0)) + studio_counts.get(module.get("module_id"), 0)}
        for module in modules
    ]
    templates += active_template_metadata()
    archive_stats = recovery_stats()
    recovered_archive_module = {
        "module_id": RECOVERED_ARCHIVE_MODULE_ID,
        "display_name": "Архив: восстановленные формулы",
        "title": "Проверенные выражения из общего корпуса",
        "template_count": archive_stats["recovered_templates"],
        "answer_status": "verified",
        "description": "Формула ответа восстановлена и проверена на исходных и новых числах.",
    }
    archive_module = {
        "module_id": ARCHIVE_MODULE_ID,
        "display_name": "Архив подготовленных шаблонов",
        "title": "Очищенные задания из общего корпуса",
        "template_count": archive_stats["unverified_templates"],
        "answer_status": "unverified",
        "description": "Тексты готовы, но формулы ответов для них ещё не восстановлены.",
    }
    return {
        "modules": modules + [recovered_archive_module, archive_module],
        "templates": templates,
        "stats": {
            "total_modules": len(modules),
            "total_templates": len(templates),
            "verified_answer_templates": len(templates),
            "archive_templates": archive_stats["recovered_templates"] + archive_stats["unverified_templates"],
            "recovered_archive_templates": archive_stats["recovered_templates"],
            "unverified_archive_templates": archive_stats["unverified_templates"],
            "catalog_templates": len(templates) + archive_stats["recovered_templates"] + archive_stats["unverified_templates"],
            "covered_source_problem_numbers": (
                int(arithmetic.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(equations.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(systems.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(comparisons.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(sequences.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(intervals.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(divisibility.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(digits.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(ratios.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(factors.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(combinatorics.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(pigeonhole.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(parity.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(processes.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(calendars.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(clocks.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(zones.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(motions.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(works.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(money.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(ages.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(counts.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(sets.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(geometry.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(grids.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(cubes.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(lines.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(quantities.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(logic.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(equation_words.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(alphabetic.get("stats", {}).get("covered_source_problem_numbers", 0))
            ),
        },
        "limits": {"min_task_count": MIN_TASK_COUNT, "max_task_count": MAX_TASK_COUNT, "default_task_count": 5},
    }


def _answer_to_text(answer: Any) -> str:
    if isinstance(answer, dict):
        if set(answer) == {"x", "y"}:
            return f"X = {answer['x']}, Y = {answer['y']}"
        return "; ".join(f"{key}: {value}" for key, value in answer.items())
    if isinstance(answer, list):
        return ", ".join(str(item) for item in answer)
    return str(answer)


def _generate_archive_problem(rng: random.Random) -> dict[str, Any]:
    template = rng.choice(unverified_templates())
    generated = generate_problem_instance(template, rng, require_changed=False)
    return {
        "module_id": ARCHIVE_MODULE_ID,
        "template_id": generated["template_id"],
        "source_problem_numbers": [generated["template_number"]],
        "rendered_problem": generated["rendered_problem"],
        "answer": "Ответ для архивного шаблона ещё не восстановлен.",
        "answer_value": None,
        "generated_values": generated["generated_values"],
        "answer_status": "unverified",
    }


def _generate_recovered_archive_problem(rng: random.Random) -> dict[str, Any]:
    template = rng.choice(recovered_templates())
    generated = generate_problem_instance(template, rng)
    answer = generated["answer"]
    return {
        "module_id": RECOVERED_ARCHIVE_MODULE_ID,
        "template_id": generated["template_id"],
        "source_problem_numbers": [generated["template_number"]],
        "rendered_problem": generated["rendered_problem"],
        "answer": _answer_to_text(answer),
        "answer_value": answer,
        "generated_values": generated["generated_values"],
        "answer_status": "verified",
    }


def generate_combined_worksheet_by_modules(
    module_ids: list[str], seed: int | None = None, *, task_count: int | None = None,
) -> dict[str, Any]:
    count = _validate_task_count(task_count if task_count is not None else len(module_ids))
    if len(module_ids) != count:
        raise ValueError("Число выбранных модулей должно совпадать с количеством задач.")
    rng = random.Random(seed)
    arithmetic_templates = load_arithmetic_templates()
    selected: list[dict[str, Any]] = []
    for position, module_id in enumerate(module_ids, start=1):
        studio_candidates = [item for item in active_templates() if item.get("module_id") == module_id]
        # Старые генераторы остаются основным источником заданий; активный
        # Studio-шаблон участвует в том же внутреннем случайном выборе модуля.
        if studio_candidates and rng.randrange(12) < len(studio_candidates):
            studio_template = rng.choice(studio_candidates)
            generated = generate_active_template(studio_template, rng)
            selected.append({
                "position": position,
                "module_id": module_id,
                "template_id": studio_template["template_id"],
                "source_problem_numbers": [studio_template.get("source_metadata", {}).get("problem_number")],
                "rendered_problem": generated["rendered_problem"],
                "answer": _answer_to_text(generated["answer"]),
                "answer_value": generated["answer"],
                "generated_values": {name: normalize_value(value) for name, value in generated["parameters"].items()},
                "answer_status": "verified",
            })
            continue
        if module_id == "arithmetic":
            template = rng.choice(arithmetic_templates)
            generated = generate_arithmetic_problem(str(template["id"]), rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "arithmetic",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "equations":
            generated = generate_equation_problem_from_module("equations", rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "equations",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "systems_of_equations":
            generated = generate_system_equation_problem_from_module("systems_of_equations", rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "systems_of_equations",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "comparison_of_numbers_and_expressions":
            generated = generate_comparison_problem_from_module("comparison_of_numbers_and_expressions", rng=rng)
            selected.append({
                "position": position,
                "module_id": "comparison_of_numbers_and_expressions",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": generated.answer_text,
                "answer_value": generated.answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "sequences_progressions_and_sums":
            generated = generate_sequence_problem_from_module("sequences_progressions_and_sums", rng=rng)
            selected.append({
                "position": position,
                "module_id": "sequences_progressions_and_sums",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": generated.answer_text,
                "answer_value": generated.answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "integer_interval_counting":
            generated = generate_integer_interval_problem_from_module("integer_interval_counting", rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "divisibility_multiples_remainders_primes":
            generated = generate_divisibility_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "digits_number_notation_and_cryptarithms":
            generated = generate_digits_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "ratios_fractions_proportions_and_percentages":
            generated = generate_ratio_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "factors_products_and_factorials":
            generated = generate_factor_product_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "combinatorics_and_counting_variants":
            generated = generate_combinatorics_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "pigeonhole_and_guaranteed_selection":
            generated = generate_pigeonhole_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "parity_invariants_strategies_and_moves":
            generated = generate_parity_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "number_processes_and_repeated_operations":
            generated = generate_process_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "calendar_and_weekdays":
            generated = generate_calendar_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "clocks_dials_and_electronic_displays":
            generated = generate_clock_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "time_zones_and_travel_schedules":
            generated = generate_time_zone_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "motion_speed_and_distance":
            generated = generate_motion_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "work_productivity_and_joint_actions":
            generated = generate_work_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "money_purchases_prices_and_calculations":
            generated = generate_money_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "ages_and_generations":
            generated = generate_age_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "heads_legs_wheels_and_object_counts":
            generated = generate_counting_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "sets_clubs_acquaintances_and_tournaments":
            generated = generate_sets_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "plane_geometry_rectangles_squares_and_areas":
            generated = generate_plane_geometry_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "grid_figures_cuts_and_routes":
            generated = generate_grid_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "cubes_volume_and_spatial_geometry":
            generated = generate_cube_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "points_segments_and_positions_on_a_line":
            generated = generate_line_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "quantities_units_weight_and_scaling":
            generated = generate_quantity_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "logic_problems_and_condition_analysis":
            generated = generate_logic_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "word_problems_for_equation_setup":
            generated = generate_equation_word_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "alphabetic_order":
            generated = generate_alphabetic_order_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == ARCHIVE_MODULE_ID:
            archive_problem = _generate_archive_problem(rng)
            archive_problem["position"] = position
            selected.append(archive_problem)
            continue
        if module_id == RECOVERED_ARCHIVE_MODULE_ID:
            archive_problem = _generate_recovered_archive_problem(rng)
            archive_problem["position"] = position
            selected.append(archive_problem)
            continue
        raise ValueError(f"Неизвестный модуль: {module_id}")
    return {
        "schema_version": 1,
        "mode": "modules",
        "selected_modules": module_ids,
        "selected_templates": selected,
        "seed": seed,
        "date": datetime.now().strftime("%d.%m.%Y"),
    }


def generate_random_worksheet(task_count: int = 5, seed: int | None = None) -> dict[str, Any]:
    """Generate a ready-to-print worksheet from modules with verified answers only."""
    count = _validate_task_count(task_count)
    rng = random.Random(seed)
    module_ids = [rng.choice(VERIFIED_MODULE_IDS) for _ in range(count)]
    worksheet = generate_combined_worksheet_by_modules(module_ids, seed=seed, task_count=count)
    worksheet["mode"] = "random_verified_modules"
    return worksheet


def _read_static_file(name: str) -> bytes:
    return (FRONTEND_ROOT / name).read_bytes()


def render_site_page() -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Генератор математических задач</title>
  <link rel="stylesheet" href="/static/worksheet_site.css">
</head>
<body>
  <main class="app-shell">
    <header class="site-nav no-print">
      <a class="site-brand" href="/" aria-label="Поступление в 239">
        <img src="/assets/logo_239.png" alt="Поступление в 239">
        <span><strong>Поступление в 239</strong><small>математика с увлечением</small></span>
      </a>
      <nav aria-label="Разделы генератора">
        <a href="#builder">Варианты</a>
        <a href="#worksheet-sheet">Предпросмотр</a>
        <a href="/admin/template-studio">Template Studio</a>
      </nav>
      <span class="nav-badge">5 задач · с ответами</span>
    </header>
    <section class="hero no-print">
      <p class="eyebrow">подготовка к математике</p>
      <h1><span>Задачи,</span> которые<br>открывают возможности</h1>
      <p>Готовые варианты для печати: автоматический подбор задач, новые числа и отдельная колонка с ответами для преподавателя.</p>
      <ul class="hero-features">
        <li>Понятные задания</li>
        <li>Олимпиадный подход</li>
        <li>Результат и уверенность</li>
      </ul>
    </section>

    <section class="builder no-print" id="builder">
      <div class="panel">
        <div class="panel-heading">
          <div>
            <h2>Вариант для печати</h2>
            <p id="catalog-summary">Загрузка каталога...</p>
          </div>
          <button id="clear-button" type="button" class="button-secondary">Очистить выбор</button>
        </div>
        <div class="quick-start">
          <div>
            <label for="task-count">Количество задач</label>
            <input id="task-count" type="number" min="1" max="20" value="5" inputmode="numeric">
          </div>
          <button id="quick-generate-button" type="button" class="button-primary" disabled>Сделать готовый вариант</button>
          <p>Автоматически выбираются только модули с вычисляемыми ответами.</p>
        </div>
        <details class="manual-builder">
          <summary>Настроить модули вручную</summary>
          <p>Для каждого номера можно выбрать модуль. В архиве отдельно выделены задания с уже восстановленными формулами; неразобранные тексты не добавляются в быстрый вариант.</p>
          <div id="selector-grid" class="selector-grid"></div>
        </details>
        <div class="actions">
          <button id="generate-button" type="button" disabled>Сгенерировать вариант</button>
          <button id="regenerate-button" type="button" class="button-secondary" disabled>Сгенерировать новые числа</button>
          <button id="print-button" type="button" class="button-secondary" disabled>Печать</button>
          <button id="print-answers-button" type="button" class="button-secondary" disabled>Печатать с ответами</button>
        </div>
        <p id="error-state" class="error" hidden></p>
      </div>
    </section>

    <section class="worksheet-sheet" id="worksheet-sheet" aria-label="Предпросмотр листа">
      <div class="worksheet-main">
        <header class="sheet-header">
          <div class="name-fields">
            <p>Фамилия: ______________________</p>
            <p>Имя: __________________________</p>
            <p>Дата: <span id="sheet-date"></span></p>
          </div>
          <div class="sheet-assets" aria-label="Логотип и QR-код">
            <img class="sheet-logo" src="/assets/logo_239.png" alt="Поступление в 239">
            <img src="/assets/qr.png" alt="QR-код Telegram-канала «Поступление в 239»">
          </div>
        </header>
        <hr>
        <ol id="worksheet-problems" class="problems-list">
          <li class="empty-problem">После генерации здесь появятся задачи.</li>
        </ol>
      </div>
      <aside class="print-answer-strip" aria-label="Отрезаемая колонка ответов">
        <img class="print-logo" src="/assets/logo_239.png" alt="Поступление в 239">
        <img class="print-qr" src="/assets/qr.png" alt="QR-код Telegram-канала «Поступление в 239»">
        <p class="cut-label">✂ Отрезать по пунктиру</p>
        <h2>Ответы</h2>
        <ol id="print-answers-list"></ol>
      </aside>
    </section>

    <section class="answer-key no-print" id="answer-key" hidden>
      <div class="panel">
        <div class="panel-heading">
          <h2>Ответы</h2>
          <button id="toggle-answers-button" type="button" class="button-secondary">Скрыть ответы</button>
        </div>
        <ol id="answers-list"></ol>
      </div>
    </section>

    <section class="no-print">
      <button id="show-answers-button" type="button" class="button-secondary" disabled>Показать ответы</button>
    </section>
  </main>
  <script src="/static/worksheet_site.js"></script>
</body>
</html>
"""


def render_template_studio_page(csrf_token: str) -> str:
    """Рендерит локальную административную страницу без пользовательского HTML."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="template-studio-csrf" content="{html.escape(csrf_token)}">
  <title>Template Studio · Генератор задач</title>
  <link rel="stylesheet" href="/static/worksheet_site.css">
</head>
<body class="studio-page">
  <main class="app-shell">
    <header class="site-nav no-print">
      <a class="site-brand" href="/" aria-label="К генератору задач"><img src="/assets/logo_239.png" alt=""><span><strong>Поступление в 239</strong><small>Template Studio · локальный администратор</small></span></a>
      <nav aria-label="Разделы"><a href="/">Варианты</a><a href="#studio-editor">Черновик</a></nav>
      <span class="nav-badge">не публикует автоматически</span>
    </header>
    <section class="studio-hero">
      <p class="eyebrow">административная зона</p>
      <h1>Template <span>Studio</span></h1>
      <p>Вставьте условие, проверьте предложенную структуру и активируйте только валидированный шаблон. Эта страница доступна лишь с локального адреса.</p>
    </section>
    <p id="studio-error" class="error" hidden></p>
    <section class="studio-grid" id="studio-editor">
      <form id="studio-source-form" class="panel studio-source">
        <div class="panel-heading"><div><h2>Источник и анализ</h2><p>Исходный текст не исполняется и сохраняется как черновик.</p></div></div>
        <label for="studio-original-text">Original mathematical problem *</label>
        <textarea id="studio-original-text" rows="7" maxlength="20000" required placeholder="Найдите сумму последовательности: 11 + 14 + 17 + … + 80 + 83."></textarea>
        <div class="studio-fields">
          <div><label for="studio-module">Target module</label><select id="studio-module"><option value="">Без модуля (только draft)</option></select></div>
          <div><label for="studio-language">Language</label><select id="studio-language"><option value="ru">ru</option></select></div>
          <div><label for="studio-answer-type">Proposed answer type</label><select id="studio-answer-type"><option value="integer">integer</option><option value="number">number</option><option value="decimal">decimal</option><option value="fraction">fraction</option><option value="boolean">boolean</option><option value="text">text</option><option value="list">list</option></select></div>
          <div><label for="studio-source-number">Source problem number</label><input id="studio-source-number" maxlength="100"></div>
          <div><label for="studio-source-file">Source filename</label><input id="studio-source-file" maxlength="1000"></div>
        </div>
        <button type="submit" class="button-primary">Анализировать и создать draft</button>
      </form>
      <aside class="panel studio-list"><div class="panel-heading"><div><h2>Черновики</h2><p>Активные записи нельзя удалить — только архивировать.</p></div><button id="studio-refresh-drafts" type="button" class="button-secondary">Обновить</button></div><div id="studio-drafts"></div></aside>
    </section>
    <section id="studio-workbench" class="panel studio-workbench" hidden>
      <div class="panel-heading"><div><h2>Редактор <span id="studio-draft-id"></span></h2><p id="studio-status"></p></div><div class="studio-actions"><button id="studio-save" type="button">Сохранить</button><button id="studio-preview" type="button" class="button-secondary">Предпросмотр</button><button id="studio-validate" type="button" class="button-secondary">Валидировать</button></div></div>
      <div class="studio-tabs" role="tablist"><button type="button" data-studio-section="source">Source</button><button type="button" data-studio-section="template">Template text</button><button type="button" data-studio-section="parameters">Parameters</button><button type="button" data-studio-section="derived">Derived values</button><button type="button" data-studio-section="solver">Solver</button><button type="button" data-studio-section="constraints">Constraints</button><button type="button" data-studio-section="grammar">Grammar</button><button type="button" data-studio-section="preview">Preview</button><button type="button" data-studio-section="validation">Validation</button><button type="button" data-studio-section="history">History</button></div>
      <section class="studio-section" data-studio-panel="source"><h3>Source</h3><p id="studio-source-view"></p><div class="studio-fields"><div><label for="studio-edit-source-number">Source problem number</label><input id="studio-edit-source-number" maxlength="100"></div><div><label for="studio-edit-source-file">Source filename</label><input id="studio-edit-source-file" maxlength="1000"></div></div><label for="studio-notes">Notes</label><textarea id="studio-notes" rows="3"></textarea></section>
      <section class="studio-section" data-studio-panel="template"><h3>Template text</h3><div class="studio-fields"><div><label for="studio-template-id">Template ID</label><input id="studio-template-id"></div><div><label for="studio-edit-module">Target module</label><select id="studio-edit-module"></select></div><div><label for="studio-edit-answer-type">Answer type</label><select id="studio-edit-answer-type"><option value="integer">integer</option><option value="number">number</option><option value="decimal">decimal</option><option value="fraction">fraction</option><option value="boolean">boolean</option><option value="text">text</option><option value="list">list</option></select></div></div><label for="studio-template-text">Текст шаблона</label><textarea id="studio-template-text" rows="6"></textarea></section>
      <section class="studio-section" data-studio-panel="parameters"><h3>Parameters</h3><p>Независимые параметры. Derived-параметры добавляются отдельно.</p><div id="studio-parameter-rows"></div><button id="studio-add-parameter" type="button" class="button-secondary">Добавить параметр</button></section>
      <section class="studio-section" data-studio-panel="derived"><h3>Derived values</h3><label for="studio-derived-values">JSON: имя → безопасное выражение</label><textarea id="studio-derived-values" rows="7">{{}}</textarea></section>
      <section class="studio-section" data-studio-panel="solver"><h3>Solver</h3><div class="studio-fields"><div><label for="studio-strategy">Strategy</label><select id="studio-strategy"><option value="formula">formula</option><option value="manual">manual (не активируется)</option></select></div><div><label for="studio-answer-expression">Answer expression</label><input id="studio-answer-expression" placeholder="a + b"></div><div><label for="studio-preview-count">Количество preview</label><input id="studio-preview-count" type="number" min="1" max="20" value="3"></div><div><label for="studio-preview-seed">Seed</label><input id="studio-preview-seed" type="number" value="1"></div></div></section>
      <section class="studio-section" data-studio-panel="constraints"><h3>Constraints</h3><label for="studio-constraints">Дополнительные generation constraints (JSON)</label><textarea id="studio-constraints" rows="5">{{}}</textarea><label for="studio-answer-rendering">Answer-rendering settings (JSON)</label><textarea id="studio-answer-rendering" rows="4">{{}}</textarea></section>
      <section class="studio-section" data-studio-panel="grammar"><h3>Grammar</h3><label for="studio-grammar">Grammar metadata (JSON)</label><textarea id="studio-grammar" rows="5">{{}}</textarea><p>Для имён используйте только данные общего морфологического слоя; Studio не склоняет имена эвристически.</p></section>
      <section class="studio-section" data-studio-panel="preview"><h3>Preview</h3><div id="studio-preview-results"></div></section>
      <section class="studio-section" data-studio-panel="validation"><h3>Validation</h3><div id="studio-validation-results"></div><div class="studio-actions"><button id="studio-activate" type="button" class="button-primary">Add to module</button><button id="studio-archive" type="button" class="button-secondary">Archive active template</button><button id="studio-restore" type="button" class="button-secondary">Restore archived template</button><button id="studio-reject" type="button" class="button-secondary">Reject draft</button><button id="studio-delete" type="button" class="button-danger">Delete draft</button></div></section>
      <section class="studio-section" data-studio-panel="history"><h3>History</h3><ol id="studio-history"></ol><details><summary>Raw JSON (advanced)</summary><textarea id="studio-raw-json" rows="16"></textarea><button id="studio-apply-raw" type="button" class="button-secondary">Применить редактируемые поля JSON</button></details></section>
    </section>
  </main>
  <script src="/static/template_studio.js"></script>
</body>
</html>"""


class WorksheetSiteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._respond_text(render_site_page(), "text/html; charset=utf-8")
            return
        if parsed.path == "/admin/template-studio":
            if not self._template_studio_is_local():
                self.send_error(HTTPStatus.FORBIDDEN, "Template Studio доступна только с локального адреса.")
                return
            self._respond_text(render_template_studio_page(_TEMPLATE_STUDIO_CSRF_TOKEN), "text/html; charset=utf-8")
            return
        if parsed.path.startswith("/api/admin/template-studio"):
            self._handle_template_studio_get(parsed.path)
            return
        if parsed.path == "/api/templates":
            self._respond_json(_combined_template_metadata())
            return
        if parsed.path == "/static/worksheet_site.css":
            self._respond_bytes(_read_static_file("worksheet_site.css"), "text/css; charset=utf-8")
            return
        if parsed.path == "/static/worksheet_site.js":
            self._respond_bytes(_read_static_file("worksheet_site.js"), "application/javascript; charset=utf-8")
            return
        if parsed.path == "/static/template_studio.js":
            self._respond_bytes(_read_static_file("template_studio.js"), "application/javascript; charset=utf-8")
            return
        if parsed.path in {"/assets/logo.png", "/assets/logo_239.png", "/assets/qr.png"}:
            asset_name = Path(parsed.path).name
            self._respond_bytes((ASSETS_ROOT / asset_name).read_bytes(), "image/png")
            return
        if parsed.path.startswith("/assets/fonts/"):
            requested_path = (ASSETS_ROOT / "fonts" / Path(parsed.path).name).resolve()
            fonts_root = (ASSETS_ROOT / "fonts").resolve()
            if fonts_root not in requested_path.parents or not requested_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Шрифт не найден")
                return
            self._respond_bytes(requested_path.read_bytes(), "font/ttf")
            return
        if parsed.path.startswith("/download/"):
            self._handle_download(parsed.path.removeprefix("/download/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/admin/template-studio"):
            self._handle_template_studio_post(parsed.path)
            return
        if parsed.path != "/generate":
            self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(content_length)
            data = json.loads(payload.decode("utf-8"))
            seed = data.get("seed")
            if seed is not None and not isinstance(seed, int):
                seed = None
            count = data.get("count", 5)
            _validate_task_count(count)
            if data.get("mode") == "random":
                worksheet = generate_random_worksheet(count, seed=seed)
                self._respond_json({"ok": True, "worksheet": worksheet})
                return
            module_ids = data.get("module_ids")
            if isinstance(module_ids, list) and all(isinstance(item, str) for item in module_ids):
                worksheet = generate_combined_worksheet_by_modules(module_ids, seed=seed, task_count=count)
                self._respond_json({"ok": True, "worksheet": worksheet})
                return
            template_ids = data.get("template_ids")
            if not isinstance(template_ids, list) or not all(isinstance(item, str) for item in template_ids):
                raise ValueError("Выберите модули для всех задач или используйте быстрый вариант.")
            worksheet = generate_arithmetic_worksheet(template_ids, seed=seed)
        except Exception as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"ok": True, "worksheet": worksheet})

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/admin/template-studio/drafts/"):
            self._handle_template_studio_patch(parsed.path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/admin/template-studio/drafts/"):
            self._handle_template_studio_delete(parsed.path)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    @staticmethod
    def _template_studio_context() -> tuple[set[str], set[str]]:
        metadata = _combined_template_metadata()
        module_ids = {
            item["module_id"] for item in metadata["modules"]
            if item["module_id"] not in {ARCHIVE_MODULE_ID, RECOVERED_ARCHIVE_MODULE_ID}
        }
        template_ids = {item.get("template_id", item.get("id")) for item in metadata["templates"]}
        return module_ids, {item for item in template_ids if isinstance(item, str)}

    def _handle_template_studio_get(self, path: str) -> None:
        if not self._template_studio_is_local():
            self._respond_json({"ok": False, "error": "Template Studio доступна только локально."}, status=HTTPStatus.FORBIDDEN)
            return
        try:
            if path == "/api/admin/template-studio/modules":
                metadata = _combined_template_metadata()
                modules = [
                    {"module_id": item["module_id"], "display_name": item["display_name"]}
                    for item in metadata["modules"]
                    if item["module_id"] not in {ARCHIVE_MODULE_ID, RECOVERED_ARCHIVE_MODULE_ID}
                ]
                self._respond_json({"ok": True, "modules": modules})
                return
            if path == "/api/admin/template-studio/drafts":
                self._respond_json({"ok": True, "drafts": _template_studio_service.store.list_drafts()})
                return
            prefix = "/api/admin/template-studio/drafts/"
            if path.startswith(prefix):
                draft_id = path.removeprefix(prefix)
                if "/" in draft_id or not draft_id:
                    raise ValueError("Некорректный draft ID.")
                self._respond_json({"ok": True, "draft": _template_studio_service.store.load_draft(draft_id)})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "API Template Studio не найден")
        except (KeyError, ValueError) as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_template_studio_post(self, path: str) -> None:
        if not self._template_studio_is_local():
            self._respond_json({"ok": False, "error": "Template Studio доступна только локально."}, status=HTTPStatus.FORBIDDEN)
            return
        try:
            data = self._template_studio_payload()
            known_modules, existing_ids = self._template_studio_context()
            if path == "/api/admin/template-studio/analyze":
                self._respond_json({"ok": True, "draft": _template_studio_service.create_from_analysis(data)})
                return
            prefix = "/api/admin/template-studio/drafts/"
            if not path.startswith(prefix):
                raise ValueError("API Template Studio не найден.")
            parts = path.removeprefix(prefix).split("/")
            if len(parts) != 2 or not parts[0]:
                raise ValueError("Некорректный путь черновика.")
            draft_id, action = parts
            if action == "preview":
                result = _template_studio_service.preview(draft_id, count=data.get("count", 3), seed=data.get("seed", 1))
                self._respond_json({"ok": True, **result})
                return
            if action == "validate":
                report = _template_studio_service.validate(draft_id, known_module_ids=known_modules, existing_template_ids=existing_ids)
                self._respond_json({"ok": True, "report": report, "draft": _template_studio_service.store.load_draft(draft_id)})
                return
            if action == "activate":
                draft = _template_studio_service.activate(draft_id, known_module_ids=known_modules, existing_template_ids=existing_ids)
                self._respond_json({"ok": True, "draft": draft})
                return
            if action == "archive":
                self._respond_json({"ok": True, "draft": _template_studio_service.archive(draft_id)})
                return
            if action == "restore":
                draft = _template_studio_service.restore(draft_id, known_module_ids=known_modules, existing_template_ids=existing_ids)
                self._respond_json({"ok": True, "draft": draft})
                return
            if action == "reject":
                self._respond_json({"ok": True, "draft": _template_studio_service.reject(draft_id, str(data.get("reason", "")))})
                return
            raise ValueError("Неизвестное действие Template Studio.")
        except (KeyError, ValueError) as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_template_studio_patch(self, path: str) -> None:
        if not self._template_studio_is_local():
            self._respond_json({"ok": False, "error": "Template Studio доступна только локально."}, status=HTTPStatus.FORBIDDEN)
            return
        try:
            data = self._template_studio_payload()
            draft_id = path.removeprefix("/api/admin/template-studio/drafts/")
            if "/" in draft_id or not draft_id:
                raise ValueError("Некорректный draft ID.")
            self._respond_json({"ok": True, "draft": _template_studio_service.update_draft(draft_id, data)})
        except (KeyError, ValueError) as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_template_studio_delete(self, path: str) -> None:
        if not self._template_studio_is_local():
            self._respond_json({"ok": False, "error": "Template Studio доступна только локально."}, status=HTTPStatus.FORBIDDEN)
            return
        try:
            data = self._template_studio_payload()
            draft_id = path.removeprefix("/api/admin/template-studio/drafts/")
            if "/" in draft_id or not draft_id:
                raise ValueError("Некорректный draft ID.")
            _template_studio_service.delete_draft(draft_id, confirmed=data.get("confirmed") is True)
            self._respond_json({"ok": True, "deleted": draft_id})
        except (KeyError, ValueError) as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def _template_studio_payload(self) -> dict[str, Any]:
        if not hmac.compare_digest(self.headers.get("X-Template-Studio-CSRF", ""), _TEMPLATE_STUDIO_CSRF_TOKEN):
            raise ValueError("Недействительный CSRF token Template Studio.")
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("application/json"):
            raise ValueError("Template Studio принимает только application/json.")
        content_length = int(self.headers.get("Content-Length", "0"))
        if not 0 < content_length <= TEMPLATE_STUDIO_MAX_REQUEST_BYTES:
            raise ValueError("Недопустимый размер запроса Template Studio.")
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Ожидался JSON-объект.")
        return payload

    def _template_studio_is_local(self) -> bool:
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def _handle_download(self, filename: str) -> None:
        safe_name = Path(filename).name
        requested_path = (OUTPUT_ROOT / safe_name).resolve()
        if OUTPUT_ROOT.resolve() not in requested_path.parents:
            self.send_error(HTTPStatus.FORBIDDEN, "Можно скачивать только файлы из outputs/generated")
            return
        if not requested_path.exists() or not requested_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Файл не найден")
            return
        content_type = mimetypes.guess_type(str(requested_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(requested_path.stat().st_size))
        self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.end_headers()
        self.wfile.write(requested_path.read_bytes())

    def _respond_text(self, text: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond_bytes(text.encode("utf-8"), content_type, status=status)

    def _respond_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond_text(json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8", status=status)

    def _respond_bytes(self, payload: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[worksheet-web] {self.address_string()} - {html.escape(format % args)}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def create_http_server(host: str, port: int, max_port_tries: int = 20) -> tuple[ReusableThreadingHTTPServer, int]:
    last_error: OSError | None = None
    for current_port in range(port, port + max_port_tries):
        try:
            server = ReusableThreadingHTTPServer((host, current_port), WorksheetSiteHandler)
            return server, current_port
        except OSError as error:
            last_error = error
            if error.errno not in (48, 10048):
                raise
    raise OSError(48, f"Не удалось найти свободный порт в диапазоне {port}-{port + max_port_tries - 1}") from last_error


def run_server(host: str = "127.0.0.1", port: int = 8090) -> None:
    server, actual_port = create_http_server(host, port)
    if actual_port != port:
        print(f"Порт {port} занят, выбран свободный порт {actual_port}.")
    print(f"Worksheet site: http://{host}:{actual_port}")
    print("Остановить сервер: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()
