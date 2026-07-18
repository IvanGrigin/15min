"""Генератор exact-integer задач на чётность соседних цифр."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="parity_invariants_strategies_and_moves";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"13_chetnost_invarianty_strategii_i_khody_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"13_chetnost_invarianty_strategii_i_khody_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class ParityTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedParityProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf-8").splitlines() if (m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf-8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def has_equal_adjacent_parity(n:int)->bool:
 ds=str(n)
 if n<0 or len(ds)<2:raise ParityTemplateError("Число должно быть положительным и многозначным")
 return any((int(a)-int(b))%2==0 for a,b in zip(ds,ds[1:]))
def load_parity_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs]
 if len(ts)!=1 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers():raise ParityTemplateError("Некорректный каталог или accounting")
 active={n for t in ts for n in t["source_problem_numbers"]};stated={r["source_problem_number"] for r in rs if r["status"]=="active_template"}
 if active!=stated or any(not r.get("reason") for r in rs if r["status"]!="active_template"):raise ParityTemplateError("Manifest не согласован")
 return list(ts)
def generate_parity_problem(template_id,*,seed=None,rng=None):
 t=load_parity_templates()[0]
 if template_id!=t["id"]:raise ParityTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 q=rng or random.Random(seed if seed is not None else datetime.now().timestamp());mode=q.choice(["equal_exists","alternating_all"]);numbers=[q.randint(10,9999999) for _ in range(5)];predicate=(lambda n:has_equal_adjacent_parity(n)) if mode=="equal_exists" else (lambda n:not has_equal_adjacent_parity(n));answer=sum(n for n in numbers if predicate(n));label="есть две соседние цифры одинаковой чётности" if mode=="equal_exists" else "любые две соседние цифры имеют разную чётность";text=f"Среди чисел {', '.join(map(str,numbers))} найдите сумму тех, у которых {label}.";return GeneratedParityProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,answer,str(answer),{"candidate_numbers":numbers,"parity_mode":mode},seed)
def generate_parity_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise ParityTemplateError(f"Неизвестный модуль {module_id}")
 return generate_parity_problem(load_parity_templates()[0]["id"],rng=rng)
def parity_template_metadata():
 t=load_parity_templates()[0];return {"modules":[{"module_id":MODULE_ID,"title":"Parity, Invariants, Strategies and Moves","display_name":"Чётность, инварианты, стратегии и ходы","template_count":1}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Чётность, инварианты, стратегии и ходы","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]}],"stats":{"total_modules":1,"total_templates":1,"covered_source_problem_numbers":len(source_problem_numbers())}}
