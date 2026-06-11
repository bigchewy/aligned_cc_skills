---
---
# Visualization Runner Extraction + `visualize-design` Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Extract the design-doc HTML visualization engine out of brainstorming's `visualization-protocol.md` into a caller-independent `skills/_shared/visualization-runner.md`, harden it against the KB-085/086 shortcut-and-skip failures, and add a standalone `/aligned:visualize-design` caller — one engine, two callers, zero duplicated procedure.

**Source Design Doc:** `docs/plans/2026-06-11-visualization-skill-design.md`

**Architecture:** Three-piece split — (1) new `skills/_shared/visualization-runner.md` owns the engine (token ladder, template copy-patch, widget injection, browser-open, mermaid gate, strip rule, nested sub-tabs, Overview-altitude gate); (2) new `skills/visualize-design/SKILL.md` is a thin standalone caller; (3) existing `skills/brainstorming/references/visualization-protocol.md` slims to a brainstorming-lifecycle wrapper that delegates to the runner. Templates, widgets, components doc, and the mermaid validator stay physically in `skills/brainstorming/`; the runner takes their paths as Configuration inputs. Four logical commits: extract (behavior-equivalent), harden KB-085/086, add the skill, optional agent dedup.

**Tech Stack:** Markdown skill/runner docs, HTML templates with inline JS tab system, pytest structural guards in `e2e/tests/`, `node` mermaid validator.

**Test command:** All structural guards are pytest. Run a single test from the repo root with:
`python3 -m pytest e2e/tests/<file>.py::<test_name> -q`
(`python` is not on PATH on this machine — always use `python3`.)

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] **Clean the working tree of the pending `widgets.html` edit.** `git status` shows `skills/brainstorming/references/widgets.html` modified but uncommitted. The autopilot creates its worktree from `main`, so this change will not carry forward unless committed. Either commit it (`git add skills/brainstorming/references/widgets.html && git commit -m "chore: land pending widgets.html edit"`) or `git stash` it before execution begins. (Design "Pre-commit-1 housekeeping". The `e2e/trigger-map.yaml` grep for a protocol path reference is already done — confirmed absent — so no action there.)

---

## Task Ordering / File-Conflict Notes

These tasks share files; execute in numeric order. The dependencies are:

- **`skills/_shared/visualization-runner.md`** is created in Task 1 and edited again in Tasks 7, 9, 10. Sequential.
- **`e2e/tests/test_shared_runners.py`** is appended in Tasks 1, 2, 7, 9, 10. Sequential.
- **`e2e/tests/test_brainstorming_files.py`** is edited/appended in Tasks 3, 5, 6, 8, 11. Sequential.
- **`skills/brainstorming/references/visualization-protocol.md`** is slimmed in Task 3, then edited in Task 8. Task 3 before Task 8.
- **`e2e/tests/test_skill_cross_references.py`** (`REQUIRED_CROSS_REFS`) is appended in Tasks 4, 13, 15. Sequential.
- **Task 1 before Task 5:** Task 5's `shared-rules.md` pointer must point at the runner created in Task 1.
- **`e2e/tests/test_visualize_design_files.py`** is created in Task 12 and appended in Task 14.

---

## ✅ Task 1: Create the visualization-runner engine

**Files:**
- Create: `skills/_shared/visualization-runner.md`
- Test: `e2e/tests/test_shared_runners.py` (new `test_visualization_runner_well_formed`)

This commit is **behavior-equivalent** — the runner holds the *current* engine procedure (extracted from `visualization-protocol.md`), not the KB-085/086 hardening (that is Tasks 7–9). The anti-shortcut contract, the unconditional browser-open, and the Overview gate are added later.

**Step 1: Write the failing test**

Append to `e2e/tests/test_shared_runners.py`:

```python
def test_visualization_runner_well_formed():
    text = read("skills/_shared/visualization-runner.md")
    # House rule: _shared/ runners carry no YAML frontmatter (mirrors framework-runner.md)
    assert not text.lstrip().startswith("---"), "runner must not have YAML frontmatter"
    # House-style sections, mirroring framework-runner.md
    assert "## Configuration" in text
    assert "## Configuration Validation (fail-closed)" in text
    assert "## Avoid These Mistakes" in text
    # Engine content relocated from visualization-protocol.md
    assert "design-principles.md" in text, "token-resolution ladder must live in the runner"
    assert "the file copy is the contract" in text, "template copy-patch contract must be present"
    assert "LIVE-REFRESH-START" in text, "strip-script rule (canonical) must live in the runner"
    assert "sub-tab" in text.lower(), "nested sub-tabs rule must live in the runner"
    assert "validate-mermaid.mjs" in text, "mermaid validation gate must live in the runner"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_well_formed -q`
Expected: FAIL — `FileNotFoundError` (runner does not exist yet).

**Step 3: Create the runner**

Create `skills/_shared/visualization-runner.md` with NO YAML frontmatter (lead with `# Visualization Runner`, like `skills/_shared/framework-runner.md:1`). Structure it in the framework-runner house style. The body is the engine **relocated** from `skills/brainstorming/references/visualization-protocol.md` — relocate the existing prose; do not invent new procedure. Convert every `{base-directory}/references/...` path into a Configuration input (the caller passes absolute paths; shared files never self-resolve, per `skills/_shared/resolve-skill-path.md`).

Author these sections:

````markdown
# Visualization Runner

Shared engine for producing the on-brand, tabbed, Mermaid-validated HTML artifact. Invoked by `skills/brainstorming/references/visualization-protocol.md` (brainstorming lifecycle wrapper) and `skills/visualize-design/SKILL.md` (standalone caller). The caller owns *when* to render and *where* the final artifact lands; this runner owns *how* a single artifact is produced.

## Configuration

The calling skill passes these inputs (all absolute paths — the runner never self-resolves):

| Input | Meaning |
|---|---|
| `{template-path}` | The HTML template to copy verbatim |
| `{widgets-path}` | `widgets.html` (widget CSS/JS/HTML blocks) |
| `{components-path}` | `brainstorm-components.md` (token contract + component classes) |
| `{source-content}` | Validated sections or document body to render |
| `{title}` / `{subtitle}` / `{context}` | Header values patched into the template |
| `{output-path}` | Final committed artifact location |
| `{live-session}` | `yes`/`no` — self-refreshing `/tmp` artifact vs one-shot |
| `{project-root}` | For the token-resolution ladder |
| `{validate-mermaid-script}` | Absolute path to `validate-mermaid.mjs` |

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** with a named error if any check fails — do not improvise:
- Every path input (`{template-path}`, `{widgets-path}`, `{components-path}`, `{validate-mermaid-script}`) must exist.
- `{output-path}`'s parent directory must be writable (create it if missing).
- `{live-session}` must be exactly `yes` or `no`.
- A missing or unresolvable input halts the runner: "Visualization runner cannot proceed: `<input>` is missing/unresolvable."

