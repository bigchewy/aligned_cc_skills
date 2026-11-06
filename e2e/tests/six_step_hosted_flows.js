// Runs the real page code of a map page as the Claude viewer would, against a fake shared data store.
// Usage: node six_step_hosted_flows.js <path to a map page>. Exits 1 if any flow fails.
// test_six_step_hosted_flows.py runs it against the template.
const fs = require('fs');
const assert = require('assert');
const vm = require('vm');
const { settle, makePage } = require('./six_step_page_stub.js');

const HTML = fs.readFileSync(process.argv[2], 'utf8');
const page = makePage(HTML);

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

// The page's own store code, so a test can build a document from a tree and read the stored document as a tree.
const storeCode = vm.createContext({});
vm.runInContext(/<script id="map-store">([\s\S]*?)<\/script>/.exec(HTML)[1], storeCode);
const Store = storeCode.MapStore;
const node = (id, text, children) => ({ id, kind: 'obstacle', text, star: false, children: children || [] });
const sol = (id, text, children, star) => ({ id, kind: 'solution', text, star: Boolean(star), children: children || [] });
const tree = (obstacles, more) => json(Store.flatten(Object.assign({ person: 'Pat', goal: { text: 'g' }, obstacles,
  key_actions: [], execute: [], feedback: { number: '', check_on: '', redraw_if: '' } }, more)));
const stored = (s) => json(Store.inflate(s.body));
function findIn(items, id) {
  for (const it of items) { if (it.id === id) return it; const hit = findIn(it.children, id); if (hit) return hit; }
  return null;
}
const selectedId = (p) => JSON.parse(p.el('canvas').walk().find((k) => k.classList.contains('selected')).dataset.ref).id;

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

const openPlan = (p) => p.sandbox.document.getElementById('toggle-plan').listeners.click[0]();
// The stub doesn't read the markup, so the window's parts are put inside it here, as the page has them.
const openAppendix = (p) => {
  const inside = p.el('appendix-window');
  if (!inside.kids.length) ['appendix-close', 'appendix-notes', 'appendix-read'].forEach((id) => inside.appendChild(p.el(id)));
  return p.fire(p.el('appendix-open'), 'click');
};

