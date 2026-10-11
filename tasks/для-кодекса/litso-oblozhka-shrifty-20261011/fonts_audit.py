"""Offline typography cascade inspection. No browser, HTTP or page execution."""
from pathlib import Path
import json, re, subprocess
from bs4 import BeautifulSoup
import soupsieve
import tinycss2

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PAGE = 'claude-ai/otsenka-vneshnosti-po-foto-v-chatgpt/index.html'
REF = 'claude-ai/chetyre-mcp-claude-code/index.html'
BASE = '66f3334'
FIELDS = ('font-family', 'font-size', 'font-weight', 'font-style', 'line-height')
ELEMENTS = [
 ('Шапка: название', '.brand', '.brand'),
 ('Шапка: название статьи', '.handout-title', '.handout-title'),
 ('Шапка: переключатель темы', '.theme-toggle', '.theme-toggle'),
 ('Рубрика', '.eyebrow', '.eyebrow'),
 ('H1', 'h1', 'h1'), ('Метка уровня', '.uroven-metka', '.uroven-metka'),
 ('Вступление', '.lead', '.lead'), ('Дата', '.meta', '.meta'),
 ('H2', '.content-section h2', '.content-section h2'),
 ('H3 (правило, в ЛИЦО отсутствует)', '#typography-probe h3', '#typography-probe h3'),
 ('Абзац', '.content-section > p', '.content-section > p'),
 ('Жирный текст', '.content-section p b', '.content-section p b'),
 ('Ссылка', '.content-section p a', '.content-section p a'),
 ('Список', '.content-section li', '.content-section li'),
 ('Предупреждение: абзац', '.warn-card p', '.warn-card p'),
 ('Предупреждение: жирный текст', '.warn-card b', '.content-section p b'),
 ('Плашка промпта: текст', '.code-card pre', '.code-card pre'),
 ('Плашка промпта: code', '.code-card pre code', '.code-card pre code'),
 ('Плашка промпта: кнопка', '.code-card .copy-button', '.code-card .copy-button'),
 ('Подпись к изображению', '.shot-fig figcaption', '.shot figcaption'),
 ('Результат: текст', '.result p', '.result p'),
 ('Результат: жирная метка', '.result b', '.result b'),
 ('Оглавление: метка', '.toc-label', '.toc-label'),
 ('Оглавление: ссылка', '.toc a', '.toc a'),
 ('Оглавление на телефоне: заголовок', '.mobile-toc summary', '.mobile-toc summary'),
 ('Оглавление на телефоне: ссылка', '.mobile-toc a', '.mobile-toc a'),
 ('Ещё про фото: метка', '.related-plaque .plaque-label', '.related-plaque .plaque-label'),
 ('Ещё про фото: заголовок', '.related-plaque h2', '.related-plaque h2'),
 ('Ещё про фото: ссылка', '.related-plaque a', '.related-plaque a'),
 ('Помощь: заголовок', '.help-banner h2', '.help-title'),
 ('Помощь: пояснение', '.help-banner > p', '.help-demo .me p'),
 ('Реклама: вопрос перед блоком', '.cta-question', '.cta-question'),
 ('Реклама: заголовок', '.cta h2', '.cta h2'),
 ('Реклама: описание', '.cta > p', '.cta > p'),
 ('Реклама: кнопка', '.cta .press-button', '.cta .press-button'),
 ('Реклама: маркировка', '.ad-disclosure', '.ad-disclosure'),
 ('Футер: ссылка', '.privacy-footer a', '.privacy-footer a'),
 ('Футер: кнопка', '.privacy-footer button', '.privacy-footer button'),
 ('Обложка: подпись', '.cover-v2 figcaption', '.cover-v2 figcaption'),
]

def source(path, revision):
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT, text=True)

def media_active(query, width):
    # Font rules here depend only on viewport width. Other media have no font declarations.
    for branch in query.split(','):
        if 'print' in branch or 'prefers-' in branch or 'hover:' in branch:
            continue
        bounds = re.findall(r'(min|max)-width\s*:\s*([\d.]+)px', branch)
        if all(width >= float(n) if side == 'min' else width <= float(n) for side,n in bounds):
            return True
    return False

def specificity(selector):
    # All font-bearing selectors in these documents use types/classes/attributes only.
    assert not any(x in selector for x in (':is(', ':where(', ':not(', ':has(')), selector
    ids = len(re.findall(r'#[\w-]+', selector))
    attrs = len(re.findall(r'\[[^]]*\]', selector))
    s = re.sub(r'\[[^]]*\]', '', selector)
    classes = len(re.findall(r'\.[\w-]+|:(?!:)[\w-]+', s)) + attrs
    s = re.sub(r'[#.][\w-]+|::?[\w-]+', '', s)
    types = len(re.findall(r'(?<![\w-])[a-zA-Z][\w-]*', s))
    return (0, ids, classes, types)

def expand(decl):
    value = tinycss2.serialize(decl.value).strip()
    if decl.name in FIELDS:
        return [(decl.name, value)]
    if decl.name != 'font':
        return []
    if value in ('inherit', 'initial', 'unset'):
        return [(k, value) for k in FIELDS]
    tokens = [x for x in decl.value if x.type not in ('whitespace','comment')]
    index = next(i for i,t in enumerate(tokens) if t.type in ('dimension','percentage','function'))
    prefix = tokens[:index]
    weight = next((str(int(t.value)) for t in prefix if t.type == 'number'),
                  next((t.value for t in prefix if t.type == 'ident' and t.value in ('bold','bolder','lighter')), '400'))
    style = next((t.value for t in prefix if t.type == 'ident' and t.value in ('italic','oblique')), 'normal')
    size = tinycss2.serialize([tokens[index]])
    index += 1
    height = 'normal'
    if tokens[index].type == 'literal' and tokens[index].value == '/':
        height = tinycss2.serialize([tokens[index+1]])
        index += 2
    family = tinycss2.serialize(tokens[index:])
    return list(zip(FIELDS,(family,size,weight,style,height)))

