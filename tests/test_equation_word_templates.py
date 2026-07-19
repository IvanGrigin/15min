import random, unittest
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.equation_word_templates import *
class T(unittest.TestCase):
 def test_accounting(self):
  rs=load_source_accounting()['records']; ns=[r['source_problem_number'] for r in rs]
  self.assertEqual(len(ns),45);self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers())
  active={n:t['id'] for t in load_equation_word_templates() for n in t['source_problem_numbers']}
  for r in rs:
   if r['status']=='active_template':self.assertEqual(active[r['source_problem_number']],r['template_id'])
   else:self.assertTrue(r['reason'])
 def test_seeded(self):
  for t in load_equation_word_templates():
   for s in range(20):
    g=generate_equation_word_problem(t['id'],seed=s);self.assertEqual(g,generate_equation_word_problem(t['id'],seed=s));self.assertIsInstance(g.answer,int);self.assertNotIn('{',g.problem_text)
 def test_characters_and_selector(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  for s in range(20):
   g=generate_equation_word_problem('equation_word_007_multiple_difference',seed=s);self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe]);self.assertEqual(len(g.characters),len(set(g.characters)))
  ids={t['id'] for t in load_equation_word_templates()}
  for s in range(100):self.assertIn(generate_equation_word_problem_from_module(MODULE_ID,rng=random.Random(s)).template_id,ids)
if __name__=='__main__':unittest.main()
