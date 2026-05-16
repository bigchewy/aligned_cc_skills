# Render review HTML: HTML-generator sub-agent prompt

This file is the prompt template the orchestrator pastes into a `subagent_type: general-purpose` Task dispatch during PHASE 3. Generates a standalone interactive HTML document from the aggregated Open Questions queue and opens it in the browser.

The orchestrator substitutes the placeholders below before dispatching.

This is NOT a registered top-level agent. It's a supporting prompt internal to `reverse-engineered-brand`. Dispatching it is the orchestrator's responsibility; reading its file is for humans auditing the framework.

---

## Prompt template (substitute placeholders, then dispatch)

You are generating a standalone interactive HTML document from the Open Questions queue produced by a brand-folder build. The HTML lets the user read every open question in the browser, type an answer or skip, then copy a follow-up prompt that pastes back into Claude Code to apply the decisions.

**Inputs** (substituted by the orchestrator):

- `{open-questions-json-path}` — path to the structured Open Questions queue (JSON, written by the orchestrator just before dispatch)
- `{brand-folder-path}` — absolute path to the `brand/` folder that was just written
- `{org-name}` — short human-readable org name (used in title and the copy-back prompt)
- `{output-html-path}` — absolute path the HTML file should be written to (typically `{brand-folder-path}/open-questions.html`)

### Step 1: Read the Open Questions JSON

Read `{open-questions-json-path}`. Expected schema:

```json
{
  "open_questions": [
    {
      "id": "OQ-1",
      "file": "strategy/positioning.md",
      "slice": "competitive-alternatives",
      "confidence": "low",
      "what_i_wrote": "Best customers were previously cobbling together spreadsheets and manual dispatch.",
      "question": "Was the real alternative for your best customers the spreadsheet state, or were they limping along on a competitor product?",
      "why_it_matters": "Determines whether positioning frames against operational chaos or migration pain.",
      "deepen_with": "5-components-positioning",
      "sources": ["#4", "#6"]
    }
  ]
}
```

The `deepen_with` field is the framework id that owns the slice. May be JSON `null` for slices without an owning framework. The HTML renders this as a "Deepen with" chip per card and includes the `/aligned:use-framework {id}` command in paste-back prompts.

If the JSON is missing or malformed, STOP and report the path that was expected. Do not silently fall back to parsing prose.

### Step 2: Render the HTML

**Output path:** `{output-html-path}` (overwrite any existing file).

Build the HTML by substituting tokens in the template below:

- `{Org Name}` — the `{org-name}` arg (already human-readable)
- `{brand-folder-path}` — used in the generated follow-up prompt
- `{question-count}` — total number of open questions
- `{question-cards}` — the HTML for each card (see card template below)
- `{open-questions-json}` — the open_questions array serialized as a JS literal with each item's `answer` field initialized to `""` and `skipped` field initialized to `false`

#### Card template (one per question)

```html
<div class="question" data-id="{id}" data-confidence="{confidence}">
  <div class="question-header">
    <span class="question-id">{id}</span>
    <span class="question-file"><code>{file}</code>{slice-suffix}</span>
    <span class="question-confidence confidence-{confidence}">{confidence}</span>
    {deepen-chip}
  </div>
  <div class="question-text">{question}</div>
  <details class="question-context">
    <summary>Context</summary>
    <div class="context-row"><strong>Current draft:</strong> {what_i_wrote}</div>
    <div class="context-row"><strong>Why it matters:</strong> {why_it_matters}</div>
    {deepen-row}
    {sources-row}
  </details>
  <div class="answer-row">
    <textarea
      class="answer-input"
      id="answer-{id}"
      placeholder="Type your answer here, or click Skip to defer."
      oninput="updateAnswer('{id}', this.value)"
    ></textarea>
    <div class="answer-actions">
      <label class="skip-toggle">
        <input type="checkbox" onchange="toggleSkip('{id}', this.checked)"> Skip for now
      </label>
      <button class="copy-one-btn" onclick="copyOne('{id}', this)">Copy this question's prompt</button>
    </div>
  </div>
</div>
```

