"""Детерминированный генератор модуля «Движение, скорость и расстояние»."""
from __future__ import annotations
import json,random,re
from fractions import Fraction
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.russian.agreement import count_with_word_ru
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
def _make(t,text,a,p,s,u=None,cs=None,answer_text=None):
 if not isinstance(a,int) or "{" in text:raise MotionTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedMotionProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a) if answer_text is None else answer_text,p,s,u,[c.name for c in cs] if cs else None)
def _alternating(t,r,s):
 minutes=r.randint(4,20);unit=r.randint(1,9)
 # Position is an alternating signed sum of the *per-minute* distances;
 # no conversion to seconds is involved.
 answer=abs(sum((1 if i%2 else -1)*i*unit for i in range(1,minutes+1)))
 text=f"Тело за каждую минуту меняет направление: в минуту с номером i оно проходит {unit}i м, начиная движение вперёд. На каком расстоянии от старта оно будет через {count_with_word_ru(minutes,('минуту','минуты','минут'))}?"
 return _make(t,text,answer,{"minutes":minutes,"step_m":unit},s,answer_text=f"{answer} м")
def _pursuit(t,r,s):
 u,cs=_chars(r,2);slow=r.randint(2,8);delta=r.randint(1,6);fast=slow+delta;answer=r.randint(5,90);gap=answer*delta; a,b=cs
 # The question refers to narrative roles, so no unverified heuristic
 # declension of a compound personal name is needed.
 text=f"{a.name} идёт впереди, а {b.name} догоняет идущего впереди. Расстояние между ними {gap} м. Скорость идущего впереди — {slow} м/мин, догоняющего — {fast} м/мин. Через сколько минут они встретятся?"
 return _make(t,text,pursuit_minutes(gap,fast,slow),{"gap_m":gap,"slow_speed":slow,"fast_speed":fast,"role_mapping":{"ahead":a.name,"pursuer":b.name}},s,u,cs)
def _piecewise(t,r,s):
 u,cs=_chars(r,1);base=r.randint(20,80);extra=r.randint(10,40);answer=base+extra;name=cs[0].name;text=f"{name} проходит первую часть пути за {count_with_word_ru(base//2,('минуту','минуты','минут'))}, вторую — за {count_with_word_ru(base-base//2,('минуту','минуты','минут'))}, а из-за остановки тратит ещё {count_with_word_ru(extra,('минуту','минуты','минут'))}. Сколько минут занял весь путь?";return _make(t,text,answer,{"first_minutes":base//2,"second_minutes":base-base//2,"stop_minutes":extra,"role_mapping":{"traveler":name}},s,u,cs)
def _train(t,r,s):
 v1,v2=r.choice([(10,11),(12,15),(18,21),(24,27)])
 # (v1+v2)*1000/3600 is the relative speed in m/s.  The chosen
 # duration makes the total length integral without converting the answer
 # to minutes.
 answer=r.choice(range(30,601,30)); total=(v1+v2)*answer*5//18
 l1=r.randint(total//3,2*total//3-1); l2=total-l1
 text=f"Два поезда длиной {l1} м и {l2} м едут навстречу со скоростями {v1} и {v2} км/ч. Сколько секунд проходит от встречи машинистов до встречи последних вагонов?"
 return _make(t,text,answer,{"lengths":[l1,l2],"speeds":[v1,v2],"relative_speed_m_per_s":(v1+v2)*1000/3600},s)
def _ant(t,r,s):
 u,cs=_chars(r,1);length=r.randint(100,500);position=r.randint(1,length-1);speed=r.randint(1,10);farther=max(position,length-position);answer=(farther+speed-1)//speed
 text=f"Муравей находится на палочке длиной {length} см в {position} см от левого конца и бежит без поворотов со скоростью {speed} см/с. Направление его движения неизвестно. Не позднее чем через сколько полных секунд муравей упадёт?"
 return _make(t,text,answer,{"length":length,"position":position,"speed":speed,"farther_end_distance":farther,"role_mapping":{"observer":cs[0].name}},s,u,cs)
def _fly(t,r,s):
 u,cs=_chars(r,2);distance=r.choice([24,30,36,40,48,60]);v1,v2=r.choice([(4,6),(5,7),(6,9),(8,10)])
 # Restrict the fly speed to values giving an integral exact answer; this is
 # a bounded candidate set, not a retry loop.
 meeting_hours=Fraction(distance,v1+v2)
 flyspeed=next(speed for speed in (60,120,180) if (Fraction(speed)*meeting_hours).denominator==1)
 travel=Fraction(flyspeed)*meeting_hours
 answer=travel.numerator;a,b=cs;text=f"{a.name} и {b.name} движутся навстречу по дороге длиной {distance} км со скоростями {v1} и {v2} км/ч. Муха летит между ними со скоростью {flyspeed} км/ч до их встречи. Сколько километров пролетит муха?"
 return _make(t,text,answer,{"distance":distance,"speeds":[v1,v2],"meeting_time_hours":str(meeting_hours),"fly_speed":flyspeed,"role_mapping":{"first":a.name,"second":b.name}},s,u,cs)
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
