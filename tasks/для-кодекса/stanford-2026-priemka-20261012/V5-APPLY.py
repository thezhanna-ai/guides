from pathlib import Path
import re, html, json, hashlib, subprocess
ROOT=Path('/Users/zslepova/IvanOS')
WT=ROOT/'.worktrees/stanford-2026-konspekt'
OUT=ROOT/'tasks/для-кодекса/stanford-2026-priemka-20261012'
REL='claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
page=WT/REL
base=subprocess.check_output(['git','show','38cd949:'+REL],cwd=WT).decode()
s=base
ops=[]
def replace(old,new,label):
    global s
    assert s.count(old)==1,(label,s.count(old))
    s=s.replace(old,new)
    ops.append({'item':label,'old':old,'new':new})
def para(prefix):
    found=[p for p in re.findall(r'<p\b[^>]*>.*?</p>',s,re.S) if html.unescape(re.sub('<[^>]+>','',p)).startswith(prefix)]
    assert len(found)==1,(prefix,len(found))
    return found[0]
def p(t): return '<p>'+t+'</p>'
def section(sid): return re.search(r'<section\b[^>]*id="'+sid+r'"[^>]*>.*?</section>',s,re.S)[0]
replace('Лектор приводит расчёт: ускорить обучение вдвое','Лектор называет такие цифры: ускорить обучение вдвое','1-speed')
for sid in ['prompt','skorost']:
    replace(re.search(r'<div class="result">.*?</div>\n',section(sid),re.S)[0],'','1-delete-'+sid)
replace('Что дали многочисленные примеры','Зачем понадобился миллион картинок','2-heading')
replace(para('ImageNet - набор'),p('ImageNet - набор из миллиона картинок с подписями, который собрала команда Фей-Фей Ли, профессора Стэнфорда. Следующий по размеру набор был примерно в 20 раз меньше, около 50 тысяч. На таких примерах учили распознавать предметы: точность выросла примерно с половины до 95% и выше (числа лектор назвал по памяти)'),'2-imagenet')
replace(para('Точность здесь -'),p('Точность здесь - доля картинок, на которых предмет назван правильно. Это ответ на вопрос из первой мысли: как измерить «лучше»'),'2-accuracy')
replace(para('Сначала лектор показывает робота'),p('Сначала лектор показывает робота, который учится ходить: каждое его движение зависит от предыдущего, а при неудачном шаге он может упасть, и продолжить уже трудно. С текстом похоже: нейросеть пишет ответ по одному слову или части слова, и написанное раньше влияет на то, что будет дальше. А в выборе следующего слова есть доля случайности, поэтому один и тот же вопрос иногда даёт разные ответы'),'3-sequence')
old=para('Готовое доказательство для сравнения')+'\n'+para('В примере со сдачей ниже')
replace(old,p('Как именно проверяют, вводная лекция не разбирает, важен порядок: для следующего обучения берут только попытки, которые прошли проверку'),'4-proof')
replace('<li><b>Разработчики снова обучают нейросеть.</b> Используют новые проверенные примеры</li>','<li><b>Разработчики обучают нейросеть на отобранных верных решениях</b></li>','4-train')
replace(para('Если сложить восемь мыслей'),p('Все восемь мыслей сводятся к одному: нейросеть выдаёт то, чему её учили, и то, что ты ей задал. Это легко увидеть самому: задай вопрос как обычно, потом в новом чате тот же вопрос с добавкой и сравни ответы. Работает в ChatGPT, Claude и любом другом чат-боте'),'5-intro')
replace(para('Запросы ниже наши'),p('Запросы ниже наши, не из лекции. Ответы Claude даны выдержками из настоящих ответов, у тебя они получатся по-своему'),'5-excerpts')
# Markdown-разметку источника переводим в HTML; слова и пунктуация остаются дословными
def inline(t):
    t=html.escape(t,quote=False)
    return re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t)
