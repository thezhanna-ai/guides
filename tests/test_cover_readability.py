"""Approved typography edits must retain the current cover composition exactly."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import unittest
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

class CoverReadabilityTest(unittest.TestCase):
    def test_published_cover_text_and_scene_preservation(self):
        policy = json.loads((ROOT / 'data/cover-readability.json').read_text())
        registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
        self.assertEqual(len(policy['updated']), 47)
        self.assertEqual(len(policy['preserved']), 9)
        for slug, edit in policy['updated'].items():
            path = registry[slug]['image']
            data = (ROOT / path).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), edit['result_sha256'], slug)
            self.assertEqual(edit['font_size'], 64, slug)
            self.assertEqual(' '.join(edit['lines']), registry[slug]['subtitle'], slug)
            source = subprocess.check_output(['git', 'show', policy['base'] + ':' + path], cwd=ROOT)
            self.assertEqual(hashlib.sha256(source).hexdigest(), edit['source_sha256'], slug)
            old = Image.open(io.BytesIO(source)).convert('RGB')
            new = Image.open(io.BytesIO(data)).convert('RGB')
            self.assertEqual(old.size, new.size, slug)
            mask = Image.new('L', old.size)
            draw = ImageDraw.Draw(mask)
            for box in edit['allowed_boxes']:
                self.assertLessEqual(box[2], 920, slug)
                self.assertGreaterEqual(box[1], 468 if slug == 'konspekt-rechi-v-chatgpt' else 485 if slug == 'pyat-instrumentov-dlya-sayta' else 540, slug)
                self.assertLessEqual(box[3], 710, slug)
                draw.rectangle(box, fill=255)
            if 'title_edit' in edit:
                self.assertEqual(slug, 'konspekt-rechi-v-chatgpt')
                for box in edit['title_edit']['allowed_boxes']:
                    self.assertGreaterEqual(box[1], 170)
                    self.assertLessEqual(box[2], 755)
                    self.assertLessEqual(box[3], 445)
                    draw.rectangle(box, fill=255)
            difference = ImageChops.difference(old, new)
            self.assertIsNone(Image.composite(Image.new('RGB', old.size), difference, mask).getbbox(), slug)
            self.assertIsNotNone(difference.getbbox(), slug)
        for slug, digest in policy['preserved'].items():
            self.assertEqual(hashlib.sha256((ROOT / registry[slug]['image']).read_bytes()).hexdigest(), digest, slug)

    def test_revised_assets_have_cache_versions_and_builder_is_idempotent(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('reading_cache', ROOT / 'scripts/optimize_reading_images.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = json.loads((ROOT / 'data/cover-readability.json').read_text())
        manifest = json.loads((ROOT / 'data/reading-images.json').read_text())
        for slug, edit in policy['updated'].items():
            key = edit['image']
            self.assertEqual(manifest['images'][key]['cache_version'], edit['result_sha256'][:12])
            attrs = module.reading_attributes(key, 'index.html', manifest)
            self.assertEqual(key, attrs['src'])
            for candidate in attrs['srcset'].split(', '):
                self.assertIn('?v=' + edit['result_sha256'][:12], candidate)
            tag = '<img src="' + key + '">'
            once = module.optimize_html(tag, 'index.html', manifest)
            self.assertEqual(once, module.optimize_html(once, 'index.html', manifest))

    def test_legacy_builder_cannot_replace_approved_scenes(self):
        result = subprocess.run(['python3.12', 'scripts/build_cover_standard.py'], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('массовая пересборка из старого BASE запрещена', result.stderr)

    def test_regeneration_retains_lossless_text_and_cache_version(self):
        import importlib.util
        import shutil
        import tempfile
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('reading_regenerate', ROOT / 'scripts/optimize_reading_images.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = json.loads((ROOT / 'data/cover-readability.json').read_text())
        edit = policy['updated']['komanda-ii-agentov-dlya-bloga']
        key = edit['image']
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder)
            (temp / key).parent.mkdir(parents=True)
            shutil.copy2(ROOT / key, temp / key)
            (temp / 'data').mkdir()
            shutil.copy2(ROOT / 'data/cover-readability.json', temp / 'data/cover-readability.json')
            with patch.object(module, 'ROOT', temp), patch.object(module, 'MANIFEST', temp / 'data/reading-images.json'), patch.object(module, 'inventory', return_value={key: {'article': True, 'cover': True, 'pages': []}}):
                result = module.generate()['images'][key]
            self.assertTrue(result['lossless'])
            self.assertEqual(result['cache_version'], edit['result_sha256'][:12])
            original = Image.open(temp / key).convert('RGB')
            for v in result['variants']:
                actual = Image.open(temp / v['path']).convert('RGB')
                expected = original.resize(actual.size, Image.Resampling.LANCZOS)
                self.assertEqual(actual.tobytes(), expected.tobytes())
