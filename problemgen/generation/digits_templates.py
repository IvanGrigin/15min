"""Детерминированный генератор модуля «Цифры, запись чисел и криптарифмы»."""

from __future__ import annotations

import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from itertools import combinations, permutations, product
from pathlib import Path
from typing import Any, Callable

from problemgen.generation.comparison_templates import Character, load_approved_characters
from problemgen.russian.agreement import pluralize_ru


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    PROJECT_ROOT / "docs" / "08a_tsifry_bez_imen_i_personazhey_deduplicated.md",
    PROJECT_ROOT / "docs" / "08b_tsifry_s_imenami_i_personazhami_deduplicated.md",
)
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "problem_sets" / "digits_number_notation_and_cryptarithms" / "templates.json"
NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\.\s+.+$")
MODULE_ID = "digits_number_notation_and_cryptarithms"
MAX_ATTEMPTS = 100


class DigitsTemplateError(ValueError):
    """Ошибка каталога или ограниченной генерации digits-модуля."""


@dataclass(frozen=True)
class GeneratedDigitsProblem:
    module: str
    template_id: str
    source_problem_numbers: list[int]
    problem_text: str
    answer: Any
    answer_text: str
    parameters: dict[str, Any]
    seed: int | None = None
    universe: str | None = None
    characters: list[str] | None = None


def source_digits_problem_numbers(paths: tuple[Path, ...] = SOURCE_PATHS) -> set[int]:
    numbers: set[int] = set()
    for path in paths:
        numbers.update(int(match.group(1)) for line in path.read_text(encoding="utf-8").splitlines() if (match := NUMBERED_LINE_RE.match(line)))
    return numbers


@lru_cache(maxsize=4)
def _load_payload(path: str, mtime_ns: int) -> dict[str, Any]:
    del mtime_ns
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_digits_templates(path: str | Path = DEFAULT_TEMPLATE_PATH) -> list[dict[str, Any]]:
    resolved = Path(path).resolve()
    templates = _load_payload(str(resolved), resolved.stat().st_mtime_ns).get("templates")
    if not isinstance(templates, list) or not templates:
        raise DigitsTemplateError("В digits problem set отсутствует templates.")
    validate_digits_catalog(templates)
    return list(templates)


