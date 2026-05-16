---
---
# Brainstorming Interactive Widgets Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Bake interactive Decision Log + Open Questions widgets into the brainstorming skill's visualization protocol so every future brainstorm gets them by default, without touching the templates' byte-identity invariant.

**Source Design Doc:** `docs/plans/2026-05-15-brainstorm-interactive-widgets-design.md`

**Mockups:** `docs/mockups/2026-05-15-ai-native-brand-folder.html` (the proving-ground reference for widget structure and JS)

**Architecture:** Add one new sidecar partial (`skills/brainstorming/references/widgets.html`) containing CSS, JS, and 5 HTML blocks. The model copies blocks verbatim into the live HTML during visualization. The 4 mode templates (`software`, `business`, `authoring`, `planning`) gain widget-state composition inside their existing `saveState`/`restoreState` IIFE — preserving md5 byte-identity across all four. Docs/mode-files/critique-checklists update to point at the new contract.

**Tech Stack:** Markdown skills, HTML/CSS/vanilla-JS templates, pytest for lint and structural tests.

---

## Prerequisites

> None — all work is automatable file edits and pytest tests.

---

### ✅ Task 1: Add failing pytest scaffold for widget tests

**Files:**
- Create: `e2e/tests/test_brainstorm_widgets.py`

**Step 1: Write the failing test file**

Write `e2e/tests/test_brainstorm_widgets.py` with 10 test functions stubbed against expected structure:

```python
"""Structural and lint tests for the brainstorming interactive-widgets sidecar."""
import hashlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "skills/brainstorming/references/templates"
WIDGETS_PARTIAL = REPO_ROOT / "skills/brainstorming/references/widgets.html"
TEMPLATE_NAMES = [
    "software-template.html",
    "business-template.html",
    "authoring-template.html",
    "planning-template.html",
]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_widgets_partial_exists():
    assert WIDGETS_PARTIAL.exists(), (
        f"widgets sidecar partial must exist at {WIDGETS_PARTIAL.relative_to(REPO_ROOT)}"
    )


def test_template_md5_equality():
    hashes = {name: _md5(TEMPLATES_DIR / name) for name in TEMPLATE_NAMES}
    distinct = set(hashes.values())
    assert len(distinct) == 1, (
        f"all four mode templates must share a single md5; got {hashes}"
    )


def test_widgets_partial_has_required_block_markers():
    text = WIDGETS_PARTIAL.read_text()
    for marker in [
        "<!-- WIDGETS-CSS-START -->",
        "<!-- WIDGETS-CSS-END -->",
        "<!-- WIDGETS-SCRIPT-START -->",
        "<!-- WIDGETS-SCRIPT-END -->",
        "<!-- WIDGET-HTML: decision-log-flat -->",
        "<!-- WIDGET-HTML: decision-log-categorized -->",
        "<!-- WIDGET-HTML: open-questions-flat -->",
        "<!-- WIDGET-HTML: open-questions-categorized -->",
        "<!-- WIDGET-HTML: prompt-box -->",
    ]:
        assert marker in text, f"widgets.html missing marker: {marker}"


def test_widget_selector_lint_no_bare_tbody_tr():
    """Mockup bug regression: widgets must never use `tbody tr` without `[data-id]`
    because section-divider rows lack a <select> and break querySelector chains."""
    text = WIDGETS_PARTIAL.read_text()
    bare = re.findall(r"querySelectorAll\(\s*['\"]tbody tr['\"]\s*\)", text)
    assert not bare, (
        "widgets.html uses bare `querySelectorAll('tbody tr')`; must scope to "
        "`tbody tr[data-id]` to skip section-divider rows"
    )


def test_widget_isolation_guards_present():
    """Each widget IIFE must guard with an early return so a page with only one
    widget table (no Decision Log OR no Open Questions) still loads cleanly."""
    text = WIDGETS_PARTIAL.read_text()
    assert "getElementById('decisions-table')" in text, (
        "missing decisions-table existence check"
    )
    assert "getElementById('questions-table')" in text, (
        "missing questions-table existence check"
    )
    # Both guards must early-return before touching the table
    assert re.search(
        r"if\s*\(\s*!\s*document\.getElementById\(\s*['\"]decisions-table['\"]\s*\)\s*\)\s*return",
        text,
    ), "decision-log widget missing `if (!document.getElementById('decisions-table')) return;` guard"
    assert re.search(
        r"if\s*\(\s*!\s*document\.getElementById\(\s*['\"]questions-table['\"]\s*\)\s*\)\s*return",
        text,
    ), "open-questions widget missing `if (!document.getElementById('questions-table')) return;` guard"


def test_widget_empty_tbody_renders_hint():
    """A widget with zero `tr[data-id]` rows must show a 'no entries' hint, not a
    false 'all approved' message."""
    text = WIDGETS_PARTIAL.read_text()
    # The hint copy is present somewhere in the script (we don't pin exact wording,
    # just that the empty-tbody branch exists)
    assert "No decisions" in text or "no decisions captured" in text.lower(), (
        "decision-log widget missing empty-tbody hint text"
    )
    assert "No open questions" in text or "no open questions" in text.lower(), (
        "open-questions widget missing empty-tbody hint text"
    )


def test_widget_clipboard_fallback_present():
    """Clipboard helper must handle file:// origins (non-secure context) without
    throwing — required because committed snapshots open at file://."""
    text = WIDGETS_PARTIAL.read_text()
    assert "isSecureContext" in text or "document.execCommand" in text, (
        "widget clipboard helper missing the non-secure-context fallback path"
    )


def test_templates_compose_widget_state():
    """Every template's saveState/restoreState IIFE must capture widget select +
    textarea state under `state.widgets`."""
    for name in TEMPLATE_NAMES:
        text = (TEMPLATES_DIR / name).read_text()
        assert "state.widgets" in text, (
            f"{name} live-refresh IIFE missing widget-state composition (state.widgets)"
        )
        assert "data-widget-state" in text or "select.dropdown[data-id]" in text, (
            f"{name} live-refresh IIFE missing widget-state selector hook"
        )
        # Restore path must dispatch change events so the existing widget JS
        # rebuilds row class + prompt textarea after reload.
        assert "dispatchEvent" in text, (
            f"{name} restoreState missing `dispatchEvent(new Event('change'))` "
            f"to re-trigger widget refresh after reload"
        )


def test_widget_script_outside_live_refresh_delimiters():
    """The widget WIDGETS-SCRIPT block must not sit inside the LIVE-REFRESH
    delimiters — otherwise the strip-script rule would destroy widgets in
    committed snapshots."""
    text = WIDGETS_PARTIAL.read_text()
    # The sidecar itself must not even contain the LIVE-REFRESH delimiters —
    # they belong only to the template's auto-refresh IIFE.
    assert "<!-- LIVE-REFRESH-START -->" not in text, (
        "widgets.html must not contain LIVE-REFRESH-START — widget JS must live "
        "in a separate <script> block outside the strip-script delimiters"
    )
    assert "<!-- LIVE-REFRESH-END -->" not in text, (
        "widgets.html must not contain LIVE-REFRESH-END"
    )


def test_widget_selects_carry_dropdown_class():
    """Selector contract: every `<select data-id=...>` in widgets.html MUST
    include `dropdown` in its class attribute, otherwise the state-composition
    selector `select.dropdown[data-id]` misses it on save/restore."""
    text = WIDGETS_PARTIAL.read_text()
    # Find every <select ... data-id="..."> opener and verify it carries
    # `class="..."` with a `dropdown` token. A select with data-id but no
    # `dropdown` class would be a contract violation.
    bad = re.findall(
        r"<select(?![^>]*\bclass\s*=\s*['\"][^'\"]*\bdropdown\b)[^>]*\bdata-id\b[^>]*>",
        text,
    )
    assert not bad, (
        "every widget <select data-id=...> must carry `dropdown` in its class "
        "attribute — `q-dropdown` alone is not sufficient. Offenders: "
        + repr(bad[:3])
    )
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py -v`

