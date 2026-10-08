#!/usr/bin/env python3
"""IndexNow: без аргументов печатает payload; --send проверяет публикацию и отправляет."""
import argparse
import json
import re
from pathlib import Path
import urllib.request
import sys

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://api.indexnow.org/indexnow'


def publication_errors(payload, get):
    """Пинг разрешён только после публикации ключа и SEO-версий всех URL."""
    if payload.get('host') != 'pronovoe.com' or not re.fullmatch(r'[a-f0-9]{32}', payload.get('key', '')):
        raise ValueError('Неверный host или ключ IndexNow')
    if payload.get('keyLocation') != 'https://pronovoe.com/' + payload['key'] + '.txt':
        raise ValueError('Ключ должен быть на pronovoe.com')
    expected = {'https://pronovoe.com/' + x.removesuffix('index.html') for x in json.loads((ROOT / 'data/seo.json').read_text())}
    if set(payload['urlList']) != expected or len(payload['urlList']) != len(expected):
        raise ValueError('Список IndexNow должен совпадать с реестром SEO')
    errors = []
    if get(payload['keyLocation']).strip() != payload['key']:
        errors.append('На живом сайте ещё нет файла ключа')
    for url in payload['urlList']:
        rel = url.removeprefix('https://pronovoe.com/') + 'index.html'
        local = (ROOT / rel).read_text(encoding='utf-8')
        live = get(url)
        # Побайтовое совпадение HTML не зависит от ложноположительного совпадения H1
        if live != local:
            errors.append('На сайте ещё другая версия: ' + url)
    return errors


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--send', action='store_true', help='Проверить публикацию всех HTML и отправить')
    args = parser.parse_args()
    payload = json.loads((ROOT / 'data/indexnow.json').read_text(encoding='utf-8'))
    if not args.send:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print('DRY RUN: запрос не отправлен. После публикации: python3 scripts/indexnow.py --send', file=sys.stderr)
        return 0
    errors = publication_errors(payload, get)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    request = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
        print('IndexNow HTTP', response.status)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
