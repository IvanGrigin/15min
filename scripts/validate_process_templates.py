from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from problemgen.generation.process_templates import *
for t in load_process_templates():
 for seed in range(300):
  a=generate_process_problem(t["id"],seed=seed);assert a==generate_process_problem(t["id"],seed=seed) and isinstance(a.answer,int)
print(f"OK: {len(load_process_templates())} шаблона, {len(load_process_templates())*300} deterministic instances")
