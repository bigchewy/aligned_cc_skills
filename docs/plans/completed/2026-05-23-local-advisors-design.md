# Repo-Scoped (Local) Advisors — Design

**Date:** 2026-05-23
**Status:** Design — corrected after Round 1 critique; ready for plan
**Topic:** local-advisors

> **Counts verified against `advisors/registry.yaml` and `frameworks/registry.yaml`
> this session (not against the stale READMEs).** The registry was edited
> mid-design: `benjamin-levine` was removed; `akiko-iwasaki`, `david-putrino`,
> `david-systrom` were added. All numbers below reflect the post-edit state:
> **76 plugin advisors**, **19 migrating**, **39 migrating frameworks**,
> **57 plugin advisors remaining** after migration.

## Goal

Let any repo define its own advisors that **merge** with the plugin's global
advisors, then move the 19 health/therapy advisors (and their 39 frameworks)
out of the plugin into the user's personal repo — where they're the only place
they're relevant.

Today, advisors are plugin-only on the read side. Frameworks already support
project-local merge. This design closes that asymmetry and then performs the
migration the new capability enables.

## Core insight — parity with frameworks

This is **not a new pattern**. `use-framework` already:
- reads the plugin `frameworks/registry.yaml` as canonical (`use-framework/SKILL.md:21`),
- globs project-local `frameworks/*/prompt.md`, dedupes by slug, **project-local wins** (`:23`),
- appends project-local frameworks not in the registry (`:25`),
- runs them through a path-agnostic runner (`framework-runner.md:59`, which also
  graceful-degrades to a generic facilitator when an advisor reference can't resolve).

Advisors are the only half of the system without a project-local read path. The
design copies the proven half. The advisor *runner* (`advisor-runner.md`) is
already location-agnostic — it takes an absolute path and fail-closes if the
file is missing (`:15`). The gap is purely in **discovery and resolution**.

**One asymmetry to preserve in mind:** `use-framework` discovers a registry-less
local framework via a *glob fallback* (`:23`). This design does **not** add a
prompt-file glob fallback for advisors — a local advisor is discovered only via
its local `advisors/registry.yaml` entry. That is intentional (full-parity
metadata requires a registry entry anyway), but it creates a workflow trap the
design must address (see "Workflow: adding a local advisor").

## Settled decisions

| Axis | Decision |
|------|----------|
| Visibility | **Merged** — in any repo, the user sees plugin advisors + that repo's local advisors |
| Local metadata | **Full parity** — local advisors carry full registry metadata and auto-participate in contextual recommendation, critique panels, and `/use-advisor` |
| Destination | **Personal repo only** for this migration |
| What stays in plugin | Leadership/coaching, strategy/startup, business, software, marketing/copy, sales advisors |
| Migration set | **19 advisors + 39 frameworks** (health/body + therapy/mental-health) |
| Collision policy | **Local-wins** on duplicate `id` (matches frameworks; inert for this migration since each id lives in exactly one scope) |
| Avatar generation | **Removed** from `add-advisor` |

### Migration set (19 advisors)

Health/body (13): `andreo-spina`, `blair-grubb`, `italo-biaggioni`,
`kelly-starrett`, `patrick-mckeown`, `roy-freeman`, `shirley-sahrmann`,
`stuart-mcgill`, `deb-dana`, `irene-lyon`, `akiko-iwasaki`, `david-putrino`,
`david-systrom`

Therapy/mental-health (6): `byron-katie`, `gabor-mate`, `marsha-linehan`,
`martin-seligman`, `richard-schwartz`, `steven-hayes`

The 3 new advisors (`akiko-iwasaki`, `david-putrino`, `david-systrom`) currently
own **0 frameworks** (verified), so the framework count stays 39.

**Stay in plugin (hybrids):** `kate-bowler` (health/wellness *copy*) and
`julie-yoo` (digital-health *GTM*) — both business-facing despite health adjacency.

**Removed phantom:** `benjamin-levine` is no longer in the registry or on disk.
It survives only in stale READMEs (`advisors/README.md`, `frameworks/README.md`)
and must be deleted from those during the README cleanup below.

## Mechanism — `skills/_shared/resolve-advisor-source.md` (new)

A shared procedure, parallel to `resolve-skill-path.md`, that every advisor
read-path calls. One source of merge truth so logic can't drift across callers.

**Procedure:**
1. Load plugin `advisors/registry.yaml` (canonical) — both its `advisors:` list
   and its top-level `selection_guidelines:` block.
2. If `<project-cwd>/advisors/registry.yaml` exists, load and merge its
   `advisors:` list; dedupe by `id`, **local-wins**. Dedupe **before** returning,
   so a shadowed plugin advisor never double-lists in panel candidate sets.
3. For each entry compute `absolute_prompt_path = <scope-root>/<prompt-dir>/<id>.md`
   where `scope-root` = plugin-root for plugin entries, **project-cwd** for local
   entries, and `<prompt-dir>` = the CLAUDE.md-configured advisor prompt path if
   present (the same key `add-advisor` Step 0 reads, `add-advisor/SKILL.md:21`),
   else the default `advisors/prompts`. (This single rule subsumes the old
   Step 3/Step 4 split: the override, when set, *is* the `<prompt-dir>`; when
   absent it defaults to `advisors/prompts`.) The stored `prompt:` field is
   **ignored for resolution** (it is plugin-relative on every entry — would
   mis-resolve a local advisor); it stays as human-readable metadata only.

**Return contract (explicit — the thing all callers couple to):**

```
{
  advisors: [
    { id, name, summary, domains, evaluation_expertise, best_for, not_for,
      absolute_prompt_path, source: "plugin" | "local" }
  ],
  selection_guidelines: { ... }   // PLUGIN-CANONICAL — local repos do not
                                  // override panel selection rules
}
```

- `selection_guidelines` is returned as a sibling of `advisors`, taken from the
  **plugin** registry only (a local repo's panel-selection rules are not honored —
  YAGNI: there is no use case for per-repo critic-count rules). This closes the
  hole where `critique-panel-orchestration.md` lost its source for that block.
- Every per-advisor field is guaranteed present for both plugin and local
  advisors (a local registry entry must carry the full schema — see Testing).

**Anchoring rule:** local advisors resolve against **project cwd**, never
plugin-root. `resolve-skill-path.md` is for plugin-bundled files only and is not
reused for locals. Location convention mirrors the framework precedent and
`add-advisor`'s existing write target: `<project-root>/advisors/` (registry +
`prompts/`), **not** a `.claude/`-nested path (the personal repo is not a plugin
and has no `.claude-plugin/plugin.json`).

