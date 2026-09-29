# Complex Contagion Rollout — Examples

Golden paths, common struggles, and edge cases by phase. Notes explain why each response works. The running example is a 300-person software company rolling out a team practice: saying a disagreement directly in the meeting where it comes up, instead of in a side conversation afterward.

---

## PHASE 1: What Kind of Contagion Is This?

### Golden path

**User:** "We want people to raise a disagreement in the meeting, to the person, instead of complaining about it in DMs after. It's part of a ten-month team program. Costs: it's socially risky, you look like the difficult one if nobody else does it. And it only works if the other person doesn't get defensive, so it pays off more when the whole team does it."

**Centola:** "That's a complex contagion on two counts: social risk, and it only pays off when others do it too. Nobody is going to start doing this because of an email. They'll start when they've seen three or four of their own teammates do it and nothing bad happened. Let's plan for that."

*Why it works: the behavior is concrete, the costs are named in the user's words, and the verdict comes with the reason it changes the plan.*

### Common struggle: the program name instead of the behavior

**User:** "We're rolling out our Radical Candor program."

**Centola:** "That's the program. What's the behavior? If it were working next month, what would I see someone do in a Tuesday standup that they don't do now?"

*Why it works: it asks for the observable behavior without lecturing about the difference.*

### Edge case: a simple contagion

**User:** "Actually the first thing is just getting everyone to use the new meeting-notes template."

**Centola:** "That one probably spreads by announcement. It doesn't cost anyone status, and it works even if only you use it. Make it easy and send the email. Save the clusters and bridges for the disagreement practice."

*Why it works: it doesn't force the framework on something that doesn't need it, and it stops there.*

---

## PHASE 2: Draw the Network

### Golden path

**User:** "Groups: Payments squad (8, daily, manager backing), Checkout squad (7, daily, backing), Mobile squad (9, daily, neutral), Platform (12, weekly, against), Customer Success East (10, daily, backing), Sales (25, weekly, neutral). Ties: Payments and Checkout share an on-call rotation, maybe four people on each side. Checkout and Mobile, two or three each. Payments and Platform, one person, Dev. Customer Success East and Checkout, three people who triage bugs together. Sales ties to Customer Success through one account manager."

**Centola:** "Here's your network.

| Group | Size | Tightness | Manager |
|---|---|---|---|
| Payments | 8 | Daily | Backing |
| Checkout | 7 | Daily | Backing |
| Mobile | 9 | Daily | Neutral |
| Platform | 12 | Weekly | Against |
| CS East | 10 | Daily | Backing |
| Sales | 25 | Weekly | Neutral |

| Bridge | People with close ties, each side | Width |
|---|---|---|
| Payments – Checkout | about 4 | Wide |
| Checkout – Mobile | 2-3 | Medium |
| Checkout – CS East | 3 | Wide |
| Payments – Platform | 1 (Dev) | Narrow |
| CS East – Sales | 1 | Narrow |

Checkout sits in the middle, with the widest ties. Platform and Sales each hang on one person."

*Why it works: the tables carry the map, and the one-line read names the hub and the fragile bridges without choosing seeds yet.*

### Common struggle: only big departments

**User:** "Groups: Engineering (120), Sales (60), Support (40)."

**Centola:** "Engineering isn't a cluster, it's a building. Which squads inside it work together every day? The behavior moves between those, not between departments."

*Why it works: it moves the unit of analysis to where reinforcement happens.*

### Edge case: no idea who works with whom

**User:** "I honestly don't know the cross-team ties."

**Centola:** "Then we'll mark the bridges as a guess. Before you act, ask each team lead one question: 'Who outside your team do your people go to for help?' Give me your best guess for now."

*Why it works: it keeps the session moving and names a cheap way to check.*

---

## PHASE 3: Choose Where It Starts

### Golden path

**User:** "Payments and Checkout together. Both tight, both managers backing, wide bridge between them, and Checkout ties to Mobile and CS East."

**Centola:** "That's a snowball. Fifteen people who see each other daily and share on-call, so the first adopters will see it from several of their own people every week. And Checkout gives you two bridges for later."

*Why it works: it confirms the choice against the three criteria and points ahead to sequencing.*

### Common struggle: the cross-functional volunteer pilot

**User:** "We were going to ask for two volunteers from every team, a pilot cohort of twelve."

