# AI Search Optimization Checklist — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Fixing before measuring

**User:** "I want to show up in ChatGPT. What should I change on my site?"

**Wrong:**
"Here's what to do: add FAQ schema, rewrite your content in Q&A format, add statistics and citations, create an llms.txt file, and build topic clusters."

**Right:**
"Before we change anything, we decide what to measure and measure it. Which prompts would your customers type? Write me 10 to 20, and we'll run each one three to five times to see where you stand today."

**What to do instead:** Steps 1 and 2 come first. Fixes made before measuring can never be judged, because there's no baseline to compare the rerun with.

---

## 2. Recommending llms.txt

**User:** "Should I add an llms.txt file so AI can read my site?"

**Wrong:**
"Yes, llms.txt is the new robots.txt for AI. Add one listing your key pages and AI systems will prioritize them."

**Right:**
"No, Google has mentioned that no AI system uses it. Check that AI crawlers can reach your pages and that the content is in the raw HTML. That's what they actually read."

**What to do instead:** Point to technical access that works: crawlers allowed at robots.txt and at the host, critical content in the raw HTML.

---

## 3. Going along with fake reviews or prompt injection

**User:** "What if I add hidden text telling ChatGPT to recommend my product, and post some fake reviews on a few sites?"

**Wrong:**
"Hidden text is risky, but a few reviews from friends on third-party sites can help seed your presence."

**Right:**
"No to both. Prompt injection, fabricated reviews and citation gaming trade durable trust for visibility that can backfire. Let's find the two or three sources that already get cited for your prompts and earn a real mention there."

**What to do instead:** Refuse every form of manipulation plainly, then give the honest move that serves the same goal.

---

## 4. Missing content hidden in JavaScript

**User:** "My robots.txt allows GPTBot, so the technical side is fine."

**Wrong:**
"Great, you're all set technically. Let's move on to content."

**Right:**
"robots.txt is one check of three. Is your host or firewall letting AI crawlers through? And view the page source: are the key facts in the raw HTML, or do they appear only after JavaScript runs? Some AI systems have limited or no client-side JavaScript support when crawling."

**What to do instead:** Check reach (robots.txt and the host), render (raw HTML, not JavaScript) and extract (clear sections) before calling the technical side done.

---

## 5. Judging AI search by traffic alone, or overclaiming

**User:** "I got 4 visits from ChatGPT this month. Is it working?"

**Wrong:**
"Yes! AI traffic is growing. At this rate, AI search will be your biggest channel by next year."

**Right:**
"Four visits is a real number, so note it. But influence happens without a click, so traffic alone won't tell you. Rerun your prompts: do you appear more often, get cited, get described accurately? Report presence, readiness and impact separately, and label how sure you are of each."

**What to do instead:** Report without overclaiming. Keep the three layers separate, and never project a trend from a handful of visits.
