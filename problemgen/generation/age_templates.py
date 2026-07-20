"""Детерминированный генератор модуля «Возраст и поколения»."""
from __future__ import annotations
import json,random,re
from problemgen.russian.agreement import count_with_word_ru
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="ages_and_generations";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"21_vozrast_i_pokoleniya_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"21_vozrast_i_pokoleniya_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class AgeTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedAgeProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding='utf8').splitlines() if(m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding='utf8'))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_age_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)['templates'];rs=load_source_accounting()['records'];ns=[r['source_problem_number'] for r in rs];active={n:t['id'] for t in ts for n in t['source_problem_numbers']};mapped={r['source_problem_number']:r['template_id'] for r in rs}
 if len(ns)!=15 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped:raise AgeTemplateError('Некорректный каталог или manifest')
 return list(ts)
def _chars(r,n):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or '{' in text:raise AgeTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedAgeProblem(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _generations(t,r,s):
 g=r.randint(1,8);a=2**g;text=f'Сколько предков имеет человек ровно в {g}-м поколении назад, если у каждого два родителя?';return _make(t,text,a,{'generation':g},s)
def _difference(t,r,s):
 u,cs=_chars(r,2);young=r.randint(3,30);diff=r.randint(1,50);older=young+diff;a,b=cs;text=f'Персонажи: {a.name} и {b.name}. Возраст старшего больше возраста младшего на {count_with_word_ru(diff,("год","года","лет"))}. Возраст младшего — {count_with_word_ru(young,("год","года","лет"))}. Сколько лет старшему?';return _make(t,text,older,{'younger_age':young,'difference':diff,'role_mapping':{'older':a.name,'younger':b.name}},s,u,cs)
def _future(t,r,s):
 u,cs=_chars(r,1);age=r.randint(1,70);years=r.randint(1,30);c=cs[0];text=f'Персонаж: {c.name}. Текущий возраст — {count_with_word_ru(age,("год","года","лет"))}. Какой возраст будет через {count_with_word_ru(years,("год","года","лет"))}?';return _make(t,text,age+years,{'current_age':age,'years':years,'role_mapping':{'character':c.name}},s,u,cs)
def _family(t,r,s):
 u,cs=_chars(r,2);child=r.randint(2,20);parent=child+r.randint(18,45);a,b=cs;text=f'Персонажи: {a.name} и {b.name}. Сумма возрастов старшего и младшего равна {parent+child}. Возраст младшего — {count_with_word_ru(child,("год","года","лет"))}. Сколько лет старшему?';return _make(t,text,parent,{'sum_ages':parent+child,'child_age':child,'role_mapping':{'parent':a.name,'child':b.name}},s,u,cs)
STRATEGIES={'generation_count':_generations,'age_difference':_difference,'future_age':_future,'family_sum':_family}
def generate_age_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_age_templates()}
 if template_id not in ts:raise AgeTemplateError(f'Неизвестный template={template_id}, seed={seed}')
 return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_age_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise AgeTemplateError(f'Неизвестный модуль {module_id}')
 return generate_age_problem(rng.choice(load_age_templates())['id'],rng=rng)
def age_template_metadata():
 ts=load_age_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Ages and Generations','display_name':'Возраст и поколения','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Возраст и поколения','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']} for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':len(source_problem_numbers())}}
