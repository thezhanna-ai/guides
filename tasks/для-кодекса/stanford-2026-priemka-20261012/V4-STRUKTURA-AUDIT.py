from pathlib import Path
import subprocess, re, json, hashlib, html
ROOT=Path('/Users/zslepova/IvanOS')
WT=ROOT/'.worktrees/stanford-2026-konspekt'
OUT=ROOT/'tasks/для-кодекса/stanford-2026-priemka-20261012'
REL='claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
def git(*args): return subprocess.check_output(['git',*args],cwd=WT)
base=git('show','e1dff77:'+REL).decode(); current=(WT/REL).read_text()
task=(ROOT/'tasks/для-кодекса/2026-10-12-STANFORD-2026-PERENAPISAT-3.md').read_text()
quotes=[]; depth=0
for i,c in enumerate(task):
    if c=='«':
        if depth==0: start=i+1
        depth+=1
    elif c=='»':
        depth-=1
        if depth==0: quotes.append(task[start:i])
def q(i): return quotes[i]
def p(s): return '<p>'+s+'</p>'
def result(s): return '<div class="result"><p><b>Как это связано с твоим чатом:</b> '+s+'</p></div>'
expected=base; ops=[]
def replace(old,new,label):
    global expected
    assert expected.count(old)==1,(label,expected.count(old))
    expected=expected.replace(old,new)
    ops.append({'item':label,'old_sha256':hashlib.sha256(old.encode()).hexdigest(),'new_sha256':hashlib.sha256(new.encode()).hexdigest()})
def paragraph(prefix):
    vals=re.findall(r'<p\b[^>]*>.*?</p>',expected,re.S)
    found=[v for v in vals if html.unescape(re.sub('<[^>]+>','',v)).startswith(prefix)]
    assert len(found)==1,(prefix,len(found))
    return found[0]
def section(sid): return re.search(r'<section\b[^>]*id="'+sid+r'"[^>]*>.*?</section>',expected,re.S)[0]
def replace_result(sid,text,label):
    old=re.search(r'<div class="result">.*?</div>',section(sid),re.S)[0]
    replace(old,result(text),label)
replace(paragraph('Можно посмотреть запись по ссылкам'),p(q(1)),'0')
replace(q(3),q(4),'0b')
replace(paragraph('Нейросеть научилась, если'),p(q(5)),'1-intro')
s=section('opyt'); old=s[s.index('<h3>Как это видно'):s.index('<div class="result">')]
replace(old,'<h3>Как это видно в шахматах</h3>\n'+p(q(7)+'. '+q(12))+'\n','1-chess-and-delete')
replace_result('opyt',q(10),'1-result')
s=section('prompt'); old=s[s.index('<h3>Что изменилось</h3>'):s.index('<div class="result">')]
replace(old,'<h3>Что изменилось</h3>\n'+p(q(14))+'\n','2')
replace_result('prompt',q(16),'2-result')
s=section('skorost'); old=s[s.index('</h2>')+5:s.index('<div class="result">')]
replace(old,'\n'+p(q(17))+'\n','3')
replace_result('skorost',q(19),'3-result')
replace_result('imagenet',q(21),'4')
s=section('slova'); old=s[s.index('<h3>'):s.index('<div class="result">')]; figure=re.search(r'<figure.*?</figure>',s,re.S)[0]
replace(old,'<h3>'+q(23)+'</h3>\n'+p(q(24))+'\n'+figure+'\n<h3>'+q(25)+'</h3>\n'+p(q(26))+'\n','5')
replace_result('slova',q(28),'5-result')
s=section('instrukcii'); old=s[s.index('<h3>Что изменилось после обычных текстов'):s.index('<div class="result">')]
replace(old,'','6')
s=section('mysli'); old=s[s.index('</h2>')+5:s.index('</section>')]; figure=re.search(r'<figure.*?</figure>',s,re.S)[0]
replace(old,'\n'+p(q(34))+'\n<h3>'+q(35)+'</h3>\n'+p(q(36))+'\n'+figure+'\n<h3>'+q(37)+'</h3>\n'+p(q(38))+'\n'+result(q(40))+'\n','7')
s=section('popytki'); old=s[s.index('<h3>Задачи есть, готового решения нет</h3>')+len('<h3>Задачи есть, готового решения нет</h3>'):s.index('<h3>Четыре действия по кругу')]
replace(old,'\n'+p(q(43))+'\n'+p(q(48))+'\n','8')
replace(paragraph('Все запросы ниже наши'),p(q(52)),'9')
s=section('practice'); a=s.index('<h3>Приём 2.'); found=re.search(r'<p>.*?</p>',s[a:],re.S)[0]
replace(found,p('Почему: '+q(54)),'10-why')
s=section('practice'); a=s.index('<h3>Приём 2.'); b=s.index('<h3>Приём 3.'); old=re.search(r'<div class="result">.*?</div>',s[a:b],re.S)[0]
replace(old,'<div class="result"><p><b>Результат:</b> '+q(56)+'</p></div>','10-result')
replace(paragraph('В своём чате ты отбираешь ответ для себя'),p(q(58)),'11')
replace(paragraph('В начале был вопрос: как нейросеть научилась отвечать?')+'\n','','12')
exact=expected.encode()==current.encode()
if not exact:
    (OUT/'V4-STRUKTURA-EXPECTED.html').write_text(expected)