def validate_digits_catalog(templates: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    seen: list[int] = []
    for template in templates:
        for field in ("id", "title", "problem_type", "source_problem_numbers", "generation_strategy", "active", "uses_characters"):
            if field not in template:
                raise DigitsTemplateError(f"У шаблона отсутствует {field}.")
        if template["id"] in ids:
            raise DigitsTemplateError(f"Повторяющийся id: {template['id']}")
        ids.add(str(template["id"]))
        seen.extend(int(number) for number in template["source_problem_numbers"])
        if not template["active"] and not template.get("exclusion_reason"):
            raise DigitsTemplateError(f"У неактивного {template['id']} нет причины исключения.")
    source = source_digits_problem_numbers()
    duplicates = sorted(number for number, count in Counter(seen).items() if count > 1)
    if set(seen) != source or duplicates:
        raise DigitsTemplateError(f"Нарушено покрытие: missing={sorted(source-set(seen))}, extra={sorted(set(seen)-source)}, duplicates={duplicates}")


def digits_template_metadata() -> dict[str, Any]:
    templates = load_digits_templates()
    active = [item for item in templates if item["active"]]
    return {
        "modules": [{"module_id": MODULE_ID, "title": "Digits, Number Notation and Cryptarithms", "display_name": "Цифры, запись чисел и криптарифмы", "template_count": len(active), "covered_source_problem_numbers": len(source_digits_problem_numbers())}],
        "templates": [{"template_id": item["id"], "title": item["title"], "display_name": item["title"], "module_name": "Цифры, запись чисел и криптарифмы", "source_problem_numbers": item["source_problem_numbers"], "problem_type": item["problem_type"]} for item in active],
        "stats": {"total_modules": 1, "total_templates": len(active), "all_templates": len(templates), "inactive_templates": len(templates)-len(active), "covered_source_problem_numbers": len(source_digits_problem_numbers())},
    }


def get_digits_template(template_id: str) -> dict[str, Any]:
    for template in load_digits_templates():
        if template["id"] == template_id:
            return template
    raise DigitsTemplateError(f"Неизвестный digits-шаблон: {template_id}")


def _make(template: dict[str, Any], text: str, answer: Any, answer_text: str, parameters: dict[str, Any], seed: int | None, universe: str | None = None, characters: list[Character] | None = None) -> GeneratedDigitsProblem:
    if "{" in text or "}" in text:
        raise DigitsTemplateError("В тексте остались заполнители.")
    return GeneratedDigitsProblem(MODULE_ID, str(template["id"]), list(template["source_problem_numbers"]), text, answer, answer_text, parameters, seed, universe, [item.name for item in characters] if characters else None)


def _characters(rng: random.Random, count: int) -> tuple[str, list[Character]]:
    universes = load_approved_characters()
    universe = rng.choice(sorted(universes))
    return universe, rng.sample(universes[universe], count)


def _cap(name: str) -> str:
    return name[:1].upper() + name[1:]


def _past(character: Character, masculine: str, feminine: str) -> str:
    return feminine if character.gender == "feminine" else masculine


def digit_occurrences_in_range(lower: int, upper: int, digit: int) -> int:
    return sum(str(number).count(str(digit)) for number in range(lower, upper + 1))


def count_n_digit_numbers_with_digit_sum(digit_count: int, target_sum: int, fixed_positions: dict[int, int] | None = None) -> int:
    fixed = fixed_positions or {}
    if digit_count < 1 or target_sum < 0 or any(position < 1 or position > digit_count or digit not in range(10) for position, digit in fixed.items()):
        return 0
    states = {0: 1}
    for position in range(1, digit_count + 1):
        allowed = [fixed[position]] if position in fixed else range(1 if position == 1 else 0, 10)
        states = {total: sum(count for subtotal, count in states.items() for digit in allowed if subtotal + digit == total) for total in range(target_sum + 1)}
    return states.get(target_sum, 0)


def count_distinct_digit_permutations(digits: str) -> int:
    result = math.factorial(len(digits))
    for amount in Counter(digits).values():
        result //= math.factorial(amount)
    return result


def count_distinct_numbers_from_digit_multiset(digits: str) -> int:
    result = count_distinct_digit_permutations(digits)
    if "0" in digits:
        remainder = digits.replace("0", "", 1)
        result -= count_distinct_digit_permutations(remainder)
    return result


def count_subsequence_methods(source: str, target: str) -> int:
    dp = [1] + [0] * len(target)
    for symbol in source:
        for index in range(len(target) - 1, -1, -1):
            if target[index] == symbol:
                dp[index + 1] += dp[index]
    return dp[-1]


def count_position_comparison(
    digit_count: int,
    left_position: int,
    right_position: int,
    operator: str,
    parity: int,
) -> int:
    """Считает числа по позициям слева без перебора всего диапазона."""
    if digit_count < 1:
        raise DigitsTemplateError("Число цифр должно быть положительным.")
    if left_position == right_position:
        raise DigitsTemplateError("Сравниваемые позиции должны различаться.")
    if not 1 <= left_position <= digit_count or not 1 <= right_position <= digit_count:
        raise DigitsTemplateError("Позиция цифры находится вне записи числа.")
    if operator not in {"<", ">"}:
        raise DigitsTemplateError(f"Неизвестный оператор сравнения: {operator}")
    if parity not in {0, 1}:
        raise DigitsTemplateError("Чётность должна быть равна 0 или 1.")

    constrained_positions = sorted({1, digit_count, left_position, right_position})
    choices: list[range] = []
    for position in constrained_positions:
        if position == 1:
            allowed = range(1, 10)
        elif position == digit_count:
            allowed = range(parity, 10, 2)
        else:
            allowed = range(10)
        choices.append(allowed)

    constrained_count = 0
    for digits in product(*choices):
        assignment = dict(zip(constrained_positions, digits))
        left_digit = assignment[left_position]
        right_digit = assignment[right_position]
        matches = left_digit < right_digit if operator == "<" else left_digit > right_digit
        if matches:
            constrained_count += 1

    unconstrained_count = digit_count - len(constrained_positions)
    return constrained_count * 10**unconstrained_count


def _bounds(rng: random.Random) -> tuple[int, int]:
    lower = rng.randint(1, 900)
    return lower, lower + rng.randint(120, 700)


def _condition_count(template: dict[str, Any], rng: random.Random, seed: int | None, *, parity: int | None, contains: bool) -> GeneratedDigitsProblem:
    lower, upper = _bounds(rng)
    digit = rng.randint(0, 9)
    values = [n for n in range(lower, upper + 1) if (parity is None or n % 2 == parity) and ((str(digit) in str(n)) == contains)]
    parity_text = "" if parity is None else ("чётных " if parity == 0 else "нечётных ")
    condition = "содержащих" if contains else "не содержащих"
    text = f"Сколько {parity_text}чисел от {lower} до {upper}, {condition} цифру {digit}?"
    return _make(template, text, len(values), str(len(values)), {"lower":lower,"upper":upper,"digit":digit,"parity":parity}, seed)


def _parity_contains(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem: return _condition_count(t,r,s,parity=r.randint(0,1),contains=True)
def _parity_excludes(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem: return _condition_count(t,r,s,parity=r.randint(0,1),contains=False)
def _contains(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem: return _condition_count(t,r,s,parity=None,contains=True)
def _excludes(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem: return _condition_count(t,r,s,parity=None,contains=False)


def _occurrences(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    lower, upper = _bounds(r); digit = r.randint(0,9); answer = digit_occurrences_in_range(lower,upper,digit)
    return _make(t, f"Натуральные числа от {lower} до {upper} выписаны подряд. Сколько раз встречается цифра {digit}?", answer, f"Цифра {digit} встречается {answer} {pluralize_ru(answer, ('раз','раза','раз'))}.", {"lower":lower,"upper":upper,"digit":digit}, s)


def _digit_sum(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    length=r.choice([5,10,20,50,90,99,100]); target=r.randint(3,min(20,9*length)); answer=count_n_digit_numbers_with_digit_sum(length,target)
    return _make(t,f"Сколько существует {length}-значных чисел, сумма цифр которых равна {target}?",answer,str(answer),{"digit_count":length,"target_sum":target},s)


def _fixed_digit_sum(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    length=r.choice([20,50,90,100]); positions=sorted(r.sample(range(2,length+1),3)); fixed={p:r.randint(0,5) for p in positions}; target=sum(fixed.values())+r.randint(2,12); answer=count_n_digit_numbers_with_digit_sum(length,target,fixed)
    if not answer: raise DigitsTemplateError("Невозможная сумма цифр.")
    details=", ".join(f"в позиции {p} справа стоит {fixed[p]}" for p in positions)
    return _make(t,f"Сколько существует {length}-значных чисел с суммой цифр {target}, у которых {details}?",answer,str(answer),{"digit_count":length,"target_sum":target,"fixed_positions":fixed},s)


def _addition_cryptarithm(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    a=r.randint(12000,49999); b=r.randint(12000,49999); total=a+b
    hidden_a=[r.randrange(5)]; hidden_b=[r.randrange(5)]; hidden_total=[r.randrange(len(str(total)))]
    def mask(value:int, hidden:list[int])->str: return "".join("*" if i in hidden else ch for i,ch in enumerate(str(value)))
    patterns=[mask(a,hidden_a),mask(b,hidden_b),mask(total,hidden_total)]
    def candidates(pattern:str)->list[int]:
        return [int(pattern.replace("*",str(d))) for d in range(10) if not (pattern.startswith("*") and d==0)]
    completions=[(left,right,left+right) for left in candidates(patterns[0]) for right in candidates(patterns[1]) if str(left+right)[0]!="0" and len(str(left+right))==len(patterns[2]) and all(pc=="*" or pc==vc for pc,vc in zip(patterns[2],str(left+right)))]
    hidden_sums={sum(int(str(value)[positions[0]]) for value,positions in zip(completion,[hidden_a,hidden_b,hidden_total])) for completion in completions}
    if len(hidden_sums)!=1: raise DigitsTemplateError("Криптарифм не определяет единственную сумму скрытых позиций.")
    answer=hidden_sums.pop()
    text=f"В примере {patterns[0]} + {patterns[1]} = {patterns[2]} звёздочками скрыты цифры. Найдите сумму всех скрытых цифр, считая каждую позицию отдельно."
    return _make(t,text,answer,str(answer),{"patterns":patterns,"solution_count":len(completions),"hidden_positions":[hidden_a,hidden_b,hidden_total]},s)


def _position_comparison(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    length = r.randint(4, 18)
    left, right = r.sample(range(1, length + 1), 2)
    operator = r.choice(["<", ">"])
    parity = r.randint(0, 1)
    answer = count_position_comparison(length, left, right, operator, parity)
    comparison_text = "меньше" if operator == "<" else "больше"
    text = f"Сколько существует {'нечётных' if parity else 'чётных'} {length}-значных чисел, у которых цифра в позиции {left} слева {comparison_text} цифры в позиции {right} слева?"
    return _make(t, text, answer, str(answer), {"digit_count": length, "left_position": left, "right_position": right, "operator": operator, "parity": parity}, s)


def _expression_edges(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    a=r.randint(100,999); b=r.randint(100,3000); c=r.randint(1,20); value=a*b+c; answer={"first_digit":int(str(value)[0]),"last_digit":value%10}
    return _make(t,f"Какой цифрой оканчивается число {a} × {b} + {c}? А начинается?",answer,f"Оканчивается цифрой {answer['last_digit']}, начинается цифрой {answer['first_digit']}.",{"a":a,"b":b,"c":c,"value":value},s)


def _two_digits(t: dict[str, Any], r: random.Random, s: int | None, either: bool) -> GeneratedDigitsProblem:
    lower,upper=_bounds(r); d1,d2=r.sample(range(10),2); op=(lambda n: str(d1) in str(n) or str(d2) in str(n)) if either else (lambda n: str(d1) in str(n) and str(d2) in str(n)); answer=sum(op(n) for n in range(lower,upper+1)); word="хотя бы одну из цифр" if either else "одновременно цифры"
    return _make(t,f"Сколько чисел от {lower} до {upper} содержат {word} {d1} и {d2}?",answer,str(answer),{"lower":lower,"upper":upper,"digits":[d1,d2]},s)


def _contains_both(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:return _two_digits(t,r,s,False)
def _contains_either(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:return _two_digits(t,r,s,True)


def _digit_product(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    digits=[r.randint(1,6) for _ in range(4)]+[r.choice([2,4,6,8])]; target=math.prod(digits); answer=sum(math.prod(map(int,str(n)))==target for n in range(10000,100000,2))
    if not 1<=answer<=500: raise DigitsTemplateError("Неудачное произведение.")
    return _make(t,f"Сколько существует чётных пятизначных чисел с произведением цифр {target}?",answer,str(answer),{"target_product":target},s)


def _selected_digit_sets(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    length=r.randint(3,7); choice=r.choice(["all_even","all_odd","first_odd_last_even","fixed_last_odd"])
    if choice=="all_even": answer=4*5**(length-1); text=f"Сколько существует {length}-значных чисел, у которых все цифры чётные?"
    elif choice=="all_odd": answer=5**length; text=f"Сколько существует {length}-значных чисел, у которых все цифры нечётные?"
    elif choice=="first_odd_last_even": answer=5*10**(length-2)*5; text=f"Сколько существует {length}-значных чисел, у которых первая цифра нечётная, а последняя чётная?"
    else: position=r.randint(2,length-1); digit=r.randint(0,9); answer=9*10**(length-3)*5; text=f"Сколько существует {length}-значных чисел, у которых цифра в позиции {position} слева равна {digit}, а последняя цифра нечётная?"
    return _make(t,text,answer,str(answer),{"digit_count":length,"condition":choice},s)


def _distinct_deletions(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    source="".join(str(r.choice([1,2,3,4])) for _ in range(7)); length=4; values=sorted({int("".join(source[i] for i in indexes)) for indexes in combinations(range(len(source)),length) if source[indexes[0]]!="0"}); answer=sum(values)
    return _make(t,f"Дано число {source}. Вычёркивая цифры без изменения порядка, получают различные четырёхзначные числа. Найдите сумму всех таких чисел.",answer,str(answer),{"source_digits":source,"values":values},s)


def _missing_divisibility(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    divisor=r.choice([9,45]); base=str(r.randint(10000,99999)); hidden=sorted(r.sample(range(1,5),2)); pattern="".join("*" if i in hidden else ch for i,ch in enumerate(base)); solutions=sorted({int("".join(ds)) for replacement in product("0123456789",repeat=2) for ds in [[replacement[hidden.index(i)] if i in hidden else ch for i,ch in enumerate(pattern)]] if int("".join(ds))%divisor==0})
    if not 1<=len(solutions)<=15: raise DigitsTemplateError("Неудобное число решений.")
    answer={"type":"integer_list","values":solutions}; return _make(t,f"Замените звёздочки в числе {pattern} цифрами так, чтобы число делилось на {divisor}. Укажите все варианты.",answer,"Варианты: "+", ".join(map(str,solutions))+".",{"pattern":pattern,"divisor":divisor},s)


def _subsequence(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    target="".join(str(r.randint(1,9)) for _ in range(3)); source="".join(r.choice(target+"0123456789") for _ in range(16)); answer=count_subsequence_methods(source,target)
    if answer==0: raise DigitsTemplateError("Подпоследовательность отсутствует.")
    return _make(t,f"Сколько есть способов вычеркнуть цифры из числа {source}, чтобы осталось {target}? Считайте способы по выбранным позициям.",answer,str(answer),{"source":source,"target":target},s)


def _digit_length(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    length=r.randint(2,8); answer=9*10**(length-1); return _make(t,f"Сколько существует {length}-значных натуральных чисел?",answer,str(answer),{"digit_count":length},s)


def _multiset(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    digits="".join(str(r.randint(0,5)) for _ in range(r.randint(5,9))); answer=count_distinct_numbers_from_digit_multiset(digits)
    return _make(t,f"Сколько различных чисел можно составить перестановкой всех цифр записи {digits}? Число не может начинаться с нуля.",answer,str(answer),{"digits":digits},s)


def _distinct_permutations(t: dict[str, Any], r: random.Random, s: int | None) -> GeneratedDigitsProblem:
    digits="".join(map(str,r.sample(range(1,10),r.randint(4,7)))); answer=math.factorial(len(digits)); return _make(t,f"Сколько различных чисел можно составить перестановкой цифр {', '.join(digits)} без повторений?",answer,str(answer),{"digits":digits},s)


def _product_last(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    start=r.choice([1,3,5,7,9]); count=r.randint(6,14); values=list(range(start,start+2*count,2)); answer=math.prod(values)%10; return _make(t,"Какой цифрой оканчивается произведение "+" · ".join(map(str,values))+"?",answer,str(answer),{"factors":values},s)


def _group_sums(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    universe,cs=_characters(r,4); endings=r.sample(range(10),4); sums=[sum(range(100+d,1000,10)) for d in endings]; first=sums[0]+sums[2]; second=sums[1]+sums[3]; diff=abs(first-second); winner=[cs[0],cs[2]] if first>second else [cs[1],cs[3]]
    clauses=[f"{_cap(c.name)} {_past(c,'сложил','сложила')} все трёхзначные числа, оканчивающиеся цифрой {d}" for c,d in zip(cs,endings)]; text=", ".join(clauses)+f". {_cap(cs[0].name)} и {_cap(cs[2].name)} объединили результаты, а {_cap(cs[1].name)} и {_cap(cs[3].name)} — свои. Какая пара получила большую сумму и на сколько?"; answer={"winner":[c.name for c in winner],"difference":diff}; return _make(t,text,answer,f"Пара {_cap(winner[0].name)} и {_cap(winner[1].name)} получила большую сумму на {diff}.",{"ending_digits":endings,"group_sums":[first,second]},s,universe,cs)


def _character_truncation(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    universe,cs=_characters(r,1); c=cs[0]; original=r.randint(20,200); m1=r.randint(3,12); m2=r.randint(3,9); result=(original*m1//10)*m2//10; text=f"{_cap(c.name)} {_past(c,'задумал','задумала')} число, умножил{'а' if c.gender=='feminine' else ''} его на {m1}, зачеркнул{'а' if c.gender=='feminine' else ''} последнюю цифру результата, умножил{'а' if c.gender=='feminine' else ''} полученное число на {m2}, снова зачеркнул{'а' if c.gender=='feminine' else ''} последнюю цифру и получил{'а' if c.gender=='feminine' else ''} {result}. Какое число было задумано?"; solutions=[n for n in range(1,1000) if (n*m1//10)*m2//10==result]
    if solutions!=[original]: raise DigitsTemplateError("Нет единственного решения.")
    return _make(t,text,original,str(original),{"multipliers":[m1,m2],"result":result},s,universe,cs)


def _character_missing(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    universe,cs=_characters(r,1); c=cs[0]; digits=list(str(r.randint(100000,999999))); pos=r.randint(1,4); digits[pos]="*"; pattern="".join(digits); divisor=r.choice([3,9]); sols=[d for d in range(10) if int(pattern.replace("*",str(d)))%divisor==0]; answer={"type":"digit_set","values":sols}; return _make(t,f"{_cap(c.name)} восстанавливает цифру в числе {pattern}, чтобы оно делилось на {divisor}. Какие цифры подходят?",answer,"Подходящие цифры: "+", ".join(map(str,sols))+".",{"pattern":pattern,"divisor":divisor},s,universe,cs)


def _character_prime(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    universe,cs=_characters(r,1); c=cs[0]; primes=[]
    for n in range(101,1000):
        ds=list(map(int,str(n)))
        if len(set(ds))==3 and ds[2]==ds[0]+ds[1] and all(n%d for d in range(2,int(math.isqrt(n))+1)): primes.append(n)
    endings=sorted({n%10 for n in primes}); answer={"type":"digit_set","values":endings}; return _make(t,f"{_cap(c.name)} {_past(c,'задумал','задумала')} простое трёхзначное число с различными цифрами. Последняя цифра равна сумме первых двух. На какую цифру оно может оканчиваться?",answer,"Возможные цифры: "+", ".join(map(str,endings))+".",{"matching_primes":primes},s,universe,cs)


def _character_trick(t:dict[str,Any],r:random.Random,s:int|None)->GeneratedDigitsProblem:
    universe,cs=_characters(r,1); c=cs[0]; addend=2*r.randint(2,10); divisor=2; result=addend//divisor; text=f"{_cap(c.name)} показывает фокус: предлагает задумать число, умножить его на {divisor}, прибавить {addend}, разделить результат на {divisor} и вычесть задуманное число. Что получится?"; return _make(t,text,result,str(result),{"multiplier":divisor,"addend":addend,"divisor":divisor},s,universe,cs)


Strategy=Callable[[dict[str,Any],random.Random,int|None],GeneratedDigitsProblem]
STRATEGIES:dict[str,Strategy]={"parity_contains":_parity_contains,"digit_occurrences":_occurrences,"fixed_digit_sum":_fixed_digit_sum,"digit_sum":_digit_sum,"addition_cryptarithm":_addition_cryptarithm,"parity_excludes":_parity_excludes,"position_comparison":_position_comparison,"expression_edges":_expression_edges,"excludes_digit":_excludes,"contains_both":_contains_both,"digit_product":_digit_product,"contains_either":_contains_either,"selected_digit_sets":_selected_digit_sets,"distinct_deletions":_distinct_deletions,"missing_divisibility":_missing_divisibility,"contains_digit":_contains,"subsequence_methods":_subsequence,"digit_length_count":_digit_length,"multiset_permutations":_multiset,"distinct_permutations":_distinct_permutations,"product_last_digit":_product_last,"character_group_sums":_group_sums,"character_truncation":_character_truncation,"character_missing_digit":_character_missing,"character_prime":_character_prime,"character_trick":_character_trick}


def generate_digits_problem(template_id:str,*,seed:int|None=None,rng:random.Random|None=None)->GeneratedDigitsProblem:
    template=get_digits_template(template_id)
    if not template["active"]: raise DigitsTemplateError(f"Шаблон {template_id} неактивен: {template.get('exclusion_reason')}")
    strategy=STRATEGIES.get(str(template["generation_strategy"])); local=rng or random.Random(seed if seed is not None else datetime.now().timestamp())
    if strategy is None: raise DigitsTemplateError(f"Неизвестная стратегия: {template['generation_strategy']}")
    failures=[]
    for _ in range(MAX_ATTEMPTS):
        try: return strategy(template,local,seed)
        except DigitsTemplateError as error: failures.append(str(error))
    raise DigitsTemplateError(f"Не удалось сгенерировать {template_id}: {failures[-3:]}")


def generate_digits_problem_from_module(module_id:str,*,rng:random.Random)->GeneratedDigitsProblem:
    if module_id!=MODULE_ID: raise DigitsTemplateError(f"Неизвестный модуль: {module_id}")
    active=[item for item in load_digits_templates() if item["active"]]
    return generate_digits_problem(str(rng.choice(active)["id"]),rng=rng)
