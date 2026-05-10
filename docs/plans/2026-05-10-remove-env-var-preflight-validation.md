---
mcp-tools-required: []
---

# Remove Env-Var Preflight Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Delete the env-var preflight validation surface end-to-end (preflight check, halt reason, manifest field, writing-plans scan) so autopilot stops halting when a project's env vars live in `.env.local` rather than the parent shell.

**Source Design Doc:** N/A — design captured in the chat root-cause session that produced this plan (2026-05-10). Original autopilot-orchestration design lives at `docs/plans/completed/2026-04-30-autopilot-orchestration-redesign.md`; this plan removes the env-var portion of that design.

**Architecture:** The April 30 redesign added two parallel preflight checks (MCP tools, env vars). The MCP check addresses a documented incident (`mcp__playwright-full__*` ghost namespace) and stays. The env-var check addresses no documented incident — it was added for symmetry and creates a false-positive halt whenever a project ships `.env.local` and frameworks auto-load it at runtime. Delete the env-var surface; keep MCP unchanged.

**Tech Stack:** Bash (`set -u`), Python pytest for static-parse + bash-function-level tests.

**Reach:** 3 source files (`lib/manifest.sh`, `phases/preflight.sh`, `lib/halt.sh`), 3 test files (`test_manifest_validation.py`, `test_halt_protocol.py`, `test_writing_plans_manifest_authoring.py`), 2 fixtures (`plan_with_manifest.md`, `plan_partial.md`), 4 docs (`plan-manifest-format.md`, `autopilot-halt-format.md`, `writing-plans/SKILL.md`, `critique-panel-prompts.md`), 2 version files.

---

## Prerequisites

None. All work is repo-internal.

---

### Task 1: Stop preflight from validating env vars

**Files:**
- Modify: `docs/ralph_loops/phases/preflight.sh` (the env-var validation loop)
- Modify: `e2e/tests/test_manifest_validation.py` (the `test_preflight_halts_on_missing_env_var` and `test_validate_env_var_*` tests)

**Step 1: Update the preflight test to assert pass instead of halt**

