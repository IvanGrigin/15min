"""Сверка покрытия глазами: задача корпуса против выдачи шаблона.

Автоматическая разметка (`tools/classify_corpus_v2.py`) считает задачу
покрытой, если её слова на 42 % совпали со словами какой-нибудь выдачи.
Мера лексическая, и она путает приёмы: «Сколько чётных четырёхзначных чисел
без нуля» и «Сколько всего трёхзначных чисел» совпадают почти дословно, а
решаются по-разному. Поэтому цифру покрытия нельзя брать из классификатора
как есть — её надо поправлять на долю ошибок, а долю ошибок узнают только
сверкой глазами.

Инструмент показывает пары «задача ↔ то, что печатает найденный шаблон», и
складывает вердикты в `data/source_index/coverage_verdicts.json`. Вердикты
накапливаются: проверенное второй раз не показывается, и работу можно вести
частями. По накопленному считается поправленное покрытие с границами
погрешности — по выборке, а не по всему корпусу.

    python3 tools/verify_coverage.py --show 20        # что проверять дальше
    python3 tools/verify_coverage.py --record 291=нет 718=да
    python3 tools/verify_coverage.py --report

Вердикт ставится по приёму, а не по словам: «да» — задачу решает этот
шаблон тем же способом; «нет» — шаблон о другом; «спорно» — приём тот же,
но вопрос или ограничение в корпусе шире. Спорные в оценку идут половиной.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

TOPICS = PROJECT_ROOT / "data" / "source_index" / "topics.json"
VERDICTS = PROJECT_ROOT / "data" / "source_index" / "coverage_verdicts.json"

# Вердикт → вес задачи в поправленном покрытии.
WEIGHT = {"да": 1.0, "спорно": 0.5, "нет": 0.0}


def load_tasks() -> list[dict]:
    """Задачи с автоматической разметкой покрытия."""
    if not TOPICS.exists():
        raise SystemExit("Нет data/source_index/topics.json — сначала "
                         "python3 tools/classify_corpus_v2.py")
    return json.loads(TOPICS.read_text(encoding="utf-8"))["tasks"]


def load_verdicts() -> dict[str, str]:
    """Ранее проставленные вердикты: номер задачи v2 → вердикт."""
    if not VERDICTS.exists():
        return {}
    return json.loads(VERDICTS.read_text(encoding="utf-8"))["verdicts"]


def save_verdicts(verdicts: dict[str, str]) -> None:
    """Записать вердикты, отсортировав по номеру задачи."""
    ordered = {key: verdicts[key] for key in sorted(verdicts, key=int)}
    VERDICTS.write_text(
        json.dumps({"verdicts": ordered}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")


def sample_output(template_id: str) -> str:
    """Что шаблон печатает на самом деле — одна выдача с постоянной жеребьёвкой."""
    library = {template["template_id"]: template for template in load_library()}
    template = library.get(template_id)
    if template is None:
        return "<шаблона нет в библиотеке>"
    try:
        return generate_active_template(template, random.Random(1))["rendered_problem"]
    except Exception as error:  # noqa: BLE001 — устойчивость проверяют другие тесты
        return f"<шаблон не разыгрался: {error}>"


def show(tasks: list[dict], verdicts: dict[str, str], count: int, seed: int) -> None:
    """Показать пары, которых ещё нет в вердиктах."""
    pending = [task for task in tasks
                if task["covered"] and str(task["v2"]) not in verdicts]
    if not pending:
        print("Все помеченные покрытыми задачи уже сверены.")
        return
    chosen = random.Random(seed).sample(pending, min(count, len(pending)))
    for task in sorted(chosen, key=lambda item: item["v2"]):
        print(f"\n=== v2 {task['v2']}  (совпадение {task['score']}) "
              f"→ {task['template']}")
        print(f"  КОРПУС : {task['text'][:300]}")
        print(f"  ШАБЛОН : {sample_output(task['template'])[:300]}")
    print(f"\nНепроверенных осталось: {len(pending)}. "
          f"Вердикты: python3 tools/verify_coverage.py --record "
          f"{chosen[0]['v2']}=да ...")


def show_missing(tasks: list[dict], verdicts: dict[str, str], count: int,
                 seed: int) -> None:
    """Показать задачи, которые автомат счёл непокрытыми.

    Пары тут нет: сверять не с чем. Вердикт «да» означает, что подходящий
    шаблон в библиотеке всё-таки есть, просто слова разошлись.
    """
    pending = [task for task in tasks
               if not task["covered"] and str(task["v2"]) not in verdicts]
    if not pending:
        print("Все непокрытые задачи уже сверены.")
        return
    chosen = random.Random(seed).sample(pending, min(count, len(pending)))
    for task in sorted(chosen, key=lambda item: item["v2"]):
        print(f"\n=== v2 {task['v2']}  (лучшее совпадение {task['score']}, "
              f"тема по признакам: {task['module']})")
        print(f"  {task['text'][:300]}")
    print(f"\nНепроверенных непокрытых осталось: {len(pending)}.")


def record(pairs: list[str], verdicts: dict[str, str]) -> None:
    """Записать вердикты вида 291=нет."""
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Ожидается вид «номер=вердикт», получено {pair!r}")
        number, verdict = pair.split("=", 1)
        if verdict not in WEIGHT:
            raise SystemExit(f"Вердикт должен быть да/нет/спорно, получено {verdict!r}")
        verdicts[number.strip()] = verdict
    save_verdicts(verdicts)
    print(f"Записано вердиктов: {len(pairs)}. Всего накоплено: {len(verdicts)}.")


def report(tasks: list[dict], verdicts: dict[str, str]) -> None:
    """Поправленное покрытие по накопленным вердиктам."""
    total = len(tasks)
    flagged = [task for task in tasks if task["covered"]]
    checked = [task for task in flagged if str(task["v2"]) in verdicts]
    print(f"Задач в корпусе: {total}")
    print(f"Помечено покрытыми автоматом: {len(flagged)} "
          f"({100 * len(flagged) / total:.1f}%)")
    if not checked:
        print("Сверенных вручную пока нет — оценке верить нельзя.")
        return

    weights = [WEIGHT[verdicts[str(task["v2"])]] for task in checked]
    precision = sum(weights) / len(weights)
    # Границы по выборке: две ошибки среднего, как обычно берут для доли.
    spread = math.sqrt(precision * (1 - precision) / len(weights))
    low, high = max(0.0, precision - 2 * spread), min(1.0, precision + 2 * spread)

    print(f"Сверено вручную: {len(checked)}")
    print(f"Из них попадание: {100 * precision:.0f}% "
          f"(границы {100 * low:.0f}–{100 * high:.0f}%)")
    # Обратная ошибка: шаблон есть, а слова разошлись, и автомат не увидел.
    missed = [task for task in tasks
              if not task["covered"] and str(task["v2"]) in verdicts]
    recovered = 0.0
    if missed:
        share = sum(WEIGHT[verdicts[str(task["v2"])]] for task in missed) / len(missed)
        recovered = (total - len(flagged)) * share
        print(f"Сверено непокрытых: {len(missed)}, из них шаблон всё же есть "
              f"у {100 * share:.0f}% → примерно {recovered:.0f} задач")

    print(f"\nПоправленное покрытие: "
          f"{100 * (len(flagged) * precision + recovered) / total:.1f}% "
          f"(границы {100 * (len(flagged) * low + recovered) / total:.1f}–"
          f"{100 * (len(flagged) * high + recovered) / total:.1f}%)")
    if not missed:
        print("Оценка снизу: непокрытые не сверялись, а среди них шаблон\n"
              "иногда всё же есть — покажите их через --show-missing.")


def main() -> None:
    """Показать пары для сверки, записать вердикты или подвести итог."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", type=int, metavar="N",
                        help="показать N ещё не сверенных пар")
    parser.add_argument("--seed", type=int, default=0,
                        help="жеребьёвка выборки, чтобы повторить показ")
    parser.add_argument("--show-missing", type=int, metavar="N",
                        dest="show_missing",
                        help="показать N задач, которые автомат счёл непокрытыми")
    parser.add_argument("--record", nargs="+", metavar="НОМЕР=ВЕРДИКТ",
                        help="записать вердикты: да, нет или спорно")
    parser.add_argument("--report", action="store_true",
                        help="поправленное покрытие по накопленным вердиктам")
    options = parser.parse_args()

    tasks = load_tasks()
    verdicts = load_verdicts()
    if options.record:
        record(options.record, verdicts)
    if options.show:
        show(tasks, verdicts, options.show, options.seed)
    if options.show_missing:
        show_missing(tasks, verdicts, options.show_missing, options.seed)
    if options.report or not (options.record or options.show
                              or options.show_missing):
        report(tasks, verdicts)


if __name__ == "__main__":
    main()
