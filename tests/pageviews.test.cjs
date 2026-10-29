const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const root = path.join(__dirname, '..');
const endpoint = 'https://test-account.goatcounter.com/count';

function counter({ configured = true, hostname = 'pronovoe.com', protocol = 'https:', referrer = 'https://www.instagram.com/path?email=secret#private', prerendering = false, failure = false, fetchAvailable = true, observerAvailable = true, ads = [{}] } = {}) {
  const requests = [], listeners = {}, observed = [];
  let intersection, disconnected = false;
  const document = { referrer, prerendering, addEventListener(name, fn) { listeners[name] = fn; }, querySelectorAll(selector) { assert.equal(selector, 'section.cta'); return ads; } };
  const window = {
    location: { hostname, protocol, pathname: '/claude-ai/shest-skillov/', search: '?email=secret', hash: '#private' },
    fetch(url, options) {
      requests.push({ url, options });
      return failure ? Promise.reject(Error('offline')) : Promise.resolve({ ok: true });
    }
  };
  if (!fetchAvailable) delete window.fetch;
  if (observerAvailable) window.IntersectionObserver = class {
    constructor(callback) { intersection = callback; }
    observe(node) { observed.push(node); }
    disconnect() { disconnected = true; }
  };
  for (const object of [window, document]) {
    for (const key of ['localStorage', 'sessionStorage', 'cookie', 'screen', 'navigator']) {
      Object.defineProperty(object, key, { get() { throw Error('forbidden read: ' + key); } });
    }
  }
  let source = fs.readFileSync(path.join(root, 'assets/pageviews.js'), 'utf8');
  source = source.replace(/const GOATCOUNTER_ENDPOINT = '[^']*';/, 'const GOATCOUNTER_ENDPOINT = ' + JSON.stringify(configured === false ? '' : configured === true ? endpoint : configured) + ';');
  vm.runInNewContext(source, { window, document, URL, URLSearchParams });
  return { requests, observed, listeners, get disconnected() { return disconnected; },
    intersect(entries) { intersection(entries); },
    click(href, { button = 0, type = 'click', nested = false } = {}) {
      const link = href === null ? null : { href };
      const element = { closest(selector) { assert.equal(selector, 'a[href]'); return link; } };
      listeners[type]({ button, type, target: nested ? { parentElement: element } : element });
    }, activate() { document.prerendering = false; listeners.prerenderingchange(); } };
}

test('empty configuration and non-production hosts send nothing', () => {
  assert.equal(counter({ configured: false }).requests.length, 0);
  for (const hostname of ['localhost', '127.0.0.1', 'preview.pronovoe.com', 'pronovoe.com.evil.test']) {
    assert.equal(counter({ hostname }).requests.length, 0);
  }
});

test('invalid endpoints, insecure pages and a missing fetch API stay silent', () => {
  for (const configured of ['http://test-account.goatcounter.com/count', 'https://evil.test/count', 'https://test-account.goatcounter.com/count?data=secret', 'https://test-account.goatcounter.com.evil.test/count']) {
    assert.equal(counter({ configured }).requests.length, 0);
  }
  assert.equal(counter({ protocol: 'http:' }).requests.length, 0);
  assert.equal(counter({ fetchAvailable: false }).requests.length, 0);
});

test('one opening sends only path, referrer origin and an explicit no-session flag', () => {
  const app = counter();
  assert.equal(app.requests.length, 1);
  const { url, options } = app.requests[0];
  const parsed = new URL(url);
  assert.equal(parsed.origin + parsed.pathname, endpoint);
  assert.deepEqual(Object.fromEntries(parsed.searchParams), {
    p: '/claude-ai/shest-skillov/', r: 'https://www.instagram.com', ns: 'true'
  });
  assert.equal(options.credentials, 'omit');
  assert.equal(options.referrerPolicy, 'no-referrer');
  assert.equal(options.cache, 'no-store');
  assert.equal(options.method, 'GET');
  assert.equal(options.keepalive, true);
  assert.ok(!url.includes('secret'));
});

test('missing, malformed and non-HTTP referrers are empty', () => {
  for (const referrer of ['', 'broken', 'file:///private/name', 'javascript:secret']) {
    assert.equal(new URL(counter({ referrer }).requests[0].url).searchParams.get('r'), '');
  }
});

test('prerender waits for activation instead of creating a false opening', () => {
  const app = counter({ prerendering: true });
  assert.equal(app.requests.length, 0);
  app.activate();
  assert.equal(app.requests.length, 1);
});

test('blocked collector has no unhandled rejection or retries', async () => {
  const app = counter({ failure: true });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(app.requests.length, 1);
});

