from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from problemgen.generation.grid_templates import *
for t in load_grid_templates():
 for s in range(300):assert generate_grid_problem(t['id'],seed=s)==generate_grid_problem(t['id'],seed=s)
print('OK')
