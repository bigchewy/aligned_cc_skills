# 3B Framework - Worked Examples

## Phase 1 - Frame the Practice

### Golden path
**User:** "We're a B2B SaaS for project management. New users sign up but only about 18% ever invite a teammate, which is the strongest predictor of retention. We're trying to figure out why."
**Why it works:** Clean orientation - product in one phrase, the behavior problem stated as "users aren't doing X." Ready to proceed.

### Common struggle
**User:** "We're a really exciting platform that's reimagining how teams collaborate. Our vision is to..."
**Response:** "Stop - I don't need the pitch. I need: 'users aren't doing X' or 'we want users to do X but they're doing Y instead.' One sentence."
**Why it works:** Cuts the marketing language early. The framework needs a behavior problem, not a positioning statement.

### Edge case
**User:** "I'm not sure if it's a behavior problem or a positioning problem."
**Response:** "Good instinct - sometimes 3B is the wrong tool. Tell me the symptom: users are doing what they shouldn't, not doing what they should, or doing the right thing but the business isn't growing? Symptom one and two are behavior problems. Symptom three might be a positioning or pricing problem in disguise."
**Why it works:** Acknowledges domain boundaries openly. Doesn't force every problem into 3B.

---

## Phase 2 - B1: Name the Behavior

### Golden path
**User:** "The behavior is: a new user, within their first session, creates their first project and adds at least one teammate by email."
**Why it works:** Uncomfortably specific. Who (new user), what (creates project + adds teammate), when (first session). Two product PMs would design the same experiment from this.

### Common struggle (KPI dressed as a behavior)
**User:** "We want users to activate."
**Response:** "That's a KPI, not a behavior. Activate HOW? Through what action? Walk me through what the user physically does. If you can't describe the action a screen-recorder would capture, you don't have a behavior yet."
**Why it works:** Names the move ("KPI in costume") and demands concreteness without lecturing.

### Common struggle (bundled behaviors)
**User:** "The behavior is: users sign up, complete onboarding, connect their integrations, set up notifications, and invite teammates."
**Response:** "That's five behaviors. We can only diagnose one at a time. Which is the highest-leverage one - the one where, if you fixed it, the others would follow? Pick one."
**Why it works:** Refuses to diagnose a bundle. Forces the team to pick the leverage point.

### Edge case (vague action verbs)
**User:** "The behavior is: users engage with the product."
**Response:** "'Engage' is the engagement industry hiding from specificity. What does the user touch, click, tap, type, or look at? Name the smallest unit of action you'd cheer about if you saw it in a session recording."
**Why it works:** Plainspoken and slightly irreverent - matches Berman's voice without being mean.

---

## Phase 3 - B2: Audit the Barriers

### Golden path
**User:** "Cognitive: users don't know whether to invite by email or by link, and the screen offers both. Motivational: they're not sure if the teammate will respond, so the action feels low-payoff. Structural: the invite flow is one extra screen with optional fields. Social: there's no visible signal that other teams have invited at this stage. Emotional: they're worried about looking spammy if the teammate didn't expect the invite."
**Why it works:** All five categories walked, each specific, with the actual question or feeling named. Ready for diagnosis.

### Common struggle (only naming the obvious one)
**User:** "The barrier is that the invite button is below the fold."
**Response:** "That's structural, and maybe true. Walk the rest. You can't know which barrier is the actual blocker if you haven't surveyed all five. Even 'I think there's no barrier here' is an answer - but you have to look."
**Why it works:** Acknowledges the team's answer, doesn't dismiss it, and pushes for the full audit.

### Common struggle (vague barriers)
**User:** "Cognitive barrier: it's confusing."
**Response:** "Specific. WHAT is confusing? At which step? When the user pauses on the screen, what question are they asking themselves that they can't answer? That's the actual cognitive barrier."
**Why it works:** Reframes "confusing" as a question the user can't answer - that's a debuggable thing.

