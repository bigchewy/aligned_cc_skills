---
mcp-tools-required: []
---

# Framework Runner Refactor and Brainstorming Mode Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Consolidate brainstorming's `business` + `authoring` modes into a single `authoring` mode that dispatches via shared `framework-runner` / `advisor-runner` and extended multi-entity contextual-recommendation; introduce a `deliverable_type` taxonomy across all 154 frameworks so the authoring mode can specialize its post-engine flow per output kind; rename `planning` → `roadmap`; introduce 4-mode always-ask routing with task-vocabulary picker labels.

**Source Design Doc:** `docs/plans/2026-05-09-framework-runner-refactor-design.md`

**Mockups:** `docs/mockups/framework-runner-refactor.html`, `docs/mockups/2026-05-17-brainstorming-mode-naming-and-routing.html`

**Architecture:** Extract `use-framework` Steps 4-5 and `use-advisor` Step 4 into `skills/_shared/framework-runner.md` and `skills/_shared/advisor-runner.md` so the brainstorming `authoring` mode can dispatch either an auto-selected framework or a structured Q&A with a topic advisor in The Architect's proxy seat. Engine selection runs through an extended `contextual-recommendation.md` that scores frameworks and advisors together. The brainstorming router collapses from 5 modes to 4 (Software / Authoring / Research / Roadmap) and always asks the user to confirm the auto-detected mode (with one skip for explicit `--mode` arg or same-mode subsequent invocation in the same conversation). A new `deliverable_type` registry field (`content` | `decision` | `plan` | `analysis`) drives Phase 3 post-engine dispatch — selecting one of four templates and a critique critic pool that can be overridden per framework via the `default_critic_advisors` field.

**Tech Stack:** Markdown skill files, YAML registries (`frameworks/registry.yaml`, `advisors/registry.yaml`), Python migration script (`tools/sync_framework_frontmatter.py`), pytest e2e tests (`e2e/tests/`), eval scenarios (`e2e/scenarios/use-skill/`).

**Scope corrections to design doc:**
- Design references "147 frameworks." Actual count is **154** (verified via `grep -c "^  - id:" frameworks/registry.yaml`). Plan uses 154 throughout.
- Design Step 0 precondition "Resolve KB-033 (empty `purpose` fields)" — **already resolved 2026-05-11**. `grep -c 'purpose: ""'` returns 0. Step 0 reduces to the name-field hygiene audit only.

---

## Prerequisites

> Complete these steps manually before starting Task 1.

*(None — all preconditions are automatable and live in Task 1.)*

---

## Task Ordering Constraints

Several tasks edit the same files; do not parallelize:

