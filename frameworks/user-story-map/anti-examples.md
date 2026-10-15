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
"Those are rules the system enforces. None of them is something a person does. Let's start with the facilitator's week. What do they do first? Each of those rules will hang under the task it affects. 'Lessons unlock weekly' is a detail under 'Read the lesson,' and it raises a question: can the facilitator see the lesson before the members can?"

**What to do instead:** Map what the person does. Put each rule underneath, as a detail of the task it changes. A design that starts from the access rules and draws screens around them never finds out what the user does each week.

---

## 3. Skipping the walkthrough

**User:** "The tasks look right. Let's slice."

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
"Not yet. We haven't agreed which tasks make Slice 1, so any screen now is a guess at what matters. Let's draw the line first. Then Ryan Singer breadboards Slice 1, and Brad Frost turns that into screens."

**What to do instead:** Draw the map, not a screen, until Slice 1 is agreed. Then Phase 8 breadboards Slice 1 in words, and Phase 9 hands the breadboard to Brad Frost for screens.

---

## 5. Giving the map as text only

**User:** "Here are the tasks under each activity." *(Phase 3 answer)*

**Wrong:**
"Got it. Here's the updated list:
- Get the team set up: Invite the members, Set the session day...
- Prepare the week's lesson: ..."
*(No picture drawn.)*

**Right:**
Update the Markdown map, rebuild the HTML from `story-map-template.html`, republish it to the same link, and say: "Map updated: 15 tasks under the six activities. Same link as before. Look at 'Check who's ready.' It only has two cards. Is that really all?"

**What to do instead:** Draw the map after every phase from 1 on. People agree on a picture they can all see. A list in a chat reply is a shared document, not shared understanding.

---

## 6. Drawing the map in made-up colors

**User:** *(The project has `brand/guidelines/design-principles.md`.)*

**Wrong:**
Hand-writing a fresh HTML page with its own blue-and-orange palette and a new layout each time.

**Right:**
"Colors and type from brand/guidelines/design-principles.md." Then build from the template, replacing only the tokens and the map data.

**What to do instead:** Read the project's design principles once, put its tokens into the template, and change only the map data on each redraw. Say which file supplied the colors, or that none was found. In a monorepo, look under `brand/*/guidelines/` too, and ask which app the map is for when more than one file matches.

---

## 7. Reading "map as text before screens" as "no picture"

**User:** "Build the facilitator and member story map as text for me to review before any screens." *(The frame is already clear from the brief.)*

**Wrong:**
"Here's the frame. User: the facilitator. Outcome: walk into each session knowing who's ready. Problem: prep is scattered across three tools. Since you asked for text, I'll keep this in chat and draw the picture later. First question: how fast should we go?"
*(No picture published. The request's wording overrode the "Draw the map" step.)*

**Right:**
Lock the frame, build the HTML from `story-map-template.html` with the frame at the top and an empty backbone, publish it, and say: "Frame's up on the map, at this link. Colors from brand/conscious-os/guidelines/design-principles.md. No screens yet: those wait until we've agreed Slice 1. Now the backbone. Tell me what the facilitator does, start to finish, as a handful of big activities."

**What to do instead:** Read "as text," "for review," and "before any screens" as "no screens yet." The picture is how the map gets reviewed, so keep drawing it. Only drop the picture if the user clearly asks for no picture, and confirm once before you do.

---

## 8. Stacked role lanes

**User:** "The member does the lesson, joins the session, and practices after." *(Phase 5 answer)*

**Wrong:**
"I'll add a member lane under the facilitator lane, with its own backbone: Join the course, Do the week's lesson, Join the session, Practice during the week. Then we'll mark where the two lanes touch."
*(Two backbones stacked on top of each other. The order between them is lost, so nobody can see that the facilitator's check waits on the member's lesson.)*

**Right:**
"The member goes on one timeline with the facilitator. 'Join the course' and 'Do the week's lesson' are new activities on the backbone, at the point in the story where they happen. Joining the session isn't new. It happens inside 'Run the session,' so the member's tasks sit under that activity next to the facilitator's, and each card says whose task it is."

**What to do instead:** Keep every role on one timeline and tag each task with its role. The Story Mapping Quick Reference places other users along the backbone where they enter the story, and Patton's 2005 article draws vertical lines where the role changes, "dividing the model into something that looks a bit like swim lanes." When two roles act at the same point, their tasks share the activity.

---

## 9. A breadboard affordance with no card

**User:** "Looks good. Anything you'd add to the breadboard?" *(Phase 8)*

**Wrong:**
"I'd add an 'Export to CSV' button on 'Who's ready for Thursday,' so the facilitator can take the list anywhere."
*(No card on the map says the facilitator needs a list outside the app. The button works against the Slice 1 measure, which is that facilitators stop using the spreadsheet by week three.)*

**Right:**
"Every affordance here names a Slice 1 card, and I wouldn't add one that doesn't. If the facilitator needs the list outside the app, that's a task we missed. It goes on the map first, as a card in Slice 1. Otherwise it stays off the breadboard."

**What to do instead:** Before an affordance goes on the breadboard, name the card it serves. If there's no card, add the card to the map first, in Slice 1, or drop the affordance.
