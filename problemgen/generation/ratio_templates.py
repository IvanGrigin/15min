"""Детерминированный генератор отношений, долей, пропорций и процентов."""

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from problemgen.generation.comparison_templates import Character, load_approved_characters
from problemgen.russian.agreement import count_with_word_ru, pluralize_ru


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "ratios_fractions_proportions_and_percentages"
MODULE_TITLE = "Ratios, Fractions, Proportions and Percentages"
MODULE_DISPLAY_NAME = "Отношения, доли, пропорции и проценты"
SOURCE_PATHS = (
    PROJECT_ROOT / "docs" / "10_otnosheniya_doli_proportsii_i_protsenty_bez_imen_i_personazhey_deduplicated.md",
    PROJECT_ROOT / "docs" / "10_otnosheniya_doli_proportsii_i_protsenty_s_imenami_i_personazhami_deduplicated.md",
)
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
DEFAULT_ACCOUNTING_PATH = DEFAULT_TEMPLATE_PATH.with_name("source_accounting.json")
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")
MAX_ATTEMPTS = 80


class RatioTemplateError(ValueError):
    """Ошибка каталога или ограниченной генерации модуля."""


@dataclass(frozen=True)
class GeneratedRatioProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None
    universe: str | None = None
    characters: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "module": self.module,
            "template_id": self.template_id,
            "source_problem_numbers": self.source_problem_numbers,
            "problem_text": self.problem_text,
            "answer": self.answer,
            "answer_text": self.answer_text,
            "parameters": self.parameters,
            "seed": self.seed,
        }
        if self.universe is not None:
            result["universe"] = self.universe
        if self.characters is not None:
            result["characters"] = self.characters
        return result


def source_ratio_problem_numbers(paths: tuple[Path, ...] = SOURCE_PATHS) -> set[int]:
    return {
        int(match.group(1))
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := NUMBERED_LINE_RE.match(line))
    }


