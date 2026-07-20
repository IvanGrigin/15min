"""Детерминированный генератор комбинаторики и подсчёта вариантов."""
from __future__ import annotations
import json, math, random, re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from itertools import permutations
from pathlib import Path
from typing import Any, Callable
from problemgen.generation.comparison_templates import Character, load_approved_characters
from problemgen.russian.agreement import pluralize_ru

ROOT=Path(__file__).resolve().parents[2]; MODULE_ID="combinatorics_and_counting_variants"; MAX_ATTEMPTS=80
SOURCE_PATHS=(ROOT/"Docs"/"11_kombinatorika_i_podschet_variantov_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"11_kombinatorika_i_podschet_variantov_s_imenami_i_personazhami_deduplicated.md")
TEMPLATE_PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json"; ACCOUNTING_PATH=TEMPLATE_PATH.with_name("source_accounting.json"); LINE_RE=re.compile(r"^\s*(\d+)\.\s+.+$")
class CombinatoricsTemplateError(ValueError): pass
@dataclass(frozen=True)
class GeneratedCombinatoricsProblem:
    module:str; template_id:str; source_problem_numbers:list[int]; problem_text:str; answer:int; answer_text:str; parameters:dict[str,Any]; seed:int|None=None; universe:str|None=None; characters:list[str]|None=None

def source_problem_numbers()->set[int]: return {int(m.group(1)) for p in SOURCE_PATHS for line in p.read_text(encoding="utf-8").splitlines() if (m:=LINE_RE.match(line))}
@lru_cache(maxsize=4)
def _json(path:str,stamp:int)->dict[str,Any]: del stamp; return json.loads(Path(path).read_text(encoding="utf-8"))
def load_source_accounting()->dict[str,Any]: return _json(str(ACCOUNTING_PATH),ACCOUNTING_PATH.stat().st_mtime_ns)
def load_combinatorics_templates()->list[dict[str,Any]]:
    ts=_json(str(TEMPLATE_PATH),TEMPLATE_PATH.stat().st_mtime_ns)["templates"]; validate_catalog(ts); return list(ts)
def validate_catalog(ts:list[dict[str,Any]])->None:
    required={"id","module","source_problem_numbers","render_template","generation_strategy","answer_type","uses_characters","required_character_count","active"}; ids=[]
    for t in ts:
        if required-set(t): raise CombinatoricsTemplateError(f"Неполная схема: {t}")
        ids.append(t["id"])
        if t["module"]!=MODULE_ID or t["answer_type"]!="integer" or not t["active"] or t["generation_strategy"] not in STRATEGIES: raise CombinatoricsTemplateError(f"Некорректный шаблон {t['id']}")
    if len(ids)!=len(set(ids)): raise CombinatoricsTemplateError("Повтор ID")
    records=load_source_accounting()["records"]; nums=[r["source_problem_number"] for r in records]
    if len(nums)!=len(set(nums)) or set(nums)!=source_problem_numbers(): raise CombinatoricsTemplateError("Нет точного покрытия источников")
    active={n:t["id"] for t in ts for n in t["source_problem_numbers"]}; manifest={r["source_problem_number"]:r["template_id"] for r in records if r["status"]=="active_template"}
    if active!=manifest: raise CombinatoricsTemplateError("Manifest не совпадает с runtime")
    if any(not r.get("reason") for r in records if r["status"]!="active_template"): raise CombinatoricsTemplateError("Нет причины исключения")
def get_template(tid:str)->dict[str,Any]:
    for t in load_combinatorics_templates():
        if t["id"]==tid:return t
    raise CombinatoricsTemplateError(f"Неизвестный шаблон {tid}")
def count_odd_open(lower:int,upper:int)->int:
    if lower>=upper: raise CombinatoricsTemplateError("lower должен быть меньше upper")
    return (upper//2)-((lower+1)//2)
def ordered_nonempty(n:int)->int:
    if not 1<=n<=10: raise CombinatoricsTemplateError("object_count вне диапазона")
    return sum(math.factorial(n)//math.factorial(n-k) for k in range(1,n+1))
def max_distinct_type_sets(counts:list[int],types_per_set:int)->int:
    if not counts or not 1<=types_per_set<=len(counts) or any(c<0 for c in counts): raise CombinatoricsTemplateError("Некорректные ресурсы")
    return max(k for k in range(sum(counts)//types_per_set+1) if sum(min(c,k) for c in counts)>=k*types_per_set)
def solve_cyclic_distribution(child_count:int,first:int,second:int,total:int,target:int)->int:
    if child_count<1 or min(first,second,total,target)<1: raise CombinatoricsTemplateError("Некорректное циклическое распределение")
    received=[0]*child_count; spent=0; step=0
    while spent<total:
        amount=first if step%2==0 else second
        if spent+amount>total: raise CombinatoricsTemplateError("Общий ресурс обрывает выдачу внутри шага")
        received[step%child_count]+=amount; spent+=amount; step+=1
    return received.count(target)
def _chars(r:random.Random,n:int)->tuple[str,list[Character]]:
    u,cs=r.choice([(u,c) for u,c in load_approved_characters().items() if len(c)>=n]); return u,r.sample(cs,n)
def _make(t,text,answer,p,seed,u=None,cs=None):
    if not isinstance(answer,int) or "{" in text: raise CombinatoricsTemplateError("Невалидный результат")
    return GeneratedCombinatoricsProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,answer,str(answer),p,seed,u,[c.name for c in cs] if cs else None)
def _odd(t,r,s):
    lo=r.randint(10,3000); hi=lo+r.randint(20,3000); ans=count_odd_open(lo,hi); brute=sum(n%2==1 for n in range(lo+1,hi));
    if ans!=brute: raise CombinatoricsTemplateError("Независимый перебор не совпал")
    return _make(t,f"Сколько существует нечётных чисел, больших {lo}, но меньших {hi}?",ans,{"lower_bound":lo,"upper_bound":hi},s)
def _ordered(t,r,s):
    n=r.randint(2,8); ans=ordered_nonempty(n); brute=sum(len(list(permutations(range(n),k))) for k in range(1,n+1));
    if ans!=brute: raise CombinatoricsTemplateError("Перебор размещений не совпал")
    return _make(t,f"На полке стоят {n} различных {pluralize_ru(n, ('альбом', 'альбома', 'альбомов'))}. Сколькими способами можно выложить в стопку несколько из них, если стопка непуста и порядок важен?",ans,{"object_count":n},s)
def _cyclic(t,r,s):
    u,cs=_chars(r,1); child_count=2*r.randint(8,30); first=r.randint(1,5); second=r.choice([x for x in range(1,7) if x!=first]); cycles=r.randint(0,3); extra_pairs=r.randint(2,child_count//2-1); pair_steps=cycles*(child_count//2)+extra_pairs; total=pair_steps*(first+second); target=r.choice([first,second,2*first,2*second]); answer=solve_cyclic_distribution(child_count,first,second,total,target)
    text=f"По кругу стоят {child_count} детей. {cs[0].name} выдаёт подарки по очереди: первому {first}, второму {second}, затем снова {first}, {second} и так далее. Всего выдано {total} подарков. Сколько детей получили ровно {target} {pluralize_ru(target,('подарок','подарка','подарков'))}?"
    return _make(t,text,answer,{"child_count":child_count,"first_amount":first,"second_amount":second,"total_gifts":total,"target_amount":target,"role_mapping":{"giver":cs[0].name}},s,u,cs)
def _packing(t,r,s):
    u,cs=_chars(r,1); counts=[r.randint(5,45) for _ in range(4)]; k=r.choice([2,3,4]); answer=max_distinct_type_sets(counts,k); fruits=("яблок","бананов","груш","апельсинов"); resources=", ".join(f"{v} {name}" for v,name in zip(counts,fruits)); text=f"{cs[0].name} получает один полный набор, когда в нём есть {k} разных вида фруктов. Есть {resources}. Какое наибольшее число полных наборов можно собрать?"; return _make(t,text,answer,{"resource_counts":counts,"types_per_set":k,"role_mapping":{"recipient":cs[0].name}},s,u,cs)
STRATEGIES:dict[str,Callable]={"odd_open_interval":_odd,"ordered_nonempty_selections":_ordered,"cyclic_alternating_distribution":_cyclic,"distinct_type_packing":_packing}
def generate_combinatorics_problem(template_id:str,*,seed:int|None=None,rng:random.Random|None=None)->GeneratedCombinatoricsProblem:
    t=get_template(template_id); local=rng or random.Random(seed if seed is not None else datetime.now().timestamp()); failures=[]
    for _ in range(MAX_ATTEMPTS):
        try:return STRATEGIES[t["generation_strategy"]](t,local,seed)
        except (ValueError,CombinatoricsTemplateError) as e: failures.append(str(e))
    raise CombinatoricsTemplateError(f"Не удалось сгенерировать template={template_id}, seed={seed}: {failures[-1:]}")
def generate_combinatorics_problem_from_module(module_id:str,*,rng:random.Random)->GeneratedCombinatoricsProblem:
    if module_id!=MODULE_ID: raise CombinatoricsTemplateError(f"Неизвестный модуль {module_id}")
    return generate_combinatorics_problem(rng.choice(load_combinatorics_templates())["id"],rng=rng)
def combinatorics_template_metadata()->dict[str,Any]:
    ts=load_combinatorics_templates(); return {"modules":[{"module_id":MODULE_ID,"title":"Combinatorics and Counting Variants","display_name":"Комбинаторика и подсчёт вариантов","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Комбинаторика и подсчёт вариантов","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
