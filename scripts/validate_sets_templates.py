"""Запуск расширенной deterministic-проверки модуля 23."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from problemgen.generation.sets_templates import generate_sets_problem, load_sets_templates

for template in load_sets_templates():
    for seed in range(300):
        generated = generate_sets_problem(template["id"], seed=seed)
        assert generated == generate_sets_problem(template["id"], seed=seed)
        assert isinstance(generated.answer, int) and "{" not in generated.problem_text
print(f"OK: {len(load_sets_templates())} шаблонов, {len(load_sets_templates()) * 300} deterministic instances")
