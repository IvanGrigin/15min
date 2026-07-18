import random,unittest
from problemgen.generation.motion_templates import *
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class MotionTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();rs=m['records'];ns=[r['source_problem_number'] for r in rs];self.assertEqual((m['original_numbered_entries'],m['removed_duplicates'],len(ns)),(78,18,60));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertTrue(all(r['status']=='active_template' or len(r['reason'])>30 for r in rs))
 def test_seeds_and_math(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  self.assertEqual(pursuit_minutes(30,8,5),10)
  for t in load_motion_templates():
   for seed in range(20):
    g=generate_motion_problem(t['id'],seed=seed);self.assertEqual(g,generate_motion_problem(t['id'],seed=seed));self.assertIsInstance(g.answer,int);self.assertNotIn('{',g.problem_text)
    if t['uses_characters']:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe]);self.assertEqual(len(g.characters),len(set(g.characters)))
 def test_site(self):
  ids={t['id'] for t in load_motion_templates()}
  for seed in range(40):self.assertIn(generate_motion_problem_from_module(MODULE_ID,rng=random.Random(seed)).template_id,ids)
  a=generate_combined_worksheet_by_modules(['time_zones_and_travel_schedules',MODULE_ID],seed=18);self.assertEqual(a,generate_combined_worksheet_by_modules(['time_zones_and_travel_schedules',MODULE_ID],seed=18))
if __name__=='__main__':unittest.main()
