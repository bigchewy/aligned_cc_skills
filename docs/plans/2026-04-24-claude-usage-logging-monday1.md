# Claude Code Usage Logging — Monday 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Ship the Monday-1 foundation of the usage-logging system — plugin hygiene, four CLAUDE.md behavioral protocols, per-session prompt capture, a Tier-A rule scorer, a weekly scoreboard generator scheduled for Monday 7am, and drift/QA-stale SessionStart detectors.

**Source Design Docs:**
- `docs/plans/2026-04-23-claude-usage-logging-outcomes.md` (outcomes / business)
- `docs/plans/2026-04-23-claude-usage-logging-design.md` (technical foundation)

**Mockups:** `docs/mockups/claude-usage-logging-outcomes.html`

**Architecture:** Two repos touched. The plugin repo (`~/software/aligned_cc_skills`) loses its byte-identical `hooks/usage-tracker.js` duplicate and keeps a non-wired reference copy under `tools/`. The user's global Claude Code config (`~/.claude/`) gains four new hooks (UserPromptSubmit capture, hook-error monitor, digest-drift detector, QA-stale detector), three new scripts (rule scorer, correction parser, decision-log extractor), a weekly scoreboard generator, a launchd plist for Monday 7am firing, and four new CLAUDE.md protocol sections (mode-echo, cite-or-uncertain, survey-first, DECISION-LOG). Storage is JSONL under `~/.claude/usage-tracking/`; digest output lands at `~/.claude/digests/YYYY-WW.md`.

**Tech Stack:** Node.js (stdin/stdout JSON hooks, same pattern as existing `usage-tracker.js`/`error-tracker.js`), bash SessionStart hooks (same pattern as `check-cron-results.sh`), launchd plist for scheduled cron, `node --test` for unit tests (same pattern as `crons/pre-commit-secrets.test.js`).

**Scope (EXPLICIT):** This plan ships **Monday 1 only**. Per the outcomes doc phased rollout, Monday 4 (sections 1/2/4) and Monday 8 (sections 3/5/6) are separate plans to be written *after* Monday 1 has run in anger for three weeks. This plan deliberately does not implement: the macOS notification nudge, Obsidian-vault digest copy, `session-meta/*.json` read path, `Stop`-hook marker extraction, `auto-approve-*` config-gap logging extensions, Tier-B rule detection, or `sessions.jsonl` / `subagents.jsonl` / `vault-provenance.jsonl` capture.

**Cross-repo note:** Tasks 5–22 modify files under `~/.claude/` (a separate git repo auto-committed every 10 minutes by a launchd agent). Tasks 1–4 modify the plugin repo. Each task header labels its target repo. When executing, run commands with `git -C <repo-path>` (or `cd` to that repo root) so commits land in the correct repo. The plan file itself lives in the plugin repo because the source design docs do.

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Confirm `/Users/ericpage/.claude/` is a clean working tree (`git -C ~/.claude status`). If there are uncommitted changes, stash or commit them first so new commits are attributable.
- [ ] Confirm `/Users/ericpage/.claude/usage-tracking/` exists as a directory (should — `usage-tracker.js` creates it). If not, `mkdir -p /Users/ericpage/.claude/usage-tracking`.
- [ ] Confirm the existing launchd agent `com.ericpage.claude-audits` is loaded. Run: `launchctl list | grep ericpage.claude`. This plan adds a *second* agent for the weekly digest; the existing one stays as-is. (The comment on `~/.claude/crons/run-all.sh` line 2 mentions the label; the plist itself lives in `~/Library/LaunchAgents/`.)
- [ ] Confirm `node --version` is ≥ 18 (required for `node:test` and the `node --test` runner used by existing `~/.claude/crons/*.test.js`).

> **Auto-commit window warning:** `~/.claude/` is auto-committed and pushed every 10 minutes by the user's launchd agent (see `~/.claude/README.md`). Any file created in this plan lives in a git-tracked path (per the `.gitignore` allowlist: `hooks/`, `analytics/`, `crons/`) and may be auto-committed in an intermediate state if you pause >10 minutes between creating a file and the explicit `git commit` step at the end of the task. Execute each task contiguously; if you must stop mid-task, finish the commit step first (even if the test step isn't yet clean) or `git stash` the partial work. The auto-commit uses `git add -A` and will pick up untracked files in allowlisted directories.

---

## ✅ Task 1: Move plugin's usage-tracker to non-wired reference copy

**Repo:** `~/software/aligned_cc_skills` (plugin repo)

**Files:**
- Create: `tools/optional-usage-tracker.js`
- Delete: `hooks/usage-tracker.js`

**Step 1: Create the reference copy under `tools/`**

```bash
mkdir -p /Users/ericpage/software/aligned_cc_skills/tools
cp /Users/ericpage/software/aligned_cc_skills/hooks/usage-tracker.js \
   /Users/ericpage/software/aligned_cc_skills/tools/optional-usage-tracker.js
```

**Step 2: Add an install-instructions header**

Replace the first line (`#!/usr/bin/env node`) of `tools/optional-usage-tracker.js` with:

```js
#!/usr/bin/env node
// optional-usage-tracker.js — reference copy, NOT wired into the plugin.
// Identical logic to the canonical ~/.claude/hooks/usage-tracker.js maintained upstream.
// To enable on your machine: copy to ~/.claude/hooks/usage-tracker.js and add a
// PostToolUse hook entry for Skill|Task|Agent in ~/.claude/settings.json. See
// docs/plans/2026-04-23-claude-usage-logging-design.md "Plugin/global duplication"
// for rationale.
```

**Step 3: Delete the wired duplicate**

```bash
rm /Users/ericpage/software/aligned_cc_skills/hooks/usage-tracker.js
```

**Step 4: Verify the file is gone and reference copy exists**

Run: `ls /Users/ericpage/software/aligned_cc_skills/hooks/ /Users/ericpage/software/aligned_cc_skills/tools/`
Expected: `hooks/` shows `auto-approve-safe-bash-paths.js`, `auto-approve-worktrees.js`, `hooks.json` (no `usage-tracker.js`). `tools/` shows `optional-usage-tracker.js`.

**Step 5: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add tools/optional-usage-tracker.js hooks/usage-tracker.js
git -C /Users/ericpage/software/aligned_cc_skills commit -m "refactor(hooks): move plugin usage-tracker to tools/ reference copy"
```

---

## ✅ Task 2: Remove plugin's hooks.json usage-tracker wire

**Repo:** `~/software/aligned_cc_skills`

**Files:**
- Delete: `hooks/hooks.json`

**Step 1: Verify the file currently contains only the usage-tracker wire**

Read `/Users/ericpage/software/aligned_cc_skills/hooks/hooks.json`. Confirm it has exactly one hook entry (`PostToolUse` matching `Skill|Task|Agent` → `usage-tracker.js`) — if it has any other entries, STOP and split this task.

**Step 2: Delete it**

```bash
rm /Users/ericpage/software/aligned_cc_skills/hooks/hooks.json
```

**Step 3: Verify the plugin still loads**

Run: `claude --plugin-dir /Users/ericpage/software/aligned_cc_skills --version`
Expected: CLI prints version; no error about missing hooks.json.

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add hooks/hooks.json
git -C /Users/ericpage/software/aligned_cc_skills commit -m "refactor(hooks): remove duplicate usage-tracker wire (canonical lives in ~/.claude)"
```

---

## ✅ Task 3: Update plugin README with "What this plugin does NOT include" section

**Repo:** `~/software/aligned_cc_skills`

**Files:**
- Modify: `README.md` (append a new section after the existing skill reference table)

**Step 1: Locate the insertion point**

Grep `README.md` for `## Reference` and read the block. Insert the new section after the skill reference table ends (look for the line containing `| kickstart |` or similar final table row) and before the next top-level `##` heading.

**Step 2: Add the section**

```markdown
## What this plugin does NOT include

This plugin is distributed to many users. It intentionally does not ship anything that writes to a user-global path or assumes the plugin author's personal infrastructure.

- **Usage tracking hooks.** A reference copy of the PostToolUse `Skill|Task|Agent` tracker lives at `tools/optional-usage-tracker.js`. It is **not wired** via `hooks/hooks.json`. To enable it on your machine, copy it to `~/.claude/hooks/usage-tracker.js` and add the hook entry shown in that file's header comment. The plugin will never write to `~/.claude/usage-tracking/` on your behalf.
- **Weekly digest / rule scorer.** Single-user features maintained in the plugin author's global config, not shipped.
- **Eval infrastructure.** The `e2e/` directory exists for plugin-author QA; skills guard on its existence and skip silently if absent.
```

**Step 3: Verify markdown renders cleanly**

Run: `head -200 /Users/ericpage/software/aligned_cc_skills/README.md` — confirm the new section has correct spacing (blank line before `##`, blank line before bullets, no broken links).

**Step 4: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add README.md
git -C /Users/ericpage/software/aligned_cc_skills commit -m "docs(readme): document what the plugin deliberately does NOT ship"
```

---

## ✅ Task 4: Add .gitignore regression test

**Repo:** `~/software/aligned_cc_skills`

**Files:**
- Create: `e2e/tests/test_gitignore_usage_tracking.py`
- Test: itself

**Step 1: Write the test**

Create the file at `/Users/ericpage/software/aligned_cc_skills/e2e/tests/test_gitignore_usage_tracking.py`:

```python
"""Regression test: ensure ~/.claude/.gitignore continues to ignore usage-tracking/.

The forward-compatibility guard from docs/plans/2026-04-23-claude-usage-logging-design.md
section 'Forward-compatibility guard (QA)'. If someone refactors the ignore file and
drops coverage of usage-tracking/, this test catches it.
"""
import subprocess
from pathlib import Path


def test_usage_tracking_is_git_ignored():
    claude_dir = Path.home() / ".claude"
    if not claude_dir.is_dir():
        # Skip on CI / fresh installs — this is a regression guard for the author's env.
        return
    candidates = [
        "usage-tracking/prompts-abc123.jsonl",
        "usage-tracking/violations.jsonl",
        "digests/2026-W17.md",
    ]
    for rel in candidates:
        result = subprocess.run(
            ["git", "-C", str(claude_dir), "check-ignore", "--no-index", rel],
            capture_output=True, text=True,
        )
        # check-ignore exits 0 if path IS ignored, 1 if NOT ignored.
        assert result.returncode == 0, (
            f"~/.claude/{rel} is NOT gitignored — auto-commit would push it. "
            f"Review the '*' catch-all + allowlist in ~/.claude/.gitignore."
        )
```

**Step 2: Verify it passes**

Run: `cd /Users/ericpage/software/aligned_cc_skills && python3 -m pytest e2e/tests/test_gitignore_usage_tracking.py -v`
Expected: PASS (usage-tracking/ and digests/ are already ignored by the `*` catch-all; only explicitly allowlisted dirs in `~/.claude/.gitignore` are tracked).

> NOTE: This is a retroactive test. The guard already exists; the test documents the invariant so future refactors of `~/.claude/.gitignore` fail the test rather than silently dropping coverage.

**Step 3: Commit**

```bash
git -C /Users/ericpage/software/aligned_cc_skills add e2e/tests/test_gitignore_usage_tracking.py
git -C /Users/ericpage/software/aligned_cc_skills commit -m "test(e2e): add regression test for usage-tracking gitignore coverage"
```

---

## ✅ Task 5: Add "mode-echo" protocol to CLAUDE.md

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/CLAUDE.md` (insert new section after `## Communication Style` block, before `## Brand Voice`)

> ORDERING: Tasks 5–8 each edit the same file using the previous task's heading as an Edit anchor. Commit each task before starting the next.

**Step 1: Insert the section**

Use Edit with:
- `old_string` = `## Brand Voice\n\n**When writing any document`
- `new_string` = the new section text below, followed by the same `## Brand Voice\n\n**When writing any document` anchor — so the new section lands immediately before Brand Voice.

New section text:

```markdown
## Mode-Echo Protocol

At the start of each response, state which mode you are operating in as the first line: `[MODE: <planner|implementer|reviewer|consultant>]`. This forces an explicit pre-action checkpoint.

- **planner** — producing a plan, design, or decision without touching files
- **implementer** — writing or editing files, committing, running tests
- **reviewer** — critiquing existing code/docs, filing KB entries
- **consultant** — answering a question, exploring, no artifact produced

The echo is required on every response, not just the first. Drift between declared mode and actual behavior (e.g., `[MODE: planner]` followed by file-editing tool calls) is detected and scored by the weekly rule scorer.

```

**Step 2: Verify the edit landed**

Grep `/Users/ericpage/.claude/CLAUDE.md` with output_mode=content for `^## (Mode-Echo Protocol|Brand Voice)`. Confirm `## Mode-Echo Protocol` appears on an earlier line than `## Brand Voice`. Do not rely on fixed line numbers — CLAUDE.md is under active edit and each task in this chain shifts downstream line positions.

**Step 3: Commit**

```bash
git -C /Users/ericpage/.claude add CLAUDE.md
git -C /Users/ericpage/.claude commit -m "feat(rules): add mode-echo protocol to CLAUDE.md"
```

---

