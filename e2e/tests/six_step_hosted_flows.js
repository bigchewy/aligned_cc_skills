// Runs the real page code of a map page as the Claude viewer would, against a fake shared data store.
// Usage: node six_step_hosted_flows.js <path to a map page>. Exits 1 if any flow fails.
// test_six_step_hosted_flows.py runs it against the template and the example map.
const fs = require('fs');
const assert = require('assert');
const { settle, makePage } = require('./six_step_page_stub.js');

const HTML = fs.readFileSync(process.argv[2], 'utf8');
const SLOT = /(<script id="map-data" type="application\/json">)([\s\S]*?)(<\/script>)/;
const fileMap = { map_id: 'm1', revision: 1, person: 'Pat', goal: { text: 'g' }, obstacles: [], key_actions: [], execute: [],
  feedback: { number: '', check_on: '', redraw_if: '' }, baseline: {} };
const page = makePage(HTML, () => HTML.replace(SLOT, (w, a, b, c) => a + JSON.stringify(fileMap) + c));

const json = (value) => JSON.parse(JSON.stringify(value));
const isObject = (v) => Boolean(v) && typeof v === 'object' && !Array.isArray(v);
function deepFreeze(value) {
  if (value && typeof value === 'object') { Object.values(value).forEach(deepFreeze); Object.freeze(value); }
  return value;
}
// What the store does with an update. It is written here again so the page's own overlay isn't testing itself.
function merge(target, change) {
  Object.keys(change).forEach((key) => {
    const value = change[key];
    if (isObject(value) && value.__delete__ === true) delete target[key];
    else if (isObject(value)) { if (!isObject(target[key])) target[key] = {}; merge(target[key], value); }
    else target[key] = value;
  });
  return target;
}

// Follows db.d.ts: frozen snapshots, your own write shows at once as pending, one terminal error at most.
function fakeStore(body, options) {
  const s = Object.assign({
    body: body === undefined ? null : json(body),
    writes: [], gets: 0, subscribes: 0, useNames: [], paths: [],
    next: null, error: null,
    hold: false, held: [], refuse: [], inFlight: 0, mostInFlight: 0,
    // Off means the test delivers every snapshot itself.
    echo: true,
    can: {}
  }, options);
  s.deliver = (data, metadata) => {
    const frozen = data === null ? undefined : deepFreeze(json(data));
    s.next(deepFreeze({ id: 'main', exists: data !== null, data: () => frozen,
      metadata: Object.assign({ fromCache: false, hasPendingWrites: false }, metadata) }));
  };
  // Another person or Claude writing.
  s.remote = (change) => { merge(s.body, json(change)); s.deliver(s.body); };
  const finish = (entry, error) => {
    s.inFlight--;
    if (error) {
      if (s.echo) s.deliver(s.body);
      entry.reject(error);
      return;
    }
    merge(s.body, entry.change);
    if (s.echo) s.deliver(s.body);
    entry.resolve();
  };
  s.release = () => { const entry = s.held.shift(); assert.ok(entry, 'no write is held'); finish(entry); };
  s.reject = (code) => { const entry = s.held.shift(); assert.ok(entry, 'no write is held'); finish(entry, { code, message: code }); };
  const ref = {
    id: 'main',
    path: 'maps/main',
    get() { s.gets++; return Promise.resolve(); },
    onSnapshot(next, error) { s.subscribes++; s.next = next; s.error = error; return () => {}; },
    update(data) {
      const change = json(data);
      s.writes.push(change);
      s.inFlight++;
      s.mostInFlight = Math.max(s.mostInFlight, s.inFlight);
      return new Promise((resolve, reject) => {
        const entry = { change, resolve, reject };
        if (s.echo) s.deliver(merge(json(s.body), change), { hasPendingWrites: true });
        if (s.hold) { s.held.push(entry); return; }
        const refused = s.refuse.shift();
        setImmediate(() => finish(entry, refused ? { code: refused, message: refused } : undefined));
      });
    }
  };
  s.db = { doc(path) { s.paths.push(path); return ref; } };
  s.user = { can: (name) => Promise.resolve(name in s.can ? s.can[name] : true) };
  s.claude = { use(name) { s.useNames.push(name); return Promise.resolve(name === 'db' ? s.db : name === 'user' ? s.user : null); } };
  return s;
}

function fakeTimers() {
  const t = { list: [], count: 0,
    set(f, ms) { t.count += 1; t.list.push({ id: t.count, f, ms }); return t.count; },
    clear(id) { t.list = t.list.filter((x) => x.id !== id); },
    has(ms) { return t.list.some((x) => x.ms === ms); },
    // Runs what the test picks, and takes it off the list first.
    run(pick) { const due = t.list.filter(pick); t.list = t.list.filter((x) => !pick(x)); due.forEach((x) => x.f()); } };
  return t;
}

const item = (kind, text, parent, order, more) => Object.assign({ kind, text, star: false, parent, order }, more);
const mapDoc = (items, more) => Object.assign({ version: 1, person: 'Pat', goal: { text: 'g' }, items: items || {},
  key_actions: [], execute: [], feedback: { number: '', check_on: '', redraw_if: '' } }, more);
const twoItems = () => mapDoc({ a1: item('obstacle', 'first', 'goal', 1), s1: item('solution', 'fix', 'a1', 1), a2: item('obstacle', 'second', 'goal', 2) });

// The page opened in the viewer, with the store's first snapshot delivered.
async function opened(doc, more) {
  const s = fakeStore(doc === undefined ? twoItems() : doc, more);
  const timers = fakeTimers();
  const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear });
  await settle();
  s.deliver(s.body);
  await settle();
  return { p, s, timers };
}

const hasBox = (p, id) => p.el('canvas').walk().some((k) => k.dataset.key && k.dataset.key.endsWith('|' + id));
const CANT_OPEN = "Can't open the saved map right now.";

