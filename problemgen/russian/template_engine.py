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

    {key:g,муж|жен}     Форма по роду объекта из context[key].
    {key:g,муж|жен|ср}  Для глаголов прошедшего времени и кратких прилагательных:
                        "{hero:g,купил|купила}", "{hero:g,должен|должна}".
                        key → объект с атрибутом gender ("m" | "f" | "n").
                        Словарь глаголов при этом не нужен: обе формы пишет
                        автор шаблона, а валидатор проверяет, что их ровно две
                        (или три).

    {count:verb,ед|мн}  Сказуемое, зависящее от числительного:
                        "1 из них состоит", "22 из них состоят".

Падежные слоты работают и с персонажами: подойдёт любой объект с методом
``get_case(case)`` — RussianNoun или problemgen.russian.characters.Character.

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
from fractions import Fraction
from typing import Any

from .agreement import pluralize_ru
from .inflection import RussianNoun

_SLOT_RE = re.compile(r"\{([^}]+)\}")


def format_scalar(value: Any) -> str:
    """Строковое представление числа по русским правилам записи.

    Дробная часть отделяется запятой («15,5 км»), точные дроби печатаются
    как обыкновенные («3/4»), целые float приводятся к int.
    """
    if isinstance(value, (list, tuple)):
        return ", ".join(format_scalar(item) for item in value)
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}".replace(".", ",")
    return str(value)


def _render_slot(content: str, context: dict[str, Any]) -> str:
    content = content.strip()

    if ":" not in content:
        key = content
        if key not in context:
            raise KeyError(f"Ключ '{key}' не найден в контексте шаблона.")
        return format_scalar(context[key])

    key, spec = content.split(":", 1)
    key = key.strip()
    spec = spec.strip()

    if key not in context:
        raise KeyError(f"Ключ '{key}' не найден в контексте шаблона.")

    if "," in spec:
        op, numkey = spec.split(",", 1)
        op = op.strip()
        numkey = numkey.strip()

        if op == "g":
            return _render_gender_choice(key, numkey, context[key])

        if op == "move":
            mover = context[key]
            if not hasattr(mover, "move"):
                raise TypeError(
                    f"Слот '{key}:move,...' ожидает персонажа, получено {type(mover).__name__}."
                )
            return mover.move(numkey)

        if op == "verb":
            return _render_count_verb(key, numkey, context[key])

        if numkey not in context:
            raise KeyError(f"Числовой ключ '{numkey}' не найден в контексте шаблона.")
        raw_number = context[numkey]
        noun = context[key]
        if not isinstance(noun, RussianNoun):
            raise TypeError(
                f"Слот '{key}:count/agree,...' ожидает RussianNoun, получено {type(noun).__name__}."
            )
        if _is_integral(raw_number):
            number: Any = int(raw_number)
            form = pluralize_ru(number, noun.count_forms())
        else:
            # Дробное количество управляет родительным падежом ед. ч.: «2,5 часа».
            number = raw_number
            form = noun.gen

        if op == "count":
            return f"{format_scalar(number)} {form}"  # неразрывный пробел между числом и словом
        if op == "agree":
            return form
        raise ValueError(f"Неизвестная операция '{op}'. Допустимые: count, agree, g, move.")

    value = context[key]
    if spec == "clock":
        # Минуты и часы на табло пишутся в два знака: «12:05», а не «12:5».
        # Форматирование общее для всех шаблонов про время, поэтому живёт здесь,
        # а не в виде отдельного derived-выражения у каждого автора.
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 99:
            raise TypeError(
                f"Слот '{key}:clock' ожидает целое от 0 до 99, получено {value!r}."
            )
        return f"{value:02d}"
    if spec == "speed_phrase":
        if not hasattr(value, "motion"):
            raise TypeError(f"Слот '{key}:speed_phrase' ожидает персонажа.")
        from .motion import profile_for as _profile_for

        return _profile_for(value.motion).speed_phrase
    if not hasattr(value, "get_case"):
        raise TypeError(
            f"Слот '{key}:{spec}' ожидает объект с падежной парадигмой "
            f"(RussianNoun или Character), получено {type(value).__name__}."
        )
    if spec == "with":
        return f"{_s_or_so(value.get_case('ins'))} {value.get_case('ins')}"
    return value.get_case(spec)


