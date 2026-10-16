const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');

function fixture(native = false, nested = false) {
  const listeners = {};
  const document = {addEventListener(type, fn) { listeners[type] = fn; }};
  class Element {
    constructor(tag = 'div') { this.tagName = tag.toUpperCase(); this.children = []; this.attrs = {}; this.style = {overflow: ''}; this.inert = false; this.isConnected = true; this.tabIndex = this.tagName === 'BUTTON' ? 0 : -1; }
    appendChild(child) { this.append(child); }
    append(...children) { children.forEach(child => {child.parentElement = this; this.children.push(child);}); }
    get src() { return this.attrs.src; }
    set src(value) { this.attrs.src = value; }
    setAttribute(key, value) { this.attrs[key] = value; }
    hasAttribute(key) { return key in this.attrs; }
    removeAttribute(key) { delete this.attrs[key]; }
    contains(element) { return this === element || this.children.some(child => child.contains(element)); }
    querySelector(selector) { return this.children.find(child => selector === 'img' ? child.tagName === 'IMG' : (child.className || '').split(' ').includes(selector.slice(1))) || null; }
    querySelectorAll() { return this.children; }
    getClientRects() { return [{}]; }
    focus() { document.activeElement = this; }
    closest() { return null; }
    addEventListener(type, fn) { this.events ||= {}; this.events[type] = fn; }
    showModal() { this.setAttribute('open', ''); }
    close() { this.removeAttribute('open'); }
  }
  const body = new Element('body'), header = new Element(), shell = new Element(), content = new Element(), viewer = new Element(native ? 'dialog' : 'div');
  const closeButton = new Element('button'), scroll = new Element(), another = new Element('button'), trigger = new Element('button');
  closeButton.className = 'viewer-close'; scroll.className = 'viewer-scroll';
  viewer.append(closeButton, scroll, another);
  header.inert = true;
  if (nested) {body.append(header, shell); shell.append(content, viewer);} else body.append(header, content, viewer);
  document.body = body; document.activeElement = trigger;
  const window = {};
  vm.runInNewContext(fs.readFileSync(path.join(root, 'assets/image-viewer.js'), 'utf8'), {window, document, Array});
  let api;
  api = window.GuideImageViewer.mount(viewer, () => api.close());
  function key(key, shiftKey = false) { const event = {key, shiftKey, preventDefault(){this.prevented=true;}, stopImmediatePropagation(){this.stopped=true;}}; listeners.keydown(event); return event; }
  return {api, body, header, shell, content, viewer, closeButton, scroll, another, trigger, document, key, window, Element};
}

for (const native of [false, true]) for (const nested of [false, true]) {
  test(`Модалка ${native ? 'dialog' : 'div'}, nested=${nested}: фон inert и точное восстановление`, () => {
    const p = fixture(native, nested); p.body.style.overflow = 'clip';
    p.api.open(); assert.equal(p.content.inert, true); assert.equal(p.header.inert, true); assert.equal(p.viewer.inert, false);
    if (nested) assert.equal(p.shell.inert, false);
    assert.equal(p.body.style.overflow, 'hidden'); assert.equal(p.document.activeElement, p.closeButton);
    p.api.open(); p.api.close();
    assert.equal(p.body.style.overflow, 'clip'); assert.equal(p.content.inert, false); assert.equal(p.header.inert, true); assert.equal(p.document.activeElement, p.trigger);
    p.api.close(); assert.equal(p.body.style.overflow, 'clip');
  });
  test(`Модалка ${native ? 'dialog' : 'div'}, nested=${nested}: обе стороны Tab и Escape`, () => {
    const p = fixture(native, nested); p.api.open();
    p.document.activeElement = p.another; assert.ok(p.key('Tab').prevented); assert.equal(p.document.activeElement, p.closeButton);
    assert.ok(p.key('Tab', true).prevented); assert.equal(p.document.activeElement, p.another);
    p.document.activeElement = p.scroll; assert.ok(!p.key('Tab').prevented);
    p.key('Escape'); assert.equal(p.viewer.hasAttribute('open'), false); assert.equal(p.document.activeElement, p.trigger);
    assert.ok(!p.key('Tab').prevented);
  });
}