**Error paths (specified, not hand-waved):**
- Local `advisors/registry.yaml` **absent** → plugin-only result, no error.
- Local registry **malformed YAML** → **degrade to plugin-only and emit a
  one-line warning naming the file**. A broken local registry must not lock the
  user out of plugin advisors. (This differs from `add-advisor`'s write-side
  revert-on-parse-failure at `add-advisor/SKILL.md:212`, which is correct for
  a write but wrong for a read.)
- Prompt-path CLAUDE.md override **absent** → default `<scope-root>/advisors/prompts/<id>.md`.
- Resolved prompt file **missing** → no resolver error; `advisor-runner.md:15`
  fail-closes at use time (preserved behavior).

## Change surface (read paths)

| File | Change | Risk |
|------|--------|------|
| `skills/_shared/resolve-advisor-source.md` | **New** shared procedure + return contract above | — |
| `skills/use-advisor/SKILL.md` | Steps 1a/1b/4: list + fuzzy-match against merged list; resolve via `absolute_prompt_path`. **Also revise the listing text** — line 35 ("all advisors live in a single flat directory") is now false; annotate `(local)` using the `source` field when both scopes contribute | Medium — listing text + path consumption |
| `skills/_shared/critique-panel-orchestration.md` | **Line 33** (direct `advisors/registry.yaml` read + parse) → call resolver, take `advisors` list **and** `selection_guidelines` from its return. **Line 35** → resolve prompt via `absolute_prompt_path` instead of the `prompt:` field | **Highest** — two coupled edits (33 + 35) |
| `skills/_shared/contextual-recommendation.md` | Make Stage 1 input **dual-contract**: accept EITHER a registry path (framework callers, unchanged) OR a pre-merged advisor entry list. State which branch each caller uses | Medium — polymorphic shared file, 4 callers |
| `skills/brainstorming/modes/research.md` | Its advisor dispatch reads `advisors/prompts/{id}.md` plugin-relative (`:75`, `:87`) and its routing examples name migrating advisors (`steven-hayes:78`, `blair-grubb:82`). Route the dispatch through the resolver **and** keep the registry-authoritative note | **High** — currently unaccounted; would resolve a deleted file |
| `skills/brainstorming/modes/authoring.md` | Its `framework-or-advisor` contextual-recommendation mode (`:18`) makes `contextual-recommendation.md:66` read **both** registries internally. Specify that the advisor side obtains the merged list, else local advisors are invisible to authoring engine selection (defeats the parity goal) | **High** — deepest integration point |

