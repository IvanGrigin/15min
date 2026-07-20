"""Собирает исключённые source-accounting задачи в Markdown-отчёт outputs/generated."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "templates" / "problem_sets" / "catalog.json"
OUTPUT = ROOT / "outputs" / "generated" / "excluded_site_problems.md"
NUMBER = re.compile(r"^\s*(\d+)\.\s*(.*)$")


def read_numbered_problems(paths: list[Path]) -> dict[int, str]:
    problems: dict[int, str] = {}
    current: int | None = None
    chunks: list[str] = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = NUMBER.match(line)
            if match:
                if current is not None:
                    problems[current] = " ".join(chunks).strip()
                current, chunks = int(match.group(1)), [match.group(2).strip()]
            elif current is not None and line.strip() and not line.startswith("#"):
                chunks.append(line.strip())
        if current is not None:
            problems[current] = " ".join(chunks).strip()
            current, chunks = None, []
    return problems


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["problem_sets"]
    sources = {
        item["id"]: [ROOT / part.strip() for part in item.get("source_file", "").split(" + ")]
        for item in catalog
    }
    records_by_module: dict[str, list[dict]] = defaultdict(list)
    manifests = sorted((ROOT / "data" / "templates" / "problem_sets").glob("*/source_accounting.json"))
    for manifest in manifests:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            if record.get("status", "active_template") != "active_template":
                records_by_module[payload["module_id"]].append(record)

    lines = [
        "# Задачи, исключённые из генерации сайта",
        "",
        "Отчёт строится из `source_accounting.json`: в нём только задачи, которые сознательно не попали в runtime-шаблоны.",
        "Модули без такого манифеста не считаются автоматически: для них репозиторий не хранит машинно проверяемый список исключений.",
        "",
    ]
    total = 0
    for module_id in sorted(records_by_module):
        paths = [path for path in sources.get(module_id, []) if path.exists()]
        texts = read_numbered_problems(paths)
        lines.extend([f"## {module_id}", ""])
        for record in sorted(records_by_module[module_id], key=lambda item: item["source_problem_number"]):
            number = record["source_problem_number"]
            text = texts.get(number, "Текст не найден в зарегистрированном source_file.")
            lines.extend([f"### {number}", "", text, "", f"Причина: {record.get('reason', 'не указана')}", ""])
            total += 1
    without_manifest = sorted(item["id"] for item in catalog if item["id"] not in {json.loads(path.read_text(encoding="utf-8"))["module_id"] for path in manifests})
    lines.extend([
        f"Всего исключённых задач с зафиксированной причиной: {total}.",
        "",
        "## Модули без source-accounting",
        "",
        "Для следующих модулей в текущем репозитории нет машинно фиксированного списка оставленных задач; они не включены в отчёт:",
        "",
        *[f"- `{module_id}`" for module_id in without_manifest],
        "",
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Создан {OUTPUT} ({total} задач)")


if __name__ == "__main__":
    main()
