"""Параметрический генератор модуля «Последовательности, прогрессии и суммы»."""

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

from problemgen.generation.comparison_templates import Character, load_approved_characters


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = [
    PROJECT_ROOT / "docs" / "05a_posledovatelnosti_bez_imen_i_personazhey.md",
    PROJECT_ROOT / "docs" / "05b_posledovatelnosti_s_imenami_i_personazhami.md",
]
DEFAULT_SEQUENCE_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "sequences_progressions_and_sums" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
MAX_ATTEMPTS = 100
FEMININE_CHARACTER_NAMES = {
    "корова Мурка", "старуха Шапокляк", "крыса Лариска", "девочка Галя", "Свинья",
    "Нюша", "Совунья", "Маша", "Медведица", "Даша", "поросёнок Розочка",
    "Мальвина", "лиса Алиса", "Сова", "Мила", "Эльза", "Анна", "Фиона",
    "Дракониха", "Гермиона Грейнджер", "Лея Органа", "Симка", "Мася", "Василиса",
    "Баба-Яга", "Элизабет Суонн", "Тиа Дальма", "Джесси", "Бо Пип", "Нала",
    "Глория", "Тигрица", "Обезьяна", "Алиса", "Червонная Королева", "Синяя Гусеница",
    "Венди Дарлинг", "Динь-Динь", "Тигровая Лилия", "Элли",
}


class SequenceTemplateError(ValueError):
    """Понятная ошибка загрузки либо генерации последовательностей."""


@dataclass(frozen=True)
class GeneratedSequenceProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int | dict[str, int]
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None
    universe: str | None = None
    characters: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = self.__dict__.copy()
        return {key: value for key, value in result.items() if value is not None}


def source_sequence_problem_numbers(paths: list[Path] | None = None) -> set[int]:
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


