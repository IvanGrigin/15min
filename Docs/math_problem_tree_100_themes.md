# Math Problem Corpus Tree — 100 Themes

This taxonomy replaces the broad `topic → easy/medium/hard` structure. A mathematical family is the leaf node; difficulty is a separate label attached to each concrete problem.

## Difficulty scale

- **D1** — Direct application: one standard fact or one short computation.
- **D2** — Routine multi-step solution: two to four standard operations.
- **D3** — Model selection: translate the condition, choose a method, and check constraints.
- **D4** — Olympiad insight: non-obvious transformation, case split, invariant, or systematic counting.
- **D5** — Multi-idea proof or construction: several interacting constraints or a general argument.

## Assignment model

- `primary_theme`: exactly one of the 100 leaf IDs below;
- `difficulty`: one of `D1`–`D5`, assigned after considering the shortest intended solution;
- `secondary_tags`: optional tags such as `construction`, `proof`, `optimization`, `case_split`, `units`, `diagram_required`;
- `source_ref`: original corpus item number and source file;
- `template_id`: the generator template used for a newly generated variant.

## Tree

## A. Arithmetic and expressions / Арифметика и выражения (8 themes)

### A01 — Direct evaluation of numerical expressions / Прямое вычисление числовых выражений

**Difficulty profile:** D1–D2

**Scope:** Evaluate a fully specified expression using standard arithmetic and the order of operations.

**Corpus examples:**

- **D1 · corpus item 6** — Вычислите 239 - 135 + 112 - 234 - 366 : 127 + 239 : 231  
  _Source: `15-минутки/Апрель 2026/03.04.2026.pdf`; source line 13._
- **D1 · corpus item 868** — Вычислите: 279 · 3 · 137 − 93 · 3 · 410 + 632 ·373 − 631 · 372  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 992._
- **D1 · corpus item 1405** — Вычислите 239 · 135 + 112 · 234 − 366 · 127 + 239 · 231  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1565._

**Generator templates:**

1. `A01-T1` — Вычислите: {a} {op1} {b} {op2} {c}.
   - Parameters: a,b,c — целые; op1,op2 ∈ {+,-,×,:}.
   - Validation: Все деления точные; промежуточные значения допустимы для класса.
1. `A01-T2` — Выполните действие: ({a} {op1} {b}) {op2} {c}.
   - Parameters: Целые параметры и две операции.
   - Validation: Нет деления на ноль; ответ однозначен.

### A02 — Nested expressions and order of operations / Скобки и порядок действий

**Difficulty profile:** D1–D3

**Scope:** Evaluate or unwind expressions with several nested parentheses.

**Corpus examples:**

- **D1 · corpus item 876** — Расставьте порядок действий, и решите в обратном порядке: 1) ((((x - 45) × 284) : 71) + 64) = -192  
  _Source: `Доп ДЗ/Доп ДЗ 03.docx`; source line 1003._
- **D2 · template-derived illustration** — Вычислите: 6·((83−47)·5+24):12.
- **D2 · template-derived illustration** — Расставьте порядок действий и вычислите: (((125+35)·9):24)−17.

**Generator templates:**

1. `A02-T1` — Вычислите: {k1}·(({a}-{b})·{k2}+{c}):{d}.
   - Parameters: Целые k1,k2,a,b,c,d.
   - Validation: Деление точное; не менее трёх уровней действий.
1. `A02-T2` — Расставьте порядок действий и вычислите: ((({a}+{b})·{c}):{d})-{e}.
   - Parameters: Положительные целые.
   - Validation: Все промежуточные результаты целые.

### A03 — Distributive-law shortcuts / Вынесение общего множителя и удобные вычисления

**Difficulty profile:** D2–D3

**Scope:** Recognize a common factor or complementary terms instead of multiplying everything directly.

**Corpus examples:**

- **D2 · corpus item 1286** — На сколько отличаются числа 201 × 205 и 202 × 204? Какое больше?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1446._
- **D2 · corpus item 1291** — На сколько отличаются числа 399 × 403 и 400 × 402? Какое больше?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1451._
- **D2 · corpus item 1536** — На сколько отличаются числа 239 · 243 и 240 · 242 и какое больше?  
  _Source: `Сб В классе/1 занятие.docx`; source line 1699._

**Generator templates:**

1. `A03-T1` — Вычислите удобным способом: {a}·{b}+{a}·{c}.
   - Parameters: b+c удобно вычисляется.
   - Validation: Предполагаемый метод — вынести a за скобки.
1. `A03-T2` — На сколько отличаются ({n}-1)·({n}+3) и {n}·({n}+2)? Какое число больше?
   - Parameters: n — натуральное.
   - Validation: Разность упрощается без полного умножения.

### A04 — Comparison of large products without full calculation / Сравнение больших произведений без полного вычисления

**Difficulty profile:** D2–D4

**Scope:** Compare two structured products by algebraic transformation, cancellation, or bounding.

**Corpus examples:**

- **D2 · corpus item 72** — Какое из чисел больше и на сколько: 6767 × 239 × 7677 (первое) или 6766 × 239 × 7676 (второе)?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 109._
- **D2 · corpus item 92** — Какое из чисел больше и на сколько: 6767 × 239 × 7675 (первое) или 7676 × 239 × 6768 (второе)?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 132._
- **D3 · template-derived illustration** — Какое число больше и на сколько: 5001·4999 или 5000·5000? Не выполняйте полное умножение.

**Generator templates:**

1. `A04-T1` — Какое число больше и на сколько: {a}·{b} или ({a}-1)·({b}+1)?
   - Parameters: a>b>0.
   - Validation: Разность имеет короткую символическую форму.
1. `A04-T2` — Сравните {k}·{m}·{n} и ({k}-1)·{m}·({n}-1), не вычисляя полностью.
   - Parameters: Положительные целые.
   - Validation: Общий множитель m явно используется.

### A05 — Long division and exact quotients / Письменное деление и точное частное

**Difficulty profile:** D1–D2

**Scope:** Compute a large exact integer quotient.

**Corpus examples:**

- **D1 · corpus item 185** — Вычислите 914037258 : 126  
  _Source: `15-минутки/Март 2026/26.03.2026.pdf`; source line 285._
- **D1 · corpus item 200** — Вычислите 739024440 : 108  
  _Source: `15-минутки/Март 2026/31.03.2026.pdf`; source line 309._
- **D1 · corpus item 2109** — Вычислите: 43586735 : 43  
  _Source: `Чт ДЗ/ДЗ 01 от 05.02.2026.docx`; source line 2338._

**Generator templates:**

1. `A05-T1` — Вычислите: {N}:{d}.
   - Parameters: N=q·d; N содержит 6–10 цифр, d — 2–3 цифры.
   - Validation: Деление без остатка.
1. `A05-T2` — Выполните деление столбиком: {N}:{d}.
   - Parameters: Заранее выбирается целое q.
   - Validation: Можно специально включить ноль внутри частного.

### A06 — Leading-digit estimation and result classification / Оценка первой цифры и величины результата

**Difficulty profile:** D2–D4

**Scope:** Determine which calculations have a result in a target magnitude interval or begin with a given digit, often without exact computation.

**Corpus examples:**

- **D3 · corpus item 340** — Какие из результатов данных действий начинаются с цифры1? Выпишите в ответ номера нужных примеров. 1)6547 − 5983; 2)487 + 569; 3)3415 × 926; 4)34789 × 37483; 5)67014910068636 : 347968524; 6)6633327517568932 : 192589; 7)10457852355532−932381476923; 8)217×342−342×146+71 ×158  
  _Source: `239-5_comb.pdf`; source line 455._
- **D3 · corpus item 360** — Какие из результатов данных действий начинаются с цифры 1? Выпишите в ответ номера нужных примеров. 1)4385 + 5892; 2)763 − 677; 3)3711 × 358; 4)32592 × 98734; 5)74173787591475 : 356894725; 6)4651722726829701 : 235681; 7)10736528548858−962332147692; 8)329×268−268×273+56 ×132  
  _Source: `239-5_comb.pdf`; source line 475._
- **D2 · corpus item 1296** — Какой цифрой оканчивается сумма 418 × 2026 + 7? А начинается?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1456._

**Generator templates:**

1. `A06-T1` — Какие из выражений имеют результат, начинающийся с цифры {d}?
   - Parameters: Список из 6–10 действий.
   - Validation: Не менее двух верных вариантов; ответы проверены точно.
1. `A06-T2` — Какой цифрой начинается значение {expression}? Ответ обоснуйте оценками.
   - Parameters: Структурированное большое выражение.
   - Validation: Первую цифру можно найти без полного вычисления.

### A07 — Integer inequalities and greatest natural solution / Неравенства и наибольшее натуральное решение

**Difficulty profile:** D2–D3

**Scope:** Evaluate the right-hand side and identify the greatest natural number satisfying an inequality.

**Corpus examples:**

- **D3 · corpus item 1599** — Найти наибольшее натуральное решение неравенства: x ≤ (4025 - 839) · 4800 : (2097 + 25389 : 403)  
  _Source: `Сб В классе/11 занятие.docx`; source line 1768._
- **D3 · corpus item 1628** — Найти наибольшее натуральное решение неравенства: x ≤ (2 - 2677 + 3245) · 4000 : (2556-1668 / 3)  
  _Source: `Сб В классе/12 занятие.docx`; source line 1800._
- **D2 · template-derived illustration** — Найдите наибольшее натуральное решение неравенства x ≤ (4800−936):12.

**Generator templates:**

1. `A07-T1` — Найдите наибольшее натуральное решение: x ≤ ({a}-{b})·{c}:({d}+{e}:{f}).
   - Parameters: Внутреннее деление точное.
   - Validation: Правая часть положительна; ответ однозначен.
1. `A07-T2` — Найдите все натуральные x, для которых {L} < {p}x+{q} ≤ {R}.
   - Parameters: p>0.
   - Validation: Множество решений конечно и непусто.

### A08 — Reverse arithmetic chains with truncation / Обратные цепочки действий и зачёркивание цифр

**Difficulty profile:** D3–D5

**Scope:** Recover an initial integer after multiplication, deletion of the last digit, and further operations.

**Corpus examples:**

- **D4 · corpus item 780** — Вовочка задумал целое число, умножил его на 13, зачеркнул последнюю цифру результата, полученное число умножил на 7, потом опять зачеркнул последнюю цифру и получил число 21. Какое число задумал Вовочка?  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 898._
- **D4 · corpus item 786** — Капитан Кежд загадал число. Он умножил его на 9, зачеркнул последнюю цифру, умножил на 7, снова зачеркнул последнюю цифру и получил 3. Какое число он загадал?  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 904._
- **D4 · template-derived illustration** — Число умножили на 11, отбросили последнюю цифру результата, затем умножили на 6 и снова отбросили последнюю цифру. Получили 18. Найдите исходное число, если решение единственно.

**Generator templates:**

1. `A08-T1` — {name} задумал целое число, умножил его на {a}, зачеркнул последнюю цифру, умножил на {b}, снова зачеркнул последнюю цифру и получил {c}. Какое число он задумал?
   - Parameters: a,b,c — положительные целые.
   - Validation: Обратные интервалы дают ровно одно целое решение.
1. `A08-T2` — Операцию «умножить на {a} и отбросить последнюю цифру» применили дважды и получили {c}. Найдите исходное число.
   - Parameters: a,c.
   - Validation: У преобразования ровно один допустимый прообраз.

## B. Algebraic modelling / Алгебраические модели (10 themes)

### B01 — Linear equations with nested operations / Линейные уравнения с несколькими действиями

**Difficulty profile:** D1–D3

**Scope:** Solve a one-variable linear equation embedded in a chain of arithmetic operations.

**Corpus examples:**

- **D1 · corpus item 1401** — Найдите значение x в примере: 1846 = (188 + 209 × x) / 3 + 111  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1561._
- **D1 · corpus item 1411** — Найдите значение x: 296 + (2015 − 3222 : x) × 14 = 26000  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1571._
- **D1 · corpus item 1416** — Найдите значение x: 2346 - (1962 - x × 19) × 2 - 239 = 311  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1576._

**Generator templates:**

1. `B01-T1` — Найдите x: {a}+({b}-{c}:x)·{d}={e}.
   - Parameters: Сначала выбирается ненулевой целый x, затем вычисляется e.
   - Validation: Все деления точные; решение единственно.
1. `B01-T2` — Найдите x: {a}-({b}-x·{c})·{d}-{e}={f}.
   - Parameters: Целые параметры.
   - Validation: Единственное целое решение.

### B02 — Age sums and passage of time / Суммарный возраст и изменение с годами

**Difficulty profile:** D1–D2

**Scope:** Use the increase of total age to determine the number of people or individual ages.

**Corpus examples:**

- **D1 · corpus item 97** — Возраст нескольких друзей в сумме составляет 74 года. Через 4 года он будет составлять 94 года. Сколько этих друзей?  
  _Source: `15-минутки/Март 2026/04.03.2026.pdf`; source line 140._
- **D1 · corpus item 102** — Возраст нескольких друзей в сумме составляет 65 лет. Через 3 года он будет составлять 86 лет. Сколько этих друзей?  
  _Source: `15-минутки/Март 2026/05.03.2026.pdf`; source line 148._
- **D1 · corpus item 1539** — Возраст нескольких друзей в сумме составляет 62 года. Через 3 года он будет составлять 80 лет. Сколько этих друзей?  
  _Source: `Сб В классе/1 занятие.docx`; source line 1702._

**Generator templates:**

1. `B02-T1` — Суммарный возраст нескольких друзей равен {S}. Через {t} лет он станет {T}. Сколько друзей?
   - Parameters: T-S делится на t.
   - Validation: n=(T-S)/t — положительное целое.
1. `B02-T2` — Сейчас сумма возрастов {n} детей равна {S}. Какой она будет через {t} лет?
   - Parameters: n,S,t>0.
   - Validation: Ответ S+n·t.

### B03 — Ratio, parts, and multiplicative comparison / Отношения, части и «в несколько раз»

**Difficulty profile:** D1–D3

**Scope:** Find quantities from a multiplicative relation and a total or difference.

**Corpus examples:**

- **D2 · corpus item 916** — 1. В комнату влетели насекомые. Пчел и ос вместе оказалось в 2 раза больше, чем мух и комаров вместе. Пчел влетело 9 пар, что на 1 пару больше, чем ос. Количество комаров на 5 меньше, чем мух. Сколько комаров влетело в комнату?  
  _Source: `Доп ДЗ/Доп ДЗ 03.docx`; source line 1043._
- **D1 · corpus item 823** — Оля знает в 5 раз больше слов, чем Катя. Катя знает на 64 слова меньше, чем Оля  
  _Source: `Доп ДЗ/Доп ДЗ 01.docx`; source line 944._
- **D1 · corpus item 825** — Лена знает в 6 раз больше слов, чем Аня. Аня знает на 50 слов меньше, чем Лена  
  _Source: `Доп ДЗ/Доп ДЗ 01.docx`; source line 946._

**Generator templates:**

1. `B03-T1` — {A} в {k} раз больше, чем {B}, а вместе у них {S}. Сколько у каждого?
   - Parameters: S делится на k+1.
   - Validation: Оба ответа положительные целые.
1. `B03-T2` — {A} в {k} раз больше, чем {B}, и на {D} больше. Найдите обе величины.
   - Parameters: D делится на k-1.
   - Validation: Положительные целые решения.

### B04 — Shared expenses, loans, and reimbursement / Совместные траты, займы и взаиморасчёты

**Difficulty profile:** D2–D4

**Scope:** Reconstruct final net contributions when participants paid, borrowed, or transferred money.

**Corpus examples:**

- **D3 · corpus item 107** — Маша и Катя хотят вместе заплатить 7200 рублей, разделив затраты поровну. Маша дала Кате взаймы 9000 рублей, Катя заплатила 4100 рублей, а Маша - оставшиеся деньги. Сколько денег должна дать Катя Маше, чтобы никто никому не был должен?  
  _Source: `15-минутки/Март 2026/06.03.2026.pdf`; source line 156._
- **D3 · corpus item 112** — Саша и Игорь хотят вместе заплатить 8400 рублей, разделив затраты поровну. Саша дал Игорю взаймы 12000 рублей, Игорь заплатил 3700 рублей, а Саша - оставшиеся деньги. Сколько денег должен дать Игорь Саше, чтобы никто никому не был должен?  
  _Source: `15-минутки/Март 2026/07.03.2026.pdf`; source line 164._
- **D3 · corpus item 211** — Дети хотели подарить Ралине подарок. Марк дал 1230 рублей, Максим дал 1270 рублей, Алина 2390 рублей, сколько дал Кирилл неизвестно. На все эти деньги купили подарок. Затем дети решили, что все должны были заплатить поровну. Оказалось, что Кирилл никому ничего не должен, и ему тоже не должны. Сколько денег заплатил Кирилл?  
  _Source: `2025-all.pdf`; source line 323._

**Generator templates:**

1. `B04-T1` — {A} и {B} должны заплатить {S} поровну. {A} дал {B} взаймы {L}, {B} заплатил {p}, а {A} — остальное. Сколько должен вернуть {B}?
   - Parameters: Денежные суммы — целые.
   - Validation: Займ учитывается отдельно от вклада в покупку.
1. `B04-T2` — Несколько друзей купили подарок. Известны вклады всех, кроме одного; после перерасчёта неизвестный никому не должен. Найдите его вклад.
   - Parameters: 3–5 участников.
   - Validation: Неизвестный вклад равен равной доле.

### B05 — Heads-and-legs systems / Задачи на головы и ноги

**Difficulty profile:** D1–D3

**Scope:** Determine counts of two species or vehicle types from totals of heads and legs or wheels.

**Corpus examples:**

- **D1 · corpus item 858** — 3. На одном из пастбищ Татуина пасутся овцы и курицы. У овец и куриц вместе 36 голов и 100 ног. Сколько овец и сколько куриц?  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 982._
- **D2 · corpus item 863** — 8. Среди невиданных зверей, оставивших следы на неведомых дорожках, было стадо одноглавых Тридцатичетырёхножек и трёхголовых Драконов. Всего в стаде 286 ног и 31 голова. Сколько лап у трёхголового Дракона?  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 987._
- **D2 · corpus item 864** — 9. Несколько гномов, навьючив свою поклажу на пони, отправились в дальний путь. Их заметили тролли, которые насчитали в караване 36 ног и 15 голов. Сколько было гномов, и сколько пони?  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 988._

**Generator templates:**

1. `B05-T1` — В хозяйстве {H} голов и {L} ног. Есть только {animal1} с {l1} ногами и {animal2} с {l2} ногами. Сколько каждого вида?
   - Parameters: l1≠l2.
   - Validation: Система имеет единственное неотрицательное целое решение.
1. `B05-T2` — В караване люди и животные: всего {H} голов и {L} ног. Найдите число людей и животных.
   - Parameters: 2 и 4 ноги.
   - Validation: Выполнены ограничения по чётности и границам.

### B06 — Price systems and mixed purchases / Системы цен и смешанные покупки

**Difficulty profile:** D2–D4

**Scope:** Infer item prices or quantities from two or more orders with the same or related totals.

**Corpus examples:**

- **D3 · corpus item 293** — Илья заказал в ресторане 2 чизбургера, 3 ролла и 6 порций картошки. Официант перепутал заказ и принес ему 2 порции картошки, 3 чизбургера и 6 роллов. При этом стоимость заказа осталась прежней. Расположите чизбургер, ролл и картошку в порядке возрастания их цен, если известно, что чизбургер дороже ролла  
  _Source: `239-5_comb.pdf`; source line 408._
