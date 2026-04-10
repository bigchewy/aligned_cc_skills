**Date:** 2026-04-09
**Status:** Draft
**Mockups:** docs/mockups/skill-auto-router.html

# Skill Auto-Router Design

## Goal

When a user types a natural-language request into Claude Code with the Aligned plugin installed, the plugin automatically detects which skill or framework to invoke — or asks a short clarifying question if ambiguous — so the user never needs to know skill names, slash commands, or the plugin's internal structure.

**Primary target user:** Technical CEO of a 10-50 person company. Uses Claude Code because it's the most powerful AI tool available, but is uncomfortable in a terminal and will not memorize slash commands. Typical tasks: competitive analysis, pricing strategy, team performance diagnosis, product positioning, go-to-market planning. Validated by direct observation — this is the plugin creator's primary user profile.

**Secondary personas (build for later):** Product managers, heads of hardware engineering, systems-oriented marketers. These share the "non-developer in a terminal" constraint but have different task distributions. Build for the primary persona first, expand once the router proves out.

**North star:** Install the plugin, and Claude Code is just better. No training required.

**Success criteria:**
- **Match precision ≥ 90%** — when the router fires, it picks the right framework or skill at least 9 out of 10 times. Measured against a test corpus of 50+ real user prompts with human-labeled correct routes.
- **False positive rate ≤ 5%** — the router intervenes on prompts that should have passed through no more than 1 in 20 times.
- **User override rate ≤ 15%** — users say "skip" or redirect fewer than 15% of the time the router fires. Higher override rates indicate poor matching.
- **Test corpus:** 50 prompts minimum, sourced from actual user sessions and the plugin creator's own usage. Each labeled with the correct route (specific framework, specific skill, or pass-through).

## Problems

1. **No interception layer** — nothing sits between the user's prompt and Claude's default behavior to route to skills. Claude Code's plugin architecture is passive: skills declare what they do, and Claude decides whether to use them. Claude prioritizes task completion over tool discovery and defaults to just answering.

