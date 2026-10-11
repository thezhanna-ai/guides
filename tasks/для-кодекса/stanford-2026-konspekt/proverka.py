"""Mechanical evidence for this draft; run from the worktree without a browser."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests'))
from test_site import ImageDocument

SLUG = 'stanford-2026-kak-uchitsya-ii'
PAGE = ROOT / 'claude-ai' / SLUG / 'index.html'
source = PAGE.read_text()
reference = (ROOT / 'claude-ai/stanford-kak-sozdayut-chatgpt/index.html').read_text()
cta_reference = (ROOT / 'claude-ai/chetyre-mcp-claude-code/index.html').read_text()
article = re.search(r'<article>(.*?)</article>', source, re.S)[1]
ref_article = re.search(r'<article>(.*?)</article>', reference, re.S)[1]
cta_pattern = r'<section class="cta"[^>]*>.*?</section>'
cta = re.search(cta_pattern, source, re.S)[0]
prose = re.sub(cta_pattern, '', article, flags=re.S)
doc = ImageDocument(source)
text = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', prose)).split())

def words(markup):
    clean = re.sub(r'<!--.*?-->', '', markup, flags=re.S)
    return len(html.unescape(re.sub(r'<[^>]+>', ' ', clean)).split())

results = {
    'words_new': words(article),
    'words_reference': words(ref_article),
    'word_difference_percent': round((words(article) / words(ref_article) - 1) * 100, 2),
    'long_dashes_entire_html': len(re.findall('[—–]', source)),
    'foreign_names_outside_ad': len(re.findall(r'иван|сергеев|ivan_ai', text, re.I)),
    'price_words_outside_ad': len(re.findall(r'бесплатн|платн|оплат|платить', text, re.I)),
    'step_zero': len(re.findall(r'Шаг\s*0', text, re.I)),
    'gendered_reader_forms': len(re.findall(r'\bты\s+[а-яё]+(?:л|ла|ли)\b', text, re.I)),
    'gendered_reflexive_address': len(re.findall(r'тебя\s+самого|нужно\s+самому|учиться\s+самому', text, re.I)),
    'formula_markers_in_article': len(re.findall(r'<math|\\\\(?:frac|begin)|функци[яию]\s+потерь|градиент|backprop', article, re.I)),
    'paragraph_final_dots': 0,
    'prompt_final_dots': 0,
    'paragraph_bad_endings': 0,
    'cta_byte_match': cta.encode() == re.search(cta_pattern, cta_reference, re.S)[0].encode(),
    'cta_sha256': hashlib.sha256(cta.encode()).hexdigest(),
    'thoughts': re.findall(r'<h2>(Мысль\s+\d+\..*?)</h2>', article),
    'formatting': {},
    'broken_local_fragments': [],
    'broken_copy_targets': [],
    'image_dimensions': {},
}
for attrs, body in re.findall(r'<p\b([^>]*)>(.*?)</p>', prose, re.S):
    if re.search(r'class="(?:eyebrow|meta|section-label|uroven-metka|cta-question|next-sub)(?: |")', attrs):
        continue
    value = html.unescape(re.sub(r'<[^>]+>', '', body)).strip()
    if value.endswith('.'):
        results['paragraph_final_dots'] += 1
    if value and not re.search(r'[А-Яа-яЁё0-9»)?!…:]$', value):
        results['paragraph_bad_endings'] += 1
for body in re.findall(r'<pre\b[^>]*>(.*?)</pre>', prose, re.S):
    value = html.unescape(re.sub(r'<[^>]+>', '', body)).strip()
    results['prompt_final_dots'] += value.endswith('.')
ids = {n.attrs.get('id') for n in doc.root.all() if n.attrs.get('id')}
for a in doc.root.all(tag='a'):
    href = a.attrs.get('href', '')
    if href.startswith('#') and href[1:] not in ids:
        results['broken_local_fragments'].append(href)
for b in doc.root.all(tag='button'):
    target = b.attrs.get('data-copy-target')
    if target and target not in ids:
        results['broken_copy_targets'].append(target)
for label,pattern in [('b',r'<b>'),('h3',r'<h3>'),('lists',r'<(?:ul|ol)\b'),('result',r'class="result"'),('warn-card',r'class="warn-card"'),('info-card',r'class="info-card"'),('code-card',r'class="code-card"'),('help-banner',r'class="help-banner"'),('figures',r'<figure\b')]:
    results['formatting'][label] = {'new':len(re.findall(pattern,article)), 'reference':len(re.findall(pattern,ref_article))}
zakryt = (ROOT / 'claude-ai/zakryt-sekrety-ot-claude-code/index.html').read_text()
zakryt_article = re.search(r'<article>(.*?)</article>', zakryt, re.S)[1]
results['additional_reference_formatting'] = {}
for label,pattern in [('b',r'<b>'),('result',r'class="result"'),('warn-card',r'class="warn-card"')]:
    counts = {'new':len(re.findall(pattern,article)), 'zakryt':len(re.findall(pattern,zakryt_article))}
    assert counts['new'] >= counts['zakryt'], (label,counts)
    results['additional_reference_formatting'][label] = counts
import struct
for img in doc.root.all(tag='img'):
    if not img.attrs.get('src'):
        continue
    path = PAGE.parent / img.attrs['src']
    assert path.is_file(), path
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    dims = struct.unpack('>II',data[16:24])
    assert dims == (int(img.attrs['width']),int(img.attrs['height']))
    results['image_dimensions'][path.name] = {'width':dims[0], 'height':dims[1], 'sha256':hashlib.sha256(data).hexdigest()}
registry = json.loads((ROOT/'data/statyi.json').read_text())['statyi']
row = next(x for x in registry if x['slug'] == SLUG)
results['metadata_description_match'] = all(
    html.unescape(re.search(pattern, source)[1]) == row['description']
    for pattern in [r'<meta name="description" content="([^"]+)"', r'<meta property="og:description" content="([^"]+)"']
)
results['draft_state'] = {k:row[k] for k in ['status','vydacha','kod_slovo']}
results['noindex'] = '<meta name="robots" content="noindex, nofollow">' in source
results['absent_from_home'] = f'href="claude-ai/{SLUG}/"' not in (ROOT/'index.html').read_text()
results['absent_from_sitemap'] = SLUG not in (ROOT/'sitemap.xml').read_text()
assert 0.85 <= results['words_new']/results['words_reference'] <= 1.15
for k in ['long_dashes_entire_html','foreign_names_outside_ad','price_words_outside_ad','step_zero','gendered_reader_forms','gendered_reflexive_address','formula_markers_in_article','paragraph_final_dots','prompt_final_dots','paragraph_bad_endings']:
    assert results[k] == 0, (k,results[k])
assert results['metadata_description_match']
assert results['cta_byte_match'] and len(results['thoughts']) == 8
assert results['noindex'] and results['absent_from_home'] and results['absent_from_sitemap']
assert results['draft_state'] == {'status':'draft','vydacha':'net','kod_slovo':''}
assert not results['broken_local_fragments'] and not results['broken_copy_targets']
for label,counts in results['formatting'].items():
    assert counts['new'] >= counts['reference'], (label,counts)
print(json.dumps(results,ensure_ascii=False,indent=2))
