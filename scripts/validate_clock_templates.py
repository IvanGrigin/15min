from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from problemgen.generation.clock_templates import generate_clock_problem, load_clock_templates

for template in load_clock_templates():
    for seed in range(200):
        generated = generate_clock_problem(template["id"], seed=seed)
        assert generated == generate_clock_problem(template["id"], seed=seed) and isinstance(generated.answer, int)
print(f"OK: {len(load_clock_templates())} шаблонов, {len(load_clock_templates()) * 200} deterministic instances")
