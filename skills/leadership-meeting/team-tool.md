# The Team's Tool

This file says how the meeting template maps onto the team's own tool, so the update job can read from it and post to it.

## Where things live

Setup records the tool and where things live in `leadership-meeting.md` at the project root. That file holds no action items. Read it first when it exists.

| Thing | Asana | Linear |
|---|---|---|
| Home | Project | Team |
| Key action, with color and date | Project | Project |
| Written update | Project status update | Project update |
| Action item | Task | Issue |
| Question to answer | Task in a section | Issue with a status |
| Agenda | Task or project document | Document |
| Key decision | Task in a section | Section of the meeting document |
| Parking lot | Task in a section | Issue with a status |

The Linear column is untested. No Linear connector was available when it was written. Treat its rows as a starting point and check them against what you find.

## Finding the tool

- Search the session's available tools at run time for the tool's name. Never hard-code a full tool name.
- If `leadership-meeting.md` names a tool and you find no matching tool in the session, treat it as no connector.

## With no connector, or any other tool

- Setup gives steps for a person to follow.
- The update job asks for a paste of last week's update and the open action items.
- Anything to write comes back as a block for the person to paste.

## Titles

The code goes at the start of the title, such as `1A: Call the top five customers`. Off strategy items start with `Off strategy:`.

## Write limits

- Write only after a person approves.
- The skill never sets an owner or an assignee. Put the implementer's name in the title or the description.
- The feedback job never writes to the tool.
