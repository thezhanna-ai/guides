"""Use the accepted series layout and ONE crop of the real ChatGPT report."""
from pathlib import Path
import hashlib, json, re, subprocess, sys
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
WORKSPACE=ROOT.parents[1]
SLUG='otsenka-vneshnosti-po-foto-v-chatgpt'
ASSETS=ROOT/'claude-ai'/SLUG/'assets'
OUT=Path(__file__).resolve().parent
BASE='66f3334'
KEY=f'claude-ai/{SLUG}/assets/oblozhka.webp'

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    import io
    baseline=subprocess.check_output(['git','show',BASE+':'+KEY],cwd=ROOT)
    image=Image.open(io.BytesIO(baseline)).convert('RGB')
    left=image.crop((0,0,880,840)).tobytes()
    source=ASSETS/'otchet-gpt-original.png'
    upstream=WORKSPACE/'tasks/content/2026-10-10-ssylka-litso/57-litso/montazh/ishodniki/от GPT.png'
    assert source.read_bytes()==upstream.read_bytes(), 'Report differs from the supplied source'
    original=Image.open(source).convert('RGB')
    # Top panel through the complete portrait, all 15 scores, and two lower panels.
    # The remaining recommendations stay available in the untouched article PNG.
    crop=[0,0,1024,1184]
    report=original.crop(crop).resize((620,717),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(image)
    d.rectangle((880,0,1599,839),fill='#102F30')
    frame=[904,56,1536,785]
    d.rectangle(frame,fill='#0C2425',outline='#6A7165',width=3)
    xy=(910,62)
    image.paste(report,xy)
    assert image.crop((0,0,880,840)).tobytes()==left
    dest=ASSETS/'oblozhka.webp'
    image.save(dest,'WEBP',lossless=True,method=6)
    decoded=Image.open(dest).convert('RGB')
    assert decoded.tobytes()==image.tobytes()
    assert decoded.crop((910,62,1530,779)).tobytes()==report.tobytes()
    layout=json.loads(subprocess.check_output(['git','show',BASE+':'+f'claude-ai/{SLUG}/assets/oblozhka-layout.json'],cwd=ROOT,text=True))
    layout.update(frames=[frame],fields=[x for x in layout['fields'] if x['text'] not in ('фото','отчёт')],
        photos=[{'source':source.relative_to(ROOT).as_posix(),'upstream':upstream.relative_to(WORKSPACE).as_posix(),
        'sha256':sha(source.read_bytes()),'original_size':list(original.size),'frame':frame,'crop':crop,
        'photo_box':[910,62,1530,779],'operation':'one crop, proportional LANCZOS resize; no generation or retouch',
        'resized_pixels_sha256':sha(report.tobytes())}],
        generation=False,labels='Один реальный отчёт: портрет с подписями, 15 оценок и итог 8,7/10',
        arrow=False,left_pixels_sha256=sha(left),baseline_commit=BASE,palette=['#102F30','#F5F7F3','#E86F4A'])
    (ASSETS/'oblozhka-layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
    registry=ROOT/'data/OBLOZHKI.json';covers=json.loads(registry.read_text())
    old=covers[SLUG]['alt']
    new='Один отчёт ChatGPT: крупный портрет с подписями вокруг лица, 15 оценок и итог 8,7/10 рядом с заголовком «Оценка лица»'
    covers[SLUG].update(alt=new,source_alt='Кадр исходного отчёта ChatGPT: один портрет, подписи и оценки, без генерации и ретуши',sha256=sha(dest.read_bytes()))
    registry.write_text(json.dumps(covers,ensure_ascii=False,indent=2)+'\n')
    page=ROOT/'claude-ai'/SLUG/'index.html';html=page.read_text().replace(old,new)
    html=html.replace('font:700 13px/1.3 -apple-system,BlinkMacSystemFont,Arial,sans-serif','font:700 13px/1.3 -apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,Arial,sans-serif')
    html=html.replace('<h2>Нужна подсказка по текущему экрану?</h2>','<h2 class="help-title">Нужна подсказка по текущему экрану?</h2>')
    html=html.replace('.help-banner p { color: var(--guide-color-paper); text-align: left }',
        '.help-banner p { color: var(--guide-color-paper); text-align: left }\n.help-banner > p { font: 400 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif }')
    page.write_text(html)
    sys.path.insert(0,str(ROOT/'scripts'))
    import optimize_reading_images as opt
    manifest_path=opt.MANIFEST
    manifest=json.loads(manifest_path.read_text())
    # Generate only the changed cover, with the standard cover policy (quality95).
    opt.inventory=lambda:{KEY:{'article':True,'cover':True,'pages':[page.relative_to(ROOT).as_posix()]}}
    generated=opt.generate()
    manifest['images'][KEY]=generated['images'][KEY]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    opt.apply_articles()
    print('Cover PASS: 1600x840, one source, crop',crop,'report 620x717, left layout unchanged')
    print('Source SHA256',sha(source.read_bytes()))

if __name__=='__main__': main()
