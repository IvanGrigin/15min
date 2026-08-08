"""Чтение читаемых оригиналов корпуса: Word, текстовый слой PDF, листки.

Свод `docs/all_tasks_all_files.md` собран одним прогоном распознавания по всем
76 источникам, и текст в нём побит: «В 2 я = прямоугольнике 408 * 915»,
«111 ульев”», «Ha пони». Кое-где потеряна часть условия — у задачи 1 пропал
размер вырезанной дырки, без которого её не решить.

Распознавать заново нечего: **у каждого источника есть читаемый оригинал.**
Тридцать семь из них — файлы Word, ещё четыре PDF имеют текстовый слой,
а все тридцать четыре скана датированных пятнадцатиминуток целиком лежат
в «Копия 15-минутки (1 часть).docx» — там 53 листка, больше, чем в своде.

Модуль ничего не пишет: это набор функций чтения и нормализации, которым
пользуется `tools/build_corpus_v2.py`. Собственный вывод у него был —
`docs/CLEAN_CORPUS_2026.md`, первый подход к чистому корпусу; он заменён
корпусом v2 и лежит в `docs/archive/`.
"""
from __future__ import annotations

import difflib
import re
import subprocess
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES = PROJECT_ROOT / "docs" / "source_documents" / "2026"
MASTER = PROJECT_ROOT / "docs" / "all_tasks_all_files.md"
SHEETS_DOCX = SOURCES / "Копия 15-минутки (1 часть).docx"

HEADING = re.compile(r"^## (.+)$")
NUMBERED = re.compile(r"^(\d+)\.\s+(.+)$")
SHEET_MARK = re.compile(r"^ФамилияИмя(\d{2}\.\d{2}\.\d{4})$")
DATED_PDF = re.compile(r"(\d{2}\.\d{2}\.\d{4})\.pdf$")
# Ниже этого сходства пара считается неопознанной: задача из свода побита
# так, что уверенно указать её чистый оригинал нельзя.
MATCH_FLOOR = 0.55


def docx_text(path: Path) -> str:
    """Текст документа Word без разметки, абзацы и строки таблиц — переводом строки."""
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", re.sub(r"</w:p>|</w:tr>", "\n", xml))


def fix_mojibake(text: str) -> str:
    """Вернуть кириллицу, вышедшую из PDF в чужой кодировке.

    У двух сводных распечаток текстовый слой записан в cp1251, а извлекается
    как cp1252: «Íàéäèòå íåèçâåñòíîå» вместо «Найдите неизвестное». Перекодируются
    только цепочки от трёх символов подряд — знаки «−» и «×» в тех же файлах
    уже верные, и одиночный «×» превратился бы в букву «Ч».
    """
    out: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if not run:
            return
        chunk = "".join(run)
        # «íî» — это «но»: двух символов достаточно, если среди них есть буква.
        # Знаки «×» и «÷» под правило не попадают и остаются собой.
        has_letter = any(char in "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ" for char in chunk)
        # Однобуквенные предлоги «в», «и», «с», «а» выходят как «â», «è», «ñ», «à»
        # и стоят отдельными словами. Знаки «×» и «÷» буквами не считаются
        # и остаются собой.
        if len(chunk) >= 3 or (len(chunk) >= 1 and has_letter):
            out.append(chunk.encode("cp1252", errors="ignore").decode("cp1251", errors="ignore"))
        else:
            out.append(chunk)
        run.clear()

    for char in text:
        try:
            encoded = char.encode("cp1252")
        except UnicodeEncodeError:
            flush()
            out.append(char)
            continue
        if encoded[0] >= 0x80:
            run.append(char)
        else:
            flush()
            out.append(char)
    flush()
    return "".join(out)


# В текстовом слое двух распечаток «ё» записана сербской «ј»: «трјхзначное»,
# «нечјтных». В русском тексте эта буква не встречается, замена безопасна.
JE_FOR_YO = str.maketrans({"ј": "ё", "Ј": "Ё"})


def pdf_text(path: Path) -> str:
    """Текстовый слой PDF; у сканов его нет, и вернётся пустая строка."""
    done = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, check=False)
    # Замена идёт после перекодировки: «ј» и появляется из неё — в исходной
    # кодировке байт «ё» совпал с байтом сербской «ј».
    return fix_mojibake(done.stdout.decode("utf-8", errors="replace")).translate(JE_FOR_YO)


