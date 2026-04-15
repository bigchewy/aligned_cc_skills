<!-- Mode file: Read into context by the brainstorming router. Do not add YAML frontmatter. -->

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by dispatching a project scan sub-agent to survey the codebase, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

## The Process

**Understanding the idea:**

**MANDATORY: The router has already dispatched a project scan.** Results will be available at `/tmp/brainstorm-context-{topic}/project-scan.md`. Do not dispatch a second scan.

**Overlap with first business question:** Do not wait for the scan to complete before starting Q&A. Immediately ask your first business question (about intent, scope, or priorities — see business question criteria below). The scan runs in parallel while the user responds. This eliminates dead wait time without skipping context gathering.

**Scan gate:** Before asking any **technical** question or dispatching an Architect auto-consult, the scan MUST have completed and you MUST have reviewed the summary. If the user responds to the first business question before the scan finishes, ask another business question — do not idle. Once the scan completes, incorporate the summary as working context for all subsequent questions.

If a question during the brainstorm requires deeper detail about the project (e.g., how a specific module works, what pattern an existing feature follows), read `/tmp/brainstorm-context-{topic}/project-scan.md` for the raw findings rather than re-exploring the codebase in the main thread.

**MANDATORY: Ask a minimum of 3 business questions before proposing any approaches or design sections.** Even when the user's request seems fully specified, there are always unstated assumptions about scope, priorities, and constraints. Do not shortcut the Q&A because the problem seems obvious.

Ask questions one at a time to refine the idea. Before asking each question, classify it:

- **Business questions** (ask the user): See "What stays user-facing" under Architect auto-consult below.
- **Technical questions** (auto-resolve via Architect): See "What counts as technical" under Architect auto-consult below.

**For business questions:** Ask the user directly. Prefer multiple choice when possible. One question per message.

**For technical questions:** Do NOT ask the user. Instead, dispatch The Architect as the user's proxy to answer the question (see "Architect as proxy" under Architect auto-consult below). Each technical question gets its own fresh sub-agent dispatch — the answer comes back to the main thread, you incorporate it, and it shapes what questions come next (which may be business or technical). Briefly note each decision to the user: what was decided and why (one sentence), plus any constraints flagged — so they have visibility without needing to weigh in.

**Gray area:** If a question has both business and technical dimensions (e.g., "should we support offline mode?" is business scope + technical feasibility), ask the user the business dimension **first** ("Is offline support important for your users?"). Only after the user answers, and only if their answer warrants it, dispatch The Architect as proxy for the technical dimension (e.g., if the user says offline matters, send The Architect the question "what's the best offline architecture approach given the current codebase?").

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**When options involve UI or layout:** Never use ASCII art in AskUserQuestion markdown previews for UI comparisons — they are too low-fidelity for the user to evaluate. Instead:

1. Draft the approach options as normal.
2. Classify the options and consult the right advisor:
   - **Technical UI decisions** (component patterns, state management, module boundaries, where logic lives) → run the Architect auto-consult (below).
   - **UX/usability decisions** (layout clarity, navigation, scanning, labeling, user flow, conventions) → consult Steve Krug (`advisors/prompts/steve-krug.md`) using the same auto-consult dispatch pattern, substituting Krug's prompt for The Architect's.
   - **Both apply?** Consult both in parallel.
3. Dispatch the mockup-generator agent with the advisor-refined options to create a comparison mockup with all options as switchable tabs. Use this dispatch template — replace placeholders with actual values. Uses `subagent_type=general-purpose`.

   "Read `agents/mockup-generator.md` for your full workflow. Generate a comparison mockup showing {number} approach options for: {brief description of what's being compared}. Project root: `{project-root}`. Brainstorming session topic: `{topic}`. Create a single HTML file at `docs/mockups/{session-name}/approach-comparison.html` with tabbed navigation to switch between options. Each tab should be labeled with the approach name and include a short description of the trade-offs. Open the file in the browser after generating."

4. After the user has reviewed the HTML mockup in the browser, proceed with the approach selection question.

**Architect auto-consult:**

Before presenting technical content to the user — whether it's a question with options or a design section — consult The Architect first. This applies in every phase: understanding, exploring approaches, and presenting the design.

**Trigger:** Any of these situations:
- **Q&A phase (proxy mode):** You need to answer a technical question to continue the brainstorm (routed here instead of asking the user — see question classification above). Use the "Architect as proxy" dispatch below.
- **Presenting options (review mode):** You are about to show the user options that contain technical alternatives. Use the standard review dispatch below.
- **Presenting design sections (review mode):** You are about to present a design section that embeds technical choices as assertions (e.g., "here's the state machine with states X, Y, Z"). This case is easy to miss — presenting a design section *is* presenting a technical decision, even though it looks like a statement rather than a question. Use the standard review dispatch below.

