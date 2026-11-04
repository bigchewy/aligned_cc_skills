# Playbook: Design

Date: 2026-11-02
Status: draft, waiting on Eric's review. Updated 2026-11-03 with the advisor panel's changes (Claire Hughes Johnson, Matt Mochary, Gino Wickman), which Eric accepted.
Asana: "Aligned: organize frameworks into I / We / It playbook flows", subtasks 6, 7 and 8

## The answer

Every framework in the plugin gets a home on a three-level map: layer (I, We or It), then area, then framework. A new file, `skills/playbook/layers.yaml`, holds that map. The 22 old categories go away. Each area names one framework to start with, and every box on the map shows the framework's `use_when` line, so a CEO can find a tool from the problem in front of them. Flows are not written down anywhere. The playbook page draws them from what each framework needs before it can run: the documents it must have and the documents that help, each linked to the framework that writes it. A CEO runs `/aligned:playbook`, opens the map, picks a framework, and sees everything that should come before it. The builder drafts the 226 document links and ships them. Eric reviews them later on an editable page, least confident first.

## Why

The categories were made up a year ago, one at a time, and nobody owns them. "Psychology," "leadership" and "strategy" each hold a mix of personal, team and company tools. A CEO can't use them to find the right tool for the problem in front of them.

Three views of the same 98 frameworks answer three different questions:

| View | Question it answers | Where it lives |
|---|---|---|
| Layers and areas | What kind of work is this: on me, on the team, or on the company? | `skills/playbook/layers.yaml` (new) |
| Seats | Who in the company does this work? | `skills/org-chart/seats.yaml` (exists) |
| Flows | What should be in place before I run this one? | Drawn from each framework's documents in `frameworks/registry.yaml` |

The registry stays the one place that says a framework exists and what it needs. The layers view and the seats view only list framework ids.

## Goals

1. Every framework sits in at least one area, or on a holding list with a reason.
2. A framework can sit in more than one area. 6-step-process sits in We (solving problems together) and in It (operations).
3. For any framework, the page shows what must come first and what helps, and says which framework writes each document or that it comes from outside the plugin.
4. Each framework says which company stages it fits and whether it is for B2B or B2C companies, when that matters.
5. The map stays true to the registry. Adding or deleting a framework fails a test until the map is updated, and the pages rebuild on commit.
6. A CEO who arrives with a problem and no framework in mind can find where to start: one start-here framework per area, the `use_when` line on every box, and a stage filter.
7. Every document a We framework needs has a framework that writes it. `proximate-objectives` writes the quarterly goals that `mochary-weekly-check-in` and `chj-operating-review` need. The build report lists every required document still sourced from outside the plugin, as the list of frameworks to build next.
8. Every It framework page ends with: "Put the result into your Top Goal or your next check-in." (Matt Mochary)

## Non-goals

- Named flows. A flow has no title or question of its own. (Eric)
- Flows in I. Personal tools stand alone; the page draws no predecessor arrows inside I. (Eric)
- Arrows into We. Claire Hughes Johnson and Gino Wickman asked for one arrow from Operating rhythm and Org design back to the It framework that writes their document. Eric said no on 2026-11-03: only It has flows. A We framework's panel lists its documents and who writes them.
- A start-here framework for each area at each stage. That would be up to 130 picks to keep current. Stage works as a filter instead.
- A B2B map and a B2C map. B2B and B2C companies get different structures only on the org chart. (Eric, 2026-11-02. This replaces the earlier decision that B2C gets its own flows; `docs/framework-flows/README.md` item 4 is updated to say so.)
- Showing a client's own project-local frameworks on the playbook. The org chart doesn't show them either.
- Changing `domains`, which drives contextual recommendation scoring.
- A checkup or scoring page for each area. Gino Wickman argued for one; Eric kept it out.

## Anti-goals

- A page that reads as a library of 98 tools with no way in.
- A map that goes stale when a framework is added or deleted.
- Two places that both claim to say what comes before a framework.

## Constraints

- Portability rule (`CLAUDE.md`): every shipped step works for any user who installs the plugin.
- The pages open from a local file. Links are relative. No script loads from the network.
- No design-principles file exists in this repo. The pages use the org chart's tokens in `scripts/org-chart-templates/style.css`.
- Tests are pytest files in `e2e/tests/`.
- The pre-commit hook (`scripts/hooks/pre-commit`) rebuilds the org chart and bumps the version. Do not bump by hand.
- `prompt.md` frontmatter repeats each framework's document lists, and the framework runner reads them from either place (`skills/_shared/framework-runner.md:46`).

## Approaches

