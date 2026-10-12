from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import subprocess, re, hashlib, json, html, difflib

ROOT = Path('/Users/zslepova/IvanOS/.worktrees/stanford-2026-konspekt')
OUT = Path('/Users/zslepova/IvanOS/tasks/для-кодекса/stanford-2026-priemka-20261012')
REL = 'claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
BASE = '2011ac0'
sha = lambda x: hashlib.sha256(x if isinstance(x, bytes) else x.encode()).hexdigest()
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT)
old = git('show',BASE+':'+REL).decode()
new = (ROOT/REL).read_text()
checks = {}
def check(key, passed, detail=None):
    checks[key] = {'pass':bool(passed),'detail':detail}
def extract(pattern, source):
    return re.findall(pattern, source, re.S)
patterns = {
 'head': r'<head\b[^>]*>.*?</head>',
 'scripts': r'<script\b[^>]*>.*?</script>',
 'styles': r'<style\b[^>]*>.*?</style>',
 'eyebrow': r'<p class="eyebrow"[^>]*>.*?</p>',
 'h1': r'<h1\b[^>]*>.*?</h1>',
 'meta': r'<p class="meta"[^>]*>.*?</p>',
 'level': r'<p class="uroven-metka[^>]*>.*?</p>',
 'CTA': r'<section class="cta"[^>]*>.*?</section>',
 'figures': r'<figure\b[^>]*>.*?</figure>',
 'footer': r'<footer\b[^>]*>.*?</footer>',
}
for name, pat in patterns.items():
    before, after = extract(pat,old),extract(pat,new)
    check('protected_'+name, before==after and bool(after), {'old_count':len(before),'new_count':len(after),'sha256':[sha(x) for x in after]})
check('exactly_four_figures',len(extract(patterns['figures'],new))==4)

original_pat = r'<section\b[^>]*id="original"[^>]*>.*?</section>'
original_old, original_new = extract(original_pat,old)[0],extract(original_pat,new)[0]
allowed_original_before = 'до моделей, которые решают задачи и собирают данные для следующего обучения'
allowed_original_after = 'до нейросетей, которые решают задачи и собирают примеры для следующего обучения'
check('original_only_authorized_two_term_substitutions',original_old.count(allowed_original_before)==1 and original_new==original_old.replace(allowed_original_before,allowed_original_after),{'permitted_before':allowed_original_before,'permitted_after':allowed_original_after,'viewing_instructions_byte_unchanged':original_old.split('<ul>',1)[1]==original_new.split('<ul>',1)[1]})

article_pat = r'<article>.*?</article>'
outside_old = re.sub(article_pat,'<article>[REMOVED]</article>',old,flags=re.S)
outside_new = re.sub(article_pat,'<article>[REMOVED]</article>',new,flags=re.S)
navigation_labels = {
 '2. Одна модель, разные задачи':'2. Один чат, разные задачи',
 '3. Скорость исследований':'3. Скорость обучения',
 '5. Слова и отношения':'5. Связи между словами',
 '7. Как модель «думает»':'7. Как нейросеть «думает»',
 '8. Где взять новые уроки?':'8. Обучение на своих попытках',
}
expected_outside = outside_old
nav_counts = {}
for before,after in navigation_labels.items():
    nav_counts[before] = {'old':outside_old.count('>'+before+'</a>'),'new':outside_new.count('>'+after+'</a>')}
    expected_outside = expected_outside.replace('>'+before+'</a>','>'+after+'</a>')
expected_outside = expected_outside.replace('<h2>Модель и глубина рассуждений под задачу</h2>','<h2>Нейросеть и глубина рассуждений под задачу</h2>')
check('outside_article_only_navigation_labels_plaque_term_and_EOF_LF',expected_outside.removesuffix('\n')==outside_new.removesuffix('\n'),{'navigation':nav_counts,'normalized_sha256':sha(expected_outside),'exact_byte_match_after_labels':expected_outside==outside_new,'baseline_ends_LF':outside_old.endswith('\n'),'current_ends_LF':outside_new.endswith('\n'),'only_EOF_LF_normalized':True})

class Tokens(HTMLParser):
    def __init__(self,source):
        super().__init__(convert_charrefs=False)
        self.tags=[]; self.events=[]; self.urls=[]
        self.feed(source)
    def handle_starttag(self,tag,attrs):
        self.tags.append((tag,tuple(attrs)))
        for key,value in attrs:
            if key.lower().startswith('on'): self.events.append((tag,key,value))
            if key.lower() in {'href','src','action','formaction'}: self.urls.append((key,value))
    def handle_startendtag(self,tag,attrs): self.handle_starttag(tag,attrs)
