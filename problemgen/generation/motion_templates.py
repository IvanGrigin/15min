"""Детерминированный генератор модуля «Движение, скорость и расстояние»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="motion_speed_and_distance";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"18_dvizhenie_skorost_i_rasstoyanie_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"18_dvizhenie_skorost_i_rasstoyanie_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class MotionTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedMotionProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf8").splitlines() if(m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_motion_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs];active={n:t["id"] for t in ts for n in t["source_problem_numbers"]};mapped={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if len(ns)!=60 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped or any(t["generation_strategy"] not in STRATEGIES for t in ts):raise MotionTemplateError("Некорректный каталог или manifest")
 return list(ts)
def pursuit_minutes(gap_m,speed_fast,speed_slow):
 if speed_fast<=speed_slow or gap_m%(speed_fast-speed_slow):raise MotionTemplateError("Догонка не целая")
 return gap_m//(speed_fast-speed_slow)
def _chars(r,n):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise MotionTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedMotionProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _alternating(t,r,s):
 minutes=r.randint(4,20);unit=r.randint(1,9);answer=abs(sum((1 if i%2 else -1)*i*unit*60 for i in range(1,minutes+1)));text=f"Тело за каждую минуту меняет направление: в минуту с номером i оно проходит i·{unit} метров, начиная вперёд. На каком расстоянии в метрах от старта оно будет через {minutes} минут?";return _make(t,text,answer,{"minutes":minutes,"unit_speed":unit},s)
def _pursuit(t,r,s):
 u,cs=_chars(r,2);slow=r.randint(2,8);delta=r.randint(1,6);fast=slow+delta;answer=r.randint(5,90);gap=answer*delta; a,b=cs;text=f"{a.name} идёт впереди {b.name}; расстояние между ними {gap} м. Скорости равны {slow} и {fast} м/мин соответственно. Через сколько минут {b.name} догонит {a.name}?";return _make(t,text,pursuit_minutes(gap,fast,slow),{"gap_m":gap,"slow_speed":slow,"fast_speed":fast,"role_mapping":{"ahead":a.name,"pursuer":b.name}},s,u,cs)
def _piecewise(t,r,s):
 u,cs=_chars(r,1);base=r.randint(20,80);extra=r.randint(10,40);answer=base+extra;name=cs[0].name;text=f"{name} проходит первую часть пути за {base//2} минут, вторую — за {base-base//2} минут, а из-за остановки тратит ещё {extra} минут. Сколько минут занял весь путь?";return _make(t,text,answer,{"first_minutes":base//2,"second_minutes":base-base//2,"stop_minutes":extra,"role_mapping":{"traveler":name}},s,u,cs)
def _train(t,r,s):
 l1,l2=r.randint(40,200),r.randint(40,200);v1,v2=r.choice([(10,11),(12,15),(18,21),(24,27)])
 # construct exact seconds by linked total and relative velocity
 answer=r.randint(2,30);total=(v1+v2)*1000*answer//60; l1=total//2;l2=total-l1;text=f"Два поезда длиной {l1} и {l2} м едут навстречу со скоростями {v1} и {v2} км/ч. Сколько секунд проходит от встречи машинистов до встречи последних вагонов?";return _make(t,text,answer,{"lengths":[l1,l2],"speeds":[v1,v2]},s)
def _ant(t,r,s):
 u,cs=_chars(r,1);length=r.randint(100,500);position=r.randint(1,length-1);speed=r.randint(1,10);answer=max(position,length-position)//speed if max(position,length-position)%speed==0 else (max(position,length-position)+speed-1)//speed;name=cs[0].name;text=f"{name} находится на палочке длиной {length} см в {position} см от левого конца и бежит без поворотов со скоростью {speed} см/с. Через сколько секунд он гарантированно упадёт?";return _make(t,text,answer,{"length":length,"position":position,"speed":speed,"role_mapping":{"ant":name}},s,u,cs)
def _fly(t,r,s):
 u,cs=_chars(r,2);distance=r.choice([24,30,36,40,48,60]);v1,v2=r.choice([(4,6),(5,7),(6,9),(8,10)])
 minutes=distance*60//(v1+v2);flyspeed=r.choice([60,120,180]);answer=flyspeed*minutes//60;a,b=cs;text=f"{a.name} и {b.name} движутся навстречу по дороге длиной {distance} км со скоростями {v1} и {v2} км/ч. Муха летит между ними со скоростью {flyspeed} км/ч до их встречи. Сколько километров пролетит муха?";return _make(t,text,answer,{"distance":distance,"speeds":[v1,v2],"meeting_minutes":minutes,"fly_speed":flyspeed,"role_mapping":{"first":a.name,"second":b.name}},s,u,cs)
STRATEGIES={"alternating_displacement":_alternating,"pursuit":_pursuit,"piecewise_trip":_piecewise,"train_overlap":_train,"ant_fall":_ant,"fly_distance":_fly}
def generate_motion_problem(template_id,*,seed=None,rng=None):
 ts={t["id"]:t for t in load_motion_templates()}
 if template_id not in ts:raise MotionTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]["generation_strategy"]](ts[template_id],rng or random.Random(seed),seed)
def generate_motion_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise MotionTemplateError(f"Неизвестный модуль {module_id}")
 return generate_motion_problem(rng.choice(load_motion_templates())["id"],rng=rng)
def motion_template_metadata():
 ts=load_motion_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Motion, Speed and Distance","display_name":"Движение, скорость и расстояние","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Движение, скорость и расстояние","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