## ✅ Task 6: Add "cite-or-uncertain" protocol to CLAUDE.md

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/CLAUDE.md`

**Step 1: Insert the section**

Anchor on `## Brand Voice\n\n**When writing any document`. Insert the new section before that anchor.

New section text:

```markdown
## Cite-or-Uncertain Protocol

When stating a fact about this codebase or any referenced external artifact, either:

1. **Cite** the evidence — file path with line number, a git SHA, a doc URL, or a direct quote — inline in the same sentence, OR
2. **Mark uncertain** — prefix the claim with `UNCERTAIN:` and describe what would verify it.

Never state a filename, function name, line count, or test-pass/fail outcome as if certain unless you have read the file this turn. Memory from prior sessions is not citation.

Examples:
- GOOD: "The scorer reads `~/.claude/CLAUDE.md` (170 lines per `wc -l` this turn) …"
- GOOD: "UNCERTAIN: I believe `check-cron-results.sh` is ~140 lines; read it to confirm before relying on a line number."
- BAD (no citation, not flagged uncertain): "The check-cron-results.sh is around 150 lines long."

```

**Step 2: Verify and commit**

Grep CLAUDE.md for `^## (Mode-Echo|Cite-or-Uncertain|Brand Voice)` (output_mode=content). Confirm section order: Mode-Echo → Cite-or-Uncertain → Brand Voice.

```bash
git -C /Users/ericpage/.claude add CLAUDE.md
git -C /Users/ericpage/.claude commit -m "feat(rules): add cite-or-uncertain protocol to CLAUDE.md"
```

---

## ✅ Task 7: Add "survey-first" protocol to CLAUDE.md

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/CLAUDE.md`

**Step 1: Insert the section**

Anchor on `## Brand Voice\n\n**When writing any document`. Insert before that anchor.

New section text:

```markdown
## Survey-First Protocol

Before taking the first file-modifying action (Write, Edit, or git commit), survey what already exists:

1. **For new skills / plans / docs:** Glob the target directory — does a file with a similar name already exist?
2. **For new plans specifically:** Read `docs/plans/` listings — is there a prior plan on the same topic whose Decision Log would change your approach?
3. **For new commands / scripts:** Grep the repo for the capability — does a function/module already provide it?
4. **For behavior changes:** Read the relevant source file in full, not just the lines you intend to edit.

Surveys that produced findings must be cited under cite-or-uncertain. A session with ≥1 Write/Edit tool call and zero prior Read/Glob/Grep calls in the same session is a survey-first violation.

```

**Step 2: Verify and commit**

```bash
git -C /Users/ericpage/.claude add CLAUDE.md
git -C /Users/ericpage/.claude commit -m "feat(rules): add survey-first protocol to CLAUDE.md"
```

---

## ✅ Task 8: Add DECISION-LOG protocol to CLAUDE.md

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/CLAUDE.md`

**Step 1: Insert the section**

Anchor on `## Brand Voice\n\n**When writing any document`. Insert before that anchor.

New section text:

```markdown
## Decision-Log Protocol

When you detect internal conflict — 2+ plausible paths, conflicting rules, low-confidence choice — emit one marker *before* continuing:

```
<!-- DECISION-LOG conflict="<text>" choice="<text>" reason="<text>" confidence="<0.0-1.0>" -->
```

**Constraints:**
- No nested markers (second `<!--` before first `-->`).
- No markers inside triple-backtick code fences.
- One marker per decision.
- Each field ≤ 500 characters.
- Truthfulness is mandatory. Fabricated markers defeat the purpose; emit no marker if unsure.

**Field semantics:**
- `conflict` — a one-sentence description of the two (or more) paths you were choosing between.
- `choice` — the path you took.
- `reason` — why that path, in one sentence.
- `confidence` — a float in `[0.0, 1.0]`. Below 0.5 = coin-flip territory; worth flagging in the weekly digest.

A weekly quality sample grades 5 random markers as `real` / `trivial` / `manufactured`. Below 7/10 `real` across a 2-week window signals the protocol is not working; review CLAUDE.md framing rather than logging more volume.

```

**Step 2: Verify and commit**

Grep CLAUDE.md for `^## (Mode-Echo|Cite-or-Uncertain|Survey-First|Decision-Log|Brand Voice)` (output_mode=content, -n). Confirm the five headings appear in that exact order — the four new protocols all before `## Brand Voice`.

```bash
git -C /Users/ericpage/.claude add CLAUDE.md
git -C /Users/ericpage/.claude commit -m "feat(rules): add DECISION-LOG protocol to CLAUDE.md"
```

---

## ✅ Task 9: Write prompt-capture hook with failure-semantics tests

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/hooks/prompt-capture.js`
- Create: `/Users/ericpage/.claude/hooks/prompt-capture.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/hooks/prompt-capture.test.js`:

```js
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { buildEntry, writeEntry, MAX_PROMPT_BYTES } = require('./prompt-capture');

