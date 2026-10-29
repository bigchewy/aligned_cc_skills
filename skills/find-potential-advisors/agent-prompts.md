# Agent Prompts for Find Potential Advisors

Each section is the instructions for one kind of agent. `workflow.js` points each agent at its
section. The Agent-tool fallback in `SKILL.md` does the same. Change the words here, not in the
script.

Rules for every agent:

- Search with `WebSearch` and read pages with `WebFetch`. Never use `Bash(curl)`. It leaves
  stale permission entries behind. If those tools are deferred, load them with ToolSearch
  `select:WebSearch,WebFetch`.
- A source is a page you opened with `WebFetch`. A search-result snippet is a lead, not a
  source. Never put a snippet's URL down as the source for a fact.
- Something you know from memory but didn't open a page for goes in the `unverified` or
  `not_found` list. It never goes in a sourced field.
- If a page won't open (403, paywall, size limit), say which page it was in `not_found` or
  `unverified`. Then try another page for the same fact.

## Research

You answer one research question about the domain in the brief. Read the brief first.

1. Run 3 to 5 searches. Phrase each one differently.
2. Open at least 3 pages. Search-result pages don't count. Open more if the first three disagree.
   - For a domain with research behind it (health, learning, behavior change), open systematic
     reviews, meta-analyses and guidelines first.
   - For a practitioner domain (design, marketing, growth), open the practitioners' own writing
     and the long interviews where they explain their method.
3. Stop when new pages repeat what you already have, and not before you've opened 3.

Return:
- `findings`: each claim with the URL of the page it came from, and the page type (review,
  guideline, own essay, interview, news).
- `approaches`: the methods or schools of thought that have the best support, with their URLs.
- `names_mentioned`: people the pages name as leading figures, with why and the URL.
- `pages_opened`: how many pages you opened with `WebFetch`.

## Candidates

You turn the research into a list of candidates. You get the research findings, how many
candidates to pick, and who is already on the board.

1. Read the brief.
2. Start from `names_mentioned` and `approaches`. Run up to 3 more searches to fill gaps, for
   example an approach with no named person or a region with no one.
3. Pick people who:
   - are recognized for a method the research supports,
   - have a large public body of work (books, talks, podcasts, essays), and
   - have a voice of their own: their own terms, their own way of explaining.
4. Leave out anyone already on the board. Leave out anyone whose method is the same as an
   existing advisor's.
5. Cover more than one approach. Ten people from one school is a bad list.
6. If someone has died, say so in `credentials`. That person can still be a candidate.

Return `candidates`: name, credentials, why you considered them, and a URL of a page you opened
that shows their standing.

## Profile

You profile 2 or 3 candidates in depth. Read the brief first.

For each candidate:
1. Open their own site or bio page, and their publisher or employer page. Confirm their current
   role there.
2. Open at least one source in their own words, such as an essay, a talk page or an interview
   transcript. Use it to describe their method.
3. List their key works, each with a URL you opened.
4. Say how they fit the brief: which part of the user's situation they would help with, and
   where they wouldn't.

Return `profiles`: name, credentials, approach, key works with URLs, fit, the URLs you used, and
`unverified`. `unverified` holds anything you believe but couldn't confirm on a page. Write
"From memory, not checked:" in front of each item.

## Evaluate

You did not pick these people and you did not profile them. Your job is to count their public
material, not to argue for them. You get names only. Find every source yourself.

For each candidate:
1. **Books.** Open the publisher page or the author's own books page. List each book with its
   year and that URL. A book you can't find on a page goes in `not_found`.
2. **Talks and podcasts.** Open each episode or video page. Write down the length shown on the
   page in minutes, with the URL. Never estimate a length. If the page doesn't show one, write 0
   and add the episode to `not_found`. Only count a recording someone can play. A conference
   schedule slot or a webinar sign-up page shows a planned length, not a recording, so it counts
   as 0. Keep going until you've listed at least 5 hours, or until you run out after 6 searches.
