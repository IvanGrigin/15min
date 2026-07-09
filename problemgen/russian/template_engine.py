"""Движок рендеринга шаблонов задач с русской морфологией.

Синтаксис слотов
----------------
Слот — это фрагмент вида ``{...}`` внутри строки шаблона.

    {key}               Прямая подстановка: str(context[key])

    {key:case}          Форма существительного по падежу.
                        key → RussianNoun в context.
                        case — одно из:
                          ед.ч.: nom  gen  dat  acc  ins  pre
                          мн.ч.: nom_pl  gen_pl  dat_pl
                                 acc_pl  ins_pl  pre_pl

    {key:count,numkey}  Число + согласованная форма существительного.
                        key → RussianNoun, numkey → int.
                        Результат: "36 голов", "1 нога", "22 ноги".

    {key:agree,numkey}  Только согласованная форма без числа.
                        Результат: "голов", "нога", "ноги".

Пример
------
    from problemgen.russian.template_engine import render_template
    from problemgen.russian.noun_dict import NOUNS

    text = render_template(
        "У {a1:gen_pl} и {a2:gen_pl} вместе {HEAD:count,h} и {LEG:count,l}.",
        {
            "a1": NOUNS["овца"],
            "a2": NOUNS["курица"],
            "HEAD": NOUNS["голова"],
            "LEG": NOUNS["нога"],
            "h": 36,
            "l": 100,
        }
    )
    # → "У овец и кур вместе 36 голов и 100 ног."
"""
from __future__ import annotations

import re
from typing import Any

from .agreement import pluralize_ru
from .inflection import RussianNoun

_SLOT_RE = re.compile(r"\{([^}]+)\}")


def _render_slot(content: str, context: dict[str, Any]) -> str:
    content = content.strip()

    if ":" not in content:
        key = content
        if key not in context:
            raise KeyError(f"Ключ '{key}' не найден в контексте шаблона.")
        return str(context[key])

    key, spec = content.split(":", 1)
    key = key.strip()
    spec = spec.strip()

    if key not in context:
        raise KeyError(f"Ключ '{key}' не найден в контексте шаблона.")

    if "," in spec:
        op, numkey = spec.split(",", 1)
        op = op.strip()
        numkey = numkey.strip()

        if numkey not in context:
            raise KeyError(f"Числовой ключ '{numkey}' не найден в контексте шаблона.")
        number = int(context[numkey])
        noun = context[key]
        if not isinstance(noun, RussianNoun):
            raise TypeError(
                f"Слот '{key}:count/agree,...' ожидает RussianNoun, получено {type(noun).__name__}."
            )
        form = pluralize_ru(number, noun.count_forms())

        if op == "count":
            return f"{number} {form}"  # неразрывный пробел между числом и словом
        if op == "agree":
            return form
        raise ValueError(f"Неизвестная операция '{op}'. Допустимые: count, agree.")

    noun = context[key]
    if not isinstance(noun, RussianNoun):
        raise TypeError(
            f"Слот '{key}:{spec}' ожидает RussianNoun, получено {type(noun).__name__}."
        )
    return noun.get_case(spec)


def render_template(template: str, context: dict[str, Any]) -> str:
    """Отрендерить строку шаблона, подставив значения из контекста.

    Args:
        template: Строка с морфологическими слотами вида ``{key:case}``.
        context: Словарь: строковые ключи → значения (int, str, RussianNoun).

    Returns:
        Готовый текст задачи с заглавной буквой в начале.
    """
    result = _SLOT_RE.sub(lambda m: _render_slot(m.group(1), context), template)
    if result:
        result = result[0].upper() + result[1:]
    return result
