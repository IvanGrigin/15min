from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DifficultyLevel:
    code: str
    label: str
    description: str


DIFFICULTY_LEVELS: Dict[str, DifficultyLevel] = {
    "easy": DifficultyLevel(
        code="easy",
        label="Легкий",
        description="Небольшие числа и короткие рассуждения. Обычно решение укладывается в один-два простых шага.",
    ),
    "medium": DifficultyLevel(
        code="medium",
        label="Средний",
        description="Числа крупнее, а промежуточные вычисления чаще становятся двузначными или трехзначными.",
    ),
    "hard": DifficultyLevel(
        code="hard",
        label="Сложный",
        description="Большие числа и более нагруженные промежуточные вычисления. Ошибиться в счете здесь заметно проще.",
    ),
}


def get_difficulty_level(code: str) -> DifficultyLevel:
    try:
        return DIFFICULTY_LEVELS[code]
    except KeyError as error:
        available = ", ".join(sorted(DIFFICULTY_LEVELS))
        raise ValueError(f"Неизвестная сложность '{code}'. Доступно: {available}") from error
