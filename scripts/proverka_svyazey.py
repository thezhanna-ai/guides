#!/usr/bin/env python3
"""Проверка связей между статьями по data/statyi.json.

Что делает:
  1. ищет в тексте каждой статьи понятия ЧУЖИХ статей - там просится ссылка
  2. считает входящие ссылки на каждую статью (норма движка: минимум 3)
  3. проверяет обязательные ссылки из поля trebuet
Ничего не правит, только показывает.
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = json.loads((ROOT / 'data' / 'statyi.json').read_text(encoding='utf-8'))
ST = {s['slug']: s for s in REG['statyi']}
NORMA_VHODYASHCHIH = 3


def text_of(slug):
    """Текст статьи без CSS/JS и без подвала «Дальше по теме»."""
    h = (ROOT / 'claude-ai' / slug / 'index.html').read_text(encoding='utf-8')
    h = re.sub(r'<(script|style|head)[^>]*>.*?</\1>', ' ', h, flags=re.S | re.I)
    cut = re.search(r'Дальше по теме', h)
    body = h[:cut.start()] if cut else h
    return re.sub(r'<[^>]+>', ' ', body), h


def links_of(full_html):
    return set(re.findall(r'href="\.\./([a-z0-9-]+)/', full_html))


def main():
    prosyatsya, vhodyashchie = [], {s: 0 for s in ST}
    for slug in ST:
        body, full = text_of(slug)
        linked = links_of(full)
        for tgt in linked:
            if tgt in vhodyashchie:
                vhodyashchie[tgt] += 1
        for other, data in ST.items():
            if other == slug or other in linked:
                continue
            for p in data['ponyatiya']:
                for m in re.finditer(r'(?<![а-яА-Яa-zA-Z])' + re.escape(p), body, re.I):
                    frag = ' '.join(body[max(0, m.start() - 90):m.end() + 90].split())
                    prosyatsya.append((slug, p, other, frag))
                    break

    print('=== ПРОСЯТСЯ ССЫЛКИ (понятие в тексте есть, ссылки нет) ===')
    for slug, p, tgt, frag in sorted(prosyatsya):
        print(f'\n[{slug}] «{p}» -> {tgt}\n    …{frag}…')

    print(f'\n=== ВХОДЯЩИЕ ССЫЛКИ (норма {NORMA_VHODYASHCHIH}) ===')
    for slug, n in sorted(vhodyashchie.items(), key=lambda x: x[1]):
        flag = 'OK ' if n >= NORMA_VHODYASHCHIH else '!! '
        print(f'{flag}{slug}: {n}')

    print('\n=== ОБЯЗАТЕЛЬНЫЕ (поле trebuet) ===')
    bad = 0
    for slug, data in ST.items():
        _, full = text_of(slug)
        linked = links_of(full)
        for need in data['trebuet']:
            if need not in linked:
                print(f'!! {slug} не ссылается на {need}')
                bad += 1
    if not bad:
        print('все обязательные ссылки на месте')
    return 0


if __name__ == '__main__':
    sys.exit(main())
