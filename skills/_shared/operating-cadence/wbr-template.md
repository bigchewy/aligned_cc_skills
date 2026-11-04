# The WBR

A WBR is one workstream owner's weekly business review. It is due a day before the leadership meeting. This is its form.

## The form

```
[Workstream], [owner], week of [date]

STATUS
[Code] [key action]: Green | Yellow | Red, due [date]
  Date moved: was [old], now [new]
  Yellow or red: [one line on what is wrong]
  Definition: [word] means [test]

METRICS
[Metric]: [number], target [target], [up | down | flat], [code]

LAST WEEK
[Code] [item]: Honored | Renegotiated, now [date], agreed with [name] | Not done, [why]

THE GOOD
THE NOT GOOD

THIS WEEK
[Code or Off strategy] [item]. Implementer: [name]. Success: [what it looks like]. Due [date].

QUESTIONS TO ANSWER
1. [One sentence]. Proposal: [what I recommend].

ASKS OF OTHER TEAMS
[Team]: [ask], [code]
```

## Required and optional

Status and Last week are required. A WBR with either one missing doesn't get saved.

Metrics, The good, The not good, This week, Questions to answer and Asks of other teams are optional. Leave out an empty one. Metrics are the numbers the person states. Nobody opens a dashboard to fill them in.

## Saving

The form above is how the WBR reads in chat. On the team page it is saved as Markdown with a `## Heading` for each section, so the page can build its table of contents. A section that is left out has no heading. The headings, in order:

- `## Status`
- `## Metrics`
- `## Last week`
- `## The good`
- `## The not good`
- `## This week`
- `## Questions to answer`
- `## Asks of other teams`

The first line, with the workstream, the owner and the week, is the title of the document and is not a heading. The statuses are also saved as a list on the document, one entry for each key action, with its code, color, due date and moved date. The page reads that list for its tiles.

## Codes

A code is a key action code, 1 to 4 and 1A to 4D. Work tied to none is `Off strategy`. That is a flag, and it is not a gate.
