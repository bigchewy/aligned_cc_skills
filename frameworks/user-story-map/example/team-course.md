# Team course story map

A course app for one team, run by a facilitator over 10 units

## Frame

- **User:** The facilitator running one team through the course
- **Outcome:** They walk into each weekly session ready, knowing who did the lesson, without an evening of prep
- **Problem:** The prep is scattered across a PDF, a group chat, and a spreadsheet, so they guess who's ready
- **Why:** Teams that finish a unit sign up for the next

## Roles

| Role | Who they are |
|---|---|
| Facilitator | Runs one team through the course |
| Member | Does each week's lesson and joins the weekly session |

## Slices

| Slice | Name | Outcome | Measure |
|---|---|---|---|
| 1 | Slice 1: Run a week | A facilitator runs a full week with one team and walks in knowing who's ready, without the spreadsheet | Facilitators stop using the spreadsheet by week three |
| 2 | Slice 2: Run a unit | The facilitator sees who fell behind across a unit and opens the next one | Facilitators talk with every member who fell behind before the next unit opens |

## Map

### Get the team set up

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Invite the members | task | step | Facilitator | 1 | | |
| Set the session day and time | task | step | Facilitator | 1 | | |
| Share the course outline | task | step | Facilitator | Later | | |

### Join the course

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Accept the invite | task | step | Member | 1 | | |
| See the course outline | task | step | Member | Later | | |

### Prepare the week's lesson

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Read the lesson | task | step | Facilitator | 1 | | |
| Lesson visible to facilitator before members | detail | rule | Facilitator | 1 | | |
| Pick the live exercise | task | step | Facilitator | 1 | | |
| Notes for this team | task | step | Facilitator | Later | | |

### Do the week's lesson

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Open this week's lesson | task | step | Member | 1 | | |
| Do the exercises | task | step | Member | 1 | | |
| Mark it done | task | step | Member | 1 | | |

### Check who's ready

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| See who finished the lesson | task | step | Facilitator | 1 | | |
| Nudge who hasn't started | task | step | Facilitator | Later | | |
| Mark someone excused | task | step | Facilitator | Later | yes | Found on the walk |

### Run the session

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Open the live exercise | task | step | Facilitator | 1 | | |
| Join from the calendar link | task | step | Member | 1 | yes | Found on the walk |
| Take part in the live exercise | task | step | Member | 1 | | |
| Take attendance | task | step | Facilitator | 1 | | |
| Note what came up | task | step | Facilitator | Later | | |

### Follow up after

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Send a recap | task | step | Facilitator | 1 | | |
| Note who needs a check-in | task | step | Facilitator | Later | | |

### Practice during the week

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Read the recap | task | step | Member | 1 | | |
| Try the practice on the team | task | step | Member | Later | | |

### Wrap up the unit

| Card | Tier | Kind | Role | Slice | Gap | Note |
|---|---|---|---|---|---|---|
| Wrap up the unit by hand, as today | task | workaround | Facilitator | 1 | | |
| See who fell behind this unit | task | step | Facilitator | 2 | | |
| Talk with anyone behind | task | step | Facilitator | 2 | | |
| Open the next unit | task | step | Facilitator | 2 | | |

## Open questions

1. Does the facilitator need to see a lesson before it unlocks for members, and how far ahead?
2. Who marks a member excused, the facilitator or the member?
3. What does "Wrap up the unit by hand, as today" look like for the facilitator until Slice 2 ships?

## Slice 1 breadboard

### Get the team set up (Facilitator)

| Affordance | Leads to | Card |
|---|---|---|
| Member email addresses field | | Invite the members |
| Send the invites button | | Invite the members |
| Session day and time field | | Set the session day and time |

### Lesson 2, before members see it (Facilitator)

| Affordance | Leads to | Card |
|---|---|---|
| The lesson text | | Read the lesson |
| A note that members can't see it yet | | Lesson visible to facilitator before members |
| List of exercises | | Pick the live exercise |
| Use this one live button | Who's ready for Thursday | Pick the live exercise |

### Who's ready for Thursday (Facilitator)

| Affordance | Leads to | Card |
|---|---|---|
| List of members with finished or not started | | See who finished the lesson |
| Count of members who finished | | See who finished the lesson |
| Run the session link | Thursday session | Open the live exercise |

### Thursday session (Facilitator)

| Affordance | Leads to | Card |
|---|---|---|
| Open the live exercise button | | Open the live exercise |
| Attendance list with here or away | | Take attendance |
| Recap link | Recap for the team | Send a recap |

### Recap for the team (Facilitator)

| Affordance | Leads to | Card |
|---|---|---|
| What we covered, and this week's practice field | | Send a recap |
| Send the recap button | | Send a recap |

### You're invited to the team course (Member)

| Affordance | Leads to | Card |
|---|---|---|
| Accept the invite button | This week's lesson | Accept the invite |

### This week's lesson (Member)

| Affordance | Leads to | Card |
|---|---|---|
| The lesson text | | Open this week's lesson |
| Each exercise | | Do the exercises |
| Mark it done button | | Mark it done |

### Thursday session at 6 (Member)

| Affordance | Leads to | Card |
|---|---|---|
| Join from the calendar link button | | Join from the calendar link |
| Exercise 2 opens here when the facilitator starts it | | Take part in the live exercise |

### Recap from Thursday (Member)

| Affordance | Leads to | Card |
|---|---|---|
| What we covered, and this week's practice | | Read the recap |
