"""Независимая проверка групп Д, А, Б и З каталога приёмов.

Семь шаблонов: справедливый делёж после общего обмена валюты, курс
витаминов пачками, соревнование из трёх этапов, велосипедист с двумя
ускорениями, всадник с письмом между двумя пешеходами, две фигуры на
доске и таблица, занумерованная змейкой.

Решатели устроены иначе, чем шаблоны. Где шаблон считает формулой —
тест моделирует происходящее по шагам: доли считаются по одному ребёнку,
движение проигрывается посекундно, расстановки на доске перебираются
клетка за клеткой. Где шаблон зовёт перебор — тест берёт формулу или
другой перебор. Совпадение ответов двух разных ходов и есть проверка.
"""
from __future__ import annotations

import itertools
import random
import re
import sys
import unittest
from fractions import Fraction
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.template_studio.runtime import generate_active_template  # noqa: E402
from problemgen.template_studio.snake_table import cell_value  # noqa: E402
from scripts.seed_worksheet_templates import load_library  # noqa: E402

LIBRARY = {template["template_id"]: template for template in load_library()}
SEEDS = range(40)


def plain(generated: dict) -> str:
    """Текст задачи с обычными пробелами.

    Счётные слоты печатают неразрывный пробел между числом и словом —
    в рабочем листе это правильно, а разбирать условие регулярными
    выражениями мешает. Тест читает условие, а не проверяет вёрстку.
    """
    return generated["rendered_problem"].replace("\u00a0", " ")


def numbers(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"\d+", text)]


def assert_text_is_clean(case: unittest.TestCase, text: str, seed: int) -> None:
    case.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
    case.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
    case.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
    case.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}")
    case.assertNotIn("Ответ:", text, f"seed {seed}: ответ попал в условие")


