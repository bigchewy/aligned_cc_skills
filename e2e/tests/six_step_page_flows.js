// Runs the real page code from a map page against a stub DOM and fake file handles.
// Usage: node six_step_page_flows.js <path to a map page>. Exits 1 if any flow fails.
// test_six_step_page_flows.py runs it against the template and the example map.
const fs = require('fs');
const assert = require('assert');
const { tick, settle, makePage } = require('./six_step_page_stub.js');

const HTML = fs.readFileSync(process.argv[2], 'utf8');
const SLOT = /(<script id="map-data" type="application\/json">)([\s\S]*?)(<\/script>)/;

function mapHtml(rev, goal, id) {
  const data = { map_id: id || 'm1', revision: rev, person: 'Pat', goal: { text: goal || 'g' },
    obstacles: [], key_actions: [], execute: [], feedback: { number: '', check_on: '', redraw_if: '' }, baseline: {} };
  return HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
}
const parse = (html) => JSON.parse(SLOT.exec(html)[2]);
const node = (id, text, children) => ({ id, kind: 'obstacle', text, star: false, children: children || [] });
const sol = (id, text, children, star) => ({ id, kind: 'solution', text, star: Boolean(star), children: children || [] });
function treeHtml(obstacles, more) {
  const data = Object.assign(parse(mapHtml(1)), { obstacles }, more || {});
  return HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);
}
function findIn(items, id) {
  for (const it of items) { if (it.id === id) return it; const hit = findIn(it.children, id); if (hit) return hit; }
  return null;
}
const withData = (html, data) => html.replace(SLOT, (w, a, b, c) => a + JSON.stringify(data) + c);

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