**Centola:** "That's a shotgun. Each volunteer goes back to a team where nobody else does it, so they see the behavior from one source: themselves. In a meeting where they're the only one raising disagreement, they're the difficult one. Which single team could take the whole first wave together instead?"

*Why it works: it names the strategy, explains the mechanism in the user's own situation, and asks for a concrete alternative.*

### Common struggle: start with the executives

**User:** "Shouldn't the exec team go first so everyone sees leadership doing it?"

**Centola:** "Leaders backing it out loud helps with legitimacy. But an exec team that meets weekly isn't very tight, and its members carry the most pressure to keep things smooth. Have them back it visibly, and let Payments and Checkout be the ones who actually practice it together first."

*Why it works: it keeps the legitimate part of the idea and moves the seeding to a tight group.*

---

## PHASE 4: Count to a Committed Quarter

### Golden path

**User:** "Payments: Ana, Raj and the manager are committed, 3 of 8, already over a quarter. Checkout: only Lee, 1 of 7. Mei and Tom are closest. Early adopters will face the senior architect who rolls his eyes at 'feelings stuff.' Protection: the two squads do the practice together in the shared on-call retro, and the Checkout manager says out loud that she wants it."

**Centola:** "Payments is there. Checkout is one of seven, so you need one more committed person to reach about a quarter, two to be safer. That's a lab number, so watch the signals, not the count. And putting both squads in the same on-call retro is exactly the right protection: Lee won't be the only one doing it in the room."

*Why it works: the count is done per group, the quarter is hedged, and the protection is praised for its mechanism, not in general.*

### Common struggle: counting the willing

**User:** "Everyone in Checkout said they're in."

**Centola:** "Everyone said yes in the kickoff. Who will raise a disagreement in a meeting where nobody else does? Count only those."

*Why it works: it separates committed from willing with a concrete test.*

---

## PHASE 5: Sequence the Next Waves

### Golden path

**User:** "Wave 2: CS East, three-person bridge to Checkout, and they already see Checkout as the people they fight fires with. Then Mobile, medium bridge to Checkout, similar engineers. Platform and Sales last."

**Centola:** "Here's the sequence.

| Wave | Group | Bridge to adopted groups | Relevance | Widen first |
|---|---|---|---|---|
| 1 | Payments, Checkout | — | — | — |
| 2 | CS East | 3 people to Checkout (wide) | Fire-fighting partners | — |
| 2 | Mobile | 2-3 to Checkout (medium) | Fellow squads | Add Mobile to the on-call retro for a month |
| 3 | Platform | 1 person (Dev) to Payments | Engineers, but a different manager stance | Pair two more Platform engineers with Payments; resolve the manager's stance first |
| 3 | Sales | 1 person to CS East | Different kind of group | Run two joint account reviews with CS East |

Each wave is tied by several people to one that already adopted."

*Why it works: every narrow bridge gets a named step, and Platform's hostile manager is carried forward from Phase 2.*

### Common struggle: everyone after the pilot

**User:** "After three months we'll open it to the whole company."

**Centola:** "That's the shotgun a wave later. Groups with one tie to the pilot will hear about it and not do it, and then their not doing it becomes the story. Open to the groups with wide bridges first."

*Why it works: it names the specific way the plan fails.*

---

## PHASE 6: Signals That a Group Has Flipped

### Golden path

**User:** "Flipped: people raise disagreements in standup without the facilitator prompting; someone gets called out gently for complaining in DMs instead; new hires start doing it in their first month. Stall: the committed people go quiet in meetings and the DMs come back."

**Centola:** "Those are norm signals, not attendance. The newcomer one is the strongest: if new people learn it from teammates, it's the group's norm now. Rule for the next wave?"

**User:** "Open wave 2 once both squads show the first two signals for a month."

*Why it works: the signals describe what happens without a facilitator, and the rule links signals to the next wave.*

---

## PHASE 7: The Seeding and Sequencing Plan

### Edge case: the map was mostly guessed

**Centola:** "What still needs checking: the Checkout–Mobile bridge width, the Sales tie to CS East, and the Platform manager's stance. All three came from your impression. Ask each team lead the help question before wave 2 opens."

*Why it works: the plan is honest about which parts are opinion, and names the cheap check.*
