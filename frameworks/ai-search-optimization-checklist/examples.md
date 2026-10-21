# AI Search Optimization Checklist — Examples

One running example, made up to show the moves. A solo founder runs a small site, three months old, that sells a printable family camping planner for $12. One country, one language. They want parents to find it when they ask ChatGPT or Gemini how to plan a first camping trip with kids.

---

## Phase 1: Establish the prompts and journeys

### Golden path

**User:** "Learn: 'what do I need for a first camping trip with a toddler', 'is camping with a 2 year old a bad idea'. Compare: 'best camping checklist for families', 'printable vs app camping planner'. Choose: 'where can I buy a family camping planner'. I'll add more to get to 15."

**Say something like:**
"That's a real library. Conversational, across the journey, and most of them don't include your name, which is where you need to show up. Tag each one learn, compare or choose, and we'll measure."

**Why it works:** The prompts are the way parents ask out loud, they cover the whole decision, and they are small enough in number for one person to run.

### Struggle: keywords instead of prompts

**User:** "camping checklist, family camping, camping planner."

**Say something like:**
"Those are search keywords. How would a parent ask it out loud at 10pm before the trip? Write it the way they'd type it into ChatGPT."

**Why it works:** AI search behavior is long and conversational. Measuring keywords would miss how people actually ask.

---

## Phase 2: Measure your initial AI presence

### Golden path

**User:** "Ran 15 prompts, three times each, in ChatGPT and Gemini, over two days. I appear in 0 of 15. REI and a Reddit thread are cited in most. One parenting blog gets cited for the 'compare' prompts."

**Say something like:**
"That's the baseline. Zero is normal for a three-month-old site. The useful part is the sources: REI, Reddit, one parenting blog. That's the map for the next steps."

**Why it works:** It was measured before any change, run several times because answers vary, and it records the cited sources, which matter more than the zero.

### Struggle: wants to skip measuring

**User:** "I already know I'm not showing up. Can we just start fixing?"

**Say something like:**
"Then in a month you won't know if anything worked. Measure first. It takes an hour, and every later step is judged against it."

**Why it works:** Step 12 needs a baseline. Without step 2, a fix can't be kept, expanded, revised or stopped on evidence.

---

## Phase 4: Make priority pages retrievable and extractable

### Golden path

**User:** "robots.txt allows everything. But the planner's description and price only load from a JavaScript widget. In the page source, the product page is basically empty."

**Say something like:**
"There it is. A crawler that doesn't run JavaScript sees an empty page. Put the description, the price and what's inside the planner in the raw HTML. Then view source again to check."

**Why it works:** It checks render, not just robots.txt, and gives a test the founder can run alone: view source and search for the sentence that matters.

### Edge case: the host blocks AI bots

**User:** "robots.txt is fine, but my server logs show no visits from GPTBot at all, and my host has a 'bot protection' setting turned on."

**Say something like:**
"Check that setting. Hosts and firewalls can block AI crawlers even when robots.txt allows them. Turn off the block for the AI crawlers you want, then watch the logs."

**Why it works:** It looks past robots.txt to the infrastructure, which is where the block often is.

---

## Phase 5: Align your brand entity

### Golden path

**User:** "Home page says 'family camping planner.' My Instagram says 'outdoor adventures for little explorers.' Etsy listing says 'kids camping printable bundle.'"

**Say something like:**
"Three descriptions, so AI systems get three different answers about what you are. Pick one, put it in the fact sheet with today's date, and make every profile say it."

**Why it works:** Consistency is a check the founder can finish in an afternoon, and it removes confusion about what the brand is.

---

## Phase 7: Grow your third-party sources

### Golden path

**User:** "The Reddit thread cited most is r/camping 'first trip with kids'. People ask about checklists there every week."

**Say something like:**
"That's a source where you can earn a real mention. Answer questions there as a parent who's done it, say who you are, and link only when it helps the person asking. Do it for months, not once."

**Why it works:** It picks a source the baseline showed is cited, and the way in is honest participation, not seeding.

### Struggle: wants to fake it

**User:** "Could I just make a few accounts and recommend my planner in those threads?"

**Say something like:**
"No. That's a manufactured community signal. It trades durable trust for visibility that can backfire, and moderators and AI systems both catch it. Earn the mention or skip the source."

**Why it works:** It refuses manipulation plainly and gives the honest version of the same move.

---

## Phase 8 and 9: Steps that rarely apply

### Edge case: one country, one product

**User:** "I only sell in the US, in English. And I have one product."

**Say something like:**
"Then step 9 rarely applies, so we skip it. Step 8 does apply a little: make sure the price and what's included are the same on your page, your structured data and your Etsy listing. Five minutes."

**Why it works:** It scales the checklist to the site instead of running every step at enterprise depth.

---

## Phase 12: Run the loop

### Golden path

**User:** "Fixes are live: raw HTML, fact sheet, one comparison page. What now?"

**Say something like:**
"Set the date, four weeks out. Rerun the same 15 prompts, same two systems, three runs each, same window. Then for each fix: keep, expand, revise or stop. If the comparison page starts getting cited, expand it. If nothing moved, revise the hypothesis from step 3."

**Why it works:** The same protocol makes the rerun comparable with the baseline, and each action gets a decision based on what moved.
