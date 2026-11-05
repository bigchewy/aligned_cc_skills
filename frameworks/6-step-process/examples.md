# 6-Step Process Examples

All of these follow one case: Maya wants 80% in-office attendance by the end of Q2, up from 40%. `example-map.html` in this folder shows a map from the same case.

## Opening

### A new run

**Advisor:** "We'll work through six steps: locate, goal, root-cause the problems, solutions, execute, feedback. You'll leave with a map you can edit and show to others. First, are you here to pick up a map you already have? If so, tell me the file name. If not, say new."

**User:** "New."

**Advisor:** "I read your strategy and your goals document. Right now, on this, are you above the line (open and curious) or below it (defensive, frustrated, afraid)?"

> One question, then a stop. Reading the documents asks nothing, and the one line names them without saying what's in them.

## Step 1: Locate

### Above the line

**User:** "Above. I'm frustrated with the situation, but I'm curious what I'm missing."

**Advisor:** "What outcome do you want, with a number if you can? From what, to what, by when?"

> The person decided. Claude trusts it and moves on.

### Below the line, and they want to continue

**User:** "Below. I've tried everything, and I'm starting to think the problem is my team."

**Advisor:** "`above-below-the-line` is the playbook's first pick for this, and it works on presence and responsibility. Do you want to run that, or continue here?"

**User:** "Continue here."

**Advisor:** "What outcome do you want, with a number if you can? From what, to what, by when?"

> One offer. When they choose to continue, Claude continues without comment.

## Step 2: Goal

### A goal with a number

**User:** "80% in-office attendance by the end of Q2. Right now we're at about 40%."

**Advisor:** "40% to 80% by the end of Q2. Your map is at `~/attendance/office-attendance-maya-map.html`. Double-click it to open it. Write your own list of what stands between you and this goal. Use paper or a note, not here, and don't tell me what's on it. If I share first, you'll gravitate toward what I said. Say "done" when you have it."

> The confirmed goal starts the file. The message ends at the next stop.

### A vague goal

**User:** "I want my team to be more collaborative and engaged."

**Advisor:** "If we talked at the end of Q2 and you'd succeeded, what would you be able to count?"

> One nudge toward a number. If none comes, Claude takes the goal without one.

## Step 3: Root-cause the problems

### 3a: Claude's list comes after "done"

**User:** "Done."

**Advisor:** "The documents and the goal suggest these: expectations are unclear, there's no reason to come in since meetings are still remote, and some people feel less productive in the office. What would you change, and what do you have that isn't here?"

**User:** "Those are good, and they aren't on my list. I had people don't want to commute, the office is too noisy, and some managers aren't enforcing the policy."

**Advisor:** "That makes six: people don't want to commute, expectations are unclear, the office is too noisy, some people feel less productive in the office, some managers aren't enforcing the policy, and there's no reason to come in since meetings are still remote. Is that the list?"

> Claude built its list after "done," and the person added theirs. The merged list shows no order of importance and doesn't say who wrote what.

### 3a: They type their list instead

**User:** "My list is people don't want to commute, the office is too noisy, and some managers aren't enforcing the policy."

**Advisor:** "I'll take those as yours, and I've now heard them. The documents and the goal suggest these as well: expectations are unclear, there's no reason to come in since meetings are still remote, and some people feel less productive in the office. What would you change, and what's missing?"

> Claude says it has heard the list and still shows its own.

### 3a: A solution comes early

**User:** "We should run a monthly pulse survey."

**Advisor:** "That's in the holding list, and we'll get to it in Step 4. Back to your list: say "done" when you have it."

> One line, then back to the current step.

### 3c: Pushing past a circular answer

**User:** "People don't want to commute because commuting sucks."

**Advisor:** "Why does it cost more than the office gives back now?"

**User:** "The value of being in the office hasn't kept up. We haven't defined what the office is for."

**Advisor:** "**We haven't defined what the office is for.** You can do something about that one. Is that it?"

> Two rounds, and the person can act on the answer. Each answer is a child of the item before it, and the last one goes in bold and ends its branch.

### 3c: Two reasons become two branches

**Advisor:** "1: People don't want to commute. Why not?"

**User:** "Two things. The commute got longer for people who moved, and the value of being in the office hasn't kept up."

**Advisor:** "That's two branches: 1A, the commute got longer, and 1B, the value of the office hasn't kept up. Take 1B first. Why hasn't it kept up?"

> Each reason becomes its own child of the item Claude asked about. Claude uses the labels and takes one branch at a time, and one question per turn still holds.

## Step 4: Solutions

### 4a: Placing a solution with no obstacle

**User:** "And the monthly pulse survey from the holding list."

**Advisor:** "Which obstacle does the pulse survey get past?"

**User:** "I don't know. I just want to hear how people feel."

**Advisor:** "One obstacle on the map is that some people feel less productive in the office. The survey would tell you how many and why. Does it belong there, or is something missing from the map?"

**User:** "It belongs there."

> Claude nudges, then helps find the obstacle. By the end of 4a, every solution is placed.

### 4a: A solution on a specific item

**Advisor:** "Which obstacle does create in-person-only experiences get past?"

**User:** "People don't want to commute. Put it on 1B, the value of the office not keeping up, because that's what it fixes."

**Advisor:** "It's on 1B. Next: which obstacle does set clear expectations with managers get past?"

