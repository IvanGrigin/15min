"""Ссылки шаблонов на источник должны вести туда, где задача есть.

`source_metadata` — единственный способ вернуться от шаблона к первоисточнику
и сверить формулировку. Проверка началась после того, как у трёх шаблонов
подряд по указанным номерам открылись чужие задачи: про жука на клетчатом
поле вместо ошибки в умножении, про периметр прямоугольника вместо уроков
и перемен.

Причина оказалась однообразной: у каждой темы корпуса два файла — «без имён
и персонажей» и «с именами», нумерация в них общая, а записан был не тот.
Глазами это не видно: путь выглядит правдоподобно, номер существует
где-то рядом, и ошибка всплывает только когда кто-то открывает файл.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.seed_worksheet_templates import load_library  # noqa: E402

NUMBERED = re.compile(r"^(\d+)\.\s+\S")


def numbers_in(path: Path) -> set[int] | None:
    """Номера задач в файле корпуса; None, если файла нет."""
    if not path.exists():
        return None
    return {
        int(match.group(1))
        for line in path.read_text(encoding="utf-8").split("\n")
        if (match := NUMBERED.match(line))
    }


class SourceReferenceTests(unittest.TestCase):
    """Каждый номер обязан существовать в том файле, который назван рядом."""

    def test_every_reference_resolves(self) -> None:
        broken: list[str] = []
        cache: dict[str, set[int] | None] = {}
        for template in load_library():
            meta = template.get("source_metadata") or {}
            raw_numbers = str(meta.get("problem_number") or "")
            filename = str(meta.get("filename") or "")
            if not raw_numbers.strip():
                continue          # шаблон без прообраза в корпусе — это законно
            if not filename:
                broken.append(f"{template['template_id']}: номера есть, файла нет")
                continue
            if filename not in cache:
                cache[filename] = numbers_in(PROJECT_ROOT / filename)
            present = cache[filename]
            if present is None:
                broken.append(f"{template['template_id']}: файла {filename} не существует")
                continue
            absent = [int(value) for value in re.findall(r"\d+", raw_numbers)
                      if int(value) not in present]
            if absent:
                broken.append(
                    f"{template['template_id']}: в {Path(filename).name} "
                    f"нет задач {absent[:5]}")
        self.assertEqual(broken, [], "битые ссылки на источник:\n" + "\n".join(broken))

    def test_two_templates_do_not_claim_the_same_task(self) -> None:
        """Одна задача корпуса — один шаблон.

        Совпадение номеров означает либо дубль, либо чужую ссылку. Так
        нашлось, что system_sum_and_difference claimed задачи, которые
        на деле покрывает system_two_linear_equations: систем вида
        «сумма и разность» в корпусе нет вовсе.
        """
        # Многопунктовые задачи законно делятся между шаблонами: у задачи
        # 1313 пункт «а» про число четырёхзначных, а «б» и «в» — про чётные
        # и нечётные среди них. Тогда в метаданных пункт указывается
        # в скобках, и он входит в ключ.
        claimed: dict[tuple[str, str], str] = {}
        clashes: list[str] = []
        for template in load_library():
            meta = template.get("source_metadata") or {}
            filename = str(meta.get("filename") or "")
            raw = str(meta.get("problem_number") or "")
            for value, part in re.findall(r"(\d+)\s*(\([^)]*\))?", raw):
                if not value:
                    continue
                key = (filename, f"{value}{part}")
                if key in claimed:
                    clashes.append(
                        f"задачу {key[1]} из {Path(filename).name} заявляют "
                        f"{claimed[key]} и {template['template_id']}")
                else:
                    claimed[key] = template["template_id"]
        self.assertEqual(clashes, [], "пересекающиеся ссылки:\n" + "\n".join(clashes))

    def test_filename_points_at_the_corpus(self) -> None:
        """В поле файла однажды стояла фраза «усложнение задачи про хоббита»."""
        for template in load_library():
            filename = str((template.get("source_metadata") or {}).get("filename") or "")
            if not filename:
                continue
            self.assertTrue(
                filename.startswith("docs/") and filename.endswith(".md"),
                f"{template['template_id']}: {filename!r} не похоже на файл корпуса")


if __name__ == "__main__":
    unittest.main()