- **D3 · corpus item 311** — Сережа заказал в кафе 3 хачапури, 4 бифштекса и 6 порций картошки. Официант перепутал заказ и принес ему 3 порции картошки, 4 хачапури и 6 бифштексов. При этом стоимость заказа осталась прежней. Расположите хачапури, бифштекс и картошку в порядке возрастания их цены, если известно, что хачапури дороже бифштек-  
  _Source: `239-5_comb.pdf`; source line 426._
- **D3 · corpus item 2116** — Илья заказал в ресторане 2 чизбургера, 3 ролла и 6 порций картошки. Официант перепутал заказ и принес ему 2 порции картошки, 3 чизбургера и 6 роллов. При этом стоимость заказа осталась прежней. Расположите чизбургер, ролл и картошку в порядке возрастания их цен, если известно, что чизбургер дороже ролла  
  _Source: `Чт ДЗ/ДЗ 01 от 05.02.2026.docx`; source line 2345._

**Generator templates:**

1. `B06-T1` — Первый заказ: {a1} A, {b1} B и {c1} C. Второй: {a2} A, {b2} B и {c2} C; суммы равны. Найдите требуемую цену или отношение цен.
   - Parameters: Целые коэффициенты.
   - Validation: Запрашиваемая величина определяется однозначно.
1. `B06-T2` — За {a} товаров A и {b} товаров B заплатили {S1}, а за {c} A и {d} B — {S2}. Найдите цены.
   - Parameters: Определитель системы ненулевой.
   - Validation: Цены положительные целые.

### B07 — Work rates and joint productivity / Производительность и совместная работа

**Difficulty profile:** D2–D4

**Scope:** Combine rates, infer individual rates, or compare completion times.

**Corpus examples:**

- **D3 · corpus item 221** — Кирилл и Максим любят составлять олимпиады для 5 класса. Кирилл составляет 34 олимпиады за 6 часов, а Максим составляет 13 олимпиад за 3 часа. Сколько олимпиад они составят вместе за 1 час? У каждого мальчика на составление одной олимпиады уходит одно и то же время, каждый составляет свою олимпиаду и задачами с  
  _Source: `2025-all.pdf`; source line 333._
- **D3 · corpus item 244** — Кирилл и Максим любят составлять олимпиады для 5 класса. Кирилл составляет 11 олимпиады за 3 часа, а Максим составляет 32 олимпиады за 6 часов. Сколько олимпиад они составят вместе за 1 час? У каждого мальчика на составление одной олимпиады уходит одно и то же время, каждый составляет свою олимпиаду и задачами  
  _Source: `2025-all.pdf`; source line 356._
- **D3 · corpus item 1122** — 2. Коля распилил за 7 часов шахматную доску размера 8 х 8 на двухклеточные прямоугольники (доминошки). За какое время он распилит доску a) 12 × 9; b) 21 × 21; c) 31 × 31 (без угловой) на трехклеточные уголки? Коля пилит с постоянной скоростью. Фигурки можно поворачивать и переворачивать, он пилит без остатка и наложений фигур  
  _Source: `Доп ДЗ/Доп ДЗ 07.docx`; source line 1261._

**Generator templates:**

1. `B07-T1` — {A} делает {m} изделий за {t1} ч, {B} — {n} изделий за {t2} ч. Сколько они сделают вместе за {T} ч?
   - Parameters: Скорости постоянны.
   - Validation: Итоговое количество целое либо формат ответа допускает дробь.
1. `B07-T2` — Два работника вместе выполняют работу за {T}, первый один — за {T1}. За сколько справится второй?
   - Parameters: 1/T-1/T1>0.
   - Validation: Полученное время положительно.

### B08 — Percentages, concentration, and conserved quantity / Проценты, концентрации и сохранение вещества

**Difficulty profile:** D2–D4

**Scope:** Use a conserved non-water or solute amount while total mass or percentage changes.

**Corpus examples:**

- **D2 · corpus item 1616** — Свежий арбуз весил 10 килограмм и на 99% состоял из воды. На базе арбуз подсох (часть воды испарилась) и в нем стало 98% воды  
  _Source: `Сб В классе/12 занятие.docx`; source line 1788._
- **D2 · corpus item 1697** — "То" да "это", да половина "того" да "этого" - сколько это будет процентов от трёх четвертей "того" да "этого"?  
  _Source: `Сб В классе/4 занятие.docx`; source line 1878._
- **D3 · corpus item 1514** — Представители литературного клуба пили кофе с молоком. Каждый из них выпил одинаковое количество жидкости, причём президенту клуба досталась четверть всего кофе и одна шестая часть всего молока. Сколько всего людей в литературном клубе?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1674._

**Generator templates:**

1. `B08-T1` — Продукт массой {M} кг содержит {p1}% воды. После высыхания воды стало {p2}%. Какова новая масса?
   - Parameters: p2<p1<100.
   - Validation: Сухое вещество M·(1-p1/100) сохраняется.
1. `B08-T2` — Из сосуда A перелили стакан в B, затем такой же объём обратно. Чего больше: вещества A в B или B в A?
   - Parameters: Объёмы переливов равны.
   - Validation: Решение основано на сохранении количества вещества.

### B09 — Direct proportion: mass, length, cost, and quantity / Прямая пропорциональность величин

**Difficulty profile:** D1–D3

**Scope:** Scale weight, cost, material, or count proportionally to area, length, or number of equal units.

**Corpus examples:**

- **D2 · corpus item 168** — Для забора нужны доски длиной 75 сантиметров в количестве 112 i, я штук. В магазине продаются доски длиной 4 метра. Сколько досок надо купить, чтобы построить забор?  
  _Source: `15-минутки/Март 2026/21.03.2026.pdf`; source line 256._
- **D2 · corpus item 867** — Для забора нужны доски длиной 75 сантиметров в количестве 112 штук. В магазине продаются доски длиной 4 метра. Сколько досок надо купить, чтобы построить забор?  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 991._
- **D1 · corpus item 1227** — 13. Лист железа размерами 20 см × 30 см весит 1200 г. Сколько весят 5 квадратных метров такого железа?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1372._

**Generator templates:**

1. `B09-T1` — Лист площадью {A1} весит {M1}. Сколько весит лист площадью {A2}?
   - Parameters: Единицы совместимы.
   - Validation: Перед пропорцией выполнен перевод единиц.
1. `B09-T2` — Нужно {n} деталей длиной {l}; заготовки имеют длину {L}. Сколько заготовок купить?
   - Parameters: Положительные длины.
   - Validation: Используются floor(L/l) деталей из заготовки и округление вверх.

### B10 — Transfers that create a prescribed difference / Передачи денег и изменение разности

**Difficulty profile:** D1–D3

**Scope:** Find a transfer between two initially equal or known amounts so that the final difference is prescribed.

**Corpus examples:**

- **D1 · corpus item 117** — У Оли и Нади денег поровну. Сколько денег должна отдать Надя Оле, чтобы у нее стало на 12 рублей меньше, чем у Оли?  
  _Source: `15-минутки/Март 2026/09.03.2026.pdf`; source line 172._
- **D1 · corpus item 122** — У Сережи и Гриши денег поровну. Сколько денег должен отдать Гриша Сереже, чтобы у него стало на 13 рублей меньше, чем у Сережи?  
  _Source: `15-минутки/Март 2026/10.03.2026.pdf`; source line 180._
- **D1 · corpus item 1686** — У Анфисы и Акулины денег поровну. Сколько денег должна отдать Акулина  
  _Source: `Сб В классе/3 занятие.docx`; source line 1864._

**Generator templates:**

1. `B10-T1` — У {A} и {B} денег поровну. Сколько должен передать {B}, чтобы у него стало на {D} меньше?
   - Parameters: D — чётное.
   - Validation: Передача равна D/2.
1. `B10-T2` — У двух участников разница {d0}. Какую сумму передать от большего к меньшему, чтобы разница стала {d1}?
   - Parameters: d0 и d1 одной чётности.
   - Validation: Передача (d0-d1)/2 неотрицательна.

## C. Digits and decimal notation / Цифры и десятичная запись (12 themes)

### C01 — Counting even or odd integers in an interval / Подсчёт чётных и нечётных чисел в промежутке

**Difficulty profile:** D1–D2

**Scope:** Count integers of prescribed parity in an inclusive interval.

**Corpus examples:**

- **D1 · corpus item 95** — Сколько нечётных чисел от 21 до 301?  
  _Source: `15-минутки/Март 2026/04.03.2026.pdf`; source line 138._
- **D1 · corpus item 100** — Сколько нечётных чисел от 35 до 275?  
  _Source: `15-минутки/Март 2026/05.03.2026.pdf`; source line 146._
- **D1 · corpus item 105** — Сколько четных чисел от 318 до 1006?  
  _Source: `15-минутки/Март 2026/06.03.2026.pdf`; source line 154._

**Generator templates:**

1. `C01-T1` — Сколько чётных чисел от {L} до {R} включительно?
   - Parameters: L≤R.
   - Validation: Найдены первый и последний подходящие члены прогрессии.
1. `C01-T2` — Сколько нечётных чисел строго между {L} и {R}?
   - Parameters: Целые границы.
   - Validation: Тип включения концов указан явно.

### C02 — Counting numbers that contain a digit / Числа, содержащие заданную цифру

**Difficulty profile:** D2–D4

**Scope:** Count numbers in a range that contain at least one occurrence of a specified digit, possibly with parity restrictions.

**Corpus examples:**

- **D2 · corpus item 3** — Сколько нечётных чисел в промежутке от 215 до 983, содержащих цифру 7?  
  _Source: `15-минутки/Апрель 2026/02.04.2026.pdf`; source line 7._
- **D2 · corpus item 33** — Сколько четных в промежутке от 104 до 640 чисел содержащих цифру 9?  
  _Source: `15-минутки/Апрель 2026/14.04.2026.pdf`; source line 58._
- **D2 · corpus item 51** — Сколько нечетных чисел от 100 до 1000 содержит хотя бы одну цифру 3  
  _Source: `15-минутки/Апрель 2026/17.04.2026.pdf`; source line 85._

**Generator templates:**

1. `C02-T1` — Сколько чисел от {L} до {R} содержат цифру {d}?
   - Parameters: Диапазон удобен для разбиения по разрядам.
   - Validation: При подсчёте дополнения ведущие нули не считаются.
1. `C02-T2` — Сколько нечётных {k}-значных чисел содержат хотя бы одну цифру {d}?
   - Parameters: d∈{0,…,9}.
   - Validation: Отдельно учтены первая и последняя цифры.

### C03 — Counting numbers that avoid a digit / Числа без заданной цифры

**Difficulty profile:** D2–D4

**Scope:** Count numbers in an interval whose decimal representation avoids one or more digits.

**Corpus examples:**

- **D2 · corpus item 58** — Сколько существует нечетных чисел больших 2139 не содержащих цифру 1, но меньших 4329?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 95._
- **D2 · corpus item 78** — Сколько существует нечетных чисел больших 2139 не содержащих цифру 4, но меньших 4329?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 118._
- **D2 · corpus item 165** — Сколько в промежутке от 507 до 835 чисел не содержащих цифру 7?  
  _Source: `15-минутки/Март 2026/21.03.2026.pdf`; source line 253._

**Generator templates:**

1. `C03-T1` — Сколько чисел от {L} до {R} не содержат цифру {d}?
   - Parameters: Целые границы.
   - Validation: Используется позиционный подсчёт или digit DP без ведущих нулей.
1. `C03-T2` — Сколько нечётных чисел между {L} и {R} не содержат цифры {d1} и {d2}?
   - Parameters: Две запрещённые цифры.
   - Validation: Одновременно выполнены ограничение диапазона и нечётность.

### C04 — Frequency of a digit in concatenated integers / Частота цифры в записи подряд идущих чисел

**Difficulty profile:** D2–D4

**Scope:** Count all occurrences of a digit when a consecutive range of integers is written out.

**Corpus examples:**

- **D2 · corpus item 8** — Натуральные числа от 1 до 120 выписаны подряд друг за другом. Сколько раз в записи всех чисел встречается цифра 2?  
  _Source: `15-минутки/Апрель 2026/03.04.2026.pdf`; source line 15._
- **D2 · corpus item 1412** — Натуральные числа от 1 до 199 выписаны подряд друг за другом. Сколько раз в записи всех чисел встречается цифра 7?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1572._
- **D3 · corpus item 1417** — Натуральные числа от 100 до 399 выписаны подряд друг за другом. Сколько раз в записи всех чисел встречается цифра 5? 4.Какое из чисел больше и на сколько: 6767 × 1212 (первое) или 6766 × 1213 (второе)?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1577._

**Generator templates:**

1. `C04-T1` — Числа от {L} до {R} выписали подряд. Сколько раз встретилась цифра {d}?
   - Parameters: Диапазон допускает разбиение по длине записи.
   - Validation: Единицы, десятки и сотни посчитаны отдельно.
1. `C04-T2` — Сколько раз цифра {d} встречается в записи всех натуральных чисел от 1 до {N}?
   - Parameters: N около круглой границы.
   - Validation: Ведущие нули не учитываются.

### C05 — Local digit rules based on adjacent parity / Свойства соседних цифр и их чётность

**Difficulty profile:** D2–D3

**Scope:** Classify or count numbers whose neighboring digits satisfy a parity relation.

**Corpus examples:**

- **D3 · corpus item 56** — Будем называть число однообразным, если какие-то две соседние цифры имеют одинаковую четность. Найдите сумму всех однообразных чисел среди данных: 101010, 104060, 674936, 1003, 1432567  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 93._
- **D3 · corpus item 76** — Будем называть число однообразным, если какие-то две соседние цифры имеют одинаковую четность. Найдите сумму всех однообразных чисел среди данных: 232323, 1043874, 6949367, 1003, 143256  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 116._
- **D3 · corpus item 1155** — 8. Будем называть число однообразным, если у него есть две соседние цифры одной чётности. Найдите сумму всех однообразных чисел среди следующих: 120304, 135724, 246813, 1112, 908172  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1297._

**Generator templates:**

1. `C05-T1` — Назовём число весёлым, если соседние цифры имеют разную чётность. Найдите сумму весёлых чисел из списка.
   - Parameters: 5–8 чисел-кандидатов.
   - Validation: Локальное свойство проверяется для каждой соседней пары.
1. `C05-T2` — Сколько {k}-значных чисел имеют одинаковую чётность у каждой пары соседних цифр?
   - Parameters: k≥2.
   - Validation: Первая цифра не ноль.

### C06 — First and last digits of expressions / Первая и последняя цифры результата

**Difficulty profile:** D1–D4

**Scope:** Determine terminal or leading digits using modular arithmetic or estimation.

**Corpus examples:**

- **D1 · corpus item 114** — Какой цифрой оканчивается сумма 418 × 2026 + 7? А начинается?  
  _Source: `15-минутки/Март 2026/09.03.2026.pdf`; source line 169._
- **D1 · corpus item 119** — Какой цифрой оканчивается сумма 127 × 2001 + 9? А начинается?  
  _Source: `15-минутки/Март 2026/10.03.2026.pdf`; source line 177._
- **D1 · corpus item 1296** — Какой цифрой оканчивается сумма 418 × 2026 + 7? А начинается?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1456._

**Generator templates:**

1. `C06-T1` — Какой цифрой оканчивается {a}^{n}+{b}?
   - Parameters: a,n,b — целые.
   - Validation: Цикл последних цифр проверен.
1. `C06-T2` — Какой цифрой начинается выражение {expression}? Ответ обоснуйте.
   - Parameters: Выражение допускает узкую оценку порядка величины.
   - Validation: Полное вычисление не требуется.

### C07 — Long numbers with prescribed digit sum / Многозначные числа с заданной суммой цифр

**Difficulty profile:** D3–D5

**Scope:** Count long decimal numbers with a small digit sum, optionally with fixed positions.

**Corpus examples:**

- **D4 · corpus item 15** — Сколько существует девяностозначных чисел, сумма цифр которых равна 17, у которых в разряде сотен стоит 2, в разряде тысяч - 4, а в разряде миллионов - 9?  
  _Source: `15-минутки/Апрель 2026/04.04.2026.pdf`; source line 25._
- **D3 · corpus item 27** — Сколько существует стозначных чисел, сумма цифр которых равна 14, у которых в разряде сотен стоит 3, и в разряде тысяч - 3, а в разряде миллионов - 6?  
  _Source: `15-минутки/Апрель 2026/08.04.2026.pdf`; source line 46._
- **D3 · corpus item 32** — Сколько существует стозначных чисел, сумма цифр которых равна 3  
  _Source: `15-минутки/Апрель 2026/13.04.2026.pdf`; source line 54._

**Generator templates:**

1. `C07-T1` — Сколько существует {n}-значных чисел с суммой цифр {S}?
   - Parameters: S относительно мало.
   - Validation: Первая цифра ненулевая; ограничения цифр ≤9 проверены.
1. `C07-T2` — Сколько {n}-значных чисел имеют сумму цифр {S}, а в разрядах {positions} стоят {digits}?
   - Parameters: Сумма фиксированных цифр ≤S.
   - Validation: Вклад фиксированных разрядов вычтен; ведущая цифра корректна.

### C08 — Positional inequalities between digits / Сравнение цифр в разных разрядах

**Difficulty profile:** D2–D4

**Scope:** Count numbers whose digits in specified positions satisfy inequalities.

**Corpus examples:**

- **D3 · corpus item 62** — Сколько существует нечетных шестизначных чисел, в записи каждого из которых первая цифра меньше третьей?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 99._
- **D3 · corpus item 82** — Сколько существует четных шестизначных чисел, в записи каждого из которых первая цифра меньше пятой?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 122._
- **D2 · corpus item 1152** — 5. Сколько существует нечётных четырёхзначных чисел, у которых первая цифра больше последней?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1294._

**Generator templates:**

1. `C08-T1` — Сколько {k}-значных чисел, у которых первая цифра меньше третьей?
   - Parameters: k≥3.
   - Validation: Первая цифра 1–9, остальные 0–9.
1. `C08-T2` — Сколько чётных {k}-значных чисел удовлетворяют d1<d{j}?
   - Parameters: 2≤j≤k.
   - Validation: Независимо учтена чётность последней цифры.

### C09 — Numbers formed from a multiset of digits / Числа из заданного набора цифр

**Difficulty profile:** D1–D4

**Scope:** Count distinct numbers or arrangements formed from supplied digits with repetition.

**Corpus examples:**

- **D1 · corpus item 1541** — Сколько существует различных комбинаций чисел можно составить из набора цифр: a) 12345; b) 11234; c) 11112; d) 1112234; e) 122333444455555  
  _Source: `Сб В классе/10 занятие.docx`; source line 1707._
- **D1 · corpus item 1577** — Сколько четырехзначных чисел из набора: a) две пары чисел от 1-9; b) две различные пары чисел от 1-9 ; c) две пары чисел от 0-9;  
  _Source: `Сб В классе/11 занятие.docx`; source line 1746._
- **D1 · corpus item 29** — Сколько существует различных комбинаций чисел можно составить из набора цифр: AEE а 112113114515 Зи, нетАЙ :  
  _Source: `15-минутки/Апрель 2026/13.04.2026.pdf`; source line 51._

**Generator templates:**

