"""Canonical v2 text; preserve the accepted right report pixel for pixel."""
from pathlib import Path
import hashlib, io, json, subprocess, sys, tempfile
from PIL import Image
import template_v2 as canon
ROOT=Path(__file__).resolve().parents[3]
WORKSPACE=ROOT.parents[1]
OUT=Path(__file__).resolve().parent
SLUG='otsenka-vneshnosti-po-foto-v-chatgpt'
KEY=f'claude-ai/{SLUG}/assets/oblozhka.webp'
ASSETS=ROOT/'claude-ai'/SLUG/'assets'
FONTS=WORKSPACE/'tasks/content/2026-10-03-oformlenie-sayta/fonts'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    before=Image.open(io.BytesIO(subprocess.check_output(['git','show','b06e490:'+KEY],cwd=ROOT))).convert('RGB')
    base=Image.new('RGB',before.size,'#102F30')
    base.paste(before.crop((880,0,1600,840)),(880,0))
    prepared=Path(tempfile.gettempdir())/'litso-kanon-prepared.png';base.save(prepared)
    cover,_,meta=canon.render('CHATGPT','Оценка\nлица','Оценка','Что расскажет твой портрет?',scene=prepared,fonts=FONTS,title_size=96,prepared=True)
    assert cover.crop((880,0,1600,840)).tobytes()==before.crop((880,0,1600,840)).tobytes()
    dest=ASSETS/'oblozhka.webp';cover.save(dest,'WEBP',lossless=True,method=6)
    old=json.loads((ASSETS/'oblozhka-layout.json').read_text())
    meta.update(reference_commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),reference='claude-ai/chetyre-mcp-claude-code/assets/oblozhka.webp',fonts={'title':'Unbounded 700 96','subtitle':'Spectral 400 42','section':'JetBrains Mono 500 28','site':'JetBrains Mono 400 30'},tracking={'section':2.5,'site':0,'title':0,'subtitle':0},palette=canon.PALETTE,photos=old['photos'],frames=old['frames'],generation=False,right_pixels_sha256=sha(before.crop((880,0,1600,840)).tobytes()),mobile_subtitle_px=round(42*390/1600,2))
    (ASSETS/'oblozhka-layout.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    registry=ROOT/'data/OBLOZHKI.json';covers=json.loads(registry.read_text());covers[SLUG]['sha256']=sha(dest.read_bytes());registry.write_text(json.dumps(covers,ensure_ascii=False,indent=2)+'\n')
    sys.path.insert(0,str(ROOT/'scripts'));import optimize_reading_images as opt
    manifest=json.loads(opt.MANIFEST.read_text());opt.inventory=lambda:{KEY:{'article':True,'cover':True,'pages':[f'claude-ai/{SLUG}/index.html']}}
    generated=opt.generate();manifest['images'][KEY]=generated['images'][KEY];opt.MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');opt.apply_articles()
    print('PASS: 1600x840; canonical 96/42/28/30 px; accepted right side unchanged')
if __name__=='__main__':main()
