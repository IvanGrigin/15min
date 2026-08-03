"""Сайт преподавательского ревью шаблонов.

Три экрана под три разные задачи.

**Тема целиком.** Все шаблоны одной темы подряд, у каждого — свежие примеры,
уровень сложности и поле для замечаний. Смысл именно в том, чтобы видеть их
рядом: так заметно и повторяющееся, и то, чего в теме нет вовсе.

**Сравнения.** Две задачи одной темы, вопрос один — какая сложнее. Абсолютные
оценки человек ставит плохо, а сравнивает хорошо, поэтому порядок по сложности
набирается отсюда, а не из уровней.

**Итоги.** Что накопилось: порядок по сложности, все замечания списком,
и чего ещё не смотрели.

Задачи берутся из тех же активных шаблонов, что и сайт пятиминуток, —
никакой отдельной копии библиотеки здесь нет.

Запуск:
    python3 run.py --review
    python3 -m problemgen.web.review_site --port 8092
"""
from __future__ import annotations

import argparse
import errno
import html
import json
import random
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from problemgen.review.store import (
    DIFFICULTIES,
    DIFFICULTY_LABELS,
    ReviewError,
    CROSS_MODULE,
    add_comparison,
    add_ranking,
    choose_cross_pair,
    choose_pair,
    commit_drafts,
    comparison_counts,
    drop_comment,
    load_comparisons,
    load_verdicts,
    ratings,
    save_draft,
    save_verdict,
)
from problemgen.template_studio.catalogue import active_templates
from problemgen.template_studio.runtime import (
    TemplateRuntimeError,
    generate_active_template,
    normalize_value,
)
from problemgen.web.studio_site import module_title

MAX_BODY_BYTES = 16_384
EXAMPLES_PER_TEMPLATE = 3


class ReviewSiteError(ValueError):
    """Некорректный запрос к сайту ревью."""


def _templates_by_module() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for template in active_templates():
        grouped.setdefault(str(template.get("module_id") or ""), []).append(template)
    for items in grouped.values():
        items.sort(key=lambda item: str(item.get("template_id")))
    return grouped


def modules_overview() -> list[dict[str, Any]]:
    """Темы со степенью готовности ревью — что смотрели, а что нет."""
    verdicts = load_verdicts()
    counts = comparison_counts()
    overview = []
    for module_id, items in _templates_by_module().items():
        ids = [str(item.get("template_id")) for item in items]
        overview.append({
            "module_id": module_id,
            "title": module_title(module_id),
            "template_count": len(ids),
            "rated": sum(1 for tid in ids if verdicts.get(tid, {}).get("difficulty")),
            "commented": sum(1 for tid in ids if verdicts.get(tid, {}).get("comments")),
            "compared": sum(counts.get(tid, 0) for tid in ids),
        })
    overview.sort(key=lambda item: item["title"])
    return overview


def _examples(template: dict[str, Any], count: int, rng: random.Random) -> list[dict[str, Any]]:
    examples = []
    for _ in range(count):
        try:
            generated = generate_active_template(template, rng)
        except TemplateRuntimeError as error:
            examples.append({"problem": f"Не удалось разыграть: {error}", "answer": "", "failed": True})
            continue
        examples.append({
            "problem": generated["rendered_problem"],
            "answer": generated.get("answer_text") or str(normalize_value(generated["answer"])),
            "variant": (generated.get("variant_metadata") or {}).get("story_variant_id"),
            "universe": (generated.get("story_context") or {}).get("universe"),
            "failed": False,
        })
    return examples


def module_review(module_id: str, seed: int | None = None) -> dict[str, Any]:
    """Все шаблоны темы с примерами и уже выставленными оценками."""
    grouped = _templates_by_module()
    if module_id not in grouped:
        raise ReviewSiteError(f"Нет активных шаблонов темы {module_id!r}.")
    rng = random.Random(seed)
    verdicts = load_verdicts()
    counts = comparison_counts(module_id)
    scores = ratings(module_id)
    items = []
    for template in grouped[module_id]:
        tid = str(template.get("template_id"))
        verdict = verdicts.get(tid, {})
        items.append({
            "template_id": tid,
            "source": (template.get("source_metadata") or {}).get("problem_number"),
            "notes": template.get("notes") or "",
            "variants": len(template.get("story_variants") or []),
            "examples": _examples(template, EXAMPLES_PER_TEMPLATE, rng),
            "difficulty": verdict.get("difficulty"),
            "comments": verdict.get("comments") or [],
            "draft": verdict.get("draft", ""),
            "updated_at": verdict.get("updated_at"),
            "comparisons": counts.get(tid, 0),
            "rating": round(scores.get(tid, 0.0)) if tid in scores else None,
        })
    return {"module_id": module_id, "title": module_title(module_id), "templates": items}


