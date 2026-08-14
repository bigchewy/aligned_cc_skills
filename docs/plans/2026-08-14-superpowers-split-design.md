# Superpowers Split — Design

**Date:** 2026-08-14
**Status:** Approved design, pending implementation plan

## Goal

The superpowers plugin now covers the software development loop better than aligned's own dev-workflow skills. Aligned drops its dev-workflow half and becomes the thinking-and-content plugin: advisors, frameworks, non-software brainstorming, persona testing, brand content, images and visualizations, project scaffolding. Superpowers owns software development: software design brainstorming, writing and executing plans, TDD, debugging, worktrees, code review, finishing branches.

This also removes the five skill-name collisions between the two plugins (`brainstorming`, `writing-plans`, `executing-plans`, `finishing-a-development-branch`, `using-git-worktrees`), which currently make auto-triggering ambiguous when both are installed.

This ships as one release: version 0.33.0, breaking change, changelog names every removed skill and its superpowers replacement.

## Removals

Skills (delete the whole directory):

| Removed skill | Superpowers replacement |
|---|---|
| `skills/writing-plans` | `superpowers:writing-plans` |
| `skills/executing-plans` | `superpowers:executing-plans` |
| `skills/finishing-a-development-branch` | `superpowers:finishing-a-development-branch` |
| `skills/using-git-worktrees` | `superpowers:using-git-worktrees` |
| `skills/kanban-resolve` | none — its queue was fed by the code-simplifier step in finishing-a-development-branch, which is gone |
| `skills/codebase-audit` | none — capability dropped |

Agents (delete):

- `agents/code-reviewer.md`
- `agents/code-simplifier.md`
- `agents/kanban-triage.md`
- `agents/doc-staleness-detector.md`

The visualization agents (architecture-diagram-generator, flowchart-generator, mockup-generator, project-scanner, critique-interactive-html-generator, session-document-generator, artifact-verifier) stay — visualize-design, create-image, and the surviving brainstorming modes use them.

Hooks:

- `hooks/auto-approve-worktrees.js` — delete; it existed for using-git-worktrees.
- `hooks/auto-approve-safe-bash-paths.js` — keep, unless planning shows its only consumers are removed skills.

e2e: delete the eval scenarios, `trigger-map.yaml` entries, and `eval-surface.yaml` entries that test removed skills.

## Rescopes

**brainstorming** — delete `modes/software.md` and the handoff into writing-plans. Authoring, research, and roadmap modes stay. Roadmap mode can still decompose a software project, but software-typed items hand off to `superpowers:brainstorming` when that plugin is installed. When it is not installed, the skill says plainly that software design is out of scope for aligned and suggests installing a dev-workflow plugin. Mode detection in `SKILL.md` no longer routes anything to a software mode.

**root-cause-analysis** — narrows to business and process problems ("why did the demo fall flat", "why is churn up"). The description and trigger language stop claiming bugs, test failures, and unexpected code behavior; those route to `superpowers:systematic-debugging`.

**kickstart** — keeps both templates and the kanban scaffolding unchanged. Only the scaffolded skill recommendations change: the software template's CLAUDE.md output recommends `superpowers:writing-plans`, `superpowers:executing-plans`, `superpowers:finishing-a-development-branch`, and `superpowers:systematic-debugging`, phrased conditionally ("if the superpowers plugin is installed") so the output is not broken for users without it. The business template's `/aligned:root-cause-analysis` reference stays — RCA survives for business problems, which is that template's context.

**eval-audit** — stays as-is. It QAs advisors and frameworks, which survive.

## Kept intact

`add-advisor`, `add-framework`, `brainstorming` (three modes), `create-design-principles`, `create-image`, `eval-audit`, `find-potential-advisors`, `kickstart`, `persona-panel`, `root-cause-analysis` (rescoped), `use-advisor`, `use-framework`, `visualize-design`, both registries, `advisors/`, `frameworks/`, `brand/` tooling.

## Autopilot

`scripts/autopilot/` stays in the repo untouched, but it drives the removed skills (WRITE-PLAN, EXECUTE-PLAN, VERIFY-BRANCH), so it is non-functional after this release. The README and changelog say so explicitly. A follow-up release ports it to drive superpowers skills. The `skills/_shared/` files it needs (plan-manifest-format.md, manual-deploy-artifact-catalog.md, and any others planning identifies) stay for the port.

## Reference cleanup

- Repo `CLAUDE.md`: remove or update sections describing the removed pipeline.
- `README.md`: skill reference table, iron rules, changelog entry for 0.33.0, autopilot non-functional note.
- `.claude-plugin/plugin.json` and `marketplace.json`: version 0.33.0 in both; description drops "TDD pipeline, automated quality gates" and reflects the new scope.
- Grep all `skills/**/*.md` for every removed skill path and `/aligned:<removed-name>` invocation; fix each hit (per the repo's cross-reference rule, breakage is silent).
- Historical documents (`docs/plans/`, `docs/kanban/`, `docs/lessons-learned/`) are records, not live references — leave them alone.

## Test updates

Per the TDD rule, the implementation plan must enumerate exact files, but the known surface is:

- Delete e2e scenarios under `e2e/scenarios/` that exercise removed skills.
- Update `e2e/trigger-map.yaml` and `e2e/eval-surface.yaml` to drop removed-skill entries.
- Update any tests in `e2e/tests/` that enumerate skills, agents, or the README table (the cross-reference test and README-table test known from KB history).
- Update fixtures such as `e2e/fixtures/skill-prompts/brainstorming-four-modes.md` to three modes.
- Run the full e2e/test suite and the portability-audit skill before release.

## Eric's local config (outside this repo)

`~/.claude/CLAUDE.md` changes with this release:

- Pasted errors and bugs route to `superpowers:systematic-debugging` instead of `/aligned:root-cause-analysis`.
- `/aligned:root-cause-analysis` stays referenced only for business problems.
- Add one routing sentence: software development work uses superpowers skills; advisors, frameworks, content, and other non-dev work use aligned.

## Sequencing

1. Land or stash the currently uncommitted changes on main (both manifests, both catalogs, `frameworks/registry.yaml`) before this work starts.
2. Do the work on a branch.
3. One release commit series: removals, rescopes, reference cleanup, test updates, version bump.
4. Follow-up (separate effort, not this release): port autopilot to superpowers skills.
