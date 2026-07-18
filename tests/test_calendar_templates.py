import math,random,unittest
from datetime import date,timedelta
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.generation.calendar_templates import *
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class CalendarTests(unittest.TestCase):
 def test_accounting(self):
  m=load_source_accounting();rs=m["records"];ns=[r["source_problem_number"] for r in rs];self.assertEqual((m["original_numbered_entries"],m["removed_duplicates"],len(ns)),(72,17,55));self.assertEqual(len(ns),len(set(ns)));self.assertEqual(set(ns),source_problem_numbers());self.assertTrue(all(r["status"]=="active_template" or len(r["reason"])>20 for r in rs))
 def test_calendar_helpers(self):
  self.assertEqual(weekday_code(date(2026,4,2)),4);self.assertEqual(nth_weekday(2024,9,0,1),date(2024,9,2));self.assertEqual(max_digit_sum_number(19,25),19);self.assertGreater(palindromic_dates(2000,2099),0)
  with self.assertRaises(CalendarTemplateError):nth_weekday(2024,2,0,5)
 def test_many_seeds(self):
  approved={u:{c.name for c in cs} for u,cs in load_approved_characters().items()}
  for t in load_calendar_templates():
   self.assertEqual(t["answer_type"],"integer")
   for seed in range(20):
    g=generate_calendar_problem(t["id"],seed=seed);self.assertEqual(g,generate_calendar_problem(t["id"],seed=seed));p=g.parameters;s=t["generation_strategy"]
    if s=="weekday_code_offset":self.assertEqual(g.answer,(date.fromisoformat(p["start_date"])+timedelta(days=p["offset_days"])).isoweekday())
    elif s=="conditional_nth_weekday":self.assertEqual(g.answer,nth_weekday(p["year"]+int(p["condition_month"]==12),p["target_month"],p["target_weekday_code"]-1,p["ordinal"]).day)
    elif s=="max_digit_sum_range":self.assertEqual(g.answer,max_digit_sum_number(p["lower_bound"],p["upper_bound"]))
    elif s=="circular_tram_interval":self.assertEqual(g.answer,p["route_period"]//p["new_trams"])
    elif s=="date_offset_day":self.assertEqual(g.answer,(date.fromisoformat(p["start_date"])+(timedelta(days=p["offset_days"]) if p["offset_days"] is not None else timedelta(hours=p["offset_hours"]))).day)
    elif s=="vacation_days":self.assertEqual(g.answer,(date.fromisoformat(p["end_date"])-date.fromisoformat(p["start_date"])).days+1)
    elif s=="palindromic_dates":self.assertEqual(g.answer,palindromic_dates(p["start_year"],p["end_year"]))
    elif s=="lcm_schedule":self.assertEqual(g.answer,math.lcm(*p["periods"]))
    elif s=="two_weekday_schedule":
     observed=[date(p["year"],p["month"],day) for day in p["observed_days"]];cutoff=date(p["year"],p["month"],p["cutoff_day"]);self.assertEqual(g.answer,max(d.day for d in (observed[0]+timedelta(days=i) for i in range((cutoff-observed[0]).days)) if d.weekday() in {x.weekday() for x in observed}))
    elif s=="school_breaks":self.assertEqual(g.answer,(p["total_until_leave"]-p["after_last"]-p["lesson_count"]*p["lesson_minutes"]-p["big_break"])//(p["lesson_count"]-2))
    if t["uses_characters"]:self.assertIn(g.universe,approved);self.assertTrue(set(g.characters)<=approved[g.universe])
 def test_module_site(self):
  for seed in range(100):self.assertIn(generate_calendar_problem_from_module(MODULE_ID,rng=random.Random(seed)).template_id,{t["id"] for t in load_calendar_templates()})
  ms=["factors_products_and_factorials","ratios_fractions_proportions_and_percentages","combinatorics_and_counting_variants","pigeonhole_and_guaranteed_selection","parity_invariants_strategies_and_moves","number_processes_and_repeated_operations",MODULE_ID];a=generate_combined_worksheet_by_modules(ms,seed=239);self.assertEqual(a,generate_combined_worksheet_by_modules(ms,seed=239))
if __name__=="__main__":unittest.main()
