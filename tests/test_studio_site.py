"""Проверки сайта, работающего только на декларативных шаблонах."""
from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.web.studio_site import (  # noqa: E402
    Handler,
    WorksheetError,
    available_modules,
    generate_worksheet,
    render_page,
)


class WorksheetGenerationTests(unittest.TestCase):
    def test_modules_come_from_active_templates_only(self) -> None:
        modules = available_modules()
        self.assertTrue(modules, "нет ни одного активного шаблона")
        for module in modules:
            self.assertTrue(module["module_id"])
            self.assertTrue(module["title"])
            self.assertGreaterEqual(module["template_count"], 1)

    def test_worksheet_is_deterministic_for_a_seed(self) -> None:
        first = generate_worksheet(task_count=5, seed=42)
        second = generate_worksheet(task_count=5, seed=42)
        self.assertEqual(
            [task["problem"] for task in first["tasks"]],
            [task["problem"] for task in second["tasks"]],
        )

    def test_every_task_is_rendered_and_answered(self) -> None:
        for seed in range(15):
            worksheet = generate_worksheet(task_count=5, seed=seed)
            self.assertEqual(len(worksheet["tasks"]), 5)
            for task in worksheet["tasks"]:
                text = task["problem"]
                self.assertNotIn("{", text, f"seed {seed}: неразрешённый слот")
                self.assertNotIn("  ", text, f"seed {seed}: двойной пробел")
                self.assertTrue(text[0].isupper(), f"seed {seed}: {text[:40]}")
                self.assertIn(text.rstrip()[-1], ".?!", f"seed {seed}: {text[-40:]}")
                self.assertTrue(str(task["answer"]).strip(), f"seed {seed}: пустой ответ")
                self.assertNotIn("Ответ", text, f"seed {seed}: ответ попал в условие")

    def test_module_filter_is_respected(self) -> None:
        module_id = available_modules()[0]["module_id"]
        worksheet = generate_worksheet(task_count=4, module_ids=[module_id], seed=3)
        for task in worksheet["tasks"]:
            self.assertEqual(task["module_id"], module_id)

    def test_unknown_module_and_bad_count_are_rejected(self) -> None:
        with self.assertRaises(WorksheetError):
            generate_worksheet(task_count=5, module_ids=["нет такой темы"])
        with self.assertRaises(WorksheetError):
            generate_worksheet(task_count=0)
        with self.assertRaises(WorksheetError):
            generate_worksheet(task_count=99)

    def test_templates_do_not_repeat_while_unused_remain(self) -> None:
        total = sum(module["template_count"] for module in available_modules())
        worksheet = generate_worksheet(task_count=min(total, 5), seed=11)
        identifiers = [task["template_id"] for task in worksheet["tasks"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_page_renders_with_module_checkboxes(self) -> None:
        page = render_page()
        self.assertIn("<title>", page)
        for module in available_modules():
            self.assertIn(module["title"], page)


class HttpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_index_and_modules_endpoint(self) -> None:
        with urllib.request.urlopen(self.url("/")) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Пятиминутки", response.read().decode("utf-8"))
        with urllib.request.urlopen(self.url("/api/modules")) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["modules"])

    def test_worksheet_endpoint_returns_tasks(self) -> None:
        request = urllib.request.Request(
            self.url("/api/worksheet"),
            data=json.dumps({"task_count": 3, "seed": 5}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(len(payload["tasks"]), 3)
        self.assertEqual(payload["source"], "template_studio_library")

    def test_bad_request_is_reported_as_json(self) -> None:
        request = urllib.request.Request(
            self.url("/api/worksheet"),
            data=json.dumps({"task_count": 999}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        payload = json.loads(caught.exception.read().decode("utf-8"))
        self.assertIn("Количество задач", payload["error"])


if __name__ == "__main__":
    unittest.main()
