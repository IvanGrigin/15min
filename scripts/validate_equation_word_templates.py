import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from problemgen.generation.equation_word_templates import generate_equation_word_problem,load_equation_word_templates
def main():
 n=0
 for t in load_equation_word_templates():
  for s in range(300):
   g=generate_equation_word_problem(t['id'],seed=s)
   if not isinstance(g.answer,int) or '{' in g.problem_text:raise SystemExit(f"bad {t['id']} {s}")
   n+=1
 print(f"OK: {n} exact-integer instances")
if __name__=='__main__':main()
