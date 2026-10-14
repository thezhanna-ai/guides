"""Regression: cap-height differences must not collapse caption leading."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

class CoverLeadingTest(unittest.TestCase):
    def test_published_leading_and_only_caption_pixels_changed(self):
        policy = json.loads((ROOT / 'data/cover-leading.json').read_text())
        font = ImageFont.truetype(str(ROOT / 'scripts/cover-fonts/Spectral-Regular.ttf'), 64)
        self.assertEqual(len(policy['updated']), 14)
        for edit in policy['updated']:
            with self.subTest(slug=edit['slug']):
                old_bytes = subprocess.check_output(['git', 'show', policy['base'] + ':' + edit['image']], cwd=ROOT)
                new_bytes = (ROOT / edit['image']).read_bytes()
                self.assertEqual(hashlib.sha256(old_bytes).hexdigest(), edit['source_sha256'])
                self.assertEqual(hashlib.sha256(new_bytes).hexdigest(), edit['result_sha256'])
                old, new = Image.open(io.BytesIO(old_bytes)).convert('RGB'), Image.open(io.BytesIO(new_bytes)).convert('RGB')
                allowed = Image.new('L', old.size)
                draw = ImageDraw.Draw(allowed)
                for box in edit['old_boxes'] + edit['new_boxes']:
                    draw.rectangle(box, fill=255)
                delta = ImageChops.difference(old, new)
                self.assertIsNone(Image.composite(Image.new('RGB', old.size), delta, allowed).getbbox())
                self.assertIsNotNone(delta.getbbox())
                self.assertEqual(edit['baselines'][1] - edit['baselines'][0], 70)
                new_text = Image.new('L', old.size)
                for line, baseline in zip(edit['lines'], edit['baselines']):
                    ImageDraw.Draw(new_text).text((edit['new_origin'][0], baseline), line, font=font, fill=255, anchor='ls')
                cleared_cores = 0
                for x1, y1, x2, y2 in edit['old_boxes']:
                    for y in range(y1, y2):
                        for x in range(x1, x2):
                            if old.getpixel((x, y)) == (187, 199, 202) and new_text.getpixel((x, y)) == 0:
                                self.assertNotEqual(new.getpixel((x, y)), (187, 199, 202), 'Old caption remains under the moved line')
                                cleared_cores += 1
                self.assertGreater(cleared_cores, 100)
                for line, baseline, box in zip(edit['lines'], edit['baselines'], edit['all_boxes']):
                    self.assertEqual(box[1], baseline + font.getbbox(line, anchor='ls')[1])
                    self.assertLessEqual(box[3], 704)
                    # Check actual glyph cores at the recorded baselines, not metadata alone.
                    mask = Image.new('L', (box[2] - box[0], box[3] - box[1]))
                    ImageDraw.Draw(mask).text((0, 0), line, font=font, fill=255, anchor='lt')
                    core = mask.point(lambda value: 255 if value == 255 else 0)
                    actual = new.crop(box)
                    color_delta = ImageChops.difference(actual, Image.new('RGB', actual.size, '#BBC7CA'))
                    self.assertIsNone(Image.composite(color_delta, Image.new('RGB', actual.size), core).getbbox())

    def test_builder_uses_baselines_for_lines_with_different_letter_heights(self):
        spec = importlib.util.spec_from_file_location('leading_builder', ROOT / 'scripts/build_cover_standard.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        _, meta = builder.render('zagruzka-faylov-v-claude', 'CLAUDE · ЧАТ', 'Загрузка\nфайлов', 'Один файл или целая пачка')
        self.assertEqual(meta['subtitle_lines'], ['Один файл или', 'целая пачка'])
        self.assertEqual(meta['subtitle_baselines'], [612, 682])
        self.assertEqual(meta['subtitle_boxes'][1][1], 652)
