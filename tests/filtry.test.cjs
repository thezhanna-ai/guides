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
  querySelector(selector) {
    assert.equal(selector, '.guide-link.kod-hit');
    return this.tracks.flatMap(track => track.links).find(link => link.classes.has('kod-hit')) || null;
  }
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
  const select = new Element(); select.value = 'all';
  const go = new Element();
  const input = new Element(); input.value = ''; input.focused = false; input.focus = () => { input.focused = true; };
  const noResults = new Element();
  const document = {
    getElementById(id) { return {'guide-search': input, 'metka': select, 'search-go': go}[id] || noResults; },
    querySelectorAll(selector) {
      return {'.guide-link': links, '.track': tracks, '.tool-block': sections}[selector];
    },
  };
  const window = {location: {href: ''}};
  const state = {};
  vm.createContext(state);
  Object.assign(state, {document, window});
  vm.runInContext(script, state);
  return {
    sections, tracks, links, select, go, input, noResults, window, state,
    key(key) { if (input.listeners.keydown) input.listeners.keydown({key}); },
    search(value) { input.value = value; input.listeners.input(); },
    filter(tag) { select.value = tag; select.listeners.change(); },
    find() { go.listeners.click(); },
    visible() { return links.filter(link => link.style.display !== 'none' && link.section.style.display !== 'none'); },
  };
}

test('Начальная страница: 43 карточки и пять рубрик', () => {
  const p = page(); assert.equal(p.visible().length, 43); assert.equal(p.sections.length, 5);
  assert.deepEqual(p.sections.map(s => s.attrs['data-section']), ['start', 'kazhdyy-den', 'kartinki', 'vaybkoding', 'servisy']);
});

