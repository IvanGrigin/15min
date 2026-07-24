"""Проверенные формы approved-персонажей без эвристического склонения."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FORMS_PATH = ROOT / "data" / "language" / "characters" / "reviewed_character_forms.json"


class CharacterFormError(ValueError):
    """Запрошена форма, которой нет в проверенном словаре."""


@lru_cache(maxsize=1)
def reviewed_character_forms() -> dict[str, dict]:
    return json.loads(FORMS_PATH.read_text(encoding="utf-8"))["records"]


def supports_cases(name: str, *cases: str) -> bool:
    record = reviewed_character_forms().get(name)
    return bool(record and all(case in record["forms"] for case in cases))


def character_form(name: str, case: str = "nom") -> str:
    try:
        return reviewed_character_forms()[name]["forms"][case]
    except KeyError as error:
        raise CharacterFormError(f"Нет проверенной формы {case} для «{name}».") from error


def character_gender(name: str) -> str:
    try:
        return str(reviewed_character_forms()[name]["gender"])
    except KeyError as error:
        raise CharacterFormError(f"Нет проверенного рода для «{name}».") from error


def personal_pronoun(name: str, case: str) -> str:
    gender = character_gender(name)
    forms = {
        "male": {"nom": "он", "gen": "его", "dat": "ему", "acc": "его"},
        "female": {"nom": "она", "gen": "её", "dat": "ей", "acc": "её"},
    }
    return forms[gender][case]
