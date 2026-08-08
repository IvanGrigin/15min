"""Иерархическая разметка корпуса v2 по темам и покрытие по каждой теме.

Тему задачи определяет ближайший шаблон библиотеки: у каждого шаблона уже
проставлен `module_id`, и это не выдуманная классификация, а та самая, по
которой собирается листочек. Так разметка и покрытие считаются одним проходом:
задача, у которой нашёлся близкий шаблон, тем самым и покрыта.

Задачам без близкого шаблона тема ставится по словарю признаков — иначе
непокрытая половина осталась бы без темы, а именно она и нужна для плана
работ. Такая разметка помечается как предположительная.

Иерархия двухуровневая: раздел (крупная область) → модуль (один из 31 в
`data/templates/problem_sets/catalog.json`). Приём — третий уровень — здесь
не выводится: он определяется способом решения, а не словами условия, и
машинной разметке не поддаётся.

    python3 tools/classify_corpus_v2.py

Пишет `docs/CORPUS_V2_TOPICS.md` и `data/source_index/topics.json`.
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tools.coverage_report as cr  # noqa: E402
from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

CORPUS = PROJECT_ROOT / "docs" / "all_tasks_all_files_v2.md"
CATALOG = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "catalog.json"
OUT_REPORT = PROJECT_ROOT / "docs" / "CORPUS_V2_TOPICS.md"
OUT_JSON = PROJECT_ROOT / "data" / "source_index" / "topics.json"

TASK_LINE = re.compile(r"^(\d+)\.\s+(.*?)\s+\((?:свод (\d+)|в своде не найдена)\)\s*$")
SAMPLES = 8

# Крупные области: модуль → раздел. Без этого тридцать один модуль читается
# как плоский список, и по нему не видно, где в корпусе дыра.
AREAS = {
    "Числа и вычисления": [
        "arithmetic", "equations", "systems_of_equations",
        "comparison_of_numbers_and_expressions", "sequences_progressions_and_sums",
        "integer_interval_counting", "divisibility_multiples_remainders_primes",
        "digits_number_notation_and_cryptarithms", "factors_products_and_factorials",
        "ratios_fractions_proportions_and_percentages",
        "number_processes_and_repeated_operations",
    ],
    "Текстовые задачи": [
        "motion_speed_and_distance", "work_productivity_and_joint_actions",
        "money_purchases_prices_and_calculations", "ages_and_generations",
        "heads_legs_wheels_and_object_counts",
        "word_problems_for_equation_setup",
        "quantities_units_weight_and_scaling",
    ],
    "Время и календарь": [
        "calendar_and_weekdays", "clocks_dials_and_electronic_displays",
        "time_zones_and_travel_schedules",
    ],
    "Геометрия": [
        "plane_geometry_rectangles_squares_and_areas",
        "grid_figures_cuts_and_routes", "cubes_volume_and_spatial_geometry",
        "points_segments_and_positions_on_a_line",
    ],
    "Комбинаторика и логика": [
        "combinatorics_and_counting_variants", "pigeonhole_and_guaranteed_selection",
        "parity_invariants_strategies_and_moves",
        "sets_clubs_acquaintances_and_tournaments",
        "logic_problems_and_condition_analysis", "alphabetic_order",
    ],
}
MODULE_AREA = {module: area for area, modules in AREAS.items() for module in modules}

# Признаки для задач, у которых близкого шаблона нет. Порядок важен:
# проверка идёт сверху вниз, первое совпадение выигрывает.
HINTS: list[tuple[str, str]] = [
    ("alphabetic_order", r"алфавит|букв\w* (?:я|и|в|а|н)\b|словар\w+ порядк"),
    ("time_zones_and_travel_schedules", r"когда в .+ \d{2}:\d{2}|часово\w+ пояс|местному времени"),
    ("clocks_dials_and_electronic_displays", r"табло|циферблат|стрелк|часы показыв"),
    ("calendar_and_weekdays", r"день недели|понедельник|вторник|среда|четверг|пятниц|суббот|воскресен|високос|какого числа"),
    ("motion_speed_and_distance", r"скорост|км/ч|навстречу|догон|поезд|велосипед|пешеход|вышел из|проехал"),
    ("work_productivity_and_joint_actions", r"производительн|за час сдела|вместе (?:сдела|выполн)|работа\w* вдвоём"),
    ("money_purchases_prices_and_calculations", r"рубл|копе|цена|стоит|подорожа|скидк|сдач"),
    ("ages_and_generations", r"возраст|лет назад|старше|младше|исполн\w+ лет"),
    ("heads_legs_wheels_and_object_counts", r"голов|ног[аиу]?\b|колёс|лап"),
    ("cubes_volume_and_spatial_geometry", r"куб|брусок|объём|грани"),
    ("grid_figures_cuts_and_routes", r"клетк|разрез|перегородк|уголк|доминошк|маршрут"),
    ("plane_geometry_rectangles_squares_and_areas", r"периметр|площад|прямоугольник|квадрат\w* со сторон"),
    ("points_segments_and_positions_on_a_line", r"на прямой|отрезк|точк\w+ отмеч"),
    ("pigeonhole_and_guaranteed_selection", r"наверняка|гарантированно|обязательно найдут|не глядя"),
    ("sets_clubs_acquaintances_and_tournaments", r"турнир|кажд\w+ с кажд\w+|рукопожат|кружок|секци"),
    ("logic_problems_and_condition_analysis", r"лжец|рыцар|правд\w+ говор|соврал|виновн"),
    ("parity_invariants_strategies_and_moves", r"чётност|инвариант|выигрышн|ход\w* игрок"),
    ("combinatorics_and_counting_variants", r"сколькими способ|перестанов|различн\w+ комбинац|вариант"),
    ("ratios_fractions_proportions_and_percentages", r"процент|доля|треть\b|четверт|половин|во сколько раз"),
    ("divisibility_multiples_remainders_primes", r"делит|остат|кратн|прост\w+ число"),
    ("digits_number_notation_and_cryptarithms", r"цифр|разряд|зачеркн|вычеркн|запис\w+ числа"),
    ("factors_products_and_factorials", r"множител|факториал|произведени"),
    ("integer_interval_counting", r"в промежутке|от \d+ до \d+"),
    ("sequences_progressions_and_sums", r"последовательн|прогресс|сумм\w+ ряда|\+ \.\.\. \+"),
    ("systems_of_equations", r"систем\w+ уравнен"),
    ("equations", r"найдите (?:значение )?x|найдите неизвестн|уравнени"),
    ("number_processes_and_repeated_operations", r"кажд\w+ (?:день|минуту|шаг)|удваива|повторя"),
    ("comparison_of_numbers_and_expressions", r"какое из чисел больше|на сколько отличают|сравнит"),
    ("arithmetic", r"вычислите|найдите значение выражения"),
]


def corpus_tasks() -> list[dict]:
    """Задачи корпуса v2: номер, текст, номер в своде, источник."""
    tasks: list[dict] = []
    source = ""
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            source = line[3:]
            continue
        found = TASK_LINE.match(line)
        if found:
            tasks.append({"v2": int(found.group(1)), "text": found.group(2),
                          "master": int(found.group(3)) if found.group(3) else None,
                          "source": source})
    return tasks


def template_prints() -> list[tuple[str, str, Counter]]:
    """Отпечатки выдачи: (template_id, module_id, мешок слов)."""
    prints = []
    for template in load_library():
        for seed in range(SAMPLES):
            try:
                generated = generate_active_template(template, random.Random(seed))
            except Exception:  # noqa: BLE001 — устойчивость шаблонов проверяют другие тесты
                continue
            prints.append((template["template_id"], template["module_id"],
                           cr.words(generated["rendered_problem"])))
    return prints


def by_hint(text: str) -> str | None:
    """Тема по словарю признаков, когда близкого шаблона не нашлось."""
    for module, pattern in HINTS:
        if re.search(pattern, text, re.IGNORECASE):
            return module
    return None


def classify(tasks: list[dict], prints: list[tuple[str, str, Counter]]) -> None:
    """Проставить каждой задаче тему, шаблон и признак покрытия."""
    for task in tasks:
        bag = cr.words(task["text"])
        best_template, best_module, best_score = None, None, 0.0
        for template_id, module_id, sample in prints:
            score = cr.similarity(bag, sample)
            if score > best_score:
                best_template, best_module, best_score = template_id, module_id, score
        covered = best_score >= cr.COVERED_AT
        task["covered"] = covered
        task["template"] = best_template if covered else None
        task["score"] = round(best_score, 3)
        module = best_module if covered else by_hint(task["text"])
        task["module"] = module
        task["area"] = MODULE_AREA.get(module or "", "Не разобрано")
        task["module_guessed"] = not covered


def main() -> None:
    """Разметить корпус v2 по темам и посчитать покрытие внутри каждой."""
    tasks = corpus_tasks()
    classify(tasks, template_prints())

    titles = {item["id"]: item["title"]
              for item in json.loads(CATALOG.read_text(encoding="utf-8"))["problem_sets"]}
    per_module: dict[str, list[dict]] = defaultdict(list)
    for task in tasks:
        per_module[task["module"] or "—"].append(task)

    covered = sum(1 for task in tasks if task["covered"])
    lines = [
        "# Корпус v2: темы и покрытие",
        "",
        f"Задач в корпусе: **{len(tasks)}**. Покрыто шаблонами: "
        f"**{covered}** ({100 * covered / len(tasks):.1f}%).",
        "",
        "Тему задаёт ближайший шаблон библиотеки — та же классификация, по",
        "которой собирается листочек. Там, где близкого шаблона нет, тема",
        "поставлена по словарю признаков и помечена как предположительная.",
        "",
        "| раздел | модуль | задач | покрыто | доля |",
        "|---|---|---:|---:|---:|",
    ]
    for area in list(AREAS) + ["Не разобрано"]:
        modules = [module for module in per_module if MODULE_AREA.get(module, "Не разобрано") == area]
        for module in sorted(modules, key=lambda name: -len(per_module[name])):
            rows = per_module[module]
            hit = sum(1 for task in rows if task["covered"])
            lines.append(f"| {area} | {titles.get(module, module)} | {len(rows)} | "
                         f"{hit} | {100 * hit / len(rows):.0f}% |")
    lines.append("")

    lines.extend(["## Непокрытые задачи по модулям", ""])
    for module, rows in sorted(per_module.items(), key=lambda item: -sum(
            1 for task in item[1] if not task["covered"])):
        missing = [task for task in rows if not task["covered"]]
        if not missing:
            continue
        lines.append(f"### {titles.get(module, module)} — не покрыто {len(missing)}")
        lines.append("")
        for task in missing[:12]:
            master = f", свод {task['master']}" if task["master"] else ""
            lines.append(f"- v2 {task['v2']}{master}: {task['text'][:150]}")
        if len(missing) > 12:
            lines.append(f"- …ещё {len(missing) - 12}")
        lines.append("")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps({
        "comment": "Тема и покрытие для каждой задачи docs/all_tasks_all_files_v2.md.",
        "tasks": tasks,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"задач: {len(tasks)}, покрыто: {covered} ({100 * covered / len(tasks):.1f}%)")
    print(f"модулей задействовано: {len(per_module)}")
    print(f"написано: {OUT_REPORT.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()
