// Promptfoo assertion for scenarios/use-framework/6-step-process-artifact-write.yaml.
//
// The eval provider has no tools, so Claude writes out the ArtifactData batch it would send.
// This applies that batch to a fake store with the tool's own refusals, runs the template's
// MapStore.inflate and label code on the result, and checks the reply. Score 5 or 1, on the
// 1 to 5 scale the other scenarios use.
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(__dirname, '..', '..');
const TEMPLATE = path.join(REPO, 'frameworks', '6-step-process', 'mind-map-template.html');
const SEED = path.join(REPO, 'e2e', 'fixtures', 'six-step-map', 'seed.json');

const NEW_TEXT = 'Nobody has said which days count';
const MAY_TOUCH = ['bb1', 'cc1', 'dd1', 'xx1', 'zz9'];
const EXPECTED_LABELS = [
  ['1', "People don't want to commute"],
  ['1A', "The value of the office hasn't kept up"],
  ['1A1', "We haven't defined what the office is for"],
  ['2', 'Expectations are unclear'],
  ['2A', NEW_TEXT],
  ['3', 'The open-plan floor is too noisy'],
  ['4', "Some managers aren't enforcing the policy"],
  ['5', 'The commute got longer'],
];

function pageCode() {
  const html = fs.readFileSync(TEMPLATE, 'utf8');
  const context = vm.createContext({});
  ['map-logic', 'map-store'].forEach((id) => {
    const found = html.match(new RegExp('<script id="' + id + '">([\\s\\S]*?)</script>'));
    vm.runInContext(found[1], context);
  });
  return { L: context.MapLogic, S: context.MapStore };
}

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

// Key order doesn't matter when two documents are compared.
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    const out = {};
    Object.keys(value).sort().forEach((key) => { out[key] = canonical(value[key]); });
    return out;
  }
  return value;
}

function same(a, b) {
  return JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
}

function hasDeleteMarker(value) {
  if (Array.isArray(value)) return value.some(hasDeleteMarker);
  if (value && typeof value === 'object') {
    return value.__delete__ === true || Object.values(value).some(hasDeleteMarker);
  }
  return false;
}

function hasMarkerInList(value, inList) {
  if (Array.isArray(value)) return value.some((v) => hasMarkerInList(v, true));
  if (value && typeof value === 'object') {
    if (inList && value.__delete__ === true) return true;
    return Object.values(value).some((v) => hasMarkerInList(v, inList));
  }
  return false;
}

function findCall(output) {
  const blocks = [...output.matchAll(/```(?:json)?\s*\n([\s\S]*?)```/g)];
  for (let i = blocks.length - 1; i >= 0; i -= 1) {
    try {
      const parsed = JSON.parse(blocks[i][1]);
      if (parsed && typeof parsed === 'object') {
        return { call: parsed, words: output.replace(/```[\s\S]*?```/g, '') };
      }
    } catch (e) { /* not this block */ }
  }
  return null;
}

// What the real tool refuses, it refuses here, and nothing is written.
function applyBatch(seed, S, writes) {
  const store = {
    main: { doc: plain(seed.main), version: seed.main_version },
    baseline: { doc: plain(seed.baseline), version: seed.baseline_version },
  };
  for (const write of writes) {
    const target = store[write.doc_id];
    if (write.collection !== 'maps' || !target) return { refused: 'unknown document ' + write.collection + '/' + write.doc_id };
    if (write.if_version === undefined) return { refused: 'a write to ' + write.doc_id + ' has no if_version' };
    if (write.if_version !== target.version) return { refused: 'version_mismatch on ' + write.doc_id };
    if (!write.data || typeof write.data !== 'object' || Array.isArray(write.data)) {
      return { refused: 'a write to ' + write.doc_id + ' has no data object: ' + JSON.stringify(write).slice(0, 300) };
    }
    if (write.op === 'set' && hasDeleteMarker(write.data)) return { refused: '__delete__ in a set on ' + write.doc_id };
    if (hasMarkerInList(write.data, false)) return { refused: '__delete__ inside a list on ' + write.doc_id };
    if (write.op !== 'set' && write.op !== 'update') return { refused: 'unknown op ' + write.op };
  }
  for (const write of writes) {
    const target = store[write.doc_id];
    target.doc = write.op === 'set' ? plain(write.data) : plain(S.overlay(target.doc, [write.data]));
  }
  return { main: store.main.doc, baseline: store.baseline.doc };
}

function checkMainWrite(write, seed, problems) {
  if (!write) {
    problems.push('the batch has no write to maps/main');
    return;
  }
  if (write.op !== 'update') {
    problems.push('maps/main must be an update that sends only what changed, not a ' + write.op);
    return;
  }
  const data = write.data || {};
  Object.keys(data).forEach((key) => {
    if (!['items', 'key_actions', 'execute'].includes(key)) problems.push('the update names ' + key + ', which did not change');
  });
  Object.keys(data.items || {}).forEach((id) => {
    if (id in seed.main.items && !MAY_TOUCH.includes(id)) problems.push('the update names item ' + id + ', which is unchanged');
  });
}

