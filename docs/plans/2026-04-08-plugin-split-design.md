# Plugin Split: aligned-advisors + aligned-works

**Date:** 2026-04-08
**Status:** Approved (post-critique revision)
**Mockups:** docs/mockups/plugin-split.html

## Problem

The aligned plugin bundles two distinct products in one package: a virtual board of advisors (personas + frameworks) and a structured creation workflow stack (brainstorming through deployment). These serve overlapping but distinct audiences — the advisors product is lighter-weight and conversational, while the works product is agent-heavy and CLI-optimized. A single plugin forces users to install everything or nothing.

**Note on Desktop compatibility:** Three of the five advisor skills (`add-advisor`, `add-framework`, `find-potential-advisors`) use CLI-only features (Task tool sub-agents, WebSearch). Full Desktop compatibility is a future goal, not a launch guarantee. Only `use-advisor` and `use-framework` are Desktop-safe today.

## Decisions

### Architecture: Mono-repo, Flat Split

Both plugins live in this repo as peer directories. Each has its own `.claude-plugin/`, skills, and content. The repo root holds shared development files (CLAUDE.md, LICENSE).

```
aligned_cc_skills/
├── aligned-advisors/
│   ├── .claude-plugin/
│   │   ├── plugin.json
│   │   └── marketplace.json
│   ├── advisors/
│   │   ├── registry.md
│   │   └── prompts/              # 65 advisor .md files
│   ├── frameworks/               # 138 frameworks
│   ├── skills/
│   │   ├── use-advisor/
│   │   ├── use-framework/
│   │   ├── add-advisor/
│   │   ├── add-framework/
│   │   └── find-potential-advisors/
│   └── README.md
│
├── aligned-works/
│   ├── .claude-plugin/
│   │   ├── plugin.json
│   │   └── marketplace.json
│   ├── advisors -> ../aligned-advisors/advisors      # symlink
│   ├── frameworks -> ../aligned-advisors/frameworks   # symlink
│   ├── skills/
│   │   ├── _shared/
│   │   │   ├── kanban-entry-format.md
│   │   │   └── critique-panel-orchestration.md
│   │   ├── brainstorming/
│   │   ├── writing-plans/
│   │   ├── executing-plans/
│   │   ├── finishing-a-development-branch/
│   │   ├── test-driven-development/
│   │   ├── verification-before-completion/
│   │   ├── using-git-worktrees/
│   │   ├── root-cause-analysis/
│   │   ├── codebase-audit/
│   │   ├── eval-audit/
│   │   ├── eval-failure-triage/
│   │   ├── kanban-resolve/
│   │   ├── kickstart/
│   │   ├── create-new-skill/
│   │   ├── create-svg-diagram/
│   │   ├── create-design-principles/
│   │   └── persona-panel/
│   ├── agents/                   # all 10 agents
│   ├── hooks/                    # all 3 hooks + hooks.json
│   ├── docs/                     # plans, mockups, ralph loops
│   └── README.md
│
├── .github/                          # workflows (update aligned: references)
├── .gitignore                        # update paths for new structure
├── CLAUDE.md
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
└── scripts/                          # autocommit infrastructure
```

**Why flat over nested:** Skills resolve the plugin root via `{base-directory}/../../` (two levels up from `skills/<name>/SKILL.md`). A flat split preserves this convention within each plugin. Nesting deeper would break every path resolution.

**Why mono-repo over multi-repo:** Content is tightly coupled at launch (brainstorming reads advisor prompts, critique panels pull personas). Atomic cross-plugin changes are easier in one repo. The marketplace supports multiple plugins from the same repo via relative source paths.

### Skill Allocation

**aligned-advisors (5 skills):**
| Skill | Purpose |
|-------|---------|
| use-advisor | Adopt advisor persona for conversation |
| use-framework | Guide user through framework phases |
| add-advisor | Create new advisor (prompt, examples, anti-examples) |
| add-framework | Add framework to existing advisor |
| find-potential-advisors | Research and evaluate potential advisors |

**aligned-works (17 skills):**
| Skill | Purpose |
|-------|---------|
| brainstorming | Idea → validated design with expert critique |
| writing-plans | Design → implementation plan |
| executing-plans | Plan → task-by-task execution |
| finishing-a-development-branch | Merge/deploy workflow |
| test-driven-development | TDD methodology |
| verification-before-completion | Evidence-before-assertions gates |
| using-git-worktrees | Worktree management |
| root-cause-analysis | Problem investigation |
| codebase-audit | Multi-dimensional code analysis |
| eval-audit | Eval coverage checker |
| eval-failure-triage | Eval failure classification |
| kanban-resolve | Kanban triage and resolution |
| kickstart | Project scaffolding |
| create-new-skill | Skill authoring |
| create-svg-diagram | Visual diagram generation |
| create-design-principles | Design system discovery (Steve Jobs persona) |
| persona-panel | Content testing against buyer personas |

