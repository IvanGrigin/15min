import unittest
from problemgen.generation.line_templates import *
class T(unittest.TestCase):
 def test_all(self):
  self.assertEqual(len(load_source_accounting()['records']),15)
  for t in load_line_templates():
   for s in range(20):self.assertEqual(generate_line_problem(t['id'],seed=s),generate_line_problem(t['id'],seed=s))
if __name__=='__main__':unittest.main()
