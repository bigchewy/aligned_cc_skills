# FEW HICCUPPS Review — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Telling the user to stop writing automated tests

**User:** "I write all my tests first with TDD. Is that the wrong approach?"

**Wrong:**
"Unit tests are just checks. Real testing is exploratory. Stop writing so many automated tests and spend that time testing by hand."

**Right:**
"No. Those are checks, and they're worth having. Checks are change detectors, tools that let you refactor with confidence. Keep writing them. The question for this review is what they don't ask. Let's find that."

**What to do instead:** Welcome the checks and keep them. Aim the review at what the checks miss. Never tell the user to stop writing them.

---

## 2. Treating passing tests as proof

**User:** "All 22 tests pass, so the design's claims are verified."

**Wrong:**
"Great, with 22 passing tests you're in good shape. Let's move on to the edge cases."

**Right:**
"Good that they pass. Keep them. But a check confirms only what it was written to check. Which of the 22 call getUserTimezone()? Which compare the digest's order with the feed? When a check passes, we don't know whether the program works. We still read the code."

**What to do instead:** Ask what each relevant check asserts. A claim stays open until a check asserts it or the code has been read.

---

## 3. Taking the doc's word about the codebase

**User:** "The doc says the existing getUserTimezone() helper handles this, so we're covered."

**Wrong:**
"Since the helper already exists, the time zone part is done. Let's look at the email template."

**Right:**
"The doc says so. Let's open lib/time.ts and see. A design doc is a claim about the codebase, and claims get checked against the code."

**What to do instead:** For every claim the doc makes about existing code, open the file and read it. Mark each one confirmed, contradicted, or can't tell.

---

## 4. Calling an inconsistency proof of a bug

**User:** "The digest uses a different template from the reset email."

**Wrong:**
"That's a bug. Fix the template before you build anything else."

**Right:**
"That's inconsistent with the Product oracle, so it might be a problem. Is it on purpose? The reset email is transactional and the digest isn't, so some difference makes sense. If it's on purpose, say so in the doc."

**What to do instead:** An inconsistency points to a possible problem. It isn't proof. Name the oracle, say why it might matter, and let the user decide whether it's intended.

---

## 5. Forcing a finding for every oracle

**User:** "I can't think of anything for Image or Comparable Products."

**Wrong:**
"Every oracle should produce at least one finding. Let me suggest some: maybe the font doesn't match your brand, maybe Asana does digests differently..."

**Right:**
"That's fine. An oracle that finds nothing did its job. Let's move on to Statutes and Standards."

**What to do instead:** Don't pad. Invented findings bury the real ones. Move on and note the oracle was checked.
