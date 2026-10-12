"""Регрессии принятого общего layout, геометрии проб и связей реестра."""
import copy
import hashlib
import importlib.util
import json
import io
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
            self.assertEqual([b[2]-b[0] for b in frames], [300, 300], f'{slug}: ширина рамок различается')
            self.assertEqual([b[3]-b[1] for b in frames], [300, 300], f'{slug}: высота рамок различается')
            self.assertEqual(m['pair']['label_baselines'], [630, 630], f'{slug}: подписи не на одной базовой линии')
        toy = layouts[SERIES[4]]
        self.assertTrue(all('proba-2-' in p['path'] for p in toy['sources']), 'ИГРУШКА А: нужна девушка и CHIBI, а не отклонённые мужчины')
        for slug, probe in zip(SERIES, [1, 3, 1, 1, 2, 3, 3]):
            self.assertTrue(all(f'proba-{probe}-' in p['path'] for p in layouts[slug]['sources']),
                            f'{slug}: выбрана другая пара, существующий сюжет нельзя подменять')
        alternative = json.loads((ROOT / 'tasks/content/2026-10-12-oblozhki-standart/IGRUSHKA-B-layout.json').read_text())
        self.assertEqual(alternative['pair'], reference, 'ИГРУШКА Б: геометрия отличается от серии')
        self.assertTrue(all('proba-3-' in p['path'] for p in alternative['sources']), 'ИГРУШКА Б: нужна проба 3 с вязаной куклой')

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
        self.assertTrue('alt="Девушка на роликах и её фигурка CHIBI: проба 2"' in page,
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

    def test_validator_rejects_drift_with_russian_message(self):
        path = ROOT / 'scripts/build_cover_standard.py'
        self.assertTrue(path.exists(), 'Нет единого сборщика обложек')
        spec = importlib.util.spec_from_file_location('cover_standard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _, layouts = self.layouts()
        for field, value, message in [('background', '#000000', 'фон'), ('fonts', {}, 'шрифты'),
                                      ('pair', {}, 'рамки')]:
            bad = copy.deepcopy(layouts[SERIES[0]])
            bad[field] = value
            with self.assertRaisesRegex(ValueError, message):
                module.validate_layout(bad)


if __name__ == '__main__':
    unittest.main()