describe('prompt-capture', () => {
  let tmpdir;
  beforeEach(() => {
    tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), 'prompt-capture-'));
  });
  afterEach(() => {
    fs.rmSync(tmpdir, { recursive: true, force: true });
  });

  describe('buildEntry', () => {
    it('captures required fields for a short prompt', () => {
      const entry = buildEntry({
        session_id: 'abc123',
        prompt: 'hello',
        cwd: '/tmp/work',
      });
      assert.equal(entry.sid, 'abc123');
      assert.equal(entry.prompt_text, 'hello');
      assert.equal(entry.prompt_chars, 5);
      assert.equal(entry.cwd, '/tmp/work');
      assert.ok(entry.ts);
      assert.equal(entry._truncated, undefined);
    });

    it('truncates prompts over MAX_PROMPT_BYTES and sets _truncated=true', () => {
      const long = 'x'.repeat(MAX_PROMPT_BYTES + 100);
      const entry = buildEntry({ session_id: 's', prompt: long, cwd: '/tmp' });
      assert.equal(entry._truncated, true);
      assert.ok(Buffer.byteLength(entry.prompt_text, 'utf-8') <= MAX_PROMPT_BYTES);
      assert.equal(entry.prompt_chars, long.length);
    });

    it('normalizes UTF-8 (invalid surrogates become replacement chars)', () => {
      const invalid = 'ok\uD800invalid';
      const entry = buildEntry({ session_id: 's', prompt: invalid, cwd: '/tmp' });
      // After Buffer round-trip, lone surrogate becomes U+FFFD replacement char
      assert.ok(!entry.prompt_text.includes('\uD800'));
    });

    it('handles empty prompts (chars=0, no truncation)', () => {
      const entry = buildEntry({ session_id: 's', prompt: '', cwd: '/tmp' });
      assert.equal(entry.prompt_chars, 0);
      assert.equal(entry._truncated, undefined);
    });
  });

  describe('writeEntry', () => {
    it('writes one JSONL line to per-session file and returns true on success', () => {
      const entry = { sid: 'sess1', ts: '2026-04-24T00:00:00Z', prompt_text: 'hi', prompt_chars: 2, cwd: '/tmp' };
      const ok = writeEntry(entry, tmpdir);
      assert.equal(ok, true);
      const lines = fs.readFileSync(path.join(tmpdir, 'prompts-sess1.jsonl'), 'utf-8').trim().split('\n');
      assert.equal(lines.length, 1);
      assert.deepEqual(JSON.parse(lines[0]), entry);
    });

    it('appends to existing per-session file (does not clobber)', () => {
      const entry1 = { sid: 's1', ts: 't1', prompt_text: 'a', prompt_chars: 1, cwd: '/' };
      const entry2 = { sid: 's1', ts: 't2', prompt_text: 'b', prompt_chars: 1, cwd: '/' };
      writeEntry(entry1, tmpdir);
      writeEntry(entry2, tmpdir);
      const lines = fs.readFileSync(path.join(tmpdir, 'prompts-s1.jsonl'), 'utf-8').trim().split('\n');
      assert.equal(lines.length, 2);
    });

    it('returns false when the log dir path points to a regular file', () => {
      // Force EACCES / ENOTDIR by passing a file path instead of a directory
      const filePath = path.join(tmpdir, 'blocker');
      fs.writeFileSync(filePath, 'x');
      const entry = { sid: 's', ts: 't', prompt_text: 'p', prompt_chars: 1, cwd: '/' };
      const ok = writeEntry(entry, filePath);
      assert.equal(ok, false);
    });

    it('writes sid="unknown" file when session_id is missing', () => {
      const entry = buildEntry({ session_id: '', prompt: 'x', cwd: '/tmp' });
      const ok = writeEntry(entry, tmpdir);
      assert.equal(ok, true);
      assert.ok(fs.existsSync(path.join(tmpdir, 'prompts-unknown.jsonl')));
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `node --test /Users/ericpage/.claude/hooks/prompt-capture.test.js`
Expected: FAIL with `Cannot find module './prompt-capture'`.

**Step 3: Write the minimal implementation**

Create `/Users/ericpage/.claude/hooks/prompt-capture.js`:

```js
#!/usr/bin/env node
// prompt-capture.js — UserPromptSubmit hook
// Logs user prompts to ~/.claude/usage-tracking/prompts-<sid>.jsonl (per-session file).
// Design: docs/plans/2026-04-23-claude-usage-logging-design.md Change 3.
// Failure semantics: crash-free pass-through (exits 0), errors recorded to .hook-errors.log.

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(process.env.HOME || '/tmp', '.claude', 'usage-tracking');
const ERROR_LOG = path.join(process.env.HOME || '/tmp', '.claude', 'usage-tracking', '.hook-errors.log');
const MAX_PROMPT_BYTES = 8 * 1024;
const HOOK_NAME = 'prompt-capture';

function buildEntry({ session_id, prompt, cwd }) {
  const text = String(prompt || '');
  // UTF-8 round-trip to strip invalid surrogates
  const safe = Buffer.from(text, 'utf-8').toString('utf-8');
  const full_chars = safe.length;
  let body = safe;
  let truncated = false;
  if (Buffer.byteLength(body, 'utf-8') > MAX_PROMPT_BYTES) {
    body = Buffer.from(body, 'utf-8').slice(0, MAX_PROMPT_BYTES).toString('utf-8');
    truncated = true;
  }
  const entry = {
    ts: new Date().toISOString(),
    sid: session_id || 'unknown',
    prompt_text: body,
    prompt_chars: full_chars,
    cwd: cwd || '',
  };
  if (truncated) entry._truncated = true;
  return entry;
}

function writeEntry(entry, logDir) {
  try {
    fs.mkdirSync(logDir, { recursive: true });
    const file = path.join(logDir, `prompts-${entry.sid}.jsonl`);
    fs.appendFileSync(file, JSON.stringify(entry) + '\n');
    return true;
  } catch (err) {
    try {
      fs.appendFileSync(ERROR_LOG, JSON.stringify({
        ts: new Date().toISOString(),
        hook: HOOK_NAME,
        error: String(err && err.message || err),
      }) + '\n');
    } catch (_) { /* last resort: suppress */ }
    return false;
  }
}

module.exports = { buildEntry, writeEntry, MAX_PROMPT_BYTES };

// CLI entry: read JSON from stdin, write entry, exit 0 no matter what
if (require.main === module) {
  const TIMEOUT_MS = 100;
  const timer = setTimeout(() => process.exit(0), TIMEOUT_MS);
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => { input += c; });
  process.stdin.on('end', () => {
    try {
      const data = JSON.parse(input);
      const entry = buildEntry({
        session_id: data.session_id,
        prompt: data.prompt || data.user_prompt || '',
        cwd: data.cwd,
      });
      writeEntry(entry, LOG_DIR);
    } catch (err) {
      try {
        fs.appendFileSync(ERROR_LOG, JSON.stringify({
          ts: new Date().toISOString(),
          hook: HOOK_NAME,
          error: String(err && err.message || err),
        }) + '\n');
      } catch (_) { /* suppress */ }
    }
    clearTimeout(timer);
    process.exit(0);
  });
  process.stdin.on('error', () => { clearTimeout(timer); process.exit(0); });
}
```

Make it executable: `chmod +x /Users/ericpage/.claude/hooks/prompt-capture.js`

**Step 4: Run tests to verify they pass**

Run: `node --test /Users/ericpage/.claude/hooks/prompt-capture.test.js`
Expected: PASS (8 tests).

**Step 5: Smoke-test via stdin**

```bash
echo '{"session_id":"smoketest","prompt":"hello world","cwd":"/tmp"}' | node /Users/ericpage/.claude/hooks/prompt-capture.js
cat /Users/ericpage/.claude/usage-tracking/prompts-smoketest.jsonl
rm /Users/ericpage/.claude/usage-tracking/prompts-smoketest.jsonl
```
Expected: one JSONL line with `prompt_text:"hello world"`, `sid:"smoketest"`.

**Step 6: Commit**

```bash
git -C /Users/ericpage/.claude add hooks/prompt-capture.js hooks/prompt-capture.test.js
git -C /Users/ericpage/.claude commit -m "feat(hooks): add UserPromptSubmit prompt-capture with failure semantics"
```

---

## ✅ Task 10: Wire prompt-capture into settings.json

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/settings.json` (add `UserPromptSubmit` hook entry inside the `hooks` object)

> ORDERING: Task 9 must be committed first — settings.json referencing a nonexistent hook file = immediate user-facing breakage on next session start.

**Step 1: Read the current settings.json first**

Read `/Users/ericpage/.claude/settings.json` in full (Read tool, no offset). This is mandatory — the Edit anchor chain used by Tasks 10/12/20/22 depends on knowing the exact current state. If the file has been hand-edited (new permissions added, hooks reordered), the anchor in Step 2 may no longer be unique and the Edit will fail cleanly.

**Step 2: Back up the file**

```bash
cp /Users/ericpage/.claude/settings.json /tmp/settings.json.bak-$(date +%s)
```

**Step 3: Add the UserPromptSubmit entry**

The existing `hooks` object has keys `PreToolUse`, `PostToolUseFailure`, `PostToolUse` (verified in Step 1). Add a new `UserPromptSubmit` key. `UserPromptSubmit` intentionally has no `matcher` field — unlike `PreToolUse`/`PostToolUse`, it has no tool-kind to match on; the hook runs on every user prompt submission. This is the same structure pattern shown in Anthropic's Claude Code hooks docs.

Use Edit with:
- `old_string` = `  "hooks": {\n    "PreToolUse": [`
- `new_string` =

```json
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node /Users/ericpage/.claude/hooks/prompt-capture.js",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
```

**Step 4: Validate JSON**

Run: `node -e "JSON.parse(require('fs').readFileSync('/Users/ericpage/.claude/settings.json','utf-8'))"`
Expected: no output (parse succeeded). If it errors, restore from backup and retry.

**Step 5: Smoke-test the wire**

Start a new Claude Code session and type any prompt. Then run:
```bash
ls -la /Users/ericpage/.claude/usage-tracking/prompts-*.jsonl
```
Expected: a file for the current session with at least one line.

**Step 6: Commit**

```bash
git -C /Users/ericpage/.claude add settings.json
git -C /Users/ericpage/.claude commit -m "feat(settings): wire UserPromptSubmit to prompt-capture.js"
```

---

## ✅ Task 11: Write hook-error monitor (SessionStart)

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/hooks/check-hook-errors.sh`
- Create: `/Users/ericpage/.claude/hooks/check-hook-errors.test.sh`

**Step 1: Write the bats-less shell test**

Create `/Users/ericpage/.claude/hooks/check-hook-errors.test.sh`:

```bash
#!/bin/bash
# Shell test for check-hook-errors.sh. Uses a TMP home so production state is untouched.
# Run: bash ~/.claude/hooks/check-hook-errors.test.sh
set -euo pipefail

SCRIPT="$(dirname "$0")/check-hook-errors.sh"
fail() { echo "FAIL: $1" >&2; exit 1; }

run_with_home() {
  local home="$1"
  HOME="$home" bash "$SCRIPT"
}

# Case 1: no error log → no output
TMP1=$(mktemp -d)
out=$(run_with_home "$TMP1")
[ -z "$out" ] || fail "case 1 expected no output; got: $out"
rm -rf "$TMP1"

# Case 2: log below 100-line threshold → no output
TMP2=$(mktemp -d)
mkdir -p "$TMP2/.claude/usage-tracking"
yes "x" | head -n 50 > "$TMP2/.claude/usage-tracking/.hook-errors.log"
out=$(run_with_home "$TMP2")
[ -z "$out" ] || fail "case 2 expected no output; got: $out"
rm -rf "$TMP2"

# Case 3: log above 100-line threshold → [HOOK ERRORS] tag
TMP3=$(mktemp -d)
mkdir -p "$TMP3/.claude/usage-tracking"
yes "x" | head -n 101 > "$TMP3/.claude/usage-tracking/.hook-errors.log"
out=$(run_with_home "$TMP3")
[[ "$out" == *"[HOOK ERRORS]"* ]] || fail "case 3 expected [HOOK ERRORS]; got: $out"
rm -rf "$TMP3"

# Case 4: log above 1MB byte threshold (but fewer than 100 lines) → [HOOK ERRORS] tag
TMP4=$(mktemp -d)
mkdir -p "$TMP4/.claude/usage-tracking"
# One single line > 1MB
printf '%s' "$(head -c 1100000 </dev/zero | tr '\0' 'x')" > "$TMP4/.claude/usage-tracking/.hook-errors.log"
out=$(run_with_home "$TMP4")
[[ "$out" == *"[HOOK ERRORS]"* ]] || fail "case 4 expected [HOOK ERRORS]; got: $out"
rm -rf "$TMP4"

echo "PASS: 4/4 cases"
```

Make it executable: `chmod +x /Users/ericpage/.claude/hooks/check-hook-errors.test.sh`

**Step 2: Verify the test fails (script does not yet exist)**

Run: `bash /Users/ericpage/.claude/hooks/check-hook-errors.test.sh`
Expected: FAIL with `check-hook-errors.sh: No such file or directory` (script referenced by the test doesn't exist yet).

**Step 3: Write the script**

Create `/Users/ericpage/.claude/hooks/check-hook-errors.sh`:

```bash
#!/bin/bash
# check-hook-errors.sh — SessionStart hook.
# Fires [HOOK ERRORS] dispatch tag when ~/.claude/usage-tracking/.hook-errors.log
# exceeds 100 lines or 1 MB. Silent crashes drop the highest-value signal; this
# monitor surfaces dormancy.
# Design: docs/plans/2026-04-23-claude-usage-logging-design.md Change 3.

ERR_LOG="$HOME/.claude/usage-tracking/.hook-errors.log"

[ -f "$ERR_LOG" ] || exit 0

line_count=$(wc -l < "$ERR_LOG" | tr -d ' ')
byte_size=$(wc -c < "$ERR_LOG" | tr -d ' ')

if [ "$line_count" -gt 100 ] || [ "$byte_size" -gt 1048576 ]; then
  echo "[HOOK ERRORS] ~/.claude/usage-tracking/.hook-errors.log has ${line_count} lines / ${byte_size} bytes — inspect for a failing hook before error volume grows."
fi

exit 0
```

Make it executable: `chmod +x /Users/ericpage/.claude/hooks/check-hook-errors.sh`

**Step 4: Run the shell test to verify all 4 cases pass**

Run: `bash /Users/ericpage/.claude/hooks/check-hook-errors.test.sh`
Expected: `PASS: 4/4 cases`. (The test uses throwaway TMP directories; production state is not touched.)

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add hooks/check-hook-errors.sh hooks/check-hook-errors.test.sh
git -C /Users/ericpage/.claude commit -m "feat(hooks): add check-hook-errors SessionStart monitor with shell test"
```

---

## ✅ Task 12: Wire check-hook-errors into settings.json

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/settings.json` (add `SessionStart` key if absent; append otherwise)

> ORDERING: Task 11 must be committed first. Task 10 also modifies this file; complete Task 10 before Task 12.

**Step 1: Read the current settings.json**

Read `/Users/ericpage/.claude/settings.json` in full. Grep (within the file contents) for `"SessionStart"`. At the time of plan writing (verified by Read during survey), `SessionStart` was NOT present — `check-cron-results.sh` appears to be wired via a project-scoped or plugin scope rather than the user `~/.claude/settings.json`. Re-verify now.

**Step 2a: If SessionStart is absent — insert the block before the UserPromptSubmit key** (added in Task 10)

Use Edit with a short, unique anchor:
- `old_string` = `    "UserPromptSubmit": [` (including the 4-space leading indent — this key was introduced in Task 10 and appears exactly once)
- `new_string` =

```json
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/ericpage/.claude/hooks/check-hook-errors.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "UserPromptSubmit": [
```

**Step 2b: If SessionStart exists** — locate the existing array and append the new hook object, anchoring on the last closing `]` of the existing `SessionStart` array (use the full JSON object contents as the anchor to guarantee uniqueness).

**Step 3: Validate JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('/Users/ericpage/.claude/settings.json','utf-8'))"
```

**Step 4: Commit**

```bash
git -C /Users/ericpage/.claude add settings.json
git -C /Users/ericpage/.claude commit -m "feat(settings): wire SessionStart to check-hook-errors"
```

---

## ✅ Task 13: Write Tier-A rule catalog module

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/analytics/rule-catalog.js`
- Create: `/Users/ericpage/.claude/analytics/rule-catalog.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/analytics/rule-catalog.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { RULES, scoreResponse } = require('./rule-catalog');

describe('rule-catalog', () => {
  describe('RULES', () => {
    it('contains at least 10 banned-phrase opener rules', () => {
      const openers = RULES.filter(r => r.category === 'banned-opener');
      assert.ok(openers.length >= 10, `expected >=10 openers, got ${openers.length}`);
    });

    it('each rule has id, category, pattern, severity, source_line', () => {
      for (const rule of RULES) {
        assert.ok(rule.id, 'missing id');
        assert.ok(rule.category, `${rule.id} missing category`);
        assert.ok(rule.pattern instanceof RegExp, `${rule.id} pattern not RegExp`);
        assert.ok(['low', 'medium', 'high'].includes(rule.severity), `${rule.id} severity invalid`);
        assert.ok(rule.source_line, `${rule.id} missing source_line`);
      }
    });

    it('rule ids are unique', () => {
      const ids = RULES.map(r => r.id);
      assert.equal(new Set(ids).size, ids.length, 'duplicate rule ids');
    });
  });

  describe('scoreResponse', () => {
    it('flags the banned opener "You\'re absolutely right"', () => {
      const hits = scoreResponse("You're absolutely right, the fix is simple.");
      assert.ok(hits.some(h => h.rule.id === 'banned-youre-right'));
    });

    it('flags banned self-adjective "surgical"', () => {
      const hits = scoreResponse("I made a surgical edit to the config.");
      assert.ok(hits.some(h => h.rule.category === 'banned-self-adjective'));
    });

    it('flags deferential closer "Want me to..."', () => {
      const hits = scoreResponse("Done. Want me to run the tests next?");
      assert.ok(hits.some(h => h.rule.category === 'banned-closer'));
    });

    it('flags HEREDOC in commit message example', () => {
      const sample = 'git commit -m "$(cat <<\'EOF\'\nfix\nEOF\n)"';
      const hits = scoreResponse(sample);
      assert.ok(hits.some(h => h.rule.id === 'heredoc-forbidden'));
    });

    it('returns empty array for clean text', () => {
      const hits = scoreResponse("I read the file and added the new function.");
      assert.deepEqual(hits, []);
    });

    it('reports hit location as character offset', () => {
      const hits = scoreResponse("ok. Absolutely working now.");
      const hit = hits.find(h => h.rule.id === 'banned-absolutely');
      assert.ok(hit);
      assert.equal(typeof hit.index, 'number');
      assert.ok(hit.index > 0);
    });

    it('is case-insensitive for banned openers', () => {
      const hits = scoreResponse("EXCELLENT point, moving on.");
      assert.ok(hits.some(h => h.rule.category === 'banned-opener'));
    });

    it('returns [] for null or non-string input', () => {
      assert.deepEqual(scoreResponse(null), []);
      assert.deepEqual(scoreResponse(undefined), []);
      assert.deepEqual(scoreResponse(42), []);
    });
  });
});
```

**Step 2: Verify tests fail**

Run: `node --test /Users/ericpage/.claude/analytics/rule-catalog.test.js`
Expected: FAIL with `Cannot find module './rule-catalog'`.

**Step 3: Write the minimal implementation**

Create `/Users/ericpage/.claude/analytics/rule-catalog.js`:

```js
// rule-catalog.js — Tier-A rule definitions extracted from ~/.claude/CLAUDE.md.
// Each rule has a regex pattern; a response is scored by running every pattern
// against it and returning the hits. Patterns are case-insensitive unless noted.
//
// Source: ~/.claude/CLAUDE.md "Banned phrases" section (openers, self-adjectives,
// closers) + "Git Commits" section (HEREDOC forbidden) + "Bash Tool Restrictions".
// Rule additions require updating both the catalog AND CLAUDE.md.

const RULES = [
  // Banned openers (CLAUDE.md:29-35)
  { id: 'banned-youre-right', category: 'banned-opener', severity: 'medium',
    pattern: /\byou'?re (?:absolutely )?right\b/i, source_line: 'CLAUDE.md:30' },
  { id: 'banned-exactly', category: 'banned-opener', severity: 'medium',
    pattern: /^\s*exactly\b/im, source_line: 'CLAUDE.md:30' },
  { id: 'banned-spot-on', category: 'banned-opener', severity: 'medium',
    pattern: /\bspot on\b/i, source_line: 'CLAUDE.md:30' },
  { id: 'banned-great-question', category: 'banned-opener', severity: 'medium',
    pattern: /\bgreat (?:question|point|call)\b/i, source_line: 'CLAUDE.md:31' },
  { id: 'banned-excellent', category: 'banned-opener', severity: 'medium',
    pattern: /^\s*excellent[!.,]/im, source_line: 'CLAUDE.md:31' },
  { id: 'banned-sharper', category: 'banned-opener', severity: 'medium',
    pattern: /\b(?:sharper|more precise) (?:read|than)\b/i, source_line: 'CLAUDE.md:32' },
  { id: 'banned-see-what-saying', category: 'banned-opener', severity: 'medium',
    pattern: /\bI see what you'?re saying\b/i, source_line: 'CLAUDE.md:33' },
  { id: 'banned-fair-point', category: 'banned-opener', severity: 'medium',
    pattern: /\b(?:that'?s fair|fair point)\b/i, source_line: 'CLAUDE.md:33' },
  { id: 'banned-fascinating', category: 'banned-opener', severity: 'low',
    pattern: /^\s*(?:fascinating|interesting)[!.,]/im, source_line: 'CLAUDE.md:34' },
  { id: 'banned-absolutely', category: 'banned-opener', severity: 'medium',
    pattern: /^\s*absolutely\b/im, source_line: 'CLAUDE.md:35' },
  { id: 'banned-of-course', category: 'banned-opener', severity: 'low',
    pattern: /^\s*of course[!.,]/im, source_line: 'CLAUDE.md:35' },

  // Banned self-adjectives (CLAUDE.md:38-39)
  { id: 'banned-self-surgical', category: 'banned-self-adjective', severity: 'medium',
    pattern: /\b(?:surgical|tight|elegant|crisp)\b/i, source_line: 'CLAUDE.md:38' },
  { id: 'banned-self-thoughtful', category: 'banned-self-adjective', severity: 'low',
    pattern: /\b(?:thoughtful|careful|nuanced|comprehensive)\b/i, source_line: 'CLAUDE.md:39' },

  // Banned deferential closers (CLAUDE.md:43-45)
  { id: 'banned-closer-resonate', category: 'banned-closer', severity: 'medium',
    pattern: /\b(?:does this land|does that resonate|how does that sit)\b\?/i,
    source_line: 'CLAUDE.md:43' },
  { id: 'banned-closer-want-me-to', category: 'banned-closer', severity: 'medium',
    pattern: /\b(?:want me to|happy to|let me know if)\b/i, source_line: 'CLAUDE.md:44' },
  { id: 'banned-closer-hope-helps', category: 'banned-closer', severity: 'low',
    pattern: /\b(?:hope this helps|thoughts\?)\b/i, source_line: 'CLAUDE.md:45' },

  // Git commit HEREDOC (CLAUDE.md:118)
  { id: 'heredoc-forbidden', category: 'git', severity: 'high',
    pattern: /\$\(cat\s*<<'EOF'/, source_line: 'CLAUDE.md:118' },

  // Bash for search (CLAUDE.md:13-16) - starts-with-rg-or-grep on a command line
  { id: 'bash-grep-search', category: 'tool-misuse', severity: 'medium',
    pattern: /^\s*(?:rg|grep)\s+(?:-[rR]|'|")/m, source_line: 'CLAUDE.md:14-15' },
];

function scoreResponse(text) {
  if (typeof text !== 'string' || !text) return [];
  const hits = [];
  for (const rule of RULES) {
    const match = text.match(rule.pattern);
    if (match && typeof match.index === 'number') {
      hits.push({ rule, index: match.index, matched: match[0] });
    }
  }
  return hits;
}

module.exports = { RULES, scoreResponse };
```

**Step 4: Verify tests pass**

Run: `node --test /Users/ericpage/.claude/analytics/rule-catalog.test.js`
Expected: PASS (11 tests).

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add analytics/rule-catalog.js analytics/rule-catalog.test.js
git -C /Users/ericpage/.claude commit -m "feat(analytics): add Tier-A rule catalog with scoring logic"
```

---

## ✅ Task 14: Write user-correction event parser

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/analytics/correction-parser.js`
- Create: `/Users/ericpage/.claude/analytics/correction-parser.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/analytics/correction-parser.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { detectCorrection, PHRASE_TIERS } = require('./correction-parser');

describe('correction-parser', () => {
  describe('PHRASE_TIERS', () => {
    it('defines high/medium/low tiers with confidences 0.9/0.6/0.3', () => {
      assert.equal(PHRASE_TIERS.high.confidence, 0.9);
      assert.equal(PHRASE_TIERS.medium.confidence, 0.6);
      assert.equal(PHRASE_TIERS.low.confidence, 0.3);
    });

    it('includes "you stopped" in the high tier', () => {
      assert.ok(PHRASE_TIERS.high.phrases.some(p => p.test('you stopped running tests')));
    });

    it('includes "wait," in the medium tier', () => {
      assert.ok(PHRASE_TIERS.medium.phrases.some(p => p.test('wait, that is wrong')));
    });
  });

  describe('detectCorrection', () => {
    it('returns {tier:"high", confidence:0.9} for a high-tier prompt', () => {
      const r = detectCorrection("why aren't you running the tests?");
      assert.equal(r.tier, 'high');
      assert.equal(r.confidence, 0.9);
      assert.ok(r.matched_phrase);
    });

    it('returns {tier:"medium"} for a medium-tier prompt', () => {
      const r = detectCorrection('wait, back up — that change is wrong');
      assert.equal(r.tier, 'medium');
    });

    it('returns {tier:"low"} for a low-tier prompt', () => {
      const r = detectCorrection('hmm');
      assert.equal(r.tier, 'low');
    });

    it('returns null for prompts with no correction signal', () => {
      const r = detectCorrection('please implement task 5');
      assert.equal(r, null);
    });

    it('returns null for empty / null input', () => {
      assert.equal(detectCorrection(''), null);
      assert.equal(detectCorrection(null), null);
      assert.equal(detectCorrection(undefined), null);
    });

    it('picks HIGHEST tier when multiple phrases match', () => {
      const r = detectCorrection('wait, you stopped running the tests');
      assert.equal(r.tier, 'high');
    });

    it('below-threshold (low tier) results still return, caller decides to suppress', () => {
      const r = detectCorrection('actually');
      assert.equal(r.tier, 'low');
      assert.ok(r.confidence < 0.5);
    });
  });
});
```

**Step 2: Verify tests fail**

Run: `node --test /Users/ericpage/.claude/analytics/correction-parser.test.js`
Expected: FAIL — module not found.

**Step 3: Write the implementation**

Create `/Users/ericpage/.claude/analytics/correction-parser.js`:

```js
// correction-parser.js — detects user-correction events in prompts.
// Source: docs/plans/2026-04-23-claude-usage-logging-outcomes.md
//   "Cross-cutting mechanism: user-correction event detection" (widened phrase list).
// Returns the HIGHEST-tier match per prompt; caller decides whether to suppress
// below-threshold (<0.5) hits.

const PHRASE_TIERS = {
  high: {
    confidence: 0.9,
    phrases: [
      /\bI thought you'?d\b/i,
      /\byou'?re supposed to\b/i,
      /\byou stopped\b/i,
      /\bwhy aren'?t you\b/i,
      /\bwhy didn'?t you\b/i,
      /\bdon'?t forget to\b/i,
    ],
  },
  medium: {
    confidence: 0.6,
    phrases: [
      /^\s*no[,.\s]/i,
      /^\s*wait[,.\s]/i,
      /^\s*stop\b/i,
      /\bundo\b/i,
      /\bthat'?s wrong\b/i,
      /\bwhy did you\b/i,
      /\bhang on\b/i,
      /\bback up\b/i,
      /\bnot that\b/i,
    ],
  },
  low: {
    confidence: 0.3,
    phrases: [
      /^\s*actually\b/i,
      /^\s*hmm\b/i,
      /^\s*nope?\b/i,
    ],
  },
};

function detectCorrection(text) {
  if (typeof text !== 'string' || !text) return null;
  for (const tier of ['high', 'medium', 'low']) {
    const { confidence, phrases } = PHRASE_TIERS[tier];
    for (const p of phrases) {
      const m = text.match(p);
      if (m) {
        return { tier, confidence, matched_phrase: m[0], index: m.index || 0 };
      }
    }
  }
  return null;
}

module.exports = { detectCorrection, PHRASE_TIERS };
```

**Step 4: Verify tests pass**

Run: `node --test /Users/ericpage/.claude/analytics/correction-parser.test.js`
Expected: PASS (8 tests).

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add analytics/correction-parser.js analytics/correction-parser.test.js
git -C /Users/ericpage/.claude commit -m "feat(analytics): add user-correction event parser with tiered phrase list"
```

---

## ✅ Task 15: Write DECISION-LOG extractor (two-stage)

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/analytics/decision-log-extractor.js`
- Create: `/Users/ericpage/.claude/analytics/decision-log-extractor.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/analytics/decision-log-extractor.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { extractMarkers } = require('./decision-log-extractor');

describe('decision-log-extractor', () => {
  it('extracts a single well-formed marker', () => {
    const text = 'Before deciding, <!-- DECISION-LOG conflict="A vs B" choice="A" reason="faster" confidence="0.8" --> proceeding.';
    const out = extractMarkers(text);
    assert.equal(out.length, 1);
    assert.equal(out[0].conflict, 'A vs B');
    assert.equal(out[0].choice, 'A');
    assert.equal(out[0].reason, 'faster');
    assert.equal(out[0].confidence, 0.8);
    assert.equal(out[0].validation_errors.length, 0);
  });

  it('ignores markers inside triple-backtick code fences', () => {
    const text = [
      'Example syntax:',
      '```',
      '<!-- DECISION-LOG conflict="x" choice="y" reason="z" confidence="0.5" -->',
      '```',
      'That was just a fence demo.',
    ].join('\n');
    const out = extractMarkers(text);
    assert.equal(out.length, 0);
  });

  it('extracts markers outside fences even when a fence appears earlier', () => {
    const text = [
      '```',
      'code here',
      '```',
      '<!-- DECISION-LOG conflict="real" choice="A" reason="r" confidence="0.7" -->',
    ].join('\n');
    const out = extractMarkers(text);
    assert.equal(out.length, 1);
    assert.equal(out[0].choice, 'A');
  });

  it('flags missing field as validation_error', () => {
    const text = '<!-- DECISION-LOG conflict="c" choice="x" confidence="0.5" -->';
    const out = extractMarkers(text);
    assert.equal(out.length, 1);
    assert.ok(out[0].validation_errors.includes('missing:reason'));
  });

  it('flags nested marker via stage-1 reject', () => {
    // Second `<!--` appears before the first `-->` closes
    const text = '<!-- DECISION-LOG conflict="x" <!-- nested --> choice="y" -->';
    const out = extractMarkers(text);
    // Stage-1 captures the outer up to first -->; validation catches missing fields
    assert.equal(out.length, 1);
    assert.ok(out[0].validation_errors.some(e => e.includes('nested') || e.startsWith('missing:')));
  });

  it('flags confidence out of range as validation_error', () => {
    const text = '<!-- DECISION-LOG conflict="c" choice="x" reason="r" confidence="1.5" -->';
    const out = extractMarkers(text);
    assert.ok(out[0].validation_errors.includes('confidence_range'));
  });

  it('detects duplicate markers in one turn via multi_marker_turn flag', () => {
    const text = [
      '<!-- DECISION-LOG conflict="a" choice="x" reason="r" confidence="0.5" -->',
      '<!-- DECISION-LOG conflict="b" choice="y" reason="r" confidence="0.5" -->',
    ].join(' ');
    const out = extractMarkers(text);
    assert.equal(out.length, 2);
    assert.ok(out[0].multi_marker_turn);
    assert.ok(out[1].multi_marker_turn);
  });

  it('returns empty array when no markers present', () => {
    assert.deepEqual(extractMarkers('just prose'), []);
    assert.deepEqual(extractMarkers(''), []);
    assert.deepEqual(extractMarkers(null), []);
  });

  it('captures field with embedded equals sign inside quoted value', () => {
    const text = '<!-- DECISION-LOG conflict="a=b" choice="x" reason="r" confidence="0.5" -->';
    const out = extractMarkers(text);
    assert.equal(out[0].conflict, 'a=b');
  });

  it('flags embedded double-quote in field as validation_error', () => {
    // Quote char inside value ends capture early → stage-2 sees truncated fields
    const text = '<!-- DECISION-LOG conflict="has \\"quote" choice="x" reason="r" confidence="0.5" -->';
    const out = extractMarkers(text);
    // Either stage-2 flags embedded_quote OR missing field; accept either.
    assert.ok(out.length > 0);
    assert.ok(out[0].validation_errors.length > 0);
  });
});
```

**Step 2: Verify tests fail**

Run: `node --test /Users/ericpage/.claude/analytics/decision-log-extractor.test.js`
Expected: FAIL — module not found.

**Step 3: Write the implementation**

Create `/Users/ericpage/.claude/analytics/decision-log-extractor.js`:

```js
// decision-log-extractor.js — two-stage DECISION-LOG parser.
// Source: docs/plans/2026-04-23-claude-usage-logging-outcomes.md
//   "Extraction at Stop-hook (two-stage parse...)"
//
// Stage 1 — structural match outside code fences.
// Stage 2 — per-field extraction with validation.

const STAGE1_RE = /<!--\s*DECISION-LOG\s+([\s\S]*?)\s*-->/g;
const FIELD_RE = /(conflict|choice|reason|confidence)="([^"]{0,500})"/g;

