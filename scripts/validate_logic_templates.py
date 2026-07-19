"""Проверяет 300 детерминированных экземпляров каждого активного шаблона модуля 30."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from problemgen.generation.logic_templates import generate_logic_problem, load_logic_templates


def main() -> None:
    checked = 0
    for template in load_logic_templates():
        for seed in range(300):
            generated = generate_logic_problem(template["id"], seed=seed)
            if not isinstance(generated.answer, int) or "{" in generated.problem_text:
                raise SystemExit(f"Невалидный экземпляр {template['id']}, seed={seed}")
            checked += 1
    print(f"OK: {checked} exact-integer instances")


if __name__ == "__main__":
    main()
