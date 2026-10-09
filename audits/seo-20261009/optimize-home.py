from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image
import json,hashlib
root=Path.cwd();folder=root/'assets/fonts';items=[]
unicodes=list(range(0x20,0x250))+list(range(0x400,0x530))+list(range(0x2000,0x2070))+list(range(0x20a0,0x20d0))+[0x2116,0x2192]
for name in ['spectral-300','unbounded-700','jetbrains-mono-500','jetbrains-mono-700']:
 source=folder/(name+'.woff2');f=TTFont(source);options=subset.Options();options.flavor='woff2';options.layout_features=['*'];sub=subset.Subsetter(options=options);sub.populate(unicodes=unicodes);sub.subset(f);dest=folder/(name+'-home.woff2');f.save(dest)
 origin=TTFont(source);assert all(f['hmtx'][g]==origin['hmtx'][g] for g in f.getGlyphOrder() if g in origin.getGlyphOrder());assert f['head'].unitsPerEm==origin['head'].unitsPerEm
 items.append({'source':source.name,'file':dest.name,'source_bytes':source.stat().st_size,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'glyphs':len(f.getGlyphOrder()),'unchanged_advance_metrics':True})
img=Image.open(root/'assets/glavnaya/hero.webp');img.resize((780,488),Image.Resampling.LANCZOS).save(root/'assets/glavnaya/hero-mobile.webp',quality=85,method=6)
# Metrics derived from actual hero texts, not generic values
pairs=[('unbounded-700.woff2','/System/Library/Fonts/Supplemental/Arial.ttf','Нейросети работают на тебя'),('spectral-300.woff2','/System/Library/Fonts/Supplemental/Georgia.ttf','Надо только научиться ставить задачу. Здесь инструкции и разборы - от первой кнопки до собранных проектов')]
metrics=[]
def width(font,text):
 cmap=font.getBestCmap();return sum(font['hmtx'][cmap[ord(c)]][0] for c in text)/font['head'].unitsPerEm
for source,fallback,text in pairs:
 a=TTFont(folder/source);b=TTFont(fallback);scale=width(a,text)/width(b,text);upem=a['head'].unitsPerEm;metrics.append({'source':source,'fallback':Path(fallback).name,'size_adjust':round(scale*100,3),'ascent_override':round(a['hhea'].ascent/upem/scale*100,3),'descent_override':round(abs(a['hhea'].descent)/upem/scale*100,3),'line_gap_override':round(a['hhea'].lineGap/upem/scale*100,3)})
(root/'assets/fonts/home-manifest.json').write_text(json.dumps({'files':items,'range':'Latin U+0020-024F, Cyrillic U+0400-052F, punctuation U+2000-206F, currencies, № and →','fallback_metrics':metrics},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fonts':items,'metrics':metrics,'mobile_image_bytes':(root/'assets/glavnaya/hero-mobile.webp').stat().st_size},ensure_ascii=False,indent=2))
