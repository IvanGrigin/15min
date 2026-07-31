"""Сайт пятиминуток на декларативных шаблонах.

Единственный источник задач — активные JSON-шаблоны Template Studio
(`data/template_studio/library/*.json`, опубликованные через
`scripts/seed_worksheet_templates.py`). Python здесь только собирает вариант
и печатает страницу; условие, параметры и формула ответа живут в JSON.

Чем отличается от `problemgen/web/worksheet_site.py`: тот тянет 33 старых
Python-генератора, у которых имена персонажей подставляются в именительном
падеже независимо от контекста. Тот путь заархивирован — см.
`docs/ARCHIVED_LEGACY.md`.

Запуск:
    python3 run.py --studio
    python3 -m problemgen.web.studio_site --port 8091
"""
from __future__ import annotations

import argparse
import errno
import html
import json
import random
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from problemgen.russian.universes import (
    UniverseRegistryError,
    age_rating_options,
    audience_options,
    load_universes,
    universes_matching,
)
from problemgen.template_studio.catalogue import active_templates
from problemgen.template_studio.runtime import (
    TemplateRuntimeError,
    generate_active_template,
    normalize_value,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "catalog.json"
MIN_TASKS = 1
# Время запуска процесса печатается на странице: по нему сразу видно,
# что смотришь на сервер, поднятый до последних правок данных.
STARTED_AT = datetime.now().strftime("%d.%m.%Y %H:%M")
DEFAULT_TASKS = 5
# «Пятнадцатиминутка» — это про пятнадцать минут, а не про число задач:
# продуктового потолка у количества нет. Осталась только техническая
# граница, чтобы запрос на миллион задач не подвесил сервер; к смыслу
# листочка она отношения не имеет и в интерфейсе не показывается.
MAX_TASKS = 200
MAX_BODY_BYTES = 16_384

RUSSIAN_TITLES = {
    "ages_and_generations": "Возраст и поколения",
    "alphabetic_order": "Алфавитный порядок",
    "arithmetic": "Арифметические вычисления",
    "calendar_and_weekdays": "Календарь и дни недели",
    "clocks_dials_and_electronic_displays": "Часы и табло",
    "combinatorics_and_counting_variants": "Комбинаторика и варианты подсчёта",
    "comparison_of_numbers_and_expressions": "Сравнение чисел и выражений",
    "cubes_volume_and_spatial_geometry": "Кубы, объём и пространственная геометрия",
    "digits_number_notation_and_cryptarithms": "Цифры, запись чисел и криптарифмы",
    "divisibility_multiples_remainders_primes": "Делимость, кратность, остатки и простые числа",
    "equations": "Уравнения",
    "factors_products_and_factorials": "Множители, произведения и факториалы",
    "grid_figures_cuts_and_routes": "Фигуры на клетчатой бумаге, разрезания и маршруты",
    "heads_legs_wheels_and_object_counts": "Головы, ноги, колёса и подсчёт объектов",
    "integer_interval_counting": "Подсчёт целых чисел на промежутках",
    "logic_problems_and_condition_analysis": "Логические задачи и анализ условий",
    "money_purchases_prices_and_calculations": "Деньги, покупки и расчёты",
    "motion_speed_and_distance": "Движение, скорость и расстояние",
    "number_processes_and_repeated_operations": "Числовые процессы",
    "parity_invariants_strategies_and_moves": "Чётность, инварианты, стратегии и ходы",
    "pigeonhole_and_guaranteed_selection": "Принцип Дирихле и гарантированный выбор",
    "plane_geometry_rectangles_squares_and_areas": "Планиметрия: прямоугольники, квадраты и площади",
    "points_segments_and_positions_on_a_line": "Точки, отрезки и положения на прямой",
    "quantities_units_weight_and_scaling": "Величины, единицы, масса и масштаб",
    "ratios_fractions_proportions_and_percentages": "Отношения, дроби, пропорции и проценты",
    "sequences_progressions_and_sums": "Последовательности, прогрессии и суммы",
    "sets_clubs_acquaintances_and_tournaments": "Множества, клубы, знакомства и турниры",
    "systems_of_equations": "Системы уравнений",
    "work_productivity_and_joint_actions": "Работа и совместные действия",
    "time_zones_and_travel_schedules": "Часовые пояса и расписания",
    "word_problems_for_equation_setup": "Текстовые задачи на составление уравнений",
}


class WorksheetError(ValueError):
    """Некорректный запрос к генератору варианта."""


def module_title(module_id: str) -> str:
    """Человекочитаемое название темы по её module_id."""
    if module_id in RUSSIAN_TITLES:
        return RUSSIAN_TITLES[module_id]
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    for item in payload.get("problem_sets", []):
        if item.get("id") == module_id:
            return str(item.get("title") or module_id)
    return module_id


def available_modules() -> list[dict[str, Any]]:
    """Модули, у которых есть хотя бы один активный шаблон."""
    counts: dict[str, int] = {}
    for template in active_templates():
        module_id = str(template.get("module_id") or "")
        if module_id:
            counts[module_id] = counts.get(module_id, 0) + 1
    return [
        {"module_id": module_id, "title": module_title(module_id), "template_count": count}
        for module_id, count in sorted(counts.items(), key=lambda item: module_title(item[0]))
    ]


def available_settings() -> dict[str, Any]:
    """Возрастные рейтинги и аудитории, реально встречающиеся среди вселенных.

    Список рейтингов строится из данных, а не из полной шкалы схемы (0+…18+):
    сейчас все 116 вселенных семейные, и предлагать в выпадающем списке 16+
    или 18+ было бы кнопкой в никуда. Появится вселенная строже — появится
    и пункт списка, без правки этого файла.
    """
    registry = load_universes().values()
    present_ratings = {universe.age_rating for universe in registry}
    ratings = [rating for rating in age_rating_options() if rating in present_ratings]
    audience_counts: dict[str, int] = {}
    for universe in registry:
        if universe.audience != "any":
            audience_counts[universe.audience] = audience_counts.get(universe.audience, 0) + 1
    return {
        "age_ratings": ratings,
        # «any» не показывается как отдельный выбор: это состояние «фильтр не
        # применён» самого поля вселенной, а не осмысленное предпочтение.
        "audiences": [a for a in audience_options() if a != "any" and audience_counts.get(a)],
    }


def _validate_count(count: Any) -> int:
    if not isinstance(count, int) or isinstance(count, bool) or count < MIN_TASKS:
        raise WorksheetError(f"Количество задач — целое число не меньше {MIN_TASKS}.")
    if count > MAX_TASKS:
        raise WorksheetError(
            f"За один раз собирается не больше {MAX_TASKS} задач — это техническая "
            "граница, а не размер пятнадцатиминутки."
        )
    return count


def _resolve_setting(max_age_rating: str | None, audience: str | None) -> frozenset[str] | None:
    """Сеттинг в набор разрешённых вселенных, или None — «оставить всё на рандом».

    None — сознательный отдельный случай, а не «пустой фильтр»: он выключает
    любую фильтрацию по вселенным в runtime, а не сужает её до пустого множества.
    """
    if max_age_rating is None and audience is None:
        return None
    try:
        matching = universes_matching(max_age_rating, audience)
    except UniverseRegistryError as error:
        raise WorksheetError(str(error)) from error
    if not matching:
        raise WorksheetError(
            "Для этого сочетания возрастного рейтинга и аудитории нет ни одной "
            "вселенной. Выберите рейтинг постарше или аудиторию «любая»."
        )
    return frozenset(matching)


def generate_worksheet(
    *,
    task_count: int = DEFAULT_TASKS,
    module_ids: list[str] | None = None,
    seed: int | None = None,
    max_age_rating: str | None = None,
    audience: str | None = None,
) -> dict[str, Any]:
    """Собрать вариант из активных шаблонов.

    Без `module_ids` темы выбираются случайно из доступных. Один и тот же
    шаблон не попадает в вариант дважды, пока есть неиспользованные.

    `max_age_rating` и `audience` — необязательный сеттинг: рейтинг «не строже
    X» и предпочтение по вкусу. По умолчанию оба `None`, и это не «фильтр,
    который ничего не пропускает», а полное отсутствие фильтра — вариант
    собирается из всех вселенных, как и раньше. Указан хотя бы один — задачи,
    у которых есть общий мир (сюжетные шаблоны с character/from_universe_*),
    берут его только из подходящих; безликие шаблоны (числа, уравнения) фильтр
    не замечают вовсе, потому что не выбирают вселенную.
    """
    count = _validate_count(task_count)
    templates = active_templates()
    if not templates:
        raise WorksheetError(
            "Нет ни одного активного шаблона. Опубликуйте их: "
            "python3 scripts/seed_worksheet_templates.py"
        )
    rng = random.Random(seed)
    allowed_universes = _resolve_setting(max_age_rating, audience)

    pool = templates
    if module_ids:
        known = {str(item.get("module_id")) for item in templates}
        unknown = [module_id for module_id in module_ids if module_id not in known]
        if unknown:
            raise WorksheetError(f"Нет активных шаблонов для тем: {', '.join(unknown)}.")
        pool = [item for item in templates if str(item.get("module_id")) in set(module_ids)]

    ordered = sorted(pool, key=lambda item: str(item.get("template_id")))

    def render_task(position: int, template: dict[str, Any]) -> dict[str, Any]:
        generated = generate_active_template(template, rng, allowed_universes)
        story_context = generated.get("story_context", {})
        return {
            "position": position,
            "module_id": template.get("module_id"),
            "module_title": module_title(str(template.get("module_id"))),
            "template_id": template.get("template_id"),
            "source_problem_number": (template.get("source_metadata") or {}).get("problem_number"),
            "problem": generated["rendered_problem"],
            "answer": generated.get("answer_text") or str(normalize_value(generated["answer"])),
            "answer_value": normalize_value(generated["answer"]),
            "universe": story_context.get("universe"),
            # Метаданные служат проверкам и экспортам; HTML ученика их не выводит.
            "variant_metadata": generated.get("variant_metadata", {}),
            "structure_signature": _structure_signature(template),
            "principal_operation": _principal_operation(template),
        }

    tasks: list[dict[str, Any]] = []
    unused = list(ordered)
    shortage_fallback = False
    attempts = 0
    max_attempts = max(count * 20, len(ordered) * 5, 100)
    filtered_by_topic = bool(module_ids)
    while len(tasks) < count and attempts < max_attempts:
        if not unused:
            # Совместимость с API, в котором тестовый или пользовательский
            # фильтр оставил меньше шаблонов, чем просит лист. В нормальном
            # смешанном листе (113 записей на пять позиций) эта ветка недостижима.
            if len(ordered) >= count:
                break
            unused = list(ordered)
            shortage_fallback = True
        attempts += 1
        module_counts = _counts(tasks, "module_id")
        structure_counts = _counts(tasks, "structure_signature")
        operation_counts = _counts(tasks, "principal_operation")
        candidates = [
            template for template in unused
            if (filtered_by_topic or module_counts.get(str(template.get("module_id")), 0) < 2)
            and (shortage_fallback or structure_counts.get(_structure_signature(template), 0) == 0)
            and (filtered_by_topic or operation_counts.get(_principal_operation(template), 0) < 2)
        ]
        if not candidates:
            # При явном выборе одной темы допускаем повтор модуля, но не шаблона
            # и не математической микроструктуры. Это осознанное, узкое
            # ослабление, а не бесконечный пересэмплинг.
            candidates = [
                template for template in unused
                if (shortage_fallback or structure_counts.get(_structure_signature(template), 0) == 0)
                and (filtered_by_topic or operation_counts.get(_principal_operation(template), 0) < 2)
            ]
        if not candidates:
            break
        template = candidates[rng.randrange(len(candidates))]
        unused.remove(template)
        try:
            task = render_task(len(tasks) + 1, template)
        except TemplateRuntimeError:
            continue
        if task["universe"] and _counts(tasks, "universe").get(task["universe"], 0) >= 2:
            continue
        tasks.append(task)
    if len(tasks) < count:
        raise WorksheetError(
            "Не удалось собрать разнообразный вариант из выбранного набора тем. "
            "Выберите больше тем или уменьшите число задач."
        )

    return {
        "schema_version": 1,
        "source": "template_studio_library",
        "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "seed": seed,
        "task_count": count,
        "max_age_rating": max_age_rating,
        "audience": audience,
        "tasks": tasks,
    }


def _counts(tasks: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Посчитать непустые значения скрытого поля задач листа."""
    result: dict[str, int] = {}
    for task in tasks:
        value = task.get(key)
        if isinstance(value, str) and value:
            result[value] = result.get(value, 0) + 1
    return result


def _structure_signature(template: dict[str, Any]) -> str:
    """Нормализованный идентификатор микроструктуры из JSON.

    Пока автор не указал явный signature, ID шаблона безопаснее, чем угадывать
    математику из текста: совпадения тогда не создают ложных запретов.
    """
    return str(template.get("structure_signature") or template.get("template_id") or "unknown")


def _principal_operation(template: dict[str, Any]) -> str:
    """Главная операция для ограничения однообразия листа, также из JSON."""
    return str(template.get("principal_operation") or template.get("module_id") or "unknown")


PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Пятиминутки — новый генератор</title>
<style>
  :root {{ color-scheme: light dark; --line: #d8d8d8; --muted: #666; }}
  body {{ font: 16px/1.55 -apple-system, "Segoe UI", Roboto, sans-serif; margin: 0 auto;
         max-width: 820px; padding: 24px 20px 64px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  .lead {{ color: var(--muted); margin: 0 0 24px; }}
  fieldset {{ border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; margin: 0 0 18px; }}
  legend {{ padding: 0 6px; color: var(--muted); font-size: 14px; }}
  label.chk {{ display: inline-block; margin: 3px 14px 3px 0; white-space: nowrap; }}
  .row {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
  input[type=number] {{ width: 76px; padding: 6px; }}
  button {{ padding: 9px 18px; border-radius: 8px; border: 1px solid var(--line);
           background: #1a73e8; color: #fff; font-size: 15px; cursor: pointer; }}
  button.secondary {{ background: transparent; color: inherit; }}
  ol {{ padding-left: 22px; }}
  li {{ margin: 0 0 16px; }}
  .meta {{ color: var(--muted); font-size: 12px; margin-top: 3px; }}
  .answers {{ border-top: 1px dashed var(--line); margin-top: 28px; padding-top: 14px; }}
  .answers li {{ margin: 0 0 6px; }}
  .empty {{ color: var(--muted); }}
  @media print {{
    form, .noprint {{ display: none; }}
    body {{ max-width: none; }}
  }}
</style>
</head>
<body>
<h1>Пятиминутки</h1>
<p class="lead">Генератор на декларативных шаблонах: падежи, род и согласование
берутся из данных. Активных шаблонов: {template_count}.<br>
Загружено при запуске: {data_summary}. Сервер поднят {started_at}.</p>

<form id="form">
  <fieldset>
    <legend>Темы (пусто — любые)</legend>
    <div id="modules">{modules}</div>
  </fieldset>
  <fieldset>
    <legend>Сеттинг (по умолчанию — полный рандом)</legend>
    <div class="row">
      <label>Возраст
        <select id="age_rating"><option value="">любой</option></select>
      </label>
      <label>Кому
        <select id="audience">
          <option value="">любая аудитория</option>
          <option value="girls">девочкам</option>
          <option value="boys">мальчикам</option>
        </select>
      </label>
    </div>
    <p class="meta">Рейтинг — по источнику вселенной (мультфильм, игра),
      не по содержанию задачи: она всегда только про числа. «Кому» — мягкое
      предпочтение по вкусу, не про то, кто способен решать; можно оставить
      «любая» и получить весь набор миров.</p>
  </fieldset>
  <div class="row">
    <label>Задач <input type="number" id="count" value="{default_tasks}" min="1"></label>
    <label>Seed <input type="number" id="seed" placeholder="любой"></label>
    <button type="submit">Собрать вариант</button>
    <button type="button" class="secondary" onclick="window.print()">Печать</button>
  </div>
</form>

<div id="result"></div>

<script>
const form = document.getElementById('form');
const result = document.getElementById('result');
const ageSelect = document.getElementById('age_rating');

// Список рейтингов приходит с сервера, а не зашит в страницу: появится
// вселенная строже 12+ — пункт возникнет сам, без правки этого файла.
fetch('/api/settings').then(response => response.json()).then(data => {{
  for (const rating of (data.age_ratings || [])) {{
    const option = document.createElement('option');
    option.value = rating; option.textContent = 'не строже ' + rating;
    ageSelect.appendChild(option);
  }}
}}).catch(() => {{}});

form.addEventListener('submit', async (event) => {{
  event.preventDefault();
  const modules = [...document.querySelectorAll('#modules input:checked')].map(node => node.value);
  const seedRaw = document.getElementById('seed').value;
  const body = {{
    task_count: Number(document.getElementById('count').value),
    module_ids: modules,
    seed: seedRaw === '' ? null : Number(seedRaw),
    max_age_rating: document.getElementById('age_rating').value || null,
    audience: document.getElementById('audience').value || null,
  }};
  result.innerHTML = '<p class="empty">Собираю…</p>';
  const response = await fetch('/api/worksheet', {{
    method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(body),
  }});
  const data = await response.json();
  if (!response.ok) {{ result.innerHTML = '<p class="empty">' + (data.error || 'Ошибка') + '</p>'; return; }}
  render(data);
}});

function escape(text) {{
  return String(text).replace(/[&<>]/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}})[ch]);
}}

function render(data) {{
  const tasks = data.tasks.map(task =>
    '<li>' + escape(task.problem) +
    '<div class="meta noprint">' + escape(task.module_title) + ' · ' + escape(task.template_id) +
    (task.universe ? ' · ' + escape(task.universe) : '') + '</div></li>').join('');
  const answers = data.tasks.map(task => '<li>' + escape(task.answer) + '</li>').join('');
  const settingBits = [];
  if (data.max_age_rating) settingBits.push('рейтинг не строже ' + data.max_age_rating);
  if (data.audience) settingBits.push('аудитория: ' + (data.audience === 'girls' ? 'девочкам' : 'мальчикам'));
  const settingLine = settingBits.length
    ? ' · сеттинг: ' + settingBits.join(', ')
    : ' · сеттинг: любой (полный рандом)';
  result.innerHTML =
    '<p class="meta">' + escape(data.generated_at) + ' · seed ' + (data.seed ?? '—') +
    escape(settingLine) + '</p>' +
    '<ol>' + tasks + '</ol>' +
    '<div class="answers"><strong>Ответы</strong><ol>' + answers + '</ol></div>';
}}

// Вариант собирается сразу при открытии: страница без задач ничего не говорит
// о том, как сейчас выглядят пятиминутки.
form.dispatchEvent(new Event('submit'));
</script>
</body>
</html>
"""


def render_page() -> str:
    """Собрать HTML страницы генератора со списком доступных тем."""
    modules = available_modules()
    checkboxes = "".join(
        f'<label class="chk"><input type="checkbox" value="{html.escape(item["module_id"])}"> '
        f'{html.escape(item["title"])} <span class="meta">({item["template_count"]})</span></label>'
        for item in modules
    ) or '<span class="empty">Активных шаблонов нет.</span>'
    return PAGE.format(
        modules=checkboxes,
        data_summary=html.escape(_data_summary()),
        started_at=STARTED_AT,
        default_tasks=DEFAULT_TASKS,
        template_count=sum(item["template_count"] for item in modules),
    )


class Handler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов сайта пятиминуток."""
    server_version = "StudioWorksheet/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Записать строку журнала запросов с понятным префиксом."""
        print(f"[studio-site] {self.address_string()} - {format % args}")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        """Отдать страницу или список тем."""
        path = urlparse(self.path).path
        if path == "/":
            self._send(HTTPStatus.OK, render_page().encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/modules":
            self._send_json(HTTPStatus.OK, {"modules": available_modules()})
            return
        if path == "/api/settings":
            self._send_json(HTTPStatus.OK, available_settings())
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Нет такого адреса."})

    def do_POST(self) -> None:  # noqa: N802
        """Собрать вариант по параметрам запроса."""
        if urlparse(self.path).path != "/api/worksheet":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Нет такого адреса."})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Некорректный Content-Length."})
            return
        if length > MAX_BODY_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Слишком большой запрос."})
            return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Тело запроса не является JSON."})
            return
        try:
            raw_rating = payload.get("max_age_rating")
            raw_audience = payload.get("audience")
            worksheet = generate_worksheet(
                task_count=payload.get("task_count", 5),
                module_ids=[str(item) for item in (payload.get("module_ids") or [])] or None,
                seed=payload.get("seed") if isinstance(payload.get("seed"), int) else None,
                max_age_rating=str(raw_rating) if isinstance(raw_rating, str) and raw_rating else None,
                audience=str(raw_audience) if isinstance(raw_audience, str) and raw_audience else None,
            )
        except (WorksheetError, ValueError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self._send_json(HTTPStatus.OK, worksheet)


def _data_summary() -> str:
    """Короткая сводка загруженных данных — по ней видно, свежий ли процесс."""
    from problemgen.russian.characters import characters_by_universe
    from problemgen.russian.noun_dict import NOUNS
    from problemgen.russian.universes import load_universes

    registry = characters_by_universe()
    return (f"{len(load_universes())} вселенных, "
            f"{sum(len(items) for items in registry.values())} персонажей, "
            f"{len(NOUNS)} существительных")


def serve(host: str = "127.0.0.1", port: int = 8091) -> None:
    """Запустить локальный сервер сайта.

    Занятый порт — не техническая мелочь, а ловушка: старый процесс держит
    в памяти словарь и реестры на момент своего запуска, поэтому страница
    показывает вчерашние данные и ошибки вида «слова "оса" нет в словаре».
    Поэтому сообщение объясняет, что делать, а не показывает traceback.
    """
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as error:
        if error.errno not in (errno.EADDRINUSE, errno.EACCES):
            raise
        raise SystemExit(
            f"Порт {port} уже занят — скорее всего, там висит запущенный раньше сайт.\n"
            "Он держит в памяти словарь и реестры на момент своего запуска,\n"
            "поэтому показывает устаревшие задачи и ошибки про «нет в словаре».\n\n"
            "Остановить старый и запустить заново:\n"
            f"  kill $(lsof -t -iTCP:{port} -sTCP:LISTEN) && python3 run.py\n\n"
            f"Либо поднять рядом на другом порту:  python3 run.py --port {port + 1}"
        ) from error
    modules = available_modules()
    print(f"Пятиминутки на декларативных шаблонах: http://{host}:{port}")
    print(f"Тем: {len(modules)}, шаблонов: {sum(item['template_count'] for item in modules)}")
    print(f"Данные загружены: {_data_summary()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        server.server_close()


def main() -> None:
    """Разобрать аргументы командной строки и запустить сервер."""
    parser = argparse.ArgumentParser(description="Сайт пятиминуток на JSON-шаблонах.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
