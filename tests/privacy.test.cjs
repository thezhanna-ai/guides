const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const source = fs.readFileSync(path.join(__dirname, '../assets/privacy.js'), 'utf8');
const KEY = 'pronovoe-analytics-v1';

function run({ id = '', saved = null, storageFails = false } = {}) {
  const nodes = new Map();
  function node(name) {
    if (!nodes.has(name)) nodes.set(name, {
      hidden: true, listeners: {}, style: {},
      addEventListener(type, fn) { this.listeners[type] = fn; },
      getBoundingClientRect() { return { height: this.hidden ? 0 : 172 }; },
      remove() { this.removed = true; }, focus() { this.focused = true; }
    });
    return nodes.get(name);
  }
  const requests = [], calls = [], ymCalls = [], store = new Map(saved === null ? [] : [[KEY, saved]]);
  const props = {}, listeners = {};
  const window = {
    localStorage: {
      getItem(key) { if (storageFails) throw Error('blocked'); return store.get(key) ?? null; },
      setItem(key, value) { if (storageFails) throw Error('blocked'); store.set(key, value); }
    },
    addEventListener(type, fn) { listeners[type] = fn; },
    location: { reload() { calls.push('reload'); } }
  };
  const document = {
    getElementById: node,
    querySelectorAll(selector) { return selector === '[data-cookie-settings]' ? [node('settings')] : []; },
    documentElement: { style: { setProperty(key, value) { props[key] = value; } } },
    createElement(tag) {
      assert.equal(tag, 'script');
      const script = node('loader');
      Object.defineProperty(script, 'src', { configurable: true, set(value) { requests.push(value); } });
      return script;
    },
    head: { appendChild(script) { calls.push('append'); } }
  };
  vm.runInNewContext(source.replace(/const METRIKA_ID = '\d*';/, `const METRIKA_ID = '${id}';`), {
    window, document, Date,
    ResizeObserver: class { constructor(fn) { this.fn = fn; } observe() { this.fn(); } },
    fetch() { requests.push('fetch'); }, XMLHttpRequest() { requests.push('xhr'); }
  });
  return {
    nodes, requests, calls, ymCalls, store, props, window,
    click(name) { node(name).listeners.click(); },
    loaded() { window.ym = (...args) => ymCalls.push(args); node('loader').onload(); },
    storage(value, key = KEY) { if (key === KEY || key === null) { if (value === null) store.delete(KEY); else store.set(KEY, value); } listeners.storage({ key, newValue: value }); }
  };
}

test('no network before consent, even with a valid ID', () => {
  const app = run({ id: '123456' });
  assert.deepEqual(app.requests, []);
  assert.equal(app.window.ym, undefined);
  assert.equal(app.nodes.get('cookie-banner').hidden, false);
  assert.equal(app.props['--cookie-height'], '172px');
});
test('empty ID never loads, before/after click or on a returning visit', () => {
  for (const saved of [null, 'accepted', 'declined']) {
    const app = run({ saved });
    app.click('cookie-accept');
    assert.deepEqual(app.requests, []);
    assert.equal(app.window.ym, undefined);
  }
});
test('accepted choice is stored; valid ID loads once and initializes after load', () => {
  const app = run({ id: '123456' });
  app.click('cookie-accept');
  assert.equal(app.store.get(KEY), 'accepted');
  assert.deepEqual(app.requests, ['https://mc.yandex.ru/metrika/tag.js']);
  assert.equal(app.nodes.get('cookie-banner').hidden, true);
  app.loaded();
  const init = app.ymCalls[0];
  assert.equal(init[0], 123456);
  assert.equal(init[1], 'init');
  assert.equal(init[2].webvisor, true);
  assert.equal(init[2].clickmap, true);
  assert.equal(init[2].disableYtm, true);
  app.click('cookie-accept');
  assert.equal(app.requests.length, 1);
});
test('explicit refusal persists and makes no requests, including next visit', () => {
  const app = run({ id: '123456' });
  app.click('cookie-decline');
  assert.equal(app.store.get(KEY), 'declined');
  assert.deepEqual(app.requests, []);
  const revisit = run({ id: '123456', saved: 'declined' });
  assert.deepEqual(revisit.requests, []);
  assert.equal(revisit.nodes.get('cookie-banner').hidden, true);
});
test('returning consent loads; unknown storage values do not consent', () => {
  assert.equal(run({ id: '123456', saved: 'accepted' }).requests.length, 1);
  for (const saved of ['true', 'yes', '', '{broken', 'accepted-v0']) {
    const app = run({ id: '123456', saved });
    assert.equal(app.requests.length, 0);
    assert.equal(app.nodes.get('cookie-banner').hidden, false);
  }
});
test('invalid IDs cannot load a script', () => {
  for (const id of ['0', 'abc', '123x', ' ', '-1', '1.5', '9007199254740993']) {
    const app = run({ id, saved: 'accepted' });
    assert.equal(app.requests.length, 0, id);
  }
});
test('blocked localStorage does not imply consent and still allows a session choice', () => {
  const app = run({ id: '123456', storageFails: true });
  assert.equal(app.requests.length, 0);
  app.click('cookie-accept');
  assert.equal(app.requests.length, 1);
});
test('footer reopens settings; refusing destroys loaded counter and reloads', () => {
  const app = run({ id: '123456', saved: 'accepted' });
  app.loaded();
  app.click('settings');
  assert.equal(app.nodes.get('cookie-banner').hidden, false);
  app.click('cookie-decline');
  assert.equal(app.store.get(KEY), 'declined');
  assert.equal(app.ymCalls.at(-1)[1], 'destruct');
  assert.equal(app.calls.at(-1), 'reload');
});
test('refusal during script download cannot initialize from a late onload', () => {
  const app = run({ id: '123456' });
  app.click('cookie-accept');
  app.click('cookie-decline');
  app.loaded();
  assert.equal(app.ymCalls.length, 0);
});
test('storage refusal in another tab stops the counter; unrelated keys do nothing', () => {
  const app = run({ id: '123456', saved: 'accepted' });
  app.loaded();
  app.storage('dark', 'guide-theme');
  assert.equal(app.calls.includes('reload'), false);
  app.storage('declined');
  assert.equal(app.ymCalls.at(-1)[1], 'destruct');
  assert.equal(app.calls.at(-1), 'reload');
});
test('clearing storage in another tab revokes consent', () => {
  const app = run({ id: '123456', saved: 'accepted' });
  app.loaded();
  app.storage(null, null);
  assert.equal(app.calls.at(-1), 'reload');
});