**Removed from plugin (personal global skills, separate task):**
- generate-deck, generate-blog-post, generate-one-pager, portability-audit

### Cross-Plugin References: Symlinks

Works skills that reference `advisors/` paths (brainstorming, create-design-principles, critique-panel-orchestration) continue to work via symlinks at the aligned-works root:

- `aligned-works/advisors` → `../aligned-advisors/advisors`
- `aligned-works/frameworks` → `../aligned-advisors/frameworks`

Symlinks are resolved during plugin cache copy. Per Claude Code plugins-reference documentation: "Symlinks are honored during the copy process" — symlinked content is copied into the plugin cache as real files. Empirically confirmed 2026-04-08 (filesystem-level resolution verified). This means zero changes to existing advisor path references in skill files.

**Marketplace caveat:** Since symlinked content is snapshot at install time, updates to advisor content require reinstalling the works plugin. This is fine for bundled distribution where both plugins version together.

**Fallback if symlinks don't resolve at runtime:** Explicit Glob-based advisor plugin root resolution in ~12 skill and agent files.

### Cross-Plugin Invocations: Bundle at Launch

aligned-works recommends co-installing aligned-advisors. No graceful degradation coding — if a works skill invokes an advisor skill and advisors isn't installed, it fails with a clear error. Fallback paths deferred until there's a real user who wants only one plugin.

**Error UX:** The aligned-works README includes a Prerequisites section listing aligned-advisors as a recommended co-install. Skills that depend on advisor content (brainstorming critique panels, create-design-principles) should print a one-line message when advisor files are unreachable: "Install aligned-advisors for full functionality: /install aligned-advisors".

### Glob Disambiguation

7 skill files across 5 locations use fallback Glob patterns filtered by "parent directory contains `.claude-plugin/plugin.json`" to re-find the plugin root after context compression. With two plugins, this filter matches twice. Each instance updated to use a two-step resolution: find via Glob, then Read plugin.json and check the `name` field matches the expected plugin (e.g., `name: aligned-works`). This is a behavior change from a single-step filter to a two-step find-and-verify pattern.

### Skill Name Prefixes

Cross-plugin invocations change prefix:
- `aligned:use-advisor` → `aligned-advisors:use-advisor`
- `aligned:brainstorming` → `aligned-works:brainstorming`

Intra-plugin invocations also get the new prefix (e.g., `aligned-works:writing-plans`). ~135 instances across 26+ files including skill files, kickstart permissions (22 entries split across advisors, works, and removed), READMEs, agent files, .github/, and CONTRIBUTING.md.

### Versioning

Both plugins start at 1.0.0 to mark the split as a major release. Independent version tracks from that point. Each plugin's CLAUDE.md documents its own version bump process.

### Hooks and Agents

All 10 agents and all 3 hooks live in aligned-works. The advisors plugin has zero agents and zero hooks.

### Marketplace Configuration

Each plugin gets its own marketplace.json with source path offsets pointing to the plugin subdirectory:

```json
{
  "source": {
    "source": "github",
    "repo": "bigchewy/aligned_cc_skills",
    "path": "aligned-advisors"
  }
}
```

The `path` field tells the marketplace to treat the subdirectory as the plugin root. Both plugins are installable independently from the same repo.

## Migration Plan

All work happens on a feature branch (`feature/plugin-split`). The intermediate state between phases will be broken — the feature branch isolates this from main.

### Phase 0 — Validate Assumptions (before any file moves)

