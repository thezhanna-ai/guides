const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const pages = ['index.html', ...fs.readdirSync(path.join(root, 'claude-ai'))
  .map(slug => `claude-ai/${slug}/index.html`)
  .filter(file => fs.existsSync(path.join(root, file)))];

function scripts(file) {
  return [...fs.readFileSync(path.join(root, file), 'utf8')
    .matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .filter(([, attrs]) => !/src=|application\/ld\+json/.test(attrs))
    .map(([, , body]) => body);
}

function render(source, token, empty = false) {
  const label = { textContent: '' }, link = { href: '' };
  const document = {
    querySelectorAll(selector) {
      assert.ok(['[data-erid]', 'a[data-partner]', '[data-partner]'].includes(selector), selector);
      return empty ? [] : selector === '[data-erid]' ? [label] : [link];
    }
  };
  vm.runInNewContext(source.replace(/var ERID = "[^"\n]+";/,
    `var ERID = ${JSON.stringify(token)};`), { document });
  return { label, link };
}

for (const file of pages) {
  test(`${file}: ERID renders from the constant and partner button keeps its target`, () => {
    const bodies = scripts(file);
    const erid = bodies.find(body => /var ERID =/.test(body));
    assert.ok(erid, 'ERID initializer must exist');
    const init = erid.match(/var ERID = "[^"\n]+";\s*document\.querySelectorAll\("\[data-erid\]"\)\.forEach\(function \(label\) \{ label\.textContent = ERID; \}\);/)[0];
    const partner = bodies.find(body => /var PARTNER_LINK =/.test(body));
    const declaration = partner.match(/var PARTNER_LINK = "[^"\n]+";/)[0];
    const binding = partner.match(/document\.querySelectorAll\("a?\[data-partner\]"\)\.forEach\(function\s*\((\w+)\)\s*\{\s*\1\.href = PARTNER_LINK;\s*\}\);/)[0];
    for (const token of ['ERID_PLACEHOLDER', '2VtzqExample42', '<img src=x onerror=alert(1)>', '']) {
      const result = render(`${declaration}\n${init}\n${binding}`, token);
      assert.equal(result.label.textContent, token);
      assert.equal(result.link.href, 'https://theivansergeev.com/koncentrat/?gcpc=16fff');
      assert.equal(result.label.innerHTML, undefined, 'Token is only text, never HTML');
    }
    assert.doesNotThrow(() => render(`${declaration}\n${init}\n${binding}`, 'token', true));
  });
}
