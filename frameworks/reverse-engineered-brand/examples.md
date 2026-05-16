# Reverse-Engineered Brand Examples

## PHASE 0: Intake

### User gives clear URL and supplementary folder

**User:** "The URL is acmecorp.com. I've also got a folder at ~/Documents/acme-brand/ — there are three customer interview transcripts and our last sales deck in there."

**Advisor:** "Perfect. I'll read the homepage and the supplementary content in parallel. Customer interviews and a sales deck are high-signal inputs — we should be able to reach medium confidence on several slices. Give me a moment to load and summarize what I'm seeing before we talk through it."

> Confirms the inputs, signals what confidence gain the supplementary content enables, and moves immediately to PHASE 1.

### User gives a vague description without a URL

**User:** "We're a software company that helps marketing teams do better content. We've been around about four years."

**Advisor:** "I need a URL before we can start. I'm going to read your public surface — your homepage or About page — as the baseline hypothesis for everything we build. Without it, I'm guessing, and guesses don't become a brand folder you can trust.

What's the company's homepage URL?"

> Holds the WAIT. Does not attempt to proceed on a verbal description alone.

### User pushes back on needing a URL

**User:** "The website is really out of date — it doesn't represent where we are at all. Can we just skip it?"

**Advisor:** "I still need it. Here's why: the public surface is the market's current perception — not what you want it to be, but what it actually is right now. That gap between 'where the website is' and 'where you are' is exactly what we need to map. It becomes evidence of positioning drift, and it tells us which slices of the brand folder need the most urgent deepening.

The outdated website is data, not a problem to skip. Give me the URL."

> Reframes the outdated-website objection as signal rather than noise.

---

## PHASE 1: Public surface review

### Advisor's read matches user's intent

**Advisor:** "Here's what I'm seeing on the surface:

Acme Corp appears to sell a content analytics platform targeted at B2B marketing teams, specifically those managing high-volume content programs. The homepage leads with 'know what's working before you publish' — a differentiated claim around predictive insights rather than post-hoc reporting. The primary audience looks like demand-gen and content ops roles at mid-market SaaS companies.

What's notably absent: no mention of integrations, no pricing signal, very little social proof above the fold.

Does this match what you know about the company? What am I missing or misreading?"

**User:** "That's pretty accurate. The only thing I'd correct is the audience — it's actually editorial teams at media companies, not marketing teams at SaaS."

> User corrects an inferred audience claim. The advisor incorporates this before seeding the sub-frameworks.

**Advisor:** "Noted — editorial teams at media companies, not demand-gen at SaaS. That changes the competitive alternatives and the JTBD frame substantially. Let me carry that forward. Everything downstream will be built from that audience, not what the website implied."

> Confirms the correction explicitly so the user knows it's been absorbed.

### Advisor catches a positioning gap the user missed

**Advisor:** "One thing worth flagging: the homepage makes three separate value claims — predictive insights, workflow automation, and team collaboration — but none of them is emphasized over the others. It reads like a feature list, not a position. If all three are equal, competitors can claim any one of them and it won't feel like a theft.

We'll need to pick one when we get to PHASE 2. Does the team have a sense of which of those three drives most purchase decisions?"

**User:** "Honestly, I think we lead with prediction — that's the thing nobody else does."

> User surfaces a prioritization insight in response to a framing observation.

**Advisor:** "Good. Predictive insights is our tentative leading differentiator. We'll test that assumption when we run the 5 Components positioning framework."

---

## PHASE 6: Messaging-distillation handoff

### Advisor surfaces tagline draft and asks for calibration

**Advisor:** "I'm about to hand off to the messaging-distillation framework. Before I do, here's what I'm carrying in from positioning and narrative:

- **Category:** Predictive content intelligence
- **Leading differentiator:** Know what will perform before you commit budget
- **Target:** Editorial directors and content ops leads at mid-market media companies
- **Tagline candidates from positioning synthesis:**
  - 'Stop guessing. Start knowing.'
  - 'Content confidence, before publish.'
  - 'Predict. Publish. Repeat.'

These are rough — messaging-distillation will refine them. But I want your reaction before we go in. Do any of these land, and are there phrases from your customers or sales calls that we should seed the framework with?"

**User:** "The first one is closest. Customers literally say 'we were guessing' when they describe life before us. Seed with that."

> User confirms a tagline direction and provides a customer language cue to seed the sub-framework.

**Advisor:** "'We were guessing' is a strong voice-of-customer signal. I'll carry that phrase and the 'stop guessing' frame into messaging-distillation."

### Advisor catches a value-prop conflict before handoff

**Advisor:** "I'm seeing a tension across our outputs. PHASE 2 positioning says the target is editorial directors. But PHASE 4's JTBD surfaced a second audience — content ops managers — with a different job-to-be-done: reduce publishing cycle time, not improve performance prediction. These two audiences want different things.

Before we go into messaging-distillation, I want a decision: do we message to both audiences with separate value props, or do we pick one primary and treat the other as secondary?

This affects how many messaging tracks messaging-distillation produces. One primary is simpler. Two parallel tracks is more work but may be the honest answer if both roles are genuinely on the buying committee."

**User:** "Two tracks. Both are in the room on every deal."

> User confirms the multi-audience structure. Advisor carries this into the sub-framework.

---

## PHASE 11: Folder write

### Advisor previews manifest and asks for confirmation

**Advisor:** "Here's everything I'm about to write:

| File | Status | Confidence |
|------|--------|------------|
| brand/positioning.md | draft | medium |
| brand/narrative.md | draft | medium |
| brand/jobs-to-be-done.md | draft | low |
| brand/personas/editorial-director.md | draft | medium |
| brand/personas/content-ops-manager.md | draft | low |
| brand/messaging.md | draft | medium |
| brand/competitive.md | draft | low |
| brand/proof-points.md | draft | low |
| brand/brand-voice.md | draft | medium |
| brand/design-principles.md | missing | — |
| brand/version.yaml | — | — |
| brand/CLAUDE.md | — | — |
| brand/contracts.yaml | — | — |

JTBD and competitive are low because we had no customer interview data or deal history to cross-reference. Content-ops persona is low because we only have one inferred data point.

**Confirm, and I'll write the folder atomically.**"

**User:** "One change: personas/editorial-director.md should be medium, but content-ops-manager.md should stay low. We have three editorial director interviews from PHASE 1's supplementary folder — that warrants medium. Ops is genuinely inferred."

> User exercises judgment on confidence levels based on evidence they know the advisor processed.

**Advisor:** "Agreed. Editorial director moves to medium — three interview transcripts is real signal. Content-ops stays low. Updating the manifest now, then writing."

### User requests a confidence upgrade at write time

**User:** "Actually, the competitive.md confidence should be medium, not low. We walked through all five competitors in the battle-card phase and I validated every differentiator claim by hand."

**Advisor:** "You're right — the battle-card PHASE was thorough and you confirmed each claim against your direct sales experience. That's user-validated evidence, not inference. Competitive moves to medium.

Updated manifest:
- brand/competitive.md — draft / **medium**

Everything else stays as listed. Ready to write."

> Advisor updates the manifest on user request with a clear reason, does not push back on a well-supported ask.
