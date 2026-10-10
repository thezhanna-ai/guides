from pathlib import Path
from html.parser import HTMLParser
import collections,difflib,hashlib,json,re,subprocess,sys
root=Path(__file__).resolve().parents[2]
audit=root/'audits/komanda-oformlenie-20261010'
rel='claude-ai/komanda-ii-agentov-dlya-bloga/index.html'
old=subprocess.check_output(['git','show','6b325b1:'+rel],cwd=root).decode()
new=(root/rel).read_text()
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)
 def handle_starttag(self,tag,attrs):
  if tag in {'p','section','li','h1','h2','h3','pre','div','summary','tr','td','th','nav','header','figure','figcaption'}:self.parts.append(' ')
 def handle_endtag(self,tag):
  if tag in {'p','section','li','h1','h2','h3','pre','div','summary','tr','td','th','nav','header','figure','figcaption'}:self.parts.append(' ')
def visible(html):
 p=Text();p.feed(html);return re.findall(r'\w+|[^\w\s]',''.join(p.parts))
def source(html):
 text=html.split('<!-- komanda:source:start -->')[1].split('<!-- komanda:source:end -->')[0]
 return re.sub(r'<section class="help-banner" id="pomoshch".*?</section>', '', text, flags=re.S)
a,b=visible(source(old)),visible(source(new))
diff=list(difflib.unified_diff(a,b,fromfile='6b325b1',tofile='working-tree',lineterm=''))
(audit/'word-diff.txt').write_text('\n'.join(diff))
assert not diff,'Source words changed: '+str(diff[:30])
assert re.search(r'<pre id="team-task">.*?</pre>',old,re.S)[0].replace('<pre id="team-task">','').replace('</pre>','')==re.search(r'<pre id="team-task"><code>(.*?)</code></pre>',new,re.S)[1]
ref=(root/'claude-ai/chetyre-mcp-claude-code/index.html').read_bytes()
pat=rb'<section class="cta"[^>]*>.*?</section>'
standard=re.search(pat,ref,re.S)[0]
def normalize_cta(cta):return re.sub(rb' id="[^"]*"',b'',cta,count=1)
variants=collections.defaultdict(list)
for p in sorted((root/'claude-ai').glob('*/index.html')):
 match=re.search(pat,p.read_bytes(),re.S)
 if not match:continue
 cta=match[0];variants[cta].append(str(p.relative_to(root)))
 assert normalize_cta(cta)==normalize_cta(standard),'Unexpected CTA difference: '+str(p)
for slug in ['komanda-ii-agentov-dlya-bloga','chatgpt-composio-prilozheniya']:
 assert re.search(pat,(root/'claude-ai'/slug/'index.html').read_bytes(),re.S)[0]==standard
assert sum(map(len,variants.values()))==51
summary={'baseline':'6b325b1','article_tokens':len(a),'word_diff_empty':True,'hermes_prompt_unchanged':True,'cta_pages':51,'cta_payload_byte_identical':True,'full_cta_variants_only_id':len(variants),'standard_sha256':hashlib.sha256(standard).hexdigest(),'variants':[{'opening':cta.split(b'>',1)[0].decode()+'>','count':len(paths),'sha256':hashlib.sha256(cta).hexdigest(),'pages':paths} for cta,paths in variants.items()]}
(audit/('verification-'+sys.argv[1]+'.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='variants'},ensure_ascii=False,indent=2))