def next_pair(module_id: str, seed: int | None = None) -> dict[str, Any]:
    """Следующая пара задач для сравнения по сложности.

    Внутри темы сравниваются близкие задачи, и вопрос упирается в устройство
    самой задачи. Между темами (module_id равен CROSS_MODULE) сравниваются
    разные приёмы, и это отдельный журнал: смешивать их нельзя, а шкала
    рейтинга всё равно одна на всю библиотеку.
    """
    grouped = _templates_by_module()
    if module_id == CROSS_MODULE:
        return _cross_pair(grouped, seed)
    if module_id not in grouped:
        raise ReviewSiteError(f"Нет активных шаблонов темы {module_id!r}.")
    templates = {str(item.get("template_id")): item for item in grouped[module_id]}
    if len(templates) < 2:
        raise ReviewSiteError("В теме меньше двух шаблонов — сравнивать не с чем.")
    rng = random.Random(seed)
    pair = choose_pair(module_id, sorted(templates), rng)
    if pair is None:
        raise ReviewSiteError("Не удалось выбрать пару.")
    sides = []
    for tid in pair:
        example = _examples(templates[tid], 1, rng)[0]
        sides.append({"template_id": tid, **example})
    return {
        "module_id": module_id, "title": module_title(module_id),
        "left": sides[0], "right": sides[1],
        "done": len([r for r in load_comparisons() if r.get("module_id") == module_id]),
        "possible": len(templates) * (len(templates) - 1) // 2,
    }


def _cross_pair(grouped: dict[str, list[dict[str, Any]]], seed: int | None) -> dict[str, Any]:
    """Пара задач из разных тем."""
    by_module = {
        module: [str(item.get("template_id")) for item in items]
        for module, items in grouped.items() if items
    }
    known = {
        str(item.get("template_id")): item
        for items in grouped.values() for item in items
    }
    rng = random.Random(seed)
    pair = choose_cross_pair(by_module, rng)
    if pair is None:
        raise ReviewSiteError("Не из чего выбирать: нужны хотя бы две разные темы.")
    sides = []
    for tid in pair:
        example = _examples(known[tid], 1, rng)[0]
        owner = next(module for module, ids in by_module.items() if tid in ids)
        sides.append({"template_id": tid, "module_title": module_title(owner), **example})
    return {
        "module_id": CROSS_MODULE, "title": "Между темами",
        "left": sides[0], "right": sides[1],
        "done": len([r for r in load_comparisons() if r.get("module_id") == CROSS_MODULE]),
        "possible": sum(
            len(ids) * (len(known) - len(ids)) for ids in by_module.values()
        ) // 2,
    }


RANKING_SIZE = 12


def next_ranking(count: int = RANKING_SIZE, seed: int | None = None) -> dict[str, Any]:
    """Набор задач для раскладки по трудности слева направо.

    Берутся самые редко сравнивавшиеся шаблоны из разных тем: раскладка
    нужна прежде всего затем, чтобы связать между собой те задачи, о которых
    ещё ничего не известно. Порядок карточек на экране перемешан нарочно —
    подсказывать ответ расстановкой нельзя.
    """
    if not 2 <= count <= 20:
        raise ReviewSiteError("В раскладке от двух до двадцати задач.")
    grouped = _templates_by_module()
    known = {
        str(item.get("template_id")): (module, item)
        for module, items in grouped.items() for item in items
    }
    if len(known) < count:
        raise ReviewSiteError(f"Шаблонов меньше {count}.")
    counts = comparison_counts()
    rng = random.Random(seed)
    # Сначала самые редкие, а среди равных — в случайном порядке, чтобы
    # раскладки не повторяли одну и ту же дюжину изо дня в день.
    ordered = sorted(known, key=lambda tid: (counts.get(tid, 0), rng.random()))
    chosen: list[str] = []
    used_modules: set[str] = set()
    for template_id in ordered:
        module, _ = known[template_id]
        if module in used_modules:
            continue
        chosen.append(template_id)
        used_modules.add(module)
        if len(chosen) == count:
            break
    for template_id in ordered:                     # добор, если тем не хватило
        if len(chosen) == count:
            break
        if template_id not in chosen:
            chosen.append(template_id)
    rng.shuffle(chosen)
    cards = []
    for template_id in chosen:
        module, template = known[template_id]
        example = _examples(template, 1, rng)[0]
        cards.append({
            "template_id": template_id,
            "module_title": module_title(module),
            "comparisons": counts.get(template_id, 0),
            **example,
        })
    return {"module_id": CROSS_MODULE, "cards": cards}


