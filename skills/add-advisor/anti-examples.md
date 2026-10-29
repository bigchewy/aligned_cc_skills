# Anti-Examples: How Add Advisor Gets Run Badly

Each of these happened in a real run between 2026-09-29 and 2026-10-28.

## One framework built when three were picked

Wrong: four advisors were added for a wedding product. Each got one framework. When the user
asked "Did you add all the appropriate frameworks and detail, or did you half-ass this?", the run
answered: "One framework each, when the skill says to pick the top 2–3. The skill's own minimum
is to build the first one, and that's all I did."

Right: Step 5 builds every framework selected in Step 2. Candidates that weren't selected are
listed in the prompt as "also available in conversation," and the report says why each wasn't
built.

## The work never read

Wrong: the same run said "I didn't read the work. I read the first 30 lines of Parker's prompt
and nothing of the other three prompts or the four frameworks. The agents' reports on which
phrases they checked are what I relied on."

Right: a fresh agent reads every file against `report-template.md` before the report goes out.
The run that skipped this turned out to have frameworks use-framework couldn't load.

## Framework files written by hand

Wrong: "I didn't use `/aligned:add-framework`. The agents wrote the framework files directly,
and I added the registry entries by hand."

Right: run `/aligned:add-framework` for each framework. Its source check and its final check
only happen if the skill runs.

## No research file

Wrong: an advisor for a low-histamine diet was added in the middle of a health question, after a
few searches and one opened page. No research file was written, so nobody can tell which
phrases in the prompt are real.

Right: every advisor gets a research file with sources, 8 to 12 real quotes with URLs, and
framework candidates with their sources, wherever the skill was started from.

## Evals skipped for a reason that wasn't true

Wrong: two runs skipped the eval because "no ANTHROPIC_API_KEY." The eval runner uses the Claude
Code login and never needed the key.

Right: run the scenario with `npm run eval -- <scenario-path>`. If it fails, quote the error in
the report.

## A one-product framework put in the plugin

Wrong: a framework about how much two sibling brands should share went into the plugin, where
every user of the plugin sees it. The user said it was "very specific to just this one repo."

Right: a framework that only makes sense for one product goes in that project's `frameworks/`.

## Voice phrases from memory

Wrong: "How You Speak" lists phrases that sound like the person but appear in no source. The eval
then scores the prompt against phrases it made up itself.

Right: every phrase in quotation marks appears word for word in the research file with its URL.
Lines in their style go outside quotation marks.
