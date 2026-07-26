"""Локальный конвейер: очередь задач -> Ollama -> валидатор -> staging.

Модель пишет только в data/template_studio/incoming/. Активировать шаблон
(seed_worksheet_templates.py) может только человек после проверки — иначе
неверная задача уйдёт в пятиминутку детям.

Цикл на каждую задачу:
    промпт -> Ollama (structured output по JSON Schema) -> валидатор Template Studio
    -> при ошибке текст ошибки возвращается модели -> до --retries попыток.

Результат:
    incoming/<id>.json    прошло валидатор, ждёт проверки человеком
    needs_data/<id>.json  модель сообщила, что не хватает слова или персонажа
    rejected/<id>.json    не прошло за все попытки, внутри — трасса ошибок
    runs/<timestamp>.json отчёт прогона: попытки, время, исходы

Запуск:
    python3 scripts/agent_loop.py --queue data/template_studio/queue/pilot.json
    python3 scripts/agent_loop.py --queue ... --model qwen3:14b --retries 5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.catalogue import catalogue_module_ids  # noqa: E402
from problemgen.template_studio.service import TemplateStudioService  # noqa: E402
from problemgen.template_studio.storage import TemplateStudioStore  # noqa: E402

STUDIO_ROOT = PROJECT_ROOT / "data" / "template_studio"
SCHEMA_PATH = STUDIO_ROOT / "schema" / "template.schema.json"
PROMPT_PATH = PROJECT_ROOT / "Docs" / "LOCAL_AGENT_PROMPT.md"
LIBRARY_ROOT = STUDIO_ROOT / "library"
NOUNS_PATH = PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json"
OLLAMA_URL = "http://localhost:11434/api/chat"

# Эталоны, которые уходят в промпт как few-shot. Короткие и разной формы:
# один с целочисленным ответом, один с multi_part.
EXAMPLE_IDS = ("joint_work_rate_sum", "process_states_merge_countdown")
NON_EDITABLE_KEYS = {"schema_version", "template_id", "math_notes"}


def load_nouns() -> list[str]:
    payload = json.loads(NOUNS_PATH.read_text(encoding="utf-8"))
    return sorted(payload["nouns"])


def build_system_prompt() -> str:
    rules = PROMPT_PATH.read_text(encoding="utf-8")
    nouns = ", ".join(load_nouns())
    modules = ", ".join(sorted(catalogue_module_ids()))
    examples = []
    for template_id in EXAMPLE_IDS:
        path = LIBRARY_ROOT / f"{template_id}.json"
        if path.is_file():
            examples.append(path.read_text(encoding="utf-8").strip())
    return (
        f"{rules}\n\n"
        f"## Доступные module_id\n\n{modules}\n\n"
        f"## Доступные существительные (только эти слова!)\n\n{nouns}\n\n"
        f"## Эталонные шаблоны\n\n" + "\n\n".join(examples)
    )


def build_user_prompt(task: dict[str, Any]) -> str:
    sources = "\n".join(f"{number}. {text}" for number, text in task["problems"].items())
    return (
        f"Исходные задачи (это варианты одной и той же задачи с разными числами):\n\n{sources}\n\n"
        f"Сделай один шаблон, покрывающий их все.\n"
        f"template_id: {task['template_id']}\n"
        f"module_id: {task['module_id']}\n"
    )


def call_ollama(model: str, system: str, messages: list[dict[str, str]], schema: dict[str, Any],
                timeout: int, temperature: float = 0.2) -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "format": schema,
        "stream": False,
        "think": False,
        "options": {"temperature": temperature, "num_ctx": 16384},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["message"]["content"], time.monotonic() - started


def validate_candidate(service: TemplateStudioService, candidate: dict[str, Any],
                       known_modules: set[str]) -> dict[str, Any]:
    """Прогнать кандидата через валидатор Studio, ничего не публикуя."""
    draft = service.create_from_analysis({
        "original_text": candidate.get("candidate_template_text") or "заглушка",
        "template_id": candidate["template_id"],
        "module_id": candidate.get("module_id"),
    })
    try:
        changes = {key: value for key, value in candidate.items() if key not in NON_EDITABLE_KEYS}
        service.update_draft(draft["draft_id"], changes)
        return service.validate(
            draft["draft_id"], known_module_ids=known_modules, existing_template_ids=set()
        )
    finally:
        # После validate черновик уже не в статусе draft, и delete_draft его не берёт.
        # Для нас это временный объект: чистим по возможности, но не роняем прогон.
        try:
            service.delete_draft(draft["draft_id"], confirmed=True)
        except Exception:
            service.store.delete_draft_file(draft["draft_id"])


def failure_text(report: dict[str, Any]) -> str:
    failed = [check for check in report.get("checks", []) if not check.get("passed")]
    if not failed:
        return "неизвестная ошибка валидации"
    return "; ".join(f"{check['label']}: {check['message']}" for check in failed)


# Сообщение валидатора -> конкретное указание, что переписать. Без этого модель
# на 8B повторяет тот же текст: общую формулировку ошибки она не переводит в правку.
HINTS: tuple[tuple[str, str], ...] = (
    ("Не определены плейсхолдеры",
     "В тексте есть слот, которого нет в parameter_schema и derived_values. "
     "Убери лишний слот или заведи параметр. Чаще всего лишний слот — это 'n' "
     "в конструкции вида {x:count,n}."),
    ("требует параметр типа noun",
     "Слот count/agree можно ставить ТОЛЬКО у существительного из списка слов, "
     "и второй аргумент — имя уже объявленного числового параметра. "
     "Для порядкового числительного пиши просто 'каждый {freq}-й день' без count."),
    ("вселенной", "Убери поле 'universe' из всех параметров типа character."),
    ("только для параметра типа location",
     "Слоты loc и dir допустимы только у параметра типа location."),
    ("мн. ч.", "Формы множественного числа доступны только у параметра типа noun."),
    ("Неизвестная операция", "Допустимы только операции count, agree, g, with, loc, dir."),
    ("Неизвестный падеж", "Допустимы падежи nom, gen, dat, acc, ins, pre и мн. ч. у noun."),
    ("не используется", "Каждый объявленный параметр обязан встречаться в тексте или в формулах."),
    ("деление на ноль", "Добавь constraint, запрещающий нулевой делитель."),
    ("Ответ не соответствует типу", "Приведи answer_type в соответствие с тем, что реально считает формула."),
    ("не удалось подобрать", "Ослабь границы параметров или убери взаимоисключающие constraints."),
)


def hints_for(problem: str, candidate: dict[str, Any] | None = None) -> str:
    matched = [hint for marker, hint in HINTS if marker in problem]
    if candidate:
        matched += broken_count_slots(candidate)
    return "\n".join(f"- {hint}" for hint in dict.fromkeys(matched))


def broken_count_slots(candidate: dict[str, Any]) -> list[str]:
    """Процитировать конкретные сломанные слоты count/agree.

    Самая устойчивая ошибка модели: `{число:count,...}` вместо
    `{существительное:count,число}`. Общая формулировка ошибки её не исправляет —
    нужен точный фрагмент из её же текста.
    """
    import re as _re

    text = str(candidate.get("candidate_template_text", ""))
    schema = candidate.get("parameter_schema", {})
    if not isinstance(schema, dict):
        return []
    problems: list[str] = []
    for key, operation, argument in _re.findall(
        r"\{\s*([A-Za-z_]\w*)\s*:\s*(count|agree)\s*,\s*([A-Za-z_]\w*)\s*\}", text
    ):
        rule = schema.get(key) if isinstance(schema.get(key), dict) else {}
        if rule.get("type") != "noun":
            nouns = sorted(name for name, spec in schema.items()
                           if isinstance(spec, dict) and spec.get("type") == "noun")
            problems.append(
                f"В тексте написано {{{key}:{operation},{argument}}}, но '{key}' — не существительное. "
                f"Первым идёт СУЩЕСТВИТЕЛЬНОЕ, вторым ЧИСЛО: правильно {{слово:{operation},{key}}}. "
                + (f"Существительные в твоей схеме: {', '.join(nouns)}."
                   if nouns else "В схеме вообще нет параметра типа noun — заведи его или убери слот count.")
            )
        elif argument not in schema and argument not in (candidate.get("derived_values") or {}):
            problems.append(
                f"В слоте {{{key}:{operation},{argument}}} число '{argument}' нигде не объявлено."
            )
    return problems


def repair_candidate(candidate: dict[str, Any]) -> list[str]:
    """Детерминированно починить механические ошибки модели, не трогая смысл.

    Чинятся только те случаи, где правильный вариант однозначен:

    1. ``{число:count,X}`` — count допустим лишь у существительного. Если слева
       числовой параметр, автор имел в виду просто подстановку числа
       («каждый {freq}-й день»), и слот схлопывается в ``{число}``.
    2. ``в {place:acc}`` / ``на {place:pre}`` — у локации предлог лежит в данных,
       поэтому предлог из текста убирается, а падеж заменяется на ``dir`` (куда)
       или ``loc`` (где). Это ровно то, ради чего слоты dir/loc и заведены.
    3. Поле ``universe`` у персонажа: модель регулярно пишет несуществующее имя
       мира, хотя движок выбирает мир сам.

    Возвращает список сделанных правок — он попадает в отчёт, чтобы проверяющий
    видел, что именно чинилось автоматически.
    """
    import re as _re

    repairs: list[str] = []
    text = str(candidate.get("candidate_template_text", ""))
    schema = candidate.get("parameter_schema", {})
    if not isinstance(schema, dict):
        return repairs
    derived = candidate.get("derived_values") or {}

    def kind_of(name: str) -> str | None:
        rule = schema.get(name)
        return rule.get("type") if isinstance(rule, dict) else None

    def fix_count(match: _re.Match[str]) -> str:
        key, operation, argument = match.group(1), match.group(2), match.group(3)
        if kind_of(key) == "noun":
            return match.group(0)
        if argument in schema or argument in derived:
            # Число объявлено — значит перепутан порядок аргументов.
            if kind_of(argument) == "noun":
                repairs.append(f"{{{key}:{operation},{argument}}} -> {{{argument}:{operation},{key}}}")
                return f"{{{argument}:{operation},{key}}}"
            return f"{{{key}}}"
        repairs.append(f"{{{key}:{operation},{argument}}} -> {{{key}}} (count не у существительного)")
        return f"{{{key}}}"

    text = _re.sub(r"\{\s*([A-Za-z_]\w*)\s*:\s*(count|agree)\s*,\s*([A-Za-z_]\w*)\s*\}", fix_count, text)

    def fix_place(match: _re.Match[str]) -> str:
        preposition, key, case = match.group(1), match.group(2), match.group(3)
        if kind_of(key) != "location":
            return match.group(0)
        target = "dir" if case == "acc" else "loc"
        repairs.append(f"{preposition} {{{key}:{case}}} -> {{{key}:{target}}} (предлог берётся из данных локации)")
        return f"{{{key}:{target}}}"

    text = _re.sub(r"\b(в|во|на)\s+\{\s*([A-Za-z_]\w*)\s*:\s*(acc|pre)\s*\}", fix_place, text)
    candidate["candidate_template_text"] = text

    for name, rule in schema.items():
        if isinstance(rule, dict) and rule.get("type") == "character" and "universe" in rule:
            repairs.append(f"убрано universe={rule['universe']!r} у параметра {name}")
            rule.pop("universe")
    return repairs


def process_task(task: dict[str, Any], *, model: str, system: str, schema: dict[str, Any],
                 service: TemplateStudioService, known_modules: set[str],
                 retries: int, timeout: int) -> dict[str, Any]:
    base_prompt = build_user_prompt(task)
    messages = [{"role": "user", "content": base_prompt}]
    record: dict[str, Any] = {
        "template_id": task["template_id"],
        "module_id": task["module_id"],
        "source_problems": list(task["problems"]),
        "attempts": [],
        "outcome": "rejected",
        "seconds": 0.0,
    }
    for attempt in range(1, retries + 1):
        # Температура растёт с попытками: на 0.2 модель воспроизводит собственный
        # предыдущий ответ дословно, и цикл исправлений не сдвигается с места.
        temperature = min(0.2 + 0.2 * (attempt - 1), 0.8)
        try:
            raw, elapsed = call_ollama(model, system, messages, schema, timeout, temperature)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            record["attempts"].append({"n": attempt, "error": f"ollama недоступна: {error}"})
            record["outcome"] = "infrastructure_error"
            return record
        record["seconds"] += elapsed

        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError as error:
            record["attempts"].append({"n": attempt, "seconds": round(elapsed, 1), "error": f"не JSON: {error}"})
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": "Ответ не разобрался как JSON. Верни только JSON-объект."}]
            continue

        if str(candidate.get("module_id")) == "NEEDS_DATA":
            record["outcome"] = "needs_data"
            record["candidate"] = candidate
            record["attempts"].append({"n": attempt, "seconds": round(elapsed, 1), "error": "модель просит данные"})
            return record

        # Поля, которые модель не должна сочинять: они целиком определяются задачей.
        candidate["template_id"] = task["template_id"]
        candidate["schema_version"] = 1
        candidate["language"] = "ru"
        candidate["solver_strategy"] = "formula"
        candidate["source_metadata"] = {
            "problem_number": ", ".join(str(number) for number in task["problems"]),
            "filename": task.get("filename", ""),
        }

        repairs = repair_candidate(candidate)
        if repairs:
            record.setdefault("repairs", []).append({"n": attempt, "fixes": repairs})

        try:
            report = validate_candidate(service, candidate, known_modules)
        except Exception as error:  # валидатор кидает разные типы — для отчёта важен текст
            report = {"passed": False, "checks": [{"passed": False, "label": "исключение", "message": str(error)}]}

        if report.get("passed"):
            record["outcome"] = "passed_validator"
            record["candidate"] = candidate
            record["attempts"].append({"n": attempt, "seconds": round(elapsed, 1), "error": None})
            record["report"] = report
            return record

        problem = failure_text(report)
        record["attempts"].append({"n": attempt, "seconds": round(elapsed, 1), "error": problem})
        # Контекст обнуляем: предыдущий ответ модели в истории заставляет её
        # копировать себя. Вместо диалога — новый одиночный запрос, куда вшиты
        # текст ошибки и конкретные указания, что переписать.
        hints = hints_for(problem, candidate)
        messages = [{"role": "user", "content":
            f"{base_prompt}\n"
            f"Предыдущая попытка была отклонена валидатором.\n"
            f"Ошибки: {problem}\n"
            + (f"Что исправить:\n{hints}\n" if hints else "")
            + "Напиши шаблон заново, с нуля, не повторяя прежних конструкций."}]
    record["candidate"] = locals().get("candidate")
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Локальный агент: очередь задач -> JSON-шаблоны.")
    parser.add_argument("--queue", required=True, help="JSON-файл очереди задач.")
    parser.add_argument("--model", default="qwen3:8b", help="Модель Ollama.")
    parser.add_argument("--retries", type=int, default=4, help="Попыток на задачу.")
    parser.add_argument("--timeout", type=int, default=600, help="Таймаут одного запроса, секунд.")
    parser.add_argument("--limit", type=int, default=0, help="Взять только первые N задач.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = json.loads(Path(args.queue).read_text(encoding="utf-8"))["tasks"]
    if args.limit:
        tasks = tasks[: args.limit]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    system = build_system_prompt()
    service = TemplateStudioService(store=TemplateStudioStore())
    known_modules = catalogue_module_ids()

    records = []
    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] {task['template_id']} ... ", end="", flush=True)
        record = process_task(
            task, model=args.model, system=system, schema=schema, service=service,
            known_modules=known_modules, retries=args.retries, timeout=args.timeout,
        )
        records.append(record)
        attempts = len(record["attempts"])
        print(f"{record['outcome']} (попыток {attempts}, {record['seconds']:.0f} c)")

        target = {"passed_validator": "incoming", "needs_data": "needs_data"}.get(record["outcome"], "rejected")
        directory = STUDIO_ROOT / target
        directory.mkdir(parents=True, exist_ok=True)
        body = record.get("candidate") if target == "incoming" else record
        (directory / f"{task['template_id']}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    summary = {
        "model": args.model,
        "queue": str(args.queue),
        "finished_at": stamp,
        "totals": {
            outcome: sum(1 for record in records if record["outcome"] == outcome)
            for outcome in sorted({record["outcome"] for record in records})
        },
        "seconds": round(sum(record["seconds"] for record in records), 1),
        "records": records,
    }
    runs = STUDIO_ROOT / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / f"{stamp}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nИтог: {summary['totals']} за {summary['seconds']:.0f} c")
    print(f"Отчёт: data/template_studio/runs/{stamp}.json")


if __name__ == "__main__":
    main()