## Step 1: Read the brand-token contract

[Relocate visualization-protocol.md Live-phase step 1 — read `{components-path}` for the `:root` token rules and component-class reference.]

## Step 2: Resolve the project's design tokens

[Relocate visualization-protocol.md Live-phase step 2 verbatim — the lookup ladder (a) `{project-root}/docs/design/design-principles.md` → (b) monorepo `apps/*` / `packages/*` glob → (c) `~/.claude/docs/design/design-principles.md`, the placeholder heuristic (<500 bytes / "This file is a placeholder" / "Run `/aligned:create-design-principles`") and its user warning, and the halt-and-ask trigger.]

## Step 3: Copy and patch the template

[Relocate Live-phase step 3 — Write `{template-path}` contents verbatim to the working artifact; patch `{title}`/`{subtitle}`/`{context}`; populate the `:root` block from Step 2 tokens; never touch `var(--color-*)`/`var(--font-*)` references; append `{source-content}`. End with the contract line: **"Do not rewrite the template from memory — the file copy is the contract."**]

## Step 4: Open the artifact in the browser

[Relocate Live-phase step 4 — platform-aware `open ... || xdg-open ...` (separate Bash call, no `&&` chaining). If both fail (headless), log a warning and continue.]

## Step 5: Inject interactive widgets (conditional)

[Relocate Live-phase step 6 — only if the content has a Decision Log (>=1 entry) or Open Questions (>=1 entry). Read `{widgets-path}`; inject WIDGETS-CSS into `<head>`, WIDGETS-SCRIPT immediately before `</body>` and OUTSIDE the `<!-- LIVE-REFRESH-START -->...<!-- LIVE-REFRESH-END -->` delimiters, WIDGET-HTML blocks into their owning sections (flat <10 entries, categorized >=10). End with "Do not rewrite the widget code from memory — the file copy is the contract."]

## Step 6: Validate Mermaid (hard gate)

