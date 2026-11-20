"""Верхний рекламный блок во всех статьях и в штатной сборке."""
import importlib.util
import json
import re
import subprocess
import unittest

from test_site import ImageDocument, ROOT


COPY = "За три вечера разберись, как создавать продукт, контент, сайты и воронки с ИИ-агентами без кода. Записи за 990 ₽."
BUTTON = "Забрать Концентрат"
LINK = "https://theivansergeev.com/koncentrat/?gcpc=16fff"
DISCLOSURE = "Реклама. ИП Сергеев И. С., ИНН 352511695540. erid: 2VtzqvBca1C"
LOWER_ERID = "2Vtzqwfc8iA"


class NightAdTopTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "data/statyi.json").read_text())["statyi"]
        cls.pages = [ROOT / "claude-ai" / item["slug"] / "index.html" for item in cls.registry]
        cls.pages.append(ROOT / "claude-ai/runway-iz-claude/podklyuchenie.html")

    def test_every_registered_article_has_one_exact_top_creative_after_article_header(self):
        for page in self.pages:
            with self.subTest(page=page.relative_to(ROOT)):
                html = page.read_text()
                doc = ImageDocument(html)
                blocks = [node for node in doc.root.all()
                          if "data-night-ad-top" in node.attrs]
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                self.assertEqual(block.tag, "aside")
                self.assertEqual(block.attrs["aria-label"], "Реклама Концентрата")
                self.assertEqual([p.text_content() for p in block.all(tag="p")],
                                 [COPY, DISCLOSURE])
                self.assertEqual([(a.attrs.get("href"), a.text_content()) for a in block.all(tag="a")],
                                 [(LINK, BUTTON)])
                self.assertLess(html.index("</h1>"), html.index("data-night-ad-top"))
                self.assertEqual(html.count('<!-- pageviews:start -->'), 1)
                self.assertEqual(html.count('/assets/pageviews.js'), 1)
                self.assertEqual(html.count("2VtzqvBca1C"), 1)
                self.assertEqual(html.count(LOWER_ERID), 1)

    def test_home_policy_and_main_template_do_not_receive_the_article_ad(self):
        for page in [ROOT / "index.html", ROOT / "politika/index.html",
                     ROOT / "scripts/shablon_glavnoy.html", ROOT / "scripts/shablon_politiki.html"]:
            with self.subTest(page=page.relative_to(ROOT)):
                self.assertNotIn("data-night-ad-top", page.read_text())

    def test_shared_builder_insertion_is_idempotent_and_keeps_lower_cta_bytes(self):
        spec = importlib.util.spec_from_file_location("night_ad_generator", ROOT / "scripts/sobrat_glavnuyu.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = '<html><head></head><body><article><header><h1>Новая статья</h1><p>Вступление</p></header><p>Текст</p><section class="cta">НИЖНИЙ БЛОК</section></article></body></html>'
        result = module.dobavit_verhnyuyu_reklamu(source)
        self.assertEqual(module.dobavit_verhnyuyu_reklamu(result), result)
        self.assertEqual(result.count("data-night-ad-top"), 1)
        self.assertIn('<link rel="stylesheet" href="../../assets/article-ads.css">', result)
        self.assertIn('<section class="cta">НИЖНИЙ БЛОК</section>', result)

    def test_lower_cta_bytes_match_fresh_head_for_every_article(self):
        pattern = rb'<section\b(?=[^>]*\bclass="cta")[^>]*>.*?</section>'
        for page in self.pages:
            rel = page.relative_to(ROOT).as_posix()
            before = subprocess.run(
                ["git", "show", "HEAD:" + rel], cwd=ROOT, check=True,
                stdout=subprocess.PIPE,
            ).stdout
            with self.subTest(page=rel):
                expected = re.findall(pattern, before, re.S)
                self.assertEqual(len(expected), 1)
                self.assertEqual(re.findall(pattern, page.read_bytes(), re.S), expected)


if __name__ == "__main__":
    unittest.main()
