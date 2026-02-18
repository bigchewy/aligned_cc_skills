# Business Skills Sync — Design Document

**Date:** 2026-02-18
**Goal:** Synchronize the 4 business-oriented skills with improvements made to their software counterparts, preserving all business domain content while layering on structural upgrades.

## Mapping

| Business Skill | Software Counterpart | Gap Size |
|---|---|---|
| business-brainstorming | brainstorming | Moderate (149 vs 103 lines, but missing critic upgrades) |
| business-write-plan | writing-plans | Large (146 vs 469 lines) |
| business-diagnosis | systematic-debugging | Large (223 vs 345 lines, missing severity/multi-agent) |
| business-executing | executing-plans | Moderate (95 vs 171 lines) |

## Strategy

**Preserve all business-domain content.** The 4-phase gates, obstacle taxonomy, 5 Whys, task types catalog, writing quality standard, and all business-specific language stay untouched. New features are layered around the existing structure.

**Skip purely software-specific features.** No awkward translations of TDD cycles, worktree guards, bash instrumentation, cross-repo guards, eval scenarios, or dev server commands.

**Adapt features with natural business analogs.** Multi-critic architecture, autonomy modes, fact-checking, verification gates, severity levels, and multi-agent investigation all have clear business translations.

---

## Skill 1: business-brainstorming

### Preserved Content
- 4-phase gated process (Goal > Problems > Root Causes > Solutions)
- Obstacle categorization taxonomy (5 categories)
- "5 Whys" root cause technique
- Root cause indicators
- All business-specific phase content

### Added Features

**1. Fact-check phase in critic prompts**

The existing "Fact-Check + Critique Panel" section already instructs critics to verify claims and flag [UNVERIFIABLE] ones. Restructure this into an explicit two-phase structure matching brainstorming's format:
- **Phase 1 (Fact-check):** Extract every factual claim (market data, competitor assertions, financial assumptions, stakeholder claims, timeline assertions). Verify against evidence provided in the document. Use WebSearch/WebFetch to check external claims where possible. Mark claims as [CONFIRMED], [INCORRECT] with correction, or [UNVERIFIABLE]. Report accuracy percentage. Include source URLs for verified claims.
- **Phase 2 (Critique):** Evaluate against the checklist using verification data.

Fact-check results stay in the critic output (matching the brainstorming counterpart) — no standalone fact-check file.

**2. Escalation protocol for Round 2**

If Round 1 reveals concerns in a domain not covered by the selected critics, add one specialist critic for Round 2. State the escalation reason. Maximum one additional critic per round.

**3. Stronger sub-agent enforcement language**

The existing skill already instructs launching critics as parallel sub-agents. Add the bold "MANDATORY" enforcement language matching brainstorming: "You MUST use the Task tool to launch fresh sub-agents for every critique round. NEVER run the critique in the main context window. Running critique inline defeats the purpose and is a skill violation."

**4. Git commit after critique**

"Commit the design document to git after critique rounds are complete."

**5. Next-step handoff prompt**

After committing, output a ready-to-paste prompt:
> Use `/aligned:business-write-plan` to write an execution plan based on the design document at `docs/plans/YYYY-MM-DD-<topic>-design.md`.

**6. `critic-registry.md` pointer file**

Add `skills/business-brainstorming/critic-registry.md` with the same 1-line pointer: "Critic selection uses `advisors/registry.md`. See that file for per-advisor domain metadata, selection guidelines, and diversity rules."

### Skipped Features
- Lessons-learned check (decided during brainstorming session — not applicable to business workflow)
- Mockup generation (UI-specific)
- Worktree creation (code-specific)

### Critique Checklist Update (`design-critique-checklist.md`)
- Add "applicability assessment" directive adapted for business context: "After reading the design document, quickly assess which of the 8 criteria below are relevant to its scope. If a criterion clearly doesn't apply (e.g., 'Missing stakeholders' when the design is a solo deliverable with no external dependencies; 'Feasibility and constraints' when the design is a pure analysis with no resource requirements), mark it **N/A** with a one-line reason in the Checklist Results table and skip verification for that criterion."
- Keep all 8 existing domain-specific criteria unchanged

---

## Skill 2: business-write-plan

### Preserved Content
- Plan file location convention (`YYYY-MM-DD-<topic>-plan.md`)
- Task types catalog (Document sections, Research, Analysis, Action items, Review gates)
- Quality checks table (Audience clarity, Evidence required, So what test, Scope discipline, Review points)