2. **Routing accuracy** — keyword/regex approaches have limited accuracy ceilings (exact benchmarks vary by domain). Claude itself only activates skills roughly half the time with hints (per Scott Spence's research). Wrong routing erodes trust faster than no routing.

3. **Precision constraint** — false positives are worse than false negatives for this audience. The router needs high confidence before intervening, which narrows the window of what it can catch.

4. **Can't rely on user behavior** — the solution must work with zero training. Users won't learn conventions or remember phrasing patterns.

## Root Causes

1. **Claude's skill activation model is passive (opt-in by the model) rather than active (opt-in by infrastructure).** Skills are discovered by Claude scanning descriptions, not by an interception layer that matches intent to skills.

2. **Skills are organized by methodology, not by user intent.** Brainstorming, RCA, advisor, framework are implementation details. Users think in problems, not processes. "I need to figure something out" could map to four different skills. Even the plugin creator picks the wrong skill sometimes.

3. **Framework catalog is narrow but fixable.** An informal audit of 10 common business tasks found matching frameworks for 5-6 of them — the catalog is heavy on positioning/marketing, startup methodology, psychology/coaching. General business categories (finance, HR, ops, governance, planning) have near-zero coverage. This is a content gap, not a structural limitation. Coverage improvement requires defining a business task taxonomy for the primary persona and building frameworks against it (see Deliverables).

4. **The machinery should be invisible until it matters.** Users should never navigate the plugin's internal architecture. But when a framework is selected, it should be surfaced — so the user can redirect if it's wrong. Hide the plumbing, show the choice.

## Solution: Problem-First Router with Framework Cascade

### Architecture

A `UserPromptSubmit` hook intercepts every user message and runs a lightweight, rule-based classification. No external API calls at runtime.

### Routing Cascade

**Step 0 — Skill invocation bypass**
If the prompt contains an explicit skill invocation (`/aligned:...` or clear intent to use a specific skill like "run root cause analysis"), pass through without routing. The user already knows what they want.

**Step 1 — Framework match (highest confidence)**
Check the user's prompt against a precomputed index of framework metadata (names, aliases, trigger phrases, intent phrases). Three outcomes:

- **Single high-confidence match:** Present the framework and proceed immediately. "This looks like a competitive analysis problem. I'll walk you through Porter's Five Forces to structure your thinking. Just say 'skip' if you'd rather go freeform."
- **Multiple plausible matches (2-3):** Present options with the recommended one first. "A few frameworks could help here: 1) Positioning Canvas — clarifies differentiation, 2) Porter's Five Forces — maps competitive dynamics, 3) Value Metric — examines pricing alignment. Which resonates, or would you rather just talk it through?"
- **No match:** Proceed to Step 2.

**Step 2 — Skill classification (medium confidence)**
Keyword/phrase pattern matching against four fallback buckets:

| Intent | Skill | Signal patterns |
|--------|-------|-----------------|
| Diagnose/fix something | root-cause-analysis | "why is," "what's causing," "keeps happening," "not working," "declining" |
| Test content against audience | persona-panel | "test this with," "how would buyers," "audience reaction," "persona" |
| Start a new project | kickstart | "new project," "start a project," "scaffold," "from scratch" |
| Build/create something | brainstorming | "figure out," "think through," "strategy for," "how should I," "help me plan" |

**Confidence requirements:** Skill-level routing requires `min_signals: 2` — at least two signal phrases must match, or one signal phrase plus a domain context signal (e.g., the prompt is longer than 20 words and contains problem-domain vocabulary). Single keyword matches are not high confidence and must not trigger routing.

**Exclusion patterns:** Each skill defines negative signals that suppress routing even when positive signals match. For example, RCA excludes "why is the sky," "why is it called," and other common non-diagnostic phrasings. Brainstorming excludes "help me plan my vacation" and similar personal/non-strategic requests.

**Error recovery for skill routes:** When the router selects a skill (not a framework), the directive must include a one-line acknowledgment with opt-out, identical to the framework interaction pattern. Example: "This sounds like a diagnostic problem. I'll help you trace the root cause. Say 'skip' if you'd rather just discuss it."

**Step 3 — Below confidence threshold**
Prompt passes through untouched. Claude handles it natively. This is the correct default — routing should only fire with high confidence. When in doubt, do nothing.

### Routing Directive Format

The hook appends a directive to the prompt that Claude sees but the user doesn't.

**Single framework match:**
```
[ALIGNED-ROUTER] A framework matches this request. Present it to the user and proceed:
- Framework: "Porter's Five Forces" (advisor: michael-porter)
- Say: "This looks like a competitive analysis problem. I'll walk you through Porter's Five Forces to structure your thinking. Just say 'skip' if you'd rather go freeform."
- Then: Use Skill(aligned:use-framework) with framework "porters-five-forces"
```

**Multiple framework matches:**
```
[ALIGNED-ROUTER] Multiple frameworks may apply. Present options and let the user choose:
- Option 1: "Positioning Canvas" — clarifies differentiation (advisor: april-dunford)
- Option 2: "Porter's Five Forces" — maps competitive dynamics (advisor: michael-porter)
- Option 3: "Value Metric" — examines pricing alignment (advisor: madhavan-ramanujam)
- Fallback: "Or just talk it through freeform"
- Then: Use Skill(aligned:use-framework) with their choice, or Use Skill(aligned:brainstorming) for freeform
```

**Skill match (no framework):**
```
[ALIGNED-ROUTER] No framework match, but intent is clear.
- Intent: diagnose/fix
- Say: "This sounds like a diagnostic problem. I'll help you trace the root cause. Say 'skip' if you'd rather just discuss it."
- Then: Use Skill(aligned:root-cause-analysis)
```

### The Routing Index (`skill-router.json`)

A static JSON file that ships with the plugin. Structure:

```json
{
  "frameworks": [
    {
      "id": "porters-five-forces",
      "name": "Porter's Five Forces",
      "advisor": "michael-porter",
      "triggers": ["porter", "five forces", "competitive forces"],
      "intent_phrases": ["competitive landscape", "industry analysis", "competitive threats", "market competition"]
    }
  ],
  "skills": {
    "root-cause-analysis": {
      "signals": ["why is", "why are", "what's causing", "root cause", "keeps happening", "not working", "failing", "broken", "declining"],
      "exclude": ["why is the sky", "why is it called", "why is there"],
      "min_signals": 2
    },
    "persona-panel": {
      "signals": ["test this with", "how would buyers", "audience reaction", "customer feedback", "persona", "would users"],
      "exclude": [],
      "min_signals": 2
    },
    "kickstart": {
      "signals": ["new project", "start a project", "scaffold", "bootstrap", "from scratch", "set up a new"],
      "exclude": [],
      "min_signals": 2
    },
    "brainstorming": {
      "signals": ["figure out", "think through", "strategy for", "how should I", "help me plan", "design a", "what's the best way to"],
      "exclude": ["help me plan my", "figure out what to eat", "think through my schedule"],
      "min_signals": 2
    }
  }
}
```

### The Build Script

A script (`scripts/build-router-index.js`) that generates `skill-router.json`:

1. Walks framework directories, reads each framework's metadata and content
2. Calls an LLM to generate intent phrases and trigger terms from framework descriptions
3. Outputs the routing index
4. Run by the developer when frameworks change, not by end users

### User Experience Examples

**Example 1 — Framework match (single):**
User types: "I need to figure out how to position our product against cheaper competitors."
Router matches: Positioning Canvas (high confidence).
User sees: "This looks like a positioning problem. I'll walk you through the Positioning Canvas to clarify your differentiation. Just say 'skip' if you'd rather go freeform." → Proceeds into framework.

**Example 2 — Framework match (multiple):**
User types: "We're losing enterprise deals to a competitor who's undercutting us on price."
Router matches: Positioning Canvas, Porter's Five Forces, Value Metric.
User sees: Options presented, picks one, enters framework.

**Example 3 — No framework, skill match:**
User types: "Our onboarding process is a mess and new hires keep quitting in the first 90 days."
Router matches: No framework (HR gap). Intent: diagnose/fix → RCA.
User sees: "This sounds like a diagnostic problem. I'll help you trace the root cause. Say 'skip' if you'd rather just discuss it." → Proceeds into RCA.

**Example 4 — No match:**
User types: "Summarize this document for me."
Router matches: Nothing above threshold.
User sees: Claude handles it natively, no intervention.

**Example 5 — Explicit skill invocation:**
User types: "/aligned:brainstorming I want to redesign our pricing page."
Router detects: Explicit skill invocation → pass through.
User sees: Brainstorming skill activates normally.

## Deliverables

1. **Hook script** (`hooks/skill-router.sh` or `.js`) — the UserPromptSubmit hook that runs the matching logic
2. **Routing index** (`skill-router.json`) — precomputed framework and skill matching rules, including exclusion patterns
3. **Build script** (`scripts/build-router-index.js`) — generates the routing index from framework content using LLM-assisted intent phrase extraction
4. **Test corpus** — 50+ real user prompts, each labeled with the correct route (specific framework, specific skill, or pass-through)
5. **Telemetry logging** — log routing decisions (which route was selected, confidence level), user overrides ("skip" events), and fall-through prompts to a local file. No external services. This data drives threshold iteration and framework gap-fill.

**Separate initiative (not part of this project):**
- **Business task taxonomy** — define 15-20 common business task categories for the primary persona. Used to measure framework coverage and prioritize gap-fill.
- **Framework gap-fill** — new frameworks for categories identified by the taxonomy and telemetry. Triggered by router data showing which prompts fall through most often, not by upfront estimation.

## Sequencing

1. Build the hook + matching logic with the current framework catalog (proves the architecture)
2. Build the index generator script
3. Build test corpus from real user prompts; run against router; measure precision, false positive rate, and override rate
4. **Gate: proceed only if precision ≥ 80% on test corpus.** If below, diagnose whether the issue is signal quality, exclusion patterns, or threshold tuning before continuing.
5. Ship to users with telemetry enabled
6. **Gate: after 2 weeks of telemetry, assess.** If override rate > 15%, review telemetry logs and adjust. If fall-through rate reveals consistent gaps, initiate the framework gap-fill initiative.
7. Iterate on trigger phrases, exclusion patterns, and confidence thresholds based on telemetry data

## Prior Art

- **ClaudeFa.st Skill Activation Hook** — UserPromptSubmit hook with keyword/regex matching and skill-rules.json config. Validates the hook-based approach.
- **Scott Spence's research** — documented that Claude Code skills don't auto-activate; direct imperatives ("Use Skill(X)") work better than suggestions (~50% activation with hints).
- **semantic-router (aurelio-labs)** — embedding-based routing library. Potential future upgrade path if rule-based matching hits accuracy ceiling. Would require benchmarking against the test corpus to establish actual precision for this use case.
- **Windsurf Cascade** — session-context-aware routing using edit/command/clipboard signals. Most advanced but heaviest implementation.

## Decision Log

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Routing approach | Problem-first with framework cascade | Skill-first routing; enhanced CLAUDE.md instructions | Skills overlap from user perspective; CLAUDE.md only ~50% activation rate |
| Framework visibility | Surface framework choice to user with opt-out | Hide machinery entirely (Christensen); surface with no opt-out | Users need ability to redirect if wrong match (Krug: "make the default obviously right, and make correcting it effortless") |
| Runtime classification | Rule-based (no API calls) | LLM-based (Haiku); embedding-based (semantic-router) | No external dependencies; adequate accuracy for precision-first system |
| Build-time index generation | LLM-assisted | Manual curation; pure extraction | Frameworks have rich content; LLM generates better intent phrases than regex extraction |
| Default fallback | Pass-through (no intervention) | Brainstorming; ask clarifying question | Precision-first: when confidence is low, do nothing rather than route wrong. Brainstorming requires min_signals: 2 like all other skills. |

## Advisor Input

Four perspectives consulted during design:

- **Steve Krug (UX):** Framework-first is correct — frameworks are concrete nouns users recognize, skills are abstract implementation details. Surface the choice with one line, proceed without waiting. "Make the default obviously right, and make correcting it effortless."
- **Clayton Christensen (JTBD):** The job users hire the plugin for is "help me think through this problem better than I would alone." Route on the problem, not the catalog. Frameworks are inventory, not interface. (Revised: user chose to surface framework choice rather than hide entirely.)
- **Systems Architect:** 138 frameworks is technically easier to match than 4 overlapping skill buckets — frameworks have high-specificity anchor terms. Cascade architecture: cheap keyword matching first, expensive inference only on residual. A 4-way skill classification (RCA, persona-panel, kickstart, brainstorming) with pass-through default is simpler than routing against abstract skill categories.
- **Framework Catalog Analysis:** Current coverage ~50% of common business tasks. Deep in positioning/marketing, startup, psychology/coaching, medical. Gaps in finance, HR, ops, governance, planning. Fixable with targeted framework development for known user personas.
