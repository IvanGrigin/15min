"""Проверки хранилища преподавательского ревью.

Каждый тест работает во временном каталоге: настоящие оценки и сравнения —
накопленный труд, и тестам к ним прикасаться нельзя ни на чтение, ни на запись.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.review import store  # noqa: E402


class ReviewStoreTestCase(unittest.TestCase):
    """Общий каркас: подменяет пути хранилища на временные."""

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        root = pathlib.Path(self._directory.name)
        self._saved = (store.REVIEW_DIR, store.VERDICTS_PATH, store.COMPARISONS_PATH)
        store.REVIEW_DIR = root
        store.VERDICTS_PATH = root / "verdicts.json"
        store.COMPARISONS_PATH = root / "comparisons.json"

    def tearDown(self) -> None:
        store.REVIEW_DIR, store.VERDICTS_PATH, store.COMPARISONS_PATH = self._saved
        self._directory.cleanup()


class VerdictTests(ReviewStoreTestCase):
    def test_empty_store_reads_as_empty(self) -> None:
        """Первый запуск не должен падать на отсутствующем файле."""
        self.assertEqual(store.load_verdicts(), {})
        self.assertEqual(store.load_comparisons(), [])

    def test_comments_accumulate_instead_of_overwriting(self) -> None:
        """Каждое замечание — отдельная правка, и терять прежние нельзя."""
        store.save_verdict("a", difficulty="hard", comment="переписать условие")
        store.save_verdict("a", difficulty="medium", comment="сузить числа")
        entry = store.load_verdicts()["a"]
        self.assertEqual([c["text"] for c in entry["comments"]],
                         ["переписать условие", "сузить числа"])
        self.assertEqual(entry["difficulty"], "medium", "уровень — текущее мнение, он один")

    def test_level_can_be_set_without_writing_a_comment(self) -> None:
        store.save_verdict("a", difficulty="easy")
        self.assertEqual(store.load_verdicts()["a"]["comments"], [])
        self.assertEqual(store.load_verdicts()["a"]["difficulty"], "easy")

    def test_comment_remembers_the_level_it_was_written_at(self) -> None:
        """«Сложно, потому что числа великоваты» — цельная мысль."""
        store.save_verdict("a", difficulty="hard", comment="числа великоваты")
        self.assertEqual(store.load_verdicts()["a"]["comments"][0]["difficulty"], "hard")

    def test_draft_is_kept_without_entering_the_log(self) -> None:
        """Набранное сохраняется сразу, но полусловом в журнал не попадает."""
        store.save_draft("a", "числа сли")
        store.save_draft("a", "числа слишком большие")
        entry = store.load_verdicts()["a"]
        self.assertEqual(entry["draft"], "числа слишком большие")
        self.assertEqual(entry["comments"], [], "черновик не должен множить записи")

    def test_commit_moves_every_draft_into_the_log(self) -> None:
        """Одно нажатие в конце разбора фиксирует всё набранное по теме."""
        store.save_draft("a", "сузить числа")
        store.save_draft("b", "переписать вопрос")
        store.save_verdict("c", difficulty="easy")
        committed = store.commit_drafts()
        self.assertEqual(sorted(committed), ["a", "b"])
        self.assertEqual(store.load_verdicts()["a"]["comments"][0]["text"], "сузить числа")
        self.assertEqual(store.load_verdicts()["a"]["draft"], "")
        self.assertEqual(store.load_verdicts()["c"]["comments"], [])

    def test_committing_twice_does_not_duplicate(self) -> None:
        store.save_draft("a", "замечание")
        store.commit_drafts()
        self.assertEqual(store.commit_drafts(), [])
        self.assertEqual(len(store.load_verdicts()["a"]["comments"]), 1)

    def test_commit_can_be_limited_to_one_theme(self) -> None:
        store.save_draft("a", "первое")
        store.save_draft("b", "второе")
        self.assertEqual(store.commit_drafts(["a"]), ["a"])
        self.assertEqual(store.load_verdicts()["b"]["draft"], "второе")

    def test_draft_survives_a_level_change(self) -> None:
        """Оценка уровня не должна сбивать недописанное замечание."""
        store.save_draft("a", "недописанное")
        store.save_verdict("a", difficulty="hard")
        self.assertEqual(store.load_verdicts()["a"]["draft"], "недописанное")

    def test_committed_draft_remembers_the_level(self) -> None:
        store.save_verdict("a", difficulty="hard")
        store.save_draft("a", "громоздкие числа")
        store.commit_drafts()
        self.assertEqual(store.load_verdicts()["a"]["comments"][0]["difficulty"], "hard")

    def test_a_single_comment_can_be_dropped(self) -> None:
        store.save_verdict("a", comment="первое")
        store.save_verdict("a", comment="второе")
        store.drop_comment("a", 0)
        self.assertEqual([c["text"] for c in store.load_verdicts()["a"]["comments"]], ["второе"])
        with self.assertRaises(store.ReviewError):
            store.drop_comment("a", 9)

    def test_old_single_comment_files_still_open(self) -> None:
        """Ранняя версия писала одно замечание строкой — не потерять его."""
        store.VERDICTS_PATH.write_text(
            json.dumps({"a": {"difficulty": "easy", "comment": "старое замечание"}}),
            encoding="utf-8")
        entry = store.load_verdicts()["a"]
        self.assertEqual([c["text"] for c in entry["comments"]], ["старое замечание"])

    def test_unknown_level_is_rejected(self) -> None:
        with self.assertRaises(store.ReviewError):
            store.save_verdict("a", difficulty="невозможно")
        with self.assertRaises(store.ReviewError):
            store.save_verdict("", difficulty="easy")

    def test_verdicts_survive_a_reread(self) -> None:
        """Оценка должна лежать в файле, а не в памяти процесса."""
        store.save_verdict("b", difficulty="easy", comment="ок")
        payload = json.loads(store.VERDICTS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["b"]["difficulty"], "easy")
        self.assertEqual(payload["b"]["comments"][0]["text"], "ок")


class ConcurrencyTests(ReviewStoreTestCase):
    """Сервер ревью многопоточный, и это не теория.

    Две вкладки, сохранившие оценку одновременно, реально оставили на диске
    склейку двух JSON: потоки писали в один временный файл вперехлёст.
    Здесь проверяется и целостность файла, и что ни одна правка не пропала.
    """

    def test_parallel_writes_keep_every_record(self) -> None:
        import threading

        def write(index: int) -> None:
            store.save_verdict(f"t{index}", difficulty="easy", comment=f"замечание {index}")

        threads = [threading.Thread(target=write, args=(i,)) for i in range(24)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        raw = store.VERDICTS_PATH.read_text(encoding="utf-8")
        payload = json.loads(raw)  # склейка двух JSON здесь и падала
        self.assertEqual(len(payload), 24, "часть оценок затёрлась")
        for index in range(24):
            self.assertEqual(payload[f"t{index}"]["comments"][0]["text"], f"замечание {index}")

    def test_parallel_comparisons_all_land_in_the_log(self) -> None:
        import threading

        threads = [
            threading.Thread(target=store.add_comparison, args=("m", f"a{i}", f"b{i}"))
            for i in range(24)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(json.loads(store.COMPARISONS_PATH.read_text(encoding="utf-8"))), 24)


class ComparisonTests(ReviewStoreTestCase):
    def test_comparison_keeps_its_comment(self) -> None:
        """Замечание к паре объясняет выбор и без пары бессмысленно."""
        store.add_comparison("m", "a", "b", comment="сложнее только из-за громоздких чисел")
        self.assertEqual(store.load_comparisons()[0]["comment"],
                         "сложнее только из-за громоздких чисел")

    def test_comparisons_only_accumulate(self) -> None:
        """Журнал сравнений — история, а не текущее состояние."""
        store.add_comparison("m", "a", "b")
        store.add_comparison("m", "b", "a")
        self.assertEqual(len(store.load_comparisons()), 2)

    def test_harder_template_gains_rating(self) -> None:
        store.add_comparison("m", "a", "b")
        scores = store.ratings("m")
        self.assertGreater(scores["a"], scores["b"])

    def test_consistent_verdicts_order_the_whole_theme(self) -> None:
        """Три согласованных сравнения дают порядок a > b > c."""
        for _ in range(3):
            store.add_comparison("m", "a", "b")
            store.add_comparison("m", "b", "c")
            store.add_comparison("m", "a", "c")
        scores = store.ratings("m")
        self.assertGreater(scores["a"], scores["b"])
        self.assertGreater(scores["b"], scores["c"])

    def test_tie_moves_both_towards_each_other(self) -> None:
        store.add_comparison("m", "a", "b")
        after_win = store.ratings("m")
        store.add_comparison("m", "a", "b", tie=True)
        after_tie = store.ratings("m")
        self.assertLess(after_tie["a"], after_win["a"])
        self.assertGreater(after_tie["b"], after_win["b"])

    def test_ratings_are_scoped_to_one_theme(self) -> None:
        """Сложность сопоставима внутри темы, а не между темами."""
        store.add_comparison("first", "a", "b")
        store.add_comparison("second", "c", "d")
        self.assertEqual(set(store.ratings("first")), {"a", "b"})

    def test_self_comparison_is_rejected(self) -> None:
        with self.assertRaises(store.ReviewError):
            store.add_comparison("m", "a", "a")
        with self.assertRaises(store.ReviewError):
            store.add_comparison("", "a", "b")


class PairChoiceTests(ReviewStoreTestCase):
    IDS = ["a", "b", "c", "d"]

    def test_unseen_pairs_come_first(self) -> None:
        """Пока есть неспрошенные пары, повторять уже спрошенную незачем."""
        store.add_comparison("m", "a", "b")
        for seed in range(20):
            pair = store.choose_pair("m", self.IDS, random.Random(seed))
            self.assertNotEqual(frozenset(pair), frozenset({"a", "b"}), f"seed {seed}")

    def test_rarely_compared_templates_are_preferred(self) -> None:
        """Сравнения расходятся по теме, а не уточняют одну верхушку."""
        for _ in range(4):
            store.add_comparison("m", "a", "b")
        counts = store.comparison_counts("m")
        self.assertEqual(counts["a"], 4)
        pair = store.choose_pair("m", self.IDS, random.Random(1))
        self.assertTrue({"c", "d"} & set(pair), f"выбрана пара {pair}")

    def test_sides_are_not_always_in_the_same_order(self) -> None:
        """Иначе «сложнее» систематически оказывалось бы с одной стороны."""
        seen = {store.choose_pair("m", ["a", "b"], random.Random(seed)) for seed in range(20)}
        self.assertEqual(seen, {("a", "b"), ("b", "a")})

    def test_single_template_theme_has_no_pair(self) -> None:
        self.assertIsNone(store.choose_pair("m", ["a"], random.Random(0)))


if __name__ == "__main__":
    unittest.main()