1. `C09-T1` — Сколько различных чисел можно составить из цифр {multiset}, используя каждую ровно один раз?
   - Parameters: В наборе могут быть повторы.
   - Validation: Записи с ведущим нулём исключены.
1. `C09-T2` — Сколько {k}-значных чисел можно составить из набора {digits}, если повторения {allowed}?
   - Parameters: Правило повторений задано явно.
   - Validation: Отдельно обработана первая цифра.

### C10 — Cryptarithms and missing digits / Числовые ребусы и пропущенные цифры

**Difficulty profile:** D2–D5

**Scope:** Restore digits hidden by stars in a valid arithmetic operation or divisibility condition.

**Corpus examples:**

- **D2 · corpus item 220** — Получилось 4244 + 12495 = 15648 . Восстановите пример. В ответ  
  _Source: `2025-all.pdf`; source line 332._
- **D2 · corpus item 243** — Получилось 3323 + 10335 = 13669 . Восстановите пример. В ответ  
  _Source: `2025-all.pdf`; source line 355._
- **D4 · corpus item 792** — Вовочка написал в тетради число 65349*0712 в качестве примера числа, которое делится: а) на 9; б) на 3. (На месте звёздочки когда-то была написана цифра, а теперь там пятно от сладкого чая.) Помогите Вовочке восстановить пропущенную цифру. Укажите все возможные варианты!  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 910._

**Generator templates:**

1. `C10-T1` — В верном сложении *{a}** + *{b}** = {c}*{d}** звёздочки обозначают цифры. Найдите их сумму.
   - Parameters: Пример генерируется из корректного сложения по столбцам.
   - Validation: Скрытые цифры или их сумма определены однозначно.
1. `C10-T2` — В числе {pattern} пропущена цифра. Восстановите все варианты, при которых число делится на {m}.
   - Parameters: Одна или две звёздочки; m∈{3,9,11}.
   - Validation: Перебраны все цифры 0–9.

### C11 — Constructing numbers with a common suffix / Числа, различающиеся только первой цифрой

**Difficulty profile:** D2–D4

**Scope:** Construct several distinct numbers sharing all but the leading digit and meeting a sum.

**Corpus examples:**

- **D2 · corpus item 61** — Придумайте 3 различных числа с суммой 999, которые различаются только первой цифрой. В ответ запишите все три числа  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 98._
- **D2 · corpus item 81** — Придумайте 3 различных числа с суммой 801, которые различаются только первой цифрой. В ответ запишите все три числа  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 121._
- **D2 · corpus item 833** — Придумайте три различных трёхзначных числа с суммой 817, которые отличаются друг от друга только первой цифрой. В ответ запишите все три числа  
  _Source: `Доп ДЗ/Доп ДЗ 01.docx`; source line 954._

**Generator templates:**

1. `C11-T1` — Придумайте {k} различных {n}-значных чисел с суммой {S}, которые различаются только первой цифрой.
   - Parameters: k≤9; сумма согласована с общим суффиксом.
   - Validation: Первые цифры различны и ненулевые; суффикс одинаков.
1. `C11-T2` — Найдите все тройки чисел вида aX, bX, cX с суммой {S}.
   - Parameters: X — общий (n-1)-значный суффикс.
   - Validation: 0≤X<10^(n-1), a,b,c∈{1,…,9}.

### C12 — Recovering a consecutive block from total digit count / Восстановление блока последовательных чисел по числу цифр

**Difficulty profile:** D3–D4

**Scope:** Find the first integer when a fixed number of consecutive integers uses a specified total number of digits.

**Corpus examples:**

- **D3 · corpus item 197** — В ряд выписали 90 подряд идущих натуральных чисел. Петя заметил, что выписана 261 7. ;  
  _Source: `15-минутки/Март 2026/30.03.2026.pdf`; source line 303._
- **D3 · corpus item 1377** — В ряд выписали 120 подряд идущих натуральных чисел. Миша заметил, что выписано 372 цифры. Какое число было выписано первым?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1537._
- **D3 · corpus item 1382** — В ряд выписали 150 подряд идущих натуральных чисел. Оля заметила, что выписано 492 цифры. Какое число было выписано первым?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1542._

**Generator templates:**

1. `C12-T1` — Выписали {k} подряд идущих натуральных чисел и получили {D} цифр. Какое число было первым?
   - Parameters: Блок пересекает не более одной границы 10^m.
   - Validation: Начальное число определяется однозначно.
1. `C12-T2` — Подряд записали числа от {a} до {b}. Сколько цифр использовали?
   - Parameters: Диапазон может пересекать границы разрядности.
   - Validation: Оба конца включены.

## D. Number theory / Теория чисел (9 themes)

### D01 — Counting multiples in an interval / Подсчёт кратных в промежутке

**Difficulty profile:** D1–D2

**Scope:** Count integers divisible by m in a specified inclusive or strict interval.

**Corpus examples:**

- **D1 · corpus item 26** — Сколько существует кратных 7 чисел больших 2139, но меньших 4329?  
  _Source: `15-минутки/Апрель 2026/08.04.2026.pdf`; source line 45._
- **D1 · corpus item 146** — Сколько чисел от 5 до 898 делятся на 4?  
  _Source: `15-минутки/Март 2026/17.03.2026.pdf`; source line 222._
- **D1 · corpus item 941** — 2. Сколько в промежутке от 187 до 600 чисел делящихся на 10?  
  _Source: `Доп ДЗ/Доп ДЗ 04.docx`; source line 1071._

**Generator templates:**

1. `D01-T1` — Сколько чисел от {L} до {R} делятся на {m}?
   - Parameters: L≤R, m>0.
   - Validation: Используется floor(R/m)-floor((L-1)/m).
1. `D01-T2` — Сколько кратных {m} чисел больше {L}, но меньше {R}?
   - Parameters: Строгие границы.
   - Validation: Кратные на концах обработаны корректно.

### D02 — Divisibility tests and missing residues / Признаки делимости

**Difficulty profile:** D1–D3

**Scope:** Use digit-based divisibility rules for 3, 9, 11, 2, 5, and related moduli.

**Corpus examples:**

- **D3 · corpus item 792** — Вовочка написал в тетради число 65349*0712 в качестве примера числа, которое делится: а) на 9; б) на 3. (На месте звёздочки когда-то была написана цифра, а теперь там пятно от сладкого чая.) Помогите Вовочке восстановить пропущенную цифру. Укажите все возможные варианты!  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 910._
- **D1 · corpus item 794** — Делится ли число 32561698 на 12? Решите эту задачу: а) с помощью признака делимости на 4; б) с помощью признака делимости на 3  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 912._
- **D2 · corpus item 798** — Замените звездочки в записи числа 72*4* цифрами так, чтобы это число делилось на 45. Укажите все возможные варианты!  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 916._

**Generator templates:**

1. `D02-T1` — Подберите цифру * в числе {pattern}, чтобы оно делилось на {m}.
   - Parameters: m∈{3,9,11}.
   - Validation: Перечислены все допустимые цифры.
1. `D02-T2` — Какие числа из списка делятся на {m}? Обоснуйте признаком делимости.
   - Parameters: Есть делящиеся и неделящиеся примеры.
   - Validation: Проверка не требует полного деления.

### D03 — Factor pairs with minimum sum / Минимальная сумма сомножителей

**Difficulty profile:** D2–D4

**Scope:** Among integer factor pairs of a fixed product, minimize the sum under stated constraints.

**Corpus examples:**

- **D3 · corpus item 129** — Попытайтесь получить 360, перемножая два целых сомножителя, один из которых нечетный. Таких пар несколько. Ответ - минимальная сумма таких чисел  
  _Source: `15-минутки/Март 2026/12.03.2026.pdf`; source line 193._
- **D3 · corpus item 134** — Попытайтесь получить 504, перемножая два целых сомножителя, один из которых нечетный. Таких пар несколько. Ответ - минимальная сумма таких чисел  
  _Source: `15-минутки/Март 2026/13.03.2026.pdf`; source line 201._
- **D4 · corpus item 148** — Попытайтесь получить 180, перемножая два целых сомножителя, один из которых I нечетный. Таких пар несколько. Ответ - минимальная сумма таких сомножителей  
  _Source: `15-минутки/Март 2026/17.03.2026.pdf`; source line 224._

**Generator templates:**

1. `D03-T1` — Представьте {N} произведением двух положительных целых сомножителей. Найдите минимальную возможную сумму.
   - Parameters: N — составное.
   - Validation: Проверяется ближайшая к √N допустимая пара делителей.
1. `D03-T2` — Найдите минимальную сумму сомножителей ab={N}, если один из них должен быть нечётным.
   - Parameters: Есть допустимые пары.
   - Validation: Условие чётности проверено для всех кандидатов около √N.

### D04 — Constrained factorization / Разложения с ограничениями на сомножители

**Difficulty profile:** D2–D5

**Scope:** Find or rule out factor pairs whose decimal form, parity, or square status obeys restrictions.

**Corpus examples:**

- **D3 · corpus item 125** — Попытайтесь получить 10000, перемножая два целых сомножителя, в каждом из которых не было бы ни одного нуля. Ответ - сумма этих чисел, если они есть, и "-1"  
  _Source: `15-минутки/Март 2026/11.03.2026.pdf`; source line 186._
- **D3 · corpus item 129** — Попытайтесь получить 360, перемножая два целых сомножителя, один из которых нечетный. Таких пар несколько. Ответ - минимальная сумма таких чисел  
  _Source: `15-минутки/Март 2026/12.03.2026.pdf`; source line 193._
- **D3 · corpus item 134** — Попытайтесь получить 504, перемножая два целых сомножителя, один из которых нечетный. Таких пар несколько. Ответ - минимальная сумма таких чисел  
  _Source: `15-минутки/Март 2026/13.03.2026.pdf`; source line 201._

**Generator templates:**

1. `D04-T1` — Разложите {N}=ab так, чтобы оба сомножителя были чётными; минимизируйте a+b.
   - Parameters: N делится на 4.
   - Validation: a,b — положительные целые.
1. `D04-T2` — Можно ли представить {N}=ab так, чтобы ни в a, ни в b не было цифры 0?
   - Parameters: N выбран для существования или невозможности.
   - Validation: Дана конструкция либо доказательство невозможности.

### D05 — Prime numbers used as parameters / Простые числа в условиях задач

**Difficulty profile:** D1–D3

**Scope:** Identify prime values and use them as dimensions, bounds, or counts.

**Corpus examples:**

- **D2 · corpus item 170** — Сколько перегородок в квадрате наибольшего простого двузначного числа?  
  _Source: `15-минутки/Март 2026/23.03.2026.pdf`; source line 261._
- **D1 · corpus item 1365** — Сколько перегородок в прямоугольнике со сторонами равными двум наименьшим простым трехзначным числам?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1525._
- **D2 · template-derived illustration** — Найдите наибольшее простое двузначное число и вычислите число внутренних перегородок в квадратной сетке с такой стороной.

**Generator templates:**

1. `D05-T1` — Найдите наибольшее двузначное простое число и используйте его как сторону квадрата в следующем вычислении.
   - Parameters: Граница простых чисел.
   - Validation: Простота числа обоснована.
1. `D05-T2` — Стороны прямоугольника равны двум наименьшим трёхзначным простым числам. Найдите {quantity}.
   - Parameters: quantity — периметр, площадь или число перегородок.
   - Validation: Оба простых числа проверены.

### D06 — GCD, LCM, and periodic coincidences / НОД, НОК и совпадение периодов

**Difficulty profile:** D1–D3

**Scope:** Find when repeating schedules coincide or determine a common cycle.

**Corpus examples:**

- **D2 · corpus item 39** — Коля, Серёжа и Ваня регулярно ходили в кинотеатр. Коля бывал в нём каждый 3-й день, к, RE t, Серёжа - каждый 17-й, Ваня - каждый 6-й. Сегодня все ребята были в кино. Когда все трое встретятся в кинотеатре в следующий раз?  
  _Source: `15-минутки/Апрель 2026/15.04.2026.pdf`; source line 67._
- **D2 · corpus item 1173** — 5. Сегодня трое друзей встретились в библиотеке. Один приходит туда каждые 4 дня, второй - каждые 6 дней, третий - каждые 15 дней. Через сколько дней они встретятся там снова?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1315._
- **D2 · template-derived illustration** — Три кружка проходят каждые 8, 12 и 18 дней. Сегодня занятия совпали. Через сколько дней они снова совпадут?

**Generator templates:**

1. `D06-T1` — Первый приходит каждые {a} дней, второй — каждые {b}, третий — каждые {c}. Через сколько дней они встретятся снова?
   - Parameters: Положительные периоды.
   - Validation: Ответ НОК(a,b,c).
1. `D06-T2` — Два сигнала повторяются через {a} и {b} минут. Сколько совпадений будет за {T} минут?
   - Parameters: Явно указано, считать ли момент 0.
   - Validation: Используется период НОК(a,b).

### D07 — Remainders and modular cycles / Остатки и циклы по модулю

**Difficulty profile:** D2–D5

**Scope:** Reason about residues, repeated operations, or cyclic last digits.

**Corpus examples:**

- **D3 · corpus item 452** — В последовательности 1, 2, 2, 4, 8, 2, 6, . . . каждая цифра равна последней цифре произведения предыдущих двух цифр. Как видно, на 4-м месте стоит цифра 4. А какая цифра стоит на 2021-м месте?  
  _Source: `239-5_comb.pdf`; source line 567._
- **D3 · corpus item 471** — В последовательности 2, 1, 2, 2, 4, 8, 2, . . . каждая цифра равна последней цифре произведения предыдущих двух цифр. Как видно, на 6-м месте стоит цифра 8. А какая цифра стоит на 2021-м месте?  
  _Source: `239-5_comb.pdf`; source line 586._
- **D3 · corpus item 531** — В последовательности 3, 4, 7, 1, 8, 9, 7, . . . каждая цифра равна последней цифре суммы предыдущих двух цифр. Как видно, на 5-м месте стоит цифра 8. А какая цифра стоит на 2022-м месте?  
  _Source: `239-5_comb.pdf`; source line 646._

**Generator templates:**

1. `D07-T1` — Найдите остаток от деления {a}^{n}+{b} на {m}.
   - Parameters: У степени короткий цикл по модулю m.
   - Validation: Цикл и остаток проверены.
1. `D07-T2` — Число при делении на {m1} даёт остаток {r1}, а на {m2} — {r2}. Найдите наименьшее возможное число.
   - Parameters: Сравнения совместны.
   - Validation: Решение единственно по модулю НОК.

### D08 — Trailing zeros and prime exponents / Количество нулей в конце произведения

**Difficulty profile:** D2–D4

**Scope:** Count powers of 10 in factorial-like or consecutive products.

**Corpus examples:**

- **D2 · corpus item 1632** — Сколько нулей в конце будет в записи результата умножения: 7⋅8⋅9⋅ ... ⋅37⋅ 38?  
  _Source: `Сб В классе/2 занятие.docx`; source line 1807._
- **D3 · template-derived illustration** — Сколько нулей оканчивают произведение 1·2·3·…·75?
- **D4 · template-derived illustration** — Сколько нулей оканчивают число 120! / 35!?

**Generator templates:**

1. `D08-T1` — Сколько нулей в конце произведения {a}·({a}+1)·…·{b}?
   - Parameters: Интервал содержит множители 5 и 2.
   - Validation: Ответ min(v2,v5).
1. `D08-T2` — Сколько нулей оканчивает {n}!?
   - Parameters: n>0.
   - Validation: Используется сумма floor(n/5^k).

### D09 — Parity and divisibility existence constructions / Конструкции и невозможность по чётности/делимости

**Difficulty profile:** D3–D5

**Scope:** Prove existence or impossibility using parity, divisibility, or restricted prime factors.

**Corpus examples:**

- **D5 · corpus item 1630** — Можно ли составить таблицу 5 х 5 из натуральных чисел так, чтобы сумма чисел в каждой строке была четной, а произведение в каждом столбце было нечетным?  
  _Source: `Сб В классе/2 занятие.docx`; source line 1805._
- **D4 · template-derived illustration** — Можно ли выбрать пять нечётных целых чисел так, чтобы их сумма была чётной? Докажите ответ.
- **D4 · template-derived illustration** — Существует ли натуральное число, которое одновременно нечётно, делится на 6 и не делится на 3? Обоснуйте ответ.

**Generator templates:**

1. `D09-T1` — Можно ли заполнить таблицу {m}×{n} натуральными числами так, чтобы суммы строк были чётными, а произведения столбцов нечётными?
   - Parameters: m,n выбраны для конструкции или противоречия.
   - Validation: Требуется доказательство или явное заполнение.
1. `D09-T2` — Назовём число хорошим, если оно равно 2^a3^b. Какие числа из списка хорошие?
   - Parameters: Смешанный список.
   - Validation: В разложении нет других простых множителей.

## E. Sequences and patterns / Последовательности и закономерности (6 themes)

### E01 — Arithmetic progressions and their sums / Арифметические прогрессии и суммы

**Difficulty profile:** D1–D3

**Scope:** Sum an arithmetic progression or determine its number of terms.

**Corpus examples:**

- **D1 · corpus item 48** — Найдите сумму последовательности: 11 + 14 + 17+... + 80 + 83 =?  
  _Source: `15-минутки/Апрель 2026/17.04.2026.pdf`; source line 82._
- **D1 · corpus item 30** — Найдите сумму последовательности: 2 +3+5+6 +... +54 =?  
  _Source: `15-минутки/Апрель 2026/13.04.2026.pdf`; source line 52._
- **D1 · corpus item 1430** — Найдите сумму последовательности: 2 + 3 + 5 + 6 + … + 54 = ?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1590._

**Generator templates:**

1. `E01-T1` — Найдите сумму: {a}+({a}+{d})+…+{last}.
   - Parameters: last=a+(n-1)d.
   - Validation: Число членов целое и не меньше трёх.
1. `E01-T2` — Найдите сумму арифметической прогрессии с первым членом {a}, разностью {d} и {n} членами.
   - Parameters: Целые a,d,n.
   - Validation: Используется формула n(2a+(n-1)d)/2.

### E02 — Alternating and block-structured sums / Знакочередующиеся и блочные суммы

**Difficulty profile:** D2–D4

**Scope:** Group terms in pairs or blocks to evaluate an alternating patterned sum.

**Corpus examples:**

- **D2 · corpus item 6** — Вычислите 239 - 135 + 112 - 234 - 366 : 127 + 239 : 231  
  _Source: `15-минутки/Апрель 2026/03.04.2026.pdf`; source line 13._
- **D2 · corpus item 1600** — Вычислите сумму a) 11 + 13 + 14 + 16 + 17 + … + 49 + 50; b) 11 - 13 + 14 - 16 + 17 + … - 49 + 50  
  _Source: `Сб В классе/12 занятие.docx`; source line 1772._
- **D2 · corpus item 1629** — a) 20 + 23 + 26 + … + 53; b) 11 + 15 + 19 + … + 43; c) 1 - 3 + 5 - 7 + … - 19 + 21  
  _Source: `Сб В классе/2 занятие.docx`; source line 1804._

**Generator templates:**

1. `E02-T1` — Вычислите: {a}-({a}+1)+({a}+3)-({a}+4)+…+{last}.
   - Parameters: Повторяющийся рисунок разностей.
   - Validation: Члены естественно группируются в равные пары.