function stripFencedRegions(text) {
  // Returns an array of {start,end} ranges OUTSIDE triple-backtick fences.
  const ranges = [];
  let inFence = false;
  let cursor = 0;
  const fenceRe = /```/g;
  let m;
  while ((m = fenceRe.exec(text)) !== null) {
    if (!inFence) {
      ranges.push({ start: cursor, end: m.index });
      inFence = true;
    } else {
      inFence = false;
    }
    cursor = m.index + 3;
  }
  if (!inFence) ranges.push({ start: cursor, end: text.length });
  return ranges;
}

function extractFields(inner) {
  const fields = {};
  const errors = [];
  let m;
  const seen = new Set();
  FIELD_RE.lastIndex = 0;
  while ((m = FIELD_RE.exec(inner)) !== null) {
    const key = m[1];
    const val = m[2];
    if (seen.has(key)) {
      errors.push(`duplicate:${key}`);
      continue;
    }
    seen.add(key);
    fields[key] = val;
  }
  for (const required of ['conflict', 'choice', 'reason', 'confidence']) {
    if (!(required in fields)) errors.push(`missing:${required}`);
  }
  if ('confidence' in fields) {
    const n = parseFloat(fields.confidence);
    if (Number.isNaN(n) || n < 0 || n > 1) errors.push('confidence_range');
    fields.confidence = n;
  }
  return { fields, errors };
}

function extractMarkers(text) {
  if (typeof text !== 'string' || !text) return [];
  const safeRanges = stripFencedRegions(text);
  const results = [];
  for (const range of safeRanges) {
    const slice = text.slice(range.start, range.end);
    STAGE1_RE.lastIndex = 0;
    let m;
    while ((m = STAGE1_RE.exec(slice)) !== null) {
      const inner = m[1];
      const validation_errors = [];
      // Nested marker check: another `<!--` in the captured inner group
      if (inner.includes('<!--')) validation_errors.push('nested');
      const { fields, errors } = extractFields(inner);
      validation_errors.push(...errors);
      results.push({
        conflict: fields.conflict,
        choice: fields.choice,
        reason: fields.reason,
        confidence: fields.confidence,
        validation_errors,
        absolute_index: range.start + m.index,
      });
    }
  }
  if (results.length > 1) {
    for (const r of results) r.multi_marker_turn = true;
  }
  return results;
}

module.exports = { extractMarkers };
```

**Step 4: Verify tests pass**

Run: `node --test /Users/ericpage/.claude/analytics/decision-log-extractor.test.js`
Expected: PASS (10 tests).

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add analytics/decision-log-extractor.js analytics/decision-log-extractor.test.js
git -C /Users/ericpage/.claude commit -m "feat(analytics): add two-stage DECISION-LOG marker extractor"
```

---

## ✅ Task 16: Write transcript-scoring library

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/analytics/transcript-scorer.js`
- Create: `/Users/ericpage/.claude/analytics/transcript-scorer.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/analytics/transcript-scorer.test.js`:

```js
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { scoreTranscriptFile, weekKey } = require('./transcript-scorer');

function writeTranscript(dir, name, entries) {
  fs.writeFileSync(path.join(dir, name), entries.map(e => JSON.stringify(e)).join('\n') + '\n');
}

describe('transcript-scorer', () => {
  let tmpdir;
  beforeEach(() => { tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), 'trans-')); });
  afterEach(() => { fs.rmSync(tmpdir, { recursive: true, force: true }); });

  describe('weekKey', () => {
    it('produces YYYY-WNN format (ISO-ish week)', () => {
      const key = weekKey(new Date('2026-04-20T12:00:00Z'));
      assert.match(key, /^2026-W\d{2}$/);
    });

    it('is stable within a single week', () => {
      const a = weekKey(new Date('2026-04-20T00:00:00Z'));
      const b = weekKey(new Date('2026-04-26T23:59:00Z'));
      assert.equal(a, b);
    });
  });

  describe('scoreTranscriptFile', () => {
    it('counts banned-phrase violations in assistant messages', () => {
      writeTranscript(tmpdir, 'a.jsonl', [
        { type: 'user', message: { role: 'user', content: 'do thing' } },
        { type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: "You're absolutely right, here we go." }] }, timestamp: '2026-04-20T10:00:00Z' },
      ]);
      const result = scoreTranscriptFile(path.join(tmpdir, 'a.jsonl'));
      assert.equal(result.violations.length, 1);
      assert.equal(result.violations[0].rule_id, 'banned-youre-right');
    });

    it('ignores user messages (only assistant responses are scored)', () => {
      writeTranscript(tmpdir, 'b.jsonl', [
        { type: 'user', message: { role: 'user', content: "You're absolutely right" } },
      ]);
      const result = scoreTranscriptFile(path.join(tmpdir, 'b.jsonl'));
      assert.equal(result.violations.length, 0);
    });

    it('handles assistant text as string OR array-of-content-blocks', () => {
      writeTranscript(tmpdir, 'c.jsonl', [
        { type: 'assistant', message: { role: 'assistant', content: "Spot on!" }, timestamp: '2026-04-20T10:00:00Z' },
        { type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: 'Fair point.' }, { type: 'tool_use' }] }, timestamp: '2026-04-20T10:01:00Z' },
      ]);
      const result = scoreTranscriptFile(path.join(tmpdir, 'c.jsonl'));
      assert.ok(result.violations.length >= 2);
    });

    it('detects user corrections in user messages and writes to corrections bucket', () => {
      writeTranscript(tmpdir, 'd.jsonl', [
        { type: 'user', message: { role: 'user', content: "wait, why aren't you running tests?" }, timestamp: '2026-04-20T10:00:00Z', sessionId: 's1' },
      ]);
      const result = scoreTranscriptFile(path.join(tmpdir, 'd.jsonl'));
      assert.equal(result.corrections.length, 1);
      assert.equal(result.corrections[0].tier, 'high');
    });

    it('extracts DECISION-LOG markers from assistant responses', () => {
      const marker = '<!-- DECISION-LOG conflict="A or B" choice="A" reason="faster" confidence="0.8" -->';
      writeTranscript(tmpdir, 'e.jsonl', [
        { type: 'assistant', message: { role: 'assistant', content: [{ type: 'text', text: `Before continuing, ${marker} done.` }] }, timestamp: '2026-04-20T10:00:00Z' },
      ]);
      const result = scoreTranscriptFile(path.join(tmpdir, 'e.jsonl'));
      assert.equal(result.decision_logs.length, 1);
      assert.equal(result.decision_logs[0].choice, 'A');
    });

    it('returns empty arrays for a missing file (returns null)', () => {
      const result = scoreTranscriptFile(path.join(tmpdir, 'nope.jsonl'));
      assert.equal(result, null);
    });

    it('skips malformed JSON lines gracefully', () => {
      fs.writeFileSync(path.join(tmpdir, 'bad.jsonl'),
        'not json\n' +
        JSON.stringify({ type: 'assistant', message: { content: "Spot on" }, timestamp: '2026-04-20T10:00:00Z' }) + '\n' +
        '{incomplete\n'
      );
      const result = scoreTranscriptFile(path.join(tmpdir, 'bad.jsonl'));
      assert.equal(result.violations.length, 1);
      assert.equal(result.malformed_lines, 2);
    });
  });
});
```

**Step 2: Verify tests fail**

Run: `node --test /Users/ericpage/.claude/analytics/transcript-scorer.test.js`
Expected: FAIL — module not found.

**Step 3: Write the implementation**

Create `/Users/ericpage/.claude/analytics/transcript-scorer.js`:

```js
// transcript-scorer.js — reads ~/.claude/projects/<project>/<sid>.jsonl
// transcripts and scores assistant responses against the Tier-A rule catalog,
// extracts DECISION-LOG markers, and runs user-correction detection on user
// messages. Returns structured results; does not write files.

const fs = require('fs');
const { scoreResponse } = require('./rule-catalog');
const { extractMarkers } = require('./decision-log-extractor');
const { detectCorrection } = require('./correction-parser');

function weekKey(date) {
  // ISO-like YYYY-WNN — Monday-start. Thursday of current week determines the year.
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const dayNum = (d.getUTCDay() + 6) % 7; // Mon=0
  d.setUTCDate(d.getUTCDate() - dayNum + 3); // Thursday of week
  const firstThursday = new Date(Date.UTC(d.getUTCFullYear(), 0, 4));
  const firstThursdayDayNum = (firstThursday.getUTCDay() + 6) % 7;
  firstThursday.setUTCDate(firstThursday.getUTCDate() - firstThursdayDayNum + 3);
  const weekNum = 1 + Math.round((d - firstThursday) / (7 * 86400000));
  return `${d.getUTCFullYear()}-W${String(weekNum).padStart(2, '0')}`;
}

function textFromContent(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    return content
      .filter(c => c && c.type === 'text' && typeof c.text === 'string')
      .map(c => c.text)
      .join('\n');
  }
  return '';
}

function scoreTranscriptFile(filePath) {
  let raw;
  try { raw = fs.readFileSync(filePath, 'utf-8'); }
  catch (_) { return null; }
  const lines = raw.split('\n').filter(Boolean);
  const out = { violations: [], corrections: [], decision_logs: [], malformed_lines: 0 };
  for (const line of lines) {
    let entry;
    try { entry = JSON.parse(line); }
    catch (_) { out.malformed_lines++; continue; }
    if (!entry || !entry.type || !entry.message) continue;
    const text = textFromContent(entry.message.content);
    if (!text) continue;
    if (entry.type === 'assistant') {
      for (const hit of scoreResponse(text)) {
        out.violations.push({
          ts: entry.timestamp || null,
          sid: entry.sessionId || null,
          rule_id: hit.rule.id,
          category: hit.rule.category,
          severity: hit.rule.severity,
          matched: hit.matched,
        });
      }
      for (const mk of extractMarkers(text)) {
        out.decision_logs.push({
          ts: entry.timestamp || null,
          sid: entry.sessionId || null,
          ...mk,
        });
      }
    } else if (entry.type === 'user') {
      const corr = detectCorrection(text);
      if (corr) {
        out.corrections.push({
          ts: entry.timestamp || null,
          sid: entry.sessionId || null,
          tier: corr.tier,
          confidence: corr.confidence,
          matched_phrase: corr.matched_phrase,
          prompt_excerpt: text.slice(0, 200),
        });
      }
    }
  }
  return out;
}

module.exports = { scoreTranscriptFile, weekKey };
```

**Step 4: Verify tests pass**

Run: `node --test /Users/ericpage/.claude/analytics/transcript-scorer.test.js`
Expected: PASS (9 tests).

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add analytics/transcript-scorer.js analytics/transcript-scorer.test.js
git -C /Users/ericpage/.claude commit -m "feat(analytics): add transcript scorer combining rules, corrections, decision-logs"
```

---

## ✅ Task 17: Write weekly-digest generator (scoreboard output)

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/analytics/weekly-digest.js`
- Create: `/Users/ericpage/.claude/analytics/weekly-digest.test.js`

**Step 1: Write the failing tests**

Create `/Users/ericpage/.claude/analytics/weekly-digest.test.js`:

```js
const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { renderScoreboard } = require('./weekly-digest');

describe('weekly-digest', () => {
  describe('renderScoreboard', () => {
    it('renders a one-page Tier-A scoreboard with the hero metric up top', () => {
      const input = {
        week_key: '2026-W17',
        window_start: '2026-04-20',
        window_end: '2026-04-26',
        this_week_total: 17,
        last_week_total: 21,
        per_rule: [
          { rule_id: 'banned-youre-right', this_week: 5, last_week: 6, trend: 'down' },
          { rule_id: 'banned-absolutely', this_week: 3, last_week: 2, trend: 'up' },
          { rule_id: 'heredoc-forbidden', this_week: 0, last_week: 1, trend: 'down' },
        ],
      };
      const md = renderScoreboard(input);
      assert.ok(md.startsWith('# Tier-A Rule Scoreboard — 2026-W17'));
      // Hero metric
      assert.ok(md.includes('Tier-A violations: 17'));
      assert.ok(md.includes('down 4')); // 17 vs 21
      // Per-rule grid
      assert.ok(md.includes('banned-youre-right'));
      assert.ok(md.includes('heredoc-forbidden'));
    });

    it('says "up N" when this week > last week', () => {
      const md = renderScoreboard({
        week_key: 'W', window_start: 'a', window_end: 'b',
        this_week_total: 25, last_week_total: 10, per_rule: [],
      });
      assert.ok(md.includes('up 15'));
    });

    it('says "flat" when this week == last week', () => {
      const md = renderScoreboard({
        week_key: 'W', window_start: 'a', window_end: 'b',
        this_week_total: 10, last_week_total: 10, per_rule: [],
      });
      assert.ok(md.includes('flat'));
    });

    it('notes "baseline (no prior week)" when last_week_total is null', () => {
      const md = renderScoreboard({
        week_key: 'W', window_start: 'a', window_end: 'b',
        this_week_total: 5, last_week_total: null, per_rule: [],
      });
      assert.ok(md.includes('baseline'));
    });

    it('is idempotent — rendering the same input twice produces identical output', () => {
      const input = {
        week_key: 'W', window_start: 'a', window_end: 'b',
        this_week_total: 3, last_week_total: 4,
        per_rule: [{ rule_id: 'r', this_week: 3, last_week: 4, trend: 'down' }],
      };
      assert.equal(renderScoreboard(input), renderScoreboard(input));
    });
  });
});
```

**Step 2: Verify tests fail**

Run: `node --test /Users/ericpage/.claude/analytics/weekly-digest.test.js`
Expected: FAIL — module not found.

**Step 3: Write the implementation**

Create `/Users/ericpage/.claude/analytics/weekly-digest.js`:

```js
#!/usr/bin/env node
// weekly-digest.js — Monday 1 scoreboard generator.
// Scans ~/.claude/projects/*/*.jsonl transcripts for the previous ISO week,
// scores them via transcript-scorer, compares to the week-before-last,
// writes a one-page markdown scoreboard to ~/.claude/digests/YYYY-WNN.md
// plus a latest.md symlink.
//
// Design: docs/plans/2026-04-23-claude-usage-logging-outcomes.md
//   "Monday 1 — protocols + scoreboard only (NO digest yet)"
// Idempotent: re-running the same week produces identical output.

const fs = require('fs');
const path = require('path');
const { scoreTranscriptFile, weekKey } = require('./transcript-scorer');
const { RULES } = require('./rule-catalog');

const PROJECTS_DIR = path.join(process.env.HOME, '.claude', 'projects');
const DIGESTS_DIR = path.join(process.env.HOME, '.claude', 'digests');

// Transcript directory structure (verified via Glob/ls during plan writing):
//   ~/.claude/projects/<project-slug>/
//     ├── <session-uuid>.jsonl                    ← MAIN session transcript (scored by Monday 1)
//     └── <session-uuid>/
//         └── subagents/
//             └── agent-<hash>.jsonl              ← subagent transcript (NOT scored Monday 1)
// readdirSync(projDir) yields both the .jsonl files AND the subdirectories; we
// filter for .endsWith('.jsonl') so only top-level main transcripts are read.
// Subagent transcripts are deferred to Monday 4+ (see Decision 7 for scope rationale).
function listTranscriptsInWindow(startMs, endMs) {
  const files = [];
  let projects = [];
  try { projects = fs.readdirSync(PROJECTS_DIR); } catch (_) { return files; }
  for (const p of projects) {
    const projDir = path.join(PROJECTS_DIR, p);
    let entries;
    try { entries = fs.readdirSync(projDir); } catch (_) { continue; }
    for (const f of entries) {
      if (!f.endsWith('.jsonl')) continue; // skip <session-uuid>/ subdirs
      const full = path.join(projDir, f);
      let stat;
      try { stat = fs.statSync(full); } catch (_) { continue; }
      if (!stat.isFile()) continue; // defensive: confirm it's not a directory
      if (stat.mtimeMs >= startMs && stat.mtimeMs < endMs) files.push(full);
    }
  }
  return files;
}

function aggregateWeek(startMs, endMs) {
  const files = listTranscriptsInWindow(startMs, endMs);
  const counts = {};
  for (const r of RULES) counts[r.id] = 0;
  for (const f of files) {
    const scored = scoreTranscriptFile(f);
    if (!scored) continue;
    for (const v of scored.violations) {
      if (counts[v.rule_id] === undefined) counts[v.rule_id] = 0;
      counts[v.rule_id]++;
    }
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  return { counts, total };
}

function renderScoreboard({ week_key, window_start, window_end, this_week_total, last_week_total, per_rule }) {
  let delta;
  if (last_week_total === null || last_week_total === undefined) {
    delta = 'baseline (no prior week)';
  } else if (this_week_total === last_week_total) {
    delta = 'flat';
  } else if (this_week_total > last_week_total) {
    delta = `up ${this_week_total - last_week_total}`;
  } else {
    delta = `down ${last_week_total - this_week_total}`;
  }
  const lines = [];
  lines.push(`# Tier-A Rule Scoreboard — ${week_key}`);
  lines.push('');
  lines.push(`**Window:** ${window_start} to ${window_end}`);
  lines.push('');
  lines.push(`> **Tier-A violations: ${this_week_total}** — ${delta}${last_week_total != null ? ` from last week (${last_week_total})` : ''}.`);
  lines.push('');
  lines.push('## Per-rule breakdown');
  lines.push('');
  lines.push('| Rule | This week | Last week | Trend |');
  lines.push('|---|---|---|---|');
  const sorted = [...per_rule].sort((a, b) => b.this_week - a.this_week);
  for (const r of sorted) {
    lines.push(`| \`${r.rule_id}\` | ${r.this_week} | ${r.last_week} | ${r.trend} |`);
  }
  lines.push('');
  lines.push('---');
  lines.push('_Generated by `~/.claude/analytics/weekly-digest.js`. See `docs/plans/2026-04-23-claude-usage-logging-outcomes.md` for interpretation._');
  return lines.join('\n') + '\n';
}