Expected: 9 failures (widgets.html missing; templates have no `state.widgets`). One test (`test_template_md5_equality`) will pass because the four templates are byte-identical today.

**Step 3: Commit**

```bash
git add e2e/tests/test_brainstorm_widgets.py
git commit -m "test(brainstorming): add failing widget sidecar + state-composition tests"
```

---

### ✅ Task 2: Build widgets.html sidecar CSS + widget HTML blocks

**Files:**
- Create: `skills/brainstorming/references/widgets.html`

**Step 1: Re-confirm the failing tests**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_widgets_partial_exists -v`
Expected: FAIL with "widgets sidecar partial must exist".

**Step 2: Write the sidecar shell with CSS + 5 widget HTML blocks**

Create `skills/brainstorming/references/widgets.html`. Place all five `<!-- WIDGET-HTML: ... -->` blocks plus the CSS-START/END and SCRIPT-START/END markers. The SCRIPT block can be a stub at this task; full IIFE logic lands in Task 3.

```html
<!--
  Interactive widgets sidecar for the brainstorming skill.

  Read this file during the visualization phase when the active design produced
  a Decision Log (>=1 entry) or an Open Questions list (>=1 entry). Inject:

    1. The WIDGETS-CSS block once into the template's <head> (after the inline
       <style> block).
    2. The WIDGETS-SCRIPT block once before </body>. It MUST land OUTSIDE the
       <!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END --> delimiters so
       the strip-script rule preserves widget JS in committed snapshots.
    3. The relevant WIDGET-HTML block(s) inside their owning <section>.

  Categorization threshold: use the flat variant when entries < 10. Use the
  categorized variant (with section-divider rows grouping decisions/questions
  by theme) when entries >= 10.

  data-id contract: every triage row carries `data-id="N"` and
  `data-title="..."`. Section-divider rows carry class `section-divider` and
  no data-id, so the JS selector `tbody tr[data-id]` skips them.
-->

