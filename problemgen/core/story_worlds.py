from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class StoryWorld:
    key: str
    title: str
    location: str
    characters: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class StoryContext:
    world: StoryWorld
    location: str
    characters: tuple[str, ...]
    lead_character: str
    support_characters: tuple[str, ...]
    world_key: str
    world_title: str
    characters_text: str

    def to_metadata(self) -> dict[str, object]:
        return {
            "world_key": self.world_key,
            "world_title": self.world_title,
            "location": self.location,
            "characters": list(self.characters),
            "lead_character": self.lead_character,
            "support_characters": list(self.support_characters),
        }


def _world(
    key: str,
    title: str,
    location: str,
    characters: list[str],
    notes: str = "",
) -> StoryWorld:
    return StoryWorld(
        key=key,
        title=title,
        location=location,
        characters=tuple(characters),
        notes=notes,
    )


STORY_WORLDS: dict[str, StoryWorld] = {
    "russian_fairytales": _world(
        "russian_fairytales",
        "Русские народные сказки",
        "Волшебный лес, тридевятое царство и избушка Бабы-Яги",
        [
            "Баба-Яга",
            "Кощей Бессмертный",
            "Змей Горыныч",
            "Иван-царевич",
            "Василиса Прекрасная",
            "Царевна-лягушка",
            "Серый Волк",
            "Емеля",
            "Щука",
            "Морозко",
            "Снегурочка",
            "Алёнушка",
            "Иванушка",
            "Конёк-Горбунок",
            "Сивка-Бурка",
        ],
    ),
    "chukovsky": _world(
        "chukovsky",
        "Сказки Корнея Чуковского",
        "Сказочный город Чуковского",
        [
            "Айболит",
            "Бармалей",
            "Муха-Цокотуха",
            "Комарик",
            "Мойдодыр",
            "Федора",
            "Тараканище",
            "Крокодил",
        ],
    ),
    "buratino": _world(
        "buratino",
        "Золотой ключик",
        "Городок Буратино, театр Карабаса-Барабаса и каморка папы Карло",
        [
            "Буратино",
            "Мальвина",
            "Пьеро",
            "Артемон",
            "Карабас-Барабас",
            "Дуремар",
            "Кот Базилио",
            "Лиса Алиса",
        ],
    ),
    "prostokvashino": _world(
        "prostokvashino",
        "Простоквашино",
        "Деревня Простоквашино",
        [
            "Дядя Фёдор",
            "Кот Матроскин",
            "Шарик",
            "Почтальон Печкин",
            "Галчонок Хватайка",
        ],
    ),
    "cheburashka": _world(
        "cheburashka",
        "Чебурашка",
        "Город Чебурашки и Крокодила Гены",
        [
            "Чебурашка",
            "Крокодил Гена",
            "Шапокляк",
            "Крыска Лариска",
        ],
    ),
    "winnie_pooh": _world(
        "winnie_pooh",
        "Винни-Пух",
        "Стоакровый лес",
        [
            "Винни-Пух",
            "Пятачок",
            "Иа-Иа",
            "Кролик",
            "Сова",
            "Тигра",
        ],
    ),
    "carlson": _world(
        "carlson",
        "Карлсон",
        "Стокгольм, дом Малыша и крыша",
        [
            "Карлсон",
            "Малыш",
            "Фрекен Бок",
            "Дядя Юлиус",
            "Боссе",
        ],
    ),
    "neznaika": _world(
        "neznaika",
        "Незнайка",
        "Цветочный город",
        [
            "Незнайка",
            "Знайка",
            "Пончик",
            "Синеглазка",
            "Торопыжка",
            "Пилюлькин",
        ],
    ),
    "fixiki": _world(
        "fixiki",
        "Фиксики",
        "Квартира ДимДимыча и лаборатория профессора Чудакова",
        [
            "Нолик",
            "Симка",
            "Папус",
            "Мася",
            "Верта",
            "Файер",
            "Игрек",
        ],
    ),
    "luntik": _world(
        "luntik",
        "Лунтик",
        "Лесная поляна и пруд",
        [
            "Лунтик",
            "Кузя",
            "Пчелёнок",
            "Мила",
            "Генерал Шер",
            "Баба Капа",
            "Дед Шер",
        ],
    ),
    "peppa_pig": _world(
        "peppa_pig",
        "Свинка Пеппа",
        "Дом семьи Свинок, детский сад и городок Пеппы",
        [
            "Свинка Пеппа",
            "Джордж",
            "Мама Свинка",
            "Папа Свин",
            "Бабушка Свинка",
            "Дедушка Свин",
        ],
    ),
    "frozen": _world(
        "frozen",
        "Холодное сердце",
        "Королевство Эренделл",
        [
            "Эльза",
            "Анна",
            "Олаф",
            "Кристофф",
            "Свен",
            "Ханс",
        ],
    ),
    "lion_king": _world(
        "lion_king",
        "Король Лев",
        "Земли Прайда",
        [
            "Симба",
            "Нала",
            "Муфаса",
            "Шрам",
            "Тимон",
            "Пумба",
            "Рафики",
        ],
    ),
    "how_to_train_your_dragon": _world(
        "how_to_train_your_dragon",
        "Как приручить дракона",
        "Остров Олух",
        [
            "Иккинг",
            "Беззубик",
            "Стоик",
            "Астрид",
            "Сморкала",
            "Рыбьеног",
        ],
    ),
    "shrek": _world(
        "shrek",
        "Шрек",
        "Болото Шрека и королевство Далеко-далеко",
        [
            "Шрек",
            "Осёл",
            "Фиона",
            "Кот в сапогах",
            "Пряничный человечек",
            "Пиноккио",
            "Лорд Фаркуад",
        ],
    ),
    "kung_fu_panda": _world(
        "kung_fu_panda",
        "Кунг-фу Панда",
        "Долина Мира и Нефритовый дворец",
        [
            "По",
            "Шифу",
            "Тигрица",
            "Обезьяна",
            "Журавль",
            "Богомол",
            "Гадюка",
        ],
    ),
    "tom_and_jerry": _world(
        "tom_and_jerry",
        "Том и Джерри",
        "Дом хозяев Тома",
        [
            "Том",
            "Джерри",
            "Спайк",
            "Тайк",
            "Таффи",
        ],
    ),
    "paw_patrol": _world(
        "paw_patrol",
        "Щенячий патруль",
        "Бухта Приключений",
        [
            "Гонщик",
            "Маршал",
            "Крепыш",
            "Скай",
            "Зума",
            "Рокки",
            "Эверест",
        ],
    ),
    "smeshariki": _world(
        "smeshariki",
        "Смешарики",
        "Долина Смешариков",
        [
            "Крош",
            "Ёжик",
            "Нюша",
            "Бараш",
            "Лосяш",
            "Копатыч",
            "Совунья",
            "Пин",
            "Кар-Карыч",
        ],
    ),
}


