# Reverse-Engineered Brand Anti-Examples

### Reading source files directly into orchestrator context

**User:** [intake done, ~30 PDFs in the source folder]

**Wrong:** Orchestrator opens each PDF with the Read tool inline, then keeps all of them in context while it begins Transform. By slice 3 it is compacting; by slice 6 it has lost the founder narrative; by slice 9 the synthesis is unreliable because earlier context was summarized away.

**Right:** Orchestrator enumerates the source list (Glob, cheap), then dispatches extract sub-agent (dispatched with the `extract.md` template) sub-agents in parallel batches — one per source. Each sub-agent reads its one file in disposable context and writes a structured JSON extract to `brand/.build/extracts/{id}.json`. The orchestrator collects only compact registry entries (~50 tokens each). Raw PDF text never enters orchestrator context.

> The context-bloat guard is the iron rule of this framework. Source folders can have dozens of multi-page PDFs. Reading them inline kills the build before Transform begins. Every file read happens behind a sub-agent boundary.

---

### Reading slice drafts back into orchestrator context

**User:** [Transform done, 12 slice drafts on disk in .build/drafts/]

**Wrong:** Orchestrator Reads each slice draft into context to "assemble" CLAUDE.md, ending up holding 12 slice bodies × ~600 words each ≈ 10K+ tokens of slice content the orchestrator doesn't need.

**Right:** Orchestrator never reads slice draft bodies. To move drafts into final paths, use `mv` (filesystem operation, no body read). To list slices in CLAUDE.md's Slice Index, use the in-memory slice metadata collected from the synthesizer sub-agents' status responses (slice path, confidence, owning framework — all small). The only slice-related content the orchestrator legitimately holds is the aggregated Open Questions queue, which is bounded (~100 tokens per question, typically <50 questions).

> Slice draft bodies are sub-agent outputs that belong on disk. The orchestrator's job is metadata and consolidation, not reading content back in to "check it."

---

### Stopping mid-flow to ask the user for clarification

**User:** [silent, during PHASE 2 Transform]

**Wrong:** Advisor drafts positioning Component 1, then stops and asks "which of these alternatives is primary?" mid-transform, dragging the user into a synchronous walkthrough.

**Right:** Advisor writes the best-defensible inference for Component 1, tags it `confidence: low`, and logs an Open Question with the calibration prompt. Continues silently to the next slice. The user reviews the question later in the HTML.

> There is exactly one WAIT in this framework: PHASE 0 intake. After that, Extract → Transform → Load runs as a single automated sweep. Mid-flow questions defeat the framework's purpose.

---

### Synthesizing without flagging confidence or gaps

**User:** [silent, during PHASE 2 Transform]

**Wrong:** Advisor produces every slice as if it were `confidence: high`, omits Open Questions for inferences it had to make, and treats guessed claims as established fact.

**Right:** Every slice carries explicit `confidence:` frontmatter per claim or section. Every low-confidence item, every gap, every "I had to guess here" lands in the Open Questions queue with a specific calibration question. The folder is a draft that knows what it doesn't know.

> The mechanism that prevents fabricated strategy is per-item confidence tagging plus the interactive HTML review queue. A folder that confidently asserts inferences is worse than a folder with explicit doubts.

---

### Showing the Source Registry to the user for confirmation

**User:** [waiting for the build to finish]

**Wrong:** Advisor builds the Source Registry, presents it to the user, and waits for "proceed" before transforming.

**Right:** Advisor builds the Source Registry silently and writes it into `brand/CLAUDE.md § Source Registry` as part of the Load pass. The user reviews it in the brand folder after the run, or in the HTML's per-question source citations. If a source was missed, the user adds it and re-runs the framework — they do not adjudicate mid-build.

> The pre-transform confirmation WAIT was an earlier design that got reverted. This is now a fully automated build; manual work happens in the HTML review afterward.

---

### Improvising a slice shape outside its owning framework

**User:** [silent, during PHASE 2 Transform]

**Wrong:** Advisor synthesizes `strategy/positioning.md` with a custom three-section structure ("Who we serve / Why we win / What we sell") because it feels cleaner than Dunford's 5 components. Or synthesizes `strategy/narrative.md` with a generic "problem → solution" arc instead of Raskin's 5-element structure.

**Right:** Advisor synthesizes positioning in Dunford's 5 components (competitive alternatives, unique attributes, value, target customers, category) — the exact shape that `5-components-positioning` produces. Advisor synthesizes narrative in Raskin's 5 elements (world, change, losers/winners, promised land, evidence) — the exact shape that `strategic-narrative` produces. Each slice's `owning_framework:` frontmatter field names the framework whose output shape was used.

> Every slice has an owning framework. The orchestrator's job is to *substitute LLM inference for human WAIT-input* inside that framework's shape — not to invent a new structure. If the user wants to deepen the slice later, they run `/aligned:use-framework {owning-framework-id}` — and the deep pass must layer cleanly onto the orchestrator's draft, which only works if both are in the same shape.

---

### Synthesizing GAP slices without flagging the absence of a framework

