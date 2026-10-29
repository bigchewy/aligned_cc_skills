# Report Template for Add Framework

Step 9 uses this file twice. A fresh agent runs the "Check agent" section. Then the main session
reports to the user in the "Report" shape.

## Check agent

You wrote none of these files. Your job is to find problems, not to fix them. You get the
framework folder and the registry path.

1. **Files.** The folder has `prompt.md`, `examples.md`, `anti-examples.md` and `sources.md`.
2. **First line.** After any YAML frontmatter, the first line of `prompt.md` reads
   `You are {Advisor}, guiding someone through {Framework} - {purpose}.` The resolver and the
   runner read the advisor's name from it, so a different form leaves the framework unloadable.
   The advisor named there resolves to an advisor in the plugin or project registry.
3. **Pauses.** Every phase that asks the user something ends with a WAIT marker.
   **Artifact.** `prompt.md` has an `## Artifact` section. Every section of the page it
   describes is filled by a named phase.
4. **Sources.** Every phase in `prompt.md` has a line in `sources.md`, either with a source or
   starting `Added:`. Open 3 of the URLs (the first, one from the middle, the last) and confirm
   each page describes what the line says. Every quote or story attributed to the expert in
   `examples.md` appears in `sources.md` with a URL.
5. **Place.** A framework for one product, brand or codebase is in the project repo, not the
   plugin.
6. **Registry.** The registry parses as YAML. The entry's category already exists in the
   registry, or the user approved a new one.
7. **Eval.** If the repo has `e2e/run_evals.py`, a scenario exists and the run shows a score or
   a quoted error.
8. **Counts.** Writing to the plugin: the counts in `README.md`, both manifests and
   `frameworks/README.md` match the registry.

Return `problems`: one specific sentence each, naming the file and what's wrong. Return an empty
list if you found none.

## Report

What the main session tells the user, in this order:

1. **Done:** the framework's name, its advisor, and its path, in one sentence.
2. **Where it comes from:** the main source, and how many phases are marked `Added:`.
3. **Eval:** the score, or the quoted error.
4. **Check:** what the fresh agent found and how each problem was fixed, or "Found nothing."

## What was skipped or not done

Every report ends with this section. List each step skipped or done partly, and why. List each
phase marked `Added:`. Write "Nothing" only when there is nothing to list.