[Relocate the mermaid check from the protocol's Pre-critique snapshot step 2.5 — run `node {validate-mermaid-script} {output-path}`; exit 0 required to proceed; exit 1 prints the offending block and must be fixed and re-run. Do not proceed past this gate until exit is 0.]

## Stripping the live-refresh script

[Relocate the CANONICAL strip-script rule here from `skills/brainstorming/references/shared-rules.md` § "Stripping the live-refresh script" — verify both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` exist; if either missing, STOP and flag; if both present, remove the block inclusive of delimiters; the committed artifact must not auto-refresh. Include the **Widget survival** paragraph (widget tables + WIDGETS-SCRIPT block must survive the strip).]

## Nested sub-tabs

[Relocate the Nested sub-tabs rule verbatim from visualization-protocol.md § "Nested sub-tabs".]

## Avoid These Mistakes

- **Rewriting the template or widgets from memory** — always copy the file and patch it.
- **Skipping the browser-open or mermaid gate** — both are unconditional numbered steps.
- **Injecting the widget script inside the LIVE-REFRESH delimiters** — it must land outside them or the strip rule removes it.
````

> Behavior note: This is a content relocation. The runner's per-artifact engine plus the wrapper's lifecycle (Task 3) must together reproduce today's `visualization-protocol.md` behavior exactly.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_well_formed -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/_shared/visualization-runner.md e2e/tests/test_shared_runners.py
git commit -m "feat(viz): extract visualization engine into _shared/visualization-runner.md"
```

---

## ✅ Task 2: Register the runner in the eval surface

**Files:**
- Modify: `e2e/eval-surface.yaml` (the `patterns:` list, alongside `framework-runner.md` / `advisor-runner.md`)
- Test: `e2e/tests/test_shared_runners.py` (new `test_visualization_runner_is_in_eval_surface`)

The runner is a new LLM behavior surface. No generic "every `_shared/` runner" enforcement exists, so this assertion must be written by hand (mirroring `test_framework_runner_is_in_eval_surface` at `test_shared_runners.py:37-41`).

**Step 1: Write the failing test**

Append to `e2e/tests/test_shared_runners.py`:

```python
def test_visualization_runner_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/visualization-runner.md" in text, (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_is_in_eval_surface -q`
Expected: FAIL — assertion error (path not yet in eval-surface.yaml).

**Step 3: Add the runner to the eval surface**

In `e2e/eval-surface.yaml`, under the `patterns:` list where `framework-runner.md` and `advisor-runner.md` are listed, add:

```yaml
  - skills/_shared/visualization-runner.md
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_is_in_eval_surface -q`
Expected: PASS

**Step 5: Commit**

```bash
git add e2e/eval-surface.yaml e2e/tests/test_shared_runners.py
git commit -m "test(viz): add visualization-runner to eval surface"
```

---

## ✅ Task 3: Slim the protocol to a brainstorming wrapper that delegates to the runner

**Files:**
- Modify: `skills/brainstorming/references/visualization-protocol.md` (replace the engine steps with lifecycle + delegation)
- Test: `e2e/tests/test_brainstorming_files.py` (new `test_visualization_protocol_delegates_to_runner`)

The protocol keeps the brainstorming-specific lifecycle (live-update-per-validated-section loop, pre-critique snapshot to `docs/mockups/{session-name}.html`, the `**Mockups:**` header field, post-critique regeneration) and delegates the engine to the runner. The delegation MUST be the first actionable line after the Inputs/Configuration block — pointer-style steps buried in prose are the documented KB-085 skip class.

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_visualization_protocol_delegates_to_runner():
    text = read("skills/brainstorming/references/visualization-protocol.md")
    # Still readable at its e2e-pinned path, still no YAML frontmatter
    assert not text.lstrip().startswith("---")
    # Delegates the engine to the shared runner
    assert "skills/_shared/visualization-runner.md" in text, "wrapper must delegate to the runner"
    # Brainstorming-specific lifecycle stays in the wrapper
    assert "docs/mockups/" in text, "pre-critique snapshot path must stay in the wrapper"
    assert "**Mockups:**" in text, "Mockups header field is brainstorming-specific"
    # Delegation appears early — within the first ~40 lines, not buried in prose
    head = "\n".join(text.splitlines()[:40])
    assert "skills/_shared/visualization-runner.md" in head, "delegation must be the first actionable line, not buried"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_visualization_protocol_delegates_to_runner -q`
Expected: FAIL — `skills/_shared/visualization-runner.md` not referenced in the protocol yet.

**Step 3: Slim the protocol**

Rewrite `skills/brainstorming/references/visualization-protocol.md` so it:
1. Keeps the leading HTML-comment banner (no YAML frontmatter) and `# Visualization Protocol` heading.
2. Keeps a short **Inputs / Configuration** block resolving the runner's Configuration inputs to **absolute** values (template = `{base-directory}/references/templates/software-template.html` resolved absolute, widgets = `{base-directory}/references/widgets.html`, components = `{base-directory}/references/brainstorm-components.md`, validate-mermaid script = `{plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs`, `{session-name}` derivation, `{output-path}` = `docs/mockups/{session-name}.html`, `{live-session}` = `yes`).
3. **First actionable line after the block:** "Follow `skills/_shared/visualization-runner.md` end-to-end with the Configuration above."
4. Keeps ONLY the brainstorming lifecycle that the runner does not own: the live-update-per-validated-section loop (call the runner as each section validates), the **Pre-critique snapshot** (copy the live artifact to `docs/mockups/{session-name}.html`; add `**Mockups:** docs/mockups/{session-name}.html` to the design doc header), and **Post-critique regeneration** (re-run the runner against the corrected design; skip if unchanged).
5. Removes the now-relocated engine prose (token ladder body, template copy-patch body, widget-injection body, the standalone Nested sub-tabs section) — these live in the runner now and are reached via the delegation.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_visualization_protocol_delegates_to_runner -q`
Expected: PASS

**Step 5: Verify no brainstorming regression in the existing protocol guards**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py -q`
Expected: PASS (the pinned-path test `test_references_describe_four_modes_post_collapse` still finds the protocol at its path and the mode language is intact).

**Step 6: Commit**

```bash
git add skills/brainstorming/references/visualization-protocol.md e2e/tests/test_brainstorming_files.py
git commit -m "refactor(viz): slim visualization-protocol to a runner-delegating wrapper"
```

---

## ✅ Task 4: Guard the wrapper→runner cross-reference

**Files:**
- Modify: `e2e/tests/test_skill_cross_references.py` (`REQUIRED_CROSS_REFS`)

The protocol now hard-references the runner path. Add a guard tuple so the link cannot rot silently. The reference already exists (Task 3), so this is a retroactive guard — write the tuple, then verify the parametrized check passes.

**Step 1: Add the guard tuple**

In `e2e/tests/test_skill_cross_references.py`, insert the tuple inside `REQUIRED_CROSS_REFS` — before the closing `]` of the list (currently at line 70; line numbers shift as tasks execute). Mirror the existing `(source_path, expected_target_substring)` tuple format:

```python
    (REPO_ROOT / "skills" / "brainstorming" / "references" / "visualization-protocol.md",
     "skills/_shared/visualization-runner.md"),
```

**Step 2: Run the parametrized check to verify it passes**

Run: `python3 -m pytest "e2e/tests/test_skill_cross_references.py::test_cross_reference_link_resolves" -q`
Expected: PASS — the protocol contains the substring and the target resolves to a real file (retroactive guard; the link was added in Task 3).

**Step 3: Commit**

```bash
git add e2e/tests/test_skill_cross_references.py
git commit -m "test(viz): guard visualization-protocol -> runner cross-reference"
```

---

## ✅ Task 5: Leave a pointer in shared-rules.md to the relocated strip rule

**Files:**
- Modify: `skills/brainstorming/references/shared-rules.md` (§ "Stripping the live-refresh script")
- Test: `e2e/tests/test_brainstorming_files.py` (new `test_shared_rules_strip_rule_points_to_runner`)

The canonical strip-script text now lives in the runner (Task 1). `shared-rules.md` keeps a one-line pointer so brainstorming's existing read still resolves (Decision 7).

> Path correction vs. design doc: `shared-rules.md` lives at `skills/brainstorming/references/shared-rules.md`, NOT `skills/_shared/shared-rules.md`. The design's Architecture bullet abbreviated the path; the Migration section's bare `shared-rules.md` is the file edited here.

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_shared_rules_strip_rule_points_to_runner():
    text = read("skills/brainstorming/references/shared-rules.md")
    # The section still exists so existing reads resolve...
    assert "## Stripping the live-refresh script" in text
    # ...but now points at the canonical text in the runner instead of restating it.
    assert "skills/_shared/visualization-runner.md" in text, "strip rule must point to the runner"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_shared_rules_strip_rule_points_to_runner -q`
Expected: FAIL — the runner path is not referenced in `shared-rules.md` yet.

**Step 3: Edit shared-rules.md**

Under `## Stripping the live-refresh script`, replace the full rule body (the verify-delimiters paragraph and the Widget-survival paragraph) with a one-line pointer:

```markdown
## Stripping the live-refresh script

The canonical strip-script rule (verify the `<!-- LIVE-REFRESH-START -->`/`<!-- LIVE-REFRESH-END -->` delimiters, remove the block, preserve the widget script) lives in `skills/_shared/visualization-runner.md` § "Stripping the live-refresh script". It applies to the software and authoring modes; research and roadmap modes skip it.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_shared_rules_strip_rule_points_to_runner -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/brainstorming/references/shared-rules.md e2e/tests/test_brainstorming_files.py
git commit -m "refactor(viz): point shared-rules strip rule at the runner"
```

---

## ✅ Task 6: Update the modes/software.md nested sub-tabs reference

**Files:**
- Modify: `skills/brainstorming/modes/software.md` (the "Nested sub-tabs rule defined in the protocol" sentence)
- Test: `e2e/tests/test_brainstorming_files.py` (new `test_software_mode_nested_subtabs_reference`)

The Nested sub-tabs rule moved from the protocol into the runner (Task 1). `software.md`'s reference must follow it. This is the one-line reference edit that scopes the "modes untouched" claim to *behavior*, not bytes (Decision 13).

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_software_mode_nested_subtabs_reference():
    text = read("skills/brainstorming/modes/software.md")
    # The rule is no longer "defined in the protocol" — it moved to the runner.
    assert "Nested sub-tabs rule defined in the protocol" not in text, (
        "stale reference: nested sub-tabs rule moved to the runner"
    )
    assert "Nested sub-tabs" in text, "the rule reference must still be present"
    assert "visualization runner" in text.lower() or "visualization-runner.md" in text, (
        "reference must point at the runner that now defines the rule"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_software_mode_nested_subtabs_reference -q`
Expected: FAIL — the file still says "Nested sub-tabs rule defined in the protocol".

**Step 3: Edit software.md**

In `skills/brainstorming/modes/software.md`, find the sentence "The Nested sub-tabs rule defined in the protocol also applies to any HTML produced by the mockup-generator dispatch..." and change it to reference the runner (the protocol delegates to it), e.g.:

```markdown
The Nested sub-tabs rule (defined in the visualization runner, applied via the protocol) also applies to any HTML produced by the mockup-generator dispatch in the "Exploring approaches" section above.
```

Leave the protocol-reading instruction earlier in that same line untouched — the mode still reads the protocol; only the nested-sub-tabs attribution changes.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_software_mode_nested_subtabs_reference -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/software.md e2e/tests/test_brainstorming_files.py
git commit -m "refactor(viz): point software mode nested-subtabs ref at the runner"
```

---

## Task 7: Add the anti-shortcut contract to the runner

**Files:**
- Modify: `skills/_shared/visualization-runner.md` (Step 3 + "Avoid These Mistakes")
- Test: `e2e/tests/test_shared_runners.py` (new `test_visualization_runner_has_anti_shortcut_contract`)

KB-085/086 primary-cause fix: name the compact-direct-write shortcut as a forbidden move so the violation is recognizable, not just discouraged.

**Step 1: Write the failing test**

Append to `e2e/tests/test_shared_runners.py`:

```python
def test_visualization_runner_has_anti_shortcut_contract():
    text = read("skills/_shared/visualization-runner.md").lower()
    assert "never hand-write" in text or "do not hand-write" in text, (
        "runner must forbid hand-writing the artifact HTML"
    )
    assert "compactly rewrite" in text, (
        "the compact-direct-write shortcut must be named as a forbidden move"
    )
    assert "even when that seems faster" in text or "even when it seems faster" in text, (
        "anti-shortcut contract must address the speed temptation"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_has_anti_shortcut_contract -q`
Expected: FAIL — anti-shortcut language not present yet.

**Step 3: Edit the runner**

In Step 3 (Copy and patch the template), add the explicit contract:

```markdown
**Anti-shortcut contract.** Copy `{template-path}` with a file-copy/Write command and patch it. NEVER hand-write or "compactly rewrite" the artifact HTML from memory, even when that seems faster. The compact-direct-write shortcut is the root cause of KB-085/086 — it bypasses the template, the widgets, the browser-open step, and the Overview gate.
```

And add to "Avoid These Mistakes":

```markdown
- **The compact-direct-write shortcut** — hand-writing tighter HTML directly instead of copying the template. Forbidden: it skips every gate below. Always copy the file.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_has_anti_shortcut_contract -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/_shared/visualization-runner.md e2e/tests/test_shared_runners.py
git commit -m "feat(viz): add anti-shortcut contract to the runner (KB-085/086)"
```

---

## Task 8: Add the anti-shortcut dispatch line to the protocol wrapper

**Files:**
- Modify: `skills/brainstorming/references/visualization-protocol.md` (the delegation line)
- Test: `e2e/tests/test_brainstorming_files.py` (new `test_protocol_dispatch_states_anti_shortcut`)

The design requires the anti-shortcut contract at the runner's first step AND each caller's dispatch text. This adds the one-liner to brainstorming's dispatch (the second caller, `visualize-design`, gets it at creation in Task 12).

**Step 1: Write the failing test**

Append to `e2e/tests/test_brainstorming_files.py`:

```python
def test_protocol_dispatch_states_anti_shortcut():
    text = read("skills/brainstorming/references/visualization-protocol.md").lower()
    assert "never hand-write" in text or "do not hand-write" in text, (
        "wrapper dispatch must restate the anti-shortcut contract"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_protocol_dispatch_states_anti_shortcut -q`
Expected: FAIL — no anti-shortcut language in the wrapper yet.

**Step 3: Edit the wrapper**

Immediately after the delegation line ("Follow `skills/_shared/visualization-runner.md`..."), add:

```markdown
> Copy the template file and patch it — NEVER hand-write or compactly rewrite the artifact HTML, even when that seems faster. See the runner's anti-shortcut contract.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_protocol_dispatch_states_anti_shortcut -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/brainstorming/references/visualization-protocol.md e2e/tests/test_brainstorming_files.py
git commit -m "feat(viz): restate anti-shortcut contract in the brainstorming wrapper"
```

---

## Task 9: Make the runner's browser-open an unconditional numbered step

**Files:**
- Modify: `skills/_shared/visualization-runner.md` (Step 4)
- Test: `e2e/tests/test_shared_runners.py` (new `test_visualization_runner_browser_open_unconditional`)

KB-085 fix: the browser-open is reliably skipped because it reads as skippable prose. Make it an explicit, unconditional numbered step.

**Step 1: Write the failing test**

Append to `e2e/tests/test_shared_runners.py`:

```python
def test_visualization_runner_browser_open_unconditional():
    text = read("skills/_shared/visualization-runner.md")
    assert "xdg-open" in text, "browser-open command must be present"
    lower = text.lower()
    assert "unconditional" in lower or "do not skip" in lower or "always open" in lower, (
        "browser-open must be marked as a mandatory, non-skippable step (KB-085)"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_browser_open_unconditional -q`
Expected: FAIL — the step exists but carries no unconditional marker.

**Step 3: Edit the runner**

Reword Step 4 (Open the artifact in the browser) so it is explicitly unconditional, e.g.:

```markdown
## Step 4: Open the artifact in the browser (unconditional — do not skip)

This step is mandatory and runs every render. Open the artifact with a platform-aware command (separate Bash call, no `&&` chaining):

`open {output-path} || xdg-open {output-path}`

Only a headless environment (both commands fail) exempts this step — log the warning and continue. There is no other condition under which the browser-open is skipped.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_browser_open_unconditional -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/_shared/visualization-runner.md e2e/tests/test_shared_runners.py
git commit -m "fix(viz): make runner browser-open an unconditional numbered step (KB-085)"
```

---

## Task 10: Add the executive-overview verify gate to the runner

**Files:**
- Modify: `skills/_shared/visualization-runner.md` (new "Executive-overview gate" section before the strip rule)
- Test: `e2e/tests/test_shared_runners.py` (new `test_visualization_runner_overview_gate`)

KB-086 fix (verify half). Two parts, honestly labeled: a mechanical, fail-closed sub-check (grep-assertable) and a semantic self-check (LLM judgment, one retry, never blocks — write anyway on second failure).

**Step 1: Write the failing test**

Append to `e2e/tests/test_shared_runners.py`:

```python
def test_visualization_runner_overview_gate():
    text = read("skills/_shared/visualization-runner.md")
    lower = text.lower()
    # Mechanical sub-check: zero mermaid blocks + zero file-path spans in the Overview panel
    assert "panel-overview" in text, "gate must reference the Overview panel"
    assert "mechanical" in lower, "gate must label the mechanical sub-check"
    assert "file-path" in lower or ".file-path" in text, "mechanical check inspects file-path spans"
    # Semantic self-check: one retry, never blocks, write anyway on second failure
    assert "semantic" in lower, "gate must label the semantic self-check"
    assert "write the artifact anyway" in lower or "write anyway" in lower, (
        "semantic check must never hold output hostage on second failure"
    )
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_overview_gate -q`
Expected: FAIL — no Overview gate in the runner yet.

**Step 3: Edit the runner**

Add a numbered gate section, placed BEFORE "Stripping the live-refresh script" (so it runs before any snapshot/commit):

```markdown
## Executive-overview gate (before any snapshot is written)

The Overview tab is the first thing a non-engineer sees. Two checks gate it.

**Mechanical sub-check (assertable, fail-closed):** the `panel-overview` panel must contain zero `<pre class="mermaid">` / `<pre class="mermaid-deferred">` blocks and zero `.file-path` spans. This is a grep with the same pass/fail contract as the mermaid gate: nonzero match → rewrite the Overview before any snapshot is written.

**Semantic self-check (not unit-testable, never blocks):** is the goal stated in the first two sentences? Is the language plain (no implementation vocabulary)? Does it fit one screen? This is an LLM judgment with no mechanical assertion — it does NOT have parity with the mermaid exit-code gate. On failure, rewrite the Overview and re-check once. **On a second failure, write the artifact anyway** and tell the user in one line which check failed and where the lever is (e.g., "Overview still leads with implementation detail — committed as-is; edit the Overview tab's `{goal}` slot to fix"). A soft semantic judgment never holds the user's output hostage; only the mechanical checks block.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_shared_runners.py::test_visualization_runner_overview_gate -q`
Expected: PASS

**Step 5: Commit**

```bash
git add skills/_shared/visualization-runner.md e2e/tests/test_shared_runners.py
git commit -m "feat(viz): add executive-overview verify gate to the runner (KB-086)"
```

---

## Task 11: Bake the Overview-tab scaffold into the five visualizing templates

**Files:**
- Modify: `skills/brainstorming/references/templates/software-template.html`
- Modify: `skills/brainstorming/references/templates/authoring-template.html`
- Modify: `skills/brainstorming/references/templates/authoring-decision-template.html`
- Modify: `skills/brainstorming/references/templates/authoring-plan-template.html`
- Modify: `skills/brainstorming/references/templates/authoring-analysis-template.html`
- Test: `e2e/tests/test_brainstorming_files.py` (rewrite the existing `test_authoring_templates_share_common_scaffolding`)

The Overview structure becomes template-guaranteed: a verbatim copy carries it and can be filled but not omitted. Scope is the **five visualizing templates** (software + four authoring variants). `roadmap-template.html` is intentionally excluded — roadmap mode does not produce the live design artifact (`shared-rules.md` § strip rule: "research and roadmap modes skip").

> Behavior change: brainstorming software/authoring artifacts now open with an Overview tab as the active panel. This is the intended KB-086 fix (overview at executive altitude), not a regression.

> Resolving the design's `panel-overview active` shorthand: `switchTab` builds panel ids as `'panel-' + tabId` (`software-template.html` ~line 629), so the Overview panel is `<div class="tab-panel active" id="panel-overview">`. The literal contiguous string `panel-overview active` cannot exist; the test asserts the two real substrings `id="panel-overview"` and `class="tab-panel active"` instead (Decision Log #5).

**Step 1: Replace the existing (currently passing) scaffolding test with a stronger failing test**

In `e2e/tests/test_brainstorming_files.py`, replace `test_authoring_templates_share_common_scaffolding` (currently iterates the 4 authoring templates and asserts only `"<script" in text`) with:

```python
def test_visualizing_templates_share_overview_scaffold():
    # All FIVE visualizing templates (software + four authoring variants) ship a baked-in
    # Overview tab so a verbatim copy carries the executive-altitude structure (KB-086).
    # roadmap-template.html is excluded — roadmap mode produces no live design artifact.
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "skills/brainstorming/references/templates"
    files = [
        "software-template.html",
        "authoring-template.html",
        "authoring-decision-template.html",
        "authoring-plan-template.html",
        "authoring-analysis-template.html",
    ]
    for name in files:
        text = (base / name).read_text()
        assert 'id="panel-overview"' in text, f"{name} missing Overview panel"
        assert 'class="tab-panel active"' in text, f"{name} Overview panel must be the active tab"
        assert "{goal}" in text, f"{name} missing {{goal}} slot"
        assert "{why-it-matters}" in text, f"{name} missing {{why-it-matters}} slot"
        assert "{outcome}" in text, f"{name} missing {{outcome}} slot"
        # Retain the live-refresh guard from the replaced test: the strip rule requires this marker
        assert "LIVE-REFRESH-START" in text, f"{name} must carry the live-refresh delimiters (strip rule precondition)"
```

**Step 2: Run new test to verify it fails — the templates lack the Overview scaffold**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_visualizing_templates_share_overview_scaffold -q`
Expected: FAIL — templates have no Overview scaffold yet (`AssertionError: ... missing Overview panel`).

**Step 3: Inject the scaffold into all five templates**

In each of the five files, replace the line `<!-- Tab bar and content panels go here -->` with:

```html
  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
    <!-- Additional tab buttons appended by the generating agent -->
  </div>

  <div class="tab-panel active" id="panel-overview">
    <div class="callout callout-note"><strong>What this is</strong>{goal}</div>
    <div class="callout callout-note"><strong>Why it matters</strong>{why-it-matters}</div>
    <div class="callout callout-note"><strong>Outcome</strong>{outcome}</div>
  </div>

  <!-- Additional tab panels appended by the generating agent -->
```

(The `callout` / `callout-note` classes already exist in every template's `<style>` block, e.g. `software-template.html:576`.)

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py::test_visualizing_templates_share_overview_scaffold -q`
Expected: PASS

**Step 5: Run the full brainstorming-files guard to confirm no regression**

Run: `python3 -m pytest e2e/tests/test_brainstorming_files.py -q`
Expected: PASS (no other test referenced the old function name; tab-system tests, if any, still pass).

**Step 6: Commit**

```bash
git add skills/brainstorming/references/templates/software-template.html skills/brainstorming/references/templates/authoring-template.html skills/brainstorming/references/templates/authoring-decision-template.html skills/brainstorming/references/templates/authoring-plan-template.html skills/brainstorming/references/templates/authoring-analysis-template.html e2e/tests/test_brainstorming_files.py
git commit -m "feat(viz): bake Overview-tab scaffold into the five visualizing templates (KB-086)"
```

---

## Task 12: Create the `visualize-design` standalone skill

**Files:**
- Create: `skills/visualize-design/SKILL.md`
- Test: `e2e/tests/test_visualize_design_files.py` (new)

Thin standalone caller. Owns source resolution, session naming, template-path resolution via plugin root, the `docs/design-visualizations/` output convention, and the anti-shortcut dispatch text. Delegates the engine to the runner. Does NOT include the critique panel or the `**Mockups:**` header field (brainstorming scaffolding, not part of a general visualizer).

**Step 1: Write the failing test**

Create `e2e/tests/test_visualize_design_files.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_visualize_design_skill_exists_and_named():
    path = REPO / "skills/visualize-design/SKILL.md"
    assert path.is_file(), "visualize-design SKILL.md must exist"
    text = path.read_text()
    assert "name: visualize-design" in text, "frontmatter name must match directory"


def test_visualize_design_delegates_to_runner():
    text = read("skills/visualize-design/SKILL.md")
    assert "skills/_shared/visualization-runner.md" in text, "must delegate to the runner"
    assert "software-template.html" in text, "must resolve the brainstorming template by path"
    assert "docs/design-visualizations/" in text, "must use the standalone output convention"


def test_visualize_design_has_fixed_no_content_question():
    text = read("skills/visualize-design/SKILL.md")
    assert "No document path was given and this conversation has no renderable content yet" in text, (
        "the bare-invocation question must use the fixed wording"
    )


def test_visualize_design_states_anti_shortcut():
    text = read("skills/visualize-design/SKILL.md").lower()
    assert "never hand-write" in text or "do not hand-write" in text, (
        "the standalone caller must restate the anti-shortcut contract"
    )


def test_visualize_design_excludes_brainstorming_scaffolding():
    text = read("skills/visualize-design/SKILL.md")
    assert "critique panel" not in text.lower(), "general visualizer excludes the critique panel"
    assert "**Mockups:**" not in text, "general visualizer excludes the Mockups header field"
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest e2e/tests/test_visualize_design_files.py -q`
Expected: FAIL — `skills/visualize-design/SKILL.md` does not exist.

**Step 3: Create the skill**

Create `skills/visualize-design/SKILL.md` with YAML frontmatter (`name` MUST equal the directory `visualize-design`):

````markdown
---
name: visualize-design
description: "Render any markdown design doc or the current conversation's validated content as an on-brand, tabbed, Mermaid-validated HTML artifact. Use when you want a standalone visualization without the brainstorming flow."
---

# Visualize Design

Standalone caller for the visualization engine. Renders a document or the current thread's validated content into the same on-brand artifact brainstorming produces.

> **Path Resolution:** Resolve the plugin root per `skills/_shared/resolve-skill-path.md`. Template, widgets, components doc, and the mermaid validator live under `{plugin-root}/skills/brainstorming/`.

## Anti-shortcut contract

Copy the template file and patch it. NEVER hand-write or "compactly rewrite" the artifact HTML from memory, even when that seems faster — that shortcut bypasses the template, the widgets, the browser-open, and the Overview gate (KB-085/086).

## Step 1: Resolve the source

- **Path argument given:** read that markdown document; it is `{source-content}`.
- **No argument:** use the validated content from the current conversation.
- **Neither yields renderable content:** ask exactly this question (fixed wording):

  > No document path was given and this conversation has no renderable content yet. Give me either: (a) a path to a markdown doc to visualize, or (b) a one-sentence description of what to visualize and I'll build it with you here.

## Step 2: Resolve Configuration and call the runner

Resolve the runner's Configuration inputs (all absolute):
- `{template-path}` = `{plugin-root}/skills/brainstorming/references/templates/software-template.html` (resolved via plugin root — NEVER `{base-directory}`-relative; no templates live under `visualize-design/`).
- `{widgets-path}` = `{plugin-root}/skills/brainstorming/references/widgets.html`
- `{components-path}` = `{plugin-root}/skills/brainstorming/references/brainstorm-components.md`
- `{validate-mermaid-script}` = `{plugin-root}/skills/brainstorming/scripts/validate-mermaid.mjs`
- `{session-name}` = `YYYY-MM-DD-<topic-slug>`
- `{output-path}` = `{project-root}/docs/design-visualizations/{session-name}.html`
- `{live-session}` = `yes`

Follow `skills/_shared/visualization-runner.md` end-to-end with that Configuration. Open the self-refreshing `/tmp` artifact immediately and update as the user iterates. Inject widgets only if the content actually contains a Decision Log or Open Questions section.

## Step 3: Finish

On user confirmation: run the runner's mermaid gate and executive-overview gate, write the final copy to `{project-root}/docs/design-visualizations/{session-name}.html` (create the directory if missing), strip the live-refresh script, and open the committed copy. **If `{output-path}` already exists, overwrite it** — re-rendering the same doc the same day is the expected workflow, not an error.
````

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest e2e/tests/test_visualize_design_files.py -q`
Expected: PASS (all five)

**Step 5: Commit**

```bash
git add skills/visualize-design/SKILL.md e2e/tests/test_visualize_design_files.py
git commit -m "feat(viz): add standalone visualize-design skill"
```

---

## Task 13: Guard the visualize-design→runner cross-reference

**Files:**
- Modify: `e2e/tests/test_skill_cross_references.py` (`REQUIRED_CROSS_REFS`)

Retroactive guard — the reference was added in Task 12.

**Step 1: Add the guard tuple**

Insert the tuple inside `REQUIRED_CROSS_REFS` — before the closing `]` of the list (line numbers shift as tasks execute; locate the `]` by searching for it after the last existing tuple):

```python
    (REPO_ROOT / "skills" / "visualize-design" / "SKILL.md",
     "skills/_shared/visualization-runner.md"),
```

**Step 2: Run the parametrized check to verify it passes**

Run: `python3 -m pytest "e2e/tests/test_skill_cross_references.py::test_cross_reference_link_resolves" -q`
Expected: PASS

**Step 3: Commit**

```bash
git add e2e/tests/test_skill_cross_references.py
git commit -m "test(viz): guard visualize-design -> runner cross-reference"
```

---

## Task 14: Add the README skill-table row and bump the plugin version

**Files:**
- Modify: `README.md` (skill reference table)
- Modify: `.claude-plugin/plugin.json` (`version`)
- Modify: `.claude-plugin/marketplace.json` (`version`)
- Test: `e2e/tests/test_visualize_design_files.py` (new `test_readme_lists_visualize_design`)

**Step 1: Write the failing test**

Append to `e2e/tests/test_visualize_design_files.py`:

```python
def test_readme_lists_visualize_design():
    text = read("README.md")
    assert "visualize-design" in text, "README skill table must list visualize-design"
    assert "/aligned:visualize-design" in text, "README must show the invocation"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest e2e/tests/test_visualize_design_files.py::test_readme_lists_visualize_design -q`
Expected: FAIL — README has no visualize-design row.

**Step 3: Edit README and bump versions**

In `README.md`'s skill reference table (header `| Skill | Type | Invocation | Description |`), add a row (alongside the other Entry Point rows, e.g. near `create-image`):

```markdown
| visualize-design | Entry Point | `/aligned:visualize-design` | Render any markdown doc or the current conversation as an on-brand, tabbed, Mermaid-validated HTML artifact |
```

Bump the version `0.31.0` → `0.32.0` in BOTH files:
- `.claude-plugin/plugin.json`: `"version": "0.32.0"`
- `.claude-plugin/marketplace.json`: the `version` field inside `plugins[0]`: `"0.32.0"`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest e2e/tests/test_visualize_design_files.py::test_readme_lists_visualize_design -q`
Expected: PASS

**Step 5: Verify both versions match**

Run: `grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json`
Expected: both lines show `0.32.0`.

**Step 6: Commit**

```bash
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json e2e/tests/test_visualize_design_files.py
git commit -m "docs(viz): add visualize-design to README and bump to 0.32.0"
```

---

## Task 15: Point the diagram agents at the runner's token-resolution section (optional dedup)

**Files:**
- Modify: `agents/flowchart-generator.md` (the token-resolution paragraph)
- Modify: `agents/architecture-diagram-generator.md` (the token-resolution paragraph)
- Modify: `agents/mockup-generator.md` (the token-resolution paragraph)
- Test: `e2e/tests/test_skill_cross_references.py` (`REQUIRED_CROSS_REFS`)

Optional cleanup, sequenced last so it cannot block the core work. Each agent currently restates a simplified project→global token lookup (e.g. `flowchart-generator.md:22`). Point them at the runner's fuller ladder instead.

> Behavior change: these agents currently read only `docs/design-principles.md` → global fallback. The runner's Step 2 adds the monorepo `apps/*` / `packages/*` glob and the placeholder heuristic. After this task the agents inherit that fuller resolution — a deliberate dedup, not a regression.
>
> Coupling note: the diagram agents are not runner callers — they reference `visualization-runner.md § "Step 2"` as a standalone read. Any future edits to Step 2 that add runner-specific context (e.g., references to Configuration Validation state) will silently affect the agents. Keep Step 2 self-contained and ladder-only.

**Step 1: Add the guard tuples**

Insert three tuples inside `REQUIRED_CROSS_REFS` in `e2e/tests/test_skill_cross_references.py` — before the closing `]` of the list (line numbers shift as tasks execute; locate the `]` by searching for it after the last existing tuple):

```python
    (REPO_ROOT / "agents" / "flowchart-generator.md",
     "skills/_shared/visualization-runner.md"),
    (REPO_ROOT / "agents" / "architecture-diagram-generator.md",
     "skills/_shared/visualization-runner.md"),
    (REPO_ROOT / "agents" / "mockup-generator.md",
     "skills/_shared/visualization-runner.md"),
```

**Step 2: Run the parametrized check to verify it fails**

Run: `python3 -m pytest "e2e/tests/test_skill_cross_references.py::test_cross_reference_link_resolves" -q`
Expected: FAIL — the three agents do not reference the runner yet.

**Step 3: Edit the three agents**

In each agent's token-resolution paragraph (e.g. `flowchart-generator.md:22`, the "Before generating any flowchart, read `docs/design/design-principles.md`..." sentence), replace the inline simplified ladder with a pointer:

```markdown
Resolve the project's design tokens using the ladder in `skills/_shared/visualization-runner.md` § "Step 2: Resolve the project's design tokens" (project root → monorepo `apps/*`/`packages/*` glob → global fallback, with the placeholder heuristic). Extract color tokens and semantic diagram colors from the resolved file and apply them to the template below.
```

Keep each agent's diagram-specific guidance (its template, the "Diagram Documentation Principles" reference, Mermaid style directives) untouched — only the token-lookup paragraph changes.

**Step 4: Run the parametrized check to verify it passes**

Run: `python3 -m pytest "e2e/tests/test_skill_cross_references.py::test_cross_reference_link_resolves" -q`
Expected: PASS

**Step 5: Commit**

```bash
git add agents/flowchart-generator.md agents/architecture-diagram-generator.md agents/mockup-generator.md e2e/tests/test_skill_cross_references.py
git commit -m "refactor(viz): point diagram agents at the runner token ladder"
```

---

## Manual Steps (Post-Automation)

Manual-deploy scan: no catalog matches detected. (No migrations or other production-deploy artifacts in this plan.)

None.

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Task granularity per logical commit | 15 small TDD tasks across the design's 4 commits | Fewer, larger tasks matching the 4 commits 1:1 |
| 2 | Where the per-doc structural guards live | Existing test files (`test_shared_runners.py`, `test_brainstorming_files.py`, `test_skill_cross_references.py`) + one new `test_visualize_design_files.py` | One new monolithic `test_visualization_extraction.py` |
| 3 | Commit-1 runner holds the *current* engine, hardening deferred to commit 2 | Behavior-equivalent extract first | Bake KB-085/086 fixes into the extraction commit |
| 4 | Overview scaffold scope | Five templates (software + 4 authoring), roadmap excluded | All six templates |
| 5 | `panel-overview active` shorthand resolution | Assert `id="panel-overview"` + `class="tab-panel active"` (two substrings) | Force a contiguous `panel-overview active` token, breaking `switchTab`'s id convention |
| 6 | Agent token-ladder dedup (Task 15) included | Included as the last, optional task | Drop it from the plan as out-of-scope |
| 7 | `{validate-mermaid-script}` as a runner Configuration input vs. hardcoded path | Caller-supplied (Configuration input) | Hardcoded absolute path inside the runner |

### Appendix: Decision Details

#### Decision 1: Task granularity per logical commit
**Chose:** 15 bite-sized TDD tasks, each one coherent commit, grouped under the design's four logical commits.
**Why:** The skill mandates 2–5 minute steps and one-commit tasks. The design's "commit 1" alone bundles a file creation, an eval-surface edit, a protocol slim, two pointer edits, and a mode-reference edit — five independently-verifiable changes. Splitting them keeps each task verifiable by running only the test it touches, and keeps failure blast radius to one commit.
**Alternatives rejected:**
- 4 tasks matching commits 1:1: each would modify 5–6 files across multiple test files in one commit, violating task-sizing (checklist Crit 3) and making per-task verification impossible.

#### Decision 2: Guard test placement
**Chose:** Reuse the three existing guard files the design names (`test_shared_runners.py` for runner/eval-surface assertions, `test_skill_cross_references.py` for `REQUIRED_CROSS_REFS`, `test_brainstorming_files.py` for protocol/shared-rules/software.md/templates) and add one new `test_visualize_design_files.py` for the new skill.
**Why:** The design's Testing section pins specific assertions to `test_shared_runners.py` and `test_skill_cross_references.py` and rewrites the scaffolding test that already lives in `test_brainstorming_files.py`. Following the existing homes keeps related guards together (a reader looking for runner guards finds them all in one file) and matches the design literally.
**Alternatives rejected:**
- One new monolithic test file: would scatter the design's named assertions away from their pinned homes and duplicate the `read()` helper for no benefit.

#### Decision 3: Behavior-equivalent extract before hardening
**Chose:** Commit 1 (Tasks 1–6) relocates the *current* engine with no behavior change; KB-085/086 hardening (anti-shortcut, unconditional browser-open, Overview gate, scaffold) lands in commit 2 (Tasks 7–11).
**Why:** This is the design's explicit "no-behavior-change first" migration order (Decision 13). A behavior-equivalent extract is reviewable as a pure move — if brainstorming visualization breaks after commit 1, the cause is the relocation, not new logic. Mixing the move with new gates would make a regression ambiguous.
**Alternatives rejected:**
- Combine extraction + hardening: faster but conflates "did the move preserve behavior?" with "do the new gates work?" — exactly the ambiguity the design's staged commits avoid.

#### Decision 4: Overview scaffold scope is five templates, not six
**Chose:** Inject the Overview scaffold into `software-template.html` + the four `authoring-*` variants; exclude `roadmap-template.html`.
**Why:** The design scopes the scaffold to "the five visualizing templates (`software-template.html` + four authoring variants)" and the rewritten scaffolding test lists exactly those five. `roadmap-template.html` exists but roadmap mode produces no live design artifact (`shared-rules.md` § strip rule explicitly exempts research and roadmap). Adding an Overview tab to a template that is never used for the design-artifact flow would be unused surface.
**Alternatives rejected:**
- All six templates: roadmap would gain an unused Overview tab; contradicts the design's stated five-template scope and the strip-rule exemption.

#### Decision 5: Resolving the `panel-overview active` shorthand
**Chose:** The test asserts two real substrings — `id="panel-overview"` and `class="tab-panel active"` — rather than a single contiguous `panel-overview active` token.
**Why:** `switchTab(tabId)` resolves panels as `document.getElementById('panel-' + tabId)` (`software-template.html` ~line 629). The Overview panel's id must therefore be exactly `panel-overview`, and its visible state is the existing `tab-panel active` class pair. A literal contiguous string `panel-overview active` would require either renaming the id (breaking `switchTab`) or an attribute ordering that doesn't match the existing template markup. The design's `panel-overview active` is descriptive shorthand for "the panel-overview panel, active"; the two-substring assertion captures that intent without fighting the tab system.
**Alternatives rejected:**
- Contiguous `panel-overview active` token: would force a non-standard markup shape and risk breaking the JS tab switcher the templates already ship.

#### Decision 6: Include the optional agent dedup (Task 15)
**Chose:** Include Task 15 (point the three diagram agents at the runner's token ladder) as the final task.
**Why:** The design lists it as commit 4. It is real implementation work with a scoped verification (the parametrized cross-ref test), not a verification sweep — so it is a valid final task. Sequenced last, it cannot block the core extraction/skill work, and if execution stops early the first three commits still deliver the full feature.
**Alternatives rejected:**
- Drop it: the token-ladder duplication across four files (the three agents + the runner) is exactly the kind of restatement the design consolidates; deferring indefinitely leaves the agents on a thinner ladder than the runner.

#### Decision 7: `{validate-mermaid-script}` as a caller-supplied Configuration input
**Chose:** Expose `{validate-mermaid-script}` as a ninth Configuration input (the caller passes the absolute path).
**Why:** `skills/_shared/` runners cannot self-resolve paths (per `skills/_shared/resolve-skill-path.md`). The mermaid validator lives under `skills/brainstorming/scripts/`, not under `_shared/`, so the runner cannot derive the path without knowing the plugin root — which only the caller knows. Caller-supplied is the correct pattern; it also makes the runner testable with a substitute validator path. The design's Runner Contract table lists only 8 inputs; this ninth input was implied by the portability rule but not made explicit.
**Alternatives rejected:**
- Hardcode the path: would make the runner author-environment-specific and break for any user with a different plugin installation path. Violates the portability rule.

