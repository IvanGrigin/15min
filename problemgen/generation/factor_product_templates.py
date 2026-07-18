"""Генератор модуля «Множители, произведения и факториалы»."""

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "factors_products_and_factorials"
SOURCE_PATHS = (
    PROJECT_ROOT / "docs" / "09_mnozhiteli_proizvedeniya_i_faktorialy_bez_imen_i_personazhey_deduplicated.md",
    PROJECT_ROOT / "docs" / "09_mnozhiteli_proizvedeniya_i_faktorialy_s_imenami_i_personazhami_deduplicated.md",
)
TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
ACCOUNTING_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "source_accounting.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")
MAX_ATTEMPTS = 100


class FactorProductTemplateError(ValueError):
    """Ошибка каталога, параметров или генерации модуля 09."""


@dataclass(frozen=True)
class GeneratedFactorProductProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None


def source_factor_product_problem_numbers(paths: tuple[Path, ...] = SOURCE_PATHS) -> set[int]:
    return {
        int(match.group(1))
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := NUMBERED_LINE_RE.match(line))
    }


@lru_cache(maxsize=6)
def _load_json(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _payload(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return _load_json(str(resolved), resolved.stat().st_mtime_ns)


def load_factor_product_templates(path: str | Path = TEMPLATE_PATH) -> list[dict[str, Any]]:
    templates = _payload(Path(path)).get("templates")
    if not isinstance(templates, list) or not templates:
        raise FactorProductTemplateError("В каталоге модуля 09 отсутствует templates.")
    validate_factor_product_catalog(templates)
    return list(templates)


def load_factor_product_accounting(path: str | Path = ACCOUNTING_PATH) -> list[dict[str, Any]]:
    records = _payload(Path(path)).get("records")
    if not isinstance(records, list) or not records:
        raise FactorProductTemplateError("В manifest модуля 09 отсутствует records.")
    return list(records)


def validate_factor_product_catalog(templates: list[dict[str, Any]]) -> None:
    required = {
        "id", "module", "title", "source_problem_numbers", "render_template",
        "generation_strategy", "answer_type", "uses_characters",
        "required_character_count", "active",
    }
    template_ids: set[str] = set()
    active_sources: list[int] = []
    for template in templates:
        missing = required - set(template)
        if missing:
            raise FactorProductTemplateError(f"У шаблона отсутствуют поля {sorted(missing)}: {template!r}")
        template_id = str(template["id"])
        if template_id in template_ids:
            raise FactorProductTemplateError(f"Повторяющийся template id: {template_id}")
        template_ids.add(template_id)
        if template["module"] != MODULE_ID or template["answer_type"] != "integer" or not template["active"]:
            raise FactorProductTemplateError(f"Нарушен runtime-контракт шаблона {template_id}.")
        if template["uses_characters"] or template["required_character_count"] != 0:
            raise FactorProductTemplateError(f"В character-free модуле обнаружены роли: {template_id}.")
        if template["generation_strategy"] not in STRATEGIES:
            raise FactorProductTemplateError(f"Стратегия не зарегистрирована: {template['generation_strategy']}")
        active_sources.extend(int(number) for number in template["source_problem_numbers"])

    records = load_factor_product_accounting()
    record_numbers = [int(record["source_problem_number"]) for record in records]
    source_numbers = source_factor_product_problem_numbers()
    duplicates = sorted(number for number, count in Counter(record_numbers).items() if count > 1)
    if set(record_numbers) != source_numbers or duplicates:
        raise FactorProductTemplateError(
            f"Нарушен source accounting: missing={sorted(source_numbers-set(record_numbers))}, "
            f"extra={sorted(set(record_numbers)-source_numbers)}, duplicates={duplicates}"
        )
    active_manifest = {
        int(record["source_problem_number"]): record.get("template_id")
        for record in records if record.get("status") == "active_template"
    }
    if set(active_sources) != set(active_manifest) or len(active_sources) != len(set(active_sources)):
        raise FactorProductTemplateError("Активные источники templates и manifest не совпадают.")
    for number, template_id in active_manifest.items():
        if template_id not in template_ids:
            raise FactorProductTemplateError(f"Источник {number} ссылается на неизвестный шаблон {template_id}.")
    allowed_exclusions = {
        "excluded_non_integer_answer", "excluded_ambiguous_or_non_unique",
        "excluded_requires_missing_diagram",
    }
    for record in records:
        if record.get("status") != "active_template":
            if record.get("status") not in allowed_exclusions or not str(record.get("exclusion_reason", "")).strip():
                raise FactorProductTemplateError(f"Нет точной причины исключения: {record!r}")


def factor_product_template_metadata() -> dict[str, Any]:
    templates = load_factor_product_templates()
    return {
        "modules": [{
            "module_id": MODULE_ID,
            "title": "Factors, Products and Factorials",
            "display_name": "Множители, произведения и факториалы",
            "template_count": len(templates),
            "covered_source_problem_numbers": len(source_factor_product_problem_numbers()),
        }],
        "templates": [{
            "template_id": template["id"],
            "title": template["title"],
            "display_name": template["title"],
            "module_name": "Множители, произведения и факториалы",
            "source_problem_numbers": template["source_problem_numbers"],
            "problem_type": template["generation_strategy"],
        } for template in templates],
        "stats": {
            "total_modules": 1,
            "total_templates": len(templates),
            "covered_source_problem_numbers": len(source_factor_product_problem_numbers()),
        },
    }


def get_factor_product_template(template_id: str) -> dict[str, Any]:
    for template in load_factor_product_templates():
        if template["id"] == template_id:
            return template
    raise FactorProductTemplateError(f"Неизвестный шаблон модуля 09: {template_id}")


def factor_pairs(target_product: int) -> list[tuple[int, int]]:
    if target_product < 1:
        raise FactorProductTemplateError("Произведение должно быть натуральным.")
    return [
        (divisor, target_product // divisor)
        for divisor in range(1, math.isqrt(target_product) + 1)
        if target_product % divisor == 0
    ]


def minimum_factor_sum(target_product: int, restriction: str) -> int:
    predicates: dict[str, Callable[[int, int], bool]] = {
        "any": lambda left, right: True,
        "one_odd": lambda left, right: left % 2 == 1 or right % 2 == 1,
        "both_even": lambda left, right: left % 2 == 0 and right % 2 == 0,
        "both_odd": lambda left, right: left % 2 == 1 and right % 2 == 1,
        "without_zero_digits": lambda left, right: "0" not in str(left) and "0" not in str(right),
    }
    if restriction not in predicates:
        raise FactorProductTemplateError(f"Неизвестное ограничение множителей: {restriction}")
    sums = [left + right for left, right in factor_pairs(target_product) if predicates[restriction](left, right)]
    return min(sums) if sums else -1


def trailing_zeros_of_product(start_value: int, end_value: int) -> int:
    if start_value < 1 or end_value < start_value:
        raise FactorProductTemplateError("Некорректные границы произведения.")

    def valuation(number: int, prime: int) -> int:
        result = 0
        while number % prime == 0:
            result += 1
            number //= prime
        return result

    twos = sum(valuation(number, 2) for number in range(start_value, end_value + 1))
    fives = sum(valuation(number, 5) for number in range(start_value, end_value + 1))
    return min(twos, fives)


def _make(template: dict[str, Any], text: str, answer: int, parameters: dict[str, Any], seed: int | None) -> GeneratedFactorProductProblem:
    if "{" in text or "}" in text:
        raise FactorProductTemplateError(f"В тексте {template['id']} остались плейсхолдеры.")
    if not isinstance(answer, int):
        raise FactorProductTemplateError(f"Ответ {template['id']} не является целым числом.")
    return GeneratedFactorProductProblem(
        MODULE_ID, str(template["id"]), list(template["source_problem_numbers"]),
        text, answer, str(answer), parameters, seed,
    )


def _factor_target(rng: random.Random, restriction: str) -> int:
    if restriction == "both_even":
        left, right = 2 * rng.randint(2, 35), 2 * rng.randint(2, 35)
    elif restriction == "both_odd":
        left, right = 2 * rng.randint(1, 35) + 1, 2 * rng.randint(1, 35) + 1
    elif restriction == "one_odd":
        left, right = 2 * rng.randint(1, 35) + 1, rng.randint(2, 70)
    elif restriction == "without_zero_digits":
        allowed = [number for number in range(2, 100) if "0" not in str(number)]
        left, right = rng.choice(allowed), rng.choice(allowed)
    else:
        left, right = rng.randint(2, 80), rng.randint(2, 80)
    return left * right


def _factor_problem(template: dict[str, Any], rng: random.Random, seed: int | None, restriction: str) -> GeneratedFactorProductProblem:
    target = _factor_target(rng, restriction)
    answer = minimum_factor_sum(target, restriction)
    if answer < 0:
        raise FactorProductTemplateError("Сконструированное произведение не имеет допустимой пары.")
    qualifiers = {
        "any": "",
        "one_odd": ", хотя бы один из которых нечётный",
        "both_even": ", оба из которых чётные",
        "both_odd": ", оба из которых нечётные",
        "without_zero_digits": ", в записи каждого из которых нет цифры 0",
    }
    text = f"Представьте число {target} в виде произведения двух натуральных сомножителей{qualifiers[restriction]}. Найдите минимальную возможную сумму сомножителей."
    return _make(template, text, answer, {"target_product": target, "factor_restriction": restriction}, seed)


def _factorial(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedFactorProductProblem:
    argument = rng.randint(5, 20)
    answer = math.factorial(argument)
    independent = math.prod(range(1, argument + 1))
    if answer != independent:
        raise FactorProductTemplateError("Факториал не прошёл независимую проверку.")
    return _make(template, f"Вычислите {argument}!.", answer, {"factorial_argument": argument}, seed)


def _trailing_zeros(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedFactorProductProblem:
    start = rng.randint(2, 20)
    end = start + rng.randint(10, 30)
    answer = trailing_zeros_of_product(start, end)
    direct_product = math.prod(range(start, end + 1))
    direct = len(str(direct_product)) - len(str(direct_product).rstrip("0"))
    if answer != direct:
        raise FactorProductTemplateError("Число конечных нулей не прошло независимую проверку.")
    text = f"Сколько нулей будет в конце произведения {start} · {start + 1} · … · {end}?"
    return _make(template, text, answer, {"start_value": start, "next_value": start + 1, "end_value": end}, seed)


Strategy = Callable[[dict[str, Any], random.Random, int | None], GeneratedFactorProductProblem]
STRATEGIES: dict[str, Strategy] = {
    "factor_pair_min_sum_any": lambda template, rng, seed: _factor_problem(template, rng, seed, "any"),
    "factor_pair_min_sum_one_odd": lambda template, rng, seed: _factor_problem(template, rng, seed, "one_odd"),
    "factor_pair_min_sum_both_even": lambda template, rng, seed: _factor_problem(template, rng, seed, "both_even"),
    "factor_pair_min_sum_both_odd": lambda template, rng, seed: _factor_problem(template, rng, seed, "both_odd"),
    "factor_pair_min_sum_without_zero_digits": lambda template, rng, seed: _factor_problem(template, rng, seed, "without_zero_digits"),
    "factorial_value": _factorial,
    "trailing_zeros_consecutive_product": _trailing_zeros,
}


def generate_factor_product_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedFactorProductProblem:
    template = get_factor_product_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy = STRATEGIES[str(template["generation_strategy"])]
    failures: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        try:
            return strategy(template, local_rng, seed)
        except FactorProductTemplateError as error:
            failures.append(str(error))
    raise FactorProductTemplateError(
        f"Не удалось сгенерировать template_id={template_id}, seed={seed} "
        f"за {MAX_ATTEMPTS} попыток: {failures[-3:]}"
    )


def generate_factor_product_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedFactorProductProblem:
    if module_id != MODULE_ID:
        raise FactorProductTemplateError(f"Неизвестный модуль: {module_id}")
    template = rng.choice(load_factor_product_templates())
    return generate_factor_product_problem(str(template["id"]), rng=rng)
