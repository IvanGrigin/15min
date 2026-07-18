from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from problemgen.generation.counting_objects_templates import *
for t in load_counting_templates():
 for s in range(200):
  g=generate_counting_problem(t['id'],seed=s);assert g==generate_counting_problem(t['id'],seed=s) and isinstance(g.answer,int)
print(f"OK: {len(load_counting_templates())} шаблонов, {len(load_counting_templates())*200} deterministic instances")
