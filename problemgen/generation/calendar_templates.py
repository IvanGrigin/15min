"""Детерминированный генератор задач модуля «Календарь и дни недели»."""
from __future__ import annotations
import calendar,json,math,random,re
from dataclasses import dataclass
from datetime import date,timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
from problemgen.generation.comparison_templates import Character,load_approved_characters
from problemgen.russian.agreement import count_with_word_ru
ROOT=Path(__file__).resolve().parents[2];MODULE_ID="calendar_and_weekdays";PATH=ROOT/"data"/"templates"/"problem_sets"/MODULE_ID/"templates.json";MANIFEST=PATH.with_name("source_accounting.json");SOURCES=(ROOT/"Docs"/"15_kalendar_i_dni_nedeli_bez_imen_i_personazhey_deduplicated.md",ROOT/"Docs"/"15_kalendar_i_dni_nedeli_s_imenami_i_personazhami_deduplicated.md");RX=re.compile(r"^\s*(\d+)\.\s+.+$")
class CalendarTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedCalendarProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict[str,Any];seed:int|None=None;universe:str|None=None;characters:list[str]|None=None
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding="utf-8").splitlines() if (m:=RX.match(x))}
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding="utf-8"))
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_calendar_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)["templates"];rs=load_source_accounting()["records"];ns=[r["source_problem_number"] for r in rs]
 if len({t["id"] for t in ts})!=len(ts) or len(ns)!=55 or len(ns)!=len(set(ns)) or set(ns)!=source_problem_numbers():raise CalendarTemplateError("Некорректный каталог или source accounting")
 if {n:t["id"] for t in ts for n in t["source_problem_numbers"]}!={r["source_problem_number"]:r["template_id"] for r in rs if r["status"]=="active_template"}:raise CalendarTemplateError("Manifest не согласован")
 return list(ts)
def weekday_code(d:date)->int:return d.isoweekday()
def nth_weekday(year,month,weekday,n):
 first=date(year,month,1);offset=(weekday-first.weekday())%7;result=first+timedelta(days=offset+7*(n-1))
 if result.month!=month:raise CalendarTemplateError("Такого дня недели нет в месяце")
 return result
def max_digit_sum_number(lo,hi):
 if lo>hi or hi-lo>20000:raise CalendarTemplateError("Некорректный диапазон")
 return max(range(lo,hi+1),key=lambda n:(sum(map(int,str(n))),n))
def palindromic_dates(year_start,year_end):
 return sum(f"{d.day:02d}{d.month:02d}{d.year:04d}"==f"{d.day:02d}{d.month:02d}{d.year:04d}"[::-1] for y in range(year_start,year_end+1) for m in range(1,13) for day in range(1,calendar.monthrange(y,m)[1]+1) if (d:=date(y,m,day)))
def _chars(r,n):
 u,cs=r.choice(list(load_approved_characters().items()));return u,r.sample(cs,n)
def _make(t,text,a,p,s,u=None,cs=None):
 if not isinstance(a,int) or "{" in text:raise CalendarTemplateError("Невалидный результат")
 return GeneratedCalendarProblem(MODULE_ID,t["id"],t["source_problem_numbers"],text,a,str(a),p,s,u,[c.name for c in cs] if cs else None)
def _weekday(t,r,s):
 start=date(r.randint(2020,2035),r.randint(1,12),r.randint(1,28));delta=r.randint(1,5000);target=start+timedelta(days=delta);text=f"Сегодня {start.strftime('%d.%m.%Y')}. Укажите ISO-код дня недели (понедельник=1, воскресенье=7) через {count_with_word_ru(delta,('день','дня','дней'))}.";return _make(t,text,weekday_code(target),{"start_date":start.isoformat(),"offset_days":delta},s)
def _conditional(t,r,s):
 # В 31-дневном месяце первые три weekday встречаются по 5 раз; выбираем условие, которое истинно.
 for _ in range(100):
  y=r.randint(2020,2035);m=r.choice([1,3,5,7,8,10,12]);first=date(y,m,1).weekday();more=(first+r.randint(0,2))%7;less=(more+3)%7
  if ((more-first)%7)<3 and ((less-first)%7)>=3:break
 target_month=1 if m==12 else m+1;target_year=y+1 if m==12 else y;weekday=r.randint(0,6);ordinal=r.randint(1,4);answer=nth_weekday(target_year,target_month,weekday,ordinal).day
 text=f"В {m}-м месяце {y} года дней с ISO-кодом {more+1} было больше, чем с кодом {less+1}. Какого числа в следующем месяце будет {ordinal}-й день с ISO-кодом {weekday+1}?";return _make(t,text,answer,{"year":y,"condition_month":m,"more_weekday_code":more+1,"less_weekday_code":less+1,"target_month":target_month,"target_weekday_code":weekday+1,"ordinal":ordinal},s)
def _digits(t,r,s):
 lo=r.randint(1000,90000);hi=lo+r.randint(100,10000);answer=max_digit_sum_number(lo,hi);text=f"Какое число от {lo} до {hi} имеет наибольшую сумму цифр? Если таких несколько, укажите наибольшее.";return _make(t,text,answer,{"lower_bound":lo,"upper_bound":hi},s)
def _tram(t,r,s):
 route=r.choice([60,72,90,120]);old=r.choice([x for x in range(4,20) if route%x==0]);new=r.choice([x for x in range(4,20) if route%x==0 and x!=old]);answer=route//new;text=f"По круговому маршруту длиной {count_with_word_ru(route,('минута','минуты','минут'))} ходят {count_with_word_ru(old,('трамвай','трамвая','трамваев'))} с равными интервалами. После изменения их стало {count_with_word_ru(new,('трамвай','трамвая','трамваев'))}. Каков новый интервал в минутах?";return _make(t,text,answer,{"route_period":route,"old_trams":old,"new_trams":new},s)
