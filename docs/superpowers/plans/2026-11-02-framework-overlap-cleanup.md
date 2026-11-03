# Framework Overlap Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 13 frameworks and 3 advisors from the plugin, and change two frameworks so they hand off to each other, as decided on 2026-11-02.

**Architecture:** Follow the James Gurney move (commit `ccdeb8f`): the guard test `e2e/tests/test_advisor_cleanup.py` lists every removed id and name, and scans shipped files for them. Extend its lists first so it fails, then remove the files and every reference until it passes. Generated files (org chart pages, catalogs) are rebuilt by their scripts, never hand-edited.

**Tech Stack:** YAML registries, Markdown prompts, Python 3.14 test suite (pytest), Python generators.

**Spec:** `docs/framework-flows/README.md`, section "Decided (2026-11-02)".

## Global Constraints

- Run tests with the main checkout's venv: `/Users/ericpage/software/aligned_cc_skills/e2e/.venv/bin/python -m pytest <worktree>/e2e/tests -q`. The worktree has no `.venv`; system `python3` is 3.9 and fails to collect.
- Baseline on main before this work: 1952 passed, 180 skipped.
- Never bump the version by hand. The pre-commit hook bumps the patch on skill commits.
- Counts after this plan: **60 advisors, 102 frameworks**.
- Leave `docs/plans/`, `docs/notes/`, `docs/mockups/`, `docs/advisors/`, `docs/superpowers/` and `docs/framework-flows/` alone. They are history and are not scanned.
- Shirin Oreizy and Chris Voss and their six frameworks are already copied to `~/Documents/aligned` (commit `bd2c3b4` there). Do not touch that repo.
- Write plain English in any prose you change: short words, one idea per sentence.

## The ids

Deleted frameworks (gone for good): `5-step-process`, `positioning-canvas`, `landing-page-assembly`, `start-with-experience`, `leadership-pipeline-passages`, `management-level-progression`, `past-year-review`.

Deleted advisor: `lara-hogan` (name "Lara Hogan"; `management-level-progression` was her only framework).

Moved advisors, target `~/Documents/aligned`:
- `shirin-oreizy` ("Shirin Oreizy"): `science-of-design`, `homer-vs-spock`, `cognitive-friction-audit`
- `chris-voss` ("Chris Voss"): `accusation-audit`, `calibrated-questions`, `tactical-empathy-labeling`

## Review Focus

1. A seat on the org chart loses its only framework for a job. Expected: the job gets the replacement named in Task 1's table, or the job is dropped. The seat's coverage label never claims more than is left.
2. Another framework's `follow_on_frameworks`, `default_critic_advisors`, `prompt.md` or `examples.md` still names a removed id. Expected: re-pointed to the replacement in the table, or removed. `test_no_framework_points_at_a_removed_entry` and `test_removed_ids_absent_from_shipped_files` pin this.
3. Another advisor's prompt or registry text sends people to Shirin Oreizy, Chris Voss or Lara Hogan. Expected: the sentence names a remaining advisor who fits, or the name is dropped. `test_removed_names_absent_from_shipped_files` pins this.
4. Someone runs build-measure-learn without having run leap-of-faith-assumptions. Expected: it sends them to leap-of-faith first, and if they decline, it asks for the riskiest assumption in one question. Task 2's test pins this.
5. The README, plugin.json and marketplace.json counts drift from the registries. Expected: 60 and 102 everywhere. `test_readme_freshness.py` pins this.

---

### Task 1: Remove the 13 frameworks and 3 advisors

