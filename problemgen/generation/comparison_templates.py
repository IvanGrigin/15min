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
SOURCE_PATHS = [
    PROJECT_ROOT / "docs" / "04a_sravnenie_bez_imen_i_personazhey.md",
    PROJECT_ROOT / "docs" / "04b_sravnenie_s_imenami_i_personazhami.md",
]
CHARACTER_SOURCE_PATH = PROJECT_ROOT / "docs" / "approved_dimensions_150_characters.md"
DEFAULT_COMPARISON_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "comparison_of_numbers_and_expressions" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
UNIVERSE_ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|$")
MAX_ATTEMPTS = 100
DIGIT_WORDS = {
    1: "один",
    2: "два",
    3: "три",
    4: "четыре",
    5: "пять",
    6: "шесть",
    7: "семь",
    8: "восемь",
    9: "девять",
}
FEMININE_NAMES = {
    "Маша", "Медведица", "Даша", "Розочка", "Мальвина", "лиса Алиса", "Сова",
    "Мила", "Эльза", "Анна", "Фиона", "Гермиона Грейнджер", "Лея Органа",
    "Симка", "Мася", "Василиса", "Элизабет Суонн", "Тиа Дальма", "Джесси",
    "Бо Пип", "Нала", "Глория", "Тигрица", "Обезьяна", "Алиса", "Червонная Королева",
    "Синяя Гусеница", "Венди Дарлинг", "Динь-Динь", "Тигровая Лилия", "Элли",
}


class ComparisonTemplateError(ValueError):
    """Понятная ошибка при загрузке или генерации шаблонов сравнения."""


@dataclass(frozen=True)
class Character:
    universe: str
    name: str
    gender: str


@dataclass(frozen=True)
class GeneratedComparisonProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: dict[str, Any]
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None
    universe: str | None = None
    characters: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
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
            payload["universe"] = self.universe
        if self.characters is not None:
            payload["characters"] = self.characters
        return payload


