"""Единый креатив и видимая маркировка на всех партнёрских страницах."""
import importlib.util
import re
import unittest

from test_site import ImageDocument, ROOT, PARTNER_LINK


TITLE = "Инструкция пройдена. А как сделать, чтобы нейросети приводили клиентов?"
COPY = ("Концентрат - онлайн-мероприятие Ивана Сергеева по вайбмаркетингу: "
        "13-15 октября, 19:00 по Москве. Участие бесплатное, регистрация на сайте до 14 октября")
DISCLOSURE = "Реклама. ИП Сергеев И. С., ИНН 352511695540. erid:"


class EridTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [ROOT / "index.html", *sorted(ROOT.glob("claude-ai/*/index.html")),
                     ROOT / "scripts/shablon_glavnoy.html"]

    def test_every_partner_page_and_template_has_exactly_one_marked_creative(self):
        self.assertEqual(len(self.pages), 47)
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                doc = ImageDocument(html)
                blocks = doc.root.all(klass="cta")
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                self.assertEqual(block.all(tag="h2")[0].text_content(), TITLE)
                self.assertEqual([p.text_content().strip() for p in block.all(tag="p")],
                                 [COPY, DISCLOSURE])
                links = [a for a in doc.root.all(tag="a") if "data-partner" in a.attrs
                         or "theivansergeev.com" in a.attrs.get("href", "")]
                self.assertEqual(len(links), 1)
                self.assertIn(links[0], block.all(tag="a"))
                self.assertEqual(links[0].attrs["href"], PARTNER_LINK)
                self.assertIn("data-partner", links[0].attrs)
                self.assertEqual(links[0].text_content(), "Зарегистрироваться")
                for header in doc.root.all(tag="header"):
                    self.assertFalse(any("data-partner" in a.attrs for a in header.all(tag="a")))
                    self.assertNotIn("На Концентрат", header.text_content())
                self.assertEqual([n.tag for n in block.children], ["h2", "p", "a", "p"])
                self.assertEqual(len(block.all(klass="ad-disclosure")), 1)
                tokens = [n for n in block.all(tag="span") if "data-erid" in n.attrs]
                self.assertEqual(len(tokens), 1)
                self.assertNotIn("style", block.all(klass="ad-disclosure")[0].attrs)

    def test_erid_has_one_editable_constant_and_safe_rendering(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                self.assertEqual(len(re.findall(r'var ERID = "[^"\n]+";', html)), 1)
                self.assertEqual(len(re.findall(r'var PARTNER_LINK = "[^"\n]+";', html)), 1)
                self.assertLessEqual(html.count("ERID_PLACEHOLDER"), 1)
                self.assertIn('document.querySelectorAll("[data-erid]")', html)
                self.assertIn("label.textContent = ERID;", html)

    def test_ad_copy_and_disclosure_share_readable_size_and_color(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text().replace("{{", "{").replace("}}", "}")
                css = re.search(r'<!-- erid:style:start -->(.*?)<!-- erid:style:end -->',
                                html, re.S).group(1)
                self.assertIn(".cta h2 {", css)
                self.assertIn("font-size: 20px", css)
                paragraphs = re.search(r'\.cta p \{([^}]+)\}', css).group(1)
                self.assertIn("font-size: 16px", paragraphs)
                self.assertIn("color: #F0E8D8", paragraphs)
                self.assertIn("padding: 22px 22px 18px", css)
                self.assertNotRegex(css, r'\.ad-disclosure[^}]*\b(?:opacity|font-size|color)\s*:')

    def test_old_article_question_is_plain_text_above_the_block(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                doc = ImageDocument(page.read_text())
                block = doc.root.all(klass="cta")[0]
                question = block.parent.children[block.parent.children.index(block) - 1]
                self.assertEqual(question.tag, "p")
                self.assertIn("cta-question", question.attrs.get("class", "").split())
                self.assertTrue(question.text_content())
                self.assertEqual(question.all(tag="a"), [])
                if page in (ROOT / "index.html", ROOT / "scripts/shablon_glavnoy.html"):
                    self.assertEqual(block.parent.attrs.get("id"), "lager",
                                     "Поиск скрывает вопрос и рекламный блок вместе")

    def test_generator_retains_the_creative_and_constants(self):
        spec = importlib.util.spec_from_file_location("erid_generator", ROOT / "scripts/sobrat_glavnuyu.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        self.assertEqual(generator.sobrat_stranicu(), (ROOT / "index.html").read_text())
        self.assertIn(DISCLOSURE, generator.sobrat_stranicu())


if __name__ == "__main__":
    unittest.main()
