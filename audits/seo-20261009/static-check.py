"""Сплошная инспекция страниц; запуск из корня: python static-check.py.
Нужны beautifulsoup4 и Pillow, например во временном venv.
"""
import collections
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup

ROOT = Path.cwd()
BASE = 'https://pronovoe.com/'
metadata = json.loads((ROOT / 'data/seo.json').read_text())
paths = [ROOT / 'index.html', ROOT / 'politika/index.html', *sorted(ROOT.glob('claude-ai/*/index.html'))]
records = []
errors = []
links = []
image_stats = collections.Counter()
protected = []
heading_changes = []

def text(soup):
    # Сравниваем исходную прозу, исключая явно разрешённые поисковые заголовки и TOC
    for node in soup.select('head,script,style,h1,h2,a[href^="#"]'):
        node.decompose()
    return ' '.join(soup.get_text(' ', strip=True).split())

for page in paths:
    rel = page.relative_to(ROOT).as_posix()
    raw = page.read_text()
    before = subprocess.check_output(['git', 'show', '2b5a5e2:' + rel], text=True)
    soup = BeautifulSoup(raw, 'html.parser')
    url = BASE + rel.removesuffix('index.html')
    h1 = soup.find_all('h1')
    if len(h1) != 1: errors.append(rel + ': H1 count')
    canonicals = soup.select('link[rel="canonical"]')
    if len(canonicals) != 1 or canonicals[0]['href'] != url: errors.append(rel + ': canonical')
    if re.search(r'<meta[^>]+content="[^"]*noindex', raw): errors.append(rel + ': noindex')
    schemas = soup.select('script[type="application/ld+json"]')
    try:
        graph = json.loads(schemas[0].get_text())['@graph']
    except (IndexError, KeyError, json.JSONDecodeError): errors.append(rel + ': invalid schema'); graph = []
    ids = [x['id'] for x in soup.select('[id]')]
    duplicates = [i for i, n in collections.Counter(ids).items() if n > 1]
    if duplicates:errors.append(rel + ': repeated ids ' + str(duplicates))
    for a in soup.select('a[href]'):
        href = a['href']; parsed = urlparse(urljoin(url, href))
        if parsed.hostname != 'pronovoe.com':continue
        target = ROOT / unquote(parsed.path).lstrip('/')
        if not target.suffix:target = target / 'index.html'
        links.append({'source':url, 'target':parsed._replace(fragment='', query='').geturl(), 'fragment':parsed.fragment})
        if not target.is_file():errors.append(rel + ': missing link ' + href); continue
        if parsed.path.endswith('index.html') or (target.name == 'index.html' and not parsed.path.endswith('/')):
            errors.append(rel + ': noncanonical internal URL ' + href)
        if parsed.fragment and parsed.fragment not in {x['id'] for x in BeautifulSoup(target.read_text(), 'html.parser').select('[id]')}:
            errors.append(rel + ': missing anchor ' + href)
    for tag in soup.select('img'):
        image_stats['total'] += 1
        src = tag.get('src', '')
        if not src:image_stats['dynamic_viewer'] += 1; continue
        if not tag.get('alt'):errors.append(rel + ': image without descriptive alt ' + src[:90])
        if not (tag.get('width') and tag.get('height')):errors.append(rel + ': image without dimensions ' + src[:90])
        image_stats[Path(urlparse(src).path).suffix.lower() or 'embedded'] += 1
        image_stats['loading_' + tag.get('loading', 'default')] += 1
        if not src.startswith(('data:', 'https://', 'http://')):
            target = ROOT / src.lstrip('/') if src.startswith('/') else page.parent / src
            if not target.is_file():errors.append(rel + ': missing image ' + src)
    for selector in ('link[href]', 'script[src]'):
        for node in soup.select(selector):
            href = node.get('href', node.get('src',''))
            if href.startswith(('http:', 'https:', 'data:')):continue
            if node.get('rel') == ['canonical']:continue
            path = ROOT / href.lstrip('/') if href.startswith('/') else page.parent / href
            if not path.is_file():errors.append(rel + ': missing asset ' + href)
    original_soup = BeautifulSoup(before, 'html.parser')
    old_headings = [n.get_text(' ',strip=True) for n in original_soup.find_all(['h1','h2'])]
    new_headings = [n.get_text(' ',strip=True) for n in soup.find_all(['h1','h2']) if not n.find_parent(class_=re.compile('seo-'))]
    heading_changes.append({'page':rel,'before':old_headings,'after':new_headings})
    pattern = r'<section\b[^>]*class="cta"[^>]*>.*?</section>'
    old_cta = re.findall(pattern,before,re.S);new_cta = re.findall(pattern,raw,re.S)
    if not old_cta or old_cta != new_cta:errors.append(rel + ': protected CTA bytes changed')
    # Own marker stripping is independent of the production generator
    stripped = re.sub(r'<!-- seo:[a-z]+:start -->.*?<!-- seo:[a-z]+:end -->', '', raw, flags=re.S)
    original_prose = text(BeautifulSoup(before,'html.parser'))
    current_prose = text(BeautifulSoup(stripped,'html.parser'))
    prose_equal = original_prose == current_prose
    if not prose_equal:errors.append(rel + ': original prose changed outside headings/TOC')
    protected.append({'page':rel,'cta_sha256_before':[hashlib.sha256(x.encode()).hexdigest() for x in old_cta], 'cta_sha256_after':[hashlib.sha256(x.encode()).hexdigest() for x in new_cta],'prose_equal':prose_equal})
    records.append({'path':rel,'url':url,'title':soup.title.get_text(),'description':soup.select_one('meta[name="description"]')['content'],'h1':h1[0].get_text(' ',strip=True),'quick_words':len((soup.select_one('.quick-answer') or BeautifulSoup('','html.parser')).get_text(' ',strip=True).split()),'schema_types':[x['@type'] for x in graph]})
