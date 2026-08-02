"""Согласование существительного с числом во всех готовых условиях.

Правило русского языка без исключений: 1 — именительный единственного,
2–4 — родительный единственного, 5 и больше (а также 11–14) — родительный
множественного. Нарушение всегда означает, что слово зашито в текст шаблона
строкой вместо счётного слота `{noun:count,n}`.

Проверка появилась после аудита, который нашёл этот класс сразу в трёх местах:
«в 4 раз больше» вместо «в 4 раза», «за 22 минут» вместо «за 22 минуты»
и «32 белых шаров» вместо «32 белых шара». Все три прошли и валидацию,
и независимые решатели — те смотрят на числа, а не на язык.

Проверяются только слова из закрытого списка: те, что уже встречались
в условиях счётными. Расширять список полезно, но каждое новое слово должно
иметь три достоверные формы — иначе тест начнёт врать.
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

SEEDS = range(40)
# Пробел между числом и словом счётный слот ставит неразрывным.
SPACE = "[\\s ]+"

# лемма -> (форма при 1, форма при 2–4, форма при 5+)
FORMS: dict[str, tuple[str, str, str]] = {
    "раз": ("раз", "раза", "раз"),
    "минута": ("минуту", "минуты", "минут"),
    "день": ("день", "дня", "дней"),
    "час": ("час", "часа", "часов"),
    "год": ("год", "года", "лет"),
    "шар": ("шар", "шара", "шаров"),
    "штука": ("штука", "штуки", "штук"),
    "партия": ("партия", "партии", "партий"),
    "очко": ("очко", "очка", "очков"),
    "цифра": ("цифра", "цифры", "цифр"),
    "нога": ("нога", "ноги", "ног"),
    "голова": ("голова", "головы", "голов"),
}


def expected(lemma: str, number: int) -> str:
    """Какая форма обязана стоять при этом числе."""
    one, few, many = FORMS[lemma]
    if 11 <= number % 100 <= 14:
        return many
    return {1: one, 2: few, 3: few, 4: few}.get(number % 10, many)


class NumeralAgreementTests(unittest.TestCase):
    """Ни одно условие не должно ставить слово в форму, невозможную для числа."""

    def test_every_template_agrees_with_its_numbers(self) -> None:
        library = load_library()
        # Ищем «<число> <любая из трёх форм слова>» и сверяем с обязательной.
        patterns = {
            lemma: re.compile(
                # Дробь управляет родительным единственного по другому правилу
                # («1,5 часа»), поэтому число, входящее в дробь, не берём:
                # перед ним не должно быть цифры, запятой или точки.
                r"(?<![\d.,])(\d+)" + SPACE + "(" + "|".join(
                    # Длинные формы первыми: иначе «раз» съест префикс «раза».
                    sorted(set(forms), key=len, reverse=True)
                ) + r")\b"
            )
            for lemma, forms in FORMS.items()
        }
        # «17 января 2028 года» — это номер года, а не количество лет:
        # там родительный падеж от «2028 год», и правило счётных слов
        # к нему не применяется. Отличаем по величине числа и по тому,
        # что перед ним стоит название месяца.
        calendar_year = re.compile(
            r"(январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*"
            r"[\s\u00a0]+(19|20)\d\d[\s\u00a0]+год")
        offenders: list[str] = []
        for template in library:
            for seed in SEEDS:
                try:
                    text = generate_active_template(template, random.Random(seed))["rendered_problem"]
                except Exception:  # noqa: BLE001 — генерация проверяется другими тестами
                    continue
                masked = calendar_year.sub(" ", text)
                for lemma, pattern in patterns.items():
                    for raw_number, word in pattern.findall(masked):
                        number = int(raw_number)
                        want = expected(lemma, number)
                        if word != want:
                            offenders.append(
                                f"{template['template_id']} (seed {seed}): "
                                f"«{number} {word}», нужно «{number} {want}» — {text[:70]}"
                            )
        self.assertEqual(
            sorted(set(offenders))[:8], [],
            f"всего нарушений согласования: {len(set(offenders))}",
        )


if __name__ == "__main__":
    unittest.main()