@lru_cache(maxsize=4)
def _load_json(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_ratio_templates(path: str | Path = DEFAULT_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    templates = _load_json(str(resolved), resolved.stat().st_mtime_ns).get("templates")
    if not isinstance(templates, list) or not templates:
        raise RatioTemplateError("В каталоге модуля нет непустого списка templates.")
    validate_ratio_catalog(templates)
    return list(templates)


def load_source_accounting(path: str | Path = DEFAULT_ACCOUNTING_PATH) -> dict[str, Any]:
    resolved = Path(path).resolve()
    payload = _load_json(str(resolved), resolved.stat().st_mtime_ns)
    records = payload.get("records")
    if not isinstance(records, list):
        raise RatioTemplateError("В source_accounting.json нет списка records.")
    return payload


def validate_ratio_catalog(templates: list[dict[str, Any]]) -> None:
    required = {
        "id", "module", "source_problem_numbers", "render_template",
        "generation_strategy", "answer_type", "uses_characters",
        "required_character_count", "active",
    }
    ids: list[str] = []
    covered: list[int] = []
    for template in templates:
        missing = required - set(template)
        if missing:
            raise RatioTemplateError(f"У шаблона отсутствуют поля {sorted(missing)}: {template!r}")
        template_id = str(template["id"])
        ids.append(template_id)
        covered.extend(int(number) for number in template["source_problem_numbers"])
        if template["module"] != MODULE_ID or template["answer_type"] != "integer":
            raise RatioTemplateError(f"Неверные module/answer_type у {template_id}.")
        if not template["active"]:
            raise RatioTemplateError(f"Runtime-каталог не должен содержать неактивный шаблон {template_id}.")
        if template["generation_strategy"] not in STRATEGIES:
            raise RatioTemplateError(f"Не зарегистрирована стратегия {template['generation_strategy']} ({template_id}).")
        expected_count = int(template["required_character_count"])
        if bool(template["uses_characters"]) != (expected_count > 0):
            raise RatioTemplateError(f"Несогласованные character-поля у {template_id}.")
    if len(ids) != len(set(ids)):
        raise RatioTemplateError("ID runtime-шаблонов повторяются.")
    accounting = load_source_accounting()
    records = accounting["records"]
    numbers = [int(record["source_problem_number"]) for record in records]
    if len(numbers) != len(set(numbers)) or set(numbers) != source_ratio_problem_numbers():
        raise RatioTemplateError("Manifest не покрывает каждый уникальный источник ровно один раз.")
    active_by_id = {template["id"]: set(template["source_problem_numbers"]) for template in templates}
    manifest_active: dict[str, set[int]] = {template_id: set() for template_id in active_by_id}
    for record in records:
        status = record.get("status")
        if status == "active_template":
            template_id = record.get("template_id")
            if template_id not in active_by_id:
                raise RatioTemplateError(f"Manifest ссылается на неизвестный шаблон: {template_id}.")
            manifest_active[str(template_id)].add(int(record["source_problem_number"]))
        elif status not in {
            "excluded_non_integer_answer", "excluded_ambiguous_or_non_unique",
            "excluded_requires_missing_diagram",
        } or not str(record.get("reason", "")).strip():
            raise RatioTemplateError(f"Некорректная исключённая запись: {record!r}")
    if manifest_active != active_by_id or set(covered) != {n for values in manifest_active.values() for n in values}:
        raise RatioTemplateError("Покрытие runtime-каталога не совпадает с manifest.")


def get_ratio_template(template_id: str) -> dict[str, Any]:
    for template in load_ratio_templates():
        if template["id"] == template_id:
            return template
    raise RatioTemplateError(f"Неизвестный шаблон {template_id}.")


def _characters(rng: random.Random, count: int) -> tuple[str, list[Character]]:
    eligible = [(universe, values) for universe, values in load_approved_characters().items() if len(values) >= count]
    universe, values = rng.choice(eligible)
    return universe, rng.sample(values, count)


def _make(
    template: dict[str, Any], text: str, answer: int, parameters: dict[str, Any], seed: int | None,
    universe: str | None = None, characters: list[Character] | None = None,
) -> GeneratedRatioProblem:
    if not isinstance(answer, int) or isinstance(answer, bool):
        raise RatioTemplateError("Независимый решатель вернул не целое число.")
    if "{" in text or "}" in text:
        raise RatioTemplateError("В условии остались незаполненные placeholders.")
    return GeneratedRatioProblem(
        MODULE_ID, str(template["id"]), list(template["source_problem_numbers"]), text,
        answer, str(answer), parameters, seed, universe,
        [character.name for character in characters] if characters else None,
    )


def solve_distinct_positive_parts(total: int) -> int:
    if total < 1:
        raise RatioTemplateError("total должен быть положительным.")
    count = (math.isqrt(8 * total + 1) - 1) // 2
    while (count + 1) * (count + 2) // 2 <= total:
        count += 1
    return count


def solve_repeated_halving(initial: int, threshold: int) -> int:
    if initial <= 0 or threshold <= 0:
        raise RatioTemplateError("Начальное значение и порог должны быть положительными.")
    days = 0
    remaining = initial
    while remaining >= threshold:
        remaining //= 2
        days += 1
    return days


def _distinct_parts(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    expected = rng.randint(4, 14)
    total = expected * (expected + 1) // 2 + rng.randint(0, expected)
    answer = solve_distinct_positive_parts(total)
    text = f"{count_with_word_ru(total, ('орех', 'ореха', 'орехов'))} разложили по нескольким тарелкам: на каждой есть хотя бы один орех, а количества на любых двух тарелках различны. Какое наибольшее число тарелок могло быть?"
    return _make(t, text, answer, {"total_items": total}, seed)


def _doubling_half(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    full_time = rng.randint(5, 40)
    period = rng.choice(["минуту", "день"])
    text = f"Количество объектов удваивается каждую {period}. Полный объём достигается за {full_time} периодов. Через сколько периодов была достигнута половина объёма?"
    return _make(t, text, full_time - 1, {"full_time": full_time, "growth_factor": 2}, seed)


def _triangular_suffix(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    original_count = rng.randint(10, 80)
    added_count = rng.randint(2, 6)
    hypothetical_count = original_count + added_count
    hypothetical_total = hypothetical_count * (hypothetical_count + 1) // 2
    answer = original_count * (original_count + 1) // 2
    text = f"В первой коробке лежит 1 предмет, во второй — 2, в третьей — 3 и так далее. Если бы коробок было на {added_count} больше, всего было бы {count_with_word_ru(hypothetical_total, ('предмет', 'предмета', 'предметов'))}. Сколько предметов лежит в имеющихся коробках?"
    return _make(t, text, answer, {"added_count": added_count, "hypothetical_total": hypothetical_total, "original_count": original_count}, seed)


def _three_boxes(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    third = rng.randint(2, 40)
    first_shortfall = rng.randint(2, 30)
    second_shortfall = first_shortfall + 2 * third
    text = f"В трёх ящиках лежат орехи. В первом на {first_shortfall} кг меньше, чем в двух других вместе, а во втором на {second_shortfall} кг меньше, чем в двух других вместе. Сколько килограммов орехов в третьем ящике?"
    answer = (second_shortfall - first_shortfall) // 2
    if 2 * answer != second_shortfall - first_shortfall:
        raise RatioTemplateError("Разность дефицитов должна быть чётной.")
    return _make(t, text, answer, {"first_shortfall": first_shortfall, "second_shortfall": second_shortfall}, seed)


def _fraction_percentage(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    denominator = rng.choice([2, 4, 5, 10])
    percent = rng.choice([50, 75, 100, 125, 150, 200, 250, 300])
    numerator = percent * denominator
    if numerator % 100:
        raise RatioTemplateError("Процент не образует целую долю.")
    numerator //= 100
    text = f"Сколько процентов составляет {numerator}/{denominator} одной и той же положительной величины от целой величины?"
    answer = numerator * 100 // denominator
    return _make(t, text, answer, {"numerator": numerator, "denominator": denominator}, seed)


def _transfer_shares(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    universe, chars = _characters(rng, 3)
    ratio = rng.randint(3, 7)
    unit = rng.randint(2, 12)
    first, second, third = (ratio - 1) * unit, 2 * unit, (ratio + 1) * unit
    total = first + second + third
    if second + first != third or third + first != ratio * second:
        raise RatioTemplateError("Передачи не удовлетворяют обеим зависимостям.")
    a, b, c = (character.name for character in chars)
    candy_word = pluralize_ru(total, ("конфета", "конфеты", "конфет"))
    ratio_word = pluralize_ru(ratio, ("раз", "раза", "раз"))
    text = f"{a}, {b} и {c} разделили {total} {candy_word}. Если первый участник отдаст все свои конфеты второму, у второго и третьего станет поровну. Если первый отдаст всё третьему, у третьего станет в {ratio} {ratio_word} больше, чем у второго. Сколько конфет было у первого участника?"
    solved = total * (ratio - 1) // (2 * (ratio + 1))
    if solved != first or total * (ratio - 1) % (2 * (ratio + 1)):
        raise RatioTemplateError("Обратное решение распределения не совпало.")
    return _make(t, text, solved, {"total_amount": total, "ratio": ratio, "role_mapping": {"first": a, "second": b, "third": c}}, seed, universe, chars)


def _repeated_halving(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    threshold = rng.randint(3, 20)
    expected_days = rng.randint(3, 9)
    initial = threshold * (2 ** (expected_days - 1)) + rng.randint(0, threshold - 1)
    answer = solve_repeated_halving(initial, threshold)
    text = f"В группе {count_with_word_ru(initial, ('человек', 'человека', 'человек'))}. Каждый день после события остаётся не более половины ещё не затронутых. На какой день уже точно останется меньше {count_with_word_ru(threshold, ('человека', 'человек', 'человек'))}?"
    return _make(t, text, answer, {"initial_count": initial, "threshold": threshold}, seed)


def _smallest_same_weekday_gap(year: int, month: int, day: int) -> int:
    weekday = date(year, month, day).weekday()
    for gap in range(1, 41):
        try:
            if date(year + gap, month, day).weekday() == weekday:
                return gap
        except ValueError:
            continue
    raise RatioTemplateError("Не найден повтор дня недели в ограниченном диапазоне.")


def _same_weekday(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    universe, chars = _characters(rng, 2)
    year = rng.randint(2001, 2030)
    month, day = rng.choice([(1, 15), (3, 12), (5, 23), (7, 17), (9, 8), (11, 19)])
    answer = _smallest_same_weekday_gap(year, month, day)
    first, second = (character.name for character in chars)
    text = f"{first} и {second} родились {day:02d}.{month:02d} в один и тот же день недели, но в разные годы. Если первый год — {year}, какова наименьшая возможная разница между годами?"
    return _make(t, text, answer, {"year": year, "month": month, "day": day, "role_mapping": {"first": first, "second": second}}, seed, universe, chars)


def _successive_remainder(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    last_distance = rng.randint(8, 40)
    # Обратный ход: перед третьим днём остаток кратен 4, перед вторым — 2, перед первым — 5.
    third_extra = rng.choice([value for value in range(1, 7) if (last_distance + value) * 4 % 3 == 0])
    after_second = (last_distance + third_extra) * 4 // 3
    if (last_distance + third_extra) * 4 % 3:
        raise RatioTemplateError("Третий обратный шаг нецелый.")
    second_extra = rng.randint(1, 5)
    after_first = (after_second + second_extra) * 2
    first_extra = rng.choice([value for value in range(1, 9) if (after_first + value) * 5 % 4 == 0])
    total = (after_first + first_extra) * 5 // 4
    if (after_first + first_extra) * 5 % 4:
        raise RatioTemplateError("Первый обратный шаг нецелый.")
    remaining = total - (total // 5 + first_extra)
    remaining -= remaining // 2 + second_extra
    remaining -= remaining // 4 + third_extra
    if total % 5 or remaining != last_distance:
        raise RatioTemplateError("Прямой независимый проход не совпал.")
    text = f"В первый день путешественник прошёл пятую часть пути и ещё {first_extra} км. Во второй — половину остатка и ещё {second_extra} км. В третий — четверть нового остатка и ещё {third_extra} км. На четвёртый день осталось {last_distance} км. Какова длина пути?"
    return _make(t, text, total, {"first_extra": first_extra, "second_extra": second_extra, "third_extra": third_extra, "last_distance": last_distance}, seed)


def _flock_equation(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    flock = 4 * rng.randint(8, 60)
    target = flock + flock + flock // 2 + flock // 4 + 1
    text = f"Лебедь встретил стаю. Если к стае добавить ещё столько же птиц, ещё половину и четверть её числа, а также самого лебедя, получится {target}. Сколько птиц было в стае?"
    solved_numerator = (target - 1) * 4
    if solved_numerator % 11:
        raise RatioTemplateError("Уравнение стаи не имеет целого решения.")
    return _make(t, text, solved_numerator // 11, {"target_total": target}, seed)


def _box_conservation(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    universe, chars = _characters(rng, 2)
    initial = [rng.randint(100, 3000) for _ in range(3)]
    total = sum(initial)
    final_first = rng.randint(1, total // 4)
    final_second = rng.randint(1, total // 3)
    answer = total - final_first - final_second
    if answer <= 0:
        raise RatioTemplateError("Третий остаток должен быть положительным.")
    first, second = chars
    first_verb = "переложила" if first.gender == "feminine" else "переложил"
    second_verb = "проверила" if second.gender == "feminine" else "проверил"
    text = f"В трёх ящиках было {initial[0]}, {initial[1]} и {initial[2]} деталей. {first.name} {first_verb} детали между ящиками, ничего не потеряв. {second.name} {second_verb}: в первом стало {final_first}, во втором — {final_second}. Сколько деталей стало в третьем?"
    return _make(t, text, answer, {"initial_counts": initial, "final_first": final_first, "final_second": final_second, "role_mapping": {"mover": first.name, "checker": second.name}}, seed, universe, chars)


def _percentage_threshold(t: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedRatioProblem:
    percent = rng.randint(51, 98)
    # Для минимального состава меньшая непустая группа состоит из одного человека.
    answer = next(total for total in range(2, 1001) if (total - 1) * 100 > percent * total)
    text = f"В кружке есть участники двух групп, причём большая группа составляет больше {percent}% состава. Какое минимальное число людей может быть в кружке?"
    return _make(t, text, answer, {"minimum_minority_count": 1, "percent_threshold": percent}, seed)


Strategy = Callable[[dict[str, Any], random.Random, int | None], GeneratedRatioProblem]
STRATEGIES: dict[str, Strategy] = {
    "distinct_positive_parts": _distinct_parts,
    "doubling_half_time": _doubling_half,
    "triangular_suffix": _triangular_suffix,
    "three_box_differences": _three_boxes,
    "fraction_percentage": _fraction_percentage,
    "transfer_shares": _transfer_shares,
    "repeated_halving_bound": _repeated_halving,
    "same_weekday_birthday": _same_weekday,
    "successive_remainder": _successive_remainder,
    "flock_ratio_equation": _flock_equation,
    "box_conservation": _box_conservation,
    "percentage_threshold": _percentage_threshold,
}


def generate_ratio_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedRatioProblem:
    template = get_ratio_template(template_id)
    local = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy = STRATEGIES[str(template["generation_strategy"])]
    failures: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        try:
            return strategy(template, local, seed)
        except (RatioTemplateError, ValueError) as error:
            failures.append(str(error))
    detail = failures[-1] if failures else "нет диагностических данных"
    raise RatioTemplateError(f"Не удалось сгенерировать template={template_id}, seed={seed}: {detail}")


def generate_ratio_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedRatioProblem:
    if module_id != MODULE_ID:
        raise RatioTemplateError(f"Неизвестный модуль: {module_id}")
    return generate_ratio_problem(str(rng.choice(load_ratio_templates())["id"]), rng=rng)


def ratio_template_metadata() -> dict[str, Any]:
    templates = load_ratio_templates()
    return {
        "modules": [{"module_id": MODULE_ID, "title": MODULE_TITLE, "display_name": MODULE_DISPLAY_NAME, "template_count": len(templates)}],
        "templates": [{"template_id": t["id"], "title": t["title"], "display_name": t["title"], "module_name": MODULE_DISPLAY_NAME, "source_problem_numbers": t["source_problem_numbers"], "problem_type": t["generation_strategy"]} for t in templates],
        "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_ratio_problem_numbers()), "source_file": "docs/10a + docs/10b deduplicated"},
    }
