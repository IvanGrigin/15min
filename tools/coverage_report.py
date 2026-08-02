"""Сколько задач корпуса умеет печатать библиотека шаблонов.

Мера грубая и намеренно простая: задача считается покрытой, если её текст
достаточно близок по словам к тому, что печатает хоть один шаблон. Точную
меру тут построить нельзя — одна и та же задача в корпусе записана десятком
способов, — но грубой хватает, чтобы видеть, какие темы стоят непочатыми.

Повторы схлопываются: в корпусе одна задача встречается в нескольких файлах
и под разными номерами, и считать её несколько раз значит обманывать себя.

    python3 tools/coverage_report.py            — сводка по темам
    python3 tools/coverage_report.py --missing 30   — 30 непокрытых задач темы
"""
from __future__ import annotations

import argparse
import random
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import (  # noqa: E402
    TemplateResampleError, TemplateRuntimeError, generate_active_template,
)
from scripts.seed_worksheet_templates import load_library  # noqa: E402

DOCS = PROJECT_ROOT / "docs"
TASK_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
SAMPLES_PER_TEMPLATE = 8
COVERED_AT = 0.42
# Слова, которые есть в любой задаче и потому ничего не различают.
STOP = frozenset("""
и в на с а но что это как за по из у к о от до для не так же то же ли бы
сколько какое какой какая какие сколькими найдите найти чему равно чтобы
если то все всех всего было были был будет может можно нужно один одна одно
числа число чисел этом этих том том числе после каждый каждая каждое
""".split())


# Окончания отрезаются грубо, по длине: «сумму» и «сумма» — одно слово,
# и считать их разными значит занижать покрытие там, где задача узнана.
# Полноценная лемматизация тут не нужна: мера и так грубая, а ошибки
# отсечения одинаково задевают обе сравниваемые стороны.
ENDINGS = (
    "ами", "ями", "ого", "ему", "ыми", "ими", "ей", "ой", "ый", "ий", "ая",
    "яя", "ое", "ее", "ые", "ие", "ам", "ям", "ах", "ях", "ов", "ев", "ью",
    "ом", "ем", "их", "ых", "ую", "юю", "а", "я", "о", "е", "у", "ю", "ы",
    "и", "й", "ь",
)


def stem(word: str) -> str:
    """Слово без окончания — настолько грубо, насколько это безопасно."""
    for ending in ENDINGS:
        if len(word) - len(ending) >= 4 and word.endswith(ending):
            return word[: -len(ending)]
    return word


def words(text: str) -> Counter[str]:
    """Значимые основы слов текста, приведённые к нижнему регистру."""
    found = re.findall(r"[а-яёa-z]+", text.lower())
    return Counter(
        stem(word) for word in found if word not in STOP and len(word) > 2
    )


def similarity(left: Counter[str], right: Counter[str]) -> float:
    """Доля общих слов относительно более короткого текста.

    Считается от короткого, а не от объединения: шаблон обычно печатает
    условие подробнее корпусного, и мера по объединению занижала бы совпадение
    там, где задача узнаётся однозначно.
    """
    if not left or not right:
        return 0.0
    shared = sum((left & right).values())
    return shared / min(sum(left.values()), sum(right.values()))


def load_corpus() -> dict[str, list[tuple[str, str]]]:
    """Пронумерованные задачи по темам: {файл: [(номер, текст)]}."""
    corpus: dict[str, list[tuple[str, str]]] = {}
    for path in sorted(DOCS.glob("*.md")):
        if not path.name[0].isdigit():
            continue
        found = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = TASK_RE.match(line)
            if match and len(match.group(2)) > 40:
                found.append((match.group(1), match.group(2).strip()))
        if found:
            corpus[path.name] = found
    return corpus


def dedup(corpus: dict[str, list[tuple[str, str]]]) -> dict[str, list[tuple[str, str]]]:
    """Схлопнуть повторы: одна задача живёт в нескольких файлах и номерах."""
    seen: set[str] = set()
    result: dict[str, list[tuple[str, str]]] = {}
    for name, tasks in corpus.items():
        kept = []
        for number, text in tasks:
            key = " ".join(sorted(words(text)))
            if key and key not in seen:
                seen.add(key)
                kept.append((number, text))
        result[name] = kept
    return result


def template_prints() -> list[Counter[str]]:
    """Слова всего, что библиотека умеет напечатать."""
    prints = []
    for template in load_library():
        for seed in range(SAMPLES_PER_TEMPLATE):
            try:
                generated = generate_active_template(template, random.Random(seed))
            except (TemplateResampleError, TemplateRuntimeError):
                continue
            prints.append(words(generated["rendered_problem"]))
    return prints


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", type=int, default=0,
                        help="показать столько непокрытых задач по каждой теме")
    parser.add_argument("--theme", default="", help="только темы, чьё имя содержит это")
    options = parser.parse_args()

    prints = template_prints()
    corpus = dedup(load_corpus())

    total = covered = 0
    for name, tasks in corpus.items():
        if options.theme and options.theme not in name:
            continue
        hits = []
        misses = []
        for number, text in tasks:
            task_words = words(text)
            best = max((similarity(task_words, printed) for printed in prints), default=0.0)
            (hits if best >= COVERED_AT else misses).append((number, text))
        total += len(tasks)
        covered += len(hits)
        share = len(hits) / len(tasks) * 100 if tasks else 0.0
        print(f"{share:5.1f}%  {len(hits):4d}/{len(tasks):<4d}  {name}")
        for number, text in misses[:options.missing]:
            print(f"          {number}. {text[:150]}")
    if total:
        print(f"\nИТОГО: {covered}/{total} = {covered / total * 100:.1f}%")


if __name__ == "__main__":
    main()