<!-- WIDGETS-CSS-START -->
<style>
  .interactive-section {
    background: var(--color-accent-subtle);
    border-radius: 12px;
    padding: 24px 28px 32px;
    margin: 32px -28px;
  }
  .interactive-banner {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 13px;
    color: var(--color-foreground);
  }
  .interactive-banner .icon { color: var(--color-accent); font-size: 16px; line-height: 1; flex-shrink: 0; margin-top: 2px; }
  table.interactive td { vertical-align: middle; }
  table.interactive .decision-num { font-feature-settings: 'tnum'; color: var(--color-dimmed); font-weight: 500; }
  table.interactive .decision-title { font-weight: 500; color: var(--color-foreground); }
  table.interactive td.decision-desc { font-size: 13px; color: var(--color-secondary); line-height: 1.5; }

  select.dropdown { font-family: var(--font-sans); font-size: 13px; padding: 6px 10px; border: 1px solid var(--color-border); border-radius: 6px; background: var(--color-surface); color: var(--color-foreground); cursor: pointer; min-width: 110px; }
  select.dropdown:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-subtle); }
  select.dropdown.reject, select.dropdown.include { color: var(--color-accent); font-weight: 500; border-color: var(--color-accent); background: var(--color-accent-subtle); }
  select.dropdown.q-reject { color: #b91c1c; font-weight: 500; border-color: #b91c1c; background: #fef2f2; }

  tr.row-active td { background: var(--color-accent-subtle) !important; }
  tr.row-rejected td { background: #fef2f2 !important; }
  tr.row-rejected td.decision-title, tr.row-rejected td:nth-child(2) { opacity: 0.7; text-decoration: line-through; text-decoration-color: #b91c1c; text-decoration-thickness: 1px; }

  tr.section-divider td { background: var(--color-muted); color: var(--color-foreground); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; padding: 14px 16px; border-top: 1px solid var(--color-border); border-bottom: 1px solid var(--color-border); }
  tr.section-divider:first-child td { border-top: none; }
  tr.section-divider .section-letter { color: var(--color-accent); font-weight: 700; margin-right: 10px; }
  tr.section-divider .section-count { color: var(--color-dimmed); font-weight: 400; margin-left: 8px; letter-spacing: 0.04em; text-transform: none; font-style: italic; }

  .prompt-box { margin-top: 20px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 12px; padding: 20px; }
  .prompt-box-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .prompt-box-label { font-size: 13px; font-weight: 600; color: var(--color-foreground); text-transform: uppercase; letter-spacing: 0.06em; }
  .prompt-actions { display: flex; gap: 8px; }
  .btn { font-family: var(--font-sans); font-size: 12px; padding: 6px 14px; border-radius: 6px; cursor: pointer; border: 1px solid var(--color-border); background: var(--color-muted); color: var(--color-foreground); font-weight: 500; }
  .btn:hover { background: var(--color-accent-subtle); border-color: var(--color-accent); }
  .btn-primary { background: var(--color-accent); color: white; border-color: var(--color-accent); }
  .btn-primary:hover { background: var(--color-accent-hover); border-color: var(--color-accent-hover); }
  .btn.copied { background: #047857; color: white; border-color: #047857; }
  .btn.btn-error { background: #b91c1c; color: white; border-color: #b91c1c; }

  textarea.prompt-textarea { width: 100%; min-height: 160px; padding: 14px 16px; font-family: var(--font-mono); font-size: 13px; line-height: 1.6; color: var(--color-foreground); background: var(--color-muted); border: 1px solid var(--color-border); border-radius: 8px; resize: vertical; }
  textarea.prompt-textarea:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-subtle); }
  .prompt-hint { margin-top: 8px; font-size: 12px; color: var(--color-dimmed); font-style: italic; }
</style>
<!-- WIDGETS-CSS-END -->

<!-- WIDGETS-SCRIPT-START -->
<script>
  // Stub — replaced in Task 3 with two guarded IIFEs.
</script>
<!-- WIDGETS-SCRIPT-END -->

<!-- WIDGET-HTML: decision-log-flat -->
<!--
  Use when Decision Log has < 10 entries. Drop into the owning <section> in place
  of the static Decision Log table. Each <tr> needs data-id and data-title.
-->
<div class="interactive-section">
  <div class="interactive-banner">
    <span class="icon">●</span>
    <div><strong>Two options per decision.</strong> <em>Approve</em> (default) means you accept it. <em>Reject</em> queues it for revision. The prompt textarea below auto-updates as you toggle dropdowns.</div>
  </div>
  <table class="interactive" id="decisions-table">
    <thead><tr><th class="num">#</th><th>Decision</th><th>Rationale</th><th style="width: 130px">Status</th></tr></thead>
    <tbody>
      <!-- One <tr data-id="N" data-title="..."> per decision; final <td> contains:
        <select class="dropdown" data-id="N"><option value="approve">Approve</option><option value="reject">Reject</option></select>
      -->
    </tbody>
  </table>
  <!-- prompt-box block: see WIDGET-HTML: prompt-box -->
</div>

<!-- WIDGET-HTML: decision-log-categorized -->
<!--
  Use when Decision Log has >= 10 entries. Identical to decision-log-flat except
  the <tbody> contains `<tr class="section-divider">` rows grouping decisions
  by theme (A, B, C ...). Section-divider rows have NO data-id.

  Example:
    <tr class="section-divider">
      <td colspan="4"><span class="section-letter">A</span>Architecture<span class="section-count">3 decisions</span></td>
    </tr>
-->

<!-- WIDGET-HTML: open-questions-flat -->
<!--
  Use when Open Questions has < 10 entries. Three-state dropdown:
    <select class="dropdown q-dropdown" data-id="N">
      <option value="defer">Defer</option>
      <option value="include">Include</option>
      <option value="reject">Reject</option>
    </select>
-->
<div class="interactive-section">
  <div class="interactive-banner">
    <span class="icon">●</span>
    <div><strong>Three options per question.</strong> <em>Defer</em> (default) keeps it on the list for later. <em>Include</em> queues it for me to ask you interactively now. <em>Reject</em> removes it from the list entirely. The prompt below auto-updates as you change dropdowns.</div>
  </div>
  <table class="interactive" id="questions-table">
    <thead><tr><th class="num">#</th><th>Question</th><th>Trigger that would resolve it</th><th style="width: 130px">Status</th></tr></thead>
    <tbody>
      <!-- One <tr data-id="N" data-title="..."> per question. -->
    </tbody>
  </table>
  <!-- prompt-box block: see WIDGET-HTML: prompt-box -->
</div>

<!-- WIDGET-HTML: open-questions-categorized -->
<!--
  Use when Open Questions has >= 10 entries. Identical to open-questions-flat
  except <tbody> contains `<tr class="section-divider">` rows grouping questions
  by theme.
-->

<!-- WIDGET-HTML: prompt-box -->
<!--
  Reusable footer for both widget tables. Inject inside `.interactive-section`
  after the table. Set `id="decisions-prompt"` / `id="questions-prompt"` and
  matching button IDs (`copy-decisions`, `regenerate-decisions`, etc.).
-->
<div class="prompt-box">
  <div class="prompt-box-header">
    <span class="prompt-box-label">Prompt to send back</span>
    <div class="prompt-actions">
      <button class="btn" id="regenerate-{widget-id}" type="button">Regenerate</button>
      <button class="btn btn-primary" id="copy-{widget-id}" type="button">Copy</button>
    </div>
  </div>
  <textarea class="prompt-textarea" id="{widget-id}-prompt" spellcheck="false"></textarea>
  <p class="prompt-hint">Textarea auto-updates when you change a dropdown. Edit freely before copying.</p>
</div>
```

**Step 3: Run tests to confirm partial scaffold passes**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_widgets_partial_exists e2e/tests/test_brainstorm_widgets.py::test_widgets_partial_has_required_block_markers e2e/tests/test_brainstorm_widgets.py::test_widget_selector_lint_no_bare_tbody_tr e2e/tests/test_brainstorm_widgets.py::test_widget_script_outside_live_refresh_delimiters -v`
Expected: 4 PASS.

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_widget_isolation_guards_present e2e/tests/test_brainstorm_widgets.py::test_widget_empty_tbody_renders_hint e2e/tests/test_brainstorm_widgets.py::test_widget_clipboard_fallback_present e2e/tests/test_brainstorm_widgets.py::test_widget_selects_carry_dropdown_class -v`
Expected: 3 FAIL (script block still a stub) + 1 PASS (`test_widget_selects_carry_dropdown_class` — Task 2's HTML blocks already declare the right classes).

**Step 4: Commit**

```bash
git add skills/brainstorming/references/widgets.html
git commit -m "feat(brainstorming): add widgets sidecar CSS + HTML blocks"
```

---

### ✅ Task 3: Build the widget JS — two guarded IIFEs, dirty-flag textareas, clipboard fallback

**Files:**
- Modify: `skills/brainstorming/references/widgets.html` (replace the SCRIPT stub with full IIFE logic)

**Step 1: Re-confirm the failing tests**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_widget_isolation_guards_present e2e/tests/test_brainstorm_widgets.py::test_widget_empty_tbody_renders_hint e2e/tests/test_brainstorm_widgets.py::test_widget_clipboard_fallback_present -v`
Expected: 3 FAIL (the stub script has none of these).

**Step 2: Replace the SCRIPT stub with the full IIFE block**

In `widgets.html`, replace the `<!-- WIDGETS-SCRIPT-START -->...<!-- WIDGETS-SCRIPT-END -->` block with:

```html
<!-- WIDGETS-SCRIPT-START -->
<script>
  (function() {
    'use strict';

    // Clipboard helper with file:// / non-secure-context fallback.
    function copyToClipboard(text, btn) {
      var originalLabel = btn.dataset.originalLabel || btn.textContent;
      btn.dataset.originalLabel = originalLabel;
      var showSuccess = function() {
        btn.textContent = 'Copied ✓';
        btn.classList.add('copied');
        setTimeout(function() {
          btn.textContent = originalLabel;
          btn.classList.remove('copied');
        }, 1800);
      };
      var showFailure = function() {
        btn.textContent = 'Copy failed — select & Cmd-C';
        btn.classList.add('btn-error');
        setTimeout(function() {
          btn.textContent = originalLabel;
          btn.classList.remove('btn-error');
        }, 3000);
      };
      if (!navigator.clipboard || !window.isSecureContext) {
        // Synchronous fallback for file:// origins and Safari/Firefox non-HTTPS.
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
        document.body.removeChild(ta);
        if (ok) showSuccess(); else showFailure();
        return;
      }
      navigator.clipboard.writeText(text).then(showSuccess).catch(showFailure);
    }

    function markDirtyOnInput(textarea) {
      textarea.addEventListener('input', function() {
        textarea.dataset.dirty = 'true';
      });
    }

    // ── DECISION LOG ─────────────────────────────────────────────
    (function decisionLogWidget() {
      if (!document.getElementById('decisions-table')) return;
      var table = document.getElementById('decisions-table');
      var prompt = document.getElementById('decisions-prompt');
      var copyBtn = document.getElementById('copy-decisions');
      var regenBtn = document.getElementById('regenerate-decisions');
      if (!prompt || !copyBtn || !regenBtn) return;

      function rows() {
        return Array.prototype.slice.call(table.querySelectorAll('tbody tr[data-id]'));
      }

      function buildPrompt() {
        var allRows = rows();
        if (allRows.length === 0) {
          return 'No decisions captured for this design. Either remove this section or add entries before triaging.';
        }
        var rejected = allRows
          .filter(function(tr) { var sel = tr.querySelector('select'); return sel && sel.value === 'reject'; })
          .map(function(tr) { return { num: tr.dataset.id, title: tr.dataset.title || '' }; });
        if (rejected.length === 0) {
          return 'All decisions approved.\n\nProceed to the implementation plan or wait for me to flag remaining concerns.';
        }
        var lines = ["I've reviewed this design and I'm rejecting the following decisions:", ''];
        rejected.forEach(function(d) {
          lines.push('  • Decision #' + d.num + ' — ' + d.title);
          lines.push('    Reason: <add your reason here>');
          lines.push('');
        });
        lines.push('Please revise the design to address these rejections and re-present.');
        lines.push('');
        lines.push('If you have an alternative recommendation for any of these, propose it before I commit to a replacement.');
        return lines.join('\n');
      }

      function updateRow(select) {
        var tr = select.closest('tr');
        if (!tr) return;
        if (select.value === 'reject') {
          select.classList.add('reject');
          tr.classList.add('row-active');
        } else {
          select.classList.remove('reject');
          tr.classList.remove('row-active');
        }
      }

      function refresh() {
        if (prompt.dataset.dirty === 'true') return;  // user edits survive
        prompt.value = buildPrompt();
      }

      table.querySelectorAll('select[data-id]').forEach(function(sel) {
        sel.addEventListener('change', function() {
          updateRow(sel);
          refresh();
        });
        updateRow(sel);  // sync initial classes for restored state
      });

      markDirtyOnInput(prompt);
      regenBtn.addEventListener('click', function() {
        prompt.dataset.dirty = 'false';
        refresh();
      });
      copyBtn.addEventListener('click', function() { copyToClipboard(prompt.value, copyBtn); });

      refresh();
    })();

    // ── OPEN QUESTIONS ───────────────────────────────────────────
    (function openQuestionsWidget() {
      if (!document.getElementById('questions-table')) return;
      var table = document.getElementById('questions-table');
      var prompt = document.getElementById('questions-prompt');
      var copyBtn = document.getElementById('copy-questions');
      var regenBtn = document.getElementById('regenerate-questions');
      if (!prompt || !copyBtn || !regenBtn) return;

      function rows() {
        return Array.prototype.slice.call(table.querySelectorAll('tbody tr[data-id]'));
      }

      function buildPrompt() {
        var allRows = rows();
        if (allRows.length === 0) {
          return 'No open questions captured for this design. Either remove this section or add entries before triaging.';
        }
        var included = allRows
          .filter(function(tr) { var s = tr.querySelector('select'); return s && s.value === 'include'; })
          .map(function(tr) { return { num: tr.dataset.id, title: tr.dataset.title || '' }; });
        var rejected = allRows
          .filter(function(tr) { var s = tr.querySelector('select'); return s && s.value === 'reject'; })
          .map(function(tr) { return { num: tr.dataset.id, title: tr.dataset.title || '' }; });
        if (included.length === 0 && rejected.length === 0) {
          return 'All open questions deferred.\n\nProceed with the design as-is; we will resolve these as the named triggers fire.';
        }
        var lines = ['Open-questions review:', ''];
        if (included.length > 0) {
          lines.push('ASK ME NOW (resolve interactively, one at a time):');
          included.forEach(function(q) { lines.push('  • Question #' + q.num + ' — ' + q.title); });
          lines.push('');
          lines.push("For these: please ask me one at a time. Use multiple-choice options when reasonable. Don't assume answers — wait for my response before moving to the next.");
          lines.push('');
        }
        if (rejected.length > 0) {
          lines.push('REJECT (remove from open-questions list entirely — not worth asking now or later):');
          rejected.forEach(function(q) {
            lines.push('  • Question #' + q.num + ' — ' + q.title);
            lines.push('    Reason: <add your reason here, or leave blank>');
          });
          lines.push('');
          lines.push("For these: drop them from the design's Open Questions section. Update the design doc and HTML to reflect their removal.");
          lines.push('');
        }
        if (included.length > 0 && rejected.length > 0) {
          lines.push('Handle the REJECT items first (housekeeping), then start the ASK ME NOW questions.');
        }
        return lines.join('\n');
      }

      function updateRow(select) {
        var tr = select.closest('tr');
        if (!tr) return;
        select.classList.remove('include', 'q-reject');
        tr.classList.remove('row-active', 'row-rejected');
        if (select.value === 'include') {
          select.classList.add('include');
          tr.classList.add('row-active');
        } else if (select.value === 'reject') {
          select.classList.add('q-reject');
          tr.classList.add('row-rejected');
        }
      }

      function refresh() {
        if (prompt.dataset.dirty === 'true') return;
        prompt.value = buildPrompt();
      }

      table.querySelectorAll('select[data-id]').forEach(function(sel) {
        sel.addEventListener('change', function() {
          updateRow(sel);
          refresh();
        });
        updateRow(sel);
      });

      markDirtyOnInput(prompt);
      regenBtn.addEventListener('click', function() {
        prompt.dataset.dirty = 'false';
        refresh();
      });
      copyBtn.addEventListener('click', function() { copyToClipboard(prompt.value, copyBtn); });

      refresh();
    })();
  })();
</script>
<!-- WIDGETS-SCRIPT-END -->
```

**Step 3: Run tests to confirm widget JS branch coverage**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py -v`
Expected: 9 PASS, 1 FAIL (`test_templates_compose_widget_state` — templates not yet extended).

**Step 4: Commit**

```bash
git add skills/brainstorming/references/widgets.html
git commit -m "feat(brainstorming): wire decision-log + open-questions widget IIFEs"
```

---

### ✅ Task 4: Extend live-refresh IIFE to compose widget state — all four templates

> **Dependency note:** This task touches all four template files in a single commit. The md5-equality lint requires byte-identity, so partial commits are not allowed. Make the same diff to all four files before committing.

**Files:**
- Modify: `skills/brainstorming/references/templates/software-template.html` (the `saveState`/`restoreState` IIFE between `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->`)
- Modify: `skills/brainstorming/references/templates/authoring-template.html` (identical change)
- Modify: `skills/brainstorming/references/templates/business-template.html` (identical change)
- Modify: `skills/brainstorming/references/templates/planning-template.html` (identical change)

**Step 1: Re-confirm the failing test**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_templates_compose_widget_state -v`
Expected: FAIL with "missing widget-state composition".

**Step 2: Extend `saveState` and `restoreState` in software-template.html**

Inside `saveState`, after the `sessionStorage.setItem(STATE_KEY, JSON.stringify(state));` line is built but BEFORE the call, add widget capture. The existing block currently reads:

```js
var state = { tab: null, subTabs: {}, scrollY: window.scrollY };
```

Replace the body of `saveState` (between `try {` and the final `setItem`) with:

```js
var state = { tab: null, subTabs: {}, scrollY: window.scrollY, widgets: { selects: {}, textareas: {} } };
var activeTabBtn = document.querySelector('#main-tabs .tab-btn.active');
if (activeTabBtn) {
  var m = (activeTabBtn.getAttribute('onclick') || '').match(/switchTab\('([^']+)'\)/);
  if (m) state.tab = m[1];
}
document.querySelectorAll('.tab-panel').forEach(function(panel) {
  var activeSubBtn = panel.querySelector('.sub-tab-btn.active');
  if (!activeSubBtn) return;
  var sm = (activeSubBtn.getAttribute('onclick') || '').match(/switchSubTab\('([^']+)',\s*'([^']+)'\)/);
  if (sm) state.subTabs[sm[1]] = sm[2];
});
// Widget state — every triage <select data-id> + every prompt textarea.
// Wrap in its own try so a widget-side failure can't disable tab/sub-tab/scrollY
// persistence (which used to be wrapped only by the outer try/catch).
try {
  document.querySelectorAll('select.dropdown[data-id]').forEach(function(sel) {
    var table = sel.closest('table');
    var tableId = (table && table.id) ? table.id : 'orphan';
    state.widgets.selects[tableId + ':' + sel.dataset.id] = sel.value;
  });
  document.querySelectorAll('textarea.prompt-textarea').forEach(function(ta) {
    if (!ta.id) return;
    state.widgets.textareas[ta.id] = { value: ta.value, dirty: ta.dataset.dirty === 'true' };
  });
} catch (we) {
  // Widget capture failed — preserve everything else by clearing the partial.
  state.widgets = { selects: {}, textareas: {} };
}
sessionStorage.setItem(STATE_KEY, JSON.stringify(state));
```

Inside `restoreState`, after `if (typeof state.scrollY === 'number') window.scrollTo(0, state.scrollY);`, BEFORE the closing `} catch (e)`, add:

```js
if (state.widgets) {
  // Inner try/catch so widget restore failure can't disable tab/sub-tab/scrollY restore.
  try {
    if (state.widgets.selects) {
      Object.keys(state.widgets.selects).forEach(function(key) {
        var parts = key.split(':');
        var tableId = parts[0];
        var dataId = parts[1];
        var sel = document.querySelector('#' + tableId + ' select[data-id="' + dataId + '"]');
        if (sel) {
          sel.value = state.widgets.selects[key];
          // Re-fire change so the widget JS rebuilds row class + prompt textarea.
          sel.dispatchEvent(new Event('change'));
        }
      });
    }
    if (state.widgets.textareas) {
      Object.keys(state.widgets.textareas).forEach(function(id) {
        var ta = document.getElementById(id);
        if (!ta) return;
        var entry = state.widgets.textareas[id];
        ta.value = entry.value;
        if (entry.dirty) ta.dataset.dirty = 'true';
      });
    }
  } catch (we) { /* widget restore failed — leave widgets at default */ }
}
```

> **Behavior change:** The existing `saveState`/`restoreState` IIFE wrapped everything in a single outer `try/catch`. This task adds inner try/catches around the widget capture and restore loops so a widget-side malformation can't disable the previously-working tab/sub-tab/scrollY persistence. Pre-existing behavior is preserved as a strict superset.

**Step 3: Mirror the change to the other three templates**

The four templates start as byte-identical copies and must remain so. Apply the EXACT same diff to:
- `skills/brainstorming/references/templates/authoring-template.html`
- `skills/brainstorming/references/templates/business-template.html`
- `skills/brainstorming/references/templates/planning-template.html`

**Step 4: Verify md5 equality and run state-composition test**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_template_md5_equality -v`
Expected: PASS. (Cross-platform — uses Python `hashlib.md5`. macOS `md5` and Linux `md5sum` differ in CLI, so we use the pytest gate as the authoritative check.)

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py -v`
Expected: 10 PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/references/templates/*.html
git commit -m "feat(brainstorming): compose widget state into live-refresh IIFE (4 templates, md5-equal)"
```

---

### ✅ Task 5: Add strip-script integration test

**Files:**
- Modify: `e2e/tests/test_brainstorm_widgets.py` (append a new test)

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorm_widgets.py`:

```python
# Reference regex modeling the documented strip rule's intent. The actual strip
# in production is performed by an LLM agent following `shared-rules.md`'s
# natural-language instruction — there is no runtime regex. This test validates
# the STRUCTURAL CONTRACT that makes any reasonable strip implementation safe:
# the widget <script> block lives OUTSIDE the LIVE-REFRESH delimiters, so any
# strip that targets LIVE-REFRESH (by regex, by AST walk, or by human edit)
# necessarily preserves the widget JS.
STRIP_RE = re.compile(
    r"<!--\s*LIVE-REFRESH-START\s*-->.*?<!--\s*LIVE-REFRESH-END\s*-->",
    re.DOTALL,
)


def _strip_live_refresh(html: str) -> str:
    """Reference implementation of the LIVE-REFRESH strip — used only by this
    structural-contract test, not by the production code path."""
    return STRIP_RE.sub("", html)


def test_widget_script_block_is_structurally_outside_live_refresh():
    """STRUCTURAL CONTRACT: the widget <script> block must live outside the
    LIVE-REFRESH delimiters. Build a fixture that mirrors a real injected page
    (template + sidecar SCRIPT block + a decisions-table) and verify that
    stripping the LIVE-REFRESH range (by any implementation that uses those
    delimiters as anchors) leaves the widget block intact.

    This is NOT a claim that the production strip uses this exact regex — the
    production strip is performed by an LLM agent following shared-rules.md.
    The test asserts the structural property that ANY anchor-honoring strip
    implementation (regex, AST, human edit) preserves widget JS."""
    template = (TEMPLATES_DIR / "software-template.html").read_text()
    widgets = WIDGETS_PARTIAL.read_text()

    # Extract the WIDGETS-SCRIPT block from the sidecar.
    script_match = re.search(
        r"<!-- WIDGETS-SCRIPT-START -->.*?<!-- WIDGETS-SCRIPT-END -->",
        widgets,
        re.DOTALL,
    )
    assert script_match, "widgets.html must contain a WIDGETS-SCRIPT block"
    widget_script = script_match.group(0)

    # Build a fixture: template with widget script injected before </body>, plus a
    # decisions-table somewhere in the body so the bind would succeed at runtime.
    table_html = (
        '<table id="decisions-table"><tbody>'
        '<tr data-id="1" data-title="x"><td><select class="dropdown" data-id="1">'
        '<option value="approve">Approve</option><option value="reject">Reject</option>'
        '</select></td></tr></tbody></table>'
        '<textarea id="decisions-prompt" class="prompt-textarea"></textarea>'
        '<button id="copy-decisions" class="btn"></button>'
        '<button id="regenerate-decisions" class="btn"></button>'
    )
    fixture = template.replace(
        "</body>", table_html + "\n" + widget_script + "\n</body>"
    )

    # Pre-condition: both delimiter pairs present in the fixture.
    assert "<!-- LIVE-REFRESH-START -->" in fixture
    assert "<!-- WIDGETS-SCRIPT-START -->" in fixture

    # Pre-condition: the WIDGETS-SCRIPT range does not overlap the LIVE-REFRESH
    # range. (This is the structural contract — proven by index comparison.)
    lr_start = fixture.index("<!-- LIVE-REFRESH-START -->")
    lr_end = fixture.index("<!-- LIVE-REFRESH-END -->")
    ws_start = fixture.index("<!-- WIDGETS-SCRIPT-START -->")
    ws_end = fixture.index("<!-- WIDGETS-SCRIPT-END -->")
    assert not (lr_start <= ws_start <= lr_end) and not (lr_start <= ws_end <= lr_end), (
        "WIDGETS-SCRIPT block is structurally inside LIVE-REFRESH range — "
        "any strip that targets LIVE-REFRESH delimiters will destroy widget JS"
    )

    # Apply the reference strip and verify the structural property: widget JS
    # survives because it lives outside the targeted range.
    stripped = _strip_live_refresh(fixture)
    assert "<!-- LIVE-REFRESH-START -->" not in stripped
    assert "<!-- LIVE-REFRESH-END -->" not in stripped
    assert "<!-- WIDGETS-SCRIPT-START -->" in stripped, (
        "anchor-based LIVE-REFRESH strip removed the widget JS block — the "
        "WIDGETS-SCRIPT block must be injected outside LIVE-REFRESH delimiters"
    )
    assert "<!-- WIDGETS-SCRIPT-END -->" in stripped
    assert 'id="decisions-table"' in stripped
    assert "decisionLogWidget" in stripped or "decisions-table" in stripped
```

**Step 2: Run the test to verify the structural contract holds**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py::test_widget_script_block_is_structurally_outside_live_refresh -v`
Expected: PASS (because the WIDGETS-SCRIPT block was injected outside the LIVE-REFRESH delimiters in Task 2).

> If this test fails, the widget block was placed inside the LIVE-REFRESH delimiters somewhere — fix the injection order in `widgets.html` and re-run.

**Step 3: Commit**

```bash
git add e2e/tests/test_brainstorm_widgets.py
git commit -m "test(brainstorming): assert strip-script preserves widget JS in committed snapshots"
```

---

### ✅ Task 6: Document the Interactive Widgets component in brainstorm-components.md

**Files:**
- Modify: `skills/brainstorming/references/brainstorm-components.md` (append a new "Interactive Widgets" component section)

**Step 1: Read current Components section to find the append point**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py -v`
Expected: 11 PASS (Task 5 added the strip-script structural-contract test). No new failing test in this task — doc-only.

**Step 2: Append "Interactive Widgets" component subsection**

Add this section at the end of `brainstorm-components.md` (after the "Section Containers" subsection):

```markdown
---

### Interactive Widgets

Triage UI for the design doc's Decision Log and Open Questions sections. Lets the user toggle Approve/Reject (decisions) or Defer/Include/Reject (questions); a textarea below auto-builds a prompt the user can copy back into the conversation.

**Workflow step:** Post-critique snapshot — wire onto the committed mockup at `docs/mockups/{session-name}.html` whenever the design produced a Decision Log (>=1 entry) OR an Open Questions list (>=1 entry).

**Source:** All widget markup, CSS, and JS lives in `{base-directory}/references/widgets.html`. The model copies the relevant blocks verbatim into the live HTML during visualization — never regenerated from memory.

#### When to use each block

| Entries  | Decision Log block               | Open Questions block             |
| -------- | -------------------------------- | -------------------------------- |
| 1–9      | `WIDGET-HTML: decision-log-flat` | `WIDGET-HTML: open-questions-flat` |
| 10+      | `WIDGET-HTML: decision-log-categorized` | `WIDGET-HTML: open-questions-categorized` |

The categorized variants add `<tr class="section-divider">` rows grouping entries into themes (A, B, C ...). Below 10 entries, flat tables are clearer.

#### Sidecar contract

The model performs three injections during visualization:

1. **WIDGETS-CSS** — one copy, inside `<head>` after the inline `<style>` block.
2. **WIDGETS-SCRIPT** — one copy, immediately before `</body>`. **MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** — otherwise the strip-script rule destroys the widget JS in the committed snapshot.
3. **WIDGET-HTML blocks** — inside the owning `<section>` (Decision Log section gets a `decision-log-*` block; Open Questions section gets an `open-questions-*` block). Both wrap in `.interactive-section`. The reusable `WIDGET-HTML: prompt-box` block follows each table.

#### data-id contract (stable IDs)

Every triage row carries:
- `data-id="N"` — the decision/question number. Stable across reorderings; cross-references in prose (e.g., "see Decision #14") survive categorization.
- `data-title="..."` — the headline used in the generated prompt text.

Section-divider rows do **not** have `data-id`. The JS selector `tbody tr[data-id]` skips them. Never use bare `tbody tr` — it crashes on dividers.

#### Selector contract (state-composition hook)

Every widget `<select>` MUST include `dropdown` in its `class` attribute (e.g., `class="dropdown"` for decisions, `class="dropdown q-dropdown"` for questions). The `saveState`/`restoreState` IIFE uses the selector `select.dropdown[data-id]` to detect widget state — a select that carries `data-id` but lacks the `dropdown` class token is invisible to the persistence layer and its value will be lost on reload. The `q-dropdown` class is a styling-only addition; `dropdown` is the contract.

#### `{widget-id}` substitution contract

The `WIDGET-HTML: prompt-box` block contains a `{widget-id}` placeholder. Valid values are exactly:
- `decisions` — for the Decision Log widget (produces IDs `decisions-prompt`, `copy-decisions`, `regenerate-decisions`).
- `questions` — for the Open Questions widget (produces IDs `questions-prompt`, `copy-questions`, `regenerate-questions`).

The widget JS hardcodes these IDs. A third triage type would substitute syntactically but never bind at runtime — adding a new widget requires editing both the sidecar JS and this contract.

#### State composition (live-refresh persistence)

The template's `saveState`/`restoreState` IIFE captures and restores widget state across the 15-second refresh. The author of the widget HTML doesn't need to wire anything extra — the IIFE auto-detects `select.dropdown[data-id]` and `textarea.prompt-textarea` instances and stores them under `state.widgets.selects` / `state.widgets.textareas`. After reload, dispatched `change` events re-trigger the widget IIFEs' row-class and prompt-textarea rebuild paths.

User edits to the prompt textarea are protected by a dirty flag (`data-dirty="true"`) — auto-refresh respects it so a hand-edited prompt is not clobbered on next dropdown change or next 15-second reload.

#### Empty-state behavior

If a widget's `<tbody>` has zero `tr[data-id]` rows, the prompt textarea renders the hint *"No {decisions|open questions} captured for this design. Either remove this section or add entries before triaging."* — not a false "all approved" message.

#### Clipboard fallback

Committed snapshots open at `file://` (not a secure context). The Copy button uses `navigator.clipboard.writeText` when available and falls back to `document.execCommand('copy')` via a temporary `<textarea>` otherwise. Failure surfaces in the button label as "Copy failed — select & Cmd-C" for 3 seconds, then reverts.
```

**Step 3: Commit**

```bash
git add skills/brainstorming/references/brainstorm-components.md
git commit -m "docs(brainstorming): document Interactive Widgets component contract"
```

---

### Task 7: Add widget-injection step to visualization-protocol.md

**Files:**
- Modify: `skills/brainstorming/references/visualization-protocol.md` (append a new step after step 5 of the Live phase, or place inside the Pre-critique snapshot section — whichever ordering matches the design intent)

**Step 1: Read current "Live phase" + "Pre-critique snapshot" sections**

Re-read `skills/brainstorming/references/visualization-protocol.md` to choose the insertion point. The widgets are most appropriately injected **after** step 5 of the Live phase (each section as it's validated) and verified again during the Pre-critique snapshot.

**Step 2: Add a Step 6 to the Live phase**

After step 5 ("Update the file as each subsequent design section is validated..."), append:

```markdown
6. **Inject interactive widgets if the design produced a Decision Log (>=1 entry) or an Open Questions list (>=1 entry).** Read `{base-directory}/references/widgets.html` and perform three injections into `/tmp/brainstorm-{topic}-{timestamp}/live.html`:

   a. **WIDGETS-CSS block** — insert once into `<head>` after the inline `<style>` block. Copy verbatim between (and including) `<!-- WIDGETS-CSS-START -->` and `<!-- WIDGETS-CSS-END -->`.

   b. **WIDGETS-SCRIPT block** — insert once immediately before `</body>`. Copy verbatim between (and including) `<!-- WIDGETS-SCRIPT-START -->` and `<!-- WIDGETS-SCRIPT-END -->`. **The block MUST land outside the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters** so the strip-script rule preserves widget JS in committed snapshots.

   c. **WIDGET-HTML blocks** — for the Decision Log section, copy `WIDGET-HTML: decision-log-flat` (if <10 entries) or `WIDGET-HTML: decision-log-categorized` (if >=10 entries) into the Decision Log `<section>`, then append the `WIDGET-HTML: prompt-box` block with `{widget-id}` substituted to `decisions`. For the Open Questions section, mirror the same with `open-questions-*` and `{widget-id}` = `questions`. Every triage row must carry `data-id="N"` and `data-title="..."`; section-divider rows must carry class `section-divider` and no `data-id` (see `brainstorm-components.md` § Interactive Widgets).

   Do not rewrite the widget code from memory — the file copy is the contract.
```

**Step 3: Add a verification line to the Pre-critique snapshot section**

In the "Pre-critique snapshot" section (between steps 1 and 3), add a step 2.5:

```markdown
2.5. If the design includes a Decision Log or Open Questions widget, verify that the committed snapshot at `docs/mockups/{session-name}.html` still contains the `<!-- WIDGETS-SCRIPT-START -->` marker and that the widget tables (`id="decisions-table"`, `id="questions-table"`) bind on load (open the file in a browser — the prompt textareas should populate without console errors).
```

**Step 4: Add widget re-injection to the Post-critique regeneration section**

The existing "Post-critique regeneration" section (currently 4 bullets describing template re-copy + brand-token preservation) re-copies the template verbatim, which has no widgets. After regeneration, the widgets would be missing from the committed snapshot.

In the "Post-critique regeneration" section, add a new bullet (or paragraph) immediately before the line "After regeneration (or if no regeneration was needed), apply the strip-script rule from ...":

```markdown
- **Re-inject interactive widgets** if the corrected design still contains a Decision Log (>=1 entry) or Open Questions list (>=1 entry). Re-run the Live-phase step 6 widget-injection procedure (Read `{base-directory}/references/widgets.html`; inject CSS into `<head>`, SCRIPT before `</body>` outside LIVE-REFRESH delimiters, HTML blocks inside their owning sections). The widget JS must land in the regenerated file BEFORE the strip-script rule runs, otherwise the committed snapshot ships without the interactive surface.
```

**Step 5: Commit**

```bash
git add skills/brainstorming/references/visualization-protocol.md
git commit -m "docs(brainstorming): inject widgets in Live + Pre-critique + Post-critique regen paths"
```

---

### Task 8: Strengthen the strip-script rule with widget-survival assertion

**Files:**
- Modify: `skills/brainstorming/references/shared-rules.md` (the "Stripping the live-refresh script" section)

**Step 1: Append a positive assertion to the strip-script rule**

In `shared-rules.md`, find the section "Stripping the live-refresh script" (the existing paragraph that says *"...remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh."*) and append a new paragraph:

```markdown
**Widget survival.** After stripping, any widget tables (`decisions-table`, `questions-table`) and their `WIDGETS-SCRIPT` block MUST still be present and bind on load. Widget code lives in a separate `<script>` block delimited by `<!-- WIDGETS-SCRIPT-START -->` / `<!-- WIDGETS-SCRIPT-END -->`, outside the LIVE-REFRESH delimiters. If a committed snapshot is missing the widget script after a strip, the widget block was injected inside the LIVE-REFRESH delimiters by mistake — re-run the visualization-protocol's widget-injection step and verify the block lands before `</body>` and AFTER `<!-- LIVE-REFRESH-END -->`.
```

**Step 2: Commit**

```bash
git add skills/brainstorming/references/shared-rules.md
git commit -m "docs(brainstorming): require widget survival in strip-script rule"
```

---

### Task 9: Mandate widget injection in all four mode files

**Files:**
- Modify: `skills/brainstorming/modes/software.md`
- Modify: `skills/brainstorming/modes/authoring.md`
- Modify: `skills/brainstorming/modes/business.md`
- Modify: `skills/brainstorming/modes/planning.md`

**Step 1: Locate the Visualization subsection in each file (headings differ)**

The four mode files use four different Visualization headings — do not search for one literal string. Use these anchors (verified by `grep -n '^\*\*Visualization' skills/brainstorming/modes/*.md` at plan-write time):

| File                  | Heading anchor (prefix-match `**Visualization (`)                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `modes/software.md`   | `**Visualization (mandatory):**`                                                                                                                        |
| `modes/business.md`   | `**Visualization (conditional):**`                                                                                                                      |
| `modes/planning.md`   | `**Visualization (conditional — most planning brainstorms produce dependency-map / sequencing visualizations):**`                                       |
| `modes/authoring.md`  | `**Visualization (mandatory for content-with-structure designs; optional for pure prose):**`                                                            |

The Visualization paragraph that follows each heading instructs the model to read `references/visualization-protocol.md`. Find the END of that paragraph (typically a blank line followed by the next `**...:**` section header) and insert the new paragraph there.

**Step 2: Append the widget-injection mandate**

Immediately after the existing Visualization paragraph in each file (and BEFORE the next `**...:**` section), append:

```markdown
**Interactive widgets (conditional, mandatory when triggered):**

If the design produced a Decision Log with >=1 entry OR an Open Questions list with >=1 entry, the visualization protocol's widget-injection step is **mandatory** (not optional). Use the categorized variant of either widget when the corresponding count is >=10; use the flat variant below 10. See `{base-directory}/references/widgets.html` and `{base-directory}/references/brainstorm-components.md` § Interactive Widgets.
```

Apply the **identical** paragraph to all four mode files so they remain consistent.

**Step 3: Commit**

```bash
git add skills/brainstorming/modes/software.md skills/brainstorming/modes/authoring.md skills/brainstorming/modes/business.md skills/brainstorming/modes/planning.md
git commit -m "docs(brainstorming): mandate widget injection when triage entries exist (4 modes)"
```

---

### Task 10: Extend criterion 9 in all five critique checklists to cover Open Questions

**Files:**
- Modify: `skills/brainstorming/design-critique-checklist.md` (criterion 9, the "Decision quality" heading)
- Modify: `skills/brainstorming/authoring-critique-checklist.md` (criterion 9)
- Modify: `skills/brainstorming/business-critique-checklist.md` (criterion 9)
- Modify: `skills/brainstorming/planning-critique-checklist.md` (criterion 9)
- Modify: `skills/brainstorming/research-critique-checklist.md` (criterion 9)

> **Scope note for research:** Research mode skips the visualization protocol (per `visualization-protocol.md:1`) and therefore never gets interactive widgets. However, research synthesis files use `## Open Questions` as a markdown heading — the same triage-quality criterion applies there. The wording change extends criterion 9 uniformly across all 5 checklists; the trigger is "Open Questions list present in the artifact," not "interactive widget present in HTML."

**Step 1: Read current criterion 9 in each file**

Re-read each file's criterion 9 ("Decision quality (if Decision Log present)") to find the exact wording. The header is `### 9. Decision quality (if Decision Log present)`; the body opens with `If the design includes a Decision Log, evaluate each decision entry.` (or `If the plan includes a Decision Log...` for planning/research).

**Step 2: Edit the criterion-9 header and intro**

In each of the five files, replace:
- Heading `### 9. Decision quality (if Decision Log present)` → `### 9. Decision quality (if Decision Log or Open Questions list present)`
- Intro `If the design includes a Decision Log, evaluate each decision entry.` → `If the design includes a Decision Log or an Open Questions list, evaluate each decision entry and each open-questions triage call.` (mirror the wording for "plan" / "synthesis" / "roadmap" / "portfolio" as the surrounding file uses).
- The "Rate each: sound/questionable/wrong" bullet — leave as-is; it applies to both kinds of entries.
- "If no Decision Log is present, mark N/A" → "If no Decision Log or Open Questions list is present, mark N/A."

Also add one additional bullet under criterion 9 in each file:

```markdown
- For each Open Questions entry, assess whether the named *trigger that would resolve it* is concrete and observable, or vague enough that the question will never actually re-fire. Vague triggers are a smell.
```

**Step 3: Commit**

```bash
git add skills/brainstorming/design-critique-checklist.md skills/brainstorming/authoring-critique-checklist.md skills/brainstorming/business-critique-checklist.md skills/brainstorming/planning-critique-checklist.md skills/brainstorming/research-critique-checklist.md
git commit -m "docs(brainstorming): extend criterion 9 to evaluate Open Questions triage entries"
```

---

### Task 11: Bump plugin version

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Bump version from 0.28.0 to 0.29.0 in both manifests**

In `.claude-plugin/plugin.json`, change `"version": "0.28.0"` → `"version": "0.29.0"`.

In `.claude-plugin/marketplace.json`, change `"version": "0.28.0"` → `"version": "0.29.0"`.

Both must match per `CLAUDE.md` § Version.

**Step 2: Run the existing version-sanity test**

Run: `python -m pytest e2e/tests/test_brainstorming_files.py::test_plugin_version_bumped -v`
Expected: PASS (parses both manifests, asserts equality and that version > 0.26.0).

**Step 3: Final full test run**

Run: `python -m pytest e2e/tests/test_brainstorm_widgets.py e2e/tests/test_brainstorming_files.py -v`
Expected: all PASS.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump plugin version to 0.29.0 for interactive widgets"
```

---

## Manual Steps (Post-Automation)

> Complete these checks after autopilot finishes all tasks above. Both are smoke checks deferred from the test plan because their automation cost exceeds value (per design doc § Orphan catalog).

### Smoke check: clipboard fallback at `file://`

1. Open `docs/mockups/2026-05-15-ai-native-brand-folder.html` (or any committed brainstorm snapshot with widgets) directly from Finder/file manager so the browser loads it at `file://`.
2. Toggle any Decision Log dropdown to "Reject."
3. Click the "Copy" button. The button label should briefly change to "Copied ✓" — confirming the `document.execCommand('copy')` fallback fired (since `file://` is not a secure context).
4. If the label flashes "Copy failed — select & Cmd-C," the fallback path triggered an exception. File a Kanban entry.

### Smoke check: live-brainstorm cycle with state survival

1. Run a brainstorm in software mode. Stop after the design doc is written and the live HTML is open at `/tmp/brainstorm-*/live.html`.
2. In the live HTML, toggle 3 Decision Log entries to "Reject" and hand-edit the generated prompt textarea (add a personal sentence).
3. Wait ~15 seconds for the auto-refresh reload.
4. After reload: confirm the 3 "Reject" dropdowns retained their state, the row classes are re-applied (rejected rows still highlighted), AND the hand-edit in the prompt textarea survived (was not clobbered by `refresh()`).
5. If any of those three checks fail, file a Kanban entry against the live-refresh state composition (Task 4).

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|-------------------------|
| 1 | Test framework for widget lints | pytest in `e2e/tests/test_brainstorm_widgets.py` | Shell `.test.sh` scripts (as design doc loosely suggested) |
| 2 | Granularity of template-modification task | Single Task 4 touching all 4 templates atomically | Four separate tasks |
| 3 | Where state-roundtrip and clipboard-fallback DOM tests live | Manual smoke checklist (Post-Automation) | jsdom-based pytest harness |
| 4 | Strip-script test fixture composition | Inline string fixture built from the real template + sidecar | Pre-rendered HTML snapshot file in `e2e/fixtures/` |
| 5 | Selector hook for widget state in `saveState` | `select.dropdown[data-id]` (DOM noise = none) | Per-design-doc `data-widget-state="select"` attribute |
| 6 | Version bump magnitude | 0.28.0 → 0.29.0 (minor) | Patch (0.28.1) |
| 7 | Test value gate for state-composition test | Single assertion across all 4 templates via parametrize-by-loop | Four separate tests (one per template) |
| 8 | Widget try/catch isolation in `saveState`/`restoreState` | Inner try/catch wraps widget capture and restore separately | Reuse the existing outer try/catch only |
| 9 | Strip-script test framing | Structural-contract assertion (indexes prove non-overlap) | Claim to replicate the runtime strip operation |
| 10 | Apply criterion-9 wording change to research-critique-checklist too | Yes — uniform across all 5 checklists | Skip research because research has no widget |

### Appendix: Decision Details

#### Decision 1: pytest, not shell scripts
**Chose:** `e2e/tests/test_brainstorm_widgets.py` (pytest).
**Why:** Existing test infrastructure in this repo is pytest under `e2e/tests/` (24 test files at the time of writing). The design doc lists targets like `tests/brainstorm-template-md5.test.sh` but appends "(or equivalent)" — explicit license to choose the project-aligned framework. Shell tests would be the only `.sh` test files in the repo, an outlier. pytest also gives parametrize, fixtures, and integration with the existing `python -m pytest` workflow contributors already run.
**Alternatives rejected:**
- Shell `.test.sh` scripts (design doc's literal example): adds a second test runner for no benefit.
- Jest/jsdom for JS DOM tests: even the design doc demoted these to manual smoke checks because the infrastructure overhead exceeds the value for v1.

#### Decision 2: One atomic task for all 4 templates
**Chose:** Task 4 modifies all four template files in a single commit.
**Why:** The md5-equality invariant (Task 1's `test_template_md5_equality`) would break between any partial commits if templates were updated one at a time. A Ralph loop iteration mid-sequence would push a broken commit. Granular tasks are good — but the granularity unit is "atomic md5-preserving change," not "one file per commit." Documented as an ordering dependency in the task header, per plan-critique-checklist criterion 6.
**Alternatives rejected:**
- Four separate tasks: would require temporarily disabling the md5 lint between commits or accepting a red-test interregnum. Both worse than one task.

#### Decision 3: Manual smoke for DOM behaviors
**Chose:** state-roundtrip and clipboard-fallback live in the Post-Automation manual smoke checklist.
**Why:** Both behaviors require running JS in a DOM. The design doc's orphan catalog already considered jsdom-based tests and rejected them: "Test infrastructure overhead exceeds value. Demoted to a manual smoke checklist." This plan honors that decision. The pytest tests still cover the *source-level* preconditions: dirty-flag code path exists, clipboard fallback branch exists, state-composition selectors exist.
**Alternatives rejected:**
- jsdom harness in `e2e/tests/`: would require Node test runner setup; one-time use; high infrastructure cost.
- Playwright: same problem at higher cost.

#### Decision 4: Inline-string strip-script fixture
**Chose:** Task 5 builds the fixture HTML from the real template + the real `widgets.html` SCRIPT block at test time.
**Why:** Tests the actual contract end-to-end. If `widgets.html` ever moves the SCRIPT block inside the LIVE-REFRESH delimiters by mistake, this test catches it because it reads the real files. A pre-rendered fixture would freeze a moment in time and miss future regressions.
**Alternatives rejected:**
- Pre-rendered `e2e/fixtures/brainstorm-widgets-snapshot.html`: would need to be regenerated whenever templates or `widgets.html` change — a maintenance burden with no upside.

#### Decision 5: Use existing `select.dropdown[data-id]` selector, not a new `data-widget-state` attribute
**Chose:** The `saveState` IIFE detects widget selects via `document.querySelectorAll('select.dropdown[data-id]')`.
**Why:** The mockup at `docs/mockups/2026-05-15-ai-native-brand-folder.html` already uses `class="dropdown" data-id="N"` on every widget select. The class+attr combo is already unique to widget selects in the page. Adding `data-widget-state="select"` would be DOM noise for no benefit. The design doc's Orphan catalog also rejected the new attribute for this reason.
**Alternatives rejected:**
- `data-widget-state="select"` (mentioned earlier in the design doc body): superseded by the orphan-catalog entry that dropped the marker.

#### Decision 6: Minor version bump (0.29.0)
**Chose:** 0.28.0 → 0.29.0.
**Why:** This adds a new opt-in capability to the brainstorming skill (interactive widgets). Existing brainstorms with no Decision Log still produce byte-identical output (the widget injection is conditional). But the visualization protocol gained a new mandatory step, mode files gained a new mandate, and the skill surface changed — a minor bump signals "new feature" without claiming breaking change.
**Alternatives rejected:**
- Patch bump (0.28.1): undersells the addition. Future skill consumers should be able to differentiate "the version where brainstorms produce interactive triage UIs by default."
- Major bump (0.29.0 is fine; jumping to 1.0.0 is out of scope for this PR per `CLAUDE.md` § Version — "pre-1.0").

#### Decision 7: One state-composition test loops the 4 templates
**Chose:** `test_templates_compose_widget_state` parametrizes over a tuple of all four template names in a single test function.
**Why:** The four templates are byte-identical. A single test asserting state.widgets composition in all four serves the same fact as four duplicated tests. If the templates ever diverge legitimately (per `brainstorm-components.md`'s explicit statement that they may), the test still fires once per file because the inner `for` loop iterates over all four. Concise without losing coverage.
**Alternatives rejected:**
- Four separate test functions: noisier output, no coverage gain.

#### Decision 8: Inner try/catch around widget state composition
**Chose:** Task 4 wraps the new widget-capture and widget-restore loops in their own try/catch blocks inside the existing `saveState`/`restoreState` IIFE.
**Why:** The existing IIFE wraps everything in a single outer try/catch. Without inner isolation, a widget-side malformation (missing `data-id` on a select, a bad sessionStorage payload) would throw and the outer catch would swallow it — also skipping the tab/sub-tab/scrollY persistence that worked before. The plugin's "no behavior regressions" expectation means an opt-in addition shouldn't break the opt-out base case. The behavior-change blockquote at the end of Task 4 makes the addition explicit.
**Alternatives rejected:**
- Reuse the outer try/catch only: silent regression of pre-existing behavior; flagged HIGH by The Architect.

#### Decision 9: Structural-contract framing of the strip-script test
**Chose:** Task 5's test (`test_widget_script_block_is_structurally_outside_live_refresh`) asserts the structural property — that the widget block's start/end indexes do not overlap the LIVE-REFRESH range — and then applies a reference regex strip as proof. Test name and docstring make clear it does NOT model the production strip path (which is LLM-agent-driven per `shared-rules.md`).
**Why:** The original framing ("Replicates the shared-rules.md rule") was misleading — `shared-rules.md` defines the strip as a natural-language instruction, not a regex. A test that claims to replicate runtime behavior would pass while real artifacts break (e.g., extra whitespace, wrapper newlines, an agent variant). Reframing as a structural-contract test makes the assertion truthful: any anchor-honoring strip implementation necessarily preserves widget JS because the widget block lives outside the targeted range.
**Alternatives rejected:**
- Codify a regex in `shared-rules.md` and reference it from the test: more durable, but a larger change with regression risk on the strip rule itself.
- Drop the test entirely: loses the contract assertion that catches an injection-order regression.

#### Decision 10: Apply criterion-9 wording change uniformly to all 5 checklists, including research
**Chose:** Task 10 extends criterion 9 in all 5 checklists (design, authoring, business, planning, research).
**Why:** The trigger is "Open Questions list present in the artifact," not "interactive widget present." Research mode skips visualization but its synthesis files use `## Open Questions` markdown headings — the same triage-quality criterion applies. Uniformity across checklists also reduces cognitive load for reviewers who switch contexts between modes.
**Alternatives rejected:**
- Skip research-critique-checklist: would create an exception case that critique-panel critics would have to remember; more complexity than benefit.