Where:
- `{slice-suffix}` is `<span class="slice-tag">#{slice}</span>` if `slice` is a non-empty string, else empty. (The `slice` field is always present per the synthesizer contract, but may be the empty string.)
- `{deepen-chip}` is `<span class="deepen-chip" title="Run this framework for a deeper interactive pass">deepen: {deepen_with}</span>` if `deepen_with` is non-null (JSON null check, not the string `"null"`), else `<span class="deepen-chip gap">no framework</span>`
- `{deepen-row}` is `<div class="context-row"><strong>Deepen with:</strong> <code>/aligned:use-framework {deepen_with}</code> for a full interactive pass on this slice</div>` if `deepen_with` is non-null, else `<div class="context-row gap-note"><strong>Deepen with:</strong> GAP — no framework owns this slice. Synthesis was ad-hoc.</div>`
- `{sources-row}` is `<div class="context-row"><strong>Sources:</strong> {sources joined with comma}</div>` if `sources` is non-empty, else empty
- Escape `<`, `>`, `&`, `"` in all HTML string substitutions

#### Empty queue

If `open_questions` is empty, render a single message card and omit the action footer's "Copy all" button:

```html
<div class="empty">No open questions — every slice landed at medium or high confidence with no calibration gaps.</div>
```

### Step 3: Verify and Open

**Before writing,** sanitize the `{open-questions-json}` JS literal:
- Replace every `</` with `<\/` in any string value of the JSON before serialization (this prevents `</script>` inside `what_i_wrote`/`question`/`why_it_matters` from closing the script tag).
- Ensure the JSON is serialized with `JSON.stringify`-equivalent escaping for backslashes, quotes, and control characters. Do not hand-build the JS literal — write the JSON object then embed the serialized string.

**After writing,** verify with a Read of the output file that:
- No occurrence of `</script>` exists anywhere in the file except the closing tag for the script block itself
- Both `<script>` tags are present
- The file ends with `</html>`

If verification fails, abort and report the offending byte range — do NOT open the browser to a malformed file.

Then open the file in the default browser:

```bash
open {output-html-path}
```

The dispatching framework is responsible for telling the user the file is open and how to use it.

### HTML Template

