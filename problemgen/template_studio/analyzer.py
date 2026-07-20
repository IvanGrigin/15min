"""Детерминированный, намеренно консервативный анализатор черновиков."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_NUMBER_RE = re.compile(r"(?<![\w,.-])-?\d+(?:[.,]\d+)?")
_NAME_RE = re.compile(r"\b[А-ЯЁ][а-яё]{2,}\b")
_OPERATIONS = (("+", "сложение"), ("-", "вычитание"), ("×", "умножение"), ("*", "умножение"), ("÷", "деление"), ("/", "деление"), ("=", "равенство"))
_UNITS = ("мм", "см", "м", "км", "г", "кг", "т", "л", "мл", "руб.", "руб", "коп.", "с", "мин", "ч", "%")
_NON_NAMES = {"Найдите", "Сколько", "Все", "Какое", "Какая", "Какой", "Через", "Ответ", "Решите"}


@dataclass(frozen=True)
class AnalysisResult:
    """Нормализованный результат, пригодный для сохранения в draft JSON."""

    values: dict[str, Any]


class TemplateAnalyzer:
    """Набор прозрачных эвристик; это не интерпретатор произвольной задачи."""

    def analyze(self, original_text: str) -> AnalysisResult:
        normalized = " ".join(original_text.strip().split())
        numbers = [match.replace(",", ".") for match in _NUMBER_RE.findall(normalized)]
        names = [name for name in _NAME_RE.findall(normalized) if name not in _NON_NAMES]
        units = [unit for unit in _UNITS if re.search(rf"(?<!\w){re.escape(unit)}(?!\w)", normalized, re.IGNORECASE)]
        operations = [label for token, label in _OPERATIONS if token in normalized]
        expressions = re.findall(r"(?:\d+\s*[+\-×*/]\s*)+\d+", normalized)
        warnings: list[str] = []
        unsupported: list[str] = []
        candidate = normalized
        parameters: dict[str, dict[str, Any]] = {}
        derived: dict[str, str] = {}
        answer_expression = ""
        answer_type = "integer"
        strategy = "manual"

        sequence = self._sequence_candidate(normalized, numbers)
        if sequence is not None:
            candidate, parameters, derived, answer_expression = sequence
            strategy = "formula"
        else:
            for index, number in enumerate(numbers, start=1):
                if "." in number:
                    parameters[f"number_{index}"] = {"type": "decimal", "minimum": 0, "maximum": 1000}
                else:
                    value = int(number)
                    lower = max(-10000, value - max(10, abs(value)))
                    parameters[f"number_{index}"] = {"type": "integer", "minimum": lower, "maximum": min(10000, value + max(10, abs(value)))}
                candidate = candidate.replace(number.replace(".", ","), "{" + f"number_{index}" + "}", 1)
                candidate = candidate.replace(number, "{" + f"number_{index}" + "}", 1)
            if not parameters:
                warnings.append("Числовые параметры не обнаружены: заполните шаблон и схему вручную.")
            warnings.append("Формула ответа не выведена автоматически: заполните её перед валидацией.")
            unsupported.append("Автоматический анализ поддерживает только очевидные числовые и последовательностные формы.")

        if any(word.lower() in normalized.lower() for word in ("докажите", "объясните", "постройте", "нарисуйте")):
            unsupported.append("Обнаружена конструктивная или доказательная формулировка; нужен ручной solver strategy.")
        return AnalysisResult({
            "original_text": original_text,
            "normalized_text": normalized,
            "candidate_template_text": candidate,
            "detected_numbers": numbers,
            "detected_names": names,
            "detected_units": units,
            "detected_operations": list(dict.fromkeys(operations)),
            "detected_expressions": expressions,
            "detected_answer_type": answer_type,
            "candidate_parameters": parameters,
            "candidate_constraints": {},
            "candidate_derived_values": derived,
            "candidate_solver_strategy": strategy,
            "candidate_answer_expression": answer_expression,
            "warnings": warnings,
            "unsupported_features": unsupported,
        })

    @staticmethod
    def _sequence_candidate(text: str, numbers: list[str]) -> tuple[str, dict[str, dict[str, Any]], dict[str, str], str] | None:
        if "…" not in text or len(numbers) < 4:
            return None
        values = [int(value) for value in numbers if value.lstrip("-").isdigit()]
        if len(values) < 4 or values[1] - values[0] != values[2] - values[1] or values[-1] - values[-2] != values[1] - values[0]:
            return None
        difference = values[1] - values[0]
        if difference == 0:
            return None
        candidate = re.sub(
            r"-?\d+\s*\+\s*-?\d+\s*\+\s*-?\d+\s*\+\s*…\s*\+\s*-?\d+\s*\+\s*-?\d+",
            "{first_term} + {second_term} + {third_term} + … + {penultimate_term} + {last_term}",
            text,
            count=1,
        )
        parameters = {
            "first_term": {"type": "integer", "minimum": max(-100, values[0] - 10), "maximum": min(100, values[0] + 10)},
            "difference": {"type": "integer", "minimum": max(-20, difference - 3), "maximum": min(20, difference + 3)},
            "term_count": {"type": "positive_integer", "minimum": 3, "maximum": 30},
        }
        derived = {
            "second_term": "first_term + difference",
            "third_term": "first_term + 2 * difference",
            "penultimate_term": "first_term + difference * (term_count - 2)",
            "last_term": "first_term + difference * (term_count - 1)",
        }
        return candidate, parameters, derived, "term_count * (first_term + last_term) / 2"
