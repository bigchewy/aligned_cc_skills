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

Also removed later on 2026-11-02: Oli Gardner, whose only framework was landing-page-assembly.

## Decided (2026-11-02): frameworks with no flow

| Framework | Decision |
|---|---|
| personal-context-intake, professional-context-intake, the-story-so-far | Deleted. They were built for va-web-app, which keeps its own copies in `src/lib/frameworks/prompts/`. They write to its profile page and read its session history, neither of which the plugin has. |
| idiot-index | Deleted. It compares a product's finished cost to its raw-material cost; a software company rarely has raw materials. The idea stays in Elon Musk's advisor prompt. |
| reverse-engineered-brand | Kept as the fast path for the "Position and message" flow: it runs that flow's frameworks at once. flows.yaml marks it as a flow runner, not a step. |
| the-algorithm | Kept, in an It flow for fixing operations, next to 6-step-process. |
| close-the-loop | Kept on the CTO and software engineer seats, outside the I / We / It flows. It is Boris Cherny's only framework. |
| stage-the-picture | Moved to the moments repo earlier. |

## Open decisions

1. ~~Same-job groups~~ — decided above.
2. ~~The unplaced frameworks~~ — decided above.
3. ~~Portability~~ — done 2026-11-02. launch-bet now works for any one-customer launch; the moments
   site-launch version lives in the moments repo as a local framework. landing-page-assembly is deleted.
4. ~~B2C~~ — decided 2026-11-02: post-PMF B2C gets its own flows. It is different enough from B2B
   that a filter isn't enough.
5. ~~Pre-PMF "We" gap~~ — decided 2026-11-02: leave it. No framework for cofounders agreeing on roles.
6. Category set: personal frameworks are filed under `leadership`/`psychology`/`strategy`; decide whether
   I / We / It becomes a field, or the categories get redrawn.
7. Then write `flows.yaml` (validated like `skills/org-chart/seats.yaml`) and build the playbook visual from it.
