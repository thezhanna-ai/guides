#!/usr/bin/env python3
"""Общий layout ЧЕТЫРЕ; только существующие пробы и иллюстрации.

python3.12 scripts/build_cover_standard.py
Pillow нужен только для сборки. Игрушка А устанавливается в локальную ветку,
Б сохраняется рядом для выбора. Все исходники зафиксированы на BASE.
"""
import hashlib
import html
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tasks/content/2026-10-12-oblozhki-standart'
BASE = 'a059df2e01d424be6922cb59c4c4e078a2579daa'
STANDARD = 'pronovoe-cover-v1'
BACKGROUND = '#102F30'
FONTS = {
    'title': {'family': 'Unbounded', 'weight': 700, 'size': 96},
    'section': {'family': 'JetBrains Mono', 'weight': 500, 'size': 28},
    'subtitle': {'family': 'Spectral', 'weight': 400, 'size': 42},
    'site': {'family': 'JetBrains Mono', 'weight': 400, 'size': 30},
}
PAIR = {'frames': [[884, 260, 1184, 560], [1244, 260, 1544, 560]],
        'label_centers': [1034, 1394], 'label_baselines': [630, 630],
        'label_font': {'family': 'JetBrains Mono', 'weight': 400, 'size': 42},
        'border': {'width': 3, 'color': '#BBC7CA'}, 'fit': 'contain'}
