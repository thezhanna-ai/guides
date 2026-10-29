const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const root = path.join(__dirname, '..');
const endpoint = 'https://test-account.goatcounter.com/count';

function counter({ configured = true, hostname = 'pronovoe.com', protocol = 'https:', referrer = 'https://www.instagram.com/path?email=secret#private', prerendering = false, failure = false, fetchAvailable = true } = {}) {
  const requests = [], listeners = {};
  const document = { referrer, prerendering, addEventListener(name, fn) { listeners[name] = fn; } };
  const window = {
    location: { hostname, protocol, pathname: '/claude-ai/shest-skillov/', search: '?email=secret', hash: '#private' },
    fetch(url, options) {
      requests.push({ url, options });
      return failure ? Promise.reject(Error('offline')) : Promise.resolve({ ok: true });
    }
  };
  if (!fetchAvailable) delete window.fetch;
  for (const object of [window, document]) {
    for (const key of ['localStorage', 'sessionStorage', 'cookie', 'screen', 'navigator']) {
      Object.defineProperty(object, key, { get() { throw Error('forbidden read: ' + key); } });
    }
  }
  let source = fs.readFileSync(path.join(root, 'assets/pageviews.js'), 'utf8');
  if (configured) source = source.replace("const GOATCOUNTER_ENDPOINT = '';", 'const GOATCOUNTER_ENDPOINT = ' + JSON.stringify(configured === true ? endpoint : configured) + ';');
  vm.runInNewContext(source, { window, document, URL, URLSearchParams });
  return { requests, activate() { document.prerendering = false; listeners.prerenderingchange(); } };
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
