from __future__ import annotations

import argparse
import html
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, quote, urlparse


# ============================================================
# МОДУЛЬ ГЕНЕРАЦИИ ЗАДАЧ НА ОТРЕЗКИ
# ============================================================
# Назначение модуля:
# - работает только с задачами на отрезки;
# - поддерживает задачи на прямой и на плоскости;
# - умеет задавать несколько отрезков и связи между ними;
# - гарантирует целочисленные ответы;
# - гарантирует целочисленные промежуточные длины;
# - умеет выдавать одну задачу по выбранному режиму;
# - умеет генерировать большой набор задач, например 1000 штук;
# - сохраняет результат в JSON с полной метаинформацией.
#
# В модуле нет алгебры общего вида, задач на скорость и других тем.
# Только отрезки.
# ============================================================


# ------------------------------------------------------------
# Русское согласование слов
# ------------------------------------------------------------
def pluralize_ru(n: int, forms: Tuple[str, str, str]) -> str:
    """Возвращает правильную форму русского слова по числу."""
    n_abs = abs(n) % 100
    last = n_abs % 10

    if 11 <= n_abs <= 14:
        return forms[2]
    if last == 1:
        return forms[0]
    if 2 <= last <= 4:
        return forms[1]
    return forms[2]



def count_with_word_ru(n: int, forms: Tuple[str, str, str]) -> str:
    """Возвращает строку вида: '1 задача', '2 задачи', '5 задач'."""
    return f"{n} {pluralize_ru(n, forms)}"


# ------------------------------------------------------------
# Разрядность числа
# ------------------------------------------------------------
def digit_length(value: int) -> int:
    """Количество цифр в числе по модулю. Для 0 возвращает 1."""
    return len(str(abs(value)))


# ------------------------------------------------------------
# Настройки сложности
# ------------------------------------------------------------
@dataclass
class DifficultyConstraints:
    """
    Ограничения сложности для промежуточных длин и ответов.

    Все длины в этом модуле считаются целыми числами.
    """
    min_intermediate_digits: int = 1
    max_intermediate_digits: int = 9
    min_answer_digits: int = 1
    max_answer_digits: int = 9

    def check_intermediates(self, values: Sequence[int]) -> bool:
        for value in values:
            if not isinstance(value, int):
                return False
            digits = digit_length(value)
            if not (self.min_intermediate_digits <= digits <= self.max_intermediate_digits):
                return False
        return True

    def check_answers(self, values: Sequence[int]) -> bool:
        for value in values:
            if not isinstance(value, int):
                return False
            digits = digit_length(value)
            if not (self.min_answer_digits <= digits <= self.max_answer_digits):
                return False
        return True


@dataclass(frozen=True)
class DifficultyProfile:
    """Готовый профиль сложности для генерации задач."""

    code: str
    label: str
    description: str
    constraints: DifficultyConstraints
    template_ranges: Dict[str, Dict[str, NumberRange]]


@dataclass(frozen=True)
class StoryScene:
    """Сюжетная сцена для текстовой вариации задачи."""

    scene_label: str
    intro: str
    location: str
    unit_short: str
    objects: Sequence[str]
    objects_between: Sequence[str]
    characters: Sequence[str]


def make_scene(
    scene_label: str,
    intro: str,
    location: str,
    unit_short: str,
    objects: Sequence[str],
    objects_between: Sequence[str],
    characters: Sequence[str] = (),
) -> StoryScene:
    """Короткий конструктор сюжетной сцены."""

    return StoryScene(
        scene_label=scene_label,
        intro=intro,
        location=location,
        unit_short=unit_short,
        objects=objects,
        objects_between=objects_between,
        characters=characters,
    )


# ------------------------------------------------------------
# Диапазон целых значений
# ------------------------------------------------------------
@dataclass
class NumberRange:
    min_value: int
    max_value: int

    def sample(self, rng: random.Random) -> int:
        return rng.randint(self.min_value, self.max_value)


DIFFICULTY_PROFILES: Dict[str, DifficultyProfile] = {
    "easy": DifficultyProfile(
        code="easy",
        label="Легкий",
        description="Небольшие числа. Обычно достаточно простых вычислений с однозначными и двузначными длинами.",
        constraints=DifficultyConstraints(
            min_intermediate_digits=1,
            max_intermediate_digits=2,
            min_answer_digits=1,
            max_answer_digits=2,
        ),
        template_ranges={
            "line_two_segments_possible_ac": {
                "ab_range": NumberRange(2, 20),
                "bc_range": NumberRange(2, 9),
            },
            "line_three_consecutive_segments": {
                "ab_range": NumberRange(2, 12),
                "bc_range": NumberRange(2, 12),
                "cd_range": NumberRange(2, 12),
            },
            "line_equality_relation": {
                "equal_part_range": NumberRange(2, 12),
                "middle_range": NumberRange(2, 12),
            },
            "plane_midpoint": {
                "half_range": NumberRange(2, 20),
            },
            "plane_point_inside_segment": {
                "ac_range": NumberRange(2, 20),
                "cb_range": NumberRange(2, 20),
            },
        },
    ),
    "medium": DifficultyProfile(
        code="medium",
        label="Средний",
        description="Числа больше, промежуточные вычисления чаще двузначные и трехзначные.",
        constraints=DifficultyConstraints(
            min_intermediate_digits=2,
            max_intermediate_digits=3,
            min_answer_digits=2,
            max_answer_digits=3,
        ),
        template_ranges={
            "line_two_segments_possible_ac": {
                "ab_range": NumberRange(40, 120),
                "bc_range": NumberRange(10, 30),
            },
            "line_three_consecutive_segments": {
                "ab_range": NumberRange(12, 60),
                "bc_range": NumberRange(12, 60),
                "cd_range": NumberRange(12, 60),
            },
            "line_equality_relation": {
                "equal_part_range": NumberRange(10, 60),
                "middle_range": NumberRange(10, 60),
            },
            "plane_midpoint": {
                "half_range": NumberRange(10, 60),
            },
            "plane_point_inside_segment": {
                "ac_range": NumberRange(10, 60),
                "cb_range": NumberRange(10, 60),
            },
        },
    ),
    "hard": DifficultyProfile(
        code="hard",
        label="Сложный",
        description="Крупные числа. Одни и те же шаблоны становятся заметно тяжелее из-за трехзначных и иногда четырехзначных вычислений.",
        constraints=DifficultyConstraints(
            min_intermediate_digits=3,
            max_intermediate_digits=4,
            min_answer_digits=3,
            max_answer_digits=4,
        ),
        template_ranges={
            "line_two_segments_possible_ac": {
                "ab_range": NumberRange(500, 999),
                "bc_range": NumberRange(100, 299),
            },
            "line_three_consecutive_segments": {
                "ab_range": NumberRange(120, 450),
                "bc_range": NumberRange(120, 450),
                "cd_range": NumberRange(120, 450),
            },
            "line_equality_relation": {
                "equal_part_range": NumberRange(100, 400),
                "middle_range": NumberRange(100, 400),
            },
            "plane_midpoint": {
                "half_range": NumberRange(100, 450),
            },
            "plane_point_inside_segment": {
                "ac_range": NumberRange(100, 450),
                "cb_range": NumberRange(100, 450),
            },
        },
    ),
}


def get_difficulty_profile(code: str) -> DifficultyProfile:
    """Возвращает профиль сложности по коду."""

    if code not in DIFFICULTY_PROFILES:
        available = ", ".join(sorted(DIFFICULTY_PROFILES))
        raise ValueError(f"Неизвестный уровень сложности '{code}'. Доступные: {available}")
    return DIFFICULTY_PROFILES[code]


STORY_THEME_LABELS: Dict[str, str] = {
    "any": "Любая тема",
    "classic": "Классическая геометрия",
    "road": "Дорога и дома",
    "village": "Деревня",
    "city": "Город",
    "fairytale": "Сказка",
    "cartoon": "Мультгерои",
    "ants": "Муравьи",
    "space": "Космос",
    "desert": "Пустыня",
    "cowboy": "Ковбои",
    "pirates": "Пираты",
    "jungle": "Джунгли",
    "ocean": "Океан",
    "mountains": "Горы",
    "arctic": "Арктика",
    "safari": "Сафари",
    "farm": "Ферма",
    "castle": "Замок",
    "robots": "Роботы",
    "dinosaurs": "Динозавры",
    "dragons": "Драконы",
    "school": "Школа",
    "museum": "Музей",
    "airport": "Аэропорт",
    "railway": "Железная дорога",
    "submarine": "Подводная лодка",
    "circus": "Цирк",
    "knights": "Рыцари",
    "superheroes": "Супергерои",
    "candy": "Сладкое королевство",
    "underwater": "Подводный мир",
}

