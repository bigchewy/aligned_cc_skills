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
    obstacles: [], solutions: [], key_actions: [], execute: [], feedback: { number: '', check_on: '', redraw_if: '' }, baseline: {} };
  return HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
}
const parse = (html) => JSON.parse(SLOT.exec(html)[2]);
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
    matchMedia: () => ({ matches: false }),
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
  async 'star wording shows in the solution editor'() {
    const html = HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify({ map_id: 'm1', revision: 1, person: 'P', goal: { text: 'g' },
      obstacles: [], solutions: [{ id: 's1', text: 'sol', star: true }], key_actions: [], execute: [], feedback: {}, baseline: {} }) + c);
    const p = page({ html }); await settle();
    p.openRef({ kind: 'solution', sid: 's1' });
    assert.ok(p.sandbox.document.getElementById('editor').textContent.includes('To change a star, tell Claude.'));
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