1. `E02-T2` — Найдите сумму 1-3+5-7+…-(2n-1)+(2n+1).
   - Parameters: n>0.
   - Validation: После группировки получается короткое выражение.

### E03 — Pattern recognition in numerical sequences / Закономерности в последовательностях

**Difficulty profile:** D1–D4

**Scope:** Infer a rule from initial terms and calculate a later term or sum.

**Corpus examples:**

- **D2 · corpus item 1583** — Разбойники кладут добычу в общий мешок. Первый положил одну монету, второй четыре монеты, третий - 13 монет и так далее. Сколько всего монет положат 8 разбойников?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1752._
- **D2 · corpus item 1019** — 06 В течение недели ученик каждый день решал на две задачи больше, чем в предыдущий день, при этом в воскресенье он решил втрое больше задач, чем в понедельник  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1152._
- **D2 · corpus item 1078** — 9. Бабочка летает хаотично. Первую минуту летит вперед со скоростью 1 м/c, вторую минуту летит назад со скоростью 2 м/c, третью минуту опять летит вперёд со скоростью 3 м/c, и так далее. Где будет бабочка через 10 минут. Бабочка разворачивается мгновенно  
  _Source: `Доп ДЗ/Доп ДЗ 06.docx`; source line 1214._

**Generator templates:**

1. `E03-T1` — Последовательность начинается {a1}, {a2}, {a3}; каждый следующий член получается по правилу {rule}. Найдите {n}-й член.
   - Parameters: Правило дано явно или однозначно следует из условия.
   - Validation: Не используется угадывание по недостаточному числу членов.
1. `E03-T2` — Первый участник кладёт {u1}, каждый следующий — в {k} раз больше плюс {c}. Сколько положат первые {n}?
   - Parameters: n невелико.
   - Validation: Сначала строится рекуррентная последовательность, затем сумма.

### E04 — Fibonacci-type recurrences and distances / Последовательности типа Фибоначчи

**Difficulty profile:** D2–D4

**Scope:** Use a recurrence where each term is the sum of preceding terms, often as distances between points.

**Corpus examples:**

- **D3 · corpus item 172** — На прямой отмечено 12 точек так, что расстояние между соседними точками равно 1, 1, 2, 3, 5, 8, 13, ... . Каково расстояние между двумя последними точками?  
  _Source: `15-минутки/Март 2026/23.03.2026.pdf`; source line 263._
- **D3 · corpus item 177** — На прямой отмечено 17 точек так, что расстояние между соседними точками равно 1, 1, те 2, 3, 5, 8, 13, ... . Каково расстояние между двумя последними точками?  
  _Source: `15-минутки/Март 2026/24.03.2026.pdf`; source line 271._
- **D3 · template-derived illustration** — Расстояния между соседними точками равны 2, 3, 5, 8, 13, …; каждый следующий отрезок равен сумме двух предыдущих. Найдите длину десятого отрезка.

**Generator templates:**

1. `E04-T1` — Расстояния между соседними точками равны 1,1,2,3,5,… . Найдите расстояние между {k}-й и {n}-й точками.
   - Parameters: k<n.
   - Validation: Суммируются правильные члены последовательности.
1. `E04-T2` — Последовательность задана a1={a}, a2={b}, an=an-1+an-2. Найдите a{n}.
   - Parameters: n умеренно.
   - Validation: Рекурсия вычислена без смещения индексов.

### E05 — Iterative number transformations / Итерационные процессы над числами

**Difficulty profile:** D2–D5

**Scope:** Trace a deterministic rule applied repeatedly until a threshold or target is reached.

**Corpus examples:**

- **D4 · corpus item 1608** — На доске было написано число. Раз в минуту, если оно чётное, то его делят пополам, а если нечетное, то умножают на 3 и прибавляют 1. Например, если на доске написано число 11, то будут выписаны последовательно: через минуту - 34, через две - 17, затем 52, 26, 13, 40, и через 7 минут - 20. Через сколько минут впервые будет выписано число меньшее 10, если в начале выписано число 70?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1780._
- **D3 · template-derived illustration** — Начав с числа 46, каждое чётное число делят на 2, а к каждому нечётному прибавляют 5. Через сколько шагов впервые получится число меньше 10?
- **D4 · template-derived illustration** — Последовательность начинается с 7; далее нечётный член заменяют на 3n+1, а чётный — на n/2. Найдите первый повтор или докажите, что до 20-го шага его нет.

**Generator templates:**

1. `E05-T1` — На доске число {N}. Если оно чётное, делят на 2; иначе умножают на 3 и прибавляют 1. Когда впервые появится число меньше {T}?
   - Parameters: Траектория заранее проверена и коротка.
   - Validation: Процесс конечен для выбранного N.
1. `E05-T2` — К числу применяют по очереди операции {ops}. Какое число будет после {k} шагов?
   - Parameters: Порядок операций циклический и однозначный.
   - Validation: Нет неоднозначности шага.

### E06 — Cumulative growth and recursive totals / Накопительные схемы и рекурсивные суммы

**Difficulty profile:** D2–D4

**Scope:** Sum quantities generated recursively, such as deposits growing by a fixed affine rule.

**Corpus examples:**

- **D3 · corpus item 1019** — 06 В течение недели ученик каждый день решал на две задачи больше, чем в предыдущий день, при этом в воскресенье он решил втрое больше задач, чем в понедельник  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1152._
- **D3 · corpus item 1583** — Разбойники кладут добычу в общий мешок. Первый положил одну монету, второй четыре монеты, третий - 13 монет и так далее. Сколько всего монет положат 8 разбойников?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1752._
- **D3 · template-derived illustration** — В первый день ученик решил 2 задачи, а каждый следующий день — на 3 задачи больше предыдущего. Сколько задач он решил за 10 дней?

**Generator templates:**

1. `E06-T1` — Первый положил {a1} монет, каждый следующий — в {k} раз больше предыдущего и ещё {c}. Сколько положили {n} участников?
   - Parameters: n невелико.
   - Validation: Все члены и итоговая сумма целые.
1. `E06-T2` — За первый день сделано {a}, каждый следующий день на {d} больше. Сколько за {n} дней?
   - Parameters: Положительные величины.
   - Validation: Это сумма арифметической прогрессии.

## F. Combinatorics / Комбинаторика (11 themes)

### F01 — Permutations of distinct symbols / Перестановки различных символов

**Difficulty profile:** D1–D3

**Scope:** Count arrangements of distinct letters, digits, or objects.

**Corpus examples:**

- **D2 · corpus item 1449** — Ключ к пещере с сокровищами - слово из пяти букв. Али-Баба узнал, что это буквы Ш, К, О, Л, А. Сколько различных комбинаций ему придётся перебрать, прежде чем пещера наверняка откроется?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1609._
- **D2 · corpus item 1459** — Ключ к пещере с сокровищами - слово из различных букв. Али-Баба узнал, что это буквы A, B, C, D, E, F, G. Сколько различных комбинаций ему придётся перебрать, прежде чем пещера наверняка откроется?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1619._
- **D2 · template-derived illustration** — Сколько перестановок можно составить из пяти различных букв А, Б, В, Г, Д?

**Generator templates:**

1. `F01-T1` — Сколько слов можно составить из {n} различных букв, используя каждую один раз?
   - Parameters: n=4…8.
   - Validation: Ответ n!.
1. `F01-T2` — Сколько различных порядков возможно для {n} разных предметов?
   - Parameters: Все предметы различимы.
   - Validation: Каждая перестановка считается один раз.

### F02 — Permutations with repeated symbols / Перестановки с повторениями

**Difficulty profile:** D2–D4

**Scope:** Count distinct arrangements of a multiset.

**Corpus examples:**

- **D3 · corpus item 1434** — Ключ к пещере с сокровищами - слово из пяти букв. Али-Баба узнал, что это буквы Б, А, Р, А, Н. Сколько различных комбинаций ему придётся перебрать, прежде чем пещера наверняка откроется?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1594._
- **D3 · corpus item 1477** — Ключ к пещере с сокровищами - слово из пяти букв. Али-Баба узнал, что это буквы М, А, Г, М, А. Сколько различных комбинаций ему придётся перебрать, прежде чем пещера наверняка откроется?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1637._
- **D2 · corpus item 1541** — Сколько существует различных комбинаций чисел можно составить из набора цифр: a) 12345; b) 11234; c) 11112; d) 1112234; e) 122333444455555  
  _Source: `Сб В классе/10 занятие.docx`; source line 1707._

**Generator templates:**

1. `F02-T1` — Сколько различных перестановок цифр в записи {multiset}?
   - Parameters: Есть повторяющиеся цифры.
   - Validation: Ответ n!/(m1!m2!…).
1. `F02-T2` — Сколько {n}-буквенных слов можно составить из букв с кратностями {counts}?
   - Parameters: Сумма кратностей равна n.
   - Validation: Все данные символы используются ровно один раз.

### F03 — Words of bounded length over an alphabet / Слова ограниченной длины

**Difficulty profile:** D1–D3

**Scope:** Count strings over a fixed alphabet with a maximum or exact length.

**Corpus examples:**

- **D1 · corpus item 1580** — Слова в словляндии состоят из букв: С, Л, О, В, А. Слово имеет максимальную длину 6. Сколько различных слов в таком алфавите?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1749._
- **D2 · template-derived illustration** — Сколько слов длины от 1 до 5 можно составить из букв А, Б, В, если повторения разрешены?
- **D3 · template-derived illustration** — Сколько слов длины не более 6 над алфавитом из четырёх букв содержат хотя бы одну букву А?

**Generator templates:**

1. `F03-T1` — Алфавит содержит {q} букв. Сколько слов длины от 1 до {n}?
   - Parameters: Повторы разрешены.
   - Validation: Сумма q+q²+…+q^n.
1. `F03-T2` — Сколько слов длины {n} над алфавитом из {q} букв, если соседние буквы не совпадают?
   - Parameters: q≥2.
   - Validation: Ответ q(q-1)^(n-1).

### F04 — Unknown alphabet and lexicographic rank / Неизвестный алфавитный порядок

**Difficulty profile:** D3–D5

**Scope:** Recover an alphabet order or a word at a specified lexicographic rank from another ranked word.

**Corpus examples:**

- **D4 · corpus item 38** — Иван придумал новый язык состоящий из букв И, В, А, Н. При этом мы не знаем, какой у них настоящий алфавитный порядок. Оказалось, что если выписать в алфавитном порядке все 24 слова из четырех различных букв, то третьим словом в этом списке будет НАВИ. Какое будет 18-е слово. .. .. м “  
  _Source: `15-минутки/Апрель 2026/15.04.2026.pdf`; source line 66._
- **D4 · corpus item 1205** — 4. Язык Ралины состоит из букв А, Р, И, Л, Н. Настоящий алфавитный порядок букв неизвестен. Если выписать в алфавитном порядке все 120 слов из пяти различных букв, то вторым словом будет АЛИНР. Какое слово будет первым?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1350._
- **D4 · corpus item 1206** — 5. Язык Ралины состоит из букв А, Р, И, Л, Н. Настоящий алфавитный порядок букв неизвестен. Если выписать в алфавитном порядке все 120 слов из пяти различных букв, то вторым словом будет ИНЛРА. Какое слово идёт сразу перед словом АНИРЛ?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1351._

**Generator templates:**

1. `F04-T1` — Все перестановки букв {letters} выписаны в неизвестном алфавитном порядке. Известно, что {r}-е слово — {word}. Найдите {s}-е слово.
   - Parameters: 4–5 разных букв.
   - Validation: Подсказка задаёт единственный порядок или единственный ответ.
1. `F04-T2` — По двум словам и их позициям восстановите порядок букв неизвестного алфавита.
   - Parameters: Подсказки совместны.
   - Validation: Порядок букв единственен.

### F05 — Selections, teams, and subsets / Выборы, команды и подмножества

**Difficulty profile:** D1–D4

**Scope:** Count ways to choose a subset or form a team under simple restrictions.

**Corpus examples:**

- **D1 · corpus item 1511** — На полке стоят 6 различных альбомов. Сколькими способами можно выложить в стопку несколько из них (стопка может состоять и из одного альбома)?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1671._
- **D2 · template-derived illustration** — Из 9 разных книг выбирают 4 для выставки. Сколькими способами это можно сделать?
- **D3 · template-derived illustration** — Из 7 учеников нужно выбрать команду хотя бы из двух человек. Сколько различных команд возможно?

**Generator templates:**

1. `F05-T1` — Сколькими способами можно выбрать {k} человек из {n}?
   - Parameters: 0≤k≤n.
   - Validation: Ответ C(n,k).
1. `F05-T2` — Из {b} мальчиков и {g} девочек выбирают команду из {k}, в которой не менее {r} девочек. Сколько способов?
   - Parameters: Ограничения выполнимы.
   - Validation: Суммируются нужные биномиальные коэффициенты.

### F06 — Round-robin tournaments and pair counting / Круговые турниры и подсчёт пар

**Difficulty profile:** D1–D3

**Scope:** Count unordered pairs when every participant meets every other participant.

**Corpus examples:**

- **D2 · corpus item 189** — В шахматном турнире участвуют 18 человек. Сколько партий будет сыграно в турнире, если каждый участник сыграет со всеми остальными участниками по одному разу?  
  _Source: `15-минутки/Март 2026/26.03.2026.pdf`; source line 289._
- **D2 · corpus item 971** — В шахматном турнире участвуют 14 человек. Сколько партий будет сыграно в турнире, если каждый участник сыграет со всеми остальными участниками по одному разу? А сколько очков будет набрано?  
  _Source: `Доп ДЗ/Доп ДЗ 04.docx`; source line 1101._
- **D1 · corpus item 1190** — 10. В шахматном турнире участвуют 18 человек. Каждый должен сыграть с каждым по одной партии. Сколько всего будет сыграно партий?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1332._

**Generator templates:**

1. `F06-T1` — В турнире {n} участников; каждый играет с каждым один раз. Сколько партий?
   - Parameters: n≥2.
   - Validation: Ответ C(n,2).
1. `F06-T2` — Каждая пара из {n} людей обменивается рукопожатием. Сколько рукопожатий?
   - Parameters: n≥2.
   - Validation: Неупорядоченные пары считаются один раз.

### F07 — Single-elimination tournaments / Турниры на выбывание

**Difficulty profile:** D1–D2

**Scope:** Count matches needed to leave one winner when each match eliminates one participant.

**Corpus examples:**

- **D2 · corpus item 1609** — Десять игроков собираются провести турнир в городки по олимпийской системе (проигравший партию выбывает из турнира).Сколько партий понадобится для выявления победителя? А если участников 16?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1781._
- **D2 · corpus item 1720** — Восемь человек собираются провести турнир в крестики-нолики по олимпийской системе (проигравший партию игрок выбывает из турнира). Сколько партий понадобится для выявления победителя? А если участников 32?  
  _Source: `Сб В классе/5 занятие.docx`; source line 1904._
- **D1 · corpus item 1495** — 15 команд сыграли турнир по олимпийской системе. Сколько всего было сыграно матчей?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1655._

**Generator templates:**

1. `F07-T1` — В турнире на выбывание {n} игроков. Сколько матчей нужно определить победителя?
   - Parameters: n≥1; допускаются пропуски раунда.
   - Validation: Нужно ровно n-1 выбываний.
1. `F07-T2` — После каждого полного раунда проигравшие выбывают. Сколько участников останется после {r} раундов из {n}?
   - Parameters: Формат пропусков указан.
   - Validation: Число оставшихся вычисляется однозначно.

### F08 — Monotone lattice paths / Маршруты по клеткам вправо и вверх

**Difficulty profile:** D2–D4

**Scope:** Count paths in a grid using only right and up steps, optionally with forbidden cells.

**Corpus examples:**

- **D4 · corpus item 65** — На квадратном поле 4 × 4 клетки растут цветы, число цветов в каждой клетке указано на схеме. Вася начинает с левой нижней клетки (с числом 8) и переходя каждый раз в соседнюю справа или сверху, добирается до правой верхней клетки, собирая цветы с клеток на которых побывал. Сколько есть маршрутов, на которых Вася соберёт ровно 25 цветков?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 102._
- **D4 · corpus item 85** — На квадратном поле 4 × 4 клетки растут цветы, число цветов в каждой клетке указано на схеме. Вася начинает с левой нижней клетки (с числом 2) и переходя каждый раз в соседнюю справа или сверху, добирается до правой верхней клетки, собирая цветы с клеток на которых побывал. Сколько есть маршрутов, на которых Вася соберёт ровно 43 цветка?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 125._
- **D2 · template-derived illustration** — Сколько путей ведёт из левого нижнего угла решётки 5×4 в правый верхний, если можно идти только вправо и вверх?

**Generator templates:**

1. `F08-T1` — Сколько путей из левого нижнего угла поля {m}×{n} в правый верхний, если идти только вправо и вверх?
   - Parameters: m,n>0.
   - Validation: Используется биномиальный коэффициент по числу шагов.
1. `F08-T2` — Сколько таких путей не проходят через клетку {forbidden}?
   - Parameters: Одна запрещённая клетка или вершина.
   - Validation: Вычитаются пути через запрещённую точку.

### F09 — Weighted grid paths with a target sum / Маршруты с заданной суммой весов

**Difficulty profile:** D3–D5

**Scope:** Count monotone paths whose visited-cell weights sum to a prescribed target.

**Corpus examples:**

- **D5 · corpus item 65** — На квадратном поле 4 × 4 клетки растут цветы, число цветов в каждой клетке указано на схеме. Вася начинает с левой нижней клетки (с числом 8) и переходя каждый раз в соседнюю справа или сверху, добирается до правой верхней клетки, собирая цветы с клеток на которых побывал. Сколько есть маршрутов, на которых Вася соберёт ровно 25 цветков?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 102._
- **D5 · corpus item 85** — На квадратном поле 4 × 4 клетки растут цветы, число цветов в каждой клетке указано на схеме. Вася начинает с левой нижней клетки (с числом 2) и переходя каждый раз в соседнюю справа или сверху, добирается до правой верхней клетки, собирая цветы с клеток на которых побывал. Сколько есть маршрутов, на которых Вася соберёт ровно 43 цветка?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 125._
- **D5 · corpus item 613** — На квадратном поле 4 × 4 клетки растут цветы, число цветов в каждой клетке указано на схеме. Вася начинает с левой нижней клетки (с числом 8) и переходя каждый раз в соседнюю справа или сверху, добирается до правой верхней клетки, собирая цветы с клеток на которых побывал. Сколько есть маршрутов, на которых Вася соберјт ровно 25 цветков? 2 2 4 4 4 4 2 4 6 2 1 2 8 4 2 2  
  _Source: `239-5_comb.pdf`; source line 728._

**Generator templates:**

1. `F09-T1` — В клетках поля {m}×{n} стоят числа. Сколько путей вправо/вверх имеют сумму {S}?
   - Parameters: Сетка 3×3 или 4×4.
   - Validation: Динамическое программирование даёт проверенный ответ.
1. `F09-T2` — Сколько маршрутов собирают ровно {S} предметов, если значения клеток заданы таблицей?
   - Parameters: Целые веса.
   - Validation: Стартовая и конечная клетки включаются одинаково во всех путях.

### F10 — Chess-piece placements / Расстановки шахматных фигур

**Difficulty profile:** D2–D5

**Scope:** Count legal placements of labeled chess pieces under attack constraints.

**Corpus examples:**

