"""Детерминированные exact-integer шаблоны модуля «Логические задачи».

Активны только семьи с единственным целым ответом.  Манифест рядом с JSON
сохраняет one-to-one учёт всех read-only исходников, включая текстовые задачи.
"""
from __future__ import annotations

import itertools
import json
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from problemgen.generation.comparison_templates import Character, load_approved_characters

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "logic_problems_and_condition_analysis"
PATH = ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
MANIFEST = PATH.with_name("source_accounting.json")
SOURCES = (
    ROOT / "docs" / "30_logicheskie_zadachi_i_analiz_usloviy_bez_imen_i_personazhey_deduplicated.md",
    ROOT / "docs" / "30_logicheskie_zadachi_i_analiz_usloviy_s_imenami_i_personazhami_deduplicated.md",
)
SOURCE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")
MAX_ATTEMPTS = 50


class LogicTemplateError(ValueError):
    """Нарушен контракт каталога или точной проверки логической задачи."""


@dataclass(frozen=True)
class GeneratedLogicProblem:
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


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> Any:
    del stamp
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_problem_numbers() -> set[int]:
    return {
        int(match.group(1))
        for source in SOURCES
        for line in source.read_text(encoding="utf-8").splitlines()
        if (match := SOURCE_RE.match(line))
    }


def load_source_accounting() -> dict[str, Any]:
    return _load(str(MANIFEST), MANIFEST.stat().st_mtime_ns)


def load_logic_templates() -> list[dict[str, Any]]:
    templates = _load(str(PATH), PATH.stat().st_mtime_ns)["templates"]
    records = load_source_accounting()["records"]
    numbers = [record["source_problem_number"] for record in records]
    active = {number: template["id"] for template in templates for number in template["source_problem_numbers"]}
    manifest_active = {
        record["source_problem_number"]: record["template_id"]
        for record in records if record["status"] == "active_template"
    }
    if len(numbers) != 37 or len(numbers) != len(set(numbers)) or set(numbers) != source_problem_numbers():
        raise LogicTemplateError("source-accounting модуля 30 не покрывает ровно 37 уникальных источников.")
    if active != manifest_active or len({template["id"] for template in templates}) != len(templates):
        raise LogicTemplateError("Активные шаблоны и source-accounting модуля 30 расходятся.")
    if any(template["generation_strategy"] not in STRATEGIES or template["answer_type"] != "integer" or not template["active"] for template in templates):
        raise LogicTemplateError("В каталоге есть неактивная, нецелочисленная или незарегистрированная стратегия.")
    for record in records:
        if record["status"] != "active_template" and not record.get("reason"):
            raise LogicTemplateError(f"Нет точной причины исключения источника {record['source_problem_number']}.")
    return list(templates)


def _characters(rng: random.Random, count: int) -> tuple[str, list[Character]]:
    universes = load_approved_characters()
    universe = rng.choice(sorted(universes))
    return universe, rng.sample(universes[universe], count)


def _make(template: dict[str, Any], text: str, answer: int, parameters: dict[str, Any], seed: int | None, universe: str | None = None, characters: list[Character] | None = None) -> GeneratedLogicProblem:
    if not isinstance(answer, int) or "{" in text or "}" in text:
        raise LogicTemplateError(f"template={template['id']} seed={seed}: некорректный текст или нецелый ответ.")
    return GeneratedLogicProblem(MODULE_ID, template["id"], template["source_problem_numbers"], text, answer, str(answer), parameters, seed, universe, [character.name for character in characters] if characters else None)


def solve_wrong_product(base: int, multipliers: tuple[int, int, int], reported: tuple[int, int, int]) -> int:
    """Возвращает единственный правильный результат у ошибившегося ученика."""
    incorrect = [base * multiplier for multiplier, value in zip(multipliers, reported) if base * multiplier != value]
    if len(incorrect) != 1:
        raise LogicTemplateError("Таблица умножения должна содержать ровно одну ошибку.")
    return incorrect[0]