### Added Features

**1. Autonomous execution mode**

Add a pre-approved actions section at the top:
```
This skill runs to completion without pausing for review between sections.

Pre-approved actions:
- Read any file in the project
- Search the codebase for context
- Write plan sections to the plan file
- Launch critique sub-agents
- Commit the plan to git
```

**2. Research/exploration phase before writing**

Before writing the plan, gather context:
1. Read the source design document (if one exists)
2. Check for prior plans on the same topic in `docs/plans/`
3. Review any relevant business documents in the project
4. Identify stakeholders, dependencies, and constraints mentioned in project docs

**3. Verification gate**

Before including any claim in the plan:
- Confirm referenced data points against the design doc
- Check that cited deliverables, documents, or artifacts actually exist
- Verify stakeholder names and roles are accurate per project docs

**4. Decision Log (mandatory)**

Every non-obvious choice in the plan gets logged. Format:

Summary table in the plan header:
| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|

Appendix with full alternatives considered for each decision.

**5. Dual-critic architecture (registry-based)**

Replace the single generic reviewer with two critics selected from `advisors/registry.md`, matching business-brainstorming's registry-based approach. Recommended defaults (can be overridden by dynamic selection if the plan's domain warrants different critics):

- **Richard Rumelt (Strategic Alignment lens)** — Evaluates whether the plan identifies the crux, whether priorities are correctly ordered, whether the guiding policy is coherent, and whether tasks form a coordinated set of actions. Owns checklist criteria 1 (Task sizing — are tasks focused on the crux?), 2 (Audience clarity), 5 (Scope discipline), and 9 (Decision quality). Does NOT fact-check individual claims.
- **The PM (Operability lens)** — Evaluates whether tasks are correctly sized, acceptance criteria are measurable, the plan is executable by someone with zero context, and review gates are at the right points. Owns checklist criteria 3 (Evidence requirements), 4 ("So what?" test), 6 (Review gates), 7 (Acceptance criteria), and 8 (Dependencies and ordering). The PM also owns all fact-checking: verifying that referenced documents exist, claims are accurate, and deliverables are correctly described.

