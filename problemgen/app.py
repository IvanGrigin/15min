from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from problemgen.core.models import ProblemRecord
from problemgen.domains.base import MathDomain
from problemgen.domains.combinatorics import CombinatoricsDomain
from problemgen.domains.counting import CountingDomain
from problemgen.domains.segments import SegmentsDomain
from problemgen.russian import attach_language_report


def build_domain_catalog() -> Dict[str, MathDomain]:
    domains: Dict[str, MathDomain] = {}
    for domain in (SegmentsDomain(), CountingDomain(), CombinatoricsDomain()):
        domains[domain.code] = domain
    return domains


def get_domain(domain_code: str) -> MathDomain:
    catalog = build_domain_catalog()
    try:
        return catalog[domain_code]
    except KeyError as error:
        available = ", ".join(sorted(catalog))
        raise ValueError(f"Неизвестный домен '{domain_code}'. Доступно: {available}") from error


def default_output_path(domain_code: str) -> str:
    return str(Path("output") / f"{domain_code}.json")


def generate_problem_bundle(
    *,
    domain_code: str,
    count: int,
    template_name: str,
    difficulty_level: str,
    story_theme: str,
    seed_mode: str,
    seed: Optional[int],
    output_path: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    domain = get_domain(domain_code)
    bundle = domain.generate_bundle(
        count=count,
        template_name=template_name,
        difficulty_level=difficulty_level,
        story_theme=story_theme,
        seed_mode=seed_mode,
        seed=seed,
        output_path=output_path,
        options=options,
    )
    normalized_problems = []
    for raw_problem in bundle.get("problems", []):
        problem = ProblemRecord(
            code=raw_problem.get("code", ""),
            category=raw_problem.get("category", domain_code),
            domain=raw_problem.get("domain", domain_code),
            template_name=raw_problem.get("template_name", ""),
            problem_text=raw_problem.get("problem_text", ""),
            answer_text=raw_problem.get("answer_text", ""),
            answer_values=list(raw_problem.get("answer_values", [])),
            difficulty=dict(raw_problem.get("difficulty", {})),
            story=dict(raw_problem.get("story", {})),
            metadata=dict(raw_problem.get("metadata", {})),
            mode=raw_problem.get("mode", ""),
            variables=dict(raw_problem.get("variables", {})),
            intermediate_values=dict(raw_problem.get("intermediate_values", {})),
            relations=list(raw_problem.get("relations", [])),
        )
        if "language_issues" not in problem.metadata:
            problem = attach_language_report(problem)
        normalized_problems.append(problem.to_dict())
    bundle["problems"] = normalized_problems
    bundle.setdefault("metadata", {})
    bundle["metadata"]["language_summary"] = {
        "issues_found": sum(
            len(problem.get("metadata", {}).get("language_issues", []))
            for problem in normalized_problems
        ),
    }
    output_path_value = bundle.get("output_path")
    if output_path_value:
        output_path_obj = Path(output_path_value)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with output_path_obj.open("w", encoding="utf-8") as file:
            json.dump(bundle, file, ensure_ascii=False, indent=2)
    return bundle
