from __future__ import annotations

import html
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from problemgen.worksheet.all_tasks_site import catalog_metadata, generate_five_problem_worksheet


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "generated"


def _read_static_file(name: str) -> bytes:
    return (FRONTEND_ROOT / name).read_bytes()


def render_site_page() -> str:
    selectors = "\n".join(
        f"""
        <article class="selector-card">
          <div class="selector-card__header">
            <span>{index}</span>
            <div>
              <h3>Задача {index}</h3>
              <p>Выберите шаблон по русскому названию.</p>
            </div>
          </div>
          <label for="template-search-{index}">Поиск шаблона</label>
          <input id="template-search-{index}" class="template-search" data-template-search="{index}" type="search" placeholder="Название, модуль или номер">
          <label for="template-select-{index}">Выберите шаблон</label>
          <select id="template-select-{index}" data-template-select="{index}">
            <option value="">Ничего не выбрано</option>
          </select>
          <p class="selector-status" data-selector-status="{index}">Шаблон не выбран.</p>
        </article>
        """
        for index in range(1, 6)
    )
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
    <section class="hero no-print">
      <p class="eyebrow">all_tasks_templates.json</p>
      <h1>Генератор математических задач</h1>
      <p>Выберите пять шаблонов. Сайт сгенерирует печатный лист A4, не меняя исходный каталог шаблонов.</p>
    </section>

    <section class="builder no-print">
      <div class="panel">
        <div class="panel-heading">
          <div>
            <h2>Выберите пять шаблонов</h2>
            <p id="catalog-summary">Загрузка каталога...</p>
          </div>
          <button id="clear-button" type="button" class="button-secondary">Очистить выбор</button>
        </div>
        <label class="repeat-toggle">
          <input id="allow-repeats" type="checkbox">
          Разрешить повторение шаблонов
        </label>
        <div class="selector-grid">
          {selectors}
        </div>
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
      <header class="sheet-header">
        <div class="name-fields">
          <p>Фамилия ____________________</p>
          <p>Имя ________________________</p>
        </div>
        <p class="sheet-date">Дата: <span id="sheet-date"></span></p>
      </header>
      <hr>
      <ol id="worksheet-problems" class="problems-list">
        <li class="empty-problem">После генерации здесь появится первая задача.</li>
        <li class="empty-problem">После генерации здесь появится вторая задача.</li>
        <li class="empty-problem">После генерации здесь появится третья задача.</li>
        <li class="empty-problem">После генерации здесь появится четвертая задача.</li>
        <li class="empty-problem">После генерации здесь появится пятая задача.</li>
      </ol>
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
            self._respond_json(catalog_metadata())
            return
        if parsed.path == "/static/worksheet_site.css":
            self._respond_bytes(_read_static_file("worksheet_site.css"), "text/css; charset=utf-8")
            return
        if parsed.path == "/static/worksheet_site.js":
            self._respond_bytes(_read_static_file("worksheet_site.js"), "application/javascript; charset=utf-8")
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
            template_ids = data.get("template_ids")
            if not isinstance(template_ids, list) or not all(isinstance(item, str) for item in template_ids):
                raise ValueError("Выберите пять шаблонов.")
            seed = data.get("seed")
            if seed is not None and not isinstance(seed, int):
                seed = None
            worksheet = generate_five_problem_worksheet(template_ids, seed=seed)
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
