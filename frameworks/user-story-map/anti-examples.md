# User Story Map — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. A backbone that lists pages or features

**User:** "Backbone: Dashboard, Lesson page, Members page, Session page, Reports."

**Wrong:**
"Great, that's a clear backbone. Under Dashboard, let's list the widgets."

**Right:**
"That's the menu, not the story. Nobody wakes up wanting to visit Reports. What's the facilitator doing when they'd go there? Give me the verb. 'Lesson page' is probably 'Prepare the week's lesson.' What about the others?"

**What to do instead:** Turn every noun into the activity behind it, as a verb phrase the user would say. If every card is a noun, it's a feature breakdown, not a story map.

---

## 2. A map built from system rules

**User:** "The activities are: Lessons unlock weekly. Facilitators can see all members. Members can only see their own team. Sessions time out after 90 minutes."

**Wrong:**
"Here's the map: Unlock schedule → Facilitator permissions → Member permissions → Session timer."

**Right:**
"Those are rules the system enforces. None of them is something a person does. Let's start with the facilitator's week. What do they do first? Each of those rules will hang under the step it affects. 'Lessons unlock weekly' is a detail under 'Prepare the week's lesson,' and it raises a question: can the facilitator see the lesson before the members can?"

**What to do instead:** Map what the person does. Put each rule underneath, as a detail of the step it changes. A design that starts from the access rules and draws screens around them never finds out what the user does each week.

---

## 3. Skipping the walkthrough

**User:** "The steps look right. Let's slice."

**Wrong:**
"Okay! For Slice 1, I'd suggest the top row of every column."

**Right:**
"Before we slice, let me walk it. Five minutes. I'll tell the story as the facilitator, left to right, using only what's on the map, and you stop me where it's wrong. ...Thursday I open the session. Wait, how do the members get in? There's no card for that. That's a gap."

**What to do instead:** Always tell the story aloud, in first person, from the cards alone, and name every gap. The walk is where the assumed steps show up.

---

## 4. Jumping to a UI mockup before the slices are agreed

**User:** "Can you sketch what the facilitator's home screen looks like?"

**Wrong:**
"Sure. Top bar with the course name, a card per member with a progress ring, a big Start Session button..."

**Right:**
"Not yet. We haven't agreed which steps make Slice 1, so any screen now is a guess at what matters. Let's draw the line first. Once everyone agrees on it, the map's ready for wireframes, and they start from Slice 1."

**What to do instead:** Draw the map, never a screen. Wireframes come after the slices are agreed, and start from Slice 1.

---

## 5. Giving the map as text only

**User:** "Here are the steps under each activity." *(Phase 3 answer)*

**Wrong:**
"Got it. Here's the updated list:
- Get the team set up: Invite the members, Set the session day...
- Prepare the week's lesson: ..."
*(No picture drawn.)*

**Right:**
Update the Markdown map, rebuild the HTML from `story-map-template.html`, republish it to the same link, and say: "Map updated: 15 steps under the six activities. Same link as before. Look at 'Check who's ready.' It only has two cards. Is that really all?"

**What to do instead:** Draw the map after every phase from 2 on. People agree on a picture they can all see. A list in a chat reply is a shared document, not shared understanding.

---

## 6. Drawing the map in made-up colors

**User:** *(The project has `brand/guidelines/design-principles.md`.)*

**Wrong:**
Hand-writing a fresh HTML page with its own blue-and-orange palette and a new layout each time.

**Right:**
"Colors and type from brand/guidelines/design-principles.md." Then build from the template, replacing only the tokens and the map data.

**What to do instead:** Read the project's design principles once, put its tokens into the template, and change only the map data on each redraw. Say which file supplied the colors, or that none was found.
