# Anti-Examples: How Find Potential Advisors Gets Run Badly

Every one of these happened in a real run between 2026-09-29 and 2026-10-28. In eight runs, none
ran the phases as written, and the user had to ask "Did you run the full program?" before the
gaps came out. `workflow.js` exists to make these impossible. When you run without it, check
yourself against this list.

## 1. Research, candidates and ratings in one wave of agents

What a run sent to a single agent:

> Research task: find the best hands-on experts on designing viral loops INTO consumer products
> ... Angles: 1. What the evidence/practitioner consensus says works ... 2. Candidates ...
> Return 5-6 candidate profiles. For each: name and credentials; primary approach; key works ...
> Voice mimicry rating ...

One agent did Phase 2, Phase 3 and Phase 4 for half a dozen people. A second agent did the same
for another angle. That was the whole search.

Why it's wrong: the agent that picks a candidate then grades its own pick. It runs out of
searches before it reaches the counting, so the ratings get filled in from whatever is at hand.
Research, profiling and evaluation are separate agents because each one checks the one before it.

## 2. A rating with no count behind it

From the same run:

> Voice rating: High. Four books, extensive talk and podcast material, and distinctive
> terminology. I did not verify the hour count.

And from the corrected run, still bent:

> Voice-mimicry rating: High, with a caveat ... Hours: 3.5 verified, below the 5-hour bar. He
> clearly has far more public audio and video.

Why it's wrong: High needs 5 hours of talks you saw. "Extensive" and "clearly has far more" are
guesses. A later count for one of these candidates found 3.0 hours, not the 5 the rating assumed.
The script now computes the rating from the items that have URLs, and nobody gets to round it up.

## 3. Search snippets used as sources

> Search quality was thin: WebSearch returned summaries, so I fetched no pages, and video/audio
> hour counts were not verified for anyone.

Why it's wrong: in the same search, two snippets gave episode lengths that were off by 15 and 20
minutes compared with the episode pages. A snippet tells you which page to open. It isn't the page.

## 4. Facts from memory in the finalist write-up

> From the research agent's memory, he also did the MIT Media Lab's parent mark and its two dozen
> group marks, all from one grid.

> His "Five Ts" framework (talkers, topics, tools, taking part, tracking) is from my memory and
> unverified.

Why it's wrong: the first one went into the recommendation to the user as a reason to pick
Michael Bierut. A fact from memory can go in "What was skipped or not verified." It can't hold up
a recommendation.

## 5. Voice samples written from memory

The run's own admission, once asked:

> Phase 5: I wrote the voice samples myself from memory, not from anyone's actual writing.

Why it's wrong: the voice sample is how the user judges whether a persona will sound like the
person. One made up from memory tests nothing. Build it from quotes with URLs.

## 6. Cuts admitted only when asked

The run presented three finalists and asked "Which of the three should I add?" It said nothing
about what it had skipped. When the user asked "Did you run the full program?", it listed five
skipped phases.

Why it's wrong: the user can't tell a researched report from a guessed one unless the report says
which is which. "What was skipped or not verified" goes in every chat summary, even when the
answer is "Nothing."

## 7. Treating the search as a side errand

Two of the runs above started in the middle of a brainstorm in another repo. The model wanted to
get back to the main task, so it ran the search in two agents and moved on.

Why it's wrong: the user still gets an advisor built on that search. Start the workflow, which
runs in the background, and carry on with the main task while it works. Don't shrink the search.