const flows = {
  async 'the appendix stays out of the way until its button is pressed'() {
    const { p } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    assert.equal(p.el('appendix-open').hidden, false);
    assert.equal(p.el('appendix-window').hidden, true);
    openPlan(p);
    assert.ok(!p.panelText().includes('Appendix'), 'the plan panel still holds the appendix');
    assert.ok(!p.panelText().includes('Old words.'));
    openAppendix(p);
    assert.equal(p.el('appendix-window').hidden, false);
    assert.equal(p.el('appendix-notes').value, 'Old words.');
  },

  async 'the button closes the window it opened'() {
    const { p } = await opened();
    openAppendix(p);
    openAppendix(p);
    assert.equal(p.el('appendix-window').hidden, true);
  },

  async 'typing in the appendix saves when they leave the box, and sends only the explanation'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    openAppendix(p);
    const box = p.el('appendix-notes');
    p.fire(box, 'focus');
    box.value = 'New words.\n\nA second note.';
    p.fire(box, 'blur');
    await settle();
    assert.deepEqual(s.writes, [{ goal: { detail: 'New words.\n\nA second note.' } }]);
    assert.equal(s.body.goal.text, 'g');
  },

  async 'an empty appendix still offers the button and a box to type in'() {
    const { p, s } = await opened();
    assert.equal(p.el('appendix-open').hidden, false);
    openAppendix(p);
    const box = p.el('appendix-notes');
    assert.equal(box.hidden, false);
    assert.equal(box.value, '');
    p.fire(box, 'focus');
    p.fire(box, 'blur');
    await settle();
    assert.deepEqual(s.writes, [], 'leaving it unchanged wrote something');
  },

  async 'clearing the appendix removes the explanation'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    openAppendix(p);
    const box = p.el('appendix-notes');
    p.fire(box, 'focus');
    box.value = '  ';
    p.fire(box, 'blur');
    await settle();
    assert.deepEqual(s.writes, [{ goal: { detail: '' } }]);
  },

  async 'Escape closes the appendix and keeps what was typed'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    openAppendix(p);
    const box = p.el('appendix-notes');
    p.fire(box, 'focus');
    box.value = 'Kept.';
    p.fire(box, 'keydown', { key: 'Escape' });
    await settle();
    assert.equal(p.el('appendix-window').hidden, true);
    assert.deepEqual(s.writes, [{ goal: { detail: 'Kept.' } }]);
  },

  async 'the Close button and a click elsewhere both close the appendix and keep what was typed'() {
    const { p, s } = await opened();
    for (const [words, close] of [
      ['By the button.', () => p.fire(p.el('appendix-close'), 'click')],
      ['By a click.', () => p.fire(p.el('map'), 'pointerdown', { button: 0 })]
    ]) {
      openAppendix(p);
      const box = p.el('appendix-notes');
      p.fire(box, 'focus');
      box.value = words;
      close();
      await settle();
      assert.equal(p.el('appendix-window').hidden, true);
      assert.equal(s.body.goal.detail, words);
    }
  },

  async 'a click inside the appendix leaves it open'() {
    const { p } = await opened();
    openAppendix(p);
    p.fire(p.el('appendix-notes'), 'pointerdown', { button: 0 });
    assert.equal(p.el('appendix-window').hidden, false);
  },

  async 'keys typed in the appendix never reach the map'() {
    const { p, s } = await opened();
    p.clickItem('a1');
    openAppendix(p);
    const box = p.el('appendix-notes');
    box.focus();
    p.fire(box, 'focus');
    const e = p.fire(box, 'keydown', { key: 'Tab' });
    assert.ok(!e.prevented, 'the map took the Tab key');
    p.fire(box, 'keydown', { key: 'Enter' });
    assert.equal(p.el('typing').hidden, true);
    assert.deepEqual(s.writes, []);
  },

  async 'a new snapshot while typing in the appendix keeps the words'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    openAppendix(p);
    const box = p.el('appendix-notes');
    box.focus();
    p.fire(box, 'focus');
    box.value = 'Half typed';
    s.remote({ items: { a9: item('obstacle', 'from someone else', 'goal', 1) } });
    await settle();
    assert.equal(box.value, 'Half typed');
    assert.equal(p.active(), box);
    assert.equal(p.el('appendix-window').hidden, false);
  },

  async 'overwriting what someone else just wrote in the appendix says so'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Old words.' } }));
    openAppendix(p);
    const box = p.el('appendix-notes');
    box.focus();
    p.fire(box, 'focus');
    box.value = 'Mine.';
    s.remote({ goal: { detail: 'Theirs.' } });
    await settle();
    box.blur();
    p.fire(box, 'blur');
    await settle();
    assert.equal(s.body.goal.detail, 'Mine.');
    assert.ok(p.el('message').textContent.includes('Your words replaced theirs'));
  },

  async 'closing the page with words in the appendix saves them and warns until they land'() {
    const { p, s } = await opened();
    s.hold = true;
    openAppendix(p);
    const box = p.el('appendix-notes');
    p.fire(box, 'focus');
    box.value = 'Typed, never left the box.';
    assert.equal(p.warnsOnClose(), true);
    assert.deepEqual(s.writes, [{ goal: { detail: 'Typed, never left the box.' } }]);
  },

  async 'a view-only person reads the appendix one paragraph at a time and gets no box'() {
    const { p } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'First part.\n\nSecond part.' } }), { can: { 'data.write': false } });
    assert.equal(p.el('appendix-open').hidden, false);
    openAppendix(p);
    assert.equal(p.el('appendix-notes').hidden, true);
    const paragraphs = p.el('appendix-read').walk().filter((k) => k.tag === 'P').map((k) => k.textContent);
    assert.deepEqual(paragraphs, ['First part.', 'Second part.']);
  },

  async 'a view-only person gets no appendix button when there is no explanation'() {
    const { p } = await opened(undefined, { can: { 'data.write': false } });
    assert.equal(p.el('appendix-open').hidden, true);
  },

  async 'editing the goal on the page sends only its text and keeps the explanation'() {
    const { p, s } = await opened(mapDoc({}, { goal: { text: 'g', detail: 'Why this matters.' } }));
    p.edit('new goal');
    await settle();
    assert.deepEqual(s.writes[s.writes.length - 1], { goal: { text: 'new goal' } });
    assert.equal(s.body.goal.detail, 'Why this matters.');
    openAppendix(p);
    assert.equal(p.el('appendix-notes').value, 'Why this matters.');
  },

  async 'opened outside Claude says the map opens inside Claude, and allows no edits'() {
    for (const opts of [{}, { claude: undefined }]) {
      const p = page(opts); await settle();
      assert.equal(p.el('outside-claude').hidden, false, 'the message is hidden');
      for (const part of ['header', 'notices', 'workspace']) assert.equal(p.el(part).hidden, true, part + ' showed');
      assert.equal(p.el('canvas').kids.length, 0, 'the map drew');
      assert.equal(p.status(), '');
      p.fire(p.el('canvas'), 'dblclick');
      assert.equal(p.el('typing').hidden, true, 'typing opened');
      assert.deepEqual(p.pluses(), [], 'a plus showed');
      assert.equal(p.el('item-tools').hidden, true, 'the toolbar showed');
      assert.equal(p.warnsOnClose(), false, 'nothing can be lost');
    }
  },
  async 'inside Claude the outside message stays hidden, even when the data can\'t open'() {
    const { p } = await opened();
    assert.equal(p.el('outside-claude').hidden, true);
    assert.equal(p.el('workspace').hidden, false);
    const q = page({ claude: { use: () => Promise.resolve(null) } }); await settle();
    assert.equal(q.el('outside-claude').hidden, true);
    assert.equal(q.status(), CANT_OPEN);
  },
  async 'window.claude with a null db shows it can\'t open and allows no edits'() {
    const claude = { use: () => Promise.resolve(null) };
    const p = page({ claude }); await settle();
    assert.equal(p.status(), CANT_OPEN);
    assertNoEditing(p);
  },
  async 'an item or plan row the page can\'t use is left out, and the rest draws'() {
    const doc = mapDoc({
      a1: item('obstacle', 'still here', 'goal', 1),
      s1: item('solution', 'a real fix', 'a1', 1),
      goal: item('obstacle', 'uses the goal id', 'goal', 2),
      'o"1': item('obstacle', 'has a quote mark', 'goal', 3),
      old: { text: 'old shape', whys: ['w'], root_cause: 'r', solution_ids: [] },
      odd: item('note', 'another kind', 'goal', 4)
    }, {
      solutions: [],
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1', 'gone', 'a1'] }],
      execute: [{ solution_id: 'gone', first_move: 'a gone move', owner: '', others_decide: '' },
        { solution_id: 'a1', first_move: 'an obstacle move', owner: '', others_decide: '' },
        { solution_id: 's1', first_move: 'a real move', owner: '', others_decide: '' }]
    });
    const { p, s } = await opened(doc);
    const seen = p.canvasText();
    assert.ok(seen.includes('still here') && seen.includes('a real fix'), seen);
    for (const gone of ['uses the goal id', 'has a quote mark', 'old shape', 'another kind']) assert.ok(!seen.includes(gone), gone);
    const panel = p.panelText();
    assert.ok(panel.includes('a real move') && panel.includes('the action'), panel);
    assert.ok(!panel.includes('a gone move') && !panel.includes('an obstacle move') && !panel.includes('undefined'), panel);
    assert.equal(p.status(), 'All changes saved');
    assert.equal(s.writes.length, 0, 'a repair was written back');
    p.typeOn('a1'); p.typeAndEnter('changed'); await settle();
    assert.deepEqual(s.writes, [{ items: { a1: { text: 'changed' } } }]);
  },
  async 'a window.claude with no use, or a use that fails, counts as can\'t open'() {
    for (const claude of [{}, { use() { throw new Error('no'); } }, { use: () => Promise.reject(new Error('no')) }]) {
      const p = page({ claude }); await settle();
      assert.equal(p.status(), CANT_OPEN);
      assertNoEditing(p);
    }
  },
  async 'no map in the data says the map isn\'t set up and allows no edits'() {
    const s = fakeStore(null); const p = page({ claude: s.claude }); await settle();
    s.deliver(null); await settle();
    assert.ok(p.status().includes("isn't set up"), p.status());
    assertNoEditing(p, s);
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
    const p = page({ claude: s.claude, setTimeout: timers.set, clearTimeout: timers.clear });
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
  async 'finishing words on an item someone deleted says it was deleted and the words were kept under the goal'() {
    const { p, s } = await opened();
    p.typeOn('s1'); p.el('typing').value = 'my words';
    assert.equal(p.message(), '');
    s.remote({ items: { s1: { __delete__: true } } }); await settle();
    assert.equal(p.message(), '', 'no notice before the words are finished');
    p.pressEnter(); await settle();
    assert.equal(p.message(), 'Someone deleted this item, so your words were kept under the goal.');
    assert.ok(p.canvasText().includes('my words'));
  },
  async 'escape after a remote delete of the item being typed on shows no notice'() {
    const { p, s } = await opened();
    p.typeOn('a2'); p.el('typing').value = 'my words';
    s.remote({ items: { a2: { __delete__: true } } }); await settle();
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(p.message(), '');
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
  async 'no state of the page says anything about reloading, a file or a copy'() {
    const { p, s, timers } = await opened(undefined, { hold: true, echo: false });
    const seen = [];
    const look = () => { seen.push(p.status(), p.message()); };
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
    // Starting the drag closes the new item and the boxes move, so the pointer moves on to s1 after that.
    a.p.press('a2'); a.p.pointerTo('s1'); a.p.pointerTo('s1'); a.p.release(); a.p.clickAfter(); await settle();
    assert.deepEqual(a.s.writes, [{ items: { a2: { parent: 's1', order: 1 } } }]);

    const b = await opened();
    b.p.clickItem('a1'); b.p.plus('obstacle'); b.p.el('typing').value = 'kept';
    b.p.press('a2'); b.p.pointerTo('s1'); b.p.pointerTo('s1'); b.p.release(); b.p.clickAfter(); await settle();
    assert.equal(b.s.writes.length, 2);
    const ids = Object.keys(b.s.writes[0].items);
    assert.deepEqual(b.s.writes[0].items[ids[0]], { kind: 'obstacle', text: 'kept', star: false, parent: 'a1', order: 2 });
    assert.deepEqual(b.s.writes[1], { items: { a2: { parent: 's1', order: 1 } } });
  },

  // Editing: selecting, typing, pluses, stars, dragging, zoom, the plan panel, deleting and focus.
  async 'an edit back to the old words during a write still goes out'() {
    const { p, s } = await opened(tree([]), { hold: true });
    p.edit('first'); await settle();
    p.edit('g'); await settle();
    assert.equal(s.writes.length, 1); assert.equal(p.status(), 'Saving...');
    s.release(); await settle();
    s.release(); await settle();
    assert.deepEqual(s.writes, [{ goal: { text: 'first' } }, { goal: { text: 'g' } }]);
    assert.equal(stored(s).goal.text, 'g'); assert.equal(p.status(), 'All changes saved');
  },
  async 'a blank new item stays out of the data until it has text'() {
    const { p, s } = await opened(tree([]));
    p.addObstacle(); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndEnter('blocker'); await settle();
    assert.equal(s.writes.length, 1); assert.equal(stored(s).obstacles[0].text, 'blocker');
  },
  async 'the star button shows on a placed solution, pressed for a star'() {
    const { p } = await opened(tree([node('o1', 'ob', [sol('s1', 'sol', [], true)])]));
    p.clickItem('s1');
    assert.equal(p.el('star-button').hidden, false);
    assert.equal(p.el('star-button').getAttribute('aria-pressed'), 'true');
    assert.equal(p.el('star-button').getAttribute('aria-label'), 'Star');
    assert.equal(p.el('star-button').textContent, '');
    p.clickItem('o1');
    assert.equal(p.el('star-button').hidden, true);
  },
  async 'the trash can asks every time, with nothing written until Delete'() {
    const { p, s } = await opened(tree([node('o1', 'plain', []), node('o2', 'first', [sol('s1', 'picked', [], true)])]));
    for (const id of ['o1', 'o2']) {
      p.clickItem(id); assert.equal(p.el('delete-card').hidden, true, id);
      p.tool('delete-item'); await settle();
      assert.equal(p.el('delete-card').hidden, false, id);
      assert.equal(s.writes.length, 0, id); assert.equal(p.status(), 'All changes saved');
      assert.ok(findIn(stored(s).obstacles, id));
    }
  },
  async 'the card says Confirm Delete and has one Delete button, with no list of effects'() {
    const { p } = await opened(tree([node('o1', 'first', [sol('s1', 'the picked fix', [], true)])], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' }]
    }));
    p.clickItem('o1'); p.tool('delete-item');
    const card = p.el('delete-card');
    assert.ok(p.el('delete-yes').getAttribute('aria-label').startsWith('Delete'));
    assert.ok(p.el('delete-yes').getAttribute('aria-label').includes('first'));
    assert.ok(card.getAttribute('aria-label').includes('first'));
    assert.equal(p.active(), p.el('delete-yes'));
    assert.equal(p.el('delete-item').hidden, false, 'the toolbar keeps its size, so the map does not jump');
    assert.equal(p.el('item-tools').classList.contains('asking'), false);
  },
  async 'Delete deletes the item and everything under it, and sends one change'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid', [node('o3', 'grandkid')]), sol('s1', 'picked', [], true)]), node('o4', 'other')], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' }]
    }));
    p.clickItem('o1'); p.tool('delete-item'); await settle();
    assert.equal(s.writes.length, 0);
    p.tool('delete-yes'); await settle();
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o4']);
    assert.deepEqual(saved.execute, []);
    assert.equal(saved.key_actions.length, 1); assert.deepEqual(saved.key_actions[0].solution_ids, []);
    assert.equal(s.writes.length, 1);
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.active(), p.box('goal'));
  },
  async 'Escape cancels, writes nothing, and puts focus back on the trash can'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'picked', [], true)])]));
    p.clickItem('o1'); p.tool('delete-item');
    p.fire(p.el('delete-yes'), 'keydown', { key: 'Escape' });
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.el('delete-item'));
    assert.equal(s.writes.length, 0);
  },
  async 'clicking elsewhere cancels and writes nothing'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]));
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
    assert.equal(s.writes.length, 0); assert.ok(findIn(stored(s).obstacles, 's1'));
  },
  async 'Enter on the focused Delete button is left to the button, and Delete then deletes'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1'); p.tool('delete-item');
    assert.equal(p.active(), p.el('delete-yes'));
    assert.ok(!p.fire(p.el('delete-yes'), 'keydown', { key: 'Enter' }).prevented, 'the page must not swallow Enter');
    assert.equal(s.writes.length, 0);
    p.fire(p.el('delete-yes'), 'click'); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['o2']); assert.equal(s.writes.length, 1);
  },
  async 'Tab and Shift+Tab stay on the Delete button while the card is open'() {
    const { p } = await opened(tree([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]));
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
    const { p } = await opened(tree([node('o1', 'first')]));
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
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'picked', [], true)])]));
    p.clickItem('o1'); p.tool('delete-item');
    p.plus('obstacle'); await settle();
    assert.equal(p.el('delete-card').hidden, true);
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    assert.equal(s.writes.length, 0); assert.ok(findIn(stored(s).obstacles, 's1'));
  },
  async 'the star button changes the star, keeps focus, and has no key in the header'() {
    const { p, s } = await opened(tree([node('o1', 'ob', [sol('s1', 'sol')])]));
    p.clickItem('s1');
    const star = p.el('star-button');
    assert.equal(star.getAttribute('aria-pressed'), 'false');
    star.focus(); p.fire(star, 'click'); await settle();
    assert.equal(s.writes.length, 1);
    assert.equal(findIn(stored(s).obstacles, 's1').star, true);
    assert.equal(star.getAttribute('aria-pressed'), 'true');
    assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('s1'), true); assert.equal(p.active(), star);
    p.fire(star, 'click'); await settle();
    assert.equal(findIn(stored(s).obstacles, 's1').star, false);
    assert.equal(star.getAttribute('aria-pressed'), 'false');
  },
  async 'a write waiting its turn never carries a blank new item'() {
    const { p, s } = await opened(tree([]), { hold: true });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.addObstacle(); await settle();
    s.release(); await settle();
    s.release(); await settle();
    assert.deepEqual(s.writes, [{ goal: { text: 'one' } }, { goal: { text: 'two' } }]);
    assert.deepEqual(stored(s).obstacles, []); assert.equal(stored(s).goal.text, 'two');
    s.hold = false;
    p.typeAndEnter('blocker'); await settle();
    assert.equal(stored(s).goal.text, 'two'); assert.equal(stored(s).obstacles[0].text, 'blocker');
    assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
  },
  async 'a write waiting its turn still goes out when a blank new item is cancelled'() {
    const { p, s } = await opened(tree([]), { hold: true });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.addObstacle(); await settle();
    p.typeAndEnter(''); await settle();
    s.release(); await settle();
    s.release(); await settle();
    assert.equal(stored(s).goal.text, 'two'); assert.deepEqual(stored(s).obstacles, []);
    assert.equal(s.writes.length, 2);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'add a sub-obstacle and see its label, and the data gets the child'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    p.typeAndEnter('why one'); await settle();
    assert.ok(p.canvasText().includes('1A'), p.canvasText());
    assert.ok(p.canvasText().includes('why one'));
    const saved = stored(s).obstacles[0];
    assert.equal(saved.children.length, 1); assert.equal(saved.children[0].text, 'why one');
    assert.deepEqual(Object.keys(saved.children[0]).sort(), ['children', 'id', 'kind', 'star', 'text']);
    assert.ok(!JSON.stringify(stored(s).obstacles).includes('1A'));
    p.clickItem(saved.children[0].id); p.plus('obstacle'); await settle();
    p.typeAndEnter('deeper'); await settle();
    assert.ok(p.canvasText().includes('1A1'), p.canvasText());
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a new obstacle and a new sub-obstacle get ids nothing else on the map uses'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o7', 'kid')])]));
    p.clickItem('o7'); p.plus('obstacle'); p.typeAndEnter('deep');
    p.addObstacle(); p.typeAndEnter('top'); await settle();
    const ids = p.el('canvas').kids.map((k) => k.dataset.ref).filter(Boolean).map(JSON.parse)
      .filter((r) => r.kind === 'obstacle').map((r) => r.id);
    assert.equal(ids.length, 4); assert.equal(new Set(ids).size, 4);
    assert.ok(ids.includes('o1') && ids.includes('o7'));
    assert.equal(s.writes.length, 2);
  },
  async 'a blank new sub-item stays out of the data until it has text'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid')])]));
    p.clickItem('o2'); p.plus('obstacle'); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(stored(s).obstacles[0].children[0].children.length, 0);
    p.typeAndEnter('now it has text'); await settle();
    assert.equal(s.writes.length, 1); assert.equal(stored(s).obstacles[0].children[0].children[0].text, 'now it has text');
  },
  async 'a blank new sub-item closed empty leaves no trace in the data or on the page'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    assert.ok(p.canvasText().includes('1A'));
    p.typeAndEnter(''); await settle();
    assert.ok(!p.canvasText().includes('1A'));
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
  },
  async 'a write waiting its turn never carries a blank new sub-item'() {
    const { p, s } = await opened(tree([node('o1', 'first')]), { hold: true });
    p.edit('one'); await settle();
    p.edit('two'); await settle();
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    s.release(); await settle();
    s.release(); await settle();
    assert.deepEqual(stored(s).obstacles[0].children, []); assert.equal(stored(s).goal.text, 'two');
    s.hold = false;
    p.typeAndEnter('kid'); await settle();
    assert.equal(stored(s).goal.text, 'two'); assert.equal(stored(s).obstacles[0].children[0].text, 'kid');
  },
  async 'delete a branch: the whole branch goes, its solutions with it, later siblings renumber'() {
    const { p, s } = await opened(tree([
      node('o1', 'first', [
        node('o2', 'kid a', [node('o3', 'grandkid', [sol('s1', 'gone with it')])]),
        node('o4', 'kid b')
      ]),
      node('o5', 'other', [sol('s2', 'stays')])
    ]));
    p.clickItem('o2');
    p.tool('delete-item'); p.tool('delete-yes'); await settle();
    const saved = stored(s);
    assert.equal(findIn(saved.obstacles, 'o2'), null); assert.equal(findIn(saved.obstacles, 's1'), null);
    assert.ok(findIn(saved.obstacles, 's2'));
    assert.ok(p.canvasText().includes('1A'), p.canvasText()); assert.ok(p.canvasText().includes('kid b'));
    assert.ok(!p.canvasText().includes('1B'));
  },
  async 'delete an item and see its plan row go, while the key action stays'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'fix it'), sol('s2', 'other fix')])], {
      key_actions: [{ text: 'the action', risk: 'low', solution_ids: ['s1', 's2'] }],
      execute: [{ solution_id: 's1', first_move: 'the first move', owner: 'o', others_decide: '' },
        { solution_id: 's2', first_move: 'the other move', owner: 'o', others_decide: '' }]
    }));
    p.sandbox.document.getElementById('toggle-plan').listeners.click[0]();
    assert.ok(p.panelText().includes('the first move'));
    p.clickItem('s1'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
    assert.ok(!p.panelText().includes('the first move'));
    assert.ok(p.panelText().includes('the other move'));
    assert.ok(p.panelText().includes('the action'));
    const saved = stored(s);
    assert.deepEqual(saved.execute.map((e) => e.solution_id), ['s2']);
    assert.deepEqual(saved.key_actions[0].solution_ids, ['s2']);
  },
  async 'add an obstacle under a solution and see its label continue the numbering'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid a'), node('o3', 'kid b', [node('o4', 'child'), sol('s1', 'the fix')])])]));
    p.clickItem('s1'); p.plus('obstacle'); await settle();
    p.typeAndEnter('in the way'); await settle();
    assert.ok(p.canvasText().includes('1B1'), p.canvasText());
    assert.ok(p.canvasText().includes('1B2'), p.canvasText());
    const under = findIn(stored(s).obstacles, 's1').children[0];
    assert.equal(under.text, 'in the way'); assert.equal(under.kind, 'obstacle');
  },
  async 'a blank new solution stays out of the data, and closing it empty leaves no trace'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('solution'); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndEnter(''); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.warnsOnClose(), false);
    assert.deepEqual(stored(s).obstacles[0].children, []);
  },
  async 'the delete control is an icon with no visible words'() {
    const { p } = await opened(tree([node('o1', 'first', [node('o2', 'a', [node('o3', 'b')]), node('o4', 'c')])]));
    for (const id of ['o1', 'o4']) {
      p.clickItem(id);
      assert.equal(p.el('delete-item').textContent, '');
      assert.equal(p.el('delete-item').getAttribute('aria-label'), 'Delete');
      assert.equal(p.el('delete-item').title, 'Delete');
    }
  },
  async 'a small press is a click and selects'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.press('o1');
    p.pointerTo('o2', 103, 103);
    assert.equal(p.ghost().hidden, true); assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release();
    p.fire(p.box('o1'), 'click', { detail: 1 }); await settle();
    assert.equal(p.isSelected('o1'), true); assert.equal(s.writes.length, 0);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['o1', 'o2']);
    p.press('o1'); p.release();
    p.fire(p.box('o1'), 'click', { detail: 2 }); p.fire(p.box('o1'), 'dblclick');
    assert.equal(p.el('typing').hidden, false); assert.equal(p.el('typing').value, 'first');
  },
  async 'dragging onto a box makes it a sub and renumbers'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'second', [node('o3', 'kid')]), node('o4', 'third')]));
    p.press('o2');
    p.pointerTo('o4');
    const spot = p.spotOn('o4', 0.5);
    assert.equal(p.ghost().hidden, false); assert.equal(p.ghost().textContent, 'second');
    assert.ok(parseFloat(p.ghost().style.left) >= spot.x); assert.ok(parseFloat(p.ghost().style.top) >= spot.y);
    assert.equal(p.box('o2').classList.contains('drag-source'), true);
    assert.equal(p.box('o4').classList.contains('drop-target'), true);
    assert.equal(p.el('canvas').contains(p.ghost()), false);
    p.pointerTo('o1');
    assert.equal(p.box('o4').classList.contains('drop-target'), false);
    assert.equal(p.box('o1').classList.contains('drop-target'), true);
    p.pointerTo('o4');
    p.release(); p.clickAfter(); await settle();
    const saved = stored(s);
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
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid')]), node('o3', 'other')]));
    p.clickItem('o3');
    p.dragOnto('o2', 'o3'); await settle();
    assert.equal(s.writes.length, 1);
    assert.equal(p.isSelected('o2'), true); assert.equal(p.isSelected('o3'), false);
    assert.equal(p.active(), p.box('o2'));
    assert.equal(p.el('item-tools').hidden, false); assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a drop holds the box it landed on still on screen'() {
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'second'), node('o3', 'third', [node('o4', 'a'), node('o5', 'b'), node('o6', 'c')])]));
    p.press('o1'); p.pointerTo('o2');
    const top = p.box('o2').getBoundingClientRect().top;
    p.release(); p.clickAfter();
    assert.equal(p.box('o2').getBoundingClientRect().top, top);
  },
  async 'an item drags onto the goal, and a solution keeps its star and what is under it'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'fix', [node('o2', 'kid')], true)])]));
    p.dragOnto('s1', 'goal'); await settle();
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1', 's1']);
    assert.equal(saved.obstacles[1].star, true); assert.equal(saved.obstacles[1].children[0].id, 'o2');
    assert.equal(p.isSelected('s1'), true);
  },
  async 'dragging onto the item\'s own parent or a descendant changes nothing'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid', [node('o3', 'grandkid')])])]));
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
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(findIn(stored(s).obstacles, 'o1').children[0].children[0].id, 'o3');
  },
  async 'escape cancels a drag with no write'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]));
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
    assert.equal(s.writes.length, 0); assert.equal(p.isSelected('o3'), true);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['o1', 'o2', 'o3']);
  },
  async 'release on empty space cancels with no write'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.press('o1'); p.pointerTo('o2'); p.pointerTo(undefined);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(p.ghost().hidden, true); assert.equal(s.writes.length, 0);
    p.press('o1'); p.pointerTo('o2'); p.pointerTo(null);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0); assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['o1', 'o2']);
  },
  async 'pointercancel, a lost window and a lost button each cancel with no write'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
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
    assert.equal(s.writes.length, 0);
  },
  async 'a drag with a blank new item open drops the blank and writes no blank'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1'); p.plus('obstacle');
    assert.ok(p.canvasText().includes('1A'));
    p.press('o2'); p.pointerTo('o1');
    assert.equal(p.el('typing').hidden, true); assert.ok(!p.canvasText().includes('New sub-obstacle'));
    assert.equal(p.box('o1').classList.contains('drop-target'), true);
    await settle(); assert.equal(s.writes.length, 0);
    p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 1);
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1']);
    assert.deepEqual(saved.obstacles[0].children.map((o) => o.id), ['o2']);
    assert.equal(p.isSelected('o2'), true);
  },
  async 'dragging the blank new item itself cancels, because finishing removes it'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1'); p.plus('obstacle');
    p.press(selectedId(p)); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true); assert.equal(p.el('typing').hidden, true);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    assert.equal(p.sandbox.document.body.classList.contains('dragging'), false);
    p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.isSelected('o1'), true);
    assert.deepEqual(stored(s).obstacles[0].children, []);
  },
  async 'a drag keeps what was typed on the item being dragged'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.typeOn('o1'); p.el('typing').value = 'better';
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.ghost().textContent, 'better'); assert.equal(p.el('typing').hidden, true);
    p.release(); p.clickAfter(); await settle();
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o2']);
    assert.equal(saved.obstacles[0].children[0].text, 'better');
  },
  async 'the click after a drag selects nothing new'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]));
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
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]));
    p.dragOnto('o1', 'o2');
    p.press('o1'); p.pointerTo('o3'); p.release();
    p.press('o3'); p.release(); p.fire(p.box('o3'), 'click', { detail: 1 });
    assert.equal(p.isSelected('o3'), true);
    p.press('o3'); p.pointerTo('o2'); p.release();
    p.fire(p.box('goal'), 'click', { detail: 0 });
    assert.equal(p.isSelected('goal'), true);
  },
  async 'the goal cannot be dragged'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.press('goal'); p.pointerTo('o1');
    assert.equal(p.ghost().hidden, true); assert.equal(p.box('o1').classList.contains('drop-target'), false);
    p.release(); p.fire(p.box('goal'), 'click', { detail: 1 }); await settle();
    assert.equal(p.isSelected('goal'), true); assert.equal(s.writes.length, 0);
  },
  async 'a press on a control starts no drag'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'fix')]), node('o2', 'other')]));
    p.clickItem('s1');
    for (const id of ['plus-obstacle', 'plus-solution', 'star-button', 'delete-item', 'typing']) {
      p.fire(p.el(id), 'pointerdown', { button: 0, buttons: 1, clientX: 100, clientY: 100 });
      p.pointerTo('o2');
      assert.equal(p.ghost().hidden, true, id); assert.equal(p.box('o2').classList.contains('drop-target'), false, id);
      p.release();
    }
    assert.equal(s.writes.length, 0); assert.equal(p.isSelected('s1'), true); assert.equal(p.el('item-tools').hidden, false);
  },
  async 'only the main button starts a drag'() {
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.press('o1', { button: 2, buttons: 2 }); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true);
  },
  async 'a drag hides the controls and clears the delete question, and cancelling brings back only the controls'() {
    const { p, s } = await opened(tree([node('o1', 'first', [sol('s1', 'picked', [], true)]), node('o2', 'other')]));
    p.clickItem('o1'); p.tool('delete-item');
    assert.equal(p.el('delete-card').hidden, false);
    p.press('o2'); p.pointerTo('o1');
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('item-tools').hidden, true); assert.deepEqual(p.pluses(), []);
    p.fire(p.box('o2'), 'keydown', { key: 'Escape' });
    assert.equal(p.el('delete-card').hidden, true); assert.equal(p.el('delete-item').hidden, false);
    assert.equal(p.isSelected('o1'), true); assert.equal(s.writes.length, 0);
  },
  async 'text cannot be selected from a press on an item'() {
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
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
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
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
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other'), node('o3', 'third')]));
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.box('o2').classList.contains('drop-target'), true);
    p.el('map').scrollTop += p.spotOn('o3', 0.5).y - p.spotOn('o2', 0.5).y;
    assert.ok(p.runFrame());
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    assert.equal(p.box('o3').classList.contains('drop-target'), true);
  },
  async 'dragging to the top quarter of a box shows the line above it and drops there'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.press('c'); p.pointerOn('b', 0.1);
    const line = p.line();
    assert.ok(line, 'no line');
    const boxAt = (id) => p.boxes().find((b) => b.key.endsWith('|' + id));
    assert.ok(line.top > boxAt('a').y + boxAt('a').h && line.top < boxAt('b').y, 'the line is not in the space');
    assert.equal(line.left, boxAt('b').x);
    assert.equal(p.box('b').classList.contains('drop-target'), false, 'a line and a highlight at once');
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(s.writes, [{ items: { c: { parent: 'goal', order: 1.5 } } }]);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'c', 'b']);
    assert.equal(p.line(), null);
    const label = (id) => p.box(id).kids[0].textContent;
    assert.deepEqual(['a', 'c', 'b'].map(label), ['1', '2', '3']);
    assert.equal(p.isSelected('c'), true); assert.equal(p.active(), p.box('c'));
    assert.equal(p.status(), 'All changes saved');
  },
  async 'dragging to the bottom quarter shows the line below it and drops there'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.press('a'); p.pointerOn('b', 0.9);
    const line = p.line();
    assert.ok(line, 'no line');
    const boxAt = (id) => p.boxes().find((b) => b.key.endsWith('|' + id));
    assert.ok(line.top > boxAt('b').y + boxAt('b').h && line.top < boxAt('c').y, 'the line is not in the space');
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(s.writes, [{ items: { a: { parent: 'goal', order: 2.5 } } }]);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['b', 'a', 'c']);
    assert.equal(p.line(), null);
  },
  async 'above the first and below the last both work, under the goal and under an item'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k1', 'kid'), node('k2', 'kid')]), node('b', 'second'), node('c', 'third')]));
    p.press('c'); p.pointerOn('a', 0.1); assert.ok(p.line()); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['c', 'a', 'b']);
    p.press('c'); p.pointerOn('b', 0.9); assert.ok(p.line()); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'b', 'c']);
    p.press('c'); p.pointerOn('k1', 0.1); assert.ok(p.line()); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(findIn(stored(s).obstacles, 'a').children.map((o) => o.id), ['c', 'k1', 'k2']);
    p.press('b'); p.pointerOn('k2', 0.9); assert.ok(p.line()); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(findIn(stored(s).obstacles, 'a').children.map((o) => o.id), ['c', 'k1', 'k2', 'b']);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a']);
  },
  async 'dragging to the middle of a box still makes a sub'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k', 'kid')]), node('b', 'second')]));
    for (const share of [0.3, 0.5, 0.7]) {
      p.press('b'); p.pointerOn('a', share);
      assert.equal(p.box('a').classList.contains('drop-target'), true, share);
      assert.equal(p.line(), null, share);
      p.fire(p.el('map'), 'keydown', { key: 'Escape' }); p.release(); p.clickAfter();
    }
    p.press('b'); p.pointerOn('a', 0.5); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(s.writes, [{ items: { b: { parent: 'a', order: 2 } } }]);
    assert.deepEqual(findIn(stored(s).obstacles, 'a').children.map((o) => o.id), ['k', 'b']);
  },
  async 'dragging into the empty space between two siblings shows the line'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k', 'kid')]), node('b', 'second'), node('c', 'third')]));
    p.press('c'); p.pointerBetween('a', 'b');
    assert.ok(p.line(), 'no line');
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'c', 'b']);
    assert.equal(findIn(stored(s).obstacles, 'a').children[0].id, 'k');
  },
  async 'a move between items brings what is under it, and leaves everyone else their subs'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('a1', 'one'), node('a2', 'two', [sol('f', 'fix')])]), node('b', 'second', [node('b1', 'other')])]));
    p.press('a2'); p.pointerOn('b', 0.1); p.release(); p.clickAfter(); await settle();
    assert.deepEqual(s.writes, [{ items: { a2: { parent: 'goal', order: 1.5 } } }]);
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['a', 'a2', 'b']);
    assert.deepEqual(findIn(saved.obstacles, 'a').children.map((o) => o.id), ['a1']);
    assert.deepEqual(findIn(saved.obstacles, 'a2').children.map((o) => o.id), ['f']);
    assert.deepEqual(findIn(saved.obstacles, 'b').children.map((o) => o.id), ['b1']);
  },
  async 'the box beside the spot holds still when a drop lands'() {
    const { p } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third', [node('k1', 'x'), node('k2', 'y'), node('k3', 'z')])]));
    p.press('c'); p.pointerOn('b', 0.1);
    const top = p.box('a').getBoundingClientRect().top;
    p.release(); p.clickAfter();
    assert.equal(p.box('a').getBoundingClientRect().top, top);
  },
  async 'the line and the middle hold at another zoom'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.fire(p.el('zoom-out'), 'click');
    p.fire(p.el('zoom-out'), 'click');
    assert.ok(p.el('canvas').style.transform.includes('0.8'), p.el('canvas').style.transform);
    p.press('c'); p.pointerOn('b', 0.5);
    assert.equal(p.box('b').classList.contains('drop-target'), true);
    p.pointerOn('b', 0.1);
    const line = p.line();
    assert.ok(line, 'no line');
    // The line sits in the frame, which isn't scaled, so the page scales its place.
    const box = p.boxes().find((b) => b.key.endsWith('|b'));
    assert.equal(line.left, box.x * 0.8); assert.equal(line.width, 240 * 0.8);
    assert.ok(line.top < box.y * 0.8 && line.top > (box.y - 18) * 0.8, 'the line is not in the space');
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'c', 'b']);
  },
  async 'a drop on its own place writes nothing'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.clickItem('a');
    const moves = [() => p.pointerOn('a', 0.9), () => p.pointerOn('c', 0.1), () => p.pointerBetween('a', 'b'), () => p.pointerBetween('b', 'c')];
    for (const move of moves) {
      p.press('b'); move();
      assert.ok(p.line(), 'no line');
      p.release(); p.clickAfter(); await settle();
      assert.equal(p.line(), null); assert.equal(p.ghost().hidden, true);
    }
    assert.equal(s.writes.length, 0);
    assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('a'), true);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'b', 'c']);
  },
  async 'no line shows inside the dragged set'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k1', 'x', [node('g1', 'deep')]), node('k2', 'y')]), node('b', 'second')]));
    p.press('a');
    const spots = [() => p.pointerOn('a', 0.1), () => p.pointerOn('a', 0.9), () => p.pointerOn('k1', 0.1), () => p.pointerOn('k1', 0.9), () => p.pointerOn('k2', 0.1), () => p.pointerOn('g1', 0.1), () => p.pointerBetween('k1', 'k2')];
    for (const spot of spots) {
      spot();
      assert.equal(p.ghost().hidden, false);
      assert.equal(p.line(), null);
      assert.ok(!['a', 'k1', 'k2', 'g1'].some((id) => p.box(id).classList.contains('drop-target')));
    }
    p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0);
  },
  async 'empty space away from a level shows no line and cancels'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k1', 'x')]), node('b', 'second', [node('k2', 'y')])]));
    p.press('b');
    p.pointerTo(undefined);
    assert.equal(p.line(), null);
    p.pointerBetween('k1', 'k2');
    assert.equal(p.line(), null, 'a line between cousins');
    p.pointerOn('a', 0.1); assert.ok(p.line());
    p.pointerTo(null); assert.equal(p.line(), null, 'a line outside the map');
    p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 0);
  },
  async 'the line clears on every way a drag ends'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    const stops = [
      () => p.fire(p.el('map'), 'keydown', { key: 'Escape' }),
      () => p.fire(p.el('map'), 'pointercancel'),
      () => p.loseWindow(),
      () => p.pointerOn('b', 0.1) && p.fire(p.el('map'), 'pointermove', { buttons: 0, clientX: 0, clientY: 0 }),
      () => { p.pointerTo(undefined); p.release(); },
      () => p.fire(p.el('zoom-out'), 'pointerdown', { button: 0, buttons: 1, clientX: 10, clientY: 10 }),
      () => { s.remote({ version: 2 }); }
    ];
    for (const stop of stops) {
      p.press('c'); p.pointerOn('b', 0.1);
      assert.ok(p.line(), 'no line');
      stop(); await settle();
      assert.equal(p.line(), null, String(stop));
      assert.equal(p.ghost().hidden, true);
      p.release(); p.clickAfter(); await settle();
    }
    assert.equal(s.writes.length, 0);
  },
  async 'the line clears when someone deletes the dragged item'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.press('c'); p.pointerOn('b', 0.1);
    s.remote({ items: { c: { __delete__: true } } }); await settle();
    assert.equal(p.line(), null); assert.equal(p.ghost().hidden, true);
    assert.equal(s.writes.length, 0);
  },
  async 'a redraw during a drag keeps the line in the space'() {
    const { p } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]));
    p.press('c'); p.pointerOn('b', 0.1);
    const before = p.line();
    p.resize();
    assert.deepEqual(p.line(), before);
    assert.equal(p.el('item-tools').hidden, true);
  },
  async 'a drop onto a box and an add send only their own item, beside a bad order and an orphan'() {
    const doc = mapDoc({ a1: item('obstacle', 'first', 'goal', 1), k1: item('obstacle', 'kid', 'a1', 'x'), a2: item('obstacle', 'second', 'goal', 2), o1: item('obstacle', 'lost', 'gone', 9) });
    const { p, s } = await opened(doc);
    p.dragOnto('a2', 'a1'); await settle();
    assert.deepEqual(s.writes, [{ items: { a2: { parent: 'a1', order: 1 } } }]);
    p.addObstacle(); p.typeAndEnter('new one'); await settle();
    assert.equal(s.writes.length, 2);
    const added = s.writes[1].items;
    assert.equal(Object.keys(added).length, 1);
    assert.equal(Object.values(added)[0].order, 10);
  },
  async 'a refused write after a placement keeps it on screen, not saved'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]), { refuse: ['invalid_argument'] });
    p.press('c'); p.pointerOn('b', 0.1); p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 1);
    assert.equal(p.status(), 'Not saved');
    assert.ok(p.message().includes('still on this page'), p.message());
    const seen = p.boxes().filter((b) => b.key !== 'goal|').sort((x, y) => x.y - y.y).map((b) => b.key.split('|')[1]);
    assert.deepEqual(seen, ['a', 'c', 'b']);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'b', 'c']);
    assert.equal(p.warnsOnClose(), true);
  },
  async 'a placement whose write fails for a while goes again and lands'() {
    const { p, s, timers } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third')]), { refuse: ['unavailable'] });
    p.press('c'); p.pointerOn('b', 0.1); p.release(); p.clickAfter(); await settle();
    assert.equal(s.writes.length, 1);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'b', 'c']);
    timers.run((t) => t.ms >= 1000 && t.ms < 2000); await settle();
    assert.equal(s.writes.length, 2);
    assert.deepEqual(s.writes[1], s.writes[0]);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'c', 'b']);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a remote delete of a neighbour during a drag doesn\'t throw'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third'), node('d', 'fourth')]));
    p.press('d'); p.pointerOn('c', 0.1);
    assert.ok(p.line());
    s.remote({ items: { b: { __delete__: true } } }); await settle();
    assert.equal(p.ghost().hidden, false, 'the drag ended');
    p.pointerOn('c', 0.1);
    assert.ok(p.line());
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'd', 'c']);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'a remote delete of the level under the line leaves the drag whole, and a drop loses nothing'() {
    const { p, s } = await opened(tree([node('a', 'first', [node('k1', 'x'), node('k2', 'y')]), node('b', 'second')]));
    p.press('b'); p.pointerOn('k1', 0.9);
    assert.ok(p.line());
    s.remote({ items: { a: { __delete__: true }, k1: { __delete__: true }, k2: { __delete__: true } } }); await settle();
    assert.equal(p.ghost().hidden, false, 'the drag ended');
    p.release(); p.clickAfter(); await settle();
    assert.equal(p.ghost().hidden, true); assert.equal(p.line(), null);
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['b']);
  },
  async 'a level reordered by someone else during a drag still lands where the line shows'() {
    const { p, s } = await opened(tree([node('a', 'first'), node('b', 'second'), node('c', 'third'), node('d', 'fourth')]));
    p.press('d'); p.pointerOn('b', 0.1);
    s.remote({ items: { c: { order: 1.5 } } }); await settle();
    p.pointerOn('b', 0.1);
    p.release(); p.clickAfter(); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['a', 'c', 'd', 'b']);
  },
  async 'a redraw during a drag keeps the dim item and the highlight'() {
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
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
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.press('o1');
    p.fire(p.el('zoom-out'), 'pointerdown', { button: 0, buttons: 1, clientX: 10, clientY: 10 });
    p.pointerTo('o2');
    assert.equal(p.ghost().hidden, true);
    assert.equal(p.box('o2').classList.contains('drop-target'), false);
    p.release(); await settle();
    assert.equal(s.writes.length, 0);
    p.press('o1'); p.pointerTo('o2');
    assert.equal(p.ghost().hidden, false);
    // The same goes for a drag whose release was lost: the next press ends it, and nothing moves.
    p.fire(p.el('zoom-out'), 'pointerdown', { button: 0, buttons: 1, clientX: 10, clientY: 10 });
    assert.equal(p.ghost().hidden, true);
    p.release(); await settle();
    assert.equal(s.writes.length, 0);
  },
  async 'a drop while a write is out goes next in the queue'() {
    const { p, s } = await opened(tree([node('a', 'A'), node('b', 'B'), node('c', 'C')]), { hold: true });
    p.typeOn('a'); p.typeAndEnter('A2'); await settle();
    assert.equal(s.writes.length, 1);
    p.dragOnto('b', 'c'); await settle();
    assert.equal(s.writes.length, 1);
    s.release(); await settle();
    assert.equal(s.writes.length, 2);
    s.release(); await settle();
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['a', 'c']);
    assert.equal(findIn(saved.obstacles, 'c').children[0].id, 'b');
    assert.equal(findIn(saved.obstacles, 'a').text, 'A2');
    assert.equal(p.status(), 'All changes saved');
  },
  async 'closing during a drag warns only for real changes and leaves the drag whole'() {
    const { p, s } = await opened(tree([node('a', 'A'), node('b', 'B'), node('c', 'C')]), { hold: true });
    p.press('b'); p.pointerTo('c');
    assert.equal(p.warnsOnClose(), false);
    assert.equal(p.ghost().hidden, false);
    p.release(); p.clickAfter(); await settle();
    p.press('c'); p.pointerTo('a');
    assert.equal(p.warnsOnClose(), true, 'the drop is still waiting for its write');
    assert.equal(p.ghost().hidden, false);
    p.fire(p.el('map'), 'keydown', { key: 'Escape' });
    assert.equal(p.ghost().hidden, true);
    s.release(); await settle();
    assert.equal(p.warnsOnClose(), false);
  },
  async 'a drag dims the whole set of sub-items and no others, and cancelling clears it'() {
    const { p, s } = await opened(tree([node('o1', 'top', [node('o2', 'kid', [node('o3', 'a'), sol('s1', 'b', [node('o4', 'c')])]), node('o5', 'next')]), node('o6', 'other')]));
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
    assert.equal(s.writes.length, 0);
    p.dragOnto('o2', 'o6'); await settle();
    assert.deepEqual(p.dimBoxes(), []); assert.deepEqual(p.dimLines(), []);
    assert.equal(s.writes.length, 1);
  },
  async 'a drag of a single item dims only that item and its own line'() {
    const { p } = await opened(tree([node('o1', 'top', [node('o2', 'kid')]), node('o3', 'other')]));
    p.press('o2'); p.pointerTo('o3');
    assert.deepEqual(p.dimBoxes(), ['o2']); assert.deepEqual(p.dimLines(), ['obstacle']);
  },
  async 'the ghost looks stacked only when items sit under the dragged item'() {
    const { p } = await opened(tree([node('o1', 'top', [node('o2', 'kid')]), node('o3', 'other')]));
    p.press('o1'); p.pointerTo('o3');
    assert.equal(p.ghost().classList.contains('stacked'), true); assert.equal(p.ghost().textContent, 'top');
    p.fire(p.el('map'), 'keydown', { key: 'Escape' }); p.release(); p.clickAfter();
    p.press('o2'); p.pointerTo('o3');
    assert.equal(p.ghost().classList.contains('stacked'), false); assert.equal(p.ghost().textContent, 'kid');
  },
  async 'a click selects and writes nothing'() {
    const { p, s } = await opened(tree([node('o1', 'first', [node('o2', 'kid')])]));
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
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
  },
  async 'selecting while a write was refused does not try the write again'() {
    const { p, s } = await opened(tree([node('o1', 'first')]), { refuse: ['invalid_argument'] });
    p.edit('x'); await settle();
    assert.equal(s.writes.length, 1); assert.equal(p.status(), 'Not saved');
    p.clickItem('o1'); p.clickItem('goal'); p.clickEmpty(); await settle();
    assert.equal(s.writes.length, 1); assert.equal(p.status(), 'Not saved');
  },
  async 'plus adds an obstacle, typing fills it, and only then the data changes'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    const text = p.el('typing');
    assert.equal(text.hidden, false); assert.equal(text.value, ''); assert.equal(p.active(), text);
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    p.typeAndEnter('  why one  '); await settle();
    assert.equal(s.writes.length, 1);
    const child = stored(s).obstacles[0].children[0];
    assert.equal(child.text, 'why one'); assert.equal(child.kind, 'obstacle');
    assert.equal(text.hidden, true);
    assert.equal(p.isSelected(child.id), true); assert.equal(p.isSelected('o1'), false);
    assert.equal(p.active(), p.box(child.id));
  },
  async 'plus adds a solution under an obstacle, and the goal plus adds at the top'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('solution'); p.typeAndEnter('the fix'); await settle();
    assert.equal(stored(s).obstacles[0].children[0].kind, 'solution');
    p.clickItem('goal'); p.plus('obstacle'); p.typeAndEnter('second'); await settle();
    assert.equal(stored(s).obstacles[1].text, 'second');
  },
  async 'a blank new item is removed when something else is selected, with no write'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    assert.ok(p.canvasText().includes('1A'));
    p.clickItem('o2'); await settle();
    assert.ok(!p.canvasText().includes('1A'));
    assert.equal(p.isSelected('o2'), true); assert.equal(p.el('typing').hidden, true);
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved'); assert.equal(p.warnsOnClose(), false);
    assert.deepEqual(stored(s).obstacles[0].children, []);
  },
  async 'selecting something else keeps text typed on a new item'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1'); p.plus('obstacle');
    p.el('typing').value = 'kept';
    p.clickItem('o2'); await settle();
    assert.equal(stored(s).obstacles[0].children[0].text, 'kept');
    assert.equal(p.isSelected('o2'), true);
  },
  async 'clicking empty space with a blank new item removes it and clears the selection'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('obstacle');
    p.clickEmpty(); await settle();
    assert.ok(!p.canvasText().includes('1A')); assert.equal(p.isSelected('o1'), false);
    assert.equal(s.writes.length, 0);
  },
  async 'escape on a new item removes it, with no write'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.plus('obstacle');
    p.el('typing').value = 'typed then dropped';
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.ok(!p.canvasText().includes('1A')); assert.ok(!p.canvasText().includes('typed then dropped'));
    assert.equal(p.el('typing').hidden, true);
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.box('o1'));
  },
  async 'escape on an existing item keeps its old text'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1');
    assert.equal(p.el('typing').value, 'first');
    p.el('typing').value = 'changed';
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(s.writes.length, 0); assert.ok(p.canvasText().includes('first'));
    assert.equal(p.isSelected('o1'), true); assert.equal(p.active(), p.box('o1'));
  },
  async 'a double-click types on an item, and clicking away keeps the text'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.typeOn('o1');
    assert.equal(p.active(), p.el('typing'));
    p.el('typing').value = 'better';
    p.clickItem('o2'); await settle();
    assert.equal(stored(s).obstacles[0].text, 'better');
    assert.equal(p.isSelected('o2'), true);
  },
  async 'clearing an existing item keeps its old text'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1'); p.typeAndEnter('   '); await settle();
    assert.equal(s.writes.length, 0); assert.ok(p.canvasText().includes('first'));
  },
  async 'shift and enter adds a line instead of finishing'() {
    const { p } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1');
    const e = p.fire(p.el('typing'), 'keydown', { key: 'Enter', shiftKey: true });
    assert.equal(p.el('typing').hidden, false); assert.ok(!e.prevented);
  },
  async 'a resize while typing keeps the text and focus'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1');
    const text = p.el('typing'); text.value = 'half typed';
    p.resize(); await settle();
    assert.equal(text.hidden, false); assert.equal(text.value, 'half typed'); assert.equal(p.active(), text);
    assert.equal(s.writes.length, 0);
    p.clickItem('goal'); p.plus('obstacle'); text.value = 'half new';
    p.resize(); await settle();
    assert.equal(text.value, 'half new'); assert.equal(p.active(), text); assert.equal(s.writes.length, 1);
  },
  async 'enter on the box of a blank new item goes back to typing, and nothing reaches the store'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.addObstacle(); await settle();
    const id = selectedId(p);
    p.box(id).focus();
    const e = p.fire(p.box(id), 'keydown', { key: 'Enter' }); await settle();
    assert.ok(e.prevented); assert.equal(p.active(), p.el('typing'));
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    p.resize(); await settle();
    assert.equal(s.writes.length, 0); assert.deepEqual(stored(s).obstacles.map((o) => o.id), ['o1']);
    assert.ok(!p.canvasText().includes('New obstacle'));
  },
  async 'enter on the box of a new item keeps what was typed'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.addObstacle(); p.el('typing').value = 'typed words';
    p.fire(p.box(selectedId(p)), 'keydown', { key: 'Enter' }); await settle();
    assert.equal(p.el('typing').value, 'typed words'); assert.equal(p.active(), p.el('typing'));
    assert.equal(s.writes.length, 0);
  },
  async 'enter on the box of an existing item keeps what was typed'() {
    const { p } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1'); p.el('typing').value = 'half typed';
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: 'Enter' }); await settle();
    assert.equal(p.el('typing').value, 'half typed'); assert.equal(p.active(), p.el('typing'));
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: ' ' }); await settle();
    assert.equal(p.el('typing').value, 'half typed'); assert.equal(p.active(), p.el('typing'));
  },
  async 'starting to type on another item finishes the open text box first'() {
    const { p, s } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.typeOn('o1'); p.el('typing').value = 'kept';
    p.fire(p.box('o2'), 'dblclick'); await settle();
    assert.equal(stored(s).obstacles[0].text, 'kept');
    assert.equal(p.el('typing').value, 'other'); assert.equal(p.isSelected('o2'), true);
    p.fire(p.el('typing'), 'keydown', { key: 'Escape' }); await settle();
    const writes = s.writes.length;
    p.clickItem('o1'); p.plus('obstacle'); await settle();
    p.fire(p.box('o2'), 'dblclick'); await settle();
    assert.equal(s.writes.length, writes); assert.equal(p.el('typing').value, 'other');
    assert.ok(!p.canvasText().includes('1A'));
  },
  async 'adding while a blank new item is open removes it, and neither blank reaches the store'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.addObstacle(); await settle();
    p.addObstacle(); await settle();
    assert.equal(s.writes.length, 0); assert.equal(p.status(), 'All changes saved');
    p.typeAndEnter('second'); await settle();
    assert.deepEqual(stored(s).obstacles.map((o) => o.text), ['first', 'second']);
  },
  async 'escape cancels typing even after focus left the text box'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1'); p.el('typing').value = 'changed';
    p.box('o1').focus();
    p.fire(p.box('o1'), 'keydown', { key: 'Escape' }); await settle();
    assert.equal(p.el('typing').hidden, true); assert.equal(s.writes.length, 0);
    assert.ok(p.canvasText().includes('first')); assert.equal(p.isSelected('o1'), true);
  },
  async 'escape on a new item returns focus to its parent'() {
    const { p } = await opened(tree([node('o1', 'first', [sol('s1', 'fix')])]));
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
    const { p, s } = await opened(tree([]));
    assert.equal(p.el('first-hint').hidden, false); assert.equal(p.el('edit-hint').hidden, true);
    p.clickItem('goal');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    p.plus('obstacle'); p.typeAndEnter('the first one'); await settle();
    const saved = stored(s);
    assert.equal(saved.obstacles.length, 1); assert.equal(saved.obstacles[0].text, 'the first one');
    assert.ok(p.canvasText().includes('1'), p.canvasText());
    assert.equal(p.el('first-hint').hidden, true); assert.equal(p.el('edit-hint').hidden, false);
    assert.equal(p.status(), 'All changes saved');
  },
  async 'add the first solution on an empty map from the goal'() {
    const { p, s } = await opened(tree([]));
    p.clickItem('goal'); p.plus('solution'); p.typeAndEnter('a fix first'); await settle();
    const saved = stored(s);
    assert.equal(saved.obstacles[0].kind, 'solution'); assert.equal(saved.obstacles[0].text, 'a fix first');
    assert.equal(p.el('first-hint').hidden, true);
    assert.ok(p.canvasText().includes('a fix first'), p.canvasText());
  },
  async 'a solution on the goal has a star, both pluses and delete, and drags onto an obstacle'() {
    const { p, s } = await opened(tree([node('o1', 'first'), sol('s1', 'on the goal')]));
    p.clickItem('s1');
    assert.equal(p.el('star-button').hidden, false);
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('delete-item').hidden, false);
    p.dragOnto('s1', 'o1'); await settle();
    const saved = stored(s);
    assert.deepEqual(saved.obstacles.map((o) => o.id), ['o1']); assert.equal(saved.obstacles[0].children[0].id, 's1');
    assert.equal(p.isSelected('s1'), true);
  },
  async 'the plan panel draws a solution on the goal and a solution under a solution'() {
    const { p } = await opened(tree([node('o1', 'first', [sol('s1', 'outer', [sol('s2', 'inner')])]), sol('s3', 'on the goal')],
      { execute: [{ solution_id: 's2', first_move: 'm', owner: '', others_decide: '' }, { solution_id: 's3', first_move: 'n', owner: '', others_decide: '' }] }));
    assert.ok(p.panelText().includes('inner (1)'), p.panelText());
    assert.ok(p.panelText().includes('on the goal'), p.panelText());
    assert.ok(!p.panelText().includes('undefined'), p.panelText());
  },
  async 'a solution shows both pluses, and a solution can go under a solution'() {
    const { p } = await opened(tree([node('o1', 'first', [sol('s1', 'the fix')])]));
    p.clickItem('s1');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the fix');
    assert.equal(p.el('plus-solution').getAttribute('aria-label'), 'Add a solution under the fix');
    p.plus('solution'); p.typeAndEnter('nested');
    assert.equal(p.canvasText().includes('nested'), true);
  },
  async 'the goal shows both pluses and no toolbar'() {
    const { p } = await opened(tree([node('o1', 'first')]));
    p.clickItem('goal');
    assert.deepEqual(p.pluses(), ['obstacle', 'solution']);
    assert.equal(p.el('plus-obstacle').getAttribute('aria-label'), 'Add an obstacle under the goal');
    assert.equal(p.el('plus-solution').getAttribute('aria-label'), 'Add a solution under the goal');
    assert.equal(p.el('item-tools').hidden, true);
  },
  async 'selection returns focus after a render'() {
    const { p } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1');
    const before = p.box('o1');
    assert.equal(p.active(), before);
    p.resize();
    assert.notEqual(p.box('o1'), before);
    assert.equal(p.active(), p.box('o1')); assert.equal(p.isSelected('o1'), true);
  },
  async 'a render leaves focus on a header button'() {
    const { p } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1');
    const zoom = p.el('zoom-in'); zoom.focus();
    p.fire(zoom, 'click');
    assert.equal(p.active(), zoom); assert.equal(p.isSelected('o1'), true);
  },
  async 'the keyboard selects, types and clears'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    const enter = p.fire(p.box('o1'), 'keydown', { key: 'Enter' });
    assert.ok(enter.prevented); assert.equal(p.isSelected('o1'), true); assert.equal(p.el('typing').hidden, true);
    p.fire(p.box('o1'), 'keydown', { key: 'Enter' });
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    p.typeAndEnter('new words'); await settle();
    assert.equal(stored(s).obstacles[0].text, 'new words');
    assert.equal(p.el('typing').hidden, true); assert.equal(p.active(), p.box('o1'));
    p.fire(p.box('o1'), 'keydown', { key: 'Escape' });
    assert.equal(p.isSelected('o1'), false); assert.equal(p.active(), p.box('o1'));
    p.fire(p.box('o1'), 'keydown', { key: ' ' });
    assert.equal(p.isSelected('o1'), true); assert.equal(p.el('typing').hidden, true);
  },
  async 'tab goes from the selected item through its controls to the next item'() {
    const { p } = await opened(tree([node('o1', 'first'), node('o2', 'other')]));
    p.clickItem('o1');
    const tab = (target, shiftKey) => p.fire(target, 'keydown', { key: 'Tab', shiftKey });
    assert.ok(tab(p.box('o1')).prevented); assert.equal(p.active(), p.el('plus-obstacle'));
    assert.ok(!tab(p.el('plus-obstacle')).prevented);
    assert.ok(tab(p.el('plus-obstacle'), true).prevented); assert.equal(p.active(), p.box('o1'));
    p.el('delete-item').focus();
    assert.ok(tab(p.el('delete-item')).prevented); assert.equal(p.active(), p.box('o2'));
  },
  async 'the selected item stays in the same place on screen after a render'() {
    const { p } = await opened(tree([node('o1', 'first', [node('o2', 'kid')]), node('o3', 'other')]));
    p.clickItem('o1');
    const top = p.box('o1').getBoundingClientRect().top;
    const y = parseFloat(p.box('o1').style.top);
    p.plus('obstacle');
    assert.notEqual(parseFloat(p.box('o1').style.top), y);
    assert.equal(p.box('o1').getBoundingClientRect().top, top);
  },
  async 'controls follow the item, and hide when it scrolls out of the map'() {
    const { p } = await opened(tree([node('o1', 'first')]));
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
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1'); p.tool('delete-item'); p.tool('delete-yes'); await settle();
    assert.deepEqual(stored(s).obstacles, []);
    assert.deepEqual(p.pluses(), []); assert.equal(p.el('item-tools').hidden, true);
    assert.equal(p.active(), p.box('goal'));
  },
  async 'the plan panel names items by label'() {
    const { p } = await opened(tree([node('o1', 'first', [node('o2', 'kid', [sol('s1', 'sol', [], true)])])],
      { key_actions: [{ text: 'act', risk: 'low', solution_ids: ['s1'] }],
        execute: [{ solution_id: 's1', first_move: 'm', owner: 'o', others_decide: '' }] }));
    assert.ok(p.panelText().includes('sol (1A)'), p.panelText());
  },
  async 'the wide map draws every box apart from every other, right of the goal'() {
    const { p } = await opened(tree([
      node('a1', 'x', [node('a2', 'y', [node('a3', 'z', [node('a4', 'w', [sol('s1', 'sol')]), sol('s2', 'sol')]), sol('s3', 'sol')]), node('a5', 'v', [sol('s4', 'sol', [node('a6', 'u')])])]),
      node('b1', 'x', [node('b2', 'y'), node('b3', 'z'), node('b4', 'w'), node('b5', 'v')]),
      node('c1', 'x', [sol('s5', 'sol')])
    ]));
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
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.typeOn('o1');
    p.el('typing').value = 'half typed';
    p.fire(p.el('typing'), 'mousedown');
    p.fire(p.el('map'), 'click', { detail: 1 }); await settle();
    assert.equal(p.el('typing').hidden, false); assert.equal(p.el('typing').value, 'half typed');
    assert.equal(s.writes.length, 0);
    p.fire(p.el('map'), 'click', { detail: 1 }); await settle();
    assert.equal(p.el('typing').hidden, true); assert.equal(stored(s).obstacles[0].text, 'half typed');
  },
  async 'the second click of a double-click on a plus does not close the new item'() {
    const { p, s } = await opened(tree([node('o1', 'first')]));
    p.clickItem('o1');
    p.fire(p.el('plus-solution'), 'click', { detail: 1 });
    assert.equal(p.el('typing').hidden, false);
    p.fire(p.el('map'), 'click', { detail: 2 }); await settle();
    assert.equal(p.el('typing').hidden, false); assert.equal(p.active(), p.el('typing'));
    p.typeAndEnter('a fix'); await settle();
    assert.equal(stored(s).obstacles[0].children[0].text, 'a fix');
  },
  async 'editing the goal sends one sentence and nothing else'() {
    const { p, s } = await opened(tree([]));
    p.edit('80% in-office attendance by end of Q2, up from 40%'); await settle();
    assert.deepEqual(stored(s).goal, { text: '80% in-office attendance by end of Q2, up from 40%' });
    p.openGoal();
    assert.equal(p.el('typing').value, '80% in-office attendance by end of Q2, up from 40%');
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
