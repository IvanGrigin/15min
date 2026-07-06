from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NounForms:
    one: str
    few: str
    many: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.one, self.few, self.many)