1. **`layers.yaml` lists framework ids under each area; the registry holds no grouping. Picked by Eric.** This is how `seats.yaml` already works, with its checks and holding list. The same id under two areas puts a framework in two places. The registry's shape stays the same apart from removing `category`. The architect recommended this one.
2. **An `area` field on each registry entry, plus a short `layers.yaml` for layer and area names.** A framework's home shows where it is defined. Sitting in two areas turns the field into a list, which breaks every place that reads it as one value. When a project-local entry has the same id as a plugin entry, it replaces the whole entry and drops the area. Rejected.

## Part 1: The map

### `skills/playbook/layers.yaml`

```yaml
layers:
  - id: i
    name: I
    does: Work on yourself.
    areas:
      - id: energy
        name: Energy
        note: Jim Loehr's energy system.
        start: energy-audit
        frameworks: [energy-audit, stress-recovery-oscillation, personal-credo]
holding:
  - id: close-the-loop
    why: How a team sets up Claude Code. It lives on the CTO and software engineer seats.
```

`start` names the one framework a CEO runs first in that area. It is required and must be in the area's list.

The draft is `docs/framework-flows/layers-draft.yaml`: 5 areas under I, 5 under We, 10 under It, with all 98 frameworks placed. The panel cut it from 26 areas: every area that held one framework merged into a neighbor, Presence joined Responsibility, Design system and Security moved under Product, and Marketing and Growth merged. Positioning and Brand stay apart because they do two jobs: why we win, and how we look. Data stays its own area because its frameworks teach how to present a chart, which is different work from running a process. Eric reviews the areas on the design page before the draft becomes the real file.

### The areas in the draft