def report() -> dict[str, Any]:
    """Итог ревью: порядок по сложности, замечания и незакрытые места."""
    verdicts = load_verdicts()
    scores = ratings()
    counts = comparison_counts()
    grouped = _templates_by_module()
    modules = []
    for module_id, items in sorted(grouped.items(), key=lambda pair: module_title(pair[0])):
        rows = []
        for template in items:
            tid = str(template.get("template_id"))
            verdict = verdicts.get(tid, {})
            rows.append({
                "template_id": tid,
                "difficulty": verdict.get("difficulty"),
                "difficulty_label": DIFFICULTY_LABELS.get(verdict.get("difficulty") or ""),
                "comments": verdict.get("comments") or [],
                "rating": round(scores.get(tid, 0.0)) if tid in scores else None,
                "comparisons": counts.get(tid, 0),
            })
        # Сложнее — выше. Шаблоны без сравнений идут в конец: у них не рейтинг
        # ноль, а отсутствие данных, и смешивать это с «оказался лёгким» нельзя.
        rows.sort(key=lambda row: (row["rating"] is None, -(row["rating"] or 0), row["template_id"]))
        modules.append({"module_id": module_id, "title": module_title(module_id), "templates": rows})
    total = sum(len(items) for items in grouped.values())
    return {
        "modules": modules,
        "total": total,
        "rated": sum(1 for tid in verdicts if verdicts[tid].get("difficulty")),
        "commented": sum(len(verdicts[tid].get("comments") or []) for tid in verdicts),
        "comparisons": len(load_comparisons()),
    }


PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ревью шаблонов</title>
<style>
:root {
  --ground: #eef1ee;
  --surface: #fff;
  --surface-2: #f5f8f5;
  --ink: #17201d;
  --soft: #55635e;
  --faint: #7d8a85;
  --line: #d7ddd8;
  --accent: #1f5468;
  --easy: #37674a;
  --easy-bg: #dfeade;
  --medium: #8a5620;
  --medium-bg: #f2e6d6;
  --hard: #8c3535;
  --hard-bg: #f2dcdc;
  --serif: Iowan Old Style, Palatino, Georgia, serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ground: #121614;
    --surface: #191f1c;
    --surface-2: #1f2622;
    --ink: #e3e8e4;
    --soft: #a3b0aa;
    --faint: #7b8883;
    --line: #2c3531;
    --accent: #79b3c8;
    --easy: #8dc09c;
    --easy-bg: #1d2b22;
    --medium: #d3a267;
    --medium-bg: #2e2418;
    --hard: #d98b8b;
    --hard-bg: #2e1d1d;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--ground);
  color: var(--ink);
  font: 16px/1.5 ui-sans-serif, -apple-system, Segoe UI, Roboto, sans-serif;
}
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 18px 80px; }
header { padding: 32px 0 8px; }
h1 { font-family: var(--serif); font-size: 30px; margin: 0 0 6px; font-weight: 600; }
.sub { color: var(--soft); margin: 0; font-size: 15px; }
nav { display: flex; gap: 8px; margin: 22px 0 0; border-bottom: 1px solid var(--line); }
nav button {
  font: inherit;
  font-size: 15px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--soft);
  padding: 10px 14px;
  border-bottom: 2px solid transparent;
}
nav button[aria-selected="true"] {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}
nav button:focus-visible,
.btn:focus-visible,
select:focus-visible,
textarea:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.bar { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 18px 0; }
select, textarea {
  font: inherit;
  color: var(--ink);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 3px;
}
select { padding: 8px 10px; font-size: 15px; }
textarea {
  width: 100%;
  padding: 9px 11px;
  font-size: 14.5px;
  min-height: 58px;
  resize: vertical;
}
.btn {
  font: inherit;
  font-size: 14.5px;
  cursor: pointer;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 3px;
  padding: 8px 14px;
}
.btn.primary { background: var(--accent); border-color: var(--accent); color: var(--ground); }
.btn.easy[aria-pressed="true"] { background: var(--easy-bg); color: var(--easy); font-weight: 600; }
.btn.medium[aria-pressed="true"] {
  background: var(--medium-bg);
  color: var(--medium);
  font-weight: 600;
}
.btn.hard[aria-pressed="true"] { background: var(--hard-bg); color: var(--hard); font-weight: 600; }
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 16px 18px;
  margin-bottom: 14px;
}
.card-head {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  align-items: baseline;
  margin-bottom: 12px;
}
.tid { font-family: var(--mono); font-weight: 600; font-size: 14.5px; }
.meta { font-family: var(--mono); font-size: 12.5px; color: var(--faint); }
.chip {
  font-family: var(--mono);
  font-size: 11.5px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--soft);
  border: 1px solid var(--line);
}
.chip.easy { background: var(--easy-bg); color: var(--easy); border-color: transparent; }
.chip.medium { background: var(--medium-bg); color: var(--medium); border-color: transparent; }
.chip.hard { background: var(--hard-bg); color: var(--hard); border-color: transparent; }
.spacer { margin-left: auto; }
.q {
  font-family: var(--serif);
  font-size: 16px;
  line-height: 1.55;
  margin: 0 0 4px;
  max-width: 68ch;
}
.a { font-family: var(--mono); font-size: 13.5px; color: var(--easy); margin: 0 0 12px; }
.a::before { content: "→ "; color: var(--faint); }
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.note-form { display: flex; gap: 8px; align-items: flex-start; margin-top: 10px; }
.note-form textarea { flex: 1; }
.notes { list-style: none; margin: 10px 0 0; padding: 0; display: grid; gap: 6px; }
.notes li {
  background: var(--surface-2);
  border-left: 2px solid var(--accent);
  padding: 7px 10px;
  font-size: 14.5px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.notes time { font-family: var(--mono); font-size: 11.5px; color: var(--faint); white-space: nowrap; }
.notes .drop {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--faint);
  font-size: 15px;
  padding: 0 2px;
}
.saved { font-size: 13px; color: var(--easy); }
.footer-bar {
  position: sticky;
  bottom: 0;
  background: var(--ground);
  border-top: 1px solid var(--line);
  padding: 12px 0;
  margin-top: 4px;
}
.rank-row { display: flex; gap: 10px; overflow-x: auto; padding: 6px 2px 14px; align-items: stretch; }
.rank-card { flex: 0 0 260px; border: 1px solid var(--line); border-radius: 10px;
  padding: 10px; background: var(--card); cursor: grab; position: relative; }
