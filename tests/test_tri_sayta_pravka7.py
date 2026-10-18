"""Регрессия замечаний Жанны к правке 7 статьи «Три сайта»."""

from hashlib import sha256
from html import unescape
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "claude-ai" / "tri-sayta-video-pdf-foto"
PAGE = ARTICLE / "index.html"
CTA_SHA256 = "4417f2b5a164ec481550b1caa304f1142ca6c91eeb7318edd94cd8b1c97204ac"


def visible_text(html):
    html = re.sub(r"<(?:script|style)\b.*?</(?:script|style)>", " ", html, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


class TriSaytaPravka7Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.visible = visible_text(cls.html)

    def test_vectis_copy_tells_only_what_export_proved(self):
        self.assertIn("Пример, до:", self.visible)
        self.assertIn("Пример, после:", self.visible)
        self.assertIn("pdftotext", self.visible)
        self.assertNotIn("при экспорте сервис стирает эти данные из файла", self.visible)
        self.assertNotIn("Обычная чёрная плашка исходный текст не удаляет", self.visible)
        self.assertNotIn("Открыть PDF с удалённым фрагментом", self.visible)
        self.assertNotIn("Открыть объединённый PDF", self.visible)

    def test_unused_vectis_pdf_downloads_are_removed(self):
        self.assertFalse((ARTICLE / "assets" / "vectis-edited-12-pages.pdf").exists())
        self.assertFalse((ARTICLE / "assets" / "vectis-merged-26-pages.pdf").exists())

    def test_vectis_crops_use_the_full_text_width(self):
        for name in ("vectis-before-crop.webp", "vectis-after-crop.webp"):
            with self.subTest(name=name):
                self.assertIn(
                    f'<img src="assets/{name}" width="1152" height="240"',
                    self.html,
                )

    def test_timestamp_heading_intro_and_result_copy(self):
        self.assertIn("TimeStamp Camera: как удалить метаданные из фотографии", self.visible)
        self.assertIn(
            "В каждую фотографию с телефона записываются метаданные (EXIF): дата и время "
            "съёмки, модель телефона, а часто и GPS-координаты места. На снимке их не видно, "
            "но они остаются в файле и уходят вместе с ним. Раздел Photo Tools на сайте "
            "TimeStamp Camera показывает эти данные и удаляет их из файла. Выложить очищенную "
            "копию ты можешь сам, куда хочешь.",
            self.visible,
        )
        self.assertIn("Каждая запись метаданных, например дата или модель телефона, называется тегом", self.visible)
        self.assertIn("в примере 13", self.visible)
        self.assertIn(
            "1 file processed, 13 metadata tags stripped: удалено 13 записей метаданных, "
            "в таблице ниже их остаётся 0",
            self.visible,
        )

    def test_memory_list_is_verbatim(self):
        rows = (
            "Картинки из видео: Video2Frames → Serial → интервал → Start Serial Extraction → Export ZIP",
            "Раскадровка видео одним файлом: Video2Frames → Export PDF",
            "PDF - удалить фрагмент: VectisPDF → Viewer & Text → Redact → обвести фрагмент → Export PDF",
            "PDF - объединение документов: VectisPDF → Merge / Split → Add PDF → Export PDF",
            "Метаданные фотографии: TimeStamp Camera → EXIF viewer → Date & Time, Camera, GPS",
            "Очистка метаданных фотографии: Strip metadata instead → Choose photos → Download cleaned file",
        )
        for row in rows:
            with self.subTest(row=row):
                self.assertIn(row, self.visible)

    def test_old_phrases_are_gone_from_visible_text(self):
        for phrase in (
            "счётчик",
            "данных внутри уже нет",
            "перед публикацией",
            "Открыть объединённый",
            "Открыть PDF с удалённым",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.visible)

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
