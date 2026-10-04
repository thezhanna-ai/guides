// Выполняет настоящий скрипт index.html на структуре настоящего HTML без браузера
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');
const {test} = require('node:test');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const fixture = JSON.parse(execFileSync(process.env.SITE_PYTHON || 'python3', ['-c', 'import json; from tests.test_site import catalog_dom_fixture; print(json.dumps(catalog_dom_fixture(), ensure_ascii=False))'], {cwd: root, encoding: 'utf8'}));

class Element {
  constructor(attrs = {}, text = '') {
    this.attrs = {...attrs}; this.textContent = text; this.style = {}; this.listeners = {};
    this.classes = new Set((attrs.class || '').split(' '));
    this.classList = {
      add: value => this.classes.add(value),
      remove: value => this.classes.delete(value),
      toggle: (value, on) => on ? this.classes.add(value) : this.classes.delete(value),
    };
  }
  getAttribute(name) { return this.attrs[name] ?? null; }
  setAttribute(name, value) { this.attrs[name] = value; }
  addEventListener(event, fn) { this.listeners[event] = fn; }
  querySelectorAll(selector) { return selector === '.track' ? this.tracks : this.links; }
  closest(selector) { assert.equal(selector, '.tool-block'); return this.section; }
}

function page() {
  const sections = fixture.sections.map(row => {
    const section = new Element({'data-section': row.tag});
    section.tracks = row.tracks.map(row => {
      const track = new Element();
      track.links = row.links.map(row => {
        const link = new Element(row.attrs, row.text); link.section = section; return link;
      });
      return track;
    });
    return section;
  });
  const tracks = sections.flatMap(section => section.tracks);
  const links = tracks.flatMap(track => track.links);
  const buttons = fixture.buttons.map(attrs => new Element(attrs));
  const input = new Element(); input.value = '';
  const noResults = new Element();
  const document = {
    getElementById(id) { return id === 'guide-search' ? input : noResults; },
    querySelectorAll(selector) {
      return {'.tag-btn': buttons, '.guide-link': links, '.track': tracks, '.tool-block': sections}[selector];
    },
  };
  vm.runInNewContext(script, {document});
  return {
    sections, tracks, links, buttons, input, noResults,
    search(value) { input.value = value; input.listeners.input(); },
    filter(tag) { buttons.find(btn => btn.attrs['data-tag'] === tag).listeners.click(); },
    visible() { return links.filter(link => link.style.display !== 'none' && link.section.style.display !== 'none'); },
  };
}

test('Начальная страница: 27 карточек и шесть разделов', () => {
  const p = page(); assert.equal(p.visible().length, 27); assert.equal(p.sections.length, 6);
});

test('Каждое настоящее название статьи находится целиком', () => {
  const p = page();
  for (const link of p.links) {
    const title = link.textContent.split(/(?:Начальный|Средний) уровень/)[0];
    p.search(title); assert.ok(p.visible().includes(link), link.attrs.href);
  }
});

test('Поиск игнорирует регистр и пробелы с краёв', () => {
  const p = page(); p.search('  ГОЛОСОВОЙ  '); assert.equal(p.visible().length, 1);
  assert.ok(p.visible()[0].attrs.href.includes('golosovoy-vvod'));
});

test('Ненайденный запрос скрывает карточки, трассы, разделы и показывает сообщение', () => {
  const p = page(); p.search('zzzzzzнебывает'); assert.equal(p.visible().length, 0);
  assert.ok(p.tracks.every(track => track.style.display === 'none'));
  assert.ok(p.sections.every(section => section.style.display === 'none'));
  assert.ok(p.noResults.classes.has('show'));
});

test('Стирание запроса возвращает карточки и пустые разделы', () => {
  const p = page(); p.search('zzzzzzнебывает'); p.search('');
  assert.equal(p.visible().length, 27); assert.ok(p.sections.every(s => s.style.display !== 'none'));
  assert.ok(!p.noResults.classes.has('show'));
});

for (const tag of ['dostup', 'claude', 'gpt', 'kartinki', 'proekty', 'proishodit']) {
  test('Фильтр ' + tag + ' сохраняет прежние правила тегов и разделов', () => {
    const p = page();
    const expected = p.links.filter(link => link.attrs['data-tags'].split(' ').includes(tag) && link.section.attrs['data-section'] === tag);
    p.filter(tag);
    assert.deepEqual(p.visible(), expected);
    assert.ok(p.sections.every(s => s.style.display === 'none' || s.attrs['data-section'] === tag));
    assert.equal(p.buttons.filter(btn => btn.classes.has('active')).length, 1);
    assert.equal(p.buttons.filter(btn => btn.attrs['aria-pressed'] === 'true').length, 1);
  });
}

test('Поиск и фильтр совместно, затем смена фильтра без потери запроса', () => {
  const p = page(); p.filter('claude'); p.search('голосовой'); assert.equal(p.visible().length, 1);
  p.filter('gpt'); assert.equal(p.visible().length, 0); assert.ok(p.noResults.classes.has('show'));
  p.filter('all'); assert.equal(p.visible().length, 1); assert.equal(p.input.value, 'голосовой');
});

test('Регрессия: совпадение в скрытом разделе не подавляет сообщение «Ничего не нашлось»', () => {
  const p = page(); p.filter('claude'); p.search('10 бесплатных');
  assert.equal(p.visible().length, 0); assert.ok(p.noResults.classes.has('show'));
});

test('Все после фильтра возвращает 27 карточек и пустые разделы', () => {
  const p = page(); p.filter('gpt'); p.filter('all');
  assert.equal(p.visible().length, 27); assert.ok(p.sections.every(s => s.style.display !== 'none'));
});

test('Скрипт не выполняет сетевых запросов и работает из локального HTML', () => {
  const p = page(); p.search('проект'); p.filter('all'); assert.ok(p.visible().length > 0);
  assert.ok(!/\b(fetch|XMLHttpRequest|import)\b/.test(script));
});
