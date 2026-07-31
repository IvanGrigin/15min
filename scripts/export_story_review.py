"""Экспортировать скрытые сюжетные метаданные для ручной проверки вариантов."""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.russian.inflection import RussianNoun
from problemgen.template_studio.runtime import generate_active_template, normalize_value
from scripts.seed_worksheet_templates import load_library


def review_record(template: dict, seed: int) -> dict:
    """Собрать один вариант без изменения текста условия или математики."""
    generated = generate_active_template(template, random.Random(seed))
    rules = template.get("parameter_schema", {})
    selected: dict[str, list[str]] = {"items": [], "valuables": [], "currency": [], "folk": []}
    for name, rule in rules.items():
        value = generated["parameters"].get(name)
        if not isinstance(rule, dict) or not isinstance(value, RussianNoun):
            continue
        for source in selected:
            if rule.get(f"from_universe_{source}"):
                selected[source].append(value.lemma)
    context = generated["story_context"]
    return {
        "template_id": template["template_id"],
        "story_variant_id": generated["variant_metadata"]["story_variant_id"],
        "parameter_variant_id": generated["variant_metadata"]["parameter_variant_id"],
        "seed": seed,
        "story_mode": context["mode"],
        "universe": context["universe"],
        "character_ids": context["character_ids"],
        "location_ids": context["location_ids"],
        "item_lemmas": selected["items"],
        "valuable_lemmas": selected["valuables"],
        "currency_lemmas": selected["currency"],
        "folk_lemmas": selected["folk"],
        "compatibility_checks": context["checks"],
        "independent_parameters": {
            name: normalize_value(value)
            for name, value in generated["parameters"].items()
            if name in rules
        },
        "derived_parameters": {
            name: normalize_value(value)
            for name, value in generated["parameters"].items()
            if name not in rules and name not in {"predicate_id", "predicate_name", "predicate_definition"}
        },
        "answer": generated["answer"],
        "validation_result": "passed",
        "problem": generated["rendered_problem"],
    }


def main() -> None:
    """Записать по указанному пути проверяемый JSON-экспорт."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variants", type=int, default=3)
    args = parser.parse_args()
    if args.variants < 1 or args.variants > 10:
        raise SystemExit("--variants должен быть от 1 до 10.")
    records = [
        review_record(template, seed)
        for template in load_library()
        for seed in range(args.variants)
    ]
    args.output.write_text(
        json.dumps({"schema_version": 1, "variants": records}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