def _s_or_so(instrumental: str) -> str:
    """Выбор между предлогами «с» и «со» перед творительным падежом.

    «со» ставится перед стечением согласных, начинающимся на с, з, ш, ж:
    со Свеном, со Знайкой, со шляпой, но с Кристоффом и с Нюшей.
    Правило работает на форму, а не на лемму, поэтому живёт рядом с рендером.
    """
    word = instrumental.lstrip()
    if len(word) < 2:
        return "с"
    first, second = word[0].lower(), word[1].lower()
    vowels = "аеёиоуыэюя"
    if first in "сзшж" and second not in vowels and second != "ь":
        return "со"
    if word[:2].lower() == "мн":
        return "со"
    return "с"


def _is_integral(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, Fraction):
        return value.denominator == 1
    if isinstance(value, float):
        return value.is_integer()
    if isinstance(value, str):
        return value.strip().lstrip("-").isdigit()
    return False


_GENDER_INDEX = {"m": 0, "f": 1, "n": 2}


def _render_gender_choice(key: str, variants_spec: str, value: Any) -> str:
    """Выбрать форму по роду: '{hero:g,купил|купила}'."""
    variants = [variant.strip() for variant in variants_spec.split("|")]
    if len(variants) not in (2, 3) or any(not variant for variant in variants):
        raise ValueError(
            f"Слот '{key}:g,...' требует две или три непустые формы через '|', получено: {variants_spec!r}."
        )
    gender = getattr(value, "gender", None)
    if gender not in _GENDER_INDEX:
        raise TypeError(
            f"Слот '{key}:g,...' ожидает объект с полем gender ('m'/'f'/'n'), "
            f"получено {type(value).__name__}."
        )
    index = _GENDER_INDEX[gender]
    if index >= len(variants):
        raise ValueError(
            f"Слот '{key}:g,...': для среднего рода нужна третья форма, указано только {len(variants)}."
        )
    return variants[index]


def _render_count_verb(key: str, variants_spec: str, value: Any) -> str:
    """Выбрать единственное или множественное сказуемое по числу.

    После количественной группы «21 из них» сказуемое стоит в единственном
    числе, а после «22 из них» — во множественном. Для дробей и нечисловых
    значений выбор невозможен: это ошибка данных шаблона, а не повод молча
    подставить произвольную форму.
    """
    variants = [variant.strip() for variant in variants_spec.split("|")]
    if len(variants) != 2 or any(not variant for variant in variants):
        raise ValueError(
            f"Слот '{key}:verb,...' требует две непустые формы через '|', получено: {variants_spec!r}."
        )
    if not _is_integral(value):
        raise TypeError(f"Слот '{key}:verb,...' ожидает целое число, получено {value!r}.")
    number = abs(int(value))
    singular = number % 10 == 1 and number % 100 != 11
    return variants[0] if singular else variants[1]


def render_template(template: str, context: dict[str, Any]) -> str:
    """Отрендерить строку шаблона, подставив значения из контекста.

    Args:
        template: Строка с морфологическими слотами вида ``{key:case}``.
        context: Словарь: строковые ключи → значения (int, str, RussianNoun).

    Returns:
        Готовый текст задачи с заглавной буквой в начале.
    """
    result = _SLOT_RE.sub(lambda m: _render_slot(m.group(1), context), template)
    return capitalize_sentences(result)


_SENTENCE_START_RE = re.compile(r"(^|(?<=[.!?])\s+)([а-яёa-z])")


def capitalize_sentences(text: str) -> str:
    """Заглавная буква в начале текста и после каждой точки.

    Нужна из-за персонажей со строчным началом имени («кот Матроскин»):
    в середине фразы имя остаётся строчным, а в начале предложения — нет.
    """
    return _SENTENCE_START_RE.sub(lambda match: match.group(1) + match.group(2).upper(), text)
