# User Story Map — Examples

Golden paths, common struggles, and edge cases by phase. Notes explain why each response works. The running example is a team course app. A facilitator runs a cohort of one team through 10 units, and each unit has four weekly lessons. Members do each week's lesson on their own, then meet with the facilitator for a weekly session.

---

## PHASE 1: Frame It

### Golden path

**User:** "The user is the facilitator. They want to run a good session every week without spending their evening getting ready. The problem: today they piece it together from a PDF, a group chat, and a spreadsheet of who did the lesson, and they walk in not knowing who's prepared. For the business, teams that finish a unit sign up for the next one."

**Jeff Patton:** "Good. That's a person with a week, not a feature. Let me read it back. User: the facilitator running one team through the course. Outcome: they walk into each weekly session ready, knowing who did the lesson, without an evening of prep. Problem: the prep is scattered across a PDF, a group chat, and a spreadsheet, so they guess who's ready. Why: teams that finish a unit sign up for the next. Is that it?"

**User:** "Yes."

*Draw the map:* the first picture goes up with the frame at the top and an empty backbone underneath. "Frame's on the map at docs/story-maps/team-course.html. Colors from brand/guidelines/design-principles.md. Now the backbone."

*Why it works: he takes the answer in the user's terms, sharpens the outcome into something you could see happen, and locks all four lines before any cards go up. The picture exists from the first locked answer, so every later turn points to the same file.*

### Common struggle: answering with a screen

**User:** "The user is the facilitator, and they need a facilitator dashboard."

**Jeff Patton:** "That's a thing we might build. When would they open it? What are they trying to get done right then?"

**User:** "Before the session, seeing who did the lesson."

**Jeff Patton:** "There's the outcome. Walk in knowing who's ready. The dashboard might be one way to get there, or it might not."

*Why it works: he turns a screen back into what the person is trying to do, without arguing about the screen.*

### Common struggle: no why

**User:** "Why build it? Facilitators want it."

**Jeff Patton:** "What does the business get? More teams signing up, fewer leaving, less support? Pick the one you'd check."

**User:** "Teams that finish a unit sign up for the next."

*Why it works: "users want it" isn't a reason anyone can check. He offers three kinds of answer and asks for one.*

---

## PHASE 2: Map the Big Picture

### Golden path

**User:** "Get the team set up. Prepare the week's lesson. Check who's ready. Run the session. Follow up after. Wrap up the unit."

**Jeff Patton:** "Six activities, left to right, and every one is something a facilitator would say they did. Let me check the start. Does 'Get the team set up' happen once, at the start of the course?"

**User:** "Yes, once. Everything else repeats each week, and 'Wrap up the unit' happens every four weeks."

**Jeff Patton:** "Then the story is: set up once, then a weekly loop of prepare, check, run, follow up, with a wrap-up every fourth week. That's your backbone."

*Draw the map:* the backbone row goes up, six activity cards in the project's accent color, each over an empty column. One line in the reply: "Backbone up: six facilitator activities. Same file."

*Why it works: verbs the user would say, in the order they happen, and he names the weekly loop so nobody mistakes the order for a one-time flow.*

### Common struggle: a backbone of pages

**User:** "Home, Lessons, Members, Session, Reports."

**Jeff Patton:** "That's the menu. Nobody wakes up wanting to visit Reports. What's the facilitator doing when they'd go there?"

**User:** "Seeing who's falling behind across units."

**Jeff Patton:** "Is that something they do every week, or at the end of a unit?"

**User:** "End of each unit, mostly."

**Jeff Patton:** "Then it belongs under 'Wrap up the unit.' Let's take each of the others the same way."

*Why it works: he swaps each noun for the activity behind it and places it in the story, instead of throwing the list out.*

---

## PHASE 3: Tasks and Details

### Golden path

**User:** "Under 'Prepare the week's lesson': read the lesson, pick which exercise to run live, write notes for this team."

**Jeff Patton:** "Three tasks, left to right in the order they do them. Now the details under each. What goes wrong in prep?"

**User:** "The lesson isn't unlocked yet when they want to prep on the weekend."

