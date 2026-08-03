"""Раскладка задач по трудности: набор, запись цепочки и её честность.

Раскладка из двенадцати карточек даёт одиннадцать связей — только соседние
пары. Именно их человек и решал, глядя на две карточки рядом; остальные
следуют по транзитивности, и записывать их отдельно значило бы выдать одно
решение за шестьдесят шесть.
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
from problemgen.review.store import ReviewError  # noqa: E402
from problemgen.web.review_site import next_ranking  # noqa: E402


class RankingJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.original = store.COMPARISONS_PATH
        store.COMPARISONS_PATH = Path(self.directory.name) / "comparisons.json"
        self.addCleanup(setattr, store, "COMPARISONS_PATH", self.original)

    def order(self, *names: str) -> list[dict]:
        return [{"template_id": name, "same_as_previous": False} for name in names]

    def test_only_neighbours_are_written(self) -> None:
        written = store.add_ranking(store.CROSS_MODULE, self.order("a", "b", "c", "d"))
        self.assertEqual(len(written), 3, "четыре карточки — три связи")
        pairs = [(record["easier"], record["harder"]) for record in written]
        self.assertEqual(pairs, [("a", "b"), ("b", "c"), ("c", "d")])

    def test_left_is_easier_than_right(self) -> None:
        store.add_ranking(store.CROSS_MODULE, self.order("простая", "средняя", "трудная"))
        scores = store.ratings()
        self.assertLess(scores["простая"], scores["трудная"])

    def test_mark_of_equality_becomes_a_tie(self) -> None:
        order = self.order("a", "b", "c")
        order[1]["same_as_previous"] = True
        written = store.add_ranking(store.CROSS_MODULE, order)
        self.assertTrue(written[0]["tie"], "пометка «≈» обязана давать ничью")
        self.assertFalse(written[1]["tie"], "непомеченная пара — обычное сравнение")

    def test_a_tie_alone_moves_nobody(self) -> None:
        order = self.order("a", "b")
        order[1]["same_as_previous"] = True
        store.add_ranking(store.CROSS_MODULE, order)
        scores = store.ratings()
        self.assertEqual(scores["a"], scores["b"])

    def test_records_remember_where_they_came_from(self) -> None:
        store.add_ranking(store.CROSS_MODULE, self.order("a", "b"))
        store.add_comparison(store.CROSS_MODULE, "c", "d")
        sources = [record.get("source") for record in store.load_comparisons()]
        self.assertEqual(sources, ["ranking", "pair"])

    def test_broken_layouts_are_refused(self) -> None:
        with self.assertRaises(ReviewError):
            store.add_ranking(store.CROSS_MODULE, self.order("a"))
        with self.assertRaises(ReviewError):
            store.add_ranking(store.CROSS_MODULE, self.order("a", "a"))
        first_marked = self.order("a", "b")
        first_marked[0]["same_as_previous"] = True
        with self.assertRaises(ReviewError):
            store.add_ranking(store.CROSS_MODULE, first_marked)


class RankingScreenTests(unittest.TestCase):
    def test_dozen_of_cards_from_different_themes(self) -> None:
        payload = next_ranking(seed=4)
        cards = payload["cards"]
        self.assertEqual(len(cards), 12)
        self.assertEqual(len({card["template_id"] for card in cards}), 12)
        themes = {card["module_title"] for card in cards}
        self.assertGreaterEqual(len(themes), 10, f"тем маловато: {sorted(themes)}")
        for card in cards:
            self.assertTrue(card["problem"].strip(), card["template_id"])
            self.assertNotIn("{", card["problem"], card["template_id"])

    def test_order_on_screen_is_shuffled(self) -> None:
        """Иначе расстановка подсказывала бы ответ."""
        by_seed = [
            [card["template_id"] for card in next_ranking(seed=seed)["cards"]]
            for seed in (1, 2, 3)
        ]
        self.assertNotEqual(by_seed[0], by_seed[1])
        self.assertNotEqual(by_seed[1], by_seed[2])

    def test_size_is_checked(self) -> None:
        from problemgen.web.review_site import ReviewSiteError
        with self.assertRaises(ReviewSiteError):
            next_ranking(count=1)
        with self.assertRaises(ReviewSiteError):
            next_ranking(count=50)


if __name__ == "__main__":
    unittest.main()