**Mode difference:** In proxy mode, The Architect makes decisions (its "do not propose alternatives" constraint is lifted). In review mode, The Architect critiques only — it recommends which option fits best but does not override the user's choice. These are different behavioral contracts for the same persona.

**What counts as technical:** Data model choices, type structures, where to put state, which layer handles something, API shape, streaming behavior, tool design, module boundaries, persistence strategies, integration approach, state machines, lifecycle flows, component patterns — anything where the answer depends on the existing codebase rather than user preference.

**What stays user-facing without consult:** Product direction, feature scope, success criteria, priorities, UX preferences, target audience, naming/branding, "do you want X or Y feature", what problem to solve, what outcome matters, deadlines, trade-off preferences between scope/quality/speed, interaction style choices.

**Architect as proxy** (Q&A-phase technical questions):

The user has delegated technical decision authority to The Architect. The brainstorm's iterative back-and-forth rhythm stays the same — but technical turns go to The Architect (via fresh sub-agent each time) instead of to the user. Each Architect answer feeds back into the main thread and shapes what comes next, just like a human technical advisor sitting in the session.

1. Dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with this template:

   "[Full contents of `advisors/prompts/the-architect.md`]

   **Role override for this dispatch:** You are acting as the user's proxy for technical decisions during a brainstorming session. Your normal constraint of 'do not propose alternatives' is suspended — the user has explicitly delegated technical decision-making to you. Investigate the codebase and make a recommendation.

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Technical question to resolve for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Question: {the technical question that needs answering}

   Investigate the existing codebase. Make a decision grounded in existing patterns, conventions, and architecture. If you identify multiple viable approaches, pick the one that best fits the codebase and explain why.

   Output format:
   - **Decision:** What to do (one clear answer)
   - **Reasoning:** Why this fits the existing codebase, citing specific files, patterns, or conventions
   - **Constraints:** Any preconditions, caveats, or risks that affect the design (e.g., 'requires migrating X first', 'incompatible with planned move to Y')"

2. Incorporate the decision into the brainstorm's working context. The Architect's answer will often shape what the next question is — that's the point. Continue the Q&A flow: if the next question is business, ask the user; if technical, dispatch a fresh Architect agent. Each new dispatch includes accumulated context from prior decisions (e.g., "Prior decisions: {list}. New question: {question}").
3. Briefly note each Architect decision to the user: what was decided and why (one sentence), plus any constraints flagged — do not drop caveats that affect the design.

**Standard review workflow** (presenting options or design sections):

1. Draft the content you're about to present (options, design section, or both)
2. Before presenting to the user, dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with The Architect's persona to review it against the codebase. Use this dispatch template — replace placeholders with actual values:

   "[Full contents of `advisors/prompts/the-architect.md`]

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Review this technical content before it is presented to the user for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Content to review:
   {the draft question with options OR design section text}

   Investigate the existing codebase. If the content presents options, recommend which best fits current patterns. If the content presents a design, validate it — check for missing states, broken flows, wrong assumptions, integration risks. In either case, ground your analysis in specific codebase evidence.

   Output format:
   - **Verdict:** APPROVE or REVISE
   - **Recommendation:** What to change and why, citing specific files, patterns, or conventions
   - **Key findings:** Codebase evidence that informed the review"

3. Incorporate The Architect's findings:
   - If REVISE: fix the issues before presenting. Note the input briefly (e.g., "The Architect caught a missing 'deploying' state — added.")
   - If presenting options: lead with the architect-recommended option and include their codebase-grounded reasoning. Still present all options — The Architect advises, the user decides.

**Presenting the design:**
- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

## After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- After visualization artifacts are generated, add a `**Mockups:**` field to the design document header listing the mockup directory path (e.g., `**Mockups:** docs/mockups/{session-name}.html`). This field is consumed by writing-plans and finishing-a-development-branch to locate mockups without guessing. If no visual artifacts were generated, omit the field.

**Visualization (mandatory):**

Every brainstorm produces a live visual artifact. After writing the design document and BEFORE the critique round, start the live visualization:

