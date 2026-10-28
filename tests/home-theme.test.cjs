const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/home-theme.js'), 'utf8');

function app(saved, blocked = false) {
  const attrs = {};
  const button = {textContent: '', setAttribute(k, v) { attrs[k] = v; }, addEventListener(_, fn) { this.click = fn; }};
  const html = {dataset: {}};
  let ready;
  const storage = {value: saved};
  vm.runInNewContext(source, {
    document: {documentElement: html, addEventListener(_, fn) { ready = fn; }, querySelector() { return button; }},
    localStorage: {
      getItem(key) { assert.equal(key, 'guide-theme'); if (blocked) throw Error('blocked'); return storage.value; },
      setItem(key, value) { assert.equal(key, 'guide-theme'); if (blocked) throw Error('blocked'); storage.value = value; },
    },
  });
  // Тема применяется в head, до появления кнопки и первого экрана
  const initial = html.dataset.theme;
  ready();
  return {html, button, attrs, storage, initial};
}

test('главная восстанавливает тёмную тему статей до готовности DOM', () => {
  const p = app('dark');
  assert.equal(p.initial, 'dark');
  assert.equal(p.attrs['aria-pressed'], 'true');
  assert.equal(p.button.textContent, '☀');
});

test('переключатель сохраняет оба режима в общем ключе статей', () => {
  const p = app('light');
  p.button.click();
  assert.equal(p.html.dataset.theme, 'dark');
  assert.equal(p.storage.value, 'dark');
  p.button.click();
  assert.equal(p.html.dataset.theme, 'light');
  assert.equal(p.storage.value, 'light');
  assert.equal(p.attrs['aria-pressed'], 'false');
});

test('без сохранённой темы и при неверном значении используется светлая', () => {
  for (const value of [null, '', 'unexpected']) assert.equal(app(value).initial, 'light');
});

test('при недоступном localStorage переключатель продолжает работать', () => {
  const p = app(null, true);
  assert.equal(p.initial, 'light');
  assert.doesNotThrow(() => p.button.click());
  assert.equal(p.html.dataset.theme, 'dark');
  assert.doesNotThrow(() => p.button.click());
  assert.equal(p.html.dataset.theme, 'light');
});

test('собранная главная и шаблон подключают один скрипт темы и переключатель', () => {
  for (const file of ['index.html', 'scripts/shablon_glavnoy.html']) {
    const html = fs.readFileSync(path.join(root, file), 'utf8');
    const scriptIndex = html.indexOf('<script src="assets/home-theme.js"></script>');
    assert.ok(scriptIndex >= 0 && scriptIndex < html.indexOf('<style>'));
    assert.match(html, /<button class="theme-toggle" type="button"[^>]*aria-label="Тёмная тема"/);
    assert.match(html, /:root\[data-theme="dark"\]/);
  }
});