const page = makePage(HTML, () => mapHtml(1, 'g'));

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
  async 'a save writes a whole page: every script, the doctype and the map data'() {
    // A browser rebuilds the document with html, head and body tags around the template.
    const wrapped = '<html lang="en"><head>' + mapHtml(1) + '</head><body></body></html>';
    for (const html of [undefined, wrapped]) {
      const f = fakeHandle(mapHtml(1));
      const p = page({ picker: f, html }); await settle();
      p.edit('saved'); p.clickSave(); await settle();
      assert.equal(f.writes, 1);
      assert.ok(f.html.startsWith('<!doctype html>') || f.html.startsWith('<!DOCTYPE html>'), 'doctype kept');
      for (const id of ['map-data', 'map-logic', 'map-store', 'map-page']) {
        assert.ok(f.html.includes('<script id="' + id + '"'), id + ' kept');
      }
      assert.ok(f.html.includes("document.documentElement.lang = 'en'"), 'language line kept');
      assert.ok(f.html.includes("document.title = 'Mind map'"), 'title line kept');
      assert.equal(parse(f.html).goal.text, 'saved');
    }
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
  async 'the star button shows on a placed solution, pressed for a star'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol', [], true)])]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.equal(p.el('star-button').hidden, false);
    assert.equal(p.el('star-button').getAttribute('aria-pressed'), 'true');
    assert.equal(p.el('star-button').getAttribute('aria-label'), 'Star');
    assert.equal(p.el('star-button').textContent, '');
    p.clickItem('o1');
    assert.equal(p.el('star-button').hidden, true);
  },
  async 'the trash can asks every time, with nothing written until Delete'() {
    const html = treeHtml([node('o1', 'plain', []), node('o2', 'first', [sol('s1', 'picked', [], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    for (const id of ['o1', 'o2']) {
      p.clickItem(id); assert.equal(p.el('delete-card').hidden, true, id);
      p.tool('delete-item'); await settle();
      assert.equal(p.el('delete-card').hidden, false, id);
      assert.equal(f.writes, 0, id); assert.equal(p.status(), 'All changes saved');
      assert.ok(findIn(parse(f.html).obstacles, id));
    }
  },
  async 'the card says Confirm Delete and has one Delete button, with no list of effects'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'the picked fix', [], true)])], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' }]
    });
    const p = page({ html }); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    const card = p.el('delete-card');
    assert.equal(p.el('delete-title').textContent, 'Confirm Delete');
    assert.equal(p.el('delete-yes').textContent, 'Delete');
    assert.ok(p.el('delete-yes').getAttribute('aria-label').startsWith('Delete'));
    assert.ok(p.el('delete-yes').getAttribute('aria-label').includes('first'));
    assert.ok(card.getAttribute('aria-label').includes('first'));
    assert.equal(p.active(), p.el('delete-yes'));
    assert.equal(p.el('delete-item').hidden, false, 'the toolbar keeps its size, so the map does not jump');
    assert.equal(p.el('item-tools').classList.contains('asking'), false);
  },
  async 'Delete deletes the item and everything under it, and sends one change'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [node('o3', 'grandkid')]), sol('s1', 'picked', [], true)]), node('o4', 'other')], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' }]
    });
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item'); await settle();
    assert.equal(f.writes, 0);
    p.tool('delete-yes'); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o4']);
    assert.deepEqual(saved.execute, []);
    assert.equal(saved.key_actions.length, 1); assert.deepEqual(saved.key_actions[0].solution_ids, []);
    assert.equal(f.writes, 1);
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.active(), p.box('goal'));
  },
  async 'Escape cancels, writes nothing, and puts focus back on the trash can'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    p.fire(p.el('delete-yes'), 'keydown', { key: 'Escape' });
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.el('delete-item'));
    assert.equal(f.writes, 0);
  },
  async 'clicking elsewhere cancels and writes nothing'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    p.clickItem('o2');
    assert.equal(p.el('delete-card').hidden, true);
    p.clickItem('o1'); assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    p.tool('delete-item'); p.clickEmpty();
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('item-tools').hidden, true);
    p.clickItem('o1'); p.tool('delete-item'); p.fire(p.el('zoom-in'), 'click');
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('item-tools').hidden, false);
    p.tool('delete-item'); p.fire(p.el('delete-card'), 'click');
    assert.equal(p.el('delete-card').hidden, false, 'a click on the card itself keeps it open');
    assert.equal(f.writes, 0); assert.ok(findIn(parse(f.html).obstacles, 's1'));
  },
  async 'Enter on the focused Delete button is left to the button, and Delete then deletes'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    assert.equal(p.active(), p.el('delete-yes'));
    assert.ok(!p.fire(p.el('delete-yes'), 'keydown', { key: 'Enter' }).prevented, 'the page must not swallow Enter');
    assert.equal(f.writes, 0);
    p.fire(p.el('delete-yes'), 'click'); await settle();
    assert.deepEqual(parse(f.html).obstacles.map((o) => o.id), ['o2']); assert.equal(f.writes, 1);
  },
  async 'Tab and Shift+Tab stay on the Delete button while the card is open'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]);
    const p = page({ html }); await settle();
    const tab = (target, shiftKey) => p.fire(target, 'keydown', { key: 'Tab', shiftKey });
    p.clickItem('o1'); p.tool('delete-item');
    p.resize();
    assert.equal(p.el('delete-card').hidden, false); assert.equal(p.active(), p.el('delete-yes'));
    assert.ok(tab(p.el('delete-yes')).prevented); assert.equal(p.active(), p.el('delete-yes'));
    assert.ok(tab(p.el('delete-yes'), true).prevented); assert.equal(p.active(), p.el('delete-yes'));
    p.box('o1').focus();
    assert.ok(tab(p.box('o1')).prevented); assert.equal(p.active(), p.el('delete-yes'));
  },
  async 'the card sits by the trash can and stays inside the window'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    const card = p.el('delete-card');
    const left = parseFloat(card.style.left), top = parseFloat(card.style.top);
    assert.ok(left >= 12 && left <= p.sandbox.innerWidth - card.offsetWidth - 12, String(left));
    assert.ok(top >= 12 && top <= p.sandbox.innerHeight - card.offsetHeight - 12, String(top));
    p.el('map').scrollLeft = 5000;
    p.el('map').listeners.scroll.forEach((f) => f());
    assert.equal(card.style.visibility, 'hidden');
  },
  async 'a plus pressed while the card shows closes it and opens the new item, with no write'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    p.plus('obstacle'); await settle();
    assert.equal(p.el('delete-card').hidden, true);
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    assert.equal(f.writes, 0); assert.ok(findIn(parse(f.html).obstacles, 's1'));
  },
  async 'the star button changes the star, keeps focus, and has no key in the header'() {
    const html = treeHtml([node('o1', 'ob', [sol('s1', 'sol')])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    assert.ok(!p.sandbox.document.documentElement.outerHTML.includes('My picks'));
    p.clickItem('s1');
    const star = p.el('star-button');
    assert.equal(star.getAttribute('aria-pressed'), 'false');
    star.focus(); p.fire(star, 'click'); await settle();
    assert.equal(f.writes, 1);
    assert.equal(findIn(parse(f.html).obstacles, 's1').star, true);
    assert.equal(star.getAttribute('aria-pressed'), 'true');
    assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('s1'), true); assert.equal(p.active(), star);
    p.fire(star, 'click'); await settle();
    assert.equal(findIn(parse(f.html).obstacles, 's1').star, false);
    assert.equal(star.getAttribute('aria-pressed'), 'false');
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
    assert.deepEqual(Object.keys(saved.children[0]).sort(), ['children', 'id', 'kind', 'star', 'text']);
    assert.ok(!JSON.stringify(parse(f.html).obstacles).includes('1A'));
    p.clickItem(saved.children[0].id); p.plus('obstacle'); await settle();
    p.typeAndEnter('deeper'); await settle();
    assert.ok(p.canvasText().includes('1A1'), p.canvasText());
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a new obstacle and a new sub-obstacle get ids nothing else in the file uses'() {
    const html = treeHtml([node('o1', 'first', [node('o7', 'kid')])], { baseline: { obstacles: [{ id: 'o9' }] } });
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
    p.clickItem('o2');
    p.tool('delete-item'); p.tool('delete-yes'); await settle();
    const saved = parse(f.html);
    assert.equal(findIn(saved.obstacles, 'o2'), null); assert.equal(findIn(saved.obstacles, 's1'), null);
    assert.ok(findIn(saved.obstacles, 's2'));
    assert.ok(p.canvasText().includes('1A'), p.canvasText()); assert.ok(p.canvasText().includes('kid b'));
    assert.ok(!p.canvasText().includes('1B'));
  },
  async 'delete an item and see its plan row go, while the key action stays'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix it'), sol('s2', 'other fix')])], {
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
  async 'the delete control is an icon with no visible words'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'a', [node('o3', 'b')]), node('o4', 'c')])]);
    const p = page({ html }); await settle();
    for (const id of ['o1', 'o4']) {
      p.clickItem(id);
      assert.equal(p.el('delete-item').textContent, '');
      assert.equal(p.el('delete-item').getAttribute('aria-label'), 'Delete');
      assert.equal(p.el('delete-item').title, 'Delete');
    }
  },

  // Dragging an item onto a box.
  async 'a small press is a click and selects'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.press('o1');
    p.pointerTo('o2', 103, 103);
    assert.equal(p.ghost().hidden, true); assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release();
    p.fire(p.box('o1'), 'click', { detail: 1 }); await settle();
    assert.equal(p.isSelected('o1'), true); assert.equal(f.writes, 0);
    assert.deepEqual(parse(f.html).obstacles.map((o) => o.id), ['o1', 'o2']);
    p.press('o1'); p.release();
    p.fire(p.box('o1'), 'click', { detail: 2 }); p.fire(p.box('o1'), 'dblclick');
    assert.equal(p.el('typing').hidden, false); assert.equal(p.el('typing').value, 'first');
  },
  async 'dragging onto a box makes it a sub and renumbers'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'second', [node('o3', 'kid')]), node('o4', 'third')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.press('o2');
    p.pointerTo('o4', 300, 320);
    assert.equal(p.ghost().hidden, false); assert.equal(p.ghost().textContent, 'second');
    assert.ok(parseFloat(p.ghost().style.left) >= 300); assert.ok(parseFloat(p.ghost().style.top) >= 320);
    assert.equal(p.box('o2').classList.contains('drag-source'), true);
    assert.equal(p.box('o4').classList.contains('drop-target'), true);
    assert.equal(p.el('canvas').contains(p.ghost()), false);
    p.pointerTo('o1', 300, 200);
    assert.equal(p.box('o4').classList.contains('drop-target'), false);
    assert.equal(p.box('o1').classList.contains('drop-target'), true);
    p.pointerTo('o4');
    p.release(); p.clickAfter(); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1', 'o4']);
    assert.deepEqual(saved.obstacles[1].children.map((o) => o.id), ['o2']);
    assert.equal(saved.obstacles[1].children[0].children[0].id, 'o3');
    assert.ok(p.canvasText().includes('2A'), p.canvasText());
    assert.equal(p.ghost().hidden, true);
    assert.equal(p.sandbox.document.body.classList.contains('dragging'), false);
    assert.equal(p.box('o2').classList.contains('drag-source'), false);
    assert.equal(p.box('o4').classList.contains('drop-target'), false);
  },
  async 'a drop writes once and keeps the item selected'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid')]), node('o3', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o3');
    p.dragOnto('o2', 'o3'); await settle();
    assert.equal(f.writes, 1);
    assert.equal(p.isSelected('o2'), true); assert.equal(p.isSelected('o3'), false);
    assert.equal(p.active(), p.box('o2'));
    assert.equal(p.el('item-tools').hidden, false); assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a drop holds the box it landed on still on screen'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'second'), node('o3', 'third', [node('o4', 'a'), node('o5', 'b'), node('o6', 'c')])]);
    const p = page({ html }); await settle();
    p.press('o1'); p.pointerTo('o2');
    const top = p.box('o2').getBoundingClientRect().top;
    p.release(); p.clickAfter();
    assert.equal(p.box('o2').getBoundingClientRect().top, top);
  },
  async 'an item drags onto the goal, and a solution keeps its star and what is under it'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix', [node('o2', 'kid')], true)])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.dragOnto('s1', 'goal'); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1', 's1']);
    assert.equal(saved.obstacles[1].star, true); assert.equal(saved.obstacles[1].children[0].id, 'o2');
    assert.equal(p.isSelected('s1'), true);
  },
  async 'dragging onto the item\'s own parent or a descendant changes nothing'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [node('o3', 'grandkid')])])]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    for (const target of ['o1', 'o3', 'o2']) {
      p.press('o2'); p.pointerTo(target);
      assert.equal(p.ghost().hidden, false);
      assert.equal(p.box(target).classList.contains('drop-target'), false, target);
      p.release(); p.clickAfter(); await settle();
      assert.equal(p.ghost().hidden, true);
    }
    p.press('o1'); p.pointerTo('goal');
    assert.equal(p.box('goal').classList.contains('drop-target'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(f.writes, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(findIn(parse(f.html).obstacles, 'o1').children[0].children[0].id, 'o3');
  },
  async 'escape cancels a drag with no write'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o3');
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.el('item-tools').hidden, true); assert.deepEqual(p.pluses(), []);
    const enter = p.fire(p.box('o1'), 'keydown', { key: 'Enter' });
    assert.ok(enter.prevented); assert.equal(p.el('typing').hidden, true);
    p.fire(p.box('o1'), 'keydown', { key: 'Escape' });
    assert.equal(p.ghost().hidden, true); assert.equal(p.box('o1').classList.contains('drag-source'), false);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    assert.equal(p.isSelected('o3'), true); assert.equal(p.el('item-tools').hidden, false);
    // The button is still down. Moving on and letting go does nothing, and neither does its click.
    p.pointerTo('o2'); assert.equal(p.ghost().hidden, true);
    p.release(); p.clickAfter(); await settle();
    assert.equal(f.writes, 0); assert.equal(p.isSelected('o3'), true);
    assert.deepEqual(parse(f.html).obstacles.map((o) => o.id), ['o1', 'o2', 'o3']);
  },
  async 'release on empty space cancels with no write'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.press('o1'); p.pointerTo('o2'); p.pointerTo(undefined);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(p.ghost().hidden, true); assert.equal(f.writes, 0);
    p.press('o1'); p.pointerTo('o2'); p.pointerTo(null);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(f.writes, 0); assert.deepEqual(parse(f.html).obstacles.map((o) => o.id), ['o1', 'o2']);
  },
  async 'pointercancel, a lost window and a lost button each cancel with no write'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    const stops = [
      () => p.fire(p.el('map'), 'pointercancel'),
      () => p.loseWindow(),
      () => p.pointerTo('o2', 400, 400, { buttons: 0 })
    ];
    for (const stop of stops) {
      p.press('o1'); p.pointerTo('o2');
      assert.equal(p.ghost().hidden, false);
      stop();
      assert.equal(p.ghost().hidden, true); assert.equal(p.box('o2').classList.contains('drop-target'), false);
      p.pointerTo('o2'); assert.equal(p.ghost().hidden, true);
      p.release(); await settle();
    }
    assert.equal(f.writes, 0);
  },
  async 'a drag with a blank new item open drops the blank and writes no blank'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle');
    assert.ok(p.canvasText().includes('1A'));
    p.press('o2'); p.pointerTo('o1');
    assert.equal(p.el('typing').hidden, true); assert.ok(!p.canvasText().includes('New sub-obstacle'));
    assert.equal(p.box('o1').classList.contains('drop-target'), true);
    await settle(); assert.equal(f.writes, 0);
    p.release(); p.clickAfter(); await settle();
    assert.equal(f.writes, 1);
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1']);
    assert.deepEqual(saved.obstacles[0].children.map((o) => o.id), ['o2']);
    assert.equal(p.isSelected('o2'), true);
  },
  async 'dragging the blank new item itself cancels, because finishing removes it'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.plus('obstacle');
    p.press('o3'); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true); assert.equal(p.el('typing').hidden, true);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    assert.equal(p.sandbox.document.body.classList.contains('dragging'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(f.writes, 0); assert.equal(p.isSelected('o1'), true);
    assert.deepEqual(parse(f.html).obstacles[0].children, []);
  },
  async 'a drag keeps what was typed on the item being dragged'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1'); p.el('typing').value = 'better';
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.ghost().textContent, 'better'); assert.equal(p.el('typing').hidden, true);
    p.release(); p.clickAfter(); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o2']);
    assert.equal(saved.obstacles[0].children[0].text, 'better');
  },
  async 'the click after a drag selects nothing new'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o3');
    p.press('o1'); p.pointerTo(undefined); p.release();
    p.fire(p.box('o1'), 'click', { detail: 1 });
    assert.equal(p.isSelected('o3'), true); assert.equal(p.isSelected('o1'), false);
    p.press('o1'); p.pointerTo(undefined); p.release();
    p.fire(p.el('map'), 'click', { detail: 1 });
    assert.equal(p.isSelected('o3'), true);
    p.dragOnto('o1', 'o2');
    assert.equal(p.isSelected('o1'), true);
    // That click was the only one held back. A later press and click works as usual.
    p.press('o2'); p.release(); p.fire(p.box('o2'), 'click', { detail: 1 });
    assert.equal(p.isSelected('o2'), true);
  },
  async 'a drag whose click never comes holds back no later click'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]);
    const p = page({ html }); await settle();
    p.dragOnto('o1', 'o2');
    p.press('o1'); p.pointerTo('o3'); p.release();
    p.press('o3'); p.release(); p.fire(p.box('o3'), 'click', { detail: 1 });
    assert.equal(p.isSelected('o3'), true);
    p.press('o3'); p.pointerTo('o2'); p.release();
    p.fire(p.box('goal'), 'click', { detail: 0 });
    assert.equal(p.isSelected('goal'), true);
  },
  async 'the goal cannot be dragged'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.press('goal'); p.pointerTo('o1');
    assert.equal(p.ghost().hidden, true); assert.equal(p.box('o1').classList.contains('drop-target'), false);
    p.release(); p.fire(p.box('goal'), 'click', { detail: 1 }); await settle();
    assert.equal(p.isSelected('goal'), true); assert.equal(f.writes, 0);
  },
  async 'a press on a control starts no drag'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix')]), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('s1');
    for (const id of ['plus-obstacle', 'plus-solution', 'star-button', 'delete-item', 'typing']) {
      p.fire(p.el(id), 'pointerdown', { button: 0, buttons: 1, clientX: 100, clientY: 100 });
      p.pointerTo('o2');
      assert.equal(p.ghost().hidden, true, id); assert.equal(p.box('o2').classList.contains('drop-target'), false, id);
      p.release();
    }
    assert.equal(f.writes, 0); assert.equal(p.isSelected('s1'), true); assert.equal(p.el('item-tools').hidden, false);
  },
  async 'only the main button starts a drag'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const p = page({ html }); await settle();
    p.press('o1', { button: 2, buttons: 2 }); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true);
  },
  async 'a drag hides the controls and clears the delete question, and cancelling brings back only the controls'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1'); p.tool('delete-item');
    assert.equal(p.el('delete-card').hidden, false);
    p.press('o2'); p.pointerTo('o1');
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('item-tools').hidden, true); assert.deepEqual(p.pluses(), []);
    p.fire(p.box('o2'), 'keydown', { key: 'Escape' });
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(p.isSelected('o1'), true); assert.equal(f.writes, 0);
  },
  async 'text cannot be selected from a press on an item'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const p = page({ html }); await settle();
    assert.ok(!p.fire(p.el('map'), 'selectstart').prevented);
    p.press('o1');
    assert.ok(p.fire(p.box('o1'), 'selectstart').prevented);
    p.pointerTo('o2');
    assert.equal(p.sandbox.document.body.classList.contains('dragging'), true);
    assert.ok(p.fire(p.box('o2'), 'selectstart').prevented);
    p.release(); p.clickAfter();
    assert.ok(!p.fire(p.el('map'), 'selectstart').prevented);
  },
  async 'a pointer near an edge of the map scrolls it, and the scroll stops with the drag'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const p = page({ html }); await settle();
    const map = p.el('map'); map.scrollLeft = 200; map.scrollTop = 200;
    p.press('o1'); p.pointerTo(undefined, 500, 400);
    assert.ok(p.runFrame());
    assert.equal(map.scrollLeft, 200); assert.equal(map.scrollTop, 200);
    p.pointerTo(undefined, 995, 795);
    assert.ok(p.runFrame());
    assert.ok(map.scrollLeft > 200); assert.ok(map.scrollTop > 200);
    const left = map.scrollLeft; const top = map.scrollTop;
    p.pointerTo(undefined, 5, 5);
    assert.ok(p.runFrame());
    assert.ok(map.scrollLeft < left); assert.ok(map.scrollTop < top);
    p.release();
    assert.equal(p.runFrame(), false);
  },
  async 'a scroll under a still pointer changes which box is highlighted'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]);
    const p = page({ html }); await settle();
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.box('o2').classList.contains('drop-target'), true);
    p.sandbox.document.elementFromPoint = () => p.box('o3');
    assert.ok(p.runFrame());
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    assert.equal(p.box('o3').classList.contains('drop-target'), true);
  },
  async 'a redraw during a drag keeps the dim item and the highlight'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const p = page({ html }); await settle();
    p.press('o1'); p.pointerTo('o2');
    p.resize();
    assert.equal(p.box('o1').classList.contains('drag-source'), true);
    assert.equal(p.box('o2').classList.contains('drop-target'), true);
    assert.equal(p.ghost().hidden, false);
    assert.equal(p.el('item-tools').hidden, true);
    p.release(); p.clickAfter();
    assert.ok(p.canvasText().includes('1A'), p.canvasText());
  },
  async 'a press whose release was lost cannot start a drag from a press outside the canvas'() {
    const html = treeHtml([node('o1', 'first'), node('o2', 'other')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.press('o1');
    p.fire(p.el('zoom-out'), 'pointerdown', { button: 0, buttons: 1, clientX: 10, clientY: 10 });
    p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); await settle();
    assert.equal(f.writes, 0);
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, false);
    // The same goes for a drag whose release was lost: the next press ends it, and nothing moves.
    p.fire(p.el('zoom-out'), 'pointerdown', { button: 0, buttons: 1, clientX: 10, clientY: 10 });
    assert.equal(p.ghost().hidden, true);
    p.release(); await settle();
    assert.equal(f.writes, 0);
  },
  async 'a drop while a save runs reaches the file in the follow-up write'() {
    const html = treeHtml([node('a', 'A'), node('b', 'B'), node('c', 'C')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    let open; f.gate = new Promise((r) => { open = r; });
    p.typeOn('a'); p.typeAndEnter('A2'); await settle();
    const before = f.writes;
    p.dragOnto('b', 'c'); await settle();
    assert.equal(f.writes, before);
    open(); f.gate = null; await settle();
    assert.equal(f.writes, before + 2);
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['a', 'c']);
    assert.equal(findIn(saved.obstacles, 'c').children[0].id, 'b');
    assert.equal(findIn(saved.obstacles, 'a').text, 'A2');
    assert.equal(p.status(), 'All changes saved');
  },
  async 'closing during a drag warns only for real changes and leaves the drag whole'() {
    const html = treeHtml([node('a', 'A'), node('b', 'B'), node('c', 'C')]);
    const p = page({ html }); await settle();
    p.press('b'); p.pointerTo('c');
    assert.equal(p.warnsOnClose(), false);
    assert.equal(p.ghost().hidden, false);
    p.release(); p.clickAfter(); await settle();
    p.press('c'); p.pointerTo('a');
    assert.equal(p.warnsOnClose(), true);
    assert.equal(p.ghost().hidden, false);
    p.fire(p.el('map'), 'keydown', { key: 'Escape' });
    assert.equal(p.ghost().hidden, true);
  },
  async 'a drag dims the whole set of sub-items and no others, and cancelling clears it'() {
    const tree = () => treeHtml([node('o1', 'top', [node('o2', 'kid', [node('o3', 'a'), sol('s1', 'b', [node('o4', 'c')])]), node('o5', 'next')]), node('o6', 'other')]);
    const f = fakeHandle(tree()); const p = page({ picker: f, html: tree() }); await settle();
    p.clickSave(); await settle();
    const stops = [
      () => p.fire(p.el('map'), 'keydown', { key: 'Escape' }),
      () => p.fire(p.el('map'), 'pointercancel'),
      () => p.loseWindow(),
      () => { p.pointerTo(undefined); p.release(); }
    ];
    for (const stop of stops) {
      p.press('o2'); p.pointerTo('o6');
      assert.deepEqual(p.dimBoxes(), ['o2', 'o3', 'o4', 's1']);
      assert.deepEqual(p.dimLines(), ['obstacle', 'obstacle', 'obstacle', 'solution']);
      p.resize();
      assert.deepEqual(p.dimBoxes(), ['o2', 'o3', 'o4', 's1']);
      assert.deepEqual(p.dimLines(), ['obstacle', 'obstacle', 'obstacle', 'solution']);
      stop();
      assert.deepEqual(p.dimBoxes(), []); assert.deepEqual(p.dimLines(), []);
      p.release(); p.clickAfter(); await settle();
    }
    assert.equal(f.writes, 0);
    p.dragOnto('o2', 'o6'); await settle();
    assert.deepEqual(p.dimBoxes(), []); assert.deepEqual(p.dimLines(), []);
    assert.equal(f.writes, 1);
  },
  async 'a drag of a single item dims only that item and its own line'() {
    const html = treeHtml([node('o1', 'top', [node('o2', 'kid')]), node('o3', 'other')]);
    const p = page({ html }); await settle();
    p.press('o2'); p.pointerTo('o3');
    assert.deepEqual(p.dimBoxes(), ['o2']); assert.deepEqual(p.dimLines(), ['obstacle']);
  },
  async 'the ghost looks stacked only when items sit under the dragged item'() {
    const html = treeHtml([node('o1', 'top', [node('o2', 'kid')]), node('o3', 'other')]);
    const p = page({ html }); await settle();
    p.press('o1'); p.pointerTo('o3');
    assert.equal(p.ghost().classList.contains('stacked'), true); assert.equal(p.ghost().textContent, 'top');
    p.fire(p.el('map'), 'keydown', { key: 'Escape' }); p.release(); p.clickAfter();
    p.press('o2'); p.pointerTo('o3');
    assert.equal(p.ghost().classList.contains('stacked'), false); assert.equal(p.ghost().textContent, 'kid');
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
    p.addObstacle(); await settle();
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
  async 'escape on a new item returns focus to its parent'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'fix')])]);
    const p = page({ html }); await settle();
    p.addObstacle();
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' });
    assert.equal(p.active(), p.box('goal')); assert.equal(p.isSelected('goal'), true);
    p.plus('solution'); p.pressEnter();
    assert.equal(p.active(), p.box('goal')); assert.equal(p.isSelected('goal'), true);
    p.clickItem('s1'); p.plus('obstacle');
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' });
    assert.equal(p.active(), p.box('s1')); assert.equal(p.isSelected('s1'), true);
    assert.ok(!p.canvasText().includes('1A'), p.canvasText());
  },
  async 'add the first obstacle on an empty map from the goal'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    assert.equal(p.el('first-hint').hidden, false); assert.equal(p.el('edit-hint').hidden, true);
    p.clickItem('goal');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    p.plus('obstacle'); p.typeAndEnter('the first one'); await settle();
    const saved = parse(f.html);
    assert.equal(saved.obstacles.length, 1); assert.equal(saved.obstacles[0].text, 'the first one');
    assert.ok(p.canvasText().includes('1'), p.canvasText());
    assert.equal(p.el('first-hint').hidden, true); assert.equal(p.el('edit-hint').hidden, false);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'add the first solution on an empty map from the goal'() {
    const f = fakeHandle(mapHtml(1)); const p = page({ picker: f }); await settle();
    p.clickSave(); await settle();
    p.clickItem('goal'); p.plus('solution'); p.typeAndEnter('a fix first'); await settle();
    const saved = parse(f.html);
    assert.equal(saved.obstacles[0].kind, 'solution'); assert.equal(saved.obstacles[0].text, 'a fix first');
    assert.equal(p.el('first-hint').hidden, true);
    assert.ok(p.canvasText().includes('a fix first'), p.canvasText());
  },
  async 'a solution on the goal has a star, both pluses and delete, and drags onto an obstacle'() {
    const html = treeHtml([node('o1', 'first'), sol('s1', 'on the goal')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('s1');
    assert.equal(p.el('star-button').hidden, false);
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('delete-item').hidden, false);
    p.dragOnto('s1', 'o1'); await settle();
    const saved = parse(f.html);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1']); assert.equal(saved.obstacles[0].children[0].id, 's1');
    assert.equal(p.isSelected('s1'), true);
  },
  async 'the plan panel draws a solution on the goal and a solution under a solution'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'outer', [sol('s2', 'inner')])]), sol('s3', 'on the goal')],
      { execute: [{ solution_id: 's2', first_move: 'm', owner: '', others_decide: '' }, { solution_id: 's3', first_move: 'n', owner: '', others_decide: '' }] });
    const p = page({ html }); await settle();
    assert.ok(p.panelText().includes('inner (1)'), p.panelText());
    assert.ok(p.panelText().includes('on the goal'), p.panelText());
    assert.ok(!p.panelText().includes('undefined'), p.panelText());
  },
  async 'a map with an old field shows the message and draws nothing'() {
    const html = treeHtml([Object.assign(node('o1', 'old'), { root_cause: false })]);
    const p = page({ html }); await settle();
    const doc = p.sandbox.document;
    assert.equal(doc.getElementById('data-problem').hidden, false);
    assert.equal(doc.getElementById('data-problem-reason').textContent, 'Obstacle 1 uses the old map shape.');
    const oldList = withData(html, Object.assign(parse(mapHtml(1)), { unplaced: [] }));
    const q = page({ html: oldList }); await settle();
    assert.equal(q.sandbox.document.getElementById('data-problem-reason').textContent, 'The map uses the old map shape.');
  },
  async 'a solution shows both pluses, and a solution can go under a solution'() {
    const html = treeHtml([node('o1', 'first', [sol('s1', 'the fix')])]);
    const p = page({ html }); await settle();
    p.clickItem('s1');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the fix');
    assert.equal(p.el('plus-solution').getAttribute('aria-label'), 'Add a solution under the fix');
    p.plus('solution'); p.typeAndEnter('nested');
    assert.equal(p.canvasText().includes('nested'), true);
  },
  async 'the goal shows both pluses and no toolbar'() {
    const html = treeHtml([node('o1', 'first')]);
    const p = page({ html }); await settle();
    p.clickItem('goal');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the goal');
    assert.equal(p.el('plus-solution').getAttribute('aria-label'), 'Add a solution under the goal');
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
    p.clickItem('o1'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
    assert.deepEqual(parse(f.html).obstacles, []);
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    assert.equal(p.active(), p.box('goal'));
  },
  async 'the plan panel names items by label'() {
    const html = treeHtml([node('o1', 'first', [node('o2', 'kid', [sol('s1', 'sol', [], true)])])],
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
  async 'a press that starts in the text box and ends outside it keeps the box open'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.typeOn('o1');
    p.el('typing').value = 'half typed';
    p.fire(p.el('typing'), 'mousedown');
    p.fire(p.el('map'), 'click', { detail: 1 }); await settle();
    assert.equal(p.el('typing').hidden, false); assert.equal(p.el('typing').value, 'half typed');
    assert.equal(f.writes, 0);
    p.fire(p.el('map'), 'click', { detail: 1 }); await settle();
    assert.equal(p.el('typing').hidden, true); assert.equal(parse(f.html).obstacles[0].text, 'half typed');
  },
  async 'the second click of a double-click on a plus does not close the new item'() {
    const html = treeHtml([node('o1', 'first')]);
    const f = fakeHandle(html); const p = page({ picker: f, html }); await settle();
    p.clickSave(); await settle();
    p.clickItem('o1');
    p.fire(p.el('plus-solution'), 'click', { detail: 1 });
    assert.equal(p.el('typing').hidden, false);
    p.fire(p.el('map'), 'click', { detail: 2 }); await settle();
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    p.typeAndEnter('a fix'); await settle();
    assert.equal(parse(f.html).obstacles[0].children[0].text, 'a fix');
  },
  async 'a map with an item id of goal is refused with a plain sentence'() {
    const p = page({ html: treeHtml([node('goal', 'x')]) }); await settle();
    const reason = p.sandbox.document.getElementById('data-problem-reason').textContent;
    assert.equal(p.sandbox.document.getElementById('data-problem').hidden, false);
    assert.ok(reason.includes('uses the id goal'), reason);
    assert.equal(p.sandbox.document.getElementById('canvas').kids.length, 0);
  },
  async 'a map with a quote mark in an item id is refused with a plain sentence'() {
    const p = page({ html: treeHtml([node('o"1', 'x')]) }); await settle();
    const reason = p.sandbox.document.getElementById('data-problem-reason').textContent;
    assert.equal(p.sandbox.document.getElementById('data-problem').hidden, false);
    assert.ok(reason.includes('quote mark in its id'), reason);
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
    const html = treeHtml([], { solutions: [] });
    const p = page({ html }); await settle();
    const doc = p.sandbox.document;
    assert.equal(doc.getElementById('data-problem').hidden, false);
    assert.equal(doc.getElementById('data-problem-reason').textContent, 'The map uses the old map shape.');
    assert.equal(doc.getElementById('canvas').kids.length, 0);
  },
  async 'a plan row naming a missing solution shows the message and draws nothing'() {
    const html = treeHtml([], { execute: [{ solution_id: 'gone', first_move: 'm', owner: '', others_decide: '' }] });
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