SERIES = [
    ('promty-sveta-dlya-foto-chatgpt', 48, 'Свет и камера'),
    ('promty-tovar-reklama-chatgpt', 72, 'Товар и реклама'),
    ('promty-blog-biznes-chatgpt', 72, 'Постеры и соцсети'),
    ('promty-risunok-zhivopis-chatgpt', 72, 'Фото в живопись'),
    ('promty-igrushki-personazhi-chatgpt', 72, 'Фото в игрушку'),
    ('promty-eda-dom-chatgpt', 48, 'Еда и дом'),
    ('promty-retro-ustroystvo-chatgpt', 48, 'Ретро и устройство'),
]
PROBES = [1, 3, 1, 1, 2, 3, 3]
OTHER = [
    ('raspisanie-zadach-v-claude', 'Кнопка за кнопкой', 'Задачи по\nрасписанию', 'План недели готов к 7:30'),
    ('zagruzka-faylov-v-claude', 'Кнопка за кнопкой', 'Загрузка\nфайлов', 'Один файл или целая пачка'),
    ('opus-55-protiv-gpt-6-astra', 'Claude Code · Codex', 'Opus\nпротив Astra', 'Один промпт, два видео'),
    ('konspekt-rechi-v-chatgpt', 'CHATGPT', 'Пять\nконспектов', 'Как запомнить длинный текст?'),
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
    if meta.get('pair') is not None and meta['pair'] != PAIR:
        raise ValueError(f'{slug}: рамки или базовая линия было/стало отличаются от серии')


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


def render(slug, section, title, subtitle, probe=None):
    from PIL import Image, ImageDraw, ImageOps
    canvas = Image.new('RGB', (1600, 840), BACKGROUND)
    meta = {'standard': STANDARD, 'slug': slug, 'size': [1600, 840],
            'section': section, 'title': title, 'subtitle': subtitle,
            'fonts': FONTS, 'background': BACKGROUND,
            'title_size': 96, 'title_origins': [[128, 270], [128, 388]],
            'subtitle_origin': [128, 563], 'sources': [], 'pair': None}
    assets = f'claude-ai/{slug}/assets/'
    if probe:
        meta['pair'] = PAIR
        for index, state in enumerate(('do', 'posle')):
            im = source(meta, assets + f'proba-{probe}-{state}.webp')
            box = PAIR['frames'][index]
            # Целое фото внутри одинаковой рамки: без обрезки ног, лица или надписей.
            fitted = ImageOps.contain(im, (294, 294), Image.Resampling.LANCZOS)
            canvas.paste(fitted, (box[0]+(300-fitted.width)//2, box[1]+(300-fitted.height)//2))
        d = ImageDraw.Draw(canvas)
        for box in PAIR['frames']:
            d.rectangle((box[0], box[1], box[2]-1, box[3]-1), outline='#BBC7CA', width=3)
        for i, label in enumerate(('было', 'стало')):
            d.text((PAIR['label_centers'][i], 630), label, font=font('site', 42), fill='#F8F7F2', anchor='ms')
        d.line((1196, 410, 1230, 410), fill='#E86F4A', width=4)
        d.line((1218, 398, 1230, 410, 1218, 422), fill='#E86F4A', width=4)
    elif slug == 'konspekt-rechi-v-chatgpt':
        im = source(meta, assets+'oblozhka-v4.webp', [760, 150, 1600, 760])
        im = ImageOps.contain(im, (740, 640), Image.Resampling.LANCZOS)
        canvas.paste(im, (840, 170))
        meta['scene_box'] = [840, 170, 840+im.width, 170+im.height]
    else:
        # Сцена без заголовков. Плавное соединение иллюстрации и однотонного полотна.
        im = source(meta, assets+'oblozhka-scena.webp', [700, 0, 1600, 840])
        mask = Image.new('L', im.size, 255)
        md = ImageDraw.Draw(mask)
        for x in range(180):
            md.line((x, 0, x, 839), fill=round(255*x/179))
        canvas.paste(im, (700, 0), mask)
        meta['scene_box'] = [700, 0, 1600, 840]
        meta['scene_feather_px'] = 180
    # Единственная левая вёрстка, после иллюстрации: длинный заголовок может налезать.
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
    d.text((128, 563), subtitle, font=font('subtitle'), fill='#BBC7CA', anchor='lt')
    d.ellipse((105, 754, 115, 764), fill='#E86F4A')
    tracked(d, (132, 743), 'pronovoe.com', font('site'), '#BBC7CA', 0)
    validate_layout(meta)
    return canvas, meta


def main():
    import optimize_reading_images as opt
    OUT.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT/'data/OBLOZHKI.json').read_text())
    old_manifest = json.loads(opt.MANIFEST.read_text())
    inventory = {}
    for (slug, count, subtitle), probe in zip(SERIES, PROBES):
        title = f'{count} ' + ('промптов' if count == 48 else 'промпта') + '\nдля фото'
        toy = slug == SERIES[4][0]
        image, meta = render(slug, 'CHATGPT', title, subtitle, probe)
        if toy:
            alt, altmeta = render(slug, 'CHATGPT', title, subtitle, 3)
            alt.save(OUT/'IGRUSHKA-B.webp', 'WEBP', lossless=True, method=6)
            altmeta['image_sha256'] = sha((OUT/'IGRUSHKA-B.webp').read_bytes())
            write_json(OUT/'IGRUSHKA-B-layout.json', altmeta)
            registry[slug]['alt'] = 'Девушка на роликах и её фигурка CHIBI: проба 2'
            registry[slug]['source_alt'] = registry[slug]['alt']
        install(slug, image, meta, registry, inventory)
    for slug, section, title, subtitle in OTHER:
        image, meta = render(slug, section, title, subtitle)
        install(slug, image, meta, registry, inventory)
    # Ограничиваем штатный генератор только 11 обложками. Остальные изображения неизменны.
    opt.inventory = lambda: inventory
    opt.TEXT_PATHS.update(inventory)  # lossless: метки и число должны сохраниться
    generated = opt.generate()
    old_manifest['images'].update(generated['images'])
    opt.MANIFEST.write_text(json.dumps(old_manifest, ensure_ascii=False, indent=2)+'\n')
    opt.apply_articles()
    write_json(ROOT/'data/OBLOZHKI.json', registry)
    # Подпись и alt должны описывать новую, разрешённую пару ИГРУШКИ.
    articles_path = ROOT/'data/statyi.json'
    articles = json.loads(articles_path.read_text())
    toy_slug = SERIES[4][0]
    for article in articles['statyi']:
        if article['slug'] == toy_slug:
            article['podpis'] = registry[toy_slug]['alt']
    articles_path.write_text(json.dumps(articles, ensure_ascii=False, indent=1)+'\n')
    page = ROOT/f'claude-ai/{toy_slug}/index.html'
    content = page.read_text()
    alt_text = html.escape(registry[toy_slug]['alt'], quote=True)
    content = re.sub(r'(<figure\b[^>]*class="cover cover-v2"[^>]*>\s*<img\b[^>]*\balt=")[^"]*(")',
                     lambda m: m[1]+alt_text+m[2], content, count=1)
    content = re.sub(r'(<meta\b[^>]*property="og:image:alt"[^>]*content=")[^"]*(")',
                     lambda m: m[1]+alt_text+m[2], content, count=1)
    page.write_text(content)
    subprocess.run(['python3.14', str(ROOT/'scripts/sobrat_glavnuyu.py')], cwd=ROOT, check=True)


def install(slug, image, meta, registry, inventory):
    key = registry[slug]['image']
    dest = ROOT/key
    image.save(dest, 'WEBP', lossless=True, method=6)
    meta['image_sha256'] = sha(dest.read_bytes())
    layout = dest.with_name('oblozhka-layout.json')
    write_json(layout, meta)
    registry[slug].update(subtitle=meta['subtitle'], sha256=meta['image_sha256'],
                          layout=layout.relative_to(ROOT).as_posix())
    inventory[key] = {'article': True, 'cover': True, 'pages': [f'claude-ai/{slug}/index.html']}
    print('Собрана:', slug, '96 / 28 / 42 / 30, фон', BACKGROUND)


if __name__ == '__main__':
    main()
