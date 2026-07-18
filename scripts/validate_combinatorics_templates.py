"""Проверка всех шаблонов модуля 11 на фиксированных seed."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from problemgen.generation.combinatorics_templates import generate_combinatorics_problem,load_combinatorics_templates
def main():
    ts=load_combinatorics_templates()
    for t in ts:
        for seed in range(300):
            a=generate_combinatorics_problem(t["id"],seed=seed); b=generate_combinatorics_problem(t["id"],seed=seed)
            assert a==b and isinstance(a.answer,int) and "{" not in a.problem_text
    print(f"OK: {len(ts)} шаблона, {len(ts)*300} deterministic instances")
if __name__=="__main__":main()
