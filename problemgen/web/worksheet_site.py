from __future__ import annotations

import html
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from problemgen.worksheet import generate_worksheet_artifacts


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
OUTPUT_ROOT = Path(__file__).resolve().parents[2] / "outputs" / "generated"


def _read_static_file(name: str) -> bytes:
    return (FRONTEND_ROOT / name).read_bytes()


def render_site_page() -> str:
    options = "".join(f'<option value="{value}">{value}</option>' for value in range(1, 11))
    selectors = "\n".join(
        f"""
        <div class="worksheet-field">
          <label for="difficulty-{index}">Задача {index}</label>
          <select id="difficulty-{index}" data-difficulty-index="{index}">
            {options}
          </select>
        </div>
        """
        for index in range(1, 6)
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Worksheet Generator</title>
  <link rel="stylesheet" href="/static/worksheet_site.css">
</head>
<body>
  <main class="worksheet-page">
    <section class="worksheet-hero">
      <p class="worksheet-eyebrow">Local Worksheet Builder</p>
      <h1>Лист с 5 задачами по выбранной сложности</h1>
      <p>Выбери уровень от 1 до 10 для каждой задачи, затем сайт сгенерирует готовый ученический лист с датой, логотипом и QR-кодом.</p>
    </section>

    <section class="worksheet-shell">
      <div class="worksheet-panel">
        <h2>Сложность задач</h2>
        <div class="worksheet-grid">
          {selectors}
        </div>
        <button id="generate-button" type="button">Создать лист</button>
        <p id="loading-state" class="worksheet-loading" hidden>Генерация листа...</p>
        <p id="error-state" class="worksheet-error" hidden></p>
      </div>

      <div class="worksheet-panel worksheet-result">
        <h2>Результат</h2>
        <p>После генерации здесь появится ссылка на готовый PDF и пути к JSON-файлам с задачами и ответами.</p>
        <div id="result-state" hidden>
          <a id="download-link" class="worksheet-download" href="#" download>Скачать PDF</a>
          <p id="answers-path" class="worksheet-note"></p>
          <p id="problems-path" class="worksheet-note"></p>
        </div>
      </div>
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
            artifact = generate_worksheet_artifacts(data.get("difficulties"))
        except Exception as error:
            self._respond_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        filename = Path(artifact.pdf_path).name
        self._respond_json(
            {
                "ok": True,
                "filename": filename,
                "download_url": f"/download/{filename}",
                "pdf_path": artifact.pdf_path,
                "answers_path": artifact.answers_json_path,
                "problems_path": artifact.student_json_path,
                "created_at": artifact.created_at,
            }
        )

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
            if error.errno != 48:
                raise
    raise OSError(
        48,
        f"Не удалось найти свободный порт в диапазоне {port}-{port + max_port_tries - 1}",
    ) from last_error


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
