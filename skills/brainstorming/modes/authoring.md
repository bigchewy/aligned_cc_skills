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
2. **Auto-select fires on an advisor (no framework match)** → Phase 2b (advisor runner).
3. **Shortlist mode** → present the unified shortlist; user picks an entry; route to 2a or 2b based on entity type.
4. **No high-confidence match (Stage 1 returns candidates but none auto-select)** → Phase 2c (structured Q&A; top-scoring topic advisor in proxy seat).
5. **Zero candidates** (both registries returned nothing after domain filter — extremely rare given 154 frameworks + 70 advisors) → Phase 2d (structured Q&A with Wise Eric in proxy seat).

Path 4 of `contextual-recommendation.md` (the "what problem are you working on?" prompt) is reserved for top-level skill invocations where the user invoked `/aligned:use-advisor` with no args and no conversation context. Authoring mode always has a topic; Path 4 never fires from here.

**Project scan failure handling:** If `/tmp/brainstorm-context-{topic}/project-scan.md` is missing or empty (scan failed or hadn't completed when Phase 1 ran), proceed without scan context; engine selection runs on topic alone; user is notified ("Scan unavailable — proceeding with topic-only engine selection."). Phase 2 may re-check for the scan and incorporate it when available.

### Phase 2: Engine execution

Four paths based on Phase 1 result:

### Phase 2a: Framework runner (engine = framework)

Read `skills/_shared/framework-runner.md` and invoke it with:
- **Matched framework path:** from Phase 1
- **`intake_gate_mode`:** `strict` (brainstorming wrapper gates on `required_documents`)

On framework completion, the runner returns control here. Proceed to Phase 3.

### Phase 2b: Advisor runner (engine = advisor)

Read `skills/_shared/advisor-runner.md` and invoke it with:
- **Matched advisor path:** from Phase 1

On advisor session completion, the runner returns control here. Proceed to Phase 3.

### Phase 2c/2d: Structured Q&A with topic advisor in proxy seat

The Q&A pattern is duplicated from `modes/software.md` (L22-134). See the parity marker below.

For Phase 2c (top-scoring advisor) — use the top-scoring advisor's prompt in the proxy dispatch.
For Phase 2d (Wise Eric default) — use `advisors/prompts/wise-eric.md`.

<!-- PARITY MARKER: DUPLICATED FROM skills/brainstorming/modes/software.md (Q&A pattern, L22-134).
     The Architect-as-proxy dispatch template (the sub-agent prompt body below) is the stable surface
     for the parity test (e2e/tests/test_qa_pattern_parity.py). Sync substantive changes to both files
     or document the intentional divergence in this marker. See decision 4 in
     docs/plans/2026-05-09-framework-runner-refactor-design.md. -->

**Understanding the idea:**

**MANDATORY: The router has already dispatched a project scan.** Results will be available at `/tmp/brainstorm-context-{topic}/project-scan.md`. Do not dispatch a second scan.

**Overlap with first business question:** Do not wait for the scan to complete before starting Q&A. Immediately ask your first business question (about intent, scope, or priorities — see business question criteria below). The scan runs in parallel while the user responds. This eliminates dead wait time without skipping context gathering.

**Scan gate:** Before asking any **content-design** question or dispatching a {topic_advisor} auto-consult, the scan MUST have completed and you MUST have reviewed the summary. If the user responds to the first business question before the scan finishes, ask another business question — do not idle. Once the scan completes, incorporate the summary as working context for all subsequent questions.

**MANDATORY: Ask a minimum of 3 business questions before proposing any approaches or design sections.** Even when the user's request seems fully specified, there are always unstated assumptions about scope, priorities, and constraints. Do not shortcut the Q&A because the problem seems obvious.

Ask questions one at a time to refine the idea. Before asking each question, classify it:

- **Business questions** (ask the user): See "What stays user-facing" under {topic_advisor} auto-consult below.
- **Content-design questions** (auto-resolve via {topic_advisor}): See "What counts as content-design" under {topic_advisor} auto-consult below.

**For business questions:** Ask the user directly. Prefer multiple choice when possible. One question per message.

**For content-design questions:** Do NOT ask the user. Instead, dispatch {topic_advisor} as the user's proxy to answer the question (see "{topic_advisor} as proxy" under auto-consult below). Each content-design question gets its own fresh sub-agent dispatch — the answer comes back to the main thread, you incorporate it, and it shapes what questions come next (which may be business or content-design). Briefly note each decision to the user: what was decided and why (one sentence), plus any constraints flagged — so they have visibility without needing to weigh in.

**Gray area:** If a question has both business and content-design dimensions, ask the user the business dimension **first**. Only after the user answers, and only if their answer warrants it, dispatch {topic_advisor} as proxy for the content-design dimension.

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**When options involve layout or structure:** Never use ASCII art in AskUserQuestion markdown previews for comparisons — they are too low-fidelity for the user to evaluate. Instead:

1. Draft the approach options as normal.
2. Classify the options and consult the right advisor:
   - **Content structure decisions** (sequence, grouping, coverage hierarchy, arrangement) → run the {topic_advisor} auto-consult (below).
   - **Layout/usability decisions** (scanning, navigation, labeling, user flow, conventions) → consult Steve Krug (`advisors/prompts/steve-krug.md`) using the same auto-consult dispatch pattern, substituting Krug's prompt for {topic_advisor}'s.
   - **Both apply?** Consult both in parallel.
3. Dispatch the mockup-generator agent with the advisor-refined options to create a comparison mockup with all options as switchable tabs. Use this dispatch template — replace placeholders with actual values. Uses `subagent_type=general-purpose`.

   "Read `agents/mockup-generator.md` for your full workflow. Generate a comparison mockup showing {number} approach options for: {brief description of what's being compared}. Project root: `{project-root}`. Brainstorming session topic: `{topic}`. Create a single HTML file at `docs/mockups/{session-name}/approach-comparison.html` with tabbed navigation to switch between options. Each tab should be labeled with the approach name and include a short description of the trade-offs. Open the file in the browser after generating."

4. After the user has reviewed the HTML mockup in the browser, proceed with the approach selection question.

**{topic_advisor} auto-consult:**

Before presenting content-design content to the user — whether it's a question with options or a design section — consult {topic_advisor} first. This applies in every phase: understanding, exploring approaches, and presenting the design.

**Trigger:** Any of these situations:
- **Q&A phase (proxy mode):** You need to answer a content-design question to continue the brainstorm (routed here instead of asking the user — see question classification above). Use the "{topic_advisor} as proxy" dispatch below.
- **Presenting options (review mode):** You are about to show the user options that contain content-design alternatives. Use the standard review dispatch below.
- **Presenting design sections (review mode):** You are about to present a design section that embeds content-design choices as assertions. This case is easy to miss — presenting a design section *is* presenting a content-design decision, even though it looks like a statement rather than a question. Use the standard review dispatch below.

**Mode difference:** In proxy mode, {topic_advisor} makes decisions (the "do not propose alternatives" constraint is lifted). In review mode, {topic_advisor} critiques only — it recommends which option fits best but does not override the user's choice. These are different behavioral contracts for the same persona.

**What counts as content-design:** Arrangement choices, sequencing principles, framework scaffold selection, corpus coverage, audience-fit validation, constraint satisfaction — anything where the answer depends on domain expertise and content patterns rather than user preference.

**What stays user-facing without consult:** Topic direction, feature scope, success criteria, priorities, UX preferences, target audience, naming/branding, "do you want X or Y element", what problem to solve, what outcome matters, deadlines, trade-off preferences between scope/quality/speed, interaction style choices.

**{topic_advisor} as proxy** (Q&A-phase content-design questions):

The user has delegated content-design decision authority to {topic_advisor}. The brainstorm's iterative back-and-forth rhythm stays the same — but content-design turns go to {topic_advisor} (via fresh sub-agent each time) instead of to the user. Each answer feeds back into the main thread and shapes what comes next, just like a human domain advisor sitting in the session.

1. Dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with this template:

   "[Full contents of `advisors/prompts/{topic_advisor}.md`]

   **Role override for this dispatch:** You are acting as the user's proxy for content-design decisions during a brainstorming session. Your normal constraint of 'do not propose alternatives' is suspended — the user has explicitly delegated technical decision-making to you. Investigate the codebase and make a recommendation.

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Content-design question to resolve for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Question: {the content-design question that needs answering}

   Investigate the existing content and registries. Make a decision grounded in existing patterns, domain knowledge, and content structure. If you identify multiple viable approaches, pick the one that best fits and explain why.

   Output format:
   - **Decision:** What to do (one clear answer)
   - **Reasoning:** Why this fits, citing specific files, patterns, or conventions
   - **Constraints:** Any preconditions, caveats, or risks that affect the design (e.g., 'requires migrating X first', 'incompatible with planned approach Y')"

2. Incorporate the decision into the brainstorm's working context. {topic_advisor}'s answer will often shape what the next question is — that's the point. Continue the Q&A flow: if the next question is business, ask the user; if content-design, dispatch a fresh {topic_advisor} agent. Each new dispatch includes accumulated context from prior decisions (e.g., "Prior decisions: {list}. New question: {question}").
3. Briefly note each {topic_advisor} decision to the user: what was decided and why (one sentence), plus any constraints flagged — do not drop caveats that affect the design.

**Standard review workflow** (presenting options or design sections):

1. Draft the content you're about to present (options, design section, or both)
2. Before presenting to the user, dispatch a sub-agent via Task tool (`subagent_type=general-purpose`, `model=opus`) with {topic_advisor}'s persona to review it. Use this dispatch template — replace placeholders with actual values:

   "[Full contents of `advisors/prompts/{topic_advisor}.md`]

   You have access to Glob, Grep, and Read tools. Do not use Bash for searching — use the Grep tool instead. For project context, first read `/tmp/brainstorm-context-{topic}/project-scan.md` — it contains a prior scan of the project structure, patterns, and conventions. Use this as a starting point rather than re-exploring from scratch.

   Review this content-design content before it is presented to the user for the project at `{project-root}`:

   Context: {1-2 sentences on what the user is building and key constraints/decisions established so far}
   Content to review:
   {the draft question with options OR design section text}

   Investigate the existing content and registries. If the content presents options, recommend which best fits current patterns. If the content presents a design, validate it — check for missing elements, broken sequences, wrong assumptions, integration risks. In either case, ground your analysis in specific evidence.

   Output format:
   - **Verdict:** APPROVE or REVISE
   - **Recommendation:** What to change and why, citing specific files, patterns, or conventions
   - **Key findings:** Evidence that informed the review"

3. Incorporate {topic_advisor}'s findings:
   - If REVISE: fix the issues before presenting. Note the input briefly (e.g., "The advisor caught a missing section — added.")
   - If presenting options: lead with the advisor-recommended option and include their domain-grounded reasoning. Still present all options — {topic_advisor} advises, the user decides.

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
- Fallback ladder paths 2c/2d are structured Q&A — never free exploration.
- Wise Eric is the last-resort default proxy. His prompt handles "I'm not sure what I need" gracefully.
