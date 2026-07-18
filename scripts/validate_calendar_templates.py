from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from problemgen.generation.calendar_templates import *
for t in load_calendar_templates():
 for seed in range(200):
  a=generate_calendar_problem(t["id"],seed=seed);assert a==generate_calendar_problem(t["id"],seed=seed) and isinstance(a.answer,int)
print(f"OK: {len(load_calendar_templates())} шаблонов, {len(load_calendar_templates())*200} deterministic instances")
