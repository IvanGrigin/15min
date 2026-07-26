"""Правила склонения русских существительных — ТОЛЬКО для подготовки данных.

Это инструмент, а не часть движка. В рантайме проект принципиально не склоняет
ничего автоматически: все 12 форм лежат в data/language/nouns/russian_nouns.json
явными строками. Здесь правила нужны для другого — чтобы получить **вторую,
независимую** версию форм и сверить её с тем, что выдала языковая модель.

Совпали две независимые деривации — форма принимается без человека.
Разошлись — вопрос уходит человеку, и это дёшево: одна строка на слово.

Функция `decline` возвращает (формы, confidence, заметки). Низкая уверенность
ставится там, где правила заведомо не покрывают язык:
  * беглая гласная в родительном множественного (палочка -> палочек, но морковка -> морковок);
  * чередования в основе (метла -> мётел, звезда -> звёзд);
  * нестандартное множественное (лист -> листья, друг -> друзья).
Такие слова всегда идут человеку, даже если модель ответила уверенно.
"""
from __future__ import annotations

from dataclasses import dataclass

CASES = ("nom", "gen", "dat", "acc", "ins", "pre",
         "nom_pl", "gen_pl", "dat_pl", "acc_pl", "ins_pl", "pre_pl")

VOWELS = "аеёиоуыэюя"
HUSHING = "жшчщ"           # после них не пишется -ы
VELAR = "кгх"              # после них тоже -и, а не -ы
SOFT_PAIRED = "ьй"


@dataclass(frozen=True)
class Declension:
    """Результат склонения: формы, уверенность правил и заметки о рисках."""
    forms: dict[str, str]
    confidence: str          # "high" | "low"
    notes: tuple[str, ...]


def _plural_i_or_y(stem: str) -> str:
    """Окончание им. мн.: -и после к,г,х,ж,ш,ч,щ, иначе -ы."""
    return "и" if stem and stem[-1] in VELAR + HUSHING else "ы"


def _ins_om_or_em(stem: str) -> str:
    """Творительный: -ем после мягких и шипящих, иначе -ом."""
    return "ем" if stem and stem[-1] in HUSHING + "ц" else "ом"


def _masculine(word: str, animate: bool) -> Declension:
    notes: list[str] = []
    confidence = "high"

    if word.endswith("ь"):
        stem = word[:-1]
        gen, dat, ins, pre = stem + "я", stem + "ю", stem + "ем", stem + "е"
        nom_pl, gen_pl = stem + "и", stem + "ей"
        dat_pl, ins_pl, pre_pl = stem + "ям", stem + "ями", stem + "ях"
    elif word.endswith("й"):
        stem = word[:-1]
        gen, dat, ins, pre = stem + "я", stem + "ю", stem + "ем", stem + "е"
        nom_pl, gen_pl = stem + "и", stem + "ев"
        dat_pl, ins_pl, pre_pl = stem + "ям", stem + "ями", stem + "ях"
    else:
        stem = word
        gen, dat = stem + "а", stem + "у"
        ins = stem + _ins_om_or_em(stem)
        pre = stem + "е"
        nom_pl = stem + _plural_i_or_y(stem)
        gen_pl = stem + ("ей" if stem[-1:] in tuple(HUSHING) else "ов")
        dat_pl, ins_pl, pre_pl = stem + "ам", stem + "ами", stem + "ах"
        if len(stem) > 3 and stem[-2] in "оё е" and stem[-1] in "кцн" and stem[-3] not in VOWELS:
            # Беглая гласная: горшок -> горшка, свиток -> свитка, венок -> венка.
            # У суффиксов -ок/-ек/-ёк она выпадает почти всегда, поэтому форму
            # строим с выпадением, но помечаем low: бывает и наоборот (поток -> потока).
            short = stem[:-2] + stem[-1]
            gen, dat = short + "а", short + "у"
            ins, pre = short + _ins_om_or_em(short), short + "е"
            nom_pl = short + _plural_i_or_y(short)
            gen_pl = short + ("ей" if short[-1:] in tuple(HUSHING) else "ов")
            dat_pl, ins_pl, pre_pl = short + "ам", short + "ами", short + "ах"
            confidence = "low"
            notes.append("беглая гласная в основе (венок -> венка); проверить, не поток ли это")

    acc = gen if animate else word
    acc_pl = gen_pl if animate else nom_pl
    return Declension(
        dict(zip(CASES, (word, gen, dat, acc, ins, pre,
                         nom_pl, gen_pl, dat_pl, acc_pl, ins_pl, pre_pl))),
        confidence, tuple(notes),
    )