test('Все настоящие inline просмотрщики используют общий lifecycle и оригинальное изображение', () => {
  let count = 0;
  for (const name of fs.readdirSync(path.join(root, 'claude-ai'))) {
    const file = path.join(root, 'claude-ai', name, 'index.html');
    if (!fs.existsSync(file)) continue;
    const html = fs.readFileSync(file, 'utf8');
    if (!/var viewer\s*=/.test(html)) continue;
    count++;
    assert.ok(html.includes('GuideImageViewer.mount(viewer,'), name);
    assert.ok(html.includes('../../assets/image-viewer.js'), name);
    assert.ok(/img\.dataset\.fullSrc\s*\|\|\s*img\.currentSrc\s*\|\|\s*img\.src/.test(html), name);
    assert.ok(!/document\.body\.style\.overflow\s*=/.test(html), name);
  }
  assert.equal(count, 41);
});

test('Disabled элемент пропускается, внешний фокус возвращается в модалку', () => {
  const p = fixture(); p.another.disabled = true; p.api.open();
  p.document.activeElement = p.scroll; p.key('Tab'); assert.equal(p.document.activeElement, p.closeButton);
  p.document.activeElement = p.trigger; p.key('Tab', true); assert.equal(p.document.activeElement, p.scroll);
});

test('Native cancel закрывает через общий lifecycle и не теряет предшествующий inert', () => {
  const p = fixture(true); p.api.open();
  let prevented = false; p.viewer.events.cancel({preventDefault() {prevented = true;}});
  assert.ok(prevented); assert.equal(p.viewer.hasAttribute('open'), false);
  assert.equal(p.header.inert, true); assert.equal(p.content.inert, false);
});

test('Удалённый trigger не получает фокус при закрытии', () => {
  const p = fixture(); p.api.open(); p.trigger.isConnected = false;
  p.trigger.focus = () => {throw Error('removed trigger was focused');};
  assert.doesNotThrow(() => p.api.close()); assert.equal(p.content.inert, false);
});

test('Каждая статья с native dialog подключает helper до promty-foto.js', () => {
  let count = 0;
  for (const name of fs.readdirSync(path.join(root, 'claude-ai'))) {
    const file = path.join(root, 'claude-ai', name, 'index.html');
    if (!fs.existsSync(file)) continue;
    const html = fs.readFileSync(file, 'utf8');
    if (!html.includes('assets/promty-foto.js')) continue;
    count++;
    assert.ok(html.indexOf('assets/image-viewer.js') < html.indexOf('assets/promty-foto.js'), name);
  }
  assert.equal(count, 9);
});

test('Регрессия: zakryt-sekrety закрывает контейнер viewer до footer и содержит hint для onload', () => {
  const html = fs.readFileSync(path.join(root, 'claude-ai/zakryt-sekrety-ot-claude-code/index.html'), 'utf8');
  const modal = html.slice(html.indexOf('<div class="viewer"'), html.indexOf('<script src="../../assets/image-viewer.js"'));
  assert.ok(/<p class="viewer-hint">[^<]+<\/p><\/div>/.test(modal));
  assert.equal((modal.match(/<div\b/g) || []).length, (modal.match(/<\/div>/g) || []).length);
});

test('Регрессия: queued native close предыдущего открытия не снимает inert/overflow нового', () => {
  const p = fixture(true); p.body.style.overflow = 'clip';
  p.api.open(); p.api.close(); p.api.open();
  p.viewer.events.close();
  assert.equal(p.viewer.hasAttribute('open'), true);
  assert.equal(p.body.style.overflow, 'hidden'); assert.equal(p.content.inert, true);
  assert.equal(p.document.activeElement, p.closeButton);
  p.api.close(); assert.equal(p.body.style.overflow, 'clip'); assert.equal(p.content.inert, false);
});

test('Регрессия: promty-foto не очищает новое изображение по предыдущему queued close', () => {
  const p = fixture();
  p.body.children = [p.header, p.content];
  const shot = new p.Element(), img = new p.Element('img'), button = new p.Element('button');
  img.dataset = {fullSrc: 'original.png'}; img.src = 'reading.webp'; img.alt = 'Схема';
  button.closest = () => shot; img.closest = () => shot;
  shot.append(img, button); p.content.append(shot);
  p.document.createElement = tag => new p.Element(tag);
  p.document.querySelectorAll = () => [button];
  vm.runInNewContext(fs.readFileSync(path.join(root, 'assets/promty-foto.js'), 'utf8'), {document: p.document, GuideImageViewer: p.window.GuideImageViewer});
  const viewer = p.body.children.at(-1), big = viewer.querySelector('img');
  p.body.style.overflow = 'clip'; button.focus(); button.events.click();
  viewer.querySelector('.viewer-close').events.click(); button.events.click();
  viewer.events.close();
  assert.equal(big.src, 'original.png'); assert.equal(viewer.hasAttribute('open'), true);
  assert.equal(p.body.style.overflow, 'hidden');
});
