from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from problemgen.generation.work_templates import *
for t in load_work_templates():
 for seed in range(200):
  g=generate_work_problem(t['id'],seed=seed);assert g==generate_work_problem(t['id'],seed=seed) and isinstance(g.answer,int)
print(f"OK: {len(load_work_templates())} шаблонов, {len(load_work_templates())*200} deterministic instances")