extra='<p>Готовое доказательство для сравнения не нужно: проверяют предложенную попытку доказательства, а не её совпадение с образцом. Как устроена эта проверка, вводная лекция не разбирает. Здесь показан порядок отбора: для следующего обучения берут только попытки, прошедшие проверку</p>\n'
extra_second='В примере со сдачей ниже готового образца ответа не нужно: складываешь предложенную сдачу 950,25 рубля и чек 1049,75 рубля и получаешь исходные 2000 рублей. Искать решение и проверять предложенное - разные действия. Это наш пример различия, а не описание проверки доказательств в лекции'
extra+=p(extra_second)+'\n'
assert current.count(extra)==1
assert current.replace(extra,'') == expected,'Unexpected changes beyond documented novice clarification'
reason=(OUT/'V4-PRAVKI-POSLE-NOVICHKA.md').read_text()
assert extra_second in reason
from decimal import Decimal
assert Decimal('950.25')+Decimal('1049.75')==Decimal('2000')
assert 'Готовое доказательство для сравнения не нужно: проверяют предложенную попытку доказательства, а не её совпадение с образцом' in reason
assert 'Как устроена эта проверка, вводная лекция не разбирает. Здесь показан порядок отбора: для следующего обучения берут только попытки, прошедшие проверку' in reason
assert hashlib.sha256(current.encode()).hexdigest()=='47f3dfb936aa9d490eed5aff641ea0dddb3c8d61fc922d9387fedd8d618ec1c7'
checks={'exact_reconstruction_from_task':exact,'exact_reconstruction_with_documented_novice_clarification':current.replace(extra,'')==expected,'documented_extra_paragraphs':extra.strip(),'replacement_operations':ops,'html_sha256':hashlib.sha256(current.encode()).hexdigest(),'base_html_sha256':hashlib.sha256(base.encode()).hexdigest()}
def unchanged(name,pattern):
    before=re.findall(pattern,base,re.S); after=re.findall(pattern,current,re.S)
    ok=before==after; assert ok and before,name
    checks[name]={'equal':ok,'count':len(after),'sha256':hashlib.sha256(''.join(after).encode()).hexdigest()}
