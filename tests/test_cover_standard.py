"""Регрессии принятого общего layout, геометрии проб и связей реестра."""
import copy
import hashlib
import importlib.util
import json
import io
import math
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
         'opus-55-protiv-gpt-6-astra', 'konspekt-rechi-v-chatgpt']


class CoverStandardTest(unittest.TestCase):
    def layouts(self):
        reg = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        for slug in SERIES + OTHER:
            self.assertIn('layout', reg[slug], f'{slug}: реестр не указывает стандартный layout')
        return reg, {slug: json.loads((ROOT / item['layout']).read_text())
                     for slug, item in reg.items() if item.get('layout')}

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

    def test_series_geometry_and_titles(self):
        _, layouts = self.layouts()
        reference = layouts[SERIES[0]]['pair']
        for slug, count in zip(SERIES, [48, 72, 72, 72, 72, 48, 48]):
            m = layouts[slug]
            title = f'{count} ' + ('промптов' if count == 48 else 'промпта') + '\nдля фото'
            self.assertEqual(m['title'], title, f'{slug}: пропали число или назначение промптов')
            self.assertEqual(m['pair'], reference, f'{slug}: рамки или базовая линия было/стало отличаются от серии')
            frames = m['pair']['frames']
            self.assertEqual([b[2]-b[0] for b in frames], [269.5, 269.5], f'{slug}: ширина рамок различается')
            for box in frames:
                self.assertAlmostEqual((box[2]-box[0])/(box[3]-box[1]), 3/4)
            self.assertEqual(frames[0][0], 973)
            self.assertEqual(frames[1][2], 1600-48)
            self.assertEqual(frames[1][0]-frames[0][2], 40)
            self.assertEqual(m['pair']['label_baselines'], [672, 672], f'{slug}: подписи не на одной базовой линии')
            self.assertEqual(m['pair']['fit'], 'fit')
            self.assertLess(max(b[2] for b in m['title_boxes']), frames[0][0])
            self.assertAlmostEqual((frames[0][1]+frames[0][3])/2, (270+602)/2)

    @unittest.skipIf(Image is None, 'Pillow нужен для измерения заголовка')
    def test_series_frame_starts_40_pixels_after_widest_title(self):
        from PIL import ImageDraw
        spec = importlib.util.spec_from_file_location('cover_standard', ROOT / 'scripts/build_cover_standard.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        draw = ImageDraw.Draw(Image.new('RGB', (1600,840)))
        _, layouts = self.layouts()
        right = max(draw.textbbox((128,270), line, font=module.font('title'), anchor='lt')[2]
                    for slug in SERIES for line in layouts[slug]['title'].splitlines())
        for slug in SERIES:
            self.assertEqual(layouts[slug]['pair']['frames'][0][0], right+40)

    def test_carousel_sources_and_full_resolution_hashes(self):
        _, layouts = self.layouts()
        selection = json.loads((ROOT / 'tasks/content/2026-10-12-oblozhki-standart/carousel-selection.json').read_text())
        expected = {SERIES[2]: '3-onemainshot.png', SERIES[3]: '4-threadart.png',
                    SERIES[4]: '5-blisterpack-foto-blur.png',
                    SERIES[5]: '6-kitchenview-foto2-blur.png',
                    SERIES[6]: '7-revealparts-foto-blur.png'}
        for row in selection['covers']:
            if row['slug'] not in expected:
                continue
            meta = layouts[row['slug']]
            self.assertEqual([x['path'] for x in meta['sources']], [x['path'] for x in row['sources']])
            self.assertEqual(Path(row['sources'][1]['workspace_path']).name, expected[row['slug']])
            for actual, declared in zip(meta['sources'], row['sources']):
                self.assertEqual(actual['sha256'], declared['sha256'])
                self.assertEqual(hashlib.sha256((ROOT / actual['path']).read_bytes()).hexdigest(), declared['sha256'])
            self.assertEqual(meta['carousel'], row['carousel'])
        self.assertIn('devushka-roliki-11745764.jpg', selection['covers'][4]['sources'][0]['workspace_path'])

    @unittest.skipIf(Image is None, 'Pillow нужен для сверки реальных фото')
    def test_selected_photos_really_appear_in_cover_frames(self):
        from PIL import ImageOps, ImageChops
        reg, layouts = self.layouts()
        for slug in SERIES:
            meta = layouts[slug]
            cover = Image.open(ROOT / reg[slug]['image']).convert('RGB')
            expected_pair = Image.new('RGB', (3474, 2160), '#102F30')
            for index, item in enumerate(meta['sources']):
                if item['revision'] == 'workspace-copy':
                    data = (ROOT / item['path']).read_bytes()
                else:
                    data = subprocess.check_output(['git', 'show', item['revision']+':'+item['path']], cwd=ROOT)
                source = Image.open(io.BytesIO(data)).convert('RGB')
                fitted = ImageOps.fit(source, (1617, 2156), Image.Resampling.LANCZOS,
                                      centering=tuple(meta['crop_centers'][index]))
                expected_pair.paste(fitted, (1857*index, 2))
            expected_pair = expected_pair.resize((579, 360), Image.Resampling.LANCZOS)
            for box in meta['pair']['frames']:
                # Реальное фото во всей рамке; исключается только край обводки/сглаживания
                inner = (math.ceil(box[0])+6, math.ceil(box[1])+6,
                         math.floor(box[2])-6, math.floor(box[3])-6)
                expected = expected_pair.crop((inner[0]-973, inner[1]-256,
                                              inner[2]-973, inner[3]-256))
                self.assertIsNone(ImageChops.difference(cover.crop(inner), expected).getbbox(), slug)

    @unittest.skipIf(Image is None, 'Pillow нужен для проверки пустых полос')
    def test_series_frames_have_no_background_bands(self):
        reg, layouts = self.layouts()
        background = (16, 47, 48)
        for slug in SERIES:
            cover = Image.open(ROOT / reg[slug]['image']).convert('RGB')
            for box in layouts[slug]['pair']['frames']:
                photo = cover.crop((math.ceil(box[0])+4, math.ceil(box[1])+4,
                                    math.floor(box[2])-4, math.floor(box[3])-4))
                for y in range(photo.height):
                    self.assertNotEqual(photo.crop((0,y,photo.width,y+1)).getextrema(),
                                        tuple((c,c) for c in background), slug)
                for x in range(photo.width):
                    self.assertNotEqual(photo.crop((x,0,x+1,photo.height)).getextrema(),
                                        tuple((c,c) for c in background), slug)

    def test_responsive_images_og_and_homepage(self):
        reg, _ = self.layouts()
        reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        homepage = (ROOT / 'index.html').read_text()
        for slug in SERIES + OTHER:
            key = reg[slug]['image']
            self.assertEqual([v['width'] for v in reading[key]['variants']], [480, 960, 1600], f'{slug}: не все размеры для карточки')
            self.assertIn(key, homepage, f'{slug}: главная использует прежнюю обложку')
            page = (ROOT / f'claude-ai/{slug}/index.html').read_text()
            self.assertIn('https://pronovoe.com/' + key, page, f'{slug}: OG ссылается не на актуальную обложку')
        page = (ROOT / f'claude-ai/{SERIES[4]}/index.html').read_text()
        self.assertTrue('alt="Девушка на роликах и фигурка Roller Girl в блистере"' in page,
                        'ИГРУШКА: alt должен описывать новую пару')

    @unittest.skipIf(Image is None, 'Pillow отсутствует в этом интерпретаторе; пиксельный тест выполняется в Python 3.12')
    def test_actual_background_and_responsive_pixels(self):
        reg, layouts = self.layouts()
        reading = json.loads((ROOT / 'data/reading-images.json').read_text())['images']
        for slug in SERIES + OTHER:
            image = Image.open(ROOT / reg[slug]['image']).convert('RGB')
            self.assertEqual(image.size, (1600, 840), f'{slug}: исходная обложка не 1600x840')
            strip = image.crop((0, 0, 96, 840))
            self.assertEqual(strip.tobytes(), bytes((16, 47, 48)) * 96 * 840,
                             f'{slug}: реальный фон слева не однотонный #102F30')
            for variant in reading[reg[slug]['image']]['variants']:
                actual = Image.open(ROOT / variant['path']).convert('RGB')
                expected = image.resize((variant['width'], variant['height']), Image.Resampling.LANCZOS)
                self.assertEqual(actual.tobytes(), expected.tobytes(), f'{slug}: размер {variant["width"]} повреждает изображение или текст')

    def test_other_42_covers_are_unchanged(self):
        base = 'a059df2e01d424be6922cb59c4c4e078a2579daa'
        registry = json.loads(subprocess.check_output(['git', 'show', base+':data/OBLOZHKI.json'], cwd=ROOT))
        unchanged = [item for slug, item in registry.items() if slug not in SERIES + OTHER]
        self.assertEqual(len(unchanged), 42, 'Число обложек за пределами задания изменилось')
        for item in unchanged:
            self.assertEqual(hashlib.sha256((ROOT/item['image']).read_bytes()).hexdigest(), item['sha256'],
                             f'{item["image"]}: обложку за пределами задания нельзя пересобирать')

    def test_this_update_keeps_all_46_other_cover_pixels_and_files(self):
        base = '0c6dc66'
        registry = json.loads(subprocess.check_output(['git', 'show', base+':data/OBLOZHKI.json'], cwd=ROOT))
        changed = set(SERIES)
        unchanged = [item for slug, item in registry.items() if slug not in changed]
        self.assertEqual(len(unchanged), 46)
        for item in unchanged:
            self.assertEqual(hashlib.sha256((ROOT/item['image']).read_bytes()).hexdigest(), item['sha256'])

    def test_validator_rejects_drift_with_russian_message(self):
        path = ROOT / 'scripts/build_cover_standard.py'
        self.assertTrue(path.exists(), 'Нет единого сборщика обложек')
        spec = importlib.util.spec_from_file_location('cover_standard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _, layouts = self.layouts()
        for field, value, message in [('background', '#000000', 'фон'), ('fonts', {}, 'шрифты'),
                                      ('pair', {}, 'рамки'),
                                      ('title_boxes', [[128,270,974,360]], 'заголовок')]:
            bad = copy.deepcopy(layouts[SERIES[0]])
            bad[field] = value
            with self.assertRaisesRegex(ValueError, message):
                module.validate_layout(bad)


if __name__ == '__main__':
    unittest.main()
