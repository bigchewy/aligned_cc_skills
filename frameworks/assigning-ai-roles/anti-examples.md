# Assigning AI Roles — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Writing the whole prompt in the first reply

**User:** "I want an AI coach for my team's leadership program. Can you write the prompt?"

**Wrong:**
"Sure! Here's a complete AI coach prompt: 'You are a supportive leadership coach…'"

**Right:**
"Before we write a word of it: what should a team member be able to do on their own, without the AI, when this moment is over? Who are they, and do they already know the idea, or are they practicing it, or reflecting after trying it?"

**What to do instead:** Start at Phase 1 and stop at the WAIT. The role, the guardrails, and the steps come from the learning goal. A prompt written before the goal is a guess.

---

## 2. Letting one prompt play several roles

**User:** "It should teach the concept, quiz them, role-play with them, and cheer them on."

**Wrong:**
Drafting one prompt that does all four.

**Right:**
"That's tutor, student, simulator, and a coach's tone. Each fails a different way. Which one moment matters most? We'll build that, and the others get their own prompts."

**What to do instead:** Hold to one role per prompt. Name the roles hidden in the request, pick the one that serves the goal, and park the rest.

---

## 3. Accepting a tool dressed as a tutor

**User:** "The tutor answers their questions about the framework clearly and completely."

**Wrong:**
"Great, clear answers will really help them learn."

**Right:**
"That's a tool, not a tutor. It does the thinking for them. In the Bastani study, students with plain ChatGPT did 17% worse once it was gone. The tutor version held back answers and asked leading questions. Where does the learner generate something here?"

**What to do instead:** Check where the learner's effort happens. If the AI produces the answer, add a guardrail line that makes the learner produce it.

---

## 4. Skipping the test

**User:** "The prompt looks good. Let's finalize."

**Wrong:**
Producing the role card with the prompt marked as done.

**Right:**
"Run it first: a strong learner, a vague one, and one who keeps asking it for the answer. Twenty minutes. If you can't do it now, the card will say 'untested,' and that's the first thing to do."

**What to do instead:** Treat the test as part of the framework, not an optional extra. Mark the card "untested" if the user doesn't run it.

---

## 5. Hype or invented evidence

**User:** "Is there research that AI coaching changes how teams communicate?"

**Wrong:**
"Yes, studies show AI coaching improves team communication by 40%."

**Right:**
"I don't know of a study that shows that for adults practicing interpersonal habits in teams. The strong results I can name are individual learners on academic content: Kestin's physics tutor and the Bastani math study. So treat this as an experiment. What would you watch in real meetings to know if it's working?"

**What to do instead:** Cite only studies you can name. When the evidence doesn't reach the user's case, say so and turn it into a test.

---

## 6. The AI replaces the people

**User:** "The coach can be where they process conflicts with teammates, so they don't have to bring it up in the team session."

**Wrong:**
"Good idea. That keeps the session focused and gives people a safe place to vent."

**Right:**
"Watch that. The AI should send people back to their teammates, not stand in for them. The coach can help someone get ready for the conversation. What's the step where they actually have it with the person?"

**What to do instead:** In Phase 6, make sure the output goes to a human. For team learning, the AI prepares people for each other; it doesn't absorb the conversation.
