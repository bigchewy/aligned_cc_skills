# User Story Map — Examples

Golden paths, common struggles, and edge cases by phase. Notes explain why each response works. The running example is a team course app. A facilitator runs a cohort of one team through 10 units, and each unit has four weekly lessons. Members do each week's lesson on their own, then meet with the facilitator for a weekly session.

---

## PHASE 1: Frame It

### Golden path

**User:** "The user is the facilitator. They want to run a good session every week without spending their evening getting ready. The problem: today they piece it together from a PDF, a group chat, and a spreadsheet of who did the lesson, and they walk in not knowing who's prepared."

**Jeff Patton:** "Good. That's a person with a week, not a feature. Let me read it back. User: the facilitator running one team through the course. Outcome: they walk into each weekly session ready, knowing who did the lesson, without an evening of prep. Problem: the prep is scattered across three tools, so they guess who's ready. Is that it?"

**User:** "Yes."

*Draw the map:* the first picture goes up with the frame at the top and an empty backbone underneath. "Frame's on the map, at this link. Colors from brand/guidelines/design-principles.md. Now the backbone."

*Why it works: he takes the answer in the user's terms, sharpens the outcome into something you could see happen, and locks it before any cards go up. The picture exists from the first locked answer, so every later turn has a link.*

### Common struggle: answering with a screen

**User:** "The user is the facilitator, and they need a facilitator dashboard."

**Jeff Patton:** "That's a thing we might build. When would they open it? What are they trying to get done right then?"

**User:** "Before the session, seeing who did the lesson."

**Jeff Patton:** "There's the outcome. Walk in knowing who's ready. The dashboard might be one way to get there, or it might not."

*Why it works: he turns a screen back into what the person is trying to do, without arguing about the screen.*

---

## PHASE 2: Map the Big Picture

### Golden path

**User:** "Get the team set up. Prepare the week's lesson. Check who's ready. Run the session. Follow up after. Wrap up the unit."

**Jeff Patton:** "Six activities, left to right, and every one is something a facilitator would say they did. Let me check the start. Does 'Get the team set up' happen once, at the start of the course?"

**User:** "Yes, once. Everything else repeats each week, and 'Wrap up the unit' happens every four weeks."

**Jeff Patton:** "Then the story is: set up once, then a weekly loop of prepare, check, run, follow up, with a wrap-up every fourth week. That's your backbone."

*Draw the map:* the backbone row goes up, six activity cards in the project's accent color. One line in the reply: "Backbone up: six facilitator activities. Same link."

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

## PHASE 3: Steps and Details

### Golden path

**User:** "Under 'Prepare the week's lesson': read the lesson, pick which exercise to run live, note anything to watch for with this team."

**Jeff Patton:** "Top to bottom, which can't they skip?"

**User:** "Reading the lesson. Picking the exercise. The notes are nice to have."

**Jeff Patton:** "So the notes go lower. Exceptions? What goes wrong in prep?"

**User:** "The lesson isn't unlocked yet when they want to prep on the weekend."

**Jeff Patton:** "That's a real one, and it's a rule, so it hangs under 'Read the lesson' as a detail. Facilitator needs to see the lesson before members can. We'll ask whether that's true when we slice."

*Why it works: priority by importance, an exception found by asking, and a system rule placed under the step it affects instead of on the backbone.*

The steps after Phase 3, facilitator lane:

| Get the team set up | Prepare the week's lesson | Check who's ready | Run the session | Follow up after | Wrap up the unit |
|---|---|---|---|---|---|
| Invite the members | Read the lesson | See who finished the lesson | Open the live exercise | Send a recap | See who fell behind this unit |
| Set the session day and time | Pick the live exercise | Nudge who hasn't started | Take attendance | Note who needs a check-in | Talk with anyone behind |
| Share the course outline | Notes for this team | | Note what came up | | Open the next unit |
| | *Detail: lesson visible to facilitator before members* | | | | |

*Draw the map:* steps go up under each activity, top to bottom. "Added 15 steps under the six activities."

### Common struggle: describing buttons

**User:** "Under 'Check who's ready' there's a green or red dot next to each member."

**Jeff Patton:** "Hold the dot. What's the facilitator trying to know?"

