"""Генератор задач о делимости, кратных, остатках и простых числах."""
from __future__ import annotations
import json, math, random, re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.russian.agreement import count_with_word_ru

ROOT=Path(__file__).resolve().parents[2]
SOURCES=[ROOT/'docs'/'07a_delimost_bez_imen_i_personazhey_deduplicated.md',ROOT/'docs'/'07b_delimost_s_imenami_i_personazhami_deduplicated.md']
PATH=ROOT/'data'/'templates'/'problem_sets'/'divisibility_multiples_remainders_primes'/'templates.json'
RE=re.compile(r'^\s*(\d+)\.')
class DivisibilityTemplateError(ValueError): pass
@dataclass(frozen=True)
class GeneratedDivisibilityProblem:
 module:str; template_id:str; source_problem_numbers:list[int]; problem_text:str; answer:Any; answer_text:str; parameters:dict[str,Any]; seed:int|None=None; universe:str|None=None; characters:list[str]|None=None
def source_divisibility_problem_numbers()->set[int]: return {int(m.group(1)) for p in SOURCES for l in p.read_text(encoding='utf8').splitlines() if (m:=RE.match(l))}
@lru_cache(maxsize=2)
def _load(s:str,m:int)->dict[str,Any]: del m; return json.loads(Path(s).read_text(encoding='utf8'))
def load_divisibility_templates(path:Path=PATH)->list[dict[str,Any]]:
 p=Path(path).resolve(); t=_load(str(p),p.stat().st_mtime_ns)['templates']; validate_divisibility_catalog(t); return list(t)
def validate_divisibility_catalog(t:list[dict[str,Any]])->None:
 nums=[n for x in t for n in x['source_problem_numbers']]
 if len({x['id'] for x in t})!=len(t) or set(nums)!=source_divisibility_problem_numbers() or len(nums)!=len(set(nums)): raise DivisibilityTemplateError('Нарушен учёт исходных задач.')
def divisibility_template_metadata()->dict[str,Any]:
 t=load_divisibility_templates(); active=[x for x in t if x['active']]
 return {'modules':[{'module_id':'divisibility_multiples_remainders_primes','title':'Divisibility, Multiples, Remainders and Prime Numbers','display_name':'Делимость, кратные, остатки и простые числа','template_count':len(active),'covered_source_problem_numbers':len(source_divisibility_problem_numbers())}],'templates':[{'template_id':x['id'],'title':x['title'],'display_name':x['title'],'module_name':'Делимость, кратные, остатки и простые числа','source_problem_numbers':x['source_problem_numbers']} for x in active],'stats':{'total_modules':1,'total_templates':len(active),'covered_source_problem_numbers':len(source_divisibility_problem_numbers())}}
def _template(id:str)->dict[str,Any]:
 for x in load_divisibility_templates():
  if x['id']==id:return x
 raise DivisibilityTemplateError(f'Неизвестный шаблон: {id}')
def _problem(t,text,answer,answer_text,p,seed,u=None,c=None):
 if '{' in text: raise DivisibilityTemplateError('В тексте остались плейсхолдеры.')
 return GeneratedDivisibilityProblem('divisibility_multiples_remainders_primes',t['id'],t['source_problem_numbers'],text,answer,answer_text,p,seed,u,c)
