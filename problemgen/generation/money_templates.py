"""Детерминированный генератор модуля «Деньги, покупки, цены и расчёты»."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import load_approved_characters
from problemgen.russian.agreement import count_with_word_ru
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="money_purchases_prices_and_calculations";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"20_dengi_pokupki_tseny_i_raschety_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"20_dengi_pokupki_tseny_i_raschety_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class MoneyTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedMoneyProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf8").splitlines() if(m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_money_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs];active={n:t["id"] for t in ts for n in t["source_problem_numbers"]};mapped={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}
 if len(ns)!=42 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers() or active!=mapped:raise MoneyTemplateError("Некорректный каталог или manifest")
 return list(ts)
def _chars(r,n):u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise MoneyTemplateError(f"Невалидный template={t['id']}, seed={s}")
 return GeneratedMoneyProblem(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _piece(t,r,s):
 need=r.randint(20,200);length=r.choice([200,250,300,400]);parts=(need+length-1)//length;text=f"Для работы нужно {need} см материала. В магазине продают отрезки по {length} см. Сколько отрезков нужно купить?";return _make(t,text,parts,{"needed_cm":need,"piece_cm":length},s)
def _discount(t,r,s):
 pct=r.choice([10,20,25,50]);answer=r.choice([100,200,300,400,500,600]);price=answer*100//(100-pct);text=f"Цена товара — {count_with_word_ru(price,('рубль','рубля','рублей'))}. Скидка {pct}%. Сколько рублей стоит товар после скидки?";return _make(t,text,answer,{"price":price,"discount_percent":pct},s)
def _change(t,r,s):
 u,cs=_chars(r,1);price=r.randint(20,300);payment=price+r.randint(1,200);name=cs[0].name;text=f"{name} купил товар за {count_with_word_ru(price,('рубль','рубля','рублей'))} и дал {count_with_word_ru(payment,('рубль','рубля','рублей'))}. Сколько рублей сдачи должен получить {name}?";return _make(t,text,payment-price,{"price":price,"payment":payment,"role_mapping":{"buyer":name}},s,u,cs)
def _split(t,r,s):
 u,cs=_chars(r,2);share=r.randint(20,300);total=share*2;paid=r.randint(0,total);answer=share-paid;a,b=cs;text=f"{a.name} и {b.name} делят счёт в {count_with_word_ru(total,('рубль','рубля','рублей'))} поровну. Одним из участников уже внесено {count_with_word_ru(paid,('рубль','рубля','рублей'))}. Сколько рублей осталось внести этому участнику до равной доли?";return _make(t,text,answer,{"total":total,"paid":paid,"role_mapping":{"first":a.name,"second":b.name}},s,u,cs)
STRATEGIES={"piece_purchase":_piece,"discount_price":_discount,"change":_change,"split_bill":_split}
def generate_money_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_money_templates()}
 if template_id not in ts:raise MoneyTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_money_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise MoneyTemplateError(f"Неизвестный модуль {module_id}")
 return generate_money_problem(rng.choice(load_money_templates())['id'],rng=rng)
def money_template_metadata():
 ts=load_money_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Money, Purchases, Prices and Calculations","display_name":"Деньги, покупки, цены и расчёты","template_count":len(ts)}],"templates":[{"template_id":t['id'],"title":t['id'],"display_name":t['id'],"module_name":"Деньги, покупки, цены и расчёты","source_problem_numbers":t['source_problem_numbers'],"problem_type":t['generation_strategy']} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
