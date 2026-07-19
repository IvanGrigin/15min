from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from problemgen.generation.quantity_templates import *
for t in load_quantity_templates():
 for s in range(300):assert generate_quantity_problem(t['id'],seed=s)==generate_quantity_problem(t['id'],seed=s)
print('OK')