**Division of labor:** The PM owns exhaustive fact-checking. Rumelt does NOT duplicate this — he reads the plan for strategic coherence, not line-by-line accuracy. This prevents overlapping verification work (matching writing-plans' Architect/Verifier division).

Both launched as parallel sub-agents (`subagent_type=general-purpose`, `model=sonnet`).

**6. Round 2 model downgrade**

Round 2 (conditional, only if Round 1 found medium/high issues) uses `model=haiku` and is scoped only to changes made since Round 1. This matches the writing-plans efficiency optimization.

**7. Handoff prompt**

After committing the plan, output:
> Use `/aligned:business-executing` to execute the plan at `docs/plans/YYYY-MM-DD-<topic>-plan.md`.

### Skipped Features
- Cross-repo guard (code-specific)
- TDD integration (code-specific)
- Error path tests for mocks (code-specific)
- Eval scenarios (code-specific)
- Worktree-aware plan reading (code-specific)
- Standalone scripts / dotenv policy (code-specific)
- Manual steps policy (code-specific — business plans inherently involve manual human steps)

### Critique Checklist Update (`plan-critique-checklist.md`)
- Add "applicability assessment" directive adapted for business context: "After reading the plan, quickly assess which of the 8 criteria below are relevant to its scope. If a criterion clearly doesn't apply (e.g., 'Dependencies and ordering' when the plan has only 1-2 tasks; 'Review gates' when the plan is a solo deliverable with no stakeholder checkpoints), mark it **N/A** with a one-line reason in the Checklist Results table and skip verification for that criterion."
- Add "Never suggest merging, combining, or consolidating tasks — granular tasks are intentional. Document ordering dependencies instead." directive
- Add a 9th criterion: "Decision quality" — evaluate whether the Decision Log captures all non-obvious choices with sufficient rationale and alternatives
- Keep all 8 existing domain-specific criteria unchanged

---

## Skill 3: business-diagnosis

### Preserved Content
- "NO SOLUTIONS WITHOUT ROOT CAUSE INVESTIGATION FIRST" iron law
- Business investigation layers (Strategy > Messaging > Deliverable > Execution)
- "Check What Changed" with business focus (new information, shifted context, environmental changes)
- "Question the Strategy" escalation at 3+ failures
- Red flags list (10 bullets)
- Quick reference table (will be expanded)

### Added Features

**1. Severity levels**

Add two modes matching systematic-debugging:
- **Low (default):** Single investigator. Standard 4-phase process.
- **High:** Multi-agent fan-out (Phase 0) before standard phases. Triggered when:
  - Cross-functional issues affecting multiple teams/stakeholders
  - Multi-stakeholder impact with conflicting perspectives
  - Recurring problems that have resisted 2+ prior fix attempts
  - Time-critical situations (deadline pressure, escalation risk)
  - User explicitly requests high severity

**2. Phase 0: Multi-Agent Investigation (high severity only)**

Five sub-agents launched in parallel, adapted for business context:

| Agent | Role |
|-------|------|
| **Backward Tracer** | Traces the problem backward from symptoms to origin. Asks: when did this start? What changed? What was working before? |
| **Stakeholder Mapper** | Identifies all affected parties, their perspectives, incentives, and potential blind spots. Maps the human system around the problem. |
| **Data Analyst** | Gathers and analyzes relevant metrics, timelines, and quantitative evidence. Looks for correlations, trends, and anomalies. |
| **Pattern Matcher** | Searches for similar past problems in project history and how they were resolved. Checks if this is a recurring pattern. |
| **JudgeAgent** | Synthesizes all findings, resolves contradictions between agents, and produces a unified hypothesis ranked by evidence strength. |

JudgeAgent output feeds into Phase 1 as the starting point for investigation.

**3. "When Process Reveals No Root Cause" section**

New section for handling situations where the standard process doesn't surface a clear root cause:
- **External/environmental factors:** Market shifts, competitor actions, regulatory changes that are outside the team's control
- **Timing issues:** The problem is intermittent or context-dependent — it only manifests under specific conditions
- **Third-party dependencies:** The root cause lies in a partner, vendor, or platform the team doesn't control
- **Action:** Document what was investigated, what was ruled out, and what external factors are suspected. Recommend monitoring rather than fixing.

**4. User Signals section**

"Your human partner's signals you're doing it wrong" — adapted for business context:
- They keep saying "but why?" after your explanations → you haven't gone deep enough
- They're getting frustrated because you keep proposing solutions → you skipped root cause investigation
- They say "we tried that already" → you didn't check history
- They redirect you to talk to someone else → you're missing a stakeholder perspective
- They ask you to "just fix it" → the process feels too slow, but don't skip steps — explain what you're doing and why

**5. Condensed rationalizations table**

Trim from 6 rows to top 4, matching the systematic-debugging trimming. Remove these 2 rows:
- "Just try this first, then investigate" — overlaps with "I see the problem, let me fix it" (both are about jumping to solutions)
- "Multiple changes at once saves effort" — less common in business contexts where changes are naturally sequential

Keep: "Issue is obvious", "Urgent, no time", "I see the problem", "One more attempt".

**6. Quick reference table update**

Expand from 4 phases to 5 (including Phase 0 for high severity), matching systematic-debugging's structure.

### Skipped Features
- Failing test case creation (code-specific)
- Kanban/bug board entry (code-specific)
- Architecture docs consultation (code-specific)
- Bash instrumentation examples (code-specific)
- Supporting technique files (root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md are all code-specific with no direct business equivalents)
- Lessons-learned gate (decided during brainstorming session — not applicable to business workflow)

---

## Skill 4: business-executing

### Preserved Content
- Task types catalog with per-type guidance (Document sections, Action items, Research/analysis)
- Writing quality standard reference (`elements-of-style:writing-clearly-and-concisely`)
- `/aligned:business-diagnosis` escalation when stuck

### Added Features

**1. Autonomous mode**

Add pre-approved actions section:
```
This skill runs to completion without pausing for review between batches.

Pre-approved actions:
- Read any file in the project
- Search for context in project files
- Write deliverable content
- Run verification checks
```

**2. Batch size increase**

Default from 3 to 5 tasks per batch, matching executing-plans.

**3. Plan archival step**

After all tasks complete, move the plan file (and associated design doc) to a `completed/` subfolder within `docs/plans/`. This keeps the active plans directory clean.

**4. Issue discovery protocol**

When unexpected business issues surface during execution (scope gaps not covered by the plan, stakeholder conflicts, assumption failures):
- Do NOT fix inline — stay focused on the current plan
- Raise the issue immediately in the conversation thread so the user is aware
- If the issue is a genuine blocker (e.g., a dependency that prevents the current task from completing), route to the existing "When to Stop and Ask" section — don't try to push through
- Collect all raised issues in the structured completion summary for user triage

**5. Structured completion handoff**

Replace the informal "Anything to adjust?" with a structured summary:

```
## Execution Complete

### Deliverables Produced
- [list each deliverable with acceptance criteria status]

### Discovered Issues
- [list any issues surfaced during execution]

### Suggested Next Steps
- [based on the deliverables and any issues]
```

### Skipped Features
- Branch verification (code-specific)
- Worktree-aware plan reading (code-specific)
- LLM surface check / eval scenarios (code-specific)
- Dev server command (code-specific)
- Ralph Wiggum autonomous loop (code-specific batch execution system)
- Kanban-based bug discovery protocol (code-specific — replaced with lightweight in-thread issue raising)

---

## Execution Order

1. **business-brainstorming** — Most complex, sets the pattern for critic architecture upgrades
2. **business-write-plan** — Biggest gap, benefits from brainstorming being done first (handoff coherence)
3. **business-diagnosis** — Independent from the pipeline but benefits from established patterns
4. **business-executing** — Simplest changes, benefits from write-plan being done first (handoff coherence)

## Deletion Audit

Before adding features, audit each business skill for content that can be trimmed:

- **business-brainstorming (149 lines):** Phase content is lean and purpose-built. No obvious cuts beyond what the rationalizations trim achieves for business-diagnosis. The existing critique prompt section will be restructured (not grown) when adding the two-phase fact-check format.
- **business-write-plan (146 lines):** Already the most under-specified skill — needs growth, not trimming.
- **business-diagnosis (223 lines):** Rationalizations table trimmed from 6→4 rows (already planned). The "Common root cause patterns in business" section (lines 72-83) is useful as investigation guidance, not a fixed list — keep it.
- **business-executing (95 lines):** Already the shortest skill. No cuts identified.

Net assessment: The business skills are lean enough that a deletion pass yields only the rationalizations trim already planned. The additions are warranted by the feature gaps documented above.

## Verification Strategy

These are prompt engineering changes to skill files. Verification approach per skill:

1. **Invoke the skill** in a test conversation with a representative business scenario
2. **Verify new features appear:**
   - business-brainstorming: fact-check phase in critic output, escalation protocol triggers, MANDATORY warning in skill text
   - business-write-plan: autonomous mode runs without pausing, two critics launch in parallel with correct model, Decision Log section appears in output, Round 2 uses haiku
   - business-diagnosis: severity prompt appears, high-severity triggers Phase 0 with 5 agents, "When Process Reveals No Root Cause" section present
   - business-executing: autonomous mode, batch size is 5, archival step runs, issues raised in thread not logged to Kanban
3. **Verify preserved content intact:** 4-phase gates, obstacle taxonomy, task types catalog still present and functional

## Decision Log

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Standalone fact-check file | Dropped | Software counterpart doesn't produce one. Adds file management overhead without clear benefit. Fact-check stays in critic output. |
| 2 | business-write-plan critic selection | Registry-based (Rumelt + The PM) | Consistency with business-brainstorming's registry approach. Avoids inventing new personas that need prompt engineering from scratch. |
| 3 | Round 1 model for business-write-plan | `model=sonnet` | Consistency with writing-plans counterpart. No evidence business plans need stronger models than software plans. |
| 4 | Rationalizations rows to cut | "Just try this first" + "Multiple changes at once" | Matches systematic-debugging's trimming. "Just try this first" overlaps with "I see the problem"; "Multiple changes" is less common in business. |
| 5 | Kanban for business skills | Not used | Business issues get raised in conversation thread. Formal Kanban logging is overkill for business workflow — no git-tracked issue board needed. |
| 6 | Phase 0 agent adaptations | Stakeholder Mapper + Data Analyst replace Forward Tracer + Data Flow Analyst | Business investigation needs human-system mapping and quantitative evidence analysis, not code-level forward/data-flow tracing. |
| 7 | Lessons-learned integration | Skipped for all business skills | Decided during brainstorming session. Business workflow doesn't maintain a `docs/lessons-learned/` directory. |

## Out of Scope

- Creating business equivalents of supporting technique files (root-cause-tracing.md, etc.)
- Changes to the advisor registry or advisor prompts
- Changes to the software counterpart skills
- Version bump in plugin.json (handled separately after all changes land)
