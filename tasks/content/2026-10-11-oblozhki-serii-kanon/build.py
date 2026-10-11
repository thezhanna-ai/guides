"""Accepted v2 typography over the unchanged right sides from 908eb6e."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys

from PIL import Image, ImageDraw
import template_v2 as canon

ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = ROOT.parents[1]
OUT = Path(__file__).resolve().parent
DELIVERY = WORKSPACE / 'tasks/content/2026-10-11-oblozhki-serii'
FONTS = WORKSPACE / 'tasks/content/2026-10-03-oformlenie-sayta/fonts'
REV = '908eb6e'
ITEMS = [
    ('promty-sveta-dlya-foto-chatgpt', 'Новый\nсвет', 'Что изменит свет?'),
    ('promty-tovar-reklama-chatgpt', 'Твой\nтовар', 'Что изменит упаковка?'),
    ('promty-blog-biznes-chatgpt', 'Своя\nафиша', 'Какой образ запомнится?'),
    ('promty-risunok-zhivopis-chatgpt', 'Живая\nкисть', 'Каким станет твоё фото?'),
    ('promty-igrushki-personazhi-chatgpt', 'Твой\nгерой', 'Кем станет человек?'),
    ('promty-eda-dom-chatgpt', 'Еда\nдом', 'Как изменится кухня?'),
    ('promty-retro-ustroystvo-chatgpt', 'Внутри\nретро', 'Что скрыто внутри?'),
]


def blob(revision, path):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import optimize_reading_images as opt
    registry_path = ROOT / 'data/OBLOZHKI.json'
    registry = json.loads(registry_path.read_text())
    manifest = json.loads(opt.MANIFEST.read_text())
    reference_key = 'claude-ai/chetyre-mcp-claude-code/assets/oblozhka.webp'
    reference = blob('origin/main', reference_key)
    (OUT / 'chetyre-reference.webp').write_bytes(reference)
    (OUT / 'opus-reference.webp').write_bytes(blob('origin/main',
        'claude-ai/opus-55-protiv-gpt-6-astra/assets/oblozhka.webp'))
    metadata = {'reference': reference_key, 'reference_sha256': sha(reference),
        'source_revision': REV, 'size': [1600, 840], 'right_box': [880, 0, 1600, 840],
        'fonts': {'title': 'Unbounded 700 96', 'subtitle': 'Spectral 400 42',
                  'section': 'JetBrains Mono 500 28', 'site': 'JetBrains Mono 400 30'},
        'tracking': {'section': 2.5, 'site': 0, 'title': 0, 'subtitle': 0},
        'palette': canon.PALETTE, 'covers': []}
    inventory = {}
    for slug, title, subtitle in ITEMS:
        key = f'claude-ai/{slug}/assets/oblozhka.webp'
        original = Image.open(io.BytesIO(blob(REV, key))).convert('RGB')
        base = Image.new('RGB', original.size, canon.PALETTE['dark'])
        base.paste(original.crop((880, 0, 1600, 840)), (880, 0))
        prepared = OUT / 'prepared.png'
        base.save(prepared)
        cover, _, meta = canon.render('CHATGPT', title, title.splitlines()[0],
            subtitle, scene=prepared, fonts=FONTS, title_size=96, prepared=True)
        right = original.crop((880, 0, 1600, 840)).tobytes()
        assert cover.crop((880, 0, 1600, 840)).tobytes() == right
        assert meta['subtitle_box'][2] < 880
        dest = ROOT / key
        cover.save(dest, 'WEBP', lossless=True, method=6)
        assert Image.open(dest).convert('RGB').crop((880, 0, 1600, 840)).tobytes() == right
        registry[slug]['sha256'] = sha(dest.read_bytes())
        assert registry[slug]['subtitle'] == subtitle
        meta.update(slug=slug, right_pixels_sha256=sha(right),
                    right_pixels_identical=True, sha256=registry[slug]['sha256'])
        metadata['covers'].append(meta)
        inventory[key] = {'article': True, 'cover': True,
                          'pages': [f'claude-ai/{slug}/index.html']}
        print('PASS unchanged right pixels:', slug)
    # Use the site's normal image generator, restricted to this task's seven files.
    opt.inventory = lambda: inventory
    generated = opt.generate()
    manifest['images'].update(generated['images'])
    opt.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    opt.apply_articles()
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'layout.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    label_font = canon.font('mono', 17, FONTS, 'Medium')
    sheet = Image.new('RGB', (2280, 245), '#F8F7F2')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), 'ЧЕТЫРЕ: образец / 7 новых обложек, карточки 265 px',
              font=label_font, fill='#102F30')
    sources = [(OUT / 'chetyre-reference.webp', 'ЧЕТЫРЕ: образец')]
    sources += [(ROOT / f'claude-ai/{slug}/assets/oblozhka.reading-480.webp',
                 title.replace('\n', ' ')) for slug, title, _ in ITEMS]
    for i, (path, label) in enumerate(sources):
        x = 16 + i * 283
        card = Image.open(path).convert('RGB').resize((265, 139), Image.Resampling.LANCZOS)
        sheet.paste(card, (x, 48))
        draw.text((x, 196), label, font=label_font, fill='#102F30')
    sheet.save(OUT / 'LIST-v2.png')
    DELIVERY.mkdir(parents=True, exist_ok=True)
    (DELIVERY / 'LIST-v2.png').write_bytes((OUT / 'LIST-v2.png').read_bytes())
    print('PASS LIST-v2.png: accepted reference + 7 new covers')


if __name__ == '__main__':
    main()
