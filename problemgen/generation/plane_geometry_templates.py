"""Детерминированный генератор модуля «Планиметрия: прямоугольники, квадраты и площади»."""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from math import isqrt
from pathlib import Path
from typing import Any, Callable
from problemgen.russian.agreement import count_phrase_ru

ROOT = Path(__file__).resolve().parents[2]
MODULE_ID = "plane_geometry_rectangles_squares_and_areas"
PATH = ROOT / "data" / "templates" / "problem_sets" / MODULE_ID / "templates.json"
MANIFEST = PATH.with_name("source_accounting.json")
SOURCES = (ROOT / "docs" / "24_planimetriya_pryamougolniki_kvadraty_i_ploshchadi_bez_imen_i_personazhey_deduplicated.md", ROOT / "docs" / "24_planimetriya_pryamougolniki_kvadraty_i_ploshchadi_s_imenami_i_personazhami_deduplicated.md")
SOURCE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")

class PlaneGeometryTemplateError(ValueError): pass

@dataclass(frozen=True)
class GeneratedPlaneGeometryProblem:
    module: str; template_id: str; source_problem_numbers: list[int]; problem_text: str; answer: int; answer_text: str; parameters: dict[str, Any]; seed: int | None = None

@lru_cache(maxsize=4)
def _load(path: str, stamp: int) -> dict[str, Any]:
    del stamp
    return json.loads(Path(path).read_text(encoding="utf-8"))

def source_problem_numbers() -> set[int]:
    return {int(match.group(1)) for source in SOURCES for line in source.read_text(encoding="utf-8").splitlines() if (match := SOURCE_RE.match(line))}

def load_source_accounting() -> dict[str, Any]: return _load(str(MANIFEST), MANIFEST.stat().st_mtime_ns)

def load_plane_geometry_templates() -> list[dict[str, Any]]:
    templates = _load(str(PATH), PATH.stat().st_mtime_ns)["templates"]
    records = load_source_accounting()["records"]
    numbers = [record["source_problem_number"] for record in records]
    active = {number: template["id"] for template in templates for number in template["source_problem_numbers"]}
    mapped = {record["source_problem_number"]: record["template_id"] for record in records if record["status"] == "active_template"}
    if len(numbers) != 75 or len(numbers) != len(set(numbers)) or set(numbers) != source_problem_numbers() or active != mapped:
        raise PlaneGeometryTemplateError("Некорректный source-accounting manifest модуля 24.")
    if len({template["id"] for template in templates}) != len(templates): raise PlaneGeometryTemplateError("Идентификаторы шаблонов должны быть уникальны.")
    return list(templates)

def _build(t: dict[str, Any], text: str, answer: int, values: dict[str, Any], seed: int | None) -> GeneratedPlaneGeometryProblem:
    if not isinstance(answer, int) or "{" in text or "}" in text: raise PlaneGeometryTemplateError(f"{t['id']} seed={seed}: неверный ответ или незаполненный параметр.")
    return GeneratedPlaneGeometryProblem(MODULE_ID, t["id"], t["source_problem_numbers"], text, answer, str(answer), values, seed)

def _cut(t,r,s):
    width=r.randint(8,40); height=2*r.randint(3,20); perimeter=2*(width+height); vertical_sum=perimeter+2*height; answer=2*width+height
    if (vertical_sum-perimeter)%2: raise PlaneGeometryTemplateError(f"{t['id']} seed={s}: деление нецелое.")
    return _build(t,f"Периметр прямоугольника равен {perimeter} см. После вертикального разреза сумма периметров частей равна {vertical_sum} см. Найдите периметр каждой части при горизонтальном разрезе пополам.",answer,{"perimeter":perimeter,"vertical_cut_perimeter_sum":vertical_sum},s)
def _square_area(t,r,s):
    side=r.randint(3,30); p=4*side; return _build(t,f"Найдите площадь квадрата, если его периметр равен {p} см.",side*side,{"perimeter_cm":p},s)
def _sub_perimeter(t,r,s):
    n=r.choice((2,3,4)); small=r.randint(2,20); small_area=small*small; return _build(t,f"Квадрат сложен из {n*n} одинаковых квадратов площадью {small_area} см² каждый. Чему равен периметр большого квадрата?",4*n*small,{"grid_side":n,"small_square_area":small_area},s)
