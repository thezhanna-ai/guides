from pathlib import Path
import re,json,hashlib,subprocess,html
wt=Path('/Users/zslepova/IvanOS/.worktrees/stanford-2026-konspekt')
out=Path('/Users/zslepova/IvanOS/tasks/для-кодекса/stanford-2026-priemka-20261012')
p='claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
base=subprocess.check_output(['git','show','38cd949:'+p],cwd=wt).decode()
cur=(wt/p).read_text()
expected=base
steps=[]
def sub(old,new,label):
 global expected
 assert expected.count(old)==1,(label,expected.count(old))
 expected=expected.replace(old,new)
 steps.append(label)
def para(prefix,new,label):
 old=re.search(r'<p>'+re.escape(prefix)+r'.*?</p>',expected,re.S)[0]
 sub(old,'<p>'+new+'</p>',label)
sub('Лектор приводит расчёт: ускорить','Лектор называет такие цифры: ускорить','1: мысль 3 начало')
for phrase in ['нужную работу опиши в вопросе, отдельная нейросеть под неё не нужна','за каждым новым умением чата стоит долгое и дорогое обучение']:
 sub('<div class="result"><p><b>Как это связано с твоим чатом:</b> '+phrase+'</p></div>\n','','1: убрать чат '+phrase[:8])
sub('<h3>Что дали многочисленные примеры</h3>','<h3>Зачем понадобился миллион картинок</h3>','2: h3')
para('ImageNet - набор','ImageNet - набор из миллиона картинок с подписями, который собрала команда Фей-Фей Ли, профессора Стэнфорда. Следующий по размеру набор был примерно в 20 раз меньше, около 50 тысяч. На таких примерах учили распознавать предметы: точность выросла примерно с половины до 95% и выше (числа лектор назвал по памяти)','2: ImageNet')
para('Точность здесь -','Точность здесь - доля картинок, на которых предмет назван правильно. Это ответ на вопрос из первой мысли: как измерить «лучше»','2: точность')
para('Сначала лектор показывает робота','Сначала лектор показывает робота, который учится ходить: каждое его движение зависит от предыдущего, а при неудачном шаге он может упасть, и продолжить уже трудно. С текстом похоже: нейросеть пишет ответ по одному слову или части слова, и написанное раньше влияет на то, что будет дальше. А в выборе следующего слова есть доля случайности, поэтому один и тот же вопрос иногда даёт разные ответы','3: шаги')
old=re.search(r'<p>Готовое доказательство для сравнения.*?</p>\n<p>В примере со сдачей ниже.*?</p>',expected,re.S)[0]
sub(old,'<p>Как именно проверяют, вводная лекция не разбирает, важен порядок: для следующего обучения берут только попытки, которые прошли проверку</p>','4: два абзаца в один')
sub('<li><b>Разработчики снова обучают нейросеть.</b> Используют новые проверенные примеры</li>','<li><b>Разработчики обучают нейросеть на отобранных верных решениях</b></li>','4: действие 3')
para('Если сложить восемь мыслей','Все восемь мыслей сводятся к одному: нейросеть выдаёт то, чему её учили, и то, что ты ей задал. Это легко увидеть самому: задай вопрос как обычно, потом в новом чате тот же вопрос с добавкой и сравни ответы. Работает в ChatGPT, Claude и любом другом чат-боте','5: практика введение')
para('Запросы ниже наши','Запросы ниже наши, не из лекции. Ответы Claude даны выдержками из настоящих ответов, у тебя они получатся по-своему','5: источник ответов')
quotes=json.loads((wt/'tasks/для-кодекса/stanford-2026-priemka-20261012/V5-CITATY.json').read_text())
blocks={q['id']:'<div class="info-card" id="'+q['id']+'"><p><b>'+q['label']+'</b></p>'+q['body']+'</div>' for q in quotes}
anchor='<p><b>До и после. Проверка в Claude 12 октября.</b> Без добавки пришло 401 слово'
sub(anchor,blocks['otvet-1a']+'\n'+blocks['otvet-1b']+'\n'+anchor,'6: 1a/1b перед до/после')
anchor=re.search(r'<p><b>До и после\. Проверка в Claude 12 октября\.</b> Оба ответа верны.*?</p>',expected,re.S)[0]
sub(anchor,anchor+'\n'+blocks['otvet-2b'],'6: 2b после до/после')
sub('<div class="result"><p><b>Результат:</b> оба ответа верны. Но с добавкой в конце есть проверка, и если бы ошибка была, её было бы видно. Для денег всё равно пересчитай в калькуляторе</p></div>','<div class="result"><p><b>Результат:</b> цифра сдачи в обоих ответах одна. Но во втором её можно проверить за десять секунд, не пересчитывая всю задачу заново. Для денег всё равно сверь калькулятором</p></div>','6: результат 2')
sub('<p>Почему: Нейросеть пишет','<p>Почему: нейросеть пишет','6: регистр')
anchor=re.search(r'<p><b>До и после\. Проверка в Claude 12 октября\.</b> Без добавки пришли 12 названий.*?</p>',expected,re.S)[0]
sub(anchor,anchor+'\n'+blocks['otvet-3a']+'\n'+blocks['otvet-3b'],'6: 3a/3b после до/после')
sub('Нейросеть сама так учится: пробует, лучшее отбирают. Сделай то же с её ответами: попроси пять и выбери по критерию','Похожий порядок в мысли 8: сначала много попыток, потом отбор. В чате можно сделать так же: попроси несколько вариантов и выбор по условию, которое задал ты','6: критерий 3')
sub('<div class="result"><p><b>Результат:</b> памятку можно скопировать в заметку и вернуться к ней перед следующим вопросом</p></div>\n','','7: убрать служебный result')
sub('. Пример наш: просто чтобы показать разницу</p>','</p>','8: мета мысли 2')
assert expected==cur,'Unauthorised adjacent change'
def sha(x):return hashlib.sha256(x.encode() if isinstance(x,str) else x).hexdigest()
def get(src,pat):return re.search(pat,src,re.S)[0]
prot={}
for label,pat in {'head':r'<head>.*?</head>','h1':r'<h1\b.*?</h1>','eyebrow':r'<p class="eyebrow".*?</p>','meta':r'<p class="meta".*?</p>','level':r'<p class="uroven-metka.*?</p>','original':r'<section class="content-section" id="original">.*?</section>','cta':r'<section class="cta".*?</section>'}.items():
 a,b=get(base,pat),get(cur,pat);prot[label]={'byte_match':a==b,'sha256':sha(b)}