unchanged('head',r'<head>.*?</head>')
unchanged('css',r'<style\b[^>]*>.*?</style>')
unchanged('scripts',r'<script\b[^>]*>.*?</script>')
unchanged('h1',r'<h1\b[^>]*>.*?</h1>')
unchanged('meta',r'<p class="meta">.*?</p>')
unchanged('eyebrow',r'<p class="eyebrow">.*?</p>')
unchanged('level_badge',r'<p class="uroven-metka\b[^>]*>.*?</p>')
unchanged('figures',r'<figure\b[^>]*>.*?</figure>')
unchanged('cta',r'<section class="cta"[^>]*>.*?</section>')
unchanged('footer',r'<footer\b[^>]*>.*?</footer>')
checks['outside_article_equal']=base.split('<article>')[0]==current.split('<article>')[0] and base.split('</article>')[1]==current.split('</article>')[1]
assert checks['outside_article_equal']
checks['thoughts']=re.findall(r'<h2>(Мысль \d+\..*?)</h2>',current)
assert len(checks['thoughts'])==8
checks['thought_3_h3_count']=len(re.findall('<h3>',section('skorost'))); assert checks['thought_3_h3_count']==0
checks['thought_5_h3']=re.findall(r'<h3>(.*?)</h3>',section('slova')); assert checks['thought_5_h3']==[q(23),q(25)]
checks['method_order']=[(sid,re.search(r'<p>(.*?)</p>',section(sid),re.S)[1]) for sid in ['imagenet','slova','instrukcii','popytki']]
assert current.index('id="instrukcii"')<current.index('id="mysli"')<current.index('id="popytki"')
checks['forbidden_absent']={x:x not in current for x in ['по правилам математики','«Судья» здесь','Что считать «лучше»','Что изменилось после обычных текстов','В начале был вопрос: как нейросеть научилась отвечать?']}
assert all(checks['forbidden_absent'].values())
checks['long_dashes']=len(re.findall('[—–]',current)); assert checks['long_dashes']==0
checks['paragraph_final_dots']=sum(html.unescape(re.sub('<[^>]+>','',x)).strip().endswith('.') for x in re.findall(r'<p\b[^>]*>(.*?)</p>',current,re.S)); assert checks['paragraph_final_dots']==0
changes=git('diff','--name-only','-z','e1dff77').decode().split('\0'); changes=[x for x in changes if x]
checks['changed_paths']=changes
helper='tasks/для-кодекса/stanford-2026-konspekt/proverka.py'
checks['scope_ok']=set(changes)=={REL,helper}
assert checks['scope_ok']
helper_before=git('show','e1dff77:'+helper).decode()
helper_after=(WT/helper).read_text()
helper_old="    assert count >= 1, ('thought_without_h3', section_id)"
helper_new="    # ТЗ третьего круга заменяет весь текст мысли 3 одним абзацем без h3\n    if section_id == 'skorost':\n        assert count == 0, ('unexpected_h3_in_thought_3', count)\n    else:\n        assert count >= 1, ('thought_without_h3', section_id)"
checks['helper_exact_adaptation']=helper_before.replace(helper_old,helper_new)==helper_after
assert checks['helper_exact_adaptation']
cache='tests/__pycache__/test_site.cpython-314.pyc'
checks['cache_restored_equal']=git('show','e1dff77:'+cache)==(WT/cache).read_bytes()
assert checks['cache_restored_equal']
files=git('ls-tree','-r','--name-only','-z','e1dff77').decode().split('\0')
protected=[x for x in files if x and (x.startswith('assets/') or x.startswith('claude-ai/stanford-2026-kak-uchitsya-ii/assets/') or x.startswith('data/') or x in ['index.html','sitemap.xml'])]
checks['protected_files']={}
for rel in protected:
    old=git('show','e1dff77:'+rel); new=(WT/rel).read_bytes(); assert old==new,rel
    checks['protected_files'][rel]=hashlib.sha256(new).hexdigest()
row=next(r for r in json.loads((WT/'data/statyi.json').read_text())['statyi'] if r['slug']=='stanford-2026-kak-uchitsya-ii')
checks['draft_state']={k:row[k] for k in ['status','vydacha','kod_slovo']}
assert checks['draft_state']=={'status':'draft','vydacha':'net','kod_slovo':'МОЗГ'}
checks['noindex']='<meta name="robots" content="noindex, nofollow">' in current
checks['home_absent']='href="claude-ai/stanford-2026-kak-uchitsya-ii/"' not in (WT/'index.html').read_text()
checks['sitemap_absent']='stanford-2026-kak-uchitsya-ii' not in (WT/'sitemap.xml').read_text()
assert checks['noindex'] and checks['home_absent'] and checks['sitemap_absent']
checks['new_url_attributes']=sorted(set(re.findall(r'(?:href|src|action|formaction)="([^"]*)"',current))-set(re.findall(r'(?:href|src|action|formaction)="([^"]*)"',base)))
checks['removed_url_attributes']=sorted(set(re.findall(r'(?:href|src|action|formaction)="([^"]*)"',base))-set(re.findall(r'(?:href|src|action|formaction)="([^"]*)"',current)))
assert checks['new_url_attributes']==[]
checks['handlers_unchanged']=re.findall(r'\bon\w+\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)',base)==re.findall(r'\bon\w+\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)',current)
assert checks['handlers_unchanged']
added='\n'.join(x[1:] for x in git('diff','e1dff77','--',REL,helper).decode().splitlines() if x.startswith('+') and not x.startswith('+++'))
secret_patterns=[r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY',r'\bAKIA[0-9A-Z]{16}\b',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}',r'(?i)\b(?:password|api_key|secret|token)\s*[:=]\s*[\x27\"][^\x27\"]{8,}']
checks['new_secret_hits']=[p for p in secret_patterns if re.search(p,added)]
assert not checks['new_secret_hits']
checks['diff_check']=subprocess.run(['git','diff','--check','e1dff77'],cwd=WT,capture_output=True,text=True).returncode
assert checks['diff_check']==0
(OUT/'V4-STRUKTURA-SECURITY-EVIDENCE.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k not in ['protected_files','replacement_operations','method_order']},ensure_ascii=False,indent=2))
print('PROTECTED FILES',len(protected),'REPLACEMENT OPERATIONS',len(ops),'PASS')
