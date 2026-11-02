# Choose an Effective Visual — Examples

One running example, made up to show the moves. Priya leads customer support at a small software company. Each quarter she shows the head of operations a page of charts. This quarter she wants approval to hire two more people for the billing queue. Her data: tickets per month for the last 18 months, split across five product areas, and the median first-response time for each area last quarter and this quarter.

---

## Phase 1: Who and What

### Golden path

**User:** "The audience is Marcus, head of operations. He knows support well but not the per-area numbers. I need him to approve two hires for billing. He'll see it on a slide in our quarterly review, and I'll talk him through it. Data: monthly tickets by product area for 18 months, and first-response time by area for two quarters."

**Say something like:**
"Good. One person, one decision, a slide you'll talk through. So the chart has one job: make the case that billing needs two more people. Everything else on that slide is optional."

**Why it works:** The audience, the action and the setting are all known before any chart is mentioned, and the chart's one job is said out loud.

### Struggle: no point yet

**User:** "I'm not sure what I want him to do. I just want to show how support is going."

**Say something like:**
"Then let's find the point first. That's its own session: `big-idea-and-takeaway-title`. We'll get the one sentence this slide has to prove, and then come back and pick the chart. If we pick now, we'll end up showing all 18 months of everything."

**Why it works:** Choosing a chart without a point is the mistake this framework exists to stop. The hand-off names the sibling framework and says why.

---

## Phase 2: Name the Comparison

### Golden path

**Say something like:**
"You have two possible comparisons here. Tickets by month is over time. First-response time this quarter against last quarter is between two points. Since the ask is about billing getting slower while volume grew, I think the point is the two-point change in response time, with volume as support. Does that match?"

**User:** "Yes. Response time is what Marcus will care about."

**Why it works:** Both comparisons in the data are named, and the advisor picks the one that carries the ask instead of trying to show both on one chart.

### Edge case: dates in the data, but the point is categories

**User:** "Should the volume chart be over time? It's monthly data."

**Say something like:**
"Only if the trend matters to Marcus. If what matters is that billing has the most tickets this quarter, that's categories, and a sorted bar chart says it faster. What do you want him to notice: that billing grew, or that billing is biggest?"

**User:** "That it grew. It doubled while the others stayed flat."

**Why it works:** The advisor doesn't assume monthly data means a line graph. The user's answer picks the comparison.

---

## Phase 3: Pick the Chart

### Golden path

**Say something like:**
"For response time between two points, I'd use a slopegraph. Five product areas, a line for each from last quarter to this quarter, and billing's line will be the one that climbs. Elizabeth Ricks on our team uses a slopegraph when the 'so what?' is what changed, and that's your case.
Ruled out:
- Grouped bars, ten bars side by side, because Marcus would have to compare pairs of bars to find the change.
- A line over 18 months, because you only have two quarters of response times.
Does anything about Marcus change that?"

**Why it works:** One chart, one reason tied to the point, and two charts ruled out with a reason for each.

### Struggle: wants something unusual

**User:** "What about a radar chart? It'd show all five areas at once and look more interesting."

**Say something like:**
"Use something less familiar only when it reveals an insight that would otherwise be difficult to see. What would the radar show that the slopegraph can't? Here, nothing. Marcus would have to learn to read it while you're talking. The slopegraph shows billing climbing at a glance."

**Why it works:** The unfamiliar chart gets a fair test, one question about what it reveals, and loses on that test instead of on taste.

### Edge case: the pie question

**User:** "My manager says pie charts are always wrong. Should I never use one?"

**Say something like:**
"No. 'Nearly every graph has a perfect use case—including the pie.' If you wanted to show that billing is 40% of all tickets this quarter, a pie with billing colored and the rest gray could do it. It's the wrong chart for change over time, which is what you have."

**Why it works:** The advisor defends the pie where it fits, then explains why it doesn't fit this data. Soft on dogma, firm on the method.

---

## Phase 4: The Rules for That Chart

### Golden path (bar chart for ticket volume)

**User:** "For the volume support chart, I'll show this quarter's tickets by area as bars. My tool starts the axis at 400."

**Say something like:**
"Move it to zero. The length of the bar carries the value, so starting at 400 makes billing look five times bigger than it is. Alex Velez on our team has the other two rules: sort the bars by value, biggest first, since product areas have no natural order. And your labels, like 'Integrations and API', are long, so turn the bars horizontal."

**Why it works:** Each rule comes with its reason, and the team member who wrote it is credited by name.

### Struggle: wants the axis cut to show a small change

**User:** "If I start the bar axis at zero, the difference between areas looks tiny."

**Say something like:**
"Then a bar chart is telling the truth: the difference is small. If the small difference is the point, show the change itself, or use a dot plot, where the axis doesn't have to start at zero."

**Why it works:** The advisor won't bend the zero rule. It offers a chart where the user's goal is honest.

---

## Phase 5: Too Many Lines or Too Many Bars

### Golden path

**User:** "For the 18-month volume chart I had five lines, and they cross all over each other."

**Say something like:**
"That's a spaghetti graph. Two fixes. One: five small panels side by side, one area each, all with the same y-axis range so they compare honestly. Two: keep all five lines in gray and color only billing. Since your story is about billing, I'd do the second."

**User:** "Highlighting billing. The others can stay gray."

**Why it works:** Both spaghetti fixes are named, and the advisor picks one based on the story.

### Edge case: live dashboard

**User:** "This also goes on a dashboard where people pick their own product area."

**Say something like:**
"Then you can't know which line to highlight. Use panels, with the same y-axis on each, so whoever is looking can find their own area and compare it to the rest."

**Why it works:** The fix changes with the setting, because a dashboard viewer chooses what to look at.

---

## Phase 6: The Chart Decision

### Golden path

**Say something like:**
"Here's what we decided.
- **Audience and point:** Marcus, head of operations, who needs to approve two billing hires.
- **Comparison:** response time between two points, last quarter and this quarter.
- **Chart:** a slopegraph, five areas, because billing's climb is the point.
- **Ruled out:** grouped bars, because pairs are hard to compare; a radar, because it shows nothing the slopegraph doesn't.
- **Rules to follow:** label each area at the line's ends; for the volume bars, axis from zero, sorted, horizontal.
- **Too many series:** for the 18-month volume line, all gray with billing highlighted.
Next, run `declutter-and-focus` to clean up both charts and put the color on billing."

**Why it works:** One page with the decision, the reason, what lost and why, and the hand-off to the next framework.
