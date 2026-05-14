#!/usr/bin/env node
// Generates an HTML triage view of the Kanban board for this repo.
//
// Reads docs/kanban/{todo,in-progress,done,did_not_complete}/*.md and produces
// docs/kanban/board.html with a per-item action dropdown (Resolve / Close /
// Defer), a hard-coded pre-flight staleness/RCA prompt, and an auto-generated
// action prompt that runs /aligned:root-cause-analysis before any work.
//
// Both prompts live in collapsed boxes by default; "View / edit" opens a
// modal dialog with the full editable textarea.
//
// Run: node scripts/generate-kanban-board.cjs
// Then: open docs/kanban/board.html
//
// Designed to be repo-portable.

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const KANBAN_DIR = path.join(REPO_ROOT, 'docs', 'kanban');
const COLUMNS = ['todo', 'in-progress', 'done', 'did_not_complete'];
const OUTPUT = path.join(KANBAN_DIR, 'board.html');

const SEVERITY_RANK = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, '': 4 };

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function parseKbFile(content) {
  const titleMatch = content.match(/^#\s+(KB-\d+):\s*(.+)$/m);
  const id = titleMatch ? titleMatch[1] : null;
  const title = titleMatch ? titleMatch[2].trim() : 'Untitled';

  const fields = {};
  const re = /^-\s+\*\*([^:]+):\*\*\s*(.+)$/gm;
  let m;
  while ((m = re.exec(content))) {
    fields[m[1].trim().toLowerCase()] = m[2].trim();
  }

  const stripBackticks = s => (s || '').replace(/`/g, '');
  const severity = (fields['severity'] || 'MEDIUM').toUpperCase().replace(/[^A-Z]/g, '');

  return {
    id,
    title,
    type: fields['type'] || '',
    discoveredDuring: fields['discovered during'] || '',
    location: stripBackticks(fields['location']),
    observed: fields['observed'] || '',
    expected: fields['expected'] || '',
    whyOutOfScope: fields['why out of scope'] || '',
    severity: SEVERITY_RANK.hasOwnProperty(severity) ? severity : 'MEDIUM',
    created: fields['created'] || '',
  };
}

function listItems(column) {
  const dir = path.join(KANBAN_DIR, column);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.md') && f.startsWith('KB-'))
    .map(f => {
      const content = fs.readFileSync(path.join(dir, f), 'utf8');
      return { file: `docs/kanban/${column}/${f}`, ...parseKbFile(content) };
    });
}

function ageDays(createdStr) {
  if (!createdStr) return null;
  const d = Date.parse(createdStr);
  if (Number.isNaN(d)) return null;
  return Math.floor((Date.now() - d) / 86400000);
}

function kbDefaultDecision(item) {
  const age = ageDays(item.created);
  const ageHint = age != null ? `${age} days old` : 'unknown age';
  const titleLower = (item.title || '').toLowerCase();

  if (/\borphan(ed)?\b|\bdead code\b|\bstale\b/.test(titleLower) && (age == null || age > 30)) {
    return { decision: 'close',
             rationale: `${ageHint}. Title suggests an orphan/dead-code/stale cleanup — likely already swept up in later work. Verify in the pre-flight, then close if no longer present.` };
  }

  if (item.severity === 'CRITICAL') {
    return { decision: 'resolve',
             rationale: `${ageHint}. CRITICAL severity — resolve now regardless of age.` };
  }

  if (item.severity === 'HIGH') {
    if (age != null && age > 45) {
      return { decision: 'defer',
               rationale: `${ageHint}. HIGH severity but old — run the pre-flight RCA first; the code may have moved or the issue may already be fixed.` };
    }
    return { decision: 'resolve',
             rationale: `${ageHint}. HIGH severity and recent — resolve in this round.` };
  }

  if (item.severity === 'MEDIUM') {
    return { decision: 'defer',
             rationale: `${ageHint}. MEDIUM severity — defer to a focused cleanup pass; not urgent enough to interrupt feature work.` };
  }

  return { decision: 'defer',
           rationale: `${ageHint}. LOW severity — defer indefinitely; pull only when batching cleanup.` };
}

function severityRank(s) { return SEVERITY_RANK[s] ?? 4; }

const PREFLIGHT_PROMPT = `For every item in docs/kanban/todo/, run a root cause analysis to confirm the item is still valid AND that its proposed solution is still the right fix. Assume nothing — items may have been resolved incidentally by parallel work, or the proposed solution may no longer fit the current code shape.

For each KB-XXX.md:

1. Read the markdown. Capture: Observed problem, Expected solution, Location(s), Severity, Created date.

2. Invoke the /aligned:root-cause-analysis skill with the Observed problem as the problem statement. Have the RCA:
   a. Verify the issue is reproducible in the current code at the stated Location (or wherever it has moved to).
   b. Trace whether the underlying cause is still present. Pay special attention to commits made after the item's Created date that touched the same files — the issue may have been fixed incidentally by parallel work. Use git log --since="<Created date>" -- <Location> as a starting probe.
   c. Evaluate whether the Expected solution still makes sense given the current code structure. The file may have been split, the function renamed, the abstraction reworked — in which case the original solution doesn't apply even if the underlying problem still does.

3. Based on the RCA, classify the item and act:

   - **still-valid-as-written**: Issue confirmed, proposed solution still correct. Leave the markdown in docs/kanban/todo/ untouched.

   - **still-valid-but-update-solution**: Issue confirmed but the Expected field is outdated. Edit the markdown in place — update Expected, Location, Severity as needed. Add a "**Revised:** <date>" line explaining what changed. Leave in docs/kanban/todo/.

   - **resolved-incidentally**: Issue is no longer present in current code. Move the markdown from docs/kanban/todo/ to docs/kanban/done/. Append a one-line note: "**Closed by RCA <date>:** Resolved incidentally by <commit-sha or branch/feature-name> — <one-sentence reason>".

   - **no-longer-relevant**: Issue can no longer be reproduced AND can't be tied to a specific resolving commit (file deleted, scope changed, refactored away, dependency removed). Move to docs/kanban/did_not_complete/. Append: "**Closed by RCA <date>:** No longer relevant — <one-sentence reason>".

4. Do NOT implement any fixes in this pass. This pass is validation only — update cards, move cards, but don't touch the source files the cards reference.

5. At the end, print a summary table with columns: ID | classification | one-line reason. Also report totals (X still valid as-written, Y solution updated, Z resolved incidentally, W no longer relevant).

When you're done I'll regenerate the board (node scripts/generate-kanban-board.cjs) and triage the survivors.`;

function renderHtml() {
  const todo = listItems('todo')
    .sort((a, b) => severityRank(a.severity) - severityRank(b.severity)
                 || (a.id || '').localeCompare(b.id || ''));
  const counts = Object.fromEntries(COLUMNS.map(c => [c, listItems(c).length]));

  const enriched = todo.map((item, i) => {
    const { decision, rationale } = kbDefaultDecision(item);
    return { ...item, idx: `k${i}`, defaultDecision: decision, rationale, age: ageDays(item.created) };
  });

  const generatedAt = new Date().toISOString().slice(0, 16).replace('T', ' ');

  const tableRows = enriched.map(item => `
    <tr data-idx="${item.idx}" class="sev-${item.severity.toLowerCase()} chose-${item.defaultDecision} clickable-row" title="Click to view full card">
      <td><span class="badge sev-${item.severity.toLowerCase()}-badge">${item.severity}</span></td>
      <td class="id-cell"><a href="${escapeHtml(item.file)}" target="_blank">${escapeHtml(item.id || '?')}</a></td>
      <td class="title-cell">
        <div class="kb-title">${escapeHtml(item.title)}</div>
        <div class="kb-observed">${escapeHtml(item.observed).slice(0, 240)}${item.observed.length > 240 ? '&hellip;' : ''}</div>
      </td>
      <td class="type-cell">${escapeHtml(item.type)}</td>
      <td class="loc-cell"><code>${escapeHtml(item.location || '—')}</code></td>
      <td class="age-cell">${item.age != null ? item.age + 'd' : '?'}</td>
      <td class="rationale-cell"><small>${escapeHtml(item.rationale)}</small></td>
      <td class="action-cell">
        <select class="action-select" data-idx="${item.idx}">
          <option value="resolve"${item.defaultDecision === 'resolve' ? ' selected' : ''}>Resolve now</option>
          <option value="close"${item.defaultDecision === 'close' ? ' selected' : ''}>Close as stale</option>
          <option value="defer"${item.defaultDecision === 'defer' ? ' selected' : ''}>Defer</option>
        </select>
      </td>
    </tr>`).join('');

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kanban Board — ${escapeHtml(path.basename(REPO_ROOT))}</title>
<style>
  :root {
    --bg: #0f1115; --panel: #1a1d24; --border: #2a2f3a;
    --text: #e6e8ec; --muted: #8b919e;
    --resolve: #2f9e44; --close: #6741d9; --defer: #868e96;
    --critical: #c92a2a; --high: #e8590c; --medium: #d4a017; --low: #4dabf7;
    --info: #4dabf7;
  }
  @media (prefers-color-scheme: light) {
    :root { --bg: #f7f8fa; --panel: #ffffff; --border: #e1e4e8; --text: #1a1d24; --muted: #6a737d; }
  }
  * { box-sizing: border-box; }
  body { font: 14px/1.5 -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
         background: var(--bg); color: var(--text); margin: 0; padding: 32px; max-width: 1200px; margin: 0 auto; }
  h1 { font-size: 22px; margin: 0 0 4px; font-weight: 600; }
  h2 { font-size: 16px; margin: 32px 0 12px; font-weight: 600; }
  .meta { color: var(--muted); margin: 0 0 24px; font-size: 13px; }
  .meta code { background: var(--panel); padding: 1px 5px; border-radius: 3px; font-size: 11px; }
  .column-counts { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .col-stat { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; min-width: 110px; }
  .col-stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
  .col-stat-value { font-size: 20px; font-weight: 600; margin-top: 2px; }

  /* Compact prompt box */
  .prompt-card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin: 16px 0; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .prompt-card.preflight { border-left: 3px solid var(--info); }
  .prompt-card.action    { border-left: 3px solid var(--resolve); }
  .prompt-card .label { flex: 1; min-width: 260px; }
  .prompt-card .label .title { font-weight: 600; font-size: 13px; margin: 0 0 2px; }
  .prompt-card .label .hint  { color: var(--muted); font-size: 12px; margin: 0; }
  .prompt-card .actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
  .prompt-card button { font-size: 12px; padding: 6px 12px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-weight: 600; }
  .prompt-card button:hover { background: var(--panel); border-color: var(--muted); }
  .prompt-card .btn-primary { background: var(--info); border-color: var(--info); color: white; }
  .prompt-card .btn-primary:hover { filter: brightness(1.1); }
  .copy-status { color: var(--resolve); font-size: 12px; opacity: 0; transition: opacity 0.2s; }
  .copy-status.visible { opacity: 1; }

  /* Modal dialog */
  dialog.prompt-dialog { width: min(900px, 90vw); max-height: 85vh; padding: 0; border: 1px solid var(--border); border-radius: 10px; background: var(--panel); color: var(--text); }
  dialog.prompt-dialog::backdrop { background: rgba(0,0,0,0.55); }
  dialog.prompt-dialog header { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid var(--border); }
  dialog.prompt-dialog header h3 { margin: 0; font-size: 15px; }
  dialog.prompt-dialog header .x { background: none; border: none; color: var(--muted); font-size: 22px; cursor: pointer; padding: 0 4px; }
  dialog.prompt-dialog header .x:hover { color: var(--text); }
  dialog.prompt-dialog textarea { width: 100%; min-height: 50vh; max-height: 65vh; background: var(--bg); color: var(--text); border: none; padding: 16px 18px; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12px; line-height: 1.55; resize: vertical; outline: none; }
  dialog.prompt-dialog footer { display: flex; gap: 8px; align-items: center; padding: 12px 18px; border-top: 1px solid var(--border); background: var(--panel); }
  dialog.prompt-dialog footer button { font-size: 12px; padding: 6px 14px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-weight: 600; }
  dialog.prompt-dialog footer button:hover { background: var(--panel); border-color: var(--muted); }
  dialog.prompt-dialog footer .btn-primary { background: var(--info); border-color: var(--info); color: white; }
  dialog.prompt-dialog footer .hint { color: var(--muted); font-size: 11px; margin-left: auto; }

  /* Bulk controls */
  .bulk-controls { display: flex; align-items: center; gap: 8px; margin: 0 0 12px; flex-wrap: wrap; }
  .bulk-controls button { font-size: 12px; padding: 6px 12px; border-radius: 4px; border: 1px solid var(--border); background: var(--panel); color: var(--text); cursor: pointer; }
  .bulk-controls button:hover { background: var(--bg); border-color: var(--muted); }
  .counter { color: var(--muted); margin-left: auto; font-size: 12px; }

  /* Findings table */
  table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  th, td { padding: 8px 10px; text-align: left; font-size: 12px; vertical-align: top; }
  th { background: var(--bg); border-bottom: 1px solid var(--border); font-weight: 600; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
  tbody tr { border-top: 1px solid var(--border); }
  .badge { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 3px; flex-shrink: 0; color: white; }
  .sev-critical-badge { background: var(--critical); }
  .sev-high-badge { background: var(--high); }
  .sev-medium-badge { background: var(--medium); }
  .sev-low-badge { background: var(--low); }
  .id-cell a { color: var(--info); text-decoration: none; font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11px; font-weight: 600; }
  .id-cell a:hover { text-decoration: underline; }
  .title-cell { max-width: 320px; }
  .kb-title { font-weight: 500; margin-bottom: 2px; }
  .kb-observed { color: var(--muted); font-size: 11px; line-height: 1.4; }
  .type-cell { color: var(--muted); font-size: 11px; white-space: nowrap; }
  .loc-cell { max-width: 220px; }
  .loc-cell code { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 10px; background: var(--bg); padding: 1px 4px; border-radius: 3px; word-break: break-all; display: inline-block; }
  .age-cell { color: var(--muted); font-size: 11px; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .rationale-cell { max-width: 240px; color: var(--muted); font-size: 11px; font-style: italic; line-height: 1.4; }
  .action-cell { white-space: nowrap; }
  .action-select { font-size: 12px; padding: 5px 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-weight: 600; font-family: inherit; }
  .action-select:hover { border-color: var(--muted); }
  tr.clickable-row { cursor: pointer; }
  tr.clickable-row:hover { background: rgba(77, 171, 247, 0.06); }
  tr.clickable-row:hover .kb-title { color: var(--info); }

  /* Card dialog */
  dialog.card-dialog { width: min(820px, 92vw); max-height: 90vh; padding: 0; border: 1px solid var(--border); border-radius: 10px; background: var(--panel); color: var(--text); }
  dialog.card-dialog::backdrop { background: rgba(0,0,0,0.55); }
  dialog.card-dialog header { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--border); }
  dialog.card-dialog header h3 { margin: 0; font-size: 15px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  dialog.card-dialog header h3 .kb-id { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12px; color: var(--info); }
  dialog.card-dialog header .x { background: none; border: none; color: var(--muted); font-size: 22px; cursor: pointer; padding: 0 4px; }
  dialog.card-dialog header .x:hover { color: var(--text); }
  dialog.card-dialog .body { padding: 16px 20px; overflow-y: auto; max-height: 70vh; }
  dialog.card-dialog dl { margin: 0; display: grid; grid-template-columns: 130px 1fr; gap: 8px 16px; }
  dialog.card-dialog dt { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 600; padding-top: 2px; }
  dialog.card-dialog dd { margin: 0; font-size: 13px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
  dialog.card-dialog dd code, dialog.card-dialog dd.location { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12px; background: var(--bg); padding: 2px 6px; border-radius: 3px; word-break: break-all; display: inline-block; }
  dialog.card-dialog dd.rationale { color: var(--muted); font-style: italic; }
  dialog.card-dialog footer { display: flex; gap: 8px; align-items: center; padding: 12px 18px; border-top: 1px solid var(--border); background: var(--panel); }
  dialog.card-dialog footer label { font-size: 12px; color: var(--muted); }
  dialog.card-dialog footer select { font-size: 12px; padding: 5px 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-weight: 600; font-family: inherit; }
  dialog.card-dialog footer button { font-size: 12px; padding: 6px 14px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-weight: 600; }
  dialog.card-dialog footer button:hover { background: var(--panel); border-color: var(--muted); }
  dialog.card-dialog footer .spacer { flex: 1; }
  dialog.card-dialog footer a.source { font-size: 12px; color: var(--info); text-decoration: none; }
  dialog.card-dialog footer a.source:hover { text-decoration: underline; }
  tbody tr.chose-resolve { background: rgba(47, 158, 68, 0.06); }
  tbody tr.chose-resolve .action-select { background: var(--resolve); border-color: var(--resolve); color: white; }
  tbody tr.chose-close { background: rgba(103, 65, 217, 0.06); }
  tbody tr.chose-close .action-select { background: var(--close); border-color: var(--close); color: white; }
  tbody tr.chose-defer { opacity: 0.6; }
  tbody tr.chose-defer .action-select { background: var(--defer); border-color: var(--defer); color: white; opacity: 1; }

  footer.page-footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }
  footer.page-footer code { background: var(--panel); padding: 1px 5px; border-radius: 3px; font-size: 11px; }
</style>
</head>
<body>
  <h1>Kanban Board — ${escapeHtml(path.basename(REPO_ROOT))}</h1>
  <p class="meta">Generated ${escapeHtml(generatedAt)} · <code>docs/kanban/board.html</code></p>

  <div class="column-counts">
    ${COLUMNS.map(c => `
      <div class="col-stat">
        <div class="col-stat-label">${escapeHtml(c.replace(/_/g, ' '))}</div>
        <div class="col-stat-value">${counts[c]}</div>
      </div>`).join('')}
  </div>

  <div class="prompt-card preflight">
    <div class="label">
      <p class="title">Pre-flight: RCA + staleness check</p>
      <p class="hint">Runs <code>/aligned:root-cause-analysis</code> on every todo item. Updates or closes invalid cards before you triage. Run this first.</p>
    </div>
    <div class="actions">
      <button class="btn-primary" id="btn-copy-preflight">Copy prompt</button>
      <button id="btn-view-preflight">View / edit</button>
      <span class="copy-status" id="copy-status-preflight">Copied</span>
    </div>
  </div>

  <dialog id="dialog-preflight" class="prompt-dialog">
    <header>
      <h3>Pre-flight: RCA + staleness check</h3>
      <button class="x" data-close="dialog-preflight" aria-label="Close">×</button>
    </header>
    <textarea id="preflight-prompt" spellcheck="false">${escapeHtml(PREFLIGHT_PROMPT)}</textarea>
    <footer>
      <button class="btn-primary" id="btn-copy-preflight-dialog">Copy</button>
      <button data-close="dialog-preflight">Close</button>
      <span class="hint">Edits persist until this page is regenerated.</span>
    </footer>
  </dialog>

  <h2>Todo (${enriched.length})</h2>

  ${enriched.length === 0 ? '<p>No items in <code>docs/kanban/todo/</code>.</p>' : `
  <div class="bulk-controls">
    <button id="btn-resolve-all">All: Resolve</button>
    <button id="btn-close-all">All: Close</button>
    <button id="btn-defer-all">All: Defer</button>
    <button id="btn-reset">Reset to recommended</button>
    <span class="counter">
      <span id="ct-resolve">0</span> resolve &middot;
      <span id="ct-close">0</span> close &middot;
      <span id="ct-defer">0</span> defer
    </span>
  </div>

  <table>
    <thead><tr>
      <th>Sev</th>
      <th>ID</th>
      <th>Title &amp; observed</th>
      <th>Type</th>
      <th>Location</th>
      <th>Age</th>
      <th>Default rationale</th>
      <th>Action</th>
    </tr></thead>
    <tbody>${tableRows}
    </tbody>
  </table>

  <div class="prompt-card action">
    <div class="label">
      <p class="title">Action prompt (regenerates as you triage)</p>
      <p class="hint">Each Resolve item is gated behind a root-cause check (inline for batches, full <code>/aligned:root-cause-analysis</code> when ambiguous). Frames the work with a simplification lens — fixes that would add bloat get refuted, not implemented.</p>
    </div>
    <div class="actions">
      <button class="btn-primary" id="btn-copy-action">Copy prompt</button>
      <button id="btn-view-action">View / edit</button>
      <span class="copy-status" id="copy-status-action">Copied</span>
    </div>
  </div>

  <dialog id="dialog-action" class="prompt-dialog">
    <header>
      <h3>Action prompt</h3>
      <button class="x" data-close="dialog-action" aria-label="Close">×</button>
    </header>
    <textarea id="prompt-output" spellcheck="false"></textarea>
    <footer>
      <button class="btn-primary" id="btn-copy-action-dialog">Copy</button>
      <button id="btn-regen-action">Regenerate from current actions</button>
      <button data-close="dialog-action">Close</button>
      <span class="hint">Edits are overwritten when you change actions above.</span>
    </footer>
  </dialog>

  <dialog id="dialog-card" class="card-dialog">
    <header>
      <h3><span class="badge" id="card-sev"></span><span class="kb-id" id="card-id"></span><span id="card-title"></span></h3>
      <button class="x" data-close="dialog-card" aria-label="Close">×</button>
    </header>
    <div class="body">
      <dl>
        <dt>Type</dt><dd id="card-type"></dd>
        <dt>Discovered during</dt><dd id="card-discovered"></dd>
        <dt>Location</dt><dd id="card-location" class="location"></dd>
        <dt>Age</dt><dd id="card-age"></dd>
        <dt>Severity</dt><dd id="card-severity"></dd>
        <dt>Created</dt><dd id="card-created"></dd>
        <dt>Observed</dt><dd id="card-observed"></dd>
        <dt>Expected</dt><dd id="card-expected"></dd>
        <dt>Why out of scope</dt><dd id="card-why-oos"></dd>
        <dt>Default rationale</dt><dd id="card-rationale" class="rationale"></dd>
      </dl>
    </div>
    <footer>
      <label for="card-action">Action:</label>
      <select id="card-action">
        <option value="resolve">Resolve now</option>
        <option value="close">Close as stale</option>
        <option value="defer">Defer</option>
      </select>
      <a id="card-source" class="source" target="_blank">Open source file</a>
      <div class="spacer"></div>
      <button data-close="dialog-card">Close</button>
    </footer>
  </dialog>`}

  <footer class="page-footer">
    <p><strong>Source:</strong> <code>docs/kanban/todo/*.md</code>. Click any KB-XXX to open the source file.</p>
    <p><strong>Regenerate:</strong> <code>node scripts/generate-kanban-board.cjs</code></p>
  </footer>

  ${enriched.length === 0 ? '' : `<script>
  const ITEMS = ${JSON.stringify(enriched)};
  const state = new Map(ITEMS.map(i => [i.idx, i.defaultDecision]));

  function refresh() {
    const counts = { resolve: 0, close: 0, defer: 0 };
    for (const [idx, decision] of state) {
      const tr = document.querySelector('tr[data-idx="' + idx + '"]');
      if (!tr) continue;
      tr.classList.remove('chose-resolve', 'chose-close', 'chose-defer');
      tr.classList.add('chose-' + decision);
      counts[decision]++;
    }
    document.getElementById('ct-resolve').textContent = counts.resolve;
    document.getElementById('ct-close').textContent = counts.close;
    document.getElementById('ct-defer').textContent = counts.defer;
    document.getElementById('prompt-output').value = buildPrompt();
  }

  function buildPrompt() {
    const resolve = ITEMS.filter(i => state.get(i.idx) === 'resolve');
    const close = ITEMS.filter(i => state.get(i.idx) === 'close');
    if (resolve.length === 0 && close.length === 0) return 'Set actions above to generate a prompt.';

    let out = 'Work through the following Kanban items with a simplification lens. Most of these items propose changes that look like dedup or cleanup — verify each one actually simplifies the codebase. Extracting a 10-line block to a new shared file, adding indirection an LLM has to chase, or replacing inline instructions with cross-references can be net BLOAT. If a proposed fix would add a new file, add reference chasing, or expand prompts without proportional savings, refute it on simplification grounds and move on.\\n\\n';
    out += 'Do NOT assume any item is correct just because it appears below — every Resolve item MUST pass a root-cause check before any code is touched.\\n\\n';
    out += 'Mandatory order of operations:\\n';
    out += '  1) For each Resolve item, perform a root-cause check on its Observed problem. Inline is fine for batch work (verify the issue still exists at the cited location, evaluate whether the Expected fix is sound or bloat-inducing). Invoke the full /aligned:root-cause-analysis skill only when the item is non-trivial or the RCA is genuinely ambiguous — running the full skill on every card in a batch is itself the kind of bloat to avoid.\\n';
    out += '  2) Only if the check confirms the issue is real, present, AND the proposed fix is actual simplification (not just rearrangement that adds indirection) — then implement.\\n';
    out += '  3) If the check refutes the item (issue gone, fix would bloat, proposed solution stale), do not implement. Move the card to docs/kanban/done/ or docs/kanban/did_not_complete/ with a one-line note explaining what the check found.\\n\\n';

    if (resolve.length > 0) {
      out += '## Resolve (root-cause-gated — do not skip step 1)\\n\\n';
      for (const i of resolve) {
        out += '- ' + i.file + ' — ' + i.title + ' [' + i.severity + ']\\n';
        if (i.location) out += '  Location: ' + i.location + '\\n';
      }
      out += '\\nFor each Resolve item, the sequence is:\\n';
      out += '  a) Read the full markdown for context.\\n';
      out += '  b) Verify the issue still exists at the cited Location. Evaluate whether the Expected fix is a real simplification or would add bloat (new files, reference indirection, expanded prompts without payoff).\\n';
      out += '  c) Report back: did the check validate or refute the item? One sentence is fine.\\n';
      out += '  d) If validated → implement the fix, add or update tests, then move the markdown from docs/kanban/todo/ to docs/kanban/done/.\\n';
      out += '  e) If refuted → move the markdown to docs/kanban/done/ (resolved elsewhere) or did_not_complete/ (invalid / would bloat) with the reason.\\n';
      out += 'Escalate to the full /aligned:root-cause-analysis skill only when the item is non-trivial or the check is genuinely ambiguous. Pause and ask before proceeding on truly ambiguous results.\\n\\n';
    }

    if (close.length > 0) {
      out += '## Close without action\\n\\n';
      for (const i of close) {
        out += '- ' + i.file + ' — ' + i.title + '\\n';
      }
      out += '\\nFor each Close item: open the markdown, write a one-line note explaining why it is being closed (already resolved, out of scope, superseded), then move it to docs/kanban/did_not_complete/. Ask if the reason is unclear.\\n\\n';
    }

    out += 'After finishing, regenerate the board: node scripts/generate-kanban-board.cjs\\n';
    return out;
  }

  document.querySelectorAll('select.action-select').forEach(sel => {
    sel.addEventListener('change', () => {
      state.set(sel.dataset.idx, sel.value);
      refresh();
    });
  });

  function setAll(value) {
    for (const i of ITEMS) {
      const v = value === 'default' ? i.defaultDecision : value;
      state.set(i.idx, v);
      const sel = document.querySelector('select.action-select[data-idx="' + i.idx + '"]');
      if (sel) sel.value = v;
    }
    refresh();
  }

  document.getElementById('btn-resolve-all').addEventListener('click', () => setAll('resolve'));
  document.getElementById('btn-close-all').addEventListener('click', () => setAll('close'));
  document.getElementById('btn-defer-all').addEventListener('click', () => setAll('defer'));
  document.getElementById('btn-reset').addEventListener('click', () => setAll('default'));

  async function copyText(text, statusId) {
    await navigator.clipboard.writeText(text);
    const s = document.getElementById(statusId);
    s.classList.add('visible');
    setTimeout(() => s.classList.remove('visible'), 1500);
  }

  // Compact-view copy buttons read from the (possibly edited) textareas
  document.getElementById('btn-copy-preflight').addEventListener('click', () => {
    copyText(document.getElementById('preflight-prompt').value, 'copy-status-preflight');
  });
  document.getElementById('btn-copy-action').addEventListener('click', () => {
    copyText(document.getElementById('prompt-output').value, 'copy-status-action');
  });
  // Dialog copy buttons share the same status pill as the compact ones
  document.getElementById('btn-copy-preflight-dialog').addEventListener('click', () => {
    copyText(document.getElementById('preflight-prompt').value, 'copy-status-preflight');
  });
  document.getElementById('btn-copy-action-dialog').addEventListener('click', () => {
    copyText(document.getElementById('prompt-output').value, 'copy-status-action');
  });

  // Dialog open / close
  document.getElementById('btn-view-preflight').addEventListener('click', () => {
    document.getElementById('dialog-preflight').showModal();
  });
  document.getElementById('btn-view-action').addEventListener('click', () => {
    document.getElementById('dialog-action').showModal();
  });
  document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById(btn.dataset.close).close();
    });
  });

  // Manual regenerate inside the action dialog
  document.getElementById('btn-regen-action').addEventListener('click', () => {
    document.getElementById('prompt-output').value = buildPrompt();
  });

  // Close dialogs when clicking on the backdrop
  document.querySelectorAll('dialog.prompt-dialog, dialog.card-dialog').forEach(dlg => {
    dlg.addEventListener('click', e => {
      if (e.target === dlg) dlg.close();
    });
  });

  // Per-card detail dialog
  const cardDialog = document.getElementById('dialog-card');
  function openCard(idx) {
    const item = ITEMS.find(i => i.idx === idx);
    if (!item) return;
    const sev = (item.severity || '').toLowerCase();
    const sevBadge = document.getElementById('card-sev');
    sevBadge.textContent = item.severity || '';
    sevBadge.className = 'badge sev-' + sev + '-badge';
    document.getElementById('card-id').textContent = item.id || '';
    document.getElementById('card-title').textContent = item.title || '';
    document.getElementById('card-type').textContent = item.type || '—';
    document.getElementById('card-discovered').textContent = item.discoveredDuring || '—';
    document.getElementById('card-location').textContent = item.location || '—';
    document.getElementById('card-age').textContent = item.age != null ? item.age + ' days' : 'unknown';
    document.getElementById('card-severity').textContent = item.severity || '—';
    document.getElementById('card-created').textContent = item.created || '—';
    document.getElementById('card-observed').textContent = item.observed || '—';
    document.getElementById('card-expected').textContent = item.expected || '—';
    document.getElementById('card-why-oos').textContent = item.whyOutOfScope || '—';
    document.getElementById('card-rationale').textContent = item.rationale || '—';
    const src = document.getElementById('card-source');
    src.href = item.file;
    src.textContent = 'Open ' + item.file;
    const sel = document.getElementById('card-action');
    sel.value = state.get(idx);
    sel.dataset.idx = idx;
    cardDialog.showModal();
  }

  document.querySelectorAll('tr.clickable-row').forEach(tr => {
    tr.addEventListener('click', e => {
      // Don't intercept clicks on the source link or the action dropdown.
      if (e.target.closest('a, select, option')) return;
      openCard(tr.dataset.idx);
    });
  });

  // Sync dialog action select back to the row select + state
  document.getElementById('card-action').addEventListener('change', e => {
    const idx = e.target.dataset.idx;
    state.set(idx, e.target.value);
    const rowSel = document.querySelector('select.action-select[data-idx="' + idx + '"]');
    if (rowSel) rowSel.value = e.target.value;
    refresh();
  });

  refresh();
  </script>`}
</body>
</html>`;
}

fs.writeFileSync(OUTPUT, renderHtml());
console.log(`Wrote ${OUTPUT}`);
