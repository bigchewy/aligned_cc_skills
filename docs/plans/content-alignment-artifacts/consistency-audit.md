# Cross-Surface Consistency Audit

**Date:** 2026-04-03
**Surfaces audited:** README, Consulting Pitch, Onboarding (Kickstart), Blog Post Draft

---

## Principle 1: Mechanism Before Metaphor

*README and docs: mechanism leads, metaphor follows. Content/blog: metaphor as hook, mechanism as payoff.*

| Surface | Result | Notes |
|---------|--------|-------|
| README | PASS | Hero leads with "62 expert advisors with real methodologies." "Virtual board of advisors" appears only in the last line of "How It Works" section, after evidence. |
| Consulting Pitch | PASS | Opens with the demonstration (mechanism), not a category claim. "Virtual board of advisors" does not appear — the document describes what the system does. |
| Onboarding (Kickstart) | PASS | "What to Try First" leads with concrete actions ("Try `/aligned:use-advisor april-dunford`"), not category claims. |
| Blog Post | PASS | Opens with the scenario hook (metaphor: "April Dunford at 2 AM"). Mechanism pays off in Section 2 (the actual exercise walkthrough). Exception correctly applied per design doc. |

**Verdict: PASS across all surfaces.**

---

## Principle 2: Outcome-First, Implementation-Second

*Lead with what it does for the reader, not how it's built.*

| Surface | Result | Notes |
|---------|--------|-------|
| README | PASS | Hero: "Leaders of growing companies get world-class strategic thinking." Scenarios show outcomes. "How It Works" mechanism section comes after outcomes. |
| Consulting Pitch | PASS | Section structure: demonstration → gap → what the engagement delivers → the outcome → proof. Outcome framing throughout. |
| Onboarding (Kickstart) | PASS | "Meet an advisor" and "Run a brainstorm" are outcome actions. Developer path ("Want to go deeper?") comes after. |
| Blog Post | PASS | Opens with the reader's problem (positioning challenge at night). System description is brief (one paragraph) before showing the exercise outcome. |

**Verdict: PASS across all surfaces.**

---

## Principle 3: Dual-Level Architecture

*Top layer for semi-technical leader, deeper layer for developer.*

| Surface | Result | Notes |
|---------|--------|-------|
| README | PASS | Top half (sections 1-4): outcome-focused for leaders. Bottom half (Get Started + Reference): developer-focused with installation, skill tables, agents, hooks. |
| Consulting Pitch | PASS | Outcome for the leader (sections 1-2-4), mechanism for technical evaluator (sections 3-5). "Proof" section explicitly points to inspectable code. |
| Onboarding (Kickstart) | PASS | Leader path: "Try an advisor, see what happens." Developer path: "Read `skills/brainstorming/SKILL.md` to see how mode detection works." Both explicitly surfaced. |
| Blog Post | PASS | Hook for leader (positioning exercise scenario). Depth for practitioner (actual process walkthrough with phases and gates). |

**Verdict: PASS across all surfaces.**

---

## Principle 4: Honest Framing of Context Layering

*Use "incorporates" / "uses" / "operates with," not "learns" / "knows." Don't imply automatic or adaptive behavior.*

| Surface | Result | Notes |
|---------|--------|-------|
| README | PASS | "advisors incorporate your company's institutional knowledge," "advisors operate with your company's specific context," "the advisor incorporates that context." No "learns" or "knows" language referring to the system. |
| Consulting Pitch | PASS | Uses "doesn't know" to describe the GAP (what the system doesn't have without company context) — this is honest framing, not a violation. "The advisors incorporate that knowledge." "The team learns" refers to human learning. |
| Onboarding (Kickstart) | PASS | "The advisors incorporate your company context." No "learns" / "knows" about the system. |
| Blog Post | PASS | No "learns" / "knows" referring to the system. Uses "know" only for the reader ("You know the positioning is off"). |

**Verdict: PASS across all surfaces.**

---

## Principle 5: The Repo Is the Proof

*Every claim backed by inspectable, working software.*

| Surface | Result | Notes |
|---------|--------|-------|
| README | PASS | "62 advisor personas" — verified: 62 files in `advisors/prompts/`. "135 structured frameworks" — verified: 135 directories in `frameworks/`. "30 skills" — verified: 30 directories excluding `_shared`. Scenario descriptions verified against actual skill code (Task 1). |
| Consulting Pitch | PASS | Section 5 explicitly states: "It's open-source — inspect the advisor prompts, read the framework definitions, trace the quality gates, run the skills." All claims map to repo contents. |
| Onboarding (Kickstart) | PASS | Directs to specific skills (`/aligned:use-advisor april-dunford`, `/aligned:brainstorming`) and code files (`skills/brainstorming/SKILL.md`, `advisors/registry.md`). All paths verified to exist. |
| Blog Post | PASS | References `docs/plugin-positioning.md` (verified to exist) as real exercise output. Advisory panel quotes are from that document. Links to GitHub repo. States "Every advisor prompt, every framework, every quality gate is inspectable in the repo." |

**Verdict: PASS across all surfaces.**

---

## Summary

| # | Principle | README | Consulting Pitch | Onboarding | Blog Post |
|---|-----------|--------|-----------------|------------|-----------|
| 1 | Mechanism before metaphor | PASS | PASS | PASS | PASS (exception applied) |
| 2 | Outcome-first | PASS | PASS | PASS | PASS |
| 3 | Dual-level architecture | PASS | PASS | PASS | PASS |
| 4 | Honest framing | PASS | PASS | PASS | PASS |
| 5 | Repo is the proof | PASS | PASS | PASS | PASS |

**All 5 principles pass across all 4 surfaces. No fixes needed.**

---

## Pending Items (not principle violations)

1. **Newsletter links:** Currently HTML comment placeholders in README, kickstart, and blog post. Blocked on Buttondown username from user. Not a principle violation — the links exist as placeholders and will be activated in Task 10.