function checkItems(main, seed, problems) {
  const items = main.items || {};
  if (main.version !== 1) problems.push('the version field is ' + main.version + ', not 1');
  ['cc1', 'dd1', 'xx1'].forEach((id) => {
    if (id in items) problems.push('removed item ' + id + ' is still in items');
  });
  const moved = items.bb1 || {};
  if (moved.parent !== 'goal') problems.push('bb1 was not moved directly under the goal');
  if (moved.text !== seed.main.items.bb1.text) problems.push('the move changed the text of bb1');
  Object.keys(seed.main.items).forEach((id) => {
    if (MAY_TOUCH.includes(id)) return;
    if (!same(items[id], seed.main.items[id])) problems.push('item ' + id + ' changed but should not have');
  });
  const added = Object.keys(items).filter((id) => !(id in seed.main.items));
  added.forEach((id) => {
    if (!/^[a-z0-9]+$/.test(id)) problems.push('new item id ' + id + ' is not lowercase letters and digits');
  });
  const fresh = added.filter((id) => items[id].text === NEW_TEXT);
  if (fresh.length !== 1 || added.length !== 1) {
    problems.push('expected exactly one new item with the asked text, found ' + added.length);
    return;
  }
  const item = items[fresh[0]];
  if (item.kind !== 'obstacle') problems.push('the new item is not an obstacle');
  if (item.parent !== 'aa2') problems.push('the new item is not under Expectations are unclear');
  if (item.star !== false) problems.push('the new item needs star false');
  if (typeof item.order !== 'number') problems.push('the new item needs a number in order');
}

function checkRows(main, seed, problems) {
  if (!same(main.execute, [seed.main.execute[0]])) {
    problems.push('execute should hold only the row for ee1: ' + JSON.stringify(main.execute));
  }
  const expected = [
    Object.assign({}, seed.main.key_actions[0], { solution_ids: ['ee1'] }),
    Object.assign({}, seed.main.key_actions[1], { solution_ids: [] }),
    Object.assign({}, seed.main.key_actions[2], { solution_ids: [] }),
  ];
  if (!same(main.key_actions, expected)) {
    problems.push('key_actions should keep all three with gone ids taken out: ' + JSON.stringify(main.key_actions));
  }
}

function checkInflate(main, code, problems) {
  const map = plain(code.S.inflate(main));
  if (code.S.unknownVersion(main)) problems.push('the page would refuse this version field');
  const ids = plain(code.L.itemLabels(map));
  const byText = {};
  (function walk(list) {
    list.forEach((item) => {
      if (ids[item.id]) byText[item.text] = ids[item.id];
      walk(item.children);
    });
  }(map.obstacles));
  const expected = {};
  EXPECTED_LABELS.forEach(([label, text]) => { expected[text] = label; });
  if (!same(byText, expected)) problems.push('the page draws different labels than expected: ' + JSON.stringify(byText));
}

function checkWords(words, problems) {
  const lines = words.split('\n');
  EXPECTED_LABELS.forEach(([label, text]) => {
    const pattern = new RegExp('(^|[^A-Za-z0-9])' + label + '([^A-Za-z0-9]|$)');
    const stated = lines.some((line) => line.toLowerCase().includes(text.toLowerCase()) && pattern.test(line));
    if (!stated) problems.push('the reply is missing labels: ' + label + ' for "' + text + '"');
  });
  if (!/pulse survey/i.test(words) || !/loud|renam|reword|now reads|now says/i.test(words)) {
    problems.push('the reply does not report the edits Claude did not make');
  }
}

module.exports = function scoreMapWrite(output) {
  const seed = JSON.parse(fs.readFileSync(SEED, 'utf8'));
  const code = pageCode();
  const fail = (problems) => ({ pass: false, score: 1, reason: problems.join('; ') });

  const found = findCall(String(output));
  if (!found) return fail(['no JSON block with the ArtifactData call']);
  const { call, words } = found;
  if (call.action !== 'batch' || !Array.isArray(call.writes)) return fail(['the call is not a batch']);

  const applied = applyBatch(seed, code.S, call.writes);
  if (applied.refused) return fail(['the tool would refuse this: ' + applied.refused]);

  const problems = [];
  checkMainWrite(call.writes.find((w) => w.doc_id === 'main'), seed, problems);
  if (!call.writes.some((w) => w.doc_id === 'baseline')) {
    problems.push('the batch has no write to maps/baseline');
  } else if (!same(applied.baseline, applied.main)) {
    problems.push('maps/baseline does not match maps/main after the batch');
  }
  checkItems(applied.main, seed, problems);
  checkRows(applied.main, seed, problems);
  checkInflate(applied.main, code, problems);
  checkWords(words, problems);

  if (problems.length) return fail(problems);
  return { pass: true, score: 5, reason: 'All checks passed.' };
};
