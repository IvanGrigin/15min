"""Exact-integer генератор модуля 31: текстовые уравнения."""
from __future__ import annotations
import json, random, re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import Character, load_approved_characters

ROOT=Path(__file__).resolve().parents[2]; MODULE_ID="word_problems_for_equation_setup"
PATH=ROOT/"data/templates/problem_sets"/MODULE_ID/"templates.json"; MANIFEST=PATH.with_name("source_accounting.json")
SOURCES=(ROOT/"docs/31_tekstovye_zadachi_na_sostavlenie_uravneniy_bez_imen_i_personazhey_deduplicated.md",ROOT/"docs/31_tekstovye_zadachi_na_sostavlenie_uravneniy_s_imenami_i_personazhami_deduplicated.md")
RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class EquationWordTemplateError(ValueError): pass
@dataclass(frozen=True)
class GeneratedEquationWordProblem:
 module:str; template_id:str; source_problem_numbers:list[int]; problem_text:str; answer:int; answer_text:str; parameters:dict[str,Any]; seed:int|None=None; universe:str|None=None; characters:list[str]|None=None
@lru_cache(maxsize=4)
def _load(p:str,s:int): del s; return json.loads(Path(p).read_text(encoding="utf-8"))
def source_problem_numbers(): return {int(m.group(1)) for f in SOURCES for l in f.read_text(encoding="utf-8").splitlines() if (m:=RX.match(l))}
def load_source_accounting(): return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_equation_word_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"]; rs=load_source_accounting()["records"]; ns=[r["source_problem_number"] for r in rs]
 active={n:t["id"] for t in ts for n in t["source_problem_numbers"]}; mapped={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if len(ns)!=45 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped: raise EquationWordTemplateError("Некорректный source-accounting модуля 31.")
 if len({t['id'] for t in ts})!=len(ts) or any(t['answer_type']!='integer' or not t['active'] or t['generation_strategy'] not in STRATEGIES for t in ts): raise EquationWordTemplateError("Некорректный каталог модуля 31.")
 if any(r['status']!='active_template' and not r.get('reason') for r in rs): raise EquationWordTemplateError("У исключения нет причины.")
 return list(ts)
def _chars(r,n):
 u=r.choice(sorted(load_approved_characters())); c=r.sample(load_approved_characters()[u],n); return u,c
def _make(t,text,a,p,seed,u=None,c=None):
 if not isinstance(a,int) or '{' in text: raise EquationWordTemplateError(f"template={t['id']} seed={seed}: нецелый ответ или placeholder")
 return GeneratedEquationWordProblem(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),p,seed,u,[x.name for x in c] if c else None)
def _zero(t,r,s):
 b=r.randint(20,200); second=r.randint(11,99); intended=b+second; shown=b+10*second
 answer=second
 if shown-intended!=9*answer: raise EquationWordTemplateError("Ошибка нуля не проверена")
 return _make(t,f"На калькуляторе складывали {b} и {second}. При наборе второго числа случайно добавили ноль и вместо {intended} получили {shown}. Какое было второе слагаемое?",answer,{"first_addend":b,"second_addend":second,"intended_sum":intended,"shown_sum":shown},s)
def _trains(t,r,s):
 seats=r.randint(31,60); parts=tuple(r.sample(range(2,13),3)); values=[seats*x for x in parts]; a=sum(parts)
 if sum(values)%seats: raise EquationWordTemplateError("Деление не точно")
 return _make(t,f"В трёх поездах {values[0]}, {values[1]} и {values[2]} мест. В каждом вагоне по {seats} мест. Сколько вагонов в поездах вместе?",a,{"seats_per_car":seats,"train_seats":values},s)
def _shelf(t,r,s):
 l=r.randint(2,30); right=r.randint(2,30); a=l+right-1; return _make(t,f"Книга стоит {l}-й слева и {right}-й справа. Сколько книг на полке?",a,{"left_position":l,"right_position":right},s)
