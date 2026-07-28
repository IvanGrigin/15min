"""Шкалы признаков: согласованные определения для трёх групп в задаче.

Чтобы добавить шкалу или ступень, отредактируйте
    data/language/trait_scales.json
Python-код менять не нужно.

Зачем отдельный слой. Задача «очередь разделилась на три группы» не обязана
делить по возрасту. Смурфики бывают красные, синие и зелёные, роботы —
маленькие, средние и большие, а гости — весёлые, спокойные и сердитые.
Если написать «молодые» и «старые» текстом шаблона, во всех ста шестнадцати
вселенных получится одна и та же очередь.

Определение согласуется с тем словом, к которому относится, поэтому шкала
знает род и число: «красный житель», но «красная фея» и «красные жители».
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_SCALES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "language" / "trait_scales.json"
)
_GENDERS = ("m", "f", "n")
# Слоты шкалы: ступень плюс число. Единственное согласуется по роду слова.
_STEP_NAMES = ("one", "two", "three")


class TraitScaleError(ValueError):
    """Шкалу признаков нельзя загрузить или она внутренне противоречива."""


@dataclass(frozen=True)
class TraitScale:
    """Шкала из трёх ступеней, уже согласованная с определяемым словом.

    Подставляется в те же слоты, что персонаж и существительное, поэтому
    отдельной механики в шаблонизаторе не понадобилось: ``{trait:one_pl}`` —
    первая ступень во множественном числе, ``{trait:two}`` — вторая
    в единственном, в роде того слова, с которым шкала связана.
    """

    scale_id: str
    title: str
    gender: str
    steps: tuple[dict[str, str], ...]

    def get_case(self, spec: str) -> str:
        """Форма ступени: ``one``/``two``/``three`` и те же с суффиксом ``_pl``."""
        name, _, number = spec.partition("_")
        if name not in _STEP_NAMES or number not in ("", "pl"):
            raise ValueError(
                "Для шкалы признаков доступны слоты "
                f"{', '.join(_STEP_NAMES)} и они же с '_pl'; получено '{spec}'."
            )
        step = self.steps[_STEP_NAMES.index(name)]
        return step["pl"] if number == "pl" else step[self.gender]


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    payload = json.loads(_SCALES_PATH.read_text(encoding="utf-8"))
    scales = payload.get("scales")
    if not isinstance(scales, dict) or not scales:
        raise TraitScaleError("trait_scales.json: нет словаря 'scales'.")
    for scale_id, entry in scales.items():
        steps = entry.get("steps")
        if not isinstance(steps, list) or len(steps) != len(_STEP_NAMES):
            raise TraitScaleError(
                f"{scale_id}: нужно ровно {len(_STEP_NAMES)} ступени, задано {len(steps or [])}."
            )
        for position, step in enumerate(steps, start=1):
            missing = [key for key in _GENDERS + ("pl",) if not str(step.get(key, "")).strip()]
            if missing:
                raise TraitScaleError(
                    f"{scale_id}, ступень {position}: не заполнены формы: {', '.join(missing)}."
                )
    return scales


def scale_ids() -> tuple[str, ...]:
    """Ключи всех описанных шкал, отсортированные."""
    return tuple(sorted(_load()))


def scale_for(scale_id: str, gender: str) -> TraitScale:
    """Шкала, согласованная с родом определяемого слова."""
    scales = _load()
    if scale_id not in scales:
        raise TraitScaleError(
            f"Шкалы {scale_id!r} нет в data/language/trait_scales.json. "
            f"Доступны: {', '.join(scale_ids())}."
        )
    if gender not in _GENDERS:
        raise TraitScaleError(f"Род должен быть одним из {_GENDERS}, получено {gender!r}.")
    entry = scales[scale_id]
    return TraitScale(
        scale_id=scale_id,
        title=str(entry.get("title") or scale_id),
        gender=gender,
        steps=tuple(dict(step) for step in entry["steps"]),
    )
