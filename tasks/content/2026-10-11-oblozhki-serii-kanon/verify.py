"""Inspect real outputs, original pixels, registry and generated HTML offline."""
import json
import re
from pathlib import Path

from PIL import Image
import build

ROOT, OUT = build.ROOT, build.OUT
manifest = json.loads((ROOT / 'data/reading-images.json').read_text())
layout = json.loads((OUT / 'layout.json').read_text())
old_registry = json.loads(build.blob(build.REV, 'data/OBLOZHKI.json'))
registry = json.loads((ROOT / 'data/OBLOZHKI.json').read_text())
old_manifest = json.loads(build.blob(build.REV, 'data/reading-images.json'))
old_layout = json.loads((build.WORKSPACE /
    'tasks/content/2026-10-11-oblozhki-serii/layout.json').read_text())
home = (ROOT / 'index.html').read_text()
results = []
keys = set()
for slug, title, subtitle in build.ITEMS:
    key = f'claude-ai/{slug}/assets/oblozhka.webp'
    keys.add(key)
    meta = next(x for x in layout['covers'] if x['slug'] == slug)
    previous = next(x for x in old_layout['covers'] if x['slug'] == slug)
    assert title.splitlines() == previous['title']
    assert subtitle == ' '.join(previous['subtitle'])
    assert meta['title_size'] == 96
    assert meta['subtitle_box'][1] == 563
    assert [b[1] for b in meta['title_boxes']] == [270, 388]
    # Ж has a -1 px left bearing; the drawing origin is still x=128.
    assert all(127 <= b[0] <= 128 for b in meta['title_boxes'])
    before = Image.open(build.io.BytesIO(build.blob(build.REV, key))).convert('RGB')
    after = Image.open(ROOT / key).convert('RGB')
    assert after.size == (1600, 840)
    assert before.crop((880, 0, 1600, 840)).tobytes() == after.crop((880, 0, 1600, 840)).tobytes()
    assert registry[slug] == {**old_registry[slug], 'sha256': build.sha((ROOT / key).read_bytes())}
    variants = manifest['images'][key]['variants']
    assert [v['width'] for v in variants] == [480, 960, 1600]
    for variant in variants:
        with Image.open(ROOT / variant['path']) as im:
            assert im.size == (variant['width'], variant['height'])
            assert (ROOT / variant['path']).stat().st_size == variant['bytes']
    html = (ROOT / f'claude-ai/{slug}/index.html').read_text()
    cover = next(t for t in re.findall(r'<img\b[^>]*>', html)
                 if 'src="assets/oblozhka.webp"' in t)
    assert all(str(w) + 'w' in cover for w in (480, 960, 1600))
    assert 'data-full-src="assets/oblozhka.webp"' in cover
    assert f'https://pronovoe.com/{key}' in html
    assert key in home and key.replace('oblozhka.webp', 'oblozhka.reading-480.webp') in home
    assert html == build.blob(build.REV, f'claude-ai/{slug}/index.html').decode()
    results.append({'slug': slug, 'right_pixels_identical': True,
        'texts_unchanged': True, 'variants': [480, 960, 1600],
        'srcset_og_card': 'PASS', 'article_html_unchanged': True})
assert {k: v for k, v in manifest['images'].items() if k not in keys} == {
    k: v for k, v in old_manifest['images'].items() if k not in keys}
assert home == build.blob(build.REV, 'index.html').decode()
assert (OUT / 'LIST-v2.png').read_bytes() == (build.DELIVERY / 'LIST-v2.png').read_bytes()
checks = {'status': 'PASS', 'covers': results, 'unrelated_manifest_unchanged': True,
          'homepage_rebuilt_identical': True, 'sheet_delivered_identical': True}
(OUT / 'CHECKS.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
print('PASS: 7 covers; 21 sizes; unchanged texts/right pixels; OG/srcset/cards; no unrelated changes')
