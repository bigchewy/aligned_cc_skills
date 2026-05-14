---
model: sonnet
---

# Critique Interactive HTML Generator

## Overview

Generate a standalone HTML decision tool from the aggregated critique report produced during a brainstorming critique panel. The HTML lets the user toggle accept/reject on each finding in the browser, add per-tab modify notes, then copy a single follow-up prompt that pastes back into Claude Code to apply the decisions.

This agent is dispatched by `skills/_shared/critique-panel-orchestration.md` after the aggregation step writes its structured output.

## When to Use

Dispatched by the critique panel orchestration. Not typically invoked directly by users.

## Inputs

The dispatch prompt must provide:

- `{aggregated-json-path}` — path to the structured aggregated report (JSON, written by the aggregation step)
- `{design-file-path}` — path to the design document being critiqued
- `{session-name}` — kebab-case session topic (used for output filename)
- `{mode}` — brainstorming mode: software | business | research | authoring | planning
- `{project-root}` — project root path

## Step 1: Read the Aggregated JSON

Read `{aggregated-json-path}`. Expected schema:

```json
{
  "fact_checks": [
    {"id": "fc-1", "claim": "<original>", "correction": "<corrected>", "critic": "<critic-name>"}
  ],
  "findings": [
    {"id": "h-1", "severity": "high",   "text": "<finding>", "action": "<suggested fix>", "critics": ["<name>", ...]},
    {"id": "m-1", "severity": "medium", "text": "<finding>", "action": "<suggested fix>", "critics": ["<name>", ...]},
    {"id": "l-1", "severity": "low",    "text": "<finding>", "action": "<suggested fix>", "critics": ["<name>", ...]}
  ]
}
```

If the JSON is missing or malformed, STOP and report the path that was expected. Do not silently fall back to parsing prose.

## Step 2: Apply Default Toggle States

Per the critique-panel-orchestration protocol, defaults match the existing chat-based flow:

| Severity | Default toggle |
|----------|----------------|
| high     | accept |
| medium   | accept |
| low      | reject |

Fact-checks are not toggleable. They are rendered in their own tab as read-only "will be applied" items, mirroring the orchestration's `Apply Fixes` step: *"Apply corrections for any INCORRECT fact-check claims"* (no user-approval gate).

The per-tab modify-notes textarea allows the user to override or annotate any tab — including fact-checks — without per-row textareas.

## Step 3: Write the HTML File

**Output path:** `docs/mockups/{session-name}-critique.html`

Overwrite any existing file at that path. The brainstorming flow may iterate; git tracks history on the design doc.

Build the HTML by substituting tokens in the template below:

- `{Session Title}` — humanize `{session-name}` (e.g., `auth-refactor` → "Auth Refactor")
- `{mode}` — the mode string
- `{design-file-path}` — used in the generated follow-up prompt
- `{high-count}`, `{medium-count}`, `{low-count}`, `{fact-count}` — counts of items in each bucket
- `{findings-cards-high}`, `{findings-cards-medium}`, `{findings-cards-low}` — the HTML for each card list (see card template below)
- `{fact-check-cards}` — the HTML for the read-only fact-check list (see fact-check template below)
- `{findings-json}` — the findings array, serialized as a JS literal with each item's `accepted` field set per the defaults above
- `{fact-checks-json}` — the fact_checks array, serialized as a JS literal
- `{session-name}` — used as the SESSION.name constant in the embedded JS

### Card template (one per finding)

```html
<div class="finding" data-id="{id}" data-severity="{severity}">
  <div class="finding-toggle">
    <div class="toggle-switch {on-or-empty}" onclick="toggleFinding('{id}', this)">
      <div class="toggle-knob"></div>
    </div>
    <div class="toggle-label">{accept-or-reject}</div>
  </div>
  <div class="finding-body">
    <div class="finding-critics">
      {one <span class="critic-tag">Name</span> per critic}
    </div>
    <div class="finding-text">{text}</div>
    <div class="finding-action"><strong>Suggested action:</strong> {action}</div>
  </div>
</div>
```

