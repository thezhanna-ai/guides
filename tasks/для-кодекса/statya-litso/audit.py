from pathlib import Path
from html import unescape
from html.parser import HTMLParser
from PIL import Image
import json,re,hashlib,subprocess
root=Path('/Users/zslepova/IvanOS'); wt=root/'.worktrees/statya-litso'; slug='otsenka-vneshnosti-po-foto-v-chatgpt'; dest=root/'tasks/для-кодекса/statya-litso'; page=wt/'claude-ai'/slug/'index.html'; s=page.read_text(); article=re.search(r'<article>(.*?)</article>',s,re.S)[1]
def text(h): return unescape(re.sub('<[^>]+>','',h)).strip()
def pre(id): return text(re.search(r'<pre id="'+id+r'"><code>(.*?)</code></pre>',s,re.S)[1])
main=(root/'tasks/content/2026-10-10-ssylka-litso/57-litso/prompt-donor-adapted-v3.txt').read_text().split('\n\nДополнительно оцени саму фотографию')[0].strip()
addition=(root/'tasks/content/2026-10-10-ssylka-litso/57-litso/prompt-practical-addition-v3.txt').read_text().strip()
assert pre('prompt-main')==main; assert pre('prompt-addition')==addition
ptexts=[text(x) for x in re.findall(r'<p\b[^>]*>(.*?)</p>',article,re.S)]
prose=re.sub(r'<pre\b.*?</pre>','',article,flags=re.S); plain=text(prose)
counts={'p_without_terminal':sum(not re.search(r'[.!?…:]$',x) for x in ptexts),'long_dashes':len(re.findall('[—–]',text(article))),'step_zero':len(re.findall('Шаг 0',plain)),'ivan_outside_cta':len(re.findall('Иван|theivansergeev',plain,re.I)),'banned_price_words':len(re.findall('бесплатно|платно|оплат|платить',plain,re.I)),'reader_gender':len(re.findall(r'ты [а-яё]+(?:л|ла|ли)\b',plain,re.I))}
assert not any(counts.values()),counts
ctare=r'<section class="cta".*?</section>'
assert re.search(ctare,s,re.S)[0]==re.search(ctare,(wt/'claude-ai/chetyre-mcp-claude-code/index.html').read_text(),re.S)[0]
blocks={'b':len(re.findall(r'<b>',article)),'result':len(re.findall('class="result"',article)),'warn-card':len(re.findall('class="warn-card"',article)),'lists':len(re.findall(r'<(?:ul|ol)\b',article))}
reference=(wt/'claude-ai/zakryt-sekrety-ot-claude-code/index.html').read_text(); refblocks={'b':len(re.findall('<b>',reference)),'result':len(re.findall('class="result"',reference)),'warn-card':len(re.findall('class="warn-card"',reference))}
assert all(blocks[k]>=v for k,v in refblocks.items())
steps=[]
for sec in re.findall(r'<section\b.*?</section>',article,re.S):
 m=re.search(r'<h2>Шаг (\d+)',sec)
 if m: assert 'class="result"' in sec; steps.append(int(m[1]))
assert steps==[1,2,3,4,5]
ids=re.findall(r'\bid="([^"]+)"',s); anchors=re.findall(r'href="#([^"]+)"',s); assert len(ids)==len(set(ids)); assert not set(anchors)-set(ids)
assets=[]
for src in re.findall(r'<img\b[^>]*src="([^"]+)"',s):
 f=page.parent/src
 assert f.exists(),f
 with Image.open(f) as im: assets.append({'file':src,'size':list(im.size)})
manifest=json.loads((dest/'ASSETS.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(manifest['video_source'])==manifest['video_sha256']; assert sha(manifest['report_source'])==manifest['report_sha256']; assert sha(page.parent/'assets/otchet-gpt-original.png')==manifest['report_sha256']
rows=json.loads((wt/'data/statyi.json').read_text())['statyi']; row=next(x for x in rows if x['slug']==slug)
assert row['status']=='draft' and row['vydacha']=='net'; assert row['ponyatiya']==['лицо','оценка внешности по фото','привлекательность в ChatGPT','анализ лица']; assert row['kod_slovo']=='ЛИЦО'; assert 'noindex, nofollow' in s
for f in ['index.html','sitemap.xml','data/indexnow.json']:
 if (wt/f).exists(): assert slug not in (wt/f).read_text(),f
reading=article
reading=re.sub(r'<nav\b.*?</nav>|<button\b.*?</button>','',reading,flags=re.S)
reading=re.sub(r'</(?:p|h1|h2|h3|li|div|section|figcaption)>','\n\n',reading)
reading=text(reading); (dest/'READING.txt').write_text(reading+'\n')
result={'article_sha256':sha(page),'prompts_exact':True,'CTA_exact':True,'mechanical':counts,'blocks':blocks,'reference_blocks':refblocks,'steps_with_result':steps,'assets':assets,'originals_sha_unchanged':True,'draft_excluded_from_live':True,'search_card_title':row['kratko']}
(dest/'MECHANICS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
class LinkParser(HTMLParser):
 def __init__(self):super().__init__();self.attrs=None;self.parts=[]
 def handle_starttag(self,t,a):
  if t=='a' and dict(a).get('class','').startswith('guide-link'):self.attrs=dict(a)
 def handle_data(self,d):
  if self.attrs:self.parts.append(d)
card=(dest/'SEARCH-CARD.html').read_text(); cp=LinkParser();cp.feed(card)
fixture=json.loads(subprocess.check_output(['/opt/homebrew/bin/python3','-c','import json; from tests.test_site import catalog_dom_fixture; print(json.dumps(catalog_dom_fixture(), ensure_ascii=False))'],cwd=wt,text=True,env={'PATH':'/opt/homebrew/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}))
section=next(x for x in fixture['sections'] if x['tag']=='kartinki');section['tracks'].append({'links':[{'attrs':cp.attrs,'text':''.join(cp.parts)}]})
js=(wt/'tests/filtry.test.cjs').read_text().split("test('Начальная страница:")[0]
js=js.replace("const root = path.resolve(__dirname, '..');",'const root = '+json.dumps(str(wt))+';')
js=re.sub(r'const fixture = .*?;\n',lambda m: 'const fixture = '+json.dumps(fixture,ensure_ascii=False)+';\n',js,count=1)
js+="\nfor (const query of ['лицо', 'ЛИЦО', ' лицо ']) { const p = page(); p.search(query); const hit=p.visible().find(x=>x.attrs.href.includes('"+slug+"')); assert.ok(hit, query); console.log(JSON.stringify({query, href:hit.attrs.href, title:hit.attrs['aria-label'], poisk:hit.attrs['data-poisk']})); }\n"
Path('/private/tmp/litso-inspect/search-final.cjs').write_text(js)
