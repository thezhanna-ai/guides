#!/usr/bin/env python3
"""Prepared-scene v2 typography; live Chetyre sizes and baseline positions.
Adapted from the accepted local cover template; Pillow only.
"""
import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
SIZE = (1600, 840)
PALETTE = dict(dark='#102F30', accent='#E86F4A', light='#F8F7F2',
               info='#E2E8E9', muted='#BBC7CA')


def font(family, size, fonts=None, weight=None):
    path = Path(fonts or ROOT.parent / 'fonts') / {
        'title': 'Unbounded-VF.ttf', 'subtitle': 'Spectral-Regular.ttf',
        'light': 'Spectral-Light.ttf', 'mono': 'JetBrainsMono-VF.ttf',
    }[family]
    face = ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.BASIC)
    if weight:
        face.set_variation_by_name(weight)
    return face


def validate_text(section, title, accent, subtitle):
    fields = (section, title, accent, subtitle)
    if any(not isinstance(t, str) or not t.strip() for t in fields):
        raise ValueError('Раздел, заголовок, акцент и подзаголовок должны быть заполнены')
    if any(len(t) > 180 for t in fields):
        raise ValueError('Слишком длинный текст для обложки')
    if '\n' in section or '\n' in subtitle:
        raise ValueError('Раздел и подзаголовок должны занимать одну строку')
    words = title.split()
    if not 2 <= len(words) <= 4:
        raise ValueError('В заголовке должно быть 2-4 слова')
    if len(accent.split()) != 1 or words.count(accent) != 1:
        raise ValueError('Акцент должен точно совпадать с одним словом заголовка')
    if title.isupper():
        raise ValueError('Заголовок должен быть в обычном регистре')


def tracked(draw, xy, text, face, fill, tracking=3):
    x, y = xy
    # У всех символов одна базовая линия: точка остаётся внизу строки.
    baseline = y-face.getbbox(text, anchor='ls')[1]
    for char in text:
        draw.text((x, baseline), char, font=face, fill=fill, anchor='ls')
        x += face.getlength(char)+tracking
    return x


def layout_title(title, face, width):
    if '\n' in title:
        lines = title.split('\n')
    else:
        lines, current = [], ''
        for word in title.split():
            candidate = (current+' '+word).strip()
            if current and face.getlength(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    if not 1 <= len(lines) <= 3 or any(not line.strip() for line in lines):
        raise ValueError('Нужны 1-3 непустые строки; перенос задаётся символом \\n')
    if any(face.getlength(line) > width for line in lines):
        raise ValueError('Заголовок не помещается; уменьшите --title-size или задайте перенос')
    return lines


def render(section, title, accent, subtitle, scene=None, fonts=None,
           title_size=96, title_width=770, symbol='§', prepared=False):
    validate_text(section, title, accent, subtitle)
    if prepared:
        with Image.open(scene) as src:
            if src.size != SIZE:
                raise ValueError(f'Подготовленная сцена должна иметь размер {SIZE}')
            base = src.convert('RGB')
    else:
        raise ValueError('Only an existing prepared scene is allowed')
    cover = base.convert('RGBA')
    typo = scene is None
    title_size = 128 if typo and title_size == 96 else title_size
    title_width = 1220 if typo and title_width == 770 else title_width
    tf = font('title', title_size, fonts, 'Bold')
    sf = font('subtitle', 42, fonts)
    mf = font('mono', 28, fonts, 'Medium')
    ff = font('mono', 30, fonts, 'Regular')
    lines = layout_title(title, tf, title_width)
    if sf.getlength(subtitle) > 790:
        raise ValueError('Однострочный подзаголовок не помещается в безопасную зону')
    if typo:
        decoration = Image.new('RGBA', SIZE)
        ImageDraw.Draw(decoration).text((1260, 315), symbol,
            font=font('subtitle', 340, fonts), fill=(232, 111, 74, 34), anchor='lt')
        cover = Image.alpha_composite(cover, decoration)
    x = 128
    label = section.upper()
    label_width = sum(mf.getlength(c)+2.5 for c in label)-2.5
    if label_width > 740:
        raise ValueError('Название раздела слишком длинное')
    furniture = Image.new('RGBA', SIZE)
    fd = ImageDraw.Draw(furniture)
    fd.rounded_rectangle((104, 106, 152+label_width, 162), radius=28,
                        fill=(232, 111, 74, 15), outline=(232, 111, 74, 105), width=1)
    fd.line((104, 716, 781 if not typo else 1496, 716),
            fill=(187, 199, 202, 51), width=1)
    cover = Image.alpha_composite(cover, furniture)
    d = ImageDraw.Draw(cover)
    tracked(d, (128, 121), label, mf, PALETTE['info'], 2.5)
    top = 270 if not typo else 240
    step = 118 if title_size == 96 else round(title_size*1.25)
    title_boxes = []
    for i, line in enumerate(lines):
        yy = top+i*step
        if accent in line.split():
            match = re.search(r'(?<!\S)'+re.escape(accent)+r'(?!\S)', line)
            before, after = line[:match.start()], line[match.end():]
            d.text((x, yy), before, font=tf, fill=PALETTE['light'], anchor='lt')
            ax = x+tf.getlength(before)
            d.text((ax, yy), accent, font=tf, fill=PALETTE['accent'], anchor='lt')
            d.text((ax+tf.getlength(accent), yy), after, font=tf,
                   fill=PALETTE['light'], anchor='lt')
        else:
            d.text((x, yy), line, font=tf, fill=PALETTE['light'], anchor='lt')
        title_boxes.append(list(d.textbbox((x, yy), line, font=tf, anchor='lt')))
    title_end = max(box[3] for box in title_boxes)
    d.rectangle((104, top-2, 108, title_end+10), fill=PALETTE['accent'])
    sub_y = max(563, title_end+50)
    if sub_y > 646:
        raise ValueError('Заголовок пересекает подзаголовок и подвал')
    d.text((128, sub_y), subtitle, font=sf, fill=PALETTE['muted'], anchor='lt')
    d.ellipse((105, 754, 115, 764), fill=PALETTE['accent'])
    tracked(d, (132, 743), 'pronovoe.com', ff, PALETTE['muted'], 0)
    metadata = dict(size=list(SIZE), section=section, title=title,
        accent=accent, subtitle=subtitle, title_size=title_size,
        title_boxes=title_boxes, subtitle_box=list(d.textbbox((128, sub_y), subtitle,
        font=sf, anchor='lt')), mobile_title_px=round(title_size*390/SIZE[0], 2),
        mobile_subtitle_px=round(42*390/SIZE[0], 2),
        mobile_section_px=round(28*390/SIZE[0], 2),
        mobile_footer_px=round(30*390/SIZE[0], 2), typographic=typo)
    return cover.convert('RGB'), base, metadata
