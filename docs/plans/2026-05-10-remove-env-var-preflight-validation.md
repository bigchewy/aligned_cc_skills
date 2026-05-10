---
mcp-tools-required: []
---

# Remove Env-Var Preflight Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Delete the env-var preflight validation surface end-to-end (preflight check, halt reason, manifest field, writing-plans scan) so autopilot stops halting when a project's env vars live in `.env.local` rather than the parent shell.

**Source Design Doc:** N/A — design captured in the chat root-cause session that produced this plan (2026-05-10). Original autopilot-orchestration design lives at `docs/plans/completed/2026-04-30-autopilot-orchestration-redesign.md`; this plan removes the env-var portion of that design.

**Architecture:** The April 30 redesign added two parallel preflight checks (MCP tools, env vars). The MCP check addresses a documented incident (`mcp__playwright-full__*` ghost namespace) and stays. The env-var check addresses no documented incident — it was added for symmetry and creates a false-positive halt whenever a project ships `.env.local` and frameworks auto-load it at runtime. Delete the env-var surface; keep MCP unchanged.

**Tech Stack:** Bash (`set -u`), Python pytest for static-parse + bash-function-level tests.

**Reach:** 3 source files (`lib/manifest.sh`, `phases/preflight.sh`, `lib/halt.sh`), 3 test files (`test_manifest_validation.py`, `test_halt_protocol.py`, `test_writing_plans_manifest_authoring.py`), 2 fixtures (`plan_with_manifest.md`, `plan_partial.md`), 5 docs (`plan-manifest-format.md`, `autopilot-halt-format.md`, `writing-plans/SKILL.md`, `critique-panel-prompts.md`, `writing-plans/plan-critique-checklist.md`), 2 version files.

**Out of scope (historical-snapshot surfaces that retain env-var references):** `docs/plans/completed/2026-04-30-autopilot-orchestration-redesign.md`, `docs/plans/completed/2026-04-30-autopilot-orchestration-impl.md`, `docs/mockups/autopilot-orchestration-redesign.html`, `docs/kanban/todo/KB-054-format-halt-mcp-cases-untested.md`. See Decision Log entry 6.

---

## Prerequisites

None. All work is repo-internal.

---

### ✅ Task 1: Stop preflight from validating env vars

**Files:**
- Modify: `docs/ralph_loops/phases/preflight.sh` (the env-var validation loop)
- Modify: `e2e/tests/test_manifest_validation.py` (the `test_preflight_halts_on_missing_env_var` and `test_validate_env_var_*` tests)

**Step 1: Update the preflight test to assert pass instead of halt**

In `e2e/tests/test_manifest_validation.py`:
- Rename the function `test_preflight_halts_on_missing_env_var` → `test_preflight_passes_when_env_vars_required_unset` (line 115).
- Update the docstring (lines 116-117) to: `"""End-to-end: invoke preflight against a fixture plan; verify env-var requirements no longer halt preflight."""`
- Update the comment at line 122 from `# explicitly omit FAKE_TEST_VAR so env_var_missing is what trips.` to `# omit FAKE_TEST_VAR — preflight no longer probes env vars, so this is informational.`
- Update the comment at line 131 from `# FAKE_TEST_VAR is not set → halt with env_var_missing → exit 2` to `# Preflight no longer validates env vars → returncode 0, no halt sentinel written.`
- Replace lines 132-135 (the three assertions) with:
  ```python
  assert r.returncode == 0, f"preflight should pass (exit 0), got {r.returncode}: {r.stderr}"
  sentinel = Path(d) / ".autopilot-halt"
  assert not sentinel.exists(), "preflight must NOT write .autopilot-halt when env vars are unset"
  ```
