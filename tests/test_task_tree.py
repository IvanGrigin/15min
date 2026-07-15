from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TREE_ROOT = PROJECT_ROOT / "data" / "source_index" / "task_tree"
CORPUS_PATH = PROJECT_ROOT / "Docs" / "all_tasks_all_files.md"


class TaskTreeTests(unittest.TestCase):
    def test_manifest_has_one_hundred_existing_theme_leaves(self) -> None:
        manifest = json.loads((TREE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        themes = manifest["themes"]

        self.assertEqual(len(themes), 100)
        self.assertEqual(len({theme["theme_id"] for theme in themes}), 100)
        self.assertEqual(sum(theme["mapped_source_records"] for theme in themes), 2121)
        self.assertTrue(all((TREE_ROOT / theme["path"]).is_file() for theme in themes))

    def test_tree_record_total_matches_numbered_source_corpus(self) -> None:
        manifest = json.loads((TREE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        corpus = CORPUS_PATH.read_text(encoding="utf-8")
        corpus_records = len(re.findall(r"(?m)^\s*\d+[.)]\s+", corpus))

        self.assertEqual(manifest["source_record_count"], corpus_records)

    def test_leaf_files_stay_small_and_identifiable(self) -> None:
        manifest = json.loads((TREE_ROOT / "manifest.json").read_text(encoding="utf-8"))
        for theme in manifest["themes"]:
            text = (TREE_ROOT / theme["path"]).read_text(encoding="utf-8")
            self.assertTrue(text.startswith(f"# {theme['theme_id']} "))
            self.assertLessEqual(len(text.splitlines()), 160, msg=theme["path"])


if __name__ == "__main__":
    unittest.main()
