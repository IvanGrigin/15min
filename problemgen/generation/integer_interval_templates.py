"""Генератор задач модуля «Подсчёт целых чисел в промежутках»."""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "docs" / "06_podschet_tselyh_chisel_v_promezhutkah.md"
DEFAULT_INTERVAL_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "integer_interval_counting" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+.+?\s*$")
MAX_ATTEMPTS = 100
PARITY_WORDS = {"odd": "нечётных", "even": "чётных"}


class IntegerIntervalTemplateError(ValueError):
    """Понятная ошибка каталога или генерации задач о промежутках."""


@dataclass(frozen=True)
class GeneratedIntegerIntervalProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None


def source_integer_interval_problem_numbers(path: Path = SOURCE_PATH) -> set[int]:
    return {int(match.group(1)) for line in path.read_text(encoding="utf-8").splitlines() if (match := NUMBERED_LINE_RE.match(line))}


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_integer_interval_templates(path: str | Path = DEFAULT_INTERVAL_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    templates = _load_payload(str(resolved), resolved.stat().st_mtime_ns).get("templates")
    if not isinstance(templates, list) or not templates:
        raise IntegerIntervalTemplateError("В integer interval problem set отсутствует templates.")
    validate_integer_interval_catalog(templates)
    return list(templates)


def validate_integer_interval_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    numbers: list[int] = []
    for template in templates:
        for field in ("id", "module_id", "source_problem_numbers", "generation_strategy", "interval_type"):
            if field not in template:
                raise IntegerIntervalTemplateError(f"У шаблона отсутствует {field}.")
        if template["id"] in ids or template["module_id"] != "integer_interval_counting":
            raise IntegerIntervalTemplateError(f"Некорректный шаблон {template['id']}.")
        ids.add(template["id"])
        numbers.extend(int(number) for number in template["source_problem_numbers"])
    source = source_integer_interval_problem_numbers()
    if set(numbers) != source or len(numbers) != len(set(numbers)):
        raise IntegerIntervalTemplateError(f"Покрытие источника нарушено: missing={sorted(source - set(numbers))}, extra={sorted(set(numbers) - source)}, duplicates={sorted(number for number, amount in Counter(numbers).items() if amount > 1)}")


def integer_interval_template_metadata() -> dict[str, Any]:
    templates = load_integer_interval_templates()
    return {"modules": [{"module_id": "integer_interval_counting", "title": "Counting Integers in Intervals", "display_name": "Подсчёт целых чисел в промежутках", "template_count": len(templates), "covered_source_problem_numbers": len(source_integer_interval_problem_numbers())}], "templates": [{"template_id": item["id"], "title": item["title"], "display_name": item["title"], "module_name": "Подсчёт целых чисел в промежутках", "source_problem_numbers": item["source_problem_numbers"], "problem_type": item["problem_type"]} for item in templates], "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_integer_interval_problem_numbers())}}


def get_integer_interval_template(template_id: str) -> dict[str, Any]:
    for template in load_integer_interval_templates():
        if template["id"] == template_id:
            return template
    raise IntegerIntervalTemplateError(f"Неизвестный шаблон подсчёта промежутков: {template_id}.")


def count_even_inclusive(lower: int, upper: int) -> int:
    if lower > upper:
        raise IntegerIntervalTemplateError("Нижняя граница больше верхней.")
    return upper // 2 - (lower - 1) // 2


def count_parity_inclusive(lower: int, upper: int, parity: str) -> int:
    even = count_even_inclusive(lower, upper)
    return even if parity == "even" else upper - lower + 1 - even


def count_parity_with_digit(lower: int, upper: int, parity: str, digit: int) -> int:
    if not 1 <= digit <= 9:
        raise IntegerIntervalTemplateError("Для шаблона допустимы цифры от 1 до 9.")
    return sum(number % 2 == (0 if parity == "even" else 1) and str(digit) in str(number) for number in range(lower, upper + 1))


def _make(template: dict[str, Any], text: str, answer: int, params: dict[str, Any], seed: int | None) -> GeneratedIntegerIntervalProblem:
    if "{" in text or "}" in text or not isinstance(answer, int) or answer < 0:
        raise IntegerIntervalTemplateError("Некорректный текст или ответ задачи.")
    return GeneratedIntegerIntervalProblem("integer_interval_counting", template["id"], list(template["source_problem_numbers"]), text, answer, str(answer), params, seed)


def _bounds(rng: random.Random, *, digit_condition: bool = False) -> tuple[int, int]:
    lower = rng.randint(1, 1000)
    width = rng.randint(100, 2500) if digit_condition else rng.randint(20, 2000)
    return lower, lower + width


def _inclusive_parity_count(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedIntegerIntervalProblem:
    lower, upper = _bounds(rng)
    parity = str(template["parity"])
    answer = count_parity_inclusive(lower, upper, parity)
    direct = sum(number % 2 == (0 if parity == "even" else 1) for number in range(lower, upper + 1))
    if answer != direct:
        raise IntegerIntervalTemplateError("Формула подсчёта чётности не прошла независимую проверку.")
    return _make(template, f"Сколько {PARITY_WORDS[parity]} чисел от {lower} до {upper}?", answer, {"lower_bound": lower, "upper_bound": upper, "parity": parity, "interval_type": "inclusive"}, seed)


def _exclusive_natural_count(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedIntegerIntervalProblem:
    lower = rng.randint(1, 1000)
    upper = lower + rng.randint(2, 2000)
    answer = upper - lower - 1
    if answer != len(list(range(lower + 1, upper))):
        raise IntegerIntervalTemplateError("Исключающие границы проверку не прошли.")
    return _make(template, f"Сколько натуральных чисел расположено между числами {lower} и {upper}?", answer, {"lower_bound": lower, "upper_bound": upper, "interval_type": "exclusive"}, seed)


def _inclusive_parity_digit_count(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedIntegerIntervalProblem:
    lower, upper = _bounds(rng, digit_condition=True)
    parity, digit = str(template["parity"]), rng.randint(1, 9)
    answer = count_parity_with_digit(lower, upper, parity, digit)
    if answer <= 0:
        raise IntegerIntervalTemplateError("Не найдено подходящих чисел.")
    return _make(template, f"Сколько {PARITY_WORDS[parity]} чисел от {lower} до {upper} содержат хотя бы одну цифру {digit}?", answer, {"lower_bound": lower, "upper_bound": upper, "parity": parity, "digit": digit, "interval_type": "inclusive"}, seed)


Strategy = Callable[[dict[str, Any], random.Random, int | None], GeneratedIntegerIntervalProblem]
STRATEGIES: dict[str, Strategy] = {"inclusive_parity_count": _inclusive_parity_count, "exclusive_natural_count": _exclusive_natural_count, "inclusive_parity_digit_count": _inclusive_parity_digit_count}


def generate_integer_interval_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedIntegerIntervalProblem:
    template = get_integer_interval_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy = STRATEGIES.get(str(template["generation_strategy"]))
    if strategy is None:
        raise IntegerIntervalTemplateError(f"Неизвестная стратегия {template['generation_strategy']}.")
    errors: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        try:
            return strategy(template, local_rng, seed)
        except Exception as error:  # noqa: BLE001
            errors.append(str(error))
    raise IntegerIntervalTemplateError(f"Не удалось сгенерировать {template_id} за {MAX_ATTEMPTS} попыток: {errors[-5:]}")


def generate_integer_interval_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedIntegerIntervalProblem:
    if module_id != "integer_interval_counting":
        raise IntegerIntervalTemplateError(f"Неизвестный модуль: {module_id}")
    template = rng.choice(load_integer_interval_templates())
    return generate_integer_interval_problem(str(template["id"]), rng=rng)
