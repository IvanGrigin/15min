from __future__ import annotations

from typing import Iterable

from .lexicon import NounForms


def pluralize_ru(number: int, forms: tuple[str, str, str]) -> str:
    number_abs = abs(number) % 100
    last_digit = number_abs % 10

    if 11 <= number_abs <= 14:
        return forms[2]
    if last_digit == 1:
        return forms[0]
    if 2 <= last_digit <= 4:
        return forms[1]
    return forms[2]


def count_with_word_ru(number: int, forms: tuple[str, str, str] | NounForms) -> str:
    if isinstance(forms, NounForms):
        forms_tuple = forms.as_tuple()
    else:
        forms_tuple = forms
    return f"{number} {pluralize_ru(number, forms_tuple)}"


def join_with_comma_and(words: Iterable[str]) -> str:
    items = [word.strip() for word in words if word and word.strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return " и ".join(items)
    return f"{', '.join(items[:-1])} и {items[-1]}"


def normalize_sentence(text: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return compact
    return compact[0].upper() + compact[1:]
