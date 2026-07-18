import random,unittest
from problemgen.generation.time_zone_templates import *
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class TimeZoneTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();rs=m["records"];ns=[r["source_problem_number"] for r in rs];self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(ns)),(64,21,43));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertTrue(all(r["status"]=="active_template" or len(r["reason"])>30 for r in rs))
 def test_math_and_seeds(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  self.assertEqual(absolute_to_local(local_to_absolute(90,120)+60,0),30)
  for t in load_time_zone_templates():
   for seed in range(20):
    g=generate_time_zone_problem(t["id"],seed=seed);self.assertEqual(g,generate_time_zone_problem(t["id"],seed=seed));self.assertIsInstance(g.answer,int);self.assertNotIn("{",g.problem_text)
    if t["uses_characters"]:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe])
 def test_site(self):
  for seed in range(50):self.assertIn(generate_time_zone_problem_from_module(MODULE_ID,rng=random.Random(seed)).template_id,{t["id"] for t in load_time_zone_templates()})
  a=generate_combined_worksheet_by_modules(["calendar_and_weekdays","clocks_dials_and_electronic_displays",MODULE_ID],seed=17);self.assertEqual(a,generate_combined_worksheet_by_modules(["calendar_and_weekdays","clocks_dials_and_electronic_displays",MODULE_ID],seed=17))
if __name__=="__main__":unittest.main()