> The person named an item, so Claude adds the solution to that item's `children`. The page draws it one column out from 1B. Without a named item, Claude places a solution under what it gets past, usually a root cause.

### 4a: A solution that serves two obstacles

**User:** "Set clear expectations with managers. That helps with managers not enforcing the policy, and with expectations being unclear."

**Advisor:** "A solution lives in one place. Which obstacle does it belong to, or should it be two separate solutions?"

> Claude asks, and doesn't write two items with the same text without asking.

### 4a: An obstacle in the way of a solution

**User:** "Creating in-person-only experiences won't work, because teams have no budget for getting together."

**Advisor:** "That goes under the solution as an obstacle, and it's 1B3. Do you want a solution for it now?"

> An obstacle under a solution continues the numbering of the nearest obstacle above it. 1B already has 1B1 and 1B2, so this one is 1B3. The map shows it sits under the solution and isn't an answer to why on 1B.

### 4b: Picks and the key-action table

**User:** "Done."

**Advisor:** "The documents and the goal suggest starring two: define the purpose of in-office time and communicate it, because the root cause sits there, and create in-person-only experiences, because meetings are still remote. Where do your picks differ?"

**User:** "They don't. I picked the same two."

**Advisor:** "Here's how those two compare to the strategy.

| Key action | Risk | Solutions that touch it |
|---|---|---|
| Say what the office is for | High | Define the purpose of in-office time |
| Give each team a reason to meet in person | Medium | Create in-person-only experiences, set clear expectations with managers |

Which ratings are wrong?"

> One ask per turn. Claude rates risk first because the rating comes from the documents. The person corrects it, Claude asks whether the table changes the picks, and the agreed picks get stars.

## Step 5: Execute

**Advisor:** "Define the purpose of in-office time: what's the first move, who owns it, and what do other people need to decide?"

**User:** "I draft one page on what the office is for. I own it. The leadership team approves the page."

> One starred solution per turn. The map marks these as planned, not done.

## Step 6: Feedback

**User:** "In-office attendance, every week. If it's under 55% by the middle of Q2, I come back and redraw this."

**Advisor:** "Your map is at `~/attendance/office-attendance-maya-map.html`. Steps 5 and 6 are planned, not done. The map is yours to edit and show to others. To keep your edits, click Turn on saving once in Chrome. When you change it, tell me."

> A number, a date and a result that sends them back. The close ends there.

## Picking up edits

### The file has edits

**User:** "I changed the map."

**Advisor:** "You renamed the noise obstacle, deleted the productivity obstacle and the pulse survey under it, and added 4A under expectations. The pulse survey had no Step 5 row, so nothing else went with it. Which step do you want to resume?"

> Claude compares the file with `baseline` and lists the changes in plain words, including what went with a deleted item. If it only lists them, it moves `baseline` in the file to this version and leaves `revision` alone, so the next pick-up sees only newer edits.

### A solution moved to another item

**User:** "I changed the map."

**Advisor:** "You moved create in-person-only experiences from 1B to 1, the commute obstacle itself. That's the only change. Which step do you want to resume?"

> The solution's parent changed, and Claude names both items by label. Claude compares items by `id` and parent, because a label can change when an item before it is deleted.

### An obstacle moved to another item

**User:** "I changed the map."

**Advisor:** "You moved the value of the office not keeping up from 1 to 5, along with the two root causes and the solutions under it. It's 5B now. Which step do you want to resume?"

> A moved obstacle gets reported with what's under it.

### No edits, and they didn't say they changed it

**User:** "I want to keep going on `office-attendance-maya-map.html`."

**Advisor:** "The map shows six obstacles, two with root causes, one solution in the tray, and no stars. The tray doesn't tell me you wrote your solutions list, so I'd resume at 4a. Which step do you want to resume?"

> They stopped early and came back, so the file having no edits is expected. Claude doesn't mention a lost save. The map can't prove 4a ran, so Claude says what it shows and asks.

### They said they changed it, and the file has no edits

**User:** "I changed the map."

**Advisor:** "The file in your folder doesn't have your edits, so the save probably went somewhere else. If the page is still open and says changes aren't being saved, click Turn on saving or Turn saving back on first. Otherwise look in Downloads, including for a copy with (1) in its name, and put it back in the folder under its original name, replacing the old one, then tell me. If the page said the map has newer changes, don't replace it. Put the copy in the folder under another name and tell me that name."

> Claude says what it found and where to look, and doesn't guess at edits.

### The second read still shows no edits

**User:** "I looked, and I can't find anything. Maybe I never saved."

**Advisor:** "The file still shows no edits, so I'll go from what it holds. The map shows six obstacles, two with root causes, one solution in the tray, and no stars. I'd resume at 4a. Which step do you want to resume?"

> Claude asks where to look once. After that, it resumes from the file.

### A copy with a lower revision than the map

**User:** "The page wouldn't save, so I put a copy in the folder as `office-attendance-maya-copy-map.html`."

**Advisor:** "That copy is older than the map. The copy renames the noise obstacle. The map has the Step 5 rows I wrote after your tab opened, and the copy doesn't. Should I bring the new name into the map and keep the Step 5 rows?"

> Claude compares the copy with the map, not with the copy's own `baseline`, which would hide the Step 5 rows. It merges into the map after their yes.