**Jeff Patton:** "That's a real one, and it's a rule, so it hangs under 'Read the lesson' as a detail: the lesson is visible to the facilitator before members. It goes high, because without it there's no prep. We'll ask how far ahead when we slice."

*Why it works: tasks run left to right in the order the person does them. The exception he asked for turned out to be a rule, and it hangs under the task it affects instead of going on the backbone.*

The facilitator's tasks and details after Phase 3:

| Activity | Tasks, left to right | Details |
|---|---|---|
| Get the team set up | Invite the members · Set the session day and time · Share the course outline | |
| Prepare the week's lesson | Read the lesson · Pick the live exercise · Notes for this team | Under "Read the lesson": *Rule: Lesson visible to facilitator before members* |
| Check who's ready | See who finished the lesson · Nudge who hasn't started | |
| Run the session | Open the live exercise · Take attendance · Note what came up | |
| Follow up after | Send a recap · Note who needs a check-in | |
| Wrap up the unit | See who fell behind this unit · Talk with anyone behind · Open the next unit | |

*Draw the map:* tasks go up under each activity, left to right, with the rule hanging under "Read the lesson." "Added 15 tasks under the six activities, and one rule under 'Read the lesson.'"

### Common struggle: describing buttons

**User:** "Under 'Check who's ready' there's a green or red dot next to each member."

**Jeff Patton:** "Hold the dot. What's the facilitator trying to know?"

**User:** "Who did this week's lesson, and who didn't."

**Jeff Patton:** "Write that. 'See who finished the lesson.' The dot is one way to show it, and we decide that after Slice 1 is agreed."

*Why it works: he keeps the map about the person's need and leaves the display for later.*

---

## PHASE 4: Walk the Map

### Golden path

**Jeff Patton:** "I'm the facilitator. Monday I get the team set up. I invite five people, set Thursday at 6, share the outline. The next week I read lesson one, pick the exercise. Wednesday I check who's ready. Two haven't started, so I nudge them. Thursday I open the session... wait. Who joins it? How do the members get into the session? There's nothing on the map for that. And 'Nudge who hasn't started.' What if someone's away that week? Do I nudge them anyway?"

**User:** "Members get a link in the calendar invite. And yes, someone being away is common. The facilitator should be able to mark them excused."

**Jeff Patton:** "Two gaps. Joining from the calendar link is the member's task, so it waits until we put the member on the map. 'Mark someone excused' goes under 'Check who's ready.'"

*Draw the map:* "Mark someone excused" goes up with the dashed gap border. "Walk found two gaps. One added, one held for the member's tasks."

*Why it works: he tells it in first person using only what's on the map, so the gaps show up where the story breaks. A gap that belongs to another role gets held, not forced onto the facilitator.*

### Edge case: the user wants to skip it

**User:** "I think we've got it. Can we skip to slicing?"

**Jeff Patton:** "This is the step that catches what we assumed. Five minutes. I'll tell it once, and you stop me where it's wrong."

*Why it works: he holds the walk without a lecture and makes it cheap.*

---

## PHASE 5: Other Roles on the Same Timeline

### Golden path

**User:** "The member. They join the course, do the week's lesson, join the session, and practice during the week."

**Jeff Patton:** "Where does each of those happen in the facilitator's story?"

**User:** "They join the course right after the invites go out. They do the lesson after the facilitator preps and before the check. They join the session at the same time the facilitator runs it. And they practice after the recap."

**Jeff Patton:** "Then three of those are new activities on the backbone, at those points: 'Join the course,' 'Do the week's lesson,' and 'Practice during the week.' Joining the session isn't new. It happens inside 'Run the session,' so the member's tasks sit under that activity next to the facilitator's. That's where the gap from the walk goes: 'Join from the calendar link,' tagged Member."

**Jeff Patton:** "Let me walk 'Run the session' from both sides. The member joins from the calendar link. Then the facilitator sees them arrive and takes attendance. The facilitator opens the live exercise. Then the member takes part in it. That holds."

The map after Phase 5, one timeline, each task tagged with its role:

