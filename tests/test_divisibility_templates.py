from __future__ import annotations
import math, random, unittest
from problemgen.generation.divisibility_templates import *
from problemgen.generation.divisibility_templates import _count
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.web.worksheet_site import generate_combined_worksheet_by_modules
class DivisibilityTests(unittest.TestCase):
 def test_source_accounting(self):
  ts=load_divisibility_templates(); ns=[n for t in ts for n in t['source_problem_numbers']]
  self.assertEqual(set(ns),source_divisibility_problem_numbers()); self.assertEqual(len(ns),len(set(ns))); self.assertEqual(len(ts),12)
 def test_interval_edges(self):
  for l,u,d in [(10,20,5),(11,20,5),(10,19,5),(11,19,5)]: self.assertEqual(_count(l,u,d,True),sum(x%d==0 for x in range(l+1,u)))
  self.assertEqual(_count(5,898,4),sum(x%4==0 for x in range(5,899)))
 def test_300_instances(self):
  for t in load_divisibility_templates():
   if not t['active']: continue
   for seed in range(300):
    p=generate_divisibility_problem(t['id'],seed=seed); self.assertNotIn('{',p.problem_text)
    if t['generation_strategy']=='composite_test':
     q=p.parameters; self.assertEqual(q['divisor'],math.lcm(q['factor_1'],q['factor_2'])); self.assertEqual(p.answer['remainder'],q['dividend']%q['divisor'])
    if t['generation_strategy'] in {'open_multiples','inclusive_divisible','even_divisible'}:
     q=p.parameters; d=q.get('combined_divisor',q['divisor']); self.assertEqual(p.answer,sum(x%d==0 for x in range(q['lower_bound']+(1 if q.get('interval_type')=='open' else 0),q['upper_bound']+(0 if q.get('interval_type')=='open' else 1))))
    if p.characters:
     approved=load_approved_characters(); self.assertIn(p.universe,approved); self.assertEqual(len(p.characters),t['required_character_count']); self.assertEqual(len(set(p.characters)),len(p.characters)); self.assertTrue(set(p.characters)<= {x.name for x in approved[p.universe]})
 def test_module_and_inactive(self):
  with self.assertRaises(DivisibilityTemplateError): generate_divisibility_problem('div_007_ambiguous_construction')
  a=generate_divisibility_problem_from_module('divisibility_multiples_remainders_primes',rng=random.Random(4)); self.assertNotEqual(a.template_id,'div_007_ambiguous_construction')
  modules=['arithmetic','equations','systems_of_equations','sequences_progressions_and_sums','divisibility_multiples_remainders_primes']; self.assertEqual(generate_combined_worksheet_by_modules(modules,seed=7),generate_combined_worksheet_by_modules(modules,seed=7))
 def test_named_templates_have_gendered_verbs_and_single_universe(self):
  approved=load_approved_characters()
  for template_id in ('div_010_honey_hypothetical','div_011_candy_classmates','div_012_honey_total'):
   for seed in range(100):
    p=generate_divisibility_problem(template_id,seed=seed)
    self.assertIn(p.universe,approved)
    self.assertTrue(set(p.characters)<= {character.name for character in approved[p.universe]})
    self.assertEqual(len(p.characters),len(set(p.characters)))
    self.assertNotIn(' у Панда ',p.problem_text)