def source_comparison_problem_numbers(paths: list[Path] | None = None) -> set[int]:
    numbers: set[int] = set()
    for path in paths or SOURCE_PATHS:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = NUMBERED_LINE_RE.match(line)
            if match:
                numbers.add(int(match.group(1)))
    return numbers


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_comparison_templates(path: str | Path = DEFAULT_COMPARISON_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    payload = _load_payload(str(resolved), resolved.stat().st_mtime_ns)
    templates = payload.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ComparisonTemplateError("В comparison problem set нет списка templates.")
    validate_comparison_catalog(templates)
    return list(templates)


def validate_comparison_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen: list[int] = []
    examples: list[str] = []
    for template in templates:
        for field in ("id", "module_id", "source_problem_numbers", "generation_strategy", "uses_characters"):
            if field not in template:
                raise ComparisonTemplateError(f"У шаблона нет поля {field}: {template!r}")
        template_id = str(template["id"])
        if template_id in ids:
            raise ComparisonTemplateError(f"Повторяющийся id шаблона: {template_id}")
        ids.add(template_id)
        if template["module_id"] != "comparison_of_numbers_and_expressions":
            raise ComparisonTemplateError(f"Неверный module_id у {template_id}: {template['module_id']}")
        seen.extend(int(number) for number in template["source_problem_numbers"])
        examples.extend(str(example) for example in template.get("source_examples", []))
    source = source_comparison_problem_numbers()
    if set(seen) != source:
        missing = sorted(source - set(seen))
        extra = sorted(set(seen) - source)
        raise ComparisonTemplateError(f"Проблема покрытия источника. missing={missing}, extra={extra}")
    duplicates = sorted(number for number, count in Counter(seen).items() if count > 1)
    if duplicates:
        raise ComparisonTemplateError(f"Номера источника встречаются дважды: {duplicates}")
    duplicate_examples = [example for example, count in Counter(examples).items() if count > 1]
    if duplicate_examples:
        raise ComparisonTemplateError(f"Повторяющиеся исходные примеры в JSON: {duplicate_examples}")


def comparison_template_metadata() -> dict[str, Any]:
    templates = load_comparison_templates()
    return {
        "modules": [{
            "module_id": "comparison_of_numbers_and_expressions",
            "title": "Comparison of Numbers and Expressions",
            "display_name": "Сравнение чисел и выражений",
            "template_count": len(templates),
            "covered_source_problem_numbers": len(source_comparison_problem_numbers()),
        }],
        "templates": [
            {
                "template_id": template["id"],
                "title": template.get("title", template["id"]),
                "display_name": template.get("title", template["id"]),
                "module_name": "Сравнение чисел и выражений",
                "source_problem_numbers": template["source_problem_numbers"],
                "problem_type": template["problem_type"],
            }
            for template in templates
        ],
        "stats": {
            "total_modules": 1,
            "total_templates": len(templates),
            "covered_source_problem_numbers": len(source_comparison_problem_numbers()),
            "source_file": "docs/04a_sravnenie_bez_imen_i_personazhey.md + docs/04b_sravnenie_s_imenami_i_personazhami.md",
        },
    }


def get_comparison_template(template_id: str) -> dict[str, Any]:
    for template in load_comparison_templates():
        if template["id"] == template_id:
            return template
    raise ComparisonTemplateError(f"Неизвестный шаблон сравнения: {template_id}.")


@lru_cache(maxsize=1)
def load_approved_characters(path: str = str(CHARACTER_SOURCE_PATH)) -> dict[str, list[Character]]:
    universes: dict[str, list[Character]] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = UNIVERSE_ROW_RE.match(line)
        if not match:
            continue
        universe = match.group(1).strip()
        names = [name.strip() for name in match.group(2).split(";")]
        universes[universe] = [Character(universe, name, _gender_for_name(name)) for name in names]
    if not universes:
        raise ComparisonTemplateError("Не удалось загрузить утверждённые вселенные и персонажей.")
    return universes


def _gender_for_name(name: str) -> str:
    if name in FEMININE_NAMES:
        return "feminine"
    if name.endswith(("а", "я")) and not name.endswith(("Илья", "Добрыня")):
        return "feminine"
    return "masculine"


def _past(character: Character, masculine: str, feminine: str) -> str:
    return feminine if character.gender == "feminine" else masculine


def _capitalize_sentence_start(name: str) -> str:
    return name[:1].upper() + name[1:]


def _choose_characters(rng: random.Random, count: int) -> tuple[str, list[Character]]:
    universes = load_approved_characters()
    universe = rng.choice(sorted(universes))
    characters = rng.sample(universes[universe], count)
    return universe, characters


def two_digit_numbers_containing_digit(digit: int) -> list[int]:
    if digit < 0 or digit > 9:
        raise ComparisonTemplateError(f"Недопустимая цифра: {digit}")
    needle = str(digit)
    return [number for number in range(10, 100) if needle in str(number)]


def _compare(first: int, second: int, first_label: str = "first", second_label: str = "second") -> dict[str, Any]:
    if first > second:
        return {"larger": first_label, "difference": first - second, "first_value": first, "second_value": second}
    if second > first:
        return {"larger": second_label, "difference": second - first, "first_value": first, "second_value": second}
    return {"larger": "equal", "difference": 0, "first_value": first, "second_value": second}


def _comparison_answer_text(answer: dict[str, Any], first_text: str = "Первое число", second_text: str = "Второе число") -> str:
    if answer["larger"] == "equal":
        return "Значения равны."
    label = first_text if answer["larger"] in {"first", "A"} else second_text
    if answer["larger"] == "A":
        label = "A"
    if answer["larger"] == "B":
        label = "B"
    return f"{label} больше на {answer['difference']}."


def _problem(template: dict[str, Any], text: str, answer: dict[str, Any], parameters: dict[str, Any], *, seed: int | None = None, universe: str | None = None, characters: list[str] | None = None, answer_text: str | None = None) -> GeneratedComparisonProblem:
    if "{" in text or "}" in text or "+ -" in text or "- -" in text:
        raise ComparisonTemplateError(f"Некорректный текст задачи: {text}")
    return GeneratedComparisonProblem(
        module="comparison_of_numbers_and_expressions",
        template_id=str(template["id"]),
        source_problem_numbers=list(template["source_problem_numbers"]),
        problem_text=text,
        answer=answer,
        answer_text=answer_text or _comparison_answer_text(answer),
        parameters=parameters,
        seed=seed,
        universe=universe,
        characters=characters,
    )


def _range_except_zero(rng: random.Random, low: int, high: int) -> int:
    value = rng.randint(low, high)
    return value if value != 0 else high


def _triple_decrement_product(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(3000, 9000)
    common = rng.randint(20, 250)
    b = a + rng.randint(400, 1300)
    first = a * common * b
    second = (a - 1) * common * (b - 1)
    text = f"Какое из чисел больше и на сколько: {a} × {common} × {b} (первое) или {a - 1} × {common} × {b - 1} (второе)?"
    return _problem(template, text, _compare(first, second), {"a": a, "common": common, "b": b, "first_value": first, "second_value": second}, seed=seed)


def _triple_cross_increment_product(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(3000, 8000)
    common = rng.randint(20, 250)
    b = a + rng.randint(500, 1400)
    first = a * common * (b - 1)
    second = b * common * (a + 1)
    text = f"Какое из чисел больше и на сколько: {a} × {common} × {b - 1} (первое) или {b} × {common} × {a + 1} (второе)?"
    return _problem(template, text, _compare(first, second), {"a": a, "common": common, "b": b, "first_value": first, "second_value": second}, seed=seed)


def _two_factor_gap_four(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(120, 900)
    first = a * (a + 4)
    second = (a + 1) * (a + 3)
    text = f"На сколько отличаются числа {a} × {a + 4} и {a + 1} × {a + 3}? Какое из них больше?"
    return _problem(template, text, _compare(first, second), {"a": a, "first_value": first, "second_value": second}, seed=seed)


def _paired_expression_common_large(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    base = rng.randint(4000, 15000)
    offset = rng.randint(1, 6)
    large = rng.randint(5000, 25000)
    small_1 = rng.randint(2, 9)
    small_2 = rng.randint(2, 9)
    other = base + offset
    first = base * large - other * small_1
    second = other * large - base * small_2
    text = f"Что больше и на сколько: A = {base} × {large} - {other} × {small_1} или B = {other} × {large} - {base} × {small_2}?"
    return _problem(template, text, _compare(first, second, "A", "B"), {"base": base, "offset": offset, "large": large, "small_1": small_1, "small_2": small_2, "first_value": first, "second_value": second}, seed=seed)


def _paired_expression_common_large_reversed(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    base = rng.randint(4000, 15000)
    offset = rng.randint(1, 6)
    large = rng.randint(5000, 25000)
    small_1 = rng.randint(2, 9)
    small_2 = rng.randint(2, 9)
    other = base + offset
    first = other * large - base * small_1
    second = base * large - other * small_2
    text = f"Что больше и на сколько: A = {other} × {large} - {base} × {small_1} или B = {base} × {large} - {other} × {small_2}?"
    return _problem(template, text, _compare(first, second, "A", "B"), {"base": base, "offset": offset, "large": large, "small_1": small_1, "small_2": small_2, "first_value": first, "second_value": second}, seed=seed)


def _shifted_product_factors(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(900, 8000)
    b = rng.randint(120, 5000)
    shift = rng.randint(1, min(20, b - 1))
    direction = rng.choice([-1, 1])
    first = a * b
    second = (a + direction * shift) * (b - direction * shift)
    text = f"Какое из чисел больше и на сколько: {a} × {b} (первое) или {a + direction * shift} × {b - direction * shift} (второе)?"
    return _problem(template, text, _compare(first, second), {"a": a, "b": b, "shift": shift, "direction": direction, "first_value": first, "second_value": second}, seed=seed)


def _triple_shared_middle_factor(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    low = rng.randint(120, 400)
    common = rng.randint(40, 300)
    shift = rng.randint(800, 1400)
    first = low * common * (low + shift + 2)
    second = (low + shift) * common * (low + 2)
    text = f"Какое из чисел больше и на сколько: {low} × {common} × {low + shift + 2} или {low + shift} × {common} × {low + 2}?"
    return _problem(template, text, _compare(first, second), {"low": low, "common": common, "shift": shift, "first_value": first, "second_value": second}, seed=seed)


def _triple_large_shift_product(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(900, 2500)
    common = rng.randint(40, 300)
    b = rng.randint(900, 2500)
    shift = rng.randint(700, 1300)
    first = (a + shift) * common * b
    second = a * common * (b + shift)
    text = f"Какое из чисел больше и на сколько: {a + shift} × {common} × {b} (первое) или {a} × {common} × {b + shift} (второе)?"
    return _problem(template, text, _compare(first, second), {"a": a, "b": b, "common": common, "shift": shift, "first_value": first, "second_value": second}, seed=seed)


def _large_opposite_shift_product(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(900, 2500)
    b = rng.randint(1800, 3500)
    shift = rng.randint(600, min(1400, b - 200))
    first = a * b
    second = (a + shift) * (b - shift)
    text = f"Какое из чисел больше и на сколько: {a} × {b} (первое) или {a + shift} × {b - shift} (второе)?"
    return _problem(template, text, _compare(first, second), {"a": a, "b": b, "shift": shift, "first_value": first, "second_value": second}, seed=seed)


def _difference_change(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    decrease = rng.randint(2, 30)
    increase = rng.randint(2, 30)
    change = decrease + increase
    text = f"Как изменится разность, если уменьшаемое уменьшить на {decrease}, а вычитаемое увеличить на {increase}?"
    answer = {"larger": "decreased", "difference": change, "change": -change}
    return _problem(template, text, answer, {"decrease_amount": decrease, "increase_amount": increase, "difference_change": -change}, seed=seed, answer_text=f"Разность уменьшится на {change}.")


def _exact_quotient_comparison(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    divisor_1 = rng.randint(120, 600)
    divisor_2 = rng.randint(120, 600)
    quotient_1 = rng.randint(3000, 120000)
    quotient_2 = quotient_1 + _range_except_zero(rng, -500, 500)
    dividend_1 = divisor_1 * quotient_1
    dividend_2 = divisor_2 * quotient_2
    first = dividend_1 // divisor_1
    second = dividend_2 // divisor_2
    if dividend_1 % divisor_1 or dividend_2 % divisor_2:
        raise ComparisonTemplateError("Деление должно быть точным.")
    text = f"Что больше {dividend_1}:{divisor_1} или {dividend_2}:{divisor_2}?"
    return _problem(template, text, _compare(first, second), {"dividend_1": dividend_1, "divisor_1": divisor_1, "dividend_2": dividend_2, "divisor_2": divisor_2, "quotient_1": first, "quotient_2": second}, seed=seed)


def _two_factor_gap_four_with_common(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(120, 900)
    common = rng.choice([101, 1001, 10001])
    first = a * common * (a + 4)
    second = (a + 1) * common * (a + 3)
    text = f"На сколько отличаются числа {a} · {common} · {a + 4} и {a + 1} · {common} · {a + 3}?"
    return _problem(template, text, _compare(first, second), {"a": a, "common": common, "first_value": first, "second_value": second}, seed=seed)


def _two_factor_offset_mixed(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    a = rng.randint(900, 9000)
    first = a * (a + 2)
    second = (a - 1) * (a + 4)
    text = f"На сколько отличаются числа {a} · {a + 2} и {a - 1} · {a + 4}?"
    return _problem(template, text, _compare(first, second), {"a": a, "first_value": first, "second_value": second}, seed=seed)


def _digit_sum_characters(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedComparisonProblem:
    digit_1, digit_2 = rng.sample(range(1, 10), 2)
    universe, characters = _choose_characters(rng, 2)
    first_character, second_character = characters
    first_sum = sum(two_digit_numbers_containing_digit(digit_1))
    second_sum = sum(two_digit_numbers_containing_digit(digit_2))
    answer = _compare(first_sum, second_sum, "character_1", "character_2")
    name_1 = _capitalize_sentence_start(first_character.name)
    name_2 = _capitalize_sentence_start(second_character.name)
    text = (
        f"{name_1} {_past(first_character, 'записал', 'записала')} все двузначные числа, которые содержат цифру {digit_1}, "
        f"затем {_past(first_character, 'сложил', 'сложила')} их. "
        f"{name_2} {_past(second_character, 'записал', 'записала')} все двузначные числа, которые содержат цифру {digit_2}, "
        f"затем {_past(second_character, 'сложил', 'сложила')} их. "
        "У кого получилась большая сумма и на сколько?"
    )
    if answer["larger"] == "character_1":
        answer_text = f"{_capitalize_sentence_start(first_character.name)} получил{'а' if first_character.gender == 'feminine' else ''} большую сумму на {answer['difference']}."
    elif answer["larger"] == "character_2":
        answer_text = f"{_capitalize_sentence_start(second_character.name)} получил{'а' if second_character.gender == 'feminine' else ''} большую сумму на {answer['difference']}."
    else:
        answer_text = "Суммы равны."
    answer = {
        **answer,
        "larger_character_role": answer["larger"],
        "digit_1_sum": first_sum,
        "digit_2_sum": second_sum,
    }
    return _problem(
        template,
        text,
        answer,
        {
            "digit_1": digit_1,
            "digit_2": digit_2,
            "digit_1_numbers": two_digit_numbers_containing_digit(digit_1),
            "digit_2_numbers": two_digit_numbers_containing_digit(digit_2),
            "digit_1_sum": first_sum,
            "digit_2_sum": second_sum,
        },
        seed=seed,
        universe=universe,
        characters=[character.name for character in characters],
        answer_text=answer_text,
    )


Strategy = Callable[[dict[str, Any], random.Random, int | None], GeneratedComparisonProblem]
STRATEGIES: dict[str, Strategy] = {
    "triple_decrement_product": _triple_decrement_product,
    "triple_cross_increment_product": _triple_cross_increment_product,
    "two_factor_gap_four": _two_factor_gap_four,
    "paired_expression_common_large": _paired_expression_common_large,
    "paired_expression_common_large_reversed": _paired_expression_common_large_reversed,
    "shifted_product_factors": _shifted_product_factors,
    "triple_shared_middle_factor": _triple_shared_middle_factor,
    "triple_large_shift_product": _triple_large_shift_product,
    "large_opposite_shift_product": _large_opposite_shift_product,
    "difference_change": _difference_change,
    "exact_quotient_comparison": _exact_quotient_comparison,
    "two_factor_gap_four_with_common": _two_factor_gap_four_with_common,
    "two_factor_offset_mixed": _two_factor_offset_mixed,
    "digit_sum_characters": _digit_sum_characters,
}


def generate_comparison_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedComparisonProblem:
    template = get_comparison_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy_name = str(template["generation_strategy"])
    if strategy_name not in STRATEGIES:
        raise ComparisonTemplateError(f"Неизвестная стратегия сравнения: {strategy_name}")
    failures: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            generated = STRATEGIES[strategy_name](template, local_rng, seed)
            if generated.answer["difference"] == 0 and strategy_name != "digit_sum_characters":
                failures.append("unexpected_equality")
                continue
            generated.parameters["attempt"] = attempt
            return generated
        except Exception as error:  # noqa: BLE001 - генератор возвращает понятную агрегированную ошибку.
            failures.append(str(error))
    raise ComparisonTemplateError(
        f"Не удалось построить задачу сравнения {template_id} за {MAX_ATTEMPTS} попыток. "
        f"seed={seed}, failed_constraints={failures[-10:]}"
    )


def generate_comparison_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedComparisonProblem:
    if module_id != "comparison_of_numbers_and_expressions":
        raise ComparisonTemplateError(f"Неизвестный модуль сравнения: {module_id}")
    template = rng.choice(load_comparison_templates())
    return generate_comparison_problem(str(template["id"]), rng=rng)
