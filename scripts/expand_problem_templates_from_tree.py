from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TREE_PATH = ROOT / "data" / "source_index" / "math_problem_tree_template_ready.md"
CATALOG_PATH = ROOT / "data" / "templates" / "problem_templates.json"
TARGET_VARIANTS_PER_LEAF = 9

ROW_RE = re.compile(r"^\| ([A-Z][0-9]{2}) \| `([^`]+)` \| ([^|]+) \| `([^`]+)` \| ([^|]+) \| ([0-9]+) \|")

DOMAIN_BY_SECTION = {
    "A": "arithmetic",
    "B": "arithmetic",
    "C": "digits",
    "D": "number_theory",
    "E": "sequences",
    "F": "combinatorics",
    "G": "geometry",
    "H": "geometry",
    "I": "logic",
    "J": "motion",
}


def supported(difficulty: int) -> list[int]:
    return list(range(max(1, difficulty - 2), min(10, difficulty + 2) + 1))


def constraints(names: list[str], template: dict[str, dict[str, int]] | None = None) -> dict[str, dict[str, Any]]:
    defaults = {name: {"type": "integer", "min": 1, "max": 10000} for name in names}
    defaults.update(template or {})
    return defaults


def bridge_models() -> list[dict[str, Any]]:
    return [
        {
            "suffix": "age_group",
            "strategy": "age_joining_group",
            "problem_type": "tree_age_total_bridge",
            "domain": "arithmetic",
            "numbers": ["current_total", "years_later", "extra_people", "extra_current_total", "future_total"],
            "characters": ["character_1"],
            "constraints": constraints(
                ["current_total", "years_later", "extra_people", "extra_current_total", "future_total"],
                {
                    "current_total": {"type": "integer", "min": 10, "max": 150},
                    "years_later": {"type": "integer", "min": 2, "max": 10},
                    "extra_people": {"type": "integer", "min": 1, "max": 3},
                    "extra_current_total": {"type": "integer", "min": 4, "max": 36},
                    "future_total": {"type": "integer", "min": 20, "max": 260},
                },
            ),
            "formula": "(future_total - current_total - extra_current_total - extra_people * years_later) / years_later",
            "text": "{character_1} разбирает задачу темы {leaf_id}. Сейчас сумма возрастов группы равна {current_total} г. Через {years_later} г. к ним присоединятся новые участники: {extra_people} чел.; их нынешний суммарный возраст {extra_current_total} г. Тогда общая сумма возрастов станет {future_total} г. Сколько человек было в группе сначала?",
        },
        {
            "suffix": "ratio_transfer",
            "strategy": "ratio_transfer",
            "problem_type": "tree_ratio_transfer_bridge",
            "domain": "arithmetic",
            "numbers": ["total", "ratio_a", "ratio_b", "transfer", "final_difference"],
            "characters": ["character_1", "character_2"],
            "constraints": constraints(
                ["total", "ratio_a", "ratio_b", "transfer", "final_difference"],
                {
                    "total": {"type": "integer", "min": 15, "max": 500},
                    "ratio_a": {"type": "integer", "min": 3, "max": 7},
                    "ratio_b": {"type": "integer", "min": 1, "max": 5},
                    "transfer": {"type": "integer", "min": 1, "max": 100},
                    "final_difference": {"type": "integer", "min": 1, "max": 300},
                },
            ),
            "formula": "total * ratio_a / (ratio_a + ratio_b)",
            "text": "{character_1} и {character_2} решают задачу темы {leaf_id}. Всего есть {total} шт. предметов, сначала две части относятся как {ratio_a}:{ratio_b}. Из большей части переложили {transfer} шт. в меньшую, и разница стала {final_difference} шт. Сколько предметов было в большей части сначала?",
        },
        {
            "suffix": "heads_legs_removed",
            "strategy": "heads_and_legs_removed",
            "problem_type": "tree_linear_system_bridge",
            "domain": "arithmetic",
            "numbers": ["removed_rabbits", "heads_after", "legs_after"],
            "characters": ["character_1"],
            "constraints": constraints(
                ["removed_rabbits", "heads_after", "legs_after"],
                {
                    "removed_rabbits": {"type": "integer", "min": 1, "max": 20},
                    "heads_after": {"type": "integer", "min": 3, "max": 80},
                    "legs_after": {"type": "integer", "min": 8, "max": 320},
                },
            ),
            "formula": "(legs_after - 2 * heads_after) / 2 + removed_rabbits",
            "text": "{character_1} классифицирует объекты для темы {leaf_id}. Были объекты с 2 и 4 опорами. Часть четырёхопорных убрали: {removed_rabbits} шт. После этого осталось {heads_after} объектов и {legs_after} опор. Сколько четырёхопорных объектов было сначала?",
        },
        {
            "suffix": "work_delay",
            "strategy": "joint_work_delay",
            "problem_type": "tree_rate_partial_time_bridge",
            "domain": "arithmetic",
            "numbers": ["rate_1", "rate_2", "delay", "duration", "total"],
            "characters": ["character_1", "character_2"],
            "constraints": constraints(
                ["rate_1", "rate_2", "delay", "duration", "total"],
                {
                    "rate_1": {"type": "integer", "min": 3, "max": 80},
                    "rate_2": {"type": "integer", "min": 3, "max": 80},
                    "delay": {"type": "integer", "min": 1, "max": 8},
                    "duration": {"type": "integer", "min": 3, "max": 12},
                    "total": {"type": "integer", "min": 1, "max": 2000},
                },
            ),
            "formula": "total",
            "text": "В модели темы {leaf_id} {character_1} делает {rate_1} шт./ч. {character_2} делает {rate_2} шт./ч, но начинает через {delay} ч. Сколько штук будет готово за {duration} ч от начала работы {character_1}?",
        },
        {
            "suffix": "round_robin_missing",
            "strategy": "round_robin_missing",
            "problem_type": "tree_pair_count_bridge",
            "domain": "combinatorics",
            "numbers": ["players", "absent_players", "active_players"],
            "characters": ["character_1"],
            "constraints": constraints(
                ["players", "absent_players", "active_players"],
                {
                    "players": {"type": "integer", "min": 5, "max": 40},
                    "absent_players": {"type": "integer", "min": 1, "max": 4},
                    "active_players": {"type": "integer", "min": 3, "max": 40},
                },
            ),
            "formula": "active_players * (active_players - 1) / 2",
            "text": "{character_1} строит парную схему для темы {leaf_id}. Было {players} участников, но не пришли {absent_players} чел. Остальные должны встретиться каждый с каждым ровно один раз. Сколько встреч получится?",
        },
        {
            "suffix": "paint_cube",
            "strategy": "paint_cube_unpainted",
            "problem_type": "tree_surface_scaling_bridge",
            "domain": "geometry",
            "numbers": ["base_paint", "scale", "unpainted_faces"],
            "characters": ["character_1"],
            "constraints": constraints(
                ["base_paint", "scale", "unpainted_faces"],
                {
                    "base_paint": {"type": "integer", "min": 6, "max": 300},
                    "scale": {"type": "integer", "min": 2, "max": 8},
                    "unpainted_faces": {"type": "integer", "min": 1, "max": 2},
                },
            ),
            "formula": "base_paint * scale * scale * (6 - unpainted_faces) / 6",
            "text": "{character_1} делает геометрическую модель темы {leaf_id}. На полный маленький куб ушло {base_paint} г краски. У нового куба коэффициент увеличения стороны равен {scale}, а без краски оставляют граней: {unpainted_faces} шт. Сколько граммов краски нужно?",
        },
        {
            "suffix": "two_stage_motion",
            "strategy": "movement_two_stage",
            "problem_type": "tree_piecewise_motion_bridge",
            "domain": "motion",
            "numbers": ["speed_1", "time_1", "rest_time", "speed_2", "time_2"],
            "characters": ["character_1"],
            "constraints": constraints(
                ["speed_1", "time_1", "rest_time", "speed_2", "time_2"],
                {
                    "speed_1": {"type": "integer", "min": 3, "max": 50},
                    "time_1": {"type": "integer", "min": 1, "max": 8},
                    "rest_time": {"type": "integer", "min": 1, "max": 3},
                    "speed_2": {"type": "integer", "min": 3, "max": 50},
                    "time_2": {"type": "integer", "min": 1, "max": 8},
                },
            ),
            "formula": "speed_1 * time_1 + speed_2 * time_2",
            "text": "Для темы {leaf_id} {character_1} сначала двигался {time_1} ч со скоростью {speed_1} км/ч, потом отдыхал {rest_time} ч и ещё {time_2} ч двигался со скоростью {speed_2} км/ч. Какой путь он прошёл?",
        },
        {
            "suffix": "opposite_motion",
            "strategy": "opposite_motion_delay",
            "problem_type": "tree_relative_speed_bridge",
            "domain": "motion",
            "numbers": ["distance", "speed_1", "speed_2", "delay"],
            "characters": ["character_1", "character_2"],
            "constraints": constraints(
                ["distance", "speed_1", "speed_2", "delay"],
                {
                    "distance": {"type": "integer", "min": 10, "max": 800},
                    "speed_1": {"type": "integer", "min": 4, "max": 60},
                    "speed_2": {"type": "integer", "min": 4, "max": 60},
                    "delay": {"type": "integer", "min": 1, "max": 5},
                },
            ),
            "formula": "delay + (distance - speed_1 * delay) / (speed_1 + speed_2)",
            "text": "В задаче темы {leaf_id} {character_1} и {character_2} находятся на расстоянии {distance} км. {character_1} вышел первым со скоростью {speed_1} км/ч, а {character_2} вышел навстречу через {delay} ч со скоростью {speed_2} км/ч. Через сколько часов после первого выхода они встретятся?",
        },
        {
            "suffix": "price_system",
            "strategy": "price_system_two_receipts",
            "problem_type": "tree_two_equation_bridge",
            "domain": "arithmetic",
            "numbers": ["count_a_1", "count_b_1", "total_1", "count_a_2", "count_b_2", "total_2"],
            "characters": [],
            "constraints": constraints(
                ["count_a_1", "count_b_1", "total_1", "count_a_2", "count_b_2", "total_2", "answer_price_a"],
                {
                    "count_a_1": {"type": "integer", "min": 1, "max": 12},
                    "count_b_1": {"type": "integer", "min": 1, "max": 12},
                    "total_1": {"type": "integer", "min": 10, "max": 50000},
                    "count_a_2": {"type": "integer", "min": 1, "max": 12},
                    "count_b_2": {"type": "integer", "min": 1, "max": 12},
                    "total_2": {"type": "integer", "min": 10, "max": 50000},
                    "answer_price_a": {"type": "integer", "min": 20, "max": 1000},
                },
            ),
            "formula": "answer_price_a",
            "text": "В прикладной версии темы {leaf_id} первый набор: товар A {count_a_1} шт., товар B {count_b_1} шт.; цена {total_1} руб. Второй набор: товар A {count_a_2} шт., товар B {count_b_2} шт.; цена {total_2} руб. Сколько стоит один товар A?",
        },
    ]