quotes=[]
def quote(qid,label,fixture,parts,body):
    src=(OUT/'PROGONY'/fixture).read_text()
    assert all(part in src for part in parts),(qid,parts)
    quotes.append({'id':qid,'label':label,'fixture':fixture,'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'parts':parts,'body':body})
    return '<div class="info-card" id="'+qid+'">'+p('<b>'+label+'</b>')+body+'</div>\n'
a=(OUT/'PROGONY/1a.txt').read_text().split('\n\n')[1]
q1=quote('otvet-1a','Ответ без добавки (выдержка, всего 401 слово)','1a.txt',[a],p(inline(a)))
b=(OUT/'PROGONY/1b.txt').read_text().rstrip('\n')
q1+=quote('otvet-1b','Ответ с добавкой, целиком (64 слова)','1b.txt',[b],p(inline(b)))
first=re.findall(r'<p><b>До и после\. Проверка в Claude 12 октября\.</b>.*?</p>',s,re.S)[0]
replace(first,q1+first,'6-reception-1')
q2src=(OUT/'PROGONY/2b.txt').read_text()
q2parts=[part.strip() for part in re.search(r'1\. Сдача.*?(?=\n\n\*\*Ответ)',q2src,re.S)[0].split('\n')]
# Сохраняем три проверки целыми, меняется только оформление нумерации и переноса строки
checks=re.findall(r'\d\. (.*?)(?=\n\d\. |$)',re.search(r'1\. Сдача.*?(?=\n\n\*\*Ответ)',q2src,re.S)[0],re.S)
q2=quote('otvet-2b','Проверка из ответа с добавкой (выдержка)','2b.txt',checks,'<ol>'+''.join('<li>'+inline(c).replace('\n   ','<br>')+'</li>' for c in checks)+'</ol>')
second=re.findall(r'<p><b>До и после\. Проверка в Claude 12 октября\.</b>.*?</p>',s,re.S)[1]
replace(second,second+'\n'+q2.rstrip(),'6-reception-2')
replace(para('Результат: оба ответа верны.'),p('<b>Результат:</b> цифра сдачи в обоих ответах одна. Но во втором её можно проверить за десять секунд, не пересчитывая всю задачу заново. Для денег всё равно сверь калькулятором'),'6-result-2')
replace('Почему: Нейросеть','Почему: нейросеть','6-case')
favsrc=(OUT/'PROGONY/3a.txt').read_text()
favs=re.search(r'1\. \*\*«Декрет в плюсе».*?(?=\n\nЕсли)',favsrc,re.S)[0]
q3=quote('otvet-3a','Без добавки (выдержка): три «фаворита»','3a.txt',[favs],'<ol>'+''.join('<li>'+inline(re.sub(r'^\d\. ','',x))+'</li>' for x in favs.splitlines())+'</ol>')
src=(OUT/'PROGONY/3b.txt').read_text()
choice='**«Деньги в декрете».**'
why=src.split('Почему:\n')[1].split('\n\n')[0].splitlines()[2:4]
dry='Сухость, главный минус этого варианта, легко компенсировать описанием канала или подзаголовком.'
q3+=quote('otvet-3b','С добавкой (выдержка): выбор и причина','3b.txt',[choice,'Почему:',*why,dry],p(inline(choice))+p('Почему:')+'<ul>'+''.join('<li>'+inline(x[2:])+'</li>' for x in why)+'</ul>'+p(dry))
third=re.findall(r'<p><b>До и после\. Проверка в Claude 12 октября\.</b>.*?</p>',s,re.S)[2]
replace(third,third+'\n'+q3.rstrip(),'6-reception-3')
replace('Нейросеть сама так учится: пробует, лучшее отбирают. Сделай то же с её ответами: попроси пять и выбери по критерию','Похожий порядок в мысли 8: сначала много попыток, потом отбор. В чате можно сделать так же: попроси несколько вариантов и выбор по условию, которое задал ты','6-criterion')
replace('<div class="result"><p><b>Результат:</b> памятку можно скопировать в заметку и вернуться к ней перед следующим вопросом</p></div>\n','','7-delete-service-result')
replace('. Пример наш: просто чтобы показать разницу','','8-meta')
# Документированная замена из ТЗ позволяет удалить финальную точку вместе с фразой
# После удаления метапометки предыдущая фраза становится концом абзаца без точки
if __name__=='__main__':
    assert page.read_text()==base,'Worktree changed, do not overwrite'
    page.write_text(s)
    (OUT/'V5-DOSLOVNYE-ZAMENY.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2)+'\n')
    (OUT/'V5-CITATY.json').write_text(json.dumps(quotes,ensure_ascii=False,indent=2)+'\n')
    print('APPLIED',len(ops),'operations;',len(quotes),'quote blocks; HTML SHA256',hashlib.sha256(s.encode()).hexdigest())
