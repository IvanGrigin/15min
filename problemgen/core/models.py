from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TemplateDescriptor:
    code: str
    label: str
    description: str


@dataclass
class ProblemRecord:
    code: str
    category: str
    domain: str
    template_name: str
    problem_text: str
    answer_text: str
    answer_values: List[int]
    difficulty: Dict[str, Any]
    story: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    mode: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    intermediate_values: Dict[str, Any] = field(default_factory=dict)
    relations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationBundle:
    count: int
    count_text: str
    domain: str
    domain_label: str
    template_name: str
    difficulty_level: str
    difficulty_label: str
    difficulty_description: str
    requested_story_theme: str
    requested_story_theme_label: str
    seed_mode: str
    seed_value: Optional[int]
    generated_at: str
    output_path: str
    problems: List[ProblemRecord]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["problems"] = [problem.to_dict() for problem in self.problems]
        return payload
