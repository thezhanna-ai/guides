"""Единый креатив и видимая маркировка на всех партнёрских страницах."""
import importlib.util
import re
import unittest

from test_site import ImageDocument, ROOT, PARTNER_LINK


TITLE = "Как собрать продажи своего дела на ИИ?"
COPY = [
    "Товары, услуги, консультации или своё обучение: в любом деле клиенту нужно узнать о тебе, понять пользу и решиться купить. Какую часть этой работы можно отдать нейросетям?",
    "Это разбирают в мастер-группе Ивана Сергеева: предложение для клиентов, продающий сайт, автоворонка и контент собираются в одну систему продаж на ИИ, без продюсера и технаря. Набор открывается редко, а предзапись доступна всегда. Люди из списка узнают о наборе первыми и получают лучшую цену и бонусы. Анкета займёт около двух минут, оплачивать ничего не нужно.",
]
DISCLOSURE = "Реклама. ИП Сергеев И. С., ИНН 352511695540. erid: 2Vtzquqo4SZ"
BUTTON = "Заполнить анкету предзаписи"


class EridTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [ROOT / "index.html", *sorted(ROOT.glob("claude-ai/*/index.html")),
                     ROOT / "scripts/shablon_glavnoy.html"]

    def test_every_partner_page_and_template_has_exactly_one_marked_creative(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                doc = ImageDocument(html)
                blocks = doc.root.all(klass="cta")
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                self.assertEqual(block.all(tag="h2")[0].text_content(), TITLE)
                self.assertEqual([p.text_content().strip() for p in block.all(tag="p")],
                                 [*COPY, DISCLOSURE])
                links = [a for a in doc.root.all(tag="a") if "data-partner" in a.attrs
                         or "theivansergeev.com" in a.attrs.get("href", "")]
                self.assertEqual(len(links), 1)
                self.assertIn(links[0], block.all(tag="a"))
                self.assertEqual(links[0].attrs["href"], PARTNER_LINK)
                self.assertIn("data-partner", links[0].attrs)
                self.assertEqual(links[0].text_content(), BUTTON)
                for header in doc.root.all(tag="header"):
                    self.assertFalse(any("data-partner" in a.attrs for a in header.all(tag="a")))
                    self.assertNotIn("На Концентрат", header.text_content())
                self.assertEqual([n.tag for n in block.children], ["h2", "p", "p", "a", "p"])
                self.assertEqual(len(block.all(klass="ad-disclosure")), 1)
                disclosure = block.all(klass="ad-disclosure")[0]
                self.assertEqual(disclosure.children, [])
                self.assertEqual(disclosure.text_content(), DISCLOSURE)
                self.assertNotIn("style", block.all(klass="ad-disclosure")[0].attrs)

    def test_standard_cta_bytes_regression_20261010(self):
        pattern = rb'<section class="cta"[^>]*>.*?</section>'
        reference = ROOT / "claude-ai/chetyre-mcp-claude-code/index.html"
        standard = re.search(pattern, reference.read_bytes(), re.S).group()
        pages = [ROOT / "index.html", *sorted(ROOT.glob("claude-ai/*/index.html")),
                 ROOT / "scripts/shablon_glavnoy.html"]
        for page in pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                match = re.search(pattern, page.read_bytes(), re.S)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(), standard)

    def test_erid_is_static_in_html_without_javascript_regression(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                self.assertNotRegex(html, r'\b(?:var|let|const)\s+ERID\b')
                self.assertEqual(len(re.findall(r'var PARTNER_LINK = "[^"\n]+";', html)), 1)
                self.assertEqual(html.count("2Vtzquqo4SZ"), 1)
                self.assertNotIn("2VtzqviiWtm", html)
                self.assertIn(f'<p class="ad-disclosure">{DISCLOSURE}</p>', html)
                self.assertNotIn("data-erid", html)
                scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.S | re.I)
                self.assertFalse(any("ERID" in body or "ad-disclosure" in body for body in scripts))

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

    def test_generator_retains_the_creative_and_static_disclosure(self):
        spec = importlib.util.spec_from_file_location("erid_generator", ROOT / "scripts/sobrat_glavnuyu.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        self.assertEqual(generator.sobrat_stranicu(), (ROOT / "index.html").read_text())
        self.assertIn(DISCLOSURE, generator.sobrat_stranicu())


if __name__ == "__main__":
    unittest.main()
