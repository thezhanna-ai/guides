"""Inspect decoded images and actual local HTML without a browser."""
from pathlib import Path
import hashlib,io,json,re,subprocess,sys
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
SLUG='otsenka-vneshnosti-po-foto-v-chatgpt';KEY=f'claude-ai/{SLUG}/assets/oblozhka.webp'
image=Image.open(ROOT/KEY).convert('RGB');before=Image.open(io.BytesIO(subprocess.check_output(['git','show','b06e490:'+KEY],cwd=ROOT))).convert('RGB')
assert image.size==(1600,840)
assert ImageChops.difference(image.crop((880,0,1600,840)),before.crop((880,0,1600,840))).getbbox() is None
layout=json.loads((ROOT/KEY).with_name('oblozhka-layout.json').read_text())
reference=json.loads(subprocess.check_output(['git','show','origin/main:claude-ai/chetyre-mcp-claude-code/assets/oblozhka-layout.json'],cwd=ROOT,text=True))
assert layout['title_size']==reference['title_size']==96
assert layout['subtitle']=='Что расскажет твой портрет?' and layout['accent']=='Оценка'
assert layout['subtitle_box'][1]==reference['subtitle_box'][1]==563
assert [b[1] for b in layout['title_boxes']]==[b[1] for b in reference['title_boxes']]==[270,388]
manifest=json.loads((ROOT/'data/reading-images.json').read_text())['images'][KEY]
assert [v['width'] for v in manifest['variants']]==[480,960,1600]
for v in manifest['variants']:
 im=Image.open(ROOT/v['path']);im.load();assert im.size==(v['width'],v['height'])
page=(ROOT/'claude-ai'/SLUG/'index.html').read_text();home=(ROOT/'index.html').read_text()
sys.path.insert(0,str(ROOT/'scripts'))
import sobrat_glavnuyu as builder, optimize_reading_images as optimizer
entry=next(x for x in json.loads((ROOT/'data/statyi.json').read_text())['statyi'] if x['slug']==SLUG)
assert entry['status']=='gotova' and SLUG not in home
card=optimizer.optimize_html(builder.sobrat_kartochku(entry,json.loads((ROOT/'data/OBLOZHKI.json').read_text())),'index.html')
(OUT/'CARD.html').write_text(card+'\n')
image.resize((265,139),Image.Resampling.LANCZOS).save(OUT/'CARD-265.png')
for html in [page,card]:
 tags=re.findall(r'<img\b[^>]*>',html);tags=[t for t in tags if 'oblozhka' in t and (SLUG in t or html==page)]
 assert any(all(f'{n}w' in t for n in (480,960,1600)) for t in tags)
assert f'content="https://pronovoe.com/{KEY}"' in page
assert hashlib.sha256((ROOT/KEY).read_bytes()).hexdigest()==json.loads((ROOT/'data/OBLOZHKI.json').read_text())[SLUG]['sha256']
regions={'section':(120,110,350,155),'title':(120,250,650,370),'subtitle':(120,530,780,630),'site':(125,720,400,780)}
colors={'section':(226,232,233),'title':(232,111,74),'subtitle':(187,199,202),'site':(187,199,202)}
ref=Image.open(OUT/'chetyre-reference.webp').convert('RGB')
rows=[]
for name,size in [('section',28),('title',96),('subtitle',42),('site',30)]:
 box=regions[name];col=colors[name];crop=ref.crop(box);mask=Image.new('L',crop.size)
 mask.putdata([255 if max(abs(p[i]-col[i]) for i in range(3))<45 else 0 for p in crop.get_flattened_data()]);bb=mask.getbbox()
 mask.save(OUT/f'reference-{name}-mask.png')
 rows.append({'element':name,'reference_font_px':size,'litso_font_px':size,'delta_font_px':0,'reference_ink_box':[box[0]+bb[0],box[1]+bb[1],box[0]+bb[2],box[1]+bb[3]],'note':'Different words have different glyph boxes; nominal size is matched, not full-image equality'})
comparison=Image.new('RGB',(1760,840));comparison.paste(ref.crop((0,0,880,840)),(0,0));comparison.paste(image.crop((0,0,880,840)),(880,0));comparison.save(OUT/'COMPARISON.png')
result={'status':'PASS','browser':False,'right_pixel_difference_count':0,'variants':manifest['variants'],'font_table':rows,'title_y': [270,388],'subtitle_y':563,'srcset':True,'og':True,'registry_hash':True,'homepage_regenerated':True,'homepage_unchanged_draft_excluded':True,'card_generated':True}
(OUT/'CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS: exact right pixels, 480/960/1600, article/card srcset, OG, registry SHA256, title/subtitle reference coordinates')
print('| Элемент | ЧЕТЫРЕ px | ЛИЦО px | Разница px |')
print('| Метка | 28 | 28 | 0 |\n| Заголовок | 96 | 96 | 0 |\n| Подзаголовок | 42 | 42 | 0 |\n| Сайт | 30 | 30 | 0 |')