1. Test symlink resolution end-to-end: create minimal plugin structure in /tmp with symlinks, load via `claude --plugin-dir`, invoke a skill that reads through the symlink. **Result (2026-04-08):** Symlinks confirmed to work both in-place (`--plugin-dir`) and via marketplace cache copy (documented in plugins-reference).
2. Verify `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin subdirectory (not repo root) when loading via `--plugin-dir aligned-works/`. If it resolves to repo root, hooks.json paths will need adjustment.

### Phase 1 — Move Files

3. Create `aligned-advisors/` and `aligned-works/` at repo root
4. `git mv` advisors/, frameworks/ into aligned-advisors/
5. `git mv` skills/ into aligned-works/skills/ (excluding the 5 advisor skills and 4 already-extracted personal skills)
6. `git mv` the 5 advisor skills into aligned-advisors/skills/
7. `git mv` agents/, hooks/, docs/ into aligned-works/
8. Create symlinks: aligned-works/advisors → ../aligned-advisors/advisors, aligned-works/frameworks → ../aligned-advisors/frameworks
9. Create new .claude-plugin/ in each plugin directory with independent plugin.json (skills arrays) and marketplace.json (source path offsets)
10. Remove old .claude-plugin/ from repo root

### Phase 2 — Update References

11. Update all 7 fallback Glob patterns to use two-step find-and-verify (Glob + Read plugin.json name field)
12. Audit docs/ralph_loops/*.sh scripts for hardcoded paths
13. Update skill name prefixes (~135 instances across 26+ files): classify each as intra-plugin vs cross-plugin, apply correct prefix (`aligned-advisors:` or `aligned-works:`)
14. Update kickstart permissions list (22 entries split across advisors, works, and removed categories)
15. Update agent files with advisor path references (document symlink dependency for mockup-generator.md and others)
16. Update add-advisor/SKILL.md and add-framework/SKILL.md count-update instructions for two-plugin structure (they update README.md, plugin.json, and marketplace.json counts)
17. Update .gitignore paths (e.g., `docs/plans/` → `aligned-works/docs/plans/`)
18. Update .github/ workflows (any `aligned:` references)
19. Update CONTRIBUTING.md, both plugin READMEs, repo-level CLAUDE.md and README.md

### Phase 3 — Validate

20. Test symlink resolution: `claude --plugin-dir aligned-works/`, invoke skill that reads advisors/registry.md
21. Test hook discovery from aligned-works/hooks/hooks.json
22. Verify both plugins load independently: `claude --plugin-dir aligned-advisors/` and `claude --plugin-dir aligned-works/`
23. Run prefix-rename verification: grep for any remaining `aligned:` references that should have been updated (excluding repo-level docs that intentionally reference the old name)
24. Verify skill counts match plugin.json skills arrays (5 for advisors, 17 for works)

### Phase 4 — Merge

25. Squash or merge feature branch to main
26. Tag both plugins at their starting versions

## Testing Strategy

The migration is a structural change, not a code change — traditional unit tests don't apply. Validation is script-driven:

| Test | What it verifies | How |
|------|-----------------|-----|
| Symlink resolution | Advisor content reachable from works plugin | Load works plugin, invoke skill that reads `advisors/registry.md` |
| Hook discovery | Hooks load from `aligned-works/hooks/` | Load works plugin, trigger a hook, verify it fires |
| Prefix completeness | No stale `aligned:` references remain | `grep -r 'aligned:' --include='*.md'` across both plugin dirs, filter known exceptions |
| Skill count | Each plugin.json lists correct skills | Count entries in `skills` array, compare to directory listing |
| Independent loading | Each plugin loads without the other | Load each via `--plugin-dir` in isolation, verify skill list |
| Cross-plugin invocation | Works skill can invoke advisor skill | Load both plugins, invoke a works skill that dispatches an advisor skill |

## Decision Log

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | This repo → aligned-works, extract advisors | Advisors is the cleaner extraction (self-contained files, no agent/hook deps) |
| 2 | Bundle at launch, defer graceful degradation | Avoid premature abstraction on a boundary that might shift |
| 3 | Mono-repo, flat split | Preserves ../../ plugin-root pattern; atomic cross-plugin changes |
| 4 | Symlinks for cross-references | Zero changes to existing advisor path references |
| 5 | Content gen + portability-audit → personal global | Brand-specific / single-use, not plugin material |
| 6 | verification-before-completion, create-svg-diagram → works | Advisors is purely personas and frameworks |
| 7 | persona-panel → works | Uses project-local personas, not advisor files |
| 8 | Glob disambiguation via two-step find-and-verify | Behavior change from single-step filter; 7 instances across 5 files |
| 9 | Naming: aligned-advisors + aligned-works | Validated by advisor panel (2026-04-07). Zero ambiguity. |
| 10 | Keep all 5 advisor skills in advisors, drop Desktop claim | add-advisor/add-framework/find-potential-advisors use CLI features; Desktop compat is a future goal |
| 11 | Feature branch for migration | Isolates broken intermediate state from main |

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Symlinks not followed during cache copy | ~~High~~ Resolved | Confirmed working per plugins-reference docs + empirical test (2026-04-08) |
| Large git diff from mass file moves | Low | Feature branch + `git mv` preserves history tracking |
| Skill name prefix change breaks muscle memory | Low | Clear migration docs; old prefix fails with helpful error |
| Hook discovery path change | Medium | Phase 0 step 2 tests `CLAUDE_PLUGIN_ROOT` resolution before any moves |
| Windows symlink portability | Low | Symlinks require Developer Mode on Windows; document in both READMEs |
| Marketplace snapshot staleness | Low | Both plugins version together; updating advisors requires reinstalling works |