def _linear(t,r,s):
 x=r.randint(3,30); k=r.randint(2,12); add=x*(k-1); a=x
 return _make(t,f"Какое число нужно умножить на {k}, чтобы получить тот же результат, что и при прибавлении к нему {add}?",a,{"multiplier":k,"addend":add},s)
def _comp(t,r,s):
 size=r.choice((4,6,8)); car=r.randint(1,30); place=(car-1)*size+r.randint(1,size); a=(place-1)//size+1
 return _make(t,f"В вагоне по {size} мест в каждом купе. В каком купе находится место №{place}?",a,{"places_per_compartment":size,"place_number":place},s)
def _quot(t,r,s):
 divisor=r.randint(2,20); q=divisor*r.choice((2,3,4)); dividend=q*3; a=q
 if dividend//q!=3 or q//divisor not in (2,3,4): raise EquationWordTemplateError("Связи частного нарушены")
 return _make(t,f"Найдите частное, если оно в 3 раза меньше делимого и в {q//divisor} раза больше делителя.",a,{"dividend":dividend,"divisor":divisor},s)
def _multiple(t,r,s):
 factor=r.randint(2,7); small=r.randint(5,40); large=factor*small; diff=large-small; u,c=_chars(r,2)
 a=small
 return _make(t,f"Первый участник — {c[0].name}, второй — {c[1].name}. У первого в {factor} раза больше карточек со словами, чем у второго, и на {diff} больше. Сколько карточек у второго?",a,{"factor":factor,"difference":diff,"role_mapping":{"first":c[0].name,"second":c[1].name}},s,u,c)
def _descending(t,r,s):
 last=r.randint(20,100); total=4*last+6; a=last
 return _make(t,f"Четыре зверя получили {total} таблеток: каждый следующий получил на одну меньше предыдущего. Сколько таблеток получил четвёртый зверь?",a,{"total_tablets":total,"step":1},s)
def _reserve(t,r,s):
 target=r.randint(200,600); remaining_second=r.randint(10,target//5); dale=target-remaining_second; chip=target-4*remaining_second
 a=target
 return _make(t,f"Двое должны запасти поровну. Один уже запас {chip}, другой — {dale}; первому осталось в 4 раза больше, чем второму. Сколько должен запасти каждый?",a,{"first_saved":chip,"second_saved":dale,"remaining_ratio":4},s)
def _food(t,r,s):
 boys=r.randint(4,20); girls=r.randint(4,20); candies=3*boys+5*girls; buns=boys*girls; a=buns
 return _make(t,f"В классе {boys+girls} детей. Каждый мальчик съел 3 конфеты, каждая девочка — 5; всего съели {candies} конфет. Каждая девочка дала по булочке каждому мальчику. Сколько булочек было нужно?",a,{"boys":boys,"girls":girls,"candies":candies},s)
STRATEGIES={"zero_key":_zero,"train_cars":_trains,"shelf_position":_shelf,"linear_balance":_linear,"compartment":_comp,"quotient_relations":_quot,"multiple_difference":_multiple,"descending_shares":_descending,"equal_reserve":_reserve,"food_system":_food}
def generate_equation_word_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_equation_word_templates()}
 if template_id not in ts: raise EquationWordTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_equation_word_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID: raise EquationWordTemplateError(f"Ожидался {MODULE_ID}, получен {module_id}")
 return generate_equation_word_problem(rng.choice(load_equation_word_templates())['id'],rng=rng)
def equation_word_template_metadata():
 ts=load_equation_word_templates(); return {"modules":[{"module_id":MODULE_ID,"title":"Word Problems for Equation Setup","display_name":"Текстовые задачи на составление уравнений","template_count":len(ts)}],"templates":[{"template_id":t['id'],"title":t['id'],"display_name":t['id'],"module_name":"Текстовые задачи на составление уравнений","source_problem_numbers":t['source_problem_numbers'],"problem_type":t['generation_strategy']} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
