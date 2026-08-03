"""Сравнение задач из разных тем: пара, журнал и общий рейтинг.

Внутри темы вопрос «что сложнее» решает устройство самой задачи, между
темами — ещё и то, какой приём труднее даётся. Это два разных журнала,
но шкала рейтинга одна, и ничья в обоих означает половину очка.
"""
from __future__ import annotations

import random
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.review import store  # noqa: E402
from problemgen.web.review_site import next_pair  # noqa: E402


class ChooseCrossPairTests(unittest.TestCase):
    BY_MODULE = {
        "движение": ["догонялки", "поезда", "муха"],
        "деньги": ["мост", "торговец"],
        "цифры": ["палиндром"],
    }

    def test_pair_always_comes_from_two_different_themes(self) -> None:
        owners = {tid: module for module, ids in self.BY_MODULE.items() for tid in ids}
        for seed in range(30):
            pair = store.choose_cross_pair(self.BY_MODULE, random.Random(seed))
            self.assertIsNotNone(pair, f"seed {seed}")
            first, second = pair
            self.assertNotEqual(owners[first], owners[second],
                                f"seed {seed}: обе задачи из темы {owners[first]}")

    def test_single_theme_gives_nothing(self) -> None:
        """Сравнивать между темами нечего, если тема одна."""
        self.assertIsNone(
            store.choose_cross_pair({"движение": ["догонялки", "поезда"]}, random.Random(0)))

    def test_both_sides_occur_on_the_left(self) -> None:
        """Иначе сторона подсказывала бы ответ."""
        seen_left = {store.choose_cross_pair(self.BY_MODULE, random.Random(seed))[0]
                     for seed in range(40)}
        self.assertGreater(len(seen_left), 1)


class CrossJournalTests(unittest.TestCase):
    """Журнал сравнений между темами отделён от журналов внутри тем."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.original = store.COMPARISONS_PATH
        store.COMPARISONS_PATH = Path(self.directory.name) / "comparisons.json"
        self.addCleanup(setattr, store, "COMPARISONS_PATH", self.original)

    def test_cross_records_do_not_leak_into_a_theme(self) -> None:
        store.add_comparison(store.CROSS_MODULE, "муха", "мост")
        store.add_comparison("движение", "поезда", "догонялки")
        self.assertEqual(store.comparison_counts("движение"), {"поезда": 1, "догонялки": 1})
        self.assertEqual(sorted(store.comparison_counts(store.CROSS_MODULE)), ["мост", "муха"])
        # А общий счёт видит и то и другое: шкала сложности одна на библиотеку.
        self.assertEqual(len(store.comparison_counts()), 4)

    def test_tie_moves_nobody_but_is_remembered(self) -> None:
        store.add_comparison(store.CROSS_MODULE, "муха", "мост", tie=True)
        scores = store.ratings()
        self.assertEqual(scores["муха"], scores["мост"])
        self.assertEqual(len(store.load_comparisons()), 1)
        self.assertTrue(store.load_comparisons()[0]["tie"])

    def test_win_raises_the_harder_and_lowers_the_easier(self) -> None:
        store.add_comparison(store.CROSS_MODULE, "муха", "мост")
        scores = store.ratings()
        self.assertGreater(scores["муха"], store.BASE_RATING)
        self.assertLess(scores["мост"], store.BASE_RATING)

    def test_same_pair_is_not_offered_twice(self) -> None:
        by_module = {"a": ["a1"], "b": ["b1"]}
        store.add_comparison(store.CROSS_MODULE, "a1", "b1")
        self.assertIsNone(store.choose_cross_pair(by_module, random.Random(0)))


class CrossPairScreenTests(unittest.TestCase):
    def test_screen_names_the_theme_of_each_side(self) -> None:
        """Без названия темы сравнение между темами читается как случайное."""
        payload = next_pair(store.CROSS_MODULE, seed=5)
        self.assertEqual(payload["module_id"], store.CROSS_MODULE)
        self.assertEqual(payload["title"], "Между темами")
        for side in ("left", "right"):
            self.assertTrue(payload[side]["module_title"], side)
        self.assertNotEqual(payload["left"]["module_title"], payload["right"]["module_title"])
        self.assertGreater(payload["possible"], 0)


if __name__ == "__main__":
    unittest.main()
