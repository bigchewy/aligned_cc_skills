# Framework flows — first pass (2026-11-03)

Every framework prompt was read and sorted into flows under I / We / It, scoped by org type
(pre-PMF, post-PMF B2B, post-PMF B2C). Interactive review page: https://claude.ai/artifact/1vyEkiuMzUQx7jKC1w7pLk

- `prompt-readings.json` — one record per framework from reading its prompt: what it does, inputs,
  output, org types, upstream/downstream, overlaps, registry issues. Taken as of the commit before the registry fixes.
- `draft-flows.py` — the draft: 26 flows (I 6, We 7, It 13), 8 frameworks unplaced.
- `reader-brief.md` — the brief the readers followed.

Factual registry fixes are applied (see the `fix: framework registry matches what each prompt does` commit).

## Open decisions

1. For each of the 8 same-job groups, pick one entry point; the rest merge in, run after it, or go:
   check-ins (presence-check-in, quadrinity, energy-audit); manager levels (leadership-pipeline-passages,
   management-level-progression, performance-standards-by-level); 5-step / 6-step process;
   leap-of-faith-assumptions / build-measure-learn; working-backwards / start-with-experience;
   storybrand-homepage / landing-page-assembly; 5-components-positioning / positioning-canvas;
   80-20-audit / zone-of-genius.
2. The 8 unplaced: personal-context-intake, professional-context-intake, the-story-so-far (depend on
   host setup the plugin doesn't ship); reverse-engineered-brand (runs a whole flow); idiot-index,
   the-algorithm, close-the-loop, stage-the-picture (not company work).
3. Portability: launch-bet is written for one event-site project; landing-page-assembly needs a hosted runtime.
4. Does B2C get its own flows (acquisition, retention loops, community) or stay a filter?
5. Pre-PMF "We": nothing helps cofounders agree on roles.
6. Category set: personal frameworks are filed under `leadership`/`psychology`/`strategy`; decide whether
   I / We / It becomes a field, or the categories get redrawn.
7. Then write `flows.yaml` (validated like `skills/org-chart/seats.yaml`) and build the playbook visual from it.