In `e2e/tests/test_manifest_validation.py`:
- Rename `test_preflight_halts_on_missing_env_var` → `test_preflight_passes_when_env_vars_required_unset`.
- Body: same fixture, same `PATH`-only env, same `PLAN_FILE`, but assert `r.returncode == 0` (preflight should pass with no env-var check) and assert the `.autopilot-halt` sentinel was NOT written.
- Delete `test_validate_env_var_missing` and `test_validate_env_var_present` outright — these test a function that's about to be deleted.
- Update `test_parse_manifest_present` to drop the `FAKE_TEST_VAR` assertion (after Task 2 the fixture won't have env-vars-required, but the parse test still runs against the same fixture; just check the MCP entry remains).

**Step 2: Run tests, verify failures**

```bash
cd /Users/ericpage/software/aligned_cc_skills
python -m pytest e2e/tests/test_manifest_validation.py -v
```

Expected:
- `test_preflight_passes_when_env_vars_required_unset`: FAIL (preflight still halts because env-var loop is intact)
- `test_validate_env_var_missing`: collected but now absent → no fail, just gone
- `test_parse_manifest_present`: PASS or FAIL depending on whether the FAKE_TEST_VAR assertion was already softened

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

### Task 2: Remove `check_env_var` and env-var parsing from manifest.sh

**Files:**
- Modify: `docs/ralph_loops/lib/manifest.sh` (the `check_env_var` function, `MANIFEST_ENV_VARS` array, env-var parsing in `parse_manifest`)
- Modify: `e2e/fixtures/manifest/plan_with_manifest.md` (drop `env-vars-required` field)
- Modify: `e2e/fixtures/manifest/plan_partial.md` (drop `env-vars-required` field — but preserve the "partial/malformed" intent; see step note)

**Step 1: Update fixtures**

`e2e/fixtures/manifest/plan_with_manifest.md` — remove the `env-vars-required:\n  - FAKE_TEST_VAR` lines from the front-matter. Final front-matter should be:
```yaml
---
mcp-tools-required:
  - mcp__playwright__browser_navigate
---
```
And remove "and FAKE_TEST_VAR" from the body prose.

`e2e/fixtures/manifest/plan_partial.md` — this fixture exists to trigger `manifest_malformed`. Read it first (it's 4 lines). If the malformed-ness comes from `env-vars-required`, replace the field with a different malformed signal (e.g., unclosed `---`) so the malformed-YAML test still triggers the `manifest_malformed` halt. If malformed-ness is unrelated to env vars, just drop the env line.

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
- In `test_write_halt_secondary_appends_not_overwrites` (around line 66): replace both `env_var_missing` reasons with two different reasons that still exist (e.g., `mcp_unreachable` first, `mcp_tool_not_allowlisted` second) and update assertions.
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
- Schema example (around line 12): remove the `env-vars-required:` block and its sample entries.
- "Both fields are arrays" sentence: change to "The field is an array of strings. It is optional; an empty list is equivalent to omitting the field."
- "Validation (autopilot preflight)" section: remove the `**Env vars.**` subsection (line 39) and the `> Authors: a variable that lives only in .env.local ...` blockquote (line 41).
- "Coherence check (Verifier critic)" bullet: remove the line `- Both directions: same rule for env-vars-required vs process.env.* / os.environ.* / shell ${VAR} references.` (line 48).

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

**Step 3: Run all writing-plans tests**

```bash
python -m pytest e2e/tests/test_writing_plans_manifest_authoring.py e2e/tests/test_writing_plans_anti_review.py -v
```

Expected: all pass.

**Step 4: Run the full e2e test suite**

```bash
python -m pytest e2e/tests/ -v
```

Expected: all pass.

**Step 5: Commit**

```bash
git add skills/writing-plans/SKILL.md skills/writing-plans/references/critique-panel-prompts.md
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

**Step 3: Grep for any leftover references**

```bash
```

Run via Grep tool (not Bash piping):
- Pattern: `env-vars-required|env_var_missing|check_env_var|MANIFEST_ENV_VARS`
- Path: repo root

Expected matches: zero. If any remain, address them before commit.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump version 0.27.1 → 0.27.2"
```

---

## Manual Steps (Post-Automation)

### Reproduction against a real project

After autopilot completes the above, verify the original failure no longer reproduces:

1. Open the `appreciations` repo: `cd ~/software/appreciations`.
2. Confirm it has `DATABASE_URL` in `.env.local` but NOT exported in your shell: `[ -f .env.local ] && grep -q DATABASE_URL .env.local && echo "in file"; echo "${DATABASE_URL:-UNSET}"`.
3. Pick (or create) a small design doc in `~/software/appreciations/docs/designs/`.
4. Run autopilot: `bash ~/software/aligned_cc_skills/docs/ralph_loops/autopilot.sh ~/software/appreciations docs/designs/<doc>.md`.
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
| 5 | Test the change against `appreciations` automatically | Manual reproduction (Post-Automation) | Build an integration test fixture |

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

**Alternatives rejected:**
- **Keep as documentation-only:** doesn't actually document anything users see at autopilot time; just clutters the front-matter.

#### Decision 3: Keep MCP-tool preflight unchanged

**Chose:** This plan touches only the env-var surface. MCP tool validation stays intact.

**Why:** MCP failures are a documented incident class (`mcp__playwright-full__*` ghost namespace, partial allowlists). The check has positive ROI. Bundling an MCP-check reconsideration into this plan expands scope and creates the kind of "while we're in here" sprawl the repo's CLAUDE.md explicitly warns against.

#### Decision 4: Don't revert `c860f1b` (May 9)

**Chose:** Move forward via deletion, not by reverting May 9.

**Why:** `c860f1b` was an honest acknowledgment of an existing bug (the April 30 implementation never matched its own design). Reverting it would restore halt-text that promised users `.env.local` would work — text that didn't reflect actual behavior. The new state (no env-var check at all) makes that text moot. Reverting and re-editing in series adds noise to git history.

#### Decision 5: Manual reproduction against `appreciations`, not an automated integration test

**Chose:** Add a Post-Automation reproduction step rather than building a fixture-based integration test.

**Why:** The reproduction is a one-time confirmation that the original symptom is gone. Building an automated test for it would require fixturing a fake project with a `.env.local` and a manifest, then running the full preflight phase against it — `test_preflight_passes_when_env_vars_required_unset` in Task 1 already covers that case at the phase level. The Post-Automation step adds a real-world smoke test on top.
