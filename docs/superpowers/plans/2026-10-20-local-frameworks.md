# Project-Local Frameworks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A project repo can keep its own `frameworks/` (registry + folders) at its root, and every framework read path in the plugin merges it with the plugin's frameworks, local winning on a matching id — the same way project-local advisors already work.

**Architecture:** One new shared procedure, `skills/_shared/resolve-framework-source.md`, mirrors `skills/_shared/resolve-advisor-source.md`. Every caller that read `frameworks/registry.yaml` directly calls it instead. `contextual-recommendation.md` gains a pre-merged framework list input. The framework runner resolves the framework's advisor through `resolve-advisor-source.md`, so a local framework with a local advisor speaks in the project's advisor prompt.

**Tech Stack:** Markdown skill procedures read by Claude; pytest text and fixture tests in `e2e/tests/`; promptfoo eval scenarios in `e2e/scenarios/` run with `npm run eval -- <scenario>` from `e2e/`.

**Spec:** Eric's request of 2026-10-20 (pasted into the session; reproduced as the "What to build" list below).

1. Shared resolver `skills/_shared/resolve-framework-source.md`, parallel to the advisor resolver: plugin registry (`source: plugin`) + `<project-cwd>/frameworks/registry.yaml` (`source: local`), dedupe by id with local winning, absolute prompt path per entry (plugin root for plugin, project-cwd for local). No local registry → plugin-only. Malformed local YAML → plugin-only plus a one-line warning naming the file. Local folders with no registry entry still found by glob.
2. Every framework read path calls it (`grep -rln "frameworks/registry.yaml" skills scripts e2e`): use-framework (listing, matching, runner path), contextual-recommendation (frameworks accept a pre-merged list), advisor-runner, brainstorming (SKILL.md, modes/authoring.md, authoring-critique-checklist.md). Local frameworks marked `(local)` in listings.
3. add-framework and add-advisor write to the project's own `frameworks/registry.yaml` in a project repo, creating it if needed, with the parse-after-append check. Plugin counts (README, plugin.json, marketplace.json) only when writing to the plugin itself.
4. framework-runner and advisor-runner find the advisor through resolve-advisor-source, so a local framework with a local advisor loads that advisor's prompt from the project.
5. Tests in e2e/tests for: no local registry, local registry, local wins on duplicate id, malformed local YAML degrades with warning, unregistered local folder found by glob, local framework with local advisor. Update trigger-map.yaml and eval-surface.yaml. Run only the touched scenarios and report their cost.
6. Docs: plugin CLAUDE.md "Registries — Sources of Truth" and README.md. Version bump.

Done: in `/Users/ericpage/software/moments`, `/aligned:use-framework` lists all seven local frameworks marked (local); "/aligned:use-framework I need to write a reminder email to people who haven't written" recommends priming unnamed; `/aligned:use-framework priming` runs it in Priya Parker's voice from moments' `advisors/prompts/priya-parker.md`.

## Global Constraints

