from __future__ import annotations

import unittest

from problemgen.worksheet import map_numeric_difficulty_to_level, validate_difficulties


class WorksheetServiceTests(unittest.TestCase):
    def test_validate_difficulties_accepts_five_numbers(self) -> None:
        values = validate_difficulties([1, 3, 5, 7, 10])
        self.assertEqual(values, [1, 3, 5, 7, 10])

    def test_validate_difficulties_rejects_non_list(self) -> None:
        with self.assertRaises(ValueError):
            validate_difficulties("1,2,3,4,5")

    def test_validate_difficulties_rejects_wrong_count(self) -> None:
        with self.assertRaises(ValueError):
            validate_difficulties([1, 2, 3])

    def test_validate_difficulties_rejects_out_of_range(self) -> None:
        with self.assertRaises(ValueError):
            validate_difficulties([1, 2, 3, 4, 11])

    def test_numeric_difficulty_maps_to_existing_levels(self) -> None:
        self.assertEqual(map_numeric_difficulty_to_level(1), "easy")
        self.assertEqual(map_numeric_difficulty_to_level(5), "medium")
        self.assertEqual(map_numeric_difficulty_to_level(10), "hard")


if __name__ == "__main__":
    unittest.main()