.rank-card.dragging { opacity: .4; }
.rank-card.over { border-color: #2f6feb; box-shadow: 0 0 0 2px rgba(47,111,235,.25); }
.rank-card .pos { font-weight: 700; margin-right: 6px; }
.rank-card .same { border: 1px solid var(--line); border-radius: 6px; background: none;
  cursor: pointer; padding: 1px 7px; font-size: 15px; }
.rank-card.tied { border-style: dashed; }
.rank-card.tied .same { background: #2f6feb; color: #fff; border-color: #2f6feb; }
.rank-card .body { font-size: 14px; margin-top: 8px; max-height: 170px; overflow: auto; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pair .card { margin: 0; display: flex; flex-direction: column; }
.pair .card .btn { margin-top: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14.5px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); }
th, td { vertical-align: top; }
th {
  font-size: 12.5px;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--faint);
  font-weight: 600;
}
td.num { font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right; }
td.tid { font-family: var(--mono); font-size: 13.5px; }
td ul { margin: 0; padding-left: 16px; }
.wide { overflow-x: auto; }
h2 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--accent);
  margin: 28px 0 10px;
}
.hint { color: var(--faint); font-size: 13.5px; margin: 6px 0 0; }
.empty { color: var(--faint); padding: 30px 0; }
@media (max-width: 700px) { .pair { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Ревью шаблонов</h1>
  <p class="sub">Активных шаблонов: {template_count} в {module_count} темах.
     Всё сохраняется в data/review.</p>
</header>

<nav>
  <button id="tab-module" aria-selected="true">Тема целиком</button>
  <button id="tab-pairs" aria-selected="false">Сравнения</button>
  <button id="tab-rank" aria-selected="false">Раскладка</button>
  <button id="tab-report" aria-selected="false">Итоги</button>
</nav>

<section id="view-module">
  <div class="bar">
    <select id="module"></select>
    <button class="btn" id="reroll">Другие примеры</button>
    <span class="meta" id="module-progress"></span>
  </div>
  <div id="templates"></div>
  <div class="bar footer-bar">
    <button class="btn primary" id="commit">Сохранить замечания и перейти к следующей теме</button>
    <span class="saved" id="commit-state"></span>
  </div>
</section>

<section id="view-pairs" hidden>
  <div class="bar">
    <select id="pair-module"></select>
    <span class="meta" id="pair-progress"></span>
  </div>
  <p class="hint">Какая из двух задач сложнее для ребёнка?
     Порядок по сложности набирается из этих ответов.</p>
  <div id="pair"></div>
  <div class="note-form">
    <textarea id="pair-note" placeholder="Замечание к этой паре (необязательно)"></textarea>
  </div>
  <div class="bar">
    <button class="btn" id="tie">Примерно равны</button>
    <button class="btn" id="skip">Пропустить пару</button>
  </div>
</section>

<section id="view-rank" hidden>
  <div class="bar">
    <button class="btn" id="rank-new">Взять другую дюжину</button>
    <span class="meta" id="rank-progress"></span>
  </div>
  <p class="meta">Перетащите карточки: слева — что проще, справа — что сложнее.
    Если задача примерно такая же, как соседняя слева, нажмите на ней «≈».</p>
  <div id="rank-row" class="rank-row"></div>
  <div class="note-form">
    <textarea id="rank-note" placeholder="Замечание к раскладке (необязательно)"></textarea>
  </div>
  <div class="bar">
    <button class="btn primary" id="rank-save">Сохранить порядок</button>
    <span class="meta" id="rank-saved"></span>
  </div>
</section>

<section id="view-report" hidden>
  <div class="bar"><span class="meta" id="report-summary"></span></div>
  <div id="report"></div>
</section>
</div>

<script>
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => (
  {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const LEVELS = [["easy", "легко"], ["medium", "средне"], ["hard", "сложно"]];
let modules = [];

async function api(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Ошибка запроса");
  return payload;
}

function showTab(name) {
  for (const key of ["module", "pairs", "rank", "report"]) {
    document.getElementById("tab-" + key).setAttribute("aria-selected", String(key === name));
    document.getElementById("view-" + key).hidden = key !== name;
  }
  flushDrafts();
  if (name === "pairs") loadPair();
  if (name === "rank") loadRanking();
  if (name === "report") loadReport();
}

function exampleHtml(example) {
  const tail = example.variant
    ? '<p class="meta">оболочка: ' + esc(example.variant) +
      (example.universe ? " · " + esc(example.universe) : "") + "</p>"
    : "";
  return '<p class="q">' + esc(example.problem) + "</p>" +
         '<p class="a">' + esc(example.answer) + "</p>" + tail;
}

function notesHtml(item) {
  if (!item.comments.length) return "";
  return '<ul class="notes">' + item.comments.map((note, index) =>
    "<li><time>" + esc((note.at || "").slice(0, 10)) + "</time><span>" + esc(note.text) +
    "</span>" + (note.difficulty
      ? '<span class="chip ' + esc(note.difficulty) + '">' +
        esc(LEVELS.find(l => l[0] === note.difficulty)?.[1] || "") + "</span>"
      : "") +
    '<button class="drop" data-drop="' + esc(item.template_id) + '" data-index="' + index +
    '" title="Убрать замечание">×</button></li>').join("") + "</ul>";
}

async function loadModules() {
  const payload = await api("/api/modules");
  modules = payload.modules;
  const options = modules.map(m => '<option value="' + esc(m.module_id) + '">' +
    esc(m.title) + " (" + m.template_count + ")</option>").join("");
  document.getElementById("module").innerHTML = options;
  // Между темами сравниваются разные приёмы, а не соседние задачи одной
  // темы, поэтому режим стоит первым и отделён чертой.
  document.getElementById("pair-module").innerHTML =
    '<option value="__cross__">— Между темами: разные типы задач —</option>' + options;
  loadModule();
}

async function loadModule() {
  const moduleId = document.getElementById("module").value;
  if (!moduleId) return;
  const payload = await api("/api/module?module_id=" + encodeURIComponent(moduleId) +
    "&seed=" + Math.floor(Math.random() * 100000));
  const rated = payload.templates.filter(t => t.difficulty).length;
  const notes = payload.templates.reduce((sum, t) => sum + t.comments.length, 0);
  const compared = payload.templates.reduce((sum, t) => sum + t.comparisons, 0);
  document.getElementById("module-progress").textContent =
    "оценено " + rated + " из " + payload.templates.length +
    ", замечаний " + notes + ", сравнений " + compared;
  document.getElementById("templates").innerHTML = payload.templates.map(t => {
    const level = LEVELS.map(([key, label]) =>
      '<button class="btn ' + key + '" data-level="' + key + '" data-tid="' +
      esc(t.template_id) + '" aria-pressed="' + (t.difficulty === key) + '">' +
      label + "</button>").join("");
    const chips = [];
    if (t.rating !== null) chips.push('<span class="chip">сложность ' + t.rating + "</span>");
    if (t.comparisons) chips.push('<span class="chip">' + t.comparisons + " сравнений</span>");
    if (t.variants > 1) chips.push('<span class="chip">' + t.variants + " оболочки</span>");
    return '<article class="card"><div class="card-head">' +
      '<span class="tid">' + esc(t.template_id) + "</span>" +
      '<span class="meta">источник: ' + esc(t.source || "—") + "</span>" +
      '<span class="spacer"></span>' + chips.join(" ") + "</div>" +
      t.examples.map(exampleHtml).join("") +
      '<div class="controls">' + level + '<span class="spacer"></span>' +
      '<span class="saved" id="saved-' + esc(t.template_id) + '"></span></div>' +
      '<div class="note-form"><textarea data-note="' + esc(t.template_id) + '" ' +
      'placeholder="Что исправить в этом шаблоне — сохраняется само">' +
      esc(t.draft) + "</textarea></div>" +
      notesHtml(t) + "</article>";
  }).join("") || '<p class="empty">В теме нет активных шаблонов.</p>';
}

async function saveVerdict(templateId, payload) {
  await api("/api/verdict", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(Object.assign({template_id: templateId}, payload)),
  });
  const mark = document.getElementById("saved-" + templateId);
  if (mark) { mark.textContent = "сохранено"; setTimeout(() => { mark.textContent = ""; }, 1500); }
}

// Набранный текст уходит на сервер сам: через паузу после последней клавиши,
// при уходе из поля и перед любым действием, которое перерисует список.
// Раньше здесь была кнопка «Добавить», и она стирала текст в остальных полях.
const drafts = new Map();
let draftTimer = null;

function markSaving(tid, text) {
  const mark = document.getElementById("saved-" + tid);
  if (mark) mark.textContent = text;
}

async function flushDrafts() {
  const pending = [...drafts.entries()];
  drafts.clear();
  for (const [tid, text] of pending) {
    await api("/api/draft", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({template_id: tid, text}),
    });
    markSaving(tid, "сохранено");
    setTimeout(() => markSaving(tid, ""), 1500);
  }
}

document.getElementById("templates").addEventListener("input", (event) => {
  const area = event.target.closest("textarea[data-note]");
  if (!area) return;
  drafts.set(area.dataset.note, area.value);
  markSaving(area.dataset.note, "сохраняю…");
  clearTimeout(draftTimer);
  draftTimer = setTimeout(flushDrafts, 700);
});

document.getElementById("templates").addEventListener("focusout", (event) => {
  const area = event.target.closest("textarea[data-note]");
  if (!area) return;
  drafts.set(area.dataset.note, area.value);
  clearTimeout(draftTimer);
  flushDrafts();
});

// Закрытая вкладка не должна уносить с собой последние набранные слова.
window.addEventListener("beforeunload", () => {
  for (const [tid, text] of drafts.entries()) {
    navigator.sendBeacon("/api/draft", new Blob(
      [JSON.stringify({template_id: tid, text})], {type: "application/json"}));
  }
});

document.getElementById("templates").addEventListener("click", async (event) => {
  const level = event.target.closest("button[data-level]");
  if (level) {
    const tid = level.dataset.tid;
    for (const other of document.querySelectorAll('button[data-tid="' + tid + '"]')) {
      other.setAttribute("aria-pressed", String(other === level));
    }
    await saveVerdict(tid, {difficulty: level.dataset.level});
    return;
  }
  const drop = event.target.closest("button[data-drop]");
  if (drop) {
    await flushDrafts();
    await api("/api/comment/drop", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({template_id: drop.dataset.drop, index: Number(drop.dataset.index)}),
    });
    loadModule();
  }
});

document.getElementById("commit").addEventListener("click", async () => {
  await flushDrafts();
  const payload = await api("/api/commit", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({}),
  });
  const state = document.getElementById("commit-state");
  state.textContent = payload.committed.length
    ? "записано замечаний: " + payload.committed.length
    : "новых замечаний не было";
  setTimeout(() => { state.textContent = ""; }, 2500);
  const select = document.getElementById("module");
  const next = select.selectedIndex + 1;
  if (next < select.options.length) {
    select.selectedIndex = next;
    window.scrollTo({top: 0});
  }
  loadModule();
});

