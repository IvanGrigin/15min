"""Exact-integer генератор модуля 28."""
from __future__ import annotations
import json,random
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MODULE_ID='quantities_units_weight_and_scaling';PATH=ROOT/'data/templates/problem_sets'/MODULE_ID/'templates.json'
@dataclass(frozen=True)
class G:module:str;template_id:str;source_problem_numbers:list;problem_text:str;answer:int;answer_text:str;parameters:dict
def load_quantity_templates():return json.loads(PATH.read_text(encoding='utf8'))['templates']
def _g(t,r):
 s=t['generation_strategy']
 if s=='self_weight':d=r.choice((3,4,5));base=r.randint(2,30)*(d-1);a=base*d//(d-1);text=f'Груз весит {base} кг плюс одну {d}-ю собственного веса. Сколько весит весь груз?';v={'base_weight':base,'denominator':d}
 elif s=='load':n=r.randint(100,1000);m=r.randint(2,50);cap=r.randint(1,20)*1000;a=(n*m+cap-1)//cap;text=f'На складе {n} коробок массой {m} кг. Сколько машин грузоподъёмностью {cap//1000} т нужно минимум?';v={'box_count':n,'box_mass':m,'capacity_kg':cap}
 elif s=='bridge':river=r.randint(20,200);d=r.choice((3,4,5));a=river*d//(d-2);text=f'Через реку шириной {river} м построен мост. По одной {d}-й длины лежит над каждым берегом. Найдите длину моста.';v={'river_width':river,'denominator':d}
 else:a=r.choice((10,20,30,40));text=f'Арбуз весил {a} кг и содержал 99% воды. После высыхания воды стало 98%. Сколько он весит?';v={'initial_mass':a}
 return G(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),v)
def generate_quantity_problem(template_id,*,seed=None,rng=None):
 t=next(x for x in load_quantity_templates()if x['id']==template_id);return _g(t,rng or random.Random(seed))
def generate_quantity_problem_from_module(module_id,*,rng):return generate_quantity_problem(rng.choice(load_quantity_templates())['id'],rng=rng)
def quantity_template_metadata():
 ts=load_quantity_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Quantities, Units, Weight and Scaling','display_name':'Величины, единицы, вес и масштабирование','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Величины, единицы, вес и масштабирование','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']}for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':12}}