- **D3 · corpus item 1612** — a) Сколькими способами можно расставить чёрную и белую ладьи на шахматной доске так, чтобы они не били друг друга? b) Сколькими способами можно поставить на шахматную доску белого и чёрного королей так, чтобы получилась допустимая правилами игры позиция?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1784._
- **D3 · template-derived illustration** — Сколькими способами можно поставить две ладьи разных цветов на доску 8×8 так, чтобы они не били друг друга?
- **D4 · template-derived illustration** — Сколькими способами можно поставить двух королей разных цветов на доску 8×8 так, чтобы позиция была допустимой?

**Generator templates:**

1. `F10-T1` — Сколькими способами поставить белую и чёрную ладьи на доску {n}×{n}, чтобы они не били друг друга?
   - Parameters: n≥2; фигуры различимы.
   - Validation: Нет общей строки и столбца.
1. `F10-T2` — Сколькими способами поставить двух королей на доску {n}×{n}, чтобы они не атаковали друг друга?
   - Parameters: Указано, различимы ли короли.
   - Validation: Исключены соседние клетки по стороне и диагонали.

### F11 — Pigeonhole and guaranteed selection / Принцип Дирихле и гарантированный выбор

**Difficulty profile:** D2–D5

**Scope:** Determine the minimum draw or infer composition from statements of what every subset must contain.

**Corpus examples:**

- **D3 · corpus item 164** — У Пети в кармане несколько монет. Если Петя наугад вытащит из кармана 3 монеты, среди них обязательно найдётся монета в 1 рубль. Если Петя наугад вытащит 4 монеты из кармана, среди них обязательно найдётся монета в 2 рубля. Петя вытащил из кармана 5 монет. Назовите эти монеты  
  _Source: `15-минутки/Март 2026/20.03.2026.pdf`; source line 249._
- **D4 · corpus item 225** — В пенале лежат ручки, карандаши и фломастеры (причјм в пенале есть хотя бы один предмет каждого вида). Если вынуть 11 ручек, то среди любых 13 оставшихся предметов будет не менее одного карандаша, если же вынуть 12 карандашей, то среди любых 12 оставшихся предметов будет не менее одной ручки. Предположим, что из пенала убрали все ручки. Сколько надо вынуть теперь предметов, чтобы среди них гарантированно был флома…  
  _Source: `2025-all.pdf`; source line 337._
- **D4 · corpus item 248** — В пенале лежат ручки, карандаши и фломастеры (причјм в пенале есть хотя бы один предмет каждого вида). Если вынуть 13 ручек, то среди любых 16 оставшихся предметов будет не менее одного карандаша, если же вынуть 15 карандашей, то среди любых 15 оставшихся предметов будет не менее одной ручки. Предположим, что из пенала убрали все ручки. Сколько надо вынуть теперь предметов, чтобы среди них гарантированно был флома…  
  _Source: `2025-all.pdf`; source line 360._

**Generator templates:**

1. `F11-T1` — В мешке предметы нескольких типов. Сколько надо вынуть вслепую, чтобы гарантированно получить предмет типа {target}?
   - Parameters: Известно максимальное число предметов других типов.
   - Validation: Ответ max_non_target+1.
1. `F11-T2` — Известно, что среди любых {k} предметов есть A, а среди любых {m} есть B. Определите возможный состав набора.
   - Parameters: 2–3 типа, малые k,m.
   - Validation: Гарантии переведены в верхние границы дополнений.

## G. Plane geometry and measurement / Планиметрия и измерения (12 themes)

### G01 — Square area and perimeter / Площадь и периметр квадрата

**Difficulty profile:** D1–D3

**Scope:** Convert between side, perimeter, and area of a square.

**Corpus examples:**

- **D1 · corpus item 96** — Найдите площадь квадрата, если периметр равен 20 см. А если периметр 34 см?  
  _Source: `15-минутки/Март 2026/04.03.2026.pdf`; source line 139._
- **D1 · corpus item 101** — Найдите площадь квадрата, если периметр равен 18 см. А если периметр 30 см?  
  _Source: `15-минутки/Март 2026/05.03.2026.pdf`; source line 147._
- **D1 · corpus item 1538** — Найдите площадь квадрата, если периметр равен 16 см. А если периметр 26 см?  
  _Source: `Сб В классе/1 занятие.docx`; source line 1701._

**Generator templates:**

1. `G01-T1` — Найдите площадь квадрата, если его периметр {P} см.
   - Parameters: P делится на 4.
   - Validation: Сторона P/4; площадь положительна.
1. `G01-T2` — Если сторону квадрата увеличить на {d}, площадь увеличится на {A}. Найдите исходную сторону.
   - Parameters: A-d² делится на 2d.
   - Validation: Исходная сторона — положительное целое.

### G02 — Rectangle area and perimeter / Площадь и периметр прямоугольника

**Difficulty profile:** D1–D3

**Scope:** Find missing dimensions, area, or perimeter of a rectangle.

**Corpus examples:**

- **D1 · corpus item 159** — Площадь прямоугольника 8 квадратных метров, а одна из его сторон 14 метров. Найдите периметр этого прямоугольника. А если его сторона 20 метров?  
  _Source: `15-минутки/Март 2026/19.03.2026.pdf`; source line 241._
- **D2 · corpus item 63** — Периметр прямоугольника 47 см. Если провести некоторый вертикальный разрез, то сумма периметров двух полученных прямоугольников будет 66 см. А чему будет равен периметр каждого из прямоугольников, если горизонтальным разрезом поделить исходный прямоугольник на два равных прямоугольника  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 100._
- **D2 · corpus item 83** — Периметр прямоугольника 49 см. Если провести некоторый вертикальный разрез, то сумма периметров двух полученных прямоугольников будет 77 см. А чему будет равен периметр каждого из прямоугольников, если горизонтальным разрезом поделить исходный прямоугольник на два равных прямоугольника  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 123._

**Generator templates:**

1. `G02-T1` — Площадь прямоугольника {A}, одна сторона {a}. Найдите периметр.
   - Parameters: A делится на a.
   - Validation: Вторая сторона положительна.
1. `G02-T2` — Периметр прямоугольника {P}, одна сторона {a}. Найдите площадь.
   - Parameters: P/2>a.
   - Validation: Вторая сторона P/2-a положительна.

### G03 — Composite rectangles made from equal squares / Составные фигуры из одинаковых квадратов

**Difficulty profile:** D1–D3

**Scope:** Find dimensions, perimeter, or area when equal squares form a larger square or rectangle.

**Corpus examples:**

- **D1 · corpus item 121** — Квадрат сложен из шестнадцати одинаковых квадратов периметром 22 см каждый. Чему Е равна площадь большого квадрата?  
  _Source: `15-минутки/Март 2026/10.03.2026.pdf`; source line 179._
- **D1 · corpus item 873** — Квадрат сложен из четырех одинаковых квадратов периметром 10 м каждый. Чему равен периметр большого квадрата?  
  _Source: `Доп ДЗ/Доп ДЗ 02.docx`; source line 997._
- **D1 · corpus item 1298** — Квадрат сложен из девяти одинаковых квадратов площадью 16 см^2 каждый. Чему равен периметр большого квадрата?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1458._

**Generator templates:**

1. `G03-T1` — Большой квадрат сложен из {k2} одинаковых квадратов площадью {a}. Найдите его периметр.
   - Parameters: k2 — полный квадрат.
   - Validation: Сторона малого квадрата √a.
1. `G03-T2` — Из {n} одинаковых квадратов периметра {p} составили прямоугольник {rows}×{cols}. Найдите площадь и периметр.
   - Parameters: rows·cols=n.
   - Validation: Общие рёбра не входят во внешний периметр.

### G04 — Perimeter changes after straight cuts / Изменение периметра после разреза

**Difficulty profile:** D2–D4

**Scope:** Use how a cut duplicates an internal segment in the sum of perimeters.

**Corpus examples:**

- **D3 · corpus item 63** — Периметр прямоугольника 47 см. Если провести некоторый вертикальный разрез, то сумма периметров двух полученных прямоугольников будет 66 см. А чему будет равен периметр каждого из прямоугольников, если горизонтальным разрезом поделить исходный прямоугольник на два равных прямоугольника  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 100._
- **D3 · corpus item 83** — Периметр прямоугольника 49 см. Если провести некоторый вертикальный разрез, то сумма периметров двух полученных прямоугольников будет 77 см. А чему будет равен периметр каждого из прямоугольников, если горизонтальным разрезом поделить исходный прямоугольник на два равных прямоугольника  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 123._
- **D3 · corpus item 1135** — 9. Периметр прямоугольника равен 46 см. Если провести некоторый вертикальный разрез, то сумма периметров двух полученных прямоугольников будет равна 54 см. Чему будет равен периметр каждого из прямоугольников, если горизонтальным разрезом поделить исходный прямоугольник на два равных?  
  _Source: `Доп ДЗ/Доп ДЗ 07.docx`; source line 1274._

**Generator templates:**

1. `G04-T1` — Периметр прямоугольника {P}. После вертикального разреза сумма периметров частей {S}. Найдите высоту.
   - Parameters: S>P и S-P чётно.
   - Validation: Добавленный периметр равен 2·height.
1. `G04-T2` — Прямоугольник разделили горизонтально на две равные части. Найдите периметр каждой по исходным данным.
   - Parameters: Размеры или высота восстановимы.
   - Validation: Полученные части равны.

### G05 — Integer-sided rectangles with a relation between area and perimeter / Целочисленные стороны при условии на площадь и периметр

**Difficulty profile:** D3–D5

**Scope:** Construct integer side lengths satisfying A-P=c or P-A=c.

**Corpus examples:**

- **D4 · corpus item 42** — Приведите пример прямоугольника, у которого стороны измеряются целыми числами и периметр которого на 2023 больше, чем площадь. В ответ запишите длины обеих сторон  
  _Source: `15-минутки/Апрель 2026/15.04.2026.pdf`; source line 70._
- **D4 · corpus item 920** — 3. Сторона квадрата, площадь которого равна 81 см², в 3 раза больше ширины прямоугольника. Вычислить третью часть площади прямоугольника, если известно, что его периметр в 5 раз больше периметра квадрата  
  _Source: `Доп ДЗ/Доп ДЗ 03.docx`; source line 1047._
- **D3 · corpus item 1032** — 19 Придумайте такой прямоугольник, у которого площадь равна 5 м², а периметр равен 21 м. В ответ запишите длину большей стороны в метрах  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1165._

**Generator templates:**

1. `G05-T1` — Приведите пример прямоугольника с целыми сторонами, у которого периметр на {C} больше площади.
   - Parameters: C допускает решения.
   - Validation: Проверяется (a-2)(b-2)=4-C.
1. `G05-T2` — Найдите все прямоугольники с целыми сторонами, для которых площадь минус периметр равна {C}.
   - Parameters: C допускает конечный перебор делителей.
   - Validation: Используется (a-2)(b-2)=C+4.

### G06 — Geometric scaling and change of area / Масштабирование и изменение площади

**Difficulty profile:** D2–D4

**Scope:** Relate linear scaling to area changes or recover a side from an area increment.

**Corpus examples:**

- **D2 · corpus item 191** — Если бы стороны квадрата были на 1 см больше, то его площадь была бы больше на 15 i A cm2 . Какова длина стороны этого квадрата?  
  _Source: `15-минутки/Март 2026/27.03.2026.pdf`; source line 294._
- **D3 · corpus item 920** — 3. Сторона квадрата, площадь которого равна 81 см², в 3 раза больше ширины прямоугольника. Вычислить третью часть площади прямоугольника, если известно, что его периметр в 5 раз больше периметра квадрата  
  _Source: `Доп ДЗ/Доп ДЗ 03.docx`; source line 1047._
- **D2 · corpus item 1381** — Если бы стороны квадрата были на 1 см больше, то его площадь была бы больше на 15 см2 . Какова длина стороны этого квадрата?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1541._

**Generator templates:**

1. `G06-T1` — Сторону квадрата увеличили в {k} раз. Во сколько раз изменилась площадь?
   - Parameters: k>0.
   - Validation: Коэффициент площади k².
1. `G06-T2` — Сторона квадрата увеличилась на {d}, а площадь — на {A}. Найдите сторону.
   - Parameters: Есть положительное целое решение.
   - Validation: Уравнение 2ad+d²=A.

### G07 — Unit conversion and areal or volumetric density / Перевод единиц и плотность на площадь/объём

**Difficulty profile:** D1–D3

**Scope:** Convert units before applying proportional relationships involving area, volume, or mass.

**Corpus examples:**

- **D1 · corpus item 159** — Площадь прямоугольника 8 квадратных метров, а одна из его сторон 14 метров. Найдите периметр этого прямоугольника. А если его сторона 20 метров?  
  _Source: `15-минутки/Март 2026/19.03.2026.pdf`; source line 241._
- **D2 · corpus item 184** — В комнате размера Змх4м разбили аквариум объемом 120 литров, заполненный наполовину. Какой высоты будет слой воды в комнате, если считать, что к соседям ничего не протечет? Напомним, что один литр равен одному кубическому дециметру  
  _Source: `15-минутки/Март 2026/25.03.2026.pdf`; source line 281._
- **D1 · corpus item 1227** — 13. Лист железа размерами 20 см × 30 см весит 1200 г. Сколько весят 5 квадратных метров такого железа?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1372._

**Generator templates:**

1. `G07-T1` — Материал площадью {A1_cm2} см² весит {M}. Сколько весят {A2_dm2} дм²?
   - Parameters: Положительные значения.
   - Validation: Используется 1 дм²=100 см².
1. `G07-T2` — Объём {V_l} литров распределён по площади {A_m2} м². Найдите высоту слоя в мм.
   - Parameters: Положительные значения.
   - Validation: 1 л=0,001 м³.

### G08 — Counting squares in a rectangular grid / Подсчёт квадратов на клетчатой сетке

**Difficulty profile:** D2–D4

**Scope:** Count all axis-aligned squares of every size in an m by n grid.

**Corpus examples:**

- **D2 · corpus item 1652** — Сколько всего различных квадратиков всевозможных размеров нарисовано?  
  _Source: `Сб В классе/2 занятие.docx`; source line 1827._
- **D2 · corpus item 106** — На клетчатом листе нарисован квадрат 6 x 6, разбитый Ha единичные квадраты. Сколько всего различных квадратиков всевозможных размеров нарисовано?  
  _Source: `15-минутки/Март 2026/06.03.2026.pdf`; source line 155._
- **D2 · corpus item 1288** — На клетчатом листе нарисован квадрат 6 x 6, разбитый на единичные квадраты. Сколько всего различных квадратиков всевозможных размеров нарисовано?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1448._

**Generator templates:**

1. `G08-T1` — Сколько квадратов всех размеров в сетке {m}×{n}?
   - Parameters: m,n>0.
   - Validation: Сумма (m-k+1)(n-k+1) по k.
1. `G08-T2` — Сколько квадратов со сторонами не меньше {s} в сетке {m}×{n}?
   - Parameters: s≤min(m,n).
   - Validation: Суммирование начинается с k=s.

### G09 — Ordered collinear points and segment equations / Точки на прямой и уравнения для отрезков

**Difficulty profile:** D2–D4

**Scope:** Use the fixed order of points and equal segment relations to find an unknown distance.

**Corpus examples:**

- **D3 · corpus item 138** — На прямой расположены пять точек A, В, С, О, Е (именно в таком порядке). Известно, что АВ = 17 см, СЕ = 94 см, АС = ВО. Найдите длину отрезка ОЕ. oO ooo: i,  
  _Source: `15-минутки/Март 2026/14.03.2026.pdf`; source line 208._
- **D2 · corpus item 1729** — Известно, что AB=19 см., CE=97 см., AC=BD. Найдите длину отрезка DE  
  _Source: `Сб В классе/5 занятие.docx`; source line 1913._
- **D2 · corpus item 1312** — На прямой расположены пять точек A, B, C, D, E (именно в таком порядке). Известно, что AB = 23 см, CE = 101 см, AC = BD. Найдите длину отрезка DE  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1472._

**Generator templates:**

1. `G09-T1` — На прямой точки A,B,C,D,E идут в этом порядке. Даны AB={p}, CE={q}, AC=BD. Найдите DE.
   - Parameters: Данные совместны.
   - Validation: Вводятся длины соседних промежутков.
1. `G09-T2` — Точки A,B,C,D расположены по порядку; AB+CD={s}, AC=BD. Найдите BC.
   - Parameters: Положительные длины.
   - Validation: Используются формулы сложения отрезков.

### G10 — Distances along a line with repeated intervals / Суммирование расстояний между последовательными точками

**Difficulty profile:** D1–D3

**Scope:** Sum periodic or explicitly defined gaps between numbered points.

**Corpus examples:**

- **D2 · corpus item 1342** — На прямой расположена тысяча точек. Известно, что между соседними идут так: 1 см, 2 см, 1 см, 2 см, 1 см, 2 см, 1 см, 2 см …. Найдите расстояние a) между первой и последней. b) от 239 до 777  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1502._
- **D2 · template-derived illustration** — На прямой отмечены 500 точек, расстояния между соседними попеременно равны 2 см и 5 см. Найдите расстояние между первой и последней точками.
- **D3 · template-derived illustration** — Между соседними точками повторяется цикл расстояний 1, 3, 2 см. Найдите расстояние между 127-й и 514-й точками.

**Generator templates:**

1. `G10-T1` — На прямой {n} точек, расстояния между соседними чередуются {a},{b}. Найдите расстояние между первой и последней.
   - Parameters: n≥2.
   - Validation: Между n точками ровно n-1 промежутков.
1. `G10-T2` — Расстояние между любыми соседними точками {d}. Найдите расстояние между точками с номерами {i} и {j}.
   - Parameters: 1≤i<j≤n.
   - Validation: Ответ (j-i)d.

### G11 — Layer depth from spilled volume / Высота слоя жидкости по объёму и площади

**Difficulty profile:** D2–D3

**Scope:** Convert liquid volume and floor area to a uniform layer height.

**Corpus examples:**

- **D3 · corpus item 184** — В комнате размера Змх4м разбили аквариум объемом 120 литров, заполненный наполовину. Какой высоты будет слой воды в комнате, если считать, что к соседям ничего не протечет? Напомним, что один литр равен одному кубическому дециметру  
  _Source: `15-минутки/Март 2026/25.03.2026.pdf`; source line 281._
- **D3 · corpus item 1225** — 11. В комнате размером 4 м* 5 м разбили аквариум объёмом 200 литров, заполненный на четверть. Какой высоты получится слой воды на полу, если считать, что к соседям ничего не протечёт?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1370._
- **D2 · corpus item 1226** — 12. В комнате размером 3 м* 6 м разбили аквариум объёмом 180 литров, заполненный наполовину. Какой высоты будет слой воды в комнате?  
  _Source: `Доп ДЗ/Доп ДЗ 10.docx`; source line 1371._

**Generator templates:**

1. `G11-T1` — В комнате {a}×{b} м пролилось {V} л воды. Какова высота слоя?
   - Parameters: Положительные значения.
   - Validation: Литры переведены в м³, высота — в требуемые единицы.
1. `G11-T2` — Аквариум объёмом {V} л заполнен на {fraction}. Вода разлилась по площади {A}. Найдите глубину.
   - Parameters: fraction — правильная дробь.
   - Validation: Объём разлива V·fraction.

### G12 — Aspect ratio and composing rectangles / Отношение сторон и составление прямоугольников

**Difficulty profile:** D3–D5