test('Каждое настоящее название статьи находится целиком', () => {
  const p = page();
  for (const link of p.links) {
    const title = link.attrs['aria-label'];
    assert.ok(title, link.attrs.href);
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
  assert.equal(p.visible().length, 43); assert.ok(p.sections.every(s => s.style.display !== 'none'));
  assert.ok(!p.noResults.classes.has('show'));
});

for (const tag of ['claude-chat', 'claude-code', 'chatgpt', 'codex', 'kartinki', 'video', 'sayt', 'bot', 'dostup', 'besplatno']) {
  test('Метка ' + tag + ' показывает ровно статьи с этой меткой', () => {
    const p = page();
    const expected = p.links.filter(link => link.attrs['data-metki'].split(' ').includes(tag));
    assert.ok(expected.length > 0, tag);
    p.filter(tag);
    assert.deepEqual(p.visible(), expected);
    assert.ok(p.sections.every(s => s.style.display === 'none' || s.tracks.some(t => t.links.some(l => expected.includes(l)))));
  });
}

test('Поиск и метка совместно, затем смена метки без потери запроса', () => {
  const p = page(); p.filter('claude-chat'); p.search('голосовой'); assert.equal(p.visible().length, 1);
  p.filter('codex'); assert.equal(p.visible().length, 0); assert.ok(p.noResults.classes.has('show'));
  p.filter('all'); assert.equal(p.visible().length, 1); assert.equal(p.input.value, 'голосовой');
});

test('Регрессия: совпадение без выбранной метки не подавляет сообщение «Ничего не нашлось»', () => {
  const p = page(); p.filter('claude-chat'); p.search('10 бесплатных');
  assert.equal(p.visible().length, 0); assert.ok(p.noResults.classes.has('show'));
});

test('«Все метки» после фильтра возвращает 43 карточки и все рубрики', () => {
  const p = page(); p.filter('codex'); p.filter('all');
  assert.equal(p.visible().length, 43); assert.ok(p.sections.every(s => s.style.display !== 'none'));
});

test('«Другое» снимает метку и ставит курсор в поле поиска', () => {
  const p = page(); p.filter('codex'); p.filter('drugoe');
  assert.equal(p.visible().length, 43); assert.ok(p.input.focused);
});

test('Кнопка «Найти» открывает единственный результат', () => {
  const p = page(); p.search('golosovoy'); p.find();
  assert.equal(p.window.location.href, articleHref('golosovoy-vvod-v-claude'));
});

test('Скрипт не выполняет сетевых запросов и работает из локального HTML', () => {
  const p = page(); p.search('проект'); p.filter('all'); assert.ok(p.visible().length > 0);
  assert.ok(!/\b(fetch|XMLHttpRequest|import)\b/.test(script));
});


const registry = JSON.parse(fs.readFileSync(path.join(root, 'data/statyi.json'), 'utf8')).statyi;
const articleHref = slug => 'claude-ai/' + slug + '/';

test('ЖЕМЧУГ находится по слову, транслиту и раскладке; Enter открывает новую статью', () => {
  const article = registry.find(a => a.slug === '10-saytov-starogo-interneta');
  assert.equal(article.kod_slovo, 'ЖЕМЧУГ');
  for (const query of ['ЖЕМЧУГ', '  жемчуг  ', 'zhemchug', ';tvxeu']) {
    const p = page(); p.filter('sravnenie'); p.search(query);
    assert.deepEqual(p.visible().map(link => link.attrs.href), [articleHref(article.slug)]);
    assert.ok(p.visible()[0].classes.has('kod-hit'));
    p.key('Enter'); assert.equal(p.window.location.href, articleHref(article.slug));
  }
});

test('Все кодовые слова реальных live-статей находят каждый связанный гайд при любом фильтре', () => {
  for (const code of new Set(registry.filter(a => a.status === 'live' && a.kod_slovo).map(a => a.kod_slovo))) {
    const p = page(); p.filter('sravnenie'); p.search(code);
    for (const article of registry.filter(a => a.status === 'live' && a.kod_slovo === code)) {
      assert.ok(p.visible().some(link => link.attrs.href === articleHref(article.slug)), code + ': ' + article.slug);
    }
    assert.ok(p.visible().every(link => link.classes.has('kod-hit')));
    assert.ok(!p.noResults.classes.has('show'));
  }
});

test('Темы из реестра находятся после удаления видимого названия с карточек', () => {
  const p = page();
  for (const article of registry.filter(a => a.status === 'live')) {
    for (const term of article.ponyatiya) {
      p.search(term);
      assert.ok(p.visible().some(link => link.attrs.href === articleHref(article.slug)), article.slug + ': ' + term);
    }
  }
});

for (const query of ['ДОСТУП', 'dostup', 'ljcneg', 'достп', 'досттуп', 'достуб']) {
  test('Кодовое слово с регистром, транслитом, раскладкой или одной правкой: ' + query, () => {
    const p = page(); p.filter('sravnenie'); p.search(query);
    assert.ok(p.visible().some(link => link.attrs.href === articleHref('podklyuchenie-iz-rossii')));
    assert.ok(p.visible().some(link => link.classes.has('kod-hit')));
  });
}

for (const [query, slug] of [['голосовои', 'golosovoy-vvod-v-claude'],
  ['golosovoy', 'golosovoy-vvod-v-claude'], ['ujkjcjdjq', 'golosovoy-vvod-v-claude'],
  ['эксел', 'gotovye-fayly-excel-word-pdf'], ['джимейл', 'podklyuchit-gmail-drive-calendar'],
  ['маркдаун', 'pdf-v-markdown-markitdown'], ['клод память', 'kak-rasskazat-o-sebe']]) {
  test('Тема: ' + query, () => {
    const p = page(); p.search(query);
    assert.ok(p.visible().some(link => link.attrs.href === articleHref(slug)), slug);
  });
}

test('Нормализация ё/е, й/и и мягкого знака, границы допуска опечатки', () => {
  const p = page();
  assert.equal(p.state.normalize('Ёж Йод соль'), 'еж иод сол');
  for (const [a, b] of [['достп', 'доступ'], ['досттуп', 'доступ'], ['достуб', 'доступ']]) {
    assert.ok(p.state.oneEdit(a, b));
  }
  assert.ok(!p.state.oneEdit('дстп', 'доступ'));
  assert.ok(!p.state.wordHits('кот', ['код']));
  assert.ok(!p.state.kodMatches('пам', 'памят'));
});

test('Общее кодовое слово сохраняет несколько результатов и Enter не открывает случайный', () => {
  const p = page();
  const code = p.links[0].attrs['data-kod'];
  // Две настоящие карточки моделируют допустимое общее кодовое слово
  p.links[1].setAttribute('data-kod', code);
  p.search(code); assert.ok(p.visible().includes(p.links[0])); assert.ok(p.visible().includes(p.links[1]));
  assert.ok(p.visible().length > 1);
  p.key('Enter'); assert.equal(p.window.location.href, '');
});

test('Enter открывает единственный результат, обычная клавиша ничего не открывает', () => {
  const p = page(); p.search('ujkjcjdjq'); assert.equal(p.visible().length, 1);
  p.key('Escape'); assert.equal(p.window.location.href, '');
  p.key('Enter'); assert.equal(p.window.location.href, articleHref('golosovoy-vvod-v-claude'));
});

test('Enter при пустом или ненайденном запросе ничего не открывает', () => {
  const p = page(); p.key('Enter'); assert.equal(p.window.location.href, '');
  p.search('zzzzzzнебывает'); p.key('Enter'); assert.equal(p.window.location.href, '');
});

test('Enter не открывает совпадение, скрытое выбранной меткой', () => {
  const p = page(); p.filter('codex'); p.search('голосовой');
  assert.equal(p.visible().length, 0); p.key('Enter'); assert.equal(p.window.location.href, '');
});

test('Стирание кодового слова снимает подсветку и сохраняет выбранный фильтр', () => {
  const p = page(); p.filter('codex'); p.search('ДОСТУП'); assert.ok(p.visible().length > 0);
  p.search(''); assert.ok(p.links.every(link => !link.classes.has('kod-hit')));
  assert.ok(p.visible().every(link => link.attrs['data-metki'].split(' ').includes('codex')));
  assert.equal(p.select.value, 'codex');
});

test('Поисковый ввод с разметкой остаётся данными', () => {
  const p = page(); p.search('<img src=x onerror=alert(1)>');
  assert.equal(p.window.location.href, ''); assert.ok(!/innerHTML|eval\(/.test(script));
});