1. Read `skills/brainstorming/references/brainstorm-components.md` for the HTML template and component reference.
2. Write the initial HTML to `/tmp/brainstorm-{topic}-{timestamp}/live.html` using the template. Replace `{title}`, `{subtitle}`, and `{context}` with session-specific values. Use a timestamp (e.g., epoch seconds) to prevent collision if the same topic is brainstormed twice. Populate the initial content with the design sections validated so far.
3. Open the file in the default browser using a platform-aware pattern (separate Bash call — no `&&` chaining):
   `open /tmp/brainstorm-{topic}-{timestamp}/live.html || xdg-open /tmp/brainstorm-{topic}-{timestamp}/live.html`
   If both commands fail (headless environment), log a warning and continue — the artifact still gets written.
4. As each subsequent design section is validated in conversation, update the HTML file (Write tool) to add the new section's content. The browser picks up changes within 3 seconds via the self-refresh script.

**Nested sub-tabs rule (applies to mockup-generator dispatches and live visualization updates):**

When a tabbed HTML document is generated, use nested sub-tabs (progressive disclosure) whenever a single tab contains more detail than can be scanned in one view. Do not flatten into many top-level tabs or cram everything into one scrollable panel. The pattern is:
- **Top-level tabs** for major conceptual sections
- **Sub-tabs within each** for natural subdivisions (phases, layers, concerns)
- Each sub-tab holds **one focused diagram or content block**

The check: if a tab contains multiple diagrams, subgraphs, or sections that each deserve their own view, break them into nested sub-tabs rather than stacking vertically.

**Pre-critique snapshot:**

Before dispatching the critique panel, copy the live visualization to its permanent location so critics can access it:
1. Copy `/tmp/brainstorm-{topic}-{timestamp}/live.html` to `docs/mockups/{session-name}.html`
2. Add `**Mockups:** docs/mockups/{session-name}.html` to the design document header (write AFTER the copy so the file exists at commit time)
3. The critique panel's `visual-artifacts` config references `docs/mockups/{session-name}.html` — this copy ensures it exists at that path.

**Fact-Check + Critique Panel (mandatory, dynamic selection with division of labor):**

**Critique panel configuration:**
- Skill name: brainstorming
- Checklist filename: design-critique-checklist.md
- Fact-check mode: division-of-labor
- Fact-check tools: Glob, Grep, Read, Write
- Aggregation: sub-agent
- Criteria assignment: yes
- Visual artifacts: docs/mockups/{session-name}.html
- Critique temp directory: /tmp/brainstorm-critique-{topic}

**Architect independence note:** If The Architect was consulted during the auto-consult phase and is also selected as a critique panel critic, add this to The Architect's critique prompt: "This design followed an earlier Architect recommendation during brainstorming. Challenge the design with fresh eyes — do not assume the earlier recommendation was correct. Look for integration risks or pattern violations that a quick options evaluation might have missed."

**Criteria mapping table:**

| Criterion | Best-fit domains |
|-----------|-----------------|
| 1. Requirements completeness | product, prioritization, scope control, user problems |
| 2. Architecture feasibility | codebase alignment, patterns, module boundaries |
| 3. YAGNI violations | simplicity, focus, first principles, scope control |
| 4. Edge cases / error handling | edge cases, failure modes, testing, reliability |
| 5. Data flow clarity | codebase alignment, patterns, integration risk |
| 6. Integration points | integration risk, security, authentication, blast radius |
| 7. Testing strategy | testing, reliability, edge cases, failure modes |
| 8. Scope creep | focus, simplicity, scope control, prioritization |

Criterion 9 (Decision quality) goes to **all** critics. Each criterion 1-8 goes to exactly one critic. If no selected critic's domain matches a criterion, assign it to the fact-checker as catch-all. Target 2-4 criteria per critic.

**Fact-checker prompt template:**

"[Full contents of the critic's prompt file]

You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead (with output_mode 'count' when counting matches). Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `{visual-artifacts-path}` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec. Your job has two phases:
**Phase 1 (Fact-check):** You are the SOLE fact-checker — no other critic is verifying claims. Be thorough. Extract every factual claim about the codebase (file paths, function names, imports, data flows, config references). Verify each using Glob/Grep/Read. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage.
**Phase 2 (Critique):** Using the verification data you already gathered (do not re-verify), evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
Write your complete report to `{report-path}` using the Write tool — fact-check summary at the top, then critique in the checklist output format. Return only a one-line confirmation: 'Report written to {report-path}'."

**Regular critic prompt template:**

"[Full contents of the critic's prompt file]

