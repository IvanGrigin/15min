"""Точные задачи модуля 26 о кубах и объёмах."""
from __future__ import annotations
import json,random,re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];MODULE_ID='cubes_volume_and_spatial_geometry';PATH=ROOT/'data/templates/problem_sets'/MODULE_ID/'templates.json';MANIFEST=PATH.with_name('source_accounting.json');SOURCES=tuple(ROOT/p for p in ('docs/26_kuby_obem_i_prostranstvennaya_geometriya_bez_imen_i_personazhey_deduplicated.md','docs/26_kuby_obem_i_prostranstvennaya_geometriya_s_imenami_i_personazhami_deduplicated.md'));RX=re.compile(r'^(\d+)\.')
class CubeTemplateError(ValueError):pass
@dataclass(frozen=True)
class GeneratedCubeProblem:module:str;template_id:str;source_problem_numbers:list[int];problem_text:str;answer:int;answer_text:str;parameters:dict;seed:int|None=None
@lru_cache(maxsize=4)
def _load(p,s):del s;return json.loads(Path(p).read_text(encoding='utf8'))
def source_problem_numbers():return {int(m.group(1))for p in SOURCES for x in p.read_text(encoding='utf8').splitlines()if(m:=RX.match(x))}
def load_source_accounting():return _load(str(MANIFEST),MANIFEST.stat().st_mtime_ns)
def load_cube_templates():
 ts=_load(str(PATH),PATH.stat().st_mtime_ns)['templates'];rs=load_source_accounting()['records'];n=[x['source_problem_number']for x in rs];a={z:t['id']for t in ts for z in t['source_problem_numbers']};m={x['source_problem_number']:x['template_id']for x in rs if x['status']=='active_template'}
 if len(n)!=44 or len(n)!=len(set(n))or set(n)!=source_problem_numbers()or a!=m:raise CubeTemplateError('Некорректный manifest модуля 26.')
 return list(ts)
def _b(t,x,a,v,s):return GeneratedCubeProblem(MODULE_ID,t['id'],t['source_problem_numbers'],x,a,str(a),v,s)
def _surface(t,r,s):
 small=r.randint(1,5);large=r.randint(6,20);paint=small*small*r.randint(1,20);a=paint*large*large//(small*small);return _b(t,f'Чтобы покрасить куб с ребром {small} см, нужно {paint} г краски. Сколько граммов понадобится для куба с ребром {large} см?',a,{'small_side':small,'large_side':large,'small_paint':paint},s)
def _painted(t,r,s):
 a,b,c=[r.randint(4,15)for _ in range(3)];answer=2*((a-2)*(b-2)+(a-2)*(c-2)+(b-2)*(c-2))+8;return _b(t,f'Параллелепипед {a} × {b} × {c} облили краской и распилили на единичные кубики. Сколько кубиков имеют чётное ненулевое число окрашенных граней?',answer,{'a':a,'b':b,'c':c},s)
def _water(t,r,s):
 w=r.randint(2,8);h=r.randint(2,8);depth=r.randint(1,9);volume_l=w*h*depth*10;return _b(t,f'В комнате {w} м × {h} м разлили {volume_l} литров воды. Какова высота слоя воды в миллиметрах?',depth,{'width_m':w,'length_m':h,'volume_l':volume_l},s)
def _packing(t,r,s):
 side=r.choice((60,72,90,120));x,y,z=r.choice(((2,3,5),(3,4,6),(2,4,5)));answer=(side//x)*(side//y)*(side//z);return _b(t,f'Деревянный куб со стороной {side} см распилили на бруски {x} × {y} × {z} см. Сколько брусков получилось?',answer,{'cube_side':side,'block_x':x,'block_y':y,'block_z':z},s)
def _visible(t,r,s):
 n=r.randint(4,15);answer=6*(n-2)**2+24*(n-2)+72;return _b(t,f'Куб со стороной {n} разрезали на единичные кубики. На каждой грани малого кубика написали число видимых в большом кубе граней этого малого кубика. Найдите сумму всех записанных чисел.',answer,{'side':n},s)
STRATEGIES={'surface':_surface,'painted':_painted,'water':_water,'packing':_packing,'visible':_visible}
def generate_cube_problem(template_id,*,seed=None,rng=None):
 ts={t['id']:t for t in load_cube_templates()};
 if template_id not in ts:raise CubeTemplateError(f'Неизвестный шаблон модуля 26: {template_id}.')
 return STRATEGIES[ts[template_id]['generation_strategy']](ts[template_id],rng or random.Random(seed),seed)
def generate_cube_problem_from_module(module_id,*,rng):return generate_cube_problem(rng.choice(load_cube_templates())['id'],rng=rng)
def cube_template_metadata():
 ts=load_cube_templates();return {'modules':[{'module_id':MODULE_ID,'title':'Cubes, Volume and Spatial Geometry','display_name':'Кубы, объем и пространственная геометрия','template_count':len(ts)}],'templates':[{'template_id':t['id'],'title':t['id'],'display_name':t['id'],'module_name':'Кубы, объем и пространственная геометрия','source_problem_numbers':t['source_problem_numbers'],'problem_type':t['generation_strategy']}for t in ts],'stats':{'total_modules':1,'total_templates':len(ts),'covered_source_problem_numbers':len(source_problem_numbers())}}
