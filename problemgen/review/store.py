"""Хранилище преподавательского ревью: оценки, замечания и сравнения.

Ревью идёт двумя способами, и они дают разное знание.

Первый — разбор темы целиком. Преподаватель видит все шаблоны одной темы
рядом, ставит каждому уровень (легко / средне / сложно) и пишет, что в нём
исправить. Рядом видно и то, чего в теме не хватает.

Второй — парные сравнения внутри темы: «какая из двух сложнее». Человек
плохо назначает абсолютные баллы и хорошо сравнивает два предмета, поэтому
порядок по сложности набирается сравнениями, а не оценками. Итог считается
рейтингом Эло: каждое сравнение чуть двигает обе задачи навстречу
результату, и после нескольких десятков сравнений порядок устаканивается.

Оба журнала пишутся по-разному не случайно. Оценка — это текущее мнение
о шаблоне, поэтому она перезаписывается. Сравнение — это состоявшийся факт
(«в тот раз я счёл эту сложнее»), поэтому журнал сравнений только пополняется:
из него всегда можно пересчитать рейтинг заново, а из перезаписанного —
уже ничего.
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
from datetime import datetime, timezone
from typing import Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEW_DIR = PROJECT_ROOT / "data" / "review"
VERDICTS_PATH = REVIEW_DIR / "verdicts.json"
COMPARISONS_PATH = REVIEW_DIR / "comparisons.json"

DIFFICULTIES = ("easy", "medium", "hard")
DIFFICULTY_LABELS = {"easy": "легко", "medium": "средне", "hard": "сложно"}
# Стартовый рейтинг и шаг. K = 24 — крупный шаг: сравнений будет не тысячи,
# а десятки, и порядок должен успеть сложиться быстро.
BASE_RATING = 1000.0
K_FACTOR = 24.0
MAX_COMMENT = 4000
# Сервер ревью многопоточный: две вкладки, сохранившие оценку одновременно,
# иначе выполняли бы «прочитать — изменить — записать» вперехлёст. Один
# потерял бы правку другого, а общий временный файл они и вовсе писали бы
# посимвольно вперемешку, оставляя на диске склейку двух JSON.
_LOCK = threading.RLock()


class ReviewError(ValueError):
    """Некорректная запись ревью."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: pathlib.Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReviewError(f"Файл ревью {path.name} повреждён: {error}") from error


def _write(path: pathlib.Path, payload: Any) -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    # Запись через временный файл: обрыв на середине не должен оставить
    # обрезанный журнал вместо накопленного ревью. Имя уникально для каждой
    # записи — общее имя два потока писали бы одновременно.
    temporary = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_verdicts() -> dict[str, dict[str, Any]]:
    """Текущие оценки и все замечания по шаблонам.

    Замечания хранятся журналом, а не одним полем: их пишут по ходу разбора,
    и каждое потом превращается в правку шаблона. Затирать предыдущее новым
    означало бы терять уже сделанную работу.
    """
    data = _read(VERDICTS_PATH, {})
    if not isinstance(data, dict):
        return {}
    for entry in data.values():
        if isinstance(entry, dict) and "comment" in entry and "comments" not in entry:
            # Ранняя версия хранила одно замечание строкой.
            text = str(entry.pop("comment") or "").strip()
            entry["comments"] = [{"text": text, "at": entry.get("updated_at", "")}] if text else []
    return data


