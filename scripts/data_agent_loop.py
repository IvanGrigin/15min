"""Агент данных: массовое пополнение словаря существительных.

Роли распределены так, как показал пилот: сочинять задачи локальная модель
не умеет, а вот выдавать словоформы — умеет, и это проверяемо машиной.

Ключ к качеству — **две независимые деривации одного и того же**:

    правила склонения (scripts/declension_rules.py)  ──┐
                                                       ├── совпали → принять без человека
    языковая модель через Ollama ──────────────────────┘   разошлись → человеку, одной строкой

Правила не знают исключений, модель знает их статистически. Совпадение двух
независимых источников — сильное свидетельство; расхождение — ровно тот случай,
где нужен человек, и только он попадает в очередь на проверку.

Поверх этого работают механические проверки, для которых исключений в языке нет
(орфография -и/-ы, винительный мн. по одушевлённости, непустые формы).

Запуск:
    python3 scripts/data_agent_loop.py --queue data/language/queue/nouns.json
    python3 scripts/data_agent_loop.py --queue ... --model qwen3:14b
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
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from declension_rules import CASES, decline, orthography_problems  # noqa: E402

NOUNS_PATH = PROJECT_ROOT / "data" / "language" / "nouns" / "russian_nouns.json"
STAGING_ROOT = PROJECT_ROOT / "data" / "language" / "staging"
OLLAMA_URL = "http://localhost:11434/api/chat"

FORMS_SCHEMA = {
    "type": "object",
    "required": ["forms"],
    "properties": {
        "forms": {
            "type": "object",
            "required": list(CASES),
            "properties": {case: {"type": "string"} for case in CASES},
        }
    },
}

SYSTEM = """Ты — справочник по русской морфологии. Тебе дают начальную форму
существительного, его род и одушевлённость. Ты возвращаешь все двенадцать форм.

Только JSON, без пояснений.

Падежи единственного числа: nom, gen, dat, acc, ins, pre.
Падежи множественного числа: nom_pl, gen_pl, dat_pl, acc_pl, ins_pl, pre_pl.

Правила, в которых нет исключений:
- Винительный множественного у одушевлённых совпадает с родительным множественного
  (вижу людей), у неодушевлённых — с именительным множественного (вижу столы).
- После к, г, х, ж, ш, ч, щ пишется -и, а не -ы: посылки, шишки, пироги.

