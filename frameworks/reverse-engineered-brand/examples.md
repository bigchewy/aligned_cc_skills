# Reverse-Engineered Brand Examples

Running example: **Fieldline** — a B2B SaaS company that helps mid-market field-service organizations dispatch, track, and invoice without spreadsheets.

---

## PHASE 0: Intake

### User giving a clear URL and optional local folder

**User:** "The URL is fieldline.io. I also have a folder at ~/Documents/fieldline-research with a few customer interview transcripts and our last sales deck."

**Advisor:** "Got it. Public surface: fieldline.io. Supplementary content: ~/Documents/fieldline-research — I'll check for interview transcripts and any deck or one-pager files. I'll read the homepage and About page first to establish a baseline before touching the supplementary content, so I'm not anchoring on internal language before I see what you say publicly. Any time pressure or hard constraints before I start?"

> Opens with explicit sequencing — public surface before internal documents — and checks for constraints before consuming the URL

### User giving a vague description without a URL

**User:** "We help field-service companies manage their operations. I don't have a public URL — we're kind of pre-launch."

**Advisor:** "Understood — pre-launch or private company, no public URL. I can still run this session, but the intake changes: instead of reading your public surface, I'll need you to walk me through what you currently say to a prospect in the first two minutes of a call. That becomes our stand-in for the homepage. Do you have a deck, one-pager, or even a strong email template I can use as the raw material? If not, start with the two-minute pitch and we'll build from there."

> Doesn't stall on the missing URL — offers a concrete fallback and keeps the session moving

---

## PHASE 1: Public surface review

### Advisor's URL summary matching the user's intent

**User:** "What did you find on the homepage?"

**Advisor:** "Fieldline leads with 'Stop losing revenue to missed appointments and manual invoicing.' The hero section targets field-service companies — HVAC, plumbing, electrical — that are growing past the point where spreadsheets and phone calls work. The value proposition is operational control: dispatch visibility, automated scheduling, and same-day invoicing. The word 'spreadsheet' appears four times above the fold. The primary audience signal is company size — language like 'your growing team' suggests 20–200 employees rather than enterprise. Does that match how you'd describe what you do?"

> Presents a concrete summary and closes with a calibration check — doesn't assume accuracy

**User:** "Yes, that's exactly it."

**Advisor:** "Good. I'll lock that as the baseline audience frame and move to your supplementary content."

> Confirms the frame is locked before proceeding — no drift between phases

### User correcting an inferred audience claim

**User:** "You said our audience is 20–200 employees — that's not right. Our sweet spot is 50–500, and we've been moving upmarket. We just closed a 600-person roofing company."

**Advisor:** "Corrected — 50–500 is the stated sweet spot, upmarket motion in progress. That changes the positioning question: your homepage is signaling small-team ('your growing team'), but your deal motion is landing mid-market. That gap is either a funnel problem — qualified buyers self-select out before they talk to sales — or a messaging lag — your best customers are bigger than your homepage implies. We'll surface that in the positioning work. I'll adjust the audience assumption across all subsequent phases."

> Accepts the correction immediately, names the strategic implication, and commits to carrying it forward across all phases

---

## PHASE 6: Messaging-distillation handoff

### Advisor surfacing a tagline draft and asking for calibration

**Advisor:** "Positioning is complete. Before I open the messaging-distillation framework, I want to surface one inference for your calibration. The positioning work landed on 'operational control for field-service teams that have outgrown spreadsheets' as the category framing. A candidate tagline that falls out of that: 'The dispatch layer your crew actually uses.' It hits the operational register, implies adoption (not just purchase), and sidesteps the generic 'platform' language that saturates your category. Does that direction feel right, or does it pull away from something important?"

> Probes tagline direction before opening the framework — surfaces the inference so the user can correct it before it gets baked in

**User:** "I like the direction but 'crew' sounds too blue-collar for our upmarket move. We'd say 'team' or 'ops team.'"

**Advisor:** "Noted — 'crew' activates the wrong register for the upmarket buyer. 'Team' is safer; 'ops team' is more precise and carries more authority. Carrying that word-choice forward into the messaging session. Opening the messaging-distillation framework now — you'll be asked about tagline variants, value-prop phrasings, and persona-specific language."

> Accepts the register correction and explicitly commits it to carry-forward before handing off to the next framework

---

## PHASE 11: Folder write

### Advisor previewing the write and asking for confirmation

**Advisor:** "Ready to write the brand folder. Here's what I'm about to create under `brand/`:

```
brand/
  strategy/
    positioning.md       (confidence: high)
    narrative.md         (confidence: high)
    jobs-to-be-done.md   (confidence: medium)
  personas/
    vp-ops.md            (confidence: high)
    owner-operator.md    (confidence: medium)
  language/
    messaging.md         (confidence: high)
    voice.md             (confidence: high)
  market/
    competitive.md       (confidence: medium)
  proof/
    proof-points.md      (confidence: low)
  design/
    design-principles.md (confidence: medium)
```

`proof-points.md` is at low confidence — I only have two quantitative claims from your homepage, both unverified. `jobs-to-be-done.md` is at medium — inferred from the interview transcripts, not validated with you directly. Everything else has session-level backing. Confirm this write, or adjust confidence tiers or paths before I proceed."

> Previews the full folder structure with confidence tiers before touching the filesystem — gives the user a final correction window

### User requesting a confidence tier change

**User:** "The jobs-to-be-done.md should be high confidence, not medium. We went through all five jobs in detail during the session."

**Advisor:** "You're right — we validated all five jobs against the interview transcripts and you confirmed each one. Bumping jobs-to-be-done.md to high confidence. Revised write:

```
  strategy/
    jobs-to-be-done.md   (confidence: high)  ← updated
```

All other tiers unchanged. Writing now."

> Accepts the correction with a one-line rationale check, restates only the changed item, and proceeds without re-listing the entire structure
