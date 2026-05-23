---
---
# Repo-Scoped (Local) Advisors Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add a project-local advisor read path that merges with the plugin's global advisors (parity with the existing framework merge), then migrate the 19 health/therapy advisors and their 39 frameworks out of the plugin into the user's personal repo (`~/.claude/`).

**Source Design Doc:** `docs/plans/2026-05-23-local-advisors-design.md`

**Architecture:** A new shared markdown procedure `skills/_shared/resolve-advisor-source.md` becomes the single source of merge truth (plugin registry canonical + project-local `advisors/registry.yaml`, dedupe-by-id, local-wins). Every advisor read path (`use-advisor`, `critique-panel-orchestration`, `contextual-recommendation`, brainstorming `research`/`authoring` modes) routes through it. With the read path in place, the 19 health/therapy advisors + 39 frameworks are moved to `~/.claude/` (file writes only — the launchd agent commits that repo), removed from the plugin in count-balanced commits, and the plugin's published counts/catalogs are corrected.

**Tech Stack:** Markdown procedure files (LLM-followed, not executable), YAML registries, Python `pytest` assertion tests (markdown-substring + YAML-schema style), `python3 scripts/generate-catalogs.py` for HTML catalogs.

---

## Prerequisites

> None. The mechanism (Part 1) is self-contained, and the migration (Part 4) writes to `~/.claude/` via plain file I/O. No manual setup is required before Task 1.

---

## Ordering Dependencies (read before executing)

- **Part 1 (mechanism) must complete before Part 4 (migration).** A local advisor in `~/.claude/advisors/` is invisible until the read paths route through the resolver. Migrating advisors before the read path exists would orphan them.
- **Task 2 (resolver) is a hard dependency for Tasks 4–7.** Task 3 (dual-contract) is a hard dependency for Tasks 4 and 7.
- **Tasks 13 → 14 → 15 are sequential** — all three edit `advisors/registry.yaml` and `frameworks/registry.yaml`. The Ralph loop runs tasks sequentially, so this is satisfied by order alone; do not reorder.
- **Tasks 16–17 require Tasks 13–15 complete** (they reflect post-migration counts).
- The `enneagram-typing` entry in `frameworks/_outliers.json` MUST be removed in the **same commit** that removes the `enneagram-typing` framework (Task 13). Removing the framework without the outlier entry turns `test_registry_schemas.py::test_outlier_frameworks_have_correct_metadata` red.

---

# Part 1 — The Mechanism (plugin repo)

### Task 1: Failing test for the resolver procedure

**Files:**
- Create: `e2e/tests/test_resolve_advisor_source.py`

