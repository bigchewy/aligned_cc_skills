# Proof-Points Audit Examples

*Running example: Carepath, a care coordination platform for chronic disease management. Sells to health systems and large medical groups. Claims appear on their homepage, investor-facing one-pager, and sales deck.*

---

## PHASE 1: Claim extraction

### User pastes copy with a mix of strong and weak claims

**User:** "Here's our homepage hero: 'Carepath reduces hospital readmissions by 40%, delivering measurable ROI for health systems nationwide.' Features section: 'Trusted by 200+ care teams.' Deck slide 3: 'Clinically validated care gap detection.' Sales sheet: 'Saves care managers 6 hours per week.' Footer badge: 'SOC 2 Type II Certified.' One more from the pitch deck: 'The leading AI-powered care coordination platform.'"

**Advisor:** "Running standalone. I've pulled every qualifying claim:

```
1. "reduces hospital readmissions by 40%" — location: homepage hero
2. "delivering measurable ROI for health systems nationwide" — location: homepage hero
3. "Trusted by 200+ care teams" — location: homepage features
4. "Clinically validated care gap detection" — location: homepage features / deck slide 3
5. "Saves care managers 6 hours per week" — location: sales sheet
6. "SOC 2 Type II Certified" — location: homepage footer badge
7. "The leading AI-powered care coordination platform" — location: pitch deck
```

Seven claims. Claims 1, 4, 5, and 7 are the ones I'll push hardest on — they're making specific or superlative assertions. Claim 2 is evidence-shaped but vague enough that it might survive as written. Claim 3 is social proof; I'll need a count methodology. Claim 6 is a certification — either you have the cert or you don't.

Confirm the list, or tell me if anything's missing."

**User:** "You missed one. Slide 8: 'Patients enrolled in Carepath show 23% higher medication adherence.'"

**Advisor:** "Added:

```
8. "Patients enrolled in Carepath show 23% higher medication adherence" — location: deck slide 8
```

Eight claims confirmed. Now: for each one, give me the source."

> Extraction is comprehensive and verbatim; flags the highest-risk claims immediately; accepts the user's correction without re-explaining the extraction criteria

---

## PHASE 2: Source identification

### User reveals a mix of documented and undocumented claims

**User:** "Claim 1 (40% readmission reduction) — that's from a pilot we ran with Memorial Health in 2022. Internal report. Claim 2 (measurable ROI) — no specific source, it's just directional. Claim 3 (200+ care teams) — we count this in Salesforce, as of Q3 2024. Claim 4 (clinically validated) — I think there's a white paper? I'd have to ask the clinical team. Claim 5 (6 hours per week) — user interviews, maybe 12 participants, summer 2023. Claim 6 (SOC 2) — yes, we have the cert. Claim 7 (the leading platform) — no source. Claim 8 (23% adherence) — same pilot as claim 1, Memorial Health 2022."

**Advisor:** "Recorded. A few things to flag now before we date everything:

Claim 4 — 'I think there's a white paper' is not a source. If the clinical team can't produce it this week, this claim is unsourced until they do.

Claim 7 — 'leading' is a superlative with no source. It's either backed by a third-party analyst report or it's not defensible. This is an immediate pull candidate regardless of what the rest of the audit finds.

Claims 1 and 8 share a source — one pilot, one customer. That's a thin basis for public claims. Note the sample size risk before we get to confidence labels.

Sources for all eight claims are recorded. Moving to dates."

> Accepts sources as stated; flags the 'I think' source immediately as insufficient; calls out the superlative claim early without waiting for the full audit to resolve it; notes the shared-source risk

---

## PHASE 3: Date verification

### User discovers several sources are past the 18-month threshold

**User:** "Claims 1 and 8 — the Memorial Health pilot — the internal report is dated March 2022. We haven't re-verified since then. Claim 3 (Salesforce count) — Q3 2024, so September 2024. Claim 5 (user interviews) — summer 2023, let's say August 2023. Claim 6 (SOC 2 cert) — renewed January 2025. Claim 4 — still trying to find the white paper."

**Advisor:** "Today is May 2026. Dates logged:

```
Claim 1: source March 2022, last verified never → 50 months old. Flagged.
Claim 2: no source, no date.
Claim 3: source September 2024, ~20 months old. Flagged (past 18-month threshold by two months).
Claim 4: source unknown. Flagged pending white paper.
Claim 5: source August 2023, ~33 months old. Flagged.
Claim 6: cert renewed January 2025, ~16 months ago. Within threshold — but barely.
Claim 7: no source, no date.
Claim 8: source March 2022 (same pilot as claim 1), never re-verified. Flagged.
```

Five of eight claims are flagged on age or missing dates. This is a typical audit result — it doesn't mean the claims are wrong. It means they haven't been maintained. Moving to confidence labels."

> Uses the actual current date to calculate ages precisely; flags the claim that's only two months past threshold rather than quietly rounding; names the pattern ('typical audit result') to prevent the user from over-reacting before seeing the full picture

---

## PHASE 4: Confidence labeling

### User challenges a label they think is too conservative

**User:** "You labeled claim 5 (6 hours per week) as low. 12 user interviews feels real to me. We designed the study."

**Advisor:** "The label is low because three things compound: sample size is small (12), the data is 33 months old, and the claim implies a precise figure ('6 hours') that an interview-based study can't actually establish — interviews give you directional signal, not hours-per-week measurements. If your team has time-tracking data from those 12 users across a defined period, the label upgrades to medium. If it's self-reported time estimates in interview, the precision isn't in the source. The claim as written on your sales sheet implies a measurement that wasn't taken.

Revised, if you want to defend it now: 'Care managers report saving significant time on documentation.' That's defensible from the source you have. '6 hours per week' is not — not yet.

Labels in full:

```
Claim 1: low (primary source; 50 months old; single customer; never re-verified)
Claim 2: low (no source)
Claim 3: medium (Salesforce CRM count; 20 months old; needs recount)
Claim 4: low (unverified source pending)
Claim 5: low (small sample; self-report; 33 months old)
Claim 6: high (cert on file; renewed 16 months ago; independently verifiable)
Claim 7: low (superlative; no source)
Claim 8: low (same pilot as claim 1; all same weaknesses apply)
```

One high-confidence claim out of eight. Does this match your read? Tell me where I'm wrong."

> Explains why the label is what it is rather than defending the rubric abstractly; offers the upgrade path; provides the safer rewrite without being asked; surfaces the 1-in-8 high ratio as a plain fact, not an alarm

---

## PHASE 5: Gap report

### Advisor produces the gap report; user escalates claim 7

**Advisor:** "Here is the gap report:

**No source:**
- Claim 2: 'delivering measurable ROI for health systems nationwide' — pull or replace with a referenced ROI figure from a named customer
- Claim 7: 'The leading AI-powered care coordination platform' — pull immediately; no analyst or third-party basis on file

**Source older than 18 months:**
- Claim 1: '40% readmission reduction' — Memorial Health pilot, March 2022. Re-verify with Memorial or run the same measurement on your current customer base.
- Claim 5: '6 hours per week savings' — user interviews, August 2023. Either re-interview or narrow the claim to what the source actually shows.
- Claim 8: '23% higher medication adherence' — same pilot as claim 1. Same re-verification requirement.

**Source pending:**
- Claim 4: 'Clinically validated care gap detection' — on hold until clinical team produces the white paper. Treat as no source until confirmed.

**Confidence: low (all of the above)**

**Confidence: medium (watch list):**
- Claim 3: '200+ care teams' — Salesforce, September 2024. Pull a fresh count now — this is the easiest fix on the list and it's 20 months old.

**Confidence: high:**
- Claim 6: SOC 2 Type II cert. Use freely until the next renewal cycle."

**User:** "Claim 7 — pull it immediately. Our CEO put it in the deck and I've been nervous about it for a year. This gives me something to show her."

**Advisor:** "Escalated to immediate pull. The gap report gives you the language: 'Superlative claim — no analyst or third-party basis on file. Cannot be defended if a prospect or regulator asks for evidence.' Your CEO put it there because it felt true; she'll respond to a clean audit output that shows the exposure. Bring the report, not just the conclusion."

