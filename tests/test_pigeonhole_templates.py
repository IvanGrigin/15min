import random,unittest
from problemgen.generation.pigeonhole_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class PigeonholeTests(unittest.TestCase):
 def test_accounting_catalog(self):
  m=load_source_accounting();rs=m["records"];ns=[r["source_problem_number"] for r in rs];self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(ns)),(9,3,6));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertEqual(len(load_pigeonhole_templates()),3);self.assertTrue(all(r["status"]=="active_template" or len(r["reason"])>30 for r in rs))
 def test_solvers_edges(self):
  self.assertEqual(guarantee_target(14,2),16);self.assertEqual(inventory_total(15,14,25),26)
  with self.assertRaises(PigeonholeTemplateError):guarantee_target(-1,2)
  with self.assertRaises(PigeonholeTemplateError):inventory_total(15,14,20)
 def test_twenty_seeds_exact(self):
  for t in load_pigeonhole_templates():
   self.assertIn(t["generation_strategy"],STRATEGIES);self.assertEqual(t["answer_type"],"integer");self.assertNotIn("{number_",t["render_template"])
   for seed in range(20):
    g=generate_pigeonhole_problem(t["id"],seed=seed);self.assertEqual(g,generate_pigeonhole_problem(t["id"],seed=seed));p=g.parameters
    if t["generation_strategy"]=="three_category_guarantee":self.assertEqual(g.answer,p["pencil_count"]+1);self.assertLessEqual(p["pen_count"]-p["removed_pens"]+p["marker_count"],p["first_guarantee"]-1)
    elif t["generation_strategy"]=="inventory_reconstruction":self.assertEqual(g.answer,inventory_total(p["red_guarantee_draw"],p["blue_guarantee_draw"],p["no_white_draw"]))
    else:self.assertEqual(g.answer,guarantee_target(p["other_count"],p["required_target"]))
 def test_excluded_and_site_stack(self):
  for seed in range(100):self.assertNotIn(1150,generate_pigeonhole_problem_from_module(MODULE_ID,rng=random.Random(seed)).source_problem_numbers)
  ms=["factors_products_and_factorials","ratios_fractions_proportions_and_percentages","combinatorics_and_counting_variants",MODULE_ID,"arithmetic"];a=generate_combined_worksheet_by_modules(ms,seed=239);self.assertEqual(a,generate_combined_worksheet_by_modules(ms,seed=239))
if __name__=="__main__":unittest.main()
