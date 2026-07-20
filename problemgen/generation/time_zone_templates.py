"""Детерминированный генератор модуля «Часовые пояса и расписания поездок»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.russian.agreement import count_with_word_ru

ROOT=Path(__file__).resolve().parents[2]; MODULE_ID="time_zones_and_travel_schedules"; PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json"; MANIFEST=PATH.with_name("source_accounting.json"); SOURCES=(ROOT/"Docs"/"17_chasovye_poyasa_i_raspisaniya_poezdok_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"17_chasovye_poyasa_i_raspisaniya_poezdok_s_imenami_i_personazhami_deduplicated.md"); RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class TimeZoneTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedTimeZoneProblem:
 module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf8").splitlines() if (m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_time_zone_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"]; rs=load_source_accounting()["records"]; ns=[r["source_problem_number"] for r in rs]; active={n:t["id"] for t in ts for n in t["source_problem_numbers"]}; mapped={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if len(ns)!=43 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped or any(t["generation_strategy"] not in STRATEGIES or t["answer_type"]!="integer" for t in ts):raise TimeZoneTemplateError("Некорректный каталог или source accounting")
 return list(ts)
def local_to_absolute(local,offset):return local-offset
def absolute_to_local(moment,offset):return (moment+offset)%(24*60)
def fmt(moment):return f"{moment//60%24:02d}:{moment%60:02d}"
def _chars(r):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,1)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise TimeZoneTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedTimeZoneProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _olympiad(t,r,s):
 duration=r.randint(2,10)*60; start=r.randint(7,11)*60; offset=r.choice([60,120,180]); a_end=start+duration; b_start=start-offset; b_end=b_start+duration; gap=b_end-start; text=f"В городах А и Б олимпиада начинается в {fmt(start)} по местному времени и длится одинаково. Город А восточнее Б на {count_with_word_ru(offset//60,('час','часа','часов'))}. Окончание в Б на {count_with_word_ru(gap//60,('час','часа','часов'))} позже местного начала в А. Сколько минут длится олимпиада?";return _make(t,text,duration,{"start_local":start,"offset_minutes":offset,"observed_gap":gap},s)
def _direct(t,r,s):
 departure=r.randrange(24*60); origin=r.choice([-360,-240,-120,0,120,240,360]); destination=r.choice([x for x in [-360,-240,-120,0,120,240,360] if x!=origin]); flight=r.randint(80,720); arrival=absolute_to_local(local_to_absolute(departure,origin)+flight,destination);text=f"Самолёт вылетает в {fmt(departure)} по местному времени города А (UTC{origin//60:+d}) и летит {count_with_word_ru(flight,('минуту','минуты','минут'))} в город Б (UTC{destination//60:+d}). Во сколько минут после полуночи по местному времени Б он прилетит?";return _make(t,text,arrival,{"departure_local":departure,"origin_offset":origin,"destination_offset":destination,"flight_minutes":flight},s)
def _turn(t,r,s):
 start=r.randrange(24*60); origin=r.choice([-240,-120,0,120,240]); dest=origin+r.choice([120,240]); west=r.randint(30,180); east=west*r.choice([2,3,4]); arrival=absolute_to_local(local_to_absolute(start,origin)+east+west,dest); turn=absolute_to_local(local_to_absolute(start,origin)+east,origin);text=f"Из города А (UTC{origin//60:+d}) транспорт выехал в {fmt(start)}, ехал на восток {count_with_word_ru(east,('минуту','минуты','минут'))}, затем вернулся {count_with_word_ru(west,('минуту','минуты','минут'))} и прибыл в город Б (UTC{dest//60:+d}) в {fmt(arrival)}. Во сколько минут после полуночи по времени А был разворот?";return _make(t,text,turn,{"start_local":start,"origin_offset":origin,"destination_offset":dest,"east_minutes":east,"west_minutes":west,"arrival_local":arrival},s)
def _round(t,r,s):
 start=r.randrange(24*60); oa=r.choice([-240,-120,0,120]); ob=oa+r.choice([-120,120,240]); f1=r.randint(60,360); wait=r.randint(30,180); f2=r.randint(60,360); answer=absolute_to_local(local_to_absolute(start,oa)+f1+wait+f2,oa);text=f"Поезд выезжает из А (UTC{oa//60:+d}) в {fmt(start)}, едет {count_with_word_ru(f1,('минуту','минуты','минут'))} в Б (UTC{ob//60:+d}), ждёт {count_with_word_ru(wait,('минуту','минуты','минут'))} и возвращается {count_with_word_ru(f2,('минуту','минуты','минут'))}. Во сколько минут после полуночи по времени А он прибудет?";return _make(t,text,answer,{"start_local":start,"offset_a":oa,"offset_b":ob,"first_leg":f1,"wait":wait,"second_leg":f2},s)
def _multileg(t,r,s):
 u,cs=_chars(r);start=r.randrange(24*60);oa=r.choice([-120,0,120]);ob=oa+r.choice([60,120]);oc=ob+r.choice([0,60,120]);a,b,w=r.randint(60,300),r.randint(30,120),r.randint(60,300);answer=absolute_to_local(local_to_absolute(start,oa)+a+b+w,oc);name=cs[0].name;text=f"{name} вылетает из города А (UTC{oa//60:+d}) в {fmt(start)}, летит {count_with_word_ru(a,('минуту','минуты','минут'))} в Б (UTC{ob//60:+d}), ждёт {count_with_word_ru(b,('минуту','минуты','минут'))} и летит {count_with_word_ru(w,('минуту','минуты','минут'))} в В (UTC{oc//60:+d}). Во сколько минут после полуночи по времени В будет прибытие?";return _make(t,text,answer,{"start":start,"offsets":[oa,ob,oc],"legs":[a,w],"wait":b,"role_mapping":{"traveler":name}},s,u,cs)
def _elapsed(t,r,s):
 u,cs=_chars(r);origin=r.choice([-240,-120,0]);dest=origin+r.choice([120,240,360]);start=r.randrange(24*60);duration=r.randint(300,1500);arrival=absolute_to_local(local_to_absolute(start,origin)+duration,dest);text=f"Поездка из А (UTC{origin//60:+d}) началась в {fmt(start)} и завершилась на следующий день в Б (UTC{dest//60:+d}) в {fmt(arrival)}. Сколько минут продолжалось путешествие?";return _make(t,text,duration,{"start_local":start,"origin_offset":origin,"destination_offset":dest,"arrival_local":arrival},s,u,cs)
STRATEGIES={"olympiad_duration":_olympiad,"turnaround":_turn,"direct_arrival":_direct,"round_trip":_round,"named_multileg":_multileg,"named_elapsed":_elapsed}
def generate_time_zone_problem(template_id,*,seed=None,rng=None):
 ts={t["id"]:t for t in load_time_zone_templates()}
 if template_id not in ts:raise TimeZoneTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]["generation_strategy"]](ts[template_id],rng or random.Random(seed),seed)
def generate_time_zone_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise TimeZoneTemplateError(f"Неизвестный модуль {module_id}")
 return generate_time_zone_problem(rng.choice(load_time_zone_templates())["id"],rng=rng)
def time_zone_template_metadata():
 ts=load_time_zone_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Time Zones and Travel Schedules","display_name":"Часовые пояса и расписания поездок","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Часовые пояса и расписания поездок","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
