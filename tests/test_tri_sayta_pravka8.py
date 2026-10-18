"""Регрессия живой проверки Redact для правки 8 статьи «Три сайта»."""

from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "claude-ai" / "tri-sayta-video-pdf-foto" / "index.html"
CTA_SHA256 = "4417f2b5a164ec481550b1caa304f1142ca6c91eeb7318edd94cd8b1c97204ac"
FAQ_ANSWER = (
    "Нет. Плашка закрывает фрагмент глазам, но текст под ней остаётся в файле, "
    "его можно найти поиском. Для настоящего удаления нужен другой режим или программа"
)


def visible_text(html):
    html = re.sub(r"<(?:script|style)\b.*?</(?:script|style)>", " ", html, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


class TriSaytaPravka8Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.visible = visible_text(cls.html)
        schema_match = re.search(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
            cls.html,
            re.S,
        )
        if schema_match is None:
            raise AssertionError("JSON-LD block not found")
        cls.schema = json.loads(schema_match.group(1))

    def test_programmer_term_is_absent_everywhere(self):
        self.assertEqual(self.html.lower().count("pdftotext"), 0)

    def test_visible_vectis_copy_states_the_verified_limit(self):
        for phrase in (
            "текст под ней по-прежнему можно найти поиском и скопировать",
            "Для настоящего удаления этот режим не подходит",
            "Текст под ней остался в файле и находится поиском",
            "Текст под плашкой остался в файле, его можно найти поиском и скопировать",
            FAQ_ANSWER,
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.visible)

    def test_faq_json_ld_matches_visible_answer(self):
        faq_pages = [item for item in self.schema["@graph"] if item.get("@type") == "FAQPage"]
        self.assertEqual(len(faq_pages), 1)
        answers = {
            item["name"]: item["acceptedAnswer"]["text"]
            for item in faq_pages[0]["mainEntity"]
        }
        self.assertEqual(answers["Удаляет ли VectisPDF скрытый текст?"], FAQ_ANSWER)

    def test_redact_result_labels_do_not_claim_deletion(self):
        vectis = self.html.split('<section id="vectispdf">', 1)[1].split("</section>", 1)[0]
        heading = re.search(r"<h2>(.*?)</h2>", vectis, re.S).group(1)
        after_caption = re.search(
            r'<img src="assets/vectis-after-crop\.webp".*?<figcaption>(.*?)</figcaption>',
            vectis,
            re.S,
        ).group(1)
        result = re.search(r'<div class="result"><p><b>Что получилось:</b>(.*?)</p>', vectis, re.S).group(1)
        for label, text in (("heading", heading), ("caption", after_caption), ("result", result)):
            with self.subTest(label=label):
                self.assertNotIn("удалить", text.lower())

    def test_registered_ad_block_is_byte_identical(self):
        block = re.search(
            r'(<section class="cta" aria-label="Концентрат и мастер-группа Ивана Сергеева">.*?</section>)',
            self.html,
            re.S,
        )
        self.assertIsNotNone(block)
        self.assertEqual(sha256(block.group(1).encode()).hexdigest(), CTA_SHA256)


if __name__ == "__main__":
    unittest.main()