# Homepage has CTA; policy deliberately has no advertising block
errors = [x for x in errors if x != 'politika/index.html: protected CTA bytes changed']
for field in ('title','description'):
    c = collections.Counter(x[field] for x in records)
    if any(n>1 for n in c.values()):errors.append('Duplicate '+field)
    for x in records:
        bounds=(20,65) if field=='title' else (70,165)
        if not bounds[0] <= len(x[field]) <= bounds[1]:errors.append(x['path']+': metadata length '+field)
for x in records:
    x['inlinks_all'] = len({l['source'] for l in links if l['target']==x['url'] and l['source']!=x['url']})
    x['inlinks_articles'] = len({l['source'] for l in links if l['target']==x['url'] and l['source']!=x['url'] and '/claude-ai/' in l['source']})
    if '/claude-ai/' in x['url'] and not x['inlinks_articles']:errors.append(x['path']+': orphan without article inlink')
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap=ET.parse(ROOT/'sitemap.xml')
entries=sitemap.findall('s:url',ns)
if {e.find('s:loc',ns).text for e in entries}!={x['url'] for x in records}:errors.append('Sitemap mismatch')
for e in entries:
    url=e.find('s:loc',ns).text
    if e.find('s:lastmod',ns).text!=metadata[url.removeprefix(BASE)+'index.html']['lastmod']:errors.append('lastmod mismatch '+url)
# All tracked image files remain byte-identical to the source commit
binary_changes = subprocess.check_output(['git','diff','--name-only','2b5a5e2'],text=True).splitlines()
changed_images = [x for x in binary_changes if Path(x).suffix.lower() in ('.png','.jpg','.jpeg','.webp','.svg','.gif')]
if changed_images:errors.append('Image source bytes changed '+str(changed_images))
result={'pages':len(records),'errors':errors,'images':dict(image_stats),'changed_source_images':changed_images,'records':records,'protected_content':protected,'heading_changes':heading_changes,'links':links}
(ROOT/'audits/seo-20261009/static-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pages':len(records),'errors':errors,'images':dict(image_stats),'source_images_changed':changed_images,'min_article_inlinks':min(x['inlinks_articles'] for x in records if '/claude-ai/' in x['url'])},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
