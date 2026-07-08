from __future__ import annotations

import unittest

from problemgen.core.story_worlds import (
    STORY_WORLDS,
    get_story_world,
    sample_story_context,
)


class StoryWorldsTests(unittest.TestCase):
    def test_all_worlds_have_required_fields(self) -> None:
        for world in STORY_WORLDS.values():
            self.assertTrue(world.key)
            self.assertTrue(world.title)
            self.assertTrue(world.location)
            self.assertTrue(world.characters)
            self.assertGreaterEqual(len(world.characters), 4)

    def test_get_story_world_by_key(self) -> None:
        world = get_story_world("smeshariki")
        self.assertEqual(world.title, "Смешарики")

    def test_unknown_key_raises_clear_error(self) -> None:
        with self.assertRaises(ValueError) as error:
            get_story_world("unknown_world")
        self.assertIn("Неизвестный сюжетный мир", str(error.exception))

    def test_sample_story_context_is_valid(self) -> None:
        context = sample_story_context(world_key="prostokvashino", min_characters=2, max_characters=3)
        self.assertEqual(context.world_key, "prostokvashino")
        self.assertTrue(context.location)
        self.assertGreaterEqual(len(context.characters), 2)
        self.assertLessEqual(len(context.characters), 3)
        self.assertIn(context.lead_character, context.characters)


if __name__ == "__main__":
    unittest.main()