**User:** "Who did this week's lesson, and who didn't."

**Jeff Patton:** "Write that. 'See who finished the lesson.' The dot is one way to show it, and the wireframes will decide that."

*Why it works: he keeps the map about the person's need and leaves the display for later.*

---

## PHASE 4: Walk the Map

### Golden path

**Jeff Patton:** "I'm the facilitator. Monday I get the team set up. I invite five people, set Thursday at 6, share the outline. The next week I read lesson one, pick the exercise. Wednesday I check who's ready. Two haven't started, so I nudge them. Thursday I open the session... wait. Who joins it? How do the members get into the session? There's nothing on the map for that. And 'Nudge who hasn't started.' What if someone's away that week? Do I nudge them anyway?"

**User:** "Members get a link in the calendar invite. And yes, someone being away is common. The facilitator should be able to mark them excused."

**Jeff Patton:** "Two gaps. 'Members join the session' belongs to the member, so it waits for their lane. 'Mark someone excused' goes under 'Check who's ready.' Who else should hear this walk? Is there a facilitator who runs this today, on the PDF and the spreadsheet?"

*Draw the map:* "Mark someone excused" goes up with the dashed gap border. "Walk found two gaps. One added, one held for the member lane."

*Why it works: he tells it in first person using only what's on the map, so the gaps show up where the story breaks, and he asks for someone who does the job today.*

### Edge case: the user wants to skip it

**User:** "I think we've got it. Can we skip to slicing?"

**Jeff Patton:** "This is the step that catches what we assumed. Five minutes. I'll tell it once, and you stop me where it's wrong."

*Why it works: he holds the walk without a lecture and makes it cheap.*

---

## PHASE 5: Explore Other Users

### Golden path

**User:** "The member: Join the course. Do the week's lesson. Join the session. Practice during the week."

**Jeff Patton:** "Where do their stories touch?"

**User:** "When the member does the lesson, the facilitator sees it in 'Check who's ready.' And the facilitator's recap lands in the member's week."

**Jeff Patton:** "And the gap from the walk, members joining the session, is in their lane now. Let me walk the touch points from both sides. The member finishes lesson two Tuesday night. Wednesday the facilitator sees it. Thursday the member joins from the calendar link, and the facilitator takes attendance. Friday the recap arrives and the member practices with it. That holds."

The member lane:

| Join the course | Do the week's lesson | Join the session | Practice during the week |
|---|---|---|---|
| Accept the invite | Open this week's lesson | Join from the calendar link | Read the recap |
| See the course outline | Do the exercises | Take part in the live exercise | Try the practice on the team |
| | Mark it done | | |

Touch points: "Do the week's lesson" ↔ facilitator "Check who's ready." "Join the session" ↔ facilitator "Run the session." Facilitator "Follow up after" ↔ member "Practice during the week."

*Draw the map:* the member lane appears below the facilitator lane, each touch point marked on both cards. "Added the member lane and three places their stories touch."

*Why it works: a lane per role, only as deep as it needs to be to show the touch points, and the touch points get walked from both sides.*

---

## PHASE 6: Slice Releases

### Golden path

**User:** "Slice 1: facilitator invites the team, reads the lesson, sees who finished, runs the session with attendance. Members accept, do the lesson, mark it done, join from the link."

**Jeff Patton:** "Check every activity. 'Follow up after' has nothing, and neither does 'Wrap up the unit.' Does the story break without them?"

**User:** "Without a recap the members lose the thread. Wrap-up can wait. They can do that by hand for the first cohort."

**Jeff Patton:** "Then 'Send a recap' goes above the line, even if it's just a text box. Wrap-up stays below for now, done by hand. What's the outcome of Slice 1?"

**User:** "A facilitator can run a full week with one team, walking in knowing who's ready, without the spreadsheet."

**Jeff Patton:** "And the measure?"

**User:** "They stop using the spreadsheet by week three."

**Jeff Patton:** "Write it next to the line."

| Slice | Outcome | Measure |
|---|---|---|
| Slice 1: Run a week | A facilitator runs a full week with one team and walks in knowing who's ready, without the spreadsheet | Facilitators stop using the spreadsheet by week three |
| Slice 2: Run a unit | The facilitator sees who fell behind across a unit and opens the next one | Every unit wrap-up happens in the app |
| Later | Nudges, excused weeks, team notes | |

