# Visualization Runner Extraction + `visualize-design` Skill — Design

**Date:** 2026-06-11
**Mode:** Software brainstorm
**Topic:** visualization-skill
**Mockups:** docs/mockups/2026-06-11-visualization-skill.html

## Goal

Make the design-doc HTML visualization (today locked inside the brainstorming skill's `references/visualization-protocol.md`) available as a standalone, user-callable capability — `/aligned:visualize-design` — while keeping brainstorming's software and authoring modes on the exact same engine. One engine, two callers, zero duplicated procedure.

A second, equally weighted goal rides along: the overview surface of every generated artifact must read at **executive altitude**. Today's artifacts open into walls of implementation detail (KB-086). The extraction is the vehicle for fixing that at the source — in the shared engine and templates — so every consumer inherits it.

## Why now

- The visualization procedure is wanted outside brainstorming (rendering arbitrary docs/threads with the same on-brand, tabbed, Mermaid-validated artifact).
- KB-085 (browser-open step reliably skipped) and KB-086 (goal/success criteria buried) name **two** causes, which KB-086 frames as **co-equal and both worth fixing independently**: the agent's compact-direct-write shortcut (hand-writing tighter HTML directly, never reaching the template, the protocol, or any gate) and protocol steps written as skippable prose. KB-085 lists the shortcut first among four unranked hypotheses; KB-086's cross-reference identifies the shortcut as the root cause shared by both bugs. This design addresses both causes — an explicit anti-shortcut contract at every entry point (primary) and the fail-closed runner structure from the framework-runner refactor (`docs/plans/completed/2026-05-09-framework-runner-refactor-design.md`) (secondary). Honest claim scope: the anti-shortcut contract is still an instruction to an LLM; this work *mitigates* KB-085/086 and makes violations visible, but closure is confirmed only by observing subsequent sessions — the KB entries move to done when that evidence exists, not at merge time.
- KB-073 and KB-087 both name `visualization-protocol.md` as a file to change; consolidating before further edits reduces churn.

## Architecture — the three-piece split

### 1. `skills/_shared/visualization-runner.md` (new — the engine)

Caller-independent, written in the framework-runner house style: **Configuration** block, **Configuration Validation (fail-closed)**, numbered steps, **Avoid These Mistakes** list. No YAML frontmatter (house rule for `_shared/`).

Owns:
- Design-token resolution ladder (project `docs/design/design-principles.md` → monorepo glob → global fallback, with the placeholder heuristic and user warning).
- Verbatim template copy-and-patch contract ("the file copy is the contract — do not rewrite from memory").
- **Anti-shortcut contract** (KB-085/086 primary-cause fix): the runner's first numbered step and each caller's dispatch text state explicitly — *copy the template file with a file-copy command and patch it; NEVER hand-write or "compactly rewrite" the artifact HTML, even when that seems faster*. The compact-direct-write shortcut is named as a forbidden move in the runner's "Avoid These Mistakes" list so the violation is recognizable, not just discouraged.
- **Executive-overview rule** (produce + verify; see Runner Contract below).
- Widget injection procedure (CSS into `<head>`, SCRIPT before `</body>` outside LIVE-REFRESH delimiters, HTML blocks per section; flat <10 entries, categorized >=10).
- **Unconditional, numbered browser-open step** (KB-085 fix).
- Mermaid validation gate — invokes `skills/brainstorming/scripts/validate-mermaid.mjs` by absolute path; exit 0 required to proceed.
- Strip-script rule (canonical text relocated here from `shared-rules.md`; one-line pointer left behind).
- Nested sub-tabs rule.

### 2. `skills/visualize-design/SKILL.md` (new — standalone caller)

Thin caller. Owns source resolution, session naming, the live-session wiring, and the `docs/design-visualizations/` output convention. Detailed below.

### 3. `skills/brainstorming/references/visualization-protocol.md` (kept, slimmed — brainstorming caller)

Stays at its e2e-pinned path (`e2e/tests/test_brainstorming_files.py` pins the literal path; it must remain a readable file). Slims to the brainstorming-specific lifecycle:
- Live-update-per-validated-section loop.
- Pre-critique snapshot to `docs/mockups/{session-name}.html`.
- Post-critique regeneration.
- A Configuration block populated with **absolute paths** (the wrapper resolves its own `{base-directory}`-relative values — shared files never self-resolve, per `skills/_shared/resolve-skill-path.md`) plus a delegation: "follow `skills/_shared/visualization-runner.md`." **Pointer placement is load-bearing:** the delegation is the first actionable line after the Configuration block, not buried in prose — pointer-style steps are the documented skip class (KB-085), and a skipped delegation leaves the agent holding a wrapper that no longer contains the procedure.

`skills/brainstorming/modes/software.md` and `modes/authoring.md` are untouched — they keep referencing the protocol file.

### What stays physically where it is

`templates/`, `widgets.html`, `brainstorm-components.md` (all in `skills/brainstorming/references/`) and `validate-mermaid.mjs` + its npm dependency (in `skills/brainstorming/scripts/`) do not move. The runner takes their paths as Configuration inputs. Moving the npm-dependency directory is blast radius for zero functional gain.

## Runner contract

**Configuration inputs** (all absolute, resolved by the caller):

| Input | Meaning |
|---|---|
| `{template-path}` | The HTML template to copy verbatim |
| `{widgets-path}` | `widgets.html` (widget CSS/JS/HTML blocks) |
| `{components-path}` | `brainstorm-components.md` (token contract + component classes) |
| `{source-content}` | Validated sections or document body to render |
| `{title}` / `{subtitle}` / `{context}` | Header values patched into the template |
| `{output-path}` | Final committed artifact location |
| `{live-session}` | yes/no — self-refreshing /tmp artifact vs one-shot |
| `{project-root}` | For the token-resolution ladder |

**Fail-closed validation:** every referenced file must exist; `{output-path}` parent must be writable; missing or unresolvable config halts with a named error instead of improvising. Numbered steps with hard gates make skipping visible — the structural fix for KB-085/086.

**Executive-overview rule — produce, then verify:**

1. **Produce (template-guaranteed after commit 2):** today the templates ship an empty `<!-- Tab bar and content panels go here -->` skeleton — the Overview structure does not exist yet. **Commit 2 bakes it in**: a pre-built tab bar whose first tab is `Overview` (`panel-overview active`), containing placeholder slots `{goal}`, `{why-it-matters}`, `{outcome}`. From then on, a verbatim copy carries the structure — it can be filled in but not omitted. The generating agent fills the slots at executive altitude: what this is, why it matters, what outcome it produces — plain language a non-engineer scans in under a minute. No Mermaid, no file paths, no implementation vocabulary **on that tab** (detail tabs keep their file paths and diagrams); roughly one screen. Applies from the first live render. **Honesty scope:** like the anti-shortcut contract, this guarantee holds only on the copy path — an agent taking the compact-direct-write shortcut never sees the scaffold, and the mechanical sub-check below has no Overview panel to grep. The scaffold and the anti-shortcut contract are complementary mitigations, not a closed loop.
2. **Verify (pre-snapshot gate):** a numbered step before any snapshot is written. Two parts, honestly labeled:
   - **Mechanical sub-check (assertable, fail-closed):** the Overview panel contains zero `<pre class="mermaid">`/`<pre class="mermaid-deferred">` blocks and zero `.file-path` spans. This is a grep, same enforceability class and same pass/fail contract as the mermaid gate: **nonzero match → rewrite the Overview before any snapshot is written.**
   - **Semantic self-check (not unit-testable, never blocks):** goal stated in the first two sentences? plain language? fits one screen? This is an LLM judgment with no mechanical assertion — it is explicitly *not* claimed to have parity with the mermaid exit-code gate. Fail → rewrite the overview, re-check once. **On a second failure, write the artifact anyway** and tell the user in one line which check failed and where the lever is (e.g., "Overview still leads with implementation detail — committed as-is; edit the Overview tab's `{goal}` slot to fix"). A soft semantic judgment never holds the user's output hostage; only the mechanical checks block.

## The `visualize-design` skill

Invoked as `/aligned:visualize-design`, optionally with a markdown file path argument.

- **Source resolution:** path argument → read that document. No argument → use validated content from the current conversation. Neither yields enough content → ask exactly this question (fixed wording, so the bare-invocation experience is stable run to run): *"No document path was given and this conversation has no renderable content yet. Give me either: (a) a path to a markdown doc to visualize, or (b) a one-sentence description of what to visualize and I'll build it with you here."*
- **Template path resolution (the load-bearing cross-skill reach):** resolve the plugin root per `skills/_shared/resolve-skill-path.md`, then use `{plugin-root}/skills/brainstorming/references/templates/software-template.html`. The skill never uses `{base-directory}`-relative resolution for this — that resolves against `visualize-design/`, where no templates exist.
- **Session flow (live, same rhythm as brainstorming):** derive `{session-name}` = `YYYY-MM-DD-<topic-slug>`; resolve brand tokens via the runner's ladder; copy and patch the template (Decision 5); open the self-refreshing `/tmp` artifact in the browser immediately; update as the user iterates. Mermaid diagrams via the same flowchart-generator / architecture-diagram-generator agent dispatches brainstorming uses.
- **Finish:** on user confirmation, run the mermaid gate and executive-overview check, write the final copy to `{project-root}/docs/design-visualizations/{session-name}.html` (create the directory if missing), strip the live-refresh script, open the committed copy. **If `{output-path}` already exists, overwrite it** — re-rendering the same doc the same day is the expected workflow, not an error.
- **Not included:** critique panel, `**Mockups:**` header field — brainstorming scaffolding, not part of a general visualizer.
- **Widgets:** injected only if the content actually contains a Decision Log or Open Questions section; same flat/categorized thresholds.

## Migration — four commits, no-behavior-change first

1. **Extract.** Create `visualization-runner.md`; slim `visualization-protocol.md` to the wrapper. This commit makes **three content relocations, all named**: (a) the strip-script rule moves from `shared-rules.md` to the runner (pointer left behind); (b) the nested sub-tabs rule moves from the protocol to the runner; (c) the engine steps themselves. Because of (b), `modes/software.md:152` ("the Nested sub-tabs rule defined in the protocol") gets a **one-line reference edit** in this commit — the "modes untouched" claim is scoped to *behavior*, not file bytes: brainstorming behavior-equivalent, with exactly one reference-wording edit in software.md. Guard work in this same commit, **all authored, none inherited — two files, two distinct guards**: (1) add the runner to `e2e/eval-surface.yaml` AND write `test_visualization_runner_is_in_eval_surface` in **`test_shared_runners.py`**, mirroring `test_framework_runner_is_in_eval_surface` (lines 37–41) and `test_advisor_runner_is_in_eval_surface` (lines 60–62) — eval-surface membership guards live in that file, and no generic enforcement exists, so omitting this assertion passes green; (2) add cross-reference guard tuples wrapper→runner to `REQUIRED_CROSS_REFS` in **`test_skill_cross_references.py`** — that file asserts reference resolution, not eval-surface membership. Note the tuple's actual trigger: it fails when the *wrapper lacks the reference*, not when the runner file appears — which is why both guards must be written by hand in this commit.
2. **Fix KB-085/086 in the engine.** Anti-shortcut contract text in the runner and both callers; unconditional browser-open step; Overview-tab scaffold baked into the five visualizing templates (`software-template.html` + four authoring variants) with the three placeholder slots; executive-altitude verify gate (mechanical sub-check + semantic self-check). The scaffolding test work is a **rewrite, not an update**: `test_authoring_templates_share_common_scaffolding` currently lists only the 4 authoring templates and asserts nothing but `"<script" in text` — add `software-template.html` to its file list, replace the script-presence check with real assertions (`panel-overview active` + the three placeholder slots), and rename the function since it no longer covers only authoring templates.
3. **Add `visualize-design`.** New SKILL.md calling the runner; README skill-table row; version bump in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; new e2e structural test mirroring the `test_brainstorming_files.py` pattern.
4. **Optional cleanup.** Point flowchart-generator / architecture-diagram-generator / mockup-generator at the runner's token-resolution section instead of each restating the ladder. Sequenced last so it cannot block the core work.

**Pre-commit-1 housekeeping:** land or stash the uncommitted `widgets.html` edit; grep `e2e/trigger-map.yaml` to confirm no path reference to the protocol (expected absent — verify, don't assume).

## Testing

All pytest, in `e2e/tests/`, each test landing in the commit that creates what it pins:

- **Commit 1:** a **new, hand-written** `test_visualization_runner_is_in_eval_surface` in `test_shared_runners.py` (mirroring that file's framework-runner/advisor-runner assertions — there is no generic "every `_shared/` runner" enforcement to inherit); cross-reference tuples wrapper→runner in `test_skill_cross_references.py`'s `REQUIRED_CROSS_REFS`; slimmed protocol still readable at its pinned path and references the runner; strip-rule pointer present in `shared-rules.md`; runner doc carries no YAML frontmatter; `software.md:152` reference wording updated to point at the runner.
- **Commit 2:** scaffolding test **rewritten** (see Migration step 2): file list gains `software-template.html`, trivial `"<script"` assertion replaced with `panel-overview active` + three-slot assertions across the five visualizing templates, function renamed.
- **Commit 3:** structural test for `visualize-design` — SKILL.md exists, frontmatter `name` matches directory, references the runner; cross-reference tuple skill→runner.

## Decision Log

1. **Engine lives in `skills/_shared/visualization-runner.md`** — follows the framework-runner precedent exactly; two skill callers plus three agents make it plugin-wide, not skill-local.
2. **Executive-overview rule applies to all callers** — baked into the shared engine and templates, not the standalone skill alone.
3. **Standalone output goes to `docs/design-visualizations/`** — brainstorming keeps `docs/mockups/` (path pinned by e2e tests and consumed by writing-plans / finishing-a-development-branch).
4. **Standalone defaults to a live self-refreshing session** — same rhythm as brainstorming; final stripped copy written on completion.
5. **`visualize-design` reuses brainstorming's `software-template.html` by absolute path** — resolved via plugin root per `skills/_shared/resolve-skill-path.md`, never `{base-directory}`-relative. Deliberate cross-skill coupling; any brainstorming edit to the template changes `visualize-design` output. Shipping a copy would recreate the duplication `docs/kanban/done/KB-036-duplicated-viz-protocol-mode-files.md` fixed. Divergence (own template) deferred until actually needed.
6. **Overview tab is baked into the templates by commit 2 (produce + verify), paired with an explicit anti-shortcut contract** — once baked in, template-guaranteed structure cannot be skipped *when the template is copied*; KB-086 names the compact-direct-write shortcut (the agent never copying the template at all) as a co-equal cause the scaffold alone cannot reach, so the runner and both callers carry explicit "copy the file; never hand-write the artifact" text, and the design claims mitigation, not closure, of those KBs.
7. **Strip-script rule relocates to the runner** — both callers need it; `shared-rules.md` keeps a one-line pointer so brainstorming's existing read resolves.
8. **Templates, widgets, components doc, and mermaid script stay physically in `skills/brainstorming/`** — the runner takes paths as config; moving the npm-dependency directory is unnecessary blast radius.
9. **`visualization-protocol.md` keeps its exact path** — hard-pinned by `test_brainstorming_files.py`; it becomes the brainstorming wrapper rather than moving.
10. **Skill name: `visualize-design`** — invoked as `/aligned:visualize-design`.
11. **Input is doc path or conversation content** — argument renders a file; no argument renders the current thread's validated content.
12. **Executive-overview check is a numbered step gate split into a mechanical sub-check and a semantic self-check** — the mechanical half (zero mermaid blocks / zero file-path spans in the Overview panel) is grep-assertable; the semantic half (altitude, length) is an LLM self-check with one retry and no claimed parity with the mermaid exit-code gate.
13. **Commit 1 is behavior-equivalent, not byte-equivalent** — three named content relocations (strip rule, nested sub-tabs rule, engine steps) plus a one-line reference edit in `modes/software.md:152`; all guards are authored by hand in the same commit because no generic enforcement exists to inherit — the eval-surface assertion in `test_shared_runners.py`, the cross-ref tuples in `test_skill_cross_references.py` (two files, two guards).
14. **Same-day re-renders overwrite** — `visualize-design` writing to an existing `{output-path}` overwrites silently; render→tweak→re-render is the expected workflow, and a prompt on every re-run would be compounding ceremony.

## Open Questions

None blocking. Two items deferred by design: template divergence for `visualize-design` (Decision 5) and the agent token-ladder dedup (commit 4, optional).
