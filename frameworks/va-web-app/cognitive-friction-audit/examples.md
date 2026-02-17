# Cognitive Friction Audit Examples

## Phase 1: Understand Cognitive Friction

### User with e-commerce checkout issues

**User:** "Our checkout has a 70% abandonment rate. People add to cart but don't buy."

**Advisor:** "70% abandonment tells me there's significant friction between 'I want this' and 'I bought this.' The brain decided to buy (Homer said yes), but something in checkout made it too hard to follow through.

Let's map this checkout journey. Walk me through every step from 'Add to Cart' to 'Order Confirmed.' What screens do they see? What do they have to fill out? What decisions do they face?"

> Acknowledge the problem and immediately focus on mapping the journey

### User who doesn't understand the types

**User:** "What's the difference between information overload and decision fatigue? They seem similar."

**Advisor:** "They're related but distinct:

**Information overload**: Too much to READ. Your page has 2,000 words, 15 features, 8 testimonials. The brain says 'I can't process all this' and leaves.

**Decision fatigue**: Too much to CHOOSE. Your page has 4 pricing tiers, 6 add-ons, custom vs standard options. The brain says 'I can't decide' and leaves.

The fix for overload is REDUCE content. The fix for fatigue is RECOMMEND a default. Different problems, different solutions.

Where do you think your friction is - too much to read, or too much to choose?"

> Clarify the distinction with concrete examples

## Phase 2: Map the Journey

### User with SaaS onboarding

**User:** "Our onboarding flow: Sign up form, email verification, profile setup, team invite, first project creation, tutorial video, dashboard."

**Advisor:** "That's 7 steps before they experience value. Each step is a potential exit point.

**Diagnostic questions**:
- What percentage complete email verification?
- Where's your biggest single drop-off?
- How long does the full flow take?
- Is the tutorial video optional or required?

The thing is, by step 7, Homer's enthusiasm has probably faded. They signed up with excitement, but you're making them do homework before they get the reward.

What's your completion rate for the full onboarding?"

> Map the journey and immediately flag the cognitive cost

### User mapping a lead gen funnel

**User:** "Landing page with form, thank you page with calendar link, booking confirmation, reminder emails, then the call."

**Advisor:** "Four touchpoints between interest and conversation. Let me understand the friction potential at each:

**Landing page form**: How many fields?
**Thank you page**: Is the calendar link above the fold? Is it the only CTA?
**Booking confirmation**: Does it set clear expectations for the call?
**Reminder emails**: How many, and do they add value or just remind?

The biggest friction I'd predict is at the calendar booking - that's a commitment decision. Walk me through what they see on that thank you page."

> Identify likely friction points before scoring

## Phase 3: Score Friction Points

### User with complex pricing page

**User:** "Our pricing page shows 4 tiers: Free, Starter, Pro, Enterprise. Each has a feature comparison table with 25 features."

**Advisor:** "Let me score this:

**Pricing Page** - Friction Score: 8/10

- **Information Overload**: 25 features across 4 tiers = 100 data points. Working memory holds 7. You're asking them to process 14x what they can hold. Major friction.
- **Unclear Next Step**: Which tier should they pick? If you're not recommending one, they have to figure it out themselves.
- **Decision Fatigue**: 4 tiers with no clear guidance. Research shows 3 options is the sweet spot. 4 creates comparison paralysis.
- **Cognitive Dissonance**: Low - assuming tiers align with expectations.

**The 5-second test**: Can someone understand which tier is right for them in 5 seconds? Almost certainly not with a 25-feature table.

Does this match what your data shows - long time on page but low conversion?"

> Score with specific numbers tied to cognitive principles

## Phase 4: Diagnose Root Causes

### User with form abandonment

**User:** "Our contact form has 12 fields and a 15% completion rate."

**Advisor:** "Let me be direct: 12 fields is homework. You're creating unexpected effort and information overload simultaneously.

**The real problem**: You want information. They want to talk to you. These goals are in conflict. Every field you add serves YOUR need, not theirs.

**The behavioral mechanism**: Each field is a micro-decision ('What do I put here?'). 12 decisions before they can submit. Decision fatigue compounds - by field 8, they're mentally exhausted.

**Working memory math**: 5-9 chunks max. You're asking for 12+ chunks (fields) plus navigation context plus 'why am I doing this' plus whatever they were thinking before. You've exceeded capacity.

Which of these 12 fields could you live without? Be honest - what do you actually NEED versus what's nice to have?"

> Direct diagnosis with specific cognitive mechanisms

## Phase 5: Design Friction Reduction

### User with checkout friction

**User:** "Checkout has: cart review, account creation, shipping, billing, review, confirmation. Drop-off is highest at account creation."

**Advisor:** "Account creation is your friction wall. Here's the intervention:

**Current Friction**: Forced account creation before purchase

| Problem | Fix |
|---------|-----|
| Unexpected effort | Guest checkout option - let them buy first |
| Decision fatigue | 'Create account' checkbox at confirmation (after purchase) |
| Information overload | Remove 'benefits of account' pitch - they don't care yet |

**Why it works**: They came to BUY, not to JOIN. Forcing registration before purchase is adding friction to get something you want (their data) at the expense of what they want (the product). Let them complete their goal first, then offer account creation as convenience ('Save your info for next time?').

**Expected impact**: Guest checkout typically increases conversion 20-35%. You'll still get most accounts - people create them post-purchase for tracking.

What's the constraint that made you require account creation in the first place?"

> Specific fixes tied to friction types with expected outcomes

## Phase 6: Create Testing Plan

### User ready to implement

**User:** "I want to reduce my form from 12 fields to 5. Just name, email, company, phone, and message."

**Advisor:** "That's a 58% reduction in cognitive load. Let me help you test this:

**Hypothesis**: 'By reducing form fields from 12 to 5, we will see increased submission rate because we're eliminating decision fatigue and unexpected effort.'

**What to measure**:
- Primary: Form submission rate
- Secondary: Lead quality score (to ensure you're not losing qualified leads)
- Watch metric: Support tickets about form confusion (should decrease)

**Test design**:
- 50/50 split between 12-field and 5-field versions
- Run until 100+ submissions per version (or 2 weeks minimum)
- Track not just completion rate but also time-to-complete

**Success threshold**: If submission rate increases 20%+ without quality decrease, the friction was real.

**One thing to watch**: Make sure the 5 fields are clear. 'Message' as a label is ambiguous. 'How can we help?' might be clearer. Don't add friction back through unclear labels.

When can you implement this test?"

> Specific test design with success criteria and potential pitfalls

## Phase 7: Build Your Friction Library

### User overwhelmed by the methodology

**User:** "This is helpful but I can't audit every page. What's the minimum I should do?"

**Advisor:** "Focus on your highest-traffic, highest-intent pages. Probably 3-5 pages matter:

1. **Home page** - First impression friction
2. **Pricing/Product page** - Decision friction
3. **Checkout/Signup** - Completion friction

**Weekly friction check** (takes 10 minutes):
1. Look at your highest drop-off step (analytics)
2. Run the 5-second test on that page
3. Count: choices, form fields, paragraphs of text
4. Ask: 'What would I remove if I had to cut 50%?'

**Monthly friction audit** (takes 1 hour):
1. Walk through your core conversion path as a new visitor
2. Score each step 1-10
3. Fix the highest-friction step before moving on

Build a 'what we fixed and what happened' log. After 6 months, you'll have your own friction playbook.

What's your highest-traffic page you haven't audited yet?"

> Simplify into practical routine