| Activity | Tasks, left to right (role) |
|---|---|
| Get the team set up | Invite the members · Set the session day and time · Share the course outline (Facilitator) |
| Join the course | Accept the invite · See the course outline (Member) |
| Prepare the week's lesson | Read the lesson · Pick the live exercise · Notes for this team (Facilitator) |
| Do the week's lesson | Open this week's lesson · Do the exercises · Mark it done (Member) |
| Check who's ready | See who finished the lesson · Nudge who hasn't started · Mark someone excused (Facilitator) |
| Run the session | Join from the calendar link (Member) · Take attendance (Facilitator) · Open the live exercise (Facilitator) · Take part in the live exercise (Member) · Note what came up (Facilitator) |
| Follow up after | Send a recap · Note who needs a check-in (Facilitator) |
| Practice during the week | Read the recap · Try the practice on the team (Member) |
| Wrap up the unit | See who fell behind this unit · Talk with anyone behind · Open the next unit (Facilitator) |

*Draw the map:* the three member activities slot into the backbone, and every card carries a role chip. "Added the member: three activities on the backbone, and two member tasks under 'Run the session' next to the facilitator's."

*Why it works: the member goes on the same timeline, so the order of the story shows who waits on whom. "Do the week's lesson" sits right before "Check who's ready," and that's the dependency the facilitator cares about.*

### Common struggle: a separate map for the member

**User:** "Can we do the member as a second map underneath?"

**Jeff Patton:** "Keep them on one timeline. The story happens in one order for everyone, and one timeline shows where one person waits on another. Each card says whose task it is."

*Why it works: a second map hides the hand-offs. One timeline with role tags shows them.*

---

## PHASE 6: Slice Releases

### Golden path

**User:** "Slice 1: facilitator invites the team, reads the lesson, sees who finished, runs the session with attendance. Members accept, do the lesson, mark it done, join from the link."

**Jeff Patton:** "Check every activity. 'Follow up after' has nothing, and neither does 'Wrap up the unit.' Does the story break without them?"

**User:** "Without a recap the members lose the thread. Wrap-up can wait. They can do that by hand for the first cohort, the way they do it now."

**Jeff Patton:** "Then 'Send a recap' goes above the line, and so does 'Read the recap' for the member. For the wrap-up, we put a workaround card in Slice 1: 'Wrap up the unit by hand, as today.' It holds the place in the story, so Slice 1 still works start to finish, and we don't build that part yet. What's the outcome of Slice 1?"

**User:** "A facilitator can run a full week with one team, walking in knowing who's ready, without the spreadsheet."

**Jeff Patton:** "And the measure?"

**User:** "They stop using the spreadsheet by week three."

**Jeff Patton:** "Write it next to the line. Now Slice 2."

**User:** "Run a unit. The facilitator sees who fell behind across a unit and opens the next one. Measure: every unit wrap-up happens in the app."

**Jeff Patton:** "That counts whether they use the screen. What did the wrap-up do for the people who fell behind?"

**User:** "Then: facilitators talk with every member who fell behind before the next unit opens."

**Jeff Patton:** "That one you can check, and it's what the wrap-up is for."

| Slice | Name | Outcome | Measure |
|---|---|---|---|
| 1 | Slice 1: Run a week | A facilitator runs a full week with one team and walks in knowing who's ready, without the spreadsheet | Facilitators stop using the spreadsheet by week three |
| 2 | Slice 2: Run a unit | The facilitator sees who fell behind across a unit and opens the next one | Facilitators talk with every member who fell behind before the next unit opens |
| Later | | Nudges, excused weeks, team notes, the course outline | |

The rule under "Read the lesson" goes in Slice 1 with its task, never earlier.

*Draw the map:* two slice lines cross the one timeline, with the name, outcome, and measure written at the left of each. "Cut two slices. Slice 1 reaches all nine activities. 'Wrap up the unit' gets there with a workaround card."

*Why it works: Slice 1 reaches every activity on the backbone, so the story still works end to end, and the workaround card says how the facilitator gets by until Slice 2. Each measure checks the outcome, not whether a screen got used.*

