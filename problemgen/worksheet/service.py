from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from problemgen.domains.arithmetic import templates as arithmetic_templates
from problemgen.io import render_worksheet


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "worksheets" / "worksheet_5_tasks.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "generated"


@dataclass(frozen=True)
class WorksheetProblem:
    id: str
    text: str
    answer: str
    difficulty: int
    type: str
    template_name: str
    domain: str = "arithmetic"

    def to_student_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "problem_text": self.text,
            "difficulty": self.difficulty,
            "type": self.type,
            "template_name": self.template_name,
            "domain": self.domain,
        }

    def to_answer_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "answer": self.answer,
            "difficulty": self.difficulty,
            "type": self.type,
            "template_name": self.template_name,
            "domain": self.domain,
        }


@dataclass(frozen=True)
class WorksheetArtifact:
    pdf_path: str
    student_json_path: str
    answers_json_path: str
    created_at: str
    difficulties: list[int]
    problems: list[WorksheetProblem]


def validate_difficulties(difficulties: Any) -> list[int]:
    if not isinstance(difficulties, list):
        raise ValueError("Поле difficulties должно быть списком из 5 чисел.")
    if len(difficulties) != 5:
        raise ValueError("Нужно передать ровно 5 уровней сложности.")

    normalized: list[int] = []
    for value in difficulties:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Каждая сложность должна быть целым числом от 1 до 10.")
        if not 1 <= value <= 10:
            raise ValueError("Каждая сложность должна быть в диапазоне от 1 до 10.")
        normalized.append(value)
    return normalized


def map_numeric_difficulty_to_level(score: int) -> str:
    if 1 <= score <= 3:
        return "easy"
    if 4 <= score <= 7:
        return "medium"
    if 8 <= score <= 10:
        return "hard"
    raise ValueError("Сложность должна быть в диапазоне от 1 до 10.")


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_problem_set(difficulties: list[int], rng: random.Random) -> list[WorksheetProblem]:
    factory_names = list(arithmetic_templates.TEMPLATE_FACTORIES)
    selected_templates = rng.sample(factory_names, k=5)
    problems: list[WorksheetProblem] = []

    for index, (difficulty, template_name) in enumerate(zip(difficulties, selected_templates, strict=True), start=1):
        level = map_numeric_difficulty_to_level(difficulty)
        problem_record = arithmetic_templates.TEMPLATE_FACTORIES[template_name](
            rng=rng,
            index=index,
            difficulty_level=level,
        )
        problems.append(
            WorksheetProblem(
                id=problem_record.code,
                text=problem_record.problem_text,
                answer=problem_record.answer_text,
                difficulty=difficulty,
                type="arithmetic",
                template_name=template_name,
            )
        )

    return problems


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def generate_worksheet_artifacts(
    difficulties: list[int],
    *,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int | None = None,
    max_attempts: int = 20,
) -> WorksheetArtifact:
    normalized_difficulties = validate_difficulties(difficulties)
    output_root = Path(output_dir)
    template = Path(template_path)
    timestamp = _timestamp()
    base_rng = random.Random(seed if seed is not None else int(datetime.now().strftime("%Y%m%d%H%M%S")))

    last_error: Exception | None = None
    for _attempt in range(1, max_attempts + 1):
        rng = random.Random(base_rng.randint(1, 10**9))
        problems = _build_problem_set(normalized_difficulties, rng)
        student_json_path = output_root / f"worksheet_problems_{timestamp}.json"
        answers_json_path = output_root / f"worksheet_answers_{timestamp}.json"
        pdf_path = output_root / f"worksheet_{timestamp}.pdf"

        student_payload = {
            "id": f"worksheet_student_{timestamp}",
            "template_id": "worksheet_5_tasks",
            "header": {
                "date": datetime.now().strftime("%d.%m.%Y"),
            },
            "difficulties": normalized_difficulties,
            "problems": [problem.to_student_dict() for problem in problems],
        }
        answers_payload = {
            "id": f"worksheet_answers_{timestamp}",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "difficulties": normalized_difficulties,
            "problems": [problem.to_answer_dict() for problem in problems],
        }

        _write_json(student_json_path, student_payload)
        _write_json(answers_json_path, answers_payload)

        try:
            render_worksheet(
                template_path=template,
                problems_path=student_json_path,
                output_path=pdf_path,
            )
            return WorksheetArtifact(
                pdf_path=str(pdf_path),
                student_json_path=str(student_json_path),
                answers_json_path=str(answers_json_path),
                created_at=datetime.now().isoformat(timespec="seconds"),
                difficulties=normalized_difficulties,
                problems=problems,
            )
        except Exception as error:
            last_error = error

    if last_error is None:
        raise ValueError("Не удалось сгенерировать лист задач.")
    raise last_error
