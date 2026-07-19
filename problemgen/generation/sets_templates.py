"""Детерминированный генератор модуля «Множества, клубы, знакомства и турниры»."""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from math import gcd
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "sets_clubs_acquaintances_and_tournaments"
PATH = ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
MANIFEST = PATH.with_name("source_accounting.json")
SOURCES = (
    ROOT / "docs" / "23_mnozhestva_kluby_znakomstva_i_turniry_bez_imen_i_personazhey_deduplicated.md",
    ROOT / "docs" / "23_mnozhestva_kluby_znakomstva_i_turniry_s_imenami_i_personazhami_deduplicated.md",
)
SOURCE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")


class SetsTemplateError(ValueError):
    """Нарушен контракт каталога или математическая проверка экземпляра."""


@dataclass(frozen=True)
class GeneratedSetsProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: int
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None


@lru_cache(maxsize=4)
def _load_json(path: str, stamp: int) -> dict[str, Any]:
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
    return _load_json(str(MANIFEST), MANIFEST.stat().st_mtime_ns)


def load_sets_templates() -> list[dict[str, Any]]:
    templates = _load_json(str(PATH), PATH.stat().st_mtime_ns)["templates"]
    records = load_source_accounting()["records"]
    record_numbers = [record["source_problem_number"] for record in records]
    active_mapping = {
        number: template["id"]
        for template in templates
        for number in template["source_problem_numbers"]
    }
    manifest_mapping = {
        record["source_problem_number"]: record["template_id"]
        for record in records
        if record["status"] == "active_template"
    }
    if (
        len(record_numbers) != 26
        or len(record_numbers) != len(set(record_numbers))
        or set(record_numbers) != source_problem_numbers()
        or active_mapping != manifest_mapping
    ):
        raise SetsTemplateError("Некорректный source-accounting manifest модуля 23.")
    if len({template["id"] for template in templates}) != len(templates):
        raise SetsTemplateError("Идентификаторы шаблонов модуля 23 должны быть уникальны.")
    return list(templates)


def _build(template: dict[str, Any], text: str, answer: int, parameters: dict[str, Any], seed: int | None) -> GeneratedSetsProblem:
    if not isinstance(answer, int):
        raise SetsTemplateError(f"{template['id']}: ответ должен быть целым числом.")
    if "{" in text or "}" in text:
        raise SetsTemplateError(f"{template['id']}: остались незаполненные параметры.")
    return GeneratedSetsProblem(MODULE_ID, template["id"], template["source_problem_numbers"], text, answer, str(answer), parameters, seed)


def _plural(number: int, one: str, few: str, many: str) -> str:
    """Возвращает форму существительного после целого русского числительного."""
    remainder = number % 100
    if 11 <= remainder <= 14:
        return many
    remainder = number % 10
    if remainder == 1:
        return one
    if 2 <= remainder <= 4:
        return few
    return many


