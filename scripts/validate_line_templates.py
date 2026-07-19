from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from problemgen.generation.line_templates import *
for t in load_line_templates():
 for s in range(300):assert generate_line_problem(t['id'],seed=s)==generate_line_problem(t['id'],seed=s)
print('OK')
