from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, quote, urlparse

from problemgen.app import build_domain_catalog, generate_problem_bundle
from problemgen.core.difficulty import DIFFICULTY_LEVELS


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"


def _read_static_file(name: str) -> bytes:
    return (FRONTEND_ROOT / name).read_bytes()


def _template_catalog() -> Dict[str, Any]:
    catalog = build_domain_catalog()
    return {
        "domains": {
            code: {
                "label": domain.label,
                "description": domain.description,
                "templates": [
                    {"code": template.code, "label": template.label, "description": template.description}
                    for template in domain.list_templates()
                ],
                "themes": domain.available_themes(),
            }
            for code, domain in catalog.items()
        },
        "difficulties": {
            code: {
                "label": level.label,
                "description": level.description,
            }
            for code, level in DIFFICULTY_LEVELS.items()
        },
    }


def render_problem_cards(problems: list[dict]) -> str:
    cards = []
    for index, problem in enumerate(problems, start=1):
        issues = problem.get("metadata", {}).get("language_issues", [])
        issue_html = ""
        if issues:
            items = "".join(
                f"<li>{html.escape(issue['field'])}: {html.escape(issue['message'])}</li>"
                for issue in issues
            )
            issue_html = f"<div class='issues'><strong>Проверка русского</strong><ul>{items}</ul></div>"

        relations = "".join(f"<li>{html.escape(item)}</li>" for item in problem.get("relations", []))
        cards.append(
            f"""
            <article class="problem-card">
              <div class="problem-card__head">
                <div>
                  <p class="eyebrow">Задача {index}</p>
                  <h3>{html.escape(problem["code"])}</h3>
                </div>
                <span class="badge">{html.escape(problem.get("category", ""))}</span>
              </div>
              <p class="problem-card__meta">{html.escape(problem.get("template_name", ""))}</p>
              <p class="problem-text">{html.escape(problem["problem_text"])}</p>
              <p class="answer"><span>Ответ:</span> {html.escape(problem["answer_text"])}</p>
              {issue_html}
              <details>
                <summary>Метаданные</summary>
                <pre>{html.escape(json.dumps(problem, ensure_ascii=False, indent=2))}</pre>
              </details>
              <ul class="relations">{relations}</ul>
            </article>
            """
        )
    return "\n".join(cards)


def render_page(form_values: Dict[str, str], result: Optional[Dict[str, Any]], error_message: Optional[str]) -> str:
    catalog_json = json.dumps(_template_catalog(), ensure_ascii=False)
    domains = build_domain_catalog()

    domain_options = []
    for code, domain in domains.items():
        selected = " selected" if form_values.get("domain") == code else ""
        domain_options.append(f'<option value="{html.escape(code)}"{selected}>{html.escape(domain.label)}</option>')

    difficulty_options = []
    for code, level in DIFFICULTY_LEVELS.items():
        selected = " selected" if form_values.get("difficulty_level") == code else ""
        difficulty_options.append(f'<option value="{html.escape(code)}"{selected}>{html.escape(level.label)}</option>')

    seed_mode_options = []
    for code, label in (("today", "По сегодняшней дате"), ("random", "Случайный"), ("fixed", "Фиксированный")):
        selected = " selected" if form_values.get("seed_mode") == code else ""
        seed_mode_options.append(f'<option value="{code}"{selected}>{label}</option>')

    mode_options = []
    for code, label in (("all", "Все"), ("line", "Прямая"), ("plane", "Плоскость")):
        selected = " selected" if form_values.get("mode") == code else ""
        mode_options.append(f'<option value="{code}"{selected}>{label}</option>')

    result_html = """
      <section class="panel result-panel empty-state">
        <p class="eyebrow">Результат</p>
        <h2>Пока пусто</h2>
        <p>Выберите блок задач, тему, сложность и нажмите «Сгенерировать».</p>
      </section>
    """
    if result:
        download_link = f"/download?path={quote(result['output_path'])}"
        result_html = f"""
        <section class="panel result-panel">
          <div class="result-panel__head">
            <div>
              <p class="eyebrow">Результат</p>
              <h2>{html.escape(result["count_text"])}</h2>
            </div>
            <a class="download-link" href="{download_link}">Скачать JSON</a>
          </div>
          <div class="meta-strip">
            <span>{html.escape(result["domain_label"])}</span>
            <span>{html.escape(result["difficulty_label"])}</span>
            <span>{html.escape(result["requested_story_theme_label"])}</span>
            <span>seed: {html.escape(str(result["seed_value"]))}</span>
          </div>
          <p class="output-path">{html.escape(result["difficulty_description"])}</p>
          <p class="output-path">Файл: <code>{html.escape(result["output_path"])}</code></p>
          <div class="problem-list">
            {render_problem_cards(result["problems"])}
          </div>
        </section>
        """

    error_html = ""
    if error_message:
        error_html = f'<section class="panel error-panel">{html.escape(error_message)}</section>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Problem Generator</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero__copy">
        <p class="eyebrow">Local Math Lab</p>
        <h1>Генератор задач с доменами, русским языком и сюжетами</h1>
        <p>Один сервер, несколько блоков задач, единая проверка русского языка и экспорт каждого набора в JSON.</p>
      </div>
      <div class="hero__badge">LaTeX-like UI</div>
    </section>
    {error_html}
    <section class="layout">
      <form class="panel controls" method="get" action="/">
        <input type="hidden" name="generate" value="1">
        <p class="eyebrow">Параметры</p>
        <h2>Новый набор</h2>
        <div class="field">
          <label for="domain">Блок задач</label>
          <select id="domain" name="domain">
            {"".join(domain_options)}
          </select>
        </div>
        <div class="field">
          <label for="template_name">Шаблон</label>
          <select id="template_name" name="template_name"></select>
        </div>
        <div class="field">
          <label for="count">Количество задач</label>
          <input id="count" name="count" type="number" min="1" max="300" value="{html.escape(form_values['count'])}">
        </div>
        <div class="field">
          <label for="difficulty_level">Сложность</label>
          <select id="difficulty_level" name="difficulty_level">
            {"".join(difficulty_options)}
          </select>
        </div>
        <div class="field">
          <label for="story_theme">Тема</label>
          <select id="story_theme" name="story_theme"></select>
        </div>
        <div class="field">
          <label for="story_world">Сюжетный мир</label>
          <input id="story_world" name="story_world" type="text" value="{html.escape(form_values['story_world'])}" placeholder="any или ключ мира">
        </div>
        <div class="field">
          <label for="mode">Режим для отрезков</label>
          <select id="mode" name="mode">
            {"".join(mode_options)}
          </select>
          <p class="hint">Поле имеет смысл только для блока «Отрезки».</p>
        </div>
        <div class="field">
          <label for="seed_mode">Случайность</label>
          <select id="seed_mode" name="seed_mode">
            {"".join(seed_mode_options)}
          </select>
        </div>
        <div class="field">
          <label for="seed">Seed</label>
          <input id="seed" name="seed" type="number" value="{html.escape(form_values['seed'])}" placeholder="Только для fixed">
        </div>
        <button type="submit">Сгенерировать</button>
      </form>
      {result_html}
    </section>
  </main>
  <script>
    window.PROBLEMGEN_CONFIG = {catalog_json};
    window.PROBLEMGEN_FORM = {json.dumps(form_values, ensure_ascii=False)};
  </script>
  <script src="/static/app.js"></script>
