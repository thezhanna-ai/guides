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
        font = ImageFont.truetype(str(ROOT / 'scripts/cover-fonts/Spectral-Regular.ttf'), 64, layout_engine=ImageFont.Layout.BASIC)
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
                # The approved PNG hash above is the pixel-level snapshot.
                # Re-rasterizing a font here depends on the host FreeType build.
                for line, baseline, box in zip(edit['lines'], edit['baselines'], edit['all_boxes']):
                    self.assertEqual(box[1], baseline + font.getbbox(line, anchor='ls')[1])
                    self.assertLessEqual(box[3], 704)
                    actual = new.crop(box)
                    self.assertGreater(sum(pixel == (187, 199, 202)
                                           for pixel in actual.get_flattened_data()), 100)

    def test_builder_uses_baselines_for_lines_with_different_letter_heights(self):
        spec = importlib.util.spec_from_file_location('leading_builder', ROOT / 'scripts/build_cover_standard.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        _, meta = builder.render('zagruzka-faylov-v-claude', 'CLAUDE · ЧАТ', 'Загрузка\nфайлов', 'Один файл или целая пачка')
        self.assertEqual(meta['subtitle_lines'], ['Один файл или', 'целая пачка'])
        self.assertEqual(meta['subtitle_baselines'], [612, 682])
        self.assertEqual(meta['subtitle_boxes'][1][1], 652)