**Files:**
- Test: `e2e/tests/test_advisor_cleanup.py`, `e2e/tests/test_readme_freshness.py`
- Delete: `frameworks/<id>/` for all 13 framework ids; `advisors/prompts/{lara-hogan,shirin-oreizy,chris-voss}.md`
- Modify: `frameworks/registry.yaml`, `advisors/registry.yaml`, `frameworks/_outliers.json`, `frameworks/README.md`, `advisors/README.md`, `advisors/prompts/{joe-pulizzi,julian-shapiro,julie-dirksen}.md`, `skills/org-chart/seats.yaml`, `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, any `e2e/scenarios` or `e2e/trigger-map.yaml` entry the test finds
- Regenerate: `skills/org-chart/pages/**` with `scripts/generate-org-chart.py`; `docs/advisor-catalog.html` and `docs/framework-catalog.html` with `scripts/generate-catalogs.py`

**Interfaces:**
- Produces: registries without these ids. Task 2 edits `build-measure-learn` and `working-backwards`, which stay.

- [ ] **Step 1: Extend the guard test lists**

In `test_advisor_cleanup.py`:
- `MOVED`: add `"shirin-oreizy": HOME / "Documents" / "aligned"` and `"chris-voss": HOME / "Documents" / "aligned"`.
- `DELETED`: add `"lara-hogan"`.
- `DELETED_FRAMEWORKS`: add the 7 deleted framework ids listed above.
- `MOVED_FRAMEWORKS`: add `"shirin-oreizy": ["science-of-design", "homer-vs-spock", "cognitive-friction-audit"]` and `"chris-voss": ["accusation-audit", "calibrated-questions", "tactical-empathy-labeling"]`.
- `REMOVED_NAMES`: add `"Shirin Oreizy"`, `"Chris Voss"`, `"Lara Hogan"`.

In `test_readme_freshness.py` `GONE_IDS`: add all 16 ids under a comment `# removed or moved to ~/Documents/aligned on 2026-11-02 (framework overlap cleanup)`.

- [ ] **Step 2: Run the guard tests and see them fail**

Run: `.../e2e/.venv/bin/python -m pytest <worktree>/e2e/tests/test_advisor_cleanup.py <worktree>/e2e/tests/test_readme_freshness.py -q`
Expected: FAIL. The ids are still present. `test_moved_advisors_present_in_target` for the two new moves should already PASS.

- [ ] **Step 3: Delete the folders and prompts, and remove their registry entries**

Delete the 13 framework folders and 3 advisor prompts. Remove their entries from both registries and from `frameworks/_outliers.json`.

- [ ] **Step 4: Fix every reference the guard test reports**

Re-run the guard tests and work through each hit. Use these replacements:

| Where | Old | New |
|---|---|---|
| any `follow_on_frameworks` or prompt text | `5-step-process` | `6-step-process` |
| any | `positioning-canvas` | `messaging-distillation` (the next step after positioning) or drop |
| any | `start-with-experience` | `getting-real-cut` |
| any | `leadership-pipeline-passages`, `management-level-progression` | `performance-standards-by-level` |
| any | `landing-page-assembly` | `storybrand-homepage` |
| any | `past-year-review` | drop |
| any | `science-of-design`, `homer-vs-spock`, `cognitive-friction-audit` | `3b-behavioral-design` or drop |
| any | `accusation-audit`, `calibrated-questions`, `tactical-empathy-labeling` | drop (no negotiation framework remains) |
| advisor redirects | Shirin Oreizy | Kristen Berman (behavioral design) |
| advisor redirects | Chris Voss | drop the clause |
| advisor redirects | Lara Hogan | Matt Mochary |

`seats.yaml` jobs:

| Seat (line on main) | Job | Change |
|---|---|---|
| CEO (63) | Look back on the past year | drop the job |
| COO (94) | `also: [5-step-process]` | `also: [6-step-process]` |
| head-of-product (117) | Start from what the customer sees | `framework: working-backwards`, `also: [getting-real-cut]`; drop the job instead if the seat already has working-backwards |
| product-designers (158) | Find the steps where users stall | `framework: 3b-behavioral-design`, no `also` |
| user-researcher (175) | Study how users decide | `framework: 3b-behavioral-design`; drop if the seat already has it |
| engineering-managers (206, 208) | two ladder jobs | one job: "Find the level a manager is working at and plan the jump to the next one", `framework: performance-standards-by-level` |
| product-marketing (301) | Put your positioning on one page | drop the job |
| growth (345, 349) | landing page job; `also_ask` shirin-oreizy | drop the job; drop shirin-oreizy |
| paid-acquisition (391, 393) | landing page; install to first use | `storybrand-homepage`; `3b-behavioral-design` |
| account-executives (474) | Handle a hard call | `framework: teach-tailor-take-control`; drop if already in the seat |
| sales-development-reps (491) | `also_ask: [chris-voss]` | drop |
| partnerships (535) | Negotiate a partner deal | drop the job |
| customer-success-managers (588) | Talk a customer out of canceling | `framework: forever-promise`; drop if already in the seat |

If a seat's coverage field now overstates what is left, lower it and list the seat in your report.

- [ ] **Step 5: Update counts and rebuild generated files**

Set counts to 60 advisors and 102 frameworks in `README.md` (lede, Advisors and Frameworks sections, Quick Start step 4, the 0.33.x changelog line), `plugin.json`, `marketplace.json`, `advisors/README.md` and `frameworks/README.md`. Recount the categories in `frameworks/README.md` from the registry and remove empty ones. Then run `scripts/generate-org-chart.py` (see its `--help` for the author page flag) and `scripts/generate-catalogs.py` with the venv python.

- [ ] **Step 6: Run the full suite**

Run: `.../e2e/.venv/bin/python -m pytest <worktree>/e2e/tests -q`
Expected: all pass, and the skip count stays at 180. A test that pinned a removed advisor or framework (for example in `test_org_chart.py`) is changed to check what is still there, the way `ccdeb8f` changed `test_brad_frost_replaces_designer.py`.

- [ ] **Step 7: Commit**

`git commit -m "refactor: remove overlapping frameworks; move Shirin Oreizy and Chris Voss to ~/Documents/aligned"` with a body that lists the deleted ids, the moved ids and Lara Hogan.

### Task 2: build-measure-learn takes its assumption from leap-of-faith-assumptions

**Files:**
- Create: `e2e/tests/test_framework_handoffs.py`
- Modify: `frameworks/build-measure-learn/prompt.md` (Phase 2, lines 30-41 on main), `frameworks/build-measure-learn/examples.md`, `frameworks/build-measure-learn/anti-examples.md`, `frameworks/registry.yaml` (entries for `build-measure-learn`, `leap-of-faith-assumptions`, `working-backwards`)

**Interfaces:**
- Consumes: the registry after Task 1.

- [ ] **Step 1: Write the failing tests**

```python
def test_build_measure_learn_phase_2_takes_assumption_from_leap_of_faith():
    text = prompt("build-measure-learn")
    phase2 = text.split("### PHASE 2")[1].split("### PHASE 3")[0]
    assert "leap-of-faith-assumptions" in phase2
    assert "/aligned:use-framework leap-of-faith-assumptions" in phase2
    assert "What's the riskiest assumption in your initiative right now?" not in text

def test_leap_of_faith_hands_off_to_build_measure_learn():
    assert "build-measure-learn" in registry()["leap-of-faith-assumptions"]["follow_on_frameworks"]

def test_working_backwards_hands_off_to_getting_real_cut():
    assert "getting-real-cut" in registry()["working-backwards"]["follow_on_frameworks"]
```

`prompt(id)` reads `frameworks/<id>/prompt.md`. `registry()` maps id to entry from `frameworks/registry.yaml`.

- [ ] **Step 2: Run them and see them fail**

Run: `.../e2e/.venv/bin/python -m pytest <worktree>/e2e/tests/test_framework_handoffs.py -q`
Expected: FAIL on the Phase 2 test and on any missing follow-on.

- [ ] **Step 3: Rewrite Phase 2 and the registry entries**

Phase 2 keeps the WAIT point and Eric Ries's voice. It asks whether they have run leap-of-faith-assumptions. If yes, it asks them to paste the riskiest assumption it produced, and confirms it in one line. If no, it recommends running `/aligned:use-framework leap-of-faith-assumptions` first. If they would rather not, it asks for the one riskiest assumption in a single question, without its own value and growth sorting. Phases 1 and 3-6 stay as they are. Update the examples and anti-examples so their Phase 2 matches. Add `leap-of-faith-assumptions` output to build-measure-learn's `helpful_documents`, and add the two follow-on links if missing.

- [ ] **Step 4: Run the full suite**

Expected: all pass.

- [ ] **Step 5: Commit**

`git commit -m "feat: build-measure-learn takes its riskiest assumption from leap-of-faith-assumptions"`
