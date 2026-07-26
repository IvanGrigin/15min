"""Превью генерации: по N задач на КАЖДЫЙ шаблон КАЖДОГО модуля.

Запуск из корня репозитория:
    python3 scripts/preview_all_templates.py
    python3 scripts/preview_all_templates.py --count 5 --module arithmetic
    python3 scripts/preview_all_templates.py --include-recovered      # + модуль 32
    python3 scripts/preview_all_templates.py --include-archive        # + модуль 33 (1017 шаблонов)

Результат: outputs/preview_all_templates.md
"""
from __future__ import annotations

import argparse
import random
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.generation import (  # noqa: E402
    age_templates,
    alphabetic_order_templates,
    arithmetic_templates,
    calendar_templates,
    clock_templates,
    combinatorics_templates,
    comparison_templates,
    counting_objects_templates,
    cube_templates,
    digits_templates,
    divisibility_templates,
    equation_templates,
    equation_word_templates,
    factor_product_templates,
    grid_templates,
    integer_interval_templates,
    line_templates,
    logic_templates,
    money_templates,
    motion_templates,
    parity_templates,
    pigeonhole_templates,
    plane_geometry_templates,
    process_templates,
    quantity_templates,
    ratio_templates,
    sequence_templates,
    sets_templates,
    system_equation_templates,
    time_zone_templates,
    work_templates,
)
from problemgen.template_studio.catalogue import active_templates  # noqa: E402
from problemgen.template_studio.runtime import generate_active_template, normalize_value  # noqa: E402
from problemgen.worksheet.all_tasks_site import (  # noqa: E402
    generate_problem_instance,
    recovered_templates,
    unverified_templates,
)

# ---------------------------------------------------------------------------
# ЕДИНОЕ МЕСТО, ГДЕ МЕНЯЕТСЯ НАБОР ТЕМ.
# Порядок повторяет нумерацию 01..31 в выпадающем списке сайта.
# Каждая запись: (модуль-файл, суффикс имени функций).
# load_<suffix>_templates()  -> список шаблонов (у каждого есть "id" и "module")
# generate_<suffix>_problem(template_id, seed=...) -> объект задачи
# ---------------------------------------------------------------------------
DOMAINS: list[tuple[Any, str]] = [
    (arithmetic_templates, "arithmetic"),
    (equation_templates, "equation"),
    (system_equation_templates, "system_equation"),
    (comparison_templates, "comparison"),
    (sequence_templates, "sequence"),
    (integer_interval_templates, "integer_interval"),
    (divisibility_templates, "divisibility"),
    (digits_templates, "digits"),
    (factor_product_templates, "factor_product"),
    (ratio_templates, "ratio"),
    (combinatorics_templates, "combinatorics"),
    (pigeonhole_templates, "pigeonhole"),
    (parity_templates, "parity"),
    (process_templates, "process"),
    (calendar_templates, "calendar"),
    (clock_templates, "clock"),
    (time_zone_templates, "time_zone"),
    (motion_templates, "motion"),
    (work_templates, "work"),
    (money_templates, "money"),
    (age_templates, "age"),
    (counting_objects_templates, "counting"),
    (sets_templates, "sets"),
    (plane_geometry_templates, "plane_geometry"),
    (grid_templates, "grid"),
    (cube_templates, "cube"),
    (line_templates, "line"),
    (quantity_templates, "quantity"),
    (logic_templates, "logic"),
    (equation_word_templates, "equation_word"),
    (alphabetic_order_templates, "alphabetic_order"),
]


def _answer_to_text(answer: Any) -> str:
    if isinstance(answer, dict):
        if set(answer) == {"x", "y"}:
            return f"X = {answer['x']}, Y = {answer['y']}"
        return "; ".join(f"{key}: {value}" for key, value in answer.items())
    if isinstance(answer, list):
        return ", ".join(str(item) for item in answer)
    return str(answer)


def _module_display_names(module: Any, suffix: str) -> dict[str, str]:
    metadata_fn: Callable[[], dict[str, Any]] | None = getattr(module, f"{suffix}_template_metadata", None)
    if metadata_fn is None:
        return {}
    try:
        metadata = metadata_fn()
    except Exception:  # noqa: BLE001 - превью не должно падать из-за метаданных.
        return {}
    modules = metadata.get("modules", [])
    names = {
        str(item.get("module_id")): str(item.get("display_name") or item.get("title") or item.get("module_id"))
        for item in modules
    }
    # Некоторые домены хранят в шаблонах внутренний module-код, отличный от module_id
    # в метаданных (например, "digits" против "digits_number_notation_and_cryptarithms").
    if len(modules) == 1:
        names["__default__"] = next(iter(names.values()))
    return names