let currentPair = null;
// ——— Раскладка: двенадцать задач, которые расставляют слева направо ———
let rankCards = [];

async function loadRanking() {
  const row = document.getElementById("rank-row");
  document.getElementById("rank-saved").textContent = "";
  document.getElementById("rank-note").value = "";
  try {
    const payload = await api("/api/ranking?seed=" + Math.floor(Math.random() * 100000));
    rankCards = payload.cards.map(card => ({...card, same: false}));
  } catch (error) {
    row.innerHTML = '<p class="empty">' + esc(error.message) + "</p>";
    return;
  }
  drawRanking();
}

function drawRanking() {
  const row = document.getElementById("rank-row");
  row.innerHTML = rankCards.map((card, index) => (
    '<article class="rank-card' + (card.same ? " tied" : "") + '" draggable="true" data-index="' +
      index + '">' +
      '<div class="card-head"><span class="pos">' + (index + 1) + ".</span>" +
      '<span class="chip">' + esc(card.module_title) + "</span>" +
      (index > 0 ? '<button class="same" title="примерно как соседняя слева">≈</button>' : "") +
      "</div>" +
      '<div class="body">' + esc(card.problem || "") + "</div>" +
    "</article>"
  )).join("");
  document.getElementById("rank-progress").textContent =
    "задач в раскладке: " + rankCards.length + ", связей получится: " + (rankCards.length - 1);
}

