# Framework flow-mapping pass — reader brief

Repo: /home/user/aligned_cc_skills (an advisory plugin: advisors + interactive frameworks for running a company).
Goal of the overall pass: organize all 116 frameworks into a set of **flows** (chains where one framework's output feeds the next), scoped by **org type**, and find out how cleanly each framework maps. The YAML metadata is believed to be inaccurate, so the PROMPT is the source of truth.

## Your job
For EACH framework id in your chunk file:
1. Read `frameworks/<id>/prompt.md` in full (frontmatter + body). Skim examples.md only if the prompt is unclear.
2. Read that framework's entry in `frameworks/registry.yaml` (fields: name, advisor, deliverable_type, domains, purpose, use_when, follow_on_frameworks, required_documents, helpful_documents, default_critic_advisors).
3. Record one JSON object (schema below). Judge from what the prompt actually makes the user do and produce.

You may glance at other frameworks' registry entries (purpose/use_when) to name upstream/downstream/overlap ids — those ids must be real ids from registry.yaml.

## Org types (scope)
- `pre_pmf`: searching for product-market fit. Founder-led, few customers, idea/problem/MVP validation, first sales by founders.
- `post_pmf_b2b`: has PMF, selling to businesses, building a team/sales org, scaling.
- `post_pmf_b2c`: has PMF, selling to consumers, growth/retention/brand at scale.
List every type where the framework genuinely earns its place. "Any company" frameworks (personal leadership, decision-making) list all three and set `stage_agnostic: true`. Be strict: a PMF-search framework is NOT post-PMF just because it could be re-run.

## Function (pick one primary)
strategy | positioning-messaging | brand-identity | content-seo | growth-marketing | conversion-copy | sales | pricing-monetization | product-discovery | product-delivery | design-ux | customer-retention | leadership-self | team-people-org | operating-cadence | decision-making | learning-design | data-viz | security-eng | other

## Output schema (one object per framework)
{
  "id": "",
  "does": "one plain sentence: what the user actually walks through and ends with",
  "trigger": "the situation that makes someone reach for it (from the prompt, plain words)",
  "inputs": ["what it needs before starting; name the upstream document if it is another framework's output"],
  "output": "the artifact/decision it produces, named concretely (e.g. 'positioning.md with 5 components')",
  "function": "",
  "org_types": ["pre_pmf","post_pmf_b2b","post_pmf_b2c"],
  "stage_agnostic": false,
  "stage_notes": "why, esp. if partial (e.g. 'B2B-only: assumes buying committee')",
  "upstream": [{"id":"", "why":"", "strength":"requires|helps"}],
  "downstream": [{"id":"", "why":"", "strength":"requires|helps"}],
  "loop_with": ["ids it is genuinely run in a repeating cycle with, if any"],
  "overlaps": [{"id":"", "how":"same job | partial | subset", "note":""}],
  "flow_guess": "short name of the chain/job it belongs in, e.g. 'Find PMF', 'Position & message', 'Build the sales machine', 'Personal leadership' — or 'standalone'",
  "flow_position": "start|middle|end|standalone",
  "fit": "clean|fuzzy|misfit",
  "fit_reason": "why it does/doesn't slot into one flow cleanly",
  "registry_issues": [{"field":"", "registry_says":"", "prompt_shows":"", "severity":"wrong|stale|vague|missing"}],
  "frontmatter_issues": ["mismatches between prompt.md frontmatter and the registry, or frontmatter fields that are wrong vs the body"]
}

Rules:
- Evidence over vibes. If the prompt names another framework or a document produced by one, that is a `requires` or `helps` edge. If you infer a logical edge, mark it `helps` and say why.
- Report registry issues only when real (purpose that doesn't match the body, follow_on that points somewhere illogical, missing obvious required doc, wrong deliverable_type). Empty list is fine.
- Keep strings short. No prose outside the JSON.
- Do NOT edit any repo files.

## Output
Write a JSON array to `<scratchpad>/flows/out<N>.json` (path given in your task), valid JSON, every id in your chunk present exactly once. Then reply with: count written, and a 5-line summary of the biggest surprises (overlaps, misfits, worst registry errors).