> Gap report is organized exactly as the framework specifies; advisor accepts the user's escalation without re-litigating; gives the user a practical note about how to present the finding internally

---

## PHASE 6: Digital-health proof split (optional)

### Example A: No clinical evidence — single file output

**Advisor:** "Two questions before I assemble the output:

1. Does Carepath have clinical evidence claims — randomized controlled trials, peer-reviewed publications, FDA clearance, real-world evidence studies, or similar?

2. Does Carepath hold formal compliance certifications — HIPAA attestation, SOC 2, HITRUST, FDA Quality System Regulation, ISO 13485, or similar?"

**User:** "We have SOC 2 Type II but that's it. No FDA clearance, no peer-reviewed studies. The Memorial Health pilot is internal only — never published."

**Advisor:** "One file: `proof/proof-points.md`. The pilot data and the SOC 2 cert both go there. Clinical-evidence and compliance are separate files only when those categories have enough verified claims to warrant a standalone document with its own use context and re-verification cycle. One cert and one unpublished pilot don't meet that bar — mixing them into the general file keeps things in proportion."

> No-split decision is explained with the 'enough to warrant' criterion rather than a mechanical rule; confirms single file output without ceremony

---

### Example B: FDA clearance + HITRUST certification — three-file output

**User:** "Different scenario — we just acquired a device-adjacent product line. Now we have: FDA 510(k) clearance for the care gap algorithm, HITRUST CSF r2 certification, and two peer-reviewed papers published in JAMIA in 2024."

**Advisor:** "Three files:

1. `proof/proof-points.md` — general quantitative claims (readmission rates, time savings, customer counts)
2. `proof/clinical-evidence.md` — the FDA clearance, the two JAMIA publications, and any real-world evidence tied to the cleared algorithm
3. `proof/compliance.md` — HITRUST CSF r2 and SOC 2 Type II

The reason to split: clinical evidence and compliance certifications are used in different conversations by different people. Clinicians and clinical evaluators read the clinical-evidence file; IT security and procurement read the compliance file; marketing reads proof-points.md. Keeping them separate prevents a marketing writer from citing the FDA clearance as if it's a general performance claim, and prevents a compliance reviewer from having to parse through sales metrics to find the cert details.

Each file has its own re-verification cadence: clinical evidence should be reviewed annually or after any product change that touches the cleared indication; compliance recertifies on the HITRUST or SOC 2 cycle. Mixing them would make those cadences impossible to manage."

> Explains the three-file rationale in terms of audience and re-verification cadence, not just structural tidiness; explicitly names the misuse risk that splitting prevents

---

## PHASE 7: File assembly

### Advisor presents the assembled output with post-audit notes

**Advisor:** "`proof/proof-points.md` is written. Before you distribute it:

Claim 1 and Claim 8 — the Memorial Health readmission and adherence figures — are in the file under 'Flagged for Follow-Up.' They carry the source, the date, and the low-confidence label. Do not use them in live copy until you've re-verified against current data or a broader customer set. The numbers may still be right; the problem is we can't say so yet.

Claim 6 (SOC 2) is the only high-confidence entry. If you need a proof point in a deal this quarter, lead with that one.

Next action on the gap items: Claims 1 and 8 require someone to go back to Memorial Health or run the same measurement on your current book of business. Claim 3 requires a Salesforce pull — that's an afternoon, not a project. Claim 5 requires either a re-interview or a rewrite. Claim 4 stays flagged until the clinical team produces the document.

Set a calendar event to re-verify Claim 6 before January 2027 — that's when the cert age crosses 18 months."

**User:** "Should the gap items stay in the file or do we pull them from the file too?"

**Advisor:** "Leave them in the file, in the 'Flagged for Follow-Up' section, exactly as they are — source, date, confidence label, and the reason they're flagged. The file is your source of truth, not a polished asset. The discipline is: nothing from the flagged section goes into copy until it's resolved and moved to a verified section. If you pull flagged items from the file, you lose track of what needs resolution and someone will resurrect the claim from memory six months from now with no idea it was pulled for a reason."

> Closes the assembly phase with concrete next actions keyed to specific claims; answers the user's process question with a 'why' that prevents a common mistake
