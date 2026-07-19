"""Детерминированный генератор модуля «Часы, циферблаты и электронные табло»."""
from __future__ import annotations

import calendar
import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from problemgen.generation.comparison_templates import Character, load_approved_characters

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "clocks_dials_and_electronic_displays"
PATH = ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
MANIFEST = PATH.with_name("source_accounting.json")
SOURCES = (
    ROOT / "Docs" / "16_chasy_tsiferblaty_i_elektronnye_tablo_bez_imen_i_personazhey_deduplicated.md",
    ROOT / "Docs" / "16_chasy_tsiferblaty_i_elektronnye_tablo_s_imenami_i_personazhami_deduplicated.md",
)
RX = re.compile(r"^\s*(\d+)\.\s+.+$")


class ClockTemplateError(ValueError):
    """Невалидный шаблон или параметры модуля часов."""


@dataclass(frozen=True)
class GeneratedClockProblem:
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


def source_problem_numbers() -> set[int]:
    return {
        int(match.group(1))
        for source in SOURCES
        for line in source.read_text(encoding="utf-8").splitlines()
        if (match := RX.match(line))
    }


@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> Any:
    del stamp
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_source_accounting() -> dict[str, Any]:
    return _load(str(MANIFEST), MANIFEST.stat().st_mtime_ns)


def load_clock_templates() -> list[dict[str, Any]]:
    templates = _load(str(PATH), PATH.stat().st_mtime_ns)["templates"]
    records = load_source_accounting()["records"]
    numbers = [record["source_problem_number"] for record in records]
    active = {number: template["id"] for template in templates for number in template["source_problem_numbers"]}
    manifest_active = {record["source_problem_number"]: record["template_id"] for record in records if record["status"] == "active_template"}
    if len({template["id"] for template in templates}) != len(templates) or len(numbers) != 25 or len(numbers) != len(set(numbers)) or set(numbers) != source_problem_numbers() or active != manifest_active:
        raise ClockTemplateError("Некорректный каталог или source accounting модуля часов")
    if any(template["generation_strategy"] not in STRATEGIES or template["answer_type"] != "integer" for template in templates):
        raise ClockTemplateError("Неизвестная стратегия или тип ответа")
    return list(templates)


def seconds_to_time(seconds: int) -> str:
    seconds %= 24 * 3600
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def _digits(seconds: int) -> str:
    return seconds_to_time(seconds).replace(":", "")


def _is_all_distinct(seconds: int) -> bool:
    digits = _digits(seconds)
    return len(set(digits)) == len(digits)


def _has_exactly_five_equal(seconds: int) -> bool:
    counts = Counter(_digits(seconds)).values()
    return max(counts) == 5


def nth_display_delta(start_seconds: int, predicate: Any, ordinal: int, direction: int) -> int:
    if not 0 <= start_seconds < 86400 or ordinal < 1 or direction not in (-1, 1):
        raise ClockTemplateError("Некорректные параметры поиска по табло")
    found = 0
    for delta in range(1, 86401):
        if predicate(start_seconds + direction * delta):
            found += 1
            if found == ordinal:
                return delta
    raise ClockTemplateError("За сутки не найдено требуемое состояние табло")


def backward_tower_meeting(first: date, first_hour: int, second: date, second_hour: int) -> int:
    earlier = (first - date(first.year, 1, 1)).days * 24 + first_hour
    later = (second - date(first.year, 1, 1)).days * 24 + second_hour
    gap = later - earlier
    if gap <= 0 or gap % 2:
        raise ClockTemplateError("Показания башенных часов не дают целой встречи")
    return gap // 2


