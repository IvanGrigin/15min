"""Пятнадцатиминутка в том виде, в каком её раздают детям.

Раскладка снята с бумажного листочка преподавателя: сверху линейка, под ней
шапка «Фамилия — Имя — дата», дальше пять задач, и каждая отделена такой же
линейкой. Между задачей и следующей линейкой оставлено место под решение —
именно оно делает листочек листочком, а не списком условий.

Линейки идут только под колонкой задач и не заходят под правое поле: там
стоят эмблема и QR-код. Оба подставляются файлами (`--logo`, `--qr`); своих
картинок модуль не рисует, потому что это чужие знаки, а не оформление.

Страница самодостаточна: разметка и стиль в одном файле, ничего не грузится
извне. Так её одинаково покажет и браузер, и печать в PDF.
"""
from __future__ import annotations

import base64
import html
import subprocess
import tempfile
from pathlib import Path

# Печатает браузером: раскладка описана обычным CSS, и заводить ради неё
# отдельную библиотеку вёрстки незачем — проект живёт на стандартной
# библиотеке, а Chrome печатает ровно то, что показывает.
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# Размеры взяты с бумажного листочка: поля узкие, чтобы пять задач с местом
# под решение уместились на одной странице.
PAGE_CSS = """
@page { size: A4 portrait; margin: 10mm 9mm; }

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
  font-size: 11.5pt;
  line-height: 1.34;
  color: #000;
}

/* Лист. На экране показывается страницей с тенью, на печати — просто лист.
   Высота задана жёстко: лист обязан заполняться до низа, иначе под
   последними задачами остаётся пустая треть страницы. */
.sheet {
  width: 192mm;
  height: 277mm;
  margin: 0 auto 8mm;
  padding: 0;
  background: #fff;
  display: grid;
  grid-template-columns: 1fr 26mm;
  column-gap: 4mm;
  page-break-after: always;
}
.sheet:last-child { page-break-after: auto; }

/* Без эмблемы и QR правое поле не резервируется: пустая полоса справа
   выглядела бы обрезанным листом. */
.sheet.plain { grid-template-columns: 1fr; column-gap: 0; }

/* Колонка задач — столбик, в котором свободное место делится между
   задачами по весу. Так место под решение не зависит от длины условия:
   длинное условие само по себе не отбирает поле для черновика. */
.column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Линейка над шапкой и под каждой задачей — одна и та же черта. */
.rule { border-top: 1px solid #9a9a9a; flex: 0 0 auto; }

.header {
  flex: 0 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-weight: bold;
  padding: 2.4mm 1mm 2.4mm;
}
.header .middle { flex: 1; text-align: center; }
.header .date { white-space: nowrap; }

/* Место под решение — это доля свободной высоты листа, а не отступ в
   миллиметрах: задача с длинным условием иначе осталась бы без черновика. */
.task {
  padding: 2.2mm 1mm 0;
  display: flex;
  flex-basis: auto;
  flex-shrink: 0;
}
.task .number { flex: 0 0 auto; padding-right: 1.6mm; }
.task .text { flex: 1 1 auto; }

.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3mm;
  padding-top: 6mm;
}
.brand img { width: 24mm; height: auto; display: block; }

/* Ключ печатается отдельной страницей и детям не выдаётся. */
.key { width: 192mm; margin: 0 auto; page-break-before: always; }
.key h2 { font-size: 12pt; margin: 0 0 3mm; }
.key ol { margin: 0; padding-left: 6mm; }
.key li { margin-bottom: 1.6mm; }
.key .meta { color: #666; font-size: 9.5pt; }

@media screen {
  body { background: #f2f2f2; padding: 6mm 0; }
  .sheet, .key {
    background: #fff;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.18);
    padding: 6mm;
  }
  .sheet { width: 210mm; height: 297mm; }
  .key { width: 210mm; }
}
"""

# Доля свободного места под решение. Счётной задаче хватает пары строк,
# сюжетной нужно поле: ребёнок пишет рассуждение, а не один пример.
# Числа — веса, а не миллиметры: делится то, что осталось от условий.
ROOM_BY_ROLE = {
    "счёт": 3,
    "уравнение или сравнение": 3,
    "средняя": 4,
    "трудная": 6,
}
DEFAULT_ROOM = 4