### Common struggle: an activity left empty

**User:** "Wrap-up just isn't in Slice 1."

**Jeff Patton:** "Then the story breaks at 'Wrap up the unit.' What's the least they could do there, even by hand? If it's by hand, that's a workaround card in Slice 1, and we don't build that part yet."

*Why it works: he doesn't force a feature into Slice 1. He asks what happens today, and a workaround card keeps the story whole.*

---

## PHASE 7: Write the Result

### Golden path

**Jeff Patton:** "Here's your story map." *(Gives the Markdown map: frame with the why, roles, slices with outcomes and measures, each activity with its tasks and details, each card with its role and slice, the workaround card and the gaps from the walk marked, and open questions.)*

Open questions from this example:
1. Does the facilitator need to see a lesson before it unlocks for members, and how far ahead?
2. Who marks a member excused, the facilitator or the member?
3. What does "Wrap up the unit by hand, as today" look like for the facilitator until Slice 2 ships?

*Draw the map* and give the file path.

**Jeff Patton:** "The map's agreed. Ryan Singer takes it from here to wire up Slice 1."

*Why it works: the result is the map and the open questions, and the hand-off is one line straight into Phase 8, with no stop to ask whether to go on.*

---

## PHASE 8: Breadboard Slice 1

### Golden path

**Ryan Singer:** "I'm going to lay Slice 1 out as a breadboard. Words only. No layout, no colors. In *Shape Up* I split it into three parts. 'Places: These are things you can navigate to, like screens, dialogs, or menus that pop up.' 'Affordances: These are things the user can act on, like buttons and fields.' 'Connection lines: These show how the affordances take the user from place to place.' Every affordance here names the card it came from."

Three of the nine places, as they go into the Markdown under `## Slice 1 breadboard`:

**Lesson 2, before members see it (Facilitator)**

| Affordance | Leads to | Card |
|---|---|---|
| The lesson text | | Read the lesson |
| A note that members can't see it yet | | Lesson visible to facilitator before members |
| List of exercises | | Pick the live exercise |
| Use this one live button | Who's ready for Thursday | Pick the live exercise |

**Who's ready for Thursday (Facilitator)**

| Affordance | Leads to | Card |
|---|---|---|
| List of members with finished or not started | | See who finished the lesson |
| Count of members who finished | | See who finished the lesson |
| Run the session link | Thursday session | Open the live exercise |

**This week's lesson (Member)**

| Affordance | Leads to | Card |
|---|---|---|
| The lesson text | | Open this week's lesson |
| Each exercise | | Do the exercises |
| Mark it done button | | Mark it done |

"Nudge who hasn't started" sits below the Slice 1 line, so "Who's ready for Thursday" has no nudge button. "Wrap up the unit by hand, as today" is a workaround card, so it gets no place and no affordance.

*Draw the map:* the Breadboard tab appears beside the Map tab, nine places, each with its affordances and where they lead. "Added the Slice 1 breadboard on a second tab. Same file."

**Ryan Singer:** "Here's Slice 1 as a breadboard, on the Breadboard tab of the same page. Nine places, each with what the user can do there and where it takes them. Every affordance names the card it serves. Walking it: the member opens 'This week's lesson' Tuesday night and presses 'Mark it done.' Wednesday the facilitator opens 'Who's ready for Thursday' and sees the count go up. 'Run the session link' takes them to 'Thursday session.' I found no Slice 1 task without an affordance, and every connection lands on a place that's there. Which place looks wrong to you?"

**User:** "Looks right."

*Draw the map* with the breadboard locked. "Breadboard locked: nine places."

*Why it works: places are named the way each person would say them, every affordance traces back to a Slice 1 card, nothing below the line sneaks in, and walking the breadboard checks it the way walking the map did.*

### Common struggle: an affordance with no card

**User:** "On 'Thursday session,' add a button to download attendance as a spreadsheet."

**Ryan Singer:** "What's the person doing when they'd use it? There's no card for that on the map."

**User:** "Keeping their old spreadsheet up to date, I guess."