def _date_day(t,r,s):
 start=date(r.randint(2020,2035),r.randint(1,12),r.randint(1,28));hours=r.choice([None,r.randint(24,1000)]);days=r.randint(1,4000) if hours is None else None;target=start+(timedelta(days=days) if days is not None else timedelta(hours=hours));word=f"через {count_with_word_ru(days,('день','дня','дней'))}" if days is not None else f"через {count_with_word_ru(hours,('час','часа','часов'))}";text=f"Сегодня {start.strftime('%d.%m.%Y')}. Какое число месяца будет {word}?";return _make(t,text,target.day,{"start_date":start.isoformat(),"offset_days":days,"offset_hours":hours},s)
def _vacation(t,r,s):
 y=r.randint(2020,2035);start=date(y,r.randint(1,10),r.randint(1,20));length=r.randint(10,50);end=start+timedelta(days=length-1);text=f"Отпуск начался {start.strftime('%d.%m')} и закончился {end.strftime('%d.%m')} включительно. Сколько календарных дней длился отпуск?";return _make(t,text,length,{"start_date":start.isoformat(),"end_date":end.isoformat()},s)
def _pal(t,r,s):
 start=r.choice([2000,2100,2200]);end=start+99;answer=palindromic_dates(start,end);text=f"Сколько дат-палиндромов в формате ДДММГГГГ приходится на годы {start}–{end}?";return _make(t,text,answer,{"start_year":start,"end_year":end},s)
def _lcm(t,r,s):
 u,cs=_chars(r,3);periods=[r.randint(2,12),r.randint(3,18),r.randint(4,20)];answer=math.lcm(*periods);names=", ".join(c.name for c in cs);text=f"{names} сегодня встретились. Они приходят в библиотеку каждые {count_with_word_ru(periods[0],('день','дня','дней'))}, {count_with_word_ru(periods[1],('день','дня','дней'))} и {count_with_word_ru(periods[2],('день','дня','дней'))} соответственно. Через сколько дней они встретятся снова?";return _make(t,text,answer,{"periods":periods,"role_mapping":{"friends":[c.name for c in cs]}},s,u,cs)
def _music(t,r,s):
 u,cs=_chars(r,1);year=r.randint(2020,2035);month=r.randint(1,12);d1=date(year,month,r.randint(1,5));d2=d1+timedelta(days=r.choice([1,2,3,4,5,6])+7*r.randint(1,2));cut=d1+timedelta(days=r.randint(1,(d2-d1).days-1));schedule={d1.weekday(),d2.weekday()};last=max(d1+timedelta(days=i) for i in range((cut-d1).days) if (d1+timedelta(days=i)).weekday() in schedule);name=cs[0].name;text=f"{name} занимается музыкой в два фиксированных дня недели. В {month}-м месяце {year} года занятия были {d1.day}-го и {d2.day}-го числа. Какого числа было последнее занятие до {cut.day}-го?";return _make(t,text,last.day,{"year":year,"month":month,"observed_days":[d1.day,d2.day],"cutoff_day":cut.day,"role_mapping":{"student":name}},s,u,cs)
def _breaks(t,r,s):
 u,cs=_chars(r,1);lessons=r.randint(4,8);lesson=45;short=r.randint(5,20);big=r.randint(20,45);total=lessons*lesson+(lessons-2)*short+big;after=r.randint(120,360);start_minutes=r.randint(480,600);leave=start_minutes+total+after;name=cs[0].name;text=f"{name} посещает {count_with_word_ru(lessons,('урок','урока','уроков'))} по {count_with_word_ru(lesson,('минута','минуты','минут'))}. Между ними одна большая перемена {count_with_word_ru(big,('минута','минуты','минут'))}, остальные одинаковы. От начала первого урока до ухода проходит {count_with_word_ru(total+after,('минута','минуты','минут'))}, после последнего урока — ещё {count_with_word_ru(after,('минута','минуты','минут'))}. Сколько длится короткая перемена?";return _make(t,text,short,{"lesson_count":lessons,"lesson_minutes":lesson,"big_break":big,"after_last":after,"total_until_leave":total+after,"role_mapping":{"student":name}},s,u,cs)
STRATEGIES={"weekday_code_offset":_weekday,"conditional_nth_weekday":_conditional,"max_digit_sum_range":_digits,"circular_tram_interval":_tram,"date_offset_day":_date_day,"vacation_days":_vacation,"palindromic_dates":_pal,"lcm_schedule":_lcm,"two_weekday_schedule":_music,"school_breaks":_breaks}
def generate_calendar_problem(template_id,*,seed=None,rng=None):
 ts={t["id"]:t for t in load_calendar_templates()}
 if template_id not in ts:raise CalendarTemplateError(f"Неизвестный template={template_id}, seed={seed}")
 return STRATEGIES[ts[template_id]["generation_strategy"]](ts[template_id],rng or random.Random(seed),seed)
def generate_calendar_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise CalendarTemplateError(f"Неизвестный модуль {module_id}")
 return generate_calendar_problem(rng.choice(load_calendar_templates())["id"],rng=rng)
def calendar_template_metadata():
 ts=load_calendar_templates();return {"modules":[{"module_id":MODULE_ID,"title":"Calendar and Weekdays","display_name":"Календарь и дни недели","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Календарь и дни недели","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
