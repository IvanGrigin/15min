"""Словарь русских существительных — загружается из JSON-библиотеки.

Чтобы добавить новое слово, отредактируйте:
    data/language/nouns/russian_nouns.json
Python-код менять не нужно.
"""
from __future__ import annotations

import json
from pathlib import Path

from .inflection import RussianNoun

_NOUN_JSON = (
    Path(__file__).resolve().parent.parent.parent
    / "data" / "language" / "nouns" / "russian_nouns.json"
)


def _load() -> dict[str, RussianNoun]:
    data = json.loads(_NOUN_JSON.read_text(encoding="utf-8"))
    result: dict[str, RussianNoun] = {}
    for key, entry in data["nouns"].items():
        f = entry["forms"]
        cf = entry.get("count_forms", [])
        result[key] = RussianNoun(
            nom=f["nom"], gen=f["gen"], dat=f["dat"],
            acc=f["acc"], ins=f["ins"], pre=f["pre"],
            nom_pl=f["nom_pl"], gen_pl=f["gen_pl"], dat_pl=f["dat_pl"],
            acc_pl=f["acc_pl"], ins_pl=f["ins_pl"], pre_pl=f["pre_pl"],
            gender=entry["gender"],
            animate=entry.get("animate", False),
            count_one=cf[0] if len(cf) > 0 else "",
            count_few=cf[1] if len(cf) > 1 else "",
            count_many=cf[2] if len(cf) > 2 else "",
        )
    return result


NOUNS: dict[str, RussianNoun] = _load()


def get_noun(name: str) -> RussianNoun:
    """Получить существительное по начальной форме (им. пад. ед.ч.)."""
    try:
        return NOUNS[name]
    except KeyError:
        available = ", ".join(sorted(NOUNS))
        raise KeyError(
            f"Существительное '{name}' не найдено. "
            f"Доступно: {available}"
        ) from None