This is a markdown-assertion test in the style of `e2e/tests/test_shared_runners.py` — it asserts the procedure file *documents* each required behavior as a substring/section. `resolve-advisor-source.md` is a procedure an LLM follows, not executable code, so there is no behavioral fixture test (matches the harness precedent noted in the design's Testing section).

**Step 1: Write the failing test**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_resolver_file_exists():
    assert (REPO / "skills/_shared/resolve-advisor-source.md").is_file()


def test_resolver_documents_merge_order_plugin_canonical():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "canonical" in text.lower()
    assert "plugin" in text.lower() and "registry.yaml" in text


def test_resolver_documents_dedupe_before_return_local_wins():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "dedupe" in text or "deduplicate" in text
    assert "before return" in text or "before returning" in text
    assert "local-wins" in text or "local wins" in text


def test_resolver_documents_scope_root_derivation():
    text = read("skills/_shared/resolve-advisor-source.md")
    # plugin entries anchor on plugin-root; local entries on project-cwd
    assert "plugin-root" in text or "plugin root" in text
    assert "project-cwd" in text or "project cwd" in text
    assert "absolute_prompt_path" in text


def test_resolver_documents_prompt_dir_override_and_default():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "advisors/prompts" in text  # the default
    assert "prompt-dir" in text or "prompt dir" in text or "<prompt-dir>" in text
    assert "CLAUDE.md" in text  # the override source


def test_resolver_documents_ignore_prompt_field():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "ignored for resolution" in text


def test_resolver_documents_selection_guidelines_plugin_canonical():
    text = read("skills/_shared/resolve-advisor-source.md")
    assert "selection_guidelines" in text
    # local repos do not override panel selection rules
    assert "plugin" in text.lower()


def test_resolver_documents_four_error_paths():
    text = read("skills/_shared/resolve-advisor-source.md").lower()
    assert "absent" in text or "does not exist" in text  # local registry absent -> plugin-only
    assert "malformed" in text and "warning" in text     # malformed local -> degrade + warn
    assert "default" in text                              # prompt-dir override absent -> default
    assert "fail-close" in text or "fail closed" in text or "use time" in text  # missing prompt file


def test_resolver_documents_return_contract():
    text = read("skills/_shared/resolve-advisor-source.md")
    for field in ["id", "name", "absolute_prompt_path", "source"]:
        assert field in text, f"return contract must name field: {field}"
    assert '"plugin"' in text or "plugin | local" in text or '"local"' in text


def test_resolver_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/resolve-advisor-source.md" in text, (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )
```

**Step 2: Run test to verify it fails**

Run: `pytest e2e/tests/test_resolve_advisor_source.py -v`
Expected: FAIL — `test_resolver_file_exists` and all others fail (file does not exist yet).

**Step 3: Commit the failing test**

```bash
git add e2e/tests/test_resolve_advisor_source.py
git commit -m "test: add failing assertions for resolve-advisor-source procedure"
```

---

### Task 2: Create the resolver procedure + register the eval surface

**Files:**
- Create: `skills/_shared/resolve-advisor-source.md`
- Modify: `e2e/eval-surface.yaml` (add the new surface pattern)

**Step 1: Create `skills/_shared/resolve-advisor-source.md`**

Write this content verbatim:

```markdown
# Resolving the Merged Advisor Source

Shared procedure that returns the merged advisor set (plugin global + project-local)
plus the plugin's panel `selection_guidelines`. Every advisor read path calls this so
the merge logic cannot drift across callers. This is the advisor-side parallel of the
framework merge already implemented in `skills/use-framework/SKILL.md` Step 1.

> **Note:** This is a `skills/_shared/` library file. `{base-directory}` refers to the
> CALLING skill's base directory; the caller resolves it per `skills/_shared/resolve-skill-path.md`
> before reading this file. Do NOT add a Path Resolution note here.

## Procedure

1. **Load the plugin registry (canonical).** Read the plugin `advisors/registry.yaml`
   (resolve the plugin root per `skills/_shared/resolve-skill-path.md` — Plugin root section).
   Parse both its `advisors:` list and its top-level `selection_guidelines:` block. Tag every
   advisor entry `source: "plugin"`.

2. **Merge the project-local registry (if present).** If `<project-cwd>/advisors/registry.yaml`
   exists, load it and merge its `advisors:` list. Tag those entries `source: "local"`.
   **Dedupe by `id` before returning** — on a duplicate `id`, **local-wins** (the local entry
   replaces the plugin entry). Deduping before return guarantees a shadowed plugin advisor
   never double-lists in a panel candidate set.

3. **Compute the absolute prompt path for every entry.**
   `absolute_prompt_path = <scope-root>/<prompt-dir>/<id>.md` where:
   - `<scope-root>` = **plugin-root** for `source: "plugin"` entries, **project-cwd** for
     `source: "local"` entries.
   - `<prompt-dir>` = the CLAUDE.md-configured advisor prompt path if present (the same key
     `add-advisor` Step 0 reads), else the default `advisors/prompts`.

   The stored `prompt:` field is **ignored for resolution** — it is plugin-relative on every
   entry and would mis-resolve a local advisor. It remains as human-readable metadata only.

**Anchoring rule:** local advisors resolve against **project-cwd**, never plugin-root.
`resolve-skill-path.md` is for plugin-bundled files only and is NOT reused for locals.
Local advisors live at `<project-root>/advisors/` (registry + `prompts/`), not a `.claude/`-nested
path — the personal repo is not a plugin and has no `.claude-plugin/plugin.json`.

## Return contract

Return a single object. Callers couple to this shape — do not vary it.

```
{
  advisors: [
    { id, name, summary, domains, evaluation_expertise, best_for, not_for,
      absolute_prompt_path, source: "plugin" | "local" }
  ],
  selection_guidelines: { ... }   // PLUGIN-CANONICAL — local repos do NOT override
                                  // panel selection rules (no use case; YAGNI)
}
```

- `selection_guidelines` is a sibling of `advisors`, taken from the **plugin** registry only.
- Every per-advisor field is present for both plugin and local advisors. A local registry entry
  MUST carry the full advisor schema (`id`, `name`, `summary`, `prompt`, `domains`; profiled
  fields when applicable).

## Error paths

- **Local `advisors/registry.yaml` absent** → return the plugin-only result. No error.
- **Local registry malformed YAML** → **degrade to plugin-only and emit a one-line warning
  naming the file.** A broken local registry must not lock the user out of plugin advisors.
  (This differs from `add-advisor`'s write-side revert-on-parse-failure, which is correct for a
  write but wrong for a read.)
- **Prompt-dir CLAUDE.md override absent** → use the default `<scope-root>/advisors/prompts/<id>.md`.
- **Resolved prompt file missing** → the resolver does NOT error. `advisor-runner.md`
  fail-closes at use time (preserved behavior).
- **Resolver file itself unreadable** → this is outside the resolver's own error contract.
  It indicates a plugin installation failure, not a merge failure. The resolver cannot handle
  its own non-existence; each call site handles it independently. `use-advisor` does NOT degrade
  silently — an unreadable resolver signals a broken plugin install, not a recoverable condition.
  `critique-panel-orchestration` falls back to the glob path (plugin-only; documented in Task 5).
```

**Step 2: Add the surface to `e2e/eval-surface.yaml`**

In `e2e/eval-surface.yaml`, locate the line `  - skills/_shared/advisor-runner.md` and add a new line immediately after it:

```yaml
  - skills/_shared/resolve-advisor-source.md
```

**Step 3: Run the test to verify it passes**

Run: `pytest e2e/tests/test_resolve_advisor_source.py -v`
Expected: PASS — all assertions satisfied.

**Step 4: Commit**

```bash
git add skills/_shared/resolve-advisor-source.md e2e/eval-surface.yaml
git commit -m "feat: add resolve-advisor-source shared merge procedure"
```

---

### Task 3: Make contextual-recommendation Stage 1 dual-contract

**Files:**
- Modify: `skills/_shared/contextual-recommendation.md` (Stage 1: Domain Filter)
- Test: `e2e/tests/test_contextual_recommendation.py`

Stage 1 currently reads only a registry YAML path. Advisor callers that have already merged via the resolver need to pass the **pre-merged advisor entry list** instead. Make Stage 1 accept EITHER input. Frameworks keep passing a path; advisors pass a pre-merged list.

**Step 1: Write the failing test (append to the existing file)**

```python
def test_stage1_accepts_premerged_advisor_list():
    text = read("skills/_shared/contextual-recommendation.md")
    # Stage 1 must document a dual contract: registry path OR pre-merged advisor entries
    assert "pre-merged" in text.lower() or "premerged" in text.lower(), (
        "Stage 1 must accept a pre-merged advisor entry list (from resolve-advisor-source)"
    )
    assert "resolve-advisor-source" in text, (
        "dual-contract must name resolve-advisor-source as the source of the merged list"
    )


def test_stage1_documents_which_branch_each_entity_uses():
    text = read("skills/_shared/contextual-recommendation.md").lower()
    # framework callers pass a path; advisor callers pass the merged list
    assert "framework" in text and "path" in text
    assert "advisor" in text and ("list" in text or "entries" in text)


def test_configuration_documents_advisor_input_variants():
    text = read("skills/_shared/contextual-recommendation.md")
    # After the dual-contract change, ## Configuration must document both input branches by name.
    # The old single "Registry path:" bullet must be updated to cover advisor callers explicitly.
    assert "advisor callers" in text.lower(), (
        "## Configuration must document the advisor-callers input variant by name"
    )
    assert "framework callers" in text.lower(), (
        "## Configuration must document the framework-callers input variant by name"
    )
```

(Use the same `read()` helper already defined at the top of `test_contextual_recommendation.py`.)

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_contextual_recommendation.py -v`
Expected: FAIL — `test_stage1_accepts_premerged_advisor_list` and the branch test fail.

**Step 3: Edit the procedure**

In `skills/_shared/contextual-recommendation.md`, make two edits:

**3a. Update the `## Configuration` section.** Replace the `**Registry path:**` bullet:

> - **Registry path:** `advisors/registry.yaml` or `frameworks/registry.yaml`

with:

```markdown
- **Input (framework callers):** a registry YAML path (`frameworks/registry.yaml`)
- **Input (advisor callers):** either a registry YAML path (`advisors/registry.yaml`, plugin-only
  scope) or a pre-merged advisor entry list from `skills/_shared/resolve-advisor-source.md`
  (plugin + local, deduped, local-wins)
```

**3b. Update the `## Stage 1: Domain Filter` opening.** Replace the Stage 1 opening line:

> Read the registry YAML file (path provided by calling skill). Parse all entries.

with:

```markdown
**Stage 1 input is dual-contract.** The calling skill passes ONE of:
- **A registry YAML path** (framework callers, and any advisor caller that wants plugin-only
  scope) — read and parse all entries.
- **A pre-merged advisor entry list** (advisor callers that already merged plugin + local via
  `skills/_shared/resolve-advisor-source.md`) — use the list as-is; do NOT re-read a registry.

Framework callers always use the path branch. Advisor callers that must surface project-local
advisors use the pre-merged-list branch — otherwise local advisors are invisible to contextual
recommendation.
```

Leave the rest of Stage 1 (scoring eligibility filter, domain signals, filter, fallback, shuffle) unchanged — it operates on "entries" regardless of how they were obtained.

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_contextual_recommendation.py -v`
Expected: PASS (including the pre-existing multi-entity tests).

**Step 5: Commit**

```bash
git add skills/_shared/contextual-recommendation.md e2e/tests/test_contextual_recommendation.py
git commit -m "feat: contextual-recommendation Stage 1 accepts pre-merged advisor list"
```

---

### Task 4: Rewire use-advisor to the merged advisor source

**Files:**
- Modify: `skills/use-advisor/SKILL.md` (Step 1a/1b, Step 2 listing text, Step 3, Step 4)
- Test: `e2e/tests/test_shared_runners.py` (append assertions)

> Behavior change: the advisor list and contextual recommendation now include project-local advisors when a `<project-cwd>/advisors/registry.yaml` exists. In the plugin repo (no separate local registry), behavior is unchanged — the resolver dedupes the plugin registry against itself.

**Preserve these existing guarantees** (asserted by `test_use_advisor_documents_absolute_path_construction` and `test_use_advisor_invokes_shared_runner`): the file must still reference `resolve-skill-path.md` (for plugin-root resolution of plugin advisors), still document the `advisors/prompts/<id>.md` path pattern, still invoke `_shared/advisor-runner.md`, still pass `greeting_mode=full`, and must NOT contain `greeting_mode=silent` or the string "Read the full advisor prompt file".

**Step 1: Write the failing test (append to `test_shared_runners.py`)**

```python
def test_use_advisor_routes_through_resolver():
    text = read("skills/use-advisor/SKILL.md")
    assert "resolve-advisor-source.md" in text, (
        "use-advisor must route discovery through the merged resolver"
    )
    # Preserve plugin-root resolution for plugin advisors
    assert "resolve-skill-path.md" in text


def test_use_advisor_listing_text_no_longer_claims_flat_directory():
    text = read("skills/use-advisor/SKILL.md")
    assert "single flat directory" not in text, (
        "the 'single flat directory' claim is false once local advisors merge"
    )
    assert "(local)" in text, (
        "use-advisor must annotate local advisors using the resolver's source field"
    )
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_shared_runners.py -v -k use_advisor`
Expected: FAIL — `test_use_advisor_routes_through_resolver` and the listing-text test fail.

**Step 3: Edit `skills/use-advisor/SKILL.md`**

1. **Step 1 (Discover Available Advisors).** Replace Step 1a/1b with a single resolver call:

```markdown
**Step 1a: Resolve the merged advisor set**

Read `skills/_shared/resolve-advisor-source.md` (plugin-relative path) and follow its procedure
to obtain the merged advisor set (plugin global + project-local, deduped, local-wins). Use the
returned `advisors` list as the listing source — each entry carries `id`, `name`, `summary`,
`domains`, `absolute_prompt_path`, and `source`.

> The resolver's own error paths already handle degradation (absent local registry → plugin-only
> result; malformed local YAML → degrade + warn). No additional fallback is needed here — a
> resolver file that cannot be read indicates a plugin installation failure, which is a distinct
> failure mode and not something `use-advisor` should silently paper over.
```

2. **Step 2 (Extract Advisor Names), final paragraph.** Replace:

> List advisors alphabetically by display name. Do not group by repo — all advisors live in a single flat directory.

with:

```markdown
List advisors alphabetically by display name. When both scopes contribute (the resolver returned
entries with `source: "local"` as well as `source: "plugin"`), annotate each local advisor with a
trailing `(local)` marker so the user can tell repo-specific advisors from global ones.
```

3. **Step 3 (Match User Input), bullet 5 and the no-arg branch.** Where it passes `registry path: advisors/registry.yaml` to contextual-recommendation, change to pass the **pre-merged advisor list** from Step 1a (the dual-contract branch added in Task 3). Keep entity type `advisor` and the task-context values unchanged.

4. **Step 4 (Run the Advisor), path construction.** Replace the manual `<plugin-root>/advisors/prompts/<id>.md` construction so it uses the matched entry's `absolute_prompt_path` from the resolver:

```markdown
**Resolving the absolute advisor path.** The runner requires a file that exists and fails closed
otherwise. Use the matched advisor's `absolute_prompt_path` returned by the resolver in Step 1a
(it already anchors plugin advisors on plugin-root and local advisors on project-cwd, per
`skills/_shared/resolve-skill-path.md` for the plugin-root case).
```

Keep the `advisors/prompts/<id>.md` pattern mentioned (the cross-reference test and
`test_use_advisor_documents_absolute_path_construction` both require it) and keep the
`greeting_mode=full` handoff to `advisor-runner.md`.

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_shared_runners.py -v -k use_advisor`
Expected: PASS — new tests pass and the pre-existing use-advisor tests still pass.