def _domain_sections(count: int, module_filter: str | None, include_inactive: bool = False) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for module, suffix in DOMAINS:
        templates = getattr(module, f"load_{suffix}_templates")()
        generate = getattr(module, f"generate_{suffix}_problem")
        names = _module_display_names(module, suffix)

        grouped: dict[str, list[dict[str, Any]]] = {}
        for template in templates:
            grouped.setdefault(str(template.get("module", suffix)), []).append(template)

        for module_id, module_templates in grouped.items():
            if module_filter and module_filter not in (module_id, suffix):
                continue
            entries: list[dict[str, Any]] = []
            for template in module_templates:
                template_id = str(template["id"])
                is_active = bool(template.get("active", True))
                samples: list[dict[str, str]] = []
                if not is_active and not include_inactive:
                    entries.append({
                        "template_id": template_id,
                        "active": False,
                        "source_problem_numbers": template.get("source_problem_numbers", []),
                        "samples": [],
                    })
                    continue
                for seed in range(count):
                    try:
                        generated = generate(template_id, seed=seed)
                        samples.append({
                            "problem": str(getattr(generated, "problem_text", "")),
                            "answer": str(
                                getattr(generated, "answer_text", None)
                                or _answer_to_text(getattr(generated, "answer", ""))
                            ),
                        })
                    except Exception as error:  # noqa: BLE001 - собираем ошибки в отчёт.
                        samples.append({
                            "problem": f"ОШИБКА ГЕНЕРАЦИИ: {error}",
                            "answer": traceback.format_exc(limit=1).strip().splitlines()[-1],
                            "failed": "1",
                        })
                entries.append({
                    "template_id": template_id,
                    "active": template.get("active", True),
                    "source_problem_numbers": template.get("source_problem_numbers", []),
                    "samples": samples,
                })
            sections.append({
                "module_id": module_id,
                "display_name": names.get(module_id) or names.get("__default__") or module_id,
                "templates": entries,
            })
    return sections


def _studio_section(count: int) -> dict[str, Any] | None:
    templates = active_templates()
    if not templates:
        return None
    entries: list[dict[str, Any]] = []
    for template in templates:
        samples: list[dict[str, str]] = []
        for seed in range(count):
            try:
                generated = generate_active_template(template, random.Random(seed))
                samples.append({
                    "problem": str(generated["rendered_problem"]),
                    "answer": _answer_to_text(
                        {key: normalize_value(value) for key, value in generated["parameters"].items()}
                        if generated.get("answer") is None
                        else generated["answer"]
                    ),
                })
            except Exception as error:  # noqa: BLE001
                samples.append({"problem": f"ОШИБКА ГЕНЕРАЦИИ: {error}", "answer": "", "failed": "1"})
        entries.append({
            "template_id": str(template.get("template_id")),
            "active": True,
            "source_problem_numbers": [],
            "samples": samples,
            "module_hint": template.get("module_id"),
        })
    return {"module_id": "template_studio", "display_name": "Template Studio (активные шаблоны)", "templates": entries}


def _corpus_section(templates: list[dict[str, Any]], module_id: str, title: str, count: int, *, verified: bool) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for template in templates:
        samples: list[dict[str, str]] = []
        for seed in range(count):
            try:
                generated = generate_problem_instance(template, random.Random(seed), require_changed=verified)
                samples.append({
                    "problem": str(generated["rendered_problem"]),
                    "answer": _answer_to_text(generated["answer"]) if verified else "— (ответ не восстановлен)",
                })
            except Exception as error:  # noqa: BLE001
                samples.append({"problem": f"ОШИБКА ГЕНЕРАЦИИ: {error}", "answer": "", "failed": "1"})
        entries.append({
            "template_id": str(template.get("template_id")),
            "active": True,
            "source_problem_numbers": [template.get("source_problem_number")],
            "samples": samples,
        })
    return {"module_id": module_id, "display_name": title, "templates": entries}