**No change needed:**
- `advisor-runner.md` — already takes an absolute path, fail-closes (`:15`).
- `use-framework` / `framework-runner.md` — frameworks already merge locally;
  migrated frameworks work immediately. Existing graceful-degradation covers
  any unresolvable advisor reference.
- `agents/code-reviewer.md` — single fixed persona (The Auditor), zero registry
  or critic-selection logic. (The "default critics" mechanism lives only in
  `critique-panel-orchestration.md` Round 1; its calibration examples name only
  STAY-set advisors, `registry.yaml:13-20`.)
- `brainstorming/modes/software.md` — hardcodes references to STAY-set advisors
  only (`steve-krug`, `the-architect`). Unaffected.
- `scripts/generate-catalogs.py` — correctly plugin-only (a build script, no
  merge-awareness needed); but see Migration step for the catalog regeneration.

## Migration (data move, enabled by the mechanism)

Move **per-advisor atomically** (registry entry + prompt file together), not
batched-by-type, so an interruption never leaves the count-match invariant red.

1. For each of the 19 advisors: move `advisors/prompts/<id>.md` → personal repo
   `advisors/prompts/`, and move its registry entry → a new personal-repo
   `advisors/registry.yaml` (with the full schema, including a `selection_guidelines`
   block copied from the plugin if the personal repo runs panels).
2. Move the 39 framework folders `frameworks/<id>/` + their `frameworks/registry.yaml`
   entries → personal repo. (`use-framework` already merges project-local frameworks.)
3. **`frameworks/_outliers.json`:** remove `enneagram-typing` (`advisor: richard-schwartz`,
   the only migrating-advisor outlier — verified) from the plugin file; carry it to
   the personal repo's outlier source if that repo regenerates its registry.
4. **Stale-artifact cleanup:**
   - `advisors/README.md` — fix "65 advisors" → **57**; remove the nonexistent
     `copywriter` entry; remove `benjamin-levine`.
   - `frameworks/README.md` — remove `benjamin-levine` and its 4 phantom framework
     listings (folders already absent).
   - Regenerate `docs/advisor-catalog.html` via `python3 scripts/generate-catalogs.py`.
   - Bump advisor count in `.claude-plugin/plugin.json` / `marketplace.json` if a
     count is embedded.
5. **Post-migration verification gate (before commit):** registry entry count ==
   prompt file count on **both** repos, and `e2e/tests/test_registry_schemas.py`
   green.

## Avatar removal

Strip from `skills/add-advisor/SKILL.md`:
- Step 5 ("Generate Avatar") and all its sub-lines (incl. the in-step file-naming note)
- The Step 0 detection row (avatar directory + generation script) and the
  dashboard "Avatars:" line
- The "Review generated avatars for likeness" note in the Notes section
- Renumber subsequent steps

The other two "avatar" hits in the repo are unrelated (a derogatory "cartoon
avatar" line in `patrick-campbell.md`; an "avatar stack" UI element in
`create-design-principles`) — left untouched.

## Workflow: adding a local advisor (DX)

Because advisors have **no glob fallback** (unlike frameworks), a prompt file
without a registry entry is a silent no-op. Close the loop:
- `add-advisor` is the tool that writes both files; it already has repo-aware
  write logic (Step 0 path detection). Confirm it works when run **in the
  personal repo** and document the two-file convention (`advisors/registry.yaml`
  entry + `advisors/prompts/<id>.md`) in `add-advisor` so the convention is
  discoverable from the tool, not only from this design.
- `add-advisor` continues to write the `prompt:` field for human readability;
  add a one-line note that the read side ignores it (so a maintainer doesn't
  trust a knob that does nothing).

## Testing (TDD)

**Harness reality:** `resolve-advisor-source.md` is a **markdown procedure an LLM
follows**, not executable code. Existing tests assert *substrings/sections in the
markdown* (`test_shared_runners.py`) or validate YAML (`test_registry_schemas.py`).
The tests below match that reality — no behavioral fixture-repo test (which the
harness has no precedent for).

**New — `e2e/tests/test_resolve_advisor_source.py`** (markdown-assertion style,
mirroring `test_shared_runners.py`): assert `resolve-advisor-source.md` *documents*
each required behavior as a section/substring — merge order (plugin canonical),
dedupe-before-return, local-wins on `id`, scope-root derivation (plugin-root vs
project-cwd), `<prompt-dir>` override + default, ignore-`prompt:`-field rule,
`selection_guidelines` plugin-canonical, and each of the four error paths.