THREE_OBJECT_STORY_SCENES: Dict[str, List[StoryScene]] = {
    "road": [
        make_scene(
            "Улица с остановкой",
            "Вдоль прямой улицы расположены",
            "улица",
            "м",
            ("дом Пети", "автобусная остановка", "булочная"),
            ("домом Пети", "автобусной остановкой", "булочной"),
            ("Петя",),
        ),
    ],
    "village": [
        make_scene(
            "Деревенский путь",
            "На деревенской дороге по одной линии стоят",
            "деревня",
            "м",
            ("дом старосты", "колодец", "мельница"),
            ("домом старосты", "колодцем", "мельницей"),
            ("староста",),
        ),
    ],
    "city": [
        make_scene(
            "Городская улица",
            "На городской улице на одной линии находятся",
            "город",
            "м",
            ("кафе", "трамвайная остановка", "библиотека"),
            ("кафе", "трамвайной остановкой", "библиотекой"),
            (),
        ),
    ],
    "fairytale": [
        make_scene(
            "Сказочная тропинка",
            "На лесной тропинке на одной линии стоят",
            "сказочный лес",
            "м",
            ("домик Красной Шапочки", "волшебный колодец", "избушка Бабы-яги"),
            ("домиком Красной Шапочки", "волшебным колодцем", "избушкой Бабы-яги"),
            ("Красная Шапочка", "Баба-яга"),
        ),
    ],
    "cartoon": [
        make_scene(
            "Лило и Стич",
            "На пляжной дорожке на одной линии находятся",
            "пляжная дорожка",
            "м",
            ("Лило", "Стич", "серф-хижина Нани"),
            ("Лило", "Стичем", "серф-хижиной Нани"),
            ("Лило", "Стич", "Нани"),
        ),
        make_scene(
            "История игрушек",
            "В комнате Энди на одной линии стоят",
            "комната Энди",
            "см",
            ("Вуди", "Базз", "ящик с игрушками"),
            ("Вуди", "Баззом", "ящиком с игрушками"),
            ("Вуди", "Базз"),
        ),
    ],
    "ants": [
        make_scene(
            "Муравьи на шлагбауме",
            "На длинном шлагбауме на одной линии сидят",
            "шлагбаум",
            "см",
            ("муравей Арчи", "капля сиропа", "муравей Жужа"),
            ("муравьем Арчи", "каплей сиропа", "муравьем Жужей"),
            ("муравей Арчи", "муравей Жужа"),
        ),
    ],
    "space": [
        make_scene(
            "Космический маршрут",
            "На одном космическом маршруте выстроились",
            "космический маршрут",
            "тыс. км",
            ("планета Терра", "маяк Альтаир", "станция Сириус"),
            ("планетой Терра", "маяком Альтаир", "станцией Сириус"),
            ("пилоты станции Сириус",),
        ),
    ],
    "desert": [
        make_scene(
            "Пустынная экспедиция",
            "В пустыне на одной линии находятся",
            "пустыня",
            "м",
            ("лагерь экспедиции", "оазис", "дюна Солнца"),
            ("лагерем экспедиции", "оазисом", "дюной Солнца"),
            ("исследователи",),
        ),
    ],
    "cowboy": [
        make_scene(
            "Ковбойская улица",
            "На пыльной улице на одной линии стоят",
            "вестерн-городок",
            "м",
            ("ковбой Билл", "колодец ранчо", "салун"),
            ("ковбоем Биллом", "колодцем ранчо", "салуном"),
            ("ковбой Билл",),
        ),
    ],
    "pirates": [
        make_scene(
            "Пиратская пристань",
            "На одной линии у пристани расположены",
            "пиратская пристань",
            "м",
            ("пиратский корабль", "маяк", "сундук капитана"),
            ("пиратским кораблем", "маяком", "сундуком капитана"),
            ("капитан",),
        ),
    ],
    "jungle": [
        make_scene(
            "Джунгли",
            "В джунглях на одной линии находятся",
            "джунгли",
            "м",
            ("хижина исследователя", "лиана", "водопад"),
            ("хижиной исследователя", "лианой", "водопадом"),
            ("исследователь",),
        ),
    ],
    "ocean": [
        make_scene(
            "Острова в океане",
            "В океане на одной линии расположены",
            "океан",
            "км",
            ("остров Чаек", "буй", "остров Черепах"),
            ("островом Чаек", "буем", "островом Черепах"),
            (),
        ),
    ],
    "mountains": [
        make_scene(
            "Горный маршрут",
            "В горах на одной линии находятся",
            "горы",
            "м",
            ("горный приют", "каменная арка", "ледниковое озеро"),
            ("горным приютом", "каменной аркой", "ледниковым озером"),
            (),
        ),
    ],
    "arctic": [
        make_scene(
            "Полярная база",
            "В Арктике на одной линии расположены",
            "Арктика",
            "м",
            ("полярная станция", "ледяная арка", "склад топлива"),
            ("полярной станцией", "ледяной аркой", "складом топлива"),
            ("полярники",),
        ),
    ],
    "safari": [
        make_scene(
            "Сафари",
            "На саванне на одной линии расположены",
            "саванна",
            "м",
            ("лагерь рейнджеров", "баобаб", "водопой"),
            ("лагерем рейнджеров", "баобабом", "водопоем"),
            ("рейнджеры",),
        ),
    ],
    "farm": [
        make_scene(
            "Ферма",
            "На ферме на одной линии стоят",
            "ферма",
            "м",
            ("амбар", "колодец", "курятник"),
            ("амбаром", "колодцем", "курятником"),
            ("фермер",),
        ),
    ],
    "castle": [
        make_scene(
            "Замковый двор",
            "Во дворе замка на одной линии расположены",
            "замок",
            "м",
            ("главные ворота", "фонтан", "башня мага"),
            ("главными воротами", "фонтаном", "башней мага"),
            ("маг",),
        ),
    ],
    "robots": [
        make_scene(
            "Завод роботов",
            "В цехе на одной линии находятся",
            "роботизированный цех",
            "м",
            ("робот Рик", "зарядная станция", "конвейер"),
            ("роботом Риком", "зарядной станцией", "конвейером"),
            ("робот Рик",),
        ),
    ],
    "dinosaurs": [
        make_scene(
            "Мир динозавров",
            "На доисторической равнине на одной линии находятся",
            "мир динозавров",
            "м",
            ("гнездо трицератопса", "пальма", "скала тираннозавра"),
            ("гнездом трицератопса", "пальмой", "скалой тираннозавра"),
            (),
        ),
    ],
    "dragons": [
        make_scene(
            "Долина драконов",
            "В долине драконов на одной линии расположены",
            "долина драконов",
            "м",
            ("пещера дракона", "магический кристалл", "башня рыцаря"),
            ("пещерой дракона", "магическим кристаллом", "башней рыцаря"),
            ("рыцарь", "дракон"),
        ),
    ],
    "school": [
        make_scene(
            "Школьный коридор",
            "В школьном коридоре на одной линии находятся",
            "школа",
            "м",
            ("кабинет математики", "лестница", "спортзал"),
            ("кабинетом математики", "лестницей", "спортзалом"),
            ("ученики",),
        ),
    ],
    "museum": [
        make_scene(
            "Музей",
            "В музее на одной линии расположены",
            "музей",
            "м",
            ("зал динозавров", "статуя", "зал космоса"),
            ("залом динозавров", "статуей", "залом космоса"),
            (),
        ),
    ],
    "airport": [
        make_scene(
            "Аэропорт",
            "В аэропорту на одной линии находятся",
            "аэропорт",
            "м",
            ("стойка регистрации", "выход B12", "кафе аэропорта"),
            ("стойкой регистрации", "выходом B12", "кафе аэропорта"),
            ("пассажиры",),
        ),
    ],
    "railway": [
        make_scene(
            "Железная дорога",
            "На одной линии вдоль путей расположены",
            "железная дорога",
            "м",
            ("станция Северная", "семафор", "станция Южная"),
            ("станцией Северной", "семафором", "станцией Южной"),
            (),
        ),
    ],
    "submarine": [
        make_scene(
            "Подводная лодка",
            "На одной линии внутри подлодки находятся",
            "подводная лодка",
            "м",
            ("рубка подлодки", "люк", "машинное отделение"),
            ("рубкой подлодки", "люком", "машинным отделением"),
            ("экипаж",),
        ),
    ],
    "circus": [
        make_scene(
            "Цирк",
            "На арене цирка на одной линии находятся",
            "цирк",
            "м",
            ("клоун Бим", "тумба жонглера", "клетка льва"),
            ("клоуном Бимом", "тумбой жонглера", "клеткой льва"),
            ("клоун Бим",),
        ),
    ],
    "knights": [
        make_scene(
            "Рыцарский путь",
            "На одной линии перед замком расположены",
            "замок",
            "м",
            ("рыцарь Артур", "каменный мост", "главная башня"),
            ("рыцарем Артуром", "каменным мостом", "главной башней"),
            ("рыцарь Артур",),
        ),
    ],
    "superheroes": [
        make_scene(
            "Город супергероев",
            "В городе на одной линии находятся",
            "город супергероев",
            "м",
            ("супергерой Макс", "энергокуб", "лаборатория"),
            ("супергероем Максом", "энергокубом", "лабораторией"),
            ("супергерой Макс",),
        ),
    ],
    "candy": [
        make_scene(
            "Сладкое королевство",
            "В сладком королевстве на одной линии стоят",
            "сладкое королевство",
            "м",
            ("леденцовый домик", "мармеладный фонарь", "шоколадный мост"),
            ("леденцовым домиком", "мармеладным фонарем", "шоколадным мостом"),
            (),
        ),
    ],
    "underwater": [
        make_scene(
            "Подводный мир",
            "Под водой на одной линии находятся",
            "подводный мир",
            "м",
            ("коралловая арка", "морская звезда", "домик русалки"),
            ("коралловой аркой", "морской звездой", "домиком русалки"),
            ("русалка",),
        ),
    ],
}

