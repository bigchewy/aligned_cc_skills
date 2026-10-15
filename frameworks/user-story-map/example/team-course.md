# Team course story map

A course app for one team, run by a facilitator over 10 units

## Frame

- **User:** The facilitator running one team through the course
- **Outcome:** They walk into each weekly session ready, knowing who did the lesson, without an evening of prep
- **Problem:** The prep is scattered across a PDF, a group chat, and a spreadsheet, so they guess who's ready

## Slices

| Slice | Name | Outcome | Measure |
|---|---|---|---|
| 1 | Slice 1: Run a week | A facilitator runs a full week with one team and walks in knowing who's ready, without the spreadsheet | Facilitators stop using the spreadsheet by week three |
| 2 | Slice 2: Run a unit | The facilitator sees who fell behind across a unit and opens the next one | Every unit wrap-up happens in the app |

## Lane: Facilitator

### Get the team set up

| Step | Slice | Gap | Note |
|---|---|---|---|
| Invite the members | 1 | | |
| Set the session day and time | 1 | | |
| Share the course outline | Later | | |

### Prepare the week's lesson

| Step | Slice | Gap | Note |
|---|---|---|---|
| Read the lesson | 1 | | |
| Pick the live exercise | 1 | | |
| Lesson visible to facilitator before members | 1 | | Detail: a rule under Read the lesson |
| Notes for this team | Later | | |

### Check who's ready

Touches: Member: Do the week's lesson

| Step | Slice | Gap | Note |
|---|---|---|---|
| See who finished the lesson | 1 | | |
| Nudge who hasn't started | Later | | |
| Mark someone excused | Later | yes | Found on the walk |

### Run the session

Touches: Member: Join the session

| Step | Slice | Gap | Note |
|---|---|---|---|
| Open the live exercise | 1 | | |
| Take attendance | 1 | | |
| Note what came up | Later | | |

### Follow up after

Touches: Member: Practice during the week

| Step | Slice | Gap | Note |
|---|---|---|---|
| Send a recap | 1 | | |
| Note who needs a check-in | Later | | |

### Wrap up the unit

| Step | Slice | Gap | Note |
|---|---|---|---|
| See who fell behind this unit | 2 | | |
| Talk with anyone behind | 2 | | |
| Open the next unit | 2 | | |

## Lane: Member

### Join the course

| Step | Slice | Gap | Note |
|---|---|---|---|
| Accept the invite | 1 | | |
| See the course outline | Later | | |

### Do the week's lesson

Touches: Facilitator: Check who's ready

| Step | Slice | Gap | Note |
|---|---|---|---|
| Open this week's lesson | 1 | | |
| Do the exercises | 1 | | |
| Mark it done | 1 | | |

### Join the session

Touches: Facilitator: Run the session

| Step | Slice | Gap | Note |
|---|---|---|---|
| Join from the calendar link | 1 | yes | Found on the walk |
| Take part in the live exercise | 1 | | |

### Practice during the week

Touches: Facilitator: Follow up after

| Step | Slice | Gap | Note |
|---|---|---|---|
| Read the recap | 1 | | |
| Try the practice on the team | Later | | |

## Open questions

1. Does the facilitator need to see a lesson before it unlocks for members, and how far ahead?
2. Who marks a member excused, the facilitator or the member?
3. What does the facilitator do by hand to wrap up a unit until Slice 2 ships?

## Slice 1 wireframes

### Facilitator: Get the team set up

| Kind | Text | Card |
|---|---|---|
| heading | Get the team set up | Get the team set up |
| field | Member email addresses | Invite the members |
| field | Session day and time | Set the session day and time |
| button | Send the invites | Invite the members |

### Facilitator: Prepare the week's lesson

| Kind | Text | Card |
|---|---|---|
| heading | Lesson 2, before members see it | Lesson visible to facilitator before members |
| text | The lesson text | Read the lesson |
| list | Exercise 1 / Exercise 2 / Exercise 3 | Pick the live exercise |
| button | Use this one live | Pick the live exercise |

### Facilitator: Check who's ready

| Kind | Text | Card |
|---|---|---|
| heading | Who's ready for Thursday | Check who's ready |
| list | Ana: Finished lesson 2 / Ben: Finished lesson 2 / Cy: Finished lesson 2 / Dee: Not started / Eli: Not started | See who finished the lesson |
| text | 3 of 5 finished | See who finished the lesson |
| link | Run the session | Run the session |

### Facilitator: Run the session

| Kind | Text | Card |
|---|---|---|
| heading | Thursday session | Run the session |
| text | Exercise 2, picked during prep | Pick the live exercise |
| button | Open the live exercise | Open the live exercise |
| list | Ana: here / Ben: here / Cy: here / Dee: away / Eli: here | Take attendance |

### Facilitator: Follow up after

| Kind | Text | Card |
|---|---|---|
| heading | Recap for the team | Follow up after |
| field | What we covered, and this week's practice | Send a recap |
| button | Send the recap | Send a recap |

### Member: Join the course

| Kind | Text | Card |
|---|---|---|
| heading | You're invited to the team course | Join the course |
| text | Sessions are Thursdays at 6 | Accept the invite |
| button | Accept the invite | Accept the invite |

### Member: Do the week's lesson

| Kind | Text | Card |
|---|---|---|
| heading | This week: Lesson 2 | Open this week's lesson |
| text | The lesson text, then each exercise | Do the exercises |
| button | Mark it done | Mark it done |

### Member: Join the session

| Kind | Text | Card |
|---|---|---|
| heading | Thursday session at 6 | Join the session |
| button | Join from the calendar link | Join from the calendar link |
| text | Exercise 2 opens here when the facilitator starts it | Take part in the live exercise |

### Member: Practice during the week

| Kind | Text | Card |
|---|---|---|
| heading | Recap from Thursday | Read the recap |
| text | What we covered, and this week's practice | Read the recap |