Where `{on-or-empty}` is `on` if the default is accept and empty string if reject, and `{accept-or-reject}` is `accept` or `reject` to match. Escape any HTML in `text`/`action`/`critic` strings (`<`, `>`, `&`, `"`).

### Fact-check template (one per fact_check)

```html
<div class="fact-check">
  <div class="fact-check-claim">{claim}</div>
  <div class="fact-check-correction">→ {correction}</div>
  <div class="fact-check-critic">{critic}</div>
</div>
```

Escape HTML the same way.

### Empty buckets

If a bucket has zero items, replace the card list with:

```html
<div class="empty">No items in this category.</div>
```

The modify-notes textarea stays present on every tab regardless.

## Step 4: Verify and Open

After writing, verify with a Read of the output file that the JS does not contain unescaped `</script>` inside any embedded string (would close the script block early). Also verify both `<script>` tags are present and the file ends with `</html>`.

Then open the file in the browser:

```bash
open docs/mockups/{session-name}-critique.html
```

The orchestration step that dispatched this agent is responsible for telling the user the file is open and how to use it.

**Do NOT commit.** The brainstorming skill commits all visual artifacts together with the design document after critique rounds complete.

## HTML Template

This is the literal template to fill in. Token names match the substitutions documented in Step 3.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Session Title} — Critique Decisions</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7;
      color: #1a1a1a;
      margin: 0 auto;
      padding: 40px 40px 120px;
      max-width: 960px;
    }
    h1 { font-size: 1.5rem; font-weight: 500; margin: 0 0 4px; }
    .subtitle { font-size: 0.95rem; color: #555; margin: 0 0 4px; }
    .context { font-size: 0.88rem; color: #6b7280; margin: 0 0 24px; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }

    .tab-bar { display: flex; gap: 2px; border-bottom: 2px solid #f0eeeb; margin-bottom: 24px; flex-wrap: wrap; }
    .tab-btn {
      padding: 10px 18px; font-size: 0.85rem; font-weight: 500; color: #6b7280;
      background: transparent; border: none; border-bottom: 2px solid transparent;
      margin-bottom: -2px; cursor: pointer; transition: color 150ms, border-color 150ms;
      font-family: inherit;
    }
    .tab-btn:hover { color: #1a1a1a; }
    .tab-btn.active { color: #e8762b; border-bottom-color: #e8762b; }
    .tab-count {
      display: inline-block; background: #f5f3ef; color: #555;
      font-size: 0.75rem; padding: 1px 7px; border-radius: 9999px;
      margin-left: 6px; font-weight: 500;
    }
    .tab-btn.active .tab-count { background: #fff7ed; color: #e8762b; }

    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    .finding {
      background: white; border: 1px solid #e5e7eb; border-radius: 12px;
      padding: 18px 20px; margin-bottom: 12px;
      display: flex; gap: 16px; align-items: flex-start;
      transition: opacity 150ms, border-color 150ms;
    }
    .finding.rejected { opacity: 0.5; border-color: #f0eeeb; background: #fafafa; }
    .finding-toggle { flex-shrink: 0; padding-top: 2px; }
    .toggle-switch {
      position: relative; width: 44px; height: 24px;
      background: #d1d5db; border-radius: 9999px; cursor: pointer;
      transition: background 150ms;
    }
    .toggle-switch.on { background: #6b8e4e; }
    .toggle-knob {
      position: absolute; top: 2px; left: 2px;
      width: 20px; height: 20px; background: white; border-radius: 9999px;
      transition: transform 150ms; box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .toggle-switch.on .toggle-knob { transform: translateX(20px); }
    .toggle-label {
      font-size: 0.72rem; color: #6b7280; text-align: center; margin-top: 4px;
      font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em;
    }
    .finding-body { flex: 1; min-width: 0; }
    .finding-critics { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
    .critic-tag {
      font-size: 0.72rem; padding: 1px 8px; border-radius: 9999px;
      background: #fff7ed; color: #e8762b; font-weight: 500;
    }
    .finding-text { font-size: 0.92rem; line-height: 1.5; color: #1a1a1a; margin-bottom: 6px; }
    .finding-action { font-size: 0.85rem; color: #555; line-height: 1.5; }
    .finding-action strong { color: #1a1a1a; font-weight: 500; }

    .fact-check {
      background: white; border: 1px solid #e5e7eb; border-left: 3px solid #6b8e4e;
      border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    }
    .fact-check-claim { font-size: 0.85rem; color: #6b7280; text-decoration: line-through; margin-bottom: 4px; }
    .fact-check-correction { font-size: 0.92rem; color: #1a1a1a; line-height: 1.5; }
    .fact-check-critic { font-size: 0.72rem; color: #e8762b; font-weight: 500; margin-top: 6px; }
    .auto-apply-notice {
      font-size: 0.82rem; color: #6b7280; background: #f5f3ef;
      padding: 10px 14px; border-radius: 8px; margin-bottom: 16px;
    }

    .modify-notes { margin-top: 24px; padding-top: 20px; border-top: 1px dashed #e5e7eb; }
    .modify-notes label {
      display: block; font-size: 0.85rem; font-weight: 500; color: #1a1a1a; margin-bottom: 8px;
    }
    .modify-notes textarea {
      width: 100%; min-height: 80px; padding: 10px 12px;
      font-family: inherit; font-size: 0.88rem;
      border: 1px solid #e5e7eb; border-radius: 8px; resize: vertical; background: white;
    }
    .modify-notes textarea:focus { outline: none; border-color: #e8762b; }

    .empty {
      font-size: 0.88rem; color: #6b7280; padding: 24px; text-align: center;
      background: #f5f3ef; border-radius: 8px;
    }

    .action-footer {
      position: fixed; bottom: 0; left: 0; right: 0;
      background: white; border-top: 1px solid #e5e7eb;
      padding: 16px 40px;
      display: flex; justify-content: space-between; align-items: center;
      box-shadow: 0 -2px 8px rgba(0,0,0,0.04); z-index: 10;
    }
    .summary { font-size: 0.88rem; color: #555; }
    .summary strong { color: #1a1a1a; }
    .copy-btn {
      padding: 10px 20px; font-size: 0.88rem; font-weight: 500; color: white;
      background: #e8762b; border: none; border-radius: 8px; cursor: pointer;
      transition: background 150ms; font-family: inherit;
    }
    .copy-btn:hover { background: #cc6725; }
    .copy-btn.copied { background: #6b8e4e; }
  </style>
</head>
<body>
  <h1>{Session Title}</h1>
  <p class="subtitle">Brainstorming session · {mode} mode</p>
  <p class="context">Critique decisions. Toggle findings to accept or reject, add modify notes per tab if needed, then copy the follow-up prompt back into Claude Code.</p>

  <div class="tab-bar">
    <button class="tab-btn active" data-tab="high">High <span class="tab-count">{high-count}</span></button>
    <button class="tab-btn" data-tab="medium">Medium <span class="tab-count">{medium-count}</span></button>
    <button class="tab-btn" data-tab="low">Low <span class="tab-count">{low-count}</span></button>
    <button class="tab-btn" data-tab="facts">Fact-checks <span class="tab-count">{fact-count}</span></button>
  </div>

  <div class="tab-panel active" id="panel-high">
    {findings-cards-high}
    <div class="modify-notes">
      <label for="notes-high">Modify notes for High severity (optional)</label>
      <textarea id="notes-high" placeholder="Anything you want to add, override, or annotate for high-severity findings..."></textarea>
    </div>
  </div>

  <div class="tab-panel" id="panel-medium">
    {findings-cards-medium}
    <div class="modify-notes">
      <label for="notes-medium">Modify notes for Medium severity (optional)</label>
      <textarea id="notes-medium" placeholder="Anything you want to add, override, or annotate for medium-severity findings..."></textarea>
    </div>
  </div>

  <div class="tab-panel" id="panel-low">
    {findings-cards-low}
    <div class="modify-notes">
      <label for="notes-low">Modify notes for Low severity (optional)</label>
      <textarea id="notes-low" placeholder="Anything you want to add, override, or annotate for low-severity findings..."></textarea>
    </div>
  </div>

  <div class="tab-panel" id="panel-facts">
    <div class="auto-apply-notice">
      Fact-check corrections are applied automatically per the critique-panel protocol. Use the modify notes below if you want to override or annotate a specific correction.
    </div>
    {fact-check-cards}
    <div class="modify-notes">
      <label for="notes-facts">Override or annotate fact-checks (optional)</label>
      <textarea id="notes-facts" placeholder="Anything to override or annotate..."></textarea>
    </div>
  </div>

  <div class="action-footer">
    <div class="summary"><strong id="accept-count">0</strong> accepted · <strong id="reject-count">0</strong> rejected</div>
    <button class="copy-btn" onclick="copyPrompt(this)">Copy follow-up prompt</button>
  </div>

  <script>
    const FINDINGS = {findings-json};
    const FACT_CHECKS = {fact-checks-json};
    const SESSION = {
      name: "{session-name}",
      mode: "{mode}",
      designPath: "{design-file-path}"
    };

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
      });
    });

    function toggleFinding(id, el) {
      const finding = FINDINGS.find(f => f.id === id);
      if (!finding) return;
      finding.accepted = !finding.accepted;
      el.classList.toggle('on');
      const card = el.closest('.finding');
      const label = el.parentElement.querySelector('.toggle-label');
      if (finding.accepted) {
        card.classList.remove('rejected');
        label.textContent = 'accept';
      } else {
        card.classList.add('rejected');
        label.textContent = 'reject';
      }
      updateSummary();
    }

    function updateSummary() {
      const accepted = FINDINGS.filter(f => f.accepted).length;
      const rejected = FINDINGS.filter(f => !f.accepted).length;
      document.getElementById('accept-count').textContent = accepted;
      document.getElementById('reject-count').textContent = rejected;
    }

    function buildPrompt() {
      const accept = FINDINGS.filter(f => f.accepted);
      const reject = FINDINGS.filter(f => !f.accepted);

      const formatFinding = f => {
        const critics = f.critics && f.critics.length ? '[' + f.critics.join(', ') + '] ' : '';
        return '- ' + critics + f.text;
      };

      const notes = {
        high:   document.getElementById('notes-high').value.trim()   || '(none)',
        medium: document.getElementById('notes-medium').value.trim() || '(none)',
        low:    document.getElementById('notes-low').value.trim()    || '(none)',
        facts:  document.getElementById('notes-facts').value.trim()  || '(none)'
      };

      const factLines = FACT_CHECKS.length
        ? FACT_CHECKS.map(fc => '- ' + fc.claim + ' → ' + fc.correction).join('\n')
        : '(none)';

      return [
        'Resume brainstorming session "' + SESSION.name + '" (' + SESSION.mode + ' mode) at `' + SESSION.designPath + '`.',
        'Critique decisions from interactive review:',
        '',
        'ACCEPT (apply these):',
        accept.length ? accept.map(formatFinding).join('\n') : '(none)',
        '',
        'REJECT (skip these):',
        reject.length ? reject.map(formatFinding).join('\n') : '(none)',
        '',
        'FACT-CHECKS (auto-applied):',
        factLines,
        '',
        'MODIFY NOTES:',
        '- High severity: '   + notes.high,
        '- Medium severity: ' + notes.medium,
        '- Low severity: '    + notes.low,
        '- Fact-checks: '     + notes.facts,
        '',
        'Apply the accepted findings and any modify notes, skip the rejected ones, regenerate the design doc, then refresh the session visualization per the post-critique checklist in the mode file.'
      ].join('\n');
    }

    function copyPrompt(btn) {
      const text = buildPrompt();
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copied — paste in Claude Code';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = original;
          btn.classList.remove('copied');
        }, 2400);
      }).catch(err => {
        btn.textContent = 'Copy failed — see console';
        console.error('Clipboard write failed:', err);
      });
    }

    updateSummary();
  </script>
</body>
</html>
```
