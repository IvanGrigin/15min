import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from problemgen.generation.alphabetic_order_templates import *
def main():
 n=0
 for t in load_alphabetic_order_templates():
  for s in range(50):
   g=generate_alphabetic_order_problem(t['id'],seed=s)
   assert g.answer and set(g.answer)<=set(g.parameters['alphabet_letters']);n+=1
 print(f'OK: {n} instances')
if __name__=='__main__':main()
