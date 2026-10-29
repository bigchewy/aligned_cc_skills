# Report Template for Add Advisor

Step 10 uses this file twice. A fresh agent runs the "Check agent" section. Then the main
session reports to the user in the "Report" shape.

## Check agent

You wrote none of these files. Your job is to find problems, not to fix them. You get the paths
of everything the run wrote and the research file.

1. **Research file.** Does it exist, with Sources, Voice, Framework candidates and "From memory,
   not checked"? Does every source have a URL?
2. **Voice.** For each phrase in quotation marks under "How You Speak", find it word for word in
   the research file. Open 3 of their URLs (the first, one from the middle, the last) and confirm
   the words are on the page.
3. **Prompt sections.** The prompt has all seven sections of the Step 4 structure. Its first line
   reads `You are {Name}, ...`, so use-advisor can read the name.
4. **Frameworks.** Every framework selected in Step 2 has a folder with `prompt.md`,
   `examples.md`, `anti-examples.md` and `sources.md`. Each `prompt.md` first line reads
   `You are {Advisor}, guiding someone through {Framework} - {purpose}.` Each folder is in the
   right place: the plugin for frameworks useful to anyone, the project repo for one-product
   frameworks.
5. **Registries.** Both registry files parse as YAML, and they hold entries for the advisor and
   for every framework.
6. **Evals.** If the repo has `e2e/run_evals.py`, a scenario exists for the advisor and for each
   framework. The run shows a score or a quoted error. "No API key" is not a reason to skip.
7. **Counts.** Writing to the plugin: the counts in `README.md`, both manifests,
   `advisors/README.md` and `frameworks/README.md` match the registries.

Return `problems`: one specific sentence each, naming the file and what's wrong. Return an empty
list if you found none.

## Report

What the main session tells the user, in this order:

1. **Done:** the advisor's name and where the prompt lives, in one sentence.
2. **Frameworks:** each one built, with its path. Then the candidates listed as "also available
   in conversation," and why each wasn't built.
3. **Sources:** the research file's path and how many sources it has.
4. **Evals:** each scenario with its score, or the quoted error.
5. **Check:** what the fresh agent found and how each problem was fixed, or "Found nothing."

## What was skipped or not done

Every report ends with this section. List each step skipped or done partly, and why. List each
fact in the research file marked "From memory, not checked." Write "Nothing" only when there is
nothing to list.
