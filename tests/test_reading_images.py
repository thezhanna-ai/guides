"""Contracts protecting original delivery, source selection and text sharpness."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import optimize_reading_images as images
import sobrat_glavnuyu as builder
try:
    from PIL import Image
except ImportError:
    Image = None


class ReadingImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(images.MANIFEST.read_text(encoding='utf-8'))

    def test_local_sources_cannot_escape_root(self):
        for src in ('../../../../private/secret.png', '/../../private/secret.png',
                    'https://example.com/picture.png', '//example.com/a.png',
                    'data:image/png;base64,AA', '%2e%2e/%2e%2e/%2e%2e/private/secret.png'):
            self.assertIsNone(images.local_path(src, 'claude-ai/article/index.html'), src)
            self.assertEqual({}, images.reading_attributes(src, 'claude-ai/article/index.html', self.manifest))

    def test_full_source_and_legacy_fallback_are_preserved(self):
        for key, item in self.manifest['images'].items():
            if not item['article']:
                continue
            page = item['pages'][0]
            src = Path(key).relative_to(Path(page).parent).as_posix()
            with self.subTest(image=key):
                attrs = images.reading_attributes(src, page, self.manifest)
                self.assertEqual(src, attrs['src'])
                self.assertEqual(src, attrs['data-full-src'])
                self.assertTrue((ROOT / key).is_file())
                # Native text remains native, even when a smaller asset is available.
                if item.get('article_reading_native_only'):
                    self.assertEqual(1, len(attrs['srcset'].split(', ')))
                    self.assertEqual(item['width'], int(attrs['srcset'].rsplit(' ', 1)[1][:-1]))

    def test_opus_article_selects_lossless_960_or_native_with_full_original(self):
        for key in images.RESPONSIVE_ARTICLE_TEXT:
            item = self.manifest['images'][key]
            page = item['pages'][0]
            attrs = images.reading_attributes(images.relative_url(key, page), page, self.manifest)
            candidates = [v.rsplit(' ', 1) for v in attrs['srcset'].split(', ')]
            self.assertEqual([960, item['width']], [int(v[1][:-1]) for v in candidates])
            self.assertFalse(item['article_reading_native_only'])
            self.assertEqual(images.relative_url(key, page), attrs['data-full-src'])
            self.assertLess((ROOT / images.local_path(candidates[0][0], page)).stat().st_size, item['original_bytes'])
            if Image is not None:
                with Image.open(ROOT / key) as original, Image.open(ROOT / images.local_path(candidates[0][0], page)) as reading:
                    expected = original.convert('RGB').resize(reading.size, Image.Resampling.LANCZOS)
                    self.assertEqual(expected.tobytes(), reading.convert('RGB').tobytes())
                    self.assertEqual(original.info.get('icc_profile'), reading.info.get('icc_profile'))

    @unittest.skipIf(Image is None, 'Pillow is required to verify actual decoded image dimensions')
    def test_srcset_descriptors_match_real_images_and_smaller_photos_exist(self):
        for key, item in self.manifest['images'].items():
            for page in (item['pages'][:1] if item['article'] else []) + (['index.html'] if item['cover'] else []):
                src = images.relative_url(key, page)
                attrs = images.reading_attributes(src, page, self.manifest)
                with self.subTest(image=key, page=page):
                    widths = []
                    for candidate in attrs['srcset'].split(', '):
                        url, descriptor = candidate.rsplit(' ', 1)
                        path = ROOT / images.local_path(url, page)
                        self.assertTrue(path.is_file())
                        with Image.open(path) as decoded:
                            width = decoded.width
                        self.assertEqual(width, int(descriptor[:-1]))
                        self.assertLessEqual(path.stat().st_size, item['original_bytes'])
                        widths.append(width)
                    self.assertEqual(len(widths), len(set(widths)))
                    if not item['lossless'] or page == 'index.html':
                        self.assertGreaterEqual(len(widths), 2)
                        self.assertLess(min(widths), item['width'])
                self.assertTrue(any(v['bytes'] < item['original_bytes'] for v in item['variants']), key)

    @unittest.skipIf(Image is None, 'Pillow is required to verify decoded pixels and ICC profiles')
    def test_native_text_lossless_pixels_and_color_profiles_are_exact(self):
        for key, item in self.manifest['images'].items():
            if not item['lossless']:
                continue
            with self.subTest(image=key):
                with Image.open(ROOT / key) as original:
                    mode = 'RGBA' if 'A' in original.getbands() else 'RGB'
                    source = original.convert(mode)
                    with Image.open(ROOT / item['lossless_reference']['path']) as variant:
                        decoded = variant.convert(mode)
                        self.assertEqual(source.size, decoded.size)
                        self.assertEqual(source.tobytes(), decoded.tobytes())
                        self.assertEqual(original.info.get('icc_profile'), variant.info.get('icc_profile'))

    def test_builder_and_article_application_are_idempotent(self):
        rendered = builder.sobrat_stranicu()
        self.assertEqual(rendered, images.optimize_html(rendered, 'index.html', self.manifest))
        self.assertEqual(rendered, builder.sobrat_stranicu())
        for page in ROOT.glob('claude-ai/*/index.html'):
            content = page.read_text(encoding='utf-8')
            self.assertEqual(content, images.optimize_html(content, page.relative_to(ROOT).as_posix(), self.manifest), str(page))

    @unittest.skipIf(Image is None, 'Pillow is required to verify native recompression')
    def test_three_inspected_native_posters_are_smaller_without_resizing(self):
        for key, quality in images.NATIVE_QUALITY.items():
            item = self.manifest['images'][key]
            self.assertEqual(quality, item['native_reading_quality'])
            self.assertFalse(item['native_reading_pixels_identical'])
            selected = ROOT / item['native_reading_path']
            self.assertLess(selected.stat().st_size, item['original_bytes'])
            with Image.open(ROOT / key) as original, Image.open(selected) as reading:
                self.assertEqual(original.size, reading.size)
                self.assertEqual(original.info.get('icc_profile'), reading.info.get('icc_profile'))
            page = item['pages'][0]
            attrs = images.reading_attributes(images.relative_url(key, page), page, self.manifest)
            self.assertEqual(item['native_reading_path'], images.local_path(attrs['srcset'].rsplit(' ', 1)[0], page))

    def test_optimizer_preserves_original_download_links_and_article_words(self):
        key = 'claude-ai/svoy-server-dlya-claude/assets/route-local.png'
        before = '<figure><a href="assets/route-local.png"><img src="assets/route-local.png" alt="Мелкий текст"><figcaption>Схема</figcaption></a></figure>'
        after = images.optimize_html(before, 'claude-ai/svoy-server-dlya-claude/index.html', self.manifest)
        self.assertIn('href="assets/route-local.png"', after)
        self.assertIn('alt="Мелкий текст"', after)
        self.assertIn('<figcaption>Схема</figcaption>', after)
        self.assertEqual(images.IMG.sub('', before), images.IMG.sub('', after))
        self.assertEqual(after, images.optimize_html(after, 'claude-ai/svoy-server-dlya-claude/index.html', self.manifest))


if __name__ == '__main__':
    unittest.main()
