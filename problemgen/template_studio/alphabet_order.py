"""Задачи о вымышленном алфавите: «язык из букв И, В, А, Н».

Сюжет модуля один и тот же. Есть язык из нескольких букв, настоящий порядок
букв в его алфавите неизвестен. Все слова заданной длины выписаны в этом
неизвестном порядке, и про одно из них сказано, на каком оно месте. По этой
подсказке нужно восстановить порядок букв и ответить на вопрос: какое слово
первое, какое двадцатое, какое идёт сразу после данного.

Почему для этого понадобился Python, хотя правило проекта — «условие в JSON».
Правило гласит, что JSON формулирует, а Python решает; язык выражений в
`safe_expressions` намеренно не умеет ни индексации, ни сортировки, ни
операций над строками, и «отсортируй 24 слова по такому-то порядку букв и
возьми третье» в нём невыразимо. Пока такого решателя не было, все пять
шаблонов темы приходилось писать перебором заранее посчитанных случаев:
один параметр `case ∈ {1, 2}` и все слова строками в `derived_values`.
Вся тема давала ровно десять разных листочков.

Здесь считает Python, а JSON по-прежнему только формулирует: он объявляет
буквы, длину слова, место подсказки и сам вопрос, а весь текст условия
остаётся в `candidate_template_text`.

Ключевая тонкость — однозначность. Подсказка сужает круг возможных алфавитов,
но не всегда до одного. Ответ здесь — всегда множество слов, возможных при
всех алфавитах, совместимых с подсказкой:

* если множество из одного слова, задача корректна и ключ единственный;
* если больше, вопрос честно звучит «какое слово *может* быть последним»,
  и в ключ должны попасть все варианты.

Молча печатать одно слово из нескольких верных нельзя: ребёнок, ответивший
вторым, прав, а получит крестик. Именно так и было в `alphabet_repetition_last`
до этого модуля.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations, product

# Пять букв — это 120 алфавитов и 120 слов без повторений: столько встречается
# в источнике («язык Ралины» из А, Р, И, Л, Н) и столько считается мгновенно.
# Шесть букв дали бы 720 алфавитов и 46 656 слов с повторениями на каждый
# вызов; такой задачи в корпусе нет, а перебор стал бы заметен.
MAX_LETTERS = 5
MAX_WORDS = 4096
QUESTION_KINDS = frozenset({"position", "after", "before", "first", "last"})


class AlphabetOrderError(ValueError):
    """Описание алфавитной задачи нельзя разыграть или решить."""


class AlphabetRangeError(AlphabetOrderError):
    """Выпавшее место больше, чем слов в языке, — неудачный жребий.

    Отдельный класс нужен, потому что языки в одном шаблоне бывают разной
    длины: четырёхбуквенный даёт 24 слова, пятибуквенный — 120. Место
    разыгрывается одним диапазоном на всех, и «120-е слово в языке из
    четырёх букв» означает «разыграть заново», а не «шаблон сломан».
    """


@dataclass(frozen=True)
class LanguageOwner:
    """Тот, кто придумал язык: «Иван придумал», «Таня придумала».

    Буквы языка — анаграмма его имени, поэтому имя и набор букв меняются
    только вместе и лежат в одной записи данных. В шаблоне это один параметр:
    ``{abc_owner}`` даёт имя, ``{abc_owner:g,придумал|придумала}`` — форму
    глагола. Род берётся из данных: выводить его из имени нельзя, «Боря»
    кончается на «я», как и «Таня».
    """

    name: str
    gender: str

    def __str__(self) -> str:
        return self.name


def check_languages(raw: object) -> tuple[tuple[LanguageOwner, tuple[str, ...]], ...]:
    """Проверить список языков: у каждого владелец, его род и буквы."""
    if not isinstance(raw, (list, tuple)) or not raw:
        raise AlphabetOrderError("Поле languages — непустой список описаний языков.")
    checked = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise AlphabetOrderError("Описание языка должно быть объектом.")
        name = entry.get("owner")
        gender = entry.get("gender")
        if not isinstance(name, str) or not name:
            raise AlphabetOrderError("У языка должно быть непустое имя владельца.")
        if gender not in {"m", "f", "n"}:
            raise AlphabetOrderError(f"Род владельца языка {name!r} должен быть 'm', 'f' или 'n'.")
        checked.append((LanguageOwner(name, gender), check_letters(entry.get("letters"))))
    return tuple(checked)


def check_letters(letters: object) -> tuple[str, ...]:
    """Проверить набор букв языка и вернуть его кортежем."""
    if not isinstance(letters, (list, tuple)) or not letters:
        raise AlphabetOrderError("Буквы языка задаются непустым списком.")
    checked = []
    for letter in letters:
        if not isinstance(letter, str) or len(letter) != 1:
            raise AlphabetOrderError(f"Буква языка должна быть одним символом, получено {letter!r}.")
        checked.append(letter)
    if len(set(checked)) != len(checked):
        raise AlphabetOrderError("Буквы языка не должны повторяться.")
    if len(checked) > MAX_LETTERS:
        raise AlphabetOrderError(f"Букв в языке не больше {MAX_LETTERS}.")
    return tuple(checked)


def check_length(length: object, letters: tuple[str, ...], repetitions: bool) -> int:
    """Проверить длину слова и посильность полного перебора."""
    if not isinstance(length, int) or isinstance(length, bool) or length < 2:
        raise AlphabetOrderError("Длина слова — целое число не меньше двух.")
    if not repetitions and length != len(letters):
        # Без повторений слово — перестановка всех букв: «все 24 слова из
        # четырёх различных букв». Слово короче набора означало бы другую
        # задачу (размещения), которой в источнике нет.
        raise AlphabetOrderError(
            "Без повторений длина слова равна числу букв языка: "
            f"букв {len(letters)}, длина {length}."
        )
    total = len(letters) ** length if repetitions else _factorial(len(letters))
    if total > MAX_WORDS:
        raise AlphabetOrderError(f"Слов получается {total}, больше предела {MAX_WORDS}.")
    return length


def _factorial(value: int) -> int:
    result = 1
    for step in range(2, value + 1):
        result *= step
    return result


def word_count(letters: tuple[str, ...], length: int, repetitions: bool) -> int:
    """Сколько всего слов выписывается — число из текста условия."""
    return len(letters) ** length if repetitions else _factorial(len(letters))


@lru_cache(maxsize=128)
def all_orderings(
    letters: tuple[str, ...], length: int, repetitions: bool
) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    """Для каждого порядка букв — все слова, выписанные в этом порядке.

    Возвращает пары (порядок букв, слова по возрастанию). Кешируется: наборов
    букв в библиотеке единицы, а обращений при генерации и в тестах — тысячи.
    """
    raw = product(letters, repeat=length) if repetitions else permutations(letters, length)
    words = tuple("".join(item) for item in raw)
    result = []
    for order in permutations(letters):
        rank = {letter: index for index, letter in enumerate(order)}
        ordered = tuple(sorted(words, key=lambda word: [rank[letter] for letter in word]))
        result.append((order, ordered))
    return tuple(result)


def word_at(
    order: tuple[str, ...], letters: tuple[str, ...], length: int, repetitions: bool, position: int
) -> str:
    """Слово, стоящее на данном месте, если алфавит именно такой."""
    total = word_count(letters, length, repetitions)
    if not isinstance(position, int) or isinstance(position, bool) or not 1 <= position <= total:
        if isinstance(position, int) and not isinstance(position, bool):
            raise AlphabetRangeError(f"В языке всего {total} слов, а спрошено {position}-е.")
        raise AlphabetOrderError(f"Место слова — целое число, получено {position!r}.")
    for candidate, words in all_orderings(letters, length, repetitions):
        if candidate == order:
            return words[position - 1]
    raise AlphabetOrderError(f"Порядок букв {order!r} не является перестановкой {letters!r}.")


def answers(
    letters: tuple[str, ...],
    length: int,
    repetitions: bool,
    clue_position: int,
    clue_word: str,
    question: dict[str, object],
) -> tuple[str, ...]:
    """Все ответы, возможные при алфавитах, совместимых с подсказкой.

    Перебираются все порядки букв; остаются те, при которых слово на месте
    ``clue_position`` действительно равно ``clue_word``; для каждого такого
    порядка вычисляется ответ на вопрос. Результат — отсортированное множество
    без повторов. Один элемент означает корректную задачу с единственным
    ключом, несколько — честную неоднозначность вида «какое может быть».
    """
    total = word_count(letters, length, repetitions)
    if not 1 <= clue_position <= total:
        raise AlphabetRangeError(f"В языке всего {total} слов, а подсказка про {clue_position}-е.")
    kind = question.get("kind")
    if kind not in QUESTION_KINDS:
        raise AlphabetOrderError(f"Неизвестный вид вопроса {kind!r}.")

    found: set[str] = set()
    for _order, words in all_orderings(letters, length, repetitions):
        if words[clue_position - 1] != clue_word:
            continue
        found.add(_answer_for(words, kind, question, total))
    if not found:
        raise AlphabetOrderError(
            f"Ни один порядок букв не ставит слово {clue_word!r} на место {clue_position}."
        )
    return tuple(sorted(found))


def _answer_for(
    words: tuple[str, ...], kind: object, question: dict[str, object], total: int
) -> str:
    if kind == "first":
        return words[0]
    if kind == "last":
        return words[-1]
    if kind == "position":
        position = question.get("position")
        if not isinstance(position, int) or isinstance(position, bool):
            raise AlphabetOrderError(f"Спрашиваемое место — целое число, получено {position!r}.")
        if not 1 <= position <= total:
            raise AlphabetRangeError(f"В языке всего {total} слов, а спрошено {position}-е.")
        return words[position - 1]
    # «сразу после» и «сразу перед»: место слова-запроса зависит от алфавита,
    # поэтому оно ищется заново в каждом совместимом порядке, а не считается
    # один раз по разыгранному.
    word = question.get("word")
    if not isinstance(word, str) or word not in words:
        raise AlphabetOrderError(f"Слова {word!r} нет среди выписанных.")
    index = words.index(word)
    if kind == "after":
        if index + 1 >= total:
            raise AlphabetRangeError(f"Слово {word!r} последнее, после него ничего нет.")
        return words[index + 1]
    if index == 0:
        raise AlphabetRangeError(f"Слово {word!r} первое, перед ним ничего нет.")
    return words[index - 1]
