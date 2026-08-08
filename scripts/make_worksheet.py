"""Сборка пятнадцатиминутки: пять задач по местам, как у преподавателя.

Раскладка разобрана в docs/WORKSHEET_FORMAT.md: первое место — счёт,
второе — уравнение или сравнение, третье и четвёртое — средние, пятое —
трудная сюжетная. Балл считается как «решённые плюс один», поэтому две
задачи обязаны быть посильными почти любому, а пятёрка должна требовать
трудной.

    python3 scripts/make_worksheet.py --date 05.05.2026 --seed 7
    python3 scripts/make_worksheet.py --count 3 --answers
    python3 scripts/make_worksheet.py --date 09.05.2026 --pdf outputs/generated/09-05.pdf
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import (  # noqa: E402
    TemplateResampleError, TemplateRuntimeError, generate_active_template,
)
from problemgen.web.worksheet_page import render_worksheets, to_pdf  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

VERDICTS = PROJECT_ROOT / "data" / "review" / "verdicts.json"

# Модули, которые в листочках преподавателя стоят на счётном месте.
COUNTING_MODULES = frozenset({
    "arithmetic", "integer_interval_counting", "sequences_progressions_and_sums",
    "digits_number_notation_and_cryptarithms",
})
# Модули второго места: уравнение или сравнение.
EQUATION_MODULES = frozenset({
    "equations", "comparison_of_numbers_and_expressions", "systems_of_equations",
})

# Место: роль, допустимая трудность, желаемые модули, нежелательные модули.
# Середина листочка нарочно уводится от счёта и уравнений: свои места
# у них уже были, и повторять тему — значит потерять половину листочка.
SLOTS = (
    ("счёт", ("easy",), COUNTING_MODULES, frozenset()),
    ("уравнение или сравнение", ("easy", "medium"), EQUATION_MODULES, frozenset()),
    ("средняя", ("medium",), None, COUNTING_MODULES | EQUATION_MODULES),
    ("средняя", ("medium",), None, COUNTING_MODULES | EQUATION_MODULES),
    ("трудная", ("hard",), None, COUNTING_MODULES | EQUATION_MODULES),
)


def teacher_difficulty() -> dict[str, str]:
    """Оценки преподавателя из смотра: шаблон → easy/medium/hard."""
    if not VERDICTS.exists():
        return {}
    data = json.loads(VERDICTS.read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    for template_id, record in data.items():
        level = record.get("difficulty")
        if not level:
            for comment in reversed(record.get("comments") or []):
                if comment.get("difficulty"):
                    level = comment["difficulty"]
                    break
        if level in {"easy", "medium", "hard"}:
            found[template_id] = level
    return found


def difficulty_of(template: dict, marked: dict[str, str]) -> str:
    """Трудность шаблона: сначала оценка преподавателя, потом собственная.

    Своя оценка грубее: `advanced` в math_notes означает, что задача требует
    приёма, а не только счёта, — такие идут в трудные. Счётные темы уровня
    `base` считаются лёгкими, остальные `base` — средними.
    """
    if template["template_id"] in marked:
        return marked[template["template_id"]]
    level = (template.get("math_notes") or {}).get("level")
    if level == "advanced":
        return "hard"
    if template.get("module_id") in COUNTING_MODULES:
        return "easy"
    return "medium"


def pick(templates: list[dict], rng: random.Random, wanted: tuple[str, ...],
         modules: frozenset[str] | None, avoid: frozenset[str],
         used_modules: set[str], used_ids: set[str],
         marked: dict[str, str]) -> dict | None:
    """Выбрать шаблон под место, не повторяя тему листочка."""
    def fits(template: dict, strict_modules: bool) -> bool:
        if template["template_id"] in used_ids:
            return False
        if template["module_id"] in used_modules or template["module_id"] in avoid:
            return False
        if strict_modules and modules is not None and template["module_id"] not in modules:
            return False
        return difficulty_of(template, marked) in wanted

    for strict in (True, False):
        candidates = [t for t in templates if fits(t, strict)]
        if candidates:
            return rng.choice(candidates)
    return None


def build(templates: list[dict], rng: random.Random,
          marked: dict[str, str]) -> list[dict]:
    """Собрать пять задач по местам."""
    used_modules: set[str] = set()
    used_ids: set[str] = set()
    sheet: list[dict] = []
    for role, wanted, modules, avoid in SLOTS:
        template = pick(templates, rng, wanted, modules, avoid,
                        used_modules, used_ids, marked)
        if template is None:
            raise SystemExit(f"Не нашлось шаблона на место «{role}» ({', '.join(wanted)}).")
        for _ in range(30):
            try:
                generated = generate_active_template(template, rng)
                break
            except (TemplateResampleError, TemplateRuntimeError):
                continue
        else:
            raise SystemExit(f"Шаблон {template['template_id']} не выдал задачу.")
        used_modules.add(template["module_id"])
        used_ids.add(template["template_id"])
        sheet.append({
            "role": role,
            "template_id": template["template_id"],
            "module_id": template["module_id"],
            "difficulty": difficulty_of(template, marked),
            "problem": generated["rendered_problem"],
            "answer": generated.get("answer_text") or generated["answer"],
        })
    return sheet


def render(sheet: list[dict], when: str, show_answers: bool) -> str:
    """Листочек в том виде, в каком его печатают детям."""
    lines = [f"Фамилия ________________  Имя ________________        {when}", ""]
    for number, task in enumerate(sheet, start=1):
        lines.append(f"{number}. {task['problem']}")
        lines.append("")
        lines.append("_" * 64)
        lines.append("")
    if show_answers:
        lines.append("Ключ (не выдавать вместе с листочком):")
        for number, task in enumerate(sheet, start=1):
            lines.append(
                f"  {number}. {task['answer']}"
                f"   [{task['role']}, {task['difficulty']}, {task['template_id']}]")
    return "\n".join(lines)


def main() -> None:
    """Разобрать аргументы и напечатать запрошенное число листочков."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="зерно случайности")
    parser.add_argument("--date", default=None, help="дата в шапке, ДД.ММ.ГГГГ")
    parser.add_argument("--count", type=int, default=1, help="сколько листочков подряд")
    parser.add_argument("--answers", action="store_true", help="напечатать ключ")
    parser.add_argument("--html", type=Path, default=None,
                        help="сохранить листочки страницей по этому пути")
    parser.add_argument("--pdf", type=Path, default=None,
                        help="напечатать листочки в PDF по этому пути")
    parser.add_argument("--logo", type=Path, default=None,
                        help="эмблема в правом поле, картинкой")
    parser.add_argument("--qr", type=Path, default=None,
                        help="QR-код в правом поле, картинкой")
    options = parser.parse_args()

    templates = load_library()
    marked = teacher_difficulty()
    start = date.today()
    made: list[tuple[list[dict], str]] = []
    for index in range(options.count):
        seed = (options.seed if options.seed is not None else random.randrange(10 ** 6)) + index
        rng = random.Random(seed)
        when = options.date or (start + timedelta(days=index)).strftime("%d.%m.%Y")
        made.append((build(templates, rng, marked), when))

    if not (options.html or options.pdf):
        for sheet, when in made:
            print(render(sheet, when, options.answers))
            print()
        return

    page = render_worksheets(made, options.logo, options.qr, options.answers)
    target = options.html or options.pdf.with_suffix(".html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    print(f"Страница: {target}")
    if options.pdf:
        options.pdf.parent.mkdir(parents=True, exist_ok=True)
        options.pdf.write_bytes(to_pdf(page))
        print(f"PDF: {options.pdf}")


if __name__ == "__main__":
    main()