- Delete `test_validate_env_var_missing` (lines 41-48) and `test_validate_env_var_present` (lines 51-56) outright — these test a function that's about to be deleted.
- Update `test_parse_manifest_present` to drop the `FAKE_TEST_VAR` assertion at line 25 (after Task 2 the fixture won't have env-vars-required, but the parse test still runs against the same fixture; just check the MCP entry remains).

**Step 2: Run tests, verify failures**

```bash
cd /Users/ericpage/software/aligned_cc_skills
python -m pytest e2e/tests/test_manifest_validation.py -v
```

Expected:
- `test_preflight_passes_when_env_vars_required_unset`: FAIL (preflight still halts because the env-var loop in `preflight.sh` is still intact)
- `test_validate_env_var_missing` and `test_validate_env_var_present`: no longer present in the run output (deleted in Step 1)
- `test_parse_manifest_present`: PASS (FAKE_TEST_VAR assertion removed in Step 1; fixture still emits it via parse_manifest until Task 2, but no test asserts on it)

**Step 3: Remove the env-var loop from preflight.sh**

In `docs/ralph_loops/phases/preflight.sh`, delete lines 43-49 (the `for var in "${MANIFEST_ENV_VARS[@]+...}"; do ... done` block — the comment "# Validate env vars" and the loop). The MCP tools loop immediately below it stays.

**Step 4: Run tests, verify they pass**

```bash
python -m pytest e2e/tests/test_manifest_validation.py -v
```

Expected: all remaining tests pass.

**Step 5: Commit**

```bash
git add docs/ralph_loops/phases/preflight.sh e2e/tests/test_manifest_validation.py
git commit -m "fix(autopilot): stop preflight from validating env-vars-required"
```

---

### ✅ Task 2: Remove `check_env_var` and env-var parsing from manifest.sh

> **Ordering:** Task 2 must follow Task 1. Task 1 softens the parse-test assertion so removing env-var parsing here doesn't fail tests for an unrelated reason.

**Files:**
- Modify: `docs/ralph_loops/lib/manifest.sh` (the `check_env_var` function, `MANIFEST_ENV_VARS` array, env-var parsing in `parse_manifest`)
- Modify: `e2e/fixtures/manifest/plan_with_manifest.md` (drop `env-vars-required` field)
- Modify: `e2e/fixtures/manifest/plan_partial.md` (drop the `env-vars-required:` line — malformed-ness is preserved by the still-missing closing `---`)

**Step 1: Update fixtures**

`e2e/fixtures/manifest/plan_with_manifest.md` — remove the `env-vars-required:\n  - FAKE_TEST_VAR` lines from the front-matter. Final front-matter should be:
```yaml
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
---
```
And remove "and FAKE_TEST_VAR" from the body prose.

`e2e/fixtures/manifest/plan_partial.md` — this fixture exists to trigger `manifest_malformed`. The malformed-ness comes from a missing closing `---` (verified: file is 4 lines, ends after `env-vars-required:`). Drop the `env-vars-required:` line on line 4. The fixture remains malformed because there is still no closing `---`. The `test_parse_manifest_malformed_returns_error` test in `test_manifest_validation.py` continues to pass.

**Step 2: Run tests, verify failures**

```bash
python -m pytest e2e/tests/test_manifest_validation.py -v
```

Any test still asserting `env:` output from `parse_manifest` or `MANIFEST_ENV_VARS` population should fail.

**Step 3: Delete env-var code from `lib/manifest.sh`**

Delete:
- Line 12: `MANIFEST_ENV_VARS=()`
- Line 20 (inside `parse_manifest`): `MANIFEST_ENV_VARS=()` reset
- Line 52 (inside the python block): the entire `for v in (d.get("env-vars-required") or []): print(f"env:{v}")` loop
- Line 59 (the bash case): `env:*) MANIFEST_ENV_VARS+=("${line#env:}"); echo "$line" ;;`
- Lines 66-75: the entire `check_env_var()` function and its comment header

After deletion, the only manifest field parsed is `mcp-tools-required`, and the only check function is `check_mcp_tool`.

**Step 4: Run tests, verify they pass**

```bash
python -m pytest e2e/tests/test_manifest_validation.py e2e/tests/test_phase_contracts.py -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add docs/ralph_loops/lib/manifest.sh e2e/fixtures/manifest/
git commit -m "refactor(autopilot): remove check_env_var and env-vars-required parsing"
```

---

### Task 3: Remove `env_var_missing` halt reason

**Files:**
- Modify: `docs/ralph_loops/lib/halt.sh` (the `env_var_missing` case in `format_halt`)
- Modify: `e2e/tests/test_halt_protocol.py` (EXPECTED_REASONS, write_halt tests, format_halt test)
- Modify: `skills/_shared/autopilot-halt-format.md` (the `env_var_missing` row in the taxonomy table)

**Step 1: Update halt-protocol tests**

In `e2e/tests/test_halt_protocol.py`:
- Remove `"env_var_missing",` from `EXPECTED_REASONS` (line 17).
- In `test_write_halt_creates_sentinel` (around line 50): replace `write_halt env_var_missing preflight "FAKE_VAR is unset"` with `write_halt mcp_unreachable preflight "playwright server undefined"` and update the assertion strings accordingly.
- In `test_write_halt_secondary_appends_not_overwrites` (lines 66-75): the test currently writes `env_var_missing` first and `mcp_unreachable` second. Replace the `env_var_missing` call at line 70 with `mcp_tool_not_allowlisted` (or any other still-valid reason), and update the assertions at lines 73-75 to match (`"reason: mcp_tool_not_allowlisted" in text`, etc.). The second call stays as `mcp_unreachable`.
- Delete `test_format_halt_echoes_canonical_fix` (lines 78-82) entirely — it specifically validates the `env_var_missing` format_halt case.

**Step 2: Update the halt-format doc**

In `skills/_shared/autopilot-halt-format.md`, delete the table row:
```
| `env_var_missing` | preflight | Plan declares an env var that is unexported in the shell that invokes `autopilot.sh` |
```

**Step 3: Run tests, verify failures**

```bash
python -m pytest e2e/tests/test_halt_protocol.py -v
```

Expected:
- `test_halt_format_doc_lists_all_reasons` should now pass (env_var_missing dropped from EXPECTED_REASONS AND from the doc)
- `test_format_halt_cases_match_write_halt_callsites` (the contract test) should FAIL because `lib/halt.sh` still has the `env_var_missing)` case but no callsite emits it (Task 1 removed the callsite).

**Step 4: Delete the `env_var_missing` case from `lib/halt.sh`**

In `docs/ralph_loops/lib/halt.sh`, delete the `env_var_missing)` case in `format_halt` — lines 89-114 (the case label, the `cat <<'EOF' ... EOF` body, and the closing `;;`).

**Step 5: Run tests, verify they pass**

```bash
python -m pytest e2e/tests/test_halt_protocol.py -v
```

Expected: all tests pass. Specifically, `test_format_halt_cases_match_write_halt_callsites` confirms zero phantom cases and zero undocumented callsites.

**Step 6: Commit**

```bash
git add docs/ralph_loops/lib/halt.sh skills/_shared/autopilot-halt-format.md e2e/tests/test_halt_protocol.py
git commit -m "refactor(autopilot): remove env_var_missing halt reason"
```

---

### Task 4: Drop `env-vars-required` from the manifest schema doc

**Files:**
- Modify: `skills/_shared/plan-manifest-format.md` (schema example, validation section, coherence-check section)
- Modify: `e2e/tests/test_writing_plans_manifest_authoring.py` (the `test_manifest_format_doc_exists` assertion that requires both fields)

**Step 1: Update the schema-doc test**

In `e2e/tests/test_writing_plans_manifest_authoring.py:20`, change:
```python
for field in ("mcp-tools-required", "env-vars-required"):
```
to:
```python
for field in ("mcp-tools-required",):
```

**Step 2: Run the test, verify it still passes (defensive)**

```bash
python -m pytest e2e/tests/test_writing_plans_manifest_authoring.py::test_manifest_format_doc_exists -v
```

Currently passes because the doc still has both fields. After Step 3 it must still pass with the narrowed assertion.

**Step 3: Update `plan-manifest-format.md`**

In `skills/_shared/plan-manifest-format.md`:
- Schema example (lines 12-15): remove the `env-vars-required:` field and its two sample entries (`SUPABASE_URL`, `OPENAI_API_KEY`). Keep only the `mcp-tools-required:` field.
- "Both fields are arrays" sentence (line 18): change to "The field is an array of strings. It is optional; an empty list is equivalent to omitting the field."
- "Validation (autopilot preflight)" section: remove the `**Env vars.**` paragraph (line 39) and the `> Authors: a variable that lives only in .env.local ...` blockquote (line 41).
- "Coherence check (Verifier critic)" bullet (line 48): remove `- Both directions: same rule for env-vars-required vs process.env.* / os.environ.* / shell ${VAR} references.`
- Replace the stale line-number reference in the MCP tools paragraph (currently "per `phases/preflight.sh:53`") with a content anchor: `per the check_mcp_tool callsite in phases/preflight.sh`. After Task 1's deletion the line number shifts.

**Step 4: Run tests, verify they pass**

```bash
python -m pytest e2e/tests/test_writing_plans_manifest_authoring.py -v
```

Expected: all pass. `test_verifier_prompt_has_manifest_coherence_rule` still passes because it only requires `mcp-tools-required` and the word "manifest" + "coherence" in the verifier prompt — not env-vars-required specifically.

**Step 5: Commit**

```bash
git add skills/_shared/plan-manifest-format.md e2e/tests/test_writing_plans_manifest_authoring.py
git commit -m "docs(autopilot): drop env-vars-required from plan-manifest schema"
```

---

### Task 5: Remove env-var scan from writing-plans

**Files:**
- Modify: `skills/writing-plans/SKILL.md` (the "Plan Manifest (autonomous authoring)" section, step 2)
- Modify: `skills/writing-plans/references/critique-panel-prompts.md` (the Verifier prompt's manifest-coherence sub-rule)
- Modify: `skills/writing-plans/plan-critique-checklist.md` (Criterion 10 table rows for "Manual-deploy artifacts" and "Manifest coherence")

**Step 1: Update writing-plans SKILL.md**

In `skills/writing-plans/SKILL.md`, find the "## Plan Manifest (autonomous authoring)" section. In the "Procedure" list:
- Step 2 currently reads: `Scan for env-var references: process\.env\.[A-Z_][A-Z0-9_]*, os\.environ\[['"]([A-Z_][A-Z0-9_]*)['"]\], and shell \$\{?[A-Z_][A-Z0-9_]*\}? patterns. Same fenced-block exclusions. Collect unique names.` — delete this entire step.
- Renumber subsequent steps (the existing step 3 becomes step 2, step 4 becomes step 3).
- In the remaining "If both lists are empty" sentence, change "both lists" to "the MCP list" and adjust the rest of the sentence accordingly.

Do NOT remove the "Standalone Scripts and Environment Variables" section at SKILL.md:150 — that section is about ensuring scripts include `import 'dotenv/config'`, which is unrelated to preflight validation. It stays.

**Step 2: Update the Verifier critique prompt**

In `skills/writing-plans/references/critique-panel-prompts.md`, find the Verifier's Phase 3 manifest-coherence section. The current text reads "...parse `mcp-tools-required` and `env-vars-required`. Walk the plan body...extract every `mcp__*__*` reference and every env-var reference..." Edit to:
- Remove `and env-vars-required` from the parse step
- Remove the env-var-reference walking and reporting
- Keep the MCP coherence rule (both-direction structural diff) intact

Specifically, the sentence "and extract every `mcp__*__*` reference and every env-var reference (`process.env.X`, `os.environ['X']`, shell `${X}` for uppercase X)" becomes "and extract every `mcp__*__*` reference."

**Step 3: Update `plan-critique-checklist.md`**

In `skills/writing-plans/plan-critique-checklist.md`, in the Criterion 10 gap-analysis table (lines 156-167):
- Line 164 ("Manual-deploy artifacts" row): change `(migrations, env vars)` to `(migrations)`.
- Line 165 ("Manifest coherence" row): remove the sentence `Same for env vars.` so the row reads "Does the plan have YAML front-matter? Does every `mcp__*__*` body reference appear in `mcp-tools-required`? Does every manifest entry appear in the body? **Mismatch is HIGH severity** — see `skills/_shared/plan-manifest-format.md`."

**Step 4: Run all writing-plans tests**

```bash
python -m pytest e2e/tests/test_writing_plans_manifest_authoring.py e2e/tests/test_writing_plans_anti_review.py -v
```

Expected: all pass.

**Step 5: Run the full e2e test suite**

```bash
python -m pytest e2e/tests/ -v
```

Expected: all pass.

**Step 6: Commit**

```bash
git add skills/writing-plans/SKILL.md skills/writing-plans/references/critique-panel-prompts.md skills/writing-plans/plan-critique-checklist.md
git commit -m "refactor(writing-plans): drop env-var scan from manifest authoring + verifier"
```

---

### Task 6: Version bump and final verification

**Files:**
- Modify: `.claude-plugin/plugin.json` (version field)
- Modify: `.claude-plugin/marketplace.json` (version field, must match plugin.json)

**Step 1: Bump version**

Both files currently read `"version": "0.27.1"`. Change both to `"version": "0.27.2"`.

**Step 2: Run the full test suite one more time**

```bash
python -m pytest e2e/tests/ -v
```

Expected: 100% pass.

**Step 3: Grep for any leftover references in live surfaces**

Run via Grep tool (not Bash piping):
- Pattern: `env-vars-required|env_var_missing|check_env_var|MANIFEST_ENV_VARS`
- Path: repo root
- Filter the result: discard any match whose path is under any of these historical-snapshot directories (see Decision 6):
  - `docs/plans/completed/`
  - `docs/mockups/`
  - `docs/kanban/todo/KB-054-*.md` (the specific historical entry)

**Expected live matches: zero.** If any non-historical file still contains a match, address it before committing.

**Expected historical matches (informational, do NOT remove):**
- `docs/plans/completed/2026-04-30-autopilot-orchestration-redesign.md`
- `docs/plans/completed/2026-04-30-autopilot-orchestration-impl.md`
- `docs/mockups/autopilot-orchestration-redesign.html`
- `docs/kanban/todo/KB-054-format-halt-mcp-cases-untested.md`

These are frozen historical surfaces — they describe the previous state of the codebase and intentionally retain the old terminology. Touching them would falsify the historical record.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version 0.27.1 → 0.27.2"
```

---

## Manual Steps (Post-Automation)

### Reproduction against a real project (optional smoke test)

After autopilot completes the above, optionally verify the original failure no longer reproduces against any external project. Pick any project on your machine that ships environment variables in `.env.local` without exporting them to the parent shell (the originating incident used `appreciations` with `DATABASE_URL`; any equivalent project works).

1. Open the chosen project: `cd <project-path>`.
2. Confirm it has some `VAR` in `.env.local` but NOT exported in your shell: `[ -f .env.local ] && grep -q '^VAR=' .env.local && echo "in file"; echo "${VAR:-UNSET}"`.
3. Pick (or create) a small design doc inside that project's plans/designs directory.
4. Run autopilot: `bash <aligned_cc_skills>/docs/ralph_loops/autopilot.sh <project-path> <relative-design-doc-path>`.
5. Expected: preflight passes (no `env_var_missing` halt). Subsequent phases may still fail on other grounds (that's normal); the test is specifically that preflight does not block on the env-var check.

If preflight still halts with `env_var_missing`, file a Kanban entry (`skills/_shared/kanban-entry-format.md`) — the plan did not deliver on its goal.

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | What to do about `.env.local` parsing | Don't parse it; remove the check entirely | Build a safe `.env.local` parser; shell out to `dotenvx` |
| 2 | Keep or remove `env-vars-required` manifest field | Remove the field entirely from schema, parser, scan | Keep as documentation-only |
| 3 | Keep MCP-tool preflight unchanged | Keep | Reconsider MCP check at the same time |
| 4 | Revert May 9 halt-copy commit (`c860f1b`)? | Don't revert; supersede via deletion | Revert, then re-edit |
| 5 | Test the change against a real project automatically | Manual reproduction (Post-Automation, optional) | Build an integration test fixture |
| 6 | What to do about historical-snapshot files that still mention the removed surface | Leave them frozen as historical record; scope Task 6's grep to live surfaces | Edit the archives to scrub all mentions; or scrub none and accept a permanently-failing grep |

### Appendix: Decision Details

#### Decision 1: Don't parse `.env.local` at all

**Chose:** Delete the env-var preflight check rather than build a safe parser.

**Why:** The April 30 redesign doc (lines 17-19) lists two motivating signals — both are about MCP tools. No incident in the design doc cites a failed autopilot run caused by an env var being missing. The env-var check was added for architectural symmetry with the MCP check. Building a `.env.local` parser to "fix" the check spends effort defending against a hypothetical problem (the user's `.env.local` is incomplete) while the real-world failure mode is the opposite (the user's `.env.local` is complete and preflight rejects it anyway). Frameworks downstream (Next.js, Vite, Prisma) auto-load `.env.local` from the worktree CWD; the worktree env-link block at `phases/worktree.sh:79-101` already makes that work. The `claude -p` subprocess itself needs system-level vars (e.g., `ANTHROPIC_API_KEY`), not project-level `.env.local` vars.

If a real env-var problem ever does surface (e.g., a Rust project that doesn't use a framework loader), it'll fail downstream with a clear, framework-native error message — fix-then is cheaper than parse-now plus parser-maintenance.

**Alternatives rejected:**
- **Build a safe `.env.local` parser (node `dotenv`, hand-rolled bash, `dotenvx`):** adds a dependency or a maintenance surface to handle `#`, spaces, multi-line PEM, quoted values. Solves a non-incident.
- **Shell out to `dotenvx`:** assumes Node is installed on every target project; the autopilot targets Node, Rust, Python projects.

#### Decision 2: Remove `env-vars-required` entirely

**Chose:** Delete the field from the schema, the parser, the writing-plans scan, and the Verifier coherence check.

**Why:** A documentation-only field that's never enforced is cruft — it invites authors to declare env requirements that the executor will silently ignore, then surfaces as a confusion-trap later. Plans already have a `## Prerequisites` section for human-readable env setup instructions. Keep the human prose; drop the YAML symmetry.

**Trade-off acknowledged:** The current SKILL.md and manifest schema treat `mcp-tools-required` and `env-vars-required` as a symmetric two-field pattern (parallel scan, parallel coherence check, parallel preflight loop). Removing one side abandons that symmetry. If a third manifest field is ever added later (e.g., `secrets-required`, `services-required`), the code path is no longer "extend the symmetric pair" but "add a third special-case." A future refactor could re-introduce symmetry via a `scan_manifest_field(name, regex)` helper, but that's deferred — YAGNI until a third field is actually proposed.

**Alternatives rejected:**
- **Keep as documentation-only:** doesn't actually document anything users see at autopilot time; just clutters the front-matter.

#### Decision 3: Keep MCP-tool preflight unchanged

**Chose:** This plan touches only the env-var surface. MCP tool validation stays intact.

**Why:** MCP failures are a documented incident class (`mcp__playwright-full__*` ghost namespace, partial allowlists). The check has positive ROI. Bundling an MCP-check reconsideration into this plan expands scope and creates the kind of "while we're in here" sprawl the repo's CLAUDE.md explicitly warns against.

#### Decision 4: Don't revert `c860f1b` (May 9)

**Chose:** Move forward via deletion, not by reverting May 9.

**Why:** `c860f1b` was an honest acknowledgment of an existing bug (the April 30 implementation never matched its own design). Reverting it would restore halt-text that promised users `.env.local` would work — text that didn't reflect actual behavior. The new state (no env-var check at all) makes that text moot. Reverting and re-editing in series adds noise to git history.

#### Decision 5: Manual reproduction against a real project, not an automated integration test

**Chose:** Add a Post-Automation reproduction step (parameterized over any project with a `.env.local`-only env-var setup, not a specific machine) rather than building a fixture-based integration test.

**Why:** The reproduction is a one-time confirmation that the original symptom is gone. Building an automated test for it would require fixturing a fake project with a `.env.local` and a manifest, then running the full preflight phase against it — `test_preflight_passes_when_env_vars_required_unset` in Task 1 already covers that case at the phase level. The Post-Automation step adds a real-world smoke test on top.

**Portability note:** The original draft of this section hardcoded `~/software/appreciations` as the reproduction target. Per CLAUDE.md's portability rule, that's an author-only path — rewritten to take any project as input.

#### Decision 6: Leave historical-snapshot files frozen rather than scrubbing all env-var refs

**Chose:** Task 6's leftover-grep step scopes the success contract to live surfaces only. Four historical files are explicitly out of scope: two completed-plan archives (`docs/plans/completed/2026-04-30-autopilot-orchestration-redesign.md`, `docs/plans/completed/2026-04-30-autopilot-orchestration-impl.md`), one mockup (`docs/mockups/autopilot-orchestration-redesign.html`), and one Kanban entry (`docs/kanban/todo/KB-054-format-halt-mcp-cases-untested.md`).

**Why:** A completed-plan archive describes what the codebase looked like at the time of the plan. Editing it post-hoc to remove now-deleted terminology falsifies the historical record — a future reader would see the archived plan reference a `check_env_var` step but no commit history showing the field ever existed at that point. Same applies to the mockup (a frozen visualization of the April 30 design) and to KB-054 (a Kanban entry whose "Observed" field cites `test_format_halt_echoes_canonical_fix` as a baseline; that test is being deleted in Task 3, but the entry's intent — surface the gap KB-054 raises — survives even after the cited test is gone).

The cleaner alternative would have been to scrub these files too, accepting the historical-record hit. The "do nothing" alternative would have left Task 6's grep contract permanently unsatisfiable. The scoped approach picks the middle path.

**Alternatives rejected:**
- **Edit the archives to scrub all mentions:** falsifies historical record; readers can't trace why the codebase looked the way it did at the time of the snapshot.
- **Scrub none and accept a permanently-failing grep:** breaks Task 6's success contract. Autopilot would halt or improvise on every re-run.

**Follow-up:** After this plan lands, file a small Kanban entry to update KB-054's "Observed" field to reference the surviving MCP cases instead of the deleted env_var_missing case. Not in scope for this plan.
