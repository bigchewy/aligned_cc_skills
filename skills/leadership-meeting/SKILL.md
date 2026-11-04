---
name: leadership-meeting
description: "Use when a leadership team wants to set up a weekly meeting, write a weekly update before it, or get feedback on a real meeting from its transcript and agenda."
---

# Leadership Meeting

> **Path Resolution:** Resolve `{base-directory}` from the "Base directory for this skill:" line printed at skill load. If compressed, Glob `$HOME` for `**/.claude-plugin/plugin.json`, take the parent of the matched `.claude-plugin/` dir as the plugin root, and compute `{base-directory}` as `<plugin-root>/skills/leadership-meeting/`. See `skills/_shared/resolve-skill-path.md` for rationale.

## Overview

This skill does three jobs for a leadership team that meets every week.

| Job | What it does |
|---|---|
| `setup` | Builds the team's meeting page from the template: purpose, roles, key actions, agenda |
| `weekly update` | Helps one person write their update for the day before the meeting |
| `feedback` | Grades a real meeting from its transcript and agenda, then writes a team page and a private note for the leader |

## Pick the Job

Read what the person asked and pick the job from it. Ask which job only if you can't tell. Words like "set up", "start", or "build our meeting" mean `setup`. Words like "my update", "what happened this week", or "prep for Thursday" mean `weekly update`. A transcript, a recording, or "how did the meeting go" means `feedback`.

## Setup

1. The plugin root is the parent of `skills/`. Check that `<plugin-root>/frameworks/leadership-meeting/prompt.md` exists. If it doesn't, say plainly that setup needs the full plugin. Then hand over `{base-directory}template.md`, tell the person to fill in the bracketed parts by hand, and stop.
2. Read `skills/_shared/framework-runner.md`.
3. Run it with these inputs:
   - Matched framework path: `<plugin-root>/frameworks/leadership-meeting/`
   - `intake_gate_mode`: `advisory`
   - `publish_artifact`: `yes`

The template is `{base-directory}template.md`. Square brackets get filled in at setup, or each week by the facilitator.

## Weekly Update

Read `{base-directory}weekly-update.md` and follow it. It sends you to `{base-directory}team-tool.md` when it needs to read or post in the team's own tool.

## Feedback

Read `{base-directory}meeting-feedback.md` and follow it.

## Files in This Skill

- `template.md`: the meeting page, with the agenda, roles, key actions and the written update form
- `weekly-update.md`: the weekly update job
- `team-tool.md`: how the job reads and posts in the team's own tool
- `meeting-feedback.md`: the seven checks and the two documents
- `frameworks/leadership-meeting/` (at the plugin root): the framework that runs setup
