"""Проверки сайта преподавательского ревью.

Как и в тестах хранилища, все записи уходят во временный каталог: настоящие
оценки и сравнения трогать нельзя. Здесь же проверяется главное свойство
экранов — что задачи на них берутся из живых активных шаблонов, а не из
какой-то отдельной копии, которая начала бы отставать от библиотеки.
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from problemgen.review import store  # noqa: E402
from problemgen.template_studio.catalogue import active_templates  # noqa: E402
from problemgen.web.review_site import (  # noqa: E402
    Handler,
    ReviewSiteError,
    module_review,
    modules_overview,
    next_pair,
    render_page,
    report,
)


class TemporaryReviewMixin(unittest.TestCase):
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


class ModuleReviewTests(TemporaryReviewMixin):
    def test_every_active_module_is_offered(self) -> None:
        """Пропущенная тема означала бы, что её никто не отсмотрит."""
        expected = {str(item.get("module_id")) for item in active_templates()}
        self.assertEqual({item["module_id"] for item in modules_overview()}, expected)

    def test_theme_shows_all_its_templates_at_once(self) -> None:
        """Смысл экрана — видеть тему целиком, а не по одной задаче."""
        overview = modules_overview()[0]
        payload = module_review(overview["module_id"], seed=3)
        self.assertEqual(len(payload["templates"]), overview["template_count"])

    def test_each_template_comes_with_worked_examples(self) -> None:
        for module in modules_overview()[:4]:
            payload = module_review(module["module_id"], seed=7)
            for item in payload["templates"]:
                self.assertTrue(item["examples"], item["template_id"])
                for example in item["examples"]:
                    self.assertFalse(example["failed"], f"{item['template_id']}: {example['problem']}")
                    self.assertNotIn("{", example["problem"], item["template_id"])
                    self.assertTrue(str(example["answer"]).strip(), item["template_id"])

    def test_saved_verdict_comes_back_with_the_theme(self) -> None:
        """Иначе после перезагрузки страницы работа выглядела бы потерянной."""
        module = modules_overview()[0]
        payload = module_review(module["module_id"], seed=1)
        template_id = payload["templates"][0]["template_id"]
        store.save_verdict(template_id, difficulty="hard", comment="сузить числа")
        store.save_verdict(template_id, comment="и добавить сюжет")

        again = module_review(module["module_id"], seed=1)
        saved = next(t for t in again["templates"] if t["template_id"] == template_id)
        self.assertEqual(saved["difficulty"], "hard")
        self.assertEqual([c["text"] for c in saved["comments"]],
                         ["сузить числа", "и добавить сюжет"])

    def test_unknown_theme_is_a_clean_error(self) -> None:
        with self.assertRaises(ReviewSiteError):
            module_review("нет такой темы")


class PairTests(TemporaryReviewMixin):
    def _multi_template_module(self) -> str:
        return next(m["module_id"] for m in modules_overview() if m["template_count"] >= 2)

    def test_pair_is_two_different_templates_of_one_theme(self) -> None:
        module_id = self._multi_template_module()
        payload = next_pair(module_id, seed=5)
        self.assertNotEqual(payload["left"]["template_id"], payload["right"]["template_id"])
        ids = {str(t.get("template_id")) for t in active_templates()
               if str(t.get("module_id")) == module_id}
        self.assertIn(payload["left"]["template_id"], ids)
        self.assertIn(payload["right"]["template_id"], ids)

    def test_both_sides_show_a_real_problem(self) -> None:
        module_id = self._multi_template_module()
        for seed in range(10):
            payload = next_pair(module_id, seed=seed)
            for side in ("left", "right"):
                self.assertFalse(payload[side]["failed"], payload[side]["problem"])
                self.assertNotIn("{", payload[side]["problem"])

    def test_comparisons_build_an_order_within_the_theme(self) -> None:
        """Ровно ради этого экран и существует: порядок по сложности."""
        module_id = self._multi_template_module()
        payload = next_pair(module_id, seed=2)
        harder, easier = payload["left"]["template_id"], payload["right"]["template_id"]
        for _ in range(3):
            store.add_comparison(module_id, harder, easier)

        rows = next(m for m in report()["modules"] if m["module_id"] == module_id)["templates"]
        order = [row["template_id"] for row in rows if row["rating"] is not None]
        self.assertLess(order.index(harder), order.index(easier), "сложная задача обязана быть выше")

    def test_theme_with_a_single_template_says_so(self) -> None:
        single = next((m["module_id"] for m in modules_overview() if m["template_count"] == 1), None)
        if single is None:
            self.skipTest("сейчас в каждой теме больше одного шаблона")
        with self.assertRaises(ReviewSiteError):
            next_pair(single)


class ReportTests(TemporaryReviewMixin):
    def test_report_covers_the_whole_library(self) -> None:
        payload = report()
        self.assertEqual(payload["total"], len(active_templates()))
        listed = sum(len(m["templates"]) for m in payload["modules"])
        self.assertEqual(listed, payload["total"])

    def test_untouched_templates_are_not_pretending_to_be_easy(self) -> None:
        """Отсутствие сравнений — это «не смотрели», а не «оказалось лёгким»."""
        for module in report()["modules"]:
            for row in module["templates"]:
                self.assertIsNone(row["rating"])
                self.assertEqual(row["comparisons"], 0)

    def test_page_renders_with_all_three_screens(self) -> None:
        page = render_page()
        for marker in ("Тема целиком", "Сравнения", "Итоги"):
            self.assertIn(marker, page)


class HttpTests(TemporaryReviewMixin):
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

    def get(self, path: str) -> dict:
        with urllib.request.urlopen(self.url(path)) as response:
            return json.loads(response.read().decode("utf-8"))

    def post(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            self.url(path), data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_index_and_modules(self) -> None:
        with urllib.request.urlopen(self.url("/")) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("Ревью шаблонов", response.read().decode("utf-8"))
        self.assertTrue(self.get("/api/modules")["modules"])

    def test_verdict_round_trip_over_http(self) -> None:
        module_id = self.get("/api/modules")["modules"][0]["module_id"]
        payload = self.get(f"/api/module?module_id={module_id}&seed=4")
        template_id = payload["templates"][0]["template_id"]

        self.post("/api/verdict", {"template_id": template_id,
                                   "difficulty": "medium", "comment": "числа великоваты"})
        again = self.get(f"/api/module?module_id={module_id}&seed=4")
        saved = next(t for t in again["templates"] if t["template_id"] == template_id)
        self.assertEqual(saved["difficulty"], "medium")
        self.assertEqual([c["text"] for c in saved["comments"]], ["числа великоваты"])

        self.post("/api/comment/drop", {"template_id": template_id, "index": 0})
        cleared = self.get(f"/api/module?module_id={module_id}&seed=4")
        saved = next(t for t in cleared["templates"] if t["template_id"] == template_id)
        self.assertEqual(saved["comments"], [])
        self.assertEqual(saved["difficulty"], "medium", "уровень удалять не просили")

    def test_comparison_over_http_changes_the_report(self) -> None:
        module_id = next(m["module_id"] for m in self.get("/api/modules")["modules"]
                         if m["template_count"] >= 2)
        pair = self.get(f"/api/pair?module_id={module_id}&seed=6")
        self.post("/api/comparison", {
            "module_id": module_id,
            "harder": pair["left"]["template_id"],
            "easier": pair["right"]["template_id"],
            "comment": "вторая проще только из-за круглых чисел",
        })
        self.assertEqual(store.load_comparisons()[-1]["comment"],
                         "вторая проще только из-за круглых чисел")
        rows = next(m for m in self.get("/api/report")["modules"]
                    if m["module_id"] == module_id)["templates"]
        rated = {row["template_id"]: row["rating"] for row in rows if row["rating"] is not None}
        self.assertGreater(rated[pair["left"]["template_id"]], rated[pair["right"]["template_id"]])

    def test_drafts_of_all_templates_survive_each_other(self) -> None:
        """Главная защита: замечание к одному шаблону не стирает остальные.

        В первой версии кнопка «Добавить» перерисовывала тему и уносила текст,
        набранный в других полях. Здесь проверяется, что теперь текст всех
        шаблонов темы доживает и до фиксации, и до журнала.
        """
        module_id = self.get("/api/modules")["modules"][0]["module_id"]
        templates = self.get(f"/api/module?module_id={module_id}&seed=8")["templates"]
        expected = {t["template_id"]: f"замечание к {t['template_id']}" for t in templates}
        for template_id, text in expected.items():
            self.post("/api/draft", {"template_id": template_id, "text": text})

        again = self.get(f"/api/module?module_id={module_id}&seed=8")["templates"]
        self.assertEqual({t["template_id"]: t["draft"] for t in again}, expected)

        committed = self.post("/api/commit", {})["committed"]
        self.assertEqual(sorted(committed), sorted(expected))
        final = self.get(f"/api/module?module_id={module_id}&seed=8")["templates"]
        for item in final:
            self.assertEqual([c["text"] for c in item["comments"]], [expected[item["template_id"]]])
            self.assertEqual(item["draft"], "", "черновик после фиксации очищается")

    def test_rating_a_template_does_not_touch_drafts(self) -> None:
        module_id = self.get("/api/modules")["modules"][0]["module_id"]
        templates = self.get(f"/api/module?module_id={module_id}&seed=9")["templates"]
        first, second = templates[0]["template_id"], templates[1]["template_id"]
        self.post("/api/draft", {"template_id": first, "text": "не потерять это"})
        self.post("/api/verdict", {"template_id": second, "difficulty": "hard"})

        again = self.get(f"/api/module?module_id={module_id}&seed=9")["templates"]
        kept = next(t for t in again if t["template_id"] == first)
        self.assertEqual(kept["draft"], "не потерять это")

    def test_bad_requests_are_reported_as_json(self) -> None:
        for path, payload in (("/api/verdict", {"template_id": "x", "difficulty": "невозможно"}),
                              ("/api/comparison", {"module_id": "m", "harder": "a", "easier": "a"})):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.post(path, payload)
            self.assertIn("error", json.loads(caught.exception.read().decode("utf-8")))
        with self.assertRaises(urllib.error.HTTPError):
            self.get("/api/module?module_id=" + urllib.parse.quote("нет такой темы"))


if __name__ == "__main__":
    unittest.main()