def save_verdict(
    template_id: str, *, difficulty: str | None = None, comment: str | None = None
) -> dict[str, Any]:
    """Поставить уровень и, если передано, добавить ещё одно замечание.

    Уровень перезаписывается — это текущее мнение. Замечание добавляется
    к журналу и уходит вместе с уровнем, при котором было написано: «сложно,
    потому что числа великоваты» — цельная мысль, и разрывать её незачем.
    Пустая строка не создаёт записи, поэтому сохранить один уровень можно.
    """
    if not isinstance(template_id, str) or not template_id.strip():
        raise ReviewError("Нужен идентификатор шаблона.")
    if difficulty is not None and difficulty not in DIFFICULTIES:
        raise ReviewError(f"Уровень должен быть одним из: {', '.join(DIFFICULTIES)}.")
    if comment is not None and len(comment) > MAX_COMMENT:
        raise ReviewError(f"Замечание длиннее {MAX_COMMENT} символов.")

    with _LOCK:
        verdicts = load_verdicts()
        entry = dict(verdicts.get(template_id) or {})
        entry.setdefault("comments", [])
        if difficulty is not None:
            entry["difficulty"] = difficulty
        text = (comment or "").strip()
        if text:
            entry["comments"] = list(entry["comments"]) + [
                {"text": text, "at": _now(), "difficulty": difficulty or entry.get("difficulty")}
            ]
        entry["updated_at"] = _now()
        verdicts[template_id] = entry
        _write(VERDICTS_PATH, verdicts)
    return entry


def save_draft(template_id: str, text: str) -> dict[str, Any]:
    """Сохранить недописанное замечание, не занося его в журнал.

    Черновик перезаписывается при каждом нажатии клавиши, поэтому в журнал
    он попасть не может: иначе одна фраза превратилась бы в полсотни записей
    «п», «пя», «пят». Зато набранное больше не пропадает — ни при переходе
    между темами, ни при закрытии вкладки, ни при перерисовке списка.

    Именно этого не хватало в первой версии: перерисовка после сохранения
    одного замечания стирала текст, набранный в остальных полях.
    """
    if not isinstance(template_id, str) or not template_id.strip():
        raise ReviewError("Нужен идентификатор шаблона.")
    if len(text) > MAX_COMMENT:
        raise ReviewError(f"Замечание длиннее {MAX_COMMENT} символов.")
    with _LOCK:
        verdicts = load_verdicts()
        entry = dict(verdicts.get(template_id) or {})
        entry.setdefault("comments", [])
        entry["draft"] = text
        entry["updated_at"] = _now()
        verdicts[template_id] = entry
        _write(VERDICTS_PATH, verdicts)
    return entry


def commit_drafts(template_ids: list[str] | None = None) -> list[str]:
    """Перенести черновики в журнал замечаний и вернуть затронутые шаблоны.

    Так набранное за один проход по теме фиксируется одним действием.
    Пустые черновики пропускаются, повторный вызов ничего не дублирует.
    """
    committed: list[str] = []
    with _LOCK:
        verdicts = load_verdicts()
        for template_id, entry in verdicts.items():
            if template_ids is not None and template_id not in template_ids:
                continue
            text = str(entry.get("draft") or "").strip()
            if not text:
                continue
            entry["comments"] = list(entry.get("comments") or []) + [
                {"text": text, "at": _now(), "difficulty": entry.get("difficulty")}
            ]
            entry["draft"] = ""
            entry["updated_at"] = _now()
            committed.append(template_id)
        if committed:
            _write(VERDICTS_PATH, verdicts)
    return committed


def drop_comment(template_id: str, index: int) -> dict[str, Any]:
    """Убрать одно замечание из журнала — для опечаток и передумал."""
    with _LOCK:
        verdicts = load_verdicts()
        entry = dict(verdicts.get(template_id) or {})
        comments = list(entry.get("comments") or [])
        if not 0 <= index < len(comments):
            raise ReviewError("Нет замечания с таким номером.")
        comments.pop(index)
        entry["comments"] = comments
        entry["updated_at"] = _now()
        verdicts[template_id] = entry
        _write(VERDICTS_PATH, verdicts)
    return entry


def load_comparisons() -> list[dict[str, Any]]:
    """Журнал парных сравнений в порядке их появления."""
    data = _read(COMPARISONS_PATH, [])
    return data if isinstance(data, list) else []


