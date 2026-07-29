"""Декларативная проверка масштаба персонажа и сцены."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from problemgen.russian.characters import Character
from problemgen.russian.inflection import RussianNoun

_PATH = Path(__file__).resolve().parents[2] / "data" / "language" / "character_compatibility.json"


def _data() -> dict[str, Any]:
    return json.loads(_PATH.read_text(encoding="utf-8"))


def character_scene_compatible(character: Character, scene_scale: str) -> bool:
    """Не допустить непроверенного героя в размерно-чувствительную сцену."""
    profile = _data()["characters"].get(character.character_id, _data()["default_unreviewed"])
    return scene_scale in profile.get("allowed_scene_scales", [])


def noun_scene_compatible(noun: RussianNoun, scene_scale: str) -> bool:
    """Определить масштаб нейтрального существительного по явному тегу словаря."""
    profiles = _data()["noun_tag_profiles"]
    for tag in noun.tags:
        if tag in profiles:
            return scene_scale in profiles[tag]["allowed_scene_scales"]
    return False
