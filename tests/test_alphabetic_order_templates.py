import math,unittest
from problemgen.generation.alphabetic_order_templates import *
class T(unittest.TestCase):
 def test_names_and_math(self):
  self.assertEqual({n for n,g in eligible_names()},EXPECTED);self.assertEqual(GEN['Артём'],'Артёма');self.assertEqual(GEN['Дарья'],'Дарьи')
  self.assertEqual(unrank_perm('ИВАН',18),unrank_perm('ИВАН',rank_perm('ИВАН',unrank_perm('ИВАН',18))))
  self.assertEqual(unrank_repeat('ИВАН',4,256),'НННН');self.assertEqual(rank_repeat('ИВАН','НННН'),256)
  self.assertEqual((plural_words(24),plural_words(120),plural_words(256),plural_words(3125)),('слова','слов','слов','слов'))
 def test_catalog_and_seeds(self):
  self.assertEqual(len(load_alphabetic_order_templates()),5)
  for t in load_alphabetic_order_templates():
   for s in range(50):
    g=generate_alphabetic_order_problem(t['id'],seed=s);self.assertEqual(g,generate_alphabetic_order_problem(t['id'],seed=s));self.assertEqual(set(g.parameters['alphabet_letters']),set(g.parameters['name_nom'].upper()));self.assertEqual(len(g.parameters['alphabet_letters']),len(set(g.parameters['alphabet_letters'])));self.assertNotIn('{',g.problem_text)
    if t['generation_strategy']=='repetition_last':self.assertEqual(g.parameters['total_word_count'],g.parameters['alphabet_size']**g.parameters['alphabet_size'])
    else:self.assertEqual(g.parameters['total_word_count'],math.factorial(g.parameters['alphabet_size']))
if __name__=='__main__':unittest.main()