FOUR_OBJECT_STORY_SCENES: Dict[str, List[StoryScene]] = {
    "road": [
        make_scene(
            "Дорога с магазинами",
            "Вдоль прямого шоссе по порядку стоят",
            "шоссе",
            "м",
            ("дом Миши", "светофор", "школа", "магазин"),
            ("домом Миши", "светофором", "школой", "магазином"),
            ("Миша",),
        ),
    ],
    "village": [
        make_scene(
            "Деревенская улица",
            "На деревенской улице последовательно расположены",
            "деревня",
            "м",
            ("дом бабушки", "колодец", "амбар", "мост"),
            ("домом бабушки", "колодцем", "амбаром", "мостом"),
            ("бабушка",),
        ),
    ],
    "city": [
        make_scene(
            "Городской квартал",
            "В городском квартале по порядку находятся",
            "город",
            "м",
            ("пекарня", "сквер", "кинотеатр", "станция метро"),
            ("пекарней", "сквером", "кинотеатром", "станцией метро"),
            (),
        ),
    ],
    "fairytale": [
        make_scene(
            "Сказочная дорога",
            "На сказочной дороге по порядку находятся",
            "сказочный лес",
            "м",
            ("домик гномов", "волшебный пень", "избушка лесника", "замок принцессы"),
            ("домиком гномов", "волшебным пнем", "избушкой лесника", "замком принцессы"),
            ("гномы", "принцесса"),
        ),
    ],
    "cartoon": [
        make_scene(
            "История игрушек",
            "В комнате Энди на одной линии последовательно стоят",
            "комната Энди",
            "см",
            ("Вуди", "Базз", "Джесси", "Рекс"),
            ("Вуди", "Баззом", "Джесси", "Рексом"),
            ("Вуди", "Базз", "Джесси", "Рекс"),
        ),
        make_scene(
            "Лило и Стич на берегу",
            "На береговой линии по порядку расположены",
            "берег",
            "м",
            ("Лило", "Стич", "Нани", "лаборатория Джамбы"),
            ("Лило", "Стичем", "Нани", "лабораторией Джамбы"),
            ("Лило", "Стич", "Нани", "Джамба"),
        ),
    ],
    "ants": [
        make_scene(
            "Муравьи на планке",
            "На длинной деревянной планке по порядку сидят",
            "деревянная планка",
            "см",
            ("муравей Арчи", "капля меда", "муравей Жужа", "крошка печенья"),
            ("муравьем Арчи", "каплей меда", "муравьем Жужей", "крошкой печенья"),
            ("муравей Арчи", "муравей Жужа"),
        ),
    ],
    "space": [
        make_scene(
            "Цепочка планет",
            "На одной космической линии по порядку находятся",
            "космос",
            "тыс. км",
            ("планета Лунара", "станция Вега", "спутник Орбис", "планета Терра"),
            ("планетой Лунара", "станцией Вега", "спутником Орбис", "планетой Терра"),
            ("экипаж станции Вега",),
        ),
    ],
    "desert": [
        make_scene(
            "Путь через пустыню",
            "В пустыне по порядку находятся",
            "пустыня",
            "м",
            ("палатка экспедиции", "колодец", "караван", "скала Заката"),
            ("палаткой экспедиции", "колодцем", "караваном", "скалой Заката"),
            ("путешественники",),
        ),
    ],
    "cowboy": [
        make_scene(
            "Город ковбоев",
            "На улице вестерн-городка последовательно стоят",
            "вестерн-городок",
            "м",
            ("ранчо", "салун", "коновязь", "банк"),
            ("ранчо", "салуном", "коновязью", "банком"),
            ("ковбои",),
        ),
    ],
    "pirates": [
        make_scene(
            "Пиратский берег",
            "На пиратском берегу по порядку расположены",
            "пиратский берег",
            "м",
            ("корабль", "маяк", "пальма", "сундук"),
            ("кораблем", "маяком", "пальмой", "сундуком"),
            ("пираты",),
        ),
    ],
    "jungle": [
        make_scene(
            "Тропа в джунглях",
            "В джунглях последовательно находятся",
            "джунгли",
            "м",
            ("лагерь", "лиана", "ручей", "водопад"),
            ("лагерем", "лианой", "ручьем", "водопадом"),
            ("исследователи",),
        ),
    ],
    "ocean": [
        make_scene(
            "Маршрут в океане",
            "В океане на одной линии находятся",
            "океан",
            "км",
            ("остров Северный", "буй", "риф", "остров Южный"),
            ("островом Северным", "буем", "рифом", "островом Южным"),
            (),
        ),
    ],
    "mountains": [
        make_scene(
            "Тропа в горах",
            "В горах по порядку расположены",
            "горы",
            "м",
            ("приют", "скала", "мостик", "вершина"),
            ("приютом", "скалой", "мостиком", "вершиной"),
            (),
        ),
    ],
    "arctic": [
        make_scene(
            "Полярный маршрут",
            "В Арктике по порядку находятся",
            "Арктика",
            "м",
            ("станция", "ледяной туннель", "склад", "маяк"),
            ("станцией", "ледяным туннелем", "складом", "маяком"),
            ("полярники",),
        ),
    ],
    "safari": [
        make_scene(
            "Сафари-маршрут",
            "На саванне по порядку находятся",
            "саванна",
            "м",
            ("лагерь", "баобаб", "водопой", "смотровая вышка"),
            ("лагерем", "баобабом", "водопоем", "смотровой вышкой"),
            (),
        ),
    ],
    "farm": [
        make_scene(
            "Фермерский двор",
            "На ферме последовательно расположены",
            "ферма",
            "м",
            ("дом фермера", "амбар", "колодец", "загон"),
            ("домом фермера", "амбаром", "колодцем", "загоном"),
            ("фермер",),
        ),
    ],
    "castle": [
        make_scene(
            "Замковая галерея",
            "В замке по порядку находятся",
            "замок",
            "м",
            ("ворота", "фонтан", "тронный зал", "башня мага"),
            ("воротами", "фонтаном", "тронным залом", "башней мага"),
            ("маг",),
        ),
    ],
    "robots": [
        make_scene(
            "Линия роботов",
            "В заводском цехе по порядку находятся",
            "цех роботов",
            "м",
            ("станция сборки", "зарядный модуль", "конвейер", "отсек тестов"),
            ("станцией сборки", "зарядным модулем", "конвейером", "отсеком тестов"),
            (),
        ),
    ],
    "dinosaurs": [
        make_scene(
            "Динозавры",
            "На доисторической равнине по порядку расположены",
            "мир динозавров",
            "м",
            ("гнездо", "пальма", "озеро", "скала"),
            ("гнездом", "пальмой", "озером", "скалой"),
            (),
        ),
    ],
    "dragons": [
        make_scene(
            "Путь дракона",
            "В долине драконов по порядку находятся",
            "долина драконов",
            "м",
            ("пещера", "кристалл", "мост", "башня"),
            ("пещерой", "кристаллом", "мостом", "башней"),
            (),
        ),
    ],
    "school": [
        make_scene(
            "Школьный маршрут",
            "В школе последовательно расположены",
            "школа",
            "м",
            ("кабинет", "лестница", "библиотека", "спортзал"),
            ("кабинетом", "лестницей", "библиотекой", "спортзалом"),
            (),
        ),
    ],
    "museum": [
        make_scene(
            "Залы музея",
            "В музее по порядку находятся",
            "музей",
            "м",
            ("зал динозавров", "галерея", "статуя", "зал космоса"),
            ("залом динозавров", "галереей", "статуей", "залом космоса"),
            (),
        ),
    ],
    "airport": [
        make_scene(
            "Маршрут в аэропорту",
            "В аэропорту по порядку находятся",
            "аэропорт",
            "м",
            ("стойка регистрации", "контроль", "выход B12", "кафе"),
            ("стойкой регистрации", "контролем", "выходом B12", "кафе"),
            (),
        ),
    ],
    "railway": [
        make_scene(
            "Железнодорожная линия",
            "Вдоль путей по порядку расположены",
            "железная дорога",
            "м",
            ("станция Северная", "семафор", "платформа", "станция Южная"),
            ("станцией Северной", "семафором", "платформой", "станцией Южной"),
            (),
        ),
    ],
    "submarine": [
        make_scene(
            "Отсеки подлодки",
            "Внутри подводной лодки по порядку расположены",
            "подводная лодка",
            "м",
            ("рубка", "люк", "машинное отделение", "склад"),
            ("рубкой", "люком", "машинным отделением", "складом"),
            ("экипаж",),
        ),
    ],
    "circus": [
        make_scene(
            "Цирковая арена",
            "На арене цирка по порядку находятся",
            "цирк",
            "м",
            ("клоун", "тумба", "батут", "клетка льва"),
            ("клоуном", "тумбой", "батутом", "клеткой льва"),
            (),
        ),
    ],
    "knights": [
        make_scene(
            "Путь рыцарей",
            "Перед замком по порядку расположены",
            "рыцарский путь",
            "м",
            ("рыцарь Артур", "мост", "ворота", "башня"),
            ("рыцарем Артуром", "мостом", "воротами", "башней"),
            ("рыцарь Артур",),
        ),
    ],
    "superheroes": [
        make_scene(
            "Маршрут супергероя",
            "В городе по порядку находятся",
            "город супергероев",
            "м",
            ("база героя", "энергокуб", "лаборатория", "небоскреб"),
            ("базой героя", "энергокубом", "лабораторией", "небоскребом"),
            (),
        ),
    ],
    "candy": [
        make_scene(
            "Сладкая улица",
            "В сладком королевстве по порядку стоят",
            "сладкое королевство",
            "м",
            ("леденцовый домик", "ириска", "мармеладная башня", "шоколадный мост"),
            ("леденцовым домиком", "ириской", "мармеладной башней", "шоколадным мостом"),
            (),
        ),
    ],
    "underwater": [
        make_scene(
            "Подводный маршрут",
            "Под водой по порядку расположены",
            "подводный мир",
            "м",
            ("коралловая арка", "ракушка", "домик русалки", "затонувший якорь"),
            ("коралловой аркой", "ракушкой", "домиком русалки", "затонувшим якорем"),
            ("русалка",),
        ),
    ],
}


def get_story_theme_label(theme_code: str) -> str:
    """Человекочитаемое название темы."""

    return STORY_THEME_LABELS.get(theme_code, theme_code)


def resolve_story_theme(requested_theme: str, rng: random.Random) -> str:
    """Определяет фактическую тему истории."""

    if requested_theme not in STORY_THEME_LABELS:
        available = ", ".join(sorted(STORY_THEME_LABELS))
        raise ValueError(f"Неизвестная тема сюжета '{requested_theme}'. Доступные: {available}")

    if requested_theme != "any":
        return requested_theme

    return rng.choice([theme for theme in STORY_THEME_LABELS if theme != "any"])


