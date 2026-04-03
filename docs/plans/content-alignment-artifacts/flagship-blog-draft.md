# How to Run a Positioning Exercise with April Dunford at 2 AM

It's 11 PM. You've been going back and forth on how to describe your product for three weeks. The homepage says one thing, the sales deck says another, and your team gives a different elevator pitch depending on who's in the room. You know the positioning is off. You just can't articulate what's wrong.

You could ask ChatGPT to help. You'd get a template: "Fill in your target audience, key differentiators, and value proposition." You know that's not how positioning works. You could ask it to "be April Dunford" and you'd get a costume — a superficially confident voice that says "positioning" a lot but has no framework behind it.

What you actually need is someone who's helped 200+ tech companies through this exact problem. Someone with a process, not just opinions. But April Dunford isn't available at 11 PM, and her consulting rate is probably higher than your monthly software budget.

Here's what I did instead.

---

## The System

I built a Claude Code plugin called [aligned](https://github.com/bigchewy/aligned_cc_skills) that encodes real expert methodologies into executable workflows. 62 advisor personas — not generic AI roleplay, but actual experts with their real frameworks, signature questions, and failure modes encoded. 135 structured decision frameworks with quality gates that enforce the process.

The difference between this and "ask AI to be an expert" is the same difference between a flight simulator and a kid holding their arms out pretending to be a plane. One has a system. The other has a pose.

I'm going to walk you through what an actual positioning exercise looks like using this system. Not a hypothetical. The real thing.

## The Exercise

I needed to position the aligned plugin itself for open-sourcing. The repo was going public and I needed a cold visitor — someone landing on the GitHub page with zero context — to understand immediately what they were looking at and why they should care.

I invoked `/aligned:brainstorming` and described the problem.

The system detected it was a business strategy problem and routed me into a structured process: goal clarification, obstacle diagnosis, root cause analysis, then solution design. Not "here are some ideas" — a gated sequence where I couldn't jump to solutions before understanding what was actually in the way.

**Goal phase.** The system asked questions one at a time. What specific outcome are we trying to achieve? Who is this for? What does success look like? It wouldn't let me proceed until the goal was stated in one clear sentence that I confirmed. This alone would have saved me the three weeks of going in circles.

**Problem diagnosis.** What's preventing this from already being true? The system identified obstacles and categorized them: knowledge gaps, misalignment, complexity. It probed for hidden obstacles — what assumptions are we making? What's been tried before? What would make this fail even if we did everything right?

**Root causes.** For each obstacle, the system dug deeper. Why does this obstacle exist? Then why again. And again. Until we reached something foundational. The root cause wasn't "our messaging is unclear" — it was that every content surface assumed a developer-only audience while the actual target was broadening to semi-technical leaders who care about outcomes, not implementation details.

**Solution design.** Only after all of that did we get to solutions. The system proposed approaches that addressed the root causes, not the symptoms. It broke the design into sections and validated each one before moving on.

Then the critique panel ran.

## The Panel

This is where it gets interesting. After the design was written, the system selected a panel of advisors to evaluate it — not random AI personas, but specific experts chosen because their domains matched the work.

April Dunford's 5 Components of Positioning framework structured the evaluation. Competitive alternatives, unique attributes, value, target customers, market category — each component examined against the actual design.

Seth Godin weighed in: "The remarkable thing isn't the feature count — it's the *opinion*. The plugin has a spine, a worldview about how AI-assisted work should be done. That's what makes people talk about it."

Clayton Christensen applied his disruption lens: "This is disruptive in the precise sense — making structured thinking that used to cost $500K from McKinsey available at the marginal cost of an API call."

Rob Walling brought the bootstrapper perspective: "Open-source plus consulting is viable but fragile if you become an installation technician. Validate with three organizations measuring before-and-after."

Joe Pulizzi challenged the content strategy: "A GitHub star is not a subscriber. Build an audience alongside the repo."

Each advisor spoke in their real voice with their real frameworks. Godin talked about tribes and permission marketing. Christensen talked about jobs to be done and disruption theory. Walling talked about MRR, churn benchmarks, and the stair step method. These aren't generated opinions — they're encoded methodologies pushing back on the work.

The output — the actual positioning document — became the strategic foundation for everything that followed: the README, the onboarding experience, the consulting pitch, and this blog post.

## What Generic AI Gives You

For contrast, here's what you get if you ask a general-purpose AI to help with positioning:

**You:** "Help me position my product."

**AI:** "Sure! Let's start by identifying your target audience, key differentiators, and unique value proposition. What problem does your product solve?"

That's a template, not a methodology. There's no diagnosis. No root cause analysis. No quality gates preventing you from jumping to a tagline before understanding what's actually different about your product. No expert pushing back when your "differentiator" is something every competitor also claims.

Ask it to "be April Dunford" and you'll get a persona that uses her vocabulary but none of her methodology. It'll say things like "you need to identify your competitive alternatives" without actually walking you through the 5 Components in order, without gating each phase, without pushing back when your answers are vague.

The difference is methodology versus pattern matching. One follows a real process with real constraints. The other generates plausible-sounding advice.

## Why This Matters for Growing Companies

Here's the problem I keep seeing with the leaders I coach: decision quality degrades as the company grows.

When you were five people, every important decision happened with the founder in the room. The positioning was consistent because one person held it all in their head. The sales pitch was sharp because the CEO did every demo.

Now you're thirty people. The new VP of Marketing is positioning the product differently than the founder. The sales team is making promises that don't match the product roadmap. The junior PM is making strategic decisions based on pattern-matching from their last job, not from deep understanding of this company's competitive position.

The traditional solution is expensive: hire senior people, bring in consultants, build a culture of rigorous thinking from the top down. It works. It's also slow, hard to scale, and breaks every time someone leaves.

What if the methodology was available in the system itself? What if the new hire could run the same positioning exercise with the same frameworks as the founder? What if the 2 AM decision got the same rigor as the Tuesday morning strategy meeting?

That's what a virtual board of advisors does. Not replacing human judgment — augmenting it with real methodology so the quality of thinking doesn't depend on who happens to be in the room.

## Try It

The aligned plugin is open-source. Install it, invoke `/aligned:use-advisor april-dunford`, and see what happens. Run `/aligned:brainstorming` with a real problem. The methodology speaks for itself.

Every advisor prompt, every framework, every quality gate is inspectable in the repo. This isn't a capabilities pitch — it's working software.

**[Install aligned →](https://github.com/bigchewy/aligned_cc_skills)**

---

*Get notified when new advisors and frameworks ship — one email, no spam, no fluff.* <!-- [Sign up](TBD) -->
