# Scenario Verification Log

**Date:** 2026-04-03
**Method:** Code analysis of skill mechanics (brainstorming, generate-deck, use-advisor) to determine reliable vs. dynamic behavior. Single invocations would only capture one sample; code analysis reveals what the system deterministically does vs. what it might do on any given run.

---

## Scenario 1: Positioning Exercise at 11pm

**Design doc description:** "Invoke `/aligned:brainstorming`, describe your product. The system pulls in April Dunford's 5 Components framework. Steve Jobs pushes back on complexity. Seth Godin challenges whether it's remarkable. You get a multi-advisor critique panel with real methodology, not generic AI advice."

**Skill invocation:** `/aligned:brainstorming` with a positioning topic

### What reliably happens (deterministic)

1. **Mode detection:** The skill auto-detects "positioning" as a business topic (business mode signal words include "positioning, strategy, marketing"). This is reliable.
2. **Structured 4-phase process:** Goal → Problems → Root Causes → Solutions. The skill enforces this sequence with mandatory gates between phases. This is deterministic.
3. **Critique panel runs with real methodology:** After the design is written, a mandatory critique panel launches with dynamically selected critics. Each critic uses their full prompt file (real voice, real frameworks, real methodology). This is deterministic.
4. **Project scan runs in background:** A project scanner gathers context about the repo while the user answers goal questions. This is deterministic.

### What varies by invocation (dynamic)

1. **Specific critics selected:** The orchestration reads `advisors/registry.md` and selects 1-4 critics based on the design's content, following selection guidelines. For a positioning topic:
   - **April Dunford** — very likely (domains: positioning, messaging, competitive-analysis, differentiation, go-to-market). Best match for positioning work.
   - **Seth Godin** — possible (domains: marketing, permission-marketing, remarkable-products, tribes). No `not_for` exclusion. But the orchestration prefers "diversity of lens" and may pick a different marketing-adjacent critic.
   - **Steve Jobs** — unlikely for pure positioning (domains: product design, simplicity, UX, focus). His `best_for` is "designs with user-facing components where simplicity and focus matter." A positioning exercise without a UI component would likely trigger a different selection.
   - **More likely critics for positioning:** April Dunford + Rob Walling or Richard Rumelt (strategic clarity) or Andy Raskin (narrative).

2. **The 5 Components framework is NOT auto-invoked:** The brainstorming skill uses its own 4-phase structure, not April Dunford's 5 Components. If April Dunford is selected as a critic, she evaluates through her positioning lens during the critique panel — but the brainstorming phases themselves are the skill's own structure. The framework would appear in the critique evaluation, not as the primary process.

### Discrepancies

| Design doc claim | Reality | Adjustment needed |
|-----------------|---------|-------------------|
| "system pulls in April Dunford's 5 Components framework" | Brainstorming uses its own 4-phase process. Dunford's methodology appears in the critique panel if she's selected as a critic. | Rewrite to describe the actual mechanic: structured process + multi-advisor critique |
| "Steve Jobs pushes back on complexity" | Steve Jobs is unlikely to be selected for a pure positioning exercise; his domain is product design/UX | Remove Steve Jobs from this scenario or change the scenario to one where he'd be selected (product design) |
| "Seth Godin challenges whether it's remarkable" | Possible but not reliable; depends on dynamic selection | Describe what reliably happens: critics selected by domain relevance, not specific names |
| "multi-advisor critique panel with real methodology" | YES — this is the core mechanic and it's deterministic | Keep this claim as-is |

### Adjusted scenario description

**Positioning exercise at 11pm:** Invoke `/aligned:brainstorming` and describe your product. The system detects it's a strategy problem and walks you through structured goal clarification, obstacle diagnosis, root cause analysis, and solution design — with gates between each phase so nothing gets skipped. Then a critique panel of 2-4 advisors evaluates the design through their real methodologies. For a positioning exercise, expect April Dunford challenging your differentiation, Richard Rumelt cutting through strategic fluff, or Rob Walling asking whether you've validated willingness to pay. Each critic uses their actual frameworks, not generic AI feedback.

---

## Scenario 2: Sales Deck for Tomorrow's Meeting

**Design doc description:** "Invoke `/aligned:generate-deck` with your prospect context. The system structures it using April Dunford's positioning framework, applies your design principles, and runs it through a review panel before delivery."

**Skill invocation:** `/aligned:generate-deck` with prospect context

### What reliably happens (deterministic)

1. **April Dunford 8-step framework:** The skill explicitly follows the "April Dunford 8-step sales pitch narrative arc" as its structural backbone. This is hard-coded, not dynamic.
2. **Brand context loading:** The skill loads `brand/guidelines/messaging-framework.md` (market category and value props) and `brand/guidelines/visual-identity.md` (colors, fonts, spacing). Also loads positioning, competitive, proof-points, and terminology files if available.
3. **Three-reviewer panel runs in parallel:** Fixed reviewers, not dynamically selected:
   - Reviewer 1: Positioning Expert (April Dunford lens) — evaluates framework adherence and positioning quality
   - Reviewer 2: Behavioral Scientist (Shirin Oreizy lens) — evaluates decision architecture and narrative psychology
   - Reviewer 3: Buyer Personas (prospect-specific) — evaluates through each stakeholder's lens
