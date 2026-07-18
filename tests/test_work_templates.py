import random,unittest
from problemgen.generation.work_templates import *
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class WorkTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();r=m['records'];n=[x['source_problem_number'] for x in r];self.assertEqual((m['original_numbered_entries'],m['removed_duplicates'],len(n)),(23,7,16));self.assertEqual(len(n),len(set(n)));self.assertEqual(set(n),source_problem_numbers())
 def test_many_seeds(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  for t in load_work_templates():
   for seed in range(20):
    g=generate_work_problem(t['id'],seed=seed);self.assertEqual(g,generate_work_problem(t['id'],seed=seed));self.assertIsInstance(g.answer,int);self.assertNotIn('{',g.problem_text)
    if t['uses_characters']:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe])
 def test_site(self):
  a=generate_combined_worksheet_by_modules(['motion_speed_and_distance',MODULE_ID],seed=19);self.assertEqual(a,generate_combined_worksheet_by_modules(['motion_speed_and_distance',MODULE_ID],seed=19))
if __name__=='__main__':unittest.main()
