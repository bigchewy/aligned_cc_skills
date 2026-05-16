# Proof-Points Audit Anti-Examples

*Running example: Cliniq, a clinical decision support platform that sells AI-assisted diagnostic tools to hospitals and health systems. Claims appear across their homepage, investor deck, and sales collateral.*

---

### Anti-Example 1: Accepting vague social proof as a proof point

**User:** "Here's one more claim I want to include: 'Trusted by many leading health systems nationwide.'"

**Advisor (wrong):** "Added:

```
Claim 9: "Trusted by many leading health systems nationwide" — location: homepage hero
Source: customer relationships
Date: current
Confidence: medium
```

This is solid social proof — it signals adoption without committing to a number you'd have to maintain."

> "Trusted by many" is not a proof point — it is a sentiment. A proof point is a quantitative, sourced, dated claim that a reader could, in principle, verify or falsify. "Many" has no number, no source, and no re-verification cycle. Recording it in the audit table gives it a false legitimacy and implies it can go into copy alongside claims that actually have evidence behind them. The correct response: reject the entry at extraction and explain why. "This claim doesn't meet the extraction criteria — it needs a number, a source (e.g., Salesforce account count or signed contracts), and a date. Tell me the actual customer count and where you pull it from, and I'll add it." Vague social proof in the table contaminates the audit — it trains the user to treat unverifiable statements as if they belong in the same category as audited metrics.

---

### Anti-Example 2: Accepting "founder said so" as source identification

**User:** "Claim 3 (reduces diagnostic errors by 31%) — the source is our CEO. He quoted it in an all-hands last quarter."

**Advisor (wrong):** "Got it:

```
Claim 3: source = CEO statement, all-hands Q3 2025
Confidence: medium — internally corroborated
```

Executive-level attestation is a valid internal source, especially for early-stage companies."

> "The CEO said it" is not a source — it is a citation of a citation. The QA Engineer's job in PHASE 2 is to push past attribution to the underlying artifact: What study produced the 31% figure? Was it an internal analysis? A customer case study? A peer-reviewed paper? An A/B test? If the CEO quoted it in an all-hands, he got it from somewhere. The source is that somewhere. The correct response: "A CEO statement is not a source — it's a reference to a source. I need the underlying artifact: the study ID, the customer name and contract date, the internal analysis doc, or the third-party report. If no artifact exists, this claim is currently unsourced." Labeling executive attribution as "internally corroborated" inflates confidence and will cause this claim to survive to copy without the evidence that would make it defensible.

---

### Anti-Example 3: Confidence inflation across the board

**User:** "Can you run through the confidence labels for all eight claims?"

**Advisor (wrong):** "Here are the confidence labels:

```
Claim 1: "reduces diagnostic errors by 31%" — high
Claim 2: "deployed across 40+ hospitals" — high
Claim 3: "clinically validated algorithm" — high
Claim 4: "reduces time-to-diagnosis by 18 minutes" — high
Claim 5: "99.7% uptime SLA" — high
Claim 6: "SOC 2 Type II Certified" — high
Claim 7: "the most accurate AI diagnostic tool on the market" — high
Claim 8: "saves physicians 2 hours per shift" — high
```

All eight claims have organizational backing and appear in formal materials — that earns high confidence across the board."

> Labeling every claim `high` defeats the purpose of confidence scoring. The label is not about organizational seriousness — it is about source quality, freshness, and verifiability. `High` is reserved for: a primary source document (a published paper, an audited cert, a signed contract), a founder-validated statistic with an identified underlying methodology, or an independently verifiable fact (e.g., an active certification). Claim 1 may be high if it comes from a published study; it is low if it comes from an internal pilot of 3 customers. Claim 7 ("most accurate") is low regardless of organizational backing — superlatives require third-party analyst validation by definition. Claim 8 is low unless it comes from a systematic time-tracking study, not self-reported estimates. Inflated labels do not help the user — they produce a clean-looking audit that fails under the first press inquiry, analyst due diligence, or enterprise procurement review. The correct behavior: label conservatively, explain each label, and offer the specific upgrade path for each low or medium claim.

---

### Anti-Example 4: Single file for a digital-health org with FDA clearance

**User:** "We just got FDA 510(k) clearance for our diagnostic algorithm and HITRUST CSF r2 certification last month. Should I assemble everything into one proof-points.md?"

**Advisor (wrong):** "Yes, one file keeps things simple. I'll include a section for clinical validation, a section for compliance certs, and the rest for general performance claims. That way your team has a single place to look."

> A digital-health organization with FDA clearance and a formal compliance certification has crossed the threshold where single-file output creates more problems than it solves. FDA clearance belongs in `proof/clinical-evidence.md` — it has its own use context (clinical evaluators, CMO conversations, IRB submissions), its own regulatory re-verification cadence, and its own misuse risk (marketing writers citing clearance as a general performance claim). HITRUST belongs in `proof/compliance.md` — it is read by IT security and enterprise procurement, recertifies on its own cycle, and should not require parsing through sales metrics to locate. Mixing them into a single file makes re-verification unmanageable and creates the exact misuse risk the split is designed to prevent: a content writer pulling the FDA clearance line into a homepage hero because it appeared next to a customer count in the same document. The correct response: three files — `proof-points.md`, `clinical-evidence.md`, and `compliance.md` — with an explanation of who reads each one and what re-verification cadence applies.

---

### Anti-Example 5: Treating the gap report as optional

**User:** "I think we both know what the gaps are at this point — we've been talking through them for the whole audit. Can we skip the formal gap report and just go straight to file assembly?"

**Advisor (wrong):** "Makes sense — the gaps are clear from context. Let me assemble `proof/proof-points.md` now with the verified claims, and you can follow up on the flagged items when you have bandwidth."

> The gap report is not a summary for the advisor's benefit — it is the artifact the organization acts on between framework runs. Skipping it because "we've already discussed the gaps" means the findings live only in conversation context, which expires. The gap report converts everything discussed into a structured, named, dated list that can be assigned, tracked, and closed by people who were not in this conversation. Without it, the correct CEO cannot assign Claim 3 re-verification to a data analyst. The clinical team cannot be handed a specific list of what they need to produce. The next time the audit runs, there is no record of what was flagged and what was resolved. The correct response: run PHASE 5 regardless of how much has been discussed. If the gaps are already clear, the report takes three minutes to produce. Its value is not the discovery — it is the permanence.
