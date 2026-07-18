from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from problemgen.generation.parity_templates import *
for seed in range(500):
 a=generate_parity_problem("parity_001_adjacent_digit_classification_sum",seed=seed);assert a==generate_parity_problem(a.template_id,seed=seed)
print("OK: 1 шаблон, 500 deterministic instances")