function weekWindowMs(anchorDate) {
  // Return [startMs, endMs) for the ISO week containing anchorDate.
  const d = new Date(anchorDate);
  const dayNum = (d.getUTCDay() + 6) % 7; // Mon=0
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(d.getUTCDate() - dayNum);
  const start = d.getTime();
  const end = start + 7 * 86400000;
  return [start, end];
}

function generate(now = new Date()) {
  // "Previous week" = the full 7-day window ending at last Monday 00:00 UTC.
  const lastWeekAnchor = new Date(now.getTime() - 7 * 86400000);
  const prevWeekAnchor = new Date(now.getTime() - 14 * 86400000);
  const [lwStart, lwEnd] = weekWindowMs(lastWeekAnchor);
  const [pwStart, pwEnd] = weekWindowMs(prevWeekAnchor);

  const thisAgg = aggregateWeek(lwStart, lwEnd);
  const prevAgg = aggregateWeek(pwStart, pwEnd);

  const per_rule = RULES.map(r => {
    const this_week = thisAgg.counts[r.id] || 0;
    const last_week = prevAgg.counts[r.id] || 0;
    const trend = this_week > last_week ? 'up' : this_week < last_week ? 'down' : 'flat';
    return { rule_id: r.id, this_week, last_week, trend };
  });

  const week_key = weekKey(new Date(lwStart + 86400000));
  const window_start = new Date(lwStart).toISOString().slice(0, 10);
  const window_end = new Date(lwEnd - 1).toISOString().slice(0, 10);

  const md = renderScoreboard({
    week_key, window_start, window_end,
    this_week_total: thisAgg.total,
    last_week_total: prevAgg.total,
    per_rule,
  });

  fs.mkdirSync(DIGESTS_DIR, { recursive: true });
  const outFile = path.join(DIGESTS_DIR, `${week_key}.md`);
  fs.writeFileSync(outFile, md);

  const latest = path.join(DIGESTS_DIR, 'latest.md');
  try { fs.unlinkSync(latest); } catch (_) { /* not yet present */ }
  fs.symlinkSync(outFile, latest);

  return outFile;
}