def _sub_area(t,r,s):
    n=r.choice((3,4)); small=r.randint(2,15); p=4*small; return _build(t,f"Квадрат сложен из {n*n} одинаковых квадратов периметром {p} см каждый. Чему равна площадь большого квадрата?",(n*small)**2,{"grid_side":n,"small_square_perimeter":p},s)
def _rectangle_area(t,r,s):
    a=r.randint(3,30); b=r.randint(3,30); return _build(t,f"Площадь прямоугольника равна {a*b} см², а одна сторона равна {a} см. Найдите его периметр.",2*(a+b),{"area":a*b,"known_side":a},s)
def _grid(t,r,s):
    w=r.randint(2,80); h=r.randint(2,80); return _build(t,f"Сколько внутренних перегородок в клетчатом прямоугольнике {w} × {h}?",2*w*h-w-h,{"width_cells":w,"height_cells":h},s)
def _square_factor(t,r,s):
    n=r.choice((72,128,200,288,392)); candidates=[a+n//a for a in range(1,n+1) if n%a==0 and (isqrt(a)**2==a or isqrt(n//a)**2==n//a)]; return _build(t,f"Число {n} представляют произведением двух целых сомножителей, один из которых — полный квадрат. Найдите минимальную сумму сомножителей.",min(candidates),{"number":n},s)
def _growth(t,r,s):
    side=r.randint(2,40); increase=2*side+1; return _build(t,f"Если сторону квадрата увеличить на 1 см, его площадь увеличится на {increase} см². Найдите исходную сторону квадрата.",side,{"area_increase":increase},s)
def _long(t,r,s):
    w=r.randint(7,25); h=r.randint(7,25)
    long=lambda a,b:max(a,b)>2*min(a,b)
    answer=sum(long(x,h) and long(w-x,h) for x in range(1,w))+sum(long(w,y) and long(w,h-y) for y in range(1,h))
    return _build(t,f"Прямоугольник {w} × {h} разрезают по линиям клеток на два прямоугольника. Прямоугольник длинный, если одна сторона больше удвоенной другой. Сколькими способами оба полученных прямоугольника будут длинными?",answer,{"width":w,"height":h},s)
def _material(t,r,s):
    w=r.randint(10,50); h=r.randint(10,50); density=r.randint(1,8); weight=w*h*density; target=r.randint(1,10)*10000; answer=density*target
    return _build(t,f"Лист материала размерами {w} см × {h} см весит {weight} г. Сколько граммов весят {target//10000} м² такого материала?",answer,{"sheet_width_cm":w,"sheet_height_cm":h,"sheet_weight_g":weight,"target_area_cm2":target},s)
def _carpets(t,r,s):
    overlap_side=r.randint(2,8); small_side=r.randint(overlap_side+1,15); room=3*small_side-overlap_side; opposite=overlap_side**2; adjacent=small_side*overlap_side
    return _build(t,f"В квадратной комнате лежат два квадратных ковра; сторона одного вдвое больше стороны другого. При размещении в противоположных углах площадь двойного покрытия равна {opposite} м², а в соседних углах — {adjacent} м². Чему равна сторона комнаты?",room,{"opposite_overlap":opposite,"adjacent_overlap":adjacent},s)
def _holes(t,r,s):
    w=r.randint(30,100); h=r.randint(30,100); hole=r.randint(2,8); count=r.randint(1,3); full=2*w*h-w-h; removed=count*(2*hole*hole+2*hole); answer=full-removed
    holes = count_phrase_ru(count, ("непересекающуюся квадратную дырку", "непересекающиеся квадратные дырки", "непересекающихся квадратных дырок"))
    return _build(t,f"Из клетчатого прямоугольника {w} × {h} вырезали {holes} {hole} × {hole}. Сколько внутренних перегородок осталось?",answer,{"width_cells":w,"height_cells":h,"hole_side":hole,"hole_count":count},s)
def _equation(t,r,s):
    multiplier=r.choice((4,9,16)); divisor=r.choice((4,9,16)); x=divisor*r.randint(2,15); result=multiplier*x*x//divisor
    if multiplier*x*x%divisor: raise PlaneGeometryTemplateError(f"{t['id']} seed={s}: нецелое деление.")
    return _build(t,f"Задумали натуральное число, его квадрат умножили на {multiplier}, а результат разделили на {divisor}. Получили {result}. Какое число задумали?",x,{"multiplier":multiplier,"divisor":divisor,"result":result},s)
def _equal_perimeter(t,r,s):
    a=r.randint(3,30); b=a+2*r.randint(1,15); side=(a+b)//2
    return _build(t,f"Стороны прямоугольника равны {a} см и {b} см. Найдите сторону квадрата того же периметра.",side,{"first_side":a,"second_side":b},s)
def _area_units(t,r,s):
    length=r.randint(5,40); width=r.randint(2,30); area_dm2=length*width*100
    return _build(t,f"Длина прямоугольника равна {length} м, а площадь — {area_dm2} дм². Найдите ширину в метрах.",width,{"length_m":length,"area_dm2":area_dm2},s)
def _unit(t,r,s):
    feet=r.randint(1,20); return _build(t,f"В одном футе 12 дюймов. Сколько квадратных дюймов в {feet} квадратных футах?",feet*144,{"square_feet":feet,"inches_per_foot":12},s)
def _frame(t,r,s):
    inner=r.randint(3,30); frame=r.randint(1,8); p=4*inner; return _build(t,f"Квадратная рамка шириной {frame} см окружает квадратную картину с периметром {p} см. Найдите площадь картины вместе с рамкой.",(inner+2*frame)**2,{"inner_perimeter":p,"frame_width":frame},s)
def _three(t,r,s):
    side=r.randint(2,40); return _build(t,f"Из трёх одинаковых квадратов со стороной {side} см составили прямоугольник. Найдите его площадь.",3*side*side,{"small_square_side":side},s)

STRATEGIES: dict[str, Callable[[dict[str, Any], random.Random, int | None], GeneratedPlaneGeometryProblem]]={"cut_perimeters":_cut,"square_area":_square_area,"subdivision_perimeter":_sub_perimeter,"subdivision_area":_sub_area,"rectangle_area_perimeter":_rectangle_area,"grid_partitions":_grid,"square_factor_minimum":_square_factor,"square_growth":_growth,"long_rectangle_cuts":_long,"material_density":_material,"overlapping_carpets":_carpets,"grid_holes":_holes,"square_equation":_equation,"equal_perimeter_square":_equal_perimeter,"rectangle_area_units":_area_units,"square_unit_conversion":_unit,"square_frame":_frame,"three_squares_rectangle":_three}
def generate_plane_geometry_problem(template_id: str, *, seed: int|None=None, rng: random.Random|None=None) -> GeneratedPlaneGeometryProblem:
    templates={t["id"]:t for t in load_plane_geometry_templates()}
    if template_id not in templates: raise PlaneGeometryTemplateError(f"Неизвестный шаблон модуля 24: {template_id}.")
    t=templates[template_id]; return STRATEGIES[t["generation_strategy"]](t,rng or random.Random(seed),seed)
def generate_plane_geometry_problem_from_module(module_id: str, *, rng: random.Random) -> GeneratedPlaneGeometryProblem:
    if module_id!=MODULE_ID: raise PlaneGeometryTemplateError(f"Ожидался модуль {MODULE_ID}, получен {module_id}.")
    t=rng.choice(load_plane_geometry_templates()); return generate_plane_geometry_problem(t["id"],rng=rng)
def plane_geometry_template_metadata() -> dict[str, Any]:
    ts=load_plane_geometry_templates(); return {"modules":[{"module_id":MODULE_ID,"title":"Plane Geometry: Rectangles, Squares and Areas","display_name":"Планиметрия: прямоугольники, квадраты и площади","template_count":len(ts)}],"templates":[{"template_id":t["id"],"title":t["id"],"display_name":t["id"],"module_name":"Планиметрия: прямоугольники, квадраты и площади","source_problem_numbers":t["source_problem_numbers"],"problem_type":t["generation_strategy"]} for t in ts],"stats":{"total_modules":1,"total_templates":len(ts),"covered_source_problem_numbers":len(source_problem_numbers())}}