**Step 5: Commit**

```bash
git add skills/use-advisor/SKILL.md e2e/tests/test_shared_runners.py
git commit -m "feat: route use-advisor discovery and path resolution through merged resolver"
```

---

### Task 5: Rewire critique-panel-orchestration to the resolver

**Files:**
- Modify: `skills/_shared/critique-panel-orchestration.md` (Round 1, steps 1 and 3)
- Create: `e2e/tests/test_critique_panel_resolver.py`

This is the highest-risk edit — two coupled changes in the Round 1 block. The current step 1 reads `advisors/registry.yaml` directly and reads `selection_guidelines` from it; step 3 reads each critic's prompt via the registry `prompt:` field. Route both through the resolver.

**Step 1: Write the failing test**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_critique_panel_uses_resolver_for_advisor_list():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "resolve-advisor-source.md" in text, (
        "Round 1 must obtain the advisor list from the merged resolver"
    )


def test_critique_panel_takes_selection_guidelines_from_resolver_return():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "selection_guidelines" in text
    # the resolver return is the source for selection_guidelines now
    assert "return" in text.lower()


def test_critique_panel_resolves_prompt_via_absolute_path():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "absolute_prompt_path" in text, (
        "critic prompt files must be resolved via the resolver's absolute_prompt_path, "
        "not the plugin-relative `prompt:` field"
    )
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_critique_panel_resolver.py -v`
Expected: FAIL — all three fail.

**Step 3: Edit `skills/_shared/critique-panel-orchestration.md`**

Under `## Round 1`, replace step 1:

> 1. Read `advisors/registry.yaml`. Parse the `advisors` list — each entry has: `id`, `name`, `prompt`, `domains` (list), `evaluation_expertise`, `best_for`, `not_for`. Read the `selection_guidelines` section for count rules, hard-exclude logic, and diversity preferences. If the YAML file doesn't exist or fails to parse, fall back to globbing `advisors/prompts/*.md` and parsing first lines for name/domain extraction.

with:

```markdown
1. Read `skills/_shared/resolve-advisor-source.md` and follow its procedure. Take the `advisors`
   list (each entry carries `id`, `name`, `domains`, `evaluation_expertise`, `best_for`, `not_for`,
   `absolute_prompt_path`, `source`) **and** the `selection_guidelines` block from its return — the
   resolver returns `selection_guidelines` as a plugin-canonical sibling of `advisors`. Use
   `selection_guidelines` for count rules, hard-exclude logic, and diversity preferences. If the
   resolver cannot be read, fall back to globbing `advisors/prompts/*.md` and parsing first lines
   for name/domain extraction (selection guidelines then default to: 2-3 critics, hard-exclude on
   `not_for`, prefer lens diversity). **Behavior note: this fallback path is intentionally
   plugin-only — after migration it will not surface local advisors. It fires only when the
   resolver file itself is unreadable (a plugin installation failure), not for absent or malformed
   local registries (those are handled by the resolver's own error paths).**
```

Then replace step 3:

> 3. Read each selected critic's full prompt file (the path listed in the registry entry).

with:

```markdown
3. Read each selected critic's full prompt file using that entry's `absolute_prompt_path` from the
   resolver (NOT the registry `prompt:` field, which is plugin-relative and mis-resolves local
   critics).
```

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_critique_panel_resolver.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/_shared/critique-panel-orchestration.md e2e/tests/test_critique_panel_resolver.py
git commit -m "feat: critique-panel reads advisors + selection_guidelines via resolver"
```

---

### Task 6: Route the research-mode advisor dispatch through the resolver

**Files:**
- Modify: `skills/brainstorming/modes/research.md` (Phase 3 auto-consult + Phase 4 Skeptic dispatch templates)
- Create: `e2e/tests/test_research_mode_resolver.py`

The Phase 3 auto-consult and Phase 4 Skeptic dispatch templates read `advisors/prompts/{advisor-id}.md` plugin-relative. Several routing examples name migrating advisors (`steven-hayes`, `blair-grubb`, and the long-COVID trio). After migration those prompts are no longer in the plugin, so the dispatch must resolve the path through the merged resolver. Keep the existing registry-authoritative note.

**Step 1: Write the failing test**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_research_mode_resolves_advisor_prompt_via_resolver():
    text = read("skills/brainstorming/modes/research.md")
    assert "resolve-advisor-source.md" in text, (
        "research-mode advisor dispatch must resolve prompt paths through the merged resolver, "
        "since migrating advisors leave the plugin"
    )


def test_research_mode_keeps_registry_authoritative_note():
    text = read("skills/brainstorming/modes/research.md")
    assert "registry.yaml` is authoritative" in text or "registry is authoritative" in text.lower()
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_research_mode_resolver.py -v`
Expected: FAIL — `test_research_mode_resolves_advisor_prompt_via_resolver` fails.

**Step 3: Edit `skills/brainstorming/modes/research.md`**

In Phase 3 ("Auto-consult domain advisors"), the sentence currently reads:

> The advisor's prompt file is at `advisors/prompts/{advisor-id}.md`.

Replace with:

```markdown
Resolve the advisor's prompt file path through `skills/_shared/resolve-advisor-source.md`: match
`{advisor-id}` in the resolver's returned `advisors` list and use that entry's
`absolute_prompt_path`. This finds advisors in the plugin OR the project-local repo — required
because health/therapy advisors now live in the user's personal repo, not the plugin. The
`advisors/registry.yaml` is authoritative for topic routing; extend the routing examples per the
merged set.
```

Update both dispatch templates (Phase 3 auto-consult and Phase 4 Skeptic) where they embed
`[Full contents of `advisors/prompts/{advisor-id}.md`]` / `[Full contents of `advisors/prompts/{skeptic-advisor-id}.md`]` to read "Full contents of the advisor prompt file at the resolved `absolute_prompt_path`".

Leave the topic-routing examples list intact (it already names `akiko-iwasaki`, `david-putrino`, `david-systrom`, `blair-grubb`, `steven-hayes`) — these resolve correctly via the merged set once they live in the personal repo and the session runs there.

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_research_mode_resolver.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/research.md e2e/tests/test_research_mode_resolver.py
git commit -m "feat: research-mode advisor dispatch resolves prompts via merged resolver"
```

---

### Task 7: Make authoring-mode engine selection use the merged advisor list

**Files:**
- Modify: `skills/brainstorming/modes/authoring.md` (Phase 1: Engine selection)
- Create: `e2e/tests/test_authoring_mode_resolver.py`

Phase 1 calls `contextual-recommendation.md` with entity type `framework-or-advisor`, which scores both registries internally. The advisor side must obtain the **merged** list (plugin + local) via the resolver and pass it through the dual-contract branch — otherwise project-local advisors are invisible to engine selection, defeating the parity goal.

**Step 1: Write the failing test**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_authoring_engine_selection_uses_merged_advisor_list():
    text = read("skills/brainstorming/modes/authoring.md")
    assert "resolve-advisor-source.md" in text, (
        "authoring engine selection must feed contextual-recommendation the merged advisor list"
    )
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_authoring_mode_resolver.py -v`
Expected: FAIL.

**Step 3: Edit `skills/brainstorming/modes/authoring.md`**

In Phase 1 ("Engine selection"), the invocation currently lists:

> - **Registries:** `frameworks/registry.yaml`, `advisors/registry.yaml`

Replace that bullet and add a note:

```markdown
- **Frameworks input:** the registry path `frameworks/registry.yaml`.
- **Advisors input:** the **pre-merged advisor list** from `skills/_shared/resolve-advisor-source.md`
  (plugin global + project-local, deduped, local-wins) — passed via contextual-recommendation's
  dual-contract list branch. Passing the plugin registry path here would make project-local
  advisors invisible to engine selection.
```

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_authoring_mode_resolver.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/brainstorming/modes/authoring.md e2e/tests/test_authoring_mode_resolver.py
git commit -m "feat: authoring engine selection uses merged advisor list"
```

---

# Part 2 — add-advisor: avatar removal + local-advisor DX

### Task 8: Remove avatar generation from add-advisor

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (Step 0 detection row + dashboard line, Step 5, Notes line, step renumbering)
- Create: `e2e/tests/test_add_advisor_no_avatar.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_add_advisor_has_no_avatar_generation_step():
    text = read("skills/add-advisor/SKILL.md")
    assert "Generate Avatar" not in text
    assert "avatar generation" not in text.lower()
    assert "Avatars:" not in text  # the Step 0 dashboard line
    assert "Review generated avatars" not in text


def test_add_advisor_steps_renumbered_contiguously():
    text = read("skills/add-advisor/SKILL.md")
    # After removing Step 5 (Generate Avatar), the remaining steps must renumber.
    # The framework step was Step 6 -> must now be a lower number; assert old labels gone.
    assert "### 5. Generate Avatar" not in text
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_add_advisor_no_avatar.py -v`
Expected: FAIL — avatar strings still present.

**Step 3: Edit `skills/add-advisor/SKILL.md`**

1. In the Step 0 infrastructure-detection table, delete the `| Avatar generation | ... | Avatar generation (Step 5) |` row.
2. In the Step 0 "Print summary" block, delete the `  Avatars:           {avatar dir} ...` line.
3. Delete the entire `### 5. Generate Avatar` section (heading through its "Continue with step 6 (non-blocking)" line).
4. In `## Notes`, delete the bullet `- Review generated avatars for likeness ...`.
5. Renumber the subsequent step headings so they are contiguous: `6. Add First Framework` → `5.`, `7. Create Eval Scenario` → `6.`, `8. Update the Registry` → `7.`, `9. Update Advisor and Framework Counts` → `8.`, `10. Commit` → `9.`. Update any in-text references to those step numbers (e.g., "Continue with step 6" references and the Step 6 framework-registry note) to match.

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_add_advisor_no_avatar.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/add-advisor/SKILL.md e2e/tests/test_add_advisor_no_avatar.py
git commit -m "feat: remove avatar generation from add-advisor"
```

---

### Task 9: Document the two-file local-advisor convention in add-advisor

**Files:**
- Modify: `skills/add-advisor/SKILL.md` (Notes section + the registry step)
- Test: `e2e/tests/test_add_advisor_no_avatar.py` (append assertions)

Because advisors have **no glob fallback** (unlike frameworks), a prompt file without a registry entry is a silent no-op. Document the two-file convention so it is discoverable from the tool, and note that the read side ignores the `prompt:` field.

**Step 1: Write the failing test (append)**

```python
def test_add_advisor_documents_two_file_convention():
    text = read("skills/add-advisor/SKILL.md")
    assert "advisors/registry.yaml" in text and "advisors/prompts/" in text
    assert "no glob fallback" in text.lower() or "silent no-op" in text.lower(), (
        "add-advisor must explain that a local advisor needs BOTH a registry entry and a prompt file"
    )


def test_add_advisor_notes_prompt_field_ignored_on_read():
    assert "ignored by the read side" in read("skills/add-advisor/SKILL.md"), (
        "add-advisor must note the read side ignores the prompt: field (it is metadata only)"
    )
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_add_advisor_no_avatar.py -v -k convention or prompt_field`
Expected: FAIL.

**Step 3: Edit `skills/add-advisor/SKILL.md`**

In the registry step (now `### 7. Update the Registry`), after the `prompt:` line in the example entry, add a note:

```markdown
> **Read-side note:** The `prompt:` field is written for human readability but is **ignored by the
> read side** — `skills/_shared/resolve-advisor-source.md` derives the prompt path from `id` + scope
> + the configured prompt-dir. Do not rely on `prompt:` to point the resolver anywhere.
```

In `## Notes`, add:

```markdown
- **Local advisors require two files.** Advisors have no glob fallback (unlike frameworks): a prompt
  file with no `advisors/registry.yaml` entry is a silent no-op — it will never appear in listings,
  panels, or contextual recommendation. When adding an advisor to a project-local repo, you MUST
  write both `advisors/registry.yaml` (full-schema entry) and `advisors/prompts/<id>.md`. This skill
  writes both; if you hand-author, do the same.
```

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_add_advisor_no_avatar.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/add-advisor/SKILL.md e2e/tests/test_add_advisor_no_avatar.py
git commit -m "docs: document two-file local-advisor convention in add-advisor"
```

---

# Part 3 — Migration guards (TDD)

These tests exist BEFORE the data migration so they catch a half-finished move. The framework→advisor reference guard is the real portability guarantee — no existing test scans it.

### Task 10: Framework→advisor dangling-reference guard

**Files:**
- Create: `e2e/tests/test_framework_advisor_references.py`

This guard passes NOW (every framework's `advisor:` resolves against the in-scope advisor set). It is the regression guard that turns RED if Part 4 removes a framework whose advisor stayed, or removes an advisor whose framework stayed. It is framed as a guard on existing behavior, so the TDD sequence is "write → verify it passes."

**Step 1: Write the guard test**

```python
"""Guard: every framework's advisor reference resolves against the in-scope advisor set.
This is the portability guarantee for the local-advisors migration — frameworks must move
WITH their advisors, or this goes red."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def _advisor_ids():
    with open(REPO / "advisors" / "registry.yaml") as f:
        data = yaml.safe_load(f)
    return {a["id"] for a in data["advisors"]}


def _frameworks():
    with open(REPO / "frameworks" / "registry.yaml") as f:
        data = yaml.safe_load(f)
    return data["frameworks"]


def test_every_framework_advisor_resolves():
    advisor_ids = _advisor_ids()
    dangling = [
        (e["id"], e["advisor"])
        for e in _frameworks()
        if e["advisor"] not in advisor_ids
    ]
    assert not dangling, (
        f"{len(dangling)} framework(s) reference an advisor not in advisors/registry.yaml — "
        f"the advisor must move WITH its frameworks: {dangling[:10]}"
    )


def test_no_framework_prompt_names_a_missing_advisor():
    """Scan each framework prompt.md first line ('You are {Advisor}, ...') and confirm the
    framework's registry advisor still resolves. Catches a prompt left behind after its
    advisor migrated."""
    advisor_ids = _advisor_ids()
    fw_dir = REPO / "frameworks"
    orphaned = []
    for e in _frameworks():
        prompt = fw_dir / e["id"] / "prompt.md"
        if not prompt.exists():
            continue
        if e["advisor"] not in advisor_ids:
            orphaned.append(e["id"])
    assert not orphaned, f"framework prompt(s) whose advisor no longer resolves: {orphaned[:10]}"
```

**Step 2: Run to verify it passes (guard on current state)**

Run: `pytest e2e/tests/test_framework_advisor_references.py -v`
Expected: PASS — all 151 framework advisor references currently resolve.

**Step 3: Commit**

```bash
git add e2e/tests/test_framework_advisor_references.py
git commit -m "test: add framework->advisor dangling-reference guard for migration"
```

---

### Task 11: Validate a project-local advisor registry against the schema

**Files:**
- Create: `e2e/fixtures/local-advisor-repo/advisors/registry.yaml`
- Create: `e2e/fixtures/local-advisor-repo/advisors/prompts/example-local-advisor.md`
- Modify: `e2e/tests/test_registry_schemas.py` (add a local-registry validation class)

The existing `test_prompt_paths_exist` resolves prompts against `REPO_ROOT`. A local registry's prompts resolve against its OWN root. Add a fixture local repo and validate it with the same required-fields schema, resolving prompt existence against the fixture root, and assert the count-match invariant holds there too.

**Step 1: Create the fixture local registry**

`e2e/fixtures/local-advisor-repo/advisors/registry.yaml`:

```yaml
advisors:
  - id: example-local-advisor
    name: "Example Local Advisor"
    summary: "A fixture advisor that exists only in a project-local repo."
    prompt: advisors/prompts/example-local-advisor.md
    domains: [fixture, local-merge]
selection_guidelines: "Plugin-canonical in production; present here only to mirror schema shape."
```

`e2e/fixtures/local-advisor-repo/advisors/prompts/example-local-advisor.md`:

```markdown
You are the Example Local Advisor, a fixture persona used to validate the local-advisor schema.

## The Voice
Plain, minimal — this file exists to satisfy the prompt-path resolution test.
```

**Step 2: Write the failing test (append a class to `test_registry_schemas.py`)**

```python
class TestLocalAdvisorRegistrySchema:
    """A project-local advisor registry must satisfy the same required-fields schema,
    with prompt paths resolved against its OWN root (not REPO_ROOT)."""

    FIXTURE_ROOT = REPO_ROOT / "e2e" / "fixtures" / "local-advisor-repo"

    @pytest.fixture
    def registry(self):
        path = self.FIXTURE_ROOT / "advisors" / "registry.yaml"
        assert path.exists(), f"Local advisor fixture registry not found at {path}"
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None and "advisors" in data
        return data

    def test_local_entries_have_required_fields(self, registry):
        for i, entry in enumerate(registry["advisors"]):
            missing = ADVISOR_REQUIRED_FIELDS - set(entry.keys())
            assert not missing, f"Local advisor entry {i} missing: {missing}"

    def test_local_prompt_paths_resolve_against_fixture_root(self, registry):
        for entry in registry["advisors"]:
            prompt_path = self.FIXTURE_ROOT / entry["prompt"]
            assert prompt_path.exists(), (
                f"Local advisor {entry['id']}: prompt not found at {entry['prompt']} "
                f"(resolved against fixture root, not REPO_ROOT)"
            )

    def test_local_entry_count_matches_prompts(self, registry):
        prompt_dir = self.FIXTURE_ROOT / "advisors" / "prompts"
        prompt_files = list(prompt_dir.glob("*.md"))
        assert len(registry["advisors"]) == len(prompt_files), (
            f"Local registry has {len(registry['advisors'])} entries but "
            f"{len(prompt_files)} prompt files"
        )
```

**Step 3: Run to verify it passes**

Run: `pytest e2e/tests/test_registry_schemas.py::TestLocalAdvisorRegistrySchema -v`
Expected: PASS.

**Step 4: Commit**

```bash
git add e2e/fixtures/local-advisor-repo e2e/tests/test_registry_schemas.py
git commit -m "test: validate project-local advisor registry against schema (fixture-rooted)"
```

---

# Part 4 — Data migration (mechanism must be in place)

> **Cross-repo model.** The destination is the user's personal repo `~/.claude/` (a git repo with
> no `advisors/`/`frameworks/` yet, auto-committed every ~10 min by a launchd agent, not a plugin).
> The loop writes files to `~/.claude/` via plain file I/O and runs **no `git` commands there** —
> the launchd agent (or the Post-Automation note) commits the personal repo. Plugin-side removals
> are committed to the plugin worktree branch as usual.
>
> **Land-then-remove ordering** within each cluster task: copy to `~/.claude/` and verify FIRST,
> then remove from the plugin. Content is never lost if the loop is interrupted.
>
> **Count-balanced commits:** each cluster removal commit removes advisor entries + their prompt
> files AND those advisors' framework entries + folders together, so
> `test_registry_schemas.py::test_entry_count_matches_prompts` and `test_entry_count_matches_directories`
> stay green at every commit boundary.
>
> **Derive frameworks from the LIVE registry, never from memory or the stale README.** For each
> advisor `<id>`, its frameworks are the entries where `advisor: <id>` in `frameworks/registry.yaml`.

### Task 12: Create the personal-repo skeleton

**Files (all outside the plugin — plain file writes, no git):**
- Create: `~/.claude/advisors/registry.yaml`
- Create: `~/.claude/advisors/prompts/` (directory)
- Create: `~/.claude/frameworks/registry.yaml`
- Create: `~/.claude/frameworks/` (directory)

**Step 1: Create the personal advisor registry skeleton**

Write `~/.claude/advisors/registry.yaml` with an empty advisors list plus the plugin's
`selection_guidelines` block copied verbatim from the plugin `advisors/registry.yaml` (so panels
run correctly if invoked while cwd is `~/.claude/`):

```yaml
# Project-local advisor registry for ~/.claude/.
# Merges with the aligned plugin's global advisors via skills/_shared/resolve-advisor-source.md.
advisors: []
selection_guidelines:
  # <copy the full selection_guidelines block from the plugin advisors/registry.yaml here>
```

**Step 2: Create the personal framework registry skeleton**

Write `~/.claude/frameworks/registry.yaml` with the plugin's `deliverable_type` taxonomy header
block copied verbatim (top ~2000 chars of the plugin `frameworks/registry.yaml` — the documented
taxonomy) followed by an empty list:

```yaml
# Project-local framework registry for ~/.claude/.
# <copy the deliverable_type taxonomy doc block from the plugin frameworks/registry.yaml here>
frameworks: []
```

**Step 3: Create the prompt and framework directories**

```bash
mkdir -p ~/.claude/advisors/prompts ~/.claude/frameworks
```

**Step 4: Verify the skeleton parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('$HOME/.claude/advisors/registry.yaml')); yaml.safe_load(open('$HOME/.claude/frameworks/registry.yaml')); print('personal registries parse OK')"
```
Expected: `personal registries parse OK`

**Step 5: Commit (plan-file progress only — no plugin source changed)**

```bash
git add docs/plans/2026-05-23-local-advisors-plan.md
git commit -m "chore: scaffold personal-repo advisor/framework registries for migration"
```

> The `~/.claude/` files are intentionally NOT committed by the loop. The launchd auto-commit agent
> commits them; see Manual Steps (Post-Automation).

---

### Task 13: Migrate the therapy / mental-health cluster

**Advisors (6):** `byron-katie`, `gabor-mate`, `marsha-linehan`, `martin-seligman`, `richard-schwartz`, `steven-hayes`

**Files:**
- Create (personal): `~/.claude/advisors/prompts/<id>.md` for each of the 6 advisors
- Modify (personal): `~/.claude/advisors/registry.yaml`, `~/.claude/frameworks/registry.yaml`
- Create (personal): `~/.claude/frameworks/<framework-id>/` for each owned framework
- Modify (plugin): `advisors/registry.yaml`, `frameworks/registry.yaml`, `frameworks/_outliers.json`
- Delete (plugin): the 6 prompt files + each owned framework folder

**Step 1: Identify this cluster's frameworks from the live registry**

For each of the 6 advisors, find owned frameworks:

For each of the 6 advisor IDs, identify owned frameworks using the **Grep tool** (NOT `Bash grep` — `Bash(grep *)` is blocked by the loop's permission system). Use:

```python
python3 -c "
import yaml
ids = ['byron-katie','gabor-mate','marsha-linehan','martin-seligman','richard-schwartz','steven-hayes']
fw = yaml.safe_load(open('frameworks/registry.yaml'))
for aid in ids:
    owned = [e['id'] for e in fw['frameworks'] if e['advisor'] == aid]
    print(aid, '->', owned)
"
```

(e.g., `richard-schwartz` owns `8-cs-self-leadership`, `enneagram-typing`, `ifs-parts-work`, `polarization-mediator`). Build the complete framework-id list for the cluster. Note that `enneagram-typing` (richard-schwartz) is the one cluster framework also listed in `frameworks/_outliers.json`.

**Step 2: Land to the personal repo (file writes only)**

- Copy each advisor prompt: `advisors/prompts/<id>.md` → `~/.claude/advisors/prompts/<id>.md`.
- Append each advisor's full-schema entry to `~/.claude/advisors/registry.yaml` (copy the entry block verbatim from the plugin registry).
- For each owned framework folder, copy the whole directory: `frameworks/<fw-id>/` → `~/.claude/frameworks/<fw-id>/`.
- Append each owned framework's registry entry to `~/.claude/frameworks/registry.yaml` (copy verbatim).

**Step 3: Verify the personal repo received the cluster**

```bash
ls ~/.claude/advisors/prompts/byron-katie.md ~/.claude/advisors/prompts/gabor-mate.md ~/.claude/advisors/prompts/marsha-linehan.md ~/.claude/advisors/prompts/martin-seligman.md ~/.claude/advisors/prompts/richard-schwartz.md ~/.claude/advisors/prompts/steven-hayes.md
python3 -c "import yaml; print('local advisors:', len(yaml.safe_load(open('$HOME/.claude/advisors/registry.yaml'))['advisors']))"
```
Expected: all 6 prompts listed; local advisors count == 6.

**Step 4: Remove from the plugin (one count-balanced commit)**

- Edit `advisors/registry.yaml`: delete the 6 advisor entry blocks (match each on its unique `- id: <id>` anchor through the line before the next `- id:`). Preserve all surrounding formatting and the `selection_guidelines` block.
- Delete the 6 plugin prompt files: `advisors/prompts/<id>.md`.
- Edit `frameworks/registry.yaml`: delete the cluster's framework entry blocks (match on each `- id: <fw-id>`).
- Delete each cluster framework folder: `frameworks/<fw-id>/`.
- Edit `frameworks/_outliers.json`: delete the `"enneagram-typing": { ... }` line (and fix the trailing comma so the JSON stays valid). This MUST be in this commit.

**Step 5: Verify plugin invariants (scoped tests)**

Run: `pytest e2e/tests/test_registry_schemas.py e2e/tests/test_framework_advisor_references.py -v`
Expected: PASS — advisor count still == prompt count, framework count still == folder count, no dangling refs, `test_outlier_frameworks_have_correct_metadata` green (enneagram-typing removed from both registry and `_outliers.json`).

**Step 6: Commit the plugin removal**

```bash
git add advisors/registry.yaml frameworks/registry.yaml frameworks/_outliers.json advisors/prompts frameworks
git commit -m "feat: migrate therapy/mental-health advisors + frameworks out of plugin"
```

---

### Task 14: Migrate the health-autonomic + long-COVID cluster

**Advisors (6):** `blair-grubb`, `italo-biaggioni`, `roy-freeman`, `akiko-iwasaki`, `david-putrino`, `david-systrom`

> `akiko-iwasaki`, `david-putrino`, `david-systrom` own **0 frameworks** (verified). They migrate as prompt + registry entry only.

**Files:** same shape as Task 13 (personal land of 6 prompts + their autonomic frameworks; plugin removal of the same). `frameworks/_outliers.json` is NOT touched (no outliers in this cluster).

**Step 1: Identify this cluster's frameworks from the live registry**

Use the Grep tool or python3 one-liner (NOT `Bash grep`) for each of the 6 advisor IDs:

```python
python3 -c "
import yaml
ids = ['blair-grubb','italo-biaggioni','roy-freeman','akiko-iwasaki','david-putrino','david-systrom']
fw = yaml.safe_load(open('frameworks/registry.yaml'))
for aid in ids:
    owned = [e['id'] for e in fw['frameworks'] if e['advisor'] == aid]
    print(aid, '->', owned)
"
```

(e.g., `blair-grubb` owns `multi-system-approach-pots`, `pots-subtype-recognition`, `quality-of-life-focus`; `roy-freeman` and `italo-biaggioni` own autonomic frameworks; the three long-COVID advisors own none.)

**Step 2: Land to the personal repo (file writes only)** — same procedure as Task 13 Step 2.

**Step 3: Verify the personal repo received the cluster**

```bash
ls ~/.claude/advisors/prompts/blair-grubb.md ~/.claude/advisors/prompts/italo-biaggioni.md ~/.claude/advisors/prompts/roy-freeman.md ~/.claude/advisors/prompts/akiko-iwasaki.md ~/.claude/advisors/prompts/david-putrino.md ~/.claude/advisors/prompts/david-systrom.md
python3 -c "import yaml; print('local advisors:', len(yaml.safe_load(open('$HOME/.claude/advisors/registry.yaml'))['advisors']))"
```
Expected: all 6 prompts listed; local advisors count == 12 (6 from Task 13 + 6 here).

**Step 4: Remove from the plugin (one count-balanced commit)** — delete the 6 advisor entries + prompts and this cluster's framework entries + folders. No `_outliers.json` change.

**Step 5: Verify plugin invariants (scoped tests)**

Run: `pytest e2e/tests/test_registry_schemas.py e2e/tests/test_framework_advisor_references.py -v`
Expected: PASS.

**Step 6: Commit**

```bash
git add advisors/registry.yaml frameworks/registry.yaml advisors/prompts frameworks
git commit -m "feat: migrate autonomic + long-COVID advisors + frameworks out of plugin"
```

---

### Task 15: Migrate the movement / body cluster

**Advisors (7):** `andreo-spina`, `kelly-starrett`, `shirley-sahrmann`, `stuart-mcgill`, `patrick-mckeown`, `deb-dana`, `irene-lyon`

> This is the final cluster — it must drain the remaining migrating advisors so the plugin holds exactly 57 advisors afterward. Derive each advisor's frameworks from the live registry; some of these advisors may own 0 frameworks (e.g., `deb-dana`, `irene-lyon`, `patrick-mckeown` — verify with grep, do not assume).

**Files:** same shape as Task 13 (personal land; plugin removal). No `_outliers.json` change.

**Step 1: Identify this cluster's frameworks from the live registry** — Use the Grep tool or python3 one-liner (NOT `Bash grep`) for each of the 7 advisor IDs:

```python
python3 -c "
import yaml
ids = ['andreo-spina','kelly-starrett','shirley-sahrmann','stuart-mcgill','patrick-mckeown','deb-dana','irene-lyon']
fw = yaml.safe_load(open('frameworks/registry.yaml'))
for aid in ids:
    owned = [e['id'] for e in fw['frameworks'] if e['advisor'] == aid]
    print(aid, '->', owned)
"
```

**Step 2: Land to the personal repo (file writes only)** — same procedure as Task 13 Step 2.

**Step 3: Verify the personal repo holds the full migration set**

```bash
python3 -c "import yaml; a=len(yaml.safe_load(open('$HOME/.claude/advisors/registry.yaml'))['advisors']); f=len(yaml.safe_load(open('$HOME/.claude/frameworks/registry.yaml'))['frameworks']); print('local advisors:', a, 'local frameworks:', f)"
ls ~/.claude/advisors/prompts/*.md | wc -l
```
Expected: `local advisors: 19`, `local frameworks: 39`, and 19 prompt files.

**Step 4: Remove from the plugin (one count-balanced commit)** — delete the 7 advisor entries + prompts and this cluster's framework entries + folders.

**Step 5: Verify the plugin reached the post-migration steady state (scoped tests)**

```bash
python3 -c "import yaml; a=yaml.safe_load(open('advisors/registry.yaml')); print('plugin advisors:', len(a['advisors']))"
python3 -c "import yaml; f=yaml.safe_load(open('frameworks/registry.yaml')); print('plugin frameworks:', len(f['frameworks']))"
pytest e2e/tests/test_registry_schemas.py e2e/tests/test_framework_advisor_references.py -v
```
Expected: `plugin advisors: 57`, `plugin frameworks: 112`, all scoped tests PASS.

**Step 6: Commit**

```bash
git add advisors/registry.yaml frameworks/registry.yaml advisors/prompts frameworks
git commit -m "feat: migrate movement/body advisors + frameworks out of plugin"
```

---

# Part 5 — Plugin metadata cleanup

### Task 16: Regenerate HTML catalogs and correct published counts

**Files:**
- Modify: `docs/advisor-catalog.html`, `docs/framework-catalog.html` (regenerated)
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`

**Step 1: Regenerate the HTML catalogs from the post-migration registries**

```bash
python3 scripts/generate-catalogs.py
```
Expected output: `Wrote docs/framework-catalog.html (112 entries)` and `Wrote docs/advisor-catalog.html (57 entries)`.

**Step 2: Update the published counts**

In `.claude-plugin/plugin.json` AND `.claude-plugin/marketplace.json`, replace `76 advisor personas, 151 frameworks` with `57 advisor personas, 112 frameworks` in the `description` field. Both files must match.

**Step 3: Verify**

```bash
grep -o "57 advisor personas, 112 frameworks" .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: both files print the new count string.

**Step 4: Commit**

```bash
git add docs/advisor-catalog.html docs/framework-catalog.html .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: regenerate catalogs and update counts to 57 advisors / 112 frameworks"
```

---

### Task 17: Regenerate the markdown READMEs from the post-migration registries

**Files:**
- Modify: `advisors/README.md`, `frameworks/README.md`
- Create: `e2e/tests/test_readme_freshness.py`

The two markdown READMEs are unreferenced human docs that were already stale before this migration (claimed 65 advisors / 138 frameworks against an actual 76 / 151, and listed the long-removed `benjamin-levine` and `copywriter`). There is no generator. Rather than hand-patch the migration delta onto stale tables, regenerate both READMEs from the post-migration registries so they are correct, and add a freshness guard so they cannot silently rot to the same degree again. (A proper generator script is the longer-term fix — filed as KB-151.)

**Step 1: Write the failing freshness guard**

```python
"""Guard the markdown READMEs against the staleness that motivated their regeneration:
headline counts must match the registries, and no migrated/phantom advisor id may appear."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

GONE_IDS = [
    "benjamin-levine", "copywriter",
    "andreo-spina", "blair-grubb", "italo-biaggioni", "kelly-starrett",
    "patrick-mckeown", "roy-freeman", "shirley-sahrmann", "stuart-mcgill",
    "deb-dana", "irene-lyon", "akiko-iwasaki", "david-putrino", "david-systrom",
    "byron-katie", "gabor-mate", "marsha-linehan", "martin-seligman",
    "richard-schwartz", "steven-hayes",
    # phantom framework IDs — benjamin-levine's 4 frameworks (folders already absent, still in README)
    "autonomic-fatigue-vs-training-fatigue", "cardiac-deconditioning-model",
    "heart-rate-reserve-training-zones", "levine-protocol",
]


def _count(rel, key):
    with open(REPO / rel) as f:
        return len(yaml.safe_load(f)[key])


def test_advisor_readme_headline_count_matches_registry():
    n = _count("advisors/registry.yaml", "advisors")
    text = (REPO / "advisors" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"advisors/README.md headline must show {n} advisors"


def test_framework_readme_headline_count_matches_registry():
    n = _count("frameworks/registry.yaml", "frameworks")
    text = (REPO / "frameworks" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"frameworks/README.md headline must show {n} frameworks"


def test_readmes_drop_migrated_and_phantom_ids():
    adv = (REPO / "advisors" / "README.md").read_text()
    fw = (REPO / "frameworks" / "README.md").read_text()
    for gid in GONE_IDS:
        assert gid not in adv, f"advisors/README.md still references migrated/phantom id: {gid}"
        assert gid not in fw, f"frameworks/README.md still references migrated/phantom id: {gid}"
```

**Step 2: Run to verify it fails**

Run: `pytest e2e/tests/test_readme_freshness.py -v`
Expected: FAIL — headline counts are stale and migrated/phantom ids still appear.

**Step 3: Regenerate the READMEs from the registries**

Read the post-migration `advisors/registry.yaml` and `frameworks/registry.yaml`, then rewrite:

- `advisors/README.md`: headline `<N> advisors | <profiled> profiled | <unprofiled> unprofiled` (profiled = entries carrying `evaluation_expertise`/`best_for`); the Quick Reference table (one row per registry advisor: ID, Name, Domains, Summary); the Profiled / Unprofiled lists; the Selection Guidelines block (copy from the registry's `selection_guidelines`).
- `frameworks/README.md`: headline `<N> frameworks across <C> categories`; the per-category count table; the Quick Reference table (one row per framework: ID, Name, Advisor, Category, Use When); the By Category sections.

Every row must come from the post-migration registry — none of the `GONE_IDS` may appear, and the headline counts must equal the registry lengths (57 advisors, 112 frameworks).

**Step 4: Run to verify it passes**

Run: `pytest e2e/tests/test_readme_freshness.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add advisors/README.md frameworks/README.md e2e/tests/test_readme_freshness.py
git commit -m "docs: regenerate advisor/framework READMEs from post-migration registries"
```

---

## Manual Steps (Post-Automation)

> Complete these after the autopilot finishes. They cannot run inside the unattended loop.

1. **Commit the personal repo (`~/.claude/`).** The migration wrote the 19 advisor prompts + `advisors/registry.yaml` and the 39 framework folders + `frameworks/registry.yaml` into `~/.claude/` as plain files. The launchd auto-commit agent commits `~/.claude/` every ~10 minutes; to commit immediately, run `git -C ~/.claude add advisors frameworks && git -C ~/.claude commit -m "feat: receive health/therapy advisors + frameworks from aligned plugin"`. Verify the merge works by listing advisors from a session whose cwd is `~/.claude/` (you should see the 19 local advisors annotated `(local)` alongside the 57 plugin advisors).
2. **Re-baseline the eval surface.** 19 advisors + 39 frameworks left the plugin and `skills/_shared/resolve-advisor-source.md` is a new LLM surface. Run `/aligned:eval-audit` (manual-invocation-only skill) to confirm eval scenario coverage matches the new surface.

## Eval Scenarios

This plan changes the advisor **read path** (discovery/resolution) and the eval **surface** (advisors leave the plugin), but it does NOT change any advisor's voice, framework content, or prompt-construction behavior — the prompt files move unmodified. Therefore no new per-advisor eval scenarios are required. The required eval action is the surface re-baseline via `/aligned:eval-audit` (Post-Automation step 2). If `eval-audit` reports that migrated advisors' scenarios should move with them, relocate those scenario files to the personal repo's eval infrastructure (only if it exists — `~/.claude/` currently has none).

---

## Decision Log

### Summary

| # | Decision | Choice Made | Alternatives Considered |
|---|----------|-------------|-------------------------|
| 1 | Cross-repo write model for the migration | Loop writes `~/.claude/` files only (no `git` there); launchd/Post-Automation commits it | Cross-repo `git` in the loop; fully manual migration |
| 2 | Migration commit granularity | 3 cluster-atomic commits (advisors + their frameworks together) | Per-advisor atomic (19 commits); batch-by-type |
| 3 | Land-then-remove ordering | Copy + verify personal repo first, then remove from plugin | Remove-then-restore; simultaneous |
| 4 | Source of each advisor's framework set | Derive from live `frameworks/registry.yaml` (`advisor: <id>`) | Enumerate in plan from the README |
| 5 | Registry editing mechanism | LLM Edit on contiguous entry blocks (preserves YAML comments/taxonomy) | PyYAML round-trip script; add ruamel dep |
| 6 | Markdown READMEs | Regenerate fully from post-migration registries + freshness guard | Hand-patch the migration delta (design's literal step 4) |
| 7 | `_outliers.json` enneagram-typing removal | Folded into Task 13's commit (same commit as the framework) | Separate cleanup task |
| 8 | Personal-repo destination | `~/.claude/` hard-coded in this plan | Parameterize; prompt at runtime |
| 9 | eval-audit | Post-Automation manual step | Loop task |
| 10 | Test style for the resolver | Markdown-substring assertions (`test_shared_runners.py` style) | Behavioral fixture-repo test |

### Appendix: Decision Details

#### Decision 1: Cross-repo write model
**Chose:** The Ralph loop writes the migrated files into `~/.claude/` via plain file I/O and runs **no `git` commands** in that repo. The plugin-side removals commit to the worktree branch as normal; the personal repo is committed by its launchd auto-commit agent (or the Post-Automation note).
**Why:** `~/.claude/` is a separate git repo with a launchd agent committing every ~10 minutes (per the global CLAUDE.md). Running `git add/commit` in `~/.claude/` from inside a plugin-worktree loop entangles two repos' git state and races the auto-commit agent. File writes are race-free (the agent simply commits whatever files exist). This keeps the loop's git operations confined to one repo while still moving the data.
**Alternatives rejected:**
- *Cross-repo git in the loop:* fragile — concurrent launchd commits and two-index management are exactly the kind of thing that strands work or produces conflict states an unattended loop can't resolve.
- *Fully manual migration:* the moves are mechanical and well-specified; forcing the user to hand-move 19 prompts + 39 folders wastes the autopilot's value. The genuinely manual part (the personal-repo commit + eval re-baseline) is already in Post-Automation.

#### Decision 2: Cluster-atomic commit granularity
**Chose:** Three cluster removal commits (therapy; autonomic+long-COVID; movement/body), each removing its advisors' registry entries + prompt files AND those advisors' framework entries + folders together.
**Why:** The design's stated invariant is "an interruption never leaves the count-match invariant red." A commit that removes advisors and their frameworks *together* keeps both `test_entry_count_matches_prompts` and `test_entry_count_matches_directories` green at every commit boundary — exactly satisfying the invariant. Three commits is enough to honor it without 19 near-identical tasks bloating the plan and the loop.
**Alternatives rejected:**
- *Per-advisor atomic (19 commits):* the design's literal phrasing, but it produces 19 nearly identical tasks. Same invariant guarantee as clustering, far more plan text and loop iterations.
- *Batch-by-type (all advisors, then all frameworks):* explicitly warned against by the design — it leaves the count invariant red between the advisor batch and the framework batch.

#### Decision 3: Land-then-remove ordering
**Chose:** Within each cluster task, copy to `~/.claude/` and verify the personal repo received the files BEFORE removing them from the plugin.
**Why:** If the loop is interrupted mid-cluster, the worst case is duplicated advisors (present in both repos), which the resolver handles via dedupe/local-wins — no data loss. Remove-first would risk a window where content exists nowhere committed.
**Alternatives rejected:** *Remove-then-restore* (data-loss window); *simultaneous* (not possible across two separate file trees in one atomic step).

#### Decision 4: Derive frameworks from the live registry
**Chose:** Each migration task derives an advisor's framework set by grepping `advisor: <id>` in the live `frameworks/registry.yaml`.
**Why:** The `frameworks/README.md` is content-stale (claims 138, actual 151; still lists removed `benjamin-levine` frameworks). A hand-enumeration in the plan drifts from reality — a trial hand-count produced 40 where the live registry has exactly 39. The registry is authoritative; the plan instructs the executor to read it.
**Alternatives rejected:** *Enumerate framework ids in the plan* — guaranteed to embed the stale README's errors.

#### Decision 5: LLM Edit-based registry removal
**Chose:** Remove entries by editing contiguous `- id: <id>` … blocks with the Edit tool, preserving all surrounding YAML.
**Why:** `frameworks/registry.yaml` carries a documented `deliverable_type` taxonomy header block (asserted by `test_registry_documents_deliverable_type_taxonomy` against the first 2000 chars) and `advisors/registry.yaml` carries the `selection_guidelines` block and inline comments. A PyYAML `safe_load`/`dump` round-trip destroys comments and reorders keys, breaking that test and the file's readability. Targeted text edits preserve everything.
**Alternatives rejected:** *PyYAML round-trip script* (destroys comments/taxonomy); *add ruamel.yaml* (new dependency in `e2e/requirements.txt` for a one-time migration — not worth it).

#### Decision 6: Regenerate the markdown READMEs
**Chose:** Regenerate `advisors/README.md` and `frameworks/README.md` from the post-migration registries, guarded by a freshness test, rather than hand-patching the migration delta.
**Why:** The design's step 4 says to fix the count "65 → 57" and remove specific stale entries — but the live registry holds 76 advisors, so "65" is already wrong, and the READMEs are missing 11 advisors / 13 frameworks added since they were last touched. Hand-patching a doubly-stale, generator-less file bakes in an incorrect number and leaves it inconsistent. Regenerating from the authoritative registries fixes the migration delta AND the pre-existing staleness, which matches the documented preference to fix the source rather than patch around it. The READMEs are unreferenced by any skill, so a full rewrite carries no runtime risk. A real generator script (making the "auto-generated" footer true) is the durable fix, filed as **KB-151**.
**Alternatives rejected:** *Hand-patch the design's literal delta* — embeds the wrong "65→57" count and leaves the file stale.

#### Decision 7: Fold the `_outliers.json` edit into Task 13
**Chose:** Remove `enneagram-typing` from `frameworks/_outliers.json` in the same commit that removes the `enneagram-typing` framework (Task 13, the richard-schwartz cluster).
**Why:** `test_outlier_frameworks_have_correct_metadata` is parametrized over `_outliers.json` and asserts each outlier exists in the registry. Removing the framework without the outlier entry (or vice versa) turns that test red. Same-commit removal keeps it green.
**Alternatives rejected:** *Separate cleanup task* — opens a window where the outlier entry references a removed framework.

#### Decision 8: Hard-code `~/.claude/` as the destination
**Chose:** Reference `~/.claude/` directly as the migration destination.
**Why:** This is a plan (an environment-specific artifact in `docs/plans/`), not a distributed skill, and the design scoped the migration to "personal repo only." `~/.claude/` is verified as the user's personal skills repo (a git repo, not a plugin, no `advisors/` yet). Parameterizing a one-time personal migration adds ceremony with no benefit.
**Alternatives rejected:** *Parameterize / prompt at runtime* — unnecessary indirection for a one-shot move; the autopilot is unattended, so a runtime prompt isn't even available.

#### Decision 9: eval-audit as a Post-Automation step
**Chose:** Surface the eval-surface re-baseline as a Post-Automation manual step.
**Why:** `eval-audit` is documented as manual-invocation-only (global CLAUDE.md). Invoking another skill mid-Ralph-loop is unsupported and the re-baseline is a judgment-bearing review, not a mechanical task.
**Alternatives rejected:** *Loop task* — violates the skill's manual-only contract and would need human review of its output.

#### Decision 10: Markdown-substring tests for the resolver
**Chose:** Test the resolver and rewired read paths with markdown-substring/section assertions (the `test_shared_runners.py` style).
**Why:** `resolve-advisor-source.md` is a procedure an LLM follows, not executable code — the harness has no precedent for behavioral fixture-repo tests of these procedures, and the existing shared-runner tests assert documented behavior as substrings. Matching that precedent keeps the suite consistent and runnable without a new test harness.
**Alternatives rejected:** *Behavioral fixture-repo test* — no harness support; would require building a merge simulator the project doesn't have.


