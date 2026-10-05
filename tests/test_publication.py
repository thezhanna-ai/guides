"""Проверка всех страниц публикационной ветки без запуска браузера."""
import base64
import json
import re
import subprocess
import unittest
from urllib.parse import unquote, urlsplit

from test_site import ImageDocument, ROOT


class PublicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/statyi.json").read_text())["statyi"]
        cls.covers = json.loads((ROOT / "data/OBLOZHKI.json").read_text())
        # 29 оформленных статей, главная и три черновика проверяются отдельно
        cls.pages = [ROOT / "index.html"] + [
            ROOT / "claude-ai" / article["slug"] / "index.html"
            for article in cls.registry
        ]
        cls.docs = {page: ImageDocument(page.read_text()) for page in cls.pages}

    def local_target(self, page, url):
        parsed = urlsplit(url)
        if parsed.netloc and parsed.netloc != "pronovoe.com":
            return None
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            return None
        path = unquote(parsed.path)
        target = (ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path) if path else page
        target = target.resolve()
        self.assertTrue(target.is_relative_to(ROOT.resolve()), url)
        return target / "index.html" if target.is_dir() else target

    def test_scope_includes_all_29_covers_home_and_draft(self):
        ready = {a["slug"] for a in self.registry if a["status"] in {"live", "gotova"}}
        self.assertEqual(len(ready), 30)
        self.assertEqual(set(self.covers), ready)
        self.assertEqual(len(self.pages), 33)
        self.assertEqual(len(set(self.pages)), len(self.pages))

    def test_all_internal_links_and_cross_page_fragments_exist(self):
        for page, doc in self.docs.items():
            for link in doc.root.all(tag="a"):
                with self.subTest(page=str(page.relative_to(ROOT)), href=link.attrs.get("href")):
                    href = link.attrs.get("href", "")
                    self.assertTrue(href.strip(), "Пустая ссылка")
                    target = self.local_target(page, href)
                    if target is None:
                        continue
                    self.assertTrue(target.is_file(), href)
                    fragment = unquote(urlsplit(href).fragment)
                    if fragment:
                        destination = self.docs.get(target) or ImageDocument(target.read_text())
                        self.assertIn(fragment, {n.attrs.get("id") for n in destination.root.all()}, href)

    def test_every_image_has_a_file_or_valid_embedded_data_and_scene_alt(self):
        for page, doc in self.docs.items():
            for image in doc.root.all(tag="img"):
                src = image.attrs.get("src", "")
                with self.subTest(page=str(page.relative_to(ROOT)), src=src[:100]):
                    if not src:
                        # Пустой img существует только в viewer, который копирует src и alt
                        parent = image.parent
                        while parent and "viewer" not in parent.attrs.get("class", "").split():
                            parent = parent.parent
                        self.assertIsNotNone(parent, "Изображение без src вне увеличителя")
                        continue
                    alt = image.attrs.get("alt", "").strip()
                    self.assertTrue(alt)
                    self.assertNotRegex(alt.lower(), r"^(image|screenshot|картинка|скриншот|обложка)\s*\d*$")
                    if src.startswith("data:"):
                        header, payload = src.split(",", 1)
                        self.assertIn(";base64", header)
                        self.assertTrue(base64.b64decode(payload, validate=True))
                    else:
                        target = self.local_target(page, src)
                        self.assertIsNotNone(target, "Внешняя картинка требует отдельной проверки")
                        self.assertTrue(target.is_file(), src)
                        self.assertGreater(target.stat().st_size, 0)

    def test_video_files_posters_and_local_resources_exist(self):
        for page, doc in self.docs.items():
            for node in doc.root.all():
                keys = {"video": ("src", "poster"), "source": ("src",), "script": ("src",), "link": ("href",)}.get(node.tag, ())
                for key in keys:
                    if node.attrs.get(key):
                        target = self.local_target(page, node.attrs[key])
                        if target is not None:
                            with self.subTest(page=str(page.relative_to(ROOT)), resource=node.attrs[key]):
                                self.assertTrue(target.is_file())
                                self.assertGreater(target.stat().st_size, 0)

    def test_copy_and_zoom_buttons_have_existing_content_targets(self):
        for page, doc in self.docs.items():
            nodes = doc.root.all()
            ids = {n.attrs.get("id"): n for n in nodes if n.attrs.get("id")}
            for button in doc.root.all(tag="button"):
                classes = set(button.attrs.get("class", "").split())
                with self.subTest(page=str(page.relative_to(ROOT)), button=button.attrs):
                    target = button.attrs.get("data-copy-target") or button.attrs.get("data-copy")
                    if target:
                        self.assertIn(target, ids)
                        self.assertTrue(ids[target].text_content().strip())
                    elif classes & {"copy", "copy-button"}:
                        candidates = button.parent.all(tag="pre") + button.parent.all(tag="code") + button.parent.all(klass="txt")
                        self.assertTrue(any(n.text_content().strip() for n in candidates))
                    elif "zoom" in classes:
                        self.assertEqual(len(button.parent.all(tag="img")), 1)
                    else:
                        self.assertTrue(classes & {"theme-toggle", "viewer-close", "tag-btn"}, "Неизвестный тип кнопки")

    def test_partner_ctas_are_nonempty_and_point_to_the_practice(self):
        for page, doc in self.docs.items():
            if page == ROOT / "index.html":
                continue
            links = [n for n in doc.root.all(tag="a") if "data-partner" in n.attrs or
                     "theivansergeev.com/ailager/" in n.attrs.get("href", "")]
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertTrue(links)
                for link in links:
                    self.assertTrue(link.attrs.get("href", "").strip())
                    self.assertTrue(link.text_content().strip())
                    url = urlsplit(link.attrs["href"])
                    self.assertEqual((url.scheme, url.netloc, url.path), ("https", "theivansergeev.com", "/ailager/"))

    def test_all_inline_javascript_parses_in_node(self):
        scripts = []
        for page in self.pages:
            for attrs, body in re.findall(r"<script\b([^>]*)>(.*?)</script>", page.read_text(), re.S | re.I):
                if "application/ld+json" in attrs:
                    json.loads(body)
                elif "src=" not in attrs:
                    scripts.append({"filename": str(page.relative_to(ROOT)), "body": body})
        result = subprocess.run([
            "node", "-e",
            "const vm=require('node:vm'),fs=require('node:fs');"
            "for(const s of JSON.parse(fs.readFileSync(0,'utf8')))new vm.Script(s.body,{filename:s.filename});"
        ], input=json.dumps(scripts), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
