from __future__ import annotations
import itertools, random, unittest
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.combinatorics_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class CombinatoricsTests(unittest.TestCase):
    def test_source_accounting(self):
        m=load_source_accounting(); rs=m["records"]; nums=[r["source_problem_number"] for r in rs]
        self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(nums)),(10,1,9)); self.assertEqual(len(nums),len(set(nums))); self.assertEqual(set(nums),source_problem_numbers()); self.assertTrue(all(r["status"]=="active_template" or len(r["reason"])>20 for r in rs))
    def test_catalog(self):
        ts=load_combinatorics_templates(); self.assertEqual(len(ts),4); self.assertEqual(len({t["id"] for t in ts}),4)
        self.assertTrue(all(t["answer_type"]=="integer" and t["generation_strategy"] in STRATEGIES and "{number_" not in t["render_template"] for t in ts))
    def test_math_edges(self):
        self.assertEqual(count_odd_open(239,2339),1049); self.assertEqual(ordered_nonempty(1),1); self.assertEqual(ordered_nonempty(6),1956)
        self.assertEqual(max_distinct_type_sets([18,26,35,41],3),39)
        with self.assertRaises(CombinatoricsTemplateError): count_odd_open(5,5)
        with self.assertRaises(CombinatoricsTemplateError): ordered_nonempty(11)
        with self.assertRaises(CombinatoricsTemplateError): max_distinct_type_sets([1],2)
        with self.assertRaises(CombinatoricsTemplateError): solve_cyclic_distribution(4,1,2,5,2)
    def test_twenty_seeds_and_invariants(self):
        for t in load_combinatorics_templates():
            for seed in range(20):
                g=generate_combinatorics_problem(t["id"],seed=seed); self.assertEqual(g,generate_combinatorics_problem(t["id"],seed=seed)); self.assertIsInstance(g.answer,int); self.assertNotIn("{",g.problem_text)
                p=g.parameters; s=t["generation_strategy"]
                if s=="odd_open_interval": self.assertEqual(g.answer,sum(n%2 for n in range(p["lower_bound"]+1,p["upper_bound"])))
                elif s=="ordered_nonempty_selections": self.assertEqual(g.answer,sum(len(list(itertools.permutations(range(p["object_count"]),k))) for k in range(1,p["object_count"]+1)))
                elif s=="cyclic_alternating_distribution": self.assertEqual(g.answer,solve_cyclic_distribution(p["child_count"],p["first_amount"],p["second_amount"],p["total_gifts"],p["target_amount"]))
                else:self.assertEqual(g.answer,max_distinct_type_sets(p["resource_counts"],p["types_per_set"]))
    def test_characters(self):
        approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
        for t in [x for x in load_combinatorics_templates() if x["uses_characters"]]:
            for seed in range(20):
                g=generate_combinatorics_problem(t["id"],seed=seed); self.assertIn(g.universe,approved); self.assertEqual(len(g.characters),len(set(g.characters))); self.assertTrue(set(g.characters)<=approved[g.universe]); self.assertTrue(all(c in g.problem_text for c in g.characters))
    def test_excluded_never_selected_and_site_stack(self):
        excluded={1205}
        for seed in range(100): self.assertTrue(excluded.isdisjoint(generate_combinatorics_problem_from_module(MODULE_ID,rng=random.Random(seed)).source_problem_numbers))
        modules=["factors_products_and_factorials","ratios_fractions_proportions_and_percentages",MODULE_ID,"arithmetic",MODULE_ID]; a=generate_combined_worksheet_by_modules(modules,seed=239); self.assertEqual(a,generate_combined_worksheet_by_modules(modules,seed=239))
if __name__=="__main__":unittest.main()
