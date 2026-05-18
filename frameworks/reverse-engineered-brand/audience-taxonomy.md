# Audience Taxonomy (Canonical — Digital Health)

> **Status:** Canonical reference for the `audiences/` slice in the AI-native `brand/` folder. Consumed by `reverse-engineered-brand` PHASE 2 to classify a brand against known payer segments and procurement channels.
>
> **Why this exists:** In digital health, "audience segments" and "procurement channels" are *exogenously defined* by the payer and regulatory landscape, not discovered through a positioning framework. A brand doesn't *invent* a Medicaid segment — it either serves the existing Medicaid market or it doesn't. So the right activity for the `audiences/` folder is **classification against a known list**, not framework-driven discovery.
>
> **Scope:** This taxonomy is digital-health-specific. The same orchestrator could plug in a different taxonomy for a different vertical, but the current `reverse-engineered-brand` framework is committed to digital health (see `docs/brand-folder-spec.md` § Target population).

## Payer segments (`audiences/segments/{segment-id}.md`)

Each segment below is a regulatory or payer-defined population category. Classification rule: a brand serves a segment if its source material references the segment by name OR describes the population context (e.g., "low-income", "dual-eligible", "65+", "self-insured") in a way that maps to the segment.

| Segment ID | Display name | Population context | Typical signals in source material |
|------------|--------------|--------------------|-----------------------------------|
| `commercial` | Commercial | Employer-sponsored or individual-market plans | "commercial book of business", "employer-sponsored", "PPO/HMO plan" |
| `medicaid` | Medicaid | State-administered programs (MCO or FFS) | "Medicaid managed care", "MCO", "state Medicaid", "Medicaid MCO" |
| `medicare-advantage` | Medicare Advantage (MA) | CMS-regulated MA plans (Part C) | "MA plan", "Part C", "Medicare Advantage", "MA-PD" |
| `aco` | ACO | Accountable Care Organizations (MSSP, REACH, Pioneer) | "ACO", "MSSP", "ACO REACH", "shared savings" |
| `dual-eligible` | Dual-Eligible | Medicare + Medicaid coverage populations | "dual eligible", "D-SNP", "MMP", "duals" |
| `pediatric` | Pediatric | Child-focused populations (often state-specific) | "pediatric", "child population", "CHIP", "pediatric Medicaid" |
| `self-funded-employer` | Self-Funded Employer | Large employers that self-fund insurance | "self-insured", "self-funded", "TPA", "ASO" |
| `tricare-va` | TRICARE / VA | Military and veteran populations | "TRICARE", "VA", "veterans", "DoD" |
| `aca-exchange` | ACA Exchange | Marketplace / individual ACA plans | "marketplace", "exchange", "ACA plan", "individual market" |
| `direct-consumer` | Direct-to-Consumer | No payer intermediary; patient pays directly | "DTC", "cash pay", "out-of-pocket", "self-pay" |

## Procurement channels (`audiences/channels/{channel-id}.md`)

Each channel describes *who buys the product* (the procurement gatekeeper), not who uses it. A brand may operate through multiple channels; a single sale may involve multiple gatekeepers (e.g., payer + employer).

| Channel ID | Display name | Procurement context | Typical signals in source material |
|------------|--------------|---------------------|-----------------------------------|
| `employer` | Employer | Sold as an employee benefit; employer is buyer | "benefits team", "HR benefits", "employee wellness", "employer customer" |
| `payer` | Payer | Sold to health insurance plans | "health plan", "payer customer", "insurer", "MCO partnership" |
| `provider` | Provider | Sold to providers (health systems, clinics, IPAs) | "health system", "clinic", "provider org", "IPA", "ACO contract" |
| `pharma` | Pharma | Sold to or partnered with pharmaceutical companies | "pharma partner", "drug manufacturer", "biotech", "Pharma Services" |
| `direct-consumer` | Direct-to-Consumer | Sold directly to patients/individuals | "patient app", "consumer purchase", "patient-pay", "DTC funnel" |
| `broker-consultant` | Broker / Consultant | Sold through benefits brokers or consultants | "benefits broker", "consultant relationship", "Mercer", "Aon", "WTW" |
| `aggregator` | Aggregator / Marketplace | Sold via aggregator platforms or marketplaces | "Epic marketplace", "Salesforce AppExchange", "aggregator listing" |

## Classification contract

When the orchestrator runs PHASE 2 classification against this taxonomy, it produces:

1. **One slice file per identified segment** at `{brand-folder-path}/.build/slices/audiences/segments/{segment-id}.md`
2. **One slice file per identified channel** at `{brand-folder-path}/.build/slices/audiences/channels/{channel-id}.md`
3. **An OQ JSON** at `{brand-folder-path}/.build/slices/audiences.oq.json` containing low-confidence classifications and any signals that didn't map cleanly to the taxonomy.

Each slice file has frontmatter `synthesis_method: classification` (distinguishes it from framework-dispatched slices which use `synthesis_method: framework`). The body contains: the segment/channel description, evidence excerpts from source material, and a confidence tag.

## When to skip

If source material contains NO signal for a given segment or channel, do not instantiate the slice file. Leaving the file absent is preferable to writing a low-confidence stub — the brand doesn't operate in that segment, and a stub creates false signal downstream.

## When a brand operates outside the taxonomy

If source material clearly references a segment or channel not in this taxonomy (e.g., a digital-health brand that explicitly sells to international payers, or a non-traditional channel like school districts), emit a P1 OQ recording the gap:

```
- file: audiences/{segments|channels}/{best-guess-id}.md
- question: "Source material references {signal phrase}. This doesn't map cleanly to the canonical taxonomy. Should {best-guess-id} be added to the taxonomy, or is this a one-off that should be folded into an existing slot?"
- confidence: low, impact: P1
- why_it_matters: ...
- rationale: ...
```

The orchestrator surfaces these in `review.html` as taxonomy-extension candidates. The user decides whether to extend this file.

## Ideal inputs

The `audiences/` folder is populated via classification (not framework dispatch), so its `input_asks` live here rather than in a framework's frontmatter. The orchestrator reads this section at PHASE 3.2 and merges these asks into the `audiences` folder entry alongside any framework-dispatched ones.

```yaml
input_asks:
- tier: critical
  ask: "Documents naming each segment served (signed agreements, BAAs, segment-specific case studies)"
- tier: recommended
  ask: "Pricing models broken out by channel or segment"
- tier: optional
  ask: "Sales notes describing channel-specific buying criteria"
```
