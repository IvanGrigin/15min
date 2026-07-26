"""Реестр персонажей с полной падежной парадигмой.

Чтобы добавить персонажа, отредактируйте один из двух файлов:
    data/entities/characters/approved_characters.json  — персонажи франшиз
        (25 вселенных из Docs/approved_dimensions_150_characters.md)
    data/entities/characters/common_names.json          — обычные русские имена
        (Вася, Петя, Надя, ...), которыми названы герои большинства текстовых
        задач корпуса (деньги, доли, возраст) — они не привязаны ни к одной
        франшизе, поэтому это отдельный пул с sentinel-«вселенной» COMMON_POOL.
Python-код менять не нужно.

Отличие от `problemgen.generation.comparison_templates.load_approved_characters`:
там персонаж — это только (вселенная, имя, род-по-эвристике), здесь — шесть явных
падежных форм полного имени вместе с приложением («кота Матроскина»), явный род
и флаг несклоняемости.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_ENTITIES_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "entities" / "characters"
_FRANCHISE_REGISTRY_PATH = _ENTITIES_ROOT / "approved_characters.json"
_EXTENDED_REGISTRY_PATH = _ENTITIES_ROOT / "extended_characters.json"
_COMMON_NAMES_PATH = _ENTITIES_ROOT / "common_names.json"

# Синтетическая «вселенная» для обычных имён: они не сверяются со списком
# франшиз в Docs/approved_dimensions_150_characters.md, зато между собой
# свободно комбинируются в одной задаче — как и было в исходном корпусе.
COMMON_POOL = "Обычные имена"

_CASES = ("nom", "gen", "dat", "acc", "ins", "pre")
_GENDERS = frozenset({"m", "f", "n"})


class CharacterRegistryError(ValueError):
    """Реестр персонажей нельзя загрузить или он внутренне противоречив."""


@dataclass(frozen=True)
class Character:
    """Персонаж с явной падежной парадигмой единственного числа."""

    character_id: str
    universe: str
    gender: str
    animate: bool
    indeclinable: bool
    lowercase_start: bool
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
        """Вернуть форму по падежу. Совместимо с протоколом RussianNoun."""
        if case not in _CASES:
            raise ValueError(
                f"Для персонажа доступны только падежи единственного числа: {', '.join(_CASES)}; получено '{case}'."
            )
        return getattr(self, case)


def _entry_to_character(entry: dict, index: int, *, default_universe: str | None, source: Path) -> Character:
    def field(name: str, default=None):
        if name not in entry and default is None:
            raise CharacterRegistryError(f"{source.name} #{index}: нет обязательного поля '{name}'.")
        return entry.get(name, default)

    character_id = str(field("character_id"))
    gender = str(field("gender"))
    if gender not in _GENDERS:
        raise CharacterRegistryError(f"{character_id}: род должен быть одним из {sorted(_GENDERS)}.")
    cases = entry.get("cases")
    if not isinstance(cases, dict):
        raise CharacterRegistryError(f"{character_id}: поле 'cases' должно быть объектом с шестью формами.")
    missing = [case for case in _CASES if not str(cases.get(case, "")).strip()]
    if missing:
        raise CharacterRegistryError(f"{character_id}: не заполнены падежи: {', '.join(missing)}.")
    indeclinable = bool(entry.get("indeclinable", False))
    if indeclinable and len({cases[case] for case in _CASES}) != 1:
        raise CharacterRegistryError(f"{character_id}: помечен несклоняемым, но формы различаются.")
    universe = entry.get("universe") or default_universe
    if not universe:
        raise CharacterRegistryError(f"{character_id}: нет поля 'universe' и не задана вселенная по умолчанию.")
    return Character(
        character_id=character_id,
        universe=str(universe),
        gender=gender,
        animate=bool(entry.get("animate", True)),
        indeclinable=indeclinable,
        lowercase_start=bool(entry.get("lowercase_start", False)),
        **{case: str(cases[case]) for case in _CASES},
    )


def _load_from(path: Path, *, default_universe: str | None) -> tuple[Character, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("characters")
    if not isinstance(entries, list) or not entries:
        raise CharacterRegistryError(f"{path.name}: в файле нет ни одной записи 'characters'.")
    return tuple(
        _entry_to_character(entry, index, default_universe=default_universe, source=path)
        for index, entry in enumerate(entries)
    )


_MARKDOWN_CANON_PATH = (
    Path(__file__).resolve().parent.parent.parent / "Docs" / "approved_dimensions_150_characters.md"
)
_MARKDOWN_ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|$")


@lru_cache(maxsize=1)
def canonical_markdown_names() -> dict[str, frozenset[str]]:
    """Вселенная -> имена из Docs/approved_dimensions_150_characters.md.

    Канонический список 25 франшиз ведётся в markdown вручную. Реестр падежей
    обязан ему соответствовать — за этим следит тест. Раньше парсер жил
    в problemgen/generation/comparison_templates.py; тот модуль заархивирован
    (см. Docs/ARCHIVED_LEGACY.md), поэтому разбор переехал сюда, к данным.
    """
    universes: dict[str, frozenset[str]] = {}
    for line in _MARKDOWN_CANON_PATH.read_text(encoding="utf-8").splitlines():
        match = _MARKDOWN_ROW_RE.match(line)
        if match:
            universes[match.group(1).strip()] = frozenset(
                name.strip() for name in match.group(2).split(";")
            )
    if not universes:
        raise CharacterRegistryError(
            f"Не удалось разобрать канонический список: {_MARKDOWN_CANON_PATH}"
        )
    return universes


@lru_cache(maxsize=1)
def canonical_universes() -> frozenset[str]:
    """Вселенные из markdown-канона: только они сверяются с Docs/."""
    return frozenset(
        character.universe
        for character in _load_from(_FRANCHISE_REGISTRY_PATH, default_universe=None)
    )


@lru_cache(maxsize=1)
def load_characters() -> tuple[Character, ...]:
    """Персонажи канона + расширенные миры + обычные имена в одном реестре."""
    characters = _load_from(_FRANCHISE_REGISTRY_PATH, default_universe=None)
    if _EXTENDED_REGISTRY_PATH.is_file():
        # Миры за пределами списка 25 франшиз: Disney сверх канона, Гравити Фолз,
        # мифы Древней Греции, легенды, сказки народов мира. Они намеренно
        # не сверяются с Docs/approved_dimensions_150_characters.md — тот файл
        # фиксирует исходный канон, а не потолок реестра.
        characters += _load_from(_EXTENDED_REGISTRY_PATH, default_universe=None)
    if _COMMON_NAMES_PATH.is_file():
        characters += _load_from(_COMMON_NAMES_PATH, default_universe=COMMON_POOL)
    identifiers = [character.character_id for character in characters]
    duplicates = {identifier for identifier in identifiers if identifiers.count(identifier) > 1}
    if duplicates:
        raise CharacterRegistryError(f"Повторяющиеся character_id: {', '.join(sorted(duplicates))}.")
    return characters


def franchise_characters() -> tuple[Character, ...]:
    """Только персонажи франшиз — для сверки со списком в Docs/."""
    return tuple(character for character in load_characters() if character.universe != COMMON_POOL)


@lru_cache(maxsize=1)
def characters_by_universe() -> dict[str, tuple[Character, ...]]:
    grouped: dict[str, list[Character]] = {}
    for character in load_characters():
        grouped.setdefault(character.universe, []).append(character)
    return {universe: tuple(items) for universe, items in grouped.items()}


def universes_with_at_least(count: int) -> tuple[str, ...]:
    """Вселенные, где хватает персонажей с готовыми падежами."""
    return tuple(
        sorted(
            universe
            for universe, characters in characters_by_universe().items()
            if len(characters) >= count
        )
    )