def _render_markdown(sections: list[dict[str, Any]], count: int) -> str:
    total_templates = sum(len(section["templates"]) for section in sections)
    inactive = sum(1 for section in sections for entry in section["templates"] if not entry.get("active", True))
    total_samples = sum(len(entry["samples"]) for section in sections for entry in section["templates"])
    failures = [
        (section["display_name"], entry["template_id"], sample["problem"])
        for section in sections
        for entry in section["templates"]
        for sample in entry["samples"]
        if sample.get("failed")
    ]

    lines: list[str] = [
        "# Превью генерации по всем шаблонам",
        "",
        f"- Тем (модулей): **{len(sections)}**",
        f"- Шаблонов: **{total_templates}** (из них выключено: {inactive})",
        f"- Сгенерировано задач: **{total_samples}** (по {count} на шаблон)",
        f"- Ошибок генерации: **{len(failures)}**",
        "",
    ]

    lines.append("## Оглавление")
    lines.append("")
    for index, section in enumerate(sections, start=1):
        anchor = f"{index:02d}-{section['module_id']}".replace("_", "-")
        lines.append(f"{index:02d}. [{section['display_name']}](#{anchor}) — шаблонов: {len(section['templates'])}")
    lines.append("")

    if failures:
        lines.append("## Ошибки генерации")
        lines.append("")
        for display_name, template_id, message in failures[:100]:
            lines.append(f"- `{template_id}` ({display_name}): {message}")
        lines.append("")

    for index, section in enumerate(sections, start=1):
        lines.append(f"## {index:02d} {section['display_name']}")
        lines.append("")
        lines.append(f"`module_id: {section['module_id']}` · шаблонов: {len(section['templates'])}")
        lines.append("")
        for entry in section["templates"]:
            flag = "" if entry.get("active", True) else " · ВЫКЛЮЧЕН"
            sources = entry.get("source_problem_numbers") or []
            source_text = f" · источники: {sources}" if sources else ""
            lines.append(f"### `{entry['template_id']}`{flag}{source_text}")
            lines.append("")
            if not entry["samples"]:
                lines.append("_Шаблон выключен — генерация пропущена (запустите с `--include-inactive`)._")
                lines.append("")
                continue
            for number, sample in enumerate(entry["samples"], start=1):
                lines.append(f"{number}. {sample['problem']}")
                lines.append(f"   - **Ответ:** {sample['answer']}")
            lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сгенерировать по N задач на каждый шаблон каждой темы.")
    parser.add_argument("--count", type=int, default=5, help="Сколько задач на один шаблон (по умолчанию 5).")
    parser.add_argument("--module", default=None, help="Ограничить одним модулем (module_id или суффикс домена).")
    parser.add_argument("--include-inactive", action="store_true", help="Пробовать генерировать и выключенные шаблоны.")
    parser.add_argument("--include-studio", action="store_true", help="Добавить активные шаблоны Template Studio.")
    parser.add_argument("--include-recovered", action="store_true", help="Добавить модуль 32 (восстановленные формулы).")
    parser.add_argument("--include-archive", action="store_true", help="Добавить модуль 33 (архив, 1000+ шаблонов).")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "outputs" / "preview_all_templates.md"),
        help="Путь к файлу отчёта.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sections = _domain_sections(args.count, args.module, include_inactive=args.include_inactive)

    if args.include_studio and not args.module:
        studio = _studio_section(args.count)
        if studio:
            sections.append(studio)
    if args.include_recovered and not args.module:
        sections.append(
            _corpus_section(recovered_templates(), "all_tasks_recovered", "Архив: восстановленные формулы", args.count, verified=True)
        )
    if args.include_archive and not args.module:
        sections.append(
            _corpus_section(unverified_templates(), "all_tasks_archive", "Архив подготовленных шаблонов", args.count, verified=False)
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(sections, args.count), encoding="utf-8")

    total_templates = sum(len(section["templates"]) for section in sections)
    failures = sum(
        1
        for section in sections
        for entry in section["templates"]
        for sample in entry["samples"]
        if sample.get("failed")
    )
    print(f"Готово: {len(sections)} тем, {total_templates} шаблонов, ошибок: {failures}")
    print(f"Отчёт: {output_path}")


if __name__ == "__main__":
    main()