module.exports = { renderScoreboard, generate, weekWindowMs };

if (require.main === module) {
  const out = generate();
  console.log(`Wrote ${out}`);
}
```

**Step 4: Verify unit tests pass**

Run: `node --test /Users/ericpage/.claude/analytics/weekly-digest.test.js`
Expected: PASS (5 tests).

**Step 5: Dry-run the generator against real transcripts**

Run: `node /Users/ericpage/.claude/analytics/weekly-digest.js`
Expected: prints `Wrote /Users/ericpage/.claude/digests/2026-WNN.md`. Inspect the output file — hero metric, per-rule grid, idempotent re-run.

**Step 6: Commit**

```bash
git -C /Users/ericpage/.claude add analytics/weekly-digest.js analytics/weekly-digest.test.js
git -C /Users/ericpage/.claude commit -m "feat(analytics): add weekly digest scoreboard generator"
```

---

## ✅ Task 18: Create launchd plist for Monday 7am digest run

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/crons/com.ericpage.claude-digest.plist`
- Create: `/Users/ericpage/.claude/crons/run-digest.sh`

**Step 1: Write the runner shell script**

Create `/Users/ericpage/.claude/crons/run-digest.sh`:

```bash
#!/bin/bash
# run-digest.sh — launchd entry point. Runs the weekly digest generator.
# Logs stdout+stderr to ~/.claude/crons/last-digest.log for debugging.

NODE="/usr/local/bin/node"
if [ ! -x "$NODE" ]; then
  NODE="$(command -v node)"
fi

"$NODE" "$HOME/.claude/analytics/weekly-digest.js" > "$HOME/.claude/crons/last-digest.log" 2>&1
exit $?
```

Make it executable: `chmod +x /Users/ericpage/.claude/crons/run-digest.sh`

**Step 2: Write the launchd plist**

Create `/Users/ericpage/.claude/crons/com.ericpage.claude-digest.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ericpage.claude-digest</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/ericpage/.claude/crons/run-digest.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>1</integer>
    <key>Hour</key>
    <integer>7</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>RunAtLoad</key>
  <false/>
  <key>StandardOutPath</key>
  <string>/Users/ericpage/.claude/crons/last-digest.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/ericpage/.claude/crons/last-digest.log</string>
</dict>
</plist>
```

**Step 3: Validate the plist**

Run: `plutil -lint /Users/ericpage/.claude/crons/com.ericpage.claude-digest.plist`
Expected: `OK`.

**Step 4: Smoke-run the runner directly (not via launchd)**

Run: `bash /Users/ericpage/.claude/crons/run-digest.sh; echo exit=$?`
Expected: `exit=0`. Inspect `~/.claude/crons/last-digest.log` — should contain `Wrote /Users/ericpage/.claude/digests/...`.

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add crons/com.ericpage.claude-digest.plist crons/run-digest.sh
git -C /Users/ericpage/.claude commit -m "feat(crons): add Monday 7am launchd plist for weekly digest"
```

> NOTE: Loading the plist via `launchctl load -w ~/Library/LaunchAgents/com.ericpage.claude-digest.plist` is a manual post-automation step (see Manual Steps section). The plist file itself belongs in `~/.claude/crons/` as a source of truth; activating it is user-scoped.

---

## ✅ Task 19: Write drift-detector SessionStart hook

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/hooks/check-digest-drift.sh`

**Step 1: Write the script**

Create `/Users/ericpage/.claude/hooks/check-digest-drift.sh`:

```bash
#!/bin/bash
# check-digest-drift.sh — SessionStart hook.
# Emits [DIGEST READY] on the first Monday-or-later session when a fresh digest
# exists but has not yet been "read" (sentinel absent). Writing the sentinel is
# the side effect of emitting the tag — tag itself == read.
# Emits [DIGEST UNREAD] when >=2 consecutive weeks of digest-exists + sentinel-absent.
# Design: docs/plans/2026-04-23-claude-usage-logging-outcomes.md "Cue mechanism".

DIGESTS_DIR="$HOME/.claude/digests"
[ -d "$DIGESTS_DIR" ] || exit 0

# Use Python3 for ISO-calendar week key (year AND week from isocalendar; %Y+%V
# diverge on Dec 28-Jan 3 because %Y is Gregorian year while %V is ISO week).
# This matches the JS weekKey() Thursday-anchor algorithm used in weekly-digest.js.
current_key=$(/usr/bin/python3 -c "
import datetime
today = datetime.date.today()
y, w, _ = today.isocalendar()
print(f'{y}-W{w:02d}')
" 2>/dev/null)
[ -z "$current_key" ] && exit 0

digest_file="$DIGESTS_DIR/${current_key}.md"
sentinel="$DIGESTS_DIR/.read-${current_key}"

# Pre-existence guard: no-op if no digest file has ever been written (Monday 1 bootstrap)
if ! ls "$DIGESTS_DIR"/*.md >/dev/null 2>&1; then
  exit 0
fi

# Primary tag: digest exists for the current week but sentinel is absent
if [ -f "$digest_file" ] && [ ! -f "$sentinel" ]; then
  # Emit the tag AND write the sentinel (per outcomes doc: tag itself = read)
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "$sentinel"
  echo "[DIGEST READY] Weekly scoreboard available at ~/.claude/digests/${current_key}.md — Tier-A rule-violation summary for the past week."
  exit 0
fi

# Drift tag: count consecutive prior weeks with digest-exists + sentinel-absent
consecutive=0
for n in 1 2 3; do
  # Walk back N weeks. Use Python for date math (portable across macOS/GNU date).
  past_key=$(/usr/bin/python3 -c "
import datetime, sys
today = datetime.date.today()
iso = today - datetime.timedelta(weeks=int(sys.argv[1]))
y, w, _ = iso.isocalendar()
print(f'{y}-W{w:02d}')
" "$n" 2>/dev/null)
  [ -z "$past_key" ] && break
  past_digest="$DIGESTS_DIR/${past_key}.md"
  past_sentinel="$DIGESTS_DIR/.read-${past_key}"
  if [ -f "$past_digest" ] && [ ! -f "$past_sentinel" ]; then
    consecutive=$((consecutive + 1))
  else
    break
  fi
done

if [ "$consecutive" -ge 2 ]; then
  echo "[DIGEST UNREAD] ${consecutive} consecutive weekly digests unread — the drift detector has fired. Either read ~/.claude/digests/latest.md or run kill-criteria review from docs/plans/2026-04-23-claude-usage-logging-outcomes.md."
fi

exit 0
```