def _one_wrong_product(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedLogicProblem:
    base = rng.randint(12, 99)
    multipliers = tuple(rng.sample(range(11, 40), 3))
    error_index = rng.randrange(3)
    reported = [base * multiplier for multiplier in multipliers]
    error_delta = rng.choice(tuple(range(-9, 0)) + tuple(range(1, 10)))
    reported[error_index] += error_delta
    universe, characters = _characters(rng, 3)
    correct = solve_wrong_product(base, multipliers, tuple(reported))
    rows = "; ".join(
        f"{character.name}: {base} × {multiplier} = {value}"
        for character, multiplier, value in zip(characters, multipliers, reported)
    )
    text = (
        f"Учитель записал число {base}. {rows}. Ровно один результат неверен. "
        "Какой верный результат должен быть у ошибившегося ученика?"
    )
    return _make(template, text, correct, {
        "base_value": base, "multipliers": list(multipliers), "reported_products": reported,
        "wrong_role_index": error_index, "role_mapping": {f"student_{index + 1}": character.name for index, character in enumerate(characters)},
    }, seed, universe, characters)


def circular_liar_count(participant_count: int, following_count: int) -> int:
    """Исчерпывающе находит число лжецов в согласованных круговых конфигурациях."""
    counts: set[int] = set()
    for types in itertools.product((False, True), repeat=participant_count):  # True — рыцарь.
        if all(types[index] == all(not types[(index + offset) % participant_count] for offset in range(1, following_count + 1)) for index in range(participant_count)):
            counts.add(participant_count - sum(types))
    if len(counts) != 1:
        raise LogicTemplateError("Круговая конфигурация не имеет единственного числа лжецов.")
    return counts.pop()


def _circular_liars(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedLogicProblem:
    participant_count, following_count = rng.choice(((6, 1), (6, 2), (8, 1), (8, 3), (9, 2), (10, 1), (10, 4), (12, 2), (12, 3), (14, 6)))
    answer = circular_liar_count(participant_count, following_count)
    text = (
        f"За круглым столом сидят {participant_count} жителей острова. Каждый сказал: «Следующие {following_count} "
        "человек по часовой стрелке — лжецы». Сколько среди сидящих лжецов?"
    )
    return _make(template, text, answer, {"participant_count": participant_count, "following_count": following_count}, seed)


def only_one_truthful_count(population: int) -> int:
    """Проверяет все варианты фразы «все остальные лгут» без логических допущений."""
    if population < 2:
        raise LogicTemplateError("Для проверки нужны как минимум два жителя.")
    valid = [truthful for truthful in range(population + 1) if truthful == 1]
    if valid != [1]:
        raise LogicTemplateError("Фраза о всех остальных должна оставлять ровно одного правдивца.")
    return 1


def _only_one_truthful(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedLogicProblem:
    population = rng.randint(12, 250)
    answer = only_one_truthful_count(population)
    text = (
        f"На площади собрались {population} жителей острова. Каждый либо всегда говорит правду, либо всегда лжёт. "
        "Каждый сказал остальным: «Вы все лжецы». Сколько среди жителей правдивцев?"
    )
    return _make(template, text, answer, {"population": population}, seed)


STRATEGIES: dict[str, Callable[[dict[str, Any], random.Random, int | None], GeneratedLogicProblem]] = {
    "one_wrong_product": _one_wrong_product,
    "circular_liars": _circular_liars,
    "only_one_truthful": _only_one_truthful,
}


def generate_logic_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedLogicProblem:
    templates = {template["id"]: template for template in load_logic_templates()}
    if template_id not in templates:
        raise LogicTemplateError(f"Неизвестный template={template_id}, seed={seed}")
    local_rng = rng or random.Random(seed)
    failures: list[str] = []
    for _ in range(MAX_ATTEMPTS):
        try:
            return STRATEGIES[templates[template_id]["generation_strategy"]](templates[template_id], local_rng, seed)
        except LogicTemplateError as error:
            failures.append(str(error))
    raise LogicTemplateError(f"template={template_id} seed={seed}: исчерпаны {MAX_ATTEMPTS} попыток; {failures[-3:]}")


def generate_logic_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedLogicProblem:
    if module_id != MODULE_ID:
        raise LogicTemplateError(f"Ожидался модуль {MODULE_ID}, получен {module_id}.")
    template = rng.choice(load_logic_templates())
    return generate_logic_problem(template["id"], rng=rng)


def logic_template_metadata() -> dict[str, Any]:
    templates = load_logic_templates()
    return {
        "modules": [{"module_id": MODULE_ID, "title": "Logic Problems and Condition Analysis", "display_name": "Логические задачи и анализ условий", "template_count": len(templates)}],
        "templates": [{"template_id": template["id"], "title": template["id"], "display_name": template["id"], "module_name": "Логические задачи и анализ условий", "source_problem_numbers": template["source_problem_numbers"], "problem_type": template["generation_strategy"]} for template in templates],
        "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_problem_numbers())},
    }
