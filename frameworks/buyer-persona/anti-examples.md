# Buyer-Persona Anti-Examples

### Conflating role with market

**User:** "I want to build a persona for healthcare CIOs — that's our main buyer."

**Wrong:** Advisor accepts "healthcare CIOs" as the role definition and immediately begins profiling Chief Information Officers in the healthcare vertical as a single unified persona.

**Right:** "Healthcare CIO describes a vertical, not a role. A CIO at a hospital system is accountable for clinical systems uptime and EHR integration. A CIO at a health plan is accountable for claims processing infrastructure and data security. Before I build this profile: which organization type is your buyer, and what are they actually measured on at the board level?" Vertical context belongs in `audiences/*`; the persona file captures the role's accountability structure.

> Role and market are different coordinates. Mixing them produces a persona that looks specific but applies to no one — an enterprise IT leader who could work at any regulated company.

---

### Producing a generic "buyer" persona

**User:** "Great — can you write the CMO persona now?"

**Wrong:** Advisor produces: "The CMO is a data-driven executive who values ROI and wants to see measurable outcomes. They are under pressure to demonstrate results to the board and are increasingly aware of the importance of digital transformation." This reads like marketing-stock copy applicable to any senior buyer at any company.

**Right:** "Before I write the file, I need the CMO's specific accountability metric — what number does she own at the board level? And where does she sit in your buying committee — initiator, champion, or late-stage blocker? Generic output is what we're replacing with this framework, and I can't replace it without specifics."

> A persona file's whole job is role-specific evaluation signal. If the output could describe any executive in any industry, it has failed. Generic language signals that PHASE 1 accountability anchoring was skipped.

---

### Skipping the commercial insight in PHASE 5

**User:** "The main objections we hear are budget, timeline, and switching costs."

**Wrong:** Advisor responds to each objection directly: "For budget, emphasize ROI. For timeline, show your fast-track implementation. For switching costs, offer migration support and case studies." No commercial insight is identified. No reframe is constructed. The advisor remains in product-defense posture.

**Right:** "Those are the expressed objections — what they say in the room. The more important question is: what does she believe about her own situation that makes those objections feel rational? If the budget objection is covering for 'I don't think this will move my number,' the real work is finding the gap in her current model she hasn't accounted for. Where is she quietly bleeding cost or risk that her current approach can't address?"

> PHASE 5's job is to find the commercial insight that reframes the buyer's thinking — not to produce a FAQ. Listing generic objection responses leaves the advisor in product-defense mode, which Dixon's Challenger frame explicitly discards.

---

### Letting the user dictate the persona

**User:** "The CFO is very numbers-focused, always asks about payback period, and is generally supportive once he sees the math."

**Wrong:** Advisor transcribes this directly: "Evaluation criteria: payback period. Disposition: supportive once ROI is demonstrated. Primary concern: financial returns." Output mirrors the user's optimistic read without interrogation.

**Right:** "'Generally supportive once he sees the math' describes deals that close. What does he say when the math doesn't land? What payback horizon does he use — 12 months, 24, internal IRR hurdle rate? Does he trust peer-company benchmarks or does he build his own model from your inputs? Supportive CFOs aren't the problem. We need his skepticism map as much as his champion map."

> The framework's job is to extract sharpness, not transcribe the seller's beliefs. If the advisor writes whatever the user asserts, the output reflects the seller's optimism, not the buyer's reality. Every claim earns its place in the file only after interrogation.

---

### Writing more than one role per run

**User:** "Can you do CMO, CFO, and CMIO in this session? All three show up in our deals."

**Wrong:** Advisor produces three persona outputs in a single run, writing CMO, CFO, and CMIO profiles to `brand/personas/` at once, treating the session as a batch job.

**Right:** "One role per run — that's the file contract. `personas/{role}.md` is scoped to a single role because each requires its own full accountability anchoring, criteria mapping, and commercial insight. Three roles in parallel produces three shallow profiles. Pick the role where your deal risk is highest right now — who is most likely to kill your next deal? Start there. We can build the others in subsequent sessions."

> The framework's WAIT points exist to extract judgment from the user at each phase — that depth cannot be spread across three simultaneous profiles. Three roles in one session produces three outputs at PHASE 2 depth instead of one at PHASE 6 depth. Shallow breadth is not a substitute for one complete profile.
