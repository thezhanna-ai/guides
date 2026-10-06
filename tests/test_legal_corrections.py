"""Проверки поручения 05.10.2026 без запуска браузера и запросов наружу."""
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import urlparse

from test_site import ImageDocument, ROOT


PROMISE = "За 3-4 дня в лагере ты пройдёшь путь от первого запуска Claude Code / Codex до своего первого продукта. Результат зависит от того, сколько сделаешь сам"
CONTENT = "Разберёшь, как делать контент, который приводит людей на сайт"
FOOTNOTE = "*Meta признана экстремистской организацией и запрещена в РФ"


class LegalCorrectionsTest(unittest.TestCase):
    def test_practicum_uses_requested_copy_and_no_old_promises_remain(self):
        for slug in ("shest-skillov", "svoy-sayt-ne-bliznec"):
            html = (ROOT / "claude-ai" / slug / "index.html").read_text()
            with self.subTest(slug=slug):
                self.assertIn(PROMISE, html)
                self.assertIn(CONTENT, html)
        for path in [ROOT / "index.html", *ROOT.glob("claude-ai/*/index.html"), *ROOT.glob("scripts/*.html")]:
            with self.subTest(path=path.relative_to(ROOT)):
                html = path.read_text()
                self.assertNotRegex(html, r"За 3-4 дня(?: в лагере)? ты пройдёшь путь[^<]*до готового продукта")
                self.assertNotIn("Научишься делать контент, который сам приводит людей на сайт", html)

    def test_first_social_reference_is_marked_and_footnote_is_at_article_end(self):
        for slug, name in (("10-saytov-starogo-interneta", "Facebook"), ("postery-iz-odnogo-foto", "Instagram")):
            doc = ImageDocument((ROOT / "claude-ai" / slug / "index.html").read_text())
            article = doc.root.all(tag="article")[0]
            text = article.text_content()
            with self.subTest(slug=slug):
                self.assertRegex(text[text.index(name):], rf"^{name}\s*\(Meta\*\)")
                self.assertEqual(text.count(FOOTNOTE), 1)
                self.assertIn(FOOTNOTE, article.children[-1].text_content())
        for path in ROOT.glob("claude-ai/*/index.html"):
            self.assertNotRegex(path.read_text(), r"WhatsApp\s*(?:\*|\(Meta\*)", str(path))

    def test_every_page_and_template_loads_existing_local_font_stylesheet(self):
        pages = [ROOT / "index.html", *ROOT.glob("claude-ai/*/index.html"), *ROOT.glob("scripts/*.html")]
        self.assertEqual(len(pages), 38)
        for path in pages:
            links = ImageDocument(path.read_text()).root.all(tag="link")
            fonts = [n.attrs["href"] for n in links if n.attrs.get("href", "").endswith("/fonts/fonts.css")]
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(len(fonts), 1)
                base = ROOT if path.parent.name == "scripts" else path.parent
                self.assertEqual((base / fonts[0]).resolve(), ROOT / "assets/fonts/fonts.css")
                self.assertTrue((base / fonts[0]).is_file())

    def test_no_google_fonts_resources_in_site_html_css_js_or_generator(self):
        paths = [ROOT / "index.html"]
        for folder in ("claude-ai", "assets", "scripts"):
            paths.extend(p for p in (ROOT / folder).rglob("*") if p.suffix in {".html", ".css", ".js", ".py"})
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(), r"fonts\.(?:googleapis|gstatic)\.com")

    def test_local_font_faces_preserve_all_requested_styles_and_valid_woff2(self):
        folder = ROOT / "assets/fonts"
        css = (folder / "fonts.css").read_text()
        faces = re.findall(r"@font-face\s*\{([^}]+)\}", css)
        found = set()
        paths = set()
        for face in faces:
            family = re.search(r"font-family:\s*'([^']+)'", face).group(1)
            weight = int(re.search(r"font-weight:\s*(\d+)", face).group(1))
            found.add((family, weight))
            self.assertRegex(face, r"font-style:\s*normal")
            self.assertRegex(face, r"font-display:\s*swap")
            self.assertIn("format('woff2')", face)
            url = re.search(r"url\('([^']+)'\)", face).group(1)
            self.assertFalse(urlparse(url).scheme)
            path = (folder / url).resolve()
            self.assertTrue(path.is_relative_to(folder))
            data = path.read_bytes()
            self.assertEqual(data[:4], b"wOF2")
            self.assertEqual(struct.unpack(">I", data[8:12])[0], len(data))
            paths.add(path.name)
        self.assertEqual(found, {("Spectral", 300), ("Spectral", 400), ("Spectral", 600),
                                 ("Unbounded", 700), ("JetBrains Mono", 500), ("JetBrains Mono", 700)})
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(paths, {f["file"] for f in manifest["files"]})
        for font in manifest["files"]:
            self.assertEqual(hashlib.sha256((folder / font["file"]).read_bytes()).hexdigest(), font["sha256"])


if __name__ == "__main__":
    unittest.main()
