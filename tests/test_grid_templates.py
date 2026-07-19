import unittest
from problemgen.generation.grid_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class GridTests(unittest.TestCase):
 def test_all(self):
  m=load_source_accounting();self.assertEqual(len(m['records']),31);self.assertEqual({x['source_problem_number'] for x in m['records']},source_problem_numbers())
  for t in load_grid_templates():
   for s in range(20):
    g=generate_grid_problem(t['id'],seed=s);self.assertEqual(g,generate_grid_problem(t['id'],seed=s));self.assertIsInstance(g.answer,int)
  a=generate_combined_worksheet_by_modules([MODULE_ID]*5,seed=4,task_count=5);self.assertEqual(a,generate_combined_worksheet_by_modules([MODULE_ID]*5,seed=4,task_count=5))
if __name__=='__main__':unittest.main()