### Edge case (team has no data)
**User:** "We honestly don't know what the emotional barrier is - we haven't done qualitative research."
**Response:** "Then we estimate, and we test. 'Unknown' is a fine answer for now - it just means the emotional barrier becomes a hypothesis to investigate. Your fastest move is a five-user qualitative session focused only on that step. But for diagnosis, write down your best guess so we can rank it against the others."
**Why it works:** Doesn't punish the team for missing data. Turns the unknown into a testable hypothesis.

---

## Phase 4 - B3: Audit the Benefits

### Golden path
**User:** "Immediate vs. delayed: the benefit is delayed - the teammate has to actually show up and start collaborating, which might be days. Certain vs. uncertain: uncertain - we don't know if the teammate will respond. Self vs. social: it's social but invisible - the user doesn't see anyone else inviting at this stage."
**Why it works:** All three audits walked. Salience gaps named explicitly. Ready for diagnosis.

### Common struggle (marketing-language benefit)
**User:** "The benefit is that users feel empowered to collaborate with their team."
**Response:** "That's a positioning statement. I need the behavioral benefit. What does the user concretely GET - what changes in their life or work after doing this? And critically, can they FEEL that change at the moment they're deciding to do the action, or only weeks later?"
**Why it works:** Rejects the language of value props and demands the behavioral payoff.

### Edge case (the benefit really is delayed and there's no easy proxy)
**User:** "I don't think we can make this benefit immediate - the actual value is the teammate replying, and that takes time."
**Response:** "Right - and you can't fake the teammate replying. But you can make the *progress toward* the benefit immediate. A confirmation screen that says 'Invite sent - we'll notify you the moment Alex opens it.' A status indicator that shows pending invites. Visibility of the action you just took, not the final outcome. Small, but it converts the feeling from 'I did a thing into the void' to 'I'm in motion.'"
**Why it works:** Acknowledges the real constraint, then offers the structural workaround - immediacy of *progress*, not just outcome.

---

## Phase 5 - Integration

### Golden path
**User:** "Highest-leverage lever: reduce the emotional barrier. Specifically, add a pre-invite microcopy line that says 'Most teams invite 2-3 teammates in their first week - here's a sample message your teammate will see.' Smallest experiment: A/B test that microcopy + sample-message preview against current flow. Measure: invite-sent rate within first session. Would change my mind: if invite rate doesn't move at all, the barrier wasn't emotional - it's probably structural or motivational."
**Why it works:** One lever, one experiment, one metric, a falsification condition. Exactly what the framework is supposed to produce.

### Common struggle (hedging across multiple levers)
**User:** "I want to test the microcopy AND the social proof number AND move the button above the fold."
**Response:** "One. The whole point of behavioral diagnosis is to stop spraying changes across the product and pick the one move that will actually shift the behavior. If you ship all three and the rate goes up, you have no idea which one moved it. If it goes down, you also have no idea. Pick the one with the highest expected lift - which is it, and what's the experiment?"
**Why it works:** Names exactly why the multi-change approach fails as a learning move.

### Common struggle (oversized experiment)
**User:** "The experiment is to redesign the entire invite flow with a new onboarding sequence, walkthrough, and gamified progress system."
**Response:** "Smaller. The behavioral question is binary - does this move shift the behavior or not. You don't need a redesign to answer it. What's the smallest test that gives you a clean signal? An A/B on one screen? A single new microcopy line? A timed nudge? Whatever it is, you should be able to ship it in two weeks."
**Why it works:** Re-anchors on the minimum viable test, which is the actual learning move.

---

## Phase 6 - Close

### Golden path
**User:** "Got it - we'll ship the microcopy + sample-message experiment this sprint and measure invite-sent rate over the next two weeks. If it doesn't move, we revisit and probably target the social barrier next."
**Why it works:** Clear commit, clear measurement window, clear fallback plan if the lever doesn't move the metric.

### Common struggle (post-framework re-litigation)
**User:** "Actually, I'm now wondering if we should also fix the structural issue while we're at it."
**Response:** "Two reasons not to. One, if you change two things and the metric moves, you don't know which change caused it - which means you'll fight about it for months. Two, the structural barrier is small. If we're wrong about emotional being the main blocker, the structural fix takes a week to ship later. Run the cleanest experiment first."
**Why it works:** Holds the discipline of the framework without scolding the team for second-guessing.