- Internal references use the `skills/` prefix, never `~/.claude/skills/` (repo CLAUDE.md Path Rule).
- Portability: nothing names Eric's machine or the moments repo. Fixtures are generic.
- Do not bump the version by hand. `scripts/hooks/pre-commit` bumps the patch in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` on skill commits. Tests may assert the two match, never a specific number.
- `skills/_shared/` files do not carry a Path Resolution note (see the note at the top of `resolve-advisor-source.md`).
- The `prompt:`-style stored path is not used for resolution; local entries resolve against project-cwd.
- Never run `npm run eval -- --all`. Run only scenarios named in Task 7.
- Commit messages use plain `-m "..."`, no heredoc, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A local framework whose id matches a plugin framework (e.g. a project overriding `fear-setting`) must list once, as `(local)`, and run from the project folder — not twice, not from the plugin. Pinned by Task 1's oracle test `test_merge_local_wins_on_duplicate_id` and Task 3's text test.
2. A local framework folder with `prompt.md` but no registry entry must still list and run. Pinned by `test_merge_finds_unregistered_local_folder_by_glob`.
3. A local framework whose `advisor` is a plugin advisor (e.g. a project framework for `april-dunford`) must load the plugin advisor's prompt; a local one whose advisor is local must load the project's. Pinned by `test_local_framework_advisor_resolves_in_merged_advisors`.
4. add-framework run inside the plugin repo itself must still write the plugin registry and update counts; run in a project it must not touch README/plugin.json. Pinned by Task 5's text tests.
5. Contextual recommendation run with a merged list must score local frameworks — otherwise moments' `priming` stays invisible. Pinned by Task 7's eval scenario.

---

### Task 1: The framework resolver, fixtures, and merge tests

**Files:**
- Create: `skills/_shared/resolve-framework-source.md`
- Create: `e2e/fixtures/local-advisor-repo/frameworks/registry.yaml`
- Create: `e2e/fixtures/local-advisor-repo/frameworks/example-local-framework/prompt.md`
- Create: `e2e/fixtures/local-advisor-repo/frameworks/unregistered-local-framework/prompt.md`
- Create: `e2e/fixtures/local-advisor-repo/frameworks/fear-setting/prompt.md` (local override of a plugin id)
- Create: `e2e/fixtures/local-malformed-repo/frameworks/registry.yaml` (deliberately invalid YAML)
- Create: `e2e/tests/test_resolve_framework_source.py`
- Modify: `e2e/tests/test_registry_schemas.py` (add `TestLocalFrameworkRegistrySchema`)
- Modify: `e2e/eval-surface.yaml` (add `skills/_shared/resolve-framework-source.md` after the advisor resolver line)

**Interfaces:**
- Produces: the resolver's return contract, which every later task couples to:

```
{
  frameworks: [
    { id, name, advisor, purpose, category, domains, use_when,
      deliverable_type?, default_critic_advisors?, required_documents?, helpful_documents?,
      absolute_framework_dir, absolute_prompt_path, source: "plugin" | "local",
      registered: true | false }
  ]
}
```

  `absolute_framework_dir = <scope-root>/frameworks/<id>/`; `absolute_prompt_path = <absolute_framework_dir>prompt.md`; `<scope-root>` is plugin-root for `source: "plugin"`, project-cwd for `source: "local"`. Unregistered local folders get `registered: false`, `id` = folder name, `name` and `advisor` parsed from the first line of `prompt.md` (`You are {Advisor}, guiding someone through {Framework} - {purpose}.`), and empty `domains`/`use_when`.
- Produces: the oracle function `merge_frameworks(plugin_root: Path, project_root: Path) -> tuple[list[dict], list[str]]` (entries, warnings) defined inside `test_resolve_framework_source.py`. It is the executable statement of the procedure; it is test-only.

- [ ] **Step 1: Write the fixtures.** `local-advisor-repo/frameworks/registry.yaml` has two entries with the full framework schema (`id, name, advisor, purpose, category, domains, use_when`): `example-local-framework` (advisor `example-local-advisor`, domains `[fixture, local-merge]`) and `fear-setting` (advisor `example-local-advisor`, name `"Fear Setting (local override)"`). Each registered id has a folder with a `prompt.md` whose first line follows the standard format. `unregistered-local-framework/prompt.md` exists with no registry entry. `local-malformed-repo/frameworks/registry.yaml` contains `frameworks:\n  - id: broken\n    name: [unclosed`.

- [ ] **Step 2: Write the failing tests** in `e2e/tests/test_resolve_framework_source.py`, in the style of `test_resolve_advisor_source.py`:
  - Text tests on the resolver: `test_resolver_file_exists`; `test_resolver_documents_plugin_canonical_then_local_merge` (mentions `canonical`, `registry.yaml`, `<project-cwd>/frameworks/registry.yaml`); `test_resolver_documents_dedupe_before_return_local_wins`; `test_resolver_documents_scope_roots` (`plugin-root`, `project-cwd`, `absolute_framework_dir`, `absolute_prompt_path`); `test_resolver_documents_glob_for_unregistered_local_folders` (`frameworks/*/prompt.md`, `registered`); `test_resolver_documents_error_paths` (absent → plugin-only; `malformed` + `warning` + names the file; resolved prompt missing → runner fails closed); `test_resolver_documents_return_contract` (each field in the contract above); `test_resolver_points_advisor_lookup_at_resolve_advisor_source`; `test_resolver_is_in_eval_surface`.
  - Oracle tests using `merge_frameworks`, with `PLUGIN = REPO` and the fixtures as project roots:
    - `test_merge_with_no_local_registry_is_plugin_only` — project root = an empty `tmp_path`; result ids == plugin registry ids, all `source == "plugin"`, no warnings.
    - `test_merge_with_local_registry_adds_local_entries` — `example-local-framework` present, `source == "local"`, `absolute_prompt_path == FIXTURE/frameworks/example-local-framework/prompt.md`.
    - `test_merge_local_wins_on_duplicate_id` — exactly one `fear-setting`, `source == "local"`, name `"Fear Setting (local override)"`, path under the fixture root.
    - `test_merge_malformed_local_yaml_degrades_with_warning` — project root = `local-malformed-repo`; result == plugin-only; exactly one warning, and it contains `frameworks/registry.yaml`.
    - `test_merge_finds_unregistered_local_folder_by_glob` — `unregistered-local-framework` present, `registered is False`, `source == "local"`, name/advisor parsed from its first line.
    - `test_local_framework_advisor_resolves_in_merged_advisors` — merge plugin `advisors/registry.yaml` with `FIXTURE/advisors/registry.yaml` (local wins); for `example-local-framework`, its `advisor` is found with `source == "local"` and its prompt path `FIXTURE/advisors/prompts/example-local-advisor.md` exists.
  - In `test_registry_schemas.py`, `TestLocalFrameworkRegistrySchema` (fixture root `local-advisor-repo`): required fields on every entry; every registered id has `frameworks/<id>/prompt.md` under the fixture root; every entry's `advisor` exists in plugin ∪ local advisor registries.

- [ ] **Step 3: Run to verify failure.** `cd e2e && python -m pytest tests/test_resolve_framework_source.py tests/test_registry_schemas.py -q` → resolver text tests and eval-surface test FAIL (file missing); oracle and schema tests PASS once fixtures exist (they test fixture consistency and the oracle).

- [ ] **Step 4: Write `skills/_shared/resolve-framework-source.md`.** Same sections and tone as `resolve-advisor-source.md` (title, `{base-directory}` note, Procedure, Anchoring rule, Return contract, Error paths). Procedure: (1) load plugin `frameworks/registry.yaml` via `skills/_shared/resolve-skill-path.md` Plugin root, tag `source: "plugin"`; (2) if `<project-cwd>/frameworks/registry.yaml` exists, merge, tag `source: "local"`, dedupe by id before returning, local wins; (3) glob `<project-cwd>/frameworks/*/prompt.md`, add any folder whose name is not already a local id as `registered: false` (if it shadows a plugin id, local still wins); (4) compute `absolute_framework_dir` and `absolute_prompt_path`. Skip the project steps when project-cwd is the plugin root. Add a short "Finding a framework's advisor" section: look up `advisor` in the merged set from `skills/_shared/resolve-advisor-source.md` and use that entry's `absolute_prompt_path`. Error paths: local registry absent → plugin-only + glob; malformed → plugin-only, keep the glob, one-line warning `Warning: could not parse <path>; using plugin frameworks only.`; resolved prompt missing → no error here, framework-runner fails closed; resolver unreadable → caller handles it.

- [ ] **Step 5: Add the eval-surface line; run tests** — same command, all PASS.

- [ ] **Step 6: Commit** `feat: add resolve-framework-source for project-local frameworks`.

### Task 2: contextual-recommendation accepts a pre-merged framework list

**Files:**
- Modify: `skills/_shared/contextual-recommendation.md` (Configuration, Stage 1, Multi-Entity Mode)
- Modify: `e2e/tests/test_contextual_recommendation.py`

**Interfaces:**
- Consumes: the Task 1 return contract.
- Produces: the input wording callers use: "Frameworks input: the pre-merged framework list from `skills/_shared/resolve-framework-source.md`".

- [ ] **Step 1: Failing tests.** `test_stage1_accepts_premerged_framework_list` (names `resolve-framework-source`); `test_configuration_framework_callers_pass_merged_list` (Configuration's framework-callers bullet names the pre-merged list); `test_stage1_no_longer_says_framework_callers_always_use_path` (`"Framework callers always use the path branch"` absent); `test_unregistered_frameworks_excluded_from_scoring` (text says entries with `registered: false` or empty `domains` are reachable by name only).
- [ ] **Step 2: Run** `cd e2e && python -m pytest tests/test_contextual_recommendation.py -q` → new tests FAIL.
- [ ] **Step 3: Edit the file.** Framework callers pass the pre-merged list; a registry path remains valid for plugin-only scope. Multi-Entity Mode runs against both pre-merged lists. Add the scoring-eligibility rule for unregistered frameworks. In presentation, local entries carry `(local)` after the name.
- [ ] **Step 4: Run tests** → PASS (including the existing six).
- [ ] **Step 5: Commit** `feat: contextual recommendation scores project-local frameworks`.

### Task 3: use-framework lists, matches, and runs through the resolver

**Files:**
- Modify: `skills/use-framework/SKILL.md` (Steps 1–4)
- Create: `e2e/tests/test_use_framework_resolver.py`
- Modify: `e2e/tests/test_shared_runners.py:99-111` (`test_use_framework_documents_absolute_path_construction`)

**Interfaces:**
- Consumes: Task 1 contract (`absolute_framework_dir`, `source`, `registered`); Task 2 wording.

- [ ] **Step 1: Failing tests.** `test_use_framework_step1_routes_through_resolver` (names `skills/_shared/resolve-framework-source.md`); `test_use_framework_marks_local_frameworks` (`(local)`); `test_use_framework_passes_merged_list_to_recommendation` (Step 3 no longer says `registry path: \`frameworks/registry.yaml\``); `test_use_framework_runner_path_is_absolute_framework_dir`. Update `test_use_framework_documents_absolute_path_construction` to require `absolute_framework_dir` instead of the `<plugin-root>/frameworks/<id>/` pattern.
- [ ] **Step 2: Run** `cd e2e && python -m pytest tests/test_use_framework_resolver.py tests/test_shared_runners.py -q` → FAIL.
- [ ] **Step 3: Rewrite Steps 1–4.** Step 1 calls the resolver (like use-advisor Step 1a); listing uses registry metadata and marks `source: "local"` entries `(local)`. Step 2's first-line parse applies only to `registered: false` entries. Step 3 matches slug and name over the merged list and passes the merged list to contextual-recommendation in both branches. Step 4 hands the entry's `absolute_framework_dir` to framework-runner. Keep the Avoid These Mistakes section.
- [ ] **Step 4: Run tests** → PASS.
- [ ] **Step 5: Commit** `feat: use-framework lists and runs project-local frameworks`.

