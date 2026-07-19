from __future__ import annotations
import random
import unittest
from math import isqrt

from problemgen.generation.plane_geometry_templates import MODULE_ID, STRATEGIES, generate_plane_geometry_problem, load_plane_geometry_templates, load_source_accounting, plane_geometry_template_metadata, source_problem_numbers
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules

class PlaneGeometryTemplatesTests(unittest.TestCase):
 def test_accounting_and_schema(self):
  manifest=load_source_accounting(); records=manifest['records']; numbers=[r['source_problem_number'] for r in records]; templates=load_plane_geometry_templates()
  self.assertEqual((manifest['original_numbered_entries'],manifest['removed_duplicates'],len(numbers)),(102,27,75));self.assertEqual(len(numbers),len(set(numbers)));self.assertEqual(set(numbers),source_problem_numbers());self.assertEqual(len(templates),18);self.assertEqual({t['generation_strategy'] for t in templates},set(STRATEGIES))
  ids={t['id'] for t in templates}
  for record in records:
   if record['status']=='active_template':self.assertIn(record['template_id'],ids)
   else:self.assertTrue(record.get('reason'))
 def test_all_strategies_are_deterministic_and_exact(self):
  for template in load_plane_geometry_templates():
   for seed in range(20):
    problem=generate_plane_geometry_problem(template['id'],seed=seed);self.assertEqual(problem,generate_plane_geometry_problem(template['id'],seed=seed));self.assertIsInstance(problem.answer,int);self.assertNotIn('{',problem.problem_text);self._verify(problem.template_id,problem.parameters,problem.answer)
 def test_site_module_and_mixed_worksheet(self):
  self.assertEqual(plane_geometry_template_metadata()['stats']['total_templates'],18)
  modules=[MODULE_ID,'arithmetic',MODULE_ID,'equations',MODULE_ID]; a=generate_combined_worksheet_by_modules(modules,seed=24,task_count=5);b=generate_combined_worksheet_by_modules(modules,seed=24,task_count=5)
  self.assertEqual(a,b);self.assertEqual([p['module_id'] for p in a['selected_templates']][::2],[MODULE_ID]*3);self.assertTrue(all('Ответ:' not in p['rendered_problem'] for p in a['selected_templates']))
 def test_unknown_template_rejected(self):
  with self.assertRaisesRegex(ValueError,'Неизвестный шаблон'):generate_plane_geometry_problem('missing',rng=random.Random(1))
 def _verify(self,tid,v,a):
  if tid=='geometry_001_cut_perimeters': expected=v['perimeter']-(v['vertical_cut_perimeter_sum']-v['perimeter'])//2
  elif tid=='geometry_002_square_area_from_perimeter': expected=(v['perimeter_cm']//4)**2
  elif tid=='geometry_003_subdivision_perimeter': expected=4*v['grid_side']*isqrt(v['small_square_area'])
  elif tid=='geometry_004_subdivision_area': expected=(v['grid_side']*(v['small_square_perimeter']//4))**2
  elif tid=='geometry_005_rectangle_area_perimeter': expected=2*(v['known_side']+v['area']//v['known_side']);self.assertEqual(v['area']%v['known_side'],0)
  elif tid=='geometry_006_grid_partitions': expected=2*v['width_cells']*v['height_cells']-v['width_cells']-v['height_cells']
  elif tid=='geometry_007_square_factor_minimum': expected=min(x+v['number']//x for x in range(1,v['number']+1) if v['number']%x==0 and (isqrt(x)**2==x or isqrt(v['number']//x)**2==v['number']//x))
  elif tid=='geometry_008_square_growth': expected=(v['area_increase']-1)//2
  elif tid=='geometry_009_long_rectangle_cuts':
   w,h=v['width'],v['height'];long=lambda x,y:max(x,y)>2*min(x,y);expected=sum(long(x,h)and long(w-x,h) for x in range(1,w))+sum(long(w,y)and long(w,h-y) for y in range(1,h))
  elif tid=='geometry_010_material_density': expected=v['sheet_weight_g']//(v['sheet_width_cm']*v['sheet_height_cm'])*v['target_area_cm2'];self.assertEqual(v['sheet_weight_g']%(v['sheet_width_cm']*v['sheet_height_cm']),0)
  elif tid=='geometry_011_overlapping_carpets': d=isqrt(v['opposite_overlap']);self.assertEqual(d*d,v['opposite_overlap']);expected=3*(v['adjacent_overlap']//d)-d;self.assertEqual(v['adjacent_overlap']%d,0)
  elif tid=='geometry_012_grid_holes': expected=2*v['width_cells']*v['height_cells']-v['width_cells']-v['height_cells']-v['hole_count']*(2*v['hole_side']**2+2*v['hole_side'])
  elif tid=='geometry_013_square_equation': expected=isqrt(v['result']*v['divisor']//v['multiplier']);self.assertEqual(v['result']*v['divisor']%v['multiplier'],0)
  elif tid=='geometry_014_equal_perimeter_square': expected=(v['first_side']+v['second_side'])//2
  elif tid=='geometry_015_rectangle_area_units': expected=v['area_dm2']//100//v['length_m'];self.assertEqual(v['area_dm2']%(100*v['length_m']),0)
  elif tid=='geometry_016_square_unit_conversion': expected=v['square_feet']*v['inches_per_foot']**2
  elif tid=='geometry_017_square_frame': expected=(v['inner_perimeter']//4+2*v['frame_width'])**2
  else: expected=3*v['small_square_side']**2
  self.assertEqual(a,expected)
if __name__=='__main__':unittest.main()
