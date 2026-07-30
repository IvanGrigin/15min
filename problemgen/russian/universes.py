"""Вселенные: группы, локации с падежами и предметы, уместные в мире.

Чтобы добавить вселенную, локацию или предмет, отредактируйте
    data/entities/universes.json
Python-код менять не нужно.

Локация ведёт себя так же, как персонаж и существительное: у неё есть шесть форм
единственного числа и метод ``get_case``, поэтому она подставляется в те же слоты
шаблона — ``{place:pre}``, ``{place:acc}``. Дополнительно у локации есть предлог
(«в» или «на»), потому что его нельзя вывести из формы слова: «в Хогвартсе», но
«на пляже». Слот ``{place:loc}`` подставляет предлог вместе с предложным падежом.

Предметы хранятся леммами: сами формы лежат в словаре существительных, здесь —
только принадлежность миру, чтобы в Простоквашино не появился световой меч.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .noun_dict import NOUNS

_UNIVERSES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "entities" / "universes.json"

_CASES = ("nom", "gen", "dat", "acc", "ins", "pre")
_PREPOSITIONS = frozenset({"в", "на"})
_GENDERS = frozenset({"m", "f", "n"})
# Возрастной рейтинг вселенной — та же шкала, что у российских медиа
# (0+/6+/12+/16+/18+). Сейчас использованы только 0+/6+/12+: все 116 вселенных
# семейные, а 16+/18+ зарезервированы под будущие темы для подростков старшего
# возраста. Ни один шаблон не производит текста, требующего такого рейтинга, —
# это фильтр по источнику франшизы, а не по содержимому сгенерированной задачи.
_AGE_RATINGS = ("0+", "6+", "12+", "16+", "18+")
# Мягкая метка «кому исторически адресован маркетинг франшизы» — не про то,
# кто способен решать задачи. По умолчанию «any», и генератор всегда может её
# игнорировать: это ровно опциональный фильтр вкуса, а не правило доступа.
_AUDIENCES = ("any", "girls", "boys")


class UniverseRegistryError(ValueError):
    """Реестр вселенных нельзя загрузить или он внутренне противоречив."""


@dataclass(frozen=True)
class Location:
    """Локация с явной падежной парадигмой и предлогом употребления."""

    location_id: str
    universe: str
    preposition: str
    gender: str
    nom: str
    gen: str
    dat: str
    acc: str
    ins: str
    pre: str

    @property
    def name(self) -> str:
        """Название локации в именительном падеже."""
        return self.nom

    def get_case(self, case: str) -> str:
        """Форма по падежу плюс два составных слота с предлогом.

        ``loc`` — где: предлог + предложный падеж («в Хогвартсе», «на пляже»).
        ``dir`` — куда: тот же предлог + винительный («в Хогвартс», «на пляж»).
        Разделять их обязательно: «отправился в Хижине чудес» — сломанный текст.
        """
        if case == "loc":
            return f"{self.preposition} {self.pre}"
        if case == "dir":
            return f"{self.preposition} {self.acc}"
        if case not in _CASES:
            raise ValueError(
                "Для локации доступны падежи единственного числа "
                f"({', '.join(_CASES)}), 'loc' (где) и 'dir' (куда); получено '{case}'."
            )
        return getattr(self, case)


@dataclass(frozen=True)
class Universe:
    """Вселенная: группа миров, её локации и уместные в ней предметы."""
    universe: str
    group: str
    locations: tuple[Location, ...]
    items: tuple[str, ...]
    valuables: tuple[str, ...]
    currency: tuple[str, ...]
    folk: tuple[str, ...]
    age_rating: str
    audience: str


def _location_from(entry: dict, universe: str) -> Location:
    location_id = str(entry.get("location_id") or "")
    if not location_id:
        raise UniverseRegistryError(f"{universe}: у локации нет 'location_id'.")
    preposition = str(entry.get("preposition") or "")
    if preposition not in _PREPOSITIONS:
        raise UniverseRegistryError(
            f"{location_id}: предлог должен быть одним из {sorted(_PREPOSITIONS)}, получено {preposition!r}."
        )
    gender = str(entry.get("gender") or "")
    if gender not in _GENDERS:
        raise UniverseRegistryError(f"{location_id}: род должен быть одним из {sorted(_GENDERS)}.")
    cases = entry.get("cases")
    if not isinstance(cases, dict):
        raise UniverseRegistryError(f"{location_id}: поле 'cases' должно быть объектом с шестью формами.")
    missing = [case for case in _CASES if not str(cases.get(case, "")).strip()]
    if missing:
        raise UniverseRegistryError(f"{location_id}: не заполнены падежи: {', '.join(missing)}.")
    return Location(
        location_id=location_id,
        universe=universe,
        preposition=preposition,
        gender=gender,
        **{case: str(cases[case]) for case in _CASES},
    )


@lru_cache(maxsize=1)
def load_universes() -> dict[str, Universe]:
    """Загрузить и проверить реестр вселенных из data/entities/universes.json."""
    payload = json.loads(_UNIVERSES_PATH.read_text(encoding="utf-8"))
    groups = payload.get("groups")
    if not isinstance(groups, dict) or not groups:
        raise UniverseRegistryError("universes.json: нет словаря 'groups'.")
    entries = payload.get("universes")
    if not isinstance(entries, list) or not entries:
        raise UniverseRegistryError("universes.json: нет списка 'universes'.")

    registry: dict[str, Universe] = {}
    seen_location_ids: set[str] = set()
    for entry in entries:
        name = str(entry.get("universe") or "")
        if not name:
            raise UniverseRegistryError("universes.json: у вселенной нет поля 'universe'.")
        if name in registry:
            raise UniverseRegistryError(f"Вселенная {name!r} описана дважды.")
        group = str(entry.get("group") or "")
        if group not in groups:
            raise UniverseRegistryError(f"{name}: группы {group!r} нет в 'groups'.")
        locations = tuple(_location_from(item, name) for item in entry.get("locations", []))
        if not locations:
            raise UniverseRegistryError(f"{name}: не задано ни одной локации.")
        for location in locations:
            if location.location_id in seen_location_ids:
                raise UniverseRegistryError(f"Повторяющийся location_id: {location.location_id}.")
            seen_location_ids.add(location.location_id)
        items = tuple(str(item) for item in entry.get("items", []))
        unknown = [item for item in items if item not in NOUNS]
        if unknown:
            raise UniverseRegistryError(
                f"{name}: предметов нет в словаре существительных: {', '.join(unknown)}."
            )
        # Предметы вселенной попадают в счётные слоты («у Кроша 5 пирогов»),
        # поэтому вещественные слова сюда нельзя: «5 мёдов» — сломанный текст.
        uncountable = [item for item in items if not NOUNS[item].countable]
        if uncountable:
            raise UniverseRegistryError(
                f"{name}: вещественные существительные нельзя класть в items: {', '.join(uncountable)}."
            )
        # Как зовут обитателей мира. Нужен задачам про толпу: очередь, класс,
        # турнир. Без этого слоя шаблон пишет «пираты» леммой и одна и та же
        # очередь за похлёбкой выпадает во всех 116 вселенных.
        folk = tuple(str(item) for item in entry.get("folk", []))
        if not folk:
            raise UniverseRegistryError(f"{name}: не задан 'folk' — как зовут обитателей мира.")
        unknown = [item for item in folk if item not in NOUNS]
        if unknown:
            raise UniverseRegistryError(
                f"{name}: обитателей нет в словаре существительных: {', '.join(unknown)}."
            )
        # Требуется только счётность. Одушевлённость здесь ни при чём: «машина»,
        # «игрушка» и «эмоция» грамматически неодушевлённые, а в сюжете это
        # полноценные обитатели мира — Тачки, История игрушек, Головоломка.
        wrong = [item for item in folk if not NOUNS[item].countable]
        if wrong:
            raise UniverseRegistryError(
                f"{name}: 'folk' — счётные слова; вещественные не годятся: {', '.join(wrong)}."
            )
        valuables = tuple(str(item) for item in entry.get("valuables", []))
        currency = tuple(str(item) for item in entry.get("currency", []))
        unknown = [item for item in valuables + currency if item not in NOUNS]
        if unknown:
            raise UniverseRegistryError(
                f"{name}: ценностей нет в словаре существительных: {', '.join(unknown)}."
            )
        uncountable = [item for item in valuables + currency if not NOUNS[item].countable]
        if uncountable:
            raise UniverseRegistryError(
                f"{name}: вещественные существительные нельзя класть в valuables: "
                f"{', '.join(uncountable)}."
            )
        age_rating = str(entry.get("age_rating") or "")
        if age_rating not in _AGE_RATINGS:
            raise UniverseRegistryError(
                f"{name}: age_rating должен быть одним из {_AGE_RATINGS}, получено {age_rating!r}."
            )
        audience = str(entry.get("audience") or "")
        if audience not in _AUDIENCES:
            raise UniverseRegistryError(
                f"{name}: audience должен быть одним из {_AUDIENCES}, получено {audience!r}."
            )
        registry[name] = Universe(
            universe=name, group=group, locations=locations, items=items,
            valuables=valuables, currency=currency, folk=folk,
            age_rating=age_rating, audience=audience)
    return registry


def universe_groups() -> dict[str, str]:
    """Ключ группы -> человекочитаемое название."""
    payload = json.loads(_UNIVERSES_PATH.read_text(encoding="utf-8"))
    return dict(payload["groups"])


def locations_of(universe: str) -> tuple[Location, ...]:
    """Вернуть локации вселенной с полной падежной парадигмой."""
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].locations


def items_of(universe: str) -> tuple[str, ...]:
    """Вернуть леммы предметов, уместных в этой вселенной."""
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].items


def valuables_of(universe: str) -> tuple[str, ...]:
    """Ценности мира: что его персонажи делят, собирают и считают."""
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].valuables


def folk_of(universe: str) -> tuple[str, ...]:
    """Как зовут обитателей мира: пираты, джедаи, роботы, жители."""
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].folk


def currency_of(universe: str) -> tuple[str, ...]:
    """Деньги мира: чем в нём расплачиваются и что делят поровну."""
    registry = load_universes()
    if universe not in registry:
        raise UniverseRegistryError(f"Вселенной {universe!r} нет в data/entities/universes.json.")
    return registry[universe].currency


def age_rating_options() -> tuple[str, ...]:
    """Шкала возрастных рейтингов по возрастанию строгости — для сайта и API."""
    return _AGE_RATINGS


def audience_options() -> tuple[str, ...]:
    """Значения мягкой метки предпочтения по вкусу — для сайта и API."""
    return _AUDIENCES


def universes_in_group(group: str) -> tuple[str, ...]:
    """Вернуть вселенные одной группы миров, отсортированные по названию."""
    return tuple(sorted(name for name, universe in load_universes().items() if universe.group == group))


# Порядок шкалы: вселенная с рейтингом X подходит запросу «не выше Y», если
# X не строже Y. «Обычные имена» — 0+, поэтому проходит любой порог.
_RATING_ORDER = {rating: index for index, rating in enumerate(_AGE_RATINGS)}


def universes_matching(
    max_age_rating: str | None = None, audience: str | None = None
) -> tuple[str, ...]:
    """Вселенные не строже заданного рейтинга и (опционально) одной аудитории.

    Пустой результат означает содержательный факт о данных (например, в этой
    аудитории нет вселенных 0+), а не ошибку — вызывающий код решает, что
    с этим делать: ослабить фильтр или сообщить пользователю.
    """
    if max_age_rating is not None and max_age_rating not in _AGE_RATINGS:
        raise UniverseRegistryError(
            f"max_age_rating должен быть одним из {_AGE_RATINGS}, получено {max_age_rating!r}."
        )
    if audience is not None and audience not in _AUDIENCES:
        raise UniverseRegistryError(
            f"audience должен быть одним из {_AUDIENCES}, получено {audience!r}."
        )
    ceiling = _RATING_ORDER[max_age_rating] if max_age_rating is not None else None
    return tuple(sorted(
        name for name, universe in load_universes().items()
        if (ceiling is None or _RATING_ORDER[universe.age_rating] <= ceiling)
        and (audience is None or universe.audience in {audience, "any"})
    ))
