# Report Template for Find Potential Advisors

The brief file uses this template. Phase 1 writes the Brief section. The Write agent adds the
rest, in this order. Every section is required. A field with nothing in it says why it's empty.
It is never left out.

---

## Brief

- **Domain:**
- **Who will use the advisor, and what situation they're in:**
- **Research angles:** (or "none given")
- **Approach preferences:** (or "let the research decide")
- **Other requirements:** (or "none given")
- **Advisors already on the board nearby:** each name, with one line on what they cover
- **Overlaps to avoid (the user's answer):** the user's own words
- **Number of candidates:** (default 10)
- **Hypothetical situation for voice samples:** one concrete situation a user of this advisor
  would bring, in 2 or 3 sentences
- **Research questions:** 3 to 5, one line each

## Research

One subsection per research question:

### <Question>

- What the best sources agree on, in 2 to 4 bullets. Each bullet ends with its URL.
- Where sources disagree, if they do.
- Approaches with the best support, each with its URLs.

## Candidates

A table with one row per candidate:

| Name | Credentials | Approach | Key works (with URLs) | Fit for this brief |
|------|-------------|----------|-----------------------|--------------------|

## Evaluation

How the rating is worked out. Only items with a URL count:

| Rating | Rule |
|--------|------|
| High | 2+ books AND 5+ hours of talks or podcasts AND 3+ distinctive terms |
| Medium | (1+ book OR 2+ hours) AND 1+ distinctive term |
| Low | anything less |

One row per candidate, sorted High, then Medium, then Low:

| Name | Books (count, each with URL) | Talks: minutes per item and their sum in hours (each with URL) | Distinctive terms (with URLs) | Rating |
|------|------------------------------|-------------------------------------------------------------|-------------------------------|--------|

Below the table, for each candidate rated High or Medium: 2 or 3 real quotes, word for word,
each with its URL. Then a line on what is free and what is behind a paywall.

## Finalists

One subsection per finalist (2 or 3):

### <Name>

- **Who they are:** 2 or 3 sentences.
- **How they differ from the board:** one line for each nearby advisor named in the Brief.
- **Frameworks we could build:** 1 to 3, each with the source it would come from.
- **Voice sample:** their answer to the Brief's hypothetical situation, 3 to 5 sentences. Built
  from their real quotes and terms. Every phrase in quotation marks is a real quote. List the
  URL of each quote used below the sample.
- **Trade-offs:** what they're good and bad at compared with the other finalists.

## Recommendation

The recommended finalist and the reason, in one or two sentences.

## What was skipped or not verified

One bullet per item. Pull them from three places:
- agents that failed, and what was lost because of it,
- facts in profiles marked "From memory, not checked:",
- items the evaluators couldn't find or open (`not_found`).

Write "Nothing" only when all three are empty.

## Run record

- Research agents: <n> (one per question)
- Candidate agent: 1
- Profile agents: <n>. Evaluation agents: <n>. The two are different agents.
- Finalists agent: 1. Write agent: 1. Check agents: <n>. Fix agents: <n>.
- Pages opened by research agents: <n>
- Problems the check found and whether they were fixed: one line each, or "none found"

## Chat summary

What the main session says to the user, in this order:

1. The recommendation and the reason, in one sentence.
2. The finalists, one short paragraph each: who they are, why they fit, the rating with its
   counts ("2 books, 6.1 hours, 4 terms"), and their biggest weakness.
3. Strong candidates who were left out, one line each with the reason.
4. **What was skipped or not verified:** the items from that section, or "Nothing."
5. The brief's path.
6. The question: which finalist to add.
