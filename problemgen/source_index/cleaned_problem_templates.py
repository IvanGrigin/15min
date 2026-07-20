from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from problemgen.catalog.problem_templates import TemplateCatalogError, load_template_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "docs" / "cleaned_math_problems.md"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_templates.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "cleaned_problem_templates_report.md"

PROBLEM_RE = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
NUMBER_RE = re.compile(
    r"\d{1,2}:\d{2}(?::\d{2})?"
    r"|\d+(?:[,.]\d+)?(?:/\d+(?:[,.]\d+)?)?"
    r"|\d+"
)
PLACEHOLDER_RE = re.compile(r"{number_([1-9]\d*)}")


MODULE_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("Задачи на время и часовые пояса", "time", "time", r"час|время|табло|день недели|ма[яр]т|апрел|ма[йя]|часов|минут|самол[её]т|Калининград|Самара|Якутск|Петербург|Новосибирск"),
    ("Геометрия и измерения", "geometry", "geometry", r"прямоугольник|квадрат|куб|периметр|площад|сторон|см|дм|м²|клет"),
    ("Комбинаторика", "combinatorics", "combinatorics", r"сколько существует|комбинац|перестанов|слов|вариант|выбрать|турнир|каждый с каждым"),
    ("Цифры и запись чисел", "digits", "digits", r"цифр|зв[её]здочк|запис[ьи]|разряд|чисел.*содержащ|палиндром"),
    ("Делимость и множители", "number_theory", "number_theory", r"делящ|кратн|сомножител|делител|НОД|НОК|прост"),
    ("Задачи на движение", "movement", "movement", r"скорост|км/ч|дорог|встрет|догон|путь|стадион"),
    ("Задачи на совместную работу", "joint_work", "joint_work", r"составляет .* за .* час|вместе за|поля для игры|потребовалось бы времени"),
    ("Задачи на деньги", "money", "money", r"рубл|стоимост|цен|плат[её]ж|деньг|отел"),
    ("Задачи на возраст", "age", "age", r"возраст|лет"),
    ("Логические задачи", "logic", "logic", r"лжец|правд|Можно ли|Верно ли|кто ошибся|ошиб"),
    ("Последовательности", "sequences", "sequences", r"последовательност|сумм[ау] .*…|1 \+ 2 \+ 3"),
    ("Уравнения", "equations", "equations", r"значение x|значение х|уравнен|неизвестн"),
    ("Арифметические вычисления", "arithmetic", "arithmetic", r"Вычислите|Как удобнее всего вычислить|Какое из чисел больше"),
)


def parse_cleaned_problems(text: str) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    current_source = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current_source = line.removeprefix("## ").strip()
            continue
        match = PROBLEM_RE.match(line)
        if not match:
            continue
        problems.append({
            "source_problem_number": int(match.group(1)),
            "source_file": current_source,
            "text": match.group(2).strip(),
        })
    return problems


def classify_problem(text: str) -> tuple[str, str, str]:
    for module_name, module_id, topic, pattern in MODULE_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return module_name, module_id, topic
    return "Арифметические текстовые задачи", "arithmetic_word", "word_problem"