let dragFrom = null;

document.getElementById("rank-row").addEventListener("dragstart", (event) => {
  const card = event.target.closest(".rank-card");
  if (!card) return;
  dragFrom = Number(card.dataset.index);
  card.classList.add("dragging");
  event.dataTransfer.effectAllowed = "move";
});

document.getElementById("rank-row").addEventListener("dragend", () => {
  dragFrom = null;
  for (const card of document.querySelectorAll(".rank-card")) {
    card.classList.remove("dragging", "over");
  }
});

document.getElementById("rank-row").addEventListener("dragover", (event) => {
  event.preventDefault();
  const card = event.target.closest(".rank-card");
  if (!card) return;
  for (const other of document.querySelectorAll(".rank-card")) other.classList.remove("over");
  card.classList.add("over");
});

document.getElementById("rank-row").addEventListener("drop", (event) => {
  event.preventDefault();
  const card = event.target.closest(".rank-card");
  if (!card || dragFrom === null) return;
  const to = Number(card.dataset.index);
  if (to === dragFrom) return;
  const [moved] = rankCards.splice(dragFrom, 1);
  rankCards.splice(to, 0, moved);
  // Первая карточка ни с чем не сравнивается слева, пометка на ней бессмысленна.
  if (rankCards.length) rankCards[0].same = false;
  drawRanking();
});

