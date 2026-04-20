# Manual-Deploy Artifacts Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a "manual-deploy artifact" detection layer that auto-injects Post-Automation plan entries at plan-write time and hard-gates merges at finish-time when catalog-matched files lack verified evidence.

**Source Design Doc:** `docs/plans/2026-04-20-manual-deploy-artifacts-rca-design.md`

**Mockups:** `docs/mockups/2026-04-20-manual-deploy-artifacts.html` (referenced by the design doc)

**Architecture:** Three-layer v1 covering Supabase migrations (M1, CRITICAL) and env-var additions (M2, MEDIUM). The foundation is a new shared catalog at `skills/_shared/manual-deploy-artifact-catalog.md`; the root fix is a new "Manual Deploy Artifact Scan" step inside `writing-plans/SKILL.md` that populates the plan's `## Manual Steps (Post-Automation)` section; the enforcement layer is a new `Step 0.5` inside `finishing-a-development-branch/SKILL.md` that hard-gates merge on missing evidence and persists pasted evidence back into the plan file. Supporting tests live under `e2e/tests/` and `e2e/scenarios/`.

**Tech Stack:** Markdown (skill files, catalog, plan), YAML (`eval-surface.yaml`, `trigger-map.yaml`, scenario files), Python + `pytest` + `pyyaml` (test suite at `e2e/tests/`), `promptfoo` (LLM eval scenarios).

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Confirm the `e2e/` Python environment is available: `pip install -r e2e/requirements.txt` from the repo root succeeds and `pytest --version` prints a version ≥7.0.
- [ ] Confirm the main worktree path is `/Users/ericpage/software/aligned_cc_skills` (run `git worktree list` — the first line's path). All tasks below use repo-root-relative paths.

---

## Task Ordering Notes

The following tasks share files and must run in the order listed (they are not safe to parallelize):

- `skills/_shared/manual-deploy-artifact-catalog.md` — Tasks 1, 3, 4 (create → add M1 → add M2).
- `e2e/tests/test_manual_deploy_catalog.py` — Tasks 2, 3, 4 (TDD-failing → pass with M1 → pass with M2).
- `skills/writing-plans/SKILL.md` — Tasks 5, 6 (add scan step → add authorship exception note).
- `skills/finishing-a-development-branch/SKILL.md` — Task 10 (Step 0.5 addition). Task 12 verifies the cross-ref test passes (no edits).
- `e2e/eval-surface.yaml` — Task 15.
- `e2e/trigger-map.yaml` — Task 16.
- `README.md` + `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — Task 22.

Phase ordering: Phase 1 (catalog + tests) → Phase 2 (writing-plans edits) → Phase 3 (finishing-a-development-branch edits + cross-ref test) → Phase 4 (fixtures + integration test) → Phase 5 (eval wiring) → Phase 6 (docs + version bump + verify).

---

## Phase 1: Catalog Foundation

### ✅ Task 1: Create the catalog file with schema header and empty severity sections

**Files:**
- Create: `skills/_shared/manual-deploy-artifact-catalog.md`

**Step 1: Create the catalog file**

Write the file with this exact content:

```markdown
# Manual-Deploy Artifact Catalog

Reference document for the manual-deploy artifact detection step. Lists file classes whose creation in a diff deterministically implies a non-automatable production step (e.g., DB migrations, environment variables). Consumed by `skills/writing-plans/SKILL.md` (Manual Deploy Artifact Scan step) and `skills/finishing-a-development-branch/SKILL.md` (Step 0.5: Manual Deploy Artifact Gate).

This catalog is a **superset** of `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` in shape: severity-section organization and prose per-entry, PLUS a small fenced block inside each entry carrying machine-matchable fields.

## Contents

- [Schema](#schema)
- [Built-in Non-Prod Exemption Patterns](#built-in-non-prod-exemption-patterns)
- [CRITICAL — Production Outage if Skipped](#critical--production-outage-if-skipped)
  - M1: Supabase Migration
- [MEDIUM — Likely Runtime Error or Silent Misconfig](#medium--likely-runtime-error-or-silent-misconfig)
  - M2: Environment Variable Addition

---

## Schema

Every entry is a `###` heading with severity inferred from the section it is under. Each entry contains:

- Prose sections: `**Why it needs manual deploy:**`, `**Detection:**`, `**Prod step (for the plan entry):**`, `**Plan section populated:**`.
- Exactly one fenced ```` ```yaml ```` block with these allowed fields:
  - `detector_glob:` OR `detector_grep:` (at least one; may have both)
  - `severity:` (`CRITICAL` | `HIGH` | `MEDIUM` | `LOW`) — must match the parent section
  - `evidence:` map with `kind:` and `template:` (regex or structured validator description)

Adding a new artifact class: copy an existing entry, replace fields, keep the fenced-block field names identical. The catalog-integrity pytest at `e2e/tests/test_manual_deploy_catalog.py` validates this schema.

---

## Built-in Non-Prod Exemption Patterns

Files matching ANY of these globs are exempt by default and never produce a gate prompt:

- `**/seed/**`
- `**/fixtures/**`
- `**/__tests__/**`
- `**/*.test.*`

Plan authors may declare additional exemptions inline (see `skills/writing-plans/SKILL.md` "Manual Deploy Artifact Scan" step for syntax).

---

## CRITICAL — Production Outage if Skipped

_Entries added in subsequent tasks._

---

## MEDIUM — Likely Runtime Error or Silent Misconfig

_Entries added in subsequent tasks._
```

**Step 2: Verify the file was created**

Run: `ls -1 skills/_shared/manual-deploy-artifact-catalog.md`
Expected: one line printing the path (no error).

**Step 3: Commit**

```bash
git add skills/_shared/manual-deploy-artifact-catalog.md
git commit -m "feat: scaffold manual-deploy artifact catalog with schema"
```

---

### ✅ Task 2: Write catalog-integrity pytest (failing)

**Files:**
- Create: `e2e/tests/test_manual_deploy_catalog.py`

**Step 1: Write the failing test file**

Create `e2e/tests/test_manual_deploy_catalog.py` with this content:

```python
"""Validate manual-deploy-artifact-catalog.md schema: every entry has required
prose sections, a single fenced yaml block with allowed fields, and severity
matching the parent section."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = E2E_DIR.parent
CATALOG_FILE = REPO_ROOT / "skills" / "_shared" / "manual-deploy-artifact-catalog.md"

ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
REQUIRED_PROSE_HEADERS = (
    "**Why it needs manual deploy:**",
    "**Detection:**",
    "**Prod step (for the plan entry):**",
    "**Plan section populated:**",
)


def _read_catalog() -> str:
    return CATALOG_FILE.read_text(encoding="utf-8")


def _section_severity(text: str, entry_start: int) -> str | None:
    """Find the nearest preceding `## <SEVERITY> —` section header."""
    header_re = re.compile(r"^## (CRITICAL|HIGH|MEDIUM|LOW) —", re.MULTILINE)
    last = None
    for m in header_re.finditer(text):
        if m.start() < entry_start:
            last = m.group(1)
        else:
            break
    return last


def _iter_entries(text: str):
    """Yield (entry_id, entry_body, parent_severity) tuples.

    An entry starts with `### <ID>: <Title>` and ends at the next `###` heading
    or a following `## ` (severity) heading, whichever comes first.
    """
    entry_starts = list(re.finditer(r"^### (M\d+): ", text, re.MULTILINE))
    next_h2 = list(re.finditer(r"^## ", text, re.MULTILINE))
    for i, m in enumerate(entry_starts):
        entry_id = m.group(1)
        body_start = m.end()
        next_h3 = entry_starts[i + 1].start() if i + 1 < len(entry_starts) else len(text)
        # Also stop at the next `## ` if it precedes the next `###`.
        stop_h2 = next((h2.start() for h2 in next_h2 if h2.start() > body_start), len(text))
        body_end = min(next_h3, stop_h2)
        parent = _section_severity(text, m.start())
        yield entry_id, text[body_start:body_end], parent


def test_catalog_file_exists():
    assert CATALOG_FILE.exists(), f"Catalog file missing: {CATALOG_FILE}"


def test_catalog_has_schema_header():
    text = _read_catalog()
    assert "## Schema" in text, "Catalog must contain a '## Schema' section"


def test_catalog_has_builtin_exemption_patterns():
    text = _read_catalog()
    assert "**/seed/**" in text
    assert "**/fixtures/**" in text
    assert "**/__tests__/**" in text
    assert "**/*.test.*" in text


def test_catalog_has_at_least_one_entry():
    text = _read_catalog()
    entries = list(_iter_entries(text))
    assert entries, "Catalog must contain at least one entry (### M<n>: ...)"


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_has_required_prose_headers(entry_id, body, parent_severity):
    for header in REQUIRED_PROSE_HEADERS:
        assert header in body, f"Entry {entry_id} missing prose header: {header}"


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_has_exactly_one_fenced_yaml_block(entry_id, body, parent_severity):
    blocks = re.findall(r"```yaml\n(.*?)```", body, re.DOTALL)
    assert len(blocks) == 1, (
        f"Entry {entry_id} must have exactly one ```yaml fenced block, found {len(blocks)}"
    )


@pytest.mark.parametrize("entry_id,body,parent_severity", list(_iter_entries(_read_catalog())))
def test_entry_yaml_block_has_allowed_fields(entry_id, body, parent_severity):
    blocks = re.findall(r"```yaml\n(.*?)```", body, re.DOTALL)
    data = yaml.safe_load(blocks[0])
    assert isinstance(data, dict), f"Entry {entry_id} yaml block must parse to a mapping"
    # Must have detector_glob or detector_grep (or both)
    assert "detector_glob" in data or "detector_grep" in data, (
        f"Entry {entry_id} must define detector_glob or detector_grep"
    )
    # severity
    assert "severity" in data, f"Entry {entry_id} missing severity"
    assert data["severity"] in ALLOWED_SEVERITIES, (
        f"Entry {entry_id} severity must be one of {ALLOWED_SEVERITIES}"
    )
    assert data["severity"] == parent_severity, (
        f"Entry {entry_id} severity {data['severity']!r} does not match parent "
        f"section {parent_severity!r}"
    )
    # evidence
    assert "evidence" in data and isinstance(data["evidence"], dict), (
        f"Entry {entry_id} missing 'evidence' map"
    )
    assert "kind" in data["evidence"] and data["evidence"]["kind"], (
        f"Entry {entry_id} evidence.kind must be non-empty"
    )
    assert "template" in data["evidence"] and data["evidence"]["template"], (
        f"Entry {entry_id} evidence.template must be non-empty"
    )
```

**Step 2: Run the test to verify it fails**

Run: `pytest e2e/tests/test_manual_deploy_catalog.py -v`
Expected: FAIL — `test_catalog_has_at_least_one_entry` fails (no `### M<n>:` entries in the catalog yet). Other tests that depend on iterating entries will collect as empty parametrize and pass trivially, which is fine.

**Step 3: Commit**

```bash
git add e2e/tests/test_manual_deploy_catalog.py
git commit -m "test: add catalog-integrity pytest for manual-deploy artifacts"
```

---

### ✅ Task 3: Add M1 (Supabase Migration) entry to the catalog

**Files:**
- Modify: `skills/_shared/manual-deploy-artifact-catalog.md` (append M1 under the CRITICAL section)

**Step 1: Edit the CRITICAL section**

Replace the placeholder line:

```
## CRITICAL — Production Outage if Skipped

_Entries added in subsequent tasks._
```

with:

```markdown
## CRITICAL — Production Outage if Skipped

### M1: Supabase Migration

**Why it needs manual deploy:** Supabase projects that use the SQL Editor workflow require each migration to be applied by hand in the target environment. Unapplied migrations mean production code depends on schema (tables, columns, RPCs, policies) that does not exist — producing 500s, infinite redirects, or silent data-path failures.

**Detection:**
- Glob new files under `supabase/migrations/*.sql` in the branch diff.
- Exclude built-in non-prod patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`).

**Prod step (for the plan entry):** "Apply each migration below via the Supabase SQL Editor in the production project. Paste the SQL Editor URL (recommended) or the file's SHA-256 hash back into this section when done."

**Plan section populated:** `## Manual Steps (Post-Automation)` — subsection `### M1 migrations`.

**Machine-matchable fields:**

```yaml
detector_glob: "supabase/migrations/*.sql"
severity: CRITICAL
evidence:
  kind: url-or-hash-or-paste
  template: "One of: (a) Supabase SQL Editor URL matching https://supabase\\.com/dashboard/project/[a-z0-9]+/sql/[0-9a-f-]+ ; (b) SHA-256 hash (64 hex chars) of the migration file's committed contents; (c) a paste containing a >=30-character substring of the committed migration file."
```
```

**Step 2: Run the catalog-integrity test**

Run: `pytest e2e/tests/test_manual_deploy_catalog.py -v`
Expected: PASS — all parametrized tests now include M1 and validate successfully.

**Step 3: Commit**

```bash
git add skills/_shared/manual-deploy-artifact-catalog.md
git commit -m "feat: add M1 (Supabase Migration) entry to manual-deploy catalog"
```

---

### ✅ Task 4: Add M2 (Environment Variable Addition) entry to the catalog

**Files:**
- Modify: `skills/_shared/manual-deploy-artifact-catalog.md` (append M2 under the MEDIUM section)

**Step 1: Edit the MEDIUM section**

Replace:

```
## MEDIUM — Likely Runtime Error or Silent Misconfig

_Entries added in subsequent tasks._
```

with:

```markdown
## MEDIUM — Likely Runtime Error or Silent Misconfig

### M2: Environment Variable Addition

**Why it needs manual deploy:** New `process.env.FOO` references in source code crash at runtime (or read `undefined` silently) unless the variable is set in the hosting provider (Vercel / Netlify / Fly / self-hosted). Code ships green; the first request on production throws.

**Detection:**
- Grep for `process\.env\.[A-Z_]+` in source and cross-check against `.env.example`. Any name referenced in the diff that is not yet in `.env.example` is a candidate.
- Also detect when `.env.example` itself is modified to add a variable.
- Exclude the built-in non-prod patterns.

**Prod step (for the plan entry):** "Set each new variable in the hosting provider's environment settings. Paste the provider dashboard URL showing the variable is set (Vercel format: `https://vercel.com/*/settings/environment-variables`; Netlify and Fly analogous)."

**Plan section populated:** `## Manual Steps (Post-Automation)` — subsection `### M2 env vars`.

**Machine-matchable fields:**

```yaml
detector_grep: "process\\.env\\.[A-Z_]+"
detector_glob: ".env.example"
severity: MEDIUM
evidence:
  kind: name-and-url
  template: "Variable name (literal match of what was added to .env.example) AND a hosting-provider dashboard URL — Vercel: https://vercel\\.com/[^ ]+/settings/environment-variables ; Netlify: https://app\\.netlify\\.com/[^ ]+/settings/env ; Fly: https://fly\\.io/apps/[^ ]+/secrets ."
```
```

**Step 2: Run the catalog-integrity test**

Run: `pytest e2e/tests/test_manual_deploy_catalog.py -v`
Expected: PASS — M1 and M2 both validated.

**Step 3: Commit**

```bash
git add skills/_shared/manual-deploy-artifact-catalog.md
git commit -m "feat: add M2 (env var addition) entry to manual-deploy catalog"
```

---

## Phase 2: writing-plans Integration

### ✅ Task 5: Add "Manual Deploy Artifact Scan" step to writing-plans/SKILL.md

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (insert a new `## Manual Deploy Artifact Scan` section immediately BEFORE the `## Fact-Check + Critique Panel` section. Note: in the current file, `## Fact-Check + Critique Panel` precedes `## Verification Gate` in document order. Use `## Fact-Check + Critique Panel (mandatory, 2 parallel technical critics)` as the INSERT-BEFORE anchor — it is the only unique literal that survives future edits.)

**Step 1: Locate the anchor**

Use Grep on `skills/writing-plans/SKILL.md` for the exact literal `## Fact-Check + Critique Panel`. This is the anchor for the INSERT-BEFORE operation.

**Step 2: Insert the new section**

Use Edit with `old_string` = the line `## Fact-Check + Critique Panel (mandatory, 2 parallel technical critics)` and `new_string` = the new section followed by the original line, preserving exact formatting:

```markdown
## Manual Deploy Artifact Scan

**Purpose:** Detect files in the plan that require a manual production step (e.g., Supabase migrations, env-var additions). Auto-populate `## Manual Steps (Post-Automation)` so the user sees the obligation at plan time.

**Run this step BEFORE the Fact-Check + Critique Panel.** In the current SKILL.md file, the `## Fact-Check + Critique Panel` section precedes `## Verification Gate` in document order; insert the new `## Manual Deploy Artifact Scan` section immediately before `## Fact-Check + Critique Panel` (which is the only reliable anchor). If the plan has no catalog match, the step still runs and emits the "no matches" message below.

**Catalog:** Read `skills/_shared/manual-deploy-artifact-catalog.md` in full. Each entry under `## CRITICAL — ...` and `## MEDIUM — ...` is a class. Each class carries a fenced ```` ```yaml ```` block with `detector_glob` / `detector_grep`, `severity`, and `evidence.template`.

**Scan procedure:**

1. Build a file list from the plan body: every path after `Create:` or `Modify:` inside any task's `**Files:**` block.
2. For each path, apply the built-in non-prod exemption patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`). Matches are exempt — do NOT produce a Post-Automation entry. Surface a single-line comment in the conversation output below: "Exempt (built-in pattern): <path>".
3. For each non-exempt path, match against every catalog entry's `detector_glob` / `detector_grep`. Bucket matches by artifact class (M1, M2).
4. If there are matches:
   - Ensure the plan has a `## Manual Steps (Post-Automation)` section; create one immediately after the final task if missing.
   - Under that section, for each matched class, inject a subsection `### <class-id> <class-name>` (e.g., `### M1 migrations`) if not already present.
   - Under the subsection, list each matched file as a bullet: `- \`<path>\` — [evidence pending]`.
   - Immediately above the `## Manual Steps (Post-Automation)` heading, inject the exemption-syntax HTML comment (see "Exemption syntax" below) if not already present.

**Exemption syntax (HTML comment injected above Post-Automation):**

```markdown
<!--
To exempt a file from the manual-deploy gate, add a subsection below:
  ### Non-prod artifacts (exempt from gate)
  - `path/to/file.sql` — reason (token: seed|fixtures|test)
The token must appear literally in the file path, OR match one of the
catalog's built-in exempt tokens (seed, fixtures, test, __tests__).
-->
```

**Visible conversation output:**

After the scan completes, print ONE of the following blocks to the user (never silently inject):

If at least one catalog match was found:

```
Manual-deploy scan: detected N catalog matches.
- Added Post-Automation entries for:
  • M1 migrations (N): <up to 10 file paths, truncate with "+ N more">
  • M2 env vars (N): <up to 10 file paths, truncate with "+ N more">
- Declared exemptions (built-in pattern match): <list or "none">
```

If no catalog matches were found:

```
Manual-deploy scan: no catalog matches detected.
```

Cap each class list at 10 entries; for overflow append a "+ N more" line.

**Idempotency:** The injection is structural (find-by-heading, append-list-item). Re-running the scan on a plan that already contains the expected entries MUST NOT duplicate them. Match existing entries by file-path string equality on each list item.

**Known v1 gap:** projects that automate migration application via CI (e.g., `supabase db push` on deploy) must declare per-file exemptions for every migration. A project-level opt-out is deferred to v2.

```

(Then the original `## Fact-Check + Critique Panel ...` line continues as before.)

**Step 3: Verify the edit did not break the rest of the file**

Run: `grep -n "^## " skills/writing-plans/SKILL.md` (use the Grep tool).
Expected: `## Manual Deploy Artifact Scan` appears between `## Verification Gate` and `## Fact-Check + Critique Panel`, no duplicates, and no other H2 moved.

**Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "feat(writing-plans): add Manual Deploy Artifact Scan step"
```

---

### ✅ Task 6: Document the authorship exception in writing-plans/SKILL.md

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (add a note inside the "Plan File Location Rule" subsection)

**Step 1: Locate the anchor**

Use Grep on `skills/writing-plans/SKILL.md` for the exact literal: `Plans MUST always be written to the main worktree directory and committed to \`main\`.`

**Step 2: Append the exception note immediately after that sentence's paragraph**

Use Edit with `old_string` = the sentence above (the entire bolded sentence) and `new_string` = the same sentence plus, on the next paragraph:

```markdown

**Exception: Step 0.5 evidence writes.** Step 0.5 of `finishing-a-development-branch` is the single allowed out-of-skill plan mutation: when it captures pasted manual-deploy evidence, it edits the plan file in place (wherever the plan is located — `docs/plans/` or `docs/plans/completed/`) and commits it with a `chore:` message. All other plan writes remain centralized in this skill. See `skills/finishing-a-development-branch/SKILL.md` "Step 0.5: Manual Deploy Artifact Gate" for the full protocol.
```

**Step 3: Verify presence**

Run: `grep -n "out-of-skill plan mutation" skills/writing-plans/SKILL.md` (use the Grep tool).
Expected: one match.

**Step 4: Commit**

```bash
git add skills/writing-plans/SKILL.md
git commit -m "docs(writing-plans): note Step 0.5 authorship exception"
```

---

### ✅ Task 7: Update plan-critique-checklist.md §10 to reference the catalog

**Files:**
- Modify: `skills/writing-plans/plan-critique-checklist.md` (the §10 "Gap analysis — unvalidated assumptions" section)

**Step 1: Locate the anchor**

Use Grep for the literal `### 10. Gap analysis — unvalidated assumptions`.

**Step 2: Add a new row to the §10 table**

Use Edit to add a new row after the "Environment assumptions" row, keeping the same markdown table format:

```markdown
| Manual-deploy artifacts | Are files matching `skills/_shared/manual-deploy-artifact-catalog.md` (migrations, env vars) covered by entries in the plan's `## Manual Steps (Post-Automation)` section? Missing coverage is a **high** severity issue. |
```

**Step 3: Add a BAD/GOOD example pair**

Still inside §10, after the existing BAD/GOOD examples, add:

```markdown
- BAD: Plan creates `supabase/migrations/022_foo.sql` but has no Post-Automation entry listing that file
- GOOD: Plan's Post-Automation section has `### M1 migrations` with `supabase/migrations/022_foo.sql` listed as a bullet
```

**Step 4: Verify presence**

Run the Grep tool for `manual-deploy-artifact-catalog.md` on `skills/writing-plans/plan-critique-checklist.md`.
Expected: one match inside §10's table.

**Step 5: Commit**

```bash
git add skills/writing-plans/plan-critique-checklist.md
git commit -m "docs(writing-plans): checklist §10 covers manual-deploy catalog"
```

---

### ✅ Task 8: Extend the Verifier prompt to enforce Post-Automation coverage

**Files:**
- Modify: `skills/writing-plans/references/critique-panel-prompts.md` (the Round 1 Verifier prompt, Phase 3 paragraph)

**Step 1: Locate the anchor**

Use Grep for the literal `**Phase 3 (Critique):**` in `skills/writing-plans/references/critique-panel-prompts.md`. Only the Round 1 Verifier section contains this anchor.

**Step 2: Append coverage-check instruction to Phase 3**

Use Edit to change the Phase 3 sentence:

Old:
```
**Phase 3 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the plan against checklist criteria 1, 2, 4, 7, and 8 through your accuracy-and-fidelity lens.
```

New:
```
**Phase 3 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the plan against checklist criteria 1, 2, 4, 7, 8, AND 10's manual-deploy row through your accuracy-and-fidelity lens. For checklist 10's manual-deploy row: read `skills/_shared/manual-deploy-artifact-catalog.md`, extract the catalog's `detector_glob` / `detector_grep` patterns, walk every `Create:` / `Modify:` path in the plan, and for each catalog-matched path verify there is a corresponding entry in the plan's `## Manual Steps (Post-Automation)` section — OR an explicit exemption under `### Non-prod artifacts (exempt from gate)`. Any catalog-matched path missing both is a **high** severity finding.
```

**Step 3: Verify presence**

Run Grep for `manual-deploy-artifact-catalog.md` on `skills/writing-plans/references/critique-panel-prompts.md`.
Expected: one match, inside Phase 3 of the Round 1 Verifier prompt.

**Step 4: Commit**

```bash
git add skills/writing-plans/references/critique-panel-prompts.md
git commit -m "feat(writing-plans): Verifier enforces Post-Automation coverage"
```

---

## Phase 3: finishing-a-development-branch Integration

### ✅ Task 9: Write cross-reference CI check (failing)

**Files:**
- Create: `e2e/tests/test_skill_cross_references.py`

**Step 1: Write the failing test**

Create `e2e/tests/test_skill_cross_references.py`:

```python
"""Guards the bidirectional authorship-exception link between writing-plans
and finishing-a-development-branch SKILL.md files. A silent rename of either
side breaks the contract; this test catches it in CI."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WRITING_PLANS = REPO_ROOT / "skills" / "writing-plans" / "SKILL.md"
FINISHING = REPO_ROOT / "skills" / "finishing-a-development-branch" / "SKILL.md"


WRITING_PLANS_REQUIRED = (
    "Step 0.5 of ",
    "finishing-a-development-branch",
    "out-of-skill plan mutation",
)

FINISHING_REQUIRED = (
    "writing-plans/SKILL.md",
    "out-of-skill plan mutation",
    "Step 0.5: Manual Deploy Artifact Gate",
)


@pytest.mark.parametrize("needle", WRITING_PLANS_REQUIRED)
def test_writing_plans_mentions_exception(needle):
    text = WRITING_PLANS.read_text(encoding="utf-8")
    assert needle in text, (
        f"writing-plans/SKILL.md is missing required string: {needle!r}. "
        f"This guards the bidirectional authorship-exception link with "
        f"finishing-a-development-branch/SKILL.md."
    )


@pytest.mark.parametrize("needle", FINISHING_REQUIRED)
def test_finishing_mentions_exception(needle):
    text = FINISHING.read_text(encoding="utf-8")
    assert needle in text, (
        f"finishing-a-development-branch/SKILL.md is missing required string: "
        f"{needle!r}. This guards the bidirectional authorship-exception link "
        f"with writing-plans/SKILL.md."
    )
```

**Step 2: Run the test — some should pass, some should fail**

Run: `pytest e2e/tests/test_skill_cross_references.py -v`
Expected:
- Tests for `WRITING_PLANS_REQUIRED` all PASS (Task 6 added these strings).
- Tests for `FINISHING_REQUIRED` all FAIL — the strings do not exist in `finishing-a-development-branch/SKILL.md` yet (Step 0.5 not written).

**Step 3: Commit**

```bash
git add e2e/tests/test_skill_cross_references.py
git commit -m "test: add cross-reference guard for authorship exception"
```

---

### ✅ Task 10: Add Step 0.5 to finishing-a-development-branch/SKILL.md

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md` (insert a new `### Step 0.5: Manual Deploy Artifact Gate` subsection between `### Step 0: Deployment Platform Audit` and `### Step 1: Verify Tests`)

**Step 1: Locate the anchor**

Use Grep for the literal `### Step 1: Verify Tests` in `skills/finishing-a-development-branch/SKILL.md`. This is the INSERT-BEFORE anchor.

**Step 2: Insert the new subsection**

Use Edit with `old_string` = the line `### Step 1: Verify Tests` and `new_string` = the new subsection followed by the original `### Step 1:` line:

```markdown
### Step 0.5: Manual Deploy Artifact Gate

**Purpose:** Block merge when the branch adds files in a "manual-deploy artifact" class (per `skills/_shared/manual-deploy-artifact-catalog.md`) without documented evidence that the manual production step was performed. This catches the failure mode where code ships but a migration / env var / etc. is never applied.

**Catalog:** Read `skills/_shared/manual-deploy-artifact-catalog.md` in full for the artifact classes, their `detector_glob` / `detector_grep` patterns, and per-class evidence `template:` regex.

**Diff source:** Reuse the diff already computed in Step 0's "Module-Level Mutable State (HIGH)" sub-check:

```bash
git diff --name-only <base-branch>...HEAD
```

Also capture each file's status letter (A/D/R/M) via `git diff --name-status <base-branch>...HEAD`. Do NOT re-run Step 1c's diff — that step has not executed yet.

**Find the plan file:** Scan both `docs/plans/*.md` (top-level) AND `docs/plans/completed/*.md`. Match on branch-name pattern or explicit plan name from the user. **If the same branch-name pattern matches both locations, prefer the active (top-level) plan.** Archived plans only load when no active plan matches. If the plan is in `completed/`, edit it in place — do NOT un-archive.

**Authorship-convention exception:** This step is the single allowed out-of-skill plan mutation. See `skills/writing-plans/SKILL.md` "Exception: Step 0.5 evidence writes" for the documented exception.

**The gate, end-to-end:**

1. **Detect.** Match each diff entry against every catalog entry's detector. Bucket matches by artifact class (M1, M2). Exclude files matching catalog built-in exempt patterns (`**/seed/**`, `**/fixtures/**`, `**/__tests__/**`, `**/*.test.*`) and files matching the plan's `### Non-prod artifacts (exempt from gate)` declarations (see "Exemption validation" below).
2. **Parse plan Post-Automation.** Read the plan's `## Manual Steps (Post-Automation)` section. For each catalog bucket, find the matching `### <class-id>` subsection. Match on structural shape (heading + list items containing the file paths), not line numbers. If `## Manual Steps (Post-Automation)` is missing entirely, STOP with this message:

   ```
   Plan is missing the Post-Automation section. Either writing-plans did not
   run the Manual Deploy Artifact Scan, or the section was manually removed.
   Re-run writing-plans' scan step to regenerate the section, then re-run
   Step 0.5.
   ```

3. **Check evidence per file.** For each file in each bucket, inspect its list item in the plan. Classify as:
   - `has-evidence` — a sub-bullet contains evidence that matches the catalog's `evidence.template:` regex
   - `already-applied` — a sub-bullet of the form `already-applied — YYYY-MM-DD by <author>` is present
   - `exempt` — the file appears in the plan's `### Non-prod artifacts (exempt from gate)` subsection AND the declaration passes exemption validation
   - `needs-evidence` — none of the above
   Also check the ledger at `docs/plans/.manual-deploy-ledger.md` (see "Ledger" below). If a ledger entry matches on BOTH `{file-hash}` AND `{project-ref}`, mark the file `has-evidence` (ledger-hit).

4. **Handle A / D / R / M statuses (per M1 diff-status handling):**
   - **A (added):** normal gate — requires evidence.
   - **D (deleted):** deletion of a migration file is itself a manual-deploy artifact. Require evidence using the same template: paste of SQL Editor `DROP` / revert output URL (kind a) or the deleted-file hash (kind b).
   - **R (renamed):** if `--find-renames` shows the content hash unchanged, treat as no-op; otherwise treat as A + D on the new and old paths respectively.
   - **M (modified):** for files matching the M1 detector (`supabase/migrations/*.sql`), modification is a severe error — Supabase does not re-apply an edited migration. STOP with:

     ```
     CRITICAL: Modified an existing migration file (<path>). This will NOT
     re-apply in Supabase — production will diverge from source. Create a
     new migration instead. Do not merge until resolved.
     ```

     Do not accept evidence for this case. Block merge.

5. **Gate.** If any file is `needs-evidence`, emit ONE prompt block per artifact class (not per file — prevents repetition when many migrations are gated). Cap the displayed file list at 10 entries with a truncation note "(+ N more — see plan for full list)".

   **Prompt text template:**

   ```
   Branch introduces {N} {artifact-class-name} requiring manual production action.

   Files:
     - <path 1>
     - <path 2>
     (up to 10; "+ N more" if exceeded)

   Prod step: <from catalog entry's "Prod step (for the plan entry)">

   For each file, paste ONE of (in order of preference):
     • RECOMMENDED: The <provider> dashboard URL showing the step was
       performed (format per catalog evidence.template regex). Only this
       kind cannot be fabricated locally.
     • FALLBACK (reduces but does not prevent reflexive-yes): <kind b from
       catalog>.
     • FALLBACK (reduces but does not prevent reflexive-yes): <kind c from
       catalog>.

   Or declare the file exempt by adding to the plan under:
     ### Non-prod artifacts (exempt from gate)
     - `<path>` — reason (token: seed|fixtures|test|__tests__)

   Or mark it `already-applied` for pre-existing branches (use sparingly;
   accepted once per file without re-prompt). Paste exactly:
     <filename>: already-applied — YYYY-MM-DD by <author>

   Paste below, one entry per line, prefixed by filename:
   ```

   Per-file paste is required; batched/aggregated evidence is not accepted.

6. **Validate pasted evidence** against the catalog's `evidence.template:` regex. Valid → proceed to Write. Invalid → re-prompt, up to 2 retries (3 total attempts). After the third failed attempt, STOP with a clear error naming the still-failing file(s).

7. **Write.** For each validated paste, edit the plan file in place:
   - Structural edit: find the `## Manual Steps (Post-Automation)` heading, then the `### <class-id>` subsection, then the list item whose path matches the file. Append a sub-bullet containing the pasted evidence.
   - Do NOT use line numbers. Anchor on headings and path-string equality.
   - If the target list item is missing (user manually removed it between writing-plans and finishing), RE-INJECT the list item under the correct class heading, then append the evidence sub-bullet.

8. **Commit.** Stage ONLY the plan file: `git add <plan-path>`. Commit with the message `chore: record manual deploy evidence for <feature-name>` — honor all pre-commit hooks (do NOT use `--no-verify`). If the project's commit-lint configuration requires a scope, use `chore(deploy): record manual deploy evidence for <feature-name>` instead.

9. **Update ledger.** Append one line per committed evidence to `docs/plans/.manual-deploy-ledger.md` (see "Ledger" below).

**Write-path failure handling:**

- **Plan file write fails** (permissions, disk full): STOP. Surface the OS error. Ask the user to resolve and re-run Step 0.5. Do NOT proceed.
- **`## Manual Steps (Post-Automation)` missing or malformed:** STOP with the message in step 2 above.
- **Evidence placeholder deleted between writing-plans and finishing:** re-inject the entry (per step 7), then continue.
- **Commit fails:**
  - **Related hook failure on the plan file:** surface the error, fix, retry.
  - **Unrelated hook failure** (e.g., ESLint failing on a staged `.js` file from another commit): instruct the user to resolve or stash the unrelated work, then re-run Step 0.5. Evidence is already on disk; on re-run, the per-file state scan (step 3) will detect `has-evidence` and skip re-prompting, jumping straight to commit.
- **Later gate fails after evidence commit:** the evidence commit stands — evidence is true regardless of whether the branch ultimately merges. Do not roll back.

**Exemption validation (per-file exemptions declared in the plan):**

Exemption entries under `### Non-prod artifacts (exempt from gate)` MUST use this form:

```markdown
- `path/to/file.sql` — reason (token: <name>)
```

The declared `<name>` MUST appear literally in the file path, OR be one of the catalog's built-in exempt tokens (`seed`, `fixtures`, `test`, `__tests__`). If the token is absent from the path and not a built-in token, REJECT the exemption with:

```
Exemption for `<path>` claims token `<name>` but the path doesn't contain
that token. Valid built-in tokens: seed, fixtures, test, __tests__.
Either (a) rename the path to include one of those tokens, (b) change
the declared token to one that appears in the path, or (c) remove the
exemption and provide evidence via the normal gate.
```

**Ledger (`docs/plans/.manual-deploy-ledger.md`):**

Append-only. One line per applied artifact. Format:

```
{file-hash} {date} {branch} {project-ref}
```

- `{file-hash}` — SHA-256 of the committed file contents (64 hex chars).
- `{date}` — YYYY-MM-DD.
- `{branch}` — the branch name.
- `{project-ref}` — parsed from evidence kind (a)'s dashboard URL (e.g., Supabase `/project/<ref>/sql/` segment). If the user pasted only kind (b) or (c) evidence, write `project-ref: unknown`.

**Ledger lookup** (step 3, ledger-hit classification): match on BOTH `{file-hash}` AND `{project-ref}`. A hash match with `project-ref: unknown` does NOT skip the gate — the entry is treated as insufficient to confirm production application.

If the ledger file does not exist, create it on first write. Commit the ledger alongside the plan in the same `chore:` commit.

**Gitignore guard (before first ledger write):** Run `git check-ignore -v docs/plans/.manual-deploy-ledger.md` in the target project. If the file is gitignored (command exits 0 with output), surface:

```
Ledger path `docs/plans/.manual-deploy-ledger.md` is gitignored in this project.
The ledger must be committed for cross-branch lookup to work. Either:
  (a) un-ignore it: add `!docs/plans/.manual-deploy-ledger.md` to .gitignore
  (b) change the ledger path in finishing-a-development-branch/SKILL.md to
      a location that is not gitignored (e.g., `.manual-deploy-ledger.md` at
      repo root)
Not resolving this means every branch re-prompts the same already-applied
migrations — safe but noisy.
```

Proceed with the evidence write + plan commit regardless (the ledger is an optimization, not a correctness requirement), but surface the warning ONCE per Step 0.5 invocation.

**Blocking behavior:** If after 3 evidence attempts any file remains `needs-evidence`, stop with:

```
Manual-deploy gate: <N> file(s) still missing valid evidence after 3 attempts.
Cannot proceed to Step 1 until resolved.

Files still failing: <list>
```

Exit. Do not proceed to `### Step 1: Verify Tests`.

**If all files pass:** Report "Manual-deploy gate passed: all N catalog-matched files have evidence." Continue to Step 1.

**If no catalog matches in the diff:** Report "Manual-deploy gate: no catalog matches detected." Continue to Step 1.

```

(Then the original `### Step 1: Verify Tests` line and its body continue as before.)

**Step 3: Verify the insertion did not duplicate or displace other step headings**

Run the Grep tool for `^### Step ` on `skills/finishing-a-development-branch/SKILL.md` (use `output_mode: content`).
Expected output includes, in order:
- `### Step 0: Deployment Platform Audit`
- `### Step 0.5: Manual Deploy Artifact Gate`
- `### Step 1: Verify Tests`
- `### Step 1a: Verify Build`
- `### Step 1b: LLM Eval (auto-run if surface changed)`
- `### Step 1c: Architecture Doc Update`
- `### Step 1d: Code Review`
- `### Step 1e: Code Simplification Scan`
- `### Step 1f: Mockup Fidelity Check`
- `### Step 1g: Fix Mockup Deviations (user-directed)`
- `### Step 2: Determine Base Branch`
- (through `### Step 7: Completion Summary`)

**Step 4: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "feat(finishing): add Step 0.5 Manual Deploy Artifact Gate"
```

---

### ✅ Task 11: Update deployment-pitfall-catalog.md intro to scope and cross-reference

**Behavior note:** `deployment-pitfall-catalog.md` is loaded by the LLM at `Step 0: Deployment Platform Audit` execution time (per `finishing-a-development-branch/SKILL.md:52`). Narrowing the intro's described scope to "runtime bugs in bundled code" may cause the model to prune audit categories that do not fit that description. The new text retains the CRITICAL/HIGH/MEDIUM/LOW sections verbatim — only the intro paragraph changes — so the per-category Detection patterns still fire. Verify Step 0's findings output format is unchanged by re-reading the catalog after the edit.

**Files:**
- Modify: `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md` (the intro paragraph)

**Step 1: Locate the anchor**

Use Grep for the literal `Reference document for the Vercel deployment audit step.`.

**Step 2: Replace the intro paragraph**

Use Edit to change:

Old:
```
Reference document for the Vercel deployment audit step. Contains detection patterns, explanations, false positive guidance, and recommended fixes for each audit category.
```

New:
```
Reference document for the Vercel deployment audit step — **scoped to runtime bugs in bundled code** (e.g., `__dirname`/`__filename` resolution, `process.env[...]` bracket access, module-level mutable state). Contains detection patterns, explanations, false positive guidance, and recommended fixes for each audit category.

> For **manual-deploy artifacts** (DB migrations, env-var additions, cron/webhook setup, DNS — anything that requires a non-automatable production step), see the separate catalog at `skills/_shared/manual-deploy-artifact-catalog.md`. That catalog is a superset of this one in shape (severity-section organization, prose per entry) and adds a fenced machine-matchable block per entry for programmatic detection. Different concern; do not conflate.
```

**Step 3: Verify presence**

Run Grep for `manual-deploy-artifact-catalog.md` on `skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md`.
Expected: one match, in the intro block.

**Step 4: Commit**

```bash
git add skills/finishing-a-development-branch/references/deployment-pitfall-catalog.md
git commit -m "docs(finishing): scope pitfall catalog and cross-ref manual-deploy catalog"
```

---

### ✅ Task 12: Verify cross-reference CI check now passes

**Files:**
- (no edits — this task runs the test suite)

**Step 1: Run the cross-reference test**

Run: `pytest e2e/tests/test_skill_cross_references.py -v`
Expected: ALL tests PASS. Both sides of the bidirectional link now contain the required strings:

- `writing-plans/SKILL.md` contains: `Step 0.5 of `, `finishing-a-development-branch`, `out-of-skill plan mutation`
- `finishing-a-development-branch/SKILL.md` contains: `writing-plans/SKILL.md`, `out-of-skill plan mutation`, `Step 0.5: Manual Deploy Artifact Gate`

**Step 2: Commit (no file changes, so this task produces no commit)**

Note: this task has no file changes. Skip `git commit`. Proceed to Task 13.

---

## Phase 4: Fixtures + Integration Test

### ✅ Task 13: Scaffold the fixture directory layout

**Files:**
- Create: `e2e/fixtures/manual-deploy/plans/active-plan-before-scan.md`
- Create: `e2e/fixtures/manual-deploy/plans/active-plan-after-scan.md`
- Create: `e2e/fixtures/manual-deploy/plans/plan-with-evidence-complete.md`
- Create: `e2e/fixtures/manual-deploy/plans/plan-with-exemption.md`
- Create: `e2e/fixtures/manual-deploy/diffs/migration-added.txt`
- Create: `e2e/fixtures/manual-deploy/diffs/env-var-added.txt`
- Create: `e2e/fixtures/manual-deploy/diffs/migration-modified.txt`
- Create: `e2e/fixtures/manual-deploy/expected-outputs/post-automation-m1.md`
- Create: `e2e/fixtures/manual-deploy/expected-outputs/post-automation-m2.md`

**Step 1: Create the directory structure and fixture plan `active-plan-before-scan.md`**

This fixture represents a plan before the Manual Deploy Artifact Scan has run. It has one task that creates a Supabase migration.

Write `e2e/fixtures/manual-deploy/plans/active-plan-before-scan.md`:

```markdown
# Fixture Plan: Add TOS Version Column

> Fixture — used by `e2e/tests/test_manual_deploy_integration.py`. Represents a plan BEFORE the Manual Deploy Artifact Scan runs.

**Goal:** Add `tos_accepted_version` column to `profiles`.

**Source Design Doc:** N/A

---

### Task 1: Add migration

**Files:**
- Create: `supabase/migrations/022_add_tos_version.sql`

**Step 1:** Write the migration.

```sql
ALTER TABLE profiles ADD COLUMN tos_accepted_version INTEGER;
```

**Step 2:** Commit.
```

**Step 2: Create `active-plan-after-scan.md`**

This is the expected post-scan version of the above — now with the injected Post-Automation section and exemption HTML comment.

Write `e2e/fixtures/manual-deploy/plans/active-plan-after-scan.md`:

```markdown
# Fixture Plan: Add TOS Version Column

> Fixture — used by `e2e/tests/test_manual_deploy_integration.py`. Represents the plan AFTER the Manual Deploy Artifact Scan has injected the Post-Automation section.

**Goal:** Add `tos_accepted_version` column to `profiles`.

**Source Design Doc:** N/A

---

### Task 1: Add migration

**Files:**
- Create: `supabase/migrations/022_add_tos_version.sql`

**Step 1:** Write the migration.

```sql
ALTER TABLE profiles ADD COLUMN tos_accepted_version INTEGER;
```

**Step 2:** Commit.

---

<!--
To exempt a file from the manual-deploy gate, add a subsection below:
  ### Non-prod artifacts (exempt from gate)
  - `path/to/file.sql` — reason (token: seed|fixtures|test)
The token must appear literally in the file path, OR match one of the
catalog's built-in exempt tokens (seed, fixtures, test, __tests__).
-->

## Manual Steps (Post-Automation)

### M1 migrations

- `supabase/migrations/022_add_tos_version.sql` — [evidence pending]
```

**Step 3: Create `plan-with-evidence-complete.md`**

This fixture represents a plan that already has evidence pasted in — the idempotent case. Used by the integration test to verify Step 0.5 does NOT re-prompt when evidence is already present.

Write `e2e/fixtures/manual-deploy/plans/plan-with-evidence-complete.md`:

```markdown
# Fixture Plan: Migration With Evidence

> Fixture — simulates a plan AFTER Step 0.5 has captured evidence.

### Task 1: Add migration

**Files:**
- Create: `supabase/migrations/022_add_tos_version.sql`

---

## Manual Steps (Post-Automation)

### M1 migrations

- `supabase/migrations/022_add_tos_version.sql` — [evidence pending]
  - https://supabase.com/dashboard/project/abcdef123456/sql/12345678-abcd-1234-abcd-123456789abc
```

**Step 4: Create `plan-with-exemption.md`**

Write `e2e/fixtures/manual-deploy/plans/plan-with-exemption.md`:

```markdown
# Fixture Plan: Seed Migration (Exempt)

> Fixture — simulates a plan declaring an exemption for a seed migration.

### Task 1: Add seed migration

**Files:**
- Create: `supabase/migrations/seed/023_test_data.sql`

---

## Manual Steps (Post-Automation)

### Non-prod artifacts (exempt from gate)

- `supabase/migrations/seed/023_test_data.sql` — seed data (token: seed)
```

**Step 5: Create the diff fixtures**

Write `e2e/fixtures/manual-deploy/diffs/migration-added.txt`:

```
A	supabase/migrations/022_add_tos_version.sql
```

Write `e2e/fixtures/manual-deploy/diffs/env-var-added.txt`:

```
M	.env.example
M	src/lib/config.ts
```

Write `e2e/fixtures/manual-deploy/diffs/migration-modified.txt`:

```
M	supabase/migrations/021_existing.sql
```

**Step 6: Create the expected-output fixtures (partial markdown snippets used by structural assertions)**

Write `e2e/fixtures/manual-deploy/expected-outputs/post-automation-m1.md`:

```markdown
## Manual Steps (Post-Automation)

### M1 migrations

- `supabase/migrations/022_add_tos_version.sql` — [evidence pending]
```

Write `e2e/fixtures/manual-deploy/expected-outputs/post-automation-m2.md`:

```markdown
## Manual Steps (Post-Automation)

### M2 env vars

- `.env.example` — [evidence pending]
```

**Step 7: Verify all fixture files exist**

Run the Glob tool for `e2e/fixtures/manual-deploy/**/*`.
Expected: 9 files listed across the three subdirectories.

**Step 8: Commit**

```bash
git add e2e/fixtures/manual-deploy/
git commit -m "test: scaffold manual-deploy fixture plans, diffs, and expected outputs"
```

---

### ✅ Task 14: Write structural integration test

**Note — intentional deviation from design doc §5 task 9:** the design doc names `e2e/tests/test_finish_step_0_5_idempotent.py` as a required deliverable. That filename is NOT created by this plan. The idempotency property is instead covered by (a) the structural fixture test below, which asserts that a post-scan plan has the expected shape (the contract the scan step must satisfy), and (b) eval scenario (a), which runs the actual LLM against a before-scan fixture and asserts the output contains the Post-Automation section exactly once. See Decision 3 for the rationale. Do NOT create `test_finish_step_0_5_idempotent.py` — it would duplicate scan logic in Python and become its own source of truth.

**Files:**
- Create: `e2e/tests/test_manual_deploy_integration.py`

**Step 1: Write the failing test**

Create `e2e/tests/test_manual_deploy_integration.py`:

```python
"""Structural fixture-driven test for the manual-deploy Post-Automation
section shape. Validates the expected post-scan plan layout — the mechanical
contract the writing-plans scan step is expected to produce, and the shape
Step 0.5 relies on for parsing. Does not invoke the LLM; behavioral coverage
lives in the promptfoo eval scenarios under e2e/scenarios/manual-deploy/."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent.parent
FIXTURES = E2E_DIR / "fixtures" / "manual-deploy"


def _read(relative: str) -> str:
    return (FIXTURES / relative).read_text(encoding="utf-8")


def test_active_plan_before_scan_has_no_post_automation_section():
    text = _read("plans/active-plan-before-scan.md")
    assert "## Manual Steps (Post-Automation)" not in text, (
        "Before-scan fixture must not have a Post-Automation section"
    )


def test_active_plan_after_scan_has_post_automation_section():
    text = _read("plans/active-plan-after-scan.md")
    assert "## Manual Steps (Post-Automation)" in text
    assert "### M1 migrations" in text
    assert "supabase/migrations/022_add_tos_version.sql" in text
    assert "[evidence pending]" in text


def test_active_plan_after_scan_injects_exemption_html_comment():
    text = _read("plans/active-plan-after-scan.md")
    # The comment must precede the Post-Automation heading
    comment_idx = text.find("To exempt a file from the manual-deploy gate")
    heading_idx = text.find("## Manual Steps (Post-Automation)")
    assert comment_idx != -1, "Exemption HTML comment must be present"
    assert comment_idx < heading_idx, (
        "Exemption HTML comment must appear before the Post-Automation heading"
    )


def test_plan_with_evidence_complete_parses_as_valid():
    text = _read("plans/plan-with-evidence-complete.md")
    m1_idx = text.find("### M1 migrations")
    assert m1_idx != -1
    # Evidence sub-bullet must be a SQL Editor URL matching M1's regex kind (a)
    url_re = re.compile(
        r"https://supabase\.com/dashboard/project/[a-z0-9]+/sql/[0-9a-f-]+"
    )
    assert url_re.search(text[m1_idx:]), (
        "plan-with-evidence-complete must have an M1 sub-bullet matching the "
        "SQL Editor URL regex"
    )


def test_plan_with_exemption_declares_built_in_token():
    text = _read("plans/plan-with-exemption.md")
    assert "### Non-prod artifacts (exempt from gate)" in text
    # Each exemption line must end with `(token: <name>)`
    exempt_lines = [
        line
        for line in text.splitlines()
        if line.startswith("- `") and "(token:" in line
    ]
    assert exempt_lines, "Exemption fixture must have at least one (token: ...) line"
    for line in exempt_lines:
        # The path must contain the declared token
        path_match = re.match(r"^- `([^`]+)`.*\(token: ([a-z_]+)\)", line)
        assert path_match, f"Malformed exemption line: {line}"
        path, token = path_match.group(1), path_match.group(2)
        builtin_tokens = {"seed", "fixtures", "test", "__tests__"}
        assert token in path or token in builtin_tokens, (
            f"Exemption token '{token}' must appear in path or be a built-in token"
        )


def test_diff_fixtures_have_expected_status_letters():
    added = _read("diffs/migration-added.txt").strip().splitlines()
    assert all(line.split("\t")[0] == "A" for line in added if line), (
        "migration-added.txt must contain only A-status entries"
    )
    env = _read("diffs/env-var-added.txt").strip().splitlines()
    assert any(line.startswith("M\t.env.example") for line in env), (
        "env-var-added.txt must include a modified .env.example"
    )
    modified = _read("diffs/migration-modified.txt").strip().splitlines()
    assert any(line.startswith("M\tsupabase/migrations/") for line in modified), (
        "migration-modified.txt must include a modified migration file"
    )


@pytest.mark.parametrize(
    "fixture,required",
    [
        ("expected-outputs/post-automation-m1.md", ["### M1 migrations", "[evidence pending]"]),
        ("expected-outputs/post-automation-m2.md", ["### M2 env vars", "[evidence pending]"]),
    ],
)
def test_expected_output_snippets_have_class_heading_and_placeholder(fixture, required):
    text = _read(fixture)
    for needle in required:
        assert needle in text, f"{fixture} missing expected substring: {needle!r}"
```

**Step 2: Run the test**

Run: `pytest e2e/tests/test_manual_deploy_integration.py -v`
Expected: all tests PASS — the fixtures from Task 13 are valid-by-construction.

**Step 3: Commit**

```bash
git add e2e/tests/test_manual_deploy_integration.py
git commit -m "test: structural fixture test for manual-deploy plan layout"
```

---

## Phase 5: Eval-Surface Wiring

### ✅ Task 15: Extend eval-surface.yaml with the three new surface files

**Files:**
- Modify: `e2e/eval-surface.yaml`

**Step 1: Append new entries**

Use Edit to add three new entries at the end of the `patterns:` list:

```yaml
  - skills/writing-plans/SKILL.md
  - skills/finishing-a-development-branch/SKILL.md
  - skills/_shared/manual-deploy-artifact-catalog.md
```

**Step 2: Run existing surface-pattern test to confirm no regressions**

Run: `pytest e2e/tests/test_eval_surface_patterns.py -v`
Expected: all patterns — including the 3 new — PASS `test_pattern_matches_at_least_one_file`.

**Step 3: Commit**

```bash
git add e2e/eval-surface.yaml
git commit -m "test: add manual-deploy skill files to eval surface"
```

---

### ✅ Task 16: Extend trigger-map.yaml with manual-deploy scenario routing

**Files:**
- Modify: `e2e/trigger-map.yaml`

**Step 1: Append new triggers**

Use Edit to append to `triggers:`:

```yaml
  - paths:
      - skills/writing-plans/SKILL.md
      - skills/_shared/manual-deploy-artifact-catalog.md
    scenarios:
      - scenarios/manual-deploy/plan-scan-emits-post-automation.yaml
      - scenarios/manual-deploy/env-var-gate-medium-evidence.yaml

  - paths:
      - skills/finishing-a-development-branch/SKILL.md
      - skills/_shared/manual-deploy-artifact-catalog.md
    scenarios:
      - scenarios/manual-deploy/finish-gate-blocks-missing-evidence.yaml
      - scenarios/manual-deploy/exemption-exempts-matching-files.yaml
```

Note: `manual-deploy-artifact-catalog.md` appears under two triggers because changes to the catalog affect both scan-time and gate-time behavior.

**Step 2: Do NOT run trigger-map tests yet** — the scenario files don't exist; `test_scenario_resolves_relative_to_e2e` would fail. Proceed to Task 17.

**Step 3: Commit**

```bash
git add e2e/trigger-map.yaml
git commit -m "test: route manual-deploy triggers to new scenarios"
```

---

### ✅ Task 17: Create scenario (a) — plan scan emits Post-Automation entry

**Files:**
- Create: `e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml`

**Step 1: Create the scenario directory and file**

Write `e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml`:

```yaml
# e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml
# Scenario (a) from design doc §4e: writing-plans Manual Deploy Artifact Scan
# injects a Post-Automation entry when the plan references a supabase migration.

description: "Manual-deploy: writing-plans scan injects Post-Automation entry for M1 migration"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 4000

prompts:
  - |
    {{system_context}}

    You are executing the "Manual Deploy Artifact Scan" step of the writing-plans skill on the following plan. Apply the step as specified in the skill file. Output ONLY the updated plan (the full file contents), no commentary.

    ---PLAN---
    {{plan}}
    ---END PLAN---

defaultTest:
  assert:
    - type: contains
      value: "## Manual Steps (Post-Automation)"
    - type: contains
      value: "### M1 migrations"
    - type: contains
      value: "supabase/migrations/022_add_tos_version.sql"
    - type: contains
      value: "To exempt a file from the manual-deploy gate"
    - type: regex
      value: "### M1 migrations[\\s\\S]{0,500}supabase/migrations/022_add_tos_version\\.sql"

tests:
  - description: "scan emits Post-Automation entry for a new migration"
    vars:
      system_context: file://../../../skills/writing-plans/SKILL.md
      plan: file://../../fixtures/manual-deploy/plans/active-plan-before-scan.md
```

**Step 2: Run the trigger-map test to confirm the scenario resolves**

Run: `pytest e2e/tests/test_trigger_map_paths.py::test_scenario_resolves_relative_to_e2e -v -k "plan-scan-emits-post-automation"`
Expected: the test for `scenarios/manual-deploy/plan-scan-emits-post-automation.yaml` PASSES.

**Step 3: Commit**

```bash
git add e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml
git commit -m "test: add eval scenario (a) plan-scan-emits-post-automation"
```

---

### ✅ Task 18: Create scenario (b) — finish-time gate blocks when evidence missing

**Files:**
- Create: `e2e/scenarios/manual-deploy/finish-gate-blocks-missing-evidence.yaml`

**Step 1: Create the scenario file**

Write `e2e/scenarios/manual-deploy/finish-gate-blocks-missing-evidence.yaml`:

```yaml
# e2e/scenarios/manual-deploy/finish-gate-blocks-missing-evidence.yaml
# Scenario (b) from design doc §4e: Step 0.5 emits the hard-gate prompt when
# a catalog-matched file is in the diff but the plan has no pasted evidence.

description: "Manual-deploy: Step 0.5 hard-gates when evidence is missing"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 3000

prompts:
  - |
    {{system_context}}

    You are executing Step 0.5 of finishing-a-development-branch. The branch diff is below, and the plan is below. Apply the gate as specified in the skill. If evidence is missing, output the hard-gate prompt to the user (do NOT fabricate evidence).

    ---DIFF---
    {{diff}}
    ---END DIFF---

    ---PLAN---
    {{plan}}
    ---END PLAN---

defaultTest:
  assert:
    - type: contains
      value: "Branch introduces"
    - type: contains
      value: "requiring manual production action"
    - type: contains
      value: "supabase/migrations/022_add_tos_version.sql"
    - type: contains
      value: "RECOMMENDED"

tests:
  - description: "gate emits hard-prompt with migration file listed"
    vars:
      system_context: file://../../../skills/finishing-a-development-branch/SKILL.md
      diff: file://../../fixtures/manual-deploy/diffs/migration-added.txt
      plan: file://../../fixtures/manual-deploy/plans/active-plan-after-scan.md
```

**Step 2: Run the trigger-map scenario-resolution test**

Run: `pytest e2e/tests/test_trigger_map_paths.py -v -k "finish-gate-blocks"`
Expected: scenario resolves and PASSES.

**Step 3: Commit**

```bash
git add e2e/scenarios/manual-deploy/finish-gate-blocks-missing-evidence.yaml
git commit -m "test: add eval scenario (b) finish-gate-blocks-missing-evidence"
```

---

### ✅ Task 19: Create scenario (c) — exemption declaration exempts matching files

**Files:**
- Create: `e2e/scenarios/manual-deploy/exemption-exempts-matching-files.yaml`

**Step 1: Create the scenario file**

Write `e2e/scenarios/manual-deploy/exemption-exempts-matching-files.yaml`:

```yaml
# e2e/scenarios/manual-deploy/exemption-exempts-matching-files.yaml
# Scenario (c) from design doc §4e: a plan declaring a `### Non-prod artifacts`
# exemption does NOT hit the hard-gate prompt for the exempt file.

description: "Manual-deploy: exemption declaration bypasses the gate for seed migrations"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 2000

prompts:
  - |
    {{system_context}}

    You are executing Step 0.5 of finishing-a-development-branch. The diff below includes a seed migration. The plan declares it exempt. Apply the gate. Output the gate result (either the hard-gate prompt or the "gate passed" message).

    ---DIFF---
    A	supabase/migrations/seed/023_test_data.sql
    ---END DIFF---

    ---PLAN---
    {{plan}}
    ---END PLAN---

defaultTest:
  assert:
    - type: not-contains
      value: "Branch introduces 1 supabase"
    - type: not-contains
      value: "requiring manual production action"
    - type: contains
      value: "Manual-deploy gate passed"

tests:
  - description: "seed-migration exemption bypasses gate prompt"
    vars:
      system_context: file://../../../skills/finishing-a-development-branch/SKILL.md
      plan: file://../../fixtures/manual-deploy/plans/plan-with-exemption.md
```

**Step 2: Run the trigger-map scenario-resolution test**

Run: `pytest e2e/tests/test_trigger_map_paths.py -v -k "exemption-exempts"`
Expected: scenario resolves and PASSES.

**Step 3: Commit**

```bash
git add e2e/scenarios/manual-deploy/exemption-exempts-matching-files.yaml
git commit -m "test: add eval scenario (c) exemption-exempts-matching-files"
```

---

### ✅ Task 20: Create scenario (d) — env-var artifact class enforces medium-tier evidence

**Files:**
- Create: `e2e/scenarios/manual-deploy/env-var-gate-medium-evidence.yaml`
- Create: `e2e/fixtures/manual-deploy/plans/plan-with-env-var.md`

**Step 1: Create the supporting plan fixture**

Write `e2e/fixtures/manual-deploy/plans/plan-with-env-var.md`:

```markdown
# Fixture Plan: Add FOO_API_KEY Config

> Fixture — env-var artifact class test plan.

### Task 1: Add env-var

**Files:**
- Modify: `.env.example`
- Modify: `src/lib/config.ts`

---

## Manual Steps (Post-Automation)

### M2 env vars

- `.env.example` — [evidence pending]
  - variable: `FOO_API_KEY`
```

**Step 2: Create the scenario file**

Write `e2e/scenarios/manual-deploy/env-var-gate-medium-evidence.yaml`:

```yaml
# e2e/scenarios/manual-deploy/env-var-gate-medium-evidence.yaml
# Scenario (d) from design doc §4e: the env-var artifact class (M2) requires
# variable name + hosting-provider dashboard URL — name alone is insufficient.

description: "Manual-deploy: M2 env-var evidence requires variable name AND dashboard URL"

providers:
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0
      max_tokens: 3000

prompts:
  - |
    {{system_context}}

    You are executing Step 0.5 of finishing-a-development-branch. The branch modifies .env.example to add FOO_API_KEY. The plan's M2 section has no pasted evidence. Apply the gate and emit the hard-gate prompt.

    ---DIFF---
    {{diff}}
    ---END DIFF---

    ---PLAN---
    {{plan}}
    ---END PLAN---

defaultTest:
  assert:
    - type: contains
      value: "FOO_API_KEY"
    - type: regex
      value: "vercel\\.com|netlify\\.com|fly\\.io"
    - type: contains
      value: "dashboard"

tests:
  - description: "M2 gate prompt names the variable and includes a dashboard URL"
    vars:
      system_context: file://../../../skills/finishing-a-development-branch/SKILL.md
      diff: file://../../fixtures/manual-deploy/diffs/env-var-added.txt
      plan: file://../../fixtures/manual-deploy/plans/plan-with-env-var.md
```

**Step 3: Run the trigger-map scenario-resolution test**

Run: `pytest e2e/tests/test_trigger_map_paths.py -v -k "env-var-gate"`
Expected: scenario resolves and PASSES.

**Step 4: Commit**

```bash
git add e2e/scenarios/manual-deploy/env-var-gate-medium-evidence.yaml e2e/fixtures/manual-deploy/plans/plan-with-env-var.md
git commit -m "test: add eval scenario (d) env-var-gate-medium-evidence"
```

---

### ✅ Task 21: Verify eval wiring — trigger-map test suite + promptfoo smoke-load
> NOTE: Verification surfaced that `promptfooconfig.yaml` was missing registrations for the 4 new manual-deploy scenarios (caught by `test_trigger_map_scenarios.py`). Added the four `file://scenarios/manual-deploy/*.yaml` entries to the master config. All 96 trigger-map tests pass; `promptfoo validate` confirms all 4 scenario configs load.

**Files:** (no edits)

**Step 1: Run the full trigger-map suite**

Run: `pytest e2e/tests/test_trigger_map_paths.py -v`
Expected: all entries resolve; all paths exist on disk; the 4 new scenario files PASS `test_scenario_resolves_relative_to_e2e` and the 3 new surface-mapped paths (`skills/writing-plans/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`, `skills/_shared/manual-deploy-artifact-catalog.md`) PASS `test_trigger_path_matches_surface_pattern`.

If any test fails, fix the source of truth (trigger-map.yaml or eval-surface.yaml) before continuing.

**Step 2: Promptfoo file-loading smoke test**

The new scenarios are the first in this codebase to use `file://` vars pointing up multiple directory levels to reference skill files at `../../../skills/...`. Existing scenarios only use `file://../../fixtures/...`. Confirm promptfoo resolves the relative paths correctly BEFORE running a real eval (which would cost tokens).

Run: `promptfoo eval -c e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml --no-cache --max-concurrency 1 --dry-run` (if `--dry-run` is supported) OR `promptfoo eval -c e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml --no-cache --max-concurrency 1 --filter-pattern 'nonexistent'` to force a load-only pass.

Expected: promptfoo loads the config and file:// references without error. If `--dry-run` is not supported in the installed version, instead run `promptfoo validate -c e2e/scenarios/manual-deploy/plan-scan-emits-post-automation.yaml`. Any "ENOENT" or "cannot resolve" error means the relative path depth is wrong — fix before proceeding.

**Fallback if `promptfoo` is not installed locally:** note this gap in the task-completion message and proceed. The trigger-map pytest covers disk-path resolution; promptfoo's `file://` loader is an additional check that CI would surface.

**Step 3: No commit (verification only).**

---

## Phase 6: Documentation, Version Bump, Final Verification

### ✅ Task 22: Update README and bump plugin version

**Files:**
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read `README.md` to locate the changelog / version reference region**

Use Read on the first 80 lines of `README.md` and find the section that lists feature highlights or the skill reference table. Locate where to add a one-line entry for the new manual-deploy catalog.

**Step 2: Add README entry**

Using Edit, add a note about the new catalog and its consumer skills to the appropriate section. A minimal form:

```markdown
- **Manual-deploy artifact catalog** (`skills/_shared/manual-deploy-artifact-catalog.md`): detects files whose creation requires a manual production step (v1: Supabase migrations, env-var additions). Consumed by `writing-plans` (auto-populates the plan's Post-Automation section) and `finishing-a-development-branch` (Step 0.5 hard-gates merge on missing evidence). See the design doc at `docs/plans/2026-04-20-manual-deploy-artifacts-rca-design.md`.
```

**Step 3: Bump the plugin version**

Use Read on `.claude-plugin/plugin.json` — the current `"version"` is `"0.25.0"`. Bump the minor version by one to `"0.26.0"`. Use Edit to make the change.

Do the same in `.claude-plugin/marketplace.json` — the two version strings MUST match per `CLAUDE.md`'s version rule.

**Step 4: Verify versions match**

Run the Grep tool for `"version"` on both files. Both must print the same version string.

**Step 5: Commit**

```bash
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "docs: note manual-deploy catalog in README and bump plugin version"
```

---

### ✅ Task 23: Run the full test suite and confirm green

**Files:** (no edits)

**Step 1: Run the full pytest suite**

Run: `pytest e2e/tests/ -v`
Expected:
- `test_manual_deploy_catalog.py` — all parametrized tests PASS for M1 and M2.
- `test_skill_cross_references.py` — all 6 parametrized tests PASS.
- `test_manual_deploy_integration.py` — all structural fixture tests PASS.
- `test_eval_surface_patterns.py` — every surface pattern (including the 3 new) matches at least one file.
- `test_trigger_map_paths.py` — every path and scenario resolves.
- All previously passing tests continue to pass.

**Step 2: Report findings**

If any test fails, DO NOT commit. Diagnose and fix the underlying issue in the earlier task's file, then re-run.

**Step 3: Final commit (skill changelog)**

If all tests pass, produce a final integration commit:

```bash
git commit --allow-empty -m "chore: manual-deploy artifacts feature complete (v1: migrations + env vars)"
```

Use `--allow-empty` only here (this is a marker commit for the feature boundary). Do not use `--allow-empty` in other commits; all previous tasks commit real changes.

---

## Eval Scenarios

Four promptfoo scenarios live under `e2e/scenarios/manual-deploy/`. They cover the four behavioral cases from the design doc §4e:

| # | Scenario file | Surface under test |
|---|----|----|
| a | `plan-scan-emits-post-automation.yaml` | `writing-plans/SKILL.md` scan step emits Post-Automation entries |
| b | `finish-gate-blocks-missing-evidence.yaml` | `finishing-a-development-branch/SKILL.md` Step 0.5 hard-gate prompt |
| c | `exemption-exempts-matching-files.yaml` | Exemption declaration bypasses the gate |
| d | `env-var-gate-medium-evidence.yaml` | M2 env-var evidence requires name + dashboard URL |

Assertions use `contains` / `regex` / `not-contains` for structural fidelity (not LLM-rubric judgment, which is harder to make deterministic).

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|-------------------------|
| 1 | Phase ordering | Catalog → writing-plans → finishing → fixtures → eval wiring → docs | Fixtures first (rejected: catalog must exist to validate); eval wiring before skill edits (rejected: trigger-map tests would fail) |
| 2 | TDD sequence for catalog | Write failing pytest before adding entries | Write catalog first, tests later (rejected: design-doc-specified TDD discipline) |
| 3 | Idempotency testing | Structural fixture test (no LLM) + eval scenario covers behavioral idempotency | Pure-Python oracle implementing scan logic (rejected: duplicates LLM work; heavyweight) |
| 4 | Cross-reference guard | Literal-string pytest covering 3 strings per side | Single-string check (rejected: QA N3 finding requires bidirectional guard); hash-based check (rejected: over-engineered) |
| 5 | Exemption HTML comment location | Injected by writing-plans ABOVE the Post-Automation heading | Inside the section (rejected: discoverability — users see the comment before the section) |
| 6 | Evidence validation strictness | Per-class template regex from catalog's `evidence.template:` field | Hard-coded regex in the skill (rejected: violates catalog-as-source-of-truth) |
| 7 | Ledger format | Plain text, append-only, hash + date + branch + project-ref | YAML/JSON (rejected: append-safety matters more than structure; one-line-per-entry reads well with `tail`) |
| 8 | Scenario assertions | `contains` / `regex` / `not-contains` (structural) | `llm-rubric` (rejected: non-deterministic; hard-gate strings are the contract) |
| 9 | No Prerequisites other than `pip install` | Single pip install step only | Listing every fixture file path (rejected: Task 13 creates them; not a manual step) |
| 10 | Version bump | Minor bump (0.x.0 → 0.x+1.0) | Patch bump (rejected: feature-level change, not a bug fix); major bump (rejected: pre-1.0 project convention) |
| 11 | Task 23 marker commit | `--allow-empty` final commit as feature boundary | No marker (rejected: nice to have a clear `git log` boundary for the feature) |
| 12 | Skill-file edits without unit tests | Rely on eval scenarios + cross-reference pytest | Add markdown-lint tests (rejected: no existing lint infra; overkill for prose files) |
| 13 | `file://` var resolution in promptfoo | Untested in this codebase before this plan; Task 21 adds a smoke-load step | Trust the docs (rejected: the existing scenarios all use inline or `file://../../fixtures/...` — none reach up to `skills/`) |
| 14 | Ledger gitignore guard | Runtime `git check-ignore` check with warning-not-block | Pre-flight at plan-write time (rejected: plan-write runs in plugin repo; the target project state is unknown then) |

### Appendix: Decision Details

#### Decision 1: Phase ordering

**Chose:** Catalog → writing-plans → finishing → fixtures → eval wiring → docs.

**Why:** Later phases depend on earlier phases. The catalog-integrity pytest in Phase 1 requires the catalog file to exist; the writing-plans scan step references the catalog by path; the finishing Step 0.5 references both the catalog and the plan-section layout that writing-plans is responsible for producing. The cross-reference CI check in Phase 3 fails until Phase 3's Step 0.5 addition (TDD sequence). Eval wiring (Phase 5) depends on Phase 4 fixtures resolving from disk. Deferring README/version bump to last keeps the plugin version stable until the feature is proven.

**Alternatives rejected:**
- Fixtures first — the fixtures' shape is determined by the catalog's schema (especially M1's evidence template), so the catalog must exist first.
- Eval wiring before skill edits — the trigger-map test `test_scenario_resolves_relative_to_e2e` and `test_trigger_path_matches_surface_pattern` would fail on a half-wired configuration.

#### Decision 3: Idempotency testing

**Chose:** Structural fixture test in `test_manual_deploy_integration.py` plus eval scenarios (especially (a) re-run against an already-scanned plan).

**Why:** True idempotency of a markdown-mutating skill step requires either (1) running the LLM twice and diffing outputs or (2) implementing the mutation logic in pure Python and testing the property. Option (2) duplicates scan logic in Python just to test it; the Python version then becomes its own source of truth and can drift from the skill. Option (1) is the eval scenario. Phase 4's structural test verifies the post-scan fixture has the expected shape — the contract the scan step must satisfy. Combined with eval scenario (a), which runs the actual LLM against the before-scan fixture, the property is covered without duplicated logic.

**Alternatives rejected:**
- Pure-Python scan oracle — would duplicate the skill's logic and create drift risk.
- Shell test that invokes `claude -p` twice — slow, expensive, and non-deterministic for CI.

#### Decision 4: Cross-reference guard

**Chose:** Literal-string pytest with 3 strings per side (total 6 parametrized cases).

**Why:** The QA N3 finding in the design doc explicitly calls out that a rename of either file breaks the bidirectional link silently. A pytest is the cheapest CI-level guard. Three strings per side gives enough specificity to catch partial renames (e.g., "Step 0.5" → "Step 0.6" while keeping "finishing-a-development-branch" unchanged).

**Alternatives rejected:**
- Single-string check — brittle; fails to catch partial renames.
- Hash-based check — would require re-computing expected hashes on every edit, defeating the low-overhead guard property.

#### Decision 6: Evidence validation strictness

**Chose:** Per-class template regex loaded from the catalog's `evidence.template:` field.

**Why:** The catalog is the single source of truth for detection and validation. Hard-coding regexes inside the skill would duplicate that contract and create drift risk when M3+ entries arrive. The skill instructions say "use the catalog's `evidence.template:` regex" — this couples the skill's behavior to the catalog without re-implementation.

**Alternatives rejected:**
- Hard-coded regex in the skill — two places to update for every catalog change; violates DRY.

#### Decision 13: `file://` var resolution in promptfoo

**Chose:** Add a `promptfoo validate` / `--dry-run` smoke-load step in Task 21 before trusting the new scenarios.

**Why:** Existing scenarios in `e2e/scenarios/` use `file://` references that reach into `advisors/` and `e2e/fixtures/` — but none reach up to primary skill files under `skills/`. The new scenarios are the first to load `skills/writing-plans/SKILL.md` and `skills/finishing-a-development-branch/SKILL.md` as prompt context. The relative path depth (`../../../skills/...`) is promptfoo's responsibility to resolve, but its behavior with that depth is unvalidated in this codebase. A disk-path resolution check alone (the trigger-map pytest) does not confirm promptfoo loads the file — it only confirms the file exists. The smoke-load step catches path-depth off-by-one bugs with a cheap no-eval call.

**Alternatives rejected:**
- Trust the docs — the risk is cheap to mitigate with one `promptfoo validate` call.
- Run a full eval on one scenario — costs tokens for a path-resolution check; the validate/dry-run variant is free.

#### Decision 14: Ledger gitignore guard timing (runtime, not plan-write-time)

**Chose:** Runtime `git check-ignore` in Step 0.5, warning-not-block.

**Why:** The ledger path `docs/plans/.manual-deploy-ledger.md` is only written during Step 0.5 execution in the USER's project, not the plugin repo. At plan-write time (when writing-plans runs), the target project's `.gitignore` state is unknown. Checking at Step 0.5 time is the earliest moment both pieces of information are available. The guard is warning-not-block because the ledger is an optimization (it only accelerates cross-branch re-gating); a gitignored ledger still allows correct per-branch gating. Escalating to a hard stop would gate the user on a setup issue that is downstream of the real failure mode this plan addresses.

**Alternatives rejected:**
- Pre-flight at plan-write time — writing-plans does not know the target project's `.gitignore` state; any check would be speculative.
- Hard-block on gitignored ledger — introduces a stoppage for an optimization, not a correctness requirement.

#### Decision 7: Ledger format

**Chose:** Plain text, append-only, one line per entry.

**Why:** The failure mode a ledger prevents is the same migration being re-gated on a different branch. Plain text lines are safest for append semantics — no YAML parser mid-write-state, no binary file to merge. `tail`, `grep`, and diff tools work out of the box. The per-line format `{hash} {date} {branch} {project-ref}` is easy to parse with `line.split()`. Concurrent writers from two Claude sessions would produce duplicate lines — harmless because step 3 of Step 0.5 does a lookup-by-content and duplicate-but-matching entries still match; deduplication can happen at read time, not write time. No file-corruption guarantee is claimed.

**Alternatives rejected:**
- YAML / JSON — append-safety requires whole-file rewrites or specialized append libraries.
- SQLite — overkill; introduces a binary file in `docs/plans/`.

---