Make it executable: `chmod +x /Users/ericpage/.claude/hooks/check-digest-drift.sh`

**Step 2: Smoke-test (empty digests dir — no-op)**

```bash
mkdir -p /tmp/test-drift-empty
HOME=/tmp/test-drift-empty bash /Users/ericpage/.claude/hooks/check-digest-drift.sh
echo exit=$?
rm -rf /tmp/test-drift-empty
```
Expected: no output, exit=0.

**Step 3: Smoke-test (digest exists, sentinel absent — tag fires, sentinel written)**

```bash
TESTHOME=$(mktemp -d)
mkdir -p "$TESTHOME/.claude/digests"
CURRENT_KEY=$(/usr/bin/python3 -c "import datetime; y,w,_=datetime.date.today().isocalendar(); print(f'{y}-W{w:02d}')")
touch "$TESTHOME/.claude/digests/${CURRENT_KEY}.md"
HOME=$TESTHOME bash /Users/ericpage/.claude/hooks/check-digest-drift.sh
ls "$TESTHOME/.claude/digests/"
rm -rf "$TESTHOME"
```
Expected: one line starting with `[DIGEST READY]`. `ls` output includes `.read-<current_key>` sentinel.

**Step 4: Smoke-test (sentinel present — no tag)**

```bash
TESTHOME=$(mktemp -d)
mkdir -p "$TESTHOME/.claude/digests"
CURRENT_KEY=$(/usr/bin/python3 -c "import datetime; y,w,_=datetime.date.today().isocalendar(); print(f'{y}-W{w:02d}')")
touch "$TESTHOME/.claude/digests/${CURRENT_KEY}.md"
touch "$TESTHOME/.claude/digests/.read-${CURRENT_KEY}"
HOME=$TESTHOME bash /Users/ericpage/.claude/hooks/check-digest-drift.sh
echo exit=$?
rm -rf "$TESTHOME"
```
Expected: no output, exit=0.

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add hooks/check-digest-drift.sh
git -C /Users/ericpage/.claude commit -m "feat(hooks): add digest drift detector with sentinel-based read signal"
```

---

## ✅ Task 20: Wire check-digest-drift into settings.json

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/settings.json` (append to `SessionStart` array)

> ORDERING: Task 12 (which adds `SessionStart`) and Task 19 must both be committed first.

**Step 1: Read the current settings.json**

Read `/Users/ericpage/.claude/settings.json` in full. The `SessionStart` array now contains one entry (check-hook-errors) added by Task 12. Confirm the exact current structure before Editing.

**Step 2: Append the new hook to the existing SessionStart array**

Use Edit with a compact anchor on the last line of the existing check-hook-errors entry so that whitespace normalization in earlier steps doesn't break the match:

- `old_string` =
```json
            "command": "bash /Users/ericpage/.claude/hooks/check-hook-errors.sh",
            "timeout": 5
          }
        ]
      }
    ],
```
- `new_string` =
```json
            "command": "bash /Users/ericpage/.claude/hooks/check-hook-errors.sh",
            "timeout": 5
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/ericpage/.claude/hooks/check-digest-drift.sh",
            "timeout": 5
          }
        ]
      }
    ],
```

**Step 3: Validate JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('/Users/ericpage/.claude/settings.json','utf-8'))"
```

**Step 4: Commit**

```bash
git -C /Users/ericpage/.claude add settings.json
git -C /Users/ericpage/.claude commit -m "feat(settings): wire SessionStart to check-digest-drift"
```

---

## ✅ Task 21: Write QA-stale detector (manual-labeling backlog)

**Repo:** `~/.claude`

**Files:**
- Create: `/Users/ericpage/.claude/hooks/check-qa-stale.sh`

**Step 1: Write the script**

Create `/Users/ericpage/.claude/hooks/check-qa-stale.sh`:

```bash
#!/bin/bash
# check-qa-stale.sh — SessionStart hook.
# Counts pending manual-labeling items (calibration samples, protocol spot-check
# sessions, decision-trail entries awaiting grading). Fires [QA STALE] when
# backlog >50 items. Independent of digest reading — catches the case where the
# ritual has stopped entirely and kill-criteria inputs are not being produced.
# Design: docs/plans/2026-04-23-claude-usage-logging-outcomes.md
#   "Out-of-band [QA STALE] SessionStart tag".

LABEL_DIR="$HOME/.claude/digests/calibration"
[ -d "$LABEL_DIR" ] || exit 0

