from pathlib import Path
import contextlib,io,json,hashlib
wt=Path('/Users/zslepova/IvanOS/.worktrees/stanford-2026-konspekt')
out=Path('/Users/zslepova/IvanOS/tasks/для-кодекса/stanford-2026-priemka-20261012')
h=wt/'tasks/для-кодекса/stanford-2026-konspekt/proverka.py'
code=h.read_text();src=(wt/'claude-ai/stanford-2026-kak-uchitsya-ii/index.html').read_text()
def run(s):
 with contextlib.redirect_stdout(io.StringIO()):
  exec(compile(code.replace('source = PAGE.read_text()','source = '+repr(s)),str(h),'exec'),{'__file__':str(h),'__name__':'__main__'})
run(src)
anchor='<section class="content-section" id="sources">'
mutations={
'quote_changed':src.replace('это математическая модель, которая','это математическая моделька, которая',1),
'quote_missing':src.replace('id="otvet-1a"','id="otvet-1a-missing"',1),
'outside_ad_name':src.replace(anchor,'<p>Иван</p>'+anchor),
'outside_quote_payment':src.replace(anchor,'<p>Оплата</p>'+anchor),
'outside_quote_step_zero':src.replace(anchor,'<p>Шаг 0</p>'+anchor),
'outside_quote_gender':src.replace(anchor,'<p>ты сделал</p>'+anchor),
'outside_quote_long_dash':src.replace(anchor,'<p>Ответ — пример</p>'+anchor),
'outside_quote_final_dot':src.replace(anchor,'<p>Ответ.</p>'+anchor),
'broken_copy_target':src.replace('data-copy-target="priem-1-do"','data-copy-target="wrong-target"',1)
}
results={}
for name,s in mutations.items():
 try:
  run(s);results[name]={'rejected':False}
 except AssertionError as ex:
  results[name]={'rejected':True,'reason':str(ex)}
assert all(x['rejected'] for x in results.values())
report={'helper_sha256':hashlib.sha256(h.read_bytes()).hexdigest(),'baseline':'PASS','mutations':results}
(out/'V5-HELPER-SECURITY-MUTATIONS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