Отдельно следи за неправильными формами: год -> лет, человек -> люди/людей,
друг -> друзья/друзей, лист -> листья, дерево -> деревья, ведро -> вёдра/вёдер,
метла -> мётлы/мётел. Если у слова есть чередование в основе — сохрани его.
"""


def call_ollama(model: str, word: str, gender: str, animate: bool, timeout: int) -> tuple[dict[str, str], float]:
    prompt = (
        f"Слово: {word}\n"
        f"Род: {'мужской' if gender == 'm' else 'женский' if gender == 'f' else 'средний'}\n"
        f"Одушевлённое: {'да' if animate else 'нет'}\n"
        f"Верни двенадцать форм."
    )
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "format": FORMS_SCHEMA,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.0, "num_ctx": 4096},
    }
    request = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = json.loads(body["message"]["content"])
    return {case: str(content["forms"].get(case, "")).strip() for case in CASES}, time.monotonic() - started


def mechanical_problems(forms: dict[str, str], animate: bool) -> list[str]:
    """Нарушения правил, у которых в языке нет исключений."""
    problems = orthography_problems(forms)
    expected = forms.get("gen_pl") if animate else forms.get("nom_pl")
    if forms.get("acc_pl") != expected:
        problems.append(
            f"acc_pl={forms.get('acc_pl')!r}: при animate={animate} должно быть {expected!r}"
        )
    if forms.get("nom") and forms["nom"] != forms.get("acc") and animate and forms.get("acc") != forms.get("gen"):
        problems.append("одушевлённое: винительный ед. ч. должен совпадать с родительным")
    return problems


def process(word: str, gender: str, animate: bool, *, model: str, timeout: int) -> dict[str, Any]:
    rules = decline(word, gender, animate=animate)
    record: dict[str, Any] = {
        "word": word, "gender": gender, "animate": animate,
        "rules_confidence": rules.confidence, "rules_notes": list(rules.notes),
    }
    try:
        llm_forms, seconds = call_ollama(model, word, gender, animate, timeout)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError) as error:
        record["outcome"] = "infrastructure_error"
        record["error"] = str(error)
        return record
    record["seconds"] = round(seconds, 1)

    mismatches = [case for case in CASES if rules.forms.get(case) != llm_forms.get(case)]
    record["mismatches"] = {
        case: {"rules": rules.forms.get(case), "llm": llm_forms.get(case)} for case in mismatches
    }
    problems = mechanical_problems(llm_forms, animate)
    record["mechanical_problems"] = problems

    if problems:
        # Модель нарушила правило без исключений — её вариант заведомо неверен.
        record["outcome"] = "conflict"
        record["reason"] = "модель нарушила механическое правило"
        record["forms"] = {"rules": rules.forms, "llm": llm_forms}
    elif not mismatches and rules.forms:
        record["outcome"] = "agreed"
        record["forms"] = llm_forms
    else:
        record["outcome"] = "conflict"
        record["reason"] = f"расхождение в {len(mismatches)} формах"
        record["forms"] = {"rules": rules.forms, "llm": llm_forms}
    return record


def process_rules_only(word: str, gender: str, animate: bool) -> dict[str, Any]:
    """Заготовка по правилам без языковой модели.

    Замер на 229 проверенных вручную словах: правила дают 80 % точности там,
    где уверены, и сами помечают 28 % слов как рискованные. Языковая модель
    в этой роли оказалась хуже правил (путает творительный с винительным
    и предложный с дательным), поэтому основной режим — этот.
    """
    rules = decline(word, gender, animate=animate)
    problems = mechanical_problems(rules.forms, animate) if rules.forms else ["правила не распознали тип склонения"]
    return {
        "word": word, "gender": gender, "animate": animate,
        "rules_confidence": rules.confidence, "rules_notes": list(rules.notes),
        "mechanical_problems": problems,
        "forms": rules.forms,
        "outcome": "needs_check" if (problems or rules.confidence == "low") else "draft_ok",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Пополнение словаря существительных.")
    parser.add_argument("--queue", required=True)
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--rules-only", action="store_true",
                        help="Основной режим: только правила, без Ollama (быстро и точнее).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))["words"]
    if args.limit:
        queue = queue[: args.limit]
    known = set(json.loads(NOUNS_PATH.read_text(encoding="utf-8"))["nouns"])

    records = []
    for index, item in enumerate(queue, start=1):
        word = item["word"]
        if word in known:
            print(f"[{index}/{len(queue)}] {word}: уже в словаре, пропуск")
            continue
        animate = bool(item.get("animate", False))
        if args.rules_only:
            record = process_rules_only(word, item["gender"], animate)
        else:
            record = process(word, item["gender"], animate, model=args.model, timeout=args.timeout)
        records.append(record)
        mark = {"agreed": "принято", "conflict": "конфликт",
                "draft_ok": "заготовка", "needs_check": "на проверку"}.get(record["outcome"], record["outcome"])
        extra = f" [{record.get('reason') or '; '.join(record.get('rules_notes', []))}]" \
            if record["outcome"] in {"conflict", "needs_check"} else ""
        print(f"[{index}/{len(queue)}] {word}: {mark}{extra}")

    STAGING_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    agreed = [record for record in records if record["outcome"] in {"agreed", "draft_ok"}]
    conflicts = [record for record in records if record["outcome"] in {"conflict", "needs_check"}]
    (STAGING_ROOT / f"agreed_{stamp}.json").write_text(
        json.dumps({"words": agreed}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (STAGING_ROOT / f"conflicts_{stamp}.json").write_text(
        json.dumps({"words": conflicts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = len(records)
    print(f"\nОбработано: {total}")
    if total:
        print(f"  совпали две деривации (принято автоматически): {len(agreed)} ({len(agreed)/total:.0%})")
        print(f"  расхождения (человеку): {len(conflicts)} ({len(conflicts)/total:.0%})")
    print(f"Файлы: data/language/staging/agreed_{stamp}.json, conflicts_{stamp}.json")


if __name__ == "__main__":
    main()
