from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from problemgen.generation.pigeonhole_templates import *
def main():
 ts=load_pigeonhole_templates()
 for t in ts:
  for seed in range(300):
   a=generate_pigeonhole_problem(t["id"],seed=seed);assert a==generate_pigeonhole_problem(t["id"],seed=seed) and isinstance(a.answer,int)
 print(f"OK: {len(ts)} шаблона, {len(ts)*300} deterministic instances")
if __name__=="__main__":main()
