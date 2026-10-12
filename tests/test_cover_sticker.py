"""Готовые обложки каруселей: защита исходников, пикселей и исключения сборки."""
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'tasks/content/2026-10-12-oblozhki-stiker'
SERIES = ['promty-sveta-dlya-foto-chatgpt', 'promty-tovar-reklama-chatgpt',
          'promty-blog-biznes-chatgpt', 'promty-risunok-zhivopis-chatgpt',
          'promty-igrushki-personazhi-chatgpt', 'promty-eda-dom-chatgpt',
          'promty-retro-ustroystvo-chatgpt']


def sha(data):
    return hashlib.sha256(data).hexdigest()


class CoverStickerTest(unittest.TestCase):
    def rows(self):
        rows = json.loads((SOURCES / 'manifest.json').read_text())['covers']
        self.assertEqual(set(rows), set(SERIES))
        return rows

    def test_source_and_installed_file_hashes_are_pinned(self):
        registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        for slug, row in self.rows().items():
            with self.subTest(slug=slug):
                self.assertEqual(sha((SOURCES / f'{slug}.png').read_bytes()), row['png_sha256'])
                cover = ROOT / registry[slug]['image']
                self.assertEqual(sha(cover.read_bytes()), row['webp_sha256'])
                self.assertEqual(registry[slug]['sha256'], row['webp_sha256'])
                meta = json.loads((ROOT / registry[slug]['layout']).read_text())
                self.assertEqual(meta['standard'], 'carousel-sticker-v1')
                self.assertEqual(meta['image_sha256'], row['webp_sha256'])

    @unittest.skipIf(Image is None, 'Pillow нужен для SHA-256 декодированных пикселей')
    def test_png_and_lossless_webp_have_identical_pixel_sha256(self):
        for slug, row in self.rows().items():
            with self.subTest(slug=slug):
                with Image.open(SOURCES / f'{slug}.png') as source, Image.open(
                        ROOT / f'claude-ai/{slug}/assets/oblozhka.webp') as installed:
                    self.assertEqual(source.size, (1600, 840))
                    self.assertEqual(installed.size, source.size)
                    self.assertEqual(installed.format, 'WEBP')
                    self.assertEqual(sha(source.convert('RGB').tobytes()), row['rgb_sha256'])
                    self.assertEqual(sha(installed.convert('RGB').tobytes()), row['rgb_sha256'])

    def test_standard_builder_cannot_render_or_install_sticker_covers(self):
        spec = importlib.util.spec_from_file_location('cover_standard', ROOT / 'scripts/build_cover_standard.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(set(SERIES).isdisjoint(row[0] for row in module.OTHER))
        for slug in SERIES:
            with self.subTest(slug=slug):
                with self.assertRaisesRegex(ValueError, 'стикер'):
                    module.render(slug, 'CHATGPT', 'Старый заголовок', 'Старая подпись')
                with patch.object(module, 'write_json') as write:
                    with self.assertRaisesRegex(ValueError, 'стикер'):
                        module.install(slug, None, {}, {}, {})
                    write.assert_not_called()

    def test_alt_og_and_homepage_describe_the_sticker(self):
        registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        homepage = (ROOT / 'index.html').read_text()
        for slug, row in self.rows().items():
            with self.subTest(slug=slug):
                expected = f"Обложка карусели: {row['sticker_text']}, рядом фото стало"
                self.assertEqual(registry[slug]['alt'], expected)
                escaped = html.escape(expected, quote=True)
                page = (ROOT / f'claude-ai/{slug}/index.html').read_text()
                self.assertIn(f'alt="{escaped}"', page)
                self.assertIn(f'property="og:image:alt" content="{escaped}"', page)
                self.assertIn('https://pronovoe.com/' + registry[slug]['image'], page)
                # Генератор главной добавляет заголовок статьи перед alt обложки
                self.assertIn(f'{escaped}"', homepage)
                self.assertIn(registry[slug]['image'], homepage)

    @unittest.skipIf(Image is None, 'Pillow нужен для проверки reading-480/960/1600')
    def test_reading_variants_match_resized_source_pixels(self):
        manifest = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        for slug in SERIES:
            key = f'claude-ai/{slug}/assets/oblozhka.webp'
            with self.subTest(slug=slug), Image.open(SOURCES / f'{slug}.png') as source:
                item = manifest[key]
                self.assertTrue(item['lossless'])
                self.assertEqual([v['width'] for v in item['variants']], [480, 960, 1600])
                self.assertEqual(item['original_bytes'], (ROOT / key).stat().st_size)
                for width in (480, 960, 1600):
                    with Image.open(ROOT / f'claude-ai/{slug}/assets/oblozhka.reading-{width}.webp') as actual:
                        expected = source.convert('RGB').resize((width, round(840*width/1600)), Image.Resampling.LANCZOS)
                        self.assertEqual(sha(actual.convert('RGB').tobytes()), sha(expected.tobytes()))

    def test_other_46_covers_and_reading_files_are_unchanged(self):
        base = '64557444515145e3e4b32c2ec128e552be96e3a4'
        registry = json.loads(subprocess.check_output(['git', 'show', base+':data/OBLOZHKI.json'], cwd=ROOT))
        unchanged = [item for slug, item in registry.items() if slug not in SERIES]
        self.assertEqual(len(unchanged), 46)
        current_registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        baseline_reading = json.loads(subprocess.check_output(['git', 'show', base+':data/reading-images.json'], cwd=ROOT))['images']
        current_reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        sticker_keys = {registry[slug]['image'] for slug in SERIES}
        for slug, item in registry.items():
            if slug not in SERIES:
                self.assertEqual(current_registry[slug], item)
        self.assertEqual({key: value for key, value in current_reading.items() if key not in sticker_keys},
                         {key: value for key, value in baseline_reading.items() if key not in sticker_keys})
        for item in unchanged:
            self.assertEqual(sha((ROOT / item['image']).read_bytes()), item['sha256'])
        changed = set(subprocess.check_output(['git', 'diff', '--name-only', base, '--', 'claude-ai'], cwd=ROOT).decode().splitlines())
        allowed = {f'claude-ai/{slug}/assets/oblozhka.webp' for slug in SERIES}
        allowed.update(f'claude-ai/{slug}/assets/oblozhka.reading-{width}.webp' for slug in SERIES for width in (480, 960, 1600))
        self.assertFalse({path for path in changed if path.endswith('.webp')} - allowed)


if __name__ == '__main__':
    unittest.main()