def add_comparison(
    module_id: str, harder: str, easier: str, *, tie: bool = False, comment: str = "",
) -> dict[str, Any]:
    """Записать одно сравнение: какая из двух задач темы сложнее.

    Замечание сохраняется вместе со сравнением: мысль «эта сложнее, но только
    из-за громоздких чисел» — самая ценная часть ответа, и без привязки
    к конкретной паре она теряет смысл.

    При ``tie`` порядок аргументов уже не важен, но они всё равно
    сохраняются как есть — журнал должен помнить, что именно показывали.
    """
    if not harder or not easier or harder == easier:
        raise ReviewError("Сравнивать нужно два разных шаблона.")
    if not module_id:
        raise ReviewError("Нужна тема, внутри которой идёт сравнение.")
    if len(comment) > MAX_COMMENT:
        raise ReviewError(f"Замечание длиннее {MAX_COMMENT} символов.")
    record = {
        "module_id": module_id, "harder": harder, "easier": easier,
        "tie": bool(tie), "comment": comment.strip(), "at": _now(),
    }
    with _LOCK:
        comparisons = load_comparisons()
        comparisons.append(record)
        _write(COMPARISONS_PATH, comparisons)
    return record


def ratings(module_id: str | None = None) -> dict[str, float]:
    """Пересчитать рейтинг сложности по всему журналу сравнений.

    Пересчёт всегда идёт с нуля, а не хранится накопленным: журнал —
    единственный источник правды, и любая правка в нём должна честно
    отражаться на порядке.
    """
    scores: dict[str, float] = {}
    for record in load_comparisons():
        if module_id is not None and record.get("module_id") != module_id:
            continue
        harder, easier = record.get("harder"), record.get("easier")
        if not isinstance(harder, str) or not isinstance(easier, str) or harder == easier:
            continue
        first = scores.setdefault(harder, BASE_RATING)
        second = scores.setdefault(easier, BASE_RATING)
        expected = 1.0 / (1.0 + 10 ** ((second - first) / 400.0))
        actual = 0.5 if record.get("tie") else 1.0
        scores[harder] = first + K_FACTOR * (actual - expected)
        scores[easier] = second - K_FACTOR * (actual - expected)
    return scores


def comparison_counts(module_id: str | None = None) -> dict[str, int]:
    """Сколько раз каждый шаблон участвовал в сравнении."""
    counts: dict[str, int] = {}
    for record in load_comparisons():
        if module_id is not None and record.get("module_id") != module_id:
            continue
        for key in ("harder", "easier"):
            value = record.get(key)
            if isinstance(value, str):
                counts[value] = counts.get(value, 0) + 1
    return counts


def seen_pairs(module_id: str) -> set[frozenset[str]]:
    """Пары, которые уже показывали, — чтобы не спрашивать об одном дважды."""
    pairs = set()
    for record in load_comparisons():
        if record.get("module_id") != module_id:
            continue
        harder, easier = record.get("harder"), record.get("easier")
        if isinstance(harder, str) and isinstance(easier, str):
            pairs.add(frozenset({harder, easier}))
    return pairs


def choose_pair(module_id: str, template_ids: list[str], rng) -> tuple[str, str] | None:
    """Выбрать следующую пару для сравнения внутри темы.

    Предпочитается пара, которую ещё не показывали, а среди таких — та, где
    оба участника сравнивались реже других. Так сравнения расходятся по теме
    равномерно, вместо того чтобы бесконечно уточнять уже понятную верхушку.
    """
    if len(template_ids) < 2:
        return None
    counts = comparison_counts(module_id)
    seen = seen_pairs(module_id)
    candidates = [
        (template_ids[i], template_ids[j])
        for i in range(len(template_ids)) for j in range(i + 1, len(template_ids))
    ]
    fresh = [pair for pair in candidates if frozenset(pair) not in seen]
    pool = fresh or candidates
    least = min(counts.get(a, 0) + counts.get(b, 0) for a, b in pool)
    pool = [pair for pair in pool if counts.get(pair[0], 0) + counts.get(pair[1], 0) == least]
    first, second = pool[rng.randrange(len(pool))]
    return (first, second) if rng.random() < 0.5 else (second, first)
