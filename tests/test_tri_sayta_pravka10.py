"""Регрессии замечаний Жанны для правки 10 статьи «Три сайта»."""

from hashlib import sha256
from html import unescape
from pathlib import Path
import re
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "claude-ai" / "tri-sayta-video-pdf-foto"
PAGE = ARTICLE / "index.html"
COVER = ARTICLE / "assets" / "oblozhka.webp"
CTA_SHA256 = "4417f2b5a164ec481550b1caa304f1142ca6c91eeb7318edd94cd8b1c97204ac"


def visible_text(fragment):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def section(html, section_id):
    match = re.search(
        rf'<section id="{re.escape(section_id)}"[^>]*>(.*?)</section>',
        html,
        re.S,
    )
    if match is None:
        raise AssertionError(f"section #{section_id} not found")
    return match.group(1)


def first_paragraph(fragment):
    match = re.search(r"<h2>.*?</h2>\s*<p>(.*?)</p>", fragment, re.S)
    if match is None:
        raise AssertionError("first paragraph after h2 not found")
    return visible_text(match.group(1))


class TriSaytaPravka10Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.video = section(cls.html, "video2frames")
        cls.vectis = section(cls.html, "vectispdf")
        cls.timestamp = section(cls.html, "timestamp-camera")

    def test_cover_uses_two_title_colors_and_keeps_expected_size(self):
        with Image.open(COVER) as image:
            rgb = image.convert("RGB")
            self.assertEqual(rgb.size, (1600, 840))
            first_line = rgb.crop((65, 220, 430, 315))
            second_line = rgb.crop((65, 315, 620, 420))
            coral_pixels = sum(
                1
                for red, green, blue in first_line.get_flattened_data()
                if red >= 210 and 80 <= green <= 140 and blue <= 100
            )
            white_pixels = sum(
                1
                for red, green, blue in second_line.get_flattened_data()
                if red >= 225 and green >= 220 and blue >= 210
            )
        self.assertGreater(coral_pixels, 3000)
        self.assertGreater(white_pixels, 8000)

    def test_cover_is_used_by_article_and_open_graph(self):
        self.assertIn('<img src="assets/oblozhka.webp" width="1600" height="840"', self.html)
        self.assertIn(
            '<meta property="og:image" content="https://pronovoe.com/claude-ai/tri-sayta-video-pdf-foto/assets/oblozhka.webp"',
            self.html,
        )

    def test_each_tool_section_starts_with_reader_problem(self):
        video_intro = first_paragraph(self.video)
        self.assertTrue(video_intro.startswith("Хочешь разобрать чужой ролик по кадрам"))
        self.assertIn("монтаж вирусного или просто интересного видео", video_intro)
        self.assertIn("Делать десятки скриншотов вручную долго", video_intro)
        self.assertNotIn("для обложки, карусели", video_intro)

        vectis_intro = first_paragraph(self.vectis)
        self.assertTrue(vectis_intro.startswith("Нужно быстро скрыть кусок текста в PDF"))
        self.assertIn("поиск по документу всё равно его найдёт", vectis_intro)
        self.assertIn("сжать страницы в картинки", vectis_intro)
        self.assertIn("Плашка останется и выглядит неаккуратно", vectis_intro)
        self.assertIn("объединять несколько PDF в один", vectis_intro)

        timestamp_intro = first_paragraph(self.timestamp)
        self.assertTrue(timestamp_intro.startswith("Выкладываешь фото в чат или объявление"))
        self.assertIn("место съёмки", timestamp_intro)
        self.assertIn("метаданные (EXIF)", timestamp_intro)
        self.assertIn("GPS-координаты", timestamp_intro)

    def test_vectis_steps_explain_why_in_reader_language(self):
        vectis_text = visible_text(self.vectis)
        for phrase in (
            "чтобы открыть нужный файл в редакторе",
            "чтобы скачать документ с плашкой",
            "Страницы станут картинками, поэтому поиск не найдёт текст; минус: во всём файле нельзя будет выделить и скопировать текст",
            "чтобы убедиться: закрытое слово больше не находится",
            "чтобы получить оба документа одним файлом",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, vectis_text)

    def test_tool_labels_have_article_local_spacing(self):
        for section_id in ("video2frames", "vectispdf", "timestamp-camera"):
            self.assertRegex(
                self.html,
                rf'<section id="{section_id}" class="tool-section">\s*<p class="eyebrow">',
            )
        self.assertIn(".tool-section>.eyebrow{margin-top:48px}", self.html)
        self.assertIn(".tool-section>.eyebrow{margin-top:36px}", self.html)

    def test_required_relative_downloads_exist(self):
        downloads = {
            "Открыть готовый PDF": "assets/video-frames-15.pdf",
            "Открыть исходный JPEG": "assets/timestamp-tagged.jpg",
            "Открыть очищенный JPEG": "assets/timestamp-cleaned.jpg",
        }
        for label, relative_path in downloads.items():
            with self.subTest(label=label):
                self.assertRegex(
                    self.html,
                    rf'href="{re.escape(relative_path)}"[^>]*>{re.escape(label)}</a>',
                )
                file_path = ARTICLE / relative_path
                self.assertTrue(file_path.is_file())
                self.assertGreater(file_path.stat().st_size, 0)

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