class CurrencyExchangeTests(unittest.TestCase):
    """539: общий обмен и делёж пропорционально вкладу."""

    TEMPLATE = LIBRARY["currency_exchange_shared_commission"]

    @staticmethod
    def read_condition(text: str) -> tuple[int, list[int], int]:
        fee = numbers(text)[0]
        amounts_part = text.split("детей было ")[1].split(" долларов")[0]
        amounts = [int(value) for value in re.findall(r"\d+", amounts_part)]
        rate = int(re.search(r"Один доллар стоит (\d+)", text).group(1))
        return fee, amounts, rate

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            fee, amounts, rate = self.read_condition(text)

            # Делёж моделируется по одному ребёнку: каждому — его доля
            # от общего котла. Шаблон считает долю одной формулой, тест
            # раскладывает котёл на всех и берёт нужного.
            pot = sum(amounts) * rate - fee
            shares = [
                Fraction(pot * amount, sum(amounts)) for amount in amounts
            ]
            self.assertEqual(sum(shares), pot, f"seed {seed}: доли не сходятся в котёл")

            if "сберегли" in text:
                expected = (len(amounts) - 1) * fee
            elif "получил больше" in text:
                asked = int(re.search(r"у кого было (\d+) долларов", text).group(1))
                index = amounts.index(asked)
                expected = shares[index] - (asked * rate - fee)
            else:
                asked = int(re.search(r"у кого было (\d+) долларов", text).group(1))
                index = amounts.index(asked)
                expected = shares[index]

            self.assertEqual(expected.denominator if isinstance(expected, Fraction) else 1, 1,
                             f"seed {seed}: доля не целая — {text}")
            self.assertEqual(generated["answer"], int(expected), f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_pooling_always_beats_going_alone(self) -> None:
        """В этом и смысл складчины: доля больше, чем свой обмен в одиночку."""
        for seed in SEEDS:
            text = plain(generate_active_template(self.TEMPLATE, random.Random(seed)))
            fee, amounts, rate = self.read_condition(text)
            pot = sum(amounts) * rate - fee
            for amount in amounts:
                alone = amount * rate - fee
                self.assertGreater(
                    Fraction(pot * amount, sum(amounts)), alone, f"seed {seed}: {text}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 539: 1250 долларов по 4 юаня, комиссия 50."""
        pot = 1250 * 4 - 50
        self.assertEqual(pot, 4950)
        self.assertEqual(pot * 150 // 1250, 594)


class VitaminPackTests(unittest.TestCase):
    """247: наименьшая стоимость курса, когда таблетки продаются пачками."""

    TEMPLATE = LIBRARY["vitamin_course_pack_cost"]

    @staticmethod
    def read_course(text: str) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
        found = re.search(
            r"от (\d+) до (\d+) таблеток от (\d+) до (\d+) раз в день "
            r"в течение от (\d+) до (\d+) недель", text)
        values = [int(value) for value in found.groups()]
        return (values[0], values[1]), (values[2], values[3]), (values[4], values[5])

    @staticmethod
    def read_packs(text: str) -> tuple[tuple[int, int], tuple[int, int]]:
        found = re.search(
            r"пачка из (\d+) таблеток стоит (\d+) рубл\S+, "
            r"а пачка из (\d+) таблеток — (\d+) рубл\S+", text)
        values = [int(value) for value in found.groups()]
        return (values[0], values[1]), (values[2], values[3])

    @staticmethod
    def brute_force(need: int, packs: tuple[tuple[int, int], ...]) -> int:
        """Прямой перебор числа пачек, без динамики по числу таблеток."""
        (big_size, big_price), (small_size, small_price) = packs
        best = None
        for big in range(need // big_size + 2):
            left = max(0, need - big * big_size)
            small = -(-left // small_size)
            cost = big * big_price + small * small_price
            if best is None or cost < best:
                best = cost
        return best

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            dose, times, weeks = self.read_course(text)
            low = dose[0] * times[0] * weeks[0] * 7
            high = dose[1] * times[1] * weeks[1] * 7

            if "Сколько таблеток съест" in text:
                self.assertEqual(generated["answer"], high, f"seed {seed}: {text}")
                assert_text_is_clean(self, text, seed)
                continue

            packs = self.read_packs(text)
            cheap, dear = self.brute_force(low, packs), self.brute_force(high, packs)
            if "На сколько рублей" in text:
                expected = dear - cheap
            else:
                expected = dear if self.asks_spender(text) else cheap

            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    @staticmethod
    def asks_spender(text: str) -> bool:
        """Кого спрашивают: кто пьёт меньше или кто больше.

        Оба имени стоят в дательном падеже в первой фразе, и вопрос
        повторяет одно из них в том же падеже — сравнение точное.
        """
        saver, spender = re.search(r"прописал (\S+) и (\S+) курс", text).groups()
        asked = re.search(r"придётся потратить ([^?]+)\?", text).group(1).strip()
        if asked not in (saver, spender):
            raise AssertionError(f"непонятно, кого спрашивают: {asked!r}")
        return asked == spender

    def test_greedy_purchase_is_not_always_right(self) -> None:
        """Смысл задачи: «бери выгодные пачки, пока хватает» промахивается."""
        packs = ((120, 239), (50, 113))
        self.assertEqual(self.brute_force(126, packs), 339)
        self.assertEqual(239 + 113, 352)
        self.assertGreater(352, 339)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 247: курс 126 и 420 таблеток."""
        packs = ((120, 239), (50, 113))
        self.assertEqual(2 * 3 * 3 * 7, 126)
        self.assertEqual(3 * 4 * 5 * 7, 420)
        self.assertEqual(self.brute_force(126, packs), 339)
        self.assertEqual(self.brute_force(420, packs), 917)


class TriathlonStagesTests(unittest.TestCase):
    """636: три этапа, каждый со своим удвоением скорости."""

    TEMPLATE = LIBRARY["triathlon_stage_speedups"]

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            total = int(re.search(r"дистанцию за (\d+) минут", text).group(1))

            if "вдвое быстрее сидя, вдвое быстрее бегом" in text:
                self.assertEqual(generated["answer"], total // 2, f"seed {seed}: {text}")
                assert_text_is_clean(self, text, seed)
                continue

            save_sit = int(re.search(r"на (\d+) минут\S* раньше", text).group(1))
            sit = 2 * save_sit
            if "решал задачи сидя" in text or "решала задачи сидя" in text:
                self.assertEqual(generated["answer"], sit, f"seed {seed}: {text}")
                assert_text_is_clean(self, text, seed)
                continue

            save_run = int(re.search(r"составил (\d+) минут", text).group(1))
            run = 2 * save_run
            ride = total - sit - run
            self.assertGreater(ride, 0, f"seed {seed}: велосипед не остался — {text}")

            if "провёл на велосипеде" in text or "провела на велосипеде" in text:
                expected = ride
            else:
                # Проигрываем последний год по этапам, а не вычитанием:
                # сидя и бегом как в первый год, велосипед вдвое короче.
                expected = sit + run + ride // 2
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 636: 180 минут, выигрыши 40 и 25."""
        sit, run = 2 * 40, 2 * 25
        ride = 180 - sit - run
        self.assertEqual((sit, run, ride), (80, 50, 50))
        self.assertEqual(sit + run + ride // 2, 155)


class CyclistOvershootTests(unittest.TestCase):
    """555: два ускорения подряд, длины пути неизвестны."""

    TEMPLATE = LIBRARY["cyclist_overshoot_and_return"]

    @staticmethod
    def simulate(mult: int, out: Fraction, extra: Fraction) -> tuple[Fraction, Fraction]:
        """Проехать маршрут по кускам и сложить время приближения и удаления.

        Шаблон пользуется тем, что ответ равен доле 1/(k+1) от всего пути.
        Тест этой доли не знает: он честно считает три участка при
        произвольных длинах и складывает куски, на которых расстояние
        до дома уменьшается.
        """
        closer = out / mult + extra / (mult * mult)
        farther = out + extra / mult
        return closer, farther

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            mult = int(re.search(r"обратно в (\d+) раза быстрее", text).group(1))
            hours = int(re.search(r"через (\d+) час\S* после", text).group(1))
            total = hours * 60

            # Длины в условии не названы: подбираем любую пару, дающую нужное
            # общее время, и проверяем, что ответ от выбора не зависит.
            answers = set()
            for share in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
                out = Fraction(total) * share
                # Остаток времени приходится на лишний отрезок.
                rest = Fraction(total) - out - out / mult
                extra = rest * mult * mult / (mult + 1)
                closer, farther = self.simulate(mult, out, extra)
                self.assertEqual(closer + farther, total, f"seed {seed}: сумма не сходится")
                answers.add((closer, farther))

            closers = {pair[0] for pair in answers}
            self.assertEqual(len(closers), 1, f"seed {seed}: ответ зависит от длин — {text}")
            closer = closers.pop()
            self.assertEqual(closer.denominator, 1, f"seed {seed}: {text}")

            if "Во сколько раз" in text:
                expected = mult
            elif "удаляясь от дома" in text:
                expected = total - int(closer)
            else:
                expected = int(closer)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 555: тройное ускорение, 5 часов -> 75 минут."""
        # Всего 300 минут: до магазина 200, лишний отрезок при той же
        # скорости занял бы 75 — тогда 200 + 275/3 + 75/9 = 300.
        closer, farther = self.simulate(3, Fraction(200), Fraction(75))
        self.assertEqual(closer + farther, 300)
        self.assertEqual(closer, 75)


class RiderLetterTests(unittest.TestCase):
    """339: всадник возит письмо между двумя пешеходами."""

    TEMPLATE = LIBRARY["rider_letter_between_walkers"]

    @staticmethod
    def chase(start_gap: Fraction, rider: int, walker: int, toward: bool) -> Fraction:
        """Сколько минут всадник закрывает разрыв: встречно или вдогонку."""
        speed = rider + walker if toward else rider - walker
        return Fraction(start_gap * 60, speed)

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            walker = int(re.search(r"со скоростью (\d+) км/ч", text).group(1))
            delay = int(re.search(r"на (\d+) час\S* позже", text).group(1))
            gap = Fraction(walker * delay)

            if "опережал второго" in text:
                self.assertEqual(generated["answer"], gap, f"seed {seed}: {text}")
                assert_text_is_clean(self, text, seed)
                continue

            deliver = int(re.search(r"довёз письмо за (\d+) минут", text).group(1))
            # Скорость всадника: за время доставки встречное сближение
            # закрывает весь разрыв.
            rider = Fraction(gap * 60, deliver) - walker
            self.assertEqual(
                self.chase(gap, rider, walker, toward=True), deliver, f"seed {seed}")

            if "километров в час проезжал" in text:
                self.assertEqual(generated["answer"], rider, f"seed {seed}: {text}")
                assert_text_is_clean(self, text, seed)
                continue

            wait = int(re.search(r"затем (\d+) минут ждал", text).group(1))
            # Пока второй пишет, первый уходит — разрыв растёт.
            grown = gap + Fraction(walker * wait, 60)
            back = self.chase(grown, rider, walker, toward=False)
            self.assertEqual(back.denominator, 1, f"seed {seed}: {text}")

            expected = deliver + wait + int(back) if "прошло с найма" in text else int(back)
            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_gap_does_not_change_while_both_walk(self) -> None:
        """Ключевой факт условия: пока идут оба, разрыв постоянен."""
        walker, delay = 6, 2
        for elapsed in range(0, 300, 15):
            first = walker * (delay + Fraction(elapsed, 60))
            second = walker * Fraction(elapsed, 60)
            self.assertEqual(first - second, walker * delay)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 339: 6 км/ч, задержка 2 ч, 30 и 40 минут."""
        gap = Fraction(12)
        rider = Fraction(gap * 60, 30) - 6
        self.assertEqual(rider, 18)
        grown = gap + Fraction(6 * 40, 60)
        self.assertEqual(grown, 16)
        self.assertEqual(self.chase(grown, rider, 6, toward=False), 80)


class ChessboardPiecesTests(unittest.TestCase):
    """1612: две фигуры на доске, ладьи и короли."""

    TEMPLATE = LIBRARY["two_pieces_on_chessboard"]

    @staticmethod
    def count_pairs(size: int, rule: str) -> int:
        """Перебор всех пар клеток подряд — без единой формулы."""
        cells = [(row, column) for row in range(size) for column in range(size)]
        total = 0
        for first, second in itertools.permutations(cells, 2):
            same_line = first[0] == second[0] or first[1] == second[1]
            touching = max(abs(first[0] - second[0]), abs(first[1] - second[1])) == 1
            if rule == "rooks_free" and not same_line:
                total += 1
            elif rule == "rooks_attack" and same_line:
                total += 1
            elif rule == "kings_free" and not touching:
                total += 1
            elif rule == "kings_touch" and touching:
                total += 1
        return total

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            size = int(re.search(r"размером (\d+) × \d+ клеток", text).group(1))

            if "допустимая правилами позиция" in text:
                expected = self.count_pairs(size, "kings_free")
            elif "оказались на соседних клетках" in text:
                expected = self.count_pairs(size, "kings_touch")
            elif "две одинаковые ладьи" in text:
                expected = self.count_pairs(size, "rooks_free") // 2
            elif "не били друг друга" in text:
                expected = self.count_pairs(size, "rooks_free")
            else:
                expected = self.count_pairs(size, "rooks_attack")

            self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_free_and_attacking_together_cover_everything(self) -> None:
        """Сверка двух вопросов: вместе они обязаны дать все пары клеток."""
        for size in range(5, 10):
            total = size * size * (size * size - 1)
            self.assertEqual(
                self.count_pairs(size, "rooks_free") + self.count_pairs(size, "rooks_attack"),
                total, f"доска {size}")
            self.assertEqual(
                self.count_pairs(size, "kings_free") + self.count_pairs(size, "kings_touch"),
                total, f"доска {size}")

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 1612: обычная доска — 3136 и 3612."""
        self.assertEqual(self.count_pairs(8, "rooks_free"), 3136)
        self.assertEqual(self.count_pairs(8, "kings_free"), 3612)


class SnakeTableTests(unittest.TestCase):
    """679: отметки по одной в строке и столбце в таблице-змейке."""

    TEMPLATE = LIBRARY["snake_table_marked_cells"]

    @staticmethod
    def build_table(size: int) -> list[list[int]]:
        """Выписать таблицу построчно, как её рисуют на доске.

        Решатель шаблона считает номер клетки формулой по чётности строки;
        тест выкладывает числа подряд, разворачивая каждую вторую строку.
        """
        table, value = [], 1
        for row in range(size):
            line = list(range(value, value + size))
            value += size
            table.append(line if row % 2 == 0 else line[::-1])
        return table

    def test_numbering_agrees_with_the_solver(self) -> None:
        for size in (4, 5, 6, 7):
            table = self.build_table(size)
            for row in range(size):
                for column in range(size):
                    self.assertEqual(
                        cell_value(size, row + 1, column + 1),
                        table[row][column], f"{size}: строка {row + 1}, столбец {column + 1}")

    def test_matches_independent_solution(self) -> None:
        for seed in SEEDS:
            generated = generate_active_template(self.TEMPLATE, random.Random(seed))
            text = plain(generated)
            size = int(re.search(r"таблицы (\d+) × \d+", text).group(1))
            shown = [
                int(value) for value in
                re.search(r"с номерами ([\d, ]+?)(?: и ещё две)?\.", text).group(1).split(",")
            ]
            table = self.build_table(size)

            # Перебор всех расстановок целиком: тест не вычёркивает строки
            # и столбцы, а просто проверяет каждую перестановку на то,
            # содержит ли она показанные номера.
            full = []
            for order in itertools.permutations(range(size)):
                picked = [table[row][order[row]] for row in range(size)]
                if set(shown) <= set(picked):
                    full.append(sorted(picked))
            self.assertTrue(full, f"seed {seed}: дополнить нельзя — {text}")

            rests = sorted({sum(group) - sum(shown) for group in full})
            if "Сколькими способами" in text:
                expected = len(full)
                self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            elif "всех отмеченных клеток" in text:
                expected = max(sum(group) for group in full)
                self.assertEqual(generated["answer"], expected, f"seed {seed}: {text}")
            else:
                self.assertEqual(generated["answer"], rests, f"seed {seed}: {text}")
                self.assertIn(" или ", generated["answer_text"], f"seed {seed}: {text}")
            assert_text_is_clean(self, text, seed)

    def test_source_example_reproduces(self) -> None:
        """Контроль по источнику 679: отмечены 1, 13, 19 — сумма 30 или 32."""
        table = self.build_table(5)
        self.assertEqual(table[3], [20, 19, 18, 17, 16])
        rests = set()
        for order in itertools.permutations(range(5)):
            picked = [table[row][order[row]] for row in range(5)]
            if {1, 13, 19} <= set(picked):
                rests.add(sum(picked) - 33)
        self.assertEqual(sorted(rests), [30, 32])


class QuestionVarietyTests(unittest.TestCase):
    """Разнообразие здесь — в вопросе, а не в именах героев.

    Каждый шаблон этого батча спрашивает о нескольких разных вещах на
    одном и том же сюжете, и ветки должны действительно выпадать: ветка,
    которую не выбирает ни один жребий, — это мёртвый текст в библиотеке.
    """

    EXPECTED = {
        "currency_exchange_shared_commission": (
            "получит тот", "сберегли", "получил больше"),
        "vitamin_course_pack_cost": (
            "придётся потратить", "На сколько рублей", "Сколько таблеток съест"),
        "triathlon_stage_speedups": (
            "закончит соревнование", "провёл на велосипеде", "провела на велосипеде",
            "решал задачи сидя", "решала задачи сидя"),
        "cyclist_overshoot_and_return": (
            "приближаясь к дому", "удаляясь от дома", "Во сколько раз"),
        "rider_letter_between_walkers": (
            "на доставку ответа", "километров в час проезжал", "прошло с найма", "опережал второго"),
        "two_pieces_on_chessboard": (
            "не били друг друга", "били друг друга", "две одинаковые ладьи",
            "допустимая правилами позиция", "оказались на соседних клетках"),
        "snake_table_marked_cells": (
            "сумма номеров этих двух клеток", "всех отмеченных клеток", "Сколькими способами"),
    }

    def test_every_question_shows_up(self) -> None:
        for template_id, marks in self.EXPECTED.items():
            template = LIBRARY[template_id]
            seen = set()
            for seed in range(200):
                text = plain(generate_active_template(template, random.Random(seed)))
                seen.update(mark for mark in marks if mark in text)
            self.assertEqual(set(marks), seen, f"{template_id}: не выпало {set(marks) - seen}")


if __name__ == "__main__":
    unittest.main()
