"""Детерминированный генератор модуля «Работа, производительность и совместные действия»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from problemgen.russian.agreement import count_with_word_ru
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="work_productivity_and_joint_actions";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"19_rabota_proizvoditelnost_i_sovmestnye_deystviya_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"19_rabota_proizvoditelnost_i_sovmestnye_deystviya_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class WorkTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedWorkProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf8").splitlines() if(m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_work_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs];active={n:t["id"] for t in ts for n in t["source_problem_numbers"]};mapped={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if len(ns)!=16 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped:raise WorkTemplateError("Некорректный каталог или manifest")
 return list(ts)
def _chars(r,n):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise WorkTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedWorkProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _saw(t,r,s):
 long_parts,short_parts=r.choice([(5,4),(6,3),(7,5)]);common=r.randint(3,20);long_count=common//(long_parts-1)*(short_parts-1);short_count=common//(short_parts-1)*(long_parts-1)
 # choose a common multiple of cuts per log
 lcm=(long_parts-1)*(short_parts-1);common=r.randint(1,12)*lcm;long_count=common//(long_parts-1);short_count=common//(short_parts-1);text=f"Длинные брёвна распиливают на {long_parts} частей, короткие — на {short_parts}. Всего {long_count+short_count} брёвен; на оба вида сделано поровну распилов. Сколько распилов сделано для каждого вида?";return _make(t,text,common,{"long_parts":long_parts,"short_parts":short_parts,"long_count":long_count,"short_count":short_count},s)
def _consume(t,r,s):
 rate=r.randint(2,12);hours=r.randint(2,20);volume=rate*hours;text=f"Машина расходует {count_with_word_ru(rate,('единицу','единицы','единиц'))} материала в час. В запасе {count_with_word_ru(volume,('единица','единицы','единиц'))}. Через сколько часов запас закончится?";return _make(t,text,hours,{"rate":rate,"volume":volume},s)
def _settle(t,r,s):
 u,cs=_chars(r,2);total=r.choice([200,400,600,800,1000]);paid=r.randint(0,total);answer=total//2-paid;a,b=cs;text=f"{a.name} и {b.name} оплачивают {count_with_word_ru(total,('рубль','рубля','рублей'))} поровну. Одним из участников уже внесено {count_with_word_ru(paid,('рубль','рубля','рублей'))}. Сколько рублей осталось внести этому участнику до половины общей суммы?";return _make(t,text,answer,{"total":total,"paid":paid,"role_mapping":{"first":a.name,"second":b.name}},s,u,cs)
def _joint(t,r,s):
 u,cs=_chars(r,2);a=r.randint(2,10);b=r.randint(2,10);hours=r.randint(2,20);total=(a+b)*hours;x,y=cs;text=f"{x.name} выполняет {count_with_word_ru(a,('деталь','детали','деталей'))} в час, а {y.name} — {count_with_word_ru(b,('деталь','детали','деталей'))} в час. Сколько деталей они сделают вместе за {count_with_word_ru(hours,('час','часа','часов'))}?";return _make(t,text,total,{"first_rate":a,"second_rate":b,"hours":hours,"role_mapping":{"first":x.name,"second":y.name}},s,u,cs)
STRATEGIES={"equal_sawing":_saw,"consumption_rate":_consume,"equal_share_settlement":_settle,"joint_productivity":_joint}
def generate_work_problem(template_id,*,seed=None,rng=None):
 ts={t["id"]:t for t in load_work_templates()}
 if template_id not in ts:raise WorkTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]["generation_strategy"]](ts[template_id],rng or random.Random(seed),seed)
def generate_work_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise WorkTemplateError(f"Неизвестный модуль {module_id}")
 return generate_work_problem(rng.choice(load_work_templates())["id"],rng=rng)
def work_template_metadata():
 ts=load_work_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Work, Productivity and Joint Actions","display_name":"Работа, производительность и совместные действия","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Работа, производительность и совместные действия","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