def meaningful(lines: list[str]) -> list[str]:
    """Строки, похожие на условие задачи, без служебных и обрывков."""
    return [line for line in (item.strip() for item in lines)
            if len(line) > 25 and not line.startswith("http")]


TASK_START = re.compile(r"^\s*\d+\*?[.)]\s")
ANSWER_COLUMN = re.compile(r"\s{2,}Ответ:\s*$")


def reflow(lines: list[str]) -> list[str]:
    """Собрать условие из строк, на которые его разбила вёрстка PDF.

    В распечатках задача занимает несколько строк с отступом, справа стоит
    колонка «Ответ:», а длинные слова перенесены дефисом. Пока это не
    склеено, ни одна строка целиком с задачей не совпадает — из-за этого
    у сводного `239-5_comb.pdf` не опознавалась половина задач.
    """
    blocks: list[list[str]] = []
    for raw in lines:
        line = ANSWER_COLUMN.sub("", raw.rstrip())
        if not line.strip():
            continue
        if TASK_START.match(line) or not blocks:
            blocks.append([line.strip()])
        else:
            blocks[-1].append(line.strip())
    joined: list[str] = []
    for block in blocks:
        text = ""
        for part in block:
            if text.endswith("-"):
                text = text[:-1] + part      # перенос по слогам: «каждо-» + «го»
            elif text:
                text += " " + part
            else:
                text = part
        if len(text) > 25:
            joined.append(text)
    return joined


def sheets_by_date() -> dict[str, list[str]]:
    """Пятнадцатиминутки из общего файла Word, разложенные по дате листка."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in docx_text(SHEETS_DOCX).splitlines():
        stripped = line.strip()
        mark = SHEET_MARK.match(stripped)
        if mark:
            current = mark.group(1)
            found.setdefault(current, [])
            continue
        if current and len(stripped) > 25:
            found[current].append(stripped)
    return found


def master_sections() -> dict[str, list[tuple[int, str]]]:
    """Свод, разложенный по источникам: путь → [(номер, текст)]."""
    sections: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for line in MASTER.read_text(encoding="utf-8").splitlines():
        heading = HEADING.match(line)
        if heading:
            current = heading.group(1)
            sections.setdefault(current, [])
            continue
        numbered = NUMBERED.match(line)
        if numbered and current:
            sections[current].append((int(numbered.group(1)), numbered.group(2).strip()))
    return sections


def clean_lines_for(source: str, sheets: dict[str, list[str]]) -> list[str]:
    """Читаемый текст источника: из Word, из текстового слоя или из общего файла листков."""
    dated = DATED_PDF.search(source)
    if dated and dated.group(1) in sheets:
        return meaningful(sheets[dated.group(1)])
    path = SOURCES / source
    if not path.exists():
        return []
    if path.suffix.lower() == ".docx":
        return meaningful(docx_text(path).splitlines())
    if path.suffix.lower() == ".pdf":
        return reflow(pdf_text(path).splitlines())
    return []


def normalized(text: str) -> str:
    """Только буквы и цифры в нижнем регистре: пунктуация у распознавания своя."""
    return re.sub(r"[^а-яёa-z0-9]", "", text.lower())


def align(master: list[tuple[int, str]], clean: list[str]) -> list[dict]:
    """Сопоставить задачи свода с их чистыми оригиналами внутри одного источника.

    Сравнение идёт по символам, а не по словам: распознавание чаще калечит
    буквы внутри слова, чем теряет слово целиком, и посимвольная мера это
    переживает. Область поиска — один источник, поэтому чужая задача
    в кандидаты почти не попадает.
    """
    aligned: list[dict] = []
    taken: set[int] = set()
    for number, text in master:
        best_index, best_score = None, 0.0
        for index, candidate in enumerate(clean):
            if index in taken:
                continue
            score = difflib.SequenceMatcher(None, normalized(text), normalized(candidate)).ratio()
            if score > best_score:
                best_index, best_score = index, score
        if best_index is None or best_score < MATCH_FLOOR:
            aligned.append({"master": number, "clean_text": None, "score": round(best_score, 3)})
            continue
        taken.add(best_index)
        aligned.append({"master": number,
                        "clean_text": re.sub(r"^\d+[.)]\s*", "", clean[best_index]).strip(),
                        "score": round(best_score, 3)})
    return aligned
