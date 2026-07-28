"""Топонимы: города с падежами и предлогом.

Чтобы добавить город, допишите одну запись в
    data/entities/toponyms.json
Python-код менять не нужно.

Зачем отдельный слой. Без падежей приходится писать «поезд из города Чита»:
конструкция с приложением грамматически верна, но делает текст деревянным.
С падежами получается «поезд идёт в Читу», «вылетел из Читы», «в Чите 15:20».

Обратный предлог не хранится, а выводится: «в Чите» -> «из Читы»,
«на Камчатке» -> «с Камчатки». Это правило без исключений, и дублировать
его в данных значит заводить место для ошибки.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_TOPONYMS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "entities" / "toponyms.json"
)
_CASES = ("nom", "gen", "dat", "acc", "ins", "pre")
_PREPOSITIONS = {"в": "из", "на": "с"}
_GENDERS = frozenset({"m", "f", "n"})


def _in_or_vo(preposition: str, word: str) -> str:
    """Выбор между «в» и «во»: во Владивосток, но в Воронеж.

    «во» ставится перед в/ф со следующей согласной. Как и «с»/«со», правило
    работает на форму слова, поэтому живёт рядом с рендером, а не в данных.
    """
    if preposition != "в" or len(word) < 2:
        return preposition
    first, second = word[0].lower(), word[1].lower()
    vowels = "аеёиоуыэюя"
    return "во" if first in "вф" and second not in vowels and second != "ь" else "в"


class ToponymRegistryError(ValueError):
    """Реестр топонимов нельзя загрузить или он внутренне противоречив."""


@dataclass(frozen=True)
class Toponym:
    """Город с падежной парадигмой, предлогом места и группой."""

    toponym_id: str
    preposition: str
    gender: str
    region: str
    kind: str
    utc_offset: int
    nom: str
    gen: str
    dat: str
    acc: str
    ins: str
    pre: str

    @property
    def name(self) -> str:
        """Название в именительном падеже."""
        return self.nom

    def get_case(self, case: str) -> str:
        """Форма по падежу плюс три составных слота с предлогом.

        ``loc`` — где: «в Чите», «на Камчатке».
        ``dir`` — куда: «в Читу», «на Камчатку».
        ``from`` — откуда: «из Читы», «с Камчатки»; предлог парный к предлогу места.
        """
        if case == "loc":
            return f"{_in_or_vo(self.preposition, self.pre)} {self.pre}"
        if case == "dir":
            return f"{_in_or_vo(self.preposition, self.acc)} {self.acc}"
        if case == "from":
            return f"{_PREPOSITIONS[self.preposition]} {self.gen}"
        if case not in _CASES:
            raise ValueError(
                "Для топонима доступны падежи единственного числа "
                f"({', '.join(_CASES)}), 'loc' (где), 'dir' (куда) и 'from' (откуда); "
                f"получено '{case}'."
            )
        return getattr(self, case)


@lru_cache(maxsize=1)
def load_toponyms() -> tuple[Toponym, ...]:
    """Загрузить и проверить реестр топонимов."""
    payload = json.loads(_TOPONYMS_PATH.read_text(encoding="utf-8"))
    entries = payload.get("toponyms")
    if not isinstance(entries, list) or not entries:
        raise ToponymRegistryError("toponyms.json: нет списка 'toponyms'.")

    result: list[Toponym] = []
    seen: set[str] = set()
    for entry in entries:
        toponym_id = str(entry.get("toponym_id") or "")
        if not toponym_id:
            raise ToponymRegistryError("В реестре есть запись без 'toponym_id'.")
        if toponym_id in seen:
            raise ToponymRegistryError(f"Повторяющийся toponym_id: {toponym_id}.")
        seen.add(toponym_id)
        preposition = str(entry.get("preposition") or "")
        if preposition not in _PREPOSITIONS:
            raise ToponymRegistryError(
                f"{toponym_id}: предлог должен быть 'в' или 'на', получено {preposition!r}."
            )
        gender = str(entry.get("gender") or "")
        if gender not in _GENDERS:
            raise ToponymRegistryError(f"{toponym_id}: род должен быть одним из {sorted(_GENDERS)}.")
        cases = entry.get("cases")
        if not isinstance(cases, dict):
            raise ToponymRegistryError(f"{toponym_id}: поле 'cases' должно быть объектом.")
        missing = [case for case in _CASES if not str(cases.get(case, "")).strip()]
        if missing:
            raise ToponymRegistryError(f"{toponym_id}: не заполнены падежи: {', '.join(missing)}.")
        result.append(Toponym(
            toponym_id=toponym_id,
            preposition=preposition,
            gender=gender,
            region=str(entry.get("region") or "россия"),
            kind=str(entry.get("kind") or "город"),
            utc_offset=int(entry.get("utc_offset", 0)),
            **{case: str(cases[case]) for case in _CASES},
        ))
    return tuple(result)


def hours_between(west: Toponym, east: Toponym) -> int:
    """На сколько часов время во втором городе опережает первый.

    Считается по данным, а не выдумывается шаблоном: иначе задача утверждает,
    что в Москве на пять часов больше, чем в Хабаровске.
    """
    return east.utc_offset - west.utc_offset


def toponyms_in_region(
    region: str | list[str] | None = None, kind: str | list[str] | None = None
) -> tuple[Toponym, ...]:
    """Топонимы выбранных групп и видов; без аргументов — все.

    Группа отделяет земные города от планет: поезд не должен ехать на Татуин,
    а звездолёт — прилетать в Воронеж.
    """
    chosen = load_toponyms()
    for value, field in ((region, "region"), (kind, "kind")):
        if value is None:
            continue
        allowed = {value} if isinstance(value, str) else set(value)
        chosen = tuple(item for item in chosen if getattr(item, field) in allowed)
        if not chosen:
            raise ToponymRegistryError(f"Нет топонимов с {field} из {sorted(allowed)}.")
    return chosen
