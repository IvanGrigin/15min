"""Библиотека и активный каталог обязаны совпадать по составу.

Эта проверка закрывает слепую зону, которая уже дважды подводила: после
слияния сюжетного слоя активными остались 67 шаблонов из 113, а раньше —
50 из 54 после введения слота `clock`. В обоих случаях остальные тесты были
зелёными, потому что читают библиотеку напрямую, а не результат публикации.
Расхождение находилось только чтением строки «Активных шаблонов: N» в консоли.

Тест не публикует ничего сам — он требует, чтобы `python3
scripts/seed_worksheet_templates.py` был прогнан заранее (как и полагается
после любого изменения библиотеки, по правилам AGENTS.md). Если публикация
не запускалась ни разу, `test_active_catalogue_is_not_stale` подскажет это
прямо в сообщении о падении.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.catalogue import active_templates  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402


class LibraryPublicationSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.library_ids = {t["template_id"] for t in load_library()}
        self.active_ids = {t.get("template_id") for t in active_templates()}

    def test_every_library_template_is_active(self) -> None:
        """Шаблон, лежащий в библиотеке, обязан быть опубликован.

        Провал здесь означает одно из двух: либо кто-то забыл прогнать
        seed_worksheet_templates.py после добавления файла, либо публикация
        молча отклонила шаблон (как было с сюжетным профилем по умолчанию
        и с неизвестным движку слотом) — в обоих случаях сайт не выдаёт то,
        что есть в репозитории.
        """
        missing = sorted(self.library_ids - self.active_ids)
        self.assertEqual(
            missing, [],
            "Есть в библиотеке, но не в активном каталоге (нужен "
            f"`python3 scripts/seed_worksheet_templates.py`, либо публикация "
            f"отклонила шаблон — смотрите вывод команды): {missing}"
        )

    def test_no_active_template_without_a_library_file(self) -> None:
        """Активный каталог не должен переживать удалённый или переименованный файл.

        Иначе сайт продолжает выдавать задачу, которой в репозитории уже нет —
        так было с queue_of_three_generations после переименования в
        queue_of_three_groups: полный прогон публикации не подчищал каталог.
        """
        stale = sorted(self.active_ids - self.library_ids)
        self.assertEqual(
            stale, [],
            "Активны, но отсутствуют в библиотеке (устарели после удаления "
            f"или переименования файла): {stale}"
        )

    def test_active_catalogue_is_not_stale(self) -> None:
        """Число активных шаблонов обязано совпадать с числом файлов библиотеки.

        Более общая версия двух проверок выше — на случай, если множества
        совпадают по идентификаторам, но не по размеру из-за дублей в каталоге.
        """
        self.assertEqual(
            len(self.active_ids), len(self.library_ids),
            f"Активных шаблонов {len(self.active_ids)}, файлов в библиотеке "
            f"{len(self.library_ids)}. Прогоните "
            "`python3 scripts/seed_worksheet_templates.py` и проверьте вывод "
            "на строки `[FAIL]` и «Не прошли валидацию»."
        )


if __name__ == "__main__":
    unittest.main()
