"""Регрессии стандартного layout; готовая серия со стикером проверяется отдельно."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parents[1]
SERIES = ['promty-sveta-dlya-foto-chatgpt', 'promty-tovar-reklama-chatgpt',
          'promty-blog-biznes-chatgpt', 'promty-risunok-zhivopis-chatgpt',
          'promty-igrushki-personazhi-chatgpt', 'promty-eda-dom-chatgpt',
          'promty-retro-ustroystvo-chatgpt']
OTHER = ['raspisanie-zadach-v-claude', 'zagruzka-faylov-v-claude',
         'opus-55-protiv-gpt-6-astra']


class CoverStandardTest(unittest.TestCase):
    def layouts(self):
        reg = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        for slug in OTHER:
            self.assertIn('layout', reg[slug], f'{slug}: реестр не указывает стандартный layout')
        return reg, {slug: json.loads((ROOT / item['layout']).read_text())
                     for slug, item in reg.items() if slug in OTHER}

    def test_all_standard_covers_use_same_fonts_background_and_positions(self):
        reg, layouts = self.layouts()
        expected = {'title': {'family': 'Unbounded', 'weight': 700, 'size': 96},
                    'section': {'family': 'JetBrains Mono', 'weight': 500, 'size': 28},
                    'subtitle': {'family': 'Spectral', 'weight': 400, 'size': 42},
                    'site': {'family': 'JetBrains Mono', 'weight': 400, 'size': 30}}
        for slug, meta in layouts.items():
            if meta.get('standard') != 'pronovoe-cover-v1':
                continue
            self.assertEqual(meta['fonts'], expected, f'{slug}: кегли или шрифты расходятся с каноном')
            self.assertEqual(meta['background'], '#102F30', f'{slug}: фон отличается от ЧЕТЫРЕ')
            self.assertEqual(meta['title_origins'], [[128, 270], [128, 388]], f'{slug}: заголовок сдвинут')
            self.assertEqual(meta['subtitle_origin'], [128, 563], f'{slug}: подзаголовок сдвинут')
            self.assertEqual(meta['image_sha256'], hashlib.sha256((ROOT / reg[slug]['image']).read_bytes()).hexdigest(), f'{slug}: layout относится к другой картинке')

    def test_responsive_images_og_and_homepage(self):
        reg, _ = self.layouts()
        reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        homepage = (ROOT / 'index.html').read_text()
        for slug in OTHER:
            key = reg[slug]['image']
            self.assertEqual([v['width'] for v in reading[key]['variants']], [480, 960, 1600], f'{slug}: не все размеры для карточки')
            self.assertIn(key, homepage, f'{slug}: главная использует прежнюю обложку')
            page = (ROOT / f'claude-ai/{slug}/index.html').read_text()
            self.assertIn('https://pronovoe.com/' + key, page, f'{slug}: OG ссылается не на актуальную обложку')

    @unittest.skipIf(Image is None, 'Pillow отсутствует в этом интерпретаторе; пиксельный тест выполняется в Python 3.12')
    def test_actual_background_and_responsive_pixels(self):
        reg, layouts = self.layouts()
        reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        for slug in OTHER:
            image = Image.open(ROOT / reg[slug]['image']).convert('RGB')
            self.assertEqual(image.size, (1600, 840), f'{slug}: исходная обложка не 1600x840')
            strip = image.crop((0, 0, 96, 840))
            self.assertEqual(strip.tobytes(), bytes((16, 47, 48)) * 96 * 840,
                             f'{slug}: реальный фон слева не однотонный #102F30')
            for variant in reading[reg[slug]['image']]['variants']:
                actual = Image.open(ROOT / variant['path']).convert('RGB')
                expected = image.resize((variant['width'], variant['height']), Image.Resampling.LANCZOS)
                self.assertEqual(actual.tobytes(), expected.tobytes(), f'{slug}: размер {variant["width"]} повреждает изображение или текст')

    def test_other_43_covers_are_unchanged(self):
        base = 'a059df2e01d424be6922cb59c4c4e078a2579daa'
        registry = json.loads(subprocess.check_output(['git', 'show', base+':data/OBLOZHKI.json'], cwd=ROOT))
        unchanged = [item for slug, item in registry.items() if slug not in SERIES + OTHER]
        self.assertEqual(len(unchanged), 43, 'Число обложек за пределами задания изменилось')
        for item in unchanged:
            self.assertEqual(hashlib.sha256((ROOT/item['image']).read_bytes()).hexdigest(), item['sha256'],
                             f'{item["image"]}: обложку за пределами задания нельзя пересобирать')

    def test_chat_cover_labels_match_originals(self):
        spec = importlib.util.spec_from_file_location('cover_standard', ROOT / 'scripts/build_cover_standard.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _, layouts = self.layouts()
        sections = {slug: section for slug, section, _, _ in module.OTHER}
        for slug in OTHER[:2]:
            self.assertEqual(sections[slug], 'CLAUDE · ЧАТ', f'{slug}: сборщик изменил исходную метку')
            self.assertEqual(layouts[slug]['section'], 'CLAUDE · ЧАТ', f'{slug}: на обложке должна быть исходная метка')

    def test_konspekt_update_keeps_covers_outside_sticker_series(self):
        base = 'e2f0969ad3d51b550c0453c15e401b802f82d88b'
        registry = json.loads(subprocess.check_output(['git', 'show', base+':data/OBLOZHKI.json'], cwd=ROOT))
        changed = {'konspekt-rechi-v-chatgpt', *SERIES}
        unchanged = [item for slug, item in registry.items() if slug not in changed]
        self.assertEqual(len(unchanged), 45)
        for item in unchanged:
            self.assertEqual(hashlib.sha256((ROOT/item['image']).read_bytes()).hexdigest(), item['sha256'])

    def test_konspekt_preserves_accepted_cover_and_is_excluded_from_standard_build(self):
        slug = 'konspekt-rechi-v-chatgpt'
        key = f'claude-ai/{slug}/assets/oblozhka-v4.webp'
        accepted = subprocess.check_output(['git', 'show', 'b57f531:'+key], cwd=ROOT)
        self.assertEqual(hashlib.sha256((ROOT / key).read_bytes()).hexdigest(), hashlib.sha256(accepted).hexdigest())
        registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        old = json.loads(subprocess.check_output(['git', 'show', 'b57f531:data/OBLOZHKI.json'], cwd=ROOT))
        self.assertEqual(registry[slug], old[slug])
        self.assertFalse((ROOT / f'claude-ai/{slug}/assets/oblozhka-layout.json').exists())
        spec = importlib.util.spec_from_file_location('cover_standard', ROOT / 'scripts/build_cover_standard.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertNotIn(slug, [row[0] for row in module.OTHER])
        reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images'][key]
        self.assertEqual(reading['original_bytes'], len(accepted))
        for width in (480, 960, 1600):
            variant = (ROOT / key).with_name(f'oblozhka-v4.reading-{width}.webp')
            self.assertTrue(variant.is_file())
            if Image is not None:
                with Image.open(ROOT / key) as original, Image.open(variant) as actual:
                    expected = original.convert('RGB').resize((width, round(840*width/1600)), Image.Resampling.LANCZOS)
                    self.assertEqual(actual.convert('RGB').tobytes(), expected.tobytes())
        self.assertIn(key, (ROOT / 'index.html').read_text())

    def test_validator_rejects_drift_with_russian_message(self):
        path = ROOT / 'scripts/build_cover_standard.py'
        self.assertTrue(path.exists(), 'Нет единого сборщика обложек')
        spec = importlib.util.spec_from_file_location('cover_standard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _, layouts = self.layouts()
        for field, value, message in [('background', '#000000', 'фон'), ('fonts', {}, 'шрифты')]:
            bad = copy.deepcopy(layouts[OTHER[0]])
            bad[field] = value
            with self.assertRaisesRegex(ValueError, message):
                module.validate_layout(bad)


if __name__ == '__main__':
    unittest.main()
