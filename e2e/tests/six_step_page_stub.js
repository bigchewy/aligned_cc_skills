// The stub DOM that runs the real scripts of a map page under node. six_step_hosted_flows.js drives it.
const vm = require('vm');
const assert = require('assert');

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
  insertAdjacentHTML(where, html) { this.inserted = html; }
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
}

// A function that opens one map page.
function makePage(html) {
  const script = (id) => new RegExp('<script id="' + id + '">([\\s\\S]*?)<\\/script>').exec(html)[1];
  const logicSrc = script('map-logic');
  const storeSrc = script('map-store');
  const pageSrc = script('map-page');

  function page(opts) {
    const els = {};
    const docListeners = {};
    const winListeners = {};
    const document = {
      body: new El('body'),
      get activeElement() { return El.active || this.body; },
      getElementById(id) { return els[id] || (els[id] = new El()); },
      createElement(t) { return new El(t); },
      createTextNode(t) { const n = new El('text'); n.textContent = t; return n; },
      // Only the page's list of what to hide comes here.
      querySelectorAll(s) { return s.split(',').map((part) => document.getElementById(part.trim().replace('#', ''))); },
      elementFromPoint() { return under(); },
      addEventListener(t, f, cap) { (docListeners[t] = docListeners[t] || []).push({ f, cap }); }
    };
    // The parts of the page's HTML the flows need in their real places.
    El.active = null;
    El.scroller = document.getElementById('map');
    El.scroller.appendChild(document.getElementById('canvas-frame')).appendChild(document.getElementById('canvas'));
    ['typing', 'drag-ghost', 'drop-line', 'plus-obstacle', 'plus-solution', 'item-tools', 'delete-card', 'outside-claude'].forEach((id) => {
      document.getElementById(id).hidden = true;
    });
    // What elementFromPoint finds: an item's box by id, the empty map, or nothing outside the window.
    // A box someone removed leaves the pointer over the empty map.
    let overId = undefined;
    const under = () => {
      if (overId === null) return null;
      if (overId === undefined) return document.getElementById('map');
      return findBox(overId) || document.getElementById('map');
    };
    const findBox = (id) => {
      const end = id === 'goal' ? 'goal|' : '|' + id;
      return document.getElementById('canvas').walk().find((k) => k.dataset.key && k.dataset.key.endsWith(end));
    };
    // The canvas draws at the page's zoom, so a spot on screen is its canvas position times that.
    const zoomNow = () => { const m = /scale\(([\d.]+)\)/.exec(document.getElementById('canvas').style.transform || ''); return m ? parseFloat(m[1]) : 1; };
    const onScreen = (x, y) => ({ x: x * zoomNow() - El.scroller.scrollLeft, y: y * zoomNow() - El.scroller.scrollTop });
    // The empty column between the goal and the first items is never over a box.
    const emptySpot = () => onScreen(320, 0).x;
    let lastPointer = { x: 400, y: 400 };
    const frames = new Map();
    let frameId = 0;
    const sandbox = { document, console, setTimeout: opts.setTimeout || setTimeout, clearTimeout: opts.clearTimeout || clearTimeout, Promise, JSON, Math, RegExp, Object, Array, Number, String, Boolean, decodeURIComponent, Date,
      innerWidth: 1200, innerHeight: 800,
      getComputedStyle: () => ({ paddingTop: '0', paddingBottom: '0' }),
      requestAnimationFrame(f) { frames.set(++frameId, f); return frameId; },
      cancelAnimationFrame(n) { frames.delete(n); },
      addEventListener(t, f) { (winListeners[t] = winListeners[t] || []).push(f); }
    };
    sandbox.window = sandbox;
    sandbox.globalThis = sandbox;
    if ('claude' in opts) sandbox.claude = opts.claude;
    vm.createContext(sandbox);
    vm.runInContext(logicSrc, sandbox);
    vm.runInContext(storeSrc, sandbox);
    vm.runInContext(pageSrc, sandbox);

    const api = {
      sandbox,
      status: () => document.getElementById('save-status').textContent,
      message: () => { const m = document.getElementById('message'); return m.hidden ? '' : m.textContent; },
      el(id) { return document.getElementById(id); },
      active() { return document.activeElement; },
      // Capture listeners, then the target and what holds it, then bubble listeners on the document.
      fire(target, type, more) {
        const e = Object.assign({ target, preventDefault() { e.prevented = true; }, stopPropagation() { e.stopped = true; } }, more);
        (docListeners[type] || []).filter((l) => l.cap).forEach((l) => l.f(e));
        if (e.stopped) return e;
        for (let n = target; n; n = n.parent) (n.listeners[type] || []).forEach((f) => f(e));
        (docListeners[type] || []).filter((l) => !l.cap).forEach((l) => l.f(e));
        return e;
      },
      box(id) {
        const end = id === 'goal' ? 'goal|' : '|' + id;
        const box = api.el('canvas').walk().find((k) => k.dataset.key && k.dataset.key.endsWith(end));
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
      addObstacle() { api.clickItem('goal'); api.plus('obstacle'); },
      canvasText() { return document.getElementById('canvas').textContent; },
      panelText() { return document.getElementById('panel').textContent; },
      boxes() { return document.getElementById('canvas').kids.filter((k) => k.dataset.key).map((k) => ({
        key: k.dataset.key, x: parseFloat(k.style.left), y: parseFloat(k.style.top), w: parseFloat(k.style.width), h: k.offsetHeight })); },
      resize() { winListeners.resize[0](); },
      press(id, more) { return api.fire(api.box(id), 'pointerdown', Object.assign({ button: 0, buttons: 1, clientX: 100, clientY: 100 }, more)); },
      // Where a spot on a box is on screen: a share of 0 is its top and 1 its bottom.
      spotOn(id, share) {
        const b = api.box(id);
        return onScreen(parseFloat(b.style.left) + parseFloat(b.style.width) / 2, parseFloat(b.style.top) + b.offsetHeight * share);
      },
      // Moves the pointer to the middle of an item, or over the empty map with no id, or outside the window with null.
      pointerTo(id, x, y, more) {
        overId = id;
        let spot = { x: x === undefined ? 400 : x, y: y === undefined ? 400 : y };
        if (x === undefined && id && findBox(id)) spot = api.spotOn(id, 0.5);
        else if (x === undefined) spot.x = emptySpot();
        lastPointer = spot;
        return api.fire(api.el('map'), 'pointermove', Object.assign({ buttons: 1, clientX: spot.x, clientY: spot.y }, more));
      },
      // A spot on a box, at a share of its height.
      pointerOn(id, share) { const spot = api.spotOn(id, share); return api.pointerTo(id, spot.x, spot.y); },
      // The empty space halfway between two boxes in one column.
      pointerBetween(a, b) {
        const low = api.spotOn(a, 1); const high = api.spotOn(b, 0);
        return api.pointerTo(undefined, low.x, (low.y + high.y) / 2);
      },
      // The blue line as the page placed it, or null while it is hidden.
      line() {
        const l = api.el('drop-line');
        return l.hidden ? null : { left: parseFloat(l.style.left), top: parseFloat(l.style.top), width: parseFloat(l.style.width) };
      },
      release() { return api.fire(api.el('map'), 'pointerup', { button: 0, buttons: 0, clientX: lastPointer.x, clientY: lastPointer.y }); },
      // The browser sends a click to what holds both the press and the release.
      clickAfter() { return api.fire(api.el('canvas'), 'click', { detail: 1 }); },
      dragOnto(id, targetId) { api.press(id); api.pointerTo(targetId); api.release(); api.clickAfter(); },
      runFrame() { const ids = Array.from(frames.keys()); if (!ids.length) return false; const n = ids[ids.length - 1]; const f = frames.get(n); frames.delete(n); f(); return true; },
      loseWindow() { winListeners.blur.forEach((f) => f()); },
      ghost() { return api.el('drag-ghost'); },
      // The ids of the dim boxes, and the kinds of the dim lines, as the page drew them.
      dimBoxes() { return api.el('canvas').walk().filter((k) => k.dataset.ref && k.classList.contains('drag-source')).map((k) => JSON.parse(k.dataset.ref).id).sort(); },
      dimLines() { return (api.el('canvas').inserted.match(/<path class="\w+ drag-source"/g) || []).map((m) => /"(\w+) /.exec(m)[1]).sort(); },
      // Outside Claude the page sets up no close warning, because nothing can be lost.
      warnsOnClose() { const e = { preventDefault() { e.prevented = true; } }; (winListeners.beforeunload || []).forEach((f) => f(e)); return Boolean(e.prevented); }
    };
    return api;
  }

  return page;
}

module.exports = { El, settle, makePage };