You have access to Glob, Grep, Read, and Write tools. Do not use Bash for searching — use the Grep tool instead. Bash grep triggers security prompts that halt execution. Read `{checklist-path}` in full, then read `{design-file-path}` in full. Also review the visual artifacts at `{visual-artifacts-path}` — open the HTML file with Read and evaluate the visuals (mockups, flowcharts, architecture diagrams) alongside the written spec.
**IMPORTANT: You do NOT fact-check.** Another critic handles exhaustive verification of file paths, line numbers, and code claims in parallel. Do not extract and verify every claim — that work is covered.
Read key codebase files relevant to your domain expertise (enough to understand existing patterns and context), then evaluate the design against criteria {criteria-list} and 9 in the checklist through your lens. Also evaluate Decision Log entries if present. Tag every finding with your name.
Write your complete report to `{report-path}` using the Write tool — use the checklist output format. No fact-check summary section needed. Return only a one-line confirmation: 'Report written to {report-path}'."

**Shared orchestration file resolution:**
1. Primary: Read `{base-directory}/../_shared/critique-panel-orchestration.md` in full.
2. **Fallback** (if the base-directory line was compressed out of context): Use Glob to search `$HOME` for `**/_shared/critique-panel-orchestration.md`. Use the match that lives under a directory containing `.claude-plugin/plugin.json`.
Follow its process using the configuration and prompt templates above.

---

**POST-CRITIQUE CHECKLIST — 3 mandatory steps. Do not skip any. Do not stop after step 2.**

**Step 1 of 3 — Visualization finalization:**

**Post-critique update** (conditional): If the design document was modified by fact-check corrections or user-approved critique fixes, fully regenerate the HTML at `docs/mockups/{session-name}.html` from the corrected design using `skills/brainstorming/references/brainstorm-components.md`. Do not surgically edit — do a full rewrite from the corrected design to avoid drift.

Only skip regeneration if the design document is unchanged (all critique verdicts were APPROVE with no corrections applied).

**Strip the refresh script:** Verify that both `<!-- LIVE-REFRESH-START -->` and `<!-- LIVE-REFRESH-END -->` delimiters exist in `docs/mockups/{session-name}.html` before stripping. If either delimiter is missing, STOP and flag the issue — a committed artifact with an active refresh script is a silent bug. If both are present, remove the block (inclusive of delimiters). The final committed artifact must not auto-refresh.

**Step 2 of 3 — Commit:**

Commit the design document, visual artifacts (`docs/mockups/{session-name}.html`), and `docs/architecture.md` (if updated) to git after critique rounds are complete. Stage all together in one commit. **The session is NOT complete after this step — continue to step 3.**

**Step 3 of 3 — Next step prompt (mandatory):**

After committing the design document, present two options. **Resolve the plugin root path first:** the plugin root is two levels up from the base directory for this skill (`{base-directory}/../..`). If the base-directory line was compressed out of context, use Glob to search `$HOME` for `**/docs/ralph_loops/autopilot.sh` and use the match whose parent directory contains `.claude-plugin/plugin.json`. Store as `{plugin-root}`.

````
## Next Steps

### Option A: Hands-on (write plan interactively, then choose execution method)
I'll create a worktree and write the implementation plan now. You'll review the plan and choose how to execute it.

> Ready to proceed? I'll invoke `/aligned:using-git-worktrees` to create the worktree, then `/aligned:writing-plans` to write the plan.

### Option B: Autopilot (fully unattended — plan through verification)
Run from any terminal. Writes the plan, creates a worktree, executes all tasks via Ralph loop, checks mockup fidelity, and verifies the branch — but does NOT merge:
```bash
bash {plugin-root}/docs/ralph_loops/autopilot.sh \
  "{project-root}" \
  "{design-doc-path}"
```
Review the work when it finishes, then merge manually or run `/aligned:finishing-a-development-branch`.
````

If the user chooses Option A, invoke `/aligned:using-git-worktrees` to create the worktree, then output:

> `cd [worktree-path]` then use `/aligned:writing-plans` to write an implementation plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.

If the user chooses Option B, no further action is needed — the terminal command handles everything.

<!-- Note: {base-directory} refers to the router's directory (skills/brainstorming/), not this file's directory. -->

## Design Critique

When critiquing an existing design (instead of writing one), resolve the checklist path using the same MANDATORY resolution steps described above (base directory → Glob fallback → STOP if not found). Use the checklist at `{base-directory}/design-critique-checklist.md`. Launch fresh sub-agents for critique rounds to ensure independent evaluation. Verify every claim against the actual codebase — don't trust file paths, architecture claims, or integration assumptions without checking.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