| Layer | Area | Start here |
|---|---|---|
| I | Energy (Jim Loehr's system) | `energy-audit` |
| I | Presence and responsibility (Conscious Leadership) | `above-below-the-line` |
| I | Courage and values | `living-into-values` |
| I | Focus | `personal-resource-allocation` |
| I | Decisions (now holds `earnestness-filter`) | `type-1-type-2-decisions` |
| We | Trust and clearing | `braving-trust-inventory` |
| We | Solving problems together (also holds `type-1-type-2-decisions`) | `root-cause-analysis` |
| We | Operating rhythm (was Cadence) | `mochary-weekly-check-in` |
| We | Org design and people (now holds `performance-standards-by-level`) | `rules-of-structure` |
| We | Learning and change | `behavior-gap-diagnosis` |
| It | Strategy | `lifecycle-strategy` |
| It | Operations | `the-algorithm` |
| It | Product-market fit | `four-market-types` |
| It | Offer and pricing | `blue-ocean-value-props` |
| It | Positioning and messaging | `5-components-positioning` |
| It | Brand | `brand-voice` |
| It | Marketing and growth | `storybrand-homepage` |
| It | Sales | `bowtie-funnel` |
| It | Product (now holds design system, security and `assigning-ai-roles`) | `frame-shape-bet` |
| It | Data | `big-idea-and-takeaway-title` |

The start-here picks are my calls. `lifecycle-strategy` starts Strategy because it tells the CEO which stage they are in, and the stage drives the filter. When the stage filter hides an area's start-here framework, the area shows no start mark.

### Checks (`e2e/tests/test_playbook.py`)

- Every area has a `start`, and it is in that area's list.
- Every registry framework sits in at least one area or on the holding list.
- No id in `layers.yaml` is missing from the registry.
- No framework is both placed and held.
- Area ids are unique across the file.
- The build prints every framework that sits in two or more areas, so a second area is always a choice someone made.

## Part 2: Predecessors

### What changes in the registry

Each entry in `required_documents` and `helpful_documents` becomes a document name plus where it comes from:

```yaml
required_documents:
  - doc: positioning statement
    from: 5-components-positioning
helpful_documents:
  - doc: customer research
    from: outside
```

`from` is a framework id, a list of ids when more than one framework can write the document (company strategy can come from `kernel-of-good-strategy` or `lifecycle-strategy`), or the word `outside`. A required document is a must-have; a helpful one helps. With a list, any one of those frameworks meets a required document. There are 226 document entries across 73 frameworks. The builder drafts every `from` and commits it, and the pages ship with those drafts. The build does not stop for Eric's review. (Eric, 2026-11-03.)

As it drafts each link, the builder also records how sure it is and why, in `docs/framework-flows/link-review.yaml`. That file feeds the review page in Part 7. Confidence stays out of the registry, because the registry says what is true and the review file says what still needs checking.

```yaml
- id: sales-pitch-structure/positioning-statement
  framework: sales-pitch-structure
  doc: positioning statement
  kind: required          # or helpful
  from: 5-components-positioning
  confidence: sure        # sure, likely or guess
  reason: 5 Components writes the positioning statement as its output.
```

- **sure**: the writing framework names this document as its output, or the document is plainly the user's own material and comes from outside.
- **likely**: one framework fits, but its output goes by a different name.
- **guess**: more than one framework could write it, or a plugin framework might write a document now marked outside.

`proximate-objectives` is the `from` for the quarterly goals that `mochary-weekly-check-in` and `chj-operating-review` need. The build report lists every required document whose `from` is `outside`. That list shows which frameworks to build next.

### Project-local frameworks

- The resolver and the runner accept both forms, plain strings and `doc` plus `from`. Existing local registries keep working unchanged.
- A local `from` may name a local framework id.
- The playbook shows plugin frameworks only and reads only the plugin registry. A local entry can't change its arrows.

### Where the arrows come from

- A solid arrow runs from the framework that writes a required document to the framework that needs it.
- A dashed arrow does the same for a helpful document.
- Outside documents show in the framework's panel with no arrow.
- The page draws an arrow only when the framework that needs the document sits in It. The framework that writes it can be in any layer, so We and I frameworks can feed It.
- A framework in I or We gets no upstream graph. Its panel still lists its documents and who writes them.
- A framework that sits in It and in another layer counts as It. (My call.)
- No arrow ever points into a We or I framework. (Eric, 2026-11-03.)

### `follow_on_frameworks` retires

The documents replace it, so there is one source for arrows. Before it goes, the builder checks each of its 52 links: if no document link already covers it, the builder adds the document that link stood for, or lists the link for Eric to drop. `e2e/tests/test_framework_handoffs.py` moves to checking document links instead.

### Checks

- Every `from` is a registry id, a list of them, or `outside`.
- No framework needs its own output.
- Required links never loop. A loop through helpful links is allowed and drawn once.
- A framework tagged with a market must feed at least one framework that is either untagged or tagged with the same market. A writer tagged B2C that feeds only B2B frameworks fails. This is how `origin-story-interview` was caught: it was tagged B2C and fed only B2B frameworks. (Claire Hughes Johnson)
- Every entry in `link-review.yaml` matches a link in the registry (same id, kind and `from`). The check runs one way only: the review file is a one-time review that shrinks as I answer links, and nothing writes it when a framework is added, so the registry may have links the file lacks.
- `prompt.md` frontmatter keeps plain document names, so the runner reads it unchanged. A test checks the names match the registry, and `tools/sync_framework_frontmatter.py` writes them.

## Part 3: Stage and market tags

Two optional fields on each registry entry:

- `stages`: one or more of `idea`, `pilot`, `nail-it`, `scale-it`, `milk-it`. Left off means any stage. The names match Lex Sisney's lifecycle in `lifecycle-strategy` (Pilot It, Nail It, Scale It, Milk It), with Idea before Pilot.
- `market`: `b2b` or `b2c`. Left off means both.

The draft is `docs/framework-flows/tags-draft.yaml`, seeded from the reader notes: 44 frameworks with stages, 14 B2B, 2 B2C. The stage seeding is rough (pre-PMF became idea and pilot; post-PMF became nail-it, scale-it and milk-it), so Eric reviews every stage tag. The page shows both tags on each framework and can filter by them.

The panel changed seven tags:

| Framework | Was | Now | Why |
|---|---|---|---|
| `mochary-weekly-check-in` | nail-it and later | pilot and later | Two cofounders need a written weekly check-in. |
| `chj-operating-review` | nail-it and later | scale-it, milk-it | A full monthly review is too heavy before Scale it. |
| `performance-standards-by-level` | nail-it and later | scale-it, milk-it | Leadership levels matter once there are managers of managers. |
| `psiu-role-fit` | nail-it and later | any stage | The first key hire happens at Pilot. |
| `kernel-of-good-strategy` | nail-it and later | any stage | A company at Pilot needs a diagnosis too. |
| `origin-story-interview` | B2C | both | It feeds B2B positioning frameworks. |
| `smallest-viable-audience` | B2C | both | It works the same for a B2B niche. |

## Part 4: Removing `category`

One commit removes it everywhere, so no test fails partway:

- `frameworks/registry.yaml`, every entry
- `e2e/tests/test_registry_schemas.py:12`, which requires the field
- the 12 framework tests that check its value, such as `test_launch_bet.py:46`
- `skills/_shared/resolve-framework-source.md`, which requires it on local entries and fills it for unregistered folders
- `skills/use-framework/SKILL.md:19`
- `skills/add-framework/SKILL.md`, `anti-examples.md` and `report-template.md`
- `skills/_shared/contextual-recommendation.md`, the tie-breaker
- `scripts/generate-framework-registry.mjs`, which writes it into every draft entry
- `scripts/catalog-template.html`, whose filter pills and grouping switch to layer and area, read from `layers.yaml` by `scripts/generate-catalogs.py`
- `frameworks/README.md` tables and `e2e/tests/test_readme_freshness.py:81-112`, which switch to layers and areas
- `e2e/tests/test_resolve_framework_source.py` and `test_add_skills_checked.py`

## Part 5: `add-framework`

When a new framework is added to the plugin, `add-framework` asks for:

1. its area, or a reason to hold it
2. its seat, as it does today
3. for each document, which framework writes it or that it comes from outside
4. its stages and market, or neither

For a project-local framework it asks only the document question, since the playbook shows plugin frameworks only.

## Part 6: The playbook pages

`scripts/generate-playbook.py` builds `skills/playbook/pages/` from `layers.yaml` and the registry, the same way `scripts/generate-org-chart.py` builds the org chart. A new skill, `skills/playbook/SKILL.md`, opens `index.html`.

- **The map (`index.html`).** Three columns: I, We, It. Each area is a box with its note and its frameworks. Each framework shows its name and its `use_when` line. The area's start-here framework comes first and is marked "Start here." Jim Loehr's Energy area reads as one system. Stage and market show as small tags. A filter row at the top narrows by stage and by market. The stage filter comes first, since it is the one question a CEO can answer right away.
- **A framework page (`frameworks/<id>.html`).** Its name, advisor and purpose; the command that starts it; its stages and market; its documents in two groups, must have and helps to have, each naming the framework that writes it or "from outside"; and a small graph of everything upstream of it, solid arrows for must-haves and dashed for helps. Every box links to that framework's page. An It framework page ends with "Put the result into your Top Goal or your next check-in."
- **The pre-commit hook** rebuilds the pages when `layers.yaml`, the registry or the generator changes. A test checks the committed pages match a fresh build.

## Part 7: The link review page

Done 2026-11-03: Eric reviewed the links, the answers are applied in the registry, and the review files and generator were deleted.

Eric reviews the 226 drafted links on an editable page, not in YAML. (Eric, 2026-11-03.)

- **What it shows.** Each link is one sentence: "Sales Pitch Structure needs *positioning statement*, written by 5 Components of Positioning (must have)." Under it is the builder's reason, then Approve, Reject and a notes box.
- **Order.** Three groups: guess first, then likely, then sure. Inside a group, links sort by the framework that needs them. A count at the top shows how many are left in each group.
- **Fast path.** The sure group has one button that approves every link in it that Eric hasn't already touched.
- **Where answers go.** Each answer saves in the page's own shared database as soon as Eric clicks, so he can stop and come back. Nothing is written to the repo from the page.
- **After the review.** I read the answers back and make one follow-up commit. A rejected link with a note gets the `from` the note names. A rejected link with no note becomes `outside` and is listed in the report. Approved links keep their draft. The review file then drops the links Eric has answered.
- **How it is built.** `scripts/generate-link-review.py` turns `link-review.yaml` into the page's data. I publish the page at the end of the build, since a builder subagent can't publish. The page is a Claude artifact and lives outside the repo, so it doesn't ship with the plugin.

## Tests

- New: `e2e/tests/test_playbook.py` (map checks, start-here checks, document links, required loops, market tags against arrows, the build matches what is committed, the hook rebuilds). It uses a small fake registry with a branch, a helpful loop and a required loop.
- New: `e2e/tests/test_link_review.py` (every review entry matches a registry link, one way only; confidence is sure, likely or guess; `generate-link-review.py` orders guess, likely, sure).
- New: `e2e/tests/test_framework_tags.py` (stage and market values).
- Changed: `test_registry_schemas.py`, `test_framework_handoffs.py`, the five tests that read `follow_on_frameworks` (`test_four_question_threat_model.py`, `test_advisor_cleanup.py`, `test_phantom_b_llm_threats.py`, `test_why_my_page_doesnt_rank.py`, `test_getting_real_cut.py`), `test_readme_freshness.py`, `test_resolve_framework_source.py`, `test_add_skills_checked.py`, the 12 framework tests that check `category`, and `test_org_chart.py` if the hook test shares code.

## Where Eric reviews

- The areas and the stage and market tags: on this design page, before approval.
- The start-here picks: on this design page, before approval.
- The document links: on the link review page (Part 7), after the build, at his own pace. Corrections are one follow-up commit.
- `follow_on_frameworks` links that no document covers: listed in the build report for Eric to keep or drop.

## Left to the builder

- The graph layout on a framework page.
- The exact wording of `add-framework`'s new questions.
- Whether the catalog page and the playbook map share a template.
