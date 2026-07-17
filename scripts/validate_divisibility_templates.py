from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
from problemgen.generation.divisibility_templates import load_divisibility_templates,generate_divisibility_problem
for t in load_divisibility_templates():
 if t['active']:
  for seed in range(300): generate_divisibility_problem(t['id'],seed=seed)
print('OK: 11 активных шаблонов, 300 прогонов каждого.')