3. **Distinctive terms.** List 3 to 6 terms or phrases that are theirs, each with the URL of a
   page where they use it. A page by someone else that writes about them doesn't count.
4. **Quotes.** Copy 2 or 3 real sentences from a page you opened, each under 30 words, with the
   URL. Copy them word for word. Don't paraphrase.
5. **Availability.** Say what is free to read or watch and what is behind a paywall.

Return `evaluations` with those fields and `not_found`. Don't give a rating. The script works it
out from what you counted. If you're running without the script, the rating rubric is in
`report-template.md` under Evaluation.

## Finalists

You pick 2 or 3 finalists from the strong candidates. Their ratings are already set from counted
sources. Don't change them.

1. Read the brief, including the hypothetical situation in it.
2. Pick 2 or 3 finalists. Weigh fit to the brief first, then the rating.
3. For each finalist, write:
   - `summary`: who they are and their approach, in 2 or 3 sentences.
   - `differentiation`: how they differ from each board member named as nearby in the brief.
   - `framework_potential`: 1 to 3 frameworks that could be built from their published method.
     Name the source for each.
   - `voice_sample`: their answer to the brief's hypothetical situation, 3 to 5 sentences. Build
     it from their quotes and terms in the evaluation. Words in quotation marks must be real
     quotes. Put the URLs of the quotes you drew on in `voice_sample_quote_urls`.
   - `tradeoffs`: what they're good and bad at compared with the other finalists.
4. Pick one to recommend, and give the reason in one or two sentences.

## Write

You fill in the report in the brief file. You get the run data as JSON.

1. Read `report-template.md` in the same folder as this file. Then read the brief.
2. Leave the Brief section as it is. Add the other sections after it, in the template's order.
3. Fill every field from the run data only. Don't add a fact, a work or a quote that isn't in the
   data.
4. Build "What was skipped or not verified" from three places: `skipped`, every profile's
   `unverified`, and every evaluation's `not_found`. Write "Nothing" only if all three are empty.
5. Fill the Run record from `agents_run` and `pages_opened`.
6. Fill the Chat summary last. The main session pastes it to the user.

If the run stopped before finalists, fill the sections up to Evaluation. Fill "What was skipped
or not verified", the Run record and the Chat summary too. In the Chat summary, say that fewer
than 2 candidates rated High or Medium. Then give the three choices: widen the search, lower the
bar, or go ahead with the best candidate.

Return the brief's path.

## Check

You did not write this brief. Read `report-template.md` in the same folder as this file, then
read the brief. Look for problems.

1. **Sections.** Is every section from the template there and filled? Is "What was skipped or
   not verified" present even when it says "Nothing"?
2. **Ratings.** For each candidate in the Evaluation table, recount from the listed items using
   the rubric. Do the books, minutes and terms each have a URL? Does the hour total equal the sum
   of the minutes listed?
3. **Sources.** For each finalist, open 3 of their cited URLs: the first, one from the middle,
   and the last. Does each page support what the brief says it does? Is the book on the page?
   Is the length shown? Does the quote appear word for word?
4. **Voice samples.** Does every phrase in quotation marks appear in a quote with a URL?
5. **Memory.** Is any fact in a finalist's summary marked as from memory without also being
   listed in "What was skipped or not verified"?

Return `problems`. Write each one as a specific sentence that names the finalist, the field and
the URL. Return an empty list if you found none. Don't fix anything yourself.

## Fix

You get the brief and a list of problems found by the check. Fix each problem in the brief.

- If a fact can be backed up, open the page and add its URL.
- If it can't, remove it from the brief and add a line to "What was skipped or not verified"
  that says what was removed and why.
- If a rating changes, update the Evaluation table, the Finalists and the Chat summary.
- Never add a new fact without a URL.

Return `fixed: true` when every problem is dealt with.
