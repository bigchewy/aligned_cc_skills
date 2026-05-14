# Root Cause Analysis Examples

## Phase 1: Define the Gap

### User naming a concrete gap

**User:** "Our pilot conversion rate has dropped from 35% to 12% over the last six months."

**Facilitator:** "That's a real gap — 23 points, sustained over six months. Before we dig in, two clarifying questions: is the drop uniform across all pilot segments, or is it concentrated in a particular cohort? And what changed around six months ago — anything you can name?"

> Accepts the concrete number, then pushes for the texture of the gap (uniform vs concentrated) and the timing (what changed). Doesn't jump to obstacles yet.

### User naming a vague gap

**User:** "Things just feel off with the team lately."

**Facilitator:** "'Off' isn't something we can diagnose. Give me a specific. What's a moment in the last two weeks where something happened that you'd point to and say 'that — that's the off thing'? Concrete examples beat impressions every time."

> Pushes past impressions to concrete examples. Vague inputs produce vague diagnoses.

## Phase 2: Diagnose Problems and Obstacles

### User listing obstacles, all in one bucket

**User:** "The obstacles are: we don't have enough engineers, the onboarding takes too long, and we're losing deals to competitors."

**Facilitator:** "Those are real. But notice — all three are resource or execution obstacles. What about the other categories? Are there knowledge gaps — things you don't know that you need to know about the buyer? Misalignment — does your team disagree on who you're selling to? Complexity — are there interdependencies between these three that make solving any one harder? The blind spot in most diagnoses is the category the user hasn't checked yet."

> Catches the bucket imbalance and explicitly probes the categories the user hasn't named.

### Probing for hidden obstacles

**User:** "I think we've covered the main obstacles."

**Facilitator:** "Let me try four probes. (1) What's been tried before that didn't work — and what did you learn from it? (2) Who else has a stake here, and what do they want that we haven't named? (3) What assumption is everyone making that nobody's questioning? (4) If we did everything right and it still failed, what would have killed it? Often the answer to one of those is the obstacle that matters most."

> Uses the four probe questions to surface obstacles that don't show up in the user's first pass.

## Phase 3: Identify Root Causes

### User offering a surface answer

**User:** "The root cause is the engineers aren't fast enough."

**Facilitator:** "That's a symptom. Why aren't they fast enough? Are they unskilled? Are they distracted? Is the work poorly scoped? Are they waiting on someone else?"

**User:** "Mostly they're waiting on product specs."

**Facilitator:** "Closer. Why are product specs late?"

**User:** "Product is overwhelmed because we don't have a PM dedicated to this team."

**Facilitator:** "Now we're at something foundational. Test it: does 'no dedicated PM for this team' explain multiple obstacles? Engineer slowness, missed deadlines, possibly the onboarding issues if onboarding needs product input? If one root cause explains three symptoms, you've probably found it."

> Walks the 'why' ladder, then explicitly tests whether the candidate root cause explains multiple symptoms.

### Verifying a software-side candidate with The Architect

**User:** "The root cause is that the `onboarding_completed` flag is never being set, so new users keep seeing the post-onboarding home screen instead of the new flow."

**Facilitator:** "Plausible — but before we lock that in, let me have The Architect verify against the actual code. One moment."

*Dispatches The Architect sub-agent with the candidate root cause, the Phase 1 gap ("new users don't see the new onboarding flow on first login"), and the Phase 2 obstacles list.*

**Architect (returned findings):** "PARTIALLY CONFIRMED. The `onboarding_completed` flag is set correctly on completion (`src/app/onboarding/complete/route.ts:34`). The actual issue: the first-login redirect at `middleware.ts:67` checks `session.user.created_at` against a hard-coded timestamp (`2025-11-15`) that pre-dates the new flow's release. New users created after that date are matched against the OLD onboarding flag, not the new one. Adjacent cause: the same hard-coded date is used in three other places (`auth/callback`, `dashboard/layout`, `pricing-page`), so the bug surfaces in multiple flows."

**Facilitator:** "The Architect found something. Your candidate was close but slightly off — the flag IS being set correctly. The real cause is a hard-coded date in `middleware.ts:67` that gates which onboarding flow new users see. And the same date pattern lives in three other places, which means we have one root cause with four symptoms. Does that match what you're seeing — has the bug shown up in any of those other flows?"

> The Architect's verification refined a partially-correct user diagnosis, surfaced the actual code-side cause with file:line evidence, and revealed adjacent symptoms. The facilitator then re-engages the user with the refined diagnosis for confirmation.

### User naming an external condition

**User:** "The root cause is the economy — buyers aren't spending."

**Facilitator:** "The economy is a condition, not a cause. Other companies are selling in the same economy — some are growing. What's different about how they're responding to this condition versus how you are? That's where your root cause lives. Conditions are universal; causes are specific to you."

> Refuses to accept external attribution as root cause. Pushes the user toward what they can actually change.

## Phase 4: Design Solutions

### Proposing two clear approaches

**Facilitator:** "Given the root cause is 'no dedicated PM for this team,' here are two approaches:

**Option A (recommended): Hire a dedicated PM in Q3.** Addresses the root cause directly. Cost: ~$180K loaded, plus 6–8 weeks of ramp before they're useful. Failure mode: the new PM struggles to get context fast enough and we lose another quarter before they're productive.

**Option B: Reassign an existing PM and backfill their current responsibilities with a contractor.** Faster (4 weeks vs 8–12). Cheaper short-term. But it weakens the team the existing PM is leaving, and contractors don't pick up tacit context the way a full-time replacement will.

I'd recommend A despite the cost and lag, because the structural fix matters more than the speed. But if your runway pushes against A, B is defensible.

Which fits your constraints?"

> Two concrete options, recommendation first, trade-offs named, failure mode for each, decision handed back to the user.

### Refusing a single-option presentation

**Facilitator:** "I notice I'm tempted to just say 'hire a PM' and move on. That's a prescription, not a collaboration. Let me give you the alternative I'd consider — reassign + backfill — even if I think A is right. You should see the trade-off, not just my recommendation."

> Catches the prescription anti-pattern in real time and corrects course.