old_tokens, new_tokens = Tokens(old),Tokens(new)
old_out_tokens,new_out_tokens=Tokens(outside_old),Tokens(outside_new)
check('outside_article_all_tags_and_attributes_unchanged',old_out_tokens.tags==new_out_tokens.tags)
attrs_old=Counter(t for t in old_tokens.tags if t[1])
attrs_new=Counter(t for t in new_tokens.tags if t[1])
added_attribute_counts=attrs_new-attrs_old
allowed_internal_attributes=Counter({('div',(('class','result'),)):8,('a',(('href','#priem-1'),)):1})
added_attribute_tags=list(added_attribute_counts.elements())
check('only_requested_prose_markup_attributes_added',added_attribute_counts==allowed_internal_attributes,{'added':added_attribute_tags,'reason':'Восемь строк связи с чатом в существующем классе result и требуемая ТЗ ссылка на приём 1 внутри article'})
url_pattern = r'https?://[^\s<>"\x27]+'
urls_old,urls_new=set(extract(url_pattern,old)),set(extract(url_pattern,new))
check('no_new_external_URLs',not urls_new-urls_old,{'added':sorted(urls_new-urls_old),'removed':sorted(urls_old-urls_new)})
check('no_new_inline_handlers',not new_tokens.events and new_tokens.events==old_tokens.events,{'old_count':len(old_tokens.events),'new_count':len(new_tokens.events)})
dangerous = [(key,value) for key,value in new_tokens.urls if value and re.match(r'\s*(?:javascript|data|vbscript):',value,re.I)]
check('no_executable_URL_attributes',not dangerous,{'count':len(dangerous)})

asset_info=[]
for fig in extract(patterns['figures'],new):
    src=re.search(r'<img\b[^>]*src="([^"]+)"',fig)[1]
    rel=str((Path(REL).parent/src))
    disk=(ROOT/rel).read_bytes()
    baseline=git('show',BASE+':'+rel)
    asset_info.append({'path':rel,'sha256':sha(disk),'bytes':len(disk),'unchanged_from_BASE':disk==baseline})
check('all_four_figure_files_byte_unchanged',len(asset_info)==4 and all(x['unchanged_from_BASE'] for x in asset_info),asset_info)

registry=json.loads((ROOT/'data/statyi.json').read_text())
row=next(x for x in registry['statyi'] if x['slug']=='stanford-2026-kak-uchitsya-ii')
state={key:row[key] for key in ['status','vydacha','kod_slovo']}
check('draft_state',state=={'status':'draft','vydacha':'net','kod_slovo':'МОЗГ'},state)
check('robots_noindex_nofollow','<meta name="robots" content="noindex, nofollow">' in new)
check('absent_from_home','stanford-2026-kak-uchitsya-ii' not in (ROOT/'index.html').read_text())
check('absent_from_sitemap','stanford-2026-kak-uchitsya-ii' not in (ROOT/'sitemap.xml').read_text())
for rel in ['data/statyi.json','index.html','sitemap.xml']:
    check('file_unchanged_'+rel,(ROOT/rel).read_bytes()==git('show',BASE+':'+rel))

changed=git('-c','core.quotepath=false','diff','--name-only',BASE).decode().splitlines()
allowed_files=[REL,'tasks/для-кодекса/stanford-2026-konspekt/proverka.py']
check('only_HTML_and_authorized_audit_helper_changed',set(changed)==set(allowed_files),changed)
diff=git('diff',BASE,'--',*allowed_files).decode()
added='\n'.join(line[1:] for line in diff.splitlines() if line.startswith('+') and not line.startswith('+++'))
secret_patterns={
 'private_key':r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----',
 'openai_key':r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}',
 'github_token':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
 'aws_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'telegram_token':r'\b\d{8,12}:[A-Za-z0-9_-]{30,}\b',
 'credential_assignment':r'(?i)\b(?:api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[:=]\s*[\x27\"][^\x27\"]{8,}',
}
secret_counts={name:len(re.findall(pattern,added)) for name,pattern in secret_patterns.items()}
check('no_secret_patterns_in_added_diff',not any(secret_counts.values()),secret_counts)
forbidden_assets=git('diff','--name-only',BASE,'--','*.js','*.cjs','*.css').decode().splitlines()
check('no_application_JS_CSS_changes',not forbidden_assets,forbidden_assets)
head=git('rev-parse','HEAD').decode().strip()
check('HEAD_is_requested_BASE',head.startswith(BASE),head)
check('HTML_unchanged_during_audit',sha((ROOT/REL).read_bytes())==sha(new))
result={'reviewer':'independent mechanics/security reviewer','base_commit':BASE,'head_commit':head,'HTML_SHA256':sha(new),'HTML_bytes':len(new.encode()),'changed_files':changed,'checks':checks,'pass':all(item['pass'] for item in checks.values())}
(OUT/'V3-MEHANIKA-DIFF.log').write_text('COMMAND: git diff '+BASE+' -- HTML and audit helper\nEXIT_CODE: 0\nHTML_SHA256: '+sha(new)+'\nOUTPUT:\n'+diff)
(OUT/'V3-SECURITY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(OUT/'V3-MEHANIKA-AUDIT.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(0 if result['pass'] else 1)
