"""Корпус v2: у каждого номера — настоящая задача, и у каждой задачи — номер.

Свод `docs/all_tasks_all_files.md` собран одним прогоном распознавания, и его
нумерация описывает не задачи, а строки: из 2121 номера настоящих задач около
1188, остальное — обрывки («Про четырёхзначное число известно,»), критерии
оценивания и служебный текст. Часть условий побита так, что задачу не решить:
у первой пропал размер вырезанной дырки.

Здесь корпус собирается **от читаемых оригиналов**, а не от свода. Это меняет
главное: задача попадает в v2, даже если её запись в своде разрушена до
неузнаваемости, — оригинал-то цел. Свод остаётся неизменяемым, а его номер
проставляется рядом там, где сопоставление уверенное.

Собирается условие целиком: в распечатках его разносит вёрстка, в файлах Word —
абзацы («Натуральные числа от 1 до 120 выписаны подряд.» и «Сколько раз
встречается цифра 2?» лежат порознь). Пока это не склеено, половина задач
выглядит обрывками — ровно тем, от чего уходим.

    python3 tools/build_corpus_v2.py

Пишет `docs/all_tasks_all_files_v2.md` и `data/source_index/number_map.json`.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

from tools.build_clean_corpus import (
    MATCH_FLOOR, SOURCES, docx_text, master_sections, normalized, pdf_text,
    sheets_by_date, DATED_PDF,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_CORPUS = PROJECT_ROOT / "docs" / "all_tasks_all_files_v2.md"
OUT_MAP = PROJECT_ROOT / "data" / "source_index" / "number_map.json"

ITEM_START = re.compile(r"^\s*\d+\*?[.)]\s")
# Пункты «a)», «б)» — продолжение той же задачи, а не новая: отрывать их
# нельзя, иначе «b) Сколько килограммов чернослива?» останется без условия.
SUBITEM = re.compile(r"^\s*[a-zа-яё]\)\s")
# Пометки проверяющего: «0/3», «нет вычисления в столбик — 1 балл».
GRADING = re.compile(r"\bбалл")
# «0/3», «0/1/3» — доли выставленного балла, попадают из полей проверки.
SCORE_MARK = re.compile(r"\s\d\s*/\s*\d(?:\s*/\s*\d)?(?=\s|$)")
# Колонка «Ответ:» стоит справа от условия и после склейки строк
# оказывается внутри него, а не в конце.
ANSWER_COLUMN = re.compile(r"\s*Ответ:\s*")
ASKS = re.compile(
    r"\?|сколько|найдите|найти|чему равн|како[еймя]|каки[ех]|во сколько|за сколько"
    r"|через сколько|определите|вычислите|может ли|сможет ли|докажите|расставьте"
    r"|придумайте|представьте|запишите|укажите|восстановите|расположите",
    re.IGNORECASE)
EXPRESSION = re.compile(r"\d\s*[+\-−⋅×*:/]\s*\d")
# Строки организационного характера: как сдавать работу, куда слать, чем снимать.
SERVICE = re.compile(
    r"http|@|почт|фамили|черновик|отправить|назвать файл|инструкц|ориентац"
    r"|проверяться|таблица с ответами|как оформлять|пример[ун] таблич|это дз",
    re.IGNORECASE)


def source_lines(source: str, sheets: dict[str, list[str]]) -> list[str]:
    """Сырые строки читаемого оригинала: Word, текстовый слой или общий файл листков."""
    dated = DATED_PDF.search(source)
    if dated and dated.group(1) in sheets:
        return list(sheets[dated.group(1)])
    path = SOURCES / source
    if not path.exists():
        return []
    if path.suffix.lower() == ".docx":
        return docx_text(path).splitlines()
    if path.suffix.lower() == ".pdf":
        return pdf_text(path).splitlines()
    return []


def merge(block: list[str]) -> str:
    """Склеить строки одной задачи, сращивая переносы по слогам."""
    text = ""
    for part in block:
        part = part.strip()
        if not part:
            continue
        if text.endswith("-"):
            text = text[:-1] + part          # «каждо-» + «го» -> «каждого»
        elif text:
            text += " " + part
        else:
            text = part
    return re.sub(r"\s{2,}", " ", text).strip()


def blocks_of(lines: list[str]) -> list[str]:
    """Разбить строки источника на условия задач.

    Новый блок начинается с номера пункта. Если номера нет, строка
    продолжает предыдущий блок до тех пор, пока в нём не появился вопрос:
    в файлах Word условие и вопрос — разные абзацы, и разрывать их нельзя.
    """
    blocks: list[list[str]] = []
    for raw in lines:
        line = SCORE_MARK.sub("", ANSWER_COLUMN.sub("", raw.rstrip())).strip()
        if not line:
            continue
        if SUBITEM.match(line) and blocks:
            blocks[-1].append(line)
            continue
        starts_item = bool(ITEM_START.match(line))
        if starts_item or not blocks:
            blocks.append([line])
            continue
        current = merge(blocks[-1])
        if "?" in current and len(current) > 40:
            blocks.append([line])            # прошлая задача закончена вопросом
        else:
            blocks[-1].append(line)
    return [merge(block) for block in blocks]


def is_task(text: str) -> bool:
    """Похоже ли это на условие задачи, а не на служебную строку."""
    if len(text) < 40 or not re.search(r"\d", text):
        return False
    if SERVICE.search(text) or GRADING.search(text):
        return False
    return bool(ASKS.search(text) or EXPRESSION.search(text))


def collect() -> list[dict]:
    """Все задачи из читаемых оригиналов, в порядке источников свода."""
    sheets = sheets_by_date()
    seen: set[str] = set()
    tasks: list[dict] = []
    for source in master_sections():
        for text in blocks_of(source_lines(source, sheets)):
            if not is_task(text):
                continue
            body = re.sub(r"^\d+\*?[.)]\s*", "", text).strip()
            key = normalized(body)
            if not key or key in seen:
                continue                     # одна задача часто лежит в двух файлах
            seen.add(key)
            tasks.append({"source": source, "text": body})
    return tasks


def attach_master_numbers(tasks: list[dict]) -> None:
    """Проставить каждой задаче её номер в своде, где сопоставление уверенное."""
    by_source: dict[str, list[tuple[int, str]]] = master_sections()
    grouped: dict[str, list[dict]] = {}
    for task in tasks:
        grouped.setdefault(task["source"], []).append(task)
    for source, entries in grouped.items():
        pool = list(by_source.get(source, []))
        for task in entries:
            best, score = None, 0.0
            for number, master_text in pool:
                ratio = difflib.SequenceMatcher(
                    None, normalized(task["text"]), normalized(master_text)).ratio()
                if ratio > score:
                    best, score = number, ratio
            if best is not None and score >= MATCH_FLOOR:
                task["master"] = best
                task["score"] = round(score, 3)
                pool = [item for item in pool if item[0] != best]
            else:
                task["master"] = None
                task["score"] = round(score, 3)


def main() -> None:
    """Собрать корпус v2 и карту соответствия номеров."""
    tasks = collect()
    attach_master_numbers(tasks)

    lines = [
        "# Все задачи из всех файлов, версия 2",
        "",
        "Собран `tools/build_corpus_v2.py` из читаемых оригиналов в",
        "`docs/source_documents/2026`. В отличие от свода",
        "`docs/all_tasks_all_files.md`, здесь **каждый номер — это задача**:",
        "обрывки строк, критерии оценивания и служебный текст отсеяны,",
        "переносы по слогам сращены, условие и вопрос собраны вместе.",
        "",
        "Номер той же задачи в своде указан в скобках — `(свод 123)`.",
        "Пометка `(в своде не найдена)` означает, что запись свода разрушена",
        "распознаванием до неузнаваемости либо задачи там нет вовсе.",
        "",
        "Свод не переписывается: на его номера ссылаются `source_metadata`",
        "шаблонов. Соответствие номеров — `data/source_index/number_map.json`.",
        "",
    ]
    mapping = []
    current_source = None
    for index, task in enumerate(tasks, start=1):
        if task["source"] != current_source:
            current_source = task["source"]
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend([f"## {current_source}", ""])
        tail = f"  (свод {task['master']})" if task["master"] else "  (в своде не найдена)"
        lines.append(f"{index}. {task['text']}{tail}")
        mapping.append({"v2": index, "master": task["master"],
                        "source": task["source"], "score": task["score"]})
    lines.append("")

    OUT_CORPUS.write_text("\n".join(lines), encoding="utf-8")
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    OUT_MAP.write_text(json.dumps({
        "comment": "Мост между нумерацией docs/all_tasks_all_files.md (master) "
                   "и docs/all_tasks_all_files_v2.md (v2).",
        "pairs": mapping,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linked = sum(1 for row in mapping if row["master"])
    print(f"задач в v2: {len(tasks)}")
    print(f"из них связаны с номером свода: {linked} ({100 * linked / len(tasks):.1f}%)")
    print(f"написано: {OUT_CORPUS.name}, {OUT_MAP.name}")


if __name__ == "__main__":
    main()
