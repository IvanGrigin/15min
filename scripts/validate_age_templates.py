from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from problemgen.generation.age_templates import *
for t in load_age_templates():
 for s in range(200):
  g=generate_age_problem(t['id'],seed=s);assert g==generate_age_problem(t['id'],seed=s) and isinstance(g.answer,int)
print(f"OK: {len(load_age_templates())} шаблонов, {len(load_age_templates())*200} deterministic instances")