def build_classic_story_context() -> Dict[str, Any]:
    """Возвращает базовый классический контекст без сюжета."""

    return {
        "theme_code": "classic",
        "theme_label": get_story_theme_label("classic"),
        "scene_label": "Классическая геометрия",
        "location": "математическая прямая",
        "unit_short": "см",
        "characters": [],
        "objects": [],
        "objects_between": [],
    }


def build_story_context_from_scene(theme_code: str, scene: StoryScene) -> Dict[str, Any]:
    """Преобразует объект сцены в словарь для JSON и UI."""

    return {
        "theme_code": theme_code,
        "theme_label": get_story_theme_label(theme_code),
        "scene_label": scene.scene_label,
        "location": scene.location,
        "unit_short": scene.unit_short,
        "characters": list(scene.characters),
        "objects": list(scene.objects),
        "objects_between": list(scene.objects_between),
        "intro": scene.intro,
    }


def format_distance(value: int, story: Dict[str, Any]) -> str:
    """Форматирует число с единицей измерения."""

    unit = story.get("unit_short", "").strip()
    if not unit:
        return str(value)
    return f"{value} {unit}"


def sample_three_object_story_context(rng: random.Random, requested_theme: str) -> Dict[str, Any]:
    """Выбирает сюжет для задач с тремя опорными объектами."""

    theme_code = resolve_story_theme(requested_theme, rng)
    if theme_code == "classic":
        return build_classic_story_context()
    return build_story_context_from_scene(
        theme_code,
        rng.choice(THREE_OBJECT_STORY_SCENES[theme_code]),
    )


def sample_four_object_story_context(rng: random.Random, requested_theme: str) -> Dict[str, Any]:
    """Выбирает сюжет для задач с четырьмя опорными объектами."""

    theme_code = resolve_story_theme(requested_theme, rng)
    if theme_code == "classic":
        return build_classic_story_context()
    return build_story_context_from_scene(
        theme_code,
        rng.choice(FOUR_OBJECT_STORY_SCENES[theme_code]),
    )


# ------------------------------------------------------------
# Результат генерации одной задачи
# ------------------------------------------------------------
@dataclass
class GeneratedProblem:
    code: str
    category: str
    mode: str
    template_name: str
    problem_text: str
    answer_text: str
    answer_values: List[int]
    story: Dict[str, Any]
    variables: Dict[str, int]
    intermediate_values: Dict[str, int]
    relations: List[str]
    difficulty: Dict[str, int]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------
# Базовый класс шаблона задач на отрезки
# ------------------------------------------------------------
class SegmentProblemTemplate:
    """
    Общий интерфейс для всех шаблонов задач на отрезки.

    Любой шаблон обязан:
    - выбрать целые переменные;
    - построить промежуточные целые длины;
    - построить целый ответ;
    - вернуть текст задачи.
    """

    def __init__(
        self,
        name: str,
        code_prefix: str,
        mode: str,
        difficulty: DifficultyConstraints,
        max_attempts: int = 10000,
    ) -> None:
        self.name = name
        self.code_prefix = code_prefix
        self.mode = mode
        self.difficulty = difficulty
        self.max_attempts = max_attempts

    def generate(
        self,
        rng: random.Random,
        sequence_number: int,
        story_theme: str = "any",
    ) -> GeneratedProblem:
        for _ in range(self.max_attempts):
            variables = self.sample_variables(rng)
            if variables is None:
                continue

            intermediate_values = self.compute_intermediate_values(variables)
            answer_values = self.compute_answer_values(variables, intermediate_values)

            if not self.is_valid(variables, intermediate_values, answer_values):
                continue

            if not self.all_positive_integers(intermediate_values.values()):
                continue

            if not self.all_positive_integers(answer_values):
                continue

            if not self.difficulty.check_intermediates(list(intermediate_values.values())):
                continue

            if not self.difficulty.check_answers(answer_values):
                continue

            story = self.sample_story_context(rng, story_theme)
            relations = self.describe_relations(variables, intermediate_values)
            problem_text = self.render_problem_text(variables, story)
            answer_text = self.render_answer_text(answer_values, story)
            code = f"{self.code_prefix}-{sequence_number:05d}"
            metadata = self.build_metadata(variables, intermediate_values, answer_values)
            metadata["story"] = story

            return GeneratedProblem(
                code=code,
                category="segments",
                mode=self.mode,
                template_name=self.name,
                problem_text=problem_text,
                answer_text=answer_text,
                answer_values=list(answer_values),
                story=story,
                variables=variables,
                intermediate_values=intermediate_values,
                relations=relations,
                difficulty={
                    "min_intermediate_digits": self.difficulty.min_intermediate_digits,
                    "max_intermediate_digits": self.difficulty.max_intermediate_digits,
                    "min_answer_digits": self.difficulty.min_answer_digits,
                    "max_answer_digits": self.difficulty.max_answer_digits,
                },
                metadata=metadata,
            )

        raise ValueError(
            f"Не удалось сгенерировать задачу для шаблона '{self.name}' "
            f"за {self.max_attempts} попыток. Ограничения слишком жесткие или диапазоны заданы неудачно."
        )

    @staticmethod
    def all_positive_integers(values: Sequence[int]) -> bool:
        for value in values:
            if not isinstance(value, int):
                return False
            if value <= 0:
                return False
        return True

    def render_answer_text(self, answer_values: Sequence[int], story: Dict[str, Any]) -> str:
        unique_sorted = sorted(set(answer_values))
        if len(unique_sorted) == 1:
            return format_distance(unique_sorted[0], story)
        return " и ".join(format_distance(x, story) for x in unique_sorted)

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        raise NotImplementedError

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        raise NotImplementedError

    def compute_answer_values(
        self,
        variables: Dict[str, int],
        intermediate_values: Dict[str, int],
    ) -> List[int]:
        raise NotImplementedError

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return build_classic_story_context()

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        raise NotImplementedError

    def describe_relations(
        self,
        variables: Dict[str, int],
        intermediate_values: Dict[str, int],
    ) -> List[str]:
        return []

    def is_valid(
        self,
        variables: Dict[str, int],
        intermediate_values: Dict[str, int],
        answer_values: Sequence[int],
    ) -> bool:
        return True

    def build_metadata(
        self,
        variables: Dict[str, int],
        intermediate_values: Dict[str, int],
        answer_values: Sequence[int],
    ) -> Dict[str, Any]:
        return {}


