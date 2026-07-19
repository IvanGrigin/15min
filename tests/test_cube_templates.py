import unittest
from problemgen.generation.cube_templates import *
class CubeTests(unittest.TestCase):
 def test_catalog_and_seeds(self):
  self.assertEqual(len(load_source_accounting()['records']),44)
  self.assertEqual({x['source_problem_number']for x in load_source_accounting()['records']},source_problem_numbers())
  for t in load_cube_templates():
   for s in range(20):self.assertEqual(generate_cube_problem(t['id'],seed=s),generate_cube_problem(t['id'],seed=s))
if __name__=='__main__':unittest.main()