### Task 4: Runners find advisors and frameworks in both scopes

**Files:**
- Modify: `skills/_shared/framework-runner.md` (Configuration, new Step 0, Voice)
- Modify: `skills/_shared/advisor-runner.md` (Composability step 1)
- Modify: `e2e/tests/test_shared_runners.py`

**Interfaces:**
- Consumes: Task 1 contract and its "Finding a framework's advisor" section; `resolve-advisor-source.md` contract (`absolute_prompt_path`).
- Produces: framework-runner Configuration gains optional `framework_entry` (the merged entry); when absent it reads the advisor id from the `prompt.md` first line.

- [ ] **Step 1: Failing tests.** `test_framework_runner_resolves_advisor_through_resolver` (names `resolve-advisor-source.md`); `test_framework_runner_loads_advisor_prompt_silently` (names `advisor-runner.md` and `greeting_mode=silent`); `test_framework_runner_voice_prefers_resolved_advisor_prompt`; `test_advisor_runner_framework_lookup_uses_resolver` (names `resolve-framework-source.md`, and the sentence "Look up the framework in `frameworks/registry.yaml`" is gone). Keep `test_framework_runner_documents_broken_advisor_reference_path` passing.
- [ ] **Step 2: Run** `cd e2e && python -m pytest tests/test_shared_runners.py -q` → FAIL.
- [ ] **Step 3: Edit.** framework-runner: before Step 1, unless an advisor persona is already active, find the framework's advisor in the merged advisor set and run advisor-runner with that entry's `absolute_prompt_path` and `greeting_mode=silent`; if not found, the existing generic-facilitator fallback applies. advisor-runner Composability step 1 looks up the advisor's frameworks in the merged list from `resolve-framework-source.md` and passes `absolute_framework_dir`.
- [ ] **Step 4: Run tests** → PASS.
- [ ] **Step 5: Commit** `feat: runners resolve advisors and frameworks across plugin and project`.

