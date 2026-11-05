// Runs the real page code from a map page against a stub DOM and fake file handles.
// Usage: node six_step_page_flows.js <path to a map page>. Exits 1 if any flow fails.
// test_six_step_page_flows.py runs it against the template and the example map.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const HTML = fs.readFileSync(process.argv[2], 'utf8');
const logicSrc = /<script id="map-logic">([\s\S]*?)<\/script>/.exec(HTML)[1];
const pageSrc = /<script id="map-page">([\s\S]*?)<\/script>/.exec(HTML)[1];
const SLOT = /(<script id="map-data" type="application\/json">)([\s\S]*?)(<\/script>)/;

function mapHtml(rev, goal, id) {
  const data = { map_id: id || 'm1', revision: rev, person: 'Pat', goal: { text: goal || 'g' },
    obstacles: [], unplaced: [], key_actions: [], execute: [], feedback: { number: '', check_on: '', redraw_if: '' }, baseline: {} };
  return HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
}
const parse = (html) => JSON.parse(SLOT.exec(html)[2]);
const node = (id, text, children, root) => ({ id, kind: 'obstacle', text, root_cause: Boolean(root), star: false, children: children || [] });
const sol = (id, text, children, star) => ({ id, kind: 'solution', text, root_cause: false, star: Boolean(star), children: children || [] });
function treeHtml(obstacles, unplaced, more) {
  const data = Object.assign(parse(mapHtml(1)), { obstacles, unplaced: unplaced || [] }, more || {});
  return HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
}
function findIn(items, id) {
  for (const it of items) { if (it.id === id) return it; const hit = findIn(it.children, id); if (hit) return hit; }
  return null;
}
const withData = (html, data) => html.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
const tick = () => new Promise((r) => setImmediate(r));
async function settle() { for (let i = 0; i < 12; i++) await tick(); }

class El {
  constructor(tag) { this.tag = (tag || 'div').toUpperCase(); this.kids = []; this.style = {}; this.dataset = {}; this.listeners = {};
    this.hidden = false; this.value = ''; this.className = ''; this._text = ''; this.options = [];
    this.classList = { add() {}, toggle() {} }; this.offsetHeight = 20; this.offsetWidth = 100; this.clientWidth = 1000; this.clientHeight = 800; this.offsetLeft = 0; this.offsetTop = 0; this.scrollLeft = 0; this.scrollTop = 0; }
  get textContent() { return this._text + this.kids.map((k) => k.textContent).join(' '); }
  set textContent(t) { this._text = t === undefined || t === null ? '' : String(t); this.kids = []; }
  appendChild(k) { this.kids.push(k); return k; }
  remove() {}
  click() {}
  focus() {}
  setSelectionRange() {}
  insertAdjacentHTML() {}
  contains() { return false; }
  closest() { return null; }
  getBoundingClientRect() { return { left: 0, top: 0, bottom: 20, right: 100 }; }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  walk() { return [this].concat(...this.kids.map((k) => k.walk())); }
  querySelector(s) { return this.querySelectorAll(s)[0] || null; }
  querySelectorAll(s) {
    if (s === '[data-field]') return this.walk().filter((k) => k.dataset.field);
    return this.walk().filter((k) => k.tag === s.toUpperCase());
  }
  button(text) { return this.walk().find((k) => k.tag === 'BUTTON' && k.textContent === text); }
}

function fakeIdb(store, opts) {
  if (opts.idbThrows) return { open() { throw new Error('no idb'); } };
  return { open() {
    const open = {};
    open.result = { createObjectStore() {}, close() {}, transaction() {
      const tx = {};
      setImmediate(() => tx.oncomplete && tx.oncomplete());
      return Object.assign(tx, { objectStore: () => ({
        get(k) { return { result: store.get(k) }; },
        put(v, k) { store.set(k, v); return {}; },
        delete(k) { store.delete(k); return {}; } }) });
    } };
    setImmediate(() => open.onsuccess());
    return open;
  } };
}

function fakeHandle(html) {
  const h = { html, writes: 0, gate: null, failWrite: false, gone: false, permission: 'granted', requestAsked: 0, written: [],
    async queryPermission() { return h.permission; },
    async requestPermission() { h.requestAsked++; if (h.permission === 'prompt') { if (h.noGesture) throw new Error('no gesture'); h.permission = h.grantOnPrompt === false ? 'denied' : 'granted'; } return h.permission; },
    async getFile() { if (h.gone) throw new Error('NotFound'); return { text: async () => h.html }; },
    async createWritable() { return {
      write: async (s) => { h.pending = s; },
      close: async () => { if (h.gate) await h.gate; if (h.failWrite) throw new Error('disk'); h.html = h.pending; h.writes++; h.written.push(parse(h.pending)); },
      abort: async () => {} }; } };
  return h;
}