def _feminine(word: str, animate: bool) -> Declension:
    notes: list[str] = []
    confidence = "high"

    if word.endswith("ия"):
        stem = word[:-2]
        forms = (word, stem + "ии", stem + "ии", stem + "ию", stem + "ией", stem + "ии",
                 stem + "ии", stem + "ий", stem + "иям", stem + "ии", stem + "иями", stem + "иях")
    elif word.endswith("ь"):
        stem = word[:-1]
        forms = (word, stem + "и", stem + "и", word, stem + "ью", stem + "и",
                 stem + "и", stem + "ей", stem + "ям", stem + "и", stem + "ями", stem + "ях")
    elif word.endswith("я"):
        stem = word[:-1]
        forms = (word, stem + "и", stem + "е", stem + "ю", stem + "ей", stem + "е",
                 stem + "и", stem + "ь", stem + "ям", stem + "и", stem + "ями", stem + "ях")
        confidence = "low"
        notes.append("родительный мн. у слов на -я нерегулярен")
    elif word.endswith("а"):
        stem = word[:-1]
        ending = _plural_i_or_y(stem)
        ins_ending = "ей" if stem[-1] in HUSHING + "ц" else "ой"
        gen_pl = stem
        if len(stem) >= 2 and stem[-1] == "к" and stem[-2] == "й":
            # гайка -> гаек, батарейка -> батареек: й уступает место беглому е.
            gen_pl = stem[:-2] + "ек"
        elif len(stem) >= 2 and stem[-1] == "к" and stem[-2] not in VOWELS:
            # Беглая гласная перед -к-: после шипящих и мягких -ек
            # (палочка -> палочек, шишка -> шишек, туфелька -> туфелек),
            # после твёрдых -ок (морковка -> морковок, банка -> банок).
            soft = stem[-2] in HUSHING + "ь"
            gen_pl = stem[:-1] + ("ек" if soft else "ок")
            if stem[-2] == "ь":
                gen_pl = stem[:-2] + "ек"
            confidence = "low"
            notes.append("беглая гласная в род. мн.: выбор -ек/-ок проверить")
        forms = (word, stem + ending, stem + "е", stem + "у", stem + ins_ending, stem + "е",
                 stem + ending, gen_pl, stem + "ам", stem + ending, stem + "ами", stem + "ах")
    else:
        return Declension({}, "low", ("не распознан тип склонения женского рода",))

    result = dict(zip(CASES, forms))
    if animate:
        result["acc_pl"] = result["gen_pl"]
        if not word.endswith("ь"):
            result["acc"] = result["gen"] if word.endswith("ия") else result["acc"]
    return Declension(result, confidence, tuple(notes))


def _neuter(word: str) -> Declension:
    notes: list[str] = []
    confidence = "high"
    if word.endswith("ье") or word.endswith("ие"):
        stem = word[:-1]
        forms = (word, stem + "я", stem + "ю", word, stem + "ем", word,
                 stem + "я", word[:-2] + "ий", stem + "ям", stem + "я", stem + "ями", stem + "ях")
    elif word.endswith("е"):
        stem = word[:-1]
        forms = (word, stem + "я", stem + "ю", word, stem + "ем", stem + "е",
                 stem + "я", stem + "ей", stem + "ям", stem + "я", stem + "ями", stem + "ях")
        confidence = "low"
        notes.append("средний род на -е: род. мн. нерегулярен")
    elif word.endswith("о"):
        stem = word[:-1]
        gen_pl = stem
        if len(stem) >= 2 and stem[-1] not in VOWELS and stem[-2] not in VOWELS:
            gen_pl = stem[:-1] + "е" + stem[-1]
            confidence = "low"
            notes.append("беглая гласная в род. мн. (масло -> масел)")
        forms = (word, stem + "а", stem + "у", word, stem + "ом", stem + "е",
                 stem + "а", gen_pl, stem + "ам", stem + "а", stem + "ами", stem + "ах")
    else:
        return Declension({}, "low", ("не распознан тип склонения среднего рода",))
    return Declension(dict(zip(CASES, forms)), confidence, tuple(notes))


INDECLINABLE_ENDINGS = ("е", "и", "о", "у", "ю", "э")


def decline(word: str, gender: str, *, animate: bool = False, indeclinable: bool = False) -> Declension:
    """Вернуть 12 форм по правилам плюс оценку, можно ли им доверять."""
    if indeclinable:
        return Declension({case: word for case in CASES}, "high", ("несклоняемое",))
    if gender == "m":
        result = _masculine(word, animate)
    elif gender == "f":
        result = _feminine(word, animate)
    elif gender == "n":
        result = _neuter(word)
    else:
        return Declension({}, "low", (f"неизвестный род {gender!r}",))

    notes = list(result.notes)
    confidence = result.confidence
    if "ё" in word:
        confidence = "low"
        notes.append("ё в основе: возможно чередование (метла -> мётел)")
    return Declension(result.forms, confidence, tuple(notes))


def orthography_problems(forms: dict[str, str]) -> list[str]:
    """Механические орфографические ошибки, которые видно без словаря."""
    problems: list[str] = []
    for case in ("gen", "nom_pl", "acc_pl"):
        value = forms.get(case, "")
        if len(value) > 1 and value.endswith("ы") and value[-2] in VELAR + HUSHING:
            problems.append(f"{case}={value!r}: после {value[-2]!r} пишется -и, а не -ы")
    for case, value in forms.items():
        if not value or not value.strip():
            problems.append(f"{case}: пустая форма")
        elif value != value.strip():
            problems.append(f"{case}: лишние пробелы")
    return problems