document.getElementById("rank-row").addEventListener("click", (event) => {
  const button = event.target.closest("button.same");
  if (!button) return;
  const index = Number(button.closest(".rank-card").dataset.index);
  rankCards[index].same = !rankCards[index].same;
  drawRanking();
});

document.getElementById("rank-new").addEventListener("click", loadRanking);

document.getElementById("rank-save").addEventListener("click", async () => {
  const saved = document.getElementById("rank-saved");
  try {
    const payload = await api("/api/ranking", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        order: rankCards.map(card => ({
          template_id: card.template_id, same_as_previous: card.same,
        })),
        comment: document.getElementById("rank-note").value,
      }),
    });
    saved.textContent = "записано связей: " + payload.written;
    setTimeout(loadRanking, 900);
  } catch (error) {
    saved.textContent = error.message;
  }
});

async function loadPair() {
  const moduleId = document.getElementById("pair-module").value;
  if (!moduleId) return;
  const box = document.getElementById("pair");
  document.getElementById("pair-note").value = "";
  try {
    currentPair = await api("/api/pair?module_id=" + encodeURIComponent(moduleId) +
      "&seed=" + Math.floor(Math.random() * 100000));
  } catch (error) {
    box.innerHTML = '<p class="empty">' + esc(error.message) + "</p>";
    document.getElementById("pair-progress").textContent = "";
    return;
  }
  const cross = currentPair.module_id === "__cross__";
  document.getElementById("pair-progress").textContent =
    (cross ? "сравнений между темами: " : "сравнений в теме: ") + currentPair.done +
    ", различных пар: " + currentPair.possible;
  box.innerHTML = '<div class="pair">' + ["left", "right"].map(side => {
    const item = currentPair[side];
    const theme = item.module_title
      ? '<span class="chip">' + esc(item.module_title) + "</span>" : "";
    return '<article class="card"><div class="card-head">' +
      '<span class="tid">' + esc(item.template_id) + "</span>" + theme + "</div>" +
      exampleHtml(item) +
      '<button class="btn primary" data-side="' + side + '">Эта сложнее</button></article>';
  }).join("") + "</div>";
}

document.getElementById("pair").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-side]");
  if (!button || !currentPair) return;
  const left = button.dataset.side === "left";
  sendComparison(
    (left ? currentPair.left : currentPair.right).template_id,
    (left ? currentPair.right : currentPair.left).template_id, false);
});

async function sendComparison(harder, easier, tie) {
  await api("/api/comparison", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      module_id: currentPair.module_id, harder, easier, tie,
      comment: document.getElementById("pair-note").value,
    }),
  });
  loadPair();
}

document.getElementById("tie").addEventListener("click", () => {
  if (currentPair) {
    sendComparison(currentPair.left.template_id, currentPair.right.template_id, true);
  }
});
document.getElementById("skip").addEventListener("click", loadPair);

async function loadReport() {
  const payload = await api("/api/report");
  document.getElementById("report-summary").textContent =
    "оценено " + payload.rated + " из " + payload.total + " шаблонов, замечаний " +
    payload.commented + ", сравнений " + payload.comparisons;
  document.getElementById("report").innerHTML = payload.modules.map(m => {
    const rows = m.templates.map(t =>
      '<tr><td class="tid">' + esc(t.template_id) + "</td><td>" +
      (t.difficulty
        ? '<span class="chip ' + t.difficulty + '">' + esc(t.difficulty_label) + "</span>"
        : "") +
      '</td><td class="num">' + (t.rating === null ? "—" : t.rating) + "</td>" +
      '<td class="num">' + t.comparisons + "</td><td>" +
      (t.comments.length
        ? "<ul>" + t.comments.map(c => "<li>" + esc(c.text) + "</li>").join("") + "</ul>"
        : "") +
      "</td></tr>").join("");
    return "<h2>" + esc(m.title) + '</h2><div class="wide"><table><thead><tr>' +
      "<th>шаблон</th><th>уровень</th><th>сложность</th><th>сравнений</th>" +
      "<th>что исправить</th></tr></thead><tbody>" + rows + "</tbody></table></div>";
  }).join("");
}

