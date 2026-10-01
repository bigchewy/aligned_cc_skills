# Boris Cherny: Advisor Research

> **Evidence base.** Primary sources read in full on 2026-10-01: Boris Cherny's X thread on his
> personal setup (2 Jan 2026, 15 posts), his X thread of tips from the Claude Code team (31 Jan 2026,
> 12 posts), the Lenny's Podcast transcript (19 Feb 2026), the Latent Space episode with Cat Wu
> (7 May 2025, auto-generated transcript), and borischerny.com/about. x.com blocks fetching, so both
> threads were read on the twitter-thread.com mirror, which shows each post's full text and number.
> ✅ marks a fact or quote read on a primary page. 🟡 marks something found only in a search summary
> or a secondary recap. The prompt must not present 🟡 material as his words.
> **Voice mimicry potential: MEDIUM-HIGH.** Two numbered-tip threads, long podcast interviews, and a
> consistent set of phrases. He writes short and practical; most of his public material is about
> exactly the subject this advisor covers.
> **Why him.** Eric wanted an advisor for working with Claude Code. No existing advisor covers it:
> The DevEx Engineer lists "skill/agent architecture" in its registry entry, but its prompt never
> mentions Claude Code. Eric chose a named person over a role on 2026-10-01.

## Sources

| Short name | What | URL |
|---|---|---|
| Thread A | Setup thread, 2 Jan 2026 | https://twitter-thread.com/t/2007179832300581177 (original https://x.com/bcherny/status/2007179832300581177) |
| Thread B | Team tips thread, 31 Jan 2026 | https://twitter-thread.com/t/2017742741636321619 (original https://x.com/bcherny/status/2017742741636321619) |
| Lenny | Lenny's Podcast transcript, 19 Feb 2026 | https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens |
| LS | Latent Space with Cat Wu, 7 May 2025 | https://www.latent.space/p/claude-code |
| About | His site | https://borischerny.com/about/ |

## Who

- Software engineer at Anthropic who created Claude Code. ✅ (About) Lenny introduces him as "creator
  and head of Claude Code at Anthropic." ✅ (Lenny)
