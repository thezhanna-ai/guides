from pathlib import Path
import subprocess, re, json, hashlib, runpy, html
ROOT=Path('/Users/zslepova/IvanOS')
WT=ROOT/'.worktrees/stanford-2026-konspekt'
OUT=ROOT/'tasks/для-кодекса/stanford-2026-priemka-20261012'
REL='claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
def git(*args):return subprocess.check_output(['git',*args],cwd=WT)
base=git('show','38cd949:'+REL).decode();current=(WT/REL).read_text()
recipe=runpy.run_path(str(OUT/'V5-APPLY.py'))
assert recipe['s']==current,'Unexpected edit outside approved replacements'
assert recipe['ops']==json.loads((OUT/'V5-DOSLOVNYE-ZAMENY.json').read_text())
assert recipe['quotes']==json.loads((OUT/'V5-CITATY.json').read_text())
checks={'base':'38cd949','html_sha256':hashlib.sha256(current.encode()).hexdigest(),'exact_reconstruction':True,'replacement_count':len(recipe['ops'])}
def same(name,pattern):
    old=re.findall(pattern,base,re.S);new=re.findall(pattern,current,re.S)
    assert old==new and old,name
    checks[name]={'equal':True,'count':len(old),'sha256':hashlib.sha256(''.join(old).encode()).hexdigest()}
for name,pattern in [('head',r'<head>.*?</head>'),('css',r'<style\b[^>]*>.*?</style>'),('js',r'<script\b[^>]*>.*?</script>'),('h1',r'<h1\b[^>]*>.*?</h1>'),('eyebrow',r'<p class="eyebrow">.*?</p>'),('meta',r'<p class="meta">.*?</p>'),('level',r'<p class="uroven-metka\b[^>]*>.*?</p>'),('cta',r'<section class="cta"[^>]*>.*?</section>'),('figures',r'<figure\b[^>]*>.*?</figure>'),('original',r'<section\b[^>]*id="original"[^>]*>.*?</section>'),('footer',r'<footer\b[^>]*>.*?</footer>'),('prompts',r'<div class="code-card">.*?</div>')]:same(name,pattern)
checks['outside_article']=base.split('<article>')[0]==current.split('<article>')[0] and base.split('</article>')[1]==current.split('</article>')[1]
assert checks['outside_article']
paths=git('ls-tree','-r','--name-only','-z','38cd949').decode().split('\0')
protected=[p for p in paths if p and (p.startswith(('assets/','data/','claude-ai/stanford-2026-kak-uchitsya-ii/assets/')) or p in ['index.html','sitemap.xml'])]
checks['protected_files']={}
for rel in protected:
    before=git('show','38cd949:'+rel);after=(WT/rel).read_bytes()
    assert before==after,rel
    checks['protected_files'][rel]=hashlib.sha256(after).hexdigest()
attr=r'(?:href|src|action|formaction)="([^"]*)"'
checks['url_attributes_unchanged']=re.findall(attr,base)==re.findall(attr,current)
assert checks['url_attributes_unchanged']
handlers=r'\bon\w+\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)'
checks['handlers_unchanged']=re.findall(handlers,base)==re.findall(handlers,current)
assert checks['handlers_unchanged']
row=next(x for x in json.loads((WT/'data/statyi.json').read_text())['statyi'] if x['slug']=='stanford-2026-kak-uchitsya-ii')
checks['draft_state']={k:row[k] for k in ['status','vydacha','kod_slovo']}
assert checks['draft_state']=={'status':'draft','vydacha':'net','kod_slovo':'МОЗГ'}
assert '<meta name="robots" content="noindex, nofollow">' in current
assert 'href="claude-ai/stanford-2026-kak-uchitsya-ii/"' not in (WT/'index.html').read_text()
assert 'stanford-2026-kak-uchitsya-ii' not in (WT/'sitemap.xml').read_text()
checks['noindex_home_sitemap']=True
checks['quotes']={}
editorial=current
for q in recipe['quotes']:
    block='<div class="info-card" id="'+q['id']+'">'+recipe['p']('<b>'+q['label']+'</b>')+q['body']+'</div>'
    assert current.count(block)==1
    editorial=editorial.replace(block,'')
    assert (WT/'tasks/для-кодекса/stanford-2026-priemka-20261012/PROGONY'/q['fixture']).read_bytes()==(OUT/'PROGONY'/q['fixture']).read_bytes()
    checks['quotes'][q['id']]={'verified':True,'fixture_sha256':q['source_sha256']}
checks['long_dashes_editorial']=len(re.findall('[—–]',editorial));assert checks['long_dashes_editorial']==0
checks['long_dashes_quotes']=len(re.findall('[—–]',current))
assert checks['long_dashes_quotes']==2
checks['paragraph_final_dots_editorial']=sum(html.unescape(re.sub('<[^>]+>','',x)).strip().endswith('.') for x in re.findall(r'<p\b[^>]*>(.*?)</p>',editorial,re.S))
assert checks['paragraph_final_dots_editorial']==0
checks['result_blocks']=current.count('class="result"');assert checks['result_blocks']==9
checks['example_our_count']=len(re.findall('Пример наш',current));assert checks['example_our_count']==1
assert 'Короткий ответ тоже может содержать ошибку' in current
assert 'Оба ответа верны: сдача 950,25 рубля. Без добавки тоже были шаги расчёта.' in current
checks['ma_count']=len(re.findall(r'\bМа\b',editorial))
checks['lecturer_count']=len(re.findall(r'\bлектор\w*\b',editorial,re.I))
checks['changed_tracked_paths']=[x for x in git('diff','--name-only','-z','38cd949').decode().split('\0') if x]
source_paths={REL,'tasks/для-кодекса/stanford-2026-konspekt/proverka.py'}
assert source_paths.issubset(checks['changed_tracked_paths'])
assert all(p in source_paths or p=='tasks/для-кодекса/2026-10-12-STANFORD-2026-PERENAPISAT-4.md' or p.startswith('tasks/для-кодекса/stanford-2026-priemka-20261012/') for p in checks['changed_tracked_paths'])
added='\n'.join(x[1:] for x in git('diff','38cd949').decode().splitlines() if x.startswith('+') and not x.startswith('+++'))
patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY',r'\bAKIA[0-9A-Z]{16}\b',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}',r'(?i)\b(?:password|api_key|secret|token)\s*[:=]\s*[\x27\"][^\x27\"]{8,}']
checks['secret_hits']=[p for p in patterns if re.search(p,added)];assert not checks['secret_hits']
checks['text_sha256']=hashlib.sha256((OUT/'TEKST-NA-SOGLASOVANIE-v5.md').read_bytes()).hexdigest()
(OUT/'V5-EVIDENCE.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print('PASS: exact reconstruction;',len(protected),'protected files;',len(checks['quotes']),'verbatim quote blocks;',checks['result_blocks'],'results; no new URL/handlers/secrets')
print('HTML SHA256',checks['html_sha256'],'Ma',checks['ma_count'],'lecturer',checks['lecturer_count'])
