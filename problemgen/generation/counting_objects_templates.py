"""Генератор модуля «Головы, ноги, колёса и подсчёт объектов»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
ROOT=Path(__file__).resolve().parents[2];MODULE_ID='heads_legs_wheels_and_object_counts';PATH=ROOT/'data'/'templates'/'problem_sets'/MODULE_ID/'templates.json';MANIFEST=PATH.with_name('source_accounting.json');SOURCES=(ROOT/'Docs'/'22_golovy_nogi_kolesa_i_podschet_obektov_bez_imen_i_personazhey_deduplicated.md',ROOT/'Docs'/'22_golovy_nogi_kolesa_i_podschet_obektov_s_imenami_i_personazhami_deduplicated.md');RX=re.compile(r'^\s*(\d+)\.\s+.+$')
class CountingTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedCountingProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding='utf8').splitlines() if(m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding='utf8'))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_counting_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)['templates'];rs=load_source_accounting()['records'];ns=[r['source_problem_number'] for r in rs];active={n:t['id'] for t in ts for n in t['source_problem_numbers']};mapped={r['source_problem_number']:r['template_id'] for r in rs}
 if len(ns)!=29 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped:raise CountingTemplateError('Некорректный manifest')
 return list(ts)
def _chars(r,n):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):return GeneratedCountingProblem(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _heads(t,r,s):
 four=r.randint(1,30);two=r.randint(1,30);total=four+two;legs=4*four+2*two;text=f'На ферме {total} животных: у одних 4 ноги, у других 2 ноги. Всего {legs} ног. Сколько четырёхногих животных?';return _make(t,text,four,{'total':total,'legs':legs},s)
def _wheels(t,r,s):
 u,cs=_chars(r,1);four=r.randint(1,20);two=r.randint(1,20);total=four+two;w=4*four+2*two;c=cs[0];text=f'{c.name} насчитал {total} машин и велосипедов с {w} колёсами. Сколько машин?';return _make(t,text,four,{'total':total,'wheels':w},s,u,cs)
def _objects(t,r,s):
 u,cs=_chars(r,1);a=r.randint(2,40);b=r.randint(2,40);c=cs[0];text=f'{c.name} собрал {a} красных и {b} синих предметов. Сколько предметов всего?';return _make(t,text,a+b,{'first':a,'second':b},s,u,cs)
STRATEGIES={'heads_legs':_heads,'wheels':_wheels,'objects':_objects}
def generate_counting_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_counting_templates()};return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_counting_problem_from_module(module_id,*,rng):return generate_counting_problem(rng.choice(load_counting_templates())['id'],rng=rng)
def counting_template_metadata():
 ts=load_counting_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Heads, Legs, Wheels and Object Counts','display_name':'Головы, ноги, колёса и подсчёт объектов','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Головы, ноги, колёса и подсчёт объектов','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']} for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':len(source_problem_numbers())}}
