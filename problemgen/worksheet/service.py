from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from problemgen.catalog.problem_templates import find_templates, list_modules
from problemgen.generation.template_generator import generate_problem_from_template
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
    domain: str
    module: str
    template_id: str
    variables: dict[str, Any]

    def to_student_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "text": self.text, "problem_text": self.text,
            "difficulty": self.difficulty, "type": self.type, "template_name": self.template_name,
            "template_id": self.template_id, "domain": self.domain, "module": self.module,
        }

    def to_answer_dict(self) -> dict[str, Any]:
        return {**self.to_student_dict(), "answer": self.answer, "variables": self.variables}


@dataclass(frozen=True)
class WorksheetArtifact:
    pdf_path: str
    student_json_path: str
    answers_json_path: str
    created_at: str
    difficulties: list[int]
    items: list[dict[str, Any]]
    problems: list[WorksheetProblem]


def validate_difficulties(difficulties: Any) -> list[int]:
    if not isinstance(difficulties, list) or len(difficulties) != 5:
        raise ValueError("Поле difficulties должно быть списком из 5 чисел.")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10 for value in difficulties):
        raise ValueError("Каждая сложность должна быть целым числом от 1 до 10.")
    return list(difficulties)


def validate_items(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or len(items) != 5:
        raise ValueError("Поле items должно быть списком ровно из 5 задач.")
    available = {module["id"] for module in list_modules()}
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Каждая задача должна быть объектом с module и difficulty.")
        module, difficulty = item.get("module"), item.get("difficulty")
        if not isinstance(module, str) or module not in available:
            raise ValueError("У каждой задачи должна быть доступная тема module.")
        if isinstance(difficulty, bool) or not isinstance(difficulty, int) or not 1 <= difficulty <= 10:
            raise ValueError("Сложность каждой задачи должна быть целым числом от 1 до 10.")
        if not find_templates(module, difficulty):
            raise ValueError(f"Для темы '{module}' и сложности {difficulty} нет подходящего шаблона.")
        normalized.append({"module": module, "difficulty": difficulty})
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


def _build_problem_set(items: list[dict[str, Any]], rng: random.Random) -> list[WorksheetProblem]:
    problems: list[WorksheetProblem] = []
    for index, item in enumerate(items, start=1):
        generated = generate_problem_from_template(item["module"], item["difficulty"], rng=rng, index=index)
        problems.append(WorksheetProblem(
            id=generated.id, text=generated.problem_text, answer=str(generated.answer),
            difficulty=generated.difficulty, type=generated.topic, template_name=generated.template_id,
            domain=generated.domain, module=generated.module, template_id=generated.template_id,
            variables=generated.variables,
        ))
    return problems


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_worksheet_artifacts(
    difficulties: list[int] | None = None,
    *,
    items: list[dict[str, Any]] | None = None,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int | None = None,
    max_attempts: int = 20,
) -> WorksheetArtifact:
    if items is None:
        normalized_difficulties = validate_difficulties(difficulties)
        module_ids = [module["id"] for module in list_modules()]
        normalized_items = [
            {"module": module, "difficulty": difficulty}
            for module, difficulty in zip((module_ids * 5)[:5], normalized_difficulties, strict=True)
        ]
    else:
        normalized_items = validate_items(items)
        normalized_difficulties = [item["difficulty"] for item in normalized_items]

    output_root, template, timestamp = Path(output_dir), Path(template_path), _timestamp()
    base_rng = random.Random(seed if seed is not None else int(datetime.now().strftime("%Y%m%d%H%M%S")))
    last_error: Exception | None = None
    for _ in range(max_attempts):
        problems = _build_problem_set(normalized_items, random.Random(base_rng.randint(1, 10**9)))
        student_json_path = output_root / f"worksheet_problems_{timestamp}.json"
        answers_json_path = output_root / f"worksheet_answers_{timestamp}.json"
        pdf_path = output_root / f"worksheet_{timestamp}.pdf"
        student_payload = {
            "id": f"worksheet_student_{timestamp}", "template_id": "worksheet_5_tasks",
            "header": {"date": datetime.now().strftime("%d.%m.%Y")},
            "difficulties": normalized_difficulties, "items": normalized_items,
            "problems": [problem.to_student_dict() for problem in problems],
        }
        answers_payload = {
            "id": f"worksheet_answers_{timestamp}", "created_at": datetime.now().isoformat(timespec="seconds"),
            "difficulties": normalized_difficulties, "items": normalized_items,
            "problems": [problem.to_answer_dict() for problem in problems],
        }
        _write_json(student_json_path, student_payload)
        _write_json(answers_json_path, answers_payload)
        try:
            render_worksheet(template_path=template, problems_path=student_json_path, output_path=pdf_path)
            return WorksheetArtifact(
                pdf_path=str(pdf_path), student_json_path=str(student_json_path), answers_json_path=str(answers_json_path),
                created_at=datetime.now().isoformat(timespec="seconds"), difficulties=normalized_difficulties,
                items=normalized_items, problems=problems,
            )
        except Exception as error:
            last_error = error
    raise last_error or ValueError("Не удалось сгенерировать лист задач.")