function page(opts) {
  const els = {};
  const docListeners = {};
  const winListeners = {};
  const document = {
    documentElement: { outerHTML: opts.html || mapHtml(1, 'g') },
    body: new El('body'),
    getElementById(id) { return els[id] || (els[id] = new El()); },
    createElement(t) { return new El(t); },
    createTextNode(t) { const n = new El('text'); n.textContent = t; return n; },
    querySelectorAll() { return []; },
    addEventListener(t, f, cap) { (docListeners[t] = docListeners[t] || []).push({ f, cap }); }
  };
  let idbUses = 0;
  const idb = fakeIdb(opts.store || new Map(), opts);
  const sandbox = { document, console, setTimeout, Promise, JSON, Math, RegExp, Object, Array, Number, String, Boolean, decodeURIComponent, Date,
    innerWidth: 1200, innerHeight: 800,
    location: { pathname: opts.path || '/a/b/m-map.html', reload() { sandbox.reloaded = (sandbox.reloaded || 0) + 1; } },
    getComputedStyle: () => ({ paddingTop: '0', paddingBottom: '0' }),
    addEventListener(t, f) { (winListeners[t] = winListeners[t] || []).push(f); },
    URL: { createObjectURL() { return 'x'; }, revokeObjectURL() {} },
    Blob: function (parts) { sandbox.downloaded = parts[0]; }
  };
  Object.defineProperty(sandbox, 'indexedDB', { get() { idbUses++; return idb; } });
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  if (opts.picker) {
    sandbox.pickerCalls = 0;
    sandbox.showOpenFilePicker = async () => { sandbox.pickerCalls++; if (opts.pickAbort) { const e = new Error('x'); e.name = 'AbortError'; throw e; } return [opts.picker]; };
  }
  vm.createContext(sandbox);
  vm.runInContext(logicSrc, sandbox);
  vm.runInContext(pageSrc, sandbox);

  const api = {
    sandbox,
    status: () => document.getElementById('save-status').textContent,
    button: () => { const b = document.getElementById('save'); return b.hidden ? '' : b.textContent; },
    message: () => { const m = document.getElementById('message'); return m.hidden ? '' : m.textContent; },
    idbUses: () => idbUses,
    clickSave() { docListeners.click.filter((l) => l.cap).forEach((l) => l.f({ target: document.getElementById('save') })); document.getElementById('save').listeners.click[0](); },
    openRef(ref) { const box = new El('button'); box.dataset.ref = JSON.stringify(ref); box.closest = () => box;
      docListeners.click.filter((l) => !l.cap).forEach((l) => l.f({ target: box })); },
    openGoal() { api.openRef({ kind: 'goal' }); },
    edit(text) { api.openGoal(); document.getElementById('editor').querySelector('textarea').value = text; document.getElementById('editor').button('Done').listeners.click[0](); },
    addObstacle() { document.getElementById('add-obstacle').listeners.click[0](); },
    editorEl() { return document.getElementById('editor'); },
    canvasText() { return document.getElementById('canvas').textContent; },
    trayText() { const t = document.getElementById('tray'); return t.hidden ? '' : t.textContent; },
    panelText() { return document.getElementById('panel').textContent; },
    openItem(id) { api.openRef({ kind: 'obstacle', id }); },
    openSolution(id) { api.openRef({ kind: 'solution', id }); },
    press(name) { const b = document.getElementById('editor').button(name); assert.ok(b, 'no button: ' + name); b.listeners.click[0](); },
    pressDone() { api.press('Done'); },
    boxes() { return document.getElementById('canvas').kids.filter((k) => k.dataset.key).map((k) => ({
      key: k.dataset.key, x: parseFloat(k.style.left), y: parseFloat(k.style.top), w: parseFloat(k.style.width), h: k.offsetHeight })); },
    typeAndDone(text) { document.getElementById('editor').querySelector('textarea').value = text; document.getElementById('editor').button('Done').listeners.click[0](); },
    resize() { winListeners.resize[0](); },
    msgButton(t) { return document.getElementById('message').button(t); },
    warnsOnClose() { const e = { preventDefault() { e.prevented = true; } }; winListeners.beforeunload[0](e); return Boolean(e.prevented); }
  };
  return api;
}

