import unittest
from problemgen.generation.quantity_templates import *
class T(unittest.TestCase):
 def test_all(self):
  self.assertEqual(len(load_quantity_templates()),4)
  for t in load_quantity_templates():
   for s in range(20):self.assertEqual(generate_quantity_problem(t['id'],seed=s),generate_quantity_problem(t['id'],seed=s))
if __name__=='__main__':unittest.main()