def drifting_watch_meeting_days(initial_difference: int, relative_drift: int) -> int:
    if not 0 < relative_drift <= 1440 or 1440 % relative_drift:
        raise ClockTemplateError("Относительный ход часов должен делить сутки")
    for days in range(1, 1440 // math.gcd(relative_drift, 1440) + 1):
        if (initial_difference + relative_drift * days) % 1440 == 0:
            return days
    raise ClockTemplateError("Часы не встретятся в ожидаемом периоде")


def daily_schedule_true_hours(forward_hours: int, backward_hours: int) -> int:
    if not 1 <= forward_hours <= 23 or not 1 <= backward_hours <= 23:
        raise ClockTemplateError("Сдвиги суточного расписания вне диапазона")
    active = lambda hour: hour >= 12
    return sum(active((hour + forward_hours) % 24) == active((hour - backward_hours) % 24) for hour in range(24))


def cuckoo_strike_count(start_hour: int) -> int:
    if not 1 <= start_hour <= 12:
        raise ClockTemplateError("Час кукушки вне циферблата")
    return sum((start_hour + offset - 1) % 12 + 1 for offset in range(1, 13))


def reverse_clock_correct_count() -> int:
    return sum((2 * hour) % 12 == 0 for hour in range(24))


def _characters(rng: random.Random, count: int) -> tuple[str, list[Character]]:
    universe, characters = rng.choice(list(load_approved_characters().items()))
    return universe, rng.sample(characters, count)


def _make(template: dict[str, Any], text: str, answer: int, parameters: dict[str, Any], seed: int | None, universe: str | None = None, characters: list[Character] | None = None) -> GeneratedClockProblem:
    if not isinstance(answer, int) or "{" in text:
        raise ClockTemplateError(f"Невалидный результат template={template['id']}, seed={seed}")
    return GeneratedClockProblem(MODULE_ID, template["id"], template["source_problem_numbers"], text, answer, str(answer), parameters, seed, universe, [character.name for character in characters] if characters else None)


def _all_digits(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    start = rng.randrange(86400)
    ordinal = rng.randint(1, 10)
    direction = rng.choice((-1, 1))
    answer = nth_display_delta(start, _is_all_distinct, ordinal, direction)
    relation = "после" if direction == 1 else "до"
    text = f"На электронном табло {seconds_to_time(start)}. Через сколько секунд {relation} этого момента в {ordinal}-й раз все шесть цифр будут различными?"
    return _make(template, text, answer, {"start_time": seconds_to_time(start), "ordinal": ordinal, "direction": direction}, seed)


def _five_equal(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    start = rng.randrange(86400)
    direction = rng.choice((-1, 1))
    answer = nth_display_delta(start, _has_exactly_five_equal, 1, direction)
    relation = "после" if direction == 1 else "до"
    text = f"На электронном табло {seconds_to_time(start)}. Через сколько секунд {relation} этого момента впервые ровно пять из шести цифр будут одинаковыми?"
    return _make(template, text, answer, {"start_time": seconds_to_time(start), "direction": direction}, seed)


def _towers(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    year = rng.randint(2024, 2034)
    first = date(year, rng.randint(1, 11), rng.randint(1, 20))
    first_hour = rng.randint(0, 23)
    answer = rng.randint(12, 240)
    second_moment = datetime.combine(first, datetime.min.time()) + timedelta(hours=first_hour + answer * 2)
    second_hour = second_moment.hour
    solved = backward_tower_meeting(first, first_hour, second_moment.date(), second_hour)
    text = f"На часах первой башни {first.strftime('%d.%m.%Y')} {first_hour:02d}:00, и они идут правильно. На второй башне {second_moment.strftime('%d.%m.%Y')} {second_hour:02d}:00, но время идёт назад с той же скоростью. Через сколько часов даты и время на двух башнях совпадут?"
    return _make(template, text, solved, {"first_date": first.isoformat(), "first_hour": first_hour, "second_date": second_moment.date().isoformat(), "second_hour": second_hour}, seed)


def _drift(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    relative = rng.choice((20, 24, 30, 36, 40, 45, 48))
    period = 1440 // relative
    target_days = rng.randint(1, period - 1)
    difference = (-relative * target_days) % 1440
    first_reading = rng.randrange(1440)
    second_reading = (first_reading - difference) % 1440
    fast = rng.randint(5, relative - 5)
    slow = relative - fast
    universe, characters = _characters(rng, 2)
    first, second = characters
    solved = drifting_watch_meeting_days(difference, relative)
    text = f"{first.name} и {second.name} одновременно сверили часы. Первые часы показывают {seconds_to_time(first_reading)[:5]}, вторые — {seconds_to_time(second_reading)[:5]}. Первые спешат на {fast} минут в сутки, вторые отстают на {slow} минут в сутки. Через сколько суток часы впервые покажут одинаковое время?"
    parameters = {"first_reading": seconds_to_time(first_reading)[:5], "second_reading": seconds_to_time(second_reading)[:5], "fast_minutes_per_day": fast, "slow_minutes_per_day": slow, "initial_difference": difference, "role_mapping": {"first_owner": first.name, "second_owner": second.name}}
    return _make(template, text, solved, parameters, seed, universe, characters)


def _schedule(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    forward, backward = rng.randint(1, 11), rng.randint(1, 11)
    universe, characters = _characters(rng, 1)
    character = characters[0]
    answer = daily_schedule_true_hours(forward, backward)
    text = f"{character.name} живёт по суточному расписанию: с 00:00 до 12:00 отдыхает, с 12:00 до 24:00 занимается делом. Сколько целых часов в сутки верно утверждение: «Через {forward} часов будет то же занятие, что и {backward} часа назад»?"
    return _make(template, text, answer, {"forward_hours": forward, "backward_hours": backward, "role_mapping": {"character": character.name}}, seed, universe, characters)


def _cuckoo(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    hour, minute = rng.randint(1, 12), rng.randint(1, 59)
    universe, characters = _characters(rng, 1)
    character = characters[0]
    answer = cuckoo_strike_count(hour)
    text = f"{character.name} переводит минутную стрелку вперёд до возвращения часовой стрелки в прежнее положение. В начале было {hour:02d}:{minute:02d}. Кукушка в каждый полный час кукует столько раз, каков номер часа на циферблате. Сколько кукований прозвучит?"
    return _make(template, text, answer, {"start_hour": hour, "start_minute": minute, "role_mapping": {"character": character.name}}, seed, universe, characters)


def _reverse(template: dict[str, Any], rng: random.Random, seed: int | None) -> GeneratedClockProblem:
    universe, characters = _characters(rng, 1)
    character = characters[0]
    answer = reverse_clock_correct_count()
    text = f"{character.name} устанавливает аналоговые часы правильно ровно в полночь, но после этого обе стрелки идут назад с обычными скоростями. Сколько раз за следующие 24 часа часы покажут верное время?"
    return _make(template, text, answer, {"period_hours": 24, "role_mapping": {"character": character.name}}, seed, universe, characters)


STRATEGIES = {"all_digits_search": _all_digits, "five_equal_digits": _five_equal, "backward_towers": _towers, "drifting_watches": _drift, "daily_schedule": _schedule, "cuckoo_strikes": _cuckoo, "reverse_clock": _reverse}


def generate_clock_problem(template_id: str, *, seed: int | None = None, rng: random.Random | None = None) -> GeneratedClockProblem:
    templates = {template["id"]: template for template in load_clock_templates()}
    if template_id not in templates:
        raise ClockTemplateError(f"Неизвестный template={template_id}, seed={seed}")
    return STRATEGIES[templates[template_id]["generation_strategy"]](templates[template_id], rng or random.Random(seed), seed)


def generate_clock_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedClockProblem:
    if module_id != MODULE_ID:
        raise ClockTemplateError(f"Неизвестный модуль {module_id}")
    return generate_clock_problem(rng.choice(load_clock_templates())["id"], rng=rng)


def clock_template_metadata() -> dict[str, Any]:
    templates = load_clock_templates()
    return {"modules": [{"module_id": MODULE_ID, "title": "Clocks, Dials and Electronic Displays", "display_name": "Часы, циферблаты и электронные табло", "template_count": len(templates)}], "templates": [{"template_id": template["id"], "title": template["id"], "display_name": template["id"], "module_name": "Часы, циферблаты и электронные табло", "source_problem_numbers": template["source_problem_numbers"], "problem_type": template["generation_strategy"]} for template in templates], "stats": {"total_modules": 1, "total_templates": len(templates), "covered_source_problem_numbers": len(source_problem_numbers())}}