const flows = {
  async 'first connect, clean page: no write, then edits write and the tell-Claude line shows once'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const p = page({ picker: f, store }); await settle();
    assert.equal(p.status(), "Changes aren't being saved yet."); assert.equal(p.button(), 'Turn on saving');
    p.clickSave();
    assert.equal(p.message(), 'Choose m-map.html in the b folder.');
    assert.equal(p.sandbox.pickerCalls, 1);
    await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved'); assert.equal(p.button(), ''); assert.equal(p.message(), '');
    assert.equal(store.size, 1);
    p.edit('one'); assert.equal(p.status(), 'Saving...'); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).goal.text, 'one'); assert.equal(parse(f.html).revision, 2);
    assert.equal(p.status(), 'All changes saved');
    assert.equal(p.message(), 'When you finish, tell Claude you changed the map.');
    p.sandbox.document.getElementById('message').hidden = true;
    p.edit('two'); await settle();
    assert.equal(f.writes, 2); assert.equal(parse(f.html).revision, 3); assert.equal(p.message(), '');
    assert.equal(p.warnsOnClose(), false);
  },
  async 'first connect, dirty page: writes once'() {
    const f = fakeHandle(mapHtml(1));
    const p = page({ picker: f }); await settle();
    p.edit('before'); await settle(); assert.equal(f.writes, 0); assert.equal(p.warnsOnClose(), true);
    p.clickSave(); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).goal.text, 'before'); assert.equal(p.status(), 'All changes saved');
  },
  async 'picker cancelled: nothing changes'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f, pickAbort: true }); await settle();
    p.clickSave(); await settle();
    assert.equal(p.message(), ''); assert.equal(p.status(), "Changes aren't being saved yet.");
    assert.equal(p.sandbox.document.getElementById('save').disabled, false);
  },
  async 'edit during a write reaches the file'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    let release; f.gate = new Promise((r) => { release = r; });
    p.edit('first'); await settle();
    assert.equal(p.warnsOnClose(), true);
    p.edit('second'); p.edit('third'); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'Saving...');
    f.gate = null; release(); await settle();
    assert.equal(parse(f.html).goal.text, 'third'); assert.equal(f.writes, 2); assert.equal(p.status(), 'All changes saved');
    assert.equal(p.warnsOnClose(), false);
  },
  async 'edit back to the old contents during a write reaches the file'() {
    const f = fakeHandle(mapHtml(1, 'g')); const p = page({ picker: f, html: mapHtml(1, 'g') }); await settle();
    p.clickSave(); await settle();
    let release; f.gate = new Promise((r) => { release = r; });
    p.edit('first'); await settle();
    p.edit('g'); await settle();
    f.gate = null; release(); await settle();
    assert.equal(parse(f.html).goal.text, 'g'); assert.equal(p.status(), 'All changes saved');
  },
  async 'stale: no loop, resize does not retry, next edit retries, a good write clears it'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.html = mapHtml(9);
    let reads = 0; const getFile = f.getFile; f.getFile = async () => { reads++; return getFile(); };
    p.edit('x'); await settle();
    assert.equal(reads, 1); assert.equal(p.status(), 'Not saved'); assert.equal(parse(f.html).revision, 9);
    assert.ok(p.message().startsWith('Claude changed this map, so your last edit is not in the file. Reload to get the new version.'));
    assert.ok(p.msgButton('Save a copy')); assert.ok(p.msgButton('Reload'));
    p.msgButton('Reload').listeners.click[0](); assert.equal(p.sandbox.reloaded, 1);
    p.resize(); p.openGoal(); p.sandbox.document.getElementById('editor').button('Done').listeners.click[0]();
    await settle(); assert.equal(reads, 1);
    p.edit('y'); await settle(); assert.equal(reads, 2); assert.equal(p.status(), 'Not saved'); assert.equal(f.writes, 0);
    f.html = mapHtml(1);
    p.edit('z'); await settle();
    assert.equal(f.writes, 1); assert.equal(p.status(), 'All changes saved'); assert.ok(!p.message().includes('Claude changed'));
  },
  async 'write-failed: stays connected, no loop, later good write clears'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true;
    p.edit('x'); await settle();
    assert.equal(p.status(), 'Not saved'); assert.ok(p.msgButton('Save a copy')); assert.ok(!p.msgButton('Reload'));
    p.resize(); await settle(); assert.equal(f.writes, 0);
    f.failWrite = false;
    p.resize(); await settle(); assert.equal(f.writes, 0);
    p.edit('y'); await settle(); assert.equal(f.writes, 1); assert.equal(p.status(), 'All changes saved');
  },
  async 'same edit again after going back gets another try'() {
    const f = fakeHandle(mapHtml(1, 'g')); const p = page({ picker: f, html: mapHtml(1, 'g') }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('x'); await settle(); f.failWrite = false;
    p.edit('g'); await settle(); assert.equal(f.writes, 0);
    p.edit('x'); await settle(); assert.equal(f.writes, 1); assert.equal(p.status(), 'All changes saved');
  },
  async 'wrong map on pick: forgotten, file untouched, edits stay'() {
    const f = fakeHandle(mapHtml(1, 'g', 'other')); const store = new Map(); const p = page({ picker: f, store }); await settle();
    p.edit('kept'); p.clickSave(); await settle();
    assert.equal(f.writes, 0); assert.equal(store.size, 0); assert.equal(p.status(), "Changes aren't being saved yet."); assert.equal(p.button(), 'Turn on saving');
    assert.ok(p.message().startsWith('That file holds a different map')); assert.equal(p.warnsOnClose(), true);
  },
  async 'write refused as wrong map mid-session: forgotten, no more writes'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map(); const p = page({ picker: f, store }); await settle();
    p.clickSave(); await settle(); assert.equal(store.size, 1);
    f.html = mapHtml(1, 'g', 'other');
    p.edit('x'); await settle();
    assert.equal(store.size, 0); assert.equal(p.status(), "Changes aren't being saved yet."); assert.equal(parse(f.html).map_id, 'other');
    p.edit('y'); await settle(); assert.equal(f.writes, 0);
  },
  async 'reload, permission granted: connects with no click, no write'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    const b = page({ picker: f, store }); await settle();
    assert.equal(b.sandbox.pickerCalls, 0); assert.equal(b.status(), 'All changes saved'); assert.equal(f.writes, 0);
    b.edit('x'); await settle(); assert.equal(f.writes, 1);
  },
  async 'reload, permission needs a click: paused, button uses the remembered file with no dialog'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    f.permission = 'prompt'; f.requestAsked = 0;
    const b = page({ picker: f, store }); await settle();
    assert.equal(b.status(), 'Saving is paused.'); assert.equal(b.button(), 'Turn saving back on'); assert.equal(f.requestAsked, 0);
    b.edit('x'); await settle(); assert.equal(f.writes, 0);
    b.clickSave(); await settle();
    assert.equal(b.sandbox.pickerCalls, 0); assert.equal(b.status(), 'All changes saved'); assert.equal(f.writes, 1);
  },
  async 'permission denied at the prompt keeps the remembered file'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    f.permission = 'prompt'; f.grantOnPrompt = false;
    const b = page({ picker: f, store }); await settle();
    b.clickSave(); await settle();
    assert.equal(b.status(), 'Saving is paused.'); assert.equal(store.size, 1); assert.ok(b.msgButton('Save a copy'));
  },
  async 'permission lost mid-session pauses, then the button turns it back on'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map(); const p = page({ picker: f, store }); await settle();
    p.clickSave(); await settle();
    f.permission = 'prompt'; f.noGesture = true;
    p.edit('x'); await settle();
    assert.equal(p.status(), 'Saving is paused.'); assert.equal(store.size, 1);
    p.edit('y'); await settle(); assert.equal(f.writes, 0);
    f.noGesture = false; p.clickSave(); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).goal.text, 'y');
  },
  async 'reload, file deleted: forgotten, asks again'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    f.gone = true;
    const b = page({ picker: f, store }); await settle();
    assert.equal(store.size, 0); assert.equal(b.status(), "Changes aren't being saved yet."); assert.equal(b.button(), 'Turn on saving');
  },
  async 'reload, file replaced by a different map: forgotten, asks again'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    f.html = mapHtml(1, 'g', 'other');
    const b = page({ picker: f, store }); await settle();
    assert.equal(store.size, 0); assert.equal(b.status(), "Changes aren't being saved yet."); assert.equal(f.writes, 0);
  },
  async 'reload, file newer: treated as paused'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle(); a.clickSave(); await settle();
    f.html = mapHtml(5);
    const b = page({ picker: f, store }); await settle();
    assert.equal(b.status(), 'Saving is paused.'); assert.equal(store.size, 1); assert.equal(b.message(), '');
    b.clickSave(); await settle();
    assert.equal(b.status(), 'Not saved'); assert.ok(b.msgButton('Reload'));
  },
  async 'copy in another folder never uses the original file'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store, path: '/one/m-map.html' }); await settle(); a.clickSave(); await settle();
    const copy = page({ store, path: '/two/m-map.html', picker: fakeHandle(mapHtml(1)) }); await settle();
    assert.equal(copy.status(), "Changes aren't being saved yet.");
    copy.edit('x'); await settle(); assert.equal(f.writes, 0);
  },
  async 'IndexedDB throws: page works, asks again after reload'() {
    const f = fakeHandle(mapHtml(1)); const a = page({ picker: f, idbThrows: true }); await settle();
    assert.equal(a.status(), "Changes aren't being saved yet.");
    a.clickSave(); await settle(); a.edit('x'); await settle();
    assert.equal(f.writes, 1); assert.equal(a.status(), 'All changes saved');
    const b = page({ picker: f, idbThrows: true }); await settle();
    assert.equal(b.status(), "Changes aren't being saved yet."); assert.equal(b.button(), 'Turn on saving');
  },
  async 'no picker: download path, no IndexedDB, nothing writes'() {
    const p = page({}); await settle();
    assert.equal(p.status(), ''); assert.equal(p.button(), 'Save to Downloads'); assert.equal(p.idbUses(), 0);
    assert.equal(p.sandbox.document.getElementById('browser-note').hidden, false);
    p.edit('x'); await settle();
    assert.equal(p.status(), 'Not saved yet.'); assert.equal(p.sandbox.downloaded, undefined);
    p.clickSave();
    assert.ok(p.sandbox.downloaded); assert.equal(parse(p.sandbox.downloaded).revision, 2);
    assert.equal(p.status(), ''); assert.ok(p.message().includes('Downloads')); assert.equal(p.idbUses(), 0);
  },
  async 'blank new item stays out of the file until it has text'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    p.addObstacle(); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndDone('blocker'); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).obstacles[0].text, 'blocker');
  },
  async 'the picks checkbox shows in the solution editor, ticked for a star'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], true)])]);
    const p = page({ html }); await settle();
    p.openSolution('s1');
    const ed = p.editorEl();
    assert.ok(ed.textContent.includes('This is one of my picks'));
    assert.ok(!ed.textContent.includes('tell Claude.'));
    assert.equal(ed.querySelector('input').checked, true);
  },
  async 'a tray solution offers no pick and no obstacle until it is attached'() {
    const html = treeHtml([node('o1', 'ob')], [sol('s1', 'tray')]);
    const p = page({ html }); await settle();
    p.openSolution('s1');
    const ed = p.editorEl();
    assert.ok(!ed.textContent.includes('This is one of my picks'));
    assert.ok(!ed.button('Add an obstacle'));
    assert.ok(ed.button('Delete'));
  },
  async 'star key shows only with stars'() {
    const none = page({ html: treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], false)])]) }); await settle();
    assert.equal(none.sandbox.document.getElementById('picks-key').hidden, true);
    const some = page({ html: treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], true)])]) }); await settle();
    assert.equal(some.sandbox.document.getElementById('picks-key').hidden, false);
  },
  async 'ticking the picks box saves the star and shows the key'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    const key = p.sandbox.document.getElementById('picks-key');
    assert.equal(key.hidden, true);
    p.openSolution('s1');
    const box = p.editorEl().querySelector('input');
    assert.equal(box.checked, false);
    box.checked = true; box.listeners.change[0](); await settle();
    assert.equal(f.writes, 1);
    assert.equal(findIn(parse(f.html).obstacles, 's1').star, true);
    assert.equal(key.hidden, false);
    assert.equal(p.status(), 'All changes saved');
    box.checked = false; box.listeners.change[0](); await settle();
    assert.equal(findIn(parse(f.html).obstacles, 's1').star, false);
    assert.equal(key.hidden, true);
  },

  // A file Claude rewrote must never be overwritten, whatever its revision says.
  async 'page at rev 3, Claude writes rev 2: the next edit is refused and the file stays'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    p.edit('m1'); await settle(); p.edit('m2'); await settle();
    assert.equal(parse(f.html).revision, 3);
    const claude = mapHtml(2, 'claude-rewrite'); f.html = claude; const before = f.writes;
    p.edit('m3'); await settle();
    assert.equal(f.html, claude); assert.equal(f.writes, before);
    assert.equal(p.status(), 'Not saved'); assert.ok(p.msgButton('Reload')); assert.ok(p.msgButton('Save a copy'));
    assert.ok(p.message().startsWith('Claude changed this map, so your last edit is not in the file.'));
    assert.equal(p.warnsOnClose(), true);
  },
  async 'page at rev 2, Claude writes rev 2: the next edit is refused and the page warns on close'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    p.edit('m1'); await settle();
    assert.equal(parse(f.html).revision, 2);
    const claude = mapHtml(2, 'claude-rewrite'); f.html = claude;
    p.edit('m2'); await settle();
    assert.equal(f.html, claude); assert.equal(f.writes, 1);
    assert.equal(p.status(), 'Not saved'); assert.equal(p.warnsOnClose(), true);
  },
  async 'clean page connects to the same revision with other content: refused, no write'() {
    const f = fakeHandle(mapHtml(1, 'other-content')); const store = new Map();
    const p = page({ picker: f, store }); await settle();
    p.clickSave(); await settle();
    assert.equal(f.writes, 0); assert.equal(parse(f.html).goal.text, 'other-content');
    assert.equal(p.status(), 'Not saved'); assert.ok(p.msgButton('Reload'));
  },
  async 'Claude moves only the baseline: not refused, and the file keeps that baseline'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    const data = parse(f.html); data.baseline = { person: 'Read by Claude' };
    f.html = withData(f.html, data);
    p.edit('mine'); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(f.writes, 1);
    assert.deepEqual(parse(f.html).baseline, { person: 'Read by Claude' });
    p.edit('mine again'); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(f.writes, 2);
  },
  async 'a file with other spacing and key order connects with no refusal'() {
    const data = parse(mapHtml(1));
    const reversed = {}; Object.keys(data).reverse().forEach((k) => { reversed[k] = data[k]; });
    const html = HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(reversed, null, 2) + c);
    const f = fakeHandle(html); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(p.message(), ''); assert.equal(f.writes, 0);
  },
  async 'the data this page ships with counts as what the file holds'() {
    if (!parse(HTML).map_id) return; // The template's starter data has no id, so it draws no page.
    const f = fakeHandle(HTML); const p = page({ picker: f, html: HTML }); await settle();
    p.clickSave(); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(p.message(), ''); assert.equal(f.writes, 0);
    assert.equal(p.warnsOnClose(), false);
  },
  async 'after reload the page matches the file its last write left'() {
    const f = fakeHandle(mapHtml(1)); const store = new Map();
    const a = page({ picker: f, store }); await settle();
    a.clickSave(); await settle(); a.edit('saved text'); await settle();
    const b = page({ picker: f, store, html: f.html }); await settle();
    assert.equal(b.status(), 'All changes saved');
    b.edit('more'); await settle();
    assert.equal(f.writes, 2); assert.equal(parse(f.html).goal.text, 'more');
  },
  async 'a copy moved over the file is not taken for a rewrite by Claude'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('in the copy'); await settle(); f.failWrite = false;
    p.msgButton('Save a copy').listeners.click[0]();
    assert.ok(p.message().includes('replacing the old one'));
    f.html = p.sandbox.downloaded;
    p.edit('after the copy'); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(parse(f.html).goal.text, 'after the copy');
    assert.equal(parse(f.html).revision, 2);
  },
  async 'a copy moved over the file, then Claude rewrites: refused again'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('in the copy'); await settle(); f.failWrite = false;
    p.msgButton('Save a copy').listeners.click[0]();
    const claude = mapHtml(2, 'claude-rewrite'); f.html = claude;
    p.edit('after the copy'); await settle();
    assert.equal(f.html, claude); assert.equal(p.status(), 'Not saved');
  },

  // After a denied permission the person can still reach the picker.
  async 'denied permission offers Choose the file, and a good pick replaces the remembered file'() {
    const old = fakeHandle(mapHtml(1)); old.permission = 'prompt'; old.grantOnPrompt = false;
    const picked = fakeHandle(mapHtml(1)); const store = new Map();
    const key = JSON.stringify(['m1', '/a/b/m-map.html']); store.set(key, old);
    const p = page({ picker: picked, store }); await settle();
    assert.equal(p.status(), 'Saving is paused.');
    p.clickSave(); await settle();
    assert.equal(p.status(), 'Saving is paused.'); assert.equal(p.sandbox.pickerCalls, 0);
    assert.ok(p.msgButton('Save a copy')); assert.ok(!p.msgButton('Reload'));
    p.msgButton('Choose the file').listeners.click[0]();
    assert.equal(p.sandbox.pickerCalls, 1);
    assert.equal(p.message(), 'Choose m-map.html in the b folder.');
    await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(store.get(key), picked);
    p.edit('x'); await settle();
    assert.equal(picked.writes, 1); assert.equal(old.writes, 0);
  },
  async 'denied permission, then the pick is cancelled: still paused with the old file'() {
    const old = fakeHandle(mapHtml(1)); old.permission = 'prompt'; old.grantOnPrompt = false;
    const store = new Map(); const key = JSON.stringify(['m1', '/a/b/m-map.html']); store.set(key, old);
    const p = page({ picker: fakeHandle(mapHtml(1)), pickAbort: true, store }); await settle();
    p.clickSave(); await settle();
    p.msgButton('Choose the file').listeners.click[0](); await settle();
    assert.equal(p.status(), 'Saving is paused.'); assert.equal(store.get(key), old);
    assert.equal(p.sandbox.document.getElementById('save').disabled, false);
  },
  async 'only a permission refusal offers Choose the file'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('x'); await settle();
    assert.ok(p.msgButton('Save a copy')); assert.ok(!p.msgButton('Choose the file'));
  },

  // Going back to what the file holds.
  async 'write-failed, then an edit back to the file contents clears Not saved'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('x'); await settle();
    assert.equal(p.status(), 'Not saved');
    p.edit('g'); await settle();
    assert.equal(p.status(), 'All changes saved'); assert.equal(p.message(), ''); assert.equal(p.warnsOnClose(), false);
    assert.equal(f.writes, 0);
  },
  async 'stale, then an edit back to what the page loaded keeps the refusal'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.html = mapHtml(5, 'claude-rewrite');
    p.edit('x'); await settle();
    p.edit('g'); await settle();
    assert.equal(p.status(), 'Not saved'); assert.ok(p.msgButton('Reload'));
    assert.ok(p.message().startsWith('Claude changed this map'));
  },

  // Save a copy while the file is newer.
  async 'stale copy message keeps Reload and survives the next stale write'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.html = mapHtml(5, 'claude-rewrite');
    p.edit('x'); await settle();
    p.msgButton('Save a copy').listeners.click[0]();
    assert.ok(p.message().includes("don't replace it")); assert.ok(p.msgButton('Reload'));
    assert.equal(parse(p.sandbox.downloaded).goal.text, 'x');
    p.edit('y'); await settle();
    assert.equal(p.status(), 'Not saved'); assert.ok(p.message().includes("don't replace it"));
    assert.ok(p.msgButton('Reload'));
    p.msgButton('Reload').listeners.click[0](); assert.equal(p.sandbox.reloaded, 1);
    // The later edit isn't in the first copy, so the message must still offer another one.
    p.msgButton('Save a copy').listeners.click[0]();
    assert.equal(parse(p.sandbox.downloaded).goal.text, 'y');
  },
  async 'a copy message gives way to a different refusal, and has no Reload unless stale'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('x'); await settle();
    p.msgButton('Save a copy').listeners.click[0]();
    assert.ok(p.message().includes('replacing the old one')); assert.ok(!p.msgButton('Reload'));
    f.failWrite = false; f.html = mapHtml(5, 'claude-rewrite');
    p.edit('y'); await settle();
    assert.ok(p.message().startsWith('Claude changed this map')); assert.ok(p.msgButton('Reload'));
  },

  async 'a queued write never puts a blank new item in the file'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    let release; f.gate = new Promise((r) => { release = r; });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.addObstacle(); await settle();
    f.gate = null; release(); await settle();
    assert.deepEqual(parse(f.html).obstacles, []); assert.equal(parse(f.html).goal.text, 'one');
    p.typeAndDone('blocker'); await settle();
    assert.equal(parse(f.html).goal.text, 'two'); assert.equal(parse(f.html).obstacles[0].text, 'blocker');
    assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
  },
  async 'a queued write held for a new item goes out if the item is cancelled'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    let release; f.gate = new Promise((r) => { release = r; });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.addObstacle(); await settle();
    f.gate = null; release(); await settle();
    p.typeAndDone(''); await settle();
    assert.equal(parse(f.html).goal.text, 'two'); assert.deepEqual(parse(f.html).obstacles, []);
    assert.equal(p.status(), 'All changes saved');
  },
  // Obstacles are a labeled tree.
  async 'add a sub-obstacle and see its label, and the file gets the child'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o1'); p.press('Add a sub-obstacle'); await settle();
    p.typeAndDone('why one'); await settle();
    assert.ok(p.canvasText().includes('1A'), p.canvasText());
    assert.ok(p.canvasText().includes('why one'));
    const saved = parse(f.html).obstacles[0];
    assert.equal(saved.children.length, 1); assert.equal(saved.children[0].text, 'why one');
    assert.deepEqual(Object.keys(saved.children[0]).sort(), ['children', 'id', 'kind', 'root_cause', 'star', 'text']);
    assert.ok(!JSON.stringify(parse(f.html).obstacles).includes('1A'));
    p.openItem(saved.children[0].id); p.press('Add a sub-obstacle'); await settle();
    p.typeAndDone('deeper'); await settle();
    assert.ok(p.canvasText().includes('1A1'), p.canvasText());
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a new obstacle and a new sub-obstacle get ids nothing else in the file uses'() {
    const html = treeHtml([node('o1', 'first', [node('o7', 'kid')])], [], { baseline: { obstacles: [{ id: 'o9' }] } });
    const p = page({ html }); await settle();
    p.openItem('o7'); p.press('Add a sub-obstacle'); p.typeAndDone('deep');
    p.addObstacle(); p.typeAndDone('top');
    const canvas = p.sandbox.document.getElementById('canvas').kids.map((k) => k.dataset.ref).filter(Boolean).map(JSON.parse);
    const ids = canvas.filter((r) => r.kind === 'obstacle').map((r) => r.id);
    assert.deepEqual(ids.slice().sort(), ['o1', 'o10', 'o11', 'o7']);
  },
  async 'a blank new sub-item stays out of the file until it has text'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o2'); p.press('Add a sub-obstacle'); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(parse(f.html).obstacles[0].children[0].children.length, 0);
    p.typeAndDone('now it has text'); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).obstacles[0].children[0].children[0].text, 'now it has text');
  },
  async 'a blank new sub-item closed empty leaves no trace in the file or on the page'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o1'); p.press('Add a sub-obstacle'); await settle();
    assert.ok(p.canvasText().includes('1A'));
    p.typeAndDone(''); await settle();
    assert.ok(!p.canvasText().includes('1A'));
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
  },
  async 'a queued write never puts a blank new sub-item in the file'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    let release; f.gate = new Promise((r) => { release = r; });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.openItem('o1'); p.press('Add a sub-obstacle'); await settle();
    f.gate = null; release(); await settle();
    assert.deepEqual(parse(f.html).obstacles[0].children, []); assert.equal(parse(f.html).goal.text, 'one');
    p.typeAndDone('kid'); await settle();
    assert.equal(parse(f.html).goal.text, 'two'); assert.equal(parse(f.html).obstacles[0].children[0].text, 'kid');
  },
  async 'delete a branch: the whole branch goes, its solutions with it, later siblings renumber'() {
    const html = treeHtml([
      node('o1', 'first', [
        node('o2', 'kid a', [node('o3', 'grandkid', [sol('s1', 'gone with it')])]),
        node('o4', 'kid b')
      ]),
      node('o5', 'other', [sol('s2', 'stays')])
    ]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o2'); p.press('Delete this and its 2 sub-items'); await settle();
    const saved = parse(f.html);
    assert.equal(findIn(saved.obstacles, 'o2'), null); assert.equal(findIn(saved.obstacles, 's1'), null);
    assert.deepEqual(saved.unplaced, []); assert.equal(p.trayText(), '');
    assert.ok(findIn(saved.obstacles, 's2'));
    assert.ok(p.canvasText().includes('1A'), p.canvasText()); assert.ok(p.canvasText().includes('kid b'));
    assert.ok(!p.canvasText().includes('1B'));
  },
  async 'delete an item and see its plan row go, while the key action stays'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix it'), sol('s2', 'other fix')])], [], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1', 's2'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' },
        { solution_id: 's2', first_move: 'the other move', owner: 'o', others_decide: '' }]
    });
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.sandbox.document.getElementById('toggle-plan').listeners.click[0]();
    assert.ok(p.panelText().includes('the first move'));
    p.openSolution('s1'); p.press('Delete'); await settle();
    assert.ok(!p.panelText().includes('the first move'));
    assert.ok(p.panelText().includes('the other move'));
    assert.ok(p.panelText().includes('the action'));
    const saved = parse(f.html);
    assert.deepEqual(saved.execute.map((e) => e.solution_id), ['s2']);
    assert.deepEqual(saved.key_actions[0].solution_ids, ['s2']);
  },
  async 'add an obstacle under a solution and see its label continue the numbering'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid a'), node('o3', 'kid b', [node('o4', 'child'), sol('s1', 'the fix')])])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openSolution('s1'); p.press('Add an obstacle'); await settle();
    p.typeAndDone('in the way'); await settle();
    assert.ok(p.canvasText().includes('1B1'), p.canvasText());
    assert.ok(p.canvasText().includes('1B2'), p.canvasText());
    const under = findIn(parse(f.html).obstacles, 's1').children[0];
    assert.equal(under.text, 'in the way'); assert.equal(under.kind, 'obstacle');
  },
  async 'attach a tray solution beside a child, add an obstacle under it, and its label continues'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])], [sol('s1', 'from the tray')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openSolution('s1');
    const select = p.editorEl().querySelector('select');
    select.value = '0'; select.listeners.change[0](); await settle();
    assert.ok(!p.canvasText().includes('1B'), p.canvasText());
    p.openSolution('s1'); p.press('Add an obstacle'); await settle();
    p.typeAndDone('in the way'); await settle();
    const text = p.canvasText();
    assert.ok(text.includes('1A'), text); assert.ok(text.includes('1B'), text);
    const saved = parse(f.html);
    assert.deepEqual(findIn(saved.obstacles, 'o1').children.map((c) => c.id), ['o2', 's1']);
    assert.equal(findIn(saved.obstacles, 's1').children[0].text, 'in the way');
    assert.ok(!JSON.stringify(saved.obstacles).includes('1B'));
  },
  async 'attach a tray solution through the form'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])], [sol('s1', 'from the tray')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    assert.ok(p.trayText().includes('from the tray'));
    p.openSolution('s1');
    const select = p.editorEl().querySelector('select');
    assert.deepEqual(select.kids.map((k) => k.textContent), ['Choose where it goes', '1 first', '1A kid']);
    select.value = '1'; select.listeners.change[0](); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.unplaced, []);
    assert.deepEqual(findIn(saved.obstacles, 'o2').children.map((c) => c.id), ['s1']);
    assert.equal(p.trayText(), '');
    assert.ok(p.canvasText().includes('from the tray'));
  },
  async 'a blank new solution stays out of the file, and closing it empty leaves no trace'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o1'); p.press('Add a solution'); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndDone(''); await settle();
    assert.equal(f.writes, 0); assert.equal(p.warnsOnClose(), false);
    assert.deepEqual(parse(f.html).obstacles[0].children, []);
  },
  async 'the delete control counts everything that goes with the item'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'a', [node('o3', 'b')]), node('o4', 'c')])]);
    const p = page({ html }); await settle();
    p.openItem('o1');
    assert.ok(p.editorEl().button('Delete this and its 3 sub-items'));
    p.pressDone(); p.openItem('o4');
    assert.ok(p.editorEl().button('Delete'));
  },
  async 'a root cause can be marked and unmarked, and offers only a solution'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openItem('o1');
    assert.ok(!p.editorEl().button('Mark as root cause'));
    assert.ok(p.editorEl().button('Add a sub-obstacle'));
    assert.ok(p.editorEl().button('Add a solution'));
    p.pressDone();
    p.openItem('o2'); p.press('Mark as root cause'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].root_cause, true);
    p.openItem('o2');
    assert.ok(!p.editorEl().button('Add a sub-obstacle')); assert.ok(p.editorEl().button('Add a solution'));
    p.press('Unmark root cause'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].root_cause, false);
  },
  async 'an obstacle with only a solution under it can still be a root cause'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix', [node('o2', 'in the way')])])]);
    const p = page({ html }); await settle();
    p.openItem('o1');
    assert.ok(p.editorEl().button('Mark as root cause'));
    p.pressDone();
    p.openItem('o2');
    assert.ok(p.editorEl().button('Mark as root cause'));
  },
  async 'a solution offers an obstacle and no solution, and Move to lists where it can go'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [sol('s1', 'sol')]), node('o3', 'kid two')]), node('o4', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.openSolution('s1');
    assert.ok(p.editorEl().button('Add an obstacle')); assert.ok(!p.editorEl().button('Add a solution'));
    assert.ok(!p.editorEl().textContent.includes('obstacles. Editing'));
    const select = p.editorEl().querySelector('select');
    const names = select.kids.map((k) => k.textContent);
    assert.deepEqual(names, ['Choose where it goes', '1 first', '1B kid two', '2 other']);
    select.value = String(1);
    select.listeners.change[0](); await settle();
    const saved = parse(f.html);
    assert.deepEqual(findIn(saved.obstacles, 'o2').children, []);
    assert.deepEqual(findIn(saved.obstacles, 'o3').children.map((c) => c.id), ['s1']);
  },
  async 'the plan panel names items by label'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [sol('s1', 'sol', [], true)])])], [],
      { key_actions: [{ text: 'act', risk: 'low', solution_ids: ['s1'] }],
        execute: [{ solution_id: 's1', first_move: 'm', owner: 'o', others_decide: '' }] });
    const p = page({ html }); await settle();
    assert.ok(p.panelText().includes('sol (1A)'), p.panelText());
  },
  async 'the wide map draws every box apart from every other, right of the goal'() {
    const html = treeHtml([
      node('a1', 'x', [node('a2', 'y', [node('a3', 'z', [node('a4', 'w', [sol('s1', 'sol')]), sol('s2', 'sol')]), sol('s3', 'sol')]), node('a5', 'v', [sol('s4', 'sol', [node('a6', 'u')])])]),
      node('b1', 'x', [node('b2', 'y'), node('b3', 'z'), node('b4', 'w'), node('b5', 'v')]),
      node('c1', 'x', [sol('s5', 'sol')])
    ]);
    const p = page({ html }); await settle();
    const boxes = p.boxes();
    assert.equal(boxes.length, 18);
    const goal = boxes.find((b) => b.key === 'goal|');
    boxes.filter((b) => b !== goal).forEach((b) => assert.ok(b.x > goal.x + goal.w, b.key));
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i]; const b = boxes[j];
        const apart = a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y;
        assert.ok(apart, a.key + ' overlaps ' + b.key);
      }
    }
  },
  async 'a map in the old shape shows the message and draws nothing'() {
    const html = treeHtml([{ id: 'o1', text: 'old', whys: ['w'], root_cause: 'r', solution_ids: [] }]);
    const p = page({ html }); await settle();
    const doc = p.sandbox.document;
    assert.equal(doc.getElementById('data-problem').hidden, false);
    assert.ok(doc.getElementById('data-problem-reason').textContent.startsWith('Obstacle 1 '));
    assert.equal(doc.getElementById('canvas').kids.length, 0);
  },
  async 'a map with the old solutions list shows the message and draws nothing'() {
    const html = treeHtml([], [], { solutions: [] });
    const p = page({ html }); await settle();
    const doc = p.sandbox.document;
    assert.equal(doc.getElementById('data-problem').hidden, false);
    assert.equal(doc.getElementById('data-problem-reason').textContent, 'The map uses the old map shape.');
    assert.equal(doc.getElementById('canvas').kids.length, 0);
  },
  async 'a plan row naming a missing solution shows the message and draws nothing'() {
    const html = treeHtml([], [], { execute: [{ solution_id: 'gone', first_move: 'm', owner: '', others_decide: '' }] });
    const p = page({ html }); await settle();
    const doc = p.sandbox.document;
    assert.ok(doc.getElementById('data-problem-reason').textContent.includes('gone'));
    assert.equal(doc.getElementById('canvas').kids.length, 0);
  },

  async 'editing the goal writes one sentence and nothing else into the file'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    p.edit('80% in-office attendance by end of Q2, up from 40%'); await settle();
    assert.deepEqual(parse(f.html).goal, { text: '80% in-office attendance by end of Q2, up from 40%' });
    p.openGoal();
    assert.equal(p.sandbox.document.getElementById('editor').querySelectorAll('[data-field]').length, 1);
  }
};

(async () => {
  let failed = 0;
  for (const name of Object.keys(flows)) {
    try { await flows[name](); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + (e.stack || e).split('\n').slice(0, 4).join('\n     ')); }
  }
  console.log(failed ? failed + ' failed' : 'all ' + Object.keys(flows).length + ' passed');
  process.exit(failed ? 1 : 0);
})();