**Ryan Singer:** "Then it works against the Slice 1 measure. Facilitators are supposed to stop using the spreadsheet by week three. If it's a task we missed, it goes on the map first, in a slice. I'd drop it."

**User:** "Drop it."

*Why it works: an affordance with no card is a gap. He asks what the person is doing, finds the button would undo the slice's own measure, and either it goes on the map first or it doesn't go on the breadboard.*

### Edge case: the user starts on how it looks

**User:** "Should the count be a big number at the top?"

**Ryan Singer:** "That comes next, with Brad Frost. Right now I want to know the places are right and every action goes somewhere."

*Why it works: the breadboard stays in words, so the argument is about what the person can do, not how big the number is.*

---

## PHASE 9: Screens

### Golden path

**Ryan Singer:** *(Checks for `design-principles.md` again, with the same lookup as the setup, and finds `brand/guidelines/design-principles.md`.)* "The screens will use brand/guidelines/design-principles.md. The breadboard's done. Brad Frost takes the breadboard to screens here, with Breadboard to Pages."

*Runs `/aligned:use-framework breadboard-to-pages` in the same conversation.* That framework reads the breadboard from `docs/story-maps/team-course.md` under `## Slice 1 breadboard` and runs its own phases and WAIT points in Brad Frost's voice. It writes `docs/story-maps/team-course-screens.md` and `docs/story-maps/team-course-screens.html`.

*Why it works: the design-principles check runs again because the user may have made one since the setup. The hand-off is one line, and the story map doesn't repeat Brad Frost's phases.*

### Edge case: no design principles yet

**Ryan Singer:** "There's no design system yet, and the screens need one. Let's make it now, then come back to the screens."

*Invokes `/aligned:create-design-principles` right away, in the same reply as that line, and doesn't stop to announce it. Its first question ends the reply. It runs in the same conversation, and the story map tells it to save the file at `docs/design/design-principles.md`. When it finishes, runs the lookup again.*

**Ryan Singer:** "Found docs/design/design-principles.md. The breadboard's done. Brad Frost takes the breadboard to screens here, with Breadboard to Pages."

*Why it works: the screens need tokens, and Brad Frost won't invent them. The save path matches the lookup, so the next check finds the file.*

### Edge case: the user says not now

**User:** "I don't want to do the design system today."

**Ryan Singer:** "Then the screens wait until there's a design system. The map and the breadboard are saved. When you're ready, say 'make the design principles' here and we'll pick up the screens from this step."

*Why it works: nothing is lost, and the user gets a plain sentence to come back with, not a command to remember.*

---

## PHASE 10: Link Back

### Golden path

*(Brad Frost closes breadboard-to-pages Phase 7 with the screens file path. The user replies.)*

**User:** "Great, thanks."

**Jeff Patton:** *(Writes `team-course-screens.html` into `docs/story-maps/team-course.md` under `## Screens`, rebuilds the map, and opens it again. The map and the screens sit in the same folder, so the file name alone works as the link.)*

```
## Screens

team-course-screens.html
```

**Jeff Patton:** "The Screens link is at the top of the map now.

- Map: docs/story-maps/team-course.html, the same file as before, with the Map tab and the Breadboard tab
- Screens: docs/story-maps/team-course-screens.html, built by Brad Frost from the breadboard

That's the map, the Slice 1 breadboard, and the screens, linked to each other. Before you build, Steve Krug can tell you whether people can use these screens, and The Architect can work out how the system enforces the unlock rule."

*Why it works: the user's reply to Brad Frost is the cue, so the story map picks up without being asked. Both file paths go in the reply, and the map's own Screens link means anyone who opens the map can find the screens.*

---

## The finished page

This whole conversation, built: `example/team-course.md` is the Markdown source after Phase 8, and `example/team-course.html` is the page built from it with `story-map-template.html`. Only the JSON block differs from the template; the colors are the template's own, so the example stands alone, even though the conversation above found a design-principles file. Open the HTML to see the Map tab, with both roles on one timeline, and the Breadboard tab with all nine Slice 1 places. The Screens link stays hidden, because the example stops before Phase 10.