# ------------------------------------------------------------
# Шаблон 1. Прямая: два отрезка AB и BC, найти возможные AC.
# ------------------------------------------------------------
class LineTwoSegmentsPossibleACTemplate(SegmentProblemTemplate):
    def __init__(
        self,
        ab_range: NumberRange,
        bc_range: NumberRange,
        difficulty: DifficultyConstraints,
    ) -> None:
        super().__init__(
            name="line_two_segments_possible_ac",
            code_prefix="LIN2",
            mode="line",
            difficulty=difficulty,
        )
        self.ab_range = ab_range
        self.bc_range = bc_range

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        ab = self.ab_range.sample(rng)
        bc = self.bc_range.sample(rng)
        if ab == bc:
            return None
        return {"AB": ab, "BC": bc}

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        ab = variables["AB"]
        bc = variables["BC"]
        return {
            "AB_plus_BC": ab + bc,
            "AB_minus_BC_abs": abs(ab - bc),
        }

    def compute_answer_values(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[int]:
        return [
            intermediate_values["AB_minus_BC_abs"],
            intermediate_values["AB_plus_BC"],
        ]

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return sample_three_object_story_context(rng, requested_theme)

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        if story["theme_code"] == "classic":
            return (
                f"На прямой отмечены отрезки AB и BC. Известно, что AB = {format_distance(variables['AB'], story)}, "
                f"BC = {format_distance(variables['BC'], story)}. "
                f"Какие значения может принимать длина отрезка AC?"
            )

        first, middle, third = story["objects"]
        first_between, middle_between, third_between = story["objects_between"]
        return (
            f"{story['intro']} {first}, {middle} и {third}. "
            f"Расстояние между {first_between} и {middle_between} равно {format_distance(variables['AB'], story)}, "
            f"а между {middle_between} и {third_between} равно {format_distance(variables['BC'], story)}. "
            f"Каким может быть расстояние между {first_between} и {third_between}?"
        )

    def describe_relations(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[str]:
        return [
            "Точки A, B, C лежат на одной прямой.",
            "Возможны два взаимных расположения точек.",
        ]

    def is_valid(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> bool:
        return all(x > 0 for x in answer_values)

    def build_metadata(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> Dict[str, Any]:
        return {
            "topic": "отрезки на прямой",
            "subtype": "два отрезка и возможные значения третьего",
            "formulas": ["AC = AB + BC", "AC = |AB - BC|"],
        }


# ------------------------------------------------------------
# Шаблон 2. Прямая: три последовательных отрезка.
# A-B-C-D лежат на одной прямой, известны AB, BC, CD.
# Найти AD.
# ------------------------------------------------------------
class LineThreeConsecutiveSegmentsTemplate(SegmentProblemTemplate):
    def __init__(
        self,
        ab_range: NumberRange,
        bc_range: NumberRange,
        cd_range: NumberRange,
        difficulty: DifficultyConstraints,
    ) -> None:
        super().__init__(
            name="line_three_consecutive_segments",
            code_prefix="LIN3",
            mode="line",
            difficulty=difficulty,
        )
        self.ab_range = ab_range
        self.bc_range = bc_range
        self.cd_range = cd_range

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        return {
            "AB": self.ab_range.sample(rng),
            "BC": self.bc_range.sample(rng),
            "CD": self.cd_range.sample(rng),
        }

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        ac = variables["AB"] + variables["BC"]
        ad = ac + variables["CD"]
        return {"AC": ac, "AD": ad}

    def compute_answer_values(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[int]:
        return [intermediate_values["AD"]]

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return sample_four_object_story_context(rng, requested_theme)

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        if story["theme_code"] == "classic":
            return (
                f"На одной прямой точки A, B, C и D расположены именно в таком порядке. "
                f"Известно, что AB = {format_distance(variables['AB'], story)}, "
                f"BC = {format_distance(variables['BC'], story)}, "
                f"CD = {format_distance(variables['CD'], story)}. "
                f"Найдите длину отрезка AD."
            )

        first, second, third, fourth = story["objects"]
        first_between, second_between, third_between, fourth_between = story["objects_between"]
        return (
            f"{story['intro']} {first}, {second}, {third} и {fourth}. "
            f"Известно, что расстояние между {first_between} и {second_between} равно {format_distance(variables['AB'], story)}, "
            f"между {second_between} и {third_between} равно {format_distance(variables['BC'], story)}, "
            f"а между {third_between} и {fourth_between} равно {format_distance(variables['CD'], story)}. "
            f"Найдите расстояние между {first_between} и {fourth_between}."
        )

    def describe_relations(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[str]:
        return [
            "Точки расположены последовательно: A-B-C-D.",
            "AC = AB + BC.",
            "AD = AC + CD.",
        ]

    def build_metadata(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> Dict[str, Any]:
        return {
            "topic": "сумма последовательных отрезков",
            "subtype": "три последовательных отрезка",
            "formulas": ["AC = AB + BC", "AD = AB + BC + CD"],
        }


# ------------------------------------------------------------
# Шаблон 3. Прямая: один отрезок равен другому.
# A-B-C-D, AB = CD, известны BC и AD. Найти AB.
#
# Так как AD = AB + BC + CD = 2*AB + BC,
# то AB = (AD - BC) / 2.
# Генерация построена так, чтобы ответ всегда был целым.
# ------------------------------------------------------------
class LineEqualityRelationTemplate(SegmentProblemTemplate):
    def __init__(
        self,
        equal_part_range: NumberRange,
        middle_range: NumberRange,
        difficulty: DifficultyConstraints,
    ) -> None:
        super().__init__(
            name="line_equality_relation",
            code_prefix="LREQ",
            mode="line",
            difficulty=difficulty,
        )
        self.equal_part_range = equal_part_range
        self.middle_range = middle_range

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        ab = self.equal_part_range.sample(rng)
        bc = self.middle_range.sample(rng)
        cd = ab
        ad = ab + bc + cd
        return {
            "AB": ab,
            "BC": bc,
            "CD": cd,
            "AD": ad,
        }

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        ad_minus_bc = variables["AD"] - variables["BC"]
        ab = ad_minus_bc // 2
        return {
            "AD_minus_BC": ad_minus_bc,
            "AB_found": ab,
        }

    def compute_answer_values(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[int]:
        return [intermediate_values["AB_found"]]

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return sample_four_object_story_context(rng, requested_theme)

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        if story["theme_code"] == "classic":
            return (
                f"На одной прямой точки A, B, C и D расположены в порядке A-B-C-D. "
                f"Известно, что AB = CD, BC = {format_distance(variables['BC'], story)}, "
                f"AD = {format_distance(variables['AD'], story)}. "
                f"Найдите длину отрезка AB."
            )

        first, second, third, fourth = story["objects"]
        first_between, second_between, third_between, fourth_between = story["objects_between"]
        return (
            f"{story['intro']} {first}, {second}, {third} и {fourth}. "
            f"Известно, что расстояние между {first_between} и {second_between} равно расстоянию между {third_between} и {fourth_between}. "
            f"Также известно, что расстояние между {second_between} и {third_between} равно {format_distance(variables['BC'], story)}, "
            f"а расстояние между {first_between} и {fourth_between} равно {format_distance(variables['AD'], story)}. "
            f"Найдите расстояние между {first_between} и {second_between}."
        )

    def describe_relations(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[str]:
        return [
            "AB = CD.",
            "AD = AB + BC + CD.",
            "Следовательно, AD = 2*AB + BC.",
        ]

    def is_valid(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> bool:
        return intermediate_values["AD_minus_BC"] % 2 == 0 and answer_values[0] > 0

    def build_metadata(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> Dict[str, Any]:
        return {
            "topic": "отношения между отрезками на прямой",
            "subtype": "равные отрезки",
            "formulas": ["AD = AB + BC + CD", "AB = CD", "AB = (AD - BC) / 2"],
        }


# ------------------------------------------------------------
# Шаблон 4. Плоскость: середина отрезка.
# M — середина AB, AM известно. Найти AB.
# ------------------------------------------------------------
class PlaneMidpointTemplate(SegmentProblemTemplate):
    def __init__(
        self,
        half_range: NumberRange,
        difficulty: DifficultyConstraints,
    ) -> None:
        super().__init__(
            name="plane_midpoint",
            code_prefix="PLMD",
            mode="plane",
            difficulty=difficulty,
        )
        self.half_range = half_range

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        am = self.half_range.sample(rng)
        ab = 2 * am
        return {"AM": am, "MB": am, "AB": ab}

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        return {"AB": variables["AB"]}

    def compute_answer_values(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[int]:
        return [variables["AB"]]

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return sample_three_object_story_context(rng, requested_theme)

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        if story["theme_code"] == "classic":
            return (
                f"На плоскости отмечены точки A, M и B. Точка M является серединой отрезка AB. "
                f"Известно, что AM = {format_distance(variables['AM'], story)}. Найдите длину отрезка AB."
            )

        first, middle, third = story["objects"]
        first_between, middle_between, third_between = story["objects_between"]
        return (
            f"{story['intro']} {first}, {middle} и {third}. "
            f"При этом {middle} находится ровно посередине между {first_between} и {third_between}. "
            f"Расстояние между {first_between} и {middle_between} равно {format_distance(variables['AM'], story)}. "
            f"Найдите расстояние между {first_between} и {third_between}."
        )

    def describe_relations(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[str]:
        return [
            "M — середина AB.",
            "AM = MB.",
            "AB = AM + MB = 2*AM.",
        ]

    def build_metadata(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> Dict[str, Any]:
        return {
            "topic": "отрезки на плоскости",
            "subtype": "середина отрезка",
            "formulas": ["AM = MB", "AB = 2*AM"],
        }


# ------------------------------------------------------------
# Шаблон 5. Плоскость: точка C лежит на отрезке AB.
# AB известно, AC известно. Найти CB.
# ------------------------------------------------------------
class PlanePointInsideSegmentTemplate(SegmentProblemTemplate):
    def __init__(
        self,
        ac_range: NumberRange,
        cb_range: NumberRange,
        difficulty: DifficultyConstraints,
    ) -> None:
        super().__init__(
            name="plane_point_inside_segment",
            code_prefix="PLIN",
            mode="plane",
            difficulty=difficulty,
        )
        self.ac_range = ac_range
        self.cb_range = cb_range

    def sample_variables(self, rng: random.Random) -> Optional[Dict[str, int]]:
        ac = self.ac_range.sample(rng)
        cb = self.cb_range.sample(rng)
        ab = ac + cb
        return {"AC": ac, "CB": cb, "AB": ab}

    def compute_intermediate_values(self, variables: Dict[str, int]) -> Dict[str, int]:
        return {"AB_minus_AC": variables["AB"] - variables["AC"]}

    def compute_answer_values(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[int]:
        return [intermediate_values["AB_minus_AC"]]

    def sample_story_context(self, rng: random.Random, requested_theme: str) -> Dict[str, Any]:
        return sample_three_object_story_context(rng, requested_theme)

    def render_problem_text(self, variables: Dict[str, int], story: Dict[str, Any]) -> str:
        if story["theme_code"] == "classic":
            return (
                f"На плоскости точка C лежит на отрезке AB. Известно, что AB = {format_distance(variables['AB'], story)}, "
                f"AC = {format_distance(variables['AC'], story)}. "
                f"Найдите длину отрезка CB."
            )

        first, middle, third = story["objects"]
        first_between, middle_between, third_between = story["objects_between"]
        return (
            f"{story['intro']} {first}, {middle} и {third}. "
            f"При этом {middle} находится между {first_between} и {third_between}. "
            f"Расстояние между {first_between} и {third_between} равно {format_distance(variables['AB'], story)}, "
            f"а между {first_between} и {middle_between} равно {format_distance(variables['AC'], story)}. "
            f"Найдите расстояние между {middle_between} и {third_between}."
        )

    def describe_relations(self, variables: Dict[str, int], intermediate_values: Dict[str, int]) -> List[str]:
        return [
            "Точка C лежит на отрезке AB.",
            "AB = AC + CB.",
            "CB = AB - AC.",
        ]

    def build_metadata(self, variables: Dict[str, int], intermediate_values: Dict[str, int], answer_values: Sequence[int]) -> Dict[str, Any]:
        return {
            "topic": "точка внутри отрезка",
            "subtype": "разбиение отрезка на части",
            "formulas": ["AB = AC + CB", "CB = AB - AC"],
        }


# ------------------------------------------------------------
# Реестр шаблонов
# ------------------------------------------------------------
class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, SegmentProblemTemplate] = {}

    def register(self, template: SegmentProblemTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> SegmentProblemTemplate:
        if name not in self._templates:
            available = ", ".join(sorted(self._templates.keys()))
            raise KeyError(f"Шаблон '{name}' не найден. Доступные шаблоны: {available}")
        return self._templates[name]

    def names(self) -> List[str]:
        return sorted(self._templates.keys())

    def choose_random(self, rng: random.Random, allowed_modes: Optional[Sequence[str]] = None) -> SegmentProblemTemplate:
        templates = list(self._templates.values())
        if allowed_modes:
            allowed_set = set(allowed_modes)
            templates = [t for t in templates if t.mode in allowed_set]
        if not templates:
            raise ValueError("Нет шаблонов, подходящих под выбранный режим.")
        return rng.choice(templates)


# ------------------------------------------------------------
# Генератор задач
# ------------------------------------------------------------
class SegmentProblemGenerator:
    """
    Генератор задач на отрезки.

    Режимы генерации:
    - seed_mode='today'  -> генерация детерминирована текущей датой;
    - seed_mode='random' -> генерация полностью случайная;
    - seed_mode='fixed'  -> генерация детерминирована заданным seed.
    """

    def __init__(self, registry: TemplateRegistry, seed_mode: str = "today", seed: Optional[int] = None) -> None:
        self.registry = registry
        self.seed_mode = seed_mode
        self.seed = self._resolve_seed(seed_mode, seed)
        self.rng = random.Random(self.seed)

    @staticmethod
    def _resolve_seed(seed_mode: str, seed: Optional[int]) -> Optional[int]:
        if seed_mode == "random":
            return None
        if seed_mode == "fixed":
            if seed is None:
                raise ValueError("Для режима 'fixed' нужно передать seed.")
            return seed
        if seed_mode == "today":
            # Используем текущую дату в формате YYYYMMDD.
            return int(datetime.now().strftime("%Y%m%d"))
        raise ValueError("seed_mode должен быть 'today', 'random' или 'fixed'.")

    def generate_one(
        self,
        template_name: Optional[str] = None,
        mode_filter: Optional[Sequence[str]] = None,
        sequence_number: int = 1,
        story_theme: str = "any",
    ) -> GeneratedProblem:
        if template_name is not None:
            template = self.registry.get(template_name)
        else:
            template = self.registry.choose_random(self.rng, allowed_modes=mode_filter)
        return template.generate(self.rng, sequence_number, story_theme=story_theme)

    def generate_many(
        self,
        count: int,
        template_names: Optional[Sequence[str]] = None,
        mode_filter: Optional[Sequence[str]] = None,
        random_templates: bool = True,
        story_theme: str = "any",
    ) -> List[GeneratedProblem]:
        if count <= 0:
            raise ValueError("Количество задач должно быть положительным.")

        problems: List[GeneratedProblem] = []

        if random_templates:
            for i in range(1, count + 1):
                template = self.registry.choose_random(self.rng, allowed_modes=mode_filter)
                problems.append(template.generate(self.rng, i, story_theme=story_theme))
            return problems

        if not template_names:
            raise ValueError(
                "Если random_templates=False, нужно передать template_names."
            )

        for i in range(1, count + 1):
            template_name = template_names[(i - 1) % len(template_names)]
            template = self.registry.get(template_name)
            if mode_filter and template.mode not in set(mode_filter):
                raise ValueError(
                    f"Шаблон '{template.name}' не входит в выбранный режим {list(mode_filter)}."
                )
            problems.append(template.generate(self.rng, i, story_theme=story_theme))

        return problems


# ------------------------------------------------------------
# Сохранение результатов
# ------------------------------------------------------------
def save_problems_to_json(
    problems: Sequence[GeneratedProblem],
    file_path: str | Path,
    seed_mode: str,
    seed_value: Optional[int],
    difficulty_level: str,
    difficulty_label: str,
    difficulty_description: str,
    requested_story_theme: str,
    requested_story_theme_label: str,
) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "count": len(problems),
        "count_text": count_with_word_ru(len(problems), ("задача", "задачи", "задач")),
        "seed_mode": seed_mode,
        "seed_value": seed_value,
        "difficulty_level": difficulty_level,
        "difficulty_label": difficulty_label,
        "difficulty_description": difficulty_description,
        "requested_story_theme": requested_story_theme,
        "requested_story_theme_label": requested_story_theme_label,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "problems": [p.to_dict() for p in problems],
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------
# Печать на экран
# ------------------------------------------------------------
def print_problems(problems: Sequence[GeneratedProblem]) -> None:
    print(f"Сгенерировано {count_with_word_ru(len(problems), ('задача', 'задачи', 'задач'))}.\n")

    for idx, problem in enumerate(problems, start=1):
        print(f"Задача {idx} [{problem.code}]")
        print(f"Режим: {problem.mode}")
        print(f"Шаблон: {problem.template_name}")
        if "label" in problem.difficulty:
            print(f"Сложность: {problem.difficulty['label']}")
        if problem.story:
            print(
                f"Сюжет: {problem.story.get('theme_label', 'без темы')} / "
                f"{problem.story.get('scene_label', 'без сцены')}"
            )
        print(f"Условие: {problem.problem_text}")
        print(f"Ответ: {problem.answer_text}")
        print("-" * 70)


# ------------------------------------------------------------
# Готовый набор шаблонов по умолчанию
# ------------------------------------------------------------
def build_default_registry(difficulty_level: str = "medium") -> TemplateRegistry:
    registry = TemplateRegistry()
    profile = get_difficulty_profile(difficulty_level)

    common_line_difficulty = profile.constraints
    common_plane_difficulty = profile.constraints

    registry.register(
        LineTwoSegmentsPossibleACTemplate(
            ab_range=profile.template_ranges["line_two_segments_possible_ac"]["ab_range"],
            bc_range=profile.template_ranges["line_two_segments_possible_ac"]["bc_range"],
            difficulty=common_line_difficulty,
        )
    )

    registry.register(
        LineThreeConsecutiveSegmentsTemplate(
            ab_range=profile.template_ranges["line_three_consecutive_segments"]["ab_range"],
            bc_range=profile.template_ranges["line_three_consecutive_segments"]["bc_range"],
            cd_range=profile.template_ranges["line_three_consecutive_segments"]["cd_range"],
            difficulty=common_line_difficulty,
        )
    )

    registry.register(
        LineEqualityRelationTemplate(
            equal_part_range=profile.template_ranges["line_equality_relation"]["equal_part_range"],
            middle_range=profile.template_ranges["line_equality_relation"]["middle_range"],
            difficulty=common_line_difficulty,
        )
    )

    registry.register(
        PlaneMidpointTemplate(
            half_range=profile.template_ranges["plane_midpoint"]["half_range"],
            difficulty=common_plane_difficulty,
        )
    )

    registry.register(
        PlanePointInsideSegmentTemplate(
            ac_range=profile.template_ranges["plane_point_inside_segment"]["ac_range"],
            cb_range=profile.template_ranges["plane_point_inside_segment"]["cb_range"],
            difficulty=common_plane_difficulty,
        )
    )

    return registry


# ------------------------------------------------------------
# Вспомогательные функции для CLI и веб-интерфейса
# ------------------------------------------------------------
def humanize_template_name(name: str) -> str:
    """Делает внутреннее имя шаблона удобнее для показа в UI."""
    return name.replace("_", " ")


def make_output_path(prefix: str = "segments") -> Path:
    """Создает имя JSON-файла по текущему времени."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("output") / f"{prefix}_{timestamp}.json"


def generate_problem_set(
    *,
    count: int,
    mode: str,
    template_name: str,
    difficulty_level: str,
    story_theme: str,
    seed_mode: str,
    seed: Optional[int],
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Генерирует набор задач и возвращает готовую структуру для UI и JSON.
    """

    profile = get_difficulty_profile(difficulty_level)
    registry = build_default_registry(difficulty_level)

    if count <= 0:
        raise ValueError("Количество задач должно быть положительным.")

    mode_filter = None if mode == "all" else [mode]

    if template_name != "any" and template_name not in registry.names():
        available = ", ".join(registry.names())
        raise ValueError(f"Шаблон '{template_name}' не найден. Доступные шаблоны: {available}")

    generator = SegmentProblemGenerator(registry, seed_mode=seed_mode, seed=seed)

    if template_name == "any":
        problems = generator.generate_many(
            count=count,
            mode_filter=mode_filter,
            random_templates=True,
            story_theme=story_theme,
        )
    else:
        problems = generator.generate_many(
            count=count,
            template_names=[template_name],
            mode_filter=mode_filter,
            random_templates=False,
            story_theme=story_theme,
        )

    if output_path is None:
        output_path = make_output_path("segments_web")

    for problem in problems:
        actual_intermediate_digits = [digit_length(value) for value in problem.intermediate_values.values()]
        actual_answer_digits = [digit_length(value) for value in problem.answer_values]
        problem.difficulty["level"] = profile.code
        problem.difficulty["label"] = profile.label
        problem.difficulty["description"] = profile.description
        problem.difficulty["actual_min_intermediate_digits"] = min(actual_intermediate_digits)
        problem.difficulty["actual_max_intermediate_digits"] = max(actual_intermediate_digits)
        problem.difficulty["actual_min_answer_digits"] = min(actual_answer_digits)
        problem.difficulty["actual_max_answer_digits"] = max(actual_answer_digits)

    save_problems_to_json(
        problems,
        file_path=output_path,
        seed_mode=generator.seed_mode,
        seed_value=generator.seed,
        difficulty_level=profile.code,
        difficulty_label=profile.label,
        difficulty_description=profile.description,
        requested_story_theme=story_theme,
        requested_story_theme_label=get_story_theme_label(story_theme),
    )

    return {
        "count": len(problems),
        "count_text": count_with_word_ru(len(problems), ("задача", "задачи", "задач")),
        "mode": mode,
        "template_name": template_name,
        "difficulty_level": profile.code,
        "difficulty_label": profile.label,
        "difficulty_description": profile.description,
        "requested_story_theme": story_theme,
        "requested_story_theme_label": get_story_theme_label(story_theme),
        "seed_mode": generator.seed_mode,
        "seed_value": generator.seed,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_path": str(output_path),
        "problems": [problem.to_dict() for problem in problems],
    }


def render_problem_cards(problems: Sequence[Dict[str, Any]]) -> str:
    """Рендерит HTML-карточки задач."""

    cards: List[str] = []

    for index, problem in enumerate(problems, start=1):
        difficulty_info = problem.get("difficulty", {})
        story_info = problem.get("story", {})
        unit_short = story_info.get("unit_short", "")
        relations_html = "".join(
            f"<li>{html.escape(relation)}</li>" for relation in problem["relations"]
        )
        variables_html = "".join(
            f"<div><span>{html.escape(name)}</span><strong>{html.escape(format_distance(value, story_info))}</strong></div>"
            for name, value in problem["variables"].items()
        )
        intermediate_html = "".join(
            f"<div><span>{html.escape(name)}</span><strong>{html.escape(format_distance(value, story_info))}</strong></div>"
            for name, value in problem["intermediate_values"].items()
        )

        cards.append(
            f"""
            <article class="problem-card">
              <div class="problem-card__head">
                <div>
                  <p class="eyebrow">Задача {index}</p>
                  <h3>{html.escape(problem["code"])}</h3>
                </div>
                <span class="badge">{html.escape(problem["mode"])}</span>
              </div>
              <p class="template-name">{html.escape(humanize_template_name(problem["template_name"]))}</p>
              <p class="template-name">Сложность: {html.escape(str(difficulty_info.get("label", "не указана")))}</p>
              <p class="template-name">Сюжет: {html.escape(str(story_info.get("theme_label", "без темы")))} / {html.escape(str(story_info.get("scene_label", "без сцены")))}</p>
              <p class="problem-text">{html.escape(problem["problem_text"])}</p>
              <p class="answer"><span>Ответ:</span> {html.escape(problem["answer_text"])}</p>
              <details>
                <summary>Показать детали</summary>
                <p class="hint">{html.escape(str(difficulty_info.get("description", "")))}</p>
                <p class="hint">Локация: {html.escape(str(story_info.get("location", "не указана")))}</p>
                <p class="hint">Единицы: {html.escape(str(unit_short or "не указаны"))}</p>
                <div class="details-grid">
                  <section>
                    <h4>Переменные</h4>
                    <div class="kv-grid">{variables_html}</div>
                  </section>
                  <section>
                    <h4>Промежуточные значения</h4>
                    <div class="kv-grid">{intermediate_html}</div>
                  </section>
                </div>
                <section>
                  <h4>Связи</h4>
                  <ul class="relations">{relations_html}</ul>
                </section>
              </details>
            </article>
            """
        )

    return "\n".join(cards)


def render_html_page(
    *,
    registry: TemplateRegistry,
    form_values: Dict[str, str],
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> str:
    """Собирает HTML страницы."""

    template_options = ['<option value="any">Любой шаблон</option>']
    for name in registry.names():
        selected = " selected" if form_values.get("template_name") == name else ""
        template_options.append(
            f'<option value="{html.escape(name)}"{selected}>{html.escape(humanize_template_name(name))}</option>'
        )

    mode_options = []
    for value, label in (("all", "Все режимы"), ("line", "Только прямая"), ("plane", "Только плоскость")):
        selected = " selected" if form_values.get("mode") == value else ""
        mode_options.append(f'<option value="{value}"{selected}>{label}</option>')

    seed_mode_options = []
    for value, label in (("today", "По сегодняшней дате"), ("random", "Случайный"), ("fixed", "Фиксированный")):
        selected = " selected" if form_values.get("seed_mode") == value else ""
        seed_mode_options.append(f'<option value="{value}"{selected}>{label}</option>')

    difficulty_options = []
    for value, profile in DIFFICULTY_PROFILES.items():
        selected = " selected" if form_values.get("difficulty_level") == value else ""
        difficulty_options.append(
            f'<option value="{value}"{selected}>{html.escape(profile.label)}</option>'
        )

    story_theme_options = []
    for value, label in STORY_THEME_LABELS.items():
        selected = " selected" if form_values.get("story_theme") == value else ""
        story_theme_options.append(
            f'<option value="{value}"{selected}>{html.escape(label)}</option>'
        )

    result_html = ""
    if result is not None:
        json_preview = html.escape(json.dumps(result, ensure_ascii=False, indent=2))
        download_link = f"/download?path={quote(result['output_path'])}"
        result_html = f"""
        <section class="panel result-panel">
          <div class="result-panel__head">
            <div>
              <p class="eyebrow">Результат</p>
              <h2>Создано: {html.escape(result["count_text"])}</h2>
            </div>
            <a class="download-link" href="{download_link}">Скачать JSON</a>
          </div>
          <div class="meta-strip">
            <span>Режим: {html.escape(result["mode"])}</span>
            <span>Шаблон: {html.escape(result["template_name"])}</span>
            <span>Сложность: {html.escape(result["difficulty_label"])}</span>
            <span>Тема: {html.escape(result["requested_story_theme_label"])}</span>
            <span>Seed mode: {html.escape(result["seed_mode"])}</span>
            <span>Seed: {html.escape(str(result["seed_value"]))}</span>
          </div>
          <p class="output-path">{html.escape(result["difficulty_description"])}</p>
          <p class="output-path">Файл сохранен: <code>{html.escape(result["output_path"])}</code></p>
          <div class="problem-list">
            {render_problem_cards(result["problems"])}
          </div>
          <details class="json-preview">
            <summary>Показать весь JSON</summary>
            <pre>{json_preview}</pre>
          </details>
        </section>
        """

    error_html = ""
    if error_message:
        error_html = f'<section class="panel error-panel">{html.escape(error_message)}</section>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Генератор задач на отрезки</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --bg-accent: #e4f0ea;
      --panel: rgba(255, 252, 246, 0.9);
      --panel-strong: #fffdf8;
      --text: #1d2a2f;
      --muted: #617174;
      --line: rgba(24, 52, 58, 0.14);
      --brand: #0e6b63;
      --brand-dark: #094d48;
      --warn: #8b2f39;
      --shadow: 0 20px 60px rgba(29, 42, 47, 0.12);
      --radius: 20px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Trebuchet MS", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, #fbf4cb 0, transparent 28%),
        radial-gradient(circle at top right, #d8efe5 0, transparent 24%),
        linear-gradient(180deg, var(--bg) 0%, #f8f4ec 48%, var(--bg-accent) 100%);
      min-height: 100vh;
    }}
    .page {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    .hero {{
      display: grid;
      gap: 10px;
      margin-bottom: 22px;
    }}
    .hero h1 {{
      margin: 0;
      font-size: clamp(2rem, 5vw, 3.8rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
      max-width: 12ch;
    }}
    .hero p {{
      margin: 0;
      color: var(--muted);
      max-width: 72ch;
      font-size: 1.05rem;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      backdrop-filter: blur(10px);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}
    .controls {{
      padding: 20px;
      position: sticky;
      top: 16px;
    }}
    .controls h2, .result-panel h2 {{
      margin: 0;
      font-size: 1.35rem;
    }}
    .eyebrow {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 0.72rem;
      color: var(--muted);
    }}
    .field {{
      display: grid;
      gap: 7px;
      margin-top: 14px;
    }}
    label {{
      font-weight: 600;
      font-size: 0.95rem;
    }}
    input, select, button {{
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      font: inherit;
      background: rgba(255, 255, 255, 0.84);
      color: var(--text);
    }}
    input:focus, select:focus {{
      outline: 2px solid rgba(14, 107, 99, 0.18);
      border-color: rgba(14, 107, 99, 0.5);
    }}
    .hint {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 0.88rem;
    }}
    button {{
      margin-top: 18px;
      background: linear-gradient(135deg, var(--brand), var(--brand-dark));
      color: white;
      border: none;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease;
    }}
    button:hover {{
      transform: translateY(-1px);
      opacity: 0.96;
    }}
    .result-panel {{
      padding: 20px;
      display: grid;
      gap: 16px;
    }}
    .result-panel__head {{
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
    }}
    .download-link {{
      color: white;
      text-decoration: none;
      background: #153f3d;
      padding: 10px 14px;
      border-radius: 999px;
    }}
    .meta-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .meta-strip span {{
      background: rgba(14, 107, 99, 0.08);
      border: 1px solid rgba(14, 107, 99, 0.12);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.92rem;
    }}
    .output-path {{
      margin: 0;
      color: var(--muted);
    }}
    .problem-list {{
      display: grid;
      gap: 14px;
    }}
    .problem-card {{
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
    }}
    .problem-card__head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
    }}
    .problem-card__head h3 {{
      margin: 0;
      font-size: 1.1rem;
    }}
    .badge {{
      background: #e6f6f4;
      color: var(--brand-dark);
      border-radius: 999px;
      padding: 8px 10px;
      font-size: 0.84rem;
      font-weight: 700;
    }}
    .template-name {{
      margin: 8px 0 0;
      color: var(--muted);
      text-transform: capitalize;
    }}
    .problem-text {{
      margin: 14px 0 12px;
      font-size: 1.02rem;
      line-height: 1.5;
    }}
    .answer {{
      margin: 0 0 10px;
      font-size: 1.05rem;
      font-weight: 700;
    }}
    .answer span {{
      color: var(--muted);
      font-weight: 600;
    }}
    details {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }}
    summary {{
      cursor: pointer;
      font-weight: 700;
    }}
    .details-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 12px;
    }}
    .details-grid h4, .problem-card h4 {{
      margin: 0 0 10px;
    }}
    .kv-grid {{
      display: grid;
      gap: 8px;
    }}
    .kv-grid div {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      background: rgba(14, 107, 99, 0.05);
      padding: 10px 12px;
      border-radius: 12px;
    }}
    .relations {{
      margin: 10px 0 0;
      padding-left: 18px;
      color: var(--muted);
    }}
    .json-preview pre {{
      overflow-x: auto;
      background: #182629;
      color: #eff8f6;
      padding: 16px;
      border-radius: 16px;
      font-size: 0.88rem;
    }}
    .error-panel {{
      padding: 16px 18px;
      color: white;
      background: linear-gradient(135deg, #9d4251, var(--warn));
      border: none;
    }}
    @media (max-width: 920px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .controls {{
        position: static;
      }}
      .details-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <p class="eyebrow">Локальный сайт</p>
      <h1>Генератор задач на отрезки</h1>
      <p>Страница запускает генерацию прямо из Python, показывает условия и ответы в браузере и сразу сохраняет тот же набор задач в JSON.</p>
    </section>
    {error_html}
    <section class="layout">
      <form class="panel controls" method="get" action="/">
        <input type="hidden" name="generate" value="1">
        <p class="eyebrow">Параметры</p>
        <h2>Новый набор</h2>
        <div class="field">
          <label for="count">Количество задач</label>
          <input id="count" type="number" min="1" max="500" name="count" value="{html.escape(form_values["count"])}">
        </div>
        <div class="field">
          <label for="mode">Режим</label>
          <select id="mode" name="mode">
            {"".join(mode_options)}
          </select>
        </div>
        <div class="field">
          <label for="template_name">Шаблон</label>
          <select id="template_name" name="template_name">
            {"".join(template_options)}
          </select>
        </div>
        <div class="field">
          <label for="difficulty_level">Сложность</label>
          <select id="difficulty_level" name="difficulty_level">
            {"".join(difficulty_options)}
          </select>
          <p class="hint">Один и тот же шаблон генерируется с разными диапазонами чисел: чем больше числа, тем сложнее вычисления.</p>
        </div>
        <div class="field">
          <label for="story_theme">Тема сюжета</label>
          <select id="story_theme" name="story_theme">
            {"".join(story_theme_options)}
          </select>
          <p class="hint">Можно оставить любую тему, а можно заставить задачу звучать как дорога, сказка, космос, муравьи или мультгерои.</p>
        </div>
        <div class="field">
          <label for="seed_mode">Источник случайности</label>
          <select id="seed_mode" name="seed_mode">
            {"".join(seed_mode_options)}
          </select>
        </div>
        <div class="field">
          <label for="seed">Seed</label>
          <input id="seed" type="number" name="seed" value="{html.escape(form_values["seed"])}" placeholder="Нужно только для fixed">
          <p class="hint">Если выбран режим <code>fixed</code>, укажите число. Для остальных режимов поле можно оставить пустым.</p>
        </div>
        <button type="submit">Сгенерировать</button>
      </form>
      {result_html or '<section class="panel result-panel"><p class="eyebrow">Результат</p><h2>Пока пусто</h2><p class="output-path">Выберите параметры слева и нажмите «Сгенерировать».</p></section>'}
    </section>
  </main>
</body>
</html>
"""


class ProblemWebHandler(BaseHTTPRequestHandler):
    """HTTP-обработчик для локального UI."""

    registry = build_default_registry()

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            form_values = {
                "count": "5",
                "mode": "all",
                "template_name": "any",
                "difficulty_level": "medium",
                "story_theme": "any",
                "seed_mode": "today",
                "seed": "",
            }
            page = render_html_page(
                registry=self.registry,
                form_values=form_values,
                result=None,
                error_message=None,
            )
            payload = page.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            return

        if parsed.path == "/download":
            query = parse_qs(parsed.query)
            raw_path = query.get("path", [""])[0]
            if not raw_path:
                self.send_error(HTTPStatus.BAD_REQUEST, "Не указан путь к файлу")
                return

            output_root = (Path.cwd() / "output").resolve()
            requested_path = Path(raw_path)
            if not requested_path.is_absolute():
                requested_path = (Path.cwd() / requested_path).resolve()
            else:
                requested_path = requested_path.resolve()

            if output_root not in requested_path.parents:
                self.send_error(HTTPStatus.FORBIDDEN, "Можно скачивать только файлы из output")
                return

            if not requested_path.exists() or not requested_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "Файл не найден")
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(requested_path.stat().st_size))
            self.send_header(
                "Content-Disposition",
                f'inline; filename="{requested_path.name}"',
            )
            self.end_headers()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.handle_index(parsed)
            return

        if parsed.path == "/download":
            self.handle_download(parsed)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Страница не найдена")

    def handle_index(self, parsed_url) -> None:
        query = parse_qs(parsed_url.query)
        form_values = {
            "count": query.get("count", ["5"])[0],
            "mode": query.get("mode", ["all"])[0],
            "template_name": query.get("template_name", ["any"])[0],
            "difficulty_level": query.get("difficulty_level", ["medium"])[0],
            "story_theme": query.get("story_theme", ["any"])[0],
            "seed_mode": query.get("seed_mode", ["today"])[0],
            "seed": query.get("seed", [""])[0],
        }

        result: Optional[Dict[str, Any]] = None
        error_message: Optional[str] = None

        if query.get("generate", ["0"])[0] == "1":
            try:
                count = int(form_values["count"])
                seed_raw = form_values["seed"].strip()
                seed = int(seed_raw) if seed_raw else None
                result = generate_problem_set(
                    count=count,
                    mode=form_values["mode"],
                    template_name=form_values["template_name"],
                    difficulty_level=form_values["difficulty_level"],
                    story_theme=form_values["story_theme"],
                    seed_mode=form_values["seed_mode"],
                    seed=seed,
                )
            except Exception as error:
                error_message = str(error)

        page = render_html_page(
            registry=self.registry,
            form_values=form_values,
            result=result,
            error_message=error_message,
        )
        self.respond_html(page)

    def handle_download(self, parsed_url) -> None:
        query = parse_qs(parsed_url.query)
        raw_path = query.get("path", [""])[0]
        if not raw_path:
            self.send_error(HTTPStatus.BAD_REQUEST, "Не указан путь к файлу")
            return

        output_root = (Path.cwd() / "output").resolve()
        requested_path = Path(raw_path)
        if not requested_path.is_absolute():
            requested_path = (Path.cwd() / requested_path).resolve()
        else:
            requested_path = requested_path.resolve()

        if output_root not in requested_path.parents:
            self.send_error(HTTPStatus.FORBIDDEN, "Можно скачивать только файлы из output")
            return

        if not requested_path.exists() or not requested_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Файл не найден")
            return

        content = requested_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header(
            "Content-Disposition",
            f'inline; filename="{requested_path.name}"',
        )
        self.end_headers()
        self.wfile.write(content)

    def respond_html(self, page: str) -> None:
        payload = page.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        """Оставляем короткий лог для локальной отладки."""
        print(f"[web] {self.address_string()} - {format % args}")


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """HTTP-сервер, который лучше переживает быстрые перезапуски."""

    allow_reuse_address = True


def create_http_server(host: str, port: int, max_port_tries: int = 20) -> tuple[ReusableThreadingHTTPServer, int]:
    """
    Пытается открыть сервер на выбранном порту.
    Если порт занят, пробует следующие порты.
    """

    last_error: Optional[OSError] = None

    for current_port in range(port, port + max_port_tries):
        try:
            server = ReusableThreadingHTTPServer((host, current_port), ProblemWebHandler)
            return server, current_port
        except OSError as error:
            last_error = error
            if error.errno != 48:
                raise

    raise OSError(
        48,
        f"Не удалось найти свободный порт в диапазоне {port}-{port + max_port_tries - 1}",
    ) from last_error


def run_server(host: str, port: int) -> None:
    """Запускает локальный HTTP-сервер."""

    try:
        server, actual_port = create_http_server(host, port)
    except OSError as error:
        if error.errno == 48:
            raise SystemExit(str(error)) from error
        raise

    if actual_port != port:
        print(f"Порт {port} занят, выбран свободный порт {actual_port}.")

    display_host = host
    if host == "0.0.0.0":
        display_host = "127.0.0.1"

    print(f"Сайт запущен: http://{display_host}:{actual_port}")
    print("Остановить сервер: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""

    parser = argparse.ArgumentParser(
        description="Генератор задач на отрезки: консольный режим и локальный сайт."
    )
    parser.add_argument("--serve", action="store_true", help="Запустить локальный веб-сервер.")
    parser.add_argument("--host", default="127.0.0.1", help="Хост для веб-сервера.")
    parser.add_argument("--port", type=int, default=8000, help="Порт для веб-сервера.")
    parser.add_argument("--count", type=int, default=5, help="Количество задач в консольном режиме.")
    parser.add_argument(
        "--mode",
        default="all",
        choices=["all", "line", "plane"],
        help="Фильтр по режиму задач.",
    )
    parser.add_argument(
        "--template-name",
        default="any",
        help="Имя шаблона или 'any', чтобы брать разные шаблоны.",
    )
    parser.add_argument(
        "--difficulty-level",
        default="medium",
        choices=sorted(DIFFICULTY_PROFILES.keys()),
        help="Уровень сложности: влияет на диапазоны чисел и размер промежуточных вычислений.",
    )
    parser.add_argument(
        "--story-theme",
        default="any",
        choices=sorted(STORY_THEME_LABELS.keys()),
        help="Сюжетная тема для текстов задач.",
    )
    parser.add_argument(
        "--seed-mode",
        default="today",
        choices=["today", "random", "fixed"],
        help="Режим генерации случайных чисел.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Число для fixed seed.")
    parser.add_argument(
        "--output",
        default="outputs/generated/segments_cli.json",
        help="Куда сохранять JSON в консольном режиме.",
    )
    return parser.parse_args()


def run_cli(args: argparse.Namespace) -> None:
    """Обычный запуск без веб-сервера."""

    result = generate_problem_set(
        count=args.count,
        mode=args.mode,
        template_name=args.template_name,
        difficulty_level=args.difficulty_level,
        story_theme=args.story_theme,
        seed_mode=args.seed_mode,
        seed=args.seed,
        output_path=Path(args.output),
    )

    problems = [
        GeneratedProblem(
            code=problem["code"],
            category=problem["category"],
            mode=problem["mode"],
            template_name=problem["template_name"],
            problem_text=problem["problem_text"],
            answer_text=problem["answer_text"],
            answer_values=problem["answer_values"],
            story=problem["story"],
            variables=problem["variables"],
            intermediate_values=problem["intermediate_values"],
            relations=problem["relations"],
            difficulty=problem["difficulty"],
            metadata=problem["metadata"],
        )
        for problem in result["problems"]
    ]
    print_problems(problems)
    print(f"JSON сохранен в файл: {result['output_path']}")


# ------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------
def main() -> None:
    args = parse_args()
    if args.serve:
        run_server(args.host, args.port)
        return
    run_cli(args)


if __name__ == "__main__":
    main()
