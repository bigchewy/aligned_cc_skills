# Close the Loop — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Answering from early-2026 memory without checking

**User:** "What's the best way to set up Claude Code for my team now?"

**Wrong:**
"Use Opus 4.5 with thinking for everything, run five tabs, and use the ralph-wiggum plugin for long tasks."

**Right:**
[Phase 0 runs first: Boris's recent posts, Anthropic's best practices writing, Cat Wu, recent interviews.]
"Let's pick one kind of work, not your whole setup. What do you hand Claude most often, and the last time it got that wrong, what happened?"

**What to do instead:** Run Phase 0 before saying anything. Model names, plugins, and features in the January 2026 tips may be out of date. Use what's newer and give its date and link.

---

## 2. A feature tour instead of a fix

**User:** "Review my Claude Code setup."

**Wrong:**
"Here are 15 things you could add: hooks for formatting, linting, and tests; five subagents; MCP servers for Slack, Linear, and Sentry; a status line; custom output styles..."

**Right:**
"Let's start with what keeps going wrong. What do you hand Claude most often, and what did it get wrong last time?"

**What to do instead:** Start at Phase 1. Every change has to name the repeated problem it fixes. Boris's own setup is "surprisingly vanilla."

---

## 3. Skipping verification for a rule

**User:** "It keeps breaking the mobile layout."

**Wrong:**
"Add 'Always make sure the layout works on mobile' to your CLAUDE.md."

**Right:**
"A reminder gets followed most of the time. How would Claude find out the layout broke? Let's give it the browser at a phone width, and have it look before it says it's done."

**What to do instead:** Fix the check first (Phase 2). A rule in CLAUDE.md should point at the check, not replace it.

---

## 4. Naming settings from memory as if they were current

**User:** "Where do I put the permission rule?"

**Wrong:**
"Add it under `permissions.allow` in `.claude/settings.json` like this: ..." [stated from memory, no check]

**Right:**
"Let me check the current settings page first. [Checks.] It goes in the project's shared settings file, under [the key the docs name today]. Here's the line."

**What to do instead:** Check the current docs before naming any file path, key, hook event, or flag. If you can't check, say you're working from memory.

---

## 5. Skipping permissions to save clicks

**User:** "I'm tired of approving commands. Should I just turn permissions off?"

**Wrong:**
"Sure, start it with the skip-permissions flag and you won't be asked again."

**Right:**
"Which commands do you approve over and over? Pre-allow those in the shared settings, and you'll stop seeing most of the prompts. Skip permissions only inside a sandbox, where a mistake can't touch anything real."

**What to do instead:** Pre-allow the safe, repeated commands (Phase 5). Boris doesn't skip permissions outside a sandbox.

---

## 6. Searching when the saved file is recent

**User:** "Review my setup."

**Wrong:**
[The saved file says `checked: 2026-09-20`, eleven days ago. Boris searches Threads, X, three blogs, and interviews anyway, and the user waits several minutes before the first question.]

**Right:**
[Boris reads the saved file, sees it is less than a month old, uses it, and opens Phase 1 straight away.]

**What to do instead:** Search only when the saved file is missing, a month old or more, or the user asks to check again. Even then, ask first whether to keep working while a subagent searches in the background, or to wait. Never start a ten-minute search without asking.

---

## 7. Quoting a tip site as Boris's words

**User:** "What does Boris say about subagents?"

**Wrong:**
"Boris says, 'Always use at least five subagents for every task.'" [from a tips aggregator, never checked against his post]

**Right:**
"In his January setup thread he named two he uses, a code simplifier and an app verifier. Let me check whether he's said more since. [Checks Threads and X.]"

**What to do instead:** Quote him only from a post or transcript you read. Tip collections and search summaries help you find the post; they are not the post.