4. **Quality gates checked before review:** 10-point quality gate including terminology compliance, proof-point accuracy, tone match, and stakeholder specificity.
5. **Rep triage of findings:** User can accept all, cherry-pick, or add context before final delivery.

### Discrepancies

| Design doc claim | Reality | Adjustment needed |
|-----------------|---------|-------------------|
| "applies your design principles" | Loads brand visual identity (colors, fonts, spacing) and messaging framework — not a "design principles" file | Change to "applies your brand identity and messaging framework" |
| "structures it using April Dunford's positioning framework" | YES — 8-step sales pitch narrative arc, hard-coded | Accurate, keep |
| "runs it through a review panel before delivery" | YES — 3 fixed reviewers in parallel | Accurate, keep. Can be more specific: "three expert reviewers" |

### Adjusted scenario description

**Sales deck for tomorrow's meeting:** Invoke `/aligned:generate-deck` with your prospect context. The system structures a 9-slide deck using April Dunford's 8-step sales pitch framework, personalized with your prospect's stakeholders, competitive context, and buying trigger. It applies your brand voice, messaging framework, and visual identity. Before delivery, three reviewers evaluate in parallel: a positioning expert checks framework adherence, a behavioral scientist checks cognitive load and decision architecture, and simulated buyer personas flag what resonates and what triggers skepticism. You triage the findings and get a final deck.

---

## Scenario 3: New Hire's First Strategic Decision

**Design doc description:** "They invoke `/aligned:use-advisor` and get Rob Walling's actual decision frameworks, calibrated to your company's context. The quality of thinking doesn't depend on who's in the room."

**Skill invocation:** `/aligned:use-advisor rob-walling`

### What reliably happens (deterministic)

1. **Fuzzy name matching:** The skill matches "rob-walling" against slug and display name. Single match → adopted immediately.
2. **Full persona adoption:** The skill reads Rob Walling's complete prompt file (voice, tone patterns, signature questions, 5 core frameworks, blind spots, failure modes) and adopts the persona for the entire conversation.
3. **Real frameworks available:** Rob Walling's prompt includes: Stair Step Method, 5 Stages of Product-Market Fit (with specific MRR/churn benchmarks), Market-First Approach, SaaS Cheat Codes, and Classic Traps. These are the actual frameworks he uses.
4. **Greeting in advisor voice:** Opens with 2-3 sentences in Rob's voice, references available frameworks, invites freeform conversation.

### What varies / requires clarification

1. **"Calibrated to your company's context":** The advisor persona operates within the Claude session, which has access to project files (CLAUDE.md, docs/, etc.). If the project contains company context (competitors, personas, strategy docs), the advisor can reference it. But the use-advisor skill itself does NOT automatically load company-specific context files. Company context depends on what's in the project directory and whether the user references it.
2. **Company-aware vs. company-calibrated:** The advisor uses company context when it's available in the session, but doesn't proactively seek it out. More accurate framing: "operates with your company's context when you've configured it" rather than "calibrated to."

### Discrepancies

| Design doc claim | Reality | Adjustment needed |
|-----------------|---------|-------------------|
| "Rob Walling's actual decision frameworks" | YES — 5 real frameworks with specific benchmarks encoded | Accurate, keep |
| "calibrated to your company's context" | Advisor uses project context when available, but doesn't proactively load company files. Context depends on project setup. | Change to "uses your company's context when you've configured it" (per principle #4) |
| "quality of thinking doesn't depend on who's in the room" | Accurate — the same frameworks and methodology are available regardless of who invokes it | Keep |

### Adjusted scenario description

**New hire's first strategic decision:** They invoke `/aligned:use-advisor rob-walling` and get Rob Walling's actual decision frameworks — the Stair Step Method, 5 Stages of Product-Market Fit with specific MRR and churn benchmarks, Market-First evaluation. The advisor speaks in his real voice, pushes back on building without evidence, and asks his signature questions. When your project includes company context — competitors, personas, strategy docs — the advisor incorporates that context into the conversation. The quality of strategic thinking doesn't depend on who's in the room.

---

## Summary

| Mechanic | Reliable? | Notes |
|----------|-----------|-------|
| Mode auto-detection (brainstorming) | Yes | Business topics reliably route to business mode |
| Structured phase process with gates | Yes | 4-phase process is mandatory |
| Critique panel runs | Yes | Mandatory after every design |
| Specific advisor names in critique panel | No | Dynamic selection based on topic; specific critics vary |
| April Dunford 8-step framework (generate-deck) | Yes | Hard-coded structure |
| Three fixed reviewers (generate-deck) | Yes | Not dynamically selected |
| Full persona adoption (use-advisor) | Yes | Reads and adopts complete prompt file |
| Company context in advisor sessions | Conditional | Available when project includes context files |

**Core finding:** The reliable mechanic across all three scenarios is: real methodology, enforced process, expert evaluation. The specific advisor names that appear in the critique panel are dynamic. README scenarios should describe what reliably happens (structured process + expert critique with real methodology) and use advisor names as illustrative examples, not guaranteed appearances.

**Pre-ship note:** Task 12 calls for re-running these scenarios against the final README copy. At that point, actual skill invocations should confirm the adjusted descriptions match real output.