def picture(path: str | Path | None) -> str:
    """Картинка, вшитая в страницу целиком.

    Внешних ссылок здесь быть не должно: листочек уходит в печать и должен
    выглядеть одинаково без сети.
    """
    if path is None:
        return ""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Картинка не найдена: {source}")
    kind = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg",
            ".gif": "gif", ".svg": "svg+xml"}.get(source.suffix.lower())
    if kind is None:
        raise ValueError(f"Не знаю такого формата картинки: {source.suffix}")
    data = base64.b64encode(source.read_bytes()).decode("ascii")
    return f'<img src="data:image/{kind};base64,{data}" alt="">'


def room_for(task: dict) -> int:
    """Вес задачи при делении свободного места листа."""
    return ROOM_BY_ROLE.get(task.get("role", ""), DEFAULT_ROOM)


def sheet_html(sheet: list[dict], when: str, logo: str, qr: str,
               room: dict[int, int] | None = None) -> str:
    """Один листочек: шапка, пять задач, место под решение, линейки."""
    room = room or {}
    plain = " plain" if not (logo or qr) else ""
    parts = [
        f'<section class="sheet{plain}">',
        '  <div class="column">',
        '    <div class="rule"></div>',
        '    <div class="header">',
        '      <span>Фамилия</span>',
        '      <span class="middle">Имя</span>',
        f'      <span class="date">{html.escape(when)}</span>',
        '    </div>',
    ]
    for number, task in enumerate(sheet, start=1):
        weight = room.get(number, room_for(task))
        parts += [
            '    <div class="rule"></div>',
            f'    <div class="task" style="flex-grow: {weight}">',
            f'      <span class="number">{number}.</span>',
            f'      <span class="text">{html.escape(task["problem"])}</span>',
            '    </div>',
        ]
    parts += ['    <div class="rule"></div>', '  </div>']
    if not plain:
        parts.append(f'  <aside class="brand">{logo}{qr}</aside>')
    parts.append('</section>')
    return "\n".join(parts)


def key_html(sheets: list[tuple[list[dict], str]]) -> str:
    """Ключ ко всем листочкам — отдельной страницей, детям не выдаётся."""
    parts = ['<section class="key">',
             '  <h2>Ключ. Не выдавать вместе с листочком</h2>']
    for sheet, when in sheets:
        parts.append(f'  <p><b>{html.escape(when)}</b></p>')
        parts.append('  <ol>')
        for task in sheet:
            meta = f"{task['role']}, {task['difficulty']}, {task['template_id']}"
            parts.append(f'    <li>{html.escape(str(task["answer"]))} '
                         f'<span class="meta">[{html.escape(meta)}]</span></li>')
        parts.append('  </ol>')
    parts.append('</section>')
    return "\n".join(parts)


def render_worksheets(sheets: list[tuple[list[dict], str]],
                      logo_path: str | Path | None = None,
                      qr_path: str | Path | None = None,
                      with_key: bool = False,
                      room: dict[int, int] | None = None) -> str:
    """Готовая страница с листочками, при желании — с ключом в конце."""
    logo, qr = picture(logo_path), picture(qr_path)
    title = sheets[0][1] if len(sheets) == 1 else f"{len(sheets)} листочков"
    body = "\n".join(sheet_html(sheet, when, logo, qr, room)
                     for sheet, when in sheets)
    if with_key:
        body += "\n" + key_html(sheets)
    return (f'<!DOCTYPE html>\n<html lang="ru">\n<head>\n'
            f'<meta charset="utf-8">\n'
            f'<title>Пятнадцатиминутка {html.escape(title)}</title>\n'
            f'<style>{PAGE_CSS}</style>\n'
            f'</head>\n<body>\n{body}\n</body>\n</html>\n')


def to_pdf(page: str) -> bytes:
    """Напечатать готовую страницу в PDF и вернуть его содержимое."""
    if not CHROME.exists():
        raise FileNotFoundError(
            f"Не нашёл Chrome по пути {CHROME}. Сохраните страницу и "
            f"напечатайте её в PDF из любого браузера: раскладка та же.")
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "sheet.html"
        target = Path(folder) / "sheet.pdf"
        source.write_text(page, encoding="utf-8")
        result = subprocess.run(
            [str(CHROME), "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={target}", source.as_uri()],
            capture_output=True, text=True)
        if not target.exists():
            raise RuntimeError(f"Chrome не напечатал PDF:\n{result.stderr.strip()}")
        return target.read_bytes()