def _count(l,r,d,open_=False): return ((r-1)//d-l//d) if open_ else r//d-(l-1)//d
def _chars(rng,n):
 u=rng.choice(sorted(load_approved_characters())); cs=rng.sample(load_approved_characters()[u],n); return u,cs
def _past(ch,m,f): return f if ch.gender=='feminine' else m
def _pronoun(ch): return 'она' if ch.gender=='feminine' else 'он'
def _sentence_name(ch): return ch.name[:1].upper()+ch.name[1:]
def _open(t,r,s):
 d=r.randint(2,20); l=r.randint(50,2000); u=l+r.randint(30,2000); a=_count(l,u,d,True); return _problem(t,f'Сколько существует кратных {d} чисел, больших {l}, но меньших {u}?',a,f'Подходящих чисел: {a}.',{'lower_bound':l,'upper_bound':u,'divisor':d,'interval_type':'open'},s)
def _inclusive(t,r,s):
 d=r.randint(2,30); l=r.randint(1,1000); u=l+r.randint(50,3000); a=_count(l,u,d); return _problem(t,f'Сколько чисел от {l} до {u} делятся на {d}?',a,f'Подходящих чисел: {a}.',{'lower_bound':l,'upper_bound':u,'divisor':d,'interval_type':'inclusive'},s)
def _even(t,r,s):
 d=r.randint(3,30); l=r.randint(1,1000); u=l+r.randint(50,3000); q=math.lcm(2,d); a=_count(l,u,q); return _problem(t,f'Сколько чётных чисел в промежутке от {l} до {u} делятся на {d}?',a,f'Подходящих чисел: {a}.',{'lower_bound':l,'upper_bound':u,'divisor':d,'combined_divisor':q},s)
def _composite(t,r,s):
 f1,f2=r.choice([(3,4),(3,8),(4,9),(5,8),(8,9),(9,10)]); d=math.lcm(f1,f2); q=r.randint(100000,999999); rem=0 if r.choice([True,False]) else r.randint(1,d-1); n=d*q+rem; checks={str(f1):n%f1==0,str(f2):n%f2==0}; a={'divisible':n%d==0,'quotient':n//d if not rem else None,'remainder':n%d,'factor_checks':checks}; txt=f'Делится ли число {n} на {d}? Решите эту задачу: а) с помощью признака делимости на {f1}; б) с помощью признака делимости на {f2}.'; ans=f"Число {'делится' if a['divisible'] else 'не делится'} на {d}; проверки: {f1} — {'да' if checks[str(f1)] else 'нет'}, {f2} — {'да' if checks[str(f2)] else 'нет'}."; return _problem(t,txt,a,ans,{'dividend':n,'divisor':d,'factor_1':f1,'factor_2':f2},s)
def _digitsets(t,r,s):
 k=r.randint(3,6); sets=[set('02468'),set('13579'),set('0369')]; vals=[sum(x!='0' for x in z)*len(z)**(k-1) for z in sets]; word={3:'трёхзначных',4:'четырёхзначных',5:'пятизначных',6:'шестизначных'}[k]; a={'а':vals[0],'б':vals[1],'в':vals[2]}; return _problem(t,f'Сколько существует {word} чисел, у которых все цифры: а) чётные; б) нечётные; в) делятся на 3?',a,f"а) {a['а']}; б) {a['б']}; в) {a['в']}.",{'digit_count':k},s)
def _contains(t,r,s):
 d=r.randint(2,9); l=r.randint(100,1000); u=l+r.randint(100,2500); a={'divisible_count':_count(l,u,d),'contains_digit_count':sum(str(d) in str(x) for x in range(l,u+1))}; return _problem(t,f'Сколько чисел из промежутка от {l} до {u} включительно делится на {d}? А сколько содержат цифру {d}?',a,f"Делятся на {d}: {a['divisible_count']}; содержат цифру: {a['contains_digit_count']}.",{'lower_bound':l,'upper_bound':u,'target_digit':d},s)
def _honey(t,r,s,hyp):
 u,cs=_chars(r,4 if hyp else 3); rec,g1,g2,*rest=cs; ratio=r.randint(2,5); b=r.randint(2,10); diff=b*(ratio-1); cap=r.choice([50,100,150]); mass=cap*ratio*b; third=b+r.randint(1,8); total=ratio*b+b+(third if hyp else 0); text=f'На день рождения {_sentence_name(rec)} {_past(rec,"получил","получила")} мёд. {_sentence_name(g1)} {_past(g1,"дал","дала")} {count_with_word_ru(mass,("грамм","грамма","граммов"))} мёда, а {_sentence_name(g2)} — в {count_with_word_ru(ratio,("раз","раза","раз"))} меньше. Весь мёд был в одинаковых банках; {_sentence_name(g1)} {_past(g1,"дал","дала")} на {count_with_word_ru(diff,("банку","банки","банок"))} больше, чем {_sentence_name(g2)}.'; 
 if hyp: text+=f' Сколько банок мёда получил бы {_sentence_name(rec)}, если бы {_sentence_name(rest[0])} {_past(rest[0],"принёс","принесла")} на {count_with_word_ru(third-b,("банку","банки","банок"))} больше, чем {_sentence_name(g2)}?'
 else: text+=f' Сколько банок мёда {_past(rec,"получил","получила")} {_sentence_name(rec)}?'
 return _problem(t,text,total,f'Всего получено {count_with_word_ru(total,("банка","банки","банок"))} мёда.',{'ratio':ratio,'jar_difference':diff,'jar_capacity_grams':cap,'total_mass_grams':mass},s,u,[x.name for x in cs])
def _candy(t,r,s):
 u,cs=_chars(r,2); a,b=cs; diff=r.randint(2,20); n=diff-1; text=f'{_sentence_name(a)} {_past(a,"угощал","угощала")} одноклассников конфетами. После раздачи у {_pronoun(a)} осталось на {count_with_word_ru(diff,("конфету","конфеты","конфет"))} больше, чем {_past(b,"получил","получила")} {_sentence_name(b)}. Затем {_sentence_name(a)} {_past(a,"дал","дала")} каждому ещё по одной конфете, и у всех детей стало одинаковое количество конфет. Сколько у {_pronoun(a)} одноклассников?'; return _problem(t,text,n,f'Одноклассников: {n}.',{'difference':diff,'classmate_count':n},s,u,[a.name,b.name])
def _proof4(t,r,s): return _problem(t,'Докажите, что из любых семи различных цифр можно составить число, которое делится на четыре.',{'answer_type':'proof','proof_strategy':'last_two_digits'},'Среди семи цифр найдутся две, образующие число, кратное 4; поставьте их последними.',{},s)
def _proofp(t,r,s): return _problem(t,'Докажите, что натуральное число В с инвариантностью делимости при перестановке цифр может быть равно только 1, 3 или 9.',{'answer_type':'proof','classification':[1,3,9]},'Перестановка сохраняет сумму цифр, поэтому подходят 1, 3 и 9; другие делители нарушаются перестановкой цифр.',{},s)
STR={'open_multiples':_open,'inclusive_divisible':_inclusive,'even_divisible':_even,'composite_test':_composite,'digit_sets':_digitsets,'divisible_and_contains':_contains,'honey_hypothetical':lambda t,r,s:_honey(t,r,s,True),'honey_total':lambda t,r,s:_honey(t,r,s,False),'candy_classmates':_candy,'proof_four':_proof4,'proof_permutation':_proofp}
def generate_divisibility_problem(id:str,*,seed:int|None=None,rng:random.Random|None=None):
 t=_template(id)
 if not t['active']: raise DivisibilityTemplateError(f"Шаблон {id} неактивен: {t['exclusion_reason']}")
 return STR[t['generation_strategy']](t,rng or random.Random(seed if seed is not None else datetime.now().timestamp()),seed)
def generate_divisibility_problem_from_module(module_id:str,*,rng:random.Random):
 if module_id!='divisibility_multiples_remainders_primes': raise DivisibilityTemplateError('Неизвестный модуль.')
 t=rng.choice([x for x in load_divisibility_templates() if x['active']]); return generate_divisibility_problem(t['id'],rng=rng)
