from __future__ import annotations

import html
import json
import mimetypes
import random
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from problemgen.generation.arithmetic_templates import (
    arithmetic_template_metadata,
    generate_arithmetic_problem,
    generate_arithmetic_worksheet,
    load_arithmetic_templates,
)
from problemgen.generation.comparison_templates import (
    comparison_template_metadata,
    generate_comparison_problem_from_module,
)
from problemgen.generation.equation_templates import (
    equation_template_metadata,
    generate_equation_problem_from_module,
)
from problemgen.generation.system_equation_templates import (
    generate_system_equation_problem_from_module,
    system_equation_template_metadata,
)
from problemgen.generation.sequence_templates import (
    generate_sequence_problem_from_module,
    sequence_template_metadata,
)
from problemgen.generation.integer_interval_templates import (
    generate_integer_interval_problem_from_module,
    integer_interval_template_metadata,
)
from problemgen.generation.divisibility_templates import generate_divisibility_problem_from_module, divisibility_template_metadata
from problemgen.generation.digits_templates import (
    digits_template_metadata,
    generate_digits_problem_from_module,
)
from problemgen.generation.ratio_templates import generate_ratio_problem_from_module, ratio_template_metadata
from problemgen.generation.factor_product_templates import (
    factor_product_template_metadata,
    generate_factor_product_problem_from_module,
)
from problemgen.generation.combinatorics_templates import combinatorics_template_metadata, generate_combinatorics_problem_from_module
from problemgen.generation.pigeonhole_templates import pigeonhole_template_metadata, generate_pigeonhole_problem_from_module
from problemgen.generation.parity_templates import parity_template_metadata, generate_parity_problem_from_module
from problemgen.worksheet.all_tasks_site import (
    generate_problem_instance,
    recovered_templates,
    recovery_stats,
    unverified_templates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "generated"
ASSETS_ROOT = PROJECT_ROOT / "assets"
MIN_TASK_COUNT = 1
MAX_TASK_COUNT = 20
VERIFIED_MODULE_IDS = (
    "arithmetic",
    "equations",
    "systems_of_equations",
    "comparison_of_numbers_and_expressions",
    "sequences_progressions_and_sums",
    "ratios_fractions_proportions_and_percentages",
    "factors_products_and_factorials",
    "combinatorics_and_counting_variants",
    "pigeonhole_and_guaranteed_selection",
    "parity_invariants_strategies_and_moves",
)
ARCHIVE_MODULE_ID = "all_tasks_archive"
RECOVERED_ARCHIVE_MODULE_ID = "all_tasks_recovered"


def _validate_task_count(count: int) -> int:
    if not isinstance(count, int) or isinstance(count, bool) or not MIN_TASK_COUNT <= count <= MAX_TASK_COUNT:
        raise ValueError(f"Количество задач должно быть целым числом от {MIN_TASK_COUNT} до {MAX_TASK_COUNT}.")
    return count


def _combined_template_metadata() -> dict[str, Any]:
    arithmetic = arithmetic_template_metadata()
    equations = equation_template_metadata()
    systems = system_equation_template_metadata()
    comparisons = comparison_template_metadata()
    sequences = sequence_template_metadata()
    intervals = integer_interval_template_metadata()
    divisibility = divisibility_template_metadata()
    digits = digits_template_metadata()
    ratios = ratio_template_metadata()
    factors = factor_product_template_metadata()
    combinatorics = combinatorics_template_metadata()
    pigeonhole = pigeonhole_template_metadata()
    parity = parity_template_metadata()
    modules = list(arithmetic.get("modules", [])) + list(equations.get("modules", [])) + list(systems.get("modules", [])) + list(comparisons.get("modules", [])) + list(sequences.get("modules", [])) + list(intervals.get("modules", [])) + list(divisibility.get("modules", [])) + list(digits.get("modules", [])) + list(factors.get("modules", [])) + list(ratios.get("modules", [])) + list(combinatorics.get("modules", [])) + list(pigeonhole.get("modules", [])) + list(parity.get("modules", []))
    templates = list(arithmetic.get("templates", [])) + list(equations.get("templates", [])) + list(systems.get("templates", [])) + list(comparisons.get("templates", [])) + list(sequences.get("templates", [])) + list(intervals.get("templates", [])) + list(divisibility.get("templates", [])) + list(digits.get("templates", [])) + list(factors.get("templates", [])) + list(ratios.get("templates", [])) + list(combinatorics.get("templates", [])) + list(pigeonhole.get("templates", [])) + list(parity.get("templates", []))
    archive_stats = recovery_stats()
    recovered_archive_module = {
        "module_id": RECOVERED_ARCHIVE_MODULE_ID,
        "display_name": "Архив: восстановленные формулы",
        "title": "Проверенные выражения из общего корпуса",
        "template_count": archive_stats["recovered_templates"],
        "answer_status": "verified",
        "description": "Формула ответа восстановлена и проверена на исходных и новых числах.",
    }
    archive_module = {
        "module_id": ARCHIVE_MODULE_ID,
        "display_name": "Архив подготовленных шаблонов",
        "title": "Очищенные задания из общего корпуса",
        "template_count": archive_stats["unverified_templates"],
        "answer_status": "unverified",
        "description": "Тексты готовы, но формулы ответов для них ещё не восстановлены.",
    }
    return {
        "modules": modules + [recovered_archive_module, archive_module],
        "templates": templates,
        "stats": {
            "total_modules": len(modules),
            "total_templates": len(templates),
            "verified_answer_templates": len(templates),
            "archive_templates": archive_stats["recovered_templates"] + archive_stats["unverified_templates"],
            "recovered_archive_templates": archive_stats["recovered_templates"],
            "unverified_archive_templates": archive_stats["unverified_templates"],
            "catalog_templates": len(templates) + archive_stats["recovered_templates"] + archive_stats["unverified_templates"],
            "covered_source_problem_numbers": (
                int(arithmetic.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(equations.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(systems.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(comparisons.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(sequences.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(intervals.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(divisibility.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(digits.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(ratios.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(factors.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(combinatorics.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(pigeonhole.get("stats", {}).get("covered_source_problem_numbers", 0))
                + int(parity.get("stats", {}).get("covered_source_problem_numbers", 0))
            ),
        },
        "limits": {"min_task_count": MIN_TASK_COUNT, "max_task_count": MAX_TASK_COUNT, "default_task_count": 5},
    }


def _answer_to_text(answer: Any) -> str:
    if isinstance(answer, dict):
        if set(answer) == {"x", "y"}:
            return f"X = {answer['x']}, Y = {answer['y']}"
        return "; ".join(f"{key}: {value}" for key, value in answer.items())
    if isinstance(answer, list):
        return ", ".join(str(item) for item in answer)
    return str(answer)


def _generate_archive_problem(rng: random.Random) -> dict[str, Any]:
    template = rng.choice(unverified_templates())
    generated = generate_problem_instance(template, rng, require_changed=False)
    return {
        "module_id": ARCHIVE_MODULE_ID,
        "template_id": generated["template_id"],
        "source_problem_numbers": [generated["template_number"]],
        "rendered_problem": generated["rendered_problem"],
        "answer": "Ответ для архивного шаблона ещё не восстановлен.",
        "answer_value": None,
        "generated_values": generated["generated_values"],
        "answer_status": "unverified",
    }


def _generate_recovered_archive_problem(rng: random.Random) -> dict[str, Any]:
    template = rng.choice(recovered_templates())
    generated = generate_problem_instance(template, rng)
    answer = generated["answer"]
    return {
        "module_id": RECOVERED_ARCHIVE_MODULE_ID,
        "template_id": generated["template_id"],
        "source_problem_numbers": [generated["template_number"]],
        "rendered_problem": generated["rendered_problem"],
        "answer": _answer_to_text(answer),
        "answer_value": answer,
        "generated_values": generated["generated_values"],
        "answer_status": "verified",
    }


def generate_combined_worksheet_by_modules(
    module_ids: list[str], seed: int | None = None, *, task_count: int | None = None,
) -> dict[str, Any]:
    count = _validate_task_count(task_count if task_count is not None else len(module_ids))
    if len(module_ids) != count:
        raise ValueError("Число выбранных модулей должно совпадать с количеством задач.")
    rng = random.Random(seed)
    arithmetic_templates = load_arithmetic_templates()
    selected: list[dict[str, Any]] = []
    for position, module_id in enumerate(module_ids, start=1):
        if module_id == "arithmetic":
            template = rng.choice(arithmetic_templates)
            generated = generate_arithmetic_problem(str(template["id"]), rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "arithmetic",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "equations":
            generated = generate_equation_problem_from_module("equations", rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "equations",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "systems_of_equations":
            generated = generate_system_equation_problem_from_module("systems_of_equations", rng=rng)
            answer = generated.answer
            selected.append({
                "position": position,
                "module_id": "systems_of_equations",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": _answer_to_text(answer),
                "answer_value": answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "comparison_of_numbers_and_expressions":
            generated = generate_comparison_problem_from_module("comparison_of_numbers_and_expressions", rng=rng)
            selected.append({
                "position": position,
                "module_id": "comparison_of_numbers_and_expressions",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": generated.answer_text,
                "answer_value": generated.answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "sequences_progressions_and_sums":
            generated = generate_sequence_problem_from_module("sequences_progressions_and_sums", rng=rng)
            selected.append({
                "position": position,
                "module_id": "sequences_progressions_and_sums",
                "template_id": generated.template_id,
                "source_problem_numbers": generated.source_problem_numbers,
                "rendered_problem": generated.problem_text,
                "answer": generated.answer_text,
                "answer_value": generated.answer,
                "generated_values": generated.parameters,
            })
            continue
        if module_id == "integer_interval_counting":
            generated = generate_integer_interval_problem_from_module("integer_interval_counting", rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "divisibility_multiples_remainders_primes":
            generated = generate_divisibility_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "digits_number_notation_and_cryptarithms":
            generated = generate_digits_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "ratios_fractions_proportions_and_percentages":
            generated = generate_ratio_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "factors_products_and_factorials":
            generated = generate_factor_product_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "combinatorics_and_counting_variants":
            generated = generate_combinatorics_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "pigeonhole_and_guaranteed_selection":
            generated = generate_pigeonhole_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == "parity_invariants_strategies_and_moves":
            generated = generate_parity_problem_from_module(module_id, rng=rng)
            selected.append({"position": position, "module_id": module_id, "template_id": generated.template_id, "source_problem_numbers": generated.source_problem_numbers, "rendered_problem": generated.problem_text, "answer": generated.answer_text, "answer_value": generated.answer, "generated_values": generated.parameters})
            continue
        if module_id == ARCHIVE_MODULE_ID:
            archive_problem = _generate_archive_problem(rng)
            archive_problem["position"] = position
            selected.append(archive_problem)
            continue
        if module_id == RECOVERED_ARCHIVE_MODULE_ID:
            archive_problem = _generate_recovered_archive_problem(rng)
            archive_problem["position"] = position
            selected.append(archive_problem)
            continue
        raise ValueError(f"Неизвестный модуль: {module_id}")
    return {
        "schema_version": 1,
        "mode": "modules",
        "selected_modules": module_ids,
        "selected_templates": selected,
        "seed": seed,
        "date": datetime.now().strftime("%d.%m.%Y"),
    }


def generate_random_worksheet(task_count: int = 5, seed: int | None = None) -> dict[str, Any]:
    """Generate a ready-to-print worksheet from modules with verified answers only."""
    count = _validate_task_count(task_count)
    rng = random.Random(seed)
    module_ids = [rng.choice(VERIFIED_MODULE_IDS) for _ in range(count)]
    worksheet = generate_combined_worksheet_by_modules(module_ids, seed=seed, task_count=count)
    worksheet["mode"] = "random_verified_modules"
    return worksheet


def _read_static_file(name: str) -> bytes:
    return (FRONTEND_ROOT / name).read_bytes()


def render_site_page() -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Генератор математических задач</title>
  <link rel="stylesheet" href="/static/worksheet_site.css">
</head>
<body>
  <main class="app-shell">
    <header class="site-nav no-print">
      <a class="site-brand" href="/" aria-label="Поступление в 239">
        <img src="/assets/logo_239.png" alt="Поступление в 239">
        <span><strong>Поступление в 239</strong><small>математика с увлечением</small></span>
      </a>
      <nav aria-label="Разделы генератора">
        <a href="#builder">Варианты</a>
        <a href="#worksheet-sheet">Предпросмотр</a>
      </nav>
      <span class="nav-badge">5 задач · с ответами</span>
    </header>
    <section class="hero no-print">
      <p class="eyebrow">подготовка к математике</p>
      <h1><span>Задачи,</span> которые<br>открывают возможности</h1>
      <p>Готовые варианты для печати: автоматический подбор задач, новые числа и отдельная колонка с ответами для преподавателя.</p>
      <ul class="hero-features">
        <li>Понятные задания</li>
        <li>Олимпиадный подход</li>
        <li>Результат и уверенность</li>
      </ul>
    </section>

    <section class="builder no-print" id="builder">
      <div class="panel">
        <div class="panel-heading">
          <div>
            <h2>Вариант для печати</h2>
            <p id="catalog-summary">Загрузка каталога...</p>
          </div>
          <button id="clear-button" type="button" class="button-secondary">Очистить выбор</button>
        </div>
        <div class="quick-start">
          <div>
            <label for="task-count">Количество задач</label>
            <input id="task-count" type="number" min="1" max="20" value="5" inputmode="numeric">
          </div>
          <button id="quick-generate-button" type="button" class="button-primary" disabled>Сделать готовый вариант</button>
          <p>Автоматически выбираются только модули с вычисляемыми ответами.</p>
        </div>
        <details class="manual-builder">
          <summary>Настроить модули вручную</summary>
          <p>Для каждого номера можно выбрать модуль. В архиве отдельно выделены задания с уже восстановленными формулами; неразобранные тексты не добавляются в быстрый вариант.</p>
          <div id="selector-grid" class="selector-grid"></div>
        </details>
        <div class="actions">
          <button id="generate-button" type="button" disabled>Сгенерировать вариант</button>
          <button id="regenerate-button" type="button" class="button-secondary" disabled>Сгенерировать новые числа</button>
          <button id="print-button" type="button" class="button-secondary" disabled>Печать</button>
          <button id="print-answers-button" type="button" class="button-secondary" disabled>Печатать с ответами</button>
        </div>
        <p id="error-state" class="error" hidden></p>
      </div>
    </section>

    <section class="worksheet-sheet" id="worksheet-sheet" aria-label="Предпросмотр листа">
      <div class="worksheet-main">
        <header class="sheet-header">
          <div class="name-fields">
            <p>Фамилия: ______________________</p>
            <p>Имя: __________________________</p>
            <p>Дата: <span id="sheet-date"></span></p>
          </div>
          <div class="sheet-assets" aria-label="Логотип и QR-код">
            <img class="sheet-logo" src="/assets/logo_239.png" alt="Поступление в 239">
            <img src="/assets/qr.png" alt="QR-код Telegram-канала «Поступление в 239»">
          </div>
        </header>
        <hr>
        <ol id="worksheet-problems" class="problems-list">
          <li class="empty-problem">После генерации здесь появятся задачи.</li>
        </ol>
      </div>
      <aside class="print-answer-strip" aria-label="Отрезаемая колонка ответов">
        <img class="print-logo" src="/assets/logo_239.png" alt="Поступление в 239">
        <img class="print-qr" src="/assets/qr.png" alt="QR-код Telegram-канала «Поступление в 239»">
        <p class="cut-label">✂ Отрезать по пунктиру</p>
        <h2>Ответы</h2>
        <ol id="print-answers-list"></ol>
      </aside>
    </section>

    <section class="answer-key no-print" id="answer-key" hidden>
      <div class="panel">
        <div class="panel-heading">
          <h2>Ответы</h2>
          <button id="toggle-answers-button" type="button" class="button-secondary">Скрыть ответы</button>
        </div>
        <ol id="answers-list"></ol>
      </div>
    </section>

    <section class="no-print">
      <button id="show-answers-button" type="button" class="button-secondary" disabled>Показать ответы</button>
    </section>
  </main>
  <script src="/static/worksheet_site.js"></script>
</body>
</html>
"""


class WorksheetSiteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._respond_text(render_site_page(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/templates":
            self._respond_json(_combined_template_metadata())
            return
        if parsed.path == "/static/worksheet_site.css":
            self._respond_bytes(_read_static_file("worksheet_site.css"), "text/css; charset=utf-8")
            return
        if parsed.path == "/static/worksheet_site.js":
            self._respond_bytes(_read_static_file("worksheet_site.js"), "application/javascript; charset=utf-8")
            return
        if parsed.path in {"/assets/logo.png", "/assets/logo_239.png", "/assets/qr.png"}:
            asset_name = Path(parsed.path).name
            self._respond_bytes((ASSETS_ROOT / asset_name).read_bytes(), "image/png")
            return
        if parsed.path.startswith("/assets/fonts/"):
            requested_path = (ASSETS_ROOT / "fonts" / Path(parsed.path).name).resolve()
            fonts_root = (ASSETS_ROOT / "fonts").resolve()
            if fonts_root not in requested_path.parents or not requested_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Шрифт не найден")
                return
            self._respond_bytes(requested_path.read_bytes(), "font/ttf")
            return
        if parsed.path.startswith("/download/"):
            self._handle_download(parsed.path.removeprefix("/download/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/generate":
            self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(content_length)
            data = json.loads(payload.decode("utf-8"))
            seed = data.get("seed")
            if seed is not None and not isinstance(seed, int):
                seed = None
            count = data.get("count", 5)
            _validate_task_count(count)
            if data.get("mode") == "random":
                worksheet = generate_random_worksheet(count, seed=seed)
                self._respond_json({"ok": True, "worksheet": worksheet})
                return
            module_ids = data.get("module_ids")
            if isinstance(module_ids, list) and all(isinstance(item, str) for item in module_ids):
                worksheet = generate_combined_worksheet_by_modules(module_ids, seed=seed, task_count=count)
                self._respond_json({"ok": True, "worksheet": worksheet})
                return
            template_ids = data.get("template_ids")
            if not isinstance(template_ids, list) or not all(isinstance(item, str) for item in template_ids):
                raise ValueError("Выберите модули для всех задач или используйте быстрый вариант.")
            worksheet = generate_arithmetic_worksheet(template_ids, seed=seed)
        except Exception as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return
        self._respond_json({"ok": True, "worksheet": worksheet})

    def _handle_download(self, filename: str) -> None:
        safe_name = Path(filename).name
        requested_path = (OUTPUT_ROOT / safe_name).resolve()
        if OUTPUT_ROOT.resolve() not in requested_path.parents:
            self.send_error(HTTPStatus.FORBIDDEN, "Можно скачивать только файлы из outputs/generated")
            return
        if not requested_path.exists() or not requested_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Файл не найден")
            return
        content_type = mimetypes.guess_type(str(requested_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(requested_path.stat().st_size))
        self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.end_headers()
        self.wfile.write(requested_path.read_bytes())

    def _respond_text(self, text: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond_bytes(text.encode("utf-8"), content_type, status=status)

    def _respond_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond_text(json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8", status=status)

    def _respond_bytes(self, payload: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[worksheet-web] {self.address_string()} - {html.escape(format % args)}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def create_http_server(host: str, port: int, max_port_tries: int = 20) -> tuple[ReusableThreadingHTTPServer, int]:
    last_error: OSError | None = None
    for current_port in range(port, port + max_port_tries):
        try:
            server = ReusableThreadingHTTPServer((host, current_port), WorksheetSiteHandler)
            return server, current_port
        except OSError as error:
            last_error = error
            if error.errno not in (48, 10048):
                raise
    raise OSError(48, f"Не удалось найти свободный порт в диапазоне {port}-{port + max_port_tries - 1}") from last_error


def run_server(host: str = "127.0.0.1", port: int = 8090) -> None:
    server, actual_port = create_http_server(host, port)
    if actual_port != port:
        print(f"Порт {port} занят, выбран свободный порт {actual_port}.")
    print(f"Worksheet site: http://{host}:{actual_port}")
    print("Остановить сервер: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()
