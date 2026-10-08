const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const root = path.resolve(__dirname, '..');
const pages = ['index.html', ...fs.readdirSync(path.join(root, 'claude-ai'))
  .map(slug => `claude-ai/${slug}/index.html`)
  .filter(file => fs.existsSync(path.join(root, file)) && file !== "claude-ai/chatgpt-composio-prilozheniya/index.html"), 'scripts/shablon_glavnoy.html'];
const disclosure = 'Реклама. ИП Сергеев И. С., ИНН 352511695540. erid: 2VtzqviiWtm';

function scripts(html) {
  return [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
    .filter(([, attrs]) => !/src=|application\/ld\+json/.test(attrs))
    .map(([, , body]) => body);
}

function bindPartner(source, empty = false) {
  const link = { href: '' };
  const document = {
    querySelectorAll(selector) {
      assert.ok(['a[data-partner]', '[data-partner]'].includes(selector), selector);
      return empty ? [] : [link];
    }
  };
  vm.runInNewContext(source, { document });
  return link;
}

for (const file of pages) {
  test(`${file}: ERID is static HTML and partner button keeps its target`, () => {
    const html = fs.readFileSync(path.join(root, file), 'utf8');
    const labels = [...html.matchAll(/<p class="ad-disclosure">([\s\S]*?)<\/p>/g)];
    assert.equal(labels.length, 1);
    assert.equal(labels[0][1], disclosure, 'The full label must be plain text without running JS');
    assert.equal((html.match(/2VtzqviiWtm/g) || []).length, 1);
    assert.doesNotMatch(html, /\b(?:var|let|const)\s+ERID\b|data-erid/);
    const bodies = scripts(html.replace(/\{\{/g, '{').replace(/\}\}/g, '}'));
    assert.ok(bodies.every(body => !/ERID|ad-disclosure/.test(body)), 'No label initializer remains');
    const partner = bodies.find(body => /var PARTNER_LINK =/.test(body));
    assert.ok(partner, 'Partner initializer must remain');
    const declaration = partner.match(/var PARTNER_LINK = "[^"\n]+";/)[0];
    const binding = partner.match(/document\.querySelectorAll\("a?\[data-partner\]"\)\.forEach\(function\s*\((\w+)\)\s*\{\s*\1\.href = PARTNER_LINK;\s*\}\);/)[0];
    assert.equal(bindPartner(`${declaration}\n${binding}`).href,
      'https://theivansergeev.com/koncentrat/?gcpc=16fff');
    assert.doesNotThrow(() => bindPartner(`${declaration}\n${binding}`, true));
  });
}