def parse_tree() -> list[dict[str, str]]:
    leaves: list[dict[str, str]] = []
    for line in TREE_PATH.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        leaf_id, module, family, variables, answer_model, min_actions = match.groups()
        leaves.append(
            {
                "leaf_id": leaf_id,
                "module": module,
                "family": family.strip(),
                "variables": variables,
                "answer_model": answer_model.strip(),
                "min_actions": min_actions,
            }
        )
    return leaves


def make_template(leaf: dict[str, str], model: dict[str, Any], variant: int) -> dict[str, Any]:
    difficulty = min(10, max(1, int(leaf["min_actions"]) + 1 + (variant % 3)))
    section_domain = DOMAIN_BY_SECTION.get(leaf["leaf_id"][0], model["domain"])
    template = {
        "template_id": f"tree_{leaf['leaf_id'].lower()}_{model['suffix']}_{variant:02d}",
        "domain": section_domain,
        "module": f"tree_{leaf['module']}",
        "topic": f"{leaf['leaf_id'].lower()}_{model['suffix']}",
        "problem_type": model["problem_type"],
        "difficulty": difficulty,
        "supported_difficulties": supported(difficulty),
        "title": f"{leaf['leaf_id']}: {leaf['family']}",
        "template_text": model["text"].replace("{leaf_id}", leaf["leaf_id"]),
        "placeholders": {
            "characters": model["characters"],
            "locations": [],
            "numbers": model["numbers"],
        },
        "constraints": deepcopy(model["constraints"]),
        "number_strategy": model["strategy"],
        "answer_formula": model["formula"],
        "answer_type": "number",
        "integer_answer_required": True,
        "derived_words": {},
        "source_tree_leaf": leaf["leaf_id"],
        "source_tree_module": leaf["module"],
        "source_tree_family": leaf["family"],
        "coverage_note": "Bridge template generated from math_problem_tree_template_ready.md. Replace with a more specific hand-written template when this leaf becomes a priority.",
    }
    return template


def main() -> None:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    templates = payload["templates"]
    existing_positions = {template["template_id"]: index for index, template in enumerate(templates)}

    leaves = parse_tree()
    if len(leaves) != 100:
        raise RuntimeError(f"Expected 100 tree leaves, found {len(leaves)}.")

    models = bridge_models()
    if len(models) != TARGET_VARIANTS_PER_LEAF:
        raise RuntimeError("Bridge model count must match TARGET_VARIANTS_PER_LEAF.")

    added = 0
    for leaf in leaves:
        for variant, model in enumerate(models, start=1):
            template = make_template(leaf, model, variant)
            if template["template_id"] in existing_positions:
                templates[existing_positions[template["template_id"]]] = template
                continue
            templates.append(template)
            existing_positions[template["template_id"]] = len(templates) - 1
            added += 1

    CATALOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Tree leaves: {len(leaves)}")
    print(f"Templates added: {added}")
    print(f"Catalog total: {len(templates)}")


if __name__ == "__main__":
    main()