- **`e2e/tests/test_brainstorming_files.py`** — Tasks 15, 17, 17b, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27 all edit this file. Run in numerical order.
- **`skills/brainstorming/SKILL.md`** — Tasks 15, 20, 21 edit this file. Run in numerical order.
- **`frameworks/registry.yaml`** — Tasks 1, 6, 7, 8, 9, 10 edit this file. Run in numerical order.
- **`e2e/tests/test_registry_schemas.py`** — Tasks 1, 6, 7, 8, 9, 10, 13 edit this file. Run in numerical order.
- **`skills/_shared/contextual-recommendation.md`** — Task 14 only.
- **`e2e/trigger-map.yaml`** — Tasks 15, 24, 25 edit this file. Run in numerical order. (Tasks 2 and 4 do NOT touch trigger-map; their trigger entries are deferred to Task 25 because the target scenarios don't exist until then.)
- **`e2e/eval-surface.yaml`** — Tasks 2, 4, 17, 24 edit this file. Run in numerical order.
- **`skills/brainstorming/modes/authoring.md`** — Tasks 17 (overwrite) and 17b (verify). Task 17b's tests are scoped to the file post-Task-17.

---

## Tasks

### ✅ Task 1: Clean `name`-field hygiene in `frameworks/registry.yaml`

Some registry entries embed purpose-like multi-sentence phrasing in the `name:` field (e.g., `5-components-positioning` line 14: `name: "your 5 Components of Positioning framework. This is the methodology from \"Obviously Awesome\""`). Multi-entity scoring will surface `name` to users; long quoted strings degrade the picker. Cap each `name` at ≤60 characters or add a `display_name` field used by the router.

**Files:**
- Modify: `frameworks/registry.yaml` (entries with `name` length > 60 chars)
- Test: `e2e/tests/test_registry_schemas.py` (add `test_name_field_is_concise`)

**Step 1: Write the failing test**

Add to `e2e/tests/test_registry_schemas.py`:

```python
def test_name_field_is_concise():
    """Framework name fields must be concise (≤60 chars) — they surface to users in pickers."""
    import yaml
    with open("frameworks/registry.yaml") as f:
        data = yaml.safe_load(f)
    long_names = [
        (e["id"], len(e["name"]))
        for e in data["frameworks"]
        if len(e["name"]) > 60
    ]
    assert not long_names, (
        f"{len(long_names)} entries have name > 60 chars: {long_names[:5]}"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_registry_schemas.py::test_name_field_is_concise -v`
Expected: FAIL — `5-components-positioning` (92 chars), `5-step-process` (113 chars), plus ~31 other offenders (~33 total). Confirm the exact list via the Python one-liner in Step 3.

**Step 3: Find all offenders**

Run: `python -c "import yaml; d=yaml.safe_load(open('frameworks/registry.yaml')); [print(e['id'], len(e['name']), repr(e['name'])) for e in d['frameworks'] if len(e['name'])>60]"`

For each offender, write a concise display name (≤60 chars). Example transformations:
- `"your 5 Components of Positioning framework. This is the methodology from \"Obviously Awesome\""` → `"5 Components of Positioning"`
- `"the 5-Step Process to help them achieve what they want in life by systematically addressing problems and evolving"` → `"5-Step Process"`

**Step 4: Edit each offender**

Use Edit tool one entry at a time. Preserve every other field unchanged.

**Step 5: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_name_field_is_concise -v`
Expected: PASS

**Step 6: Run full registry schema suite to confirm no regressions**

Run: `pytest e2e/tests/test_registry_schemas.py -v`
Expected: all pass.

**Step 7: Commit**

```bash
git add frameworks/registry.yaml e2e/tests/test_registry_schemas.py
git commit -m "fix(frameworks): cap registry name fields at 60 chars for picker discoverability"
```

---

### ✅ Task 2: Create `skills/_shared/framework-runner.md` with intake-gate parameter

Extract `use-framework/SKILL.md` Steps 4-5 (lines 55-74), Voice rules (76-79), and Composability (81-88) into a shared runner. Add a configurable `intake_gate_mode` parameter — `strict` (gate on missing `required_documents`, prompt user) or `advisory` (note missing, proceed). Default `advisory` preserves existing behavior; brainstorming wrapper will pass `strict`.

**Files:**
- Create: `skills/_shared/framework-runner.md`
- Modify: `e2e/eval-surface.yaml` (add the new runner to the LLM-behavior surface list)
- Modify: `e2e/trigger-map.yaml` (add a trigger entry pointing at `framework-runner-extraction.yaml`, which will be created in Task 25)
- Test: `e2e/tests/test_shared_runners.py` (new)

**Step 1: Write the failing test**

Create `e2e/tests/test_shared_runners.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_framework_runner_exists():
    assert (REPO / "skills/_shared/framework-runner.md").is_file()


def test_framework_runner_has_intake_gate_parameter():
    text = read("skills/_shared/framework-runner.md")
    assert "intake_gate_mode" in text, "missing intake_gate_mode parameter"
    assert "strict" in text and "advisory" in text, "missing intake gate modes"
    assert "default" in text.lower() and "advisory" in text, "default mode not documented"


def test_framework_runner_carries_runner_protocol():
    text = read("skills/_shared/framework-runner.md")
    assert "Load Framework Content" in text or "load the framework content" in text.lower()
    assert "WAIT" in text, "missing WAIT discipline rule"
    assert "examples.md" in text and "anti-examples.md" in text
    assert "Composability" in text, "missing Composability rule"


def test_framework_runner_strict_mode_prompts_on_missing_required_documents():
    text = read("skills/_shared/framework-runner.md")
    assert "required_documents" in text
    assert "strict" in text
    # Strict mode must describe the prompt-user flow
    assert "prompt" in text.lower() or "ask" in text.lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_shared_runners.py -v`
Expected: all 4 tests FAIL — file doesn't exist.

**Step 3: Create `skills/_shared/framework-runner.md`**

Content (verbatim shape):

```markdown
# Framework Runner

Shared runner protocol for executing a matched framework. Invoked by `skills/use-framework/SKILL.md` (top-level invocation) and by `skills/brainstorming/modes/authoring.md` (engine selection via contextual-recommendation).

## Configuration

The calling skill passes:
- **Matched framework path:** absolute path to the framework folder containing `prompt.md` / `examples.md` / `anti-examples.md`
- **`intake_gate_mode`:** `strict` or `advisory` (default `advisory`)

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** if any check fails:

- **Matched framework path:** must be an absolute path AND must be a directory AND must contain at least `prompt.md`. If absent, stop and tell the caller "Framework runner cannot proceed: matched framework path `<path>` is missing or has no prompt.md."
- **`intake_gate_mode`:** must be exactly `strict` or `advisory`. If unset, default to `advisory`. If set to any other value, stop and tell the caller "Framework runner cannot proceed: invalid `intake_gate_mode=<value>`."

These checks fail closed — the runner refuses to start with invalid inputs rather than silently degrading.

## Step 1: Load Framework Content

Read three files from the matched framework's directory:

1. `prompt.md` — the phase-by-phase guide (required)
2. `examples.md` — calibration examples per phase (read if exists, skip silently if missing)
3. `anti-examples.md` — failure modes to avoid (read if exists, skip silently if missing)

If `prompt.md` is missing or empty, report the error and stop. Do not attempt to run a framework without its prompt.

## Step 2: Apply the Intake Gate

If the framework's registry entry (or its `prompt.md` YAML frontmatter) lists `required_documents`:

- **`advisory` mode (default):** Note the missing documents to the user as a one-line observation; proceed with Phase 1 regardless. Preserves existing `use-framework` behavior.
- **`strict` mode:** Pause and prompt the user with the missing-document list. Options the user can pick from:
  - Provide a path to each missing document
  - Mark missing documents as N/A and proceed (the framework will run without that input)
  - Downgrade to advisory for this session

Strict mode is used when the framework is part of a larger brainstorming flow that expects each gate to be honored before continuing.

`helpful_documents` are noted but never gate execution regardless of mode.

## Step 3: Run the Framework

1. Inject all loaded content as operating instructions.
2. Begin Phase 1 immediately with the framework's scripted opening.
3. Complete each phase fully before advancing to the next.
4. **WAIT** for the user's response at each marked pause point — do not continue until they respond.
5. Use examples from `examples.md` to calibrate responses.
6. Actively avoid patterns described in `anti-examples.md`.

A phase is complete when: (a) the scripted content for that phase has been delivered, (b) the user has responded to all prompts within the phase, and (c) any reflection or summary the phase calls for has been provided.

## Voice

- If an advisor persona is active (via `skills/_shared/advisor-runner.md` or `/aligned:use-advisor`): deliver the framework in that advisor's voice.
- If no advisor is active: follow the framework prompt as-is — it already names an advisor in its opening line, so adopt that advisor's voice as written.

## Composability

When invoked alongside an active advisor persona (advisor-runner running):

1. The advisor sets the voice
2. The framework sets the structure
3. Begin Phase 1 immediately in the advisor's voice
4. No intermediate acknowledgment — straight into the framework

On framework completion, control returns to the caller (advisor mid-conversation, or the brainstorming authoring mode for post-engine dispatch).

## Avoid These Mistakes

- **Skipping phases** — Complete every phase in order.
- **Rushing past pause points** — When the framework says to wait for a response, stop. Do not continue with the next question or phase in the same message.
- **Combining multiple frameworks** — Run one framework per session.
- **Improvising structure** — Follow the framework's phases exactly as written.
- **Ignoring anti-examples** — Treat anti-example patterns as hard constraints.
```

**Step 4: Update `e2e/eval-surface.yaml`**

Read the file (22 lines). Under the appropriate `patterns:` list (the LLM-behavior surface for prompt construction — Note: the key is `patterns`, not `paths`), add:

```yaml
  - skills/_shared/framework-runner.md
```

Add a new test asserting the runner is in the surface:

```python
def test_framework_runner_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/framework-runner.md" in text, (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )
```

Run: `pytest e2e/tests/test_shared_runners.py::test_framework_runner_is_in_eval_surface -v` — expected PASS.

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_shared_runners.py e2e/tests/test_eval_surface_patterns.py -v`
Expected: all PASS.

> **Trigger-map deferral (mandatory):** The corresponding trigger-map entry for `skills/_shared/framework-runner.md` MUST be deferred to Task 25 — the trigger points at `scenarios/use-skill/framework-runner-extraction.yaml`, which Task 25 creates. The project's `test_trigger_map_paths.py` asserts every scenario path resolves to an existing file, so wiring the trigger before the scenario exists would break the test. Do NOT stage `e2e/trigger-map.yaml` in this task's commit.

**Step 6: Commit**

```bash
git add skills/_shared/framework-runner.md e2e/tests/test_shared_runners.py e2e/eval-surface.yaml
git commit -m "feat(_shared): extract framework-runner.md with configurable intake gate and eval surface entry"
```

---

### ✅ Task 3: Refactor `skills/use-framework/SKILL.md` to invoke shared runner

Replace Steps 4-5 (lines 55-74), Voice section (76-79), and Composability section (81-88) with one section invoking `skills/_shared/framework-runner.md` (intake=`advisory`, preserving current behavior).

**Files:**
- Modify: `skills/use-framework/SKILL.md` (replace L55-88 with shared-runner invocation)
- Test: `e2e/tests/test_shared_runners.py` (add invocation assertion)

**Step 1: Write the failing assertion**

Add to `e2e/tests/test_shared_runners.py`:

```python
def test_use_framework_invokes_shared_runner():
    text = read("skills/use-framework/SKILL.md")
    assert "_shared/framework-runner.md" in text, "use-framework must invoke shared runner"
    assert "intake_gate_mode" in text and "advisory" in text, (
        "use-framework must pass intake_gate_mode=advisory to preserve behavior"
    )
    # Anti-regression: inline runner protocol should be removed from use-framework
    assert "Inject all loaded content as operating instructions" not in text, (
        "runner protocol must live in _shared/framework-runner.md, not here"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_shared_runners.py::test_use_framework_invokes_shared_runner -v`
Expected: FAIL — current file still contains the inline runner.

**Step 3: Replace Steps 4-5 + Voice + Composability**

Use Edit tool. Replace lines 55-88 (the `## Step 4: Load Framework Content` through `## Composability with /aligned:use-advisor` section). The new content:

```markdown
## Step 4: Run the Framework

After matching, hand off to the shared runner.

Read `skills/_shared/framework-runner.md` and invoke it with:
- **Matched framework path:** the directory of the matched framework (from Step 3)
- **`intake_gate_mode`:** `advisory` (preserves existing top-level invocation behavior — `required_documents` are noted to the user but execution proceeds)

The runner handles loading content, applying the intake gate, running phases with WAIT discipline, voice rules, and composability with `/aligned:use-advisor`.
```

Leave Steps 1-3 and "Avoid These Mistakes" intact. The "Avoid These Mistakes" section can stay where it was (after old Composability) — it's caller-facing advice, not runner protocol.

**Step 4: Run tests to verify backward-compat**

Run: `pytest e2e/tests/test_shared_runners.py -v`
Expected: all tests including the new `test_use_framework_invokes_shared_runner` PASS.

Run: `pytest e2e/tests/test_skill_cross_references.py -v` to confirm no stale path references.

**Step 5: Commit**

```bash
git add skills/use-framework/SKILL.md e2e/tests/test_shared_runners.py
git commit -m "refactor(use-framework): delegate runner protocol to _shared/framework-runner.md"
```

---

### ✅ Task 4: Create `skills/_shared/advisor-runner.md`

Extract `use-advisor/SKILL.md` Step 4 (persona adoption, L53-61), Switching/Ending Persona (L63-67), Composability with use-framework (L69-75), and Avoid Mistakes (L77-83).

**Files:**
- Create: `skills/_shared/advisor-runner.md`
- Modify: `e2e/eval-surface.yaml` (add the new runner)
- Modify: `e2e/trigger-map.yaml` (add a trigger entry; same caveat as Task 2 about scenario-file ordering)
- Test: `e2e/tests/test_shared_runners.py` (extend)

> **Behavior-change acknowledgment:** This task introduces `greeting_mode=silent` as a new code path. Top-level `/aligned:use-advisor` invocations pass `greeting_mode=full` to preserve the existing brief greeting + Core Frameworks listing. Silent mode is reserved for inter-runner composability (framework-runner invoking advisor-runner for voice setup). Task 5's test asserts `greeting_mode=full` is passed by the top-level caller — change here is additive, not breaking.

**Step 1: Write the failing test**

Add to `e2e/tests/test_shared_runners.py`:

```python
def test_advisor_runner_exists():
    assert (REPO / "skills/_shared/advisor-runner.md").is_file()


def test_advisor_runner_carries_persona_protocol():
    text = read("skills/_shared/advisor-runner.md")
    assert "Adopt the Persona" in text or "adopt the persona" in text.lower()
    assert "Core Frameworks" in text, "missing Core Frameworks reference"
    assert "Switching" in text and "Ending" in text, "missing persona lifecycle rules"
    assert "Composability" in text, "missing Composability rule"
    # Bidirectional dispatch hook
    assert "framework-runner.md" in text, (
        "advisor runner should reference framework-runner.md for mid-conversation dispatch"
    )
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_shared_runners.py -v`
Expected: the two new tests FAIL.

**Step 3: Create `skills/_shared/advisor-runner.md`**

```markdown
# Advisor Runner

Shared runner protocol for adopting and maintaining an advisor persona. Invoked by `skills/use-advisor/SKILL.md` (top-level invocation), by `skills/brainstorming/modes/authoring.md` (engine fallback when no framework matches), and by any caller that wants to run an advisor-led conversation.

## Configuration

The calling skill passes:
- **Matched advisor path:** path to the advisor prompt file (resolved by the caller via registry lookup or direct path)
- **`greeting_mode`:** `full` (default) emits a brief greeting and lists Core Frameworks; `silent` skips the greeting (used when composed inside a framework-runner dispatch, see Composability)

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** if any check fails:

- **Matched advisor path:** must be a file that exists. If absent, stop and tell the caller "Advisor runner cannot proceed: matched advisor path `<path>` does not exist."
- **`greeting_mode`:** must be exactly `full` or `silent`. If unset, default to `full`. If set to any other value, stop and tell the caller "Advisor runner cannot proceed: invalid `greeting_mode=<value>`."

## Step 1: Adopt the Persona

When a match is found:

1. Read the full advisor prompt file
2. Adopt the persona for the rest of the conversation — speak as this advisor, use their voice, tone, and patterns
3. If `greeting_mode=full`: open with a brief greeting in the advisor's voice (2-3 sentences max), reference the advisor's available frameworks naturally by reading the "Core Frameworks" section. If no "Core Frameworks" section exists, skip the listing — do not fabricate frameworks. Make clear that freeform conversation is equally welcome.
4. If `greeting_mode=silent`: skip the greeting entirely; the caller (e.g., framework-runner) takes over immediately.
5. Wait for the user's response (unless `greeting_mode=silent`).

## Switching or Ending a Persona

- To switch advisors, the user invokes `/aligned:use-advisor` again with a different name. Drop the previous persona entirely and adopt the new one.
- To end a persona without switching, the user says something like "drop the persona" or "back to normal." Acknowledge briefly and return to default behavior.
- Do not blend personas. Only one advisor voice is active at a time.

## Composability

When an advisor wants to start a framework mid-conversation (e.g., the user asks for it, or the advisor recommends one):

1. Read `skills/_shared/framework-runner.md` and invoke it with the chosen framework's path and `intake_gate_mode=advisory`
2. The advisor's voice carries through the framework
3. On framework completion, control returns here — the advisor resumes free conversation

When invoked by another caller that has already loaded a framework (e.g., `framework-runner` dispatched here for voice setup):

- Use `greeting_mode=silent`
- Adopt the voice; the framework's Phase 1 follows immediately in the advisor's voice
- No intermediate acknowledgment

## Avoid These Mistakes

- **Breaking character mid-conversation** — Stay in the advisor's voice for all responses until the user switches or exits.
- **Editorializing outside the persona** — Do not add "As Claude, I should note..." disclaimers.
- **Mixing advisor voices** — If the user mentions another advisor, do not adopt their patterns. Stay in the current persona.
- **Fabricating frameworks** — Only mention frameworks listed in the file's "Core Frameworks" section.
```

**Step 4: Update `e2e/eval-surface.yaml`**

Same procedure as Task 2 Step 4: add `skills/_shared/advisor-runner.md` to the `patterns:` list in `eval-surface.yaml` (Note: the key is `patterns`, not `paths`).

Add a test assertion:

```python
def test_advisor_runner_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/advisor-runner.md" in text
```

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_shared_runners.py e2e/tests/test_eval_surface_patterns.py -v`
Expected: all PASS.

> **Trigger-map deferral (mandatory):** Same as Task 2 — the corresponding trigger-map entry for `skills/_shared/advisor-runner.md` (pointing at `scenarios/use-skill/use-framework-backward-compat.yaml`) MUST be deferred to Task 25. Do NOT stage `e2e/trigger-map.yaml` in this task's commit.

**Step 6: Commit**

```bash
git add skills/_shared/advisor-runner.md e2e/tests/test_shared_runners.py e2e/eval-surface.yaml
git commit -m "feat(_shared): extract advisor-runner.md with configurable greeting mode and eval surface entry"
```

---

### ✅ Task 5: Refactor `skills/use-advisor/SKILL.md` to invoke shared runner

Replace Step 4 (L53-61), Switching section (L63-67), Composability (L69-75) with one section invoking `_shared/advisor-runner.md`.

**Files:**
- Modify: `skills/use-advisor/SKILL.md`
- Test: `e2e/tests/test_shared_runners.py` (extend)

**Step 1: Write the failing assertion**

Add to `e2e/tests/test_shared_runners.py`:

```python
def test_use_advisor_invokes_shared_runner():
    text = read("skills/use-advisor/SKILL.md")
    assert "_shared/advisor-runner.md" in text, "use-advisor must invoke shared runner"
    # Behavior preservation: top-level invocation must explicitly pass greeting_mode=full,
    # since silent is the new code path introduced by this refactor.
    assert "greeting_mode" in text and "full" in text, (
        "use-advisor must pass greeting_mode=full to preserve top-level behavior"
    )
    # Behavior preservation: top-level invocation MUST NOT pass greeting_mode=silent,
    # which would suppress the brief greeting and Core Frameworks listing that
    # users expect from /aligned:use-advisor.
    assert "greeting_mode=silent" not in text and "greeting_mode: silent" not in text, (
        "top-level use-advisor must not pass silent — that path is reserved for runner composition"
    )
    # Anti-regression: inline persona protocol should be removed
    assert "Read the full advisor prompt file" not in text, (
        "persona adoption protocol must live in _shared/advisor-runner.md"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_shared_runners.py::test_use_advisor_invokes_shared_runner -v`
Expected: FAIL.

**Step 3: Replace Step 4 + Switching + Composability**

Use Edit tool. Replace lines 53-75. New content:

```markdown
## Step 4: Run the Advisor

After matching, hand off to the shared runner.

Read `skills/_shared/advisor-runner.md` and invoke it with:
- **Matched advisor path:** the prompt file for the matched advisor (from Step 3)
- **`greeting_mode`:** `full` (preserves existing top-level invocation behavior — brief greeting + Core Frameworks listing)

The runner handles persona adoption, voice rules, the switching/ending lifecycle, and composability with `/aligned:use-framework`.
```

Keep "Avoid These Mistakes" if it carries any advice not already in the runner (currently identical — move it into the runner, drop here). Verify by re-reading both files after edit.

**Step 4: Run tests**

Run: `pytest e2e/tests/test_shared_runners.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add skills/use-advisor/SKILL.md e2e/tests/test_shared_runners.py
git commit -m "refactor(use-advisor): delegate persona protocol to _shared/advisor-runner.md"
```

---

### ✅ Task 6: Add `deliverable_type` taxonomy doc + validate against 10-15 ambiguous frameworks

The `deliverable_type` field is one of four values: `content`, `decision`, `plan`, `analysis`. Document the taxonomy at the top of `frameworks/registry.yaml` and validate the primary-tag rule by classifying 10-15 frameworks that produce multiple deliverable types before bulk-classifying.

**Files:**
- Modify: `frameworks/registry.yaml` (add schema doc block at top)
- Create: `docs/notes/2026-05-17-deliverable-type-validation.md` (one-shot validation notes)

**Step 1: Write the failing test**

Add to `e2e/tests/test_registry_schemas.py`:

```python
def test_registry_documents_deliverable_type_taxonomy():
    with open("frameworks/registry.yaml") as f:
        head = f.read(2000)
    for tag in ["content", "decision", "plan", "analysis"]:
        assert tag in head, f"deliverable_type taxonomy must document tag: {tag}"
    assert "deliverable_type" in head, "missing taxonomy doc block"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_registry_schemas.py::test_registry_documents_deliverable_type_taxonomy -v`
Expected: FAIL.

**Step 3: Edit `frameworks/registry.yaml` to add schema doc block**

After the existing two header comment lines and before `frameworks:`, insert:

```yaml
#
# Schema: each entry MUST have id, name, advisor, purpose, category, domains, use_when.
# Optional: required_documents, helpful_documents, deliverable_type, default_critic_advisors,
#           follow_on_frameworks.
#
# deliverable_type taxonomy (mandatory for all entries; pick the closing-phase output type):
#   content   — artifact humans consume (positioning canvas, landing page copy, exercise sequence)
#   decision  — a choice made (RCA verdict, fear-setting outcome, the-work turnaround)
#   plan      — sequenced actions (6-step output, kernel-of-good-strategy, OKR set)
#   analysis  — structured understanding of a situation (jobs-to-be-done, finding-the-crux)
#
# Tiebreaker: the closing phase's output determines the type, not intermediate phases.
#
```

**Step 4: Validate the primary-tag rule against 10-15 ambiguous frameworks**

Pick these candidates (multiple-deliverable shape) and document the classification:
- `5-components-positioning` — closing output = canvas → **content**
- `the-work` — closing output = turnaround statement → **decision**
- `fear-setting` — closing output = define/prevent/repair grid → **decision**
- `kernel-of-good-strategy` — closing output = guiding policy + coherent actions → **plan**
- `jobs-to-be-done` — closing output = job map → **analysis**
- `accusation-audit` — closing output = pre-empt script → **content**
- `insane-honesty` — closing output = honest message → **content**
- `okr-setting` — closing output = OKR set → **plan**
- `finding-the-crux` — closing output = crux diagnosis → **analysis**
- `landing-page-assembly` — closing output = page copy → **content**
- `competitive-analysis` (if present) → **analysis**
- `100-percent-responsibility` — closing output = ownership statement → **decision**
- `5-step-process` — closing output = action plan → **plan**

Write the validation outcomes to `docs/notes/2026-05-17-deliverable-type-validation.md` (one paragraph: any frameworks where the primary tag was ambiguous, plus any taxonomy refinements suggested by the exercise).

**Step 5: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_registry_documents_deliverable_type_taxonomy -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add frameworks/registry.yaml docs/notes/2026-05-17-deliverable-type-validation.md e2e/tests/test_registry_schemas.py
git commit -m "docs(frameworks): document deliverable_type taxonomy and validate against 13 ambiguous frameworks"
```

---

### ✅ Task 7: Classify frameworks batch 1 — first 50 entries (alphabetical by `id`)

Add `deliverable_type` field to the first 50 framework entries in `frameworks/registry.yaml`. For each entry, judge based on the closing-phase output rule documented in Task 6.

**Files:**
- Modify: `frameworks/registry.yaml`
- Test: `e2e/tests/test_registry_schemas.py` (add `test_first_50_frameworks_have_deliverable_type`)

**Step 1: Write the failing test**

```python
def test_at_least_50_frameworks_have_deliverable_type():
    import yaml
    valid = {"content", "decision", "plan", "analysis"}
    with open("frameworks/registry.yaml") as f:
        data = yaml.safe_load(f)
    typed = [e for e in data["frameworks"] if "deliverable_type" in e]
    assert len(typed) >= 50, f"only {len(typed)} entries have deliverable_type yet"
    for e in typed[:50]:
        assert e["deliverable_type"] in valid, (
            f"{e['id']} has invalid deliverable_type: {e['deliverable_type']}"
        )
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_registry_schemas.py::test_at_least_50_frameworks_have_deliverable_type -v`
Expected: FAIL.

**Step 3: Classify and edit batch 1**

Open `frameworks/registry.yaml`. For the first 50 entries (alphabetical by `id`), add `deliverable_type:` after `use_when:` (preserving optional `required_documents` and `helpful_documents` below it). Use the closing-phase output rule. Document any judgment calls inline as comments if the call is non-obvious.

Tip: read each entry's `purpose` and `use_when` to inform the classification. If still uncertain, read `frameworks/<id>/prompt.md` to inspect the closing phase.

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_at_least_50_frameworks_have_deliverable_type -v`
Expected: PASS.

Also run full schema suite to confirm no YAML parse errors:
Run: `pytest e2e/tests/test_registry_schemas.py -v`

**Step 5: Commit**

```bash
git add frameworks/registry.yaml e2e/tests/test_registry_schemas.py
git commit -m "feat(frameworks): classify deliverable_type for first 50 registry entries (batch 1/3)"
```

---

### ✅ Task 8: Classify frameworks batch 2 — entries 51–100

Continue classification for entries 51–100 (alphabetical by `id`).

**Files:**
- Modify: `frameworks/registry.yaml`
- Test: `e2e/tests/test_registry_schemas.py` (tighten threshold)

**Step 1: Update the threshold assertion**

Edit `test_at_least_50_frameworks_have_deliverable_type` to `test_at_least_100_frameworks_have_deliverable_type` (and update `>= 50` to `>= 100`). This is the failing test for batch 2.

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_registry_schemas.py::test_at_least_100_frameworks_have_deliverable_type -v`
Expected: FAIL.

**Step 3: Classify entries 51–100**

Same procedure as Task 7.

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_at_least_100_frameworks_have_deliverable_type -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add frameworks/registry.yaml e2e/tests/test_registry_schemas.py
git commit -m "feat(frameworks): classify deliverable_type for entries 51-100 (batch 2/3)"
```

---

### ✅ Task 9: Classify frameworks batch 3 — remaining ~54 entries

Complete classification for the remaining ~54 entries. After this task, every framework MUST have `deliverable_type`.

**Files:**
- Modify: `frameworks/registry.yaml`
- Test: `e2e/tests/test_registry_schemas.py` (final assertion)

**Step 1: Replace the threshold assertion with a 100%-coverage test**

Remove `test_at_least_100_frameworks_have_deliverable_type` and replace with:

```python
def test_every_framework_has_valid_deliverable_type():
    import yaml
    valid = {"content", "decision", "plan", "analysis"}
    with open("frameworks/registry.yaml") as f:
        data = yaml.safe_load(f)
    missing = [e["id"] for e in data["frameworks"] if "deliverable_type" not in e]
    assert not missing, f"{len(missing)} frameworks missing deliverable_type: {missing[:5]}"
    bad = [
        (e["id"], e["deliverable_type"])
        for e in data["frameworks"]
        if e["deliverable_type"] not in valid
    ]
    assert not bad, f"invalid deliverable_type values: {bad[:5]}"
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_registry_schemas.py::test_every_framework_has_valid_deliverable_type -v`
Expected: FAIL.

**Step 3: Classify the remaining ~54 entries**

Same procedure.

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_every_framework_has_valid_deliverable_type -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add frameworks/registry.yaml e2e/tests/test_registry_schemas.py
git commit -m "feat(frameworks): complete deliverable_type classification for all 154 entries (batch 3/3)"
```

---

### ✅ Task 10: Add optional `default_critic_advisors` + `follow_on_frameworks` where applicable

Add the two optional fields to entries with clear domain fits. Not every framework needs them; only add where there is concrete signal. Examples:
- `5-components-positioning` → `default_critic_advisors: [april-dunford, steve-krug]`, `follow_on_frameworks: [strategic-narrative, landing-page-assembly]`
- `fear-setting` → `default_critic_advisors: [tim-ferriss, diana-chapman]`

**Files:**
- Modify: `frameworks/registry.yaml`
- Test: `e2e/tests/test_registry_schemas.py` (validates field shapes when present)

**Step 1: Write the failing test**

```python
def test_optional_fields_have_correct_shape_when_present():
    import yaml
    with open("frameworks/registry.yaml") as f:
        data = yaml.safe_load(f)
    with open("advisors/registry.yaml") as f:
        adv = yaml.safe_load(f)
    advisor_ids = {a["id"] for a in adv["advisors"]}
    framework_ids = {e["id"] for e in data["frameworks"]}

    typed_count = 0
    for e in data["frameworks"]:
        if "default_critic_advisors" in e:
            assert isinstance(e["default_critic_advisors"], list), e["id"]
            for aid in e["default_critic_advisors"]:
                assert aid in advisor_ids, f"{e['id']} references unknown advisor: {aid}"
            typed_count += 1
        if "follow_on_frameworks" in e:
            assert isinstance(e["follow_on_frameworks"], list), e["id"]
            for fid in e["follow_on_frameworks"]:
                assert fid in framework_ids, f"{e['id']} references unknown framework: {fid}"

    # Anti-inflation: assert at least 5 entries got the optional metadata (otherwise the field
    # adds no signal and Decision 4 was wrong)
    assert typed_count >= 5, "fewer than 5 entries got default_critic_advisors — field adds no signal"
```

**Step 2: Run test to verify it fails**

Expected: FAIL — no entries have these fields yet.

**Step 3: Edit registry**

Add `default_critic_advisors` and `follow_on_frameworks` to clear-fit entries only (aim for 8–15 entries — quality over coverage; missing the field is intentional for frameworks without strong follow-on signal).

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add frameworks/registry.yaml e2e/tests/test_registry_schemas.py
git commit -m "feat(frameworks): add default_critic_advisors and follow_on_frameworks where applicable"
```

---

### ✅ Task 11: Create `tools/sync_framework_frontmatter.py` migration script with unit tests

Idempotent migration script that walks every framework folder, reads the registry entry's `deliverable_type`, and mirrors it into the framework's `prompt.md` YAML frontmatter. Handles missing frontmatter (creates one), existing frontmatter without the field (adds it), and existing field with stale value (updates it). Failure cases: missing `prompt.md` (logs warning, continues); missing registry entry for an existing folder (logs warning, continues).

**Files:**
- Create: `tools/sync_framework_frontmatter.py`
- Create: `tools/test_sync_framework_frontmatter.py`
- Test: `tools/test_sync_framework_frontmatter.py` (unit tests for the script)

**Step 1: Write the failing tests**

Create `tools/test_sync_framework_frontmatter.py`:

```python
import textwrap
from pathlib import Path
import pytest
import yaml

from sync_framework_frontmatter import sync_framework_frontmatter, parse_frontmatter, write_frontmatter


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_adds_field_when_frontmatter_missing(tmp_path):
    fw = tmp_path / "frameworks" / "alpha"
    write(fw / "prompt.md", "You are Foo, guiding...\n\nPhase 1...\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: alpha\n    deliverable_type: content\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, body = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "content"
    assert "You are Foo" in body


def test_updates_field_when_value_stale(tmp_path):
    fw = tmp_path / "frameworks" / "beta"
    write(fw / "prompt.md", "---\ndeliverable_type: plan\nrequired_documents: []\n---\nbody\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: beta\n    deliverable_type: decision\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")

    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "decision"
    assert fm.get("required_documents") == [], "must preserve sibling fields"


def test_idempotent(tmp_path):
    fw = tmp_path / "frameworks" / "gamma"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: gamma\n    deliverable_type: analysis\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    first = (fw / "prompt.md").read_text()
    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    second = (fw / "prompt.md").read_text()
    assert first == second, "script must be idempotent"


def test_missing_prompt_logs_warning_and_continues(tmp_path, caplog):
    (tmp_path / "frameworks" / "delta").mkdir(parents=True)
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks:\n  - id: delta\n    deliverable_type: content\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert "missing prompt.md" in caplog.text.lower()


def test_missing_registry_entry_logs_warning_and_continues(tmp_path, caplog):
    fw = tmp_path / "frameworks" / "epsilon"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, "frameworks: []\n")

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    assert "no registry entry" in caplog.text.lower()


def test_handles_quoted_name_field_with_embedded_quotes(tmp_path):
    """Regression test for entries like 5-components-positioning whose name contains escaped quotes."""
    fw = tmp_path / "frameworks" / "5-components-positioning"
    write(fw / "prompt.md", "body\n")
    registry = tmp_path / "registry.yaml"
    write(registry, textwrap.dedent('''\
        frameworks:
          - id: 5-components-positioning
            name: "5 Components of Positioning"
            deliverable_type: content
        '''))

    sync_framework_frontmatter(registry, tmp_path / "frameworks")
    fm, _ = parse_frontmatter((fw / "prompt.md").read_text())
    assert fm["deliverable_type"] == "content"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tools/test_sync_framework_frontmatter.py -v`
Expected: all FAIL — script doesn't exist.

**Step 3: Implement `tools/sync_framework_frontmatter.py`**

```python
"""Mirror deliverable_type from frameworks/registry.yaml into each framework's prompt.md YAML frontmatter.

Idempotent. Safe to re-run. Logs warnings for missing prompt.md or missing registry entries.

Usage:
    python tools/sync_framework_frontmatter.py [--registry PATH] [--frameworks-dir PATH]
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import yaml

LOG = logging.getLogger("sync_framework_frontmatter")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def write_frontmatter(fm: dict, body: str) -> str:
    fm_text = yaml.safe_dump(fm, sort_keys=False).rstrip()
    return f"---\n{fm_text}\n---\n{body}"


def sync_framework_frontmatter(registry_path: Path, frameworks_dir: Path) -> None:
    registry = yaml.safe_load(Path(registry_path).read_text()) or {}
    entries_by_id = {e["id"]: e for e in registry.get("frameworks", [])}
    seen_ids = set()

    for folder in sorted(Path(frameworks_dir).iterdir()):
        if not folder.is_dir():
            continue
        fid = folder.name
        entry = entries_by_id.get(fid)
        if entry is None:
            LOG.warning("no registry entry for framework folder: %s", fid)
            continue
        seen_ids.add(fid)
        if "deliverable_type" not in entry:
            LOG.warning("registry entry %s missing deliverable_type — skipping", fid)
            continue

        prompt = folder / "prompt.md"
        if not prompt.exists():
            LOG.warning("missing prompt.md for framework: %s", fid)
            continue

        text = prompt.read_text()
        fm, body = parse_frontmatter(text)
        if fm.get("deliverable_type") == entry["deliverable_type"]:
            continue  # idempotent: nothing to change
        fm["deliverable_type"] = entry["deliverable_type"]
        prompt.write_text(write_frontmatter(fm, body))
        LOG.info("updated %s with deliverable_type=%s", fid, entry["deliverable_type"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("frameworks/registry.yaml"))
    parser.add_argument("--frameworks-dir", type=Path, default=Path("frameworks"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sync_framework_frontmatter(args.registry, args.frameworks_dir)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tools/test_sync_framework_frontmatter.py -v`
Expected: all 6 tests PASS.

**Step 5: Commit**

```bash
git add tools/sync_framework_frontmatter.py tools/test_sync_framework_frontmatter.py
git commit -m "feat(tools): add idempotent sync_framework_frontmatter.py with unit tests"
```

---

### ✅ Task 12: Run sync script on the real repo + commit prompt.md changes

Apply the migration to all 154 framework `prompt.md` files.

**Files:**
- Modify: every `frameworks/*/prompt.md` (up to 154 files)

**Step 1: Dry-run the script by hand on one file**

Pick `frameworks/the-work/prompt.md`. Check its current frontmatter. Confirm it does NOT have `deliverable_type`.

**Step 2: Run the script**

Run: `python tools/sync_framework_frontmatter.py`
Expected output: ~154 INFO lines, zero WARNINGS (if any folder lacks a registry entry or any `prompt.md`, the warning is benign — record the count).

**Step 3: Spot-check 5 files**

Read `frameworks/the-work/prompt.md`, `frameworks/5-components-positioning/prompt.md`, `frameworks/fear-setting/prompt.md`, `frameworks/kernel-of-good-strategy/prompt.md`, `frameworks/jobs-to-be-done/prompt.md`. Each must have `deliverable_type: <value>` in YAML frontmatter, value matching the registry classification.

**Step 4: Run script again to confirm idempotency**

Run: `python tools/sync_framework_frontmatter.py`
Expected output: zero INFO updates (all entries already in sync).

Run: `git diff --stat` — expected zero file changes after second run.

**Step 5: Commit**

```bash
git add frameworks/
git commit -m "chore(frameworks): mirror deliverable_type from registry to prompt.md frontmatter (154 files)"
```

---

### ✅ Task 13: Add drift-detection test (`test_deliverable_type_frontmatter_matches_registry`)

A pytest assertion that registry and prompt.md frontmatter stay in sync. Catches manual edits that bypass the sync script.

**Files:**
- Modify: `e2e/tests/test_registry_schemas.py`

**Step 1: Write the failing test**

Add:

```python
def test_deliverable_type_frontmatter_matches_registry():
    """Every framework prompt.md frontmatter must mirror its registry deliverable_type."""
    import yaml, re
    from pathlib import Path

    with open("frameworks/registry.yaml") as f:
        data = yaml.safe_load(f)

    fm_re = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    mismatches = []
    for e in data["frameworks"]:
        prompt = Path(f"frameworks/{e['id']}/prompt.md")
        if not prompt.exists():
            continue
        m = fm_re.match(prompt.read_text())
        fm = yaml.safe_load(m.group(1)) if m else {}
        registry_value = e["deliverable_type"]
        prompt_value = (fm or {}).get("deliverable_type")
        if prompt_value != registry_value:
            mismatches.append((e["id"], registry_value, prompt_value))

    assert not mismatches, (
        f"{len(mismatches)} drift(s): "
        + "\n".join(f"  {i}: registry={r} prompt={p}" for i, r, p in mismatches[:5])
        + "\nRun: python tools/sync_framework_frontmatter.py"
    )
```

**Step 2: Run test to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::test_deliverable_type_frontmatter_matches_registry -v`
Expected: PASS (sync script just ran in Task 12).

> Note: This is a retroactive test — implementation already exists (the sync script + Task 12 commit). The test asserts the post-Task-12 state. No code change needed.

**Step 3: Commit**

```bash
git add e2e/tests/test_registry_schemas.py
git commit -m "test(frameworks): assert deliverable_type stays in sync between registry and prompt.md"
```

---

### ✅ Task 13b: Add design-mandated error-path tests for shared runners

Per the design doc's `## Testing Strategy` (L206-212) and CLAUDE.md's TDD rule, every error path must have a test. Round 1 critique flagged five error-path tests as missing. Three of those test runner specs (which exist by this point); the remaining two test `modes/authoring.md` and run in Task 17b (after Task 17 rewrites that file).

**Files:**
- Modify: `e2e/tests/test_shared_runners.py` (add 3 runner error-path tests)

**Step 1: Write the failing tests**

Add to `e2e/tests/test_shared_runners.py`:

```python
def test_framework_runner_documents_empty_prompt_error_path():
    """Design L207: framework runner with empty prompt.md."""
    text = read("skills/_shared/framework-runner.md")
    # "missing or empty" is the Step 1 contract sentence
    assert "empty" in text.lower(), "framework-runner must handle empty prompt.md as error"
    assert "report the error and stop" in text or "STOP" in text


def test_framework_runner_documents_broken_advisor_reference_path():
    """Design L208: framework with broken advisor field reference."""
    text = read("skills/_shared/framework-runner.md")
    # The runner must describe what happens when a framework references a non-existent advisor
    assert "advisor" in text.lower()
    # Either: the runner documents falling back to generic facilitator,
    # OR: the runner documents stopping with an error.
    # Both are acceptable contracts; assert at least one is present.
    assert (
        "fallback" in text.lower()
        or "generic facilitator" in text.lower()
        or "broken" in text.lower()
        or "missing advisor" in text.lower()
    ), "framework-runner must document broken-advisor-reference handling"


def test_advisor_runner_documents_missing_prompt_file_path():
    """Advisor runner must STOP when matched advisor path doesn't exist."""
    text = read("skills/_shared/advisor-runner.md")
    assert "STOP" in text or "does not exist" in text
    assert "Configuration Validation" in text, (
        "advisor-runner must have a fail-closed validation section"
    )
```

**Step 2: Run tests to identify gaps**

Run: `pytest e2e/tests/test_shared_runners.py -k "documents" -v`
Expected: some FAIL — addressing them is part of this task.

**Step 3: Add missing error-path documentation to the relevant spec files**

For each failing test:
- If `framework-runner.md` is missing empty-prompt handling, expand the "If `prompt.md` is missing or empty..." sentence to be explicit.
- If `framework-runner.md` is missing broken-advisor-reference handling, add a sub-bullet under Voice that documents the fallback to "generic facilitator voice" with a Decision Log entry.
- If `advisor-runner.md` lacks STOP language, the Configuration Validation section (added in Task 4) covers it — verify it's present.

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_shared_runners.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add e2e/tests/test_shared_runners.py skills/_shared/framework-runner.md skills/_shared/advisor-runner.md
git commit -m "test(shared-runners): add design-mandated error-path tests for runner specs"
```

---

### ✅ Task 14: Extend `_shared/contextual-recommendation.md` with multi-entity scoring

Add `framework-or-advisor` entity type. Scoring runs Stage 1 + Stage 2 over both registries; results are merged and ranked. Auto-select threshold treats top entry as canonical; shortlist mode presents a unified list when 2+ entries score similarly.

**Files:**
- Modify: `skills/_shared/contextual-recommendation.md`
- Test: `e2e/tests/test_contextual_recommendation.py` (new)

**Step 1: Write the failing test**

Create `e2e/tests/test_contextual_recommendation.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_contextual_recommendation_documents_multi_entity_mode():
    text = read("skills/_shared/contextual-recommendation.md")
    assert "framework-or-advisor" in text, "missing multi-entity entity type"
    assert "merge" in text.lower() and "rank" in text.lower(), (
        "multi-entity mode must describe merge + rank behavior"
    )


def test_multi_entity_mode_documents_tiebreaker_against_purpose():
    text = read("skills/_shared/contextual-recommendation.md")
    # When framework and advisor score similarly, framework wins for actionable tasks;
    # advisor wins for exploration. Document the rule.
    assert "tiebreaker" in text.lower() or "tie-breaker" in text.lower()


def test_multi_entity_mode_handles_zero_signal():
    text = read("skills/_shared/contextual-recommendation.md")
    # Multi-entity mode with empty registries (or zero overlap) must degrade to Path 4
    assert "Path 4" in text  # already present, but now also referenced from multi-entity section
```

**Step 2: Run tests to verify they fail**

Expected: FAIL — multi-entity content not yet added.

**Step 3: Edit `_shared/contextual-recommendation.md`**

Insert a new section after `## Stage 2: Semantic Ranking` and before `## Confidence Test and Presentation`:

```markdown
## Multi-Entity Mode (entity type: `framework-or-advisor`)

When the calling skill passes entity type `framework-or-advisor`, run Stages 1-2 against **both** registries and merge the results into a single ranked list.

### Field mapping (merged)

| Scoring role | Source (framework) | Source (advisor) |
|---|---|---|
| Primary match | `use_when` | `best_for` |
| Domain overlap | `domains` | `domains` |
| Disambiguation | `purpose`, `category` | `evaluation_expertise`, `summary` |

Each entry carries its entity type into the merged list (so the caller knows whether to dispatch the framework runner or the advisor runner).

### Tiebreaker (framework vs advisor at similar confidence)

When a framework and an advisor score similarly in Stage 2:
1. **Actionable task signal** — if the task contains a clear deliverable ("build a positioning brief", "run an RCA"), prefer the framework. Frameworks structure work that has a known shape.
2. **Exploratory task signal** — if the task contains "I'm not sure what I need" or "help me think about X", prefer the advisor. Advisors handle ambiguity better than framework prompts.
3. **No clear signal** — present a shortlist that mixes both.

### Zero-signal handling

If no framework scores AND no advisor scores (both registries empty or zero domain overlap after Stage 1), degrade to Path 4 (No Context Available) per the top of this file.
```

Also extend the existing **Configuration** block at the top to document the new entity type:

Change `Entity type: \`advisor\` or \`framework\`` → `Entity type: \`advisor\`, \`framework\`, or \`framework-or-advisor\``.

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_contextual_recommendation.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/_shared/contextual-recommendation.md e2e/tests/test_contextual_recommendation.py
git commit -m "feat(_shared): add framework-or-advisor multi-entity scoring mode to contextual-recommendation"
```

---

### ✅ Task 15: Rename planning → roadmap (files + all string references) + post-commit grep gate

Rename the planning mode to roadmap across the repo. This is a single atomic commit because the test suite (`test_brainstorming_files.py`) and trigger-map paths cross-reference these names.

**Files:**
- Rename via `git mv`:
  - `skills/brainstorming/modes/planning.md` → `skills/brainstorming/modes/roadmap.md`
  - `skills/brainstorming/planning-critique-checklist.md` → `skills/brainstorming/roadmap-critique-checklist.md`
  - `skills/brainstorming/references/templates/planning-template.html` → `skills/brainstorming/references/templates/roadmap-template.html`
- Modify (string updates inside files):
  - `skills/brainstorming/SKILL.md` (L18, L79, L83, L91, L100, L102, L119, L133, L157, L173, plus frontmatter L3, Overview L11-18, mode list L21, refusal-handling L105)
  - `skills/_shared/critique-panel-orchestration.md` (L18, L60, L104 — Mode enum line)
  - `skills/brainstorming/references/brainstorm-components.md` (L74, L76-83 template table)
  - `skills/brainstorming/references/shared-rules.md` (L19 — enumerated mode list)
  - `skills/brainstorming/references/visualization-protocol.md` (L1)
  - `skills/brainstorming/references/spawn-brief-template.md` (L12 — add Roadmap to enum; L34 explanatory text)
  - `skills/kickstart/SKILL.md` (L196 — 4-mode listing)
- Modify (test updates):
  - `e2e/tests/test_brainstorming_files.py` (`test_planning_mode_file_structure`, `test_planning_mode_handles_cagan_absence`, and ~3 other functions referencing `planning`)

**Step 1: Write/update failing tests**

In `e2e/tests/test_brainstorming_files.py`:
- Rename `test_planning_mode_file_structure` → `test_roadmap_mode_file_structure` and update `read("skills/brainstorming/modes/planning.md")` → `read("skills/brainstorming/modes/roadmap.md")`, and update the `planning-critique-checklist.md` reference to `roadmap-critique-checklist.md`.
- Rename `test_planning_mode_handles_cagan_absence` → `test_roadmap_mode_handles_cagan_absence`.
- Add a new test:

```python
def test_planning_mode_file_removed_after_rename():
    """Planning → Roadmap rename must be complete; no planning mode file remains."""
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    assert not (REPO / "skills/brainstorming/modes/planning.md").exists(), \
        "modes/planning.md must be renamed to modes/roadmap.md"
    assert not (REPO / "skills/brainstorming/planning-critique-checklist.md").exists()
    assert not (REPO / "skills/brainstorming/references/templates/planning-template.html").exists()
    assert (REPO / "skills/brainstorming/modes/roadmap.md").exists()


def test_planning_string_references_purged_from_brainstorming_skill():
    """Post-rename grep gate: `planning` should appear ≤2 times in skills/brainstorming/
    (only intentional references to /aligned:writing-plans or historical CHANGELOG context)."""
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    hits = 0
    for p in (REPO / "skills/brainstorming").rglob("*"):
        if not p.is_file() or p.suffix not in {".md", ".html", ".yaml"}:
            continue
        for line in p.read_text().splitlines():
            if "planning" in line.lower() and "writing-plans" not in line:
                hits += 1
    assert hits <= 2, f"too many residual 'planning' references: {hits} (expected ≤2)"
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_brainstorming_files.py -v`
Expected: at least the renamed tests + the new tests FAIL.

**Step 3: Rename files via `git mv`**

```bash
git mv skills/brainstorming/modes/planning.md skills/brainstorming/modes/roadmap.md
git mv skills/brainstorming/planning-critique-checklist.md skills/brainstorming/roadmap-critique-checklist.md
git mv skills/brainstorming/references/templates/planning-template.html skills/brainstorming/references/templates/roadmap-template.html
```

**Step 4: Update string references**

For each file in the Modify list above, use Grep first to find every `planning` / `Planning` / `planning-template` / `planning-critique-checklist` / `modes/planning.md` reference. Replace with the `roadmap` form. Do not rewrite occurrences of `/aligned:writing-plans` or "implementation planning" (those reference a different skill).

Within `skills/brainstorming/SKILL.md`, also update:
- L3 frontmatter description (replace "multi-feature planning" → "multi-feature roadmap")
- L11-18 Overview list (planning bullet → roadmap bullet)
- L21 ("...five modes" → "...four modes" — but final 4-mode collapse happens in Task 22; here just update the planning→roadmap label)
- L91 (5-way question) — leave the 5-way phrasing for now; Task 22 collapses to 4-way
- L105 ("...routes to Business mode" — leave the Business reference; Task 22 changes it to Authoring)

The Task 22 work will overwrite some of these. Keep edits in this task minimal: rename `Planning` → `Roadmap` everywhere, but do NOT touch the Business references.

For `spawn-brief-template.md` L12: replace `{Software | Authoring | Research}` → `{Software | Authoring | Research | Roadmap}`. Update L34 prose to mention that Roadmap can spawn nested Roadmap sessions.

For `critique-panel-orchestration.md` L104: replace `software | business | research | authoring | planning` → `software | business | research | authoring | roadmap` (Business stays until Task 22).

**Step 5: Run tests**

Run: `pytest e2e/tests/test_brainstorming_files.py -v`
Expected: the new rename-related tests PASS. Other tests (still expecting `planning`) may fail — those are addressed by the previous step-4 string updates.

Run: `pytest e2e/tests/test_trigger_map_paths.py -v` to confirm no broken paths.
Run: `pytest e2e/tests/test_skill_cross_references.py -v`.

**Step 6: Post-commit grep verify gate**

The pytest `test_planning_string_references_purged_from_brainstorming_skill` (added in Step 1) covers this assertion programmatically. Run it now as a final check:

Run: `pytest e2e/tests/test_brainstorming_files.py::test_planning_string_references_purged_from_brainstorming_skill -v`
Expected: PASS (≤2 residual hits).

If FAIL, inspect the offenders by running (Grep tool inside Python, not Bash):

```python
import os, re
for root, _, files in os.walk("skills/brainstorming"):
    for name in files:
        if name.endswith((".md", ".html", ".yaml")):
            p = os.path.join(root, name)
            for i, line in enumerate(open(p), 1):
                if "planning" in line.lower() and "writing-plans" not in line:
                    print(f"{p}:{i}: {line.rstrip()}")
```

Fix the offenders, re-run the test.

**Step 7: Commit**

```bash
git add \
  skills/brainstorming/modes/roadmap.md \
  skills/brainstorming/roadmap-critique-checklist.md \
  skills/brainstorming/references/templates/roadmap-template.html \
  skills/brainstorming/SKILL.md \
  skills/_shared/critique-panel-orchestration.md \
  skills/brainstorming/references/brainstorm-components.md \
  skills/brainstorming/references/shared-rules.md \
  skills/brainstorming/references/visualization-protocol.md \
  skills/brainstorming/references/spawn-brief-template.md \
  skills/kickstart/SKILL.md \
  e2e/tests/test_brainstorming_files.py
git commit -m "refactor(brainstorming): rename planning mode to roadmap (3 files + string sweep across 8 docs)"
```

The renamed files (planning.md / planning-critique-checklist.md / planning-template.html) are tracked as renames automatically by `git mv` in Step 3.

---

### ✅ Task 16: Add Q&A parity marker comment to `modes/software.md`

Mark the Architect-as-proxy dispatch template (L80-98) as the stable surface that `modes/authoring.md` will duplicate. The marker is a single comment above the dispatch template; non-functional but visible to a reader.

**Files:**
- Modify: `skills/brainstorming/modes/software.md`

**Step 1: Write the failing test**

In a new file `e2e/tests/test_qa_pattern_parity.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_software_mode_has_parity_marker():
    text = read("skills/brainstorming/modes/software.md")
    assert "PARITY MARKER" in text or "DUPLICATED TO" in text or "DUPLICATED FROM/TO" in text, (
        "software.md Q&A dispatch template must carry a parity marker comment"
    )
    assert "modes/authoring.md" in text, "marker must point at the sibling duplication site"
```

**Step 2: Run test to verify it fails**

Expected: FAIL.

**Step 3: Insert the marker comment**

Above the line `**Architect as proxy** (Q&A-phase technical questions):` in `modes/software.md` (around L76), insert:

```markdown
<!-- PARITY MARKER: DUPLICATED TO skills/brainstorming/modes/authoring.md (no-framework fallback Q&A).
     The Architect-as-proxy dispatch template (the sub-agent prompt body below) is the stable surface
     for the parity test (e2e/tests/test_qa_pattern_parity.py). Sync substantive changes to both files
     or document the intentional divergence in this marker. See decision 4 in
     docs/plans/2026-05-09-framework-runner-refactor-design.md. -->
```

**Step 4: Run test to verify it passes**

Run: `pytest e2e/tests/test_qa_pattern_parity.py::test_software_mode_has_parity_marker -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/software.md e2e/tests/test_qa_pattern_parity.py
git commit -m "docs(brainstorming): add parity marker on software.md Q&A dispatch template"
```

---

### ✅ Task 17: Create new `skills/brainstorming/modes/authoring.md` (delete-then-recreate)

Overwrite the existing `modes/authoring.md` (369-line 7-phase content arrangement) with a new file that dispatches via shared runners and falls back to structured Q&A duplicated from `modes/software.md`. Phases:
- Phase 1: Engine selection (invokes `_shared/contextual-recommendation.md`, entity=`framework-or-advisor`)
- Phase 2: Engine execution (one of four ladder paths)
- Phase 3: Post-engine dispatch by `deliverable_type`
- Then: shared visualization, critique panel, commit, handoff

The Q&A pattern is **duplicated from software.md L22-134** with the parity marker pointing back.

**Files:**
- Modify (overwrite): `skills/brainstorming/modes/authoring.md`
- Test: `e2e/tests/test_brainstorming_files.py::test_authoring_mode_file_structure` (rewrite for new shape) + `e2e/tests/test_qa_pattern_parity.py` (extend)

**Step 1: Write the failing test**

Rewrite `test_authoring_mode_file_structure` in `e2e/tests/test_brainstorming_files.py`:

```python
def test_authoring_mode_file_structure():
    """New authoring.md dispatches via shared runners with no-framework Q&A fallback."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert text.splitlines()[0] == "<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->"
    # 3-phase dispatch shape
    assert "Phase 1: Engine selection" in text
    assert "Phase 2: Engine execution" in text
    assert "Phase 3:" in text and "deliverable_type" in text
    # Engine selection invokes contextual-recommendation
    assert "_shared/contextual-recommendation.md" in text
    assert "framework-or-advisor" in text
    # Shared runners
    assert "_shared/framework-runner.md" in text
    assert "intake_gate_mode" in text and "strict" in text
    assert "_shared/advisor-runner.md" in text
    # Fallback ladder
    assert "Wise Eric" in text, "missing last-resort default advisor"
    assert "structured Q&A" in text or "Architect" in text and "proxy" in text
    # Duplication marker
    assert "PARITY MARKER" in text or "DUPLICATED FROM" in text
    assert "modes/software.md" in text
    # Critique panel config
    assert "authoring-critique-checklist.md" in text
    assert "deliverable_type" in text  # post-engine dispatch
    # default_critic_advisors must be consumed by Phase 3 (the field added in Task 10
    # is load-bearing here, not just metadata).
    assert "default_critic_advisors" in text, (
        "Phase 3 must consume default_critic_advisors from the registry"
    )
    # Path 4 handoff must be documented so contextual-recommendation does not
    # double-prompt the user.
    assert "Path 4" in text, (
        "authoring mode must document how it interacts with contextual-recommendation's Path 4"
    )
```

Add to `e2e/tests/test_qa_pattern_parity.py`:

```python
def test_authoring_mode_dispatch_template_matches_software():
    sw = read("skills/brainstorming/modes/software.md")
    au = read("skills/brainstorming/modes/authoring.md")
    # The Architect-as-proxy dispatch sub-agent prompt body should appear in both files.
    # Stable anchor: the role-override sentence.
    anchor = "Your normal constraint of 'do not propose alternatives' is suspended"
    assert anchor in sw, "anchor sentence missing from software.md"
    assert anchor in au, (
        "authoring.md's no-framework Q&A must use the same Architect-as-proxy dispatch as software.md"
    )
```

**Step 2: Run tests to verify they fail**

Run: `pytest e2e/tests/test_brainstorming_files.py::test_authoring_mode_file_structure e2e/tests/test_qa_pattern_parity.py -v`
Expected: FAIL.

**Step 3: Overwrite `modes/authoring.md`**

The new file outline (write the complete content):

```markdown
<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->

# Authoring Mode

A wrapper around either a registered framework or a structured Q&A with a topic advisor in The Architect's proxy seat. Produces a design doc that feeds `/aligned:writing-plans`.

## Disambiguation rules

- **Authoring vs Software:** if the deliverable is content (deck, memo, brief, positioning, curriculum), Authoring. If it's code that runs, Software.
- **Authoring vs Research:** Authoring produces an arrangement (sequenced document); Research produces an evidence map. Authoring may invoke a Research sub-flow but is not Research.
- **Authoring vs Roadmap:** Roadmap produces a portfolio + spawn list (multi-feature). Authoring produces a single document.

## The Process

### Phase 1: Engine selection

Read `skills/_shared/contextual-recommendation.md` and invoke it with:
- **Entity type:** `framework-or-advisor`
- **Registries:** `frameworks/registry.yaml`, `advisors/registry.yaml`
- **Task context:** the user's topic (1-3 sentence summary). **MUST be non-empty.** This is required so contextual-recommendation does not enter Path 4 (No Context Available) and ask the user a second AskUserQuestion immediately after the router asked for mode confirmation in SKILL.md Step 1. If the user's topic is empty (rare — the router should have refused to dispatch), construct one from the prior user message.

Outcomes (the fallback ladder):

1. **Auto-select fires on a framework** → Phase 2a (framework runner, intake=strict).
2. **Auto-select fires on an advisor (no framework match)** → Phase 2b (structured Q&A with the matched advisor in The Architect's proxy seat).
3. **Shortlist mode** → present the unified shortlist; user picks an entry; route to 2a or 2b based on entity type.
4. **No high-confidence match (Stage 1 returns candidates but none auto-select)** → Phase 2c (structured Q&A; top-scoring topic advisor in proxy seat).
5. **Zero candidates** (both registries returned nothing after domain filter — extremely rare given 154 frameworks + 70 advisors) → Phase 2d (structured Q&A with Wise Eric in proxy seat).

Path 4 of `contextual-recommendation.md` (the "what problem are you working on?" prompt) is reserved for top-level skill invocations where the user invoked `/aligned:use-advisor` with no args and no conversation context. Authoring mode always has a topic; Path 4 never fires from here.

**Project scan failure handling:** If `/tmp/brainstorm-context-{topic}/project-scan.md` is missing or empty (scan failed or hadn't completed when Phase 1 ran), proceed without scan context; engine selection runs on topic alone; user is notified ("Scan unavailable — proceeding with topic-only engine selection."). Phase 2 may re-check for the scan and incorporate it when available.

### Phase 2a: Framework runner (engine = framework)

Read `skills/_shared/framework-runner.md` and invoke it with:
- **Matched framework path:** from Phase 1
- **`intake_gate_mode`:** `strict` (brainstorming wrapper gates on `required_documents`)

On framework completion, the runner returns control here. Proceed to Phase 3.

### Phase 2b/2c/2d: Structured Q&A with topic advisor in Architect's proxy seat

The Q&A pattern is duplicated from `modes/software.md` (L22-134). See the parity marker below.

For Phase 2b (matched advisor) — use the matched advisor's prompt in the Architect-as-proxy dispatch.
For Phase 2c (top-scoring advisor) — same, with the top-scoring advisor.
For Phase 2d (Wise Eric default) — same, with `advisors/prompts/wise-eric.md`.

<!-- PARITY MARKER: DUPLICATED FROM skills/brainstorming/modes/software.md (Q&A pattern, L22-134).
     The Architect-as-proxy dispatch template (the sub-agent prompt body below) is the stable surface
     for the parity test (e2e/tests/test_qa_pattern_parity.py). Sync substantive changes to both files
     or document the intentional divergence in this marker. See decision 4 in
     docs/plans/2026-05-09-framework-runner-refactor-design.md. -->

**Understanding the idea:**

(The full Q&A protocol block duplicated from software.md L22-134, lightly adapted: replace "Architect" with "{topic_advisor}" wherever the proxy seat is filled, but keep the role-override sentence ("Your normal constraint of 'do not propose alternatives' is suspended — the user has explicitly delegated technical decision-making to you...") verbatim because the parity test asserts on it. Mockup-generator dispatch stays — content work also benefits from comparison mockups for layout/sequencing decisions.)

[... full Q&A block copied verbatim from modes/software.md L22-134 ...]

**Presenting the design:**
The design doc is the deliverable. Save to `{worktree}/docs/plans/YYYY-MM-DD-{topic}-design.md`.

### Phase 3: Post-engine dispatch by `deliverable_type`

Read the engine's `deliverable_type` from the framework registry. If the engine was a Q&A fallback (no framework), prompt the user to pick `content | decision | plan | analysis` once (a single AskUserQuestion in the design-doc-finalization step — this is NOT mid-flow human review; it is the deliverable-type tag that the user must own as part of authoring).

Dispatch table:

| deliverable_type | Template path | Critique checklist sections (passed to orchestrator) | Default critic pool (when registry's `default_critic_advisors` is unset) | Handoff prompt |
|---|---|---|---|---|
| content | `references/templates/authoring-template.html` | `["universal", "content"]` | brand-voice advisors + topic advisor | "Run /aligned:writing-plans against this doc to produce an implementation plan." |
| decision | `references/templates/authoring-decision-template.html` | `["universal", "decision"]` | The Skeptic + topic advisor | "Document the decision; close any open questions." |
| plan | `references/templates/authoring-plan-template.html` | `["universal", "plan"]` | strategy advisors (Rumelt, Christensen, Ries) | "Run /aligned:writing-plans." |
| analysis | `references/templates/authoring-analysis-template.html` | `["universal", "analysis"]` | topic advisors + The Skeptic | "Save analysis; surface follow-on actions." |

**Critic pool override:** Before falling back to the default critic pool for the deliverable_type row, check the engine's `default_critic_advisors` field in `frameworks/registry.yaml`. If present and non-empty, use those advisor IDs as the critic pool instead of the defaults. (This is the consumption site for the field added in Task 10 — it is what makes the field load-bearing.)

**Interaction with `critique-panel-orchestration.md`:** That file expects ONE critique checklist with one `criteria-mapping` per calling mode file. The authoring mode supplies the `authoring-critique-checklist.md` file (single checklist) and passes the list of section IDs from the Critique-checklist-sections column above. The orchestrator runs only the listed sections, skipping inapplicable ones. The `authoring-critique-checklist.md` (Task 18) is authored so sections are independently runnable.

**Registry drift fallback:** If the registry entry is missing `deliverable_type` (manual edit drifted from script), fall back to the `content` template + a generic critique pool and append a one-line drift note to the design doc's Decision Log. Suggest running `python tools/sync_framework_frontmatter.py` to re-sync.

## After the Design

### Documentation

Save the design doc to `{worktree}/docs/plans/YYYY-MM-DD-{topic}-design.md`. Use the deliverable-type-specific template chosen in Phase 3.

### Visualization

Read `{base-directory}/references/visualization-protocol.md` and follow it.

### Widgets

Per `references/brainstorm-components.md` widget table.

### Critique Panel

Read `{base-directory}/../_shared/critique-panel-orchestration.md`. Config:

- Fact-check mode: `division-of-labor`
- Criteria assignment: `yes` (per-section, conditioned on `deliverable_type`)
- Checklist: `authoring-critique-checklist.md`

## Key Principles

- The wrapper owns scaffolding (project scan, intake gates, visualization, critique, commit, handoff). The engine (framework or Q&A) owns the conversation.
- Always-ask routing means the user has confirmed they want Authoring before this file runs.
- Fallback ladder paths 2b/2c/2d are structured Q&A — never free exploration.
- Wise Eric is the last-resort default proxy. His prompt handles "I'm not sure what I need" gracefully.
```

(Where the new file says `[... full Q&A block copied verbatim from modes/software.md L22-134 ...]`, paste the actual Q&A content from `skills/brainstorming/modes/software.md` lines 22-134 into the new authoring.md, with `Architect` references re-pointed to the topic advisor's proxy as documented above. The role-override sentence stays verbatim.)

**Step 4: Add `modes/authoring.md` to `e2e/eval-surface.yaml`**

The new authoring mode is a fresh LLM-behavior surface (it dispatches engines and constructs prompts). Add it to the `patterns:` list in `e2e/eval-surface.yaml` now so any eval-audit runs between this task and Task 24 see the new surface. Add a test assertion:

```python
def test_authoring_mode_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/brainstorming/modes/authoring.md" in text
```

Run: `pytest e2e/tests/test_brainstorming_files.py::test_authoring_mode_is_in_eval_surface -v` — expected PASS.

> The `modes/business.md` entry stays in `eval-surface.yaml` until Task 24 (cutover commit) — both modes coexist in the surface during the migration window.

**Step 5: Run tests to verify they pass**

Run: `pytest e2e/tests/test_brainstorming_files.py::test_authoring_mode_file_structure e2e/tests/test_qa_pattern_parity.py e2e/tests/test_eval_surface_patterns.py -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add skills/brainstorming/modes/authoring.md e2e/tests/test_brainstorming_files.py e2e/tests/test_qa_pattern_parity.py e2e/eval-surface.yaml
git commit -m "refactor(brainstorming): rewrite authoring.md as engine-dispatch + no-framework Q&A fallback"
```

---

### ✅ Task 17b: Add design-mandated error-path tests for the new authoring.md

Two error-path tests from the design doc's `## Testing Strategy` apply specifically to the new `modes/authoring.md` written in Task 17 — they couldn't run earlier because the file's old shape was incompatible.

**Files:**
- Modify: `e2e/tests/test_brainstorming_files.py` (add 2 authoring-mode error-path tests)

**Step 1: Write the failing tests**

Add to `e2e/tests/test_brainstorming_files.py`:

```python
def test_authoring_mode_documents_missing_deliverable_type_fallback():
    """Phase 3 must define behavior when registry drift loses deliverable_type."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert "missing" in text.lower() and "deliverable_type" in text
    assert "content" in text.lower(), "fallback to content template must be documented"
    assert "sync_framework_frontmatter" in text or "re-sync" in text.lower(), (
        "drift remediation hint must point at the sync script"
    )


def test_authoring_mode_documents_project_scan_failure():
    """Design L211: authoring mode with project scan failure."""
    text = read("skills/brainstorming/modes/authoring.md")
    assert "scan" in text.lower()
    # Acceptable phrasings: "scan fails", "scan failure", "scan unavailable", "without scan"
    assert any(s in text.lower() for s in [
        "scan fail", "scan returns empty", "without scan", "scan unavailable",
    ]), "missing project-scan-failure handling"
```

**Step 2: Run tests to verify they pass**

The Task 17 spec includes both the deliverable_type drift fallback paragraph (Phase 3) and the project-scan-failure paragraph (Phase 1). Run:

Run: `pytest e2e/tests/test_brainstorming_files.py -k "documents_missing_deliverable_type or documents_project_scan_failure" -v`
Expected: PASS.

If FAIL: return to Task 17 and confirm the spec includes the exact phrases the tests check for. Amend `modes/authoring.md` and re-run.

**Step 3: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py
git commit -m "test(brainstorming): add error-path tests for authoring mode deliverable_type drift and scan failure"
```

---

### ✅ Task 18: Create new `skills/brainstorming/authoring-critique-checklist.md`

Overwrite the existing checklist with one that has conditional sections per `deliverable_type`.

**Files:**
- Modify (overwrite): `skills/brainstorming/authoring-critique-checklist.md`
- Test: `e2e/tests/test_brainstorming_files.py` (add `test_authoring_critique_checklist_has_conditional_sections`)

**Step 1: Write the failing test**

```python
def test_authoring_critique_checklist_has_conditional_sections():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    for tag in ["content", "decision", "plan", "analysis"]:
        assert tag in text.lower(), f"checklist missing conditional section for {tag}"
    # Section anchors so the orchestrator can find them
    assert "## Conditional sections" in text or "### deliverable_type:" in text
```

**Step 2: Run test to verify it fails**

Expected: FAIL — current file lacks conditional sections.

**Step 3: Overwrite the file**

The new checklist has:
1. **Universal sections** (always run): Goal clarity, Audience fit, Reasoning quality, Internal consistency, Action surface
2. **Conditional sections** (run only when `deliverable_type` matches):
   - `content` → Voice/tone, Arrangement, Readability
   - `decision` → Trade-off rigor, Evidence, Reversibility
   - `plan` → Sequencing, Dependencies, Risk identification
   - `analysis` → Evidence quality, Conclusion strength, Counter-arguments

Each section follows the existing checklist format (numbered criteria + how-to-verify column). Use the previous `authoring-critique-checklist.md`'s structure as a starting reference (read it before overwriting).

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add skills/brainstorming/authoring-critique-checklist.md e2e/tests/test_brainstorming_files.py
git commit -m "feat(brainstorming): rewrite authoring-critique-checklist with deliverable_type sections"
```

---

### ✅ Task 19: Create four per-`deliverable_type` HTML templates

The codebase pattern is one HTML file per visualization shape (e.g., `software-template.html`). Following that pattern, this task overwrites the existing `authoring-template.html` and creates three sibling templates — one per deliverable_type. The Phase 3 dispatch table in `modes/authoring.md` selects which template to use; no attribute-conditional rendering is involved (the project has no renderer that interprets `data-deliverable-type`).

**Files:**
- Modify (overwrite): `skills/brainstorming/references/templates/authoring-template.html` (becomes the `content`-type default)
- Create: `skills/brainstorming/references/templates/authoring-decision-template.html`
- Create: `skills/brainstorming/references/templates/authoring-plan-template.html`
- Create: `skills/brainstorming/references/templates/authoring-analysis-template.html`
- Test: `e2e/tests/test_brainstorming_files.py`

**Step 1: Write the failing test**

In `e2e/tests/test_brainstorming_files.py`:

```python
def test_authoring_has_one_template_per_deliverable_type():
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "skills/brainstorming/references/templates"
    assert (base / "authoring-template.html").is_file(), "default content template missing"
    for kind in ["decision", "plan", "analysis"]:
        assert (base / f"authoring-{kind}-template.html").is_file(), (
            f"missing per-deliverable-type template: authoring-{kind}-template.html"
        )


def test_authoring_templates_share_common_scaffolding():
    # All four templates must share the live-refresh script and the design-doc header anchor
    # so visualization-protocol's strip step works uniformly.
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    base = REPO / "skills/brainstorming/references/templates"
    files = [
        "authoring-template.html",
        "authoring-decision-template.html",
        "authoring-plan-template.html",
        "authoring-analysis-template.html",
    ]
    for name in files:
        text = (base / name).read_text()
        # Anchor: every template carries the live-refresh script marker that
        # visualization-protocol.md's strip rule looks for.
        assert "<script" in text, f"{name} missing live-refresh script anchor"
```

**Step 2: Run tests to verify they fail**

Expected: FAIL — three of four files don't exist yet.

**Step 3: Overwrite the default content template + create three siblings**

Read the existing `authoring-template.html` (23640 bytes) for the common scaffolding (header, design-doc body sections, live-refresh script). Use that as the base for all four files. Customize the per-type sections:

- `authoring-template.html` (content): "Content Arrangement" section (voice + sequence + readability prompts in the design doc body).
- `authoring-decision-template.html`: "Decision Quality" section (trade-offs + evidence + reversibility).
- `authoring-plan-template.html`: "Plan Structure" section (sequencing + dependencies + risks).
- `authoring-analysis-template.html`: "Analysis Depth" section (evidence quality + conclusions + counter-arguments).

All four templates carry the live-refresh script (per `references/shared-rules.md` L7-9 byte-identical-starting-copies note) so the visualization protocol's strip rule applies uniformly.

**Step 4: Run tests to verify they pass**

**Step 5: Commit**

```bash
git add skills/brainstorming/references/templates/ e2e/tests/test_brainstorming_files.py
git commit -m "feat(brainstorming): split authoring template into four per-deliverable-type variants"
```

---

### ✅ Task 20: Restructure `skills/brainstorming/SKILL.md` Step 1 — 4-mode always-ask routing + picker labels + keyword expansion

Collapse the 5-mode classification into 4 (Software / Authoring / Research / Roadmap). Replace the silent-auto-route branch with always-ask. Inline the mode-explanation block into the AskUserQuestion prompt. Expand authoring and roadmap keyword lists per the May 17 amendment. Update "I'm not sure" → Authoring.

**Files:**
- Modify: `skills/brainstorming/SKILL.md`
- Test: `e2e/tests/test_brainstorming_files.py` (rewrite multiple functions)

**Step 1: Write/update failing tests**

Replace these tests in `e2e/tests/test_brainstorming_files.py`:

```python
def test_skill_md_description_names_four_modes():
    text = read("skills/brainstorming/SKILL.md")
    lines = text.splitlines()
    desc_line = next((l for l in lines[:10] if l.startswith("description:")), None)
    assert desc_line is not None
    for mode in ["software", "authoring", "research", "roadmap"]:
        assert mode.lower() in desc_line.lower(), f"description missing mode: {mode}"
    for gone in ["business", "planning"]:
        assert gone.lower() not in desc_line.lower(), f"description still mentions retired mode: {gone}"


def test_skill_md_overview_describes_four_modes():
    text = read("skills/brainstorming/SKILL.md")
    overview = text[text.index("## Overview"):text.index("## Step 1")]
    for mode in ["Software", "Authoring", "Research", "Roadmap"]:
        assert mode in overview, f"overview missing: {mode}"
    assert "Business" not in overview, "overview still mentions retired Business mode"
    assert "Planning" not in overview, "overview still mentions retired Planning mode"


def test_skill_md_step1_has_four_signal_sets_and_always_ask():
    text = read("skills/brainstorming/SKILL.md")
    step1 = text[text.index("## Step 1"):text.index("## Step 2")]
    for h in ["**Software mode**", "**Authoring mode**", "**Research mode**", "**Roadmap mode**"]:
        assert h in step1, f"missing signal-set header: {h}"
    for gone in ["**Business mode**", "**Planning mode**"]:
        assert gone not in step1, f"retired signal-set still present: {gone}"
    # Always-ask discipline
    assert "always" in step1.lower() and ("ask" in step1.lower() or "present the question" in step1.lower())
    # Picker label format (task vocabulary, not mode IDs)
    for label_fragment in ["Write a document", "Design a code change", "Synthesize research", "Break a big initiative"]:
        assert label_fragment in step1, f"missing picker label: {label_fragment}"


def test_skill_md_keyword_expansion_includes_deck_and_breakdown_signals():
    text = read("skills/brainstorming/SKILL.md")
    # Authoring keyword expansion (May 17 amendment)
    for kw in ["deck", "presentation", "pitch deck", "memo", "battle card"]:
        assert kw in text.lower(), f"authoring missing keyword: {kw}"
    # Roadmap keyword expansion (May 17 amendment)
    for kw in ["break", "decompose", "big idea", "smaller pieces", "spawn list"]:
        assert kw in text.lower(), f"roadmap missing keyword: {kw}"


def test_skill_md_im_not_sure_routes_to_authoring():
    text = read("skills/brainstorming/SKILL.md")
    # The post-collapse refusal-handling rule
    assert "I'm not sure" in text or "not sure" in text.lower()
    # Find context around "I'm not sure" and assert routes to Authoring
    idx = text.lower().find("not sure")
    nearby = text[idx:idx+300].lower()
    assert "authoring" in nearby, "'I'm not sure' must route to Authoring post-collapse"
    assert "business" not in nearby, "stale Business reference"


def test_skill_md_explicit_mode_arg_skips_question():
    text = read("skills/brainstorming/SKILL.md")
    assert "--mode" in text, "missing explicit --mode arg skip condition"
    assert "session" in text.lower(), "missing session-scoped skip rule"
```

Delete or rename the old `test_skill_md_description_names_five_modes`, `test_skill_md_overview_describes_five_modes`, `test_skill_md_step1_has_five_signal_sets`, `test_skill_md_mode_explanation_block_grouped`.

**Step 2: Run tests to verify they fail**

Expected: FAIL.

**Step 3: Edit `skills/brainstorming/SKILL.md` Step 1**

This is the largest single edit in the plan. The new Step 1 structure:

1. **Frontmatter `description:`** — list 4 modes (software / authoring / research / roadmap).
2. **Overview list** — 4 bullets.
3. **Step 1 header:** "Detect Mode and Confirm with User"
4. **Signal precedence note** (unchanged).
5. **Signal blocks for each of 4 modes** — Software (unchanged), Authoring (expanded with deck/memo/etc keywords, plus the diagnostic signals inherited from former Business), Research (unchanged), Roadmap (expanded with break/decompose/big-idea keywords).
6. **Always-ask routing block:**
   ```markdown
   **Always ask the user to confirm.** Even when signals point cleanly at one mode, present an AskUserQuestion with the auto-detected mode pre-selected. The user confirms with one tap or picks another. Exceptions:
   - Explicit `--mode software|authoring|research|roadmap` arg → skip the question.
   - This is the second+ brainstorm in the conversation AND the auto-detected mode matches the prior brainstorm's mode → skip the question (best-effort session marker; on uncertainty, fall back to always-ask).
   ```
7. **AskUserQuestion prompt** with task-vocabulary picker labels (per design L325-342):
   - "Write a document" (deck, memo, brief, positioning, sales pitch, curriculum, RCA write-up)
   - "Design a code change" (feature, refactor, integration, schema)
   - "Synthesize research" (compare frameworks, literature review, prior art)
   - "Break a big initiative into smaller pieces" (roadmap, multi-feature breakdown)
8. **Disambiguation rules** (collapsed from 5-mode to 4-mode — drop Business vs Planning, Business vs Authoring; keep Software vs Authoring rules).
9. **Refusal handling:** "I'm not sure" → Authoring (post-collapse absorber).
10. **Error handling for the question:** timeout → default to pre-selected; Other → follow-up; mid-brainstorm "wrong mode" → re-fire question with no pre-selection.

Inline the mode-explanation block into the AskUserQuestion option descriptions (drop the standalone mode-explanation block at current L107-133).

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_brainstorming_files.py -v -k "skill_md or signal or always_ask or keyword or im_not_sure or explicit_mode"`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md e2e/tests/test_brainstorming_files.py
git commit -m "feat(brainstorming): collapse to 4-mode always-ask routing with task-vocabulary picker labels"
```

---

### ✅ Task 21: Update `SKILL.md` per-mode emphasis table + table-driven handoff for 4 modes

The Step 2 per-mode emphasis table and Step 3 handoff table still list 5 modes. Update to 4.

**Files:**
- Modify: `skills/brainstorming/SKILL.md` (Step 2 emphasis table around L150-158, Step 3 handoff table around L165-173)
- Test: `e2e/tests/test_brainstorming_files.py` (`test_skill_md_step2_has_per_mode_emphasis`, `test_skill_md_step3_uses_table_driven_handoff`)

**Step 1: Update failing tests**

Rewrite both tests for the 4-mode shape (Software / Authoring / Research / Roadmap) with the new mode file paths (`modes/roadmap.md`) and new checklist paths (`roadmap-critique-checklist.md`).

**Step 2: Run tests to verify they fail**

Expected: FAIL (tables still 5-mode).

**Step 3: Edit the two tables**

For the Step 2 emphasis table: drop the Business row; rename Planning → Roadmap.

For the Step 3 handoff table: drop the Business row; rename Planning → Roadmap. Also update the `{software|business|research|authoring|planning}` enum near it.

**Step 4: Run tests to verify they pass**

**Step 5: Commit**

```bash
git add skills/brainstorming/SKILL.md e2e/tests/test_brainstorming_files.py
git commit -m "refactor(brainstorming): collapse SKILL.md Step 2-3 tables to 4-mode shape"
```

---

### Task 22: Update remaining brainstorming references (shared-rules, brainstorm-components, visualization-protocol, critique-panel-orchestration)

Sweep mode-list mentions and template-table rows in supporting reference files.

**Files:**
- Modify: `skills/brainstorming/references/shared-rules.md` (L1, L19)
- Modify: `skills/brainstorming/references/brainstorm-components.md` (L74, L76-83 template table)
- Modify: `skills/brainstorming/references/visualization-protocol.md` (L1)
- Modify: `skills/_shared/critique-panel-orchestration.md` (L18, L60, L104 Mode enum)
- Test: `e2e/tests/test_brainstorming_files.py` (`test_orchestration_supports_portfolio_file_path` may need updating; also add a sweep test)

**Step 1: Write failing sweep test**

```python
def test_references_describe_four_modes_post_collapse():
    for rel in [
        "skills/brainstorming/references/shared-rules.md",
        "skills/brainstorming/references/visualization-protocol.md",
        "skills/brainstorming/references/brainstorm-components.md",
        "skills/_shared/critique-panel-orchestration.md",
    ]:
        text = read(rel)
        # Must not enumerate business or planning anymore (writing-plans excepted)
        for retired in [" business,", " planning,", "business |", "planning |"]:
            assert retired not in text.lower(), f"{rel} still enumerates retired mode: {retired!r}"
        # Must enumerate Authoring and Roadmap as part of the 4-mode set
        assert "authoring" in text.lower(), f"{rel} missing authoring"
        # roadmap or research must be present in any mode enumeration
        assert "roadmap" in text.lower() or "research" in text.lower()
```

**Step 2: Run test to verify it fails**

Expected: FAIL.

**Step 3: Edit the four files**

- `shared-rules.md` L1, L19: update the "applies to all five modes" → "applies to all four modes" + enumerated list (`software, authoring, roadmap` for the live-artifact rule; Research still skips).
- `visualization-protocol.md` L1: update the enumerated mode list comment.
- `brainstorm-components.md` L74, L76-83: update the prose mode list and the template table (drop Business row; rename Planning row to Roadmap with `roadmap-template.html`).
- `critique-panel-orchestration.md` L18 (`Planning mode` → `Roadmap mode`), L60 (same), L104 (`Mode` enum: `software | business | research | authoring | planning` → `software | authoring | research | roadmap`).

**Step 4: Run test to verify it passes**

**Step 5: Commit**

```bash
git add skills/brainstorming/references/ skills/_shared/critique-panel-orchestration.md e2e/tests/test_brainstorming_files.py
git commit -m "refactor(brainstorming): sweep references for 4-mode shape and roadmap rename"
```

---

### Task 23: Update `kickstart/SKILL.md` marketing copy + remaining doc cross-references

**Files:**
- Modify: `skills/kickstart/SKILL.md` (L196)
- Modify: `README.md` (L36, L69, L80, L222 — adjust as appropriate; L222 is CHANGELOG context so leave historical)
- Modify: `docs/skill-orchestration.html` (L338, L342-346 signal bullets, L359 Mermaid, L446 Planning Mode header, L450 checklist reference)
- Modify: `docs/workflow.html` (L408 five-mode router, L411-449 mode-label sections)

**Step 1: Write failing tests**

```python
def test_kickstart_marketing_copy_mentions_four_modes():
    text = read("skills/kickstart/SKILL.md")
    assert "four modes" in text.lower(), "kickstart must declare four modes"
    # Must not still claim five modes outside of CHANGELOG context
    assert "five modes" not in text.lower(), "kickstart still claims five modes"


def test_readme_does_not_claim_two_mode_brainstorm():
    text = read("README.md")
    # L80's stale "Auto-detects software vs business mode" must be retired
    assert "software vs business" not in text.lower()
```

**Step 2: Run tests to verify they fail**

**Step 3: Edit each file**

- `kickstart/SKILL.md` L196: "...auto-routes across four modes (software, authoring, research, roadmap)..."
- `README.md` L36, L69, L80: update prose; preserve L222 CHANGELOG entry (historical record).
- `docs/skill-orchestration.html` L338, L342-346, L359, L446, L450: 4-mode shape + Roadmap label; Mermaid node `BizMode["Business mode"]` → can be removed or repointed at Authoring; `<h3>Planning Mode</h3>` → `<h3>Roadmap Mode</h3>`.
- `docs/workflow.html` L408, L411-449: collapse the 5-mode block to 4-mode (Business section removed; Planning section renamed to Roadmap).

**Step 4: Run tests to verify they pass**

**Step 5: Commit**

```bash
git add skills/kickstart/SKILL.md README.md docs/skill-orchestration.html docs/workflow.html e2e/tests/test_brainstorming_files.py
git commit -m "docs: sweep kickstart, README, skill-orchestration, workflow for 4-mode collapse"
```

---

### Task 24: Delete old business files + update `e2e/trigger-map.yaml` + `e2e/eval-surface.yaml` (single commit)

This is the user-visible cutover commit. Deletes must happen together with the trigger-map/eval-surface updates so the test suite (`test_trigger_map_paths.py`) doesn't fail mid-deploy.

**Files:**
- Delete: `skills/brainstorming/modes/business.md`
- Delete: `skills/brainstorming/business-critique-checklist.md`
- Delete: `skills/brainstorming/references/templates/business-template.html`
- Modify: `e2e/trigger-map.yaml` (the `modes/business.md` entry — currently L49 in a paths block starting at L47-49; replace `modes/business.md` with `modes/authoring.md`)
- Modify: `e2e/eval-surface.yaml` (L17-18: drop `modes/business.md`, add `modes/authoring.md`)
- Modify: `e2e/tests/test_brainstorming_files.py` (drop `test_business_mode_critique_config_unchanged`)
- Modify: `skills/brainstorming/modes/research.md` (L199: stale reference to `modes/business.md`)

**Step 1: Write failing tests**

```python
def test_business_files_removed_after_collapse():
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    for rel in [
        "skills/brainstorming/modes/business.md",
        "skills/brainstorming/business-critique-checklist.md",
        "skills/brainstorming/references/templates/business-template.html",
    ]:
        assert not (REPO / rel).exists(), f"{rel} must be deleted in mode-collapse cutover"


def test_trigger_map_does_not_reference_business():
    text = read("e2e/trigger-map.yaml")
    assert "modes/business.md" not in text, "trigger-map still references deleted file"


def test_eval_surface_does_not_reference_business():
    text = read("e2e/eval-surface.yaml")
    assert "modes/business.md" not in text, "eval-surface still references deleted file"
```

Drop `test_business_mode_critique_config_unchanged` (it asserted against the now-deleted file).

**Step 2: Run tests to verify they fail**

Expected: FAIL (files still exist; trigger-map / eval-surface unchanged).

**Step 3: Delete files + edit configs**

```bash
git rm skills/brainstorming/modes/business.md
git rm skills/brainstorming/business-critique-checklist.md
git rm skills/brainstorming/references/templates/business-template.html
```

In `e2e/trigger-map.yaml`: locate the trigger block whose `paths:` list currently contains `skills/brainstorming/modes/business.md` (single line — survey reported this as line 49 in a block starting at L47-49). Replace `skills/brainstorming/modes/business.md` with `skills/brainstorming/modes/authoring.md`. Optionally add a second trigger block for `modes/roadmap.md` if there are any roadmap-specific scenarios (defer that to Task 25 — for now the trigger covers Authoring's positioning scenario).

In `e2e/eval-surface.yaml` L17-18: drop `modes/business.md`; add `modes/authoring.md` and `modes/roadmap.md` (Research stays out — design observation).

In `modes/research.md` L199: update the stale reference (`...the visualization-finalization pattern from modes/business.md Step 1...`) to point at `modes/authoring.md` or the appropriate step.

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_brainstorming_files.py e2e/tests/test_trigger_map_paths.py e2e/tests/test_eval_surface_patterns.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add \
  e2e/trigger-map.yaml \
  e2e/eval-surface.yaml \
  skills/brainstorming/modes/research.md \
  e2e/tests/test_brainstorming_files.py
git commit -m "refactor(brainstorming): delete business mode files; route trigger-map/eval-surface to authoring"
```

The `git rm` calls in Step 3 already stage the deletions.

---

### Task 25: Rename `brainstorming-five-modes.md` fixture → `brainstorming-four-modes.md` and create new eval scenarios

Rename the eval fixture and add the new scenarios required by the design.

**Files:**
- Rename via `git mv`: `e2e/fixtures/skill-prompts/brainstorming-five-modes.md` → `e2e/fixtures/skill-prompts/brainstorming-four-modes.md`
- Modify fixture content for 4-mode shape
- Create:
  - `e2e/scenarios/use-skill/always-ask-routing.yaml`
  - `e2e/scenarios/use-skill/deck-routing.yaml`
  - `e2e/scenarios/use-skill/authoring-no-framework-fallback.yaml`
  - `e2e/scenarios/use-skill/brainstorming-four-modes.yaml` (replaces five-modes if present)
  - `e2e/scenarios/use-skill/framework-runner-extraction.yaml`
  - `e2e/scenarios/use-skill/deliverable-type-dispatch.yaml`
  - `e2e/scenarios/use-skill/use-framework-backward-compat.yaml`
  - `e2e/scenarios/use-skill/authoring-mode-engine-selection.yaml`
- Modify: `e2e/trigger-map.yaml` to reference the new scenarios
- Modify: `e2e/tests/test_brainstorming_files.py` (rename `test_five_modes_eval_fixture_lists_15_briefs` → `test_four_modes_eval_fixture_lists_briefs` and update label assertions)

**Step 1: Write/update failing tests**

```python
def test_four_modes_fixture_exists_and_lists_four_modes():
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    assert not (REPO / "e2e/fixtures/skill-prompts/brainstorming-five-modes.md").exists()
    assert (REPO / "e2e/fixtures/skill-prompts/brainstorming-four-modes.md").exists()
    text = (REPO / "e2e/fixtures/skill-prompts/brainstorming-four-modes.md").read_text()
    for label in ["Software", "Authoring", "Research", "Roadmap"]:
        assert label in text
    for retired in ["Business mode", "Planning mode"]:
        assert retired not in text
```

Plus assertions that the eight new scenario YAML files exist and parse.

**Step 2: Run tests to verify they fail**

**Step 3: Rename + create**

```bash
git mv e2e/fixtures/skill-prompts/brainstorming-five-modes.md e2e/fixtures/skill-prompts/brainstorming-four-modes.md
```

Edit the fixture content to drop Business and Planning blocks and add a Roadmap block (mirroring the new SKILL.md Step 1 shape). Replace 5-way disambiguation question with the 4-way picker label format.

Create each new YAML scenario as a stub with the design's stated coverage:

- `always-ask-routing.yaml` — six sub-scenarios: (a) first invocation always asks, (b) subsequent same-mode skips, (c) subsequent different-mode re-asks, (d) explicit `--mode` arg skips, (e) session-marker uncertainty falls through, (f) error path mid-brainstorm wrong-mode re-invoke.
- `deck-routing.yaml` — single scenario: prompt "I need to build a deck for a client" → router presents 4-mode question with Authoring pre-selected.
- `authoring-no-framework-fallback.yaml` — three sub-scenarios: (a) no-framework topic falls to Q&A with topic advisor, (b) Q&A produces a design doc, (c) design doc feeds writing-plans.
- `brainstorming-four-modes.yaml` — five sub-scenarios, one per mode, asserting correct routing.
- `framework-runner-extraction.yaml` — backward-compat: use-framework still runs frameworks identically.
- `deliverable-type-dispatch.yaml` — four sub-scenarios, one per deliverable_type, plus a fifth for the missing-deliverable_type fallback.
- `use-framework-backward-compat.yaml` — direct invocation of `/aligned:use-framework` produces identical pre-refactor behavior.
- `authoring-mode-engine-selection.yaml` — five sub-scenarios calibrating the auto-select/shortlist/fallback ladder per the design's Phase 1 ladder.

Each scenario YAML follows the existing format used by `e2e/scenarios/use-skill/brainstorming-positioning.yaml` (read it as a template before authoring the new ones).

In `e2e/trigger-map.yaml`, add new trigger blocks pointing at the new scenarios from the relevant source files (the writing-plans guidance file specifies this).

**Step 4: Run tests to verify they pass**

Run: `pytest e2e/tests/test_brainstorming_files.py e2e/tests/test_trigger_map_scenarios.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add \
  e2e/fixtures/skill-prompts/brainstorming-four-modes.md \
  e2e/scenarios/use-skill/always-ask-routing.yaml \
  e2e/scenarios/use-skill/deck-routing.yaml \
  e2e/scenarios/use-skill/authoring-no-framework-fallback.yaml \
  e2e/scenarios/use-skill/brainstorming-four-modes.yaml \
  e2e/scenarios/use-skill/framework-runner-extraction.yaml \
  e2e/scenarios/use-skill/deliverable-type-dispatch.yaml \
  e2e/scenarios/use-skill/use-framework-backward-compat.yaml \
  e2e/scenarios/use-skill/authoring-mode-engine-selection.yaml \
  e2e/trigger-map.yaml \
  e2e/tests/test_brainstorming_files.py
git commit -m "test(brainstorming): rename fixture to four-modes; add 8 new eval scenarios for engine selection and routing"
```

The renamed fixture (brainstorming-five-modes.md) is tracked as a rename automatically by `git mv` in Step 3.

---

### Task 26: Sweep remaining `test_brainstorming_files.py` functions for 4-mode shape

After Tasks 15, 17, 18, 19, 20, 21, 22, 23, 24, 25 have all changed the source, run the full `test_brainstorming_files.py` and update any remaining functions that still hardcode 5-mode or use `business`/`planning` labels.

**Files:**
- Modify: `e2e/tests/test_brainstorming_files.py`

**Step 1: Run the full test file to identify remaining failures**

Run: `pytest e2e/tests/test_brainstorming_files.py -v`
Identify any failing tests not already updated by prior tasks. Per the survey, candidates include:
- `test_authoring_mode_handles_sisney_absence` — verify it still applies post-rewrite (Sisney check may still be relevant in advisor pool).
- `test_orchestration_dispatches_interactive_html` — verify it doesn't reference deleted files.
- `test_critique_checklist_structure` (parametrized) — drop business + planning, add roadmap.

**Step 2: Edit each remaining failing function**

For each failing test, decide:
- If still applicable post-collapse, update labels/paths and confirm.
- If made obsolete by the collapse, delete it.

**Step 3: Run the full test file to verify everything passes**

Run: `pytest e2e/tests/test_brainstorming_files.py -v`
Expected: 0 failures.

**Step 4: Commit**

```bash
git add e2e/tests/test_brainstorming_files.py
git commit -m "test(brainstorming): finalize 4-mode test sweep across test_brainstorming_files.py"
```

---

### Task 27: Update `spawn-brief-template.md` to add Roadmap to target_mode enum

Already partially addressed in Task 15. This task confirms and finalizes the Roadmap enum addition + L34 prose update on recursive Roadmap breakdown.

**Files:**
- Modify: `skills/brainstorming/references/spawn-brief-template.md` (L12, L34)

**Step 1: Write failing test**

```python
def test_spawn_brief_target_mode_includes_roadmap():
    text = read("skills/brainstorming/references/spawn-brief-template.md")
    assert "Roadmap" in text, "spawn-brief must include Roadmap in target_mode enum"
    # Recursive breakdown explanation
    assert "recursive" in text.lower() or "nested" in text.lower() or "sub-portfolios" in text.lower()
```

**Step 2: Run test to verify it fails**

If Task 15 already added Roadmap, this passes. Otherwise FAIL.

**Step 3: Edit if needed**

Add `| Roadmap` to the L12 enum if missing. Update L34 prose to explain recursive Roadmap breakdown.

**Step 4: Run test to verify it passes**

**Step 5: Commit (only if any changes)**

```bash
git add skills/brainstorming/references/spawn-brief-template.md e2e/tests/test_brainstorming_files.py
git commit -m "docs(spawn-brief): finalize Roadmap addition to target_mode enum"
```

---

### Task 28: Bump plugin version + run full suite

Bump `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` from `0.30.0` → `0.31.0`. Run the full test suite to confirm no regressions.

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Edit both files**

Use Edit tool to change `"version": "0.30.0"` to `"version": "0.31.0"` in both files.

**Step 2: Run `test_plugin_version_bumped`**

Run: `pytest e2e/tests/test_brainstorming_files.py::test_plugin_version_bumped -v`
Expected: PASS.

**Step 3: Run the full test suite**

Run: `pytest e2e/tests/ -v`
Expected: all tests PASS (or at least, no new failures introduced by this refactor — unrelated flakes are out of scope).

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump plugin version to 0.31.0 for framework-runner refactor"
```

---

## Eval Scenarios

The following scenarios are created in Task 25 and must be authored to the project's existing scenario format (see `e2e/scenarios/use-skill/brainstorming-positioning.yaml` as a reference):

1. `e2e/scenarios/use-skill/always-ask-routing.yaml` — six sub-scenarios covering first-invocation ask, subsequent skip, subsequent re-ask, `--mode` arg, session-marker uncertainty fall-through, and mid-brainstorm wrong-mode re-invoke.
2. `e2e/scenarios/use-skill/deck-routing.yaml` — regression test for the May 17 failure case ("I need to build a deck for a client" → Authoring pre-selected).
3. `e2e/scenarios/use-skill/authoring-no-framework-fallback.yaml` — three sub-scenarios for the structured-Q&A fallback ladder.
4. `e2e/scenarios/use-skill/brainstorming-four-modes.yaml` — replaces `brainstorming-five-modes.yaml`; five sub-scenarios, one per mode plus a shortlist case.
5. `e2e/scenarios/use-skill/framework-runner-extraction.yaml` — backward-compat: `/aligned:use-framework` runs frameworks identically post-extraction; covers WAIT discipline, voice carrying, intake-gate behavior.
6. `e2e/scenarios/use-skill/deliverable-type-dispatch.yaml` — Phase 3 dispatch picks the right template + critique pool for each `deliverable_type` value, including the missing-field fallback path.
7. `e2e/scenarios/use-skill/use-framework-backward-compat.yaml` — direct invocation backward-compat baseline.
8. `e2e/scenarios/use-skill/authoring-mode-engine-selection.yaml` — calibrates the auto-select/shortlist thresholds with five sub-scenarios across the fallback ladder.

These scenarios cover prompt-construction changes (framework runner extraction), routing logic (always-ask, mode collapse), and personalization (advisor proxy seat selection). The project's eval conventions are read from existing scenarios in `e2e/scenarios/use-skill/`.

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Q&A pattern duplication test surface | Anchor on the role-override sentence (verbatim in both files) | Structural AST diff; section-header anchors |
| 2 | Test sequencing for delete-then-recreate authoring.md | Overwrite via Write tool (new content), then delete business siblings separately | Two commits (delete first, recreate later); single bundle |
| 3 | When to add the `default_critic_advisors` field | Quality over coverage — only add to 8-15 clear-fit entries; assert ≥5 in tests; Phase 3 dispatch consumes the field at runtime | Mandate for all 154; require none |
| 4 | Roadmap-Roadmap recursive spawn-brief target_mode | Include Roadmap in enum and document recursive use as rare | Exclude (avoid recursion); include with no caveat |
| 5 | Validate deliverable_type taxonomy before bulk-classifying | Manually classify 13 ambiguous frameworks first, document in `docs/notes/` | Classify all 154 in one shot; rely on per-entry judgment without pre-validation |
| 6 | Per-deliverable_type templates (4 files) vs attribute-conditional rendering (1 file) | One template per type (4 files); matches codebase pattern of one HTML per visualization shape | `data-deliverable-type` attribute conditionals (rejected — no renderer in the codebase) |
| 7 | Implementation choices (batching, name-cap, test-window) | 3 classification batches of ~50; 60-char name cap; window-based "I'm not sure" assertion | Various single-commit / strict / brittle alternatives |

### Appendix: Decision Details

#### Decision 1: Q&A pattern duplication test surface

**Chose:** Anchor the parity test on the verbatim sentence "Your normal constraint of 'do not propose alternatives' is suspended" — assert it appears in both `modes/software.md` and `modes/authoring.md`.

**Why:** The design's stated stable surface is "the Architect-as-proxy dispatch template structure." Any stable test anchor must be (a) stable across edits, (b) cheap to assert against, and (c) verifiable that the actual operative content (the role-override) is the same. The role-override sentence is the operative imperative — if it's missing or altered, the proxy mode is broken. Anchoring on it is necessary AND sufficient. Structural AST diff was rejected because Markdown has no AST that distinguishes substantive prose from formatting noise. Section-header anchors fail when one file restructures headings.

**Alternatives rejected:**
- Structural AST diff of the dispatch template: no widely-used Markdown structural diff tool; either too strict (fails on whitespace) or too loose (passes a hollowed-out template).
- Section-header anchors only: misses the case where the section header survives but the prompt body is gutted.

#### Decision 2: Test sequencing for delete-then-recreate authoring.md

**Chose:** Overwrite the old authoring.md with new content (Task 17 uses Write tool, which reads-then-overwrites), then delete the business siblings in a separate commit (Task 24).

**Why:** Bundling overwrite + delete in one commit would force a multi-step task with file deletions interleaved with file creations — high cognitive load and easy to flub. Splitting them keeps each task focused: Task 17 is "ship the new authoring.md"; Task 24 is "remove the obsolete business mode files." The authoring.md test rewrite happens in Task 17 (so the test exercises the new shape immediately). Business test deletion + file deletion + trigger-map update bundle cleanly in Task 24. Each task verifies its own slice via pytest.

**Alternatives rejected:**
- Two commits (delete first, then recreate): leaves the repo in an unrunnable state mid-sequence.
- Single bundled commit: too large for one TDD task; spans multiple test files.

#### Decision 3: When to add `default_critic_advisors`

**Chose:** Quality over coverage. Add the field to only 8-15 entries with clear-fit advisors. Test asserts ≥5 to prevent the field from becoming inert. Phase 3 dispatch in `modes/authoring.md` consumes the field at runtime to override the default critic pool — this is what makes the field load-bearing.

**Why:** The design lists this as `optional` and the field exists to override the generic-by-deliverable-type critic pool. Forcing it onto all 154 entries dilutes the signal (most frameworks don't have specific critic preferences). Asserting ≥5 ensures the field is exercised. Without a consumption site, the field would be inert metadata — Phase 3's override step is the consumption site.

**Alternatives rejected:**
- Mandate for all 154: dilutes signal, adds bulk-classification work without value.
- No floor (none required): risks the field being added to schema but never used.
- Delete the field entirely: rejected because Phase 3 dispatch needs per-framework critic-pool tuning for ~10 high-traffic frameworks (the design's intent).

#### Decision 4: Roadmap-Roadmap recursive spawn-brief target_mode

**Chose:** Include Roadmap in the spawn-brief `target_mode` enum, with a one-line caveat in L34 that recursive Roadmap breakdown is rare but supported.

**Why:** The design (Open Question 6) explicitly addresses this: a real portfolio entry may need further decomposition before brainstorming. Excluding Roadmap from the enum would force authors to use a different target_mode (Software/Authoring) for what is really a nested-portfolio case. Including it with a "rare" caveat surfaces the capability without encouraging routine use.

**Alternatives rejected:**
- Exclude Roadmap: forces incorrect target_mode for nested portfolios.
- Include with no caveat: encourages routine recursion when the simpler pattern is usually right.

#### Decision 5: Validate deliverable_type taxonomy before bulk-classifying

**Chose:** Manually classify 13 known-ambiguous frameworks (5-components-positioning, the-work, fear-setting, kernel-of-good-strategy, jobs-to-be-done, accusation-audit, insane-honesty, okr-setting, finding-the-crux, landing-page-assembly, 100-percent-responsibility, 5-step-process, competitive-analysis) in Task 6 before launching the full 154-entry classification.

**Why:** The design's Open Question 2 ("Deliverable type taxonomy edge cases") explicitly calls this out. Validating the primary-tag rule against 10-15 ambiguous cases catches taxonomy gaps before they propagate across 154 entries. The cost is ~30 minutes; the benefit is avoiding a 154-entry re-classification if the taxonomy turns out incomplete.

**Alternatives rejected:**
- Classify all 154 in one shot: high risk of late discovery that the taxonomy needs a fifth tag.
- Skip pre-validation: relies on per-entry judgment without a calibration anchor.

#### Decision 6: Per-deliverable_type templates (4 files) vs attribute-conditional rendering (1 file)

**Chose:** Four separate HTML template files (`authoring-template.html`, `authoring-decision-template.html`, `authoring-plan-template.html`, `authoring-analysis-template.html`) — one per `deliverable_type`. Phase 3 dispatch picks which file to use by string match.

**Why:** The original draft used `data-deliverable-type="..."` attribute-conditional sections inside one HTML file. The Round 1 Architect critique flagged that no renderer in the codebase interprets that attribute — the visualization protocol reads a single template and serves it directly. Adding attribute-conditional rendering would require a new renderer, which is out of scope. Matching the existing one-template-per-shape codebase pattern (cf. `software-template.html`, `research-template.html`) eliminates the renderer dependency.

**Alternatives rejected:**
- Attribute-conditional sections inside one file: requires a renderer that doesn't exist.
- Server-side templating: out of scope for a markdown-skill plugin.

#### Decision 7: Implementation choices (batching, name-cap, test-window)

Three reversible implementation details that don't warrant their own Decision Log entries:

- **Classification batching (Tasks 7-9):** 3 batches of ~50 frameworks each. Threshold-test pattern (assert ≥50, ≥100, 100%) makes each batch verifiable independently. Per-entry commits would bloat history; one mega-commit would exceed the per-task time budget.
- **Name-field cap at 60 chars:** Hard cap is enforceable in CI and prevents regressions. 60 chars is a generous upper bound that fits in standard picker UIs. A separate `display_name` field would double the metadata.
- **Window-based "I'm not sure" assertion:** The refusal handler is multi-sentence prose. Window-based assertion (300-char neighborhood) captures the intent (route destination changed) without over-coupling to phrasing.
