# Anti-Examples: How Add Framework Gets Run Badly

Each of these happened in a real run between 2026-10-06 and 2026-11-17.

## Examples written only where one came to mind

Wrong: a run built three frameworks in one turn and reported them done. 12 of 24 phases had
fewer than two examples, and the closing phase of all three had none. It never opened the model
file. It wrote its own list for the check agent, and that list didn't count examples. Its
"What was skipped" section didn't mention them.

Right: every phase gets at least 2 examples, the closing phase included. Run
`check_framework.py` and paste its output in the report. Give the check agent the template file
as it is.

## Phases the expert never wrote

Wrong: a framework for Steve Blank laid out six phases for a deck, voiced as Blank. When it was
checked, the run found that "Blank's book has no slide-by-slide script." The phases were made up
and credited to him.

Right: find the method in the expert's own work before building. If they never described one,
say so and stop. A phase you add yourself goes in `sources.md` starting `Added:`.

## A one-product framework in the plugin

Wrong: a framework about how much two sibling brands should share went into the plugin, built
from other authors' brand-family rules in Michael Bierut's voice. The user said it was "very
specific to just this one repo."

Right: a framework for one product goes in that project's `frameworks/`. And it has to be the
expert's own method (see above).

## README counts missed

Wrong: a run updated the counts in `README.md` and the two manifests, but not
`frameworks/README.md`. The next two runs hit a failing count test that the earlier commit had
caused.

Right: update `frameworks/README.md` too, and run `e2e/tests/test_readme_freshness.py` if it
exists.

## Eval skipped for a reason that wasn't true

Wrong: the run started from inside a deck task skipped the eval because "no ANTHROPIC_API_KEY,"
then went back to the deck.

Right: the eval runner uses the Claude Code login. Run the scenario. If it fails, quote the error
in the report.
