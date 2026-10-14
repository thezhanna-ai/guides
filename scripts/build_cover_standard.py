#!/usr/bin/env python3
"""Общий layout ЧЕТЫРЕ; только существующие пробы и иллюстрации.

python3.12 scripts/build_cover_standard.py
Pillow нужен только для сборки. Сцены берутся из BASE.
Серия со стикером устанавливается из готовых PNG и не пересобирается здесь.
"""
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tasks/content/2026-10-12-oblozhki-standart'
BASE = 'a059df2e01d424be6922cb59c4c4e078a2579daa'
STANDARD = 'pronovoe-cover-v1'
BACKGROUND = '#102F30'
FONTS = {
    'title': {'family': 'Unbounded', 'weight': 700, 'size': 96},
    'section': {'family': 'JetBrains Mono', 'weight': 500, 'size': 28},
    'subtitle': {'family': 'Spectral', 'weight': 400, 'size': 64},
    'site': {'family': 'JetBrains Mono', 'weight': 400, 'size': 30},
}
# Готовые обложки каруселей защищены от стандартной пересборки
STICKER_SLUGS = frozenset({
    'promty-sveta-dlya-foto-chatgpt', 'promty-tovar-reklama-chatgpt',
    'promty-blog-biznes-chatgpt', 'promty-risunok-zhivopis-chatgpt',
    'promty-igrushki-personazhi-chatgpt', 'promty-eda-dom-chatgpt',
    'promty-retro-ustroystvo-chatgpt',
})
OTHER = [
    ('raspisanie-zadach-v-claude', 'CLAUDE · ЧАТ', 'Задачи по\nрасписанию', 'План недели готов к 7:30'),
    ('zagruzka-faylov-v-claude', 'CLAUDE · ЧАТ', 'Загрузка\nфайлов', 'Один файл или целая пачка'),
    ('opus-55-protiv-gpt-6-astra', 'Claude Code · Codex', 'Opus\nпротив Astra', 'Один промпт, два видео'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def original(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_layout(meta):
    slug = meta['slug']
    if meta['fonts'] != FONTS:
        raise ValueError(f'{slug}: шрифты или кегли отличаются от канона')
    if meta['background'] != BACKGROUND:
        raise ValueError(f'{slug}: фон отличается от ЧЕТЫРЕ')


def font(kind, size=None):
    from PIL import ImageFont
    name = {'title': 'Unbounded-VF.ttf', 'subtitle': 'Spectral-Regular.ttf',
            'section': 'JetBrainsMono-VF.ttf', 'site': 'JetBrainsMono-VF.ttf'}[kind]
    face = ImageFont.truetype(str(ROOT / 'scripts/cover-fonts' / name),
                              size or FONTS[kind]['size'], layout_engine=ImageFont.Layout.BASIC)
    if kind != 'subtitle':
        face.set_variation_by_name({'title': 'Bold', 'section': 'Medium', 'site': 'Regular'}[kind])
    return face


def tracked(draw, xy, text, face, color, tracking):
    x, y = xy
    baseline = y - face.getbbox(text, anchor='ls')[1]
    for char in text:
        draw.text((x, baseline), char, font=face, fill=color, anchor='ls')
        x += face.getlength(char) + tracking


def source(meta, path, crop=None):
    from PIL import Image
    data = original(path)
    im = Image.open(io.BytesIO(data)).convert('RGB')
    item = {'path': path, 'revision': BASE, 'sha256': sha(data), 'size': list(im.size)}
    if crop:
        item['crop'] = crop
        im = im.crop(crop)
    meta['sources'].append(item)
    return im


def render(slug, section, title, subtitle):
    if slug in STICKER_SLUGS:
        raise ValueError(f'{slug}: готовый стикер нельзя пересобирать стандартным layout')
    from PIL import Image, ImageDraw
    canvas = Image.new('RGB', (1600, 840), BACKGROUND)
    meta = {'standard': STANDARD, 'slug': slug, 'size': [1600, 840],
            'section': section, 'title': title, 'subtitle': subtitle,
            'fonts': FONTS, 'background': BACKGROUND,
            'title_size': 96, 'title_origins': [[128, 270], [128, 388]],
            'subtitle_origin': [128, 563], 'sources': [], 'pair': None}
    assets = f'claude-ai/{slug}/assets/'
    # Сцена без заголовков. Плавное соединение иллюстрации и однотонного полотна.
    im = source(meta, assets+'oblozhka-scena.webp', [700, 0, 1600, 840])
    mask = Image.new('L', im.size, 255)
    md = ImageDraw.Draw(mask)
    for x in range(180):
        md.line((x, 0, x, 839), fill=round(255*x/179))
    canvas.paste(im, (700, 0), mask)
    meta['scene_box'] = [700, 0, 1600, 840]
    meta['scene_feather_px'] = 180
    # Общая левая вёрстка поверх одиночной сцены
    furniture = Image.new('RGBA', canvas.size)
    d = ImageDraw.Draw(furniture)
    label = section.upper()
    mf = font('section')
    label_width = sum(mf.getlength(c)+2.5 for c in label)-2.5
    d.rounded_rectangle((104, 106, 152+label_width, 162), radius=28,
                        fill=(232,111,74,15), outline=(232,111,74,105), width=1)
    d.line((104, 716, 781, 716), fill=(187,199,202,51), width=1)
    canvas = Image.alpha_composite(canvas.convert('RGBA'), furniture).convert('RGB')
    d = ImageDraw.Draw(canvas)
    tracked(d, (128, 121), label, mf, '#E2E8E9', 2.5)
    tf = font('title')
    meta['title_boxes'] = []
    for i, line in enumerate(title.splitlines()):
        xy = (128, 270+118*i)
        d.text(xy, line, font=tf, fill='#E86F4A' if i == 0 else '#F8F7F2', anchor='lt')
        meta['title_boxes'].append(list(d.textbbox(xy, line, font=tf, anchor='lt')))
    d.rectangle((104, 268, 108, max(b[3] for b in meta['title_boxes'])+10), fill='#E86F4A')
    sf = font('subtitle')
    subtitle_lines = [subtitle]
    if sf.getlength(subtitle) > 740:
        words = subtitle.split()
        candidates = [[' '.join(words[:i]), ' '.join(words[i:])] for i in range(1, len(words))]
        if not candidates:
            raise ValueError('Подзаголовок не помещается без уменьшения кегля')
        subtitle_lines = min(candidates, key=lambda lines: max(sf.getlength(line) for line in lines))
    if max(sf.getlength(line) for line in subtitle_lines) > 740:
        raise ValueError('Подзаголовок не помещается в две строки при кегле 64')
    meta['subtitle_lines'] = subtitle_lines
    meta['subtitle_size'] = 64
    meta['subtitle_boxes'] = []
    for i, line in enumerate(subtitle_lines):
        xy = (128, 563 + i * 70)
        d.text(xy, line, font=sf, fill='#BBC7CA', anchor='lt')
        meta['subtitle_boxes'].append(list(d.textbbox(xy, line, font=sf, anchor='lt')))
    d.ellipse((105, 754, 115, 764), fill='#E86F4A')
    tracked(d, (132, 743), 'pronovoe.com', font('site'), '#BBC7CA', 0)
    validate_layout(meta)
    return canvas, meta


def main():
    # Legacy BASE predates approved scene changes. Never overwrite published
    # covers by replaying that old composition after a typography-only update.
    if (ROOT / 'data/cover-readability.json').exists():
        raise SystemExit('Защита текущих обложек: массовая пересборка из старого BASE запрещена. Используйте текущий оригинал и сохраните пиксели вне области текста.')
    import optimize_reading_images as opt
    OUT.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT/'data/OBLOZHKI.json').read_text())
    old_manifest = json.loads(opt.MANIFEST.read_text())
    inventory = {}
    for slug, section, title, subtitle in OTHER:
        image, meta = render(slug, section, title, subtitle)
        install(slug, image, meta, registry, inventory)
    # Штатный генератор обрабатывает только три стандартные обложки
    opt.inventory = lambda: inventory
    opt.TEXT_PATHS.update(inventory)  # lossless: метки и число должны сохраниться
    generated = opt.generate()
    old_manifest['images'].update(generated['images'])
    opt.MANIFEST.write_text(json.dumps(old_manifest, ensure_ascii=False, indent=2)+'\n')
    opt.apply_articles()
    write_json(ROOT/'data/OBLOZHKI.json', registry)
    subprocess.run(['python3.14', str(ROOT/'scripts/sobrat_glavnuyu.py')], cwd=ROOT, check=True)


def install(slug, image, meta, registry, inventory):
    if slug in STICKER_SLUGS:
        raise ValueError(f'{slug}: готовый стикер нельзя перезаписывать стандартной обложкой')
    key = registry[slug]['image']
    dest = ROOT/key
    image.save(dest, 'WEBP', lossless=True, method=6)
    meta['image_sha256'] = sha(dest.read_bytes())
    layout = dest.with_name('oblozhka-layout.json')
    write_json(layout, meta)
    registry[slug].update(subtitle=meta['subtitle'], sha256=meta['image_sha256'],
                          layout=layout.relative_to(ROOT).as_posix())
    inventory[key] = {'article': True, 'cover': True, 'pages': [f'claude-ai/{slug}/index.html']}
    print('Собрана:', slug, '96 / 28 / 64 / 30, фон', BACKGROUND)


if __name__ == '__main__':
    main()