document.getElementById("tab-module").addEventListener("click", () => showTab("module"));
document.getElementById("tab-pairs").addEventListener("click", () => showTab("pairs"));
document.getElementById("tab-report").addEventListener("click", () => showTab("report"));
document.getElementById("module").addEventListener("change", async () => {
  await flushDrafts();
  loadModule();
});
document.getElementById("reroll").addEventListener("click", async () => {
  await flushDrafts();
  loadModule();
});
document.getElementById("pair-module").addEventListener("change", loadPair);
loadModules();
</script>
</body>
</html>
"""


def render_page() -> str:
    """Собрать страницу ревью."""
    overview = modules_overview()
    return PAGE.replace("{template_count}", str(sum(m["template_count"] for m in overview))) \
               .replace("{module_count}", str(len(overview)))


class Handler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов сайта ревью."""
    server_version = "TemplateReview/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Записать строку журнала запросов с понятным префиксом."""
        print(f"[review-site] {self.address_string()} - {format % args}")

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: Any) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    def do_GET(self) -> None:  # noqa: N802
        """Отдать страницу, список тем, тему целиком, пару или итоги."""
        path = urlparse(self.path).path
        query = self._query()
        seed_raw = (query.get("seed") or [""])[0]
        seed = int(seed_raw) if seed_raw.isdigit() else None
        try:
            if path == "/":
                self._send(HTTPStatus.OK, render_page().encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/modules":
                self._send_json(HTTPStatus.OK, {"modules": modules_overview()})
                return
            if path == "/api/module":
                module_id = (query.get("module_id") or [""])[0]
                self._send_json(HTTPStatus.OK, module_review(module_id, seed))
                return
            if path == "/api/pair":
                module_id = (query.get("module_id") or [""])[0]
                self._send_json(HTTPStatus.OK, next_pair(module_id, seed))
                return
            if path == "/api/ranking":
                raw = (query.get("count") or ["12"])[0]
                count = int(raw) if raw.isdigit() else 12
                self._send_json(HTTPStatus.OK, next_ranking(count, seed))
                return
            if path == "/api/report":
                self._send_json(HTTPStatus.OK, report())
                return
        except (ReviewSiteError, ReviewError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Нет такого адреса."})

    def do_POST(self) -> None:  # noqa: N802
        """Записать оценку с замечанием или результат сравнения."""
        path = urlparse(self.path).path
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
            if path == "/api/verdict":
                entry = save_verdict(
                    str(payload.get("template_id") or ""),
                    difficulty=payload.get("difficulty"),
                    comment=payload.get("comment"),
                )
                self._send_json(HTTPStatus.OK, {"saved": entry})
                return
            if path == "/api/draft":
                entry = save_draft(
                    str(payload.get("template_id") or ""), str(payload.get("text") or ""))
                self._send_json(HTTPStatus.OK, {"saved": entry})
                return
            if path == "/api/commit":
                raw = payload.get("template_ids")
                ids = [str(item) for item in raw] if isinstance(raw, list) else None
                self._send_json(HTTPStatus.OK, {"committed": commit_drafts(ids)})
                return
            if path == "/api/ranking":
                raw = payload.get("order")
                order = raw if isinstance(raw, list) else []
                written = add_ranking(
                    CROSS_MODULE, order, comment=str(payload.get("comment") or ""))
                self._send_json(HTTPStatus.OK, {"written": len(written)})
                return
            if path == "/api/comment/drop":
                entry = drop_comment(
                    str(payload.get("template_id") or ""), int(payload.get("index", -1)))
                self._send_json(HTTPStatus.OK, {"saved": entry})
                return
            if path == "/api/comparison":
                record = add_comparison(
                    str(payload.get("module_id") or ""),
                    str(payload.get("harder") or ""),
                    str(payload.get("easier") or ""),
                    tie=bool(payload.get("tie")),
                    comment=str(payload.get("comment") or ""),
                )
                self._send_json(HTTPStatus.OK, {"saved": record})
                return
        except (ReviewError, ReviewSiteError, TypeError, ValueError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Нет такого адреса."})


def serve(host: str = "127.0.0.1", port: int = 8092) -> None:
    """Запустить локальный сервер ревью."""
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            raise SystemExit(f"Порт {port} занят. Запустите с другим --port.") from error
        raise
    print(f"Ревью шаблонов: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлено.")
    finally:
        server.server_close()


def main() -> None:
    """Точка входа для python3 -m problemgen.web.review_site."""
    parser = argparse.ArgumentParser(description="Сайт преподавательского ревью шаблонов.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8092)
    args = parser.parse_args()
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