def parameterize_problem(text: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    values: dict[str, Any] = {}
    constraints: dict[str, Any] = {}
    parts: list[str] = []
    last = 0
    counter = 1
    for match in NUMBER_RE.finditer(text):
        raw = match.group(0)
        name = f"number_{counter}"
        parts.append(text[last:match.start()])
        parts.append("{" + name + "}")
        is_plain_integer = re.fullmatch(r"\d+", raw) is not None
        values[name] = int(raw) if is_plain_integer else raw
        constraints[name] = {
            "type": "integer" if is_plain_integer else "text_number",
            "original": raw,
        }
        last = match.end()
        counter += 1
    parts.append(text[last:])
    return "".join(parts), values, constraints


def placeholders_are_sequential(template_text: str) -> bool:
    numbers = [int(value) for value in PLACEHOLDER_RE.findall(template_text)]
    return sorted(set(numbers)) == list(range(1, max(numbers, default=0) + 1))


def build_templates(problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for index, problem in enumerate(problems, start=1):
        module_name, module_id, topic = classify_problem(problem["text"])
        template_text, values, constraints = parameterize_problem(problem["text"])
        templates.append({
            "template_id": f"template_{index:04d}",
            "domain": "cleaned_math_problems",
            "module": module_name,
            "module_id": module_id,
            "topic": topic,
            "problem_type": topic,
            "difficulty": 5,
            "supported_difficulties": list(range(1, 11)),
            "title": module_name,
            "source_problem_number": problem["source_problem_number"],
            "source_file": problem["source_file"],
            "source_text": problem["text"],
            "template_text": template_text,
            "placeholders": {
                "characters": [],
                "locations": [],
                "numbers": list(values),
            },
            "constraints": constraints,
            "original_values": values,
            "number_strategy": "source_values",
            "answer_formula": "'Ответ не задан'",
            "answer_type": "text",
            "integer_answer_required": False,
            "derived_words": {},
        })
    return templates


def validate_templates(templates: list[dict[str, Any]], source_count: int | None = None) -> list[str]:
    errors: list[str] = []
    ids = [template["template_id"] for template in templates]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_template_ids")
    if source_count is not None and len(templates) != source_count:
        errors.append(f"template_count_mismatch:{len(templates)}!={source_count}")
    for template in templates:
        text = template.get("template_text", "")
        if not text or "TODO" in text:
            errors.append(f"empty_or_placeholder:{template['template_id']}")
        if not placeholders_are_sequential(text):
            errors.append(f"non_sequential_placeholders:{template['template_id']}")
        declared = set(template.get("placeholders", {}).get("numbers", []))
        used = {"number_" + value for value in PLACEHOLDER_RE.findall(text)}
        if declared != used:
            errors.append(f"placeholder_declaration_mismatch:{template['template_id']}")
        if not re.search(r"[А-Яа-яЁё]", template["module"]):
            errors.append(f"module_not_russian:{template['template_id']}")
    return errors


def build_report(source_count: int, templates: list[dict[str, Any]], errors: list[str]) -> str:
    modules = Counter(template["module"] for template in templates)
    lines = [
        "# Cleaned Problem Templates Report",
        "",
        f"- Source problems found: {source_count}",
        f"- Templates created: {len(templates)}",
        f"- Modules: {len(modules)}",
        f"- Exclusions: 0",
        f"- Validation errors: {len(errors)}",
        "",
        "## Modules",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in sorted(modules.items()))
    lines.extend(["", "## Validation Errors", ""])
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- None.")
    lines.extend([
        "",
        "## Commands",
        "",
        "```powershell",
        "python scripts/rebuild_problem_templates_from_cleaned.py",
        "python scripts/validate_cleaned_problem_templates.py",
        "python -m unittest tests.test_cleaned_problem_templates",
        "```",
    ])
    return "\n".join(lines) + "\n"


def rebuild_catalog() -> dict[str, Any]:
    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    problems = parse_cleaned_problems(source_text)
    templates = build_templates(problems)
    errors = validate_templates(templates, len(problems))
    payload = {
        "schema_version": "2.0",
        "description": "Шаблоны, детерминированно построенные из docs/cleaned_math_problems.md.",
        "source_file": "docs/cleaned_math_problems.md",
        "templates": templates,
    }
    write_json(TEMPLATE_PATH, payload)
    REPORT_PATH.write_text(build_report(len(problems), templates, errors), encoding="utf-8")
    return {"source_count": len(problems), "template_count": len(templates), "module_count": len({template["module"] for template in templates}), "errors": errors}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_current_catalog() -> dict[str, Any]:
    source_count = len(parse_cleaned_problems(SOURCE_PATH.read_text(encoding="utf-8")))
    # `problem_templates.json` is now a curated compatibility catalogue with
    # general placeholders and strategies.  Its runtime schema is deliberately
    # different from a freshly rebuilt `number_1` source overlay, so validate
    # it through the canonical static-catalogue loader.
    try:
        templates = load_template_catalog(TEMPLATE_PATH)
        errors: list[str] = []
    except TemplateCatalogError as error:
        templates = []
        errors = [str(error)]
    return {
        "source_count": source_count,
        "template_count": len(templates),
        "module_count": len({template["module"] for template in templates}),
        "modules": sorted({template["module"] for template in templates}),
        "errors": errors,
    }


def main() -> None:
    stats = rebuild_catalog()
    print(f"source_count: {stats['source_count']}")
    print(f"template_count: {stats['template_count']}")
    print(f"module_count: {stats['module_count']}")
    print(f"errors: {len(stats['errors'])}")


if __name__ == "__main__":
    main()
