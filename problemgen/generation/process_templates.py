"""Детерминированный генератор числовых процессов и повторяющихся операций."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import Character,load_approved_characters
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="number_processes_and_repeated_operations";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"14_chislovye_protsessy_i_povtoryayushchiesya_operatsii_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"14_chislovye_protsessy_i_povtoryayushchiesya_operatsii_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class ProcessTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedProcessProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf-8").splitlines() if (m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf-8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_process_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs]
 if len({t["id"] for t in ts})!=len(ts) or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers():raise ProcessTemplateError("Некорректный каталог")
 if {n:t["id"] for t in ts for n in t["source_problem_numbers"]}!={r["source_problem_number"]:r["template_id"] for r in rs}:raise ProcessTemplateError("Manifest не согласован")
 return list(ts)
def collatz_steps(start,threshold,limit=1000):
 if start<1 or threshold<1:raise ProcessTemplateError("Некорректный старт или порог")
 x=start
 for step in range(limit+1):
  if x<threshold:return step
  x=x//2 if x%2==0 else 3*x+1
 raise ProcessTemplateError("Не достигнут порог в ограничении")
def overlay_value(sectors,under,over,query):
 if not 1<=under<=sectors or not 1<=over<=sectors or not 1<=query<=sectors:raise ProcessTemplateError("Сектор вне круга")
 return ((query+over-under-1)%sectors)+1
def triangular(n):return n*(n+1)//2
def _chars(r):
 u,cs=r.choice(list(load_approved_characters().items()));return u,[r.choice(cs)]
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise ProcessTemplateError("Невалидный результат")
 return GeneratedProcessProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _collatz(t,r,s):
 threshold=r.choice([10,20,30]);start=r.randint(threshold,10000);answer=collatz_steps(start,threshold);text=f"На доске число {start}. Каждую минуту чётное число делят пополам, а нечётное умножают на 3 и прибавляют 1. Через сколько минут впервые получится число меньше {threshold}?";return _make(t,text,answer,{"start_value":start,"threshold":threshold},s)
def _mergers(t,r,s):
 start=r.randint(20,200);years=r.randint(1,(start-1)//2);answer=start-2*years;finish=(start-1)//2; text=f"На планете {start} государств. Каждый год три государства объединяются в одно. Сколько государств будет через {years} лет?";return _make(t,text,answer,{"start_states":start,"years":years,"completion_years":finish},s)
def _overlay(t,r,s):
 u,cs=_chars(r);n=r.randint(20,500);under=r.randint(1,n);over=r.randint(1,n);query=over;answer=overlay_value(n,under,over,query);name=cs[0].name;text=f"{name} рассматривает два круга из {n} секторов, пронумерованных от 1 до {n}. Круги положили без переворота так, что на {under} лежит {over}. Какое число лежит на {query}?";return _make(t,text,answer,{"sector_count":n,"under_sector":under,"over_sector":over,"query_sector":query,"role_mapping":{"observer":name}},s,u,cs)
def _triangular(t,r,s):
 u,cs=_chars(r);n=r.randint(5,1000);first=triangular(n);second=triangular(n+1);answer=triangular(n+2);name=cs[0].name;text=f"{name} складывает натуральные числа по порядку. В какой-то момент получены подряд {first} и {second}. Какое число получится следующим?";return _make(t,text,answer,{"term_index":n,"first_sum":first,"second_sum":second,"role_mapping":{"calculator":name}},s,u,cs)
STRATEGIES={"collatz_threshold":_collatz,"three_to_one_mergers":_mergers,"cyclic_overlay":_overlay,"successive_triangular_sums":_triangular}
def generate_process_problem(template_id,*,seed=None,rng=None):
 ts={t["id"]:t for t in load_process_templates()}
 if template_id not in ts:raise ProcessTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]["generation_strategy"]](ts[template_id],rng or random.Random(seed if seed is not None else datetime.now().timestamp()),seed)
def generate_process_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise ProcessTemplateError(f"Неизвестный модуль {module_id}")
 return generate_process_problem(rng.choice(load_process_templates())["id"],rng=rng)
def process_template_metadata():
 ts=load_process_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Number Processes and Repeated Operations","display_name":"Числовые процессы и повторяющиеся операции","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Числовые процессы и повторяющиеся операции","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
