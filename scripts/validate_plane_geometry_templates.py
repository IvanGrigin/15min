"""Расширенная deterministic-проверка модуля 24."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from problemgen.generation.plane_geometry_templates import generate_plane_geometry_problem,load_plane_geometry_templates
for template in load_plane_geometry_templates():
 for seed in range(300):
  generated=generate_plane_geometry_problem(template['id'],seed=seed);assert generated==generate_plane_geometry_problem(template['id'],seed=seed) and isinstance(generated.answer,int) and '{' not in generated.problem_text
print(f"OK: {len(load_plane_geometry_templates())} шаблонов, {len(load_plane_geometry_templates())*300} deterministic instances")