**Scope:** Determine possible aspect ratios after joining rectangles with a prescribed ratio.

**Corpus examples:**

- **D4 · corpus item 37** — Будем говорить, что прямоугольник имеет пузатость 2 : 1, если одна его сторона в два раза больше другой. А у прямоугольника со сторонами Зсм и 2см пузатость равна 3 : 2. Было два прямоугольника, у каждого из которых пузатость равнялась 4 : 1. Из них сложили один прямоугольник. а) Чему может быть равна его пузатость?  
  _Source: `15-минутки/Апрель 2026/14.04.2026.pdf`; source line 62._
- **D4 · corpus item 52** — Будем говорить, что прямоугольник имеет пузатость 2 : 1, если одна его сторона в два раза больше другой. А у прямоугольника со сторонами Зсм и 2см пузатость равна 3 : 2. Было два прямоугольника, у каждого из которых пузатость равнялась 3 : 2. Из них сложили один прямоугольник. а) Чему может быть равна его пузатость?  
  _Source: `15-минутки/Апрель 2026/17.04.2026.pdf`; source line 86._
- **D4 · corpus item 210** — Прямоугольник называется длинным , если одна его сторона больше удвоенной другой. Дан прямоугольник 10 × 15. Всего есть 23 способа разрезать его по клеточкам на два прямоугольника. А в скольких из этих способов оба прямоугольника будут длинными?  
  _Source: `2025-all.pdf`; source line 322._

**Generator templates:**

1. `G12-T1` — Два прямоугольника отношения сторон {p}:{q} сложили без наложений в один прямоугольник. Какие отношения сторон возможны?
   - Parameters: p,q — небольшие взаимно простые.
   - Validation: Перебраны все склейки по равным сторонам.
1. `G12-T2` — Прямоугольник называют длинным, если одна сторона в {k} раз больше другой. Можно ли составить его из {n} одинаковых заданных прямоугольников?
   - Parameters: Небольшие n,k.
   - Validation: Дана конструкция или доказательство невозможности.

## H. Grid and solid geometry / Клетчатая и пространственная геометрия (9 themes)

### H01 — Internal partitions in a rectangular cell grid / Перегородки в прямоугольной решётке

**Difficulty profile:** D1–D3

**Scope:** Count unit internal edges separating adjacent cells in an m by n rectangle.

**Corpus examples:**

- **D2 · corpus item 170** — Сколько перегородок в квадрате наибольшего простого двузначного числа?  
  _Source: `15-минутки/Март 2026/23.03.2026.pdf`; source line 261._
- **D3 · corpus item 1768** — В прямоугольнике 1 × 2 ровно одна перегородка, а в прямоугольнике 2 × 3 ровно 7.В прямоугольнике 105 × 205 в центре вырезали дырку размера 15 × 15.Сколько перегородок в получившейся фигуре?  
  _Source: `Сб В классе/7 занятие.docx`; source line 1958._
- **D1 · corpus item 1365** — Сколько перегородок в прямоугольнике со сторонами равными двум наименьшим простым трехзначным числам?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1525._

**Generator templates:**

1. `H01-T1` — Сколько внутренних перегородок в прямоугольнике {m}×{n}, разбитом на единичные клетки?
   - Parameters: m,n>0.
   - Validation: Формула m(n-1)+n(m-1).
1. `H01-T2` — Стороны прямоугольника — числа {a},{b}. Найдите число перегородок.
   - Parameters: a,b могут быть получены из дополнительных условий.
   - Validation: Применяется формула для внутренних рёбер.

### H02 — Grid partitions in figures with holes / Перегородки в фигурах с вырезами

**Difficulty profile:** D3–D5

**Scope:** Update the count of adjacency edges after removing a central rectangle or another cell region.

**Corpus examples:**

- **D5 · corpus item 684** — В прямоугольнике 1 × 2 ровно одна перегородка, а в прямоугольнике 2 × 3 ровно 7. В прямоугольнике 105 × 205 в центре вырезали дырку размера 15 × 15. Сколько перегородок в получившейся фигуре?  
  _Source: `239-5_comb.pdf`; source line 799._
- **D5 · corpus item 705** — В прямоугольнике 1 × 2 ровно одна перегородка, а в прямоугольнике 2 × 3 ровно 7. В прямоугольнике 103 × 203 в центре вырезали дырку размера 13 × 13. Сколько перегородок в получившейся фигуре?  
  _Source: `239-5_comb.pdf`; source line 820._
- **D5 · corpus item 1400** — В прямоугольнике 1 × 2 ровно одна перегородка, а в прямоугольнике 2 × 3 - ровно 7. В прямоугольнике 408 × 915 в центре вырезали дырку размера 302 × 302. Сколько перегородок в получившейся фигуре?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1560._

**Generator templates:**

1. `H02-T1` — Из прямоугольника {M}×{N} вырезали центральный прямоугольник {a}×{b}. Сколько перегородок осталось?
   - Parameters: Вырез строго внутри.
   - Validation: Вычтены все рёбра, инцидентные удалённым клеткам.
1. `H02-T2` — Из квадрата удалили центральную область заданной формы. Найдите изменение числа внутренних рёбер.
   - Parameters: Фигура выровнена по сетке.
   - Validation: Учтены внутренние рёбра выреза и контакты с оставшейся частью.

### H03 — Cell-grid letters and polyomino boundaries / Клетчатые буквы и составные фигуры

**Difficulty profile:** D2–D5

**Scope:** Count partitions, cells, or boundary segments in large block letters or repeated polyominoes.

**Corpus examples:**

- **D3 · corpus item 1017** — 04 На рисунке изображена буква П , у которой - ширина 7 клеточек, высота 5, а толщина ножек и перекладины 2 клетки. Сколько клеток содержит аналогичная буква П ширины 70, высоты 60 и толщиной ножки и перекладины 6 клеток?  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1150._
- **D3 · corpus item 1123** — 3.1. На рисунке изображена буква О ширины 5, высоты 7, толщины 2 клетки. Суммарная длина её внутренних перегородок равна 48. Чему равна суммарная длина внутренних перегородок буквы a) П; b) С; с) E; d) H; e) L, у которой толщина 5, высота 45, ширина 35 клеток?  
  _Source: `Доп ДЗ/Доп ДЗ 07.docx`; source line 1262._
- **D3 · corpus item 1124** — 3.2. На рисунке изображена буква О ширины 5, высоты 7, толщины 2 клетки. Суммарная длина её внутренних перегородок равна 48. Чему равна суммарная длина внутренних перегородок буквы a) П; b) С; с) E; d) H; e) L, у которой толщина 7, высота 47, ширина 37 клеток?  
  _Source: `Доп ДЗ/Доп ДЗ 07.docx`; source line 1263._

**Generator templates:**

1. `H03-T1` — Клетчатая буква {letter} построена из полос толщины {t} и внешних размеров {m}×{n}. Сколько в ней клеток или перегородок?
   - Parameters: Геометрия буквы описана без неоднозначности.
   - Validation: Фигуру можно восстановить без изображения.
1. `H03-T2` — Составьте формулу для числа внутренних рёбер в фигуре из {n} повторяющихся клетчатых блоков.
   - Parameters: Способ соединения блоков задан.
   - Validation: Общие границы считаются один раз.

### H04 — Cutting boards and minimum number or time of cuts / Распилы досок и число разрезов

**Difficulty profile:** D2–D4

**Scope:** Relate number of pieces to cuts, or compare cutting schedules with stacking.

**Corpus examples:**

- **D3 · corpus item 207** — Коля распилил за 7 часов шахматную доску размера 8 × 8 на двухклеточные прямоугольники (доминошки) . За какое время он распилит доску 2 × 6 на трјхклеточные уголки ? Коля пилит с постоянной скоростью. Фигурки можно поворачивать и переворачивать, он пилит без остатка и наложений фигур  
  _Source: `2025-all.pdf`; source line 319._
- **D3 · corpus item 230** — Коля распилил за 3 часа шахматную доску размера 8 × 8 на двухклеточные прямоугольники (доминошки) . За какое время он распилит доску 2 × 9 на трјхклеточные уголки ? Коля пилит с постоянной скоростью. Фигурки можно поворачивать и переворачивать, он пилит без остатка и наложений фигур  
  _Source: `2025-all.pdf`; source line 342._
- **D3 · corpus item 1122** — 2. Коля распилил за 7 часов шахматную доску размера 8 х 8 на двухклеточные прямоугольники (доминошки). За какое время он распилит доску a) 12 × 9; b) 21 × 21; c) 31 × 31 (без угловой) на трехклеточные уголки? Коля пилит с постоянной скоростью. Фигурки можно поворачивать и переворачивать, он пилит без остатка и наложений фигур  
  _Source: `Доп ДЗ/Доп ДЗ 07.docx`; source line 1261._

**Generator templates:**

1. `H04-T1` — Доску нужно разделить на {n} частей последовательными распилами. Сколько минимум распилов?
   - Parameters: Складывание не разрешено, если не указано иное.
   - Validation: Ответ n-1.
1. `H04-T2` — Мастер распиливает доску на {p} частей за {t}. Сколько времени нужно на {q} частей при постоянном времени распила?
   - Parameters: p,q≥2.
   - Validation: Время пропорционально числу распилов, а не частей.

### H05 — Number of blocks after cutting a cube or cuboid / Число брусков после распила куба

**Difficulty profile:** D1–D3

**Scope:** Divide each dimension by block dimensions and multiply counts.

**Corpus examples:**

- **D2 · corpus item 66** — Петя взял деревянный куб со стороной 90 см и распилил его на бруски размером 0.5 × 2 × 3 дециметра. А Коля распилил такой же куб на бруски размером 3 × 6 × 12 см. a) У кого получилось больше брусков? b) На сколько у одного получилось больше количество брусков, чем у другого?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 103._
- **D2 · corpus item 86** — Петя взял деревянный куб со стороной 120 см и распилил его на бруски размером 1 × 2 × 3 дециметра. А Коля распилил такой же куб на бруски размером 4 × 6 × 12 см. a) У кого получилось больше брусков? b) На сколько у одного получилось больше количество брусков, чем у другого?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 126._
- **D2 · corpus item 1187** — 7. Петя распилил деревянный куб со стороной 60 см на бруски 2 × 3 × 5 см, а Коля - такой же куб на бруски 1 × 4 × 6 см. а) У кого получилось больше брусков? б) На сколько больше?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1329._

**Generator templates:**

1. `H05-T1` — Куб со стороной {L} разрезали на бруски {a}×{b}×{c}. Сколько брусков?
   - Parameters: Размеры после перевода единиц делят L.
   - Validation: Число равно (L/a)(L/b)(L/c).
1. `H05-T2` — Параллелепипед {A}×{B}×{C} разрезали на кубики стороны {s}. Сколько кубиков?
   - Parameters: s делит все размеры.
   - Validation: Ответ ABC/s³.

### H06 — Comparing two cuboid-cutting schemes / Сравнение двух способов распила

**Difficulty profile:** D2–D4

**Scope:** Compare the number of blocks produced by different block dimensions and compute the difference.

**Corpus examples:**

- **D3 · corpus item 66** — Петя взял деревянный куб со стороной 90 см и распилил его на бруски размером 0.5 × 2 × 3 дециметра. А Коля распилил такой же куб на бруски размером 3 × 6 × 12 см. a) У кого получилось больше брусков? b) На сколько у одного получилось больше количество брусков, чем у другого?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 103._
- **D3 · corpus item 86** — Петя взял деревянный куб со стороной 120 см и распилил его на бруски размером 1 × 2 × 3 дециметра. А Коля распилил такой же куб на бруски размером 4 × 6 × 12 см. a) У кого получилось больше брусков? b) На сколько у одного получилось больше количество брусков, чем у другого?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 126._
- **D3 · corpus item 1187** — 7. Петя распилил деревянный куб со стороной 60 см на бруски 2 × 3 × 5 см, а Коля - такой же куб на бруски 1 × 4 × 6 см. а) У кого получилось больше брусков? б) На сколько больше?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1329._

**Generator templates:**

1. `H06-T1` — Два одинаковых куба разрезали на бруски размеров {a1}×{b1}×{c1} и {a2}×{b2}×{c2}. У кого больше и на сколько?
   - Parameters: Оба разбиения корректны.
   - Validation: Единицы переведены; оба количества целые.
1. `H06-T2` — Сравните два разбиения параллелепипеда на одинаковые малые блоки.
   - Parameters: Повороты блоков разрешены или запрещены явно.
   - Validation: Для каждого варианта существует укладка без остатка.

### H07 — Painted cubes: number of painted faces / Окрашенный куб и число окрашенных граней

**Difficulty profile:** D2–D4

**Scope:** Count small cubes with zero, one, two, or three painted faces after painting a solid and cutting it.

**Corpus examples:**

- **D3 · corpus item 154** — Поверхность куба со стороной 6 см покрасили снаружи в красный цвет. После этого его распилили на кубики со стороной 1 см. У каждого из получившихся кубиков посчитали количество красных граней. У скольких кубиков это количество нечетное?  
  _Source: `15-минутки/Март 2026/18.03.2026.pdf`; source line 233._
- **D3 · corpus item 1529** — Поверхность куба со стороной 6см покрасили снаружи в красный цвет. После этого его распилили на кубики со стороной 1 см. У каждого из получившихся кубиков посчитали количество красных граней. У скольких кубиков это количество не равно двум?  
  _Source: `Сб В классе/1 занятие.docx`; source line 1692._
- **D3 · corpus item 1602** — Деревянный параллелепипед со сторонами 5*6*7 облили красной краской. После этого его распилили на кубики с единичной стороной. Сколько получилось кубиков с закрашенными a) 1; b) 2; c) 3 d) 0 сторонами?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1774._

**Generator templates:**

1. `H07-T1` — Куб {n}×{n}×{n} покрасили снаружи и разрезали на единичные кубики. Сколько имеют 0,1,2,3 окрашенных граней?
   - Parameters: n≥3.
   - Validation: Используются формулы для внутренних, гранных, рёберных и угловых кубиков.
1. `H07-T2` — У скольких маленьких кубиков число окрашенных граней нечётно?
   - Parameters: n≥2.
   - Validation: Считаются кубики ровно с 1 и 3 окрашенными гранями.

### H08 — Surface paint and scale factors / Расход краски на поверхность

**Difficulty profile:** D1–D4

**Scope:** Scale paint amount with total surface area, including boxes and cuboids.

**Corpus examples:**

- **D2 · corpus item 130** — Чтобы покрасить поверхность (все грани) деревянного кубика высотой 1 см нужно 1 гкраски. Сколько краски понадобится, чтобы покрасить деревянный куб высотой 4 см?  
  _Source: `15-минутки/Март 2026/12.03.2026.pdf`; source line 194._
- **D2 · corpus item 140** — Чтобы покрасить поверхность (все грани) деревянного кубика высотой 1 см нужно 1 гкраски. Сколько краски понадобится, чтобы покрасить деревянный куб высотой 5 см?  
  _Source: `15-минутки/Март 2026/14.03.2026.pdf`; source line 210._
- **D2 · corpus item 1552** — Чтобы покрасить поверхность (все грани) деревянного кубика высотой 2 см нужно 370 мг краски. Сколько краски понадобится, чтобы покрасить деревянный ящик размером 4 × 4 × 7 дециметров? b) 14 × 12 × 9?  
  _Source: `Сб В классе/10 занятие.docx`; source line 1718._

**Generator templates:**

1. `H08-T1` — На покраску куба стороны {a} нужно {m} г краски. Сколько нужно для куба стороны {b}?
   - Parameters: Толщина слоя одинаковая.
   - Validation: Расход масштабируется как (b/a)².
1. `H08-T2` — Сколько краски нужно для закрытого ящика {A}×{B}×{C}, если известен расход на единицу площади?
   - Parameters: Единицы согласованы.
   - Validation: Площадь 2(AB+AC+BC).

### H09 — Face labels determined by visible faces / Подписи на гранях малых кубиков

**Difficulty profile:** D3–D5

**Scope:** After subdividing a cube, label all faces of each small cube by the number of visible outer faces and sum all labels.

**Corpus examples:**

- **D4 · corpus item 1186** — 6. Иван взял деревянный куб со стороной 8 дм и разрезал его на маленькие кубики со стороной 1 дм. На каждой грани каждого маленького кубика он написал число, равное числу видимых граней этого кубика в большом кубе. Затем сложил все написанные числа. Что получилось?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1328._
- **D4 · corpus item 70** — Иван взял большой деревянный кубик со стороной 7 дм, разрезал его на маленькие кубики со стороной 1 дм. Взял кисточку и на каждой грани каждого из них написал число - такое, сколько граней видно у этого кубика. Например у него получилось 8 кубиков, на каждом из которых записаны шесть чисел три. Потом он выложил их в ряд и посчитал сумму чисел на всех гранях всех маленьких кубиков. Что за число он получил?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 107._
- **D4 · corpus item 90** — Иван взял маленький деревянный кубик со стороной 9 см, разрезал его на маленькие кубики со стороной 1 см. Взял кисточку и на каждой грани каждого из них написал число - такое, сколько граней видно у этого кубика. Например у него получилось 8 кубиков, на каждом из которых записаны шесть чисел три. Потом он выложил их в ряд и посчитал сумму чисел на всех гранях всех маленьких кубиков. Что за число он получил?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 130._

**Generator templates:**

1. `H09-T1` — Куб {n}×{n}×{n} разрезали на единичные. На каждой грани малого кубика написали число видимых внешних граней этого кубика. Найдите сумму.
   - Parameters: n≥2.
   - Validation: Кубик с v видимыми гранями даёт вклад 6v.
1. `H09-T2` — Выведите общую формулу суммы надписей и вычислите её при n={n}.
   - Parameters: n задано.
   - Validation: Кубики классифицированы по положению.

## I. Time, calendars, and clocks / Время, календарь и часы (8 themes)

### I01 — Day of week after a number of days / День недели через N дней

**Difficulty profile:** D1–D2

**Scope:** Advance a weekday by a given number of days modulo 7.

**Corpus examples:**

- **D1 · corpus item 1403** — Сегодня 2 апреля 2026 года. Какой день недели будет через 2026 дней?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1563._
- **D1 · template-derived illustration** — Сегодня среда. Какой день недели будет через 100 дней?
- **D2 · template-derived illustration** — 1 января было воскресенье. Какой день недели будет 1 марта невисокосного года?

**Generator templates:**

1. `I01-T1` — Сегодня {weekday}. Какой день недели будет через {N} дней?
   - Parameters: N>0.
   - Validation: Используется N mod 7.
1. `I01-T2` — Какой день недели был {N} дней назад, если сегодня {weekday}?
   - Parameters: N>0.
   - Validation: Вычитание по модулю 7.

### I02 — Weekday counts within a month / Число дней недели в месяце

**Difficulty profile:** D2–D4

**Scope:** Infer the weekday of a date from which weekdays occur five times in a month.

**Corpus examples:**

- **D2 · corpus item 41** — В некотором году в марте было четвергов больше, чем сред. А какого числа в том году был первый понедельник лета?  
  _Source: `15-минутки/Апрель 2026/15.04.2026.pdf`; source line 69._
- **D2 · corpus item 1605** — В некотором году в апреле было четвергов больше, чем вторников. А какого числа в том году был четвертый четверг лета?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1777._
- **D2 · corpus item 1717** — В некотором году в марте было суббот больше, чем пятниц. А какого числа в том году был первый понедельник лета?  
  _Source: `Сб В классе/5 занятие.docx`; source line 1901._

