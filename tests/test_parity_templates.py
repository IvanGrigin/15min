import random,unittest
from problemgen.generation.parity_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class ParityTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();rs=m["records"];ns=[r["source_problem_number"] for r in rs];self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(ns)),(31,8,23));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertTrue(all(r["status"]=="active_template" or len(r["reason"])>20 for r in rs))
 def test_predicate(self):
  self.assertFalse(has_equal_adjacent_parity(101010));self.assertTrue(has_equal_adjacent_parity(104060));self.assertFalse(has_equal_adjacent_parity(1212));self.assertTrue(has_equal_adjacent_parity(135));
  with self.assertRaises(ParityTemplateError):has_equal_adjacent_parity(7)
 def test_many_seeds(self):
  t=load_parity_templates()[0];self.assertEqual(t["answer_type"],"integer");self.assertNotIn("{number_",t["render_template"])
  for seed in range(100):
   g=generate_parity_problem(t["id"],seed=seed);p=g.parameters;pred=has_equal_adjacent_parity if p["parity_mode"]=="equal_exists" else lambda n:not has_equal_adjacent_parity(n);self.assertEqual(g.answer,sum(n for n in p["candidate_numbers"] if pred(n)));self.assertEqual(g,generate_parity_problem(t["id"],seed=seed))
 def test_site_stack(self):
  ms=["factors_products_and_factorials","ratios_fractions_proportions_and_percentages","combinatorics_and_counting_variants","pigeonhole_and_guaranteed_selection",MODULE_ID];a=generate_combined_worksheet_by_modules(ms,seed=239);self.assertEqual(a,generate_combined_worksheet_by_modules(ms,seed=239))
if __name__=="__main__":unittest.main()
