"""Вселенные: группы, локации с падежами и предметы, уместные в мире.

Чтобы добавить вселенную, локацию или предмет, отредактируйте
    data/entities/universes.json
Python-код менять не нужно.

Локация ведёт себя так же, как персонаж и существительное: у неё есть шесть форм
единственного числа и метод ``get_case``, поэтому она подставляется в те же слоты
шаблона — ``{place:pre}``, ``{place:acc}``. Дополнительно у локации есть предлог
(«в» или «на»), потому что его нельзя вывести из формы слова: «в Хогвартсе», но
«на пляже». Слот ``{place:loc}`` подставляет предлог вместе с предложным падежом.

Предметы хранятся леммами: сами формы лежат в словаре существительных, здесь —
только принадлежность миру, чтобы в Простоквашино не появился световой меч.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .noun_dict import NOUNS

_UNIVERSES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "entities" / "universes.json"

_CASES = ("nom", "gen", "dat", "acc", "ins", "pre")
_PREPOSITIONS = frozenset({"в", "на"})
_GENDERS = frozenset({"m", "f", "n"})


class UniverseRegistryError(ValueError):
    """Реестр вселенных нельзя загрузить или он внутренне противоречив."""


@dataclass(frozen=True)
class Location:
    """Локация с явной падежной парадигмой и предлогом употребления."""

    location_id: str
    universe: str
    preposition: str
    gender: str
    nom: str
    gen: str
    dat: str
    acc: str
    ins: str
    pre: str

    @property
    def name(self) -> str:
        return self.nom

    def get_case(self, case: str) -> str:
        """Форма по падежу плюс два составных слота с предлогом.

        ``loc`` — где: предлог + предложный падеж («в Хогвартсе», «на пляже»).
        ``dir`` — куда: тот же предлог + винительный («в Хогвартс», «на пляж»).
        Разделять их обязательно: «отправился в Хижине чудес» — сломанный текст.
        """
        if case == "loc":
            return f"{self.preposition} {self.pre}"
        if case == "dir":
            return f"{self.preposition} {self.acc}"
        if case not in _CASES:
            raise ValueError(
                "Для локации доступны падежи единственного числа "
                f"({', '.join(_CASES)}), 'loc' (где) и 'dir' (куда); получено '{case}'."
            )
        return getattr(self, case)


@dataclass(frozen=True)
class Universe:
    universe: str
    group: str
    locations: tuple[Location, ...]
    items: tuple[str, ...]


def _location_from(entry: dict, universe: str) -> Location:
    location_id = str(entry.get("location_id") or "")
    if not location_id:
        raise UniverseRegistryError(f"{universe}: у локации нет 'location_id'.")
    preposition = str(entry.get("preposition") or "")
    if preposition not in _PREPOSITIONS:
        raise UniverseRegistryError(
            f"{location_id}: предлог должен быть одним из {sorted(_PREPOSITIONS)}, получено {preposition!r}."
        )
    gender = str(entry.get("gender") or "")
    if gender not in _GENDERS:
        raise UniverseRegistryError(f"{location_id}: род должен быть одним из {sorted(_GENDERS)}.")
    cases = entry.get("cases")
    if not isinstance(cases, dict):
        raise UniverseRegistryError(f"{location_id}: поле 'cases' должно быть объектом с шестью формами.")
    missing = [case for case in _CASES if not str(cases.get(case, "")).strip()]
    if missing:
        raise UniverseRegistryError(f"{location_id}: не заполнены падежи: {', '.join(missing)}.")
    return Location(
        location_id=location_id,
        universe=universe,
        preposition=preposition,
        gender=gender,
        **{case: str(cases[case]) for case in _CASES},
    )


@lru_cache(maxsize=1)
def load_universes() -> dict[str, Universe]:
    payload = json.loads(_UNIVERSES_PATH.read_text(encoding="utf-8"))
    groups = payload.get("groups")
    if not isinstance(groups, dict) or not groups:
        raise UniverseRegistryError("universes.json: нет словаря 'groups'.")
    entries = payload.get("universes")
    if not isinstance(entries, list) or not entries:
        raise UniverseRegistryError("universes.json: нет списка 'universes'.")

    registry: dict[str, Universe] = {}
    seen_location_ids: set[str] = set()
    for entry in entries:
        name = str(entry.get("universe") or "")
        if not name:
            raise UniverseRegistryError("universes.json: у вселенной нет поля 'universe'.")
        if name in registry:
            raise UniverseRegistryError(f"Вселенная {name!r} описана дважды.")
        group = str(entry.get("group") or "")
        if group not in groups:
            raise UniverseRegistryError(f"{name}: группы {group!r} нет в 'groups'.")
        locations = tuple(_location_from(item, name) for item in entry.get("locations", []))
        if not locations:
            raise UniverseRegistryError(f"{name}: не задано ни одной локации.")
        for location in locations:
            if location.location_id in seen_location_ids:
                raise UniverseRegistryError(f"Повторяющийся location_id: {location.location_id}.")
            seen_location_ids.add(location.location_id)
        items = tuple(str(item) for item in entry.get("items", []))
        unknown = [item for item in items if item not in NOUNS]
        if unknown:
            raise UniverseRegistryError(
                f"{name}: предметов нет в словаре существительных: {', '.join(unknown)}."
            )
        # Предметы вселенной попадают в счётные слоты («у Кроша 5 пирогов»),
        # поэтому вещественные слова сюда нельзя: «5 мёдов» — сломанный текст.
        uncountable = [item for item in items if not NOUNS[item].countable]
        if uncountable:
            raise UniverseRegistryError(
                f"{name}: вещественные существительные нельзя класть в items: {', '.join(uncountable)}."
            )
        registry[name] = Universe(universe=name, group=group, locations=locations, items=items)
    return registry


def universe_groups() -> dict[str, str]:
    """Ключ группы -> человекочитаемое название."""
    payload = json.loads(_UNIVERSES_PATH.read_text(encoding="utf-8"))
    return dict(payload["groups"])


def locations_of(universe: str) -> tuple[Location, ...]:
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].locations


def items_of(universe: str) -> tuple[str, ...]:
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].items


def universes_in_group(group: str) -> tuple[str, ...]:
    return tuple(sorted(name for name, universe in load_universes().items() if universe.group == group))
