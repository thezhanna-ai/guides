"""The approved notebook photograph stays intact when resizing its title."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import unittest
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]

class KonspektTitleTest(unittest.TestCase):
    def test_native_title_and_preserved_caption_and_scene(self):
        edit = json.loads((ROOT / 'data/cover-readability.json').read_text())['updated']['konspekt-rechi-v-chatgpt']
        title = edit['title_edit']
        old_bytes = subprocess.check_output(['git', 'show', title['base'] + ':' + edit['image']], cwd=ROOT)
        self.assertEqual(hashlib.sha256(old_bytes).hexdigest(), title['source_sha256'])
        old = Image.open(io.BytesIO(old_bytes)).convert('RGB')
        new_bytes = (ROOT / edit['image']).read_bytes()
        self.assertEqual(hashlib.sha256(new_bytes).hexdigest(), edit['result_sha256'])
        new = Image.open(io.BytesIO(new_bytes)).convert('RGB')
        allowed = Image.new('L', old.size)
        for box in title['allowed_boxes'] + edit.get('label_edit', {}).get('allowed_boxes', []):
            ImageDraw.Draw(allowed).rectangle(box, fill=255)
        difference = ImageChops.difference(old, new)
        self.assertIsNone(Image.composite(Image.new('RGB', old.size), difference, allowed).getbbox())
        self.assertIsNotNone(difference.getbbox())
        self.assertEqual(old.crop((0, 445, 1600, 840)).tobytes(), new.crop((0, 445, 1600, 840)).tobytes())
        self.assertEqual(title['font_family'], 'Unbounded')
        self.assertEqual(title['font_weight'], 700)
        self.assertEqual([line['text'] for line in title['lines']], ['Пять', 'конспектов'])
        self.assertEqual([line['font_size'] for line in title['lines']], [96, 90])
        for line in title['lines']:
            # The approved image hash is a complete pixel-level snapshot.
            # Font rasterization varies with the host FreeType build.
            box = line['box']
            expected = tuple(int(line['color'][i:i+2], 16) for i in (1, 3, 5))
            self.assertGreater(sum(pixel == expected for pixel in
                                   new.crop(box).get_flattened_data()), 100)
        # No opaque letters from the former oversized second line survive below the new title.
        below = new.crop((55, 398, 725, 420))
        self.assertLess(below.getchannel('R').getextrema()[1], 100)

    def test_label_move_retains_current_title_caption_and_notebook(self):
        edit = json.loads((ROOT / 'data/cover-readability.json').read_text())['updated']['konspekt-rechi-v-chatgpt']
        label = edit['label_edit']
        source = subprocess.check_output(['git', 'show', label['base'] + ':' + edit['image']], cwd=ROOT)
        self.assertEqual(hashlib.sha256(source).hexdigest(), label['source_sha256'])
        old = Image.open(io.BytesIO(source)).convert('RGB')
        new = Image.open(ROOT / edit['image']).convert('RGB')
        allowed = Image.new('L', old.size)
        for box in label['allowed_boxes']:
            ImageDraw.Draw(allowed).rectangle(box, fill=255)
        difference = ImageChops.difference(old, new)
        self.assertIsNone(Image.composite(Image.new('RGB', old.size), difference, allowed).getbbox())
        self.assertEqual(new.crop((55, 48, 210, 90)).getchannel('R').getextrema()[1] < 90, True)
        dy = label['delta_y']
        count = 0
        for y in range(48, 90):
            for x in range(55, 210):
                pixel = old.getpixel((x, y))
                if min(pixel) > 90:
                    self.assertEqual(new.getpixel((x, y + dy)), pixel)
                    count += 1
        self.assertGreater(count, 1000)
        self.assertEqual(label['visible_top'], 121)
