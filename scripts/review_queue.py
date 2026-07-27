"""Компактная выжимка очереди на проверку человеком.

Цель — чтобы проверяющий (человек или сильная модель) читал сотни токенов
на шаблон вместо тысяч: только то, по чему принимается решение.

    python3 scripts/review_queue.py                # дайджест incoming/
    python3 scripts/review_queue.py --examples 5   # больше примеров
    python3 scripts/review_queue.py --rejected     # что и почему не прошло
    python3 scripts/review_queue.py --accept <id>  # перенести в library/
    python3 scripts/review_queue.py --branch       # разбор текущей ветки против main

Режим `--branch` собирает всё, по чему принимается решение «мерджить или нет»,
одной командой: соблюдено ли железное правило про Python, что добавлено в данные,
примеры по каждому шаблону с покрытием веток choice, есть ли независимый решатель
и обновлён ли журнал. Работает по текущему checkout, потому что примеры нужно
генерировать реестрами той же ветки.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402

STUDIO_ROOT = PROJECT_ROOT / "data" / "template_studio"
INCOMING = STUDIO_ROOT / "incoming"
REJECTED = STUDIO_ROOT / "rejected"
LIBRARY = STUDIO_ROOT / "library"
# Каталоги, где Python описывает задачу, а не решает её: сюда правки запрещены.
ENGINE_PATHS = ("problemgen/", "scripts/", "run.py")


def git(*args: str) -> str:
    """Выполнить git и вернуть вывод; при ошибке — пустая строка."""
    result = subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def branching_values(template: dict[str, Any]) -> dict[str, list[Any]]:
    """Значения choice-параметров: каждое должно попасться проверяющему на глаза."""
    branches: dict[str, list[Any]] = {}
    for name, rule in (template.get("parameter_schema") or {}).items():
        if isinstance(rule, dict) and rule.get("type") == "choice":
            values = rule.get("allowed_values")
            if isinstance(values, list) and 2 <= len(values) <= 8:
                branches[name] = list(values)
    return branches


def digest(template: dict[str, Any], examples: int) -> str:
    """Собрать компактную выжимку по шаблону: математика, параметры, примеры."""
    lines = [f"### {template['template_id']}  [{template.get('module_id')}]"]
    source = template.get("source_metadata", {})
    lines.append(f"источник: задачи {source.get('problem_number', '—')}")

    notes = template.get("math_notes") or {}
    if notes.get("structure"):
        lines.append(f"структура: {notes['structure']}")
    for step in (notes.get("math") or [])[:6]:
        lines.append(f"  математика: {step}")

    schema = template.get("parameter_schema", {})
    compact = ", ".join(
        f"{name}:{rule.get('type')}"
        + (f"[{rule.get('min')}..{rule.get('max')}]" if "min" in rule else "")
        for name, rule in schema.items()
    )
    lines.append(f"параметры: {compact}")
    if template.get("derived_values"):
        lines.append("derived: " + "; ".join(f"{k} = {v}" for k, v in template["derived_values"].items()))
    lines.append(f"ответ: {template.get('answer_expression')}  ({template.get('answer_type')})")
    constraints = template.get("constraints") or []
    lines.append(f"constraints ({len(constraints)}): " + "; ".join(constraints) if constraints
                 else "constraints: НЕТ — проверь, точно ли не нужны")

    branches = branching_values(template)
    seen: dict[str, set[Any]] = {name: set() for name in branches}
    ok = 0

    def render(seed: int, note: str = "") -> bool:
        nonlocal ok
        try:
            generated = generate_active_template(template, random.Random(seed))
        except Exception as error:
            lines.append(f"  [seed {seed}] ОШИБКА: {error}")
            return False
        ok += 1
        for name in branches:
            seen[name].add(generated["parameters"].get(name))
        lines.append(f"  [{seed}]{note} {generated['rendered_problem']}")
        lines.append(f"       -> {generated.get('answer_text') or generated['answer']}")
        return True

    for seed in range(examples):
        render(seed)

    # Восемь примеров подряд могут показать одну ветку choice — так в шаблоне
    # про трамваи выжило «на маршрут убрали». Добираем недостающие значения.
    for name, values in branches.items():
        for value in values:
            if value in seen[name]:
                continue
            for seed in range(examples, examples + 400):
                try:
                    generated = generate_active_template(template, random.Random(seed))
                except Exception:
                    continue
                if generated["parameters"].get(name) == value:
                    render(seed, f" [{name}={value!r}]")
                    break
            else:
                lines.append(f"  ВНИМАНИЕ: ветка {name}={value!r} не встретилась за 400 сидов")

    lines.append(f"сгенерировано без ошибок: {ok}")
    if branches:
        lines.append("покрытие веток: " + ", ".join(
            f"{name} {len(seen[name])}/{len(values)}" for name, values in branches.items()))
    return "\n".join(lines)


def review_branch(base: str, examples: int) -> None:
    """Разобрать текущую ветку против базовой: всё, по чему решают «мерджить»."""
    head = git("rev-parse", "--abbrev-ref", "HEAD")
    if head == base:
        raise SystemExit(f"Текущая ветка — {base}. Переключитесь на проверяемую: git switch <ветка>")
    print(f"# Ветка {head} против {base}\n")

    commits = git("log", "--oneline", f"{base}..HEAD")
    print(f"## Коммиты ({len(commits.splitlines())})\n{commits or '—'}\n")

    changed = git("diff", "--name-only", f"{base}...HEAD").splitlines()

    engine = [
        path for path in changed
        if any(path.startswith(prefix) for prefix in ENGINE_PATHS) and not path.startswith("tests/")
    ]
    print("## Железное правило: Python под задачу")
    if engine:
        print("тронут код движка — прочитайте диффы и решите, общая это возможность или логика задачи:")
        for path in engine:
            # Показываем, каким коммитом тронуто: правка движка допустима,
            # если это общая возможность, и недопустима, если логика задачи.
            touched = git("log", "--oneline", f"{base}..HEAD", "--", path).splitlines()
            print(f"  {path}")
            for line in touched:
                print(f"      {line}")
    else:
        print("соблюдено: код движка не тронут")
    print()

    added_files = git("diff", "--name-only", "--diff-filter=A", f"{base}...HEAD").splitlines()
    noise = [
        path for path in added_files
        if "/history/" in path or "/runs/" in path or "/incoming/" in path or "/staging/" in path
    ]
    print("## Служебные файлы, добавленные в коммиты")
    print("\n".join(f"  {path}" for path in noise) if noise else "  нет")
    print()

    print("## Данные")
    data_paths = [
        path for path in changed
        if path.endswith("russian_nouns.json") or "entities/characters" in path or "universes.json" in path
    ]
    for path in data_paths:
        # Ключи верхнего уровня словаря и значения nom — то, что человек реально
        # вычитывает; служебные "forms": { и "cases": { только зашумляют.
        entries = []
        for line in git("diff", f"{base}...HEAD", "--", path).splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            stripped = line[1:].strip().rstrip(",")
            if stripped.endswith(': {') and stripped.count('"') == 2:
                key = stripped.split('"')[1]
                if key not in {"forms", "cases", "source_metadata"}:
                    entries.append(key)
            elif stripped.startswith('"nom":'):
                entries.append(stripped.split('"')[3])
        unique = list(dict.fromkeys(entries))
        print(f"  {path}: {len(unique)} новых — {', '.join(unique[:15])}")
    if not data_paths:
        print("  реестры не менялись")
    print()

    tests = [path for path in changed if path.startswith("tests/")]
    print("## Тесты")
    for path in tests:
        text = (PROJECT_ROOT / path).read_text(encoding="utf-8") if (PROJECT_ROOT / path).is_file() else ""
        has_solver = "matches_independent_solution" in text
        solver = "решатель есть" if has_solver else "РЕШАТЕЛЯ НЕТ"
        # Разбор отрендеренного текста — более сильная независимость: так решатель
        # физически не может подсмотреть формулу шаблона.
        source = "по тексту задачи" if "rendered_problem" in text and "findall" in text else "по parameters"
        print(f"  {path}: {solver}, решает {source}")
    if not tests:
        print("  НЕТ новых тестов")
    print()

    ledger = git("diff", "--stat", f"{base}...HEAD", "--", "docs/MIGRATION_LEDGER.md")
    print(f"## Журнал\n  {ledger or 'НЕ обновлён'}\n")

    templates = [path for path in changed if path.startswith("data/template_studio/library/")]
    print(f"## Шаблоны ({len(templates)})\n")
    for path in templates:
        file = PROJECT_ROOT / path
        if not file.is_file():
            print(f"### {path}: файл удалён\n")
            continue
        print(digest(json.loads(file.read_text(encoding="utf-8")), examples))
        print()


def main() -> None:
    """Показать очередь на проверку или принять шаблон в библиотеку."""
    parser = argparse.ArgumentParser(description="Выжимка очереди на проверку.")
    parser.add_argument("--examples", type=int, default=3)
    parser.add_argument("--rejected", action="store_true", help="Показать отклонённые и причины.")
    parser.add_argument("--accept", default=None, help="Перенести шаблон из incoming в library.")
    parser.add_argument("--branch", nargs="?", const="main", default=None, metavar="BASE",
                        help="Разобрать текущую ветку против базовой (по умолчанию main).")
    args = parser.parse_args()

    if args.branch:
        review_branch(args.branch, args.examples)
        return

    if args.accept:
        source = INCOMING / f"{args.accept}.json"
        if not source.is_file():
            raise SystemExit(f"Нет файла {source}")
        LIBRARY.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(LIBRARY / source.name))
        print(f"Принято в библиотеку: {source.name}. Дальше нужен тест-решатель и публикация.")
        return

    if args.rejected:
        paths = sorted(REJECTED.glob("*.json"))
        print(f"Отклонено: {len(paths)}\n")
        for path in paths:
            record = json.loads(path.read_text(encoding="utf-8"))
            print(f"### {record['template_id']} — задачи {', '.join(record.get('source_problems', []))}")
            for attempt in record.get("attempts", []):
                print(f"  попытка {attempt['n']}: {attempt.get('error')}")
            print()
        return

    paths = sorted(INCOMING.glob("*.json"))
    print(f"На проверке: {len(paths)} шаблонов\n")
    for path in paths:
        print(digest(json.loads(path.read_text(encoding="utf-8")), args.examples))
        print()


if __name__ == "__main__":
    main()
