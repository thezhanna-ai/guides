"""Регрессия рабочего двухшагового удаления поискового слоя для правки 9."""

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
    "Да, если сначала закрыть фрагмент через Redact и Export PDF, затем заново открыть "
    "этот PDF и выбрать Tools → Compress PDF → Maximum (JPEG) → Compress & Download. "
    "Обычная плашка Redact текст не стирает"
)


def visible_text(html):
    html = re.sub(r"<(?:script|style)\b.*?</(?:script|style)>", " ", html, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


class TriSaytaPravka9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.visible = visible_text(cls.html)
        vectis_match = re.search(r'<section id="vectispdf"[^>]*>(.*?)</section>', cls.html, re.S)
        if vectis_match is None:
            raise AssertionError("VectisPDF section not found")
        cls.vectis = vectis_match.group(1)
        memory_match = re.search(r'<section id="pamyatka"[^>]*>(.*?)</section>', cls.html, re.S)
        if memory_match is None:
            raise AssertionError("Memory section not found")
        cls.memory = memory_match.group(1)
        schema_match = re.search(
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
            cls.html,
            re.S,
        )
        if schema_match is None:
            raise AssertionError("JSON-LD block not found")
        cls.schema = json.loads(schema_match.group(1))

    def test_two_step_workflow_uses_exact_button_names(self):
        vectis_text = visible_text(self.vectis)
        for phrase in (
            "Select PDF document",
            "Viewer & Text и выбери Redact",
            "Задай имя и нажми Export PDF",
            "Close, затем Select PDF document",
            "Compress PDF выбери Maximum (JPEG)",
            "Compress & Download",
            "закрытое слово больше не находится",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, vectis_text)

    def test_intro_and_result_explain_direct_and_rasterized_exports(self):
        vectis_text = visible_text(self.vectis)
        self.assertIn("поиск по документу всё равно его найдёт", vectis_text)
        self.assertIn("После повторного открытия файла и Compress PDF → Maximum (JPEG)", vectis_text)
        self.assertIn("каждая страница стала изображением", vectis_text)
        self.assertNotIn("проверенном", vectis_text.lower())
        self.assertNotIn("другой режим", vectis_text.lower())
        self.assertNotIn("настоящее удаление", vectis_text.lower())
        self.assertNotIn("pdftotext", self.html.lower())

    def test_faq_and_json_ld_match(self):
        self.assertIn(FAQ_ANSWER, self.visible)
        faq_pages = [item for item in self.schema["@graph"] if item.get("@type") == "FAQPage"]
        self.assertEqual(len(faq_pages), 1)
        answers = {
            item["name"]: item["acceptedAnswer"]["text"]
            for item in faq_pages[0]["mainEntity"]
        }
        self.assertEqual(answers["Удаляет ли VectisPDF скрытый текст?"], FAQ_ANSWER)

    def test_memory_contains_the_complete_two_step_workflow(self):
        memory_text = visible_text(self.memory)
        self.assertIn(
            "PDF - удалить фрагмент: VectisPDF → Viewer & Text → Redact → обвести фрагмент → Export PDF",
            memory_text,
        )
        self.assertIn("Maximum (JPEG)", memory_text)

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
