"""Шаблоны арифметических задач с правильным склонением русских слов.

Каждый шаблон — это строка с морфологическими слотами вида {key:падеж}
или {key:count,числовой_ключ}. Движок рендеринга (template_engine.py)
заменяет слоты на нужные словоформы автоматически.

Документацию по синтаксису слотов см. в Docs/RUSSIAN_TEMPLATES.md.
"""
from __future__ import annotations

import random
from typing import Callable, Dict, List

from problemgen.core.models import ProblemRecord, TemplateDescriptor
from problemgen.russian.noun_dict import NOUNS
from problemgen.russian.template_engine import render_template

from .solvers import (
    solve_age_friends,
    solve_equal_payment,
    solve_heads_and_legs,
    solve_paint_cube,
    solve_ratio_sum,
    solve_round_robin,
)

# ---------------------------------------------------------------------------
# Константы и вспомогательные данные
# ---------------------------------------------------------------------------

# Пары животных (animal_key, legs_count)
_ANIMAL_PAIRS: list[tuple[str, int, str, int]] = [
    ("овца",    4, "курица", 2),
    ("корова",  4, "курица", 2),
    ("лошадь",  4, "курица", 2),
    ("овца",    4, "гусь",   2),
    ("корова",  4, "гусь",   2),
    ("гном",    2, "пони",   4),   # гномы = 2 ноги, пони = 4
]

# Локации-фразы для задач про пастбище (предложный падеж без предлога)
_PASTURE_PHRASES: list[str] = [
    "лугах вблизи Простоквашино",
    "пастбищах Смешариков",
    "полях Нарнии",
    "угодьях Шира",
    "лугах острова Чудес",
    "угодьях Изумрудного города",
    "полях волшебного леса",
    "лугах вблизи деревни Муми-троллей",
]

# Пары персонажей (name, verb_past_sg, gender)
# gender нужен для согласования глаголов
_CHARACTERS: list[tuple[str, str, str]] = [   # (имя, глагол пр.вр., род)
    ("Алёша",  "m"),
    ("Саша",   "m"),
    ("Коля",   "m"),
    ("Вася",   "m"),
    ("Петя",   "m"),
    ("Миша",   "m"),
    ("Маша",   "f"),
    ("Катя",   "f"),
    ("Оля",    "f"),
    ("Надя",   "f"),
    ("Аня",    "f"),
    ("Таня",   "f"),
]

def _verb(base_m: str, base_f: str, gender: str) -> str:
    """Вернуть прошедшее время глагола, согласованное с полом персонажа."""
    return base_m if gender == "m" else base_f

def _modal(gender: str) -> str:
    """«должен» / «должна» — краткое прилагательное по роду."""
    return "должен" if gender == "m" else "должна"

# Действия в задачах на пропорцию (base_m, base_f, pl_form)
# Используем универсальные глаголы, подходящие для любых объектов
_ACTIONS: list[tuple[str, str, str]] = [
    ("собрал",   "собрала",   "собрали"),
    ("нашёл",    "нашла",     "нашли"),
    ("купил",    "купила",    "купили"),
    ("принёс",   "принесла",  "принесли"),
    ("получил",  "получила",  "получили"),
]

# Предметы для задач на пропорцию (noun_key)
_RATIO_NOUNS: list[str] = [
    "дерево", "яблоко", "книга", "орех", "конфета", "монета", "цветок",
]

# Соревнования для round_robin
_TOURNAMENTS: list[tuple[str, str, str]] = [
    # (название в предл.п., noun_key для счёта участников, noun_key для партий)
    ("шахматном турнире",         "человек", "партия"),
    ("турнире по шашкам",         "человек", "партия"),
    ("турнире по настольному теннису", "участник", "матч"),
    ("шашечном турнире",          "участник", "партия"),
    ("соревновании по математике", "участник", "встреча"),
]

# ---------------------------------------------------------------------------
# Списки шаблонов
# ---------------------------------------------------------------------------