def get_story_world(key: str) -> StoryWorld:
    try:
        return STORY_WORLDS[key]
    except KeyError as error:
        available = ", ".join(sorted(STORY_WORLDS))
        raise ValueError(f"Неизвестный сюжетный мир '{key}'. Доступно: {available}") from error


def list_story_worlds() -> list[StoryWorld]:
    return [STORY_WORLDS[key] for key in sorted(STORY_WORLDS)]


def sample_story_world(
    rng: random.Random | None = None,
    allowed_keys: list[str] | tuple[str, ...] | None = None,
) -> StoryWorld:
    chooser = rng or random.Random()
    if allowed_keys:
        worlds = [get_story_world(key) for key in allowed_keys]
    else:
        worlds = list(STORY_WORLDS.values())
    return chooser.choice(worlds)


def sample_story_context(
    rng: random.Random | None = None,
    world_key: str | None = None,
    min_characters: int = 2,
    max_characters: int = 4,
) -> StoryContext:
    chooser = rng or random.Random()
    world = get_story_world(world_key) if world_key else sample_story_world(chooser)
    if min_characters < 1:
        raise ValueError("min_characters должно быть не меньше 1.")
    if max_characters < min_characters:
        raise ValueError("max_characters должно быть не меньше min_characters.")

    upper_bound = min(max_characters, len(world.characters))
    sample_size = chooser.randint(min_characters, upper_bound)
    characters = tuple(chooser.sample(list(world.characters), sample_size))
    lead_character = characters[0]
    support_characters = characters[1:]
    characters_text = ", ".join(characters)
    return StoryContext(
        world=world,
        location=world.location,
        characters=characters,
        lead_character=lead_character,
        support_characters=support_characters,
        world_key=world.key,
        world_title=world.title,
        characters_text=characters_text,
    )
