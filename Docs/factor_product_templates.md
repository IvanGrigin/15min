# Множители, произведения и факториалы

Модуль `factors_products_and_factorials` объединяет 31 уникальный источник из:

- `09_mnozhiteli_proizvedeniya_i_faktorialy_bez_imen_i_personazhey_deduplicated.md`;
- `09_mnozhiteli_proizvedeniya_i_faktorialy_s_imenami_i_personazhami_deduplicated.md`.

Во втором файле после удаления дублей задач не осталось. Из первоначальных 44
записей удалено 13 дублей; они не восстанавливаются как отдельные источники.

## Файлы и учёт

- runtime-каталог: `data/templates/problem_sets/factors_products_and_factorials/templates.json`;
- полный manifest: `data/templates/problem_sets/factors_products_and_factorials/source_accounting.json`;
- генератор: `problemgen/generation/factor_product_templates.py`.

Manifest учитывает каждый из 31 номера ровно один раз. 22 номера связаны с
семью active exact-integer семействами; 9 конструктивных, списочных, логических
или неоднозначных форматов исключены с индивидуальной причиной и не участвуют
в случайном выборе.

## Активные семейства

1. минимальная сумма произвольной пары натуральных множителей;
2. минимум при условии, что хотя бы один множитель нечётный;
3. минимум для двух чётных множителей;
4. минимум для двух нечётных множителей;
5. минимум для множителей без цифры ноль;
6. вычисление одного факториала;
7. число нулей в конце произведения последовательных чисел.

Пары множителей перебираются только до `isqrt(target_product)`. Произведение
генерируется назад от заведомо допустимой пары, после чего минимум независимо
решается по всем делителям. Факториал ограничен диапазоном 5–20 и вычисляется
целочисленно. Конечные нули считаются по суммарным показателям степеней 2 и 5 и
сверяются с прямым произведением.

Именованных runtime-шаблонов нет, поэтому выбор вселенной и склонение имён этому
модулю не требуются. Общий morphology-слой не изменялся.

## Сайт и проверки

Модуль зарегистрирован в общем каталоге и `problemgen/web/worksheet_site.py`.
Он доступен в selector, поддерживает explicit template ID, mixed worksheet и
fixed seed. Условие попадает на ученический лист, а целый ответ — в answer key.

```powershell
python -m unittest tests.test_factor_product_templates
python scripts/validate_factor_product_templates.py
python -m unittest tests.test_worksheet_site
```

Чтобы безопасно добавить семейство, сначала внесите source accounting, затем
active JSON-запись с семантическими параметрами, зарегистрируйте bounded
strategy и добавьте независимую проверку минимум на 20 seed.
