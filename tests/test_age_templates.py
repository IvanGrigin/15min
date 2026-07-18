import unittest
from problemgen.generation.age_templates import *
class AgeTests(unittest.TestCase):
 def test_accounting_and_seeds(self):
  m=load_source_accounting();n=[x['source_problem_number'] for x in m['records']];self.assertEqual((m['original_numbered_entries'],m['removed_duplicates'],len(n)),(16,1,15));self.assertEqual(len(n),len(set(n)));self.assertEqual(set(n),source_problem_numbers())
  for t in load_age_templates():
   for s in range(20):
    g=generate_age_problem(t['id'],seed=s);self.assertEqual(g,generate_age_problem(t['id'],seed=s));self.assertIsInstance(g.answer,int)
if __name__=='__main__':unittest.main()
