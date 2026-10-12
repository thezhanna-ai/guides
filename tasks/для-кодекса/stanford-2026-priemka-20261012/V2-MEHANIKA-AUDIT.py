from pathlib import Path
import subprocess, re, hashlib, json, html
ROOT = Path('/Users/zslepova/IvanOS/.worktrees/stanford-2026-konspekt')
OUT = Path('/Users/zslepova/IvanOS/tasks/для-кодекса/stanford-2026-priemka-20261012')
REL = 'claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
new = (ROOT / REL).read_text()
old = subprocess.check_output(['git', 'show', f'HEAD:{REL}'], cwd=ROOT, text=True)
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
find = lambda pat, s: re.findall(pat, s, re.S)
patterns = {'scripts': r'<script\b[^>]*>.*?</script>', 'styles': r'<style\b[^>]*>.*?</style>', 'header': r'<header id="nachalo">.*?</header>', 'original': r'<section\b[^>]*id="original"[^>]*>.*?</section>', 'figures': r'<figure\b[^>]*>.*?</figure>', 'CTA': r'<section class="cta"[^>]*>.*?</section>', 'footer': r'<footer\b[^>]*>.*?</footer>'}
checks = {}
for label, pat in patterns.items():
    before, after = find(pat, old), find(pat, new)
    checks[label] = {'equal_to_HEAD': before == after, 'old_count': len(before), 'new_count': len(after), 'sha256': [sha(s) for s in after]}
    assert before == after, label
assert checks['figures']['new_count'] == 4
article_pat = r'<article>(.*?)</article>'
article = find(article_pat, new)[0]
outside_new = re.sub(article_pat, '<article>[REMOVED]</article>', new, flags=re.S)
outside_old = re.sub(article_pat, '<article>[REMOVED]</article>', old, flags=re.S)
checks['outside_article'] = {'equal_to_HEAD': outside_new == outside_old, 'sha256': sha(outside_new)}
assert outside_new == outside_old
urlpat = r'https?://[^\s<>"\x27]+'
urls_old, urls_new = set(find(urlpat, old)), set(find(urlpat, new))
added_urls = sorted(urls_new - urls_old)
assert not added_urls, added_urls
inline_event_pat = r'\bon[a-z]+\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)'
assert find(inline_event_pat, new) == find(inline_event_pat, old)
js_url_pat = r'\b(?:href|src)\s*=\s*["\x27]\s*javascript:[^"\x27]*'
assert find(js_url_pat, new) == find(js_url_pat, old)
editable = article
for label in ['header', 'original', 'figures', 'CTA', 'footer']:
    editable = re.sub(patterns[label], '', editable, flags=re.S)
visible = lambda s: html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<!--.*?-->', '', s, flags=re.S)))
ma_pat = r'\bМа\b|\bлектор[а-яё]*\b'
count = lambda s: len(re.findall(ma_pat, s, re.I))
word_count = len(visible(article).split())
assert word_count == 3385 and word_count <= 3400, word_count
raw_count, visible_count, editable_count = count(article), count(visible(article)), count(visible(editable))
assert raw_count == 9 and visible_count == 8 and editable_count == 0
occurrences = [{'html_line': new.count('\n', 0, m.start()) + 1, 'match': m.group(0), 'context': html.unescape(new[max(0, m.start()-65):m.end()+80])} for m in re.finditer(ma_pat, new, re.I)]
changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
assert changed == [REL], changed
checks.update({'words_article': word_count, 'word_limit': 3400, 'word_limit_pass': True, 'Ma_lector_raw_article_count': raw_count, 'Ma_lector_visible_article_count': visible_count, 'Ma_lector_editable_count': editable_count, 'Ma_lector_all_HTML_occurrences': occurrences, 'added_external_urls': added_urls, 'removed_external_urls': sorted(urls_old-urls_new), 'inline_event_handlers_equal': True, 'javascript_URLs_equal': True})
result = {'head_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'HTML_SHA256': sha(new), 'html_bytes': len(new.encode()), 'tracked_changed_files': changed, 'checks': checks, 'exit_code': 0}
assert sha((ROOT/REL).read_text()) == result['HTML_SHA256']
(OUT/'V2-MEHANIKA-SECURITY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
diff = subprocess.check_output(['git', 'diff', '--', REL], cwd=ROOT, text=True)
(OUT/'V2-MEHANIKA-DIFF.log').write_text('COMMAND: git diff -- '+REL+'\nEXIT_CODE: 0\nHTML_SHA256: '+sha(new)+'\nOUTPUT:\n'+diff)
print(json.dumps(result, ensure_ascii=False, indent=2))
