"""Точный генератор модуля «Принцип Дирихле и гарантированный выбор»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any,Callable
ROOT=Path(__file__).resolve().parents[2]; MODULE_ID="pigeonhole_and_guaranteed_selection"; MAX_ATTEMPTS=50
SOURCES=(ROOT/"Docs"/"12_printsip_dirikhle_i_garantirovannyy_vybor_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"12_printsip_dirikhle_i_garantirovannyy_vybor_s_imenami_i_personazhami_deduplicated.md"); PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json"; MANIFEST=PATH.with_name("source_accounting.json"); RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class PigeonholeTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedPigeonholeProblem:
 module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf-8").splitlines() if (m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,stamp):del stamp;return json.loads(Path(p).read_text(encoding="utf-8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_pigeonhole_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];validate_catalog(ts);return list(ts)
def validate_catalog(ts):
 req={"id","module","source_problem_numbers","render_template","generation_strategy","answer_type","uses_characters","required_character_count","active"};ids=[]
 for t in ts:
  if req-set(t) or t["module"]!=MODULE_ID or t["answer_type"]!="integer" or t["generation_strategy"] not in STRATEGIES:raise PigeonholeTemplateError(f"Некорректный шаблон {t}")
  ids.append(t["id"])
 if len(ids)!=len(set(ids)):raise PigeonholeTemplateError("Повтор ID")
 rs=load_source_accounting()["records"];nums=[r["source_problem_number"] for r in rs]
 if len(nums)!=len(set(nums)) or set(nums)!=source_problem_numbers():raise PigeonholeTemplateError("Нет точного source accounting")
 active={n:t["id"] for t in ts for n in t["source_problem_numbers"]}; stated={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if active!=stated or any(not r.get("reason") for r in rs if r["status"]!="active_template"):raise PigeonholeTemplateError("Manifest не согласован")
def get_template(i):
 for t in load_pigeonhole_templates():
  if t["id"]==i:return t
 raise PigeonholeTemplateError(f"Неизвестный шаблон {i}")
def guarantee_target(other_count,required):
 if other_count<0 or required<1:raise PigeonholeTemplateError("Некорректные количества")
 return other_count+required
def inventory_total(red_draw,blue_draw,no_white_draw):
 # non-red <= red_draw-1; non-blue <= blue_draw-1; red+blue >= no_white_draw.
 white_max=(red_draw+blue_draw-2-no_white_draw)//2
 if white_max!=1:raise PigeonholeTemplateError("Условия не восстанавливают единственный положительный белый запас")
 return no_white_draw+1
def _make(t,text,a,p,s):
 if not isinstance(a,int) or "{" in text:raise PigeonholeTemplateError("Невалидный результат")
 return GeneratedPigeonholeProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s)
def _three(t,r,s):
 removed_pencils=r.randint(5,25); guarantee=removed_pencils; max_pencils=removed_pencils+guarantee-2; answer=max_pencils+1; removed_pens=r.randint(5,25); first_guarantee=removed_pens+r.randint(1,5); pen_count=removed_pens+first_guarantee-2
 text=f"В пенале есть ручки, карандаши и фломастеры. Если убрать {removed_pens} ручек, среди любых {first_guarantee} оставшихся есть карандаш. Если убрать {removed_pencils} карандашей, среди любых {guarantee} оставшихся есть ручка. После удаления всех ручек сколько предметов нужно вынуть, чтобы гарантировать фломастер?"
 return _make(t,text,answer,{"removed_pencils":removed_pencils,"second_guarantee":guarantee,"pencil_count":max_pencils,"marker_count":1,"removed_pens":removed_pens,"first_guarantee":first_guarantee,"pen_count":pen_count},s)
def _inventory(t,r,s):
 red=r.randint(8,25); blue=red-1; no_white=red+blue-4; answer=inventory_total(red,blue,no_white); text=f"В мешке есть белые, красные и синие карандаши. Среди любых {red} есть красный, среди любых {blue} есть синий, и можно вынуть {no_white} без белого. Сколько карандашей может быть в мешке?";return _make(t,text,answer,{"red_guarantee_draw":red,"blue_guarantee_draw":blue,"no_white_draw":no_white},s)
def _target(t,r,s):
 other=r.randint(4,40); target=r.randint(4,40); required=r.randint(2,min(8,target)); answer=guarantee_target(other,required); text=f"В коробке {other} белых и {target} чёрных шариков. Какое минимальное число шариков нужно достать, чтобы гарантированно получить {required} чёрных?";return _make(t,text,answer,{"other_count":other,"target_count":target,"required_target":required},s)
STRATEGIES:dict[str,Callable]={"three_category_guarantee":_three,"inventory_reconstruction":_inventory,"target_count_draws":_target}
def generate_pigeonhole_problem(template_id,*,seed=None,rng=None):
 t=get_template(template_id);q=rng or random.Random(seed if seed is not None else datetime.now().timestamp());fails=[]
 for _ in range(MAX_ATTEMPTS):
  try:return STRATEGIES[t["generation_strategy"]](t,q,seed)
  except (ValueError,PigeonholeTemplateError) as e:fails.append(str(e))
 raise PigeonholeTemplateError(f"Не удалось сгенерировать template={template_id}, seed={seed}: {fails[-1:]}")
def generate_pigeonhole_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise PigeonholeTemplateError(f"Неизвестный модуль {module_id}")
 return generate_pigeonhole_problem(rng.choice(load_pigeonhole_templates())["id"],rng=rng)
def pigeonhole_template_metadata():
 ts=load_pigeonhole_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Pigeonhole Principle and Guaranteed Selection","display_name":"Принцип Дирихле и гарантированный выбор","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Принцип Дирихле и гарантированный выбор","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