**User:** [silent, during PHASE 2 Transform]

**Wrong:** Advisor synthesizes `audiences/channels/employer.md` with whatever structure seems natural, sets `confidence: medium`, and proceeds as if it had an owning framework like the other slices.

**Right:** Advisor synthesizes the GAP slice ad-hoc, sets `synthesis_method: ad_hoc` in the slice's frontmatter, sets `owning_framework: null`, and raises exactly one P0 meta-Open-Question *per missing framework* (not per GAP slice instance): "No framework currently owns the `audiences/channels/` slice. Synthesis was ad-hoc. Do you want to commission a `channel-strategy` framework, or accept ad-hoc synthesis going forward?" PHASE 3.1 deduplicates these: if three GAP slices share the same missing framework, one meta-OQ surfaces — not three.

> GAP slices are a known weakness — making them invisible means future improvements happen ad-hoc too. Surfacing the gap as a deduplicated meta-question lets the user decide whether to build a framework for it. Duplicating the meta-OQ per-slice floods the HTML with redundant prompts and defeats the deduplication logic.

---

### Synthesizing a slice's shape without dispatching its owning framework

**User:** [the prompt says "compose 5-components-positioning"]

**Wrong (old design, now superseded):** Orchestrator reads what `5-components-positioning` *produces* (the 5-component output shape) and synthesizes that shape directly from the Source Registry. Causes structural drift — the synthesizer's "5-component-like" output is structurally similar but vocabulary-inconsistent with what the framework actually produces.

**Right:** Orchestrator dispatches the owning framework in AUTO_MODE with the auto-mode-preamble injected, overriding every WAIT. The sub-agent runs the framework's full methodology end-to-end and emits a draft + OQ JSON. The orchestrator collects those outputs — it does not manufacture the slice itself.

> AUTO_MODE dispatch replaced the old "synthesize the output shape" pattern. The preamble turns interactive WAIT-gated frameworks into single-shot machines. The slice content comes from the framework's methodology, not from the orchestrator's inference.

---

### Skipping the HTML review document

**User:** [the build is done]

**Wrong:** Advisor writes the brand folder and ends without producing `brand/review.html`, telling the user "review the Open Questions section of CLAUDE.md when you have time."

**Right:** Advisor writes `brand/.open-questions.json`, dispatches a sub-agent using the `render-review-html.md` prompt template, and waits for it to write and open `brand/review.html` in the browser. The HTML is part of the deliverable, not optional.

> The interactive HTML is the review surface the user expects to see at the end of a run. Producing the JSON but not the HTML breaks the handoff.

---

### Switching advisor voice mid-pass incorrectly

**User:** [during transform of narrative.md]

**Wrong:** Advisor remains in pure April Dunford positioning logic when synthesizing the Raskin 5-element narrative arc — framing narrative around category and competitive alternatives instead of world/change/losers-winners/promised-land/evidence.

**Right:** Each slice has a native frame. When synthesizing narrative, think in Raskin's terms. When synthesizing positioning, think in Dunford's. The orchestrator's outer voice is April Dunford; the per-slice frame matches the slice's source sub-framework.

> The orchestrator narrates as Dunford. The slice content respects the slice's native frame. Leaking one frame into another produces muddled output.

---

### Compound open questions (PHASE 2.4 warning)

**User:** [silent, PHASE 2 Transform emitting OQs]

**Wrong:** Sub-agent emits an OQ with `question: "Is the alternative spreadsheets and is the segment mid-market?"` — two separate predicates joined by `and`. PHASE 2.4 regex flags this as compound; it cannot be routed to a single calibration answer.

**Right:** Split into two atomic OQs: `"Is the primary competitive alternative spreadsheets?"` and `"Is the primary customer segment mid-market?"` — one predicate each. Each can be answered independently in the HTML review.

**Edge case (not compound):** `"Is the pricing model per-member, per-transport, or hybrid?"` — `or` inside a comma-separated alternatives list is not a compound question. The regex correctly does NOT flag this; the single OQ stands.

> PHASE 2.4 validates OQ structure before Load. A compound question that slips through produces an HTML prompt the user cannot answer with a single calibration — splitting it is cheaper than post-hoc repair.

---

### Fabricating verification evidence in AUTO_MODE

**User:** [proof-points-audit sub-agent running in AUTO_MODE]

**Wrong:** Sub-agent writes "Industry studies show 73% reduction in delivery time" in a proof-point draft without an evidence anchor. No source citation, no confidence tag — the claim reads as verified fact.

**Right:** Same situation, no source available → emit an OQ: `confidence: low`, `impact: P0`, `inferred_value: null`, `why_it_matters: "Claim implies verified industry benchmark; no source found in Source Registry. Provide a citation or remove the claim before publishing."` Do NOT write a draft sentence that implies the claim was verified.

> VERIFICATION-STYLE FRAMEWORKS (proof-points-audit, competitive-battle-card) run with elevated fabrication risk in AUTO_MODE because their purpose is to validate claims — not invent them. When evidence is absent, the correct output is an OQ flagging the gap, not a plausible-sounding sentence filling it.