**Generator templates:**

1. `I02-T1` — В месяце из {days} дней {weekday1} было больше, чем {weekday2}. Какой день недели был 1-го числа?
   - Parameters: days∈{28,29,30,31}.
   - Validation: Учтены лишние дни после полных недель.
1. `I02-T2` — В некотором мае суббот больше, чем пятниц. Определите возможные даты первого понедельника лета.
   - Parameters: Длина мая фиксирована.
   - Validation: Перебраны все допустимые начала месяца.

### I03 — Last or nth weekday of a month / Последний или n-й день недели месяца

**Difficulty profile:** D2–D4

**Scope:** Find possible dates or day-of-year numbers for the last or nth weekday.

**Corpus examples:**

- **D4 · corpus item 59** — У одной моей группы последнее занятие будет в последний четверг мая. Каким по счету днем этого года может быть этот день? Например, 1 февраля - 32-й день года. Перечислите через точку с запятой все возможные варианты  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 96._
- **D4 · corpus item 79** — У одной моей группы последнее занятие будет в последнюю субботу мая. Каким по счету днем этого года может быть этот день? Например, 1 февраля - 32-й день года. Перечислите через точку с запятой все возможные варианты  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 119._
- **D4 · corpus item 1061** — 8 Вступительная работа в 5 класс проводится в последнюю субботу июня. Каким по счёту днём года может быть день вступительной работы? Перечислите через точку с запятой все возможные варианты  
  _Source: `Доп ДЗ/Доп ДЗ 06.docx`; source line 1197._

**Generator templates:**

1. `I03-T1` — Какой датой может быть последний {weekday} мая? Перечислите варианты.
   - Parameters: weekday фиксирован.
   - Validation: Ответы лежат в диапазоне 25–31.
1. `I03-T2` — Каким по счёту днём года является {nth}-й {weekday} месяца?
   - Parameters: Тип года задан или перечисляются оба.
   - Validation: Суммы длин предыдущих месяцев верны.

### I04 — Direct time-zone conversion / Прямой перевод времени между часовыми поясами

**Difficulty profile:** D1–D3

**Scope:** Convert local times between cities and combine with a travel duration.

**Corpus examples:**

- **D2 · corpus item 991** — 8 Поезд из Москвы выходит в 00-35 и приходит в Талдан в 18-15 местного времени. Обратный поезд идет столько же времени и выходит из Талдана в 8-23 местного времени, а приходит в Москву в 14-03. Какова разница во времени между Москвой и Талданом?  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1124._
- **D2 · corpus item 993** — 10 Когда в Петербурге 12:12, то в Екатеринбурге 14:12. Когда в Екатеринбурге 12:15, то Хабаровске 17:15. Самолёт вылетел из Хабаровска в Петербург в 10:15 и летел 8 часов 40 минут. Во сколько он приземлился?  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1126._
- **D2 · corpus item 1714** — Поезд из Москвы выходит в 00:35 и приходит в Талдан в 18:15 местного времени. Обратный поезд идет столько же времени и выходит из Талдана в 8:23 местного времени, а приходит в Москву в 14:03. Какова разница во времени между Москвой и Талданом?  
  _Source: `Сб В классе/5 занятие.docx`; source line 1898._

**Generator templates:**

1. `I04-T1` — Когда в городе A {tA}, в городе B {tB}. Самолёт вылетел из B в {depart} и летел {duration}. Когда он прилетел по времени A?
   - Parameters: Разница часовых поясов постоянна.
   - Validation: Учтён переход через полночь.
1. `I04-T2` — В городе B на {h} часов больше, чем в A. Переведите время {t} из A в B.
   - Parameters: h — целое.
   - Validation: Результат нормализован к 24-часовому формату.

### I05 — Multi-leg travel across time zones / Маршрут с пересадками и часовыми поясами

**Difficulty profile:** D2–D4

**Scope:** Track local time through several flights, layovers, and time-zone changes.

**Corpus examples:**

- **D3 · corpus item 990** — 7 Катя вылетела из Парижа в Рим в 12:50 по парижскому времени. В пути она провела 1 час 55 минут. Разница между Парижем и Римом отсутствует. После 2 часов в аэропорту она вылетела в Афины, перелёт занял 2 часа 25 минут. В Афинах на час больше, чем в Париже. Во сколько по афинскому времени Катя прилетела?  
  _Source: `Доп ДЗ/Доп ДЗ 05.docx`; source line 1123._
- **D3 · corpus item 1356** — Катя вылетела из Парижа в Рим в 12:50 по парижскому времени. В пути она провела 1 час 55 минут. Разница между Парижем и Римом отсутствует. После 2 часов в аэропорту она вылетела в Афины, перелёт занял 2 часа 25 минут. В Афинах на час больше, чем в Париже. Во сколько по афинскому времени Катя прилетела?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1516._
- **D3 · corpus item 1351** — Когда в Петербурге 14:12, то в Новосибирске 18:12. Когда в Новосибирске 15:12, то Якутске 18:12. Вася сел на самолет и вылетел из Якутска в Петербург в 6:47 и летел 8 часов 14 минут. Затем съев за полчаса корюшку он полетел обратно. Во сколько он приземлился в Якутске, если обратный полет делал вынужденную посадку на час в Москве?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1511._

**Generator templates:**

1. `I05-T1` — Путешественник летит A→B {t1}, ждёт {w}, затем B→C {t2}. Даны разницы времени. Когда он прибывает в C?
   - Parameters: Два перелёта и две разницы поясов.
   - Validation: Все моменты переведены через одну временную шкалу.
1. `I05-T2` — Самолёт совершил вынужденную посадку на {w}. Найдите местное время прибытия после обратного рейса.
   - Parameters: Длительности и пояса заданы.
   - Validation: Учтён переход даты.

### I06 — Turnaround trips with local-time data / Разворот в пути и восстановление момента по местному времени

**Difficulty profile:** D3–D5

**Scope:** Recover a turnaround time when eastbound and westbound durations have a known ratio and endpoints use different local times.

**Corpus examples:**

- **D5 · corpus item 216** — Якутск восточнее Петербурга и сейчас там на 6 часов больше, чем в Петербурге. Самолјт вылетел из Петербурга в 10:00 на восток, но в некоторый момент испортилась погода, он развернулся и сел в Якутске в 03:00. Известно, что на восток он летел в три раза дольше, чем на запад. Во сколько самолјт развернулся по Якутскому времени?  
  _Source: `2025-all.pdf`; source line 328._
- **D5 · corpus item 199** — Иркутск восточнее Москвы Ha 5 часа. Поезд выехал из Москвы в 21:15, ехал некоторое время на восток, затем из-за преграды на рельсах вернулся назад и прибыл в Иркутск в 19:00 по местному времени. Известно, что в восточном направлении он ехал в 4 раза дольше, чем в западном. Во сколько поезд развернулся по московскому времени?  
  _Source: `15-минутки/Март 2026/30.03.2026.pdf`; source line 305._
- **D5 · corpus item 57** — Самара восточнее Калининграда, и сейчас там на 2 часа больше. Калининград западнее Екатеринбург и разница во времени 3 часа. Самолёт вылетел из Самары в 08:30 на восток, но из-за непогоды в некоторый момент развернулся и сел в Екатеринбурге в 18:50. Известно, что на восток он летел в 3 раза дольше, чем на запад после разворота. Во сколько самолет развернулся по екатеринбургскому времени?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 94._

**Generator templates:**

1. `I06-T1` — Транспорт выехал из A, ехал на восток, развернулся и прибыл в B. Восточный участок длился в {k} раз дольше западного. Найдите момент разворота в поясе C.
   - Parameters: Времена и смещения согласованы.
   - Validation: Сначала все времена переводятся в один пояс.
1. `I06-T2` — Поезд двигался в одном направлении t, затем обратно t/{k}. По местным временам известны отправление и прибытие. Найдите t.
   - Parameters: Получается положительная длительность.
   - Validation: Учтён переход суток.

### I07 — Clocks that gain or lose time / Спешащие и отстающие часы

**Difficulty profile:** D3–D5

**Scope:** Find when inaccurate clocks next show the same display or the correct time.

**Corpus examples:**

- **D4 · corpus item 71** — Васины часы уходят вперёд на 15 минут в день, а часы Пети отстают на 10 минут в день. 26 марта в полдень на Васиных часах 22 : 00, а на Петиных 16 : 00. Какого числа и какого месяца впервые после 26 марта в полдень их часы покажут одинаковое время одновременно?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 108._
- **D4 · corpus item 91** — Васины часы уходят вперёд на 15 минут в день, а часы Пети отстают на 10 минут в день. 28 марта в полдень на Васиных часах 21 : 00, а на Петиных 11 : 00. Какого числа и какого месяца впервые после 28 марта в полдень их часы покажут одинаковое время одновременно?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 131._
- **D4 · corpus item 1744** — Васины часы уходят вперёд на 15 минут в день, а часы Пети отстают на 10 минут в день. 1 мая в полдень на Васиных часах 17 : 00, а на Петиных 13 : 00. Какого числа и какого месяца впервые после 1 мая в полдень их часы покажут одинаковое время одновременно?  
  _Source: `Сб В классе/6 занятие.docx`; source line 1931._

**Generator templates:**

1. `I07-T1` — Одни часы спешат на {a} минут в сутки, другие отстают на {b}. Сейчас показания различаются на {D}. Когда они совпадут?
   - Parameters: Формат 12 или 24 часа указан.
   - Validation: Решается относительный дрейф по модулю цикла дисплея.
1. `I07-T2` — Часы спешат на {a} минут в день. Через сколько дней они впервые снова покажут правильное время?
   - Parameters: Указан 12- или 24-часовой циферблат.
   - Validation: Найден минимальный положительный период.

### I08 — Digital displays and analog clock mechanisms / Цифровые табло и стрелочные часы

**Difficulty profile:** D2–D5

**Scope:** Search clock displays for digit constraints or reason about hand motion and chimes.

**Corpus examples:**

- **D2 · corpus item 19** — На электронном табло высвечивается время 10 : 20 : 30. В какое время после этого в 7 раз все цифры на табло будут различными?  
  _Source: `15-минутки/Апрель 2026/06.04.2026.pdf`; source line 32._
- **D2 · corpus item 67** — На электронном табло высвечивается время 23 : 23 : 23. В какое время после этого в десятый раз все цифры на табло будут различными?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 104._
- **D2 · corpus item 87** — На электронном табло высвечивается время 21 : 21 : 21. В какое время до этого в пятый раз все цифры на табло были различными?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 127._

**Generator templates:**

1. `I08-T1` — На табло hh:mm:ss показано {time}. Когда после этого в {k}-й раз все шесть цифр будут различны?
   - Parameters: Корректное время в 24-часовом формате.
   - Validation: Явно указано, считается ли начальный момент.
1. `I08-T2` — Минутную стрелку вращают, пока часовая вернётся в исходное положение. Сколько ударов или оборотов произойдёт?
   - Parameters: Правила механизма и боя часов заданы.
   - Validation: Используется отношение угловых скоростей 12:1.

## J. Motion and rates / Движение и скорости (7 themes)

### J01 — Basic distance-speed-time relations / Базовые задачи на путь, скорость и время

**Difficulty profile:** D1–D3

**Scope:** Use s=vt for one moving object or a direct comparison.

**Corpus examples:**

- **D2 · corpus item 1569** — Расстояние между Атосом и Арамисом, скачущими по одной дороге, равно 20 лье. За час Атос покрывает 4 лье, а Арамис - 5 лье. Какое расстояние будет между ними через час?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1738._
- **D1 · corpus item 1573** — Андрей ведёт машину со скоростью 60 км/ч. Он хочет проезжать каждый километр на 1 минуту быстрее. На сколько ему следует увеличить скорость?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1742._
- **D2 · corpus item 456** — Впереди на прямой дороге собака заметила кусок колбасы. Собака бежит к колбасе со скоростью 30км/ч, а потом сразу бежит обратно к хозяину со скоростью 15 км/ч. Хозяин идёт за собакой со скоростью 5 км/ч. Они встретились через 9 минут. Какое расстояние пробежала собака?  
  _Source: `239-5_comb.pdf`; source line 571._

**Generator templates:**

1. `J01-T1` — Объект движется со скоростью {v} км/ч в течение {t}. Какой путь он прошёл?
   - Parameters: v,t>0.
   - Validation: Единицы согласованы.
1. `J01-T2` — Скорость {v} км/ч. На сколько её изменить, чтобы каждый километр проходить на {dt} минут быстрее?
   - Parameters: dt<60/v.
   - Validation: Сначала находится новая скорость через темп мин/км.

### J02 — Meeting in opposite directions / Встречное движение

**Difficulty profile:** D2–D4

**Scope:** Find meeting time, distance, or start separation for objects moving toward each other.

**Corpus examples:**

- **D3 · corpus item 753** — Два поезда, оба длиной 50 м, движутся навстречу друг другу со скоростью 45 км/ч. Сколько времени пройдёт от момента, когда встретятся машинисты, до момента, когда встретятся проводники последних вагонов?  
  _Source: `3.0 КТП + Задачи Интенсив ОлМат .docx`; source line 871._
- **D4 · corpus item 1081** — 11. Два всадника одновременно скачут навстречу друг другу из Парижа в Версаль (расстояние между ними 40 км). Скорость первого 10 км/ч, скорость второго - 14 км/ч. На шлеме первого всадника сидела бешеная муха и как только он тронулся она полетела в направлении второго всадника со скоростью 1000 м/мин. Как только она долетела до всадника - она развернулась и полетела к первому, затем как только она долетела до перв…  
  _Source: `Доп ДЗ/Доп ДЗ 06.docx`; source line 1217._
- **D2 · template-derived illustration** — Из двух городов навстречу друг другу одновременно выехали автомобили со скоростями 60 и 75 км/ч. Расстояние между городами 405 км. Через сколько часов они встретятся?

**Generator templates:**

1. `J02-T1` — Из A и B навстречу вышли два участника со скоростями {v1},{v2}. Расстояние {S}. Когда встретятся?
   - Parameters: Положительные значения.
   - Validation: t=S/(v1+v2).
1. `J02-T2` — Они встретились через {t}. Один прошёл на {d} больше. Найдите скорости или расстояние.
   - Parameters: Данных достаточно для единственного решения.
   - Validation: Все найденные величины положительны.

### J03 — Catch-up motion in one direction / Движение вдогонку

**Difficulty profile:** D2–D4

**Scope:** Use relative speed to find catch-up time or initial lead.

**Corpus examples:**

- **D2 · corpus item 968** — Ваня вышел из дома на 1 час 45 минут раньше Пети. Через какое время Петя догонит Ваню, если скорость Вани 4 км/ч, а скорость Пети 6 км/ч?  
  _Source: `Доп ДЗ/Доп ДЗ 04.docx`; source line 1098._
- **D3 · corpus item 60** — На прямой дороге расположены 3 домика. Из них одновременно вышли 3 человека. Первый пошел направо со скоростью 4 км/ч, а второй и третий налево со скоростью 3 и 5 километра в час соответственно. Первый встретил второго через 2 часа, а третьего через 2 часа 40 мин после выхода. Через какое время после встречи c первым человеком, третий догонит второго?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 97._
- **D3 · corpus item 80** — На прямой дороге расположены 3 домика. Из них одновременно вышли 3 человека. Первый пошел направо со скоростью 4 км/ч, а второй и третий налево со скоростью 3 и 5 километра в час соответственно. Первый встретил второго через 4 часа, а третьего через 4 часа 40 мин после выхода. Через какое время после встречи c первым человеком, третий догонит второго?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 120._

**Generator templates:**

1. `J03-T1` — Первый движется со скоростью {v1}, второй впереди на {S} и движется со скоростью {v2}<v1. Через сколько первый догонит?
   - Parameters: v1>v2.
   - Validation: t=S/(v1-v2).
1. `J03-T2` — Более быстрый объект стартует через {tau} после медленного. Когда он догонит?
   - Parameters: Скорость быстрого больше.
   - Validation: Начальный отрыв равен v_slow·tau.

### J04 — Three movers and hidden initial positions / Три участника и скрытые расстояния

**Difficulty profile:** D3–D5

**Scope:** Use two meeting times to reconstruct spacing and then a later catch-up.

**Corpus examples:**

- **D4 · corpus item 60** — На прямой дороге расположены 3 домика. Из них одновременно вышли 3 человека. Первый пошел направо со скоростью 4 км/ч, а второй и третий налево со скоростью 3 и 5 километра в час соответственно. Первый встретил второго через 2 часа, а третьего через 2 часа 40 мин после выхода. Через какое время после встречи c первым человеком, третий догонит второго?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 97._
- **D4 · corpus item 80** — На прямой дороге расположены 3 домика. Из них одновременно вышли 3 человека. Первый пошел направо со скоростью 4 км/ч, а второй и третий налево со скоростью 3 и 5 километра в час соответственно. Первый встретил второго через 4 часа, а третьего через 4 часа 40 мин после выхода. Через какое время после встречи c первым человеком, третий догонит второго?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 120._
- **D4 · corpus item 1185** — 5. На прямой дороге расположены три домика. Из них одновременно вышли три человека. Первый пошёл направо со скоростью 5 км/ч, второй и третий - налево со скоростями 4 км/ч и 7 км/ч. Первый встретил второго через 3 часа, а третьего через 4 часа после выхода. Через какое время после встречи с первым человеком третий догонит второго?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1327._

**Generator templates:**

1. `J04-T1` — На прямой три дома. Трое вышли одновременно; известны скорости и времена встреч первого со вторым и третьим. Когда третий догонит второго?
   - Parameters: Направления и скорости согласованы.
   - Validation: Сначала восстановлены оба начальных расстояния.
1. `J04-T2` — Три участника движутся по прямой; по двум событиям встреч найдите третье событие.
   - Parameters: Линейные функции координат.
   - Validation: Начальные положения определяются с точностью до общего сдвига.

### J05 — Out-and-back and turnaround motion / Движение туда-обратно и развороты

**Difficulty profile:** D2–D5

**Scope:** Analyze a mover who turns around after meeting or at an unknown point.

**Corpus examples:**

- **D3 · corpus item 456** — Впереди на прямой дороге собака заметила кусок колбасы. Собака бежит к колбасе со скоростью 30км/ч, а потом сразу бежит обратно к хозяину со скоростью 15 км/ч. Хозяин идёт за собакой со скоростью 5 км/ч. Они встретились через 9 минут. Какое расстояние пробежала собака?  
  _Source: `239-5_comb.pdf`; source line 571._
- **D3 · corpus item 475** — Впереди на прямой дороге собака заметила кусок колбасы. Собака бежит к колбасе со скоростью 30км/ч, а потом сразу бежит обратно к хозяину со скоростью 12 км/ч. Хозяин идёт за собакой со скоростью 6 км/ч. Они встретились через 7 минут. Какое расстояние пробежала собака?  
  _Source: `239-5_comb.pdf`; source line 590._
- **D3 · corpus item 535** — В домике на шоссе живёт велосипедист Олег. Однажды он выехал из дома в магазин. Доехав до магазина, он сообразил, что забыл карточку, и поехал обратно в два раза быстрее. Он так сильно переживал, что проехал мимо своего дома некоторое расстояние. Повернув назад и ещё в два раза увеличив скорость, Олег успешно остановился у дома через 5 часов после того как выехал из него. Сколько времени Олег ехал, удаляясь от сво…  
  _Source: `239-5_comb.pdf`; source line 650._

