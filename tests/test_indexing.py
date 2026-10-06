"""Реестр управляет noindex и sitemap при обычной сборке, без браузера."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from test_site import ImageDocument, ROOT


BASE = "https://pronovoe.com/"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
RELEASED = {"shest-skillov", "svoy-sayt-ne-bliznec"}


def robots(html):
    return [n.attrs.get("content", "").lower() for n in ImageDocument(html).root.all(tag="meta")
            if n.attrs.get("name", "").lower() in {"robots", "googlebot", "yandex"}]


def locations(xml):
    tree = ET.fromstring(xml)
    assert tree.tag == "{" + NS["s"] + "}urlset"
    return [n.text for n in tree.findall("s:url/s:loc", NS)]


def generator():
    spec = importlib.util.spec_from_file_location("indexing_generator", ROOT / "scripts/sobrat_glavnuyu.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IndexingTest(unittest.TestCase):
    def test_only_nonlive_pages_keep_noindex_after_authorized_corrections(self):
        registry = json.loads((ROOT / "data/statyi.json").read_text())["statyi"]
        held = {a["slug"] for a in registry if a.get("noindex_reason")}
        self.assertEqual(held, set())
        self.assertTrue(all("noindex_reason" not in a for a in registry if a["slug"] in RELEASED))
        self.assertFalse(any("noindex" in r or "nofollow" in r for r in robots((ROOT / "index.html").read_text())))
        for a in registry:
            with self.subTest(slug=a["slug"]):
                directives = robots((ROOT / "claude-ai" / a["slug"] / "index.html").read_text())
                if a["status"] != "live" or a["slug"] in held:
                    self.assertEqual(directives, ["noindex, nofollow"])
                else:
                    self.assertFalse(any("noindex" in r or "nofollow" in r or "none" in r for r in directives))

    def test_sitemap_matches_indexable_live_registry_and_home_exactly(self):
        registry = json.loads((ROOT / "data/statyi.json").read_text())["statyi"]
        urls = locations((ROOT / "sitemap.xml").read_text())
        expected = [BASE] + [BASE + "claude-ai/" + a["slug"] + "/" for a in registry
                             if a["status"] == "live" and not a.get("noindex_reason")]
        self.assertEqual(urls, expected)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(len(urls), 36)
        self.assertNotIn("lastmod", (ROOT / "sitemap.xml").read_text())

    def test_robots_announces_sitemap_without_blocking_noindex_crawling(self):
        text = (ROOT / "robots.txt").read_text()
        self.assertIn("User-agent: *\n", text)
        self.assertIn("Sitemap: " + BASE + "sitemap.xml\n", text)
        self.assertNotRegex(text, r"(?im)^Disallow:\s*/")

    def fixture(self, directory):
        root = Path(directory).resolve()
        for folder in ("scripts", "data"):
            (root / folder).mkdir()
        for name in ("data/statyi.json", "data/OBLOZHKI.json", "scripts/shablon_glavnoy.html", "index.html"):
            shutil.copyfile(ROOT / name, root / name)
        for a in json.loads((root / "data/statyi.json").read_text())["statyi"]:
            target = root / "claude-ai" / a["slug"] / "index.html"
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / "claude-ai" / a["slug"] / "index.html", target)
        return root

    def run_generator(self, root, check=False):
        module = generator()
        with patch.multiple(module, KORNI=root, REESTR=root / "data/statyi.json",
                            OBLOZHKI=root / "data/OBLOZHKI.json", GLAVNAYA=root / "index.html"), \
                patch("sys.argv", ["sobrat_glavnuyu.py"] + (["--proverit"] if check else [])), \
                contextlib.redirect_stdout(io.StringIO()):
            return module.main()

    def test_new_live_status_changes_and_legal_hold_survive_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            path = root / "data/statyi.json"
            data = json.loads(path.read_text())
            for held in data["statyi"]:
                if held["slug"] in RELEASED:
                    held["noindex_reason"] = "Тест: независимый юридический запрет"
            source = data["statyi"][0]
            article = dict(source, slug="novaya-statya", status="live")
            data["statyi"].append(article)
            page = root / "claude-ai/novaya-statya/index.html"
            page.parent.mkdir()
            shutil.copyfile(root / "claude-ai" / source["slug"] / "index.html", page)
            url = BASE + "claude-ai/novaya-statya/"
            for status, reason in (("live", ""), ("gotova", ""), ("draft", ""),
                                   ("live", "Высокий риск: проверка"), ("live", "")):
                with self.subTest(status=status, reason=reason):
                    article.update(status=status, noindex_reason=reason)
                    path.write_text(json.dumps(data, ensure_ascii=False))
                    self.assertEqual(self.run_generator(root), 0)
                    allowed = status == "live" and not reason
                    self.assertEqual(url in locations((root / "sitemap.xml").read_text()), allowed)
                    self.assertEqual(robots(page.read_text()), [] if allowed else ["noindex, nofollow"])
                    for slug in RELEASED:
                        self.assertEqual(robots((root / "claude-ai" / slug / "index.html").read_text()),
                                         ["noindex, nofollow"])
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(self.run_generator(root), 0)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_check_detects_each_stale_artifact_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            self.assertEqual(self.run_generator(root), 0)
            self.assertEqual(self.run_generator(root, check=True), 0)
            paths = [root / "sitemap.xml", root / "robots.txt", root / "index.html",
                     root / "claude-ai/shest-skillov/index.html",
                     root / "claude-ai/podklyuchenie-iz-rossii/index.html"]
            for path in paths:
                with self.subTest(path=path):
                    original = path.read_bytes()
                    path.write_bytes(original + b"\nSTALE\n")
                    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
                    # Sitemap/robots/home are fully generated; article metadata needs a real directive change.
                    if "claude-ai" in path.parts:
                        html = path.read_text().replace("</head>", '<meta name="robots" content="noindex, nofollow"></head>')
                        path.write_text(html)
                        before[path] = path.read_bytes()
                    self.assertEqual(self.run_generator(root, check=True), 1)
                    self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})
                    path.write_bytes(original)

    def test_registry_slug_cannot_escape_site_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            path = root / "data/statyi.json"
            data = json.loads(path.read_text())
            data["statyi"].append(dict(data["statyi"][0], slug="../../outside"))
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                self.run_generator(root)

    def test_existing_index_follow_directive_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.fixture(directory)
            page = root / "claude-ai/podklyuchenie-iz-rossii/index.html"
            html = page.read_text().replace("</head>", '<meta name="robots" content="index,follow">\n</head>')
            page.write_text(html)
            self.assertEqual(self.run_generator(root), 0)
            self.assertEqual(page.read_text(), html)


if __name__ == "__main__":
    unittest.main()
