"""Генератор точных клетчатых задач модуля 25."""
from __future__ import annotations
import json,random,re
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MODULE_ID='grid_figures_cuts_and_routes';PATH=ROOT/'data/templates/problem_sets'/MODULE_ID/'templates.json';MANIFEST=PATH.with_name('source_accounting.json');SOURCES=(ROOT/'docs/25_kletchatye_figury_razrezaniya_i_marshruty_bez_imen_i_personazhey_deduplicated.md',ROOT/'docs/25_kletchatye_figury_razrezaniya_i_marshruty_s_imenami_i_personazhami_deduplicated.md');RX=re.compile(r'^(\d+)\.')
class GridTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedGridProblem: module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict;seed:int|None=None
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding='utf8'))
def source_problem_numbers():return {int(m.group(1)) for p in SOURCES for x in p.read_text(encoding='utf8').splitlines() if(m:=RX.match(x))}
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_grid_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)['templates'];rs=load_source_accounting()['records'];n=[r['source_problem_number'] for r in rs];a={n:t['id'] for t in ts for n in t['source_problem_numbers']};m={r['source_problem_number']:r['template_id'] for r in rs if r['status']=='active_template'}
 if len(n)!=31 or len(n)!=len(set(n)) or set(n)!=source_problem_numbers() or a!=m:raise GridTemplateError('Некорректный manifest модуля 25.')
 return list(ts)
def _b(t,text,a,v,s):return GeneratedGridProblem(MODULE_ID,t['id'],t['source_problem_numbers'],text,a,str(a),v,s)
def _parts(w,h):return 2*w*h-w-h
def _holes(t,r,s):
 w=r.randint(30,100);h=r.randint(30,100);q=r.choice((3,5,7));a=_parts(w,h)-(2*q*q+2*q);return _b(t,f'В клетчатом прямоугольнике {w} × {h} в центре вырезали квадратную дырку {q} × {q}. Сколько внутренних перегородок осталось?',a,{'width':w,'height':h,'hole_side':q},s)
def _squares(t,r,s):
 w=r.randint(3,20);h=r.randint(3,20);a=sum((w-k+1)*(h-k+1) for k in range(1,min(w,h)+1));return _b(t,f'На клетчатом листе нарисован прямоугольник {w} × {h}. Сколько квадратов всех возможных размеров на нём изображено?',a,{'width':w,'height':h},s)
def _p(t,r,s):
 w=r.randint(8,40);h=r.randint(8,40);q=r.randint(1,min(w//2,h//2));a=w*q+2*q*(h-q);return _b(t,f'Клетчатая буква П имеет ширину {w}, высоту {h} и толщину ножек и перекладины {q}. Сколько клеток она содержит?',a,{'width':w,'height':h,'thickness':q},s)
def _inverse(t,r,s):
 n=r.randint(30,150);q=r.choice((2,3));c=r.randint(2,6);total=_parts(n,n)-c*(2*q*q+2*q);return _b(t,f'Из клетчатого квадрата вырезали {c} непересекающихся квадратных дырки {q} × {q}. После этого осталось {total} внутренних перегородок. Чему равна сторона исходного квадрата?',n,{'hole_count':c,'hole_side':q,'remaining_partitions':total},s)
def _bfs(n,aw,ah):
 x0=(n-aw)//2;y0=(n-ah)//2;blocked={(x,y) for x in range(x0,x0+aw) for y in range(y0,y0+ah)};q=deque([((0,0),0)]);seen={(0,0)}
 while q:
  (x,y),d=q.popleft()
  if(x,y)==(n-1,n-1):return d
  for dx in(-1,0,1):
   for dy in(-1,0,1):
    z=(x+dx,y+dy)
    if (dx or dy) and 0<=z[0]<n and 0<=z[1]<n and z not in blocked and z not in seen:seen.add(z);q.append((z,d+1))
 raise GridTemplateError('Маршрут не найден.')
def _beetle(t,r,s):
 n=r.choice((21,25,29,33));a=r.choice((3,5,7));b=r.choice((3,5,7));ans=_bfs(n,a,b);return _b(t,f'В углу клетчатого квадрата {n} × {n} живёт жук, а в противоположном углу — школа. Жук ходит в соседнюю по стороне или вершине клетку. Центральный прямоугольник аварии имеет размер {a} × {b}. Сколько шагов нужно жуку до школы?',ans,{'grid_side':n,'accident_width':a,'accident_height':b},s)
STRATEGIES={'holes':_holes,'squares':_squares,'letter_p':_p,'inverse_holes':_inverse,'beetle_route':_beetle}
def generate_grid_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_grid_templates()};
 if template_id not in ts:raise GridTemplateError(f'Неизвестный шаблон модуля 25: {template_id}.')
 return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_grid_problem_from_module(module_id,*,rng):
 if module_id!=MODULE_ID:raise GridTemplateError(f'Ожидался модуль {MODULE_ID}.')
 return generate_grid_problem(rng.choice(load_grid_templates())['id'],rng=rng)
def grid_template_metadata():
 ts=load_grid_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Grid Figures, Cuts and Routes','display_name':'Клетчатые фигуры, разрезания и маршруты','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Клетчатые фигуры, разрезания и маршруты','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']}for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':len(source_problem_numbers())}}