# Count files matching the pending-label convention: *.pending.jsonl
pending=0
for f in "$LABEL_DIR"/*.pending.jsonl; do
  [ -f "$f" ] || continue
  n=$(wc -l < "$f" | tr -d ' ')
  pending=$((pending + n))
done

if [ "$pending" -gt 50 ]; then
  echo "[QA STALE] ${pending} manual-labeling items pending (threshold: 50). See ~/.claude/digests/calibration/ — label at least 20 before the next Monday digest, or pause calibration-dependent kill criteria."
fi

exit 0
```

Make it executable: `chmod +x /Users/ericpage/.claude/hooks/check-qa-stale.sh`

**Step 2: Smoke-test (missing dir — no-op)**

```bash
bash /Users/ericpage/.claude/hooks/check-qa-stale.sh; echo exit=$?
```
Expected: no output, exit=0.

**Step 3: Smoke-test (trigger path)**

```bash
TESTHOME=$(mktemp -d)
mkdir -p "$TESTHOME/.claude/digests/calibration"
yes '{"stub":true}' | head -n 51 > "$TESTHOME/.claude/digests/calibration/sample.pending.jsonl"
HOME=$TESTHOME bash /Users/ericpage/.claude/hooks/check-qa-stale.sh
rm -rf "$TESTHOME"
```
Expected: one line starting with `[QA STALE]`.

**Step 4: Commit**

```bash
git -C /Users/ericpage/.claude add hooks/check-qa-stale.sh
git -C /Users/ericpage/.claude commit -m "feat(hooks): add QA-stale detector for manual-labeling backlog"
```

---

## ✅ Task 22: Wire check-qa-stale into settings.json

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/settings.json` (append to `SessionStart` array)

> ORDERING: Task 20 (previous SessionStart entry) and Task 21 must both be committed first.

**Step 1: Read the current settings.json**

Read `/Users/ericpage/.claude/settings.json` in full. The `SessionStart` array should now have exactly two entries (check-hook-errors and check-digest-drift). Confirm before Editing.

**Step 2: Append the third SessionStart entry**

Use Edit with a compact anchor on the unique digest-drift command line so downstream whitespace differences don't break the match:

- `old_string` =
```json
            "command": "bash /Users/ericpage/.claude/hooks/check-digest-drift.sh",
            "timeout": 5
          }
        ]
      }
    ],
```
- `new_string` =
```json
            "command": "bash /Users/ericpage/.claude/hooks/check-digest-drift.sh",
            "timeout": 5
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/ericpage/.claude/hooks/check-qa-stale.sh",
            "timeout": 5
          }
        ]
      }
    ],
```

**Step 3: Validate JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('/Users/ericpage/.claude/settings.json','utf-8'))"
```

**Step 4: Integration sanity check**

Start a new Claude Code session. Confirm no user-facing errors at session start (the three SessionStart hooks should all run silently unless their conditions trigger).

**Step 5: Commit**

```bash
git -C /Users/ericpage/.claude add settings.json
git -C /Users/ericpage/.claude commit -m "feat(settings): wire SessionStart to check-qa-stale"
```

---

## ✅ Task 23: Extend settings-audit knownHookCommands for new hooks

**Repo:** `~/.claude`

**Files:**
- Modify: `/Users/ericpage/.claude/crons/settings-audit.js` (the `knownHookCommands` set at lines 61-67)

> ORDERING: Tasks 10, 12, 20, and 22 must be committed first — each of those wires a new hook command that this task will register as "known" in the security auditor. If you skip this task, the next scheduled settings-audit run will emit MEDIUM findings for every new hook command and fire `[SETTINGS AUDIT]` SessionStart tags.

**Step 1: Read the current set**

Read `/Users/ericpage/.claude/crons/settings-audit.js` in full. Confirm the `knownHookCommands` Set literal is at (or near) lines 61-67 with five current entries. Note: the existing set is already *missing* `node /Users/ericpage/.claude/hooks/usage-tracker.js` — this pre-existing drift gets cleaned up as part of this task.

**Step 2: Extend the set**

Use Edit with:
- `old_string` =
```js
const knownHookCommands = new Set([
  '/Users/ericpage/.claude/hooks/check-cron-results.sh',
  '/Users/ericpage/.claude/hooks/check-test-audit.sh',
  'node /Users/ericpage/.claude/hooks/auto-approve-worktrees.js',
  'node /Users/ericpage/.claude/hooks/error-tracker.js',
  'node /Users/ericpage/.claude/hooks/auto-approve-safe-bash-paths.js',
]);
```
- `new_string` =
```js
const knownHookCommands = new Set([
  '/Users/ericpage/.claude/hooks/check-cron-results.sh',
  '/Users/ericpage/.claude/hooks/check-test-audit.sh',
  'node /Users/ericpage/.claude/hooks/auto-approve-worktrees.js',
  'node /Users/ericpage/.claude/hooks/error-tracker.js',
  'node /Users/ericpage/.claude/hooks/auto-approve-safe-bash-paths.js',
  'node /Users/ericpage/.claude/hooks/usage-tracker.js',
  'node /Users/ericpage/.claude/hooks/prompt-capture.js',
  'bash /Users/ericpage/.claude/hooks/check-hook-errors.sh',
  'bash /Users/ericpage/.claude/hooks/check-digest-drift.sh',
  'bash /Users/ericpage/.claude/hooks/check-qa-stale.sh',
]);
```

**Step 3: Run the audit script to verify no unknown-hook findings**

```bash
node /Users/ericpage/.claude/crons/settings-audit.js
cat /Users/ericpage/.claude/last-settings-audit.result
cat /Users/ericpage/.claude/last-settings-audit.details
```
Expected: `result` file contains `clean`, and `details` contains no `Unknown hook command` entries.

**Step 4: Commit**

```bash
git -C /Users/ericpage/.claude add crons/settings-audit.js
git -C /Users/ericpage/.claude commit -m "chore(security): register new hooks in settings-audit knownHookCommands"
```

---

## Manual Steps (Post-Automation)

<!--
To exempt a file from the manual-deploy gate, add a subsection below:
  ### Non-prod artifacts (exempt from gate)
  - `path/to/file.sql` — reason (token: seed|fixtures|test)
The token must appear literally in the file path, OR match one of the
catalog's built-in exempt tokens (seed, fixtures, test, __tests__).
-->

> Manual-deploy scan: no catalog matches detected.

The scan checked every `Create:` / `Modify:` file path in this plan against `skills/_shared/manual-deploy-artifact-catalog.md` (M1 Supabase migrations, M2 env-var additions). **No catalog matches** — this plan creates no `.sql` files under `supabase/migrations/`, and every `process.env.X` reference in the plan's code snippets uses only pre-existing system variables (`HOME`), not new `.env`-sourced variables.

### Non-prod artifacts (exempt from gate)

- `process.env.HOME` (appearing in `prompt-capture.js`, `weekly-digest.js`, `transcript-scorer.js`, `rule-catalog.js`) — system environment variable provided by the OS; not a deploy-time configuration variable (token: existing `.env.example` does not list it, and no deploy target requires it to be set).
- All `.test.js` / `.test.sh` files — built-in catalog exemption (`**/*.test.*`).

However, the launchd plist created in Task 18 is a manual-deploy artifact of a *different* kind (not catalogued): it must be loaded into user-level launchd before it fires. Complete these steps after Task 23 commits.

### Launchd activation

- [ ] Verify the Node binary path in the plist matches this machine. Run: `command -v node`. If the result is not `/usr/local/bin/node` (the path hard-coded in `~/.claude/crons/run-digest.sh`), update that script to use the correct path (or `"$(command -v node)"`). Apple Silicon Homebrew typically installs to `/opt/homebrew/bin/node`; nvm installs vary per user.
- [ ] Symlink the plist into `~/Library/LaunchAgents/`:
      `ln -sf /Users/ericpage/.claude/crons/com.ericpage.claude-digest.plist ~/Library/LaunchAgents/com.ericpage.claude-digest.plist`
- [ ] Load it: `launchctl load -w ~/Library/LaunchAgents/com.ericpage.claude-digest.plist`
- [ ] Verify it's registered: `launchctl list | grep ericpage.claude-digest` — should print the label.
- [ ] Force a one-shot run to confirm the wire: `launchctl start com.ericpage.claude-digest` — then `cat ~/.claude/crons/last-digest.log` should show `Wrote ...`.
- [ ] Inspect the digest file visually: `cat ~/.claude/digests/latest.md` — hero metric at top, per-rule grid below.

### Week-0 retroactive scoring (optional, recommended)

- [ ] Run the scorer manually against the last 4 weeks of transcripts to establish empirical Tier distribution before Monday 1's cadence kicks in:
      `node -e "const {generate} = require('/Users/ericpage/.claude/analytics/weekly-digest.js'); for (let w=1; w<=4; w++) generate(new Date(Date.now() - w*7*86400000));"`
- [ ] Inspect the 4 generated digest files in `~/.claude/digests/` — this is the empirical prior for the "Tier-A trending DOWN" week-4 outcome metric.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|-------------------------|
| 1 | Plan scope | Monday 1 only (not Monday 4/8) | All phases in one plan |
| 2 | Plan file location | `~/software/aligned_cc_skills/docs/plans/` (plugin repo) | `~/.claude/docs/plans/` (where most work lands) |
| 3 | Rule-catalog storage | JS module with regex literals | YAML file + loader; JSON file; read CLAUDE.md directly each run |
| 4 | Prompt-capture file-per-session | `prompts-<sid>.jsonl` | Shared `prompts.jsonl` with lock; daemon + Unix socket |
| 5 | Digest-read signal | Sentinel file written by the tag itself | `stat` access-time; a user-typed command |
| 6 | launchd plist location | `~/.claude/crons/` + symlink into `~/Library/LaunchAgents/` | Plist directly in `~/Library/LaunchAgents/` |
| 7 | Transcript scope | Main `<session-uuid>.jsonl` files only; exclude subagent transcripts | Include all nested `subagents/*.jsonl`; add new `Stop`-hook capture |
| 8 | DECISION-LOG extractor placement | New `~/.claude/analytics/` module | Inline in `weekly-digest.js` |
| 9 | Testing framework | `node --test` + `node:assert/strict` | Jest; Mocha; ava |
| 10 | Tier-A rule count at Monday 1 | ~18 rules (banned phrases + HEREDOC + bash-search) | 30% of CLAUDE.md rules (the outcomes doc target) |
| 11 | Week-key computation | Python3 isocalendar() in bash hooks; Thursday-anchor algorithm in JS | `date +%Y-W%V` (diverges on Dec 28-Jan 3 because `%Y` is Gregorian) |

### Appendix: Decision Details

#### Decision 1: Plan scope is Monday 1 only

**Chose:** Ship only the Monday-1 surface (protocols + scoreboard + prompt capture + drift detection).

**Why:** The outcomes doc is explicit that Monday 1 is a falsification setup — "do the protocols alone move Tier-A violations down? If yes, continue. If no, reconsider." Bundling Monday 4 and Monday 8 into a single plan forecloses that falsification by front-loading infrastructure whose value depends on Monday 1's validation. It also makes the plan unreviewable (~60 tasks, 3 cache windows of context). The outcomes doc's "phased rollout" section maps cleanly onto three separate plans; writing the next plan only after we've seen Monday 1 run means we can adjust based on empirical Tier distribution from Week 0 scoring, false-positive rates on the correction parser, and actual hook-error volumes.

**Alternatives rejected:**
- **All phases in one plan:** bloats the plan to >50 tasks, most of which cannot be evaluated without Monday 1 data. Pre-builds Monday 4's `session-meta/*.json` read path even if Monday 1's scoreboard reveals the technical design's architecture changes aren't needed. Worst: it couples the rollout gate (Monday 1 validates protocols) to infrastructure delivery, making "retire if protocols don't work" a larger throwaway.

#### Decision 2: Plan file location is the plugin repo

**Chose:** Write the plan to `~/software/aligned_cc_skills/docs/plans/2026-04-24-claude-usage-logging-monday1.md`.

**Why:** Both source design docs (`2026-04-23-claude-usage-logging-outcomes.md` and `2026-04-23-claude-usage-logging-design.md`) live in the plugin repo's `docs/plans/`. Plans co-located with their design docs let a future reader navigate the chain (design → plan → commits) without crossing repos. The skill's cross-repo guard exists to prevent plan-B-in-repo-A mistakes; here the plan and its primary design docs are correctly co-located. Tasks 5–22 edit files in `~/.claude/` — that's a distribution artifact of the work, not the plan itself.

**Alternatives rejected:**
- **`~/.claude/docs/plans/`:** would split the design docs from the plan across two repos, breaking the "plans live where the work happens" intent. Also: `~/.claude/` has no existing `docs/plans/` convention; adding one is a project-structure decision that shouldn't be smuggled in alongside unrelated work.

#### Decision 3: Rule-catalog is a JS module with regex literals

**Chose:** Hand-written `rule-catalog.js` with `RULES` array of `{id, category, pattern, severity, source_line}`.

**Why:** Regex literals in JS are checked by the JS parser at module-load time; a malformed pattern crashes the test suite immediately rather than silently failing to match at runtime. The source-of-truth for *why* each rule exists is CLAUDE.md; `source_line` citations in each entry keep the catalog auditable. When Eric edits CLAUDE.md, the rule catalog is a separate deliberate update (not auto-derived), which prevents accidental scope changes — the alternative (regenerating rules from CLAUDE.md text) would have the scorer's behavior silently change every time a word in CLAUDE.md is rephrased.

**Alternatives rejected:**
- **YAML + loader:** adds a dependency (js-yaml) for no gain; YAML strings that look like regexes need careful escaping. Loses parser-time syntax checking.
- **Read CLAUDE.md directly each run:** couples scorer behavior to prose drift. Every typo fix in CLAUDE.md silently changes measurement — exactly the "bad data is a bug" anti-pattern the author's global CLAUDE.md warns against.

#### Decision 4: Per-session prompt files, not shared

**Chose:** `prompts-<sid>.jsonl` per session.

**Why:** The technical design calls this out explicitly (`Change 3`, first bullet). macOS `PIPE_BUF` is 512 bytes — lines longer than that from parallel sessions interleave on a shared file. Per-session files sidestep the concurrency question entirely. The digest generator concatenates at read time, which is cheap even at thousands of files (current `~/.claude/projects/` already has 100+ transcript dirs and the generator reads them all fine).

**Alternatives rejected:**
- **Shared `prompts.jsonl` with lock:** introduces file-locking on the hot path with a <50ms p95 budget. File locks on macOS via `fs.flockSync` are unreliable on APFS under load.
- **Daemon + Unix socket:** major new surface area (daemon lifecycle, restart on crash, socket cleanup). Technical design says "not now."

#### Decision 5: Digest-read signal is sentinel-written-by-tag

**Chose:** The `[DIGEST READY]` tag itself writes `.read-<week>` as its side effect.

**Why:** The outcomes doc says "tag itself = read" explicitly. This eliminates the contamination of `stat` access-time (Spotlight, Time Machine, editor mmap, iCloud Drive all update access-time without human eyeballs on the file). It also means if Eric opens a session on Tuesday morning, the tag fires once, the sentinel is written, and no more nagging that week — matching the intended habit cue (one weekly notification, not a nag loop).

**Alternatives rejected:**
- **`stat` access-time:** contaminated by background processes as noted.
- **Require typed command to write sentinel:** bad UX. The tag fires before Eric has typed anything; requiring a separate command splits the read-acknowledgement ritual.

#### Decision 6: Plist in `~/.claude/crons/` with symlink activation

**Chose:** Source-of-truth plist at `~/.claude/crons/com.ericpage.claude-digest.plist`; user symlinks into `~/Library/LaunchAgents/` as a manual activation step.

**Why:** `~/.claude/` is git-tracked (crons dir is in the allowlist). `~/Library/LaunchAgents/` is not — and shouldn't be, because symlinks into version control is fragile across machines. The symlink approach means the plist's content history lives with the rest of the config, and if Eric re-clones `~/.claude/` on a new machine, activation is a one-line `ln -sf + launchctl load`.

**Alternatives rejected:**
- **Plist directly in `~/Library/LaunchAgents/`:** un-version-controlled. A typo in the schedule is unrecoverable.
- **Auto-load via post-install hook:** `~/.claude/` has no install step; the auto-commit launchd agent is user-configured, not plugin-configured. Adding install automation is out of Monday 1's scope.

#### Decision 7: Main-session transcripts only for Monday 1

**Chose:** The scorer reads `~/.claude/projects/<project-slug>/<session-uuid>.jsonl` only. Subagent transcripts at `<session-uuid>/subagents/agent-*.jsonl` are intentionally excluded from Monday 1.

**Why:** Verified directory structure via `ls ~/.claude/projects/<project-slug>/` during plan writing — each project slug contains BOTH top-level `<session-uuid>.jsonl` files (main sessions) AND `<session-uuid>/` subdirectories holding `subagents/agent-*.jsonl` (dispatched sub-agent transcripts). Monday 1's scope is "Eric's direct interaction with Claude" — rule violations in his own sessions. Subagent responses are produced by agents Claude dispatched (Explore, general-purpose, code-reviewer, etc.) and they don't share Eric's CLAUDE.md behavioral constraints the same way — they're tool uses, not conversation. Scoring them would contaminate the Tier-A signal with agent-response noise. Adding a `Stop`-hook to capture anything new is work without signal, and the technical design defers full-response logging to Monday 4+.

**Alternatives rejected:**
- **Include subagent transcripts:** adds volume without improving the Tier-A trend signal. Different agents have different prompts; banned-phrase matches against (e.g.) a code-reviewer's "excellent coverage" self-praise would fire rule `banned-excellent` even though that rule targets Eric-facing responses. Defer to Monday 4+ when per-agent scoring can be calibrated separately.
- **`Stop`-hook capture:** duplicates existing data, introduces a new <50ms hot-path hook. Monday 4+ scope per technical design.

#### Decision 8: DECISION-LOG extractor as a separate module

**Chose:** `decision-log-extractor.js` in `analytics/`, exported to the transcript scorer and (future) Monday 4 section-3 generator.

**Why:** Two-stage parsing with code-fence exclusion is non-trivial (~80 lines including error handling). Isolating it in a module with its own test file means the parser's edge cases (nested markers, embedded quotes, confidence range) are unit-tested without dragging the transcript-scoring orchestration along. Monday 4's section-3 generator will reuse it.

**Alternatives rejected:**
- **Inline in weekly-digest.js:** digest generator bloats. Edge-case tests end up embedded in a larger test file that's harder to run selectively.

#### Decision 9: `node --test` + `node:assert/strict`

**Chose:** Stdlib test runner.

**Why:** Matches the existing testing pattern in `~/.claude/crons/pre-commit-secrets.test.js` (verified by Read during survey). Zero dependencies, which matters here since `~/.claude/` has no `package.json` and no install step.

**Alternatives rejected:**
- **Jest:** requires `npm install`, `node_modules/` in a repo that auto-commits. Would break the auto-commit pattern unless gitignored carefully.
- **Mocha/ava:** same npm dependency concern as Jest.

#### Decision 10: ~18 rules at Monday 1

**Chose:** Ship with all detectable banned phrases + HEREDOC + bash-search (~18 rules total) rather than the "30% of CLAUDE.md rules" target the outcomes doc cites.

**Why:** The 30% figure was aspirational prior to the Week-0 empirical scoring. Banned phrases, HEREDOC, and bash-search are the deterministic rules with zero ambiguity — substring-or-regex matches against exact quoted text in CLAUDE.md. Starting with these minimizes false positives in Week 1 when the correction-parser and scoreboard need trust. Additional Tier-A rules (e.g., "cd + && compound commands" from CLAUDE.md:20-23) can be added as one-per-week items post Week-0 calibration.

**Alternatives rejected:**
- **Exactly 30% of CLAUDE.md rules:** forces padding the catalog with harder-to-detect rules (e.g., "confirm the frame first" → no deterministic regex exists). Shipping false-positive-prone rules Week 1 poisons the calibration signal that informs Tier-B phase-in.

#### Decision 11: Python3 isocalendar() for bash week keys

**Chose:** All bash scripts that compute the current ISO week (check-digest-drift.sh) use `/usr/bin/python3 -c "...isocalendar()..."` rather than `date +%Y-W%V`.

**Why:** `date +%Y` returns the Gregorian calendar year, while `date +%V` returns the ISO week number. These diverge on Dec 28–Jan 3: Dec 29, 2026 is in ISO week 2027-W01 but `%Y` returns `2026`, producing the nonsense key `2026-W01`. The JS weekly-digest.js uses a Thursday-anchor algorithm that correctly computes ISO year + week together; the bash scripts must match that algorithm so sentinel filenames align with digest filenames. Python's `datetime.date.isocalendar()` returns `(iso_year, iso_week, iso_weekday)` as a tuple — exactly what's needed. The Python3 shebang line `/usr/bin/python3` ships with macOS by default (verified via `ls /usr/bin/python3`).

**Alternatives rejected:**
- **`date +%Y-W%V`:** silently wrong ~3 days per year. The cost of debugging a Jan-2 sentinel mismatch outweighs the cost of one Python3 call on session start (Python3 cold start is ~50-80ms; the SessionStart timeout budget is 5s per hook).
- **GNU date `+%G-W%V`:** `%G` is the ISO year, but `/usr/bin/date` on macOS is BSD date and does not support `%G`. Would require `brew install coreutils` and invoking `gdate`, adding a hidden system dependency for every plan executor.