def _two_fields(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    hours_with_two_fields = rng.randint(4, 12)
    answer = hours_with_two_fields * 2
    if answer % 2:
        raise SetsTemplateError(f"{template['id']} seed={seed}: нарушена кратность числу полей.")
    text = (
        f"Шесть специалистов сыграли каждый с каждым по одной партии за {hours_with_two_fields} часов. "
        "Все партии длились одинаково, одновременно работали два поля. Сколько часов понадобилось бы при одном поле?"
    )
    return _build(template, text, answer, {"hours_with_two_fields": hours_with_two_fields, "field_count": 2}, seed)


def _single_elimination(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    participant_count = rng.randint(2, 32)
    answer = participant_count - 1
    text = f"Турнир по олимпийской системе проводят {participant_count} {_plural(participant_count, 'команда', 'команды', 'команд')}. Сколько матчей нужно для выявления победителя?"
    return _build(template, text, answer, {"participant_count": participant_count}, seed)


def _round_robin(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    participant_count = rng.randint(4, 30)
    games_per_pair = rng.randint(1, 3)
    dividend = participant_count * (participant_count - 1) * games_per_pair
    if dividend % 2:
        raise SetsTemplateError(f"{template['id']} seed={seed}: нечётное число направленных партий.")
    answer = dividend // 2
    game_phrase = {1: "одной партии", 2: "две партии", 3: "три партии"}[games_per_pair]
    text = (
        f"В шахматном турнире играют {participant_count} {_plural(participant_count, 'участник', 'участника', 'участников')}. Каждый играет с каждым другим по {game_phrase}. "
        "Сколько всего партий будет сыграно?"
    )
    return _build(template, text, answer, {"participant_count": participant_count, "games_per_pair": games_per_pair}, seed)


def _clubs(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    music_members = rng.randint(16, 30)
    no_club = rng.randint(3, 12)
    girls_in_literature = rng.randint(2, 12)
    overlap = 1
    boys_in_literature = 1
    total = music_members + no_club + girls_in_literature
    answer = total - music_members - no_club + overlap - boys_in_literature
    if answer != girls_in_literature:
        raise SetsTemplateError(f"{template['id']} seed={seed}: неверная формула включения-исключения.")
    text = (
        f"В классе всего {total} человек. В музыкальном клубе состоят {music_members} человек, а {no_club} не состоят ни в одном клубе. "
        "Только одна девочка состоит сразу в музыкальном и литературном клубах, среди мальчиков таких нет. "
        f"В литературном клубе {boys_in_literature} мальчик. Сколько девочек состоит в литературном клубе?"
    )
    return _build(template, text, answer, {"total_people": total, "music_members": music_members, "no_club": no_club, "overlap_girls": overlap, "boys_in_literature": boys_in_literature}, seed)


def _language_overlap(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    overlap = rng.randint(2, 16)
    english_only = rng.randint(3, 20)
    french_only = rng.randint(3, 20)
    neither = rng.randint(0, 12)
    english = overlap + english_only
    french = overlap + french_only
    total = english_only + french_only + overlap + neither
    answer = english + french + neither - total
    if answer != overlap:
        raise SetsTemplateError(f"{template['id']} seed={seed}: неверная формула пересечения языков.")
    text = (
        f"В группе {total} человек. Английский язык изучают {english}, французский — {french}, а {neither} не изучают ни один из этих языков. "
        "Сколько школьников изучают оба языка?"
    )
    return _build(template, text, answer, {"total_people": total, "english_members": english, "french_members": french, "neither": neither}, seed)


def _bipartite_handshakes(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    first_count = rng.randint(5, 14)
    second_count = rng.randint(5, 14)
    edge_multiplier = rng.randint(1, gcd(first_count, second_count))
    edge_count = first_count * second_count // gcd(first_count, second_count) * edge_multiplier
    first_degree = edge_count // first_count
    second_degree = edge_count // second_count
    total = first_count + second_count
    if edge_count % first_count or edge_count % second_count or first_count * first_degree != second_count * second_degree:
        raise SetsTemplateError(f"{template['id']} seed={seed}: степени двудольного графа не согласованы.")
    answer = first_count
    text = (
        f"В двух классах всего {total} человек. Каждый ученик первого класса пожал руку {first_degree} {_plural(first_degree, 'ученику', 'ученикам', 'ученикам')} второго класса, "
        f"а каждый ученик второго класса — {second_degree} {_plural(second_degree, 'ученику', 'ученикам', 'ученикам')} первого. Сколько учеников в первом классе?"
    )
    return _build(template, text, answer, {"total_people": total, "first_to_second_degree": first_degree, "second_to_first_degree": second_degree, "cross_handshakes": edge_count}, seed)


def _score_balance(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    first_group = rng.randint(4, 8)
    second_group = rng.randint(4, 8)
    cross_games = first_group * second_group
    first_wins = rng.randint(cross_games // 2 + 1, cross_games)
    remaining = cross_games - first_wins
    second_wins = rng.randint(0, remaining)
    draws = remaining - second_wins
    internal_points = first_group * (first_group - 1)
    first_group_points = internal_points + 2 * first_wins + draws
    answer = first_wins - second_wins
    independently_solved = first_group_points - internal_points - cross_games
    if independently_solved != answer:
        raise SetsTemplateError(f"{template['id']} seed={seed}: баланс очков не прошёл независимую проверку.")
    text = (
        f"{first_group} {_plural(first_group, 'игрок', 'игрока', 'игроков')} первой группы и {second_group} {_plural(second_group, 'игрок', 'игрока', 'игроков')} второй группы сыграли круговой турнир. "
        f"За победу дают 2 очка, за ничью — 1 очко, за поражение — 0 очков. Первая группа набрала {first_group_points} очков. "
        "На сколько игр, выигранных первой группой у второй, больше, чем игр, выигранных второй группой у первой?"
    )
    return _build(template, text, answer, {"first_group_size": first_group, "second_group_size": second_group, "first_group_points": first_group_points, "cross_game_count": cross_games}, seed)


def _tournament_summary(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedSetsProblem:
    participant_count = rng.randint(4, 12)
    match_count = participant_count * (participant_count - 1) // 2
    games_per_participant = participant_count - 1
    total_points = match_count
    answer = match_count + games_per_participant + total_points
    text = (
        f"В шахматном турнире играют {participant_count} {_plural(participant_count, 'шахматист', 'шахматиста', 'шахматистов')}, каждый играет с каждым по одной партии. "
        "За каждую партию участники вместе получают ровно 1 очко. Найдите сумму: числа всех партий, числа партий у одного участника и общего числа очков."
    )
    return _build(template, text, answer, {"participant_count": participant_count, "match_count": match_count, "games_per_participant": games_per_participant, "total_points": total_points}, seed)


STRATEGIES: dict[str, Callable[[dict[str, Any], random.Random, int | None], GeneratedSetsProblem]] = {
    "two_fields": _two_fields,
    "single_elimination": _single_elimination,
    "round_robin": _round_robin,
    "club_inclusion_exclusion": _clubs,
    "language_overlap": _language_overlap,
    "bipartite_handshakes": _bipartite_handshakes,
    "cross_group_score_balance": _score_balance,
    "tournament_summary": _tournament_summary,
}


def generate_sets_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedSetsProblem:
    templates = {template["id"]: template for template in load_sets_templates()}
    if template_id not in templates:
        raise SetsTemplateError(f"Неизвестный шаблон модуля 23: {template_id}.")
    template = templates[template_id]
    return STRATEGIES[template["generation_strategy"]](template, rng or random.Random(seed), seed)


def generate_sets_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedSetsProblem:
    if module_id != MODULE_ID:
        raise SetsTemplateError(f"Ожидался модуль {MODULE_ID}, получен {module_id}.")
    template = rng.choice(load_sets_templates())
    return generate_sets_problem(template["id"], rng=rng)


def sets_template_metadata() -> dict[str, Any]:
    templates = load_sets_templates()
    return {
        "modules": [{"module_id": MODULE_ID, "title": "Sets, Clubs, Acquaintances and Tournaments", "display_name": "Множества, клубы, знакомства и турниры", "template_count": len(templates)}],
        "templates": [{"template_id": template["id"], "title": template["id"], "display_name": template["id"], "module_name": "Множества, клубы, знакомства и турниры", "source_problem_numbers": template["source_problem_numbers"], "problem_type": template["generation_strategy"]} for template in templates],
        "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_problem_numbers())},
    }