*Draw the map:* two dashed slice lines cross both lanes, with the outcome written at the left of each. "Cut two slices. Slice 1 reaches every facilitator and member activity except Wrap up the unit, which is done by hand for now."

*Why it works: Slice 1 reaches across the whole backbone, so the story still works end to end, and each slice is named by what someone can do after it.*

---

## PHASE 7: Write the Result

### Golden path

**Jeff Patton:** "Here's your story map." *(Gives the Markdown map: frame, both lanes, steps with their slices, touch points, slices with outcomes and measures, and open questions.)*

Open questions from this example:
1. Does the facilitator need to see a lesson before it unlocks for members, and how far ahead?
2. Who marks a member excused, the facilitator or the member?
3. What does the facilitator do by hand to wrap up a unit until Slice 2 ships?

*Draw the map* and give the link.

**Jeff Patton:** "The map's agreed. Now we sketch Slice 1, one screen per activity, using the words already on the cards. Same page, second tab."

*Why it works: the result is the map and the open questions, and it moves straight into the Slice 1 wireframes instead of stopping at "ready for wireframes."*

---

## PHASE 8: Wireframe Slice 1

### Golden path

Slice 1 reaches nine activities: five in the facilitator lane (everything but "Wrap up the unit") and all four in the member lane. That makes nine wireframes. Two of them, as they go into the Markdown:

**Facilitator: Check who's ready**

| Element | Text | Card |
|---|---|---|
| Heading | Who's ready for Thursday | Check who's ready |
| List, one row per member | Name, and "Finished lesson 2" or "Not started" | See who finished the lesson |
| Detail under the list | "3 of 5 finished" | See who finished the lesson |
| Link to the next screen | Run the session | Run the session |

**Member: Do the week's lesson**

| Element | Text | Card |
|---|---|---|
| Heading | This week: Lesson 2 | Open this week's lesson |
| Lesson body and exercises | The lesson text, then each exercise | Do the exercises |
| Main button | Mark it done | Mark it done |

"Nudge who hasn't started" sits below the Slice 1 line, so the readiness list has no nudge button.

*Draw the map:* the Wireframes tab appears beside the Map tab, nine sketches in the project's colors, each box labeled with its card. "Added nine Slice 1 wireframes on a second tab. Same link."

**Jeff Patton:** "Here's Slice 1 as screens, on the Wireframes tab of the same link. Every box names the card it came from. Walking it: I'm the member, Tuesday night, I mark lesson 2 done. Wednesday the facilitator opens 'Who's ready for Thursday' and sees me in the finished rows. Thursday they run the session and take attendance. Friday the recap lands and I read it. One hole: on 'Run the session,' the facilitator needs the exercise they picked during prep, and nothing on that screen shows it. The card exists, 'Pick the live exercise,' so the screen needs a box for it. Which screen looks wrong to you?"

**User:** "Can we put a message button next to each member who hasn't started?"

**Jeff Patton:** "That's 'Nudge who hasn't started,' and it's below the Slice 1 line. If it belongs in Slice 1, move the card up on the map first, then it goes on the screen. Does it?"

**User:** "No, it can wait. Add the exercise to the session screen."

*Draw the map* one last time with both tabs. "Added the picked exercise to 'Run the session.' Nudge stays in Later."

**Jeff Patton:** "That's the map and the first screens, on one page. Before anyone builds, walk both again with the people who'll build it and someone who runs a team today. Steve Krug can tell you whether people can use these screens, Brad Frost can build them from your design system, and The Architect can work out how the system enforces the unlock rule."

*Why it works: every element traces back to a card, the screens use the map's own words, nothing below the Slice 1 line sneaks in, and walking the screens finds a hole the way walking the map did.*

---

## The finished page

This whole conversation, built: `example/team-course.md` is the Markdown source after Phase 8, and `example/team-course.html` is the page built from it with `story-map-template.html`. Only the JSON block differs from the template; the colors are the template's own, since the example has no design-principles file. Open the HTML to see the Map tab and the Wireframes tab with all nine Slice 1 sketches.
