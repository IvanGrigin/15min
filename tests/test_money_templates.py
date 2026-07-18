import random,unittest
from problemgen.generation.money_templates import *
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class MoneyTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();r=m['records'];n=[x['source_problem_number'] for x in r];self.assertEqual((m['original_numbered_entries'],m['removed_duplicates'],len(n)),(61,19,42));self.assertEqual(len(n),len(set(n)));self.assertEqual(set(n),source_problem_numbers())
 def test_seeds(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  for t in load_money_templates():
   for s in range(20):
    g=generate_money_problem(t['id'],seed=s);self.assertEqual(g,generate_money_problem(t['id'],seed=s));self.assertIsInstance(g.answer,int);self.assertNotIn('{',g.problem_text)
    if t['uses_characters']:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe])
 def test_site(self):
  a=generate_combined_worksheet_by_modules(['work_productivity_and_joint_actions',MODULE_ID],seed=20);self.assertEqual(a,generate_combined_worksheet_by_modules(['work_productivity_and_joint_actions',MODULE_ID],seed=20))
if __name__=='__main__':unittest.main()
