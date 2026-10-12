from pathlib import Path
from html.parser import HTMLParser
import re, html, hashlib
ROOT=Path('/Users/zslepova/IvanOS')
PAGE=ROOT/'.worktrees/stanford-2026-konspekt/claude-ai/stanford-2026-kak-uchitsya-ii/index.html'
OUT=ROOT/'tasks/для-кодекса/stanford-2026-priemka-20261012/TEKST-NA-SOGLASOVANIE-v5.md'
class Export(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.stack=[]; self.skip=0; self.lists=[]
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        blocked=t in ['button','footer','script','style','nav'] or a.get('class') in ['cta','next-read','cta-question']
        if t not in ['img','br','meta','link','input','hr']: self.stack.append((t,blocked))
        if blocked: self.skip+=1
        if self.skip:return
        if t in ['h1','h2','h3']: self.out.append('\n\n'+'#'*int(t[1])+' ')
        elif t=='p':
            if not self.out or not re.fullmatch(r'(?:- |\d+\. )',self.out[-1]):
                self.out.append('\n\n')
        elif t=='ol':self.lists.append(['ol',0])
        elif t=='ul':self.lists.append(['ul',0])
        elif t=='li':
            self.out.append('\n'); kind=self.lists[-1];kind[1]+=1
            self.out.append(str(kind[1])+'. ' if kind[0]=='ol' else '- ')
        elif t=='tr':self.out.append('\n')
        elif t in ['td','th']:self.out.append(' | ')
        elif t in ['pre','figcaption']:self.out.append('\n\n')
        elif t=='br':self.out.append(' ')
        elif t in ['b','strong']:self.out.append('**')
    def handle_endtag(self,t):
        if not self.skip:
            if t in ['b','strong']:self.out.append('**')
            if t in ['ol','ul'] and self.lists:self.lists.pop()
            if t in ['p','h1','h2','h3','div','section','pre','figcaption']:self.out.append('\n\n')
        if self.stack:
            name,blocked=self.stack.pop()
            assert name==t,(name,t)
            if blocked:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.out.append(data)
s=PAGE.read_text();article=re.search(r'<article>(.*?)</article>',s,re.S)[1]
e=Export();e.feed(article)
result=''.join(e.out)
result=re.sub(r'\n[ \t]+','\n',result)
result=re.sub(r'\n{3,}','\n\n',result).strip()+'\n'
result='\n'.join(line.rstrip() for line in result.splitlines())+'\n'
OUT.write_text(result)
print('TEXT',len(result.split()),'elements; SHA256',hashlib.sha256(result.encode()).hexdigest())