**Generator templates:**

1. `J05-T1` — Из A в B выехал велосипедист, навстречу вышел пешеход. После встречи велосипедист повернул обратно. По разнице времён прибытия найдите время пешехода.
   - Parameters: Отношение скоростей задано.
   - Validation: Используются доли пути до точки встречи.
1. `J05-T2` — Объект движется вперёд t, затем назад t/{k}. Найдите положение и общий путь.
   - Parameters: Скорости постоянны.
   - Validation: Путь и перемещение не смешиваются.

### J06 — Piecewise motion and average speed / Средняя скорость и движение по участкам

**Difficulty profile:** D2–D5

**Scope:** Compare half-distance and half-time regimes or compute total time across segments.

**Corpus examples:**

- **D3 · corpus item 1571** — Буратино и Пьеро бежали наперегонки. Пьеро весь путь бежал с одной и той же скоростью, а Буратино первую половину пути бежал вдвое быстрее, чем Пьеро, а вторую половину - вдвое медленней, чем Пьеро. Кто победил?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1740._
- **D3 · corpus item 1574** — Вадим и Лёша спускались с горы. Вадим шёл пешком, а Лёша съезжал на лыжах в семь раз быстрее Вадима. На полпути Лёша упал, сломал лыжи и ногу и пошёл в два раза медленней Вадима. Кто первым спустится с горы?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1743._
- **D3 · corpus item 1615** — Один путник шел первые полпути со скоростью 4 км/ч, а вторые полпути со скоростью 6 км/ч. Другой путник шел первую половину времени со скоростью со скоростью 4км/ч, а вторую половину времени со скоростью 6 км/ч. С какой постоянной скоростью должен был бы идти каждый из них, чтобы затратить на свое путешествие то же самое время?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1787._

**Generator templates:**

1. `J06-T1` — Первую половину пути прошли со скоростью {v1}, вторую — {v2}. Найдите среднюю скорость.
   - Parameters: v1,v2>0.
   - Validation: Средняя скорость — гармоническое среднее.
1. `J06-T2` — Первую половину времени двигались со скоростью {v1}, вторую — {v2}. Найдите среднюю скорость.
   - Parameters: v1,v2>0.
   - Validation: Средняя скорость — арифметическое среднее.

### J07 — Circular motion, laps, and races / Движение по кругу и соревнования

**Difficulty profile:** D3–D5

**Scope:** Use relative angular speed, lap frequency, or discrete jumps in a race.

**Corpus examples:**

- **D4 · corpus item 1571** — Буратино и Пьеро бежали наперегонки. Пьеро весь путь бежал с одной и той же скоростью, а Буратино первую половину пути бежал вдвое быстрее, чем Пьеро, а вторую половину - вдвое медленней, чем Пьеро. Кто победил?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1740._
- **D4 · corpus item 1576** — Две лягушки Ква и Кви участвуют в "забеге" - 20 метров вперед по прямой и обратно. Ква преодолевает за один прыжок 6 дм, а Кви только 4, но зато Кви делает три прыжка в то время, как ее соперница делает два. Скажите, каков при этих обстоятельствах возможный исход состязания?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1745._
- **D4 · corpus item 1582** — Отец и сын катаются на коньках по кругу. Время от времени отец обгоняет сына. После того, как сын переменил направление своего движения на противоположное, они стали встречаться в 5 раз чаще. Во сколько раз отец бегает быстрее сына?  
  _Source: `Сб В классе/11 занятие.docx`; source line 1751._

**Generator templates:**

1. `J07-T1` — Два участника движутся по кругу в одном или противоположных направлениях. Как часто они встречаются?
   - Parameters: Длина круга и скорости заданы.
   - Validation: Используется относительная скорость; стартовые положения указаны.
1. `J07-T2` — Два прыгуна проходят путь туда и обратно; длины и частоты прыжков различны. Кто победит?
   - Parameters: Правило разворота и перепрыгивания финиша задано.
   - Validation: Дискретность прыжков учтена.

## K. Logic, invariants, and algorithms / Логика, инварианты и алгоритмы (8 themes)

### K01 — Truth-tellers, liars, and role deduction / Рыцари, лжецы и логические роли

**Difficulty profile:** D3–D5

**Scope:** Determine roles from statements that are always true or always false.

**Corpus examples:**

- **D4 · corpus item 1667** — В одном городе все люди были торговцами или гончарами. Торговцы всегда говорили неправду, а гончары - правду. Когда все люди собрались на площади, каждый из собравшихся сказал остальным: «Вы все торговцы!» Сколько гончаров было в этом городе?  
  _Source: `Сб В классе/3 занятие.docx`; source line 1845._
- **D3 · corpus item 1676** — Известно, что тот, кто решил больше всех, сказал правду, а остальные --- солгали. Кто решил больше всех задач?  
  _Source: `Сб В классе/3 занятие.docx`; source line 1854._
- **D3 · corpus item 1702** — Третий (остальным): Все что вы тут наговорили --- вранье. Только я --- эльф. Кто есть кто?  
  _Source: `Сб В классе/4 занятие.docx`; source line 1883._

**Generator templates:**

1. `K01-T1` — За столом сидят рыцари и лжецы. Каждый говорит: «{statement}». Сколько рыцарей возможно?
   - Parameters: Высказывание локальное или глобальное.
   - Validation: Проверены все согласованные распределения ролей.
1. `K01-T2` — Несколько персонажей делают взаимосвязанные заявления о своих ролях. Кто есть кто?
   - Parameters: 2–5 персонажей.
   - Validation: Решение единственно.

### K02 — Exactly one incorrect calculation / Ровно одна ошибка в вычислениях

**Difficulty profile:** D2–D4

**Scope:** Match products to multipliers when exactly one reported answer is wrong.

**Corpus examples:**

- **D4 · corpus item 69** — Учитель выписал на доску число. Вася должен был умножить число на 23, Коля - на 27, а Петя - на 29. В итоге у них получились ответы 3841, 4509, 4823 в каком-то порядке. Известно, что ровно один из мальчиков ошибся. Кто ошибся, и какой у него должен быть верный ответ?  
  _Source: `15-минутки/КР/1 вариант. Президентский Физико-Математический Лицей №239 (3).pdf`; source line 106._
- **D4 · corpus item 89** — Учитель выписал на доску число. Вася должен был умножить число на 43, Коля - на 47, а Петя - на 51. В итоге у них получились ответы 10277, 11233, 12179 в каком-то порядке. Известно, что ровно один из мальчиков ошибся. Кто ошибся, и какой у него должен быть верный ответ?  
  _Source: `15-минутки/КР/2 вариант. Президентский Физико-Математический Лицей №239 (1).pdf`; source line 129._
- **D4 · corpus item 1177** — 7. Учитель выписал число. Вася должен был умножить его на 14, Коля - на 18, а Петя - на 22. У них получились ответы 1988, 2556 и 2838 в каком-то порядке. Известно, что ровно один ошибся. Кто ошибся, и какой ответ должен был получиться у него?  
  _Source: `Доп ДЗ/Доп ДЗ 09.docx`; source line 1319._

**Generator templates:**

1. `K02-T1` — Трое умножали одно число на {a},{b},{c} и получили {r1},{r2},{r3} в неизвестном порядке. Ровно один ошибся. Кто и каков верный ответ?
   - Parameters: Два результата соответствуют одному общему исходному числу.
   - Validation: Виновник и правильный ответ определяются однозначно.
1. `K02-T2` — Из нескольких равенств ровно одно неверно. Найдите его, не вычисляя всё полностью.
   - Parameters: Есть общие множители или делимость.
   - Validation: Ровно одно противоречие.

### K03 — Elevator reachability with fixed moves / Лифт с двумя кнопками и достижимость этажей

**Difficulty profile:** D2–D5

**Scope:** Determine whether floor differences can be represented by allowed up and down moves while respecting building bounds.

**Corpus examples:**

- **D3 · corpus item 814** — 1. Лифт 100-этажного дома испортил хулиган Вася, и теперь там работают только две кнопки: кнопка, позволяющая спуститься на 9 этажей, и кнопка, позволяющая подняться на 7 этажей. Можно ли пользуясь этим лифтом попасть a) с 1-го этажа на 2-ой? b) со 2-го этажа на 1-ый?  
  _Source: `Доп ДЗ/Доп ДЗ 01.docx`; source line 935._
- **D3 · corpus item 1528** — Лифт 100-этажного дома испортил хулиган Вася, и теперь там работают только две кнопки: кнопка, позволяющая спуститься на 9 этажей, и кнопка, позволяющая подняться на 7 этажей. Можно ли пользуясь этим лифтом попасть a) с 1-го этажа на 2-ой? b) со 2-го этажа на 1-ый?  
  _Source: `Сб В классе/1 занятие.docx`; source line 1691._
- **D3 · corpus item 1297** — Жильцы 30-этажного дома вызвали ремонтную бригаду, и она попыталась отремонтировать лифт. В нем по-прежнему работают только две кнопки: "+5" и "-7". Могут ли Аня и Миша доехать на новом лифте от Ани, живущей на 4 этаже, до друга Паши, живущего на 19-ом? А от Паши на 6 этаж к соседке Лене?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1457._

**Generator templates:**

1. `K03-T1` — В лифте работают кнопки +{a} и -{b}. Можно ли попасть с этажа {s} на {t} в доме 1…{N}?
   - Parameters: a,b,N>0.
   - Validation: Проверяются НОД и существование пути внутри границ.
1. `K03-T2` — Найдите минимальное число нажатий для перехода между этажами при шагах +a и -b.
   - Parameters: Пара этажей достижима.
   - Validation: Минимальность подтверждена BFS или строгим рассуждением.

### K04 — Parity invariants on boards and tables / Инварианты чётности на досках и в таблицах

**Difficulty profile:** D3–D5

**Scope:** Prove impossibility or construct a configuration using parity of row sums, column products, or neighbor counts.

**Corpus examples:**

- **D5 · corpus item 1630** — Можно ли составить таблицу 5 х 5 из натуральных чисел так, чтобы сумма чисел в каждой строке была четной, а произведение в каждом столбце было нечетным?  
  _Source: `Сб В классе/2 занятие.docx`; source line 1805._
- **D4 · corpus item 1353** — На клетчатом листе закрасили 25 клеток. Может ли каждая из них иметь нечетное число закрашенных соседей?  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1513._
- **D4 · template-derived illustration** — Можно ли закрасить клетки доски 6×6 так, чтобы у каждой закрашенной клетки было нечётное число закрашенных соседей по стороне?

**Generator templates:**

1. `K04-T1` — Можно ли заполнить таблицу {m}×{n}, чтобы суммы строк имели одну чётность, а произведения столбцов — другую?
   - Parameters: Небольшая доска.
   - Validation: Дано противоречие по чётности или явная конструкция.
1. `K04-T2` — Можно ли закрасить {k} клеток так, чтобы каждая имела нечётное число закрашенных соседей?
   - Parameters: Определение соседства указано.
   - Validation: Используется лемма о сумме степеней графа.

### K05 — Neighbor-difference invariants on a line / Разности соседних величин и инварианты

**Difficulty profile:** D3–D5

**Scope:** Decide whether a prescribed total is possible when adjacent values differ by a fixed amount.

**Corpus examples:**

- **D5 · corpus item 126** — Вдоль забора растет 9 кустов смородины. Ha каждых двух соседних кустах количество ягод отличается а) на 1; b) на 3. Может ли общее число ягод на всех кустах быть равным 250? Должно быть 2 ответа. Также запишите примеры или пояснения что нельзя  
  _Source: `15-минутки/Март 2026/11.03.2026.pdf`; source line 187._
- **D5 · corpus item 135** — Вдоль забора растет 7 кустов крыжовника. Ha каждых двух соседних кустах количество ягод отличается а) на 2; b) на 4. Может ли общее число ягод на всех кустах быть равным 141? Должно быть 2 ответа. Также запишите примеры или пояснения что нельзя  
  _Source: `15-минутки/Март 2026/13.03.2026.pdf`; source line 202._
- **D5 · corpus item 1309** — Вдоль забора растет 9 кустов смородины. На каждых двух соседних кустах количество ягод отличается а) на 1; b) на 3. Может ли общее число ягод на всех кустах быть равным 250? Должно быть 2 ответа. Также запишите примеры или пояснения что нельзя  
  _Source: `Копия 15-минутки (1 часть).docx`; source line 1469._

**Generator templates:**

1. `K05-T1` — На {n} соседних кустах количества ягод у соседей отличаются на {d}. Может ли общая сумма быть {S}?
   - Parameters: n,d,S заданы.
   - Validation: Проверяется чётность или сравнение по модулю; при возможности дан пример.
1. `K05-T2` — Последовательность из {n} натуральных чисел имеет |a_i-a_{i+1}|={d}. Какие остатки может иметь сумма?
   - Parameters: Небольшие n,d.
   - Validation: Учтена положительность членов.

### K06 — Hidden composition from guaranteed draws / Состав набора по гарантированным выборкам

**Difficulty profile:** D3–D5

**Scope:** Infer exact or bounded counts of object types from guarantees about arbitrary samples.

**Corpus examples:**

- **D4 · corpus item 164** — У Пети в кармане несколько монет. Если Петя наугад вытащит из кармана 3 монеты, среди них обязательно найдётся монета в 1 рубль. Если Петя наугад вытащит 4 монеты из кармана, среди них обязательно найдётся монета в 2 рубля. Петя вытащил из кармана 5 монет. Назовите эти монеты  
  _Source: `15-минутки/Март 2026/20.03.2026.pdf`; source line 249._
- **D5 · corpus item 225** — В пенале лежат ручки, карандаши и фломастеры (причјм в пенале есть хотя бы один предмет каждого вида). Если вынуть 11 ручек, то среди любых 13 оставшихся предметов будет не менее одного карандаша, если же вынуть 12 карандашей, то среди любых 12 оставшихся предметов будет не менее одной ручки. Предположим, что из пенала убрали все ручки. Сколько надо вынуть теперь предметов, чтобы среди них гарантированно был флома…  
  _Source: `2025-all.pdf`; source line 337._
- **D5 · corpus item 248** — В пенале лежат ручки, карандаши и фломастеры (причјм в пенале есть хотя бы один предмет каждого вида). Если вынуть 13 ручек, то среди любых 16 оставшихся предметов будет не менее одного карандаша, если же вынуть 15 карандашей, то среди любых 15 оставшихся предметов будет не менее одной ручки. Предположим, что из пенала убрали все ручки. Сколько надо вынуть теперь предметов, чтобы среди них гарантированно был флома…  
  _Source: `2025-all.pdf`; source line 360._

**Generator templates:**

1. `K06-T1` — Если вынуть любые {k} предметов, среди них обязательно есть A; если любые {m}, обязательно есть B. Определите возможные количества типов.
   - Parameters: 2–3 типа.
   - Validation: Гарантии переведены в ограничения на числа не-A и не-B.
1. `K06-T2` — Из кармана вынули {n} монет; гарантии для выборок размеров k,m определяют их номиналы. Назовите состав.
   - Parameters: Состав единственен.
   - Validation: Проверены все подмножества нужных размеров.

### K07 — Deduction from ordered clues and calendar or label constraints / Логическое восстановление по упорядоченным подсказкам

**Difficulty profile:** D2–D5

**Scope:** Recover labels, dates, positions, or assignments from a chain of inequalities and order clues.

**Corpus examples:**

- **D3 · corpus item 1613** — Саша гостил у бабушки. В субботу он сел в поезд и приехал домой в понедельник. Саша заметил, что в этот понедельник число совпало с номером вагона, в котором он ехал, что номер его места в вагоне был меньше номера вагона и что в ту субботу, когда он садился в поезд, число было больше номера вагона. Какими были номера вагона и места?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1785._
- **D3 · template-derived illustration** — Аня, Боря и Вера заняли три разных места. Аня не первая, Боря выше Веры, а Вера не третья. Кто какое место занял?
- **D4 · template-derived illustration** — Три коробки имеют номера 1, 2 и 3 и разные массы. Коробка 1 не самая тяжёлая, коробка 2 тяжелее коробки 3. Восстановите порядок масс.

**Generator templates:**

1. `K07-T1` — Даны несколько объектов и числовые подсказки об их порядке. Восстановите соответствие.
   - Parameters: 3–5 объектов.
   - Validation: Ровно одно распределение удовлетворяет всем условиям.
1. `K07-T2` — Дата, номер вагона и место связаны неравенствами и днями недели. Найдите возможные значения.
   - Parameters: Небольшой календарный диапазон.
   - Validation: Перебор оставляет единственный ответ.

### K08 — State transformations, reachability, and finite algorithms / Преобразования состояний и алгоритмическая достижимость

**Difficulty profile:** D3–D5

**Scope:** Analyze repeated operations on a state, minimum moves, or whether a target configuration is reachable.

**Corpus examples:**

- **D5 · corpus item 1608** — На доске было написано число. Раз в минуту, если оно чётное, то его делят пополам, а если нечетное, то умножают на 3 и прибавляют 1. Например, если на доске написано число 11, то будут выписаны последовательно: через минуту - 34, через две - 17, затем 52, 26, 13, 40, и через 7 минут - 20. Через сколько минут впервые будет выписано число меньшее 10, если в начале выписано число 70?  
  _Source: `Сб В классе/12 занятие.docx`; source line 1780._
- **D3 · template-derived illustration** — Из числа 1 разрешено за ход прибавить 3 или умножить на 2. Можно ли получить 41? Найдите минимальное число ходов.
- **D4 · template-derived illustration** — Фишка стоит в клетке (0,0). За ход она переходит на (x+2,y+1) или (x−1,y+2). Достижима ли клетка (7,8)?

**Generator templates:**

1. `K08-T1` — Состояние изменяется одной из операций {ops}. Можно ли из {start} получить {target}? Найдите минимум шагов.
   - Parameters: Пространство состояний конечно или есть инвариант.
   - Validation: Дана цепочка и доказана минимальность либо невозможность.
1. `K08-T2` — После последовательности направлений или операций известны их количества. Сколько минимум действий нужно до границы или цели?
   - Parameters: Состояние — точка сетки или целое число.
   - Validation: Отдельно решены возможность и гарантированная оценка.

## Coverage and implementation rules

1. Do not create `easy`, `medium`, or `hard` branches inside a theme. Store difficulty on each problem record.
2. Classify by the mathematical method needed for the intended solution, not by story vocabulary. A flight problem can primarily be `I06`, `J05`, or `B01` depending on the actual reasoning.
3. When two themes apply, choose the theme that contains the decisive idea as `primary_theme`; put the other in `secondary_tags`.
4. Every generated task must run a validator: integrality, positivity, range limits, uniqueness, and answer verification.
5. Keep examples linked to original item numbers; do not use OCR-corrupted snippets as canonical templates without normalization.
6. Difficulty calibration should be reviewed against a solved version, because text length alone is not a reliable difficulty measure.

## Recommended record schema

```json
{
  "problem_id": "source-or-generated-id",
  "primary_theme": "C11",
  "secondary_tags": [
    "construction",
    "digits"
  ],
  "difficulty": "D3",
  "source_ref": {
    "item": 61,
    "file": "15-минутки/КР/1 вариант...pdf"
  },
  "template_id": "C11-T1",
  "parameters": {},
  "statement_ru": "...",
  "answer": "...",
  "validator": "function-or-rule-id"
}
```