def list_templates() -> List[TemplateDescriptor]:
    return [
        TemplateDescriptor(
            code="heads_and_legs",
            label="Головы и ноги",
            description=(
                "По суммарному количеству голов и ног двух видов животных "
                "найти количество животных каждого вида."
            ),
        ),
        TemplateDescriptor(
            code="ratio_sum",
            label="Пропорция и сумма",
            description=(
                "Один персонаж собрал в K раз больше предметов, чем другой; "
                "вместе — N штук. Найти количество у каждого."
            ),
        ),
        TemplateDescriptor(
            code="age_friends",
            label="Возраст друзей",
            description=(
                "Сумма возрастов нескольких друзей сейчас и через D лет. "
                "Найти количество друзей."
            ),
        ),
        TemplateDescriptor(
            code="round_robin",
            label="Круговой турнир",
            description=(
                "N участников играют друг с другом по одному разу. "
                "Найти общее количество партий."
            ),
        ),
        TemplateDescriptor(
            code="paint_cube",
            label="Окраска куба",
            description=(
                "Для куба со стороной 1 см нужно G граммов краски. "
                "Сколько краски нужно для куба со стороной H см?"
            ),
        ),
        TemplateDescriptor(
            code="equal_payment",
            label="Совместная оплата",
            description=(
                "Два персонажа делят расходы поровну. Один даёт другому "
                "заём; затем каждый платит часть счёта. "
                "Найти итоговый долг."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# ── Шаблон 1: heads_and_legs ────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_HEADS_LEGS_TMPL = (
    "На {place} пасутся {a1:nom_pl} и {a2:nom_pl}. "
    "У {a1:gen_pl} и {a2:gen_pl} вместе {HEAD:count,heads} "
    "и {LEG:count,legs}. "
    "Сколько {a1:gen_pl} и сколько {a2:gen_pl}?"
)


def generate_heads_and_legs(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    difficulties = {"easy": (10, 30), "medium": (20, 60), "hard": (40, 120)}
    lo, hi = difficulties.get(difficulty_level, (10, 30))

    a1_key, legs1, a2_key, legs2 = rng.choice(_ANIMAL_PAIRS)

    for _ in range(200):
        total_heads = rng.randint(lo, hi)
        result = solve_heads_and_legs(legs1, legs2, total_heads,
                                      total_heads * legs1 - rng.randint(1, total_heads - 1) * (legs1 - legs2))
        if result:
            count1, count2 = result
            total_legs = count1 * legs1 + count2 * legs2
            break
    else:
        count1, count2 = 10, 8
        total_heads = count1 + count2
        total_legs = count1 * legs1 + count2 * legs2

    a1 = NOUNS[a1_key]
    a2 = NOUNS[a2_key]
    place = rng.choice(_PASTURE_PHRASES)

    problem_text = render_template(
        _HEADS_LEGS_TMPL,
        {
            "place": place,
            "a1": a1,
            "a2": a2,
            "HEAD": NOUNS["голова"],
            "LEG": NOUNS["нога"],
            "heads": total_heads,
            "legs": total_legs,
        },
    )

    answer_text = (
        f"{a1_key.capitalize()}: {count1}, {a2_key}: {count2}"
    )

    return ProblemRecord(
        code=f"ARI-HLG-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="heads_and_legs",
        problem_text=problem_text,
        answer_text=answer_text,
        answer_values=[count1, count2],
        difficulty={
            "level": difficulty_level,
            "total_heads": total_heads,
            "total_legs": total_legs,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "головы и ноги",
            "formula": f"x+y={total_heads}, {legs1}x+{legs2}y={total_legs}",
        },
        variables={
            "animal1": a1_key,
            "animal2": a2_key,
            "legs1": legs1,
            "legs2": legs2,
            "total_heads": total_heads,
            "total_legs": total_legs,
        },
        intermediate_values={
            f"count_{a1_key}": count1,
            f"count_{a2_key}": count2,
        },
        relations=[
            f"{a1.nom_pl.capitalize()} имеют {legs1} ноги, {a2.nom_pl} — {legs2}.",
            "Система: x+y=голов, legs1*x+legs2*y=ног.",
        ],
    )


# ---------------------------------------------------------------------------
# ── Шаблон 2: ratio_sum ─────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_RATIO_TMPL = (
    "{name1} {v_sg} в {РАЗ:count,ratio} больше {THING:gen_pl}, чем {name2}, "
    "а вместе они {v_pl} {THING:count,total}. "
    "Сколько {THING:gen_pl} {v_sg} {name1} и сколько {name2}?"
)


def generate_ratio_sum(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    difficulties = {"easy": (2, 4, 6, 50), "medium": (2, 6, 30, 200), "hard": (3, 9, 100, 800)}
    r_lo, r_hi, n_lo, n_hi = difficulties.get(difficulty_level, (2, 4, 6, 50))

    thing_key = rng.choice(_RATIO_NOUNS)
    thing = NOUNS[thing_key]

    char1 = rng.choice(_CHARACTERS)
    char2 = rng.choice([c for c in _CHARACTERS if c[0] != char1[0]])
    name1, g1 = char1
    name2, _g2 = char2

    action = rng.choice(_ACTIONS)
    v_sg = _verb(action[0], action[1], g1)
    v_pl = action[2]

    for _ in range(200):
        ratio = rng.randint(r_lo, r_hi)
        total = rng.randint(n_lo, n_hi) * (ratio + 1)
        result = solve_ratio_sum(ratio, total)
        if result:
            count1, count2 = result
            break
    else:
        ratio, total = 2, 12
        count1, count2 = 8, 4

    problem_text = render_template(
        _RATIO_TMPL,
        {
            "name1": name1,
            "name2": name2,
            "v_sg": v_sg,
            "v_pl": v_pl,
            "РАЗ": NOUNS["раз"],
            "THING": thing,
            "ratio": ratio,
            "total": total,
        },
    )

    return ProblemRecord(
        code=f"ARI-RAT-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="ratio_sum",
        problem_text=problem_text,
        answer_text=f"{name1}: {count1}, {name2}: {count2}",
        answer_values=[count1, count2],
        difficulty={
            "level": difficulty_level,
            "ratio": ratio,
            "total": total,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "пропорция и сумма",
            "formula": f"x={ratio}*y, x+y={total}",
        },
        variables={
            "name1": name1,
            "name2": name2,
            "thing": thing_key,
            "ratio": ratio,
            "total": total,
        },
        intermediate_values={"count1": count1, "count2": count2},
        relations=[f"{name1} в {ratio} раза больше {name2}; сумма {total}."],
    )


# ---------------------------------------------------------------------------
# ── Шаблон 3: age_friends ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_AGE_TMPL = (
    "Возраст нескольких {PERSON:gen_pl} в сумме составляет {ГОД:count,sum_now}. "
    "Через {ГОД:count,delta} их общий возраст составит {ГОД:count,sum_then}. "
    "Сколько {PERSON:gen_pl}?"
)


def generate_age_friends(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    person_choices = ["друг", "подруга", "одноклассник"]
    person_key = rng.choice(person_choices)
    person = NOUNS[person_key]

    difficulties = {
        "easy":   (2, 6,  2, 6,  8, 15),
        "medium": (3, 10, 3, 8, 12, 25),
        "hard":   (4, 15, 4, 10, 15, 35),
    }
    n_lo, n_hi, d_lo, d_hi, age_lo, age_hi = difficulties.get(difficulty_level, (2, 6, 2, 6, 8, 15))

    for _ in range(300):
        n = rng.randint(n_lo, n_hi)
        delta = rng.randint(d_lo, d_hi)
        avg_age = rng.randint(age_lo, age_hi)
        sum_now = n * avg_age + rng.randint(-(n * 2), n * 2)
        if sum_now <= 0:
            continue
        sum_then = sum_now + n * delta
        result = solve_age_friends(sum_now, delta, sum_then)
        if result == n:
            break
    else:
        n, delta, sum_now, sum_then = 5, 4, 74, 94

    problem_text = render_template(
        _AGE_TMPL,
        {
            "PERSON": person,
            "ГОД": NOUNS["год"],
            "sum_now": sum_now,
            "delta": delta,
            "sum_then": sum_then,
        },
    )

    return ProblemRecord(
        code=f"ARI-AGE-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="age_friends",
        problem_text=problem_text,
        answer_text=str(n),
        answer_values=[n],
        difficulty={
            "level": difficulty_level,
            "n_friends": n,
            "delta_years": delta,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "возраст друзей",
            "formula": f"n = (sum_then - sum_now) / delta = ({sum_then}-{sum_now})/{delta}",
        },
        variables={
            "person": person_key,
            "sum_now": sum_now,
            "delta": delta,
            "sum_then": sum_then,
        },
        intermediate_values={"n_friends": n},
        relations=[f"Каждый из {n} {person.gen_pl} становится старше на {delta} лет."],
    )


# ---------------------------------------------------------------------------
# ── Шаблон 4: round_robin ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_ROUND_ROBIN_TMPL = (
    "В {tournament} участвуют {PERSON:count,n}. "
    "Сколько {GAME:gen_pl} будет сыграно, "
    "если каждый участник сыграет со всеми остальными ровно по одному разу?"
)


def generate_round_robin(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    difficulties = {"easy": (4, 10), "medium": (8, 20), "hard": (15, 40)}
    n_lo, n_hi = difficulties.get(difficulty_level, (4, 10))
    n = rng.randint(n_lo, n_hi)

    tournament, person_key, game_key = rng.choice(_TOURNAMENTS)
    games = solve_round_robin(n)

    problem_text = render_template(
        _ROUND_ROBIN_TMPL,
        {
            "tournament": tournament,
            "PERSON": NOUNS[person_key],
            "GAME": NOUNS[game_key],
            "n": n,
        },
    )

    return ProblemRecord(
        code=f"ARI-RRB-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="round_robin",
        problem_text=problem_text,
        answer_text=str(games),
        answer_values=[games],
        difficulty={
            "level": difficulty_level,
            "n_participants": n,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "круговой турнир",
            "formula": "n*(n-1)//2",
        },
        variables={"n_participants": n, "tournament": tournament},
        intermediate_values={"total_games": games},
        relations=[f"Каждая из {n} пар встречается ровно раз: C({n},2) = {games}."],
    )


# ---------------------------------------------------------------------------
# ── Шаблон 5: paint_cube ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_PAINT_CUBE_TMPL = (
    "Чтобы покрасить поверхность деревянного {CUBE:gen} высотой 1 см "
    "нужно {ГР:count,g} краски. "
    "Сколько краски понадобится, чтобы покрасить деревянный {CUBE:acc} "
    "высотой {h} см?"
)


def generate_paint_cube(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    difficulties = {
        "easy":   (2, 5,   6, 20),
        "medium": (4, 10, 10, 30),
        "hard":   (6, 15, 12, 50),
    }
    h_lo, h_hi, g_lo, g_hi = difficulties.get(difficulty_level, (2, 5, 6, 20))
    h = rng.randint(h_lo, h_hi)
    g = rng.randint(g_lo, g_hi)
    answer = solve_paint_cube(g, h)

    problem_text = render_template(
        _PAINT_CUBE_TMPL,
        {
            "CUBE": NOUNS["кубик"],
            "ГР": NOUNS["грамм"],
            "g": g,
            "h": h,
        },
    )

    return ProblemRecord(
        code=f"ARI-CUB-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="paint_cube",
        problem_text=problem_text,
        answer_text=f"{answer} граммов",
        answer_values=[answer],
        difficulty={
            "level": difficulty_level,
            "h_cm": h,
            "g_per_unit": g,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "окраска куба",
            "formula": f"g * h² = {g} * {h}² = {answer}",
        },
        variables={"g_per_unit": g, "h": h},
        intermediate_values={"surface_ratio": h * h, "answer_grams": answer},
        relations=["Площадь поверхности куба ∝ h², поэтому расход краски тоже ∝ h²."],
    )


# ---------------------------------------------------------------------------
# ── Шаблон 6: equal_payment ─────────────────────────────────────────────────
# ---------------------------------------------------------------------------

_EQUAL_PAYMENT_TMPL = (
    "{name1} и {name2} хотят вместе заплатить {РУБ:count,total}, "
    "разделив затраты поровну. "
    "{name1} {v1_lend} {pron2_dat} взаймы {РУБ:count,loan}. "
    "{name2} {v2_pay} {РУБ:count,paid2}, а {name1} — оставшиеся {РУБ:count,paid1}. "
    "Сколько {РУБ:gen_pl} {v2_modal} вернуть {name2}?"
)


def generate_equal_payment(
    *, rng: random.Random, index: int, difficulty_level: str,
) -> ProblemRecord:
    difficulties = {
        "easy":   (500,  5_000, 1_000, 10_000),
        "medium": (2_000, 20_000, 3_000, 30_000),
        "hard":   (10_000, 100_000, 15_000, 150_000),
    }
    t_lo, t_hi, l_lo, l_hi = difficulties.get(difficulty_level, (500, 5_000, 1_000, 10_000))

    char1 = rng.choice(_CHARACTERS)
    char2 = rng.choice([c for c in _CHARACTERS if c[0] != char1[0]])
    name1, g1 = char1
    name2, g2 = char2

    for _ in range(300):
        total = rng.randint(t_lo // 2, t_hi // 2) * 2   # чётное
        loan = rng.randint(l_lo, l_hi)
        max_paid2 = loan + total // 2 - 1   # debt > 0
        if max_paid2 <= total // 5:
            continue
        paid2 = rng.randint(total // 5, min(max_paid2, total - 1))
        debt = solve_equal_payment(total, loan, paid2)
        if debt and debt > 0:
            paid1 = total - paid2
            break
    else:
        total, loan, paid2, paid1 = 7200, 9000, 4100, 3100
        g2 = "f"
        name2 = "Катя"
        name1 = "Маша"
        g1 = "f"
        debt = 8500

    v1_lend   = _verb("дал", "дала", g1)
    v2_pay    = _verb("заплатил", "заплатила", g2)
    v2_modal  = _modal(g2)
    pron2_dat = "ему" if g2 == "m" else "ей"

    problem_text = render_template(
        _EQUAL_PAYMENT_TMPL,
        {
            "name1": name1,
            "name2": name2,
            "v1_lend":   v1_lend,
            "v2_pay":    v2_pay,
            "v2_modal":  v2_modal,
            "pron2_dat": pron2_dat,
            "РУБ": NOUNS["рубль"],
            "total": total,
            "loan":  loan,
            "paid2": paid2,
            "paid1": paid1,
        },
    )

    return ProblemRecord(
        code=f"ARI-PAY-{index:05d}",
        category="arithmetic",
        domain="arithmetic",
        template_name="equal_payment",
        problem_text=problem_text,
        answer_text=f"{debt} рублей",
        answer_values=[debt],
        difficulty={
            "level": difficulty_level,
            "total": total,
            "loan": loan,
        },
        story={},
        metadata={
            "topic": "арифметика",
            "subtype": "совместная оплата",
            "formula": f"loan + total/2 - paid2 = {loan} + {total//2} - {paid2} = {debt}",
        },
        variables={
            "name1": name1, "name2": name2,
            "total": total, "loan": loan, "paid2": paid2, "paid1": paid1,
        },
        intermediate_values={"debt": debt, "each_share": total // 2},
        relations=[
            f"Каждый должен заплатить {total//2} руб.",
            f"{name2} вернёт заём {loan} руб. + разницу в платежах = {debt} руб.",
        ],
    )


# ---------------------------------------------------------------------------
# Реестр фабрик
# ---------------------------------------------------------------------------

TEMPLATE_FACTORIES: Dict[str, Callable[..., ProblemRecord]] = {
    "heads_and_legs": generate_heads_and_legs,
    "ratio_sum":      generate_ratio_sum,
    "age_friends":    generate_age_friends,
    "round_robin":    generate_round_robin,
    "paint_cube":     generate_paint_cube,
    "equal_payment":  generate_equal_payment,
}
