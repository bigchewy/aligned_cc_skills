# 3B Framework - Anti-Examples

These are failure modes to avoid when running the 3B framework. Each section names the temptation, shows the wrong response, and offers the right one.

---

## Anti-Pattern 1: Skipping B1 to Get to "the Real Work"

**User input:** "OK we know the behavior is sign-up conversion. Can we skip to barriers?"

**Wrong response:**
"Sure, let's go to barriers. What barriers do you see in the sign-up flow?"

**Why this fails:** "Sign-up conversion" is not a behavior - it's a metric. The team will end up debating which UI step to tweak without ever agreeing on what success looks like, because "conversion" can mean "they hit Submit," "they verified email," "they completed the onboarding flow," or "they connected an integration." Different behaviors require different diagnoses.

**Right response:**
"Sign-up conversion is a metric, not a behavior. We can't diagnose barriers until we agree what 'sign up' specifically means. Is it: hits Submit on the form? Verifies email? Completes onboarding step three? Connects a payment method? Each one has different barriers. Name the exact behavior - the action you'd see in a screen recording - and then we move to B2."

**The discipline:** B1 is the load-bearing step. If the team rushes past it, every downstream diagnosis is unfounded.

---

## Anti-Pattern 2: Treating "Remove Friction" as the Default Move

**User input:** "We've identified barriers in the structural category - too many steps. Let's just remove the steps."

**Wrong response:**
"Good - shorter flows usually convert better. Cut what you can."

**Why this fails:** Friction is not always the enemy. Sometimes adding the right friction (a confirmation question, a small commitment step, a clarifying choice) *increases* the desired behavior because it changes the user's mental model or filters in users who actually want the product. Apartment List added questions and conversion went up. Removing all friction is the lazy answer.

**Right response:**
"Slow down. Friction is not always the enemy. Before you remove a step, ask: does this step make the user think about what they actually want? Does it filter in users who will succeed? Does it create a small commitment that increases follow-through? Sometimes the right move is to keep the step but make it more useful - a question that helps the user, not just data collection for you. What does each step actually do for the user?"

**The discipline:** Diagnose each barrier individually. Some are real friction (remove). Some are misclassified - they're actually useful commitment or clarification (keep, or even amplify).

---

## Anti-Pattern 3: Trusting Survey Data Over Product Data

**User input:** "Our user research shows users say they want a one-click sign-up. So the barrier is the number of fields."

**Wrong response:**
"That's strong qualitative data. Let's remove fields and see if conversion rises."

**Why this fails:** What users say and what they do are different categories of fact. Users say they want one-click sign-up because that's the socially-correct, low-effort answer to a survey question. But behavioral data often shows that longer sign-ups can outperform short ones because they create commitment, clarify fit, and signal seriousness. Acting on stated preference over revealed behavior is one of the most common - and most expensive - mistakes in product design.

**Right response:**
"What users *said* in the survey is the lowest tier of evidence I trust. What did they DO in the product? Pull the data: at which step do users actually drop off? How does session length correlate with retention? Run a small A/B - same flow, fewer fields - and measure not just sign-up rate but 30-day retention. If short-flow users sign up more but churn faster, you just optimized the wrong metric."

**The discipline:** Rank evidence: revealed behavior > behavioral intent > stated preference. Always.

---

## Anti-Pattern 4: Ending With a List of Levers Instead of One Experiment

**User input:** "Great - so we'll add social proof, reduce friction on step 3, change the microcopy, and improve the onboarding sequence."

**Wrong response:**
"Sounds like a solid roadmap. Let's prioritize and ship them in order."

**Why this fails:** The whole point of behavioral diagnosis is to pick the highest-leverage bet and test it cleanly. Shipping four changes at once means you can't isolate which one moved the metric. If conversion improves, you'll fight for months about attribution. If it falls, you can't roll back the right change. You've turned a learning experiment into a deployment.

**Right response:**
"One. Pick one. The 3B framework's value is forcing a single high-leverage bet, not generating a four-item roadmap. Of those four, which one do you believe will move the needle most? Tell me which, why, and the smallest version that gives you a clean signal. The other three are still on the list - we'll get to them after we learn from the first."

**The discipline:** End with one experiment, one metric, one falsification condition. Roadmaps come after learning, not instead of it.

---

## Anti-Pattern 5: Applying 3B When the Real Problem Isn't Behavioral

**User input:** "We've run 3B three times now and our retention is still flat. What other barriers should we test?"

**Wrong response:**
"Let's dig deeper into the emotional barrier category - there must be one we missed."

**Why this fails:** Sometimes the problem isn't a behavior problem. It's a positioning problem (users don't know why they need the product), a pricing problem (the price is wrong for the segment), or a product-market-fit problem (the product doesn't solve a strong-enough problem for this audience). Repeating behavioral diagnosis on a non-behavioral problem is doing physics on a chemistry question - the framework is the wrong tool.

**Right response:**
"Three failed diagnoses is a signal. The problem might not be behavioral. Step back: are users not retaining because they don't see why this product matters (positioning), because the price doesn't match the perceived value (pricing), because the product doesn't actually solve a strong-enough pain (PMF), or because the wrong people are signing up (acquisition mismatch)? Behavioral design is powerful for behavior problems. It's not the answer to everything. Which category does this actually belong in?"

**The discipline:** Domain humility. 3B has boundaries. When it stops working, the move is to question the category, not run the framework a fourth time.

---

## Anti-Pattern 6: Behavioral Design Sliding Into Dark Patterns

**User input:** "What if we add emotional friction - make it really hard to cancel, hide the unsubscribe button, use guilt copy when they try to leave?"

**Wrong response:**
"Those are valid friction levers. They'll likely reduce churn."

**Why this fails:** Behavioral design can be used to change behavior the user *would endorse on reflection* - or to manipulate behavior they wouldn't. The line matters. Hiding the cancel button raises a short-term metric and destroys long-term trust, often producing public backlash and regulatory attention. It also corrupts the team - once dark patterns are normalized, they spread.

**Right response:**
"Stop. There's a line between behavioral design and manipulation. The test: would the user, on reflection, endorse the behavior you're trying to create? If a user signed up expecting easy cancellation and you're hiding the button to retain them, you're not designing - you're manipulating. Short-term metric goes up, long-term trust collapses, and you'll show up in a Twitter thread about dark patterns by next quarter. Find the legitimate retention lever - one that improves the product or makes the value more salient. That's the real work."

**The discipline:** Behavioral design has an ethical anchor. State it explicitly when the conversation drifts toward manipulation. Don't lecture; name it once, clearly, and redirect.
