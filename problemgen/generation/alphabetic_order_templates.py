"""Модуль 29A: слова в скрытом алфавитном порядке."""
from __future__ import annotations
import itertools,json,math,random,re
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; MODULE_ID='alphabetic_order'; PATH=ROOT/'data/templates/problem_sets'/MODULE_ID/'templates.json'; MANIFEST=PATH.with_name('source_accounting.json'); NAMES=ROOT/'docs/module_29a_regular_human_names.md'; SOURCE=ROOT/'docs/29a_alphabetic_order_deduplicated.md'
EXPECTED={'Иван','Андрей','Артём','Борис','Виктор','Игорь','Николай','Олег','Павел','Роман','Валерия','Вера','Дарья','Ксения','Мария','Ольга','Полина','София','Юлия'}
GEN={'Иван':'Ивана','Андрей':'Андрея','Артём':'Артёма','Борис':'Бориса','Виктор':'Виктора','Игорь':'Игоря','Николай':'Николая','Олег':'Олега','Павел':'Павла','Роман':'Романа','Валерия':'Валерии','Вера':'Веры','Дарья':'Дарьи','Ксения':'Ксении','Мария':'Марии','Ольга':'Ольги','Полина':'Полины','София':'Софии','Юлия':'Юлии'}
class AlphabeticOrderError(ValueError):pass
@dataclass(frozen=True)
class G: module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:str;answer_text:str;parameters:dict;seed:int|None=None
def parse_names():
 gender=None; out=[]
 for line in NAMES.read_text(encoding='utf8').splitlines():
  if 'Мужские' in line:gender='male'
  elif 'Женские' in line:gender='female'
  elif line.startswith('- '):out.append((line[2:].strip(),gender))
 return out
def eligible_names():return [(n,g) for n,g in parse_names() if len(set(n.upper()))==len(n.upper())]
def plural_words(n):return 'слово' if n%10==1 and n%100!=11 else 'слова' if n%10 in (2,3,4) and n%100 not in (12,13,14) else 'слов'
def ordinal(n):return f'{n}-м'
def unrank_perm(order,rank):
 available=list(order); rank-=1; result=[]
 for k in range(len(order),0,-1):
  size=math.factorial(k-1); i,rank=divmod(rank,size);result.append(available.pop(i))
 return ''.join(result)
def rank_perm(order,word):
 available=list(order); result=0
 for k,ch in zip(range(len(order),0,-1),word):i=available.index(ch);result+=i*math.factorial(k-1);available.pop(i)
 return result+1
def unrank_repeat(order,length,rank):
 rank-=1; result=[]; n=len(order)
 for power in range(length-1,-1,-1):i,rank=divmod(rank,n**power);result.append(order[i])
 return ''.join(result)
def rank_repeat(order,word):
 n=len(order);return 1+sum(order.index(ch)*n**p for ch,p in zip(word,range(len(word)-1,-1,-1)))
def _load():return json.loads(PATH.read_text(encoding='utf8'))['templates']
def load_alphabetic_order_templates():
 ts=_load(); rs=json.loads(MANIFEST.read_text(encoding='utf8'))['records']; nums={int(x.group(1)) for x in re.finditer(r'(?m)^(\d+)\.',SOURCE.read_text(encoding='utf8'))}
 if set(nums)!={r['source_problem_number'] for r in rs} or len(rs)!=13:raise AlphabeticOrderError('Неполный source accounting')
 if {n for t in ts for n in t['source_problem_numbers']}!=nums:raise AlphabeticOrderError('Шаблоны не покрывают источник')
 return ts
def _make(t,r,s):
 name,gender=r.choice(eligible_names()); letters=tuple(name.upper());order=tuple(r.sample(letters,len(letters)));n=len(order); total=math.factorial(n); first=''.join(order); verb='придумал' if gender=='male' else 'придумала'; known=first
 base=f'{name} {verb} язык из букв {", ".join(letters)}. Настоящий порядок неизвестен. Все {total} {plural_words(total)} из этих {n} различных букв выписали по алфавиту. Первым словом стало {known}.'
 strategy=t['generation_strategy']
 if strategy=='permutation_rank':target=r.randint(2,total); answer=unrank_perm(order,target);q=f'Какое слово будет {ordinal(target)}?'
 elif strategy=='permutation_next':query=unrank_perm(order,r.randint(1,total-1));answer=unrank_perm(order,rank_perm(order,query)+1);q=f'Какое слово идёт сразу после слова {query}?'
 elif strategy=='permutation_previous':query=unrank_perm(order,r.randint(2,total));answer=unrank_perm(order,rank_perm(order,query)-1);q=f'Какое слово идёт сразу перед словом {query}?'
 elif strategy=='permutation_first':answer=first;q='Какое слово будет первым?'
 else:
  total=n**n;known=unrank_repeat(order,1,1)*n;answer=order[-1]*n;base=f'{name} {verb} язык из букв {", ".join(letters)}. Все {total} {plural_words(total)} длины {n} из этих букв с повторениями выписали по алфавиту. Первым словом стало {known}.';q='Какое слово может быть последним?'
 # First-word clue fixes the total order; this is an independent uniqueness witness.
 if (strategy!='repetition_last' and rank_perm(order,known)!=1) or (strategy=='repetition_last' and rank_repeat(order,known)!=1):raise AlphabeticOrderError('Некорректная clue')
 return G(MODULE_ID,t['id'],t['source_problem_numbers'],base+' '+q,answer,answer,{'name_nom':name,'name_gen':GEN[name],'gender':gender,'alphabet_letters':list(letters),'hidden_alphabet_order':list(order),'alphabet_size':n,'total_word_count':total,'known_word':known},s)
def generate_alphabetic_order_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_alphabetic_order_templates()}
 if template_id not in ts:raise AlphabeticOrderError(f'Неизвестный template={template_id}, seed={seed}')
 return _make(ts[template_id],rng or random.Random(seed),seed)
def generate_alphabetic_order_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise AlphabeticOrderError(module_id)
 return generate_alphabetic_order_problem(rng.choice(load_alphabetic_order_templates())['id'],rng=rng)
def alphabetic_order_template_metadata():
 ts=load_alphabetic_order_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Alphabetic Order','display_name':'Алфавитный порядок','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Алфавитный порядок','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']} for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':13}}
