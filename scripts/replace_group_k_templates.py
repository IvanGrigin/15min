"""Replace Group K bridge templates with reviewed, thematic runtime templates.

The script is intentionally narrow: it only removes catalog entries and updates
worklist rows whose ``source_tree_leaf`` / ``leaf_id`` is K01..K08.  It is
idempotent and is the audit trail for this authoring batch.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data/templates/problem_templates.json"
WORKLIST_PATH = ROOT / "data/source_index/per_task_template_worklist.json"
DIFFICULTIES = list(range(1, 11))


def template(
    template_id: str,
    module: str,
    topic: str,
    title: str,
    text: str,
    numbers: list[str],
    constraints: dict[str, dict[str, int | str]],
    strategy: str,
    formula: str,
    leaf: str,
    answer_type: str = "number",
    integer_answer_required: bool = False,
) -> dict[str, object]:
    """Build one complete catalog record with the shared Group K metadata."""
    return {
        "template_id": template_id,
        "domain": "logic",
        "module": module,
        "topic": topic,
        "problem_type": topic,
        "difficulty": 6,
        "supported_difficulties": DIFFICULTIES,
        "title": title,
        "template_text": text,
        "placeholders": {"characters": [], "locations": [], "numbers": numbers},
        "constraints": constraints,
        "number_strategy": strategy,
        "answer_formula": formula,
        "answer_type": answer_type,
        "integer_answer_required": integer_answer_required,
        "derived_words": {},
        "source_tree_leaf": leaf,
    }


TEMPLATES = [
    template(
        "k01_truth_liars_fixed_001", "k01_truth_liars", "truth_liars",
        "Рыцари и лжецы: три связанных утверждения",
        "На острове каждый житель либо всегда говорит правду, либо всегда лжёт. "
        "Аня сказала: «Борис лжёт». Борис сказал: «Вера лжёт». "
        "Вера сказала: «Аня и Борис говорят правду». Кто из них говорит правду?",
        [], {}, "k01_fixed_truth_liars", "k01_unique_truth_teller()", "K01", "text",
    ),
    template(
        "k02_one_wrong_equation_001", "k02_one_wrong_equation", "one_wrong_calculation",
        "Одна ошибка в трёх уравнениях",
        "Проверяя вычисления, учитель записал три равенства: "
        "{multiplier_1} · x = {result_1}; {multiplier_2} · x = {result_2}; "
        "{multiplier_3} · x = {result_3}. Известно, что ровно одно равенство ошибочно. "
        "Найдите x.",
        ["multiplier_1", "multiplier_2", "multiplier_3", "result_1", "result_2", "result_3"],
        {
            "multiplier_1": {"type": "integer", "min": 3, "max": 19},
            "multiplier_2": {"type": "integer", "min": 3, "max": 19},
            "multiplier_3": {"type": "integer", "min": 3, "max": 19},
            "result_1": {"type": "integer", "min": 18, "max": 10450},
            "result_2": {"type": "integer", "min": 18, "max": 10450},
            "result_3": {"type": "integer", "min": 19, "max": 10460},
        },
        "k02_one_wrong_equation", "x", "K02", "number", True,
    ),
    template(
        "k03_elevator_gcd_001", "k03_elevator_reachability", "elevator_reachability",
        "Достижимость этажа двумя кнопками",
        "В лифте работают только две кнопки: «+{up} этажей» и «−{down} этажей». "
        "Можно ли, несколько раз нажимая кнопки, изменить номер этажа ровно на "
        "{difference} этажей? Ответьте «можно» или «нельзя».",
        ["up", "down", "difference"],
        {
            "up": {"type": "integer", "min": 3, "max": 28},
            "down": {"type": "integer", "min": 3, "max": 28},
            "difference": {"type": "integer", "min": 1, "max": 620},
        },
        "k03_elevator_gcd", "k_reachable_by_gcd(up, down, difference)", "K03", "text",
    ),
    template(
        "k04_domino_parity_001", "k04_domino_parity", "parity_invariant_grid",
        "Чётностный инвариант домино",
        "Можно ли полностью покрыть прямоугольную таблицу {rows} × {columns} "
        "косточками домино размером 1 × 2 без наложений и пробелов? "
        "Ответьте «можно» или «нельзя».",
        ["rows", "columns"],
        {
            "rows": {"type": "integer", "min": 3, "max": 14},
            "columns": {"type": "integer", "min": 3, "max": 14},
        },
        "k04_domino_parity", "k_domino_coverable(rows, columns)", "K04", "text",
    ),
    template(
        "k05_progression_invariant_001", "k05_neighbor_difference", "neighbor_difference_invariant",
        "Сумма при фиксированной разности соседей",
        "Вдоль забора растут {count} кустов. На каждом следующем кусте ягод ровно "
        "на {step} больше, чем на предыдущем. Может ли общее число ягод быть равно "
        "{total}? Ответьте «можно» или «нельзя».",
        ["count", "step", "total"],
        {
            "count": {"type": "integer", "min": 4, "max": 17},
            "step": {"type": "integer", "min": 1, "max": 12},
            "total": {"type": "integer", "min": 10, "max": 2500},
        },
        "k05_progression_invariant", "k_progression_sum_possible(count, step, total)", "K05", "text",
    ),
    template(
        "k06_guaranteed_draw_composition_001", "k06_guaranteed_draws", "guaranteed_draw_composition",
        "Состав набора по гарантиям выборки",
        "В коробке лежат красные, синие и зелёные карандаши; каждый цвет есть. Всего "
        "карандашей {total}. Наименьшее число карандашей, которое надо вынуть вслепую, "
        "чтобы наверняка получить красный, равно {red_draw}; для синего — {blue_draw}. "
        "Сколько в коробке красных, синих и зелёных карандашей? Ответ запишите в этом порядке.",
        ["total", "red_draw", "blue_draw"],
        {
            "total": {"type": "integer", "min": 6, "max": 45},
            "red_draw": {"type": "integer", "min": 3, "max": 44},
            "blue_draw": {"type": "integer", "min": 3, "max": 44},
        },
        "k06_guaranteed_draws",
        "[total - red_draw + 1, total - blue_draw + 1, red_draw + blue_draw - total - 2]",
        "K06", "multi",
    ),
    template(
        "k07_ordered_clues_fixed_001", "k07_ordered_clues", "ordered_clue_deduction",
        "Восстановление порядка по трём подсказкам",
        "Аня, Борис и Вера заняли три разных места с первого по третье. Известно, что "
        "Аня не первая, Борис стоит раньше Веры, а Вера не третья. Кто занял первое место?",
        [], {}, "k07_fixed_order_clues", "k07_first_by_clues()", "K07", "text",
    ),
    template(
        "k08_state_gcd_reachability_001", "k08_state_reachability", "state_reachability",
        "Достижимость состояния преобразованиями",
        "На табло записано 0. За один ход разрешено либо прибавить {up}, либо вычесть "
        "{down}. Можно ли получить число {difference}? Ответьте «можно» или «нельзя».",
        ["up", "down", "difference"],
        {
            "up": {"type": "integer", "min": 3, "max": 28},
            "down": {"type": "integer", "min": 3, "max": 28},
            "difference": {"type": "integer", "min": 1, "max": 620},
        },
        "k08_transform_gcd", "k_reachable_by_gcd(up, down, difference)", "K08", "text",
    ),
]


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    leaves = {record["source_tree_leaf"] for record in TEMPLATES}
    catalog["templates"] = [
        record for record in catalog["templates"]
        if record.get("source_tree_leaf") not in leaves
    ] + TEMPLATES
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    worklist = json.loads(WORKLIST_PATH.read_text(encoding="utf-8"))
    by_leaf = {record["source_tree_leaf"]: record for record in TEMPLATES}
    for task in worklist["tasks"]:
        record = by_leaf.get(task["leaf_id"])
        if record is None:
            continue
        task.update({
            "number_strategy": record["number_strategy"],
            "template_text": record["template_text"],
            "answer_formula": record["answer_formula"],
            "answer_type": record["answer_type"],
            "notes": f"Авторский шаблон {record['template_id']}; ответ независимо сверяется тестом группы K.",
            "status": "done",
        })
    worklist["tasks_done"] = sum(task["status"] == "done" for task in worklist["tasks"])
    WORKLIST_PATH.write_text(
        json.dumps(worklist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
