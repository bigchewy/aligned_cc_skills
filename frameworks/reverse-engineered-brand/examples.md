# Reverse-Engineered Brand Examples

Running example: **Fieldline** — a B2B SaaS company that helps mid-market field-service organizations dispatch, track, and invoice without spreadsheets.

---

## PHASE 0: Intake (the only WAIT in the build pass)

### User giving a clear URL, source folder, write target, and org name

**User:** "URL is fieldline.io. Source folder is ~/Documents/fieldline-research with customer interview transcripts and our last sales deck. Write the brand folder into ~/Documents/fieldline-research/brand. Org name: Fieldline."

**Advisor:** "Got it. Sources: fieldline.io (public) plus ~/Documents/fieldline-research (local). Write target: ~/Documents/fieldline-research/brand. Org name: Fieldline. Running Extract → Transform → Load now. No further interruptions until the HTML review opens in your browser."

> The advisor restates the inputs once and proceeds to a fully automated build. No mid-flow questions.

### User giving a vague description without a URL

**User:** "We help field-service companies manage their operations. I don't have a public URL — we're kind of pre-launch."

**Advisor:** "Understood — pre-launch, no public URL. For Extract, I'll work from local material only. Point me at a folder with anything written down: deck, one-pager, email template, founder essay, Loom transcript. If you have nothing in writing yet, this framework isn't the right starting point — you'd need to do an intake conversation first and dump that into a file."

> Offers a concrete substitute for the URL. Does not stall.

---

## PHASE 1: Extract (silent — no advisor narration to the user)

The Extract phase is fully silent. No user interaction. The advisor reads every URL page and local file, classifies them, and holds the Source Registry in memory until the Load phase writes it into `brand/CLAUDE.md § Source Registry`.

---

## PHASE 2: Transform (silent — no advisor narration to the user)

The Transform phase is fully silent. The advisor produces all slice drafts in memory with confidence tagging, logs every gap and inference as an Open Question, and proceeds straight to Load.

---

## PHASE 3: Load and final report

### Advisor's end-of-run report

**Advisor:** "Done. Wrote `~/Documents/fieldline-research/brand` with 11 slice files plus `CLAUDE.md`, `version.yaml`, `contracts.yaml`.

Confidence distribution: 3 high, 5 medium, 3 low.

Logged 14 Open Questions covering: primary competitive alternative, owner-operator persona depth, voice register, pricing language, four unverified proof claims, three tagline candidates. The interactive review document is open in your browser at `~/Documents/fieldline-research/brand/open-questions.html` — type answers in the browser, click 'Copy all answers,' then paste the resulting prompt back into Claude Code (this session or a new one) to apply the answers to the folder.

The canonical Open Questions queue lives in `brand/CLAUDE.md § Open Questions`. The HTML is a view of it — paste-back keeps them in sync."

> The final report is single-shot. The advisor reports the manifest, confidence distribution, Open Questions count + topic summary, and the HTML path. No mid-flow updates.

---

## Open Question shape (what the advisor writes during Transform)

Every Open Question in the queue (both in `brand/CLAUDE.md § Open Questions` and `brand/.open-questions.json`) has the same shape:

```markdown
### OQ-1: Primary competitive alternative

**File:** `strategy/positioning.md`#competitive-alternatives
**Confidence:** low
**What I wrote:** Best customers were previously cobbling together spreadsheets and manual dispatch.
**Question for you:** Was the real alternative for your best customers the spreadsheet state, or were they limping along on a competitor product they hated?
**Why it matters:** If it's the spreadsheet state, positioning frames against operational chaos. If it's incumbent software, positioning frames against migration pain. Two different messaging arcs.
**Deepen with:** `/aligned:use-framework 5-components-positioning` for a full interactive pass on this slice
**Sources:** #4, #6
```

> The Open Question is a self-contained card: file/anchor, current draft, the calibration question, the downstream consequence, the owning framework for deeper work, and source provenance. The HTML renders each one as an answer-textarea card; the markdown form is the canonical record.

---

## Slice → owning framework mapping (in CLAUDE.md)

After the build, `brand/CLAUDE.md § Next Steps to Deepen` lists every slice with its owning framework. Example:

```markdown
## Next Steps to Deepen

- `strategy/positioning.md` → run `/aligned:use-framework 5-components-positioning` for a deeper, interactive pass
- `strategy/narrative.md` → run `/aligned:use-framework strategic-narrative` for a deeper, interactive pass
- `language/messaging.md` → run `/aligned:use-framework messaging-distillation` for a deeper, interactive pass
- `language/voice.md` → run `/aligned:use-framework brand-voice` for a deeper, interactive pass
- `personas/vp-ops.md` → run `/aligned:use-framework buyer-persona` for a deeper, interactive pass
- `market/competitive.md` → run `/aligned:use-framework competitive-battle-card` for a deeper, interactive pass
- `market/alternatives.md` → run `/aligned:use-framework 5-components-positioning` (Component 1 is the canonical source)
- `proof/proof-points.md` → run `/aligned:use-framework proof-points-audit` for a deeper, interactive pass
- `audiences/channels/employer.md` → GAP — no framework owns this slice; synthesis is ad-hoc. Consider commissioning a `channel-strategy` framework.
```

> Every slice in the folder appears here. The user never has to guess which framework to run; the mapping is explicit and authoritative.

---

## HTML review (offline from this session)

After the framework ends, the user reviews `brand/open-questions.html` in the browser. The HTML has:

- One card per Open Question, with file, confidence, draft, question, why-it-matters, and source provenance
- A textarea on each card for the user's answer
- A "Skip for now" checkbox on each card
- Per-card "Copy this question's prompt" button — copies a one-question paste-back prompt
- Bottom-of-page "Copy all answers" button — copies a batch paste-back prompt

The paste-back prompt is plain Claude Code instructions to apply the answers to the slice files and mark Open Questions resolved in `brand/CLAUDE.md`. The user can paste it into this session, a new session, or any session — the prompt is self-contained and identifies the brand folder path.

> The framework's job ends when the HTML opens. The HTML is the review surface. The paste-back is the apply mechanism. The brand folder is the canonical store.