def rules(css, width):
    for rule in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if rule.type == 'at-rule' and rule.lower_at_keyword == 'media' and rule.content:
            if media_active(tinycss2.serialize(rule.prelude),width):
                yield from rules(tinycss2.serialize(rule.content),width)
        elif rule.type == 'qualified-rule':
            decls = [(d, expand(d)) for d in tinycss2.parse_declaration_list(rule.content,skip_comments=True,skip_whitespace=True) if d.type == 'declaration']
            selected = [(name,value,d.important) for d,items in decls for name,value in items]
            if selected:
                for selector in tinycss2.serialize(rule.prelude).split(','):
                    yield selector.strip(), selected

def family(value):
    return ', '.join(part.strip().strip('\"\'') for part in value.split(','))

def length(value, parent, width):
    value = value.strip()
    if value.startswith('clamp('):
        args = value[6:-1].split(',')
        a,b,c = [length(x,parent,width) for x in args]
        return max(a,min(b,c))
    m = re.fullmatch(r'([\d.]+)(px|em|rem|vw|%)?',value)
    assert m, value
    n = float(m[1]); unit=m[2]
    return n * {'px':1,'em':parent,'rem':16,'vw':width/100,'%':parent/100,None:1}[unit]

def inspect(html, revision, width):
    soup = BeautifulSoup(html,'html.parser')
    probe=soup.new_tag('section',id='typography-probe',attrs={'class':'content-section'})
    probe.append(soup.new_tag('h3'));soup.select_one('article').append(probe)
    css=''
    for el in soup.select('style, link[rel="stylesheet"]'):
        if el.name == 'style': css += '\n'+el.get_text()
        else:
            path=el['href'].lstrip('/')
            css += '\n'+source(path,revision)
    selectors=[]
    for order,(sel,decls) in enumerate(rules(css,width)):
        if '::' in sel: continue
        selectors.append((soupsieve.compile(sel),specificity(sel),order,decls))
    cache={}
    def computed(el):
        if id(el) in cache:return cache[id(el)]
        parent=computed(el.parent) if el.parent and el.parent.name != '[document]' else dict(zip(FIELDS,('serif',16,400,'normal','normal')))
        raw={}; ranks={}
        # UA defaults needed by the inspected bold and button elements.
        if el.name in ('b','strong'):raw['font-weight']='bolder'
        if el.name in ('button','input'):raw.update({'font-family':'Arial, sans-serif','font-size':'13.3333px','font-weight':'400'})
        for matcher,spec,order,decls in selectors:
            if not matcher.match(el):continue
            for k,v,important in decls:
                rank=(important,spec,order)
                if k not in ranks or rank>=ranks[k]:ranks[k]=rank;raw[k]=v
        for d in tinycss2.parse_declaration_list(el.get('style',''),skip_whitespace=True,skip_comments=True):
            if d.type != 'declaration':continue
            for k,v in expand(d):
                rank=(d.important,(1,0,0,0),len(selectors))
                if k not in ranks or rank>=ranks[k]:ranks[k]=rank;raw[k]=v
        result=parent.copy()
        for k,v in raw.items():
            if v in ('inherit','unset'):continue
            if k=='font-family':result[k]=family(v)
            elif k=='font-size':result[k]=length(v,parent['font-size'],width)
            elif k=='font-weight':
                result[k]=(400 if parent[k]<350 else 700 if parent[k]<550 else 900) if v=='bolder' else {'normal':400,'bold':700}.get(v, int(v) if v.isdigit() else None)
                assert result[k] is not None,v
            else:result[k]=v
        if raw.get('line-height') and raw['line-height'] not in ('inherit','unset','normal'):
            v=raw['line-height']
            if re.search(r'[a-z%]',v):result['line-height']=str(length(v,result['font-size'],width))+'px'
        cache[id(el)]=result
        return result
    return soup,computed

def main():
    before=source(PAGE,BASE);after=(ROOT/PAGE).read_text();ref=source(REF,'origin/main')
    result={'method':'Offline CSS cascade: tinycss2 + soupsieve; inline style, specificity, media width, inheritance and font shorthand; no browser/getComputedStyle', 'reference_commit':subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip(),'base_commit':BASE,'rows':[]}
    for width in (390,860,1024,1440):
        views=[inspect(t,rev,width) for t,rev in [(before,BASE),(after,'HEAD'),(ref,'origin/main')]]
        for label,ours,theirs in ELEMENTS:
            vals=[]
            groups=[]
            for index,(soup,computed) in enumerate(views):
                nodes=soup.select(theirs if index==2 else ours)
                assert nodes,(label,index)
                vals.append(computed(nodes[0]))
                groups.append({json.dumps(computed(node),sort_keys=True) for node in nodes})
            row={'element':label,'width':width,'before':vals[0],'after':vals[1],'reference':vals[2]}
            row['equal']=groups[1]==groups[2]
            row['all_instances_checked']=True
            result['rows'].append(row)
    (OUT/'FONTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    differences=[x for x in result['rows'] if not x['equal']]
    for row in differences:print(row['width'],row['element'],'LITSO',row['after'],'REF',row['reference'])
    print('Typography:',len(result['rows']),'comparisons;',len(differences),'differences')
    return len(differences)

if __name__=='__main__':
    raise SystemExit(bool(main()))
