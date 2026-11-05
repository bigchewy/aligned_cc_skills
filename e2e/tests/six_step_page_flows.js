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
  constructor(tag) { this.tag = (tag || 'div').toUpperCase(); this.kids = []; this.parent = null; this.style = {}; this.dataset = {}; this.listeners = {}; this.attrs = {};
    this.hidden = false; this.value = ''; this.className = ''; this._text = ''; this.options = [];
    const self = this;
    const names = () => self.className.split(' ').filter(Boolean);
    this.classList = {
      add(c) { if (!names().includes(c)) self.className = names().concat(c).join(' '); },
      remove(c) { self.className = names().filter((n) => n !== c).join(' '); },
      toggle(c, on) { if (on) self.classList.add(c); else self.classList.remove(c); },
      contains(c) { return names().includes(c); } };
    this.offsetHeight = 20; this.offsetWidth = 100; this.clientWidth = 1000; this.clientHeight = 800; this.scrollHeight = 20; this.offsetLeft = 0; this.offsetTop = 0; this.scrollLeft = 0; this.scrollTop = 0; }
  get textContent() { return this._text + this.kids.map((k) => k.textContent).join(' '); }
  // Removing a focused element drops the focus, as a browser does.
  set textContent(t) { if (El.active && El.active !== this && this.contains(El.active)) El.active = null;
    this._text = t === undefined || t === null ? '' : String(t); this.kids = []; }
  appendChild(k) { k.parent = this; this.kids.push(k); return k; }
  remove() {}
  click() {}
  focus() { El.active = this; }
  blur() { if (El.active === this) El.active = null; }
  scrollIntoView() {}
  setSelectionRange() {}
  insertAdjacentHTML() {}
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  contains(other) { for (let n = other; n; n = n.parent) { if (n === this) return true; } return false; }
  closest(s) { const attr = /^\[data-(\w+)\]$/.exec(s)[1]; for (let n = this; n; n = n.parent) { if (n.dataset[attr]) return n; } return null; }
  // A box sits where its style puts it, moved by how far the map has scrolled.
  getBoundingClientRect() {
    if (this === El.scroller) return { left: 0, top: 0, right: 1000, bottom: 800, width: 1000, height: 800 };
    const left = (parseFloat(this.style.left) || 0) - El.scroller.scrollLeft;
    const top = (parseFloat(this.style.top) || 0) - El.scroller.scrollTop;
    return { left, top, right: left + 100, bottom: top + 20, width: 100, height: 20 };
  }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  walk() { return [this].concat(...this.kids.map((k) => k.walk())); }
  querySelector(s) { return this.querySelectorAll(s)[0] || null; }
  querySelectorAll(s) {
    const keyed = /^\[data-key="(.*)"\]$/.exec(s);
    if (keyed) return this.walk().filter((k) => k.dataset.key === keyed[1]);
    if (s === '[data-ref]') return this.walk().filter((k) => k.dataset.ref);
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
    get activeElement() { return El.active || this.body; },
    getElementById(id) { return els[id] || (els[id] = new El()); },
    createElement(t) { return new El(t); },
    createTextNode(t) { const n = new El('text'); n.textContent = t; return n; },
    querySelectorAll() { return []; },
    addEventListener(t, f, cap) { (docListeners[t] = docListeners[t] || []).push({ f, cap }); }
  };
  // The parts of the page's HTML the flows need in their real places.
  El.active = null;
  El.scroller = document.getElementById('map');
  El.scroller.appendChild(document.getElementById('canvas-frame')).appendChild(document.getElementById('canvas'));
  document.getElementById('typing').hidden = true;
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
    el(id) { return document.getElementById(id); },
    active() { return document.activeElement; },
    // Capture listeners, then the target and what holds it, then bubble listeners on the document.
    fire(target, type, more) {
      const e = Object.assign({ target, preventDefault() { e.prevented = true; } }, more);
      (docListeners[type] || []).filter((l) => l.cap).forEach((l) => l.f(e));
      for (let n = target; n; n = n.parent) (n.listeners[type] || []).forEach((f) => f(e));
      (docListeners[type] || []).filter((l) => !l.cap).forEach((l) => l.f(e));
      return e;
    },
    box(id) {
      const end = id === 'goal' ? 'goal|' : '|' + id;
      const all = api.el('canvas').walk().concat(api.el('tray').walk());
      const box = all.find((k) => k.dataset.key && k.dataset.key.endsWith(end));
      assert.ok(box, 'no box: ' + id);
      return box;
    },
    clickItem(id) { api.fire(api.box(id), 'click'); },
    clickEmpty() { api.fire(api.el('map'), 'click'); },
    typeOn(id) { api.clickItem(id); api.fire(api.box(id), 'dblclick'); },
    openGoal() { api.typeOn('goal'); },
    pressEnter() { return api.fire(api.el('typing'), 'keydown', { key: 'Enter' }); },
    typeAndEnter(text) { api.el('typing').value = text; api.pressEnter(); },
    edit(text) { api.openGoal(); api.typeAndEnter(text); },
    plus(kind) { const b = api.el('plus-' + kind); assert.equal(b.hidden, false, 'no ' + kind + ' plus'); api.fire(b, 'click'); },
    tool(id) { const b = api.el(id); assert.equal(b.hidden, false, 'no tool: ' + id); api.fire(b, 'click'); },
    pluses() { return ['obstacle', 'solution'].filter((k) => !api.el('plus-' + k).hidden); },
    isSelected(id) { return api.box(id).classList.contains('selected'); },
    addObstacle() { api.fire(document.getElementById('add-obstacle'), 'click'); },
    canvasText() { return document.getElementById('canvas').textContent; },
    trayText() { const t = document.getElementById('tray'); return t.hidden ? '' : t.textContent; },
    panelText() { return document.getElementById('panel').textContent; },
    boxes() { return document.getElementById('canvas').kids.filter((k) => k.dataset.key).map((k) => ({
      key: k.dataset.key, x: parseFloat(k.style.left), y: parseFloat(k.style.top), w: parseFloat(k.style.width), h: k.offsetHeight })); },
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
    p.resize(); p.openGoal(); p.pressEnter();
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
    p.typeAndEnter('blocker'); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).obstacles[0].text, 'blocker');
  },
  async 'the pick box shows on a placed solution, ticked for a star'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], true)])]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.equal(p.el('pick-control').hidden, false);
    assert.equal(p.el('pick-box').checked, true);
    p.clickItem('o1');
    assert.equal(p.el('pick-control').hidden, true);
  },
  async 'a tray solution shows Delete, and no pick box or plus until it is attached'() {
    const html = treeHtml([node('o1', 'ob')], [sol('s1', 'tray')]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.equal(p.isSelected('s1'), true);
    assert.equal(p.el('pick-control').hidden, true);
    assert.deepEqual(p.pluses(), []);
    assert.equal(p.el('delete-item').hidden, false);
  },
  async 'delete with a pick asks, and keep changes nothing'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'the picked fix', [], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item'); await settle();
    assert.equal(p.el('delete-question').hidden, false);
    const said = p.el('delete-question').textContent;
    assert.ok(said.includes('Delete this? It would also remove: '), said);
    assert.ok(said.includes('the picked fix'), said);
    assert.ok(!said.includes('These key actions'), said);
    assert.equal(p.el('delete-item').hidden, true); assert.equal(p.el('delete-yes').textContent, 'Delete');
    assert.equal(p.el('delete-keep').textContent, 'Keep');
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(p.active(), p.el('delete-keep'));
    p.tool('delete-keep'); await settle();
    assert.equal(p.el('delete-question').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(f.writes, 0); assert.equal(p.isSelected('o1'), true);
    assert.equal(p.active(), p.el('delete-item'));
    assert.ok(findIn(parse(f.html).obstacles, 's1'));
    assert.ok(p.canvasText().includes('the picked fix'));
  },
  async 'delete with a plan row asks, and yes removes the row but keeps the key action'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix it'), sol('s2', 'other fix')])], [], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1', 's2'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' },
        { solution_id: 's2', first_move: 'the other move', owner: 'o', others_decide: '' }]
    });
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('s1'); p.tool('delete-item'); await settle();
    const said = p.el('delete-question').textContent;
    assert.ok(said.includes('the first move'), said);
    assert.ok(said.includes('These key actions would lose a solution: '), said);
    assert.ok(said.includes('the action'), said);
    assert.equal(f.writes, 0);
    p.tool('delete-yes'); await settle();
    const saved = parse(f.html);
    assert.equal(findIn(saved.obstacles, 's1'), null);
    assert.deepEqual(saved.execute.map((e) => e.solution_id), ['s2']);
    assert.equal(saved.key_actions.length, 1); assert.deepEqual(saved.key_actions[0].solution_ids, ['s2']);
    assert.equal(p.el('delete-question').hidden, true); assert.equal(p.active(), p.box('goal'));
  },
  async 'delete with nothing at stake deletes straight away, including sub-items'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [node('o3', 'grandkid')])]), node('o4', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item'); await settle();
    assert.equal(p.el('delete-question').hidden, true);
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o4']);
    assert.equal(f.writes, 1);
  },
  async 'escape closes the question and changes nothing, and focus returns to Delete'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    p.fire(p.el('delete-keep'), 'keydown', { key: 'Escape' });
    assert.equal(p.el('delete-question').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.el('delete-item'));
    assert.equal(f.writes, 0);
  },
  async 'selecting another item or clicking empty space closes the question and deletes nothing'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    p.clickItem('o2');
    assert.equal(p.el('delete-question').hidden, true);
    p.clickItem('o1'); assert.equal(p.el('delete-question').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    p.tool('delete-item'); p.clickEmpty();
    assert.equal(p.el('delete-question').hidden, true); assert.equal(p.el('item-tools').hidden, true);
    assert.equal(f.writes, 0); assert.ok(findIn(parse(f.html).obstacles, 's1'));
  },
  async 'tab reaches the question buttons, and a render keeps the question showing'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]);
    const p = page({ html }); await settle();
    const tab = (target, shiftKey) => p.fire(target, 'keydown', { key: 'Tab', shiftKey });
    p.clickItem('o1'); p.tool('delete-item');
    p.resize();
    assert.equal(p.el('delete-question').hidden, false); assert.equal(p.active(), p.el('delete-keep'));
    assert.ok(tab(p.el('delete-keep')).prevented); assert.equal(p.active(), p.box('s1'));
    p.el('delete-yes').focus();
    assert.ok(!tab(p.el('delete-yes')).prevented);
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: 'Tab' });
    assert.equal(p.active(), p.el('plus-obstacle'));
  },
  async 'move to moves an obstacle with what is under it and renumbers'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'second', [node('o3', 'kid')]), node('o4', 'third')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o2');
    const choices = p.el('move-to').walk().filter((k) => k.tag === 'OPTION' && k.value).map((k) => k.value);
    assert.deepEqual(choices, ['o1', 'o4']);
    assert.ok(p.el('move-to').walk().some((k) => k.tag === 'OPTION' && k.textContent.includes('third')));
    p.el('move-to').focus();
    p.el('move-to').value = 'o4'; p.fire(p.el('move-to'), 'change'); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1', 'o4']);
    assert.deepEqual(saved.obstacles[1].children.map((o) => o.id), ['o2']);
    assert.equal(saved.obstacles[1].children[0].children[0].id, 'o3');
    assert.ok(p.canvasText().includes('2A'), p.canvasText());
    assert.equal(p.isSelected('o2'), true); assert.equal(p.el('item-tools').hidden, false);
    assert.equal(p.active(), p.el('move-to'));
  },
  async 'move to lists the goal for a sub-obstacle and hides when there is nowhere to go'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const p = page({ html }); await settle();
    p.clickItem('o2');
    assert.equal(p.el('move-control').hidden, false);
    assert.deepEqual(p.el('move-to').walk().filter((k) => k.tag === 'OPTION' && k.value).map((k) => k.value), ['goal']);
    p.clickItem('o1');
    assert.equal(p.el('move-control').hidden, true); assert.equal(p.el('move-to').hidden, true);
  },
  async 'a tray solution attaches through move to and leaves the tray'() {
    const html = treeHtml([node('o1', 'first')], [sol('s1', 'loose fix')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('s1');
    assert.deepEqual(p.el('move-to').walk().filter((k) => k.tag === 'OPTION' && k.value).map((k) => k.value), ['o1']);
    p.el('move-to').value = 'o1'; p.fire(p.el('move-to'), 'change'); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.unplaced, []); assert.equal(saved.obstacles[0].children[0].id, 's1');
    assert.equal(p.trayText(), ''); assert.equal(p.isSelected('s1'), true);
    assert.ok(p.canvasText().includes('loose fix'));
  },
  async 'a tray solution offers no pick box or plus'() {
    const html = treeHtml([node('o1', 'first')], [sol('s1', 'loose fix')]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.equal(p.el('pick-control').hidden, true); assert.equal(p.el('pick-box').hidden, true);
    assert.deepEqual(p.pluses(), []);
    assert.equal(p.el('move-control').hidden, false); assert.equal(p.el('delete-item').hidden, false);
  },
  async 'the tray says the solution is not on the map yet'() {
    const one = page({ html: treeHtml([node('o1', 'first')], [sol('s1', 'a')]) }); await settle();
    assert.equal(one.trayText().includes('1 solution is not on the map yet.'), true, one.trayText());
    const two = page({ html: treeHtml([node('o1', 'first')], [sol('s1', 'a'), sol('s2', 'b')]) }); await settle();
    assert.equal(two.trayText().includes('2 solutions are not on the map yet.'), true, two.trayText());
    assert.ok(!two.trayText().includes('tied'));
  },
  async 'star key shows only with stars'() {
    const none = page({ html: treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], false)])]) }); await settle();
    assert.equal(none.sandbox.document.getElementById('picks-key').hidden, true);
    const some = page({ html: treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], true)])]) }); await settle();
    assert.equal(some.sandbox.document.getElementById('picks-key').hidden, false);
  },
  async 'the pick box changes the star and the key'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    const key = p.sandbox.document.getElementById('picks-key');
    assert.equal(key.hidden, true);
    p.clickItem('s1');
    const box = p.el('pick-box');
    assert.equal(box.checked, false);
    box.checked = true; box.focus(); p.fire(box, 'change'); await settle();
    assert.equal(f.writes, 1);
    assert.equal(findIn(parse(f.html).obstacles, 's1').star, true);
    assert.equal(key.hidden, false);
    assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('s1'), true);
    assert.equal(p.active(), box);
    box.checked = false; p.fire(box, 'change'); await settle();
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
    p.typeAndEnter('blocker'); await settle();
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
    p.typeAndEnter(''); await settle();
    assert.equal(parse(f.html).goal.text, 'two'); assert.deepEqual(parse(f.html).obstacles, []);
    assert.equal(p.status(), 'All changes saved');
  },
  // Obstacles are a labeled tree.
  async 'add a sub-obstacle and see its label, and the file gets the child'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    p.typeAndEnter('why one'); await settle();
    assert.ok(p.canvasText().includes('1A'), p.canvasText());
    assert.ok(p.canvasText().includes('why one'));
    const saved = parse(f.html).obstacles[0];
    assert.equal(saved.children.length, 1); assert.equal(saved.children[0].text, 'why one');
    assert.deepEqual(Object.keys(saved.children[0]).sort(), ['children', 'id', 'kind', 'root_cause', 'star', 'text']);
    assert.ok(!JSON.stringify(parse(f.html).obstacles).includes('1A'));
    p.clickItem(saved.children[0].id); p.plus('obstacle'); await settle();
    p.typeAndEnter('deeper'); await settle();
    assert.ok(p.canvasText().includes('1A1'), p.canvasText());
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a new obstacle and a new sub-obstacle get ids nothing else in the file uses'() {
    const html = treeHtml([node('o1', 'first', [node('o7', 'kid')])], [], { baseline: { obstacles: [{ id: 'o9' }] } });
    const p = page({ html }); await settle();
    p.clickItem('o7'); p.plus('obstacle'); p.typeAndEnter('deep');
    p.addObstacle(); p.typeAndEnter('top');
    const canvas = p.sandbox.document.getElementById('canvas').kids.map((k) => k.dataset.ref).filter(Boolean).map(JSON.parse);
    const ids = canvas.filter((r) => r.kind === 'obstacle').map((r) => r.id);
    assert.deepEqual(ids.slice().sort(), ['o1', 'o10', 'o11', 'o7']);
  },
  async 'a blank new sub-item stays out of the file until it has text'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o2'); p.plus('obstacle'); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(parse(f.html).obstacles[0].children[0].children.length, 0);
    p.typeAndEnter('now it has text'); await settle();
    assert.equal(f.writes, 1); assert.equal(parse(f.html).obstacles[0].children[0].children[0].text, 'now it has text');
  },
  async 'a blank new sub-item closed empty leaves no trace in the file or on the page'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    assert.ok(p.canvasText().includes('1A'));
    p.typeAndEnter(''); await settle();
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
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    f.gate = null; release(); await settle();
    assert.deepEqual(parse(f.html).obstacles[0].children, []); assert.equal(parse(f.html).goal.text, 'one');
    p.typeAndEnter('kid'); await settle();
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
    p.clickItem('o2'); assert.equal(p.el('delete-item').textContent, 'Delete this and its 2 sub-items');
    p.tool('delete-item'); await settle();
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
    p.clickItem('s1'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
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
    p.clickItem('s1'); p.plus('obstacle'); await settle();
    p.typeAndEnter('in the way'); await settle();
    assert.ok(p.canvasText().includes('1B1'), p.canvasText());
    assert.ok(p.canvasText().includes('1B2'), p.canvasText());
    const under = findIn(parse(f.html).obstacles, 's1').children[0];
    assert.equal(under.text, 'in the way'); assert.equal(under.kind, 'obstacle');
  },
  async 'a blank new solution stays out of the file, and closing it empty leaves no trace'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('solution'); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndEnter(''); await settle();
    assert.equal(f.writes, 0); assert.equal(p.warnsOnClose(), false);
    assert.deepEqual(parse(f.html).obstacles[0].children, []);
  },
  async 'the delete control counts everything that goes with the item'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'a', [node('o3', 'b')]), node('o4', 'c')])]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    assert.equal(p.el('delete-item').textContent, 'Delete this and its 3 sub-items');
    p.clickItem('o4');
    assert.equal(p.el('delete-item').textContent, 'Delete');
  },
  async 'a root cause can be marked and unmarked, and offers only a solution'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1');
    assert.equal(p.el('root-toggle').hidden, true);
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    p.clickItem('o2');
    assert.equal(p.el('root-toggle').textContent, 'Mark as root cause');
    p.tool('root-toggle'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].root_cause, true);
    assert.equal(p.isSelected('o2'), true);
    assert.deepEqual(p.pluses(), ['solution']);
    assert.equal(p.el('root-toggle').textContent, 'Unmark root cause');
    p.tool('root-toggle'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].root_cause, false);
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
  },
  async 'an obstacle with only a solution under it can still be a root cause'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix', [node('o2', 'in the way')])])]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    assert.equal(p.el('root-toggle').hidden, false);
    p.clickItem('o2');
    assert.equal(p.el('root-toggle').hidden, false);
  },

  // Selecting, pressing a plus and typing in place.
  async 'a click selects and writes nothing'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    let reads = 0; const getFile = f.getFile; f.getFile = async () => { reads++; return getFile(); };
    p.clickItem('o2'); await settle();
    assert.equal(p.isSelected('o2'), true);
    assert.equal(p.el('typing').hidden, true);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under 1A');
    assert.equal(p.el('plus-solution').getAttribute('aria-label'), 'Add a solution under 1A');
    assert.equal(p.el('item-tools').hidden, false);
    p.clickItem('o1'); await settle();
    assert.equal(p.isSelected('o2'), false); assert.equal(p.isSelected('o1'), true);
    p.clickEmpty(); await settle();
    assert.equal(p.isSelected('o1'), false);
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    assert.equal(f.writes, 0); assert.equal(reads, 0); assert.equal(p.status(), 'All changes saved');
  },
  async 'selecting while a write was refused does not try the write again'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    f.failWrite = true; p.edit('x'); await settle(); f.failWrite = false;
    let reads = 0; const getFile = f.getFile; f.getFile = async () => { reads++; return getFile(); };
    p.clickItem('o1'); p.clickItem('goal'); p.clickEmpty(); await settle();
    assert.equal(reads, 0); assert.equal(p.status(), 'Not saved');
  },
  async 'plus adds an obstacle, typing fills it, and only then the file changes'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    const text = p.el('typing');
    assert.equal(text.hidden, false); assert.equal(text.value, ''); assert.equal(p.active(), text);
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    p.typeAndEnter('  why one  '); await settle();
    assert.equal(f.writes, 1);
    const child = parse(f.html).obstacles[0].children[0];
    assert.equal(child.text, 'why one'); assert.equal(child.kind, 'obstacle');
    assert.equal(text.hidden, true);
    assert.equal(p.isSelected(child.id), true); assert.equal(p.isSelected('o1'), false);
    assert.equal(p.active(), p.box(child.id));
  },
  async 'plus adds a solution under an obstacle, and the goal plus adds at the top'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('solution'); p.typeAndEnter('the fix'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].kind, 'solution');
    p.clickItem('goal'); p.plus('obstacle'); p.typeAndEnter('second'); await settle();
    assert.equal(parse(f.html).obstacles[1].text, 'second');
  },
  async 'a blank new item is removed when something else is selected, with no write'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    assert.ok(p.canvasText().includes('1A'));
    p.clickItem('o2'); await settle();
    assert.ok(!p.canvasText().includes('1A'));
    assert.equal(p.isSelected('o2'), true); assert.equal(p.el('typing').hidden, true);
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
    assert.deepEqual(parse(f.html).obstacles[0].children, []);
  },
  async 'selecting something else keeps text typed on a new item'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle');
    p.el('typing').value = 'kept';
    p.clickItem('o2'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].text, 'kept');
    assert.equal(p.isSelected('o2'), true);
  },
  async 'clicking empty space with a blank new item removes it and clears the selection'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle');
    p.clickEmpty(); await settle();
    assert.ok(!p.canvasText().includes('1A')); assert.equal(p.isSelected('o1'), false);
    assert.equal(f.writes, 0);
  },
  async 'escape on a new item removes it, with no write'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle');
    p.el('typing').value = 'typed then dropped';
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.ok(!p.canvasText().includes('1A')); assert.ok(!p.canvasText().includes('typed then dropped'));
    assert.equal(p.el('typing').hidden, true);
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.box('o1'));
  },
  async 'escape on an existing item keeps its old text'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1');
    assert.equal(p.el('typing').value, 'first');
    p.el('typing').value = 'changed';
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(f.writes, 0); assert.ok(p.canvasText().includes('first'));
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.box('o1'));
  },
  async 'a double-click types on an item, and clicking away keeps the text'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1');
    assert.equal(p.active(), p.el('typing'));
    p.el('typing').value = 'better';
    p.clickItem('o2'); await settle();
    assert.equal(parse(f.html).obstacles[0].text, 'better');
    assert.equal(p.isSelected('o2'), true);
  },
  async 'clearing an existing item keeps its old text'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1'); p.typeAndEnter('   '); await settle();
    assert.equal(f.writes, 0); assert.ok(p.canvasText().includes('first'));
  },
  async 'shift and enter adds a line instead of finishing'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.typeOn('o1');
    const e = p.fire(p.el('typing'), 'keydown', { key: 'Enter', shiftKey: true });
    assert.equal(p.el('typing').hidden, false); assert.ok(!e.prevented);
  },
  async 'a resize while typing keeps the text and focus'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1');
    const text = p.el('typing'); text.value = 'half typed';
    p.resize(); await settle();
    assert.equal(text.hidden, false); assert.equal(text.value, 'half typed'); assert.equal(p.active(), text);
    assert.equal(f.writes, 0);
    p.clickItem('goal'); p.plus('obstacle'); text.value = 'half new';
    p.resize(); await settle();
    assert.equal(text.value, 'half new'); assert.equal(p.active(), text); assert.equal(f.writes, 1);
  },
  async 'enter on the box of a blank new item goes back to typing, and nothing reaches the file'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.addObstacle(); await settle();
    p.box('o2').focus();
    const e = p.fire(p.box('o2'), 'keydown', { key: 'Enter' }); await settle();
    assert.ok(e.prevented); assert.equal(p.active(), p.el('typing'));
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    p.resize(); await settle();
    assert.equal(f.writes, 0); assert.deepEqual(parse(f.html).obstacles.map((o) => o.id), ['o1']);
    assert.ok(!p.canvasText().includes('New obstacle'));
  },
  async 'enter on the box of a new item keeps what was typed'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.addObstacle(); p.el('typing').value = 'typed words';
    p.fire(p.box('o2'), 'keydown', { key: 'Enter' }); await settle();
    assert.equal(p.el('typing').value, 'typed words'); assert.equal(p.active(), p.el('typing'));
    assert.equal(f.writes, 0);
  },
  async 'enter on the box of an existing item keeps what was typed'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.typeOn('o1'); p.el('typing').value = 'half typed';
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: 'Enter' }); await settle();
    assert.equal(p.el('typing').value, 'half typed'); assert.equal(p.active(), p.el('typing'));
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: ' ' }); await settle();
    assert.equal(p.el('typing').value, 'half typed'); assert.equal(p.active(), p.el('typing'));
  },
  async 'starting to type on another item finishes the open text box first'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1'); p.el('typing').value = 'kept';
    p.fire(p.box('o2'), 'dblclick'); await settle();
    assert.equal(parse(f.html).obstacles[0].text, 'kept');
    assert.equal(p.el('typing').value, 'other'); assert.equal(p.isSelected('o2'), true);
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    const writes = f.writes;
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    p.fire(p.box('o2'), 'dblclick'); await settle();
    assert.equal(f.writes, writes); assert.equal(p.el('typing').value, 'other');
    assert.ok(!p.canvasText().includes('1A'));
  },
  async 'adding while a blank new item is open removes it, and neither blank reaches the file'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.addObstacle(); await settle();
    p.el('add-obstacle').listeners.click[0](); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndEnter('second'); await settle();
    assert.deepEqual(parse(f.html).obstacles.map((o) => o.text), ['first', 'second']);
  },
  async 'escape cancels typing even after focus left the text box'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1'); p.el('typing').value = 'changed';
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(p.el('typing').hidden, true); assert.equal(f.writes, 0);
    assert.ok(p.canvasText().includes('first')); assert.equal(p.isSelected('o1'), true);
  },
  async 'escape on an item from the header add returns focus to that button'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.addObstacle();
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' });
    assert.equal(p.active(), p.el('add-obstacle'));
    p.addObstacle(); p.pressEnter();
    assert.equal(p.active(), p.el('add-obstacle'));
  },
  async 'root cause shows only the green plus'() {
    const html = treeHtml([node('o1', 'first', [], true)]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    assert.deepEqual(p.pluses(), ['solution']);
  },
  async 'solution shows only the orange plus'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'the fix')])]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.deepEqual(p.pluses(), ['obstacle']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the fix');
  },
  async 'the goal shows only the orange plus and no toolbar'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('goal');
    assert.deepEqual(p.pluses(), ['obstacle']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the goal');
    assert.equal(p.el('item-tools').hidden, true);
  },
  async 'selection returns focus after a render'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    const before = p.box('o1');
    assert.equal(p.active(), before);
    p.resize();
    assert.notEqual(p.box('o1'), before);
    assert.equal(p.active(), p.box('o1')); assert.equal(p.isSelected('o1'), true);
  },
  async 'a render leaves focus on a header button'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    const zoom = p.el('zoom-in'); zoom.focus();
    p.fire(zoom, 'click');
    assert.equal(p.active(), zoom); assert.equal(p.isSelected('o1'), true);
  },
  async 'the keyboard selects, types and clears'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    const enter = p.fire(p.box('o1'), 'keydown', { key: 'Enter' });
    assert.ok(enter.prevented); assert.equal(p.isSelected('o1'), true); assert.equal(p.el('typing').hidden, true);
    p.fire(p.box('o1'), 'keydown', { key: 'Enter' });
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    p.typeAndEnter('new words'); await settle();
    assert.equal(parse(f.html).obstacles[0].text, 'new words');
    assert.equal(p.el('typing').hidden, true); assert.equal(p.active(), p.box('o1'));
    p.fire(p.box('o1'), 'keydown', { key: 'Escape' });
    assert.equal(p.isSelected('o1'), false); assert.equal(p.active(), p.box('o1'));
    p.fire(p.box('o1'), 'keydown', { key: ' ' });
    assert.equal(p.isSelected('o1'), true); assert.equal(p.el('typing').hidden, true);
  },
  async 'tab goes from the selected item through its controls to the next item'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    const tab = (target, shiftKey) => p.fire(target, 'keydown', { key: 'Tab', shiftKey });
    assert.ok(tab(p.box('o1')).prevented); assert.equal(p.active(), p.el('plus-obstacle'));
    assert.ok(!tab(p.el('plus-obstacle')).prevented);
    assert.ok(tab(p.el('plus-obstacle'), true).prevented); assert.equal(p.active(), p.box('o1'));
    p.el('delete-item').focus();
    assert.ok(tab(p.el('delete-item')).prevented); assert.equal(p.active(), p.box('o2'));
  },
  async 'the selected item stays in the same place on screen after a render'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')]), node('o3', 'other')]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    const top = p.box('o1').getBoundingClientRect().top;
    const y = parseFloat(p.box('o1').style.top);
    p.plus('obstacle');
    assert.notEqual(parseFloat(p.box('o1').style.top), y);
    assert.equal(p.box('o1').getBoundingClientRect().top, top);
  },
  async 'controls follow the item, and hide when it scrolls out of the map'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('o1');
    const plus = p.el('plus-obstacle');
    assert.notEqual(plus.style.visibility, 'hidden');
    const left = parseFloat(plus.style.left);
    p.el('map').scrollLeft = 50;
    p.el('map').listeners.scroll.forEach((f) => f());
    assert.equal(parseFloat(plus.style.left), left - 50);
    p.el('map').scrollLeft = 5000;
    p.el('map').listeners.scroll.forEach((f) => f());
    assert.equal(plus.style.visibility, 'hidden'); assert.equal(p.el('item-tools').style.visibility, 'hidden');
  },
  async 'deleting from the toolbar clears the selection and puts focus on the goal'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item'); await settle();
    assert.deepEqual(parse(f.html).obstacles, []);
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    assert.equal(p.active(), p.box('goal'));
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
    assert.equal(p.el('typing').value, '80% in-office attendance by end of Q2, up from 40%');
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
