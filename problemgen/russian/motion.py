"""Способы передвижения: глаголы, единицы и правдоподобные скорости.

Персонаж знает, **как** он движется, а способ задаёт всё остальное. Без этого
слоя шаблон вынужден писать «шёл» и «км/ч» руками, и получается «Джек Воробей
шёл со скоростью 6 км/ч», «Молния Маккуин идёт 3 км/ч», «Тритона вёз Флаундер»
по суше. Проверка такое не ловит: текст синтаксически безупречен.

Чтобы добавить или поправить способ, редактируйте
    data/language/motion_profiles.json
Python-код менять не нужно.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PROFILES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "language" / "motion_profiles.json"
)
_GENDERS = ("m", "f", "n")


class MotionProfileError(ValueError):
    """Профиль передвижения нельзя загрузить или он неполон."""


@dataclass(frozen=True)
class MotionProfile:
    """Как двигается персонаж: глаголы, единицы и разброс скоростей."""

    key: str
    title: str
    self_past: dict[str, str]
    self_fast_past: dict[str, str]
    carry_past: dict[str, str]
    self_present: str
    speed_phrase: str
    distance_unit: str
    small_distance_unit: str
    small_per_main: int
    speed_min: int
    speed_max: int
    vehicle: str | None

    def verb(self, kind: str, gender: str) -> str:
        """Форма глагола по виду действия и роду персонажа."""
        table = {
            "past": self.self_past,
            "fast_past": self.self_fast_past,
            "carry_past": self.carry_past,
        }.get(kind)
        if table is None:
            raise MotionProfileError(
                f"Неизвестный вид действия {kind!r}; доступны past, fast_past, carry_past."
            )
        if gender not in table:
            raise MotionProfileError(f"{self.key}: нет формы рода {gender!r} для {kind}.")
        return table[gender]


def _verb_table(raw: object, key: str, field: str) -> dict[str, str]:
    if not isinstance(raw, dict) or any(gender not in raw for gender in _GENDERS):
        raise MotionProfileError(f"{key}: поле {field} должно содержать формы m, f и n.")
    return {gender: str(raw[gender]) for gender in _GENDERS}


@lru_cache(maxsize=1)
def load_motion_profiles() -> dict[str, MotionProfile]:
    """Загрузить и проверить профили передвижения."""
    payload = json.loads(_PROFILES_PATH.read_text(encoding="utf-8"))
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise MotionProfileError("motion_profiles.json: нет словаря 'profiles'.")

    result: dict[str, MotionProfile] = {}
    for key, entry in profiles.items():
        speed_min = int(entry.get("speed_min", 0))
        speed_max = int(entry.get("speed_max", 0))
        if not 0 < speed_min < speed_max:
            raise MotionProfileError(f"{key}: разброс скоростей должен быть 0 < min < max.")
        result[key] = MotionProfile(
            key=key,
            title=str(entry.get("title") or key),
            self_past=_verb_table(entry.get("self_past"), key, "self_past"),
            self_fast_past=_verb_table(entry.get("self_fast_past"), key, "self_fast_past"),
            carry_past=_verb_table(entry.get("carry_past"), key, "carry_past"),
            self_present=str(entry.get("self_present") or ""),
            speed_phrase=str(entry.get("speed_phrase") or ""),
            distance_unit=str(entry.get("distance_unit") or ""),
            small_distance_unit=str(entry.get("small_distance_unit") or ""),
            small_per_main=int(entry.get("small_per_main") or 1),
            speed_min=speed_min,
            speed_max=speed_max,
            vehicle=entry.get("vehicle") or None,
        )
    return result


def profile_for(key: str) -> MotionProfile:
    """Профиль по ключу способа передвижения."""
    profiles = load_motion_profiles()
    if key not in profiles:
        raise MotionProfileError(
            f"Неизвестный способ передвижения {key!r}. Доступны: {', '.join(sorted(profiles))}."
        )
    return profiles[key]