**New — framework→advisor dangling-reference guard** (the real portability
guarantee, since no existing test provides it): enumerate `frameworks/registry.yaml`
`advisor:` values and assert each resolves against the in-scope advisor set; scan
each framework `prompt.md` first line for an advisor name that no longer resolves.

**Update:**
- `test_registry_schemas.py` — validate a project-local advisor registry against
  the same schema, but **resolve its `prompt:` existence check against the
  project (fixture) root**, not `REPO_ROOT`. Reconcile the "metadata only"
  framing: the field must still exist and resolve *within its own scope*. Assert
  the count-match invariant holds on both repos.
- `test_contextual_recommendation.py` — the dual-contract (path OR pre-merged list).

**Guardrail correction:** the real existing prompt-existence guard is
`test_registry_schemas.py::test_prompt_paths_exist` (asserts every plugin registry
entry's prompt resolves) — **not** `test_skill_cross_references.py`, which only
checks 4 hardcoded refs and would catch none of the dangling-reference scenarios.
`test_outlier_frameworks_have_correct_metadata` will go red if `enneagram-typing`
is removed without updating `_outliers.json` (migration step 3 handles this).

**Flag for plan phase:** `eval-surface.yaml` baseline shifts when 19 advisors +
39 frameworks leave the plugin; re-run `eval-audit`.

## Decision Log

| # | Decision | Alternatives considered | Why |
|---|----------|------------------------|-----|
| 1 | Merged visibility (plugin + local) | Local-only when present; merged-with-override | User wants software/strategy advisors everywhere PLUS medical in personal — union, not replacement |
| 2 | Full parity (local registry per repo) | Explicit-only (prompt files, no metadata) | User wants local advisors to auto-join panels/recommendation — requires metadata. (Implies: no glob fallback; a local advisor needs a registry entry) |
| 3 | Local advisors at `<project-root>/advisors/` | `.claude/advisors/` nested | Mirrors framework precedent + add-advisor's write target; personal repo is not a plugin |
| 4 | Shared `resolve-advisor-source.md` **with a single typed return contract** | Inline merge per caller | Three+ read paths would drift if logic is duplicated; `resolve-skill-path.md` sets the precedent. The procedure must publish one return contract (incl. `selection_guidelines`), or callers re-introduce drift at the consumption boundary |
| 5 | Ignore `prompt:` field, derive path from `id`+scope+`<prompt-dir>` | Trust the stored field | All plugin `prompt:` values are plugin-relative; would mis-resolve locals. `use-advisor` already constructs from `id`. Trade-off accepted: an inert-but-still-written field (removing it would touch every entry and break nothing functional) |
| 6 | Local-wins on collision | error / skip-local / main-wins | Matches framework precedent; only policy consistent with "local indistinguishable from global." Inert for this migration |
| 7 | Frameworks migrate with their advisors | Leave frameworks in plugin | Otherwise **39** dangling advisor refs ship in the plugin — portability violation. Guarded by the **new** framework→advisor reference test + `test_registry_schemas.py::test_prompt_paths_exist` (NOT `test_skill_cross_references.py`, which does not scan these) |
| 8 | Leadership cluster stays in plugin | Move to personal; split by usage | User decision — broadly useful across work contexts |
| 9 | Hybrids (kate-bowler, julie-yoo) stay in plugin | Move with health set | Business-facing (health *copy*, digital-health *GTM*), not personal medical |
| 10 | Remove avatar generation from add-advisor | Keep conditional step | User no longer builds avatars |
| 11 | Include 3 new medical advisors (akiko-iwasaki, david-putrino, david-systrom) | Keep them in plugin | Added mid-session; unambiguously health (Long COVID/ME-CFS) — same principle as the rest of the health set. Own 0 frameworks |
| 12 | Malformed local registry → degrade to plugin-only + warning | Halt | A broken local file must not lock the user out of plugin advisors |
| 13 | `selection_guidelines` plugin-canonical (local can't override) | Merge/override per repo | No use case for per-repo critic-selection rules (YAGNI) |

## Open Questions

- **None blocking after corrections.** The `eval-surface.yaml` re-baseline is the
  one known follow-up, resolved by running `eval-audit` during the plan phase
  (concrete trigger: the writing-plans step that touches the registries).