function loader(readyState) {
  const callbacks = [], scripts = [], timers = [];
  const document = {
    readyState,
    getElementById(id) { return scripts.find(s => s.id === id); },
    createElement(tag) { assert.equal(tag, 'script'); return {}; },
    head: { appendChild(script) { scripts.push(script); } }
  };
  const window = {
    addEventListener(event, fn, options) { assert.equal(event, 'load'); assert.equal(options.once, true); callbacks.push(fn); },
    setTimeout(fn) { timers.push(fn); }
  };
  const source = fs.readFileSync(path.join(root, 'scripts/pageviews-loader.html'), 'utf8').match(/<script>\s*([\s\S]*?)<\/script>/)[1];
  vm.runInNewContext(source, { window, document });
  return { callbacks, scripts, timers };
}

test('local asset is requested asynchronously only after load, once', () => {
  const app = loader('interactive');
  assert.equal(app.scripts.length, 0);
  app.callbacks[0]();
  app.callbacks[0]();
  assert.equal(app.scripts.length, 1);
  assert.equal(app.scripts[0].src, '/assets/pageviews.js');
  assert.equal(app.scripts[0].async, true);
  assert.equal(app.scripts[0].referrerPolicy, 'no-referrer');
});

test('late execution schedules the loader without waiting for a lost load event', () => {
  const app = loader('complete');
  assert.equal(app.scripts.length, 0);
  assert.equal(app.callbacks.length, 0);
  app.timers[0]();
  assert.equal(app.scripts.length, 1);
});


test('production collector is the exact owner-provided provovoe account', () => {
  assert.match(fs.readFileSync(path.join(root, 'assets/pageviews.js'), 'utf8'), /const GOATCOUNTER_ENDPOINT = 'https:\/\/provovoe\.goatcounter\.com\/count';/);
});

test('ad impression waits for an actual intersection and is sent once per opening', () => {
  const ad = {}, app = counter({ ads: [ad] });
  assert.deepEqual(app.observed, [ad]);
  app.intersect([{ isIntersecting: false, target: ad }]);
  assert.equal(app.requests.length, 1);
  app.intersect([{ isIntersecting: true, target: ad }]);
  app.intersect([{ isIntersecting: true, target: ad }]);
  assert.equal(app.requests.length, 2);
  assert.equal(app.disconnected, true);
  const req = app.requests[1];
  assert.deepEqual(Object.fromEntries(new URL(req.url).searchParams), { p: 'reklama-pokaz', ns: 'true', e: 'true' });
  assert.equal(req.options.credentials, 'omit');
  assert.equal(req.options.referrerPolicy, 'no-referrer');
});

test('no observer or no ad section never invents an impression and clicks still work', () => {
  for (const settings of [{ observerAvailable: false }, { ads: [] }]) {
    const app = counter(settings);
    assert.equal(app.observed.length, 0);
    app.click('https://theivansergeev.com/koncentrat/?gcpc=16fff', { nested: true });
    assert.equal(app.requests.length, 2);
  }
});

test('click events send only the fixed event name and flags, including nested and middle clicks', () => {
  const app = counter();
  app.click('https://theivansergeev.com/koncentrat/?email=secret#private');
  app.click('https://theivansergeev.com/zapis/?gcpc=16fff', { nested: true });
  app.click('https://theivansergeev.com/zapis/', { type: 'auxclick', button: 1 });
  assert.equal(app.requests.length, 4);
  for (const req of app.requests.slice(1)) {
    assert.deepEqual(Object.fromEntries(new URL(req.url).searchParams), { p: 'reklama-klik', ns: 'true', e: 'true' });
    assert.equal(req.options.method, 'GET');
    assert.equal(req.options.credentials, 'omit');
    assert.equal(req.options.referrerPolicy, 'no-referrer');
    assert.equal(req.options.keepalive, true);
  }
});

test('unrelated domains, schemes, non-links and other mouse buttons are ignored', () => {
  const app = counter();
  for (const href of [null, 'broken', 'https://example.com/', 'https://theivansergeev.com.evil.test/', 'https://evil.theivansergeev.com/', 'javascript:alert(1)', 'mailto:test@theivansergeev.com']) app.click(href);
  app.click('https://theivansergeev.com/', { button: 2 });
  app.click('https://theivansergeev.com/', { type: 'auxclick', button: 2 });
  assert.equal(app.requests.length, 1);
});

test('prerender installs ad listeners only on activation', () => {
  const app = counter({ prerendering: true });
  assert.equal(app.observed.length, 0);
  assert.equal(app.listeners.click, undefined);
  app.activate();
  assert.equal(app.observed.length, 1);
  app.click('https://theivansergeev.com/');
  assert.equal(app.requests.length, 2);
});

test('collector failures on events do not interrupt interaction or retry', async () => {
  const app = counter({ failure: true });
  app.intersect([{ isIntersecting: true }]);
  app.click('https://theivansergeev.com/');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(app.requests.length, 3);
});