a,b=base.split('<article>'),cur.split('<article>')
prot['outside_article']={'byte_match':a[0]==b[0] and a[1].split('</article>')[1]==b[1].split('</article>')[1]}
for tag in ['script','style','figure']:
 aa=re.findall(r'<'+tag+r'\b.*?</'+tag+'>',base,re.S);bb=re.findall(r'<'+tag+r'\b.*?</'+tag+'>',cur,re.S)
 prot[tag]={'byte_match':aa==bb,'count':len(bb),'sha256s':[sha(v) for v in bb]}
paths=['data/statyi.json','index.html','sitemap.xml']+[str(x.relative_to(wt)) for x in (wt/'claude-ai/stanford-2026-kak-uchitsya-ii/assets').iterdir()]
for name in paths:
 bb=(wt/name).read_bytes();aa=subprocess.check_output(['git','show','38cd949:'+name],cwd=wt)
 prot[name]={'byte_match':aa==bb,'sha256':sha(bb)}
assert all(v['byte_match'] for v in prot.values())
assert prot['figure']['count']==4
secids=['opyt','prompt','skorost','imagenet','slova','instrukcii','mysli','popytki']
structure=[]
for i,sid in enumerate(secids,1):
 part=get(cur,r'<section class="content-section" id="'+sid+r'">.*?</section>')
 h2=get(part,r'<h2>.*?</h2>')
 assert part.index('Смотреть с')<part.index('<h2>')
 structure.append({'thought':i,'id':sid,'h2':re.sub('<[^>]*>','',h2),'h3':re.findall(r'<h3>(.*?)</h3>',part),'result_count':part.count('class="result"'),'figures':part.count('<figure'),'opening_paragraph_before_h3':part.index('</h2>')<part.index('<p>',part.index('</h2>')) and ('<h3>' not in part or part.index('<p>',part.index('</h2>'))<part.index('<h3>'))})
practice=get(cur,r'<section class="content-section" id="practice">.*?</section>')
pre=re.findall(r'<pre\b[^>]*id="([^"]+)"[^>]*>(.*?)</pre>',practice,re.S)
assert len(pre)==6
buttons=re.findall(r'<button\b[^>]*data-copy-target="([^"]+)"[^>]*>',practice)
assert [x[0] for x in pre]==buttons
assert re.findall(r'<pre\b.*?</pre>',get(base,r'<section class="content-section" id="practice">.*?</section>'),re.S)==re.findall(r'<pre\b.*?</pre>',practice,re.S)
assert re.findall(r'<button\b.*?</button>',get(base,r'<section class="content-section" id="practice">.*?</section>'),re.S)==re.findall(r'<button\b.*?</button>',practice,re.S)
attrs=lambda s:re.findall(r'\b(?:href|src|style|on[a-z]+)\s*=\s*[\"\'][^\"\']*[\"\']',s)
assert attrs(base)==attrs(cur)
row=next(x for x in json.loads((wt/'data/statyi.json').read_text())['statyi'] if x['slug']=='stanford-2026-kak-uchitsya-ii')
quote_checks=[]
for q in quotes:
 src=(wt/'tasks/для-кодекса/stanford-2026-priemka-20261012/PROGONY'/q['fixture']).read_text()
 assert sha(src)==q['source_sha256']
 assert all(part in src for part in q['parts'])
 clean=lambda text:' '.join(html.unescape(re.sub('<[^>]+>','',re.sub(r'<br>|</(?:p|li)>',' ',text))).replace('**','').split())
 raw=re.sub(r'^\d+\. |^- ','','\n'.join(q['parts']),flags=re.M)
 assert clean(q['body'])==clean(raw)
 quote_checks.append({'id':q['id'],'fixture':q['fixture'],'sha256':sha(src),'verbatim':True})
result={'html_sha256':sha(cur),'base_commit':'38cd949','exact_reconstruction':expected==cur,'authorized_changes':steps,'protected':prot,'thought_structure':structure,'practice_pre_ids':[x[0] for x in pre],'copy_targets':buttons,'attrs_byte_equal':attrs(base)==attrs(cur),'draft':{k:row[k] for k in ['status','vydacha','kod_slovo']},'noindex_nofollow':'<meta name="robots" content="noindex, nofollow">' in cur,'quotes':quote_checks}
(out/'V5-STRUKTURA-SECURITY-EVIDENCE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