### Task 5: Brainstorming reads the merged framework list

**Files:**
- Modify: `skills/brainstorming/SKILL.md:55`, `skills/brainstorming/modes/authoring.md:19,214`, `skills/brainstorming/authoring-critique-checklist.md:135`
- Modify: `e2e/fixtures/skill-prompts/brainstorming-three-modes.md:43` only if `e2e/tests/test_fixtures.py` requires it to mirror SKILL.md (check that test first)
- Modify: `e2e/tests/test_authoring_mode_resolver.py`

- [ ] **Step 1: Failing tests.** `test_authoring_frameworks_input_is_merged_list` (authoring.md names `resolve-framework-source.md` and no longer says "the registry path `frameworks/registry.yaml`"); `test_authoring_critic_override_reads_merged_entry` (line about `default_critic_advisors` reads the engine's merged entry); `test_brainstorming_topic_tiebreaker_uses_merged_domains`; `test_critique_checklist_deliverable_type_from_merged_entry`.
- [ ] **Step 2: Run** `cd e2e && python -m pytest tests/test_authoring_mode_resolver.py tests/test_fixtures.py -q` → FAIL.
- [ ] **Step 3: Edit the three files** to point at the resolver's merged list.
- [ ] **Step 4: Run tests** → PASS.
- [ ] **Step 5: Commit** `feat: brainstorming sees project-local frameworks`.

### Task 6: add-framework and add-advisor write the project's own registry

**Files:**
- Modify: `skills/add-framework/SKILL.md` (Step 0 detection table and summary, Step 5, Step 7)
- Modify: `skills/add-advisor/SKILL.md` (Step 0 table and summary, Step 3, Step 5 note at :162, Step 7, Step 8)
- Create: `e2e/tests/test_add_skills_local_registry.py`

**Interfaces:**
- Produces: the shared detection rule both skills state the same way: "Writing to the plugin itself" means project-cwd contains `.claude-plugin/plugin.json` whose `name` is `aligned`. Otherwise it is a project repo.

- [ ] **Step 1: Failing tests** (for both skill files, parametrized): `test_documents_plugin_vs_project_detection` (`.claude-plugin/plugin.json`); `test_project_repo_writes_local_framework_registry` (`<project-cwd>/frameworks/registry.yaml` and "create it" wording); `test_keeps_parse_after_append_check` (`parse` + `revert`); `test_counts_only_when_writing_plugin` (the counts step is conditional on writing to the plugin). add-framework: `test_registry_step_no_longer_requires_plugin_directory` (`"exists in the plugin directory"` absent). add-advisor: `test_project_repo_writes_local_advisor_registry` (creates `<project-cwd>/advisors/registry.yaml` with the full schema when absent in a project repo).
- [ ] **Step 2: Run** `cd e2e && python -m pytest tests/test_add_skills_local_registry.py -q` → FAIL.
- [ ] **Step 3: Edit both skills.** New file content when creating a local registry: a one-line comment header and `frameworks:` (or `advisors:`) list. Lightweight mode (no registry, no wish to create) stays possible only in the plugin-absent case the skills already describe; in a project repo the default is to create.
- [ ] **Step 4: Run tests** → PASS. Also run `python -m pytest tests/test_add_advisor_no_avatar.py -q` → PASS.
- [ ] **Step 5: Commit** `feat: add-framework and add-advisor write project-local registries`.

### Task 7: Eval scenario, trigger map, and the touched-scenario run

**Files:**
- Create: `e2e/scenarios/use-framework/local-framework-recommendation.yaml`
- Create: `e2e/fixtures/local-advisor-repo/frameworks/nudge-the-quiet-ones/prompt.md` + registry entry (advisor `example-local-advisor`, domains `[reminders, follow-ups, group-asks]`, use_when about writing a reminder to people in a group who haven't responded yet)
- Modify: `e2e/trigger-map.yaml`
- Modify: `e2e/tests/test_trigger_map_paths.py` only if it needs the new path registered (check first)

- [ ] **Step 1: Write the scenario**, modeled on `scenarios/use-framework/contextual-recommendation.yaml`, one full-stack arm only. Vars: `skill_prompt` = use-framework SKILL.md, `resolver` = resolve-framework-source.md, `recommendation_logic` = contextual-recommendation.md, `registry` = plugin `frameworks/registry.yaml`, `local_registry` = fixture `frameworks/registry.yaml`; prompt states the project's local registry is at `<project-cwd>/frameworks/registry.yaml` with the given contents. Task: "I need to write a reminder email to people in the group who haven't replied yet." Rubric: recommends Nudge the Quiet Ones, marks it `(local)`, uses Selected/shortlist format, offers "list all".
- [ ] **Step 2: Trigger map.** Add an entry with paths `skills/_shared/resolve-framework-source.md`, `e2e/fixtures/local-advisor-repo/frameworks/registry.yaml` → `scenarios/use-framework/local-framework-recommendation.yaml` and `scenarios/use-framework/contextual-recommendation.yaml`. Add the new scenario to the existing `skills/_shared/contextual-recommendation.md` and `skills/use-framework/SKILL.md` entries.
- [ ] **Step 3: Run** `cd e2e && python -m pytest -q` → full pytest suite PASS (pytest only, no LLM calls).
- [ ] **Step 4: Commit** `test: eval that use-framework recommends a project-local framework`.

The controller (not a subagent) runs the touched evals after Task 8 and reports their cost.

### Task 8: Documentation

**Files:**
- Modify: `CLAUDE.md` ("Registries — Sources of Truth")
- Modify: `README.md` (near the advisors/registry paragraph around line 114, and a framework counterpart)
- Modify: `skills/add-advisor/SKILL.md:162` only if Task 6 left plugin-only wording there

- [ ] **Step 1: Failing test** in `e2e/tests/test_resolve_framework_source.py`: `test_docs_say_projects_keep_local_registries` — both `CLAUDE.md` and `README.md` mention `frameworks/registry.yaml` and `advisors/registry.yaml` at the project root, say they merge with the plugin's, and say local wins. `test_plugin_and_marketplace_versions_match`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write the docs.** Two or three plain sentences in each place. Name both resolvers in CLAUDE.md.
- [ ] **Step 4: Run** `cd e2e && python -m pytest -q` → PASS.
- [ ] **Step 5: Commit** `docs: projects can keep their own advisors and frameworks` (the pre-commit hook bumps the version).