</body>
</html>
"""


class ProblemWebHandler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond_bytes(b"", "text/html; charset=utf-8")
            return
        if parsed.path == "/download":
            self.respond_bytes(b"", "application/json; charset=utf-8")
            return
        if parsed.path == "/static/styles.css":
            self.respond_bytes(b"", "text/css; charset=utf-8")
            return
        if parsed.path == "/static/app.js":
            self.respond_bytes(b"", "application/javascript; charset=utf-8")
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.handle_index(parsed)
            return
        if parsed.path == "/download":
            self.handle_download(parsed)
            return
        if parsed.path == "/static/styles.css":
            self.respond_bytes(_read_static_file("styles.css"), "text/css; charset=utf-8")
            return
        if parsed.path == "/static/app.js":
            self.respond_bytes(_read_static_file("app.js"), "application/javascript; charset=utf-8")
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def handle_index(self, parsed_url) -> None:
        query = parse_qs(parsed_url.query)
        form_values = {
            "domain": query.get("domain", ["segments"])[0],
            "count": query.get("count", ["5"])[0],
            "template_name": query.get("template_name", ["any"])[0],
            "difficulty_level": query.get("difficulty_level", ["medium"])[0],
            "story_theme": query.get("story_theme", ["any"])[0],
            "story_world": query.get("story_world", ["any"])[0],
            "seed_mode": query.get("seed_mode", ["today"])[0],
            "seed": query.get("seed", [""])[0],
            "mode": query.get("mode", ["all"])[0],
        }

        result = None
        error_message = None

        if query.get("generate", ["0"])[0] == "1":
            try:
                seed_raw = form_values["seed"].strip()
                seed = int(seed_raw) if seed_raw else None
                result = generate_problem_bundle(
                    domain_code=form_values["domain"],
                    count=int(form_values["count"]),
                    template_name=form_values["template_name"],
                    difficulty_level=form_values["difficulty_level"],
                    story_theme=form_values["story_theme"],
                    story_world=form_values["story_world"],
                    seed_mode=form_values["seed_mode"],
                    seed=seed,
                    output_path=None,
                    options={"mode": form_values["mode"]},
                )
            except Exception as error:
                error_message = str(error)

        page = render_page(form_values, result, error_message)
        self.respond_bytes(page.encode("utf-8"), "text/html; charset=utf-8")

    def handle_download(self, parsed_url) -> None:
        query = parse_qs(parsed_url.query)
        raw_path = query.get("path", [""])[0]
        if not raw_path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Не указан путь к файлу")
            return

        output_root = (Path.cwd() / "outputs").resolve()
        requested_path = Path(raw_path)
        if not requested_path.is_absolute():
            requested_path = (Path.cwd() / requested_path).resolve()
        else:
            requested_path = requested_path.resolve()

        if output_root not in requested_path.parents:
            self.send_error(HTTPStatus.FORBIDDEN, "Можно скачивать только файлы из outputs")
            return
        if not requested_path.exists() or not requested_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Файл не найден")
            return

        self.respond_bytes(requested_path.read_bytes(), "application/json; charset=utf-8")

    def respond_bytes(self, payload: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {format % args}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def create_http_server(host: str, port: int, max_port_tries: int = 20) -> tuple[ReusableThreadingHTTPServer, int]:
    last_error: Optional[OSError] = None
    for current_port in range(port, port + max_port_tries):
        try:
            server = ReusableThreadingHTTPServer((host, current_port), ProblemWebHandler)
            return server, current_port
        except OSError as error:
            last_error = error
            if error.errno != 48:
                raise
    raise OSError(
        48,
        f"Не удалось найти свободный порт в диапазоне {port}-{port + max_port_tries - 1}",
    ) from last_error


def run_server(host: str, port: int) -> None:
    server, actual_port = create_http_server(host, port)
    if actual_port != port:
        print(f"Порт {port} занят, выбран свободный порт {actual_port}.")
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"Сайт запущен: http://{display_host}:{actual_port}")
    print("Остановить сервер: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()
