"""Замеры исходной базы и лист из настоящего HTML карточек главной."""
from pathlib import Path
import sys, json, re, io, base64, hashlib
from collections import Counter
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
import build_cover_standard as build
OUT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
STYLE = WORKSPACE/'tasks/content/2026-10-03-oformlenie-sayta'
registry = json.loads(build.original('data/OBLOZHKI.json'))
series = {x[0] for x in build.SERIES}
changed = [x[0] for x in build.SERIES]+[x[0] for x in build.OTHER]
extra = {
 'svoy-server-dlya-claude': STYLE/'rossiya-dve/svoy-server-layout.json',
 'otozvat-ssylku-na-chat-claude': WORKSPACE/'tasks/content/2026-09-26-stati-10/illustrations-2026-10-05/otozvat-ssylku-na-chat-claude/oblozhka-layout.json',
 'pyat-skillov-claude-code': WORKSPACE/'tasks/content/2026-10-03-avatary-do-sbrosa/07-skilly/oblozhka/oblozhka-layout.json',
 'chatgpt-composio-prilozheniya': ROOT/'audits/statya-svyaz-20261006/oblozhka-layout.json',
 'uley-agentov-ruflo': WORKSPACE/'.worktrees/statya-uley/audits/statya-uley-20261006/oblozhka-layout.json',
 'pyat-instrumentov-dlya-sayta': STYLE/'shablon-v2/podzag/pyat-instrumentov-sayt-claude-codex-layout.json',
}
unknown_titles={'montazh-video-claude-code-codex':'Монтаж\nнейросетью', 'zakryt-sekrety-ot-claude-code':'Секретные\nфайлы'}
rows=[]
for slug, item in registry.items():
    data = build.original(item['image'])
    im=Image.open(io.BytesIO(data)).convert('RGB')
    patches=[im.crop(box) for box in [(0,0,40,80),(0,360,40,440),(0,760,40,840)]]
    colors=Counter(p for patch in patches for p in patch.get_flattened_data())
    bg=colors.most_common(1)[0][0]
    hexbg='#'+''.join(f'{n:02X}' for n in bg)
    ranges=[[min(p[c] for p in colors),max(p[c] for p in colors)] for c in range(3)]
    flat=all(hi-lo<=2 for lo,hi in ranges)
    candidates=[]
    p=ROOT/f'claude-ai/{slug}/assets/oblozhka-layout.json'
    # Читаем layout именно базовой ревизии, не только что записанный новый.
    try:
        raw=__import__('subprocess').check_output(['git','show',build.BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT,stderr=__import__('subprocess').DEVNULL)
        candidates.append((p.relative_to(ROOT).as_posix(),json.loads(raw)))
    except Exception: pass
    if slug in series:
        q=json.loads(build.original('tasks/content/2026-10-11-oblozhki-serii-kanon/layout.json'))
        m=next(x for x in q['covers'] if x['slug']==slug)
        candidates.append(('tasks/content/2026-10-11-oblozhki-serii-kanon/layout.json',m))
    if slug in extra and extra[slug].exists():
        p=extra[slug];candidates.append((str(p.relative_to(WORKSPACE)),json.loads(p.read_text())))
    for dirname in ['podzag','chatgpt-pravka','vse']:
        p=STYLE/'shablon-v2'/dirname/(slug+'-layout.json')
        if p.exists(): candidates.append((str(p.relative_to(WORKSPACE)),json.loads(p.read_text())))
    # Сначала метаданные базовой обложки, далее layout с совпадающим подзаголовком.
    if candidates:
        path, meta=next((c for c in candidates if c[1].get('subtitle')==item['subtitle']),candidates[0])
        size=meta.get('title_size');title=meta['title'];method='layout: '+path
    else:
        size=None;title=unknown_titles.get(slug,'');method='измерение растра'
    # Реальная высота букв первой строки, без вертикальной черты слева.
    points=[]
    for y in range(240,351):
        for x in range(125,875):
            r,g,b=im.getpixel((x,y))
            if (r>165 and g>65 and r>g*1.4 and g>b*1.2) or (min(r,g,b)>175 and max(r,g,b)-min(r,g,b)<32):
                points.append((x,y))
    glyph_height=max(y for x,y in points)-min(y for x,y in points)+1 if points else None
    if size is None and title:
        # Без исходника это оценка по глифам, не точный размер из layout.
        line=title.splitlines()[0]
        observed=(max(x for x,y in points)-min(x for x,y in points)+1,glyph_height)
        def err(n):
            f=build.font('title',n);bb=f.getbbox(line,anchor='lt')
            return abs(bb[2]-bb[0]-observed[0])+2*abs(bb[3]-bb[1]-observed[1])
        size=min(range(60,141),key=err);method+='; ориентировочная оценка Unbounded по глифам'
    if slug == 'konspekt-rechi-v-chatgpt':
        pts=[(x,y) for y in range(180,320) for x in range(50,410) if (lambda c: c[0]>170 and c[0]>c[1]*1.4 and c[1]>c[2]*1.2)(im.getpixel((x,y)))]
        glyph_height=max(y for x,y in pts)-min(y for x,y in pts)+1
        method='растр: первая строка Пять, область [50,180,410,320], точный кегль неизвестен'
    if slug == 'stanford-kak-sozdayut-chatgpt':
        pts=[(x,y) for y in range(210,295) for x in range(200,770) if (lambda c: c[2]>90 and c[2]>c[0]*1.5 and c[2]>c[1]*1.5)(im.getpixel((x,y)))]
        glyph_height=max(y for x,y in pts)-min(y for x,y in pts)+1
        method='растр: первая строка Introduction to, область [200,210,770,295], точный кегль неизвестен'
    reasons=[]
    if size!=96: reasons.append('кегль '+(str(size) if size else 'вшитый текст, кегль из растра не восстанавливается'))
    if hexbg!='#102F30' or not flat: reasons.append('фон '+hexbg+(' неоднородный' if not flat else ''))
    if slug in series: reasons.append('заголовок без числа; старая геометрия пар')
    elif slug=='stanford-kak-sozdayut-chatgpt': reasons.append('готовый титульный слайд, другая гарнитура и шаблон')
    elif slug=='konspekt-rechi-v-chatgpt': reasons.append('сгенерированная сцена с вшитой типографикой')
    elif slug!='chetyre-mcp-claude-code' and slug!='otsenka-vneshnosti-po-foto-v-chatgpt': reasons.append('предыдущая версия левого layout')
    rows.append({'slug':slug,'image':item['image'],'sha256':hashlib.sha256(data).hexdigest(),'title_size':size,
                 'glyph_height_px':glyph_height,'method':method,'background_sample':hexbg,'background_ranges_rgb':ranges,
                 'background_flat':flat,'deviations':reasons,'changed':slug in changed})
build.write_json(OUT/'audit.json',{'base':build.BASE,'count':len(rows),'method':'Три фоновых участка 40x80 слева, мода RGB и диапазон. Кегль из layout; без него оценка по глифам, помечена отдельно. Текст внутри фото не считается фоном полотна.','#102F30':'Палитра сборщика ЧЕТЫРЕ; сама историческая сцена ЧЕТЫРЕ имеет градиент','covers':rows})
# Семь slide-01 рядом с актуальными карточками, без вариантов А/Б.
selection = json.loads((OUT/'carousel-selection.json').read_text())['covers']
current = json.loads((ROOT/'data/OBLOZHKI.json').read_text())
new = (ROOT/'index.html').read_text()
css = re.search(r'<style>(.*?)</style>', new, re.S)[1]
labels = ['СВЕТ', 'ВИТРИНА', 'АФИША', 'КИСТЬ', 'ИГРУШКА', 'КУХНЯ', 'РЕТРО']
page = ['<!doctype html><html lang="ru"><meta charset="utf-8"><title>Карусель и статья</title><style>'+css+
        'body{padding:20px}.comparison{display:grid;grid-template-columns:168px 264.5px;gap:24px;margin:26px 0}.carousel{width:168px;height:210px;object-fit:contain}.guide-link{pointer-events:none}h1{font-size:28px}</style><main><h1>Карусель и обложка статьи</h1><p>СВЕТ и ВИТРИНА: в slide-01 нет фото, сохранены прежние пары</p>']
canvas = Image.new('RGB', (1000, 1980), '#efece4')
draw = ImageDraw.Draw(canvas)
titlefont = build.font('section', 27)
smallfont = build.font('site', 18)
draw.text((30, 20), 'КАРУСЕЛЬ И ОБЛОЖКА СТАТЬИ', font=titlefont, fill='#102F30')
draw.text((30, 65), 'Slide-01 слева, обложка статьи справа. Полные фото без обрезки', font=smallfont, fill='#102F30')
for i, row in enumerate(selection):
    slug = row['slug']
    y = 115 + i*265
    draw.text((30, y), labels[i], font=titlefont, fill='#102F30')
    photo = Image.open(ROOT/row['carousel']['path']).convert('RGB').resize((168,210), Image.Resampling.LANCZOS)
    canvas.paste(photo, (30,y+42))
    cover = Image.open(ROOT/current[slug]['image']).convert('RGB').resize((400,210), Image.Resampling.LANCZOS)
    canvas.paste(cover, (225,y+42))
    draw.text((650,y+65), '1600 × 840', font=smallfont, fill='#102F30')
    if row['status'] == 'confirmed':
        draw.text((650,y+110), 'Та же фотография', font=smallfont, fill='#102F30')
        draw.text((650,y+140), 'на первом слайде', font=smallfont, fill='#102F30')
    else:
        for j,line in enumerate(['В slide-01 нет фото', 'Прежняя пара', 'сохранена']):
            draw.text((650,y+110+j*30), line, font=smallfont, fill='#984025')
    card = next(x for x in re.findall(r'<a\b[^>]*class="guide-link[^>]*>.*?</a>',new,re.S) if f'href="claude-ai/{slug}/"' in x)
    card = re.sub(r'\s(?:srcset|sizes|data-full-src)="[^"]*"', '', card)
    card = re.sub(r'src="[^"]*"', lambda m:'src="data:image/webp;base64,'+base64.b64encode((ROOT/current[slug]['image']).read_bytes()).decode()+'"',card,count=1)
    card = card.replace('loading="lazy"','loading="eager"')
    slide = base64.b64encode((ROOT/row['carousel']['path']).read_bytes()).decode()
    note = 'Та же фотография' if row['status']=='confirmed' else 'Slide-01 без фото, прежняя пара сохранена'
    page.append('<h2>'+labels[i]+'</h2><p>'+note+'</p><div class="comparison"><img class="carousel" src="data:image/png;base64,'+slide+'">'+card+'</div>')
page.append('</main></html>')
(OUT/'comparison.html').write_text(''.join(page)+'\n')
canvas.save(OUT/'LIST.png')
print('LIST.png: 7 rows, slide-01 + cover; comparison.html: real homepage cards at 264.5 CSS px')