function assertNoEditing(p, s, id) {
  const before = s ? s.writes.length : 0;
  p.openGoal();
  assert.equal(p.el('typing').hidden, true, 'typing opened');
  assert.deepEqual(p.pluses(), [], 'a plus showed');
  assert.equal(p.el('item-tools').hidden, true, 'the toolbar showed');
  if (id) {
    p.typeOn(id);
    assert.equal(p.el('typing').hidden, true, 'typing opened on an item');
    assert.deepEqual(p.pluses(), []);
    assert.equal(p.el('item-tools').hidden, true);
    p.press(id); p.pointerTo('goal');
    assert.equal(p.ghost().hidden, true, 'a drag started');
    p.release(); p.clickAfter();
  }
  if (s) assert.equal(s.writes.length, before, 'something wrote');
}

const flows = {
  async 'no window.claude uses file saving, with no store call'() {
    const s = fakeStore(twoItems());
    const p = page({ picker: {} }); await settle();
    assert.deepEqual(s.useNames, []);
    assert.equal(p.status(), "Changes aren't being saved yet."); assert.equal(p.button(), 'Turn on saving');
    assert.equal(p.el('data-problem-reason').textContent, '');
    p.edit('x'); await settle();
    assert.equal(p.status(), "Changes aren't being saved yet."); assert.equal(p.warnsOnClose(), true);
  },
  async 'window.claude with a null db shows it can\'t open, allows no edits and never uses the picker'() {
    const claude = { use: () => Promise.resolve(null) };
    const p = page({ claude, picker: {} }); await settle();
    assert.equal(p.status(), CANT_OPEN);
    assert.equal(p.el('data-problem-reason').textContent, '', 'the data problem page showed');
    assert.equal(p.button(), '');
    assertNoEditing(p);
    p.clickSave(); await settle();
    assert.equal(p.sandbox.pickerCalls, 0); assert.equal(p.idbUses(), 0);
  },
  async 'a window.claude with no use, or a use that fails, counts as can\'t open'() {
    for (const claude of [{}, { use() { throw new Error('no'); } }, { use: () => Promise.reject(new Error('no')) }]) {
      const p = page({ claude, picker: {} }); await settle();
      assert.equal(p.status(), CANT_OPEN);
      assertNoEditing(p);
      assert.equal(p.sandbox.pickerCalls, 0);
    }
  },
  async 'no map in the data says the map isn\'t set up and allows no edits'() {
    const s = fakeStore(null); const p = page({ claude: s.claude, picker: {} }); await settle();
    s.deliver(null); await settle();
    assert.ok(p.status().includes("isn't set up"), p.status());
    assertNoEditing(p, s);
    assert.equal(p.sandbox.pickerCalls, 0);
    s.body = twoItems(); s.deliver(s.body); await settle();
    assert.equal(p.status(), 'All changes saved');
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
  },
  async 'a map removed from the data mid-edit closes everything and writes nothing'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    s.body = null; s.deliver(null); await settle();
    assert.equal(p.el('typing').hidden, true);
    assert.ok(p.status().includes("isn't set up"), p.status());
    assert.ok(!p.canvasText().includes('first'));
    assertNoEditing(p, s);
    assert.equal(s.writes.length, 0);
  },
  async 'a missing map from a cached view waits for the store to answer'() {
    const s = fakeStore(null); const p = page({ claude: s.claude }); await settle();
    s.deliver(null, { fromCache: true }); await settle();
    assert.equal(p.status(), 'Opening...');
    s.deliver(null); await settle();
    assert.ok(p.status().includes("isn't set up"), p.status());
  },
  async 'unknown version shows the map with no editing controls and asks for a newer page'() {
    const { p, s } = await opened(Object.assign(twoItems(), { version: 2 }));
    assert.ok(p.canvasText().includes('first'));
    assert.equal(p.status(), 'This page is out of date. Open the newest version to keep editing.');
    p.clickItem('a1');
    assert.equal(p.isSelected('a1'), true);
    assertNoEditing(p, s, 'a1');
  },
  async 'a version change mid-edit closes the box and writes nothing'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    s.remote({ version: 2 }); await settle();
    assert.equal(p.el('typing').hidden, true);
    assert.equal(s.writes.length, 0);
    assert.ok(p.canvasText().includes('first'));
  },
  async 'no edits until the first snapshot, and 10 seconds of silence says it can\'t reach the map'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear, picker: {} });
    assert.equal(p.status(), 'Opening...');
    await settle();
    assert.equal(p.status(), 'Opening...');
    assert.deepEqual(s.paths, ['maps/main']); assert.equal(s.subscribes, 1);
    assertNoEditing(p, s);
    assert.equal(timers.has(10000), true);
    timers.run((x) => x.ms === 10000); await settle();
    assert.equal(p.status(), CANT_OPEN);
    assertNoEditing(p, s);
    s.deliver(s.body); await settle();
    assert.equal(p.status(), 'All changes saved');
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
    assert.equal(s.subscribes, 1);
  },
  async 'a confirmed snapshot stops the 10 second wait, and a cached one doesn\'t'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body, { fromCache: true }); await settle();
    assert.equal(timers.has(10000), true);
    s.deliver(s.body); await settle();
    assert.equal(timers.has(10000), false);
  },
  async 'a snapshot error before the first snapshot says it can\'t reach the map'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.error({ code: 'revoked', message: 'x' }); await settle();
    assert.equal(p.status(), CANT_OPEN);
    assert.equal(timers.has(10000), false);
    assertNoEditing(p, s);
  },
  async 'a star sends only that field, once'() {
    const { p, s } = await opened();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.deepEqual(s.writes, [{ items: { s1: { star: true } } }]);
    assert.equal(p.status(), 'All changes saved');
    p.resize(); await settle();
    assert.equal(s.writes.length, 1);
  },
  async 'a drag sends only the moved item, once'() {
    const { p, s } = await opened();
    p.dragOnto('a2', 'a1'); await settle();
    assert.deepEqual(s.writes, [{ items: { a2: { parent: 'a1', order: 2 } } }]);
    assert.equal(p.isSelected('a2'), true);
    assert.ok(p.boxes().length > 0);
  },
  async 'typing on an item or the goal sends only that text, once'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.typeAndEnter('new words'); await settle();
    p.edit('new goal'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'new words' } } }, { goal: { text: 'new goal' } }]);
  },
  async 'a delete sends the item and everything under it'() {
    const { p, s } = await opened();
    p.clickItem('a1'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { __delete__: true }, s1: { __delete__: true } } }]);
    assert.equal(hasBox(p, 'a1'), false); assert.equal(hasBox(p, 's1'), false);
    assert.equal(p.active(), p.box('goal'));
  },
  async 'a second edit while the first is in flight survives the first\'s confirmed snapshot'() {
    const { p, s } = await opened(undefined, { hold: true, echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    p.typeOn('a2'); p.typeAndEnter('two'); await settle();
    assert.equal(s.writes.length, 1, 'a second write started');
    assert.equal(s.mostInFlight, 1);
    assert.equal(p.status(), 'Saving...');

    // The store has the first change only. The second is still waiting here.
    s.deliver(merge(json(s.body), { items: { a1: { text: 'one' } } }));
    await settle();
    assert.ok(p.canvasText().includes('two'), p.canvasText());
    assert.equal(p.status(), 'Saving...');

    s.release(); await settle();
    assert.deepEqual(s.writes[1], { items: { a2: { text: 'two' } } });
    assert.equal(s.mostInFlight, 1);
    assert.equal(p.status(), 'Saving...');
    assert.ok(p.canvasText().includes('two'));

    s.release(); await settle();
    s.deliver(s.body); await settle();
    assert.equal(p.status(), 'All changes saved');
    assert.ok(p.canvasText().includes('one')); assert.ok(p.canvasText().includes('two'));
  },
  async 'a snapshot that drops a change in flight keeps it on screen'() {
    const { p, s } = await opened(undefined, { hold: true, echo: false });
    p.clickItem('a2'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
    s.deliver(s.body); await settle();
    assert.equal(hasBox(p, 'a2'), false);
    assert.equal(s.writes.length, 1);
  },
  async 'a live update keeps focus on the box that had it, even when it is not the selected one'() {
    const { p, s } = await opened();
    p.clickItem('a1'); p.box('a2').focus();
    s.remote({ items: { s1: { text: 'other change' } } }); await settle();
    assert.equal(p.active(), p.box('a2'));
    assert.equal(p.isSelected('a1'), true);
    p.el('toggle-plan').focus();
    s.remote({ items: { s1: { text: 'another change' } } }); await settle();
    assert.equal(p.active(), p.el('toggle-plan'));
  },
  async 'a live update changes the screen and writes nothing'() {
    const { p, s } = await opened();
    s.remote({ items: { a1: { text: 'their words' }, n1: item('obstacle', 'added by them', 'a2', 1) }, goal: { text: 'their goal' }, person: 'Sam' });
    await settle();
    const seen = p.canvasText();
    assert.ok(seen.includes('their words') && seen.includes('added by them') && seen.includes('their goal'), seen);
    assert.equal(p.el('person').textContent, 'Sam');
    assert.equal(s.writes.length, 0);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a repair made while reading is never written back'() {
    const doc = mapDoc({
      orphan: item('obstacle', 'lost parent', 'gone', 1),
      loopa: item('obstacle', 'loop a', 'loopb', 1),
      loopb: item('obstacle', 'loop b', 'loopa', 1),
      nokind: { text: 'half deleted', star: true }
    });
    const { p, s } = await opened(doc);
    assert.ok(p.canvasText().includes('lost parent')); assert.ok(!p.canvasText().includes('half deleted'));
    p.resize(); p.clickItem('orphan'); p.clickEmpty(); await settle();
    assert.equal(s.writes.length, 0);
    p.typeOn('orphan'); p.typeAndEnter('found'); await settle();
    assert.deepEqual(s.writes, [{ items: { orphan: { text: 'found' } } }]);
  },
  async 'an open text box with no change writes nothing, even after a remote change to that item'() {
    const { p, s } = await opened();
    p.typeOn('a1');
    s.remote({ items: { a1: { text: 'their words' } } }); await settle();
    assert.equal(p.el('typing').value, 'first');
    p.pressEnter(); await settle();
    assert.equal(s.writes.length, 0);
    assert.equal(p.el('typing').hidden, true);
    assert.ok(p.canvasText().includes('their words'), p.canvasText());
    assert.equal(p.message(), '');
  },
  async 'an open goal box with no change writes nothing'() {
    const { p, s } = await opened();
    p.openGoal();
    s.remote({ goal: { text: 'their goal' } }); await settle();
    p.pressEnter(); await settle();
    assert.equal(s.writes.length, 0);
    assert.ok(p.canvasText().includes('their goal'));
  },
  async 'a changed text box over a remote change writes, and shows a notice'() {
    const { p, s } = await opened();
    p.typeOn('a1');
    s.remote({ items: { a1: { text: 'their words' } } }); await settle();
    p.typeAndEnter('my words'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'my words' } } }]);
    assert.ok(p.canvasText().includes('my words'));
    assert.ok(p.message().length > 0, 'no notice');
    p.typeOn('a2'); p.typeAndEnter('calm'); await settle();
    assert.equal(p.message(), '', 'the notice stayed');
  },
  async 'a changed text box with no remote change shows no notice'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.typeAndEnter('my words'); await settle();
    assert.equal(s.writes.length, 1); assert.equal(p.message(), '');
  },
  async 'typing survives a live update'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    s.remote({ items: { a2: { text: 'other change' } } }); await settle();
    assert.equal(p.el('typing').hidden, false);
    assert.equal(p.el('typing').value, 'half typed');
    assert.equal(p.active(), p.el('typing'));
    assert.ok(p.canvasText().includes('other change'));
    p.pressEnter(); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'half typed' } } }]);
  },
  async 'a new blank item survives a live update and never reaches the store'() {
    const { p, s } = await opened();
    p.clickItem('a1'); p.plus('obstacle');
    const id = JSON.parse(p.el('canvas').walk().find((k) => k.classList.contains('selected')).dataset.ref).id;
    s.remote({ items: { a2: { text: 'other change' } } }); await settle();
    assert.equal(hasBox(p, id), true);
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    assert.equal(s.writes.length, 0);
    assert.equal(p.status(), 'All changes saved');
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(hasBox(p, id), false);
    assert.equal(s.writes.length, 0);
    assert.equal(p.isSelected('a1'), true);
  },
  async 'a new blank item under an item someone deletes moves under the goal'() {
    const { p, s } = await opened();
    p.clickItem('a2'); p.plus('solution');
    const id = JSON.parse(p.el('canvas').walk().find((k) => k.classList.contains('selected')).dataset.ref).id;
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    assert.equal(hasBox(p, 'a2'), false); assert.equal(hasBox(p, id), true);
    assert.equal(s.writes.length, 0);
    p.typeAndEnter('still here'); await settle();
    assert.deepEqual(s.writes[0].items[id], { kind: 'solution', text: 'still here', star: false, parent: 'goal', order: 2 });
  },
  async 'closing a new item empty after its starting point is deleted leaves nothing selected'() {
    const { p, s } = await opened();
    p.clickItem('a2'); p.plus('obstacle');
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(p.el('item-tools').hidden, true); assert.deepEqual(p.pluses(), []);
    assert.equal(s.writes.length, 0);
  },
  async 'finishing a new item sends all its fields with a random id'() {
    const { p, s } = await opened();
    p.clickItem('a1'); p.plus('solution'); p.typeAndEnter('a new fix'); await settle();
    assert.equal(s.writes.length, 1);
    const ids = Object.keys(s.writes[0].items);
    assert.equal(ids.length, 1);
    assert.ok(/^[a-z0-9]+$/.test(ids[0]) && ids[0].length >= 8, ids[0]);
    assert.deepEqual(s.writes[0].items[ids[0]], { kind: 'solution', text: 'a new fix', star: false, parent: 'a1', order: 2 });
    assert.ok(!('key_actions' in s.writes[0]) && !('execute' in s.writes[0]));
    assert.equal(hasBox(p, ids[0]), true);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a remote delete of the item being typed on keeps the box open, and finishing adds the text as a new item under the goal'() {
    const { p, s } = await opened();
    p.typeOn('s1'); p.el('typing').value = 'my words';
    s.remote({ items: { s1: { __delete__: true } } }); await settle();
    assert.equal(p.el('typing').hidden, false); assert.equal(p.el('typing').value, 'my words');
    assert.equal(p.active(), p.el('typing'));
    assert.equal(hasBox(p, 's1'), false);
    assert.equal(s.writes.length, 0);
    p.pressEnter(); await settle();
    assert.equal(s.writes.length, 1);
    const ids = Object.keys(s.writes[0].items);
    assert.equal(ids.length, 1); assert.notEqual(ids[0], 's1');
    assert.deepEqual(s.writes[0].items[ids[0]], { kind: 'solution', text: 'my words', star: false, parent: 'goal', order: 3 });
    assert.ok(p.canvasText().includes('my words'));
  },
  async 'a remote delete of an item with an unchanged box stays deleted when the box closes'() {
    const { p, s } = await opened();
    p.typeOn('a2');
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    p.pressEnter(); await settle();
    assert.equal(s.writes.length, 0);
    assert.ok(!p.canvasText().includes('second'));
    assert.equal(p.el('typing').hidden, true);
    assert.equal(p.el('item-tools').hidden, true);
  },
  async 'escape after a remote delete of the item being typed on adds nothing'() {
    const { p, s } = await opened();
    p.typeOn('a2'); p.el('typing').value = 'my words';
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(s.writes.length, 0);
    assert.ok(!p.canvasText().includes('my words'));
  },
  async 'a remote delete of the dragged item cancels the drag'() {
    const { p, s } = await opened();
    p.press('a2'); p.pointerTo('a1');
    assert.equal(p.ghost().hidden, false);
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    assert.equal(p.ghost().hidden, true);
    assert.equal(hasBox(p, 'a2'), false);
    assert.equal(p.sandbox.document.body.classList.contains('dragging'), false);
    p.pointerTo('a1'); p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0);
  },
  async 'a remote delete of an item being pressed starts no drag'() {
    const { p, s } = await opened();
    p.press('a2');
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    p.pointerTo('a1');
    assert.equal(p.ghost().hidden, true);
    p.release(); await settle();
    assert.equal(s.writes.length, 0);
  },
  async 'a remote delete of the selected item clears the selection'() {
    const { p, s } = await opened();
    p.clickItem('a2');
    assert.equal(p.el('item-tools').hidden, false);
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    assert.equal(p.el('item-tools').hidden, true); assert.deepEqual(p.pluses(), []);
    assert.equal(s.writes.length, 0);
    p.resize(); await settle();
    assert.equal(p.el('item-tools').hidden, true);
  },
  async 'a remote delete of that item closes the card'() {
    const doc = mapDoc({ a1: item('obstacle', 'first', 'goal', 1), s1: item('solution', 'fix', 'a1', 1, { star: true }) });
    const { p, s } = await opened(doc);
    p.clickItem('a1'); p.tool('delete-item');
    assert.equal(p.el('delete-card').hidden, false);
    s.remote({ items: { a1: { __delete__: true }, s1: { __delete__: true } } }); await settle();
    assert.equal(p.el('delete-card').hidden, true);
    assert.equal(p.el('item-tools').hidden, true);
    assert.equal(s.writes.length, 0);
  },
  async 'a refused delete keeps the item gone on screen, says not saved, and closes the card'() {
    const doc = mapDoc({ a1: item('obstacle', 'first', 'goal', 1), a2: item('obstacle', 'second', 'goal', 2) });
    const { p, s } = await opened(doc, { refuse: ['invalid_argument'] });
    p.clickItem('a1'); p.tool('delete-item'); await settle();
    assert.equal(s.writes.length, 0, 'asking wrote something');
    p.tool('delete-yes'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { __delete__: true } } }]);
    assert.equal(p.status(), 'Not saved');
    assert.equal(p.el('delete-card').hidden, true);
    assert.ok(!p.canvasText().includes('first'), p.canvasText());
    assert.ok(p.canvasText().includes('second'));
    await settle();
    assert.equal(s.writes.length, 1, 'a refused delete went again by itself');
  },
  async 'a live update keeps the card open, and Delete takes what is under the item by then'() {
    const doc = mapDoc({ a1: item('obstacle', 'first', 'goal', 1), s1: item('solution', 'fix', 'a1', 1, { star: true }) });
    const { p, s } = await opened(doc);
    p.clickItem('a1'); p.tool('delete-item');
    s.remote({ items: { s2: item('solution', 'their pick', 'a1', 2, { star: true }) } }); await settle();
    assert.equal(p.el('delete-card').hidden, false);
    p.tool('delete-yes'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { __delete__: true }, s1: { __delete__: true }, s2: { __delete__: true } } }]);
  },
  async 'a live update during a drag keeps the drag'() {
    const { p, s } = await opened();
    p.press('a2'); p.pointerTo('a1');
    assert.ok(p.box('a1').classList.contains('drop-target'));
    s.remote({ items: { a1: { text: 'their words' }, n1: item('solution', 'under the drag', 'a2', 1) } }); await settle();
    assert.equal(p.ghost().hidden, false);
    assert.ok(p.dimBoxes().includes('a2') && p.dimBoxes().includes('n1'), String(p.dimBoxes()));
    assert.ok(p.box('a1').classList.contains('drop-target'));
    p.pointerTo('a1'); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(s.writes, [{ items: { a2: { parent: 'a1', order: 2 } } }]);
  },
  async 'a live update that removes the drop target leaves the drag going with no target'() {
    const { p, s } = await opened();
    p.press('s1'); p.pointerTo('a2');
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    assert.equal(p.ghost().hidden, false);
    p.pointerTo(undefined); p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0);
    assert.equal(p.ghost().hidden, true);
  },
  async 'deleting a solution hides its plan rows and sends no plan fields'() {
    const doc = Object.assign(twoItems(), {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' }]
    });
    const { p, s } = await opened(doc);
    assert.ok(p.panelText().includes('the first move'));
    p.clickItem('s1'); p.tool('delete-item');
    p.tool('delete-yes'); await settle();
    assert.deepEqual(s.writes, [{ items: { s1: { __delete__: true } } }]);
    assert.ok(!p.panelText().includes('the first move'), p.panelText());
    assert.ok(p.panelText().includes('the action'));
    assert.equal(s.body.execute.length, 1, 'the page changed the plan');
  },
  async 'odd text from another writer shows as plain text'() {
    const odd = '<img src=x onerror=alert(1)>';
    const doc = mapDoc({
      a1: item('obstacle', odd, 'goal', 1),
      s1: item('solution', odd, 'a1', 1),
      n1: item('obstacle', 42, 'goal', 2),
      constructor: item('solution', 'an odd id', 'goal', 3),
      '"><b>': item('obstacle', 'a bad id', 'goal', 4)
    }, { person: odd, goal: { text: odd },
      execute: [{ solution_id: 's1', first_move: odd, owner: odd, others_decide: '' }],
      key_actions: [{ text: odd, risk: odd, solution_ids: ['s1'] }] });
    const { p, s } = await opened(doc);
    assert.ok(p.box('a1').textContent.includes(odd));
    assert.equal(p.box('goal').textContent, odd);
    assert.equal(p.el('person').textContent, odd);
    assert.ok(p.panelText().includes(odd));
    assert.ok(!p.canvasText().includes('a bad id'));
    assert.ok(!p.el('canvas').walk().concat(p.el('panel').walk()).some((k) => k.tag === 'IMG' || k.tag === 'B'));
    assert.ok(!p.el('canvas').inserted.includes(odd));
    p.clickItem('constructor'); p.clickItem('n1'); p.clickItem('a1');
    assert.equal(s.writes.length, 0);
  },
  async 'snapshots are frozen and the page opens with one subscription'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.typeAndEnter('x'); await settle();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    p.resize(); await settle();
    assert.equal(s.subscribes, 1); assert.deepEqual(s.paths, ['maps/main']);
    assert.ok(!s.writes.some((w) => 'key_actions' in w || 'execute' in w || 'version' in w));
  },
  async 'a refused write keeps the edit on screen and says not saved'() {
    const { p, s } = await opened(undefined, { refuse: ['invalid_argument'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(s.writes.length, 1);
    assert.equal(p.status(), 'Not saved');
    assert.ok(p.box('s1').textContent.includes('★'), p.box('s1').textContent);
    await settle();
    assert.equal(s.writes.length, 1, 'a refused write went again by itself');
    p.typeOn('a2'); p.typeAndEnter('next'); await settle();
    assert.deepEqual(s.writes.slice(1), [{ items: { s1: { star: true } } }, { items: { a2: { text: 'next' } } }]);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a write lost to a dropped connection is sent again with the same change'() {
    const { p, s, timers } = await opened(undefined, { refuse: ['unavailable'] });
    p.typeOn('a1'); p.typeAndEnter('kept'); await settle();
    assert.equal(s.writes.length, 1);
    assert.equal(p.status(), 'Saving...');
    assert.ok(p.canvasText().includes('kept'));
    timers.run((x) => x.ms < 10000); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'kept' } } }, { items: { a1: { text: 'kept' } } }]);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a write whose call throws counts as failed and keeps the edit'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    const update = s.db.doc('maps/main').update;
    s.paths.length = 0;
    s.db.doc('maps/main').update = () => { throw new Error('no'); };
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    p.typeOn('a1'); p.typeAndEnter('kept'); await settle();
    assert.ok(p.canvasText().includes('kept'));
    assert.equal(p.status(), 'Saving...');
    s.db.doc('maps/main').update = update;
    timers.run((x) => x.ms < 10000); await settle();
    assert.equal(p.status(), 'All changes saved');
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'kept' } } }]);
  },
  async 'status goes Saving... then All changes saved only after the write confirms'() {
    const { p, s } = await opened(undefined, { hold: true });
    assert.equal(p.status(), 'All changes saved');
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    // The store has echoed the edit back as a pending write. That is not a confirmation.
    assert.equal(p.status(), 'Saving...');
    s.release(); await settle();
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a write held past 15 seconds says so and keeps the edit'() {
    const { p, s, timers } = await opened(undefined, { hold: true, echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    assert.equal(timers.has(15000), true, 'no 15 second timer');
    assert.equal(p.status(), 'Saving...');
    timers.run((x) => x.ms === 15000); await settle();
    assert.notEqual(p.status(), 'Saving...'); assert.notEqual(p.status(), 'All changes saved');
    assert.ok(/longer/i.test(p.status()), p.status());
    assert.ok(p.canvasText().includes('one'));
    // A second edit queues behind it and the slow note stays.
    p.typeOn('a2'); p.typeAndEnter('two'); await settle();
    assert.ok(/longer/i.test(p.status()), p.status());
    assert.equal(s.writes.length, 1);
    s.release(); await settle();
    assert.equal(s.writes.length, 2);
    assert.equal(p.status(), 'Saving...', 'the next write is fresh');
    s.release(); await settle();
    assert.equal(p.status(), 'All changes saved');
    assert.equal(timers.has(15000), false, 'a timer was left');
  },
  async 'a slow write that then fails shows not saved, and the slow note is gone when it settles'() {
    const { p, s, timers } = await opened(undefined, { hold: true, echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    timers.run((x) => x.ms === 15000); await settle();
    s.reject('invalid_argument'); await settle();
    assert.equal(p.status(), 'Not saved');
    assert.ok(p.canvasText().includes('one'));
  },
  async 'a refused write keeps the edit on screen, marked not saved, with a plain message'() {
    const { p, s } = await opened(undefined, { refuse: ['invalid_argument'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(p.status(), 'Not saved');
    assert.ok(p.box('s1').textContent.includes('★'));
    const m = p.message();
    assert.ok(/isn't saved/.test(m) && /still on this page/.test(m), m);
    assert.ok(!/reload|file|copy/i.test(m), m);
    assert.equal(s.writes.length, 1);
  },
  async 'a failed-write message stays through the next action while the failure is still true, and clears once a write confirms'() {
    const { p, s } = await opened(undefined, { refuse: ['invalid_argument'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    const m = p.message();
    assert.ok(m.length > 0);
    s.hold = true; s.echo = false;
    p.typeOn('a2'); p.typeAndEnter('next'); await settle();
    assert.equal(s.writes.length, 2);
    assert.equal(p.message(), m, 'the message went while still true');
    assert.equal(p.status(), 'Not saved');
    s.release(); await settle();
    assert.equal(p.message(), '', 'the star went through, so the failure is over');
    assert.equal(p.status(), 'Saving...');
    s.release(); await settle();
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a notice about someone else\'s change does not hide a failed-write message'() {
    const { p, s } = await opened(undefined, { refuse: ['quota_exceeded', 'quota_exceeded'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.ok(/full/i.test(p.message()), p.message());
    p.typeOn('a1');
    s.remote({ items: { a1: { text: 'their words' } } }); await settle();
    p.typeAndEnter('my words'); await settle();
    // The star is sent again first and refused again, so the failure is still true.
    assert.equal(s.writes.length, 2);
    assert.ok(/full/i.test(p.message()), p.message());
  },
  async 'can("data.write") false hides pluses, toolbar and dragging, and draws live'() {
    const { p, s } = await opened(undefined, { can: { 'data.write': false } });
    assert.ok(p.canvasText().includes('first'));
    assert.ok(/view only/i.test(p.status()), p.status());
    p.clickItem('a1');
    assert.equal(p.isSelected('a1'), true);
    assertNoEditing(p, s, 'a1');
    s.remote({ items: { a1: { text: 'their words' } } }); await settle();
    assert.ok(p.canvasText().includes('their words'));
    assert.equal(s.writes.length, 0);
  },
  async 'can("data.write") null keeps editing until invalid_argument, then goes read-only for the visit'() {
    const { p, s } = await opened(undefined, { can: { 'data.write': null }, refuse: ['invalid_argument'] });
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false); p.pressEnter();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(s.writes.length, 1);
    assert.ok(/view only/i.test(p.status()), p.status());
    assert.ok(p.box('s1').textContent.includes('★'), 'the edit left the screen');
    assert.ok(/isn't saved/.test(p.message()) || /view/i.test(p.message()), p.message());
    assertNoEditing(p, s, 'a1');
    s.remote({ items: { a2: { text: 'live' } } }); await settle();
    assert.ok(p.canvasText().includes('live'));
  },
  async 'a missing user capability counts as not told, and a refusal makes it read-only'() {
    const s = fakeStore(twoItems(), { refuse: ['invalid_argument'] });
    s.claude.use = (name) => { s.useNames.push(name); return Promise.resolve(name === 'db' ? s.db : null); };
    const timers = fakeTimers();
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false); p.pressEnter();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.ok(/view only/i.test(p.status()), p.status());
    assertNoEditing(p, s, 'a1');
  },
  async 'a user capability that throws counts as not told'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    s.claude.use = (name) => (name === 'db' ? Promise.resolve(s.db) : Promise.reject(new Error('no')));
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
  },
  async 'invalid_argument with can("data.write") true stays editable and says not saved'() {
    const { p, s } = await opened(undefined, { can: { 'data.write': true }, refuse: ['invalid_argument'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(p.status(), 'Not saved');
    p.typeOn('a2'); assert.equal(p.el('typing').hidden, false);
    p.typeAndEnter('again'); await settle();
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a write rejected as revoked shows the map can\'t be reached and allows no edits'() {
    const { p, s } = await opened(undefined, { refuse: ['revoked'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(p.status(), CANT_OPEN);
    assert.ok(p.canvasText().includes('first'));
    assertNoEditing(p, s, 'a1');
  },
  async '10 seconds with no fromCache:false says the map may be out of date, and the next definitive snapshot clears it'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body, { fromCache: true }); await settle();
    assert.equal(p.status(), 'All changes saved');
    timers.run((x) => x.ms === 10000); await settle();
    assert.ok(/out of date/i.test(p.status()), p.status());
    assert.ok(p.canvasText().includes('first'));
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
    p.pressEnter();
    s.deliver(s.body); await settle();
    assert.equal(p.status(), 'All changes saved');
    assert.equal(s.subscribes, 1);
  },
  async 'a listener ended with unavailable subscribes again once, and a second end says live updates stopped'() {
    const { p, s } = await opened();
    s.error({ code: 'unavailable', message: 'x' }); await settle();
    assert.equal(s.subscribes, 2);
    assert.equal(p.status(), 'All changes saved');
    s.deliver(s.body); await settle();
    s.error({ code: 'unavailable', message: 'x' }); await settle();
    assert.equal(s.subscribes, 2, 'subscribed a third time');
    assert.ok(/live updates/i.test(p.status()), p.status());
    assert.ok(p.canvasText().includes('first'));
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
  },
  async 'a terminal code other than unavailable does not subscribe again'() {
    const { p, s } = await opened();
    s.error({ code: 'resource_exhausted', message: 'x' }); await settle();
    assert.equal(s.subscribes, 1);
    assert.ok(/live updates/i.test(p.status()), p.status());
  },
  async 'revoked shows the map can\'t be reached and allows no edits'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    s.error({ code: 'revoked', message: 'x' }); await settle();
    assert.equal(s.subscribes, 1);
    assert.equal(p.status(), CANT_OPEN);
    assert.ok(p.canvasText().includes('first'));
    assert.equal(p.el('typing').hidden, true);
    assertNoEditing(p, s, 'a1');
  },
  async 'a change to an item someone deleted is dropped from the screen with no throw'() {
    const { p, s } = await opened(undefined, { hold: true, echo: false });
    p.typeOn('a2'); p.typeAndEnter('late edit'); await settle();
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    assert.equal(hasBox(p, 'a2'), false);
    assert.ok(!p.canvasText().includes('late edit'));
    s.release(); await settle();
    s.deliver(s.body); await settle();
    assert.equal(hasBox(p, 'a2'), false);
    assert.equal(p.status(), 'All changes saved');
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.deepEqual(s.writes[1], { items: { s1: { star: true } } });
  },
  async 'the hosted page hides Save a copy, Turn on saving and the browser note, and shows no reload or file-name text'() {
    const { p, s, timers } = await opened(undefined, { hold: true, echo: false });
    const seen = [];
    const look = () => { seen.push(p.status(), p.message()); assert.equal(p.el('save').hidden, true); assert.equal(p.el('browser-note').hidden, true); };
    look();
    p.typeOn('a1'); p.typeAndEnter('one'); await settle(); look();
    timers.run((x) => x.ms === 15000); await settle(); look();
    s.reject('invalid_argument'); await settle(); look();
    p.typeOn('a2'); p.typeAndEnter('two'); await settle();
    s.reject('quota_exceeded'); await settle(); look();
    s.error({ code: 'unavailable' }); await settle(); look();
    s.error({ code: 'unavailable' }); await settle(); look();
    s.error({ code: 'revoked' }); await settle(); look();
    for (const t of seen) assert.ok(!/reload|\.html|file|save a copy|turn on saving|picker|download/i.test(t), t);
    assert.equal(p.button(), '');
  },
  async 'closing the tab warns only while a change is unconfirmed'() {
    const { p, s } = await opened(undefined, { hold: true, echo: false });
    assert.equal(p.warnsOnClose(), false);
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    assert.equal(p.warnsOnClose(), true, 'an open box with new text');
    assert.equal(p.el('typing').hidden, true);
    assert.equal(s.writes.length, 1, 'closing the tab sends the open box text as one change');
    s.release(); await settle();
    assert.equal(p.warnsOnClose(), false);
  },
  async 'closing the tab warns when a write failed and the edit is not saved'() {
    const { p, s } = await opened(undefined, { refuse: ['invalid_argument'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.equal(p.warnsOnClose(), true);
  },
  async 'a box left open with unchanged text does not make closing warn'() {
    const { p } = await opened();
    p.typeOn('a1');
    assert.equal(p.warnsOnClose(), false);
  },
  async 'after a write confirms and before any snapshot shows it, the next action sends only its own change'() {
    const { p, s } = await opened(undefined, { echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'one' } } }, { items: { s1: { star: true } } }]);
    assert.ok(p.canvasText().includes('one'));
    s.deliver(s.body); await settle();
    assert.ok(p.canvasText().includes('one'));
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a confirmed change leaves the overlay when a snapshot arrives after it, even one without it'() {
    const { p, s } = await opened(undefined, { echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    assert.ok(p.canvasText().includes('one'));
    // Someone else's later write replaced it. The page shows what the store holds.
    s.remote({ items: { a1: { text: 'theirs' } } }); await settle();
    assert.ok(p.canvasText().includes('theirs'), p.canvasText());
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.deepEqual(s.writes[1], { items: { s1: { star: true } } });
  },
  async 'a cached snapshot with no map after a confirmation keeps the confirmed change in the overlay'() {
    const { p, s } = await opened(undefined, { echo: false });
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    s.deliver(null, { fromCache: true }); await settle();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'one' } } }, { items: { s1: { star: true } } }]);
  },
  async 'a cached snapshot with a map after a confirmation keeps the confirmed change too'() {
    const { p, s } = await opened(undefined, { echo: false });
    const old = json(s.body);
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    s.deliver(old, { fromCache: true }); await settle();
    assert.ok(p.canvasText().includes('one'), p.canvasText());
    s.deliver(s.body); await settle();
    assert.ok(p.canvasText().includes('one'));
  },
  async 'a pending snapshot holding a later write but not an earlier confirmed one keeps the earlier one on screen'() {
    const { p, s } = await opened(undefined, { echo: false, hold: true });
    const before = json(s.body);
    p.typeOn('a1'); p.typeAndEnter('one'); await settle();
    s.release(); await settle();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    const stale = json(before); stale.items.s1.star = true;
    s.deliver(stale, { hasPendingWrites: true }); await settle();
    assert.ok(p.canvasText().includes('one'), 'the confirmed change left the screen');
    s.release(); await settle();
    s.deliver(s.body); await settle();
    assert.ok(p.canvasText().includes('one'));
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a can that never answers falls to not told after 5 seconds, and a late false takes the controls away'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    let answer; s.user = { can: () => new Promise((r) => { answer = r; }) };
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    p.typeOn('a1');
    assert.equal(p.el('typing').hidden, true, 'editing opened before any answer');
    assert.equal(timers.has(5000), true);
    timers.run((x) => x.ms === 5000); await settle();
    p.typeOn('a1');
    assert.equal(p.el('typing').hidden, false);
    p.el('typing').value = 'half typed';
    answer(false); await settle();
    assert.equal(p.el('typing').hidden, true);
    assert.ok(/weren't saved/.test(p.message()), p.message());
    assert.equal(s.writes.length, 0);
    assert.ok(/view only/i.test(p.status()), p.status());
    assertNoEditing(p, s, 'a1');
  },
  async 'a late true after the 5 seconds keeps editing, and a refusal still decides before it'() {
    const s = fakeStore(twoItems(), { refuse: ['invalid_argument'] }); const timers = fakeTimers();
    let answer; s.user = { can: () => new Promise((r) => { answer = r; }) };
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    timers.run((x) => x.ms === 5000); await settle();
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.ok(/view only/i.test(p.status()), p.status());
    answer(true); await settle();
    assert.equal(timers.has(5000), false);
    assertNoEditing(p, s, 'a1');
  },
  async 'an answer inside 5 seconds clears the timer'() {
    const s = fakeStore(twoItems()); const timers = fakeTimers();
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear }); await settle();
    s.deliver(s.body); await settle();
    assert.equal(timers.has(5000), false);
    p.typeOn('a1'); assert.equal(p.el('typing').hidden, false);
  },
  async 'text in an open box that is thrown away because editing turned off says so'() {
    const { p, s } = await opened();
    p.typeOn('a1'); p.el('typing').value = 'half typed';
    s.remote({ version: 2 }); await settle();
    assert.equal(p.el('typing').hidden, true);
    assert.ok(/weren't saved/.test(p.message()), p.message());
    assert.ok(!/reload|file/i.test(p.message()), p.message());
  },
  async 'an unchanged open box that editing turned off shows no message'() {
    const { p, s } = await opened();
    p.typeOn('a1');
    s.remote({ version: 2 }); await settle();
    assert.equal(p.message(), '');
  },
  async 'a write rejected as revoked does not explain why'() {
    const { p } = await opened(undefined, { refuse: ['revoked'] });
    p.clickItem('s1'); p.tool('star-button'); await settle();
    assert.ok(/Can't reach the saved map/.test(p.message()), p.message());
    assert.ok(!/access/i.test(p.message()), p.message());
  },
  async 'finishing text that is exactly what the item already holds shows no notice'() {
    const { p, s } = await opened();
    p.typeOn('a1');
    s.remote({ items: { a1: { text: 'same' } } }); await settle();
    p.typeAndEnter('same'); await settle();
    assert.equal(s.writes.length, 0);
    assert.equal(p.message(), '');
  },
  async 'typing elsewhere during a held new item'() {
    const a = await opened();
    a.p.clickItem('a1'); a.p.plus('obstacle');
    const id = JSON.parse(a.p.el('canvas').walk().find((k) => k.classList.contains('selected')).dataset.ref).id;
    a.p.typeOn('a2');
    await settle();
    assert.equal(a.p.el('typing').hidden, false); assert.equal(a.p.el('typing').value, 'second');
    assert.equal(hasBox(a.p, id), false, 'the blank item stayed');
    assert.equal(a.s.writes.length, 0);

    const b = await opened();
    b.p.clickItem('a1'); b.p.plus('obstacle');
    b.p.el('typing').value = 'kept';
    b.p.typeOn('a2');
    await settle();
    assert.equal(b.p.el('typing').value, 'second');
    assert.equal(b.s.writes.length, 1);
    const ids = Object.keys(b.s.writes[0].items);
    assert.equal(ids.length, 1);
    assert.deepEqual(b.s.writes[0].items[ids[0]], { kind: 'obstacle', text: 'kept', star: false, parent: 'a1', order: 2 });
    assert.ok(b.p.canvasText().includes('kept'));
  },
  async 'dragging during a held new item'() {
    const a = await opened();
    a.p.clickItem('a1'); a.p.plus('obstacle');
    a.p.press('a2'); a.p.pointerTo('s1'); a.p.release(); a.p.clickAfter(); await settle();
    assert.deepEqual(a.s.writes, [{ items: { a2: { parent: 's1', order: 1 } } }]);

    const b = await opened();
    b.p.clickItem('a1'); b.p.plus('obstacle'); b.p.el('typing').value = 'kept';
    b.p.press('a2'); b.p.pointerTo('s1'); b.p.release(); b.p.clickAfter(); await settle();
    assert.equal(b.s.writes.length, 2);
    const ids = Object.keys(b.s.writes[0].items);
    assert.deepEqual(b.s.writes[0].items[ids[0]], { kind: 'obstacle', text: 'kept', star: false, parent: 'a1', order: 2 });
    assert.deepEqual(b.s.writes[1], { items: { a2: { parent: 's1', order: 1 } } });
  }
};

(async () => {
  let failed = 0;
  for (const name of Object.keys(flows)) {
    try { await flows[name](); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + '\n     ' + String(e.stack || e).split('\n').slice(0, 4).join('\n     ')); }
  }
  console.log(failed ? failed + ' failed' : 'all ' + Object.keys(flows).length + ' passed');
  process.exit(failed ? 1 : 0);
})();