- Wrote *Programming TypeScript* (O'Reilly). ✅ (About) Publication year 2019 🟡 (search snippet).
- Worked at Meta, including Instagram, where he was responsible for code quality across Facebook,
  Instagram, and WhatsApp. ✅ (Lenny 00:16:23, 00:21:31)
- Left Anthropic for Cursor briefly and came back after two weeks. ✅ (Lenny 00:03:55)
- Claude Code started as his experiment with the public API: "There was no master plan." ✅ (LS)
  It launched on 24 Feb 2025 as a limited research preview alongside Claude 3.7 Sonnet. ✅
  (anthropic.com/news/claude-3-7-sonnet) "Claude Code was not initially a hit." ✅ (Lenny)
- Earlier startups and work in adtech and venture capital 🟡 (book retailer bio, search snippet).

## Working methods

| Method | Status | Source |
|---|---|---|
| Starts most sessions in plan mode, goes back and forth until the plan is good, then lets Claude auto-accept edits. About 80% of his tasks start this way. | ✅ | A/6; Lenny 01:09:51 |
| Plan mode "is actually really simple": one sentence in the prompt saying not to write code yet. | ✅ | Lenny 01:09:51 |
| Runs about five sessions in numbered terminal tabs with system notifications, plus more on claude.ai/code, and hands sessions between them. | ✅ | A/1-2 |
| The team's top tip is 3-5 git worktrees, each with its own session, "the single biggest productivity unlock." | ✅ | B/1 |
| One shared CLAUDE.md, checked into git. The team adds to it several times a week, whenever Claude does something wrong. | ✅ | A/4-5 |
| After a correction: "Update your CLAUDE.md so you don't make that mistake again." Edits CLAUDE.md ruthlessly. | ✅ | B/3 |
| Slash commands for every inner-loop workflow, in `.claude/commands/`, checked into git. /commit-push-pr runs dozens of times a day. | ✅ | A/7 |
| Subagents for repeated jobs (his examples: code-simplifier, verify-app). | ✅ | A/8 |
| A PostToolUse hook formats code and "handles the last 10%." | ✅ | A/9 |
| Doesn't skip permissions. Pre-allows safe commands with /permissions and shares them in the project settings file. Skips permissions only inside a sandbox. | ✅ | A/10, A/12 |
| Gives Claude a way to verify its own work. He calls it probably the most important tip: it "will 2-3x the quality of the final result." | ✅ | A/13 |
| For long tasks: a background agent that checks the work, a Stop hook, or a loop plugin. | ✅ | A/12 |
| Connects tools with MCP servers and command-line tools (Slack, BigQuery through `bq`, Sentry), shared through the project's MCP config. | ✅ | A/11; B/9 |
| Uses the most capable model with maximum effort; says it is cheaper overall because it needs less steering. | ✅ | A/3; Lenny 01:09:17-35 |
| Re-plans when a task goes sideways. Asks Claude to "grill me" on changes. Asks it to scrap a mediocre fix and do the elegant one. | ✅ | B/2, B/6-7 |

## Principles

- "The product is the model." ✅ (Lenny 00:51:28)
- Build for the model six months from now, not the model of today. ✅ (Lenny 01:05:50)
- "Do the simple thing first" is an Anthropic product principle he quotes. He did not coin it. ✅ (LS 00:04:32)
- Claude Code is "the thinnest possible wrapper over the model," built so "you can use it, customize
  it, and hack it however you like." ✅ (LS; A intro) "Unopinionated" and "hackable" are not his words.
- Give the model tools and a goal, not a box of context up front. ✅ (Lenny 01:04)
- Scaffolding gains of 10-20% "often... just get wiped out with the next model." ✅ (Lenny 01:05:29)

## Verbatim quotes ✅

- "My setup might be surprisingly vanilla! Claude Code works great out of the box, so I personally don't customize it much." (A)
- "Anytime we see Claude do something incorrectly we add it to the CLAUDE.md, so Claude knows not to do it next time." (A/4)
- "A good plan is really important!" (A/6)
- "give Claude a way to verify its work. If Claude has that feedback loop, it will 2-3x the quality of the final result." (A/13)
- "Verification looks different for each domain... Make sure to invest in making this rock-solid." (A/13)
- "Pour your energy into the plan so Claude can 1-shot the implementation." (B/2)
- "Claude is eerily good at writing rules for itself." (B/3)
- "If you do something more than once a day, turn it into a skill or command" (B/4)
- "Or, just say 'Go fix the failing CI tests.' Don't micromanage how." (B/5)
- "you get better results if you just give the model tools, you give it a goal, and you let it figure it out." (Lenny 01:04:06)
- "Don't try to put it into a box. Don't try to give it a bunch of context upfront. Give it a tool, so, that it can get the context it needs." (Lenny 01:04:16)
- "you still have to transport yourself to the current moment... it's not Sonnet 3.5 anymore." (Lenny 00:23:43)
- "There is no one correct way to use Claude Code." (B)

🟡 Recaps phrase the verification tip as "2-3× improve results." His wording is "2-3x the quality."

## Voice

- Numbered tips, each short and concrete, often with a docs link.
- Understated and practical: "surprisingly vanilla," "there is no one correct way."
- Enthusiasm in small doses: "eerily good," "A good plan is really important!"
- Recurring phrases: "1-shot it," "inner loop," "feedback loop," "let Claude cook," "the model,"
  "latent demand," "bet on the more general model."
- Credits people by name for ideas (Dan Shipper for compounding engineering).

## Where he stays hands-on ✅

- "I don't think we're at the point at where you can be totally hands-off... You have to make sure that
  it's correct." Claude reviews every PR, then a human does, except for throwaway prototypes. (Lenny 00:16:51)
- In 2025 he kept intricate data-model refactors for himself (LS ~00:17). By Feb 2026 he said he hadn't
  edited a line by hand since November. Treat this as a change over time, not two current views.
- Skip permissions only inside a sandbox. (A/10, A/12)
- No clear public list of what Claude Code is bad at. His framing is that the model improves, so wait for it.

## Framework candidates

| Candidate | Signature | Conversational | Repeatable | Notes |
|---|---|---|---|---|
| Setup audit run against one kind of work, leading with verification | High (Threads A and B) | High | High | **Chosen: Close the Loop** |
| Give Claude a way to verify its work | Highest (his top tip) | Medium (one decision) | Medium | Folded into Close the Loop as Phase 2 |
| Plan, then execute | High | Medium | Medium | Folded in as Phase 3 |
| The compounding CLAUDE.md | High | Medium | High | Folded in as Phase 4 |
| Turn repeated work into commands and skills | High | Medium | High | Folded in as Phase 5 |
| Product principles for building on models | Medium (Lenny) | Medium | Low | Conversation only |

## Live sources for the "check what's new" step

Eric asked on 2026-10-01 that Boris look up current best practices before giving advice, because they
change quickly. He said the changelog is the least useful source: mostly bug fixes and minor features.
The search looks for how people work, not what shipped. Each source below was checked on 2026-10-01.

| Source | URL | Checked |
|---|---|---|
| Boris on Threads | https://www.threads.com/@boris_cherny | ✅ Fetchable; shows posts with dates (newest seen: late Sep 2026) |
| Boris on X | @bcherny | ✅ x.com returns 402 to fetchers; web search finds posts; twitter-thread.com/t/<status> mirrors threads |
| Boris's blog | https://borischerny.com/feed.xml | ✅ Newest post "I am often wrong," 19 Sep 2026 (a six-step problem-solving process; does not mention Claude Code) |
| Best practices page | https://code.claude.com/docs/en/best-practices | ✅ Linked from the docs overview |
| Docs page index | https://code.claude.com/docs/llms.txt | ✅ For mechanics questions only |
| Claude blog | https://claude.com/blog | ✅ Product posts, several about Claude Code in Sep 2026 |
| Anthropic engineering | https://www.anthropic.com/engineering | ✅ Posts on Claude Code auto mode, long-running harnesses |
| Cat Wu | @_catwu on X | ✅ Head of product for Claude Code (Lenny's Newsletter, her own X posts) |

Searching every conversation was too slow (Eric, 2026-10-01). What Boris finds is saved to
`~/.claude/aligned/boris-cherny-whats-new.md`, one dated line per item with a link, and he searches
again only when the file is a month old or more, or the user asks him to check again. The file sits in
the user's home folder so every project shares it and plugin updates don't erase it.

Tip collections such as howborisusesclaudecode.com and a GitHub "playbook" repo exist. They are useful
for finding posts, not as sources of his words.

## Dropped or held back

- Specific model names ("Opus 4.5 with thinking," "Opus 4.6, maximum effort"). They date fast. The
  prompt says "the most capable model" instead.
- Exact flags, commands, and settings names. Claude Code changes weekly. The prompt tells the persona
  to check current docs before giving mechanics, and to say when it is working from memory.
- The Claude Code changelog as a source for best practices (Eric, 2026-10-01).
- Not checked: Pragmatic Engineer, Every / AI & I, YC episodes, and the original Anthropic "Claude Code
  best practices" post (now a docs page with no byline; not attributed to him).
