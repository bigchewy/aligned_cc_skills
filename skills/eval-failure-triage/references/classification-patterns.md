# Eval Failure Classification Patterns

Detailed taxonomy of LLM eval failure types with examples. Load this reference when classifying failures in Phase 2.

---

## Category (a): Real Prompt Quality Issue

**Definition:** The LLM response is genuinely poor — the prompt doesn't guide the model to produce good output.

**Signals:**
- Both heuristic and judge fail consistently (4+ out of 5 runs)
- Reading the actual response confirms it's bad (verbose, off-voice, generic)
- The prompt lacks guidance that would fix the issue (no length constraints, no pacing instructions)

**Example:**
Advisor prompt encourages verbose responses but no pacing guidance exists. The model faithfully follows these instructions and produces 10-12 sentence, multi-paragraph responses with 4-6 questions. This is the prompt working as written — but producing poor conversational quality.

**Fix strategy:** Add missing guidance to the prompt without changing the advisor's voice. E.g., a "Conversation Pacing" section that says "ask ONE question at a time" and "keep responses to 2-3 short paragraphs."

---

## Category (b): Prompt Template Constraint

**Definition:** The prompt template structure limits what the model can do, even if the voice prompt is good.

**Signals:**
- The response follows the template correctly but loses distinctive voice
- Template instructions are more salient than voice instructions
- Framework phases crowd out personalization or voice

**Example — Template crowding:**
A framework has rigid phases with scripted language. The personalization context IS appended to the prompt, but the framework's procedural structure is more salient. The model follows the phases rather than weaving in contextual patterns.

**Fix strategy:** Add brief bridging instructions. E.g., "Stay in your natural voice for the themes" or "When personalization context reveals a relevant pattern, name it briefly before moving to the next phase."

---

## Category (c): Eval Calibration Issue

**Definition:** The eval infrastructure is testing the wrong thing — thresholds, keywords, fingerprints, or heuristic logic don't match what the model actually produces.

### Subcategory c1: Wrong Keywords

**Signals:**
- Heuristic fails but judge passes
- Keywords reference content from a different turn or context
- Keywords use specific terms the model won't naturally produce

**Fix strategy:** Change keywords to match what the model can produce in that turn's context. For openings, use theme-derived terms. For response turns, use terms from the user's message.

### Subcategory c2: Wrong Voice Fingerprint

**Signals:**
- Voice heuristic or judge evaluates against the wrong advisor's patterns
- Scenario names an advisor that isn't the one actually responding

**Example:**
Scenario names advisor X but the framework loads advisor Y as primary responder. The voice fingerprint checks for advisor X patterns against advisor Y's responses.

**Fix strategy:** Update the fingerprint to match the actual responding advisor. Consider renaming the scenario for clarity.

### Subcategory c3: Thresholds Too Strict

**Signals:**
- Deterministic failure across all runs on a specific metric
- The response is actually good when read by a human
- The metric penalizes the advisor for doing their job

**Fix strategy:** Adjust thresholds globally or add per-scenario overrides. Prefer global changes if the threshold is too strict for the general case.

### Subcategory c4: Turn-Type Mismatch

**Signals:**
- Opening turns fail differently than response turns
- The heuristic applies uniformly but the turns have different characteristics

**Fix strategy:** Skip the heuristic on specific turn types, or add turn-type-aware keyword sets.

### Subcategory c5: Infrastructure Bug

**Signals:**
- Judge reasoning doesn't match the response ("No response was provided to evaluate")
- Scores are 0 or 1 with nonsensical reasoning
- Long system prompts are involved

**Fix strategy:** Increase truncation limits, or selectively send only the relevant prompt section to the judge for each dimension.

---

## Category (d): Model Variance

**Definition:** The failure is caused by inherent randomness in the response model, the judge model, or both.

### Response Model Variance

**Signals:**
- Same scenario passes some runs, fails others
- The response quality genuinely varies — some runs produce strong voice, others are generic
- No prompt change can eliminate the variance, only shift the distribution

**Example:**
Same scenario scores 2-5 across runs with identical prompts. In some runs, the opening themes are distinctively voiced. In others, the themes are generic. The prompt is the same; the model samples differently.

### Judge Model Variance

**Signals:**
- Same response gets different scores across runs
- Judge reasoning contradicts itself across evaluations
- Smaller judge models: shorter context and less nuanced evaluation

**Fix strategy for variance:**
- Accept that some variance is inherent — a 70% pass rate may be the realistic ceiling
- Consider multi-run averaging (run 3x, take median) for high-stakes evaluations
- Improve judge rubric specificity to reduce judge variance
- Upgrade judge model if variance is too high for the dimension
- Don't chase 100% pass rate on variable scenarios — it leads to over-permissive evals

---

## Classification Decision Tree

```
For each failing dimension:

1. Did the heuristic fail?
   YES → Read the heuristic details
     - Are the keywords/thresholds appropriate for this turn type?
       NO → (c) Eval calibration
       YES → Continue to step 2
   NO (heuristic passed or n/a) → Go to step 2

2. Did the judge fail?
   YES → Check judge reasoning
     - Is the reasoning coherent and specific?
       NO → (c5) Infrastructure bug or (d) judge variance
       YES → Read the actual response
         - Is the response genuinely poor?
           YES → (a) Real prompt issue or (b) template constraint
           NO → (d) Judge variance
   NO → Heuristic was the sole failure → (c) Eval calibration

3. Is the failure consistent (4+ out of 5 runs)?
   YES → (a) or (c) — not variance
   NO → (d) Variance is a factor — fix (a)/(c) first, accept remaining variance
```

---

## Fix Priority Order

Always fix in this order:

1. **(c) Eval calibration** — cheapest, no prompt risk, instant verification
2. **(b) Template constraints** — minor additions, low risk
3. **(a) Prompt quality** — substantive changes, run evals to verify
4. **(d) Variance mitigation** — accept or add multi-run logic

Fixing (c) before (a) is critical. Many apparent prompt failures disappear when the eval is properly calibrated.
