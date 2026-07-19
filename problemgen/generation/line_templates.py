"""Точные задачи о точках и отрезках модуля 27."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from math import gcd
ROOT=Path(__file__).resolve().parents[2];MODULE_ID='points_segments_and_positions_on_a_line';PATH=ROOT/'data/templates/problem_sets'/MODULE_ID/'templates.json';MANIFEST=PATH.with_name('source_accounting.json');SOURCES=tuple(ROOT/p for p in('docs/27_tochki_otrezki_i_raspolozhenie_na_pryamoy_bez_imen_i_personazhey_deduplicated.md','docs/27_tochki_otrezki_i_raspolozhenie_na_pryamoy_s_imenami_i_personazhami_deduplicated.md'));RX=re.compile(r'^(\d+)\.')
class LineTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedLineProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict;seed:int|None=None
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding='utf8'))
def source_problem_numbers():return {int(m.group(1))for p in SOURCES for x in p.read_text(encoding='utf8').splitlines()if(m:=RX.match(x))}
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_line_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)['templates'];rs=load_source_accounting()['records'];n=[x['source_problem_number']for x in rs];a={z:t['id']for t in ts for z in t['source_problem_numbers']};m={x['source_problem_number']:x['template_id']for x in rs if x['status']=='active_template'}
 if len(n)!=15 or len(n)!=len(set(n))or set(n)!=source_problem_numbers()or a!=m:raise LineTemplateError('Некорректный manifest модуля 27.')
 return list(ts)
def _b(t,x,a,v,s):return GeneratedLineProblem(MODULE_ID,t['id'],t['source_problem_numbers'],x,a,str(a),v,s)
def _ordered(t,r,s):
 ab=r.randint(5,50);bc=r.randint(5,50);cd=r.randint(5,50);de=r.randint(5,50);ce=cd+de
 # AC=BD => AB+BC=BC+CD, so choose CD=AB and ask DE.
 cd=ab;ce=cd+de
 return _b(t,f'На прямой точки A, B, C, D, E расположены именно в таком порядке. AB = {ab} см, CE = {ce} см, AC = BD. Найдите DE.',de,{'ab':ab,'ce':ce},s)
def _alt(t,r,s):
 n=r.randint(20,200);a=r.randint(1,9);b=r.randint(1,9);d=sum(a if i%2==0 else b for i in range(n-1));return _b(t,f'На прямой отмечено {n} точек; расстояния между соседними чередуются: {a} см, {b} см. Найдите расстояние между крайними точками.',d,{'point_count':n,'first_gap':a,'second_gap':b},s)
def _fib(t,r,s):
 n=r.randint(8,20);f=[1,1]
 while len(f)<n-1:f.append(f[-1]+f[-2])
 return _b(t,f'На прямой отмечено {n} точек, расстояния между соседними равны 1, 1, 2, 3, 5 и далее по Фибоначчи. Найдите расстояние между крайними точками.',sum(f),{'point_count':n},s)
def _step(t,r,s):
 n=r.randint(20,300);step=r.randint(2,30);marked=n//gcd(n,step);return _b(t,f'Вершины {n}-угольника отмечают через {step} вершин, начиная с первой, пока не вернутся в уже отмеченную. Сколько вершин останутся неотмеченными?',n-marked,{'vertex_count':n,'step':step},s)
def _equal(t,r,s):
 n=r.randint(4,500);gap=r.randint(1,20);return _b(t,f'На прямой отмечено {n} точек, расстояние между соседними равно {gap} см. Найдите расстояние между крайними точками.',(n-1)*gap,{'point_count':n,'gap':gap},s)
def _tri(t,r,s):
 n=r.randint(4,100);return _b(t,f'Одну вершину выпуклого {n}-угольника соединили диагоналями со всеми не соседними вершинами. На сколько треугольников он разделился?',n-2,{'vertex_count':n},s)
STRATEGIES={'ordered':_ordered,'alternating':_alt,'fibonacci':_fib,'polygon_step':_step,'equal_gaps':_equal,'polygon_triangles':_tri}
def generate_line_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_line_templates()};return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_line_problem_from_module(module_id,*,rng):return generate_line_problem(rng.choice(load_line_templates())['id'],rng=rng)
def line_template_metadata():
 ts=load_line_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Points, Segments and Positions on a Line','display_name':'Точки, отрезки и расположение на прямой','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Точки, отрезки и расположение на прямой','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']}for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':len(source_problem_numbers())}}
