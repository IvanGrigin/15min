import random,unittest
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.process_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class ProcessTests(unittest.TestCase):
 def test_accounting_schema(self):
  m=load_source_accounting();rs=m["records"];ns=[r["source_problem_number"] for r in rs];self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(ns)),(10,2,8));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertEqual(len(load_process_templates()),4)
 def test_independent_solvers(self):
  self.assertEqual(collatz_steps(70,10),9);self.assertEqual(overlay_value(6,3,5,6),2);self.assertEqual(triangular(4),10)
  with self.assertRaises(ProcessTemplateError):collatz_steps(0,10)
  with self.assertRaises(ProcessTemplateError):overlay_value(6,0,5,6)
 def test_many_seeds_and_invariants(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  for t in load_process_templates():
   for seed in range(20):
    g=generate_process_problem(t["id"],seed=seed);self.assertEqual(g,generate_process_problem(t["id"],seed=seed));self.assertNotIn("{",g.problem_text);p=g.parameters;s=t["generation_strategy"]
    if s=="collatz_threshold":self.assertEqual(g.answer,collatz_steps(p["start_value"],p["threshold"]))
    elif s=="three_to_one_mergers":self.assertEqual(g.answer,p["start_states"]-2*p["years"])
    elif s=="cyclic_overlay":self.assertEqual(g.answer,overlay_value(p["sector_count"],p["under_sector"],p["over_sector"],p["query_sector"]))
    else:self.assertEqual(g.answer,triangular(p["term_index"]+2))
    if t["uses_characters"]:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe])
 def test_module_and_site_stack(self):
  for seed in range(100):self.assertIn(generate_process_problem_from_module(MODULE_ID,rng=random.Random(seed)).template_id,{t["id"] for t in load_process_templates()})
  ms=["factors_products_and_factorials","ratios_fractions_proportions_and_percentages","combinatorics_and_counting_variants","pigeonhole_and_guaranteed_selection","parity_invariants_strategies_and_moves",MODULE_ID];a=generate_combined_worksheet_by_modules(ms,seed=239);self.assertEqual(a,generate_combined_worksheet_by_modules(ms,seed=239))
if __name__=="__main__":unittest.main()