This is the literal template to fill in. Token names match the substitutions documented in Step 2.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Org Name} — Brand Folder Open Questions</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #faf9f7;
      color: #1a1a1a;
      margin: 0 auto;
      padding: 40px 40px 140px;
      max-width: 960px;
    }
    h1 { font-size: 1.5rem; font-weight: 500; margin: 0 0 4px; }
    .subtitle { font-size: 0.95rem; color: #555; margin: 0 0 4px; }
    .context-line {
      font-size: 0.88rem; color: #6b7280; margin: 0 0 24px;
      padding-bottom: 16px; border-bottom: 1px solid #e5e7eb;
    }
    .context-line code {
      background: #f5f3ef; padding: 1px 6px; border-radius: 4px;
      font-size: 0.82rem;
    }

    .question {
      background: white; border: 1px solid #e5e7eb; border-radius: 12px;
      padding: 20px 22px; margin-bottom: 16px;
      transition: opacity 150ms, border-color 150ms;
    }
    .question.skipped { opacity: 0.55; border-style: dashed; }
    .question.answered { border-left: 3px solid #6b8e4e; }

    .question-header {
      display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
      margin-bottom: 10px; font-size: 0.82rem; color: #6b7280;
    }
    .question-id {
      font-weight: 600; color: #1a1a1a; letter-spacing: 0.02em;
    }
    .question-file code {
      background: #f5f3ef; padding: 1px 6px; border-radius: 4px;
      font-size: 0.78rem; color: #1a1a1a;
    }
    .slice-tag {
      background: #fff7ed; color: #e8762b; padding: 1px 7px;
      border-radius: 9999px; font-size: 0.72rem; font-weight: 500;
      margin-left: 4px;
    }
    .question-confidence {
      padding: 1px 8px; border-radius: 9999px;
      font-size: 0.72rem; font-weight: 500; text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .confidence-low    { background: #fef2f2; color: #b91c1c; }
    .confidence-medium { background: #fffbeb; color: #b45309; }
    .confidence-high   { background: #f0fdf4; color: #15803d; }

    .deepen-chip {
      padding: 1px 8px; border-radius: 9999px;
      font-size: 0.72rem; font-weight: 500;
      background: #eef2ff; color: #4338ca;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }
    .deepen-chip.gap { background: #f3f4f6; color: #6b7280; font-family: inherit; font-style: italic; }
    .context-row.gap-note { color: #6b7280; font-style: italic; }
    .context-row code {
      background: #f5f3ef; padding: 1px 6px; border-radius: 4px;
      font-size: 0.82rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    .question-text {
      font-size: 1rem; line-height: 1.5; color: #1a1a1a;
      margin-bottom: 12px; font-weight: 500;
    }
    .question-context {
      font-size: 0.88rem; color: #555; margin-bottom: 14px;
      background: #faf9f7; border-radius: 8px; padding: 0 14px;
    }
    .question-context summary {
      cursor: pointer; padding: 10px 0; font-weight: 500; color: #6b7280;
      font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em;
    }
    .context-row {
      padding: 6px 0 10px; line-height: 1.5;
    }
    .context-row strong { color: #1a1a1a; font-weight: 500; margin-right: 4px; }

    .answer-row { margin-top: 6px; }
    .answer-input {
      width: 100%; min-height: 70px; padding: 10px 12px;
      font-family: inherit; font-size: 0.9rem; line-height: 1.5;
      border: 1px solid #e5e7eb; border-radius: 8px;
      resize: vertical; background: white;
    }
    .answer-input:focus { outline: none; border-color: #e8762b; }
    .answer-actions {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: 10px; gap: 16px;
    }
    .skip-toggle {
      font-size: 0.82rem; color: #6b7280; cursor: pointer;
      display: flex; align-items: center; gap: 6px;
    }
    .skip-toggle input { cursor: pointer; }
    .copy-one-btn {
      padding: 6px 14px; font-size: 0.8rem; font-weight: 500;
      color: #1a1a1a; background: #f5f3ef; border: 1px solid #e5e7eb;
      border-radius: 6px; cursor: pointer; font-family: inherit;
      transition: background 150ms;
    }
    .copy-one-btn:hover { background: #ebe8e2; }
    .copy-one-btn.copied { background: #6b8e4e; color: white; border-color: #6b8e4e; }

    .empty {
      font-size: 0.95rem; color: #6b7280; padding: 40px; text-align: center;
      background: #f5f3ef; border-radius: 12px;
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
    .copy-all-btn {
      padding: 10px 20px; font-size: 0.88rem; font-weight: 500; color: white;
      background: #e8762b; border: none; border-radius: 8px; cursor: pointer;
      transition: background 150ms; font-family: inherit;
    }
    .copy-all-btn:hover { background: #cc6725; }
    .copy-all-btn.copied { background: #6b8e4e; }
  </style>
</head>
<body>
  <h1>{Org Name} — Brand Folder Open Questions</h1>
  <p class="subtitle">Reverse-engineered-brand · review queue</p>
  <p class="context-line">Brand folder: <code>{brand-folder-path}</code> · {question-count} open questions. Type an answer for each question, or skip to defer. When you're ready, click <strong>Copy all answers</strong> at the bottom and paste back into Claude Code to apply.</p>

  <div id="questions-list">
    {question-cards}
  </div>

  <div class="action-footer">
    <div class="summary"><strong id="answered-count">0</strong> answered · <strong id="skipped-count">0</strong> skipped · <strong id="pending-count">{question-count}</strong> pending</div>
    <button class="copy-all-btn" onclick="copyAll(this)">Copy all answers</button>
  </div>

  <script>
    const OPEN_QUESTIONS = {open-questions-json};
    const BRAND_FOLDER_PATH = "{brand-folder-path}";
    const ORG_NAME = "{Org Name}";

    function updateAnswer(id, value) {
      const q = OPEN_QUESTIONS.find(x => x.id === id);
      if (!q) return;
      q.answer = value;
      const card = document.querySelector('.question[data-id="' + id + '"]');
      if (value.trim()) card.classList.add('answered');
      else card.classList.remove('answered');
      updateSummary();
    }

    function toggleSkip(id, checked) {
      const q = OPEN_QUESTIONS.find(x => x.id === id);
      if (!q) return;
      q.skipped = checked;
      const card = document.querySelector('.question[data-id="' + id + '"]');
      if (checked) card.classList.add('skipped');
      else card.classList.remove('skipped');
      updateSummary();
    }

    function updateSummary() {
      const answered = OPEN_QUESTIONS.filter(q => q.answer && q.answer.trim() && !q.skipped).length;
      const skipped  = OPEN_QUESTIONS.filter(q => q.skipped).length;
      const pending  = OPEN_QUESTIONS.length - answered - skipped;
      document.getElementById('answered-count').textContent = answered;
      document.getElementById('skipped-count').textContent  = skipped;
      document.getElementById('pending-count').textContent  = pending;
    }

    function formatOne(q) {
      const deepen = q.deepen_with
        ? '  Deepen with: /aligned:use-framework ' + q.deepen_with
        : '  Deepen with: (no framework owns this slice — synthesis is ad-hoc)';
      return [
        '- ' + q.id + ' (' + q.file + (q.slice ? '#' + q.slice : '') + '):',
        '  Question: ' + q.question,
        '  Answer: '   + (q.answer && q.answer.trim() ? q.answer.trim() : '(skipped — leave open)'),
        deepen
      ].join('\n');
    }

    function buildBatchPrompt() {
      const answered = OPEN_QUESTIONS.filter(q => q.answer && q.answer.trim() && !q.skipped);
      const skipped  = OPEN_QUESTIONS.filter(q => q.skipped);

      return [
        'Apply review answers to the ' + ORG_NAME + ' brand folder at `' + BRAND_FOLDER_PATH + '`.',
        '',
        'For each answered open question below: update the referenced slice file with the answer, bump its confidence accordingly, and mark the question resolved in `brand/CLAUDE.md § Open Questions`. For each skipped question: leave the slice draft as-is and leave the question open. If the user wants a deeper pass on any slice beyond just applying these answers, run the framework named under "Deepen with" — never improvise a slice update outside its owning framework.',
        '',
        'ANSWERED:',
        answered.length ? answered.map(formatOne).join('\n') : '(none)',
        '',
        'SKIPPED (leave open):',
        skipped.length ? skipped.map(q => '- ' + q.id + ' (deepen with: ' + (q.deepen_with || 'no framework — ad-hoc') + ')').join('\n') : '(none)',
        ''
      ].join('\n');
    }

    function buildOnePrompt(id) {
      const q = OPEN_QUESTIONS.find(x => x.id === id);
      if (!q) return '';
      const deepenNote = q.deepen_with
        ? 'If a deeper pass on this slice is wanted beyond applying this answer, run `/aligned:use-framework ' + q.deepen_with + '` — that is the framework that owns this slice. Do not improvise a slice update outside its owning framework.'
        : 'This slice has no owning framework (synthesis was ad-hoc). Apply the answer directly to the draft.';
      return [
        'Apply this single review answer to the ' + ORG_NAME + ' brand folder at `' + BRAND_FOLDER_PATH + '`.',
        '',
        'Update `' + q.file + '`' + (q.slice ? ' (slice: ' + q.slice + ')' : '') + ' with the answer below, bump its confidence accordingly, and mark ' + q.id + ' resolved in `brand/CLAUDE.md § Open Questions`.',
        '',
        'Question: ' + q.question,
        'Answer: '   + (q.answer && q.answer.trim() ? q.answer.trim() : '(no answer provided — leave open)'),
        '',
        deepenNote
      ].join('\n');
    }

    function copyAll(btn) {
      const text = buildBatchPrompt();
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copied — paste in Claude Code';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = original; btn.classList.remove('copied'); }, 2400);
      }).catch(err => {
        btn.textContent = 'Copy failed — see console';
        console.error('Clipboard write failed:', err);
      });
    }

    function copyOne(id, btn) {
      const text = buildOnePrompt(id);
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copied';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = original; btn.classList.remove('copied'); }, 1800);
      }).catch(err => {
        btn.textContent = 'Copy failed';
        console.error('Clipboard write failed:', err);
      });
    }

    updateSummary();
  </script>
</body>
</html>
```
