"""Единый креатив и видимая маркировка на всех партнёрских страницах."""
import importlib.util
import re
import html as html_module
import unittest

from test_site import ImageDocument, ROOT, PARTNER_LINK


TITLE = "Инструкция пройдена. А как сделать, чтобы нейросети приводили клиентов?"
COPY = ("Концентрат - онлайн-мероприятие Ивана Сергеева по вайбмаркетингу: "
        "13-15 октября, 19:00 по Москве. Участие бесплатное, регистрация на сайте до 14 октября")
DISCLOSURE = "Реклама. ИП Сергеев И. С., ИНН 352511695540. erid: 2VtzqviiWtm"


class EridTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [ROOT / "index.html", *sorted(p for p in ROOT.glob("claude-ai/*/index.html")
                     if p.parent.name != "chatgpt-composio-prilozheniya"),
                     ROOT / "scripts/shablon_glavnoy.html"]

    def test_every_partner_page_and_template_has_exactly_one_marked_creative(self):
        self.assertEqual(len(self.pages), 49)
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                doc = ImageDocument(html)
                blocks = doc.root.all(klass="cta")
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                if page == ROOT / "claude-ai/pyat-instrumentov-dlya-sayta/index.html":
                    self.assertEqual(block.all(tag="h2")[0].text_content(),
                                     "Сайт собран. Как поручить его проверки команде ИИ-агентов?")
                    creative = re.search(r'<section[^>]*class="cta".*?</section>', html, re.S).group()
                    paragraphs = [
                        html_module.unescape(re.sub(r"<[^>]+>", "", text)).strip()
                        for text in re.findall(r"<p\b[^>]*>(.*?)</p>", creative, re.S)
                    ]
                    self.assertEqual(paragraphs, [
                        "Бесплатный Концентрат",
                        "Ты знаешь, чем проверить кнопки и заявки. Дальше можно собрать команду ИИ-агентов для таких проверок. На Концентрате три вечера, 13-15 октября в 19:00 по Москве, онлайн: работа с командой агентов в Claude Code, Codex и ChatGPT.",
                        "Регистрация на сайте до 14 октября, участие бесплатное",
                        DISCLOSURE])
                else:
                    self.assertEqual(block.all(tag="h2")[0].text_content(), TITLE)
                    self.assertEqual([p.text_content().strip() for p in block.all(tag="p")],
                                     [COPY, DISCLOSURE])
                links = [a for a in doc.root.all(tag="a") if "data-partner" in a.attrs
                         or "theivansergeev.com" in a.attrs.get("href", "")]
                self.assertEqual(len(links), 1)
                self.assertIn(links[0], block.all(tag="a"))
                self.assertEqual(links[0].attrs["href"], PARTNER_LINK)
                self.assertIn("data-partner", links[0].attrs)
                self.assertEqual(links[0].text_content(), "Занять место" if page.name == "index.html" and page.parent.name == "pyat-instrumentov-dlya-sayta" else "Зарегистрироваться")
                for header in doc.root.all(tag="header"):
                    self.assertFalse(any("data-partner" in a.attrs for a in header.all(tag="a")))
                    self.assertNotIn("На Концентрат", header.text_content())
                self.assertEqual([n.tag for n in block.children], ["p", "h2", "p", "a", "p", "p"] if page.parent.name == "pyat-instrumentov-dlya-sayta" else ["h2", "p", "a", "p"])
                self.assertEqual(len(block.all(klass="ad-disclosure")), 1)
                disclosure = block.all(klass="ad-disclosure")[0]
                self.assertEqual(disclosure.children, [])
                self.assertEqual(disclosure.text_content(), DISCLOSURE)
                self.assertNotIn("style", block.all(klass="ad-disclosure")[0].attrs)

    def test_erid_is_static_in_html_without_javascript_regression(self):
        for page in self.pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text()
                self.assertNotRegex(html, r'\b(?:var|let|const)\s+ERID\b')
                self.assertEqual(len(re.findall(r'var PARTNER_LINK = "[^"\n]+";', html)), 1)
                self.assertEqual(html.count("2VtzqviiWtm"), 1)
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
