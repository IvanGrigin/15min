import unittest
from unittest.mock import patch
from problemgen.generation.comparison_templates import Character
from problemgen.generation.counting_objects_templates import *
class CountingObjectsTests(unittest.TestCase):
 def test_accounting_and_seeds(self):
  m=load_source_accounting();n=[x['source_problem_number'] for x in m['records']];self.assertEqual((m['original_numbered_entries'],m['removed_duplicates'],len(n)),(34,5,29));self.assertEqual(len(n),len(set(n)));self.assertEqual(set(n),source_problem_numbers())
  for t in load_counting_templates():
   for s in range(20):
    g=generate_counting_problem(t['id'],seed=s);self.assertEqual(g,generate_counting_problem(t['id'],seed=s));self.assertIsInstance(g.answer,int)
 def test_feminine_character_uses_gender_neutral_wording(self):
  characters={'Тестовая вселенная':[Character('Тестовая вселенная','Нюша','feminine')]}
  with patch('problemgen.generation.counting_objects_templates.load_approved_characters',return_value=characters):
   for template_id in ('count_002_wheels','count_003_objects'):
    text=generate_counting_problem(template_id,seed=1).problem_text
    self.assertIn('Нюша',text);self.assertNotIn('насчитал',text);self.assertNotIn('собрал',text)
if __name__=='__main__':unittest.main()
