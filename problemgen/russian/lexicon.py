"""Минимальные лексические структуры: формы слова для согласования с числом."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NounForms:
    """Три формы существительного для счёта: 1, 2–4, 5+."""

    one: str
    few: str
    many: str

    def as_tuple(self) -> tuple[str, str, str]:
        """Вернуть формы кортежем в порядке 1, 2–4, 5+."""
        return (self.one, self.few, self.many)
