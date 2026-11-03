# Framework flows — first pass (2026-11-03)

Every framework prompt was read and sorted into flows under I / We / It, scoped by org type
(pre-PMF, post-PMF B2B, post-PMF B2C). Interactive review page: https://claude.ai/artifact/1vyEkiuMzUQx7jKC1w7pLk

- `prompt-readings.json` — one record per framework from reading its prompt: what it does, inputs,
  output, org types, upstream/downstream, overlaps, registry issues. Taken as of the commit before the registry fixes.
- `draft-flows.py` — the draft: 26 flows (I 6, We 7, It 13), 8 frameworks unplaced.
- `reader-brief.md` — the brief the readers followed.

Factual registry fixes are applied (see the `fix: framework registry matches what each prompt does` commit).

## Decided (2026-11-02): same-job groups and other overlaps

Eric's rule going forward: simplify wherever two frameworks do the same job.

| Group | Decision |
|---|---|
| Check-ins | Keep energy-audit and quadrinity; they share a core idea but run differently. presence-check-in is an optional warm-up before any personal (I) flow. |
| Manager levels | Keep performance-standards-by-level; it already covers self-diagnosis and is a superset of leadership-pipeline-passages. Delete leadership-pipeline-passages. Delete management-level-progression and the Lara Hogan advisor, her only framework. |
| 5-step / 6-step | Keep 6-step-process. Delete 5-step-process. |
| Assumptions | leap-of-faith-assumptions first, then build-measure-learn. build-measure-learn drops its own riskiest-assumption phase and takes it from leap-of-faith. |
| Product definition | Start with working-backwards, then getting-real-cut. Delete start-with-experience: working-backwards already starts from the experience, and getting-real-cut does the feature cut. |
| Homepage | Keep storybrand-homepage. Delete landing-page-assembly: it was the agent script for the epch app (epch.vercel.app), which now uses its own TypeScript pipeline. |
| Positioning | Keep 5-components-positioning. Delete positioning-canvas; it re-asks the same five components. |
| Personal focus | 80-20-audit first, then zone-of-genius. Delete past-year-review. |
| Shirin Oreizy | Move science-of-design, homer-vs-spock, cognitive-friction-audit and her advisor to the `~/Documents/aligned` project. |
| Chris Voss | Move accusation-audit, calibrated-questions, tactical-empathy-labeling and his advisor to the `~/Documents/aligned` project. |
| Kept on purpose | 100-percent-responsibility and pillars-of-integrity (the second is larger); fear-setting and regret-minimization (different people, different approach); living-into-values and personal-credo (different systems); the three Rumelt frameworks; ICE inside growth-hacking-process; chj-operating-review and mochary-weekly-check-in; both Aleyda Solis SEO frameworks; both Bierut logo frameworks; strategic-narrative feeding sales-pitch-structure; buyer-persona and mobilizer-taxonomy; the Steve Blank pair; breadboard-to-pages and interface-inventory. |

**Systems inside I / We / It.** Some frameworks belong to one system. Loehr's energy system
(energy-audit, stress-recovery-oscillation, personal-credo) is the first example, under I. flows.yaml
and the playbook visual must show a system as one area of focus that holds several frameworks.

## Open decisions

1. ~~Same-job groups~~ — decided above.
2. The 8 unplaced (stage-the-picture has since moved to the moments repo): personal-context-intake, professional-context-intake, the-story-so-far (depend on
   host setup the plugin doesn't ship); reverse-engineered-brand (runs a whole flow); idiot-index,
   the-algorithm, close-the-loop, stage-the-picture (not company work).
3. Portability: launch-bet is written for one event-site project; landing-page-assembly needs a hosted runtime.
4. Does B2C get its own flows (acquisition, retention loops, community) or stay a filter?
5. Pre-PMF "We": nothing helps cofounders agree on roles.
6. Category set: personal frameworks are filed under `leadership`/`psychology`/`strategy`; decide whether
   I / We / It becomes a field, or the categories get redrawn.
7. Then write `flows.yaml` (validated like `skills/org-chart/seats.yaml`) and build the playbook visual from it.
