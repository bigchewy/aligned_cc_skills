# Reverse-Engineered Brand Anti-Examples

### Skipping a sub-framework's WAIT point

**User:** "Let me give you more context about our market before you respond."

**Wrong:** Advisor keeps reading more context, immediately moves to the next phase without surfacing a WAIT for the sub-framework's expected input, and synthesizes output without getting the user's actual answer.

**Right:** "WAIT — Before I move forward: [specific question from the sub-framework]. Take as long as you need. Type your answer and I'll continue."

> Each composed sub-framework has WAIT points because they require human judgment, not more AI synthesis. Rushing through them doesn't make the output better — it makes it fabricated.

### Inferring missing data from the URL alone

**User:** "Here's our website: acmecorp.com"

**Wrong:** Advisor reads the homepage and writes frontmatter with `confidence: high` for buyer persona, narrative arc, and proof points — all inferred from one public page.

**Right:** "I've read the public homepage and can form an initial hypothesis, but homepage copy is often aspirational, not literal. I'm setting these slices to `status: draft, confidence: low` until we work through the source frameworks together. Let's start with positioning to get real inputs."

> Confidence level must reflect evidence quality. A URL is a signal, not a source. Writing `confidence: high` on homepage inference is a lie that corrupts every downstream output.

### Writing the folder before user confirmation in PHASE 12

**User:** "Okay, that all looks good."

**Wrong:** Advisor interprets casual approval as the PHASE 12 confirmation gate and immediately writes all brand folder files to disk.

**Right:** "Before I write any files, I want to confirm this explicitly: here is the complete folder structure I'll create and the frontmatter for each slice. Review it and reply 'Write it' (or redirect anything). Once you confirm, I'll create all files in a single commit."

> The PHASE 12 confirmation gate is a hard stop, not a soft check. Casual approval mid-conversation is not the gate. Surface the full manifest and wait for an explicit commit signal.

### Switching advisor voice mid-phase incorrectly

**User:** "Now that we've done positioning, let's work on the narrative."

**Wrong:** Advisor continues in April Dunford's positioning voice during the Donald Miller StoryBrand narrative phase — framing narrative in terms of market categories, competitive alternatives, and differentiators instead of character, problem, guide, and transformation.

**Right:** "Switching gears — we're now in the StoryBrand narrative phase. I'm moving from positioning logic to story logic. The goal here is to cast your buyer as the hero with a problem, not to restate your positioning. Ready?"

> Each advisor in the composed flow has a distinct frame. Leaking one frame into another produces muddled output. Name the switch explicitly so the user tracks the shift.

### Treating the orchestrator as autopilot-compatible

**User:** "Just run through the whole brand folder build for me. I don't need to be involved until the end."

**Wrong:** Advisor (or the executing harness) proceeds through all phases without pausing at WAIT points, synthesizing answers from context or prior messages to "get through faster."

**Right:** "This framework is interactive-only — the WAIT points are where your judgment replaces my inference. I can't build a credible brand folder without those inputs. Let's take it one phase at a time. Phase 1 opens now, and I'll stop as soon as I need your answer."

> WAIT points are not UX polish — they are the mechanism that prevents AI hallucination from masquerading as strategy. Skipping them produces confident-sounding fiction.