def load_sequence_templates(path: str | Path = DEFAULT_SEQUENCE_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    templates = _load_payload(str(resolved), resolved.stat().st_mtime_ns).get("templates")
    if not isinstance(templates, list) or not templates:
        raise SequenceTemplateError("В sequence problem set нет списка templates.")
    validate_sequence_catalog(templates)
    return list(templates)


def validate_sequence_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen: list[int] = []
    for template in templates:
        for field in ("id", "module_id", "source_problem_numbers", "generation_strategy", "uses_characters"):
            if field not in template:
                raise SequenceTemplateError(f"У шаблона нет поля {field}: {template!r}")
        if template["id"] in ids:
            raise SequenceTemplateError(f"Повторяющийся id шаблона: {template['id']}")
        ids.add(template["id"])
        if template["module_id"] != "sequences_progressions_and_sums":
            raise SequenceTemplateError(f"Неверный module_id у {template['id']}")
        seen.extend(int(number) for number in template["source_problem_numbers"])
    source = source_sequence_problem_numbers()
    if set(seen) != source or len(seen) != len(set(seen)):
        raise SequenceTemplateError(
            f"Проблема покрытия источника. missing={sorted(source - set(seen))}, "
            f"extra={sorted(set(seen) - source)}, duplicates={sorted(n for n, c in Counter(seen).items() if c > 1)}"
        )


def sequence_template_metadata() -> dict[str, Any]:
    templates = load_sequence_templates()
    return {
        "modules": [{"module_id": "sequences_progressions_and_sums", "title": "Sequences, Progressions and Sums", "display_name": "Последовательности, прогрессии и суммы", "template_count": len(templates), "covered_source_problem_numbers": len(source_sequence_problem_numbers())}],
        "templates": [{"template_id": item["id"], "title": item["title"], "display_name": item["title"], "module_name": "Последовательности, прогрессии и суммы", "source_problem_numbers": item["source_problem_numbers"], "problem_type": item["problem_type"]} for item in templates],
        "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_sequence_problem_numbers())},
    }


def get_sequence_template(template_id: str) -> dict[str, Any]:
    for template in load_sequence_templates():
        if template["id"] == template_id:
            return template
    raise SequenceTemplateError(f"Неизвестный шаблон последовательностей: {template_id}.")


def _digit_word(number: int) -> str:
    tail = number % 100
    if 11 <= tail <= 14:
        return "цифр"
    return {1: "цифра", 2: "цифры", 3: "цифры", 4: "цифры"}.get(number % 10, "цифр")


def _capitalized(name: str) -> str:
    return name[:1].upper() + name[1:]


def character_gender(character: Character) -> str:
    """Уточняет род составных имён, где окончание последнего слова ненадёжно."""
    if character.name in FEMININE_CHARACTER_NAMES:
        return "feminine"
    return character.gender


def _pick_character(rng: random.Random) -> tuple[str, Character]:
    universes = load_approved_characters()
    universe = rng.choice(sorted(universes))
    return universe, rng.choice(universes[universe])


def _make(template: dict[str, Any], text: str, answer: int | dict[str, int], answer_text: str, parameters: dict[str, Any], *, seed: int | None, universe: str | None = None, characters: list[str] | None = None) -> GeneratedSequenceProblem:
    if "{" in text or "}" in text:
        raise SequenceTemplateError("В тексте остались плейсхолдеры.")
    values = answer.values() if isinstance(answer, dict) else [answer]
    if not all(isinstance(value, int) for value in values):
        raise SequenceTemplateError("Ответ должен состоять только из целых чисел.")
    return GeneratedSequenceProblem("sequences_progressions_and_sums", template["id"], list(template["source_problem_numbers"]), text, answer, answer_text, parameters, seed, universe, characters)


def _ap_terms(start: int, step: int, count: int) -> list[int]:
    return [start + index * step for index in range(count)]


def _arithmetic_progression_sum(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    start, step, count = rng.randint(1, 50), rng.randint(1, 12), rng.randint(8, 40)
    terms = _ap_terms(start, step, count)
    numerator = count * (terms[0] + terms[-1])
    if numerator % 2:
        raise SequenceTemplateError("Сумма прогрессии должна быть целой.")
    answer = numerator // 2
    if answer != sum(terms):
        raise SequenceTemplateError("Независимая проверка суммы прогрессии не пройдена.")
    text = f"Найдите сумму последовательности: {terms[0]} + {terms[1]} + {terms[2]} + … + {terms[-2]} + {terms[-1]} =?"
    return _make(template, text, answer, str(answer), {"start": start, "step": step, "term_count": count, "terms": terms, "last_term": terms[-1]}, seed=seed)


def _alternating_steps_sum(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    start, first, second, count = rng.randint(1, 12), rng.randint(1, 6), rng.randint(1, 8), rng.randint(12, 32)
    if first == second:
        raise SequenceTemplateError("Шаги не должны совпадать.")
    terms = [start]
    for index in range(1, count):
        terms.append(terms[-1] + (first if index % 2 else second))
    differences = [right - left for left, right in zip(terms, terms[1:])]
    if any(value != (first if index % 2 == 0 else second) for index, value in enumerate(differences)):
        raise SequenceTemplateError("Нарушено чередование шагов.")
    answer = sum(terms)
    text = f"Найдите сумму последовательности: {terms[0]} + {terms[1]} + {terms[2]} + {terms[3]} + … + {terms[-1]}."
    return _make(template, text, answer, str(answer), {"start": start, "step_1": first, "step_2": second, "term_count": count, "terms": terms, "last_term": terms[-1]}, seed=seed)


def recurrence_terms(first: int, second: int, operation: str, count: int) -> list[int]:
    terms = [first, second]
    for _ in range(2, count):
        terms.append(((terms[-1] * terms[-2]) if operation == "multiplication_mod_10" else (terms[-1] + terms[-2])) % 10)
    return terms[:count]


def recurrence_value(first: int, second: int, operation: str, position: int) -> int:
    if position < 1:
        raise SequenceTemplateError("Номер позиции должен быть положительным.")
    if position <= 2:
        return [first, second][position - 1]
    terms = [first, second]
    states: dict[tuple[int, int], int] = {(first, second): 2}
    while len(terms) < position:
        next_value = ((terms[-2] * terms[-1]) if operation == "multiplication_mod_10" else (terms[-2] + terms[-1])) % 10
        terms.append(next_value)
        state = (terms[-2], terms[-1])
        if state in states:
            cycle_start, cycle_end = states[state], len(terms)
            cycle_length = cycle_end - cycle_start
            repeated_position = cycle_start + ((position - cycle_start) % cycle_length)
            return terms[repeated_position - 1]
        states[state] = len(terms)
        if len(states) > 100:
            raise SequenceTemplateError("Цикл рекурсии не найден в конечном пространстве состояний.")
    return terms[position - 1]


def _recurrence(template: dict[str, Any], rng: random.Random, seed: int | None, operation: str) -> GeneratedSequenceProblem:
    first, second = rng.randint(0, 9), rng.randint(0, 9)
    shown_count, reference_position, target_position = 7, rng.randint(3, 7), rng.randint(1000, 5000)
    shown = recurrence_terms(first, second, operation, shown_count)
    reference = shown[reference_position - 1]
    answer = recurrence_value(first, second, operation, target_position)
    direct = recurrence_terms(first, second, operation, min(target_position, 100))[-1]
    if target_position <= 100 and answer != direct:
        raise SequenceTemplateError("Циклический расчёт рекурсии не совпал с прямым.")
    action = "произведения" if operation == "multiplication_mod_10" else "суммы"
    text = f"В последовательности {', '.join(map(str, shown))}, … каждая цифра равна последней цифре {action} предыдущих двух цифр. Как видно, на {reference_position}-м месте стоит цифра {reference}. А какая цифра стоит на {target_position}-м месте?"
    return _make(template, text, answer, f"На {target_position}-м месте стоит цифра {answer}.", {"first_digit": first, "second_digit": second, "shown_terms": shown, "shown_term_count": shown_count, "reference_position": reference_position, "reference_value": reference, "target_position": target_position, "recurrence_operation": operation}, seed=seed)


def _product_mod_10(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    return _recurrence(template, rng, seed, "multiplication_mod_10")


def _sum_mod_10(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    return _recurrence(template, rng, seed, "addition_mod_10")


def _cyclic_digit_shift_sum(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    digit_string = "".join(map(str, rng.sample(range(1, 10), 6)))
    rotations = [digit_string[index:] + digit_string[:index] for index in range(len(digit_string))]
    if len(set(rotations)) != len(rotations):
        raise SequenceTemplateError("Циклические сдвиги должны быть уникальны.")
    numbers = [int(value) for value in rotations]
    answer = sum(numbers)
    text = f"Чему равна сумма {numbers[0]} + {numbers[1]} + {numbers[2]} + … + {numbers[-1]}?"
    return _make(template, text, answer, str(answer), {"digit_string": digit_string, "rotation_direction": "left", "rotation_count": len(rotations), "rotations": rotations}, seed=seed)


def _alternating_operations(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    start, multiplier, subtraction = rng.randint(3, 20), rng.randint(2, 4), rng.randint(1, 12)
    terms = [start]
    for index in range(10):
        terms.append(terms[-1] * multiplier if index % 2 == 0 else terms[-1] - subtraction)
    if min(terms) <= 0:
        raise SequenceTemplateError("В последовательности появились неположительные члены.")
    shown, next_terms = terms[:8], terms[8:11]
    text = f"Продолжите последовательность {', '.join(map(str, shown))}, … В ответ напишите сумму трёх следующих чисел."
    answer = sum(next_terms)
    return _make(template, text, answer, f"Следующие числа: {', '.join(map(str, next_terms))}. Их сумма равна {answer}.", {"start": start, "multiplier": multiplier, "subtraction": subtraction, "shown_terms": shown, "next_terms": next_terms}, seed=seed)


def _signed_expression(terms: list[int]) -> str:
    result = str(terms[0])
    for index, value in enumerate(terms[1:], start=1):
        result += f" {'-' if index % 2 else '+'} {value}"
    return result


def _multi_part_sequence(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    first = _ap_terms(rng.randint(5, 25), rng.randint(2, 7), rng.randint(8, 16))
    second = _ap_terms(rng.randint(5, 25), rng.randint(2, 7), rng.randint(8, 16))
    signs = _ap_terms(rng.choice([1, 3, 5]), rng.choice([2, 4]), rng.choice([10, 12, 14]))
    answers = {"а": sum(first), "б": sum(second), "в": sum(value if index % 2 == 0 else -value for index, value in enumerate(signs))}
    text = f"Найдите суммы: а) {first[0]} + {first[1]} + {first[2]} + … + {first[-1]}; б) {second[0]} + {second[1]} + {second[2]} + … + {second[-1]}; в) {_signed_expression(signs[:4])} + … {'-' if len(signs) % 2 == 0 else '+'} {signs[-1]}."
    answer_text = f"а) {answers['а']}; б) {answers['б']}; в) {answers['в']}."
    return _make(template, text, answers, answer_text, {"part_a_terms": first, "part_b_terms": second, "part_c_terms": signs}, seed=seed)


def digit_count(first: int, count: int) -> int:
    if first < 1 or count < 1:
        raise SequenceTemplateError("Натуральные числа начинаются с 1, число членов должно быть положительным.")
    last = first + count - 1
    result = 0
    lower = 1
    digits = 1
    while lower <= last:
        upper = lower * 10 - 1
        overlap_start, overlap_end = max(first, lower), min(last, upper)
        if overlap_start <= overlap_end:
            result += (overlap_end - overlap_start + 1) * digits
        lower *= 10
        digits += 1
    return result


def solve_digit_count_intervals(count: int, total: int, upper_bound: int = 6000) -> list[int]:
    return [first for first in range(1, upper_bound + 1) if digit_count(first, count) == total]


def _digit_count_problem(template: dict[str, Any], rng: random.Random, seed: int | None, endpoint: str) -> GeneratedSequenceProblem:
    count = rng.randint(90, 180) if endpoint == "first" else rng.randint(900, 1100)
    first = rng.randint(1, 80) if endpoint == "first" else rng.randint(1, 500)
    last = first + count - 1
    total = digit_count(first, count)
    solutions = solve_digit_count_intervals(count, total)
    if solutions != [first]:
        raise SequenceTemplateError(f"Задача о цифрах не имеет единственного решения: {solutions[:10]}")
    universe, character = _pick_character(rng)
    name = _capitalized(character.name)
    noticed = "заметила" if character_gender(character) == "feminine" else "заметил"
    requested = "первым" if endpoint == "first" else "последним"
    answer = first if endpoint == "first" else last
    text = f"В ряд выписали {count} подряд идущих натуральных чисел. {name} {noticed}, что всего выписано {total} {_digit_word(total)}. Какое число было выписано {requested}?"
    answer_text = f"{requested.capitalize()} было выписано число {answer}."
    return _make(template, text, answer, answer_text, {"first_number": first, "last_number": last, "count_of_numbers": count, "total_digit_count": total, "number_of_solutions": len(solutions), "solution_search_upper_bound": 6000}, seed=seed, universe=universe, characters=[character.name])


def _digit_count_find_first(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    return _digit_count_problem(template, rng, seed, "first")


def _digit_count_find_last(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSequenceProblem:
    return _digit_count_problem(template, rng, seed, "last")


Strategy = Callable[[dict[str, Any], random.Random, int | None], GeneratedSequenceProblem]
STRATEGIES: dict[str, Strategy] = {"alternating_steps_sum": _alternating_steps_sum, "arithmetic_progression_sum": _arithmetic_progression_sum, "product_mod_10": _product_mod_10, "sum_mod_10": _sum_mod_10, "cyclic_digit_shift_sum": _cyclic_digit_shift_sum, "alternating_operations": _alternating_operations, "multi_part_sequence": _multi_part_sequence, "digit_count_find_first": _digit_count_find_first, "digit_count_find_last": _digit_count_find_last}


def generate_sequence_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedSequenceProblem:
    template = get_sequence_template(template_id)
    local_rng = rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    strategy = STRATEGIES.get(str(template["generation_strategy"]))
    if strategy is None:
        raise SequenceTemplateError(f"Неизвестная стратегия: {template['generation_strategy']}")
    failures: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            generated = strategy(template, local_rng, seed)
            generated.parameters["attempt"] = attempt
            return generated
        except Exception as error:  # noqa: BLE001
            failures.append(str(error))
    raise SequenceTemplateError(f"Не удалось построить {template_id} за {MAX_ATTEMPTS} попыток: {failures[-5:]}")


def generate_sequence_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedSequenceProblem:
    if module_id != "sequences_progressions_and_sums":
        raise SequenceTemplateError(f"Неизвестный модуль последовательностей: {module_id}")
    template = rng.choice(load_sequence_templates())
    return generate_sequence_problem(str(template["id"]), rng=rng)
