#!/usr/bin/env python3
"""Общий layout ЧЕТЫРЕ; только существующие пробы и иллюстрации.

python3.12 scripts/build_cover_standard.py
Pillow нужен только для сборки. Источники серии закреплены в carousel-selection.json
побайтовыми копиями и SHA-256; прочие сцены берутся из BASE.
"""
import hashlib
import html
import io
import json
import math
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
# Дробные координаты сохраняют равные рамки и точные поля 40/48 px
PAIR = {'frames': [[973, 256+1/3, 1242.5, 615+2/3],
                   [1282.5, 256+1/3, 1552, 615+2/3]],
        'label_centers': [1107.75, 1417.25], 'label_baselines': [672, 672],
        'label_font': {'family': 'JetBrains Mono', 'weight': 400, 'size': 42},
        'border': {'width': 3, 'color': '#BBC7CA'}, 'fit': 'fit'}
CROP_CENTERS = {
    'promty-igrushki-personazhi-chatgpt': [[0.5, 0.5], [0.5, 0.65]],
    'promty-retro-ustroystvo-chatgpt': [[0.5, 0.5], [0.5, 0.5]],
}
SERIES = [
    ('promty-sveta-dlya-foto-chatgpt', 48, 'Свет и камера'),
    ('promty-tovar-reklama-chatgpt', 72, 'Товар и реклама'),
    ('promty-blog-biznes-chatgpt', 72, 'Постеры и соцсети'),
    ('promty-risunok-zhivopis-chatgpt', 72, 'Фото в живопись'),
    ('promty-igrushki-personazhi-chatgpt', 72, 'Фото в игрушку'),
    ('promty-eda-dom-chatgpt', 48, 'Еда и дом'),
    ('promty-retro-ustroystvo-chatgpt', 48, 'Ретро и устройство'),
]
PROBES = [1, 3, 1, 1, 2, 3, 3]  # Резерв только для slide-01 без фотографии
SELECTION = OUT / 'carousel-selection.json'
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
    if meta.get('pair') is not None:
        if meta['pair'] != PAIR:
            raise ValueError(f'{slug}: рамки или базовая линия было/стало отличаются от серии')
        if max(box[2] for box in meta['title_boxes']) >= PAIR['frames'][0][0]:
            raise ValueError(f'{slug}: заголовок заходит на рамки серии')


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


def selected_source(meta, item):
    from PIL import Image
    data = (ROOT / item['path']).read_bytes()
    if sha(data) != item['sha256']:
        raise ValueError(f"{meta['slug']}: исходник не совпадает с выбранным SHA-256")
    im = Image.open(io.BytesIO(data)).convert('RGB')
    meta['sources'].append(dict(item, revision='workspace-copy', size=list(im.size)))
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
        meta['crop_centers'] = CROP_CENTERS.get(slug, [[0.5, 0.5], [0.5, 0.5]])
        # Только фото и рамки в масштабе 6: половины и трети пикселя точны
        scale = 6
        left = PAIR['frames'][0][0]
        top = int(PAIR['frames'][0][1])
        pair_size = (PAIR['frames'][1][2]-left, math.ceil(PAIR['frames'][0][3])-top)
        pair_canvas = Image.new('RGB', tuple(n*scale for n in pair_size), BACKGROUND)
        selection = json.loads(SELECTION.read_text())['covers']
        row = next(item for item in selection if item['slug'] == slug)
        meta['carousel'] = row['carousel']
        meta['selection_status'] = row['status']
        for index, state in enumerate(('do', 'posle')):
            im = (selected_source(meta, row['sources'][index]) if row['sources']
                  else source(meta, assets + f'proba-{probe}-{state}.webp'))
            box = PAIR['frames'][index]
            size = tuple(round((box[i+2]-box[i])*scale) for i in (0, 1))
            fitted = ImageOps.fit(im, size, Image.Resampling.LANCZOS,
                                  centering=tuple(meta['crop_centers'][index]))
            xy = (round((box[0]-left)*scale), round((box[1]-top)*scale))
            pair_canvas.paste(fitted, xy)
            ImageDraw.Draw(pair_canvas).rectangle(
                (*xy, xy[0]+size[0]-1, xy[1]+size[1]-1),
                outline=PAIR['border']['color'], width=PAIR['border']['width']*scale)
        canvas.paste(pair_canvas.resize(pair_size, Image.Resampling.LANCZOS), (left, top))
        d = ImageDraw.Draw(canvas)
        for i, label in enumerate(('было', 'стало')):
            d.text((PAIR['label_centers'][i], PAIR['label_baselines'][i]), label,
                   font=font('site', PAIR['label_font']['size']), fill='#F8F7F2', anchor='ms')
        arrow_x = (PAIR['frames'][0][2]+PAIR['frames'][1][0])/2
        arrow_y = (PAIR['frames'][0][1]+PAIR['frames'][0][3])/2
        d.line((arrow_x-12, arrow_y, arrow_x+12, arrow_y), fill='#E86F4A', width=4)
        d.line((arrow_x+2, arrow_y-10, arrow_x+12, arrow_y, arrow_x+2, arrow_y+10),
               fill='#E86F4A', width=4)
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
    # Общая левая вёрстка. Наложение допустимо только на одиночную сцену, не на пару.
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
        image, meta = render(slug, 'CHATGPT', title, subtitle, probe)
        if slug == SERIES[3][0]:
            registry[slug]['alt'] = 'Портрет до и после превращения в вышитую тканевую нашивку'
        if slug == SERIES[4][0]:
            registry[slug]['alt'] = 'Девушка на роликах и фигурка Roller Girl в блистере'
            registry[slug]['source_alt'] = registry[slug]['alt']
        install(slug, image, meta, registry, inventory)
    for slug, section, title, subtitle in OTHER:
        image, meta = render(slug, section, title, subtitle)
        install(slug, image, meta, registry, inventory)
    # Ограничиваем штатный генератор только 10 обложками. Остальные изображения неизменны.
    opt.inventory = lambda: inventory
    opt.TEXT_PATHS.update(inventory)  # lossless: метки и число должны сохраниться
    generated = opt.generate()
    old_manifest['images'].update(generated['images'])
    opt.MANIFEST.write_text(json.dumps(old_manifest, ensure_ascii=False, indent=2)+'\n')
    opt.apply_articles()
    write_json(ROOT/'data/OBLOZHKI.json', registry)
    # Подписи, alt и OG описывают выбранную обложку, текст статьи сохранён.
    articles_path = ROOT/'data/statyi.json'
    articles = json.loads(articles_path.read_text())
    series_slugs = {item[0] for item in SERIES}
    for article in articles['statyi']:
        if article['slug'] in series_slugs:
            article['podpis'] = registry[article['slug']]['alt']
    articles_path.write_text(json.dumps(articles, ensure_ascii=False, indent=1)+'\n')
    for slug in series_slugs:
        page = ROOT/f'claude-ai/{slug}/index.html'
        content = page.read_text()
        alt_text = html.escape(registry[slug]['alt'], quote=True)
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
