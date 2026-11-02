# Org Chart Pages: Design

Date: 2026-11-02
Status: draft, waiting on Eric's review

## The answer

The plugin ships two org charts as linked HTML pages: a 100-person B2B software company and a 100-person B2C software company. A client's CEO runs `/aligned:org-chart`, the chart opens in their browser, and every seat links to its own page. A seat page tells the CEO how to do that job well before they can hire for it. It lists the jobs the seat does, the framework to run for each job, and the command that starts it. Before the charts are built, the advisor list is cleaned up: 13 advisors and 31 frameworks leave the plugin, and Wise Eric becomes Coach Eric.

## Why

Eric's clients are CEOs of lean companies. Most seats on a 100-person org chart are empty for them: they do the job themselves, or nobody does. The plugin holds expert advice for many of those seats, but a CEO has no way to see it seat by seat. The pages let a CEO get a head of sales', a head of product's, or a CFO's expertise years before they could hire one.

Building the first chart (https://claude.ai/artifact/Gy9Hz3geUxwRmzMWrkxJaL) showed that the plugin carries advisors that don't belong in a software company's toolkit. Some were added for a single client or prospect before project-local advisors existed. Those move to the repo of the client they were built for, or leave.

## Goals

1. A CEO opens the charts from inside Claude Code with one command.
2. One click from a chart opens any seat. One click from a seat returns to its chart. A switch moves between the B2B and B2C charts.
3. Each seat page is organized by the jobs the seat does. Each job names one framework, its advisor, and the exact command to start it.
4. Seats with no framework say "Nothing yet" and name what the plugin does not cover, so the CEO knows to get help elsewhere.
5. The pages stay true to the registries. Adding an advisor or framework to the plugin forces a decision about where it goes on the charts, and the pages rebuild on commit.
6. The plugin holds only advisors that fit a software company. Client-specific advisors live in that client's repo.

## Non-goals

- Marking which seats a CEO has already hired. Every CEO sees the same full chart. (Eric)
- Showing a client's own project-local advisors on the charts. That needs the pages built on the client's machine; it can be added later on top of the same data file.
- Hosting the pages on claude.ai or any website.
- Writing new frameworks for the empty seats.
- Deciding what happens to the advisors in the undecided group. They go to a holding list and Eric decides later.

## Anti-goals

- A client page that reads like Eric's backlog. The gap list and the undecided list go on an author page that never ships.
- Pages that go stale silently when an advisor is added or removed.
- Anything that needs the client to install Python, a YAML library, or anything else. The shipped pages are plain HTML files.

## Constraints

- Portability rule (`CLAUDE.md`): every shipped step must make sense for any user who installs the plugin. Author-only steps are gated on writing to the plugin itself.
- Everything in the repo ships. `marketplace.json` has `"source": "./"` and `plugin.json` has no file list. Only git-ignored paths stay home; `docs/plans/` is one.
- Six existing tests scan every `.md`, `.yaml`, `.html`, and `.json` file under `skills/` for retired advisor names, ignoring case, including "QA Engineer" and "SEO Expert" (for example `e2e/tests/test_michael_bolton_replaces_qa_engineer.py:42`). Seat names must avoid those words.
- The pages open from a local file (`file://`). Links between them are relative. No script loads from the network; Google Fonts load when online, with system font fallbacks.
- No design-principles file exists in this repo. The pages use the first artifact's tokens: a cool paper background, ink text, one blue accent, and green, amber, and red for coverage, each with a dark-theme value.
- Tests are pytest files in `e2e/tests/`, which already use PyYAML (`e2e/requirements.txt`).
- The pre-commit hook (`scripts/hooks/pre-commit`) bumps the plugin version when shipped folders are staged. Do not bump by hand.
- The repo has no CI. A test only catches stale pages when someone runs it.

## Approaches

1. **Pages built ahead of time and shipped in the plugin, plus a command that opens them. Picked by Eric.** A script turns the data file and both registries into the charts and seat pages, committed to the repo. A skill opens the chart. A test and the pre-commit hook keep the pages and the registries in step. Trade-off: a client's own advisors don't appear.
2. **Pages built on the client's machine when they run the command.** Shows their own advisors, but needs Python and PyYAML on every client machine, and their own advisors still sit on no seat. Rejected for now.
3. **Hosted pages on claude.ai.** Not in the repo, and each page has to be shared by hand. Dropped.

## Part 1: Clean up the advisor list

### Who leaves the plugin and where they go

| Advisor | Frameworks | Goes to | Why (Eric) |
|---|---|---|---|
| Joan Garry | Big BAT Board Assessment, Organizational Readiness | Deleted. Git history keeps her at `012f043`. | Built for one nonprofit prospect. |
| Jonathan Baker | Sellability Index | `~/Documents/nextstep/advisors/` and `frameworks/` | Belongs with the nextstep sale. |
| Robb Wolf | none | `~/Documents/aligned/advisors/` | Belongs with Vindara Health. Eric starts Vindara sessions from `~/Documents/aligned`. |
| Kate Bowler | Permission Blessing | `~/Documents/aligned/advisors/` and `frameworks/` | Same. |
| Danny Iny | Audience-First Business Model, Integrative Piloting Process, Leveraged Learning, Pilot Program Methodology | `~/software/planted/advisors/` and `frameworks/` | Belongs with Planted. |
| Elise Darma, Jasmine Star, Sue B. Zimmerman, Rachel Pedersen, Jenna Kutcher | 13 Instagram frameworks | Deleted. | Built for solo service businesses. |
| Arielle Nissenblatt, Jeremy Enns, Jay Clouse | 10 creator and podcast frameworks | Deleted. | Built for solo creators. |

Totals: 13 advisors and 31 frameworks leave. The plugin goes from 77 advisors and 147 frameworks to 64 and 116.

A move copies the advisor's prompt into the target repo's `advisors/prompts/`, appends their registry entry to the target's `advisors/registry.yaml`, and copies each framework folder plus its registry entry into the target's `frameworks/`, creating the registry files where they don't exist (the format in `skills/_shared/resolve-advisor-source.md` and `resolve-framework-source.md`). Then the plugin copies are deleted. `~/Documents/nextstep` is not a git repo, so that move has no history to roll back to.

### What else changes in the plugin

- Three registry entries point at leaving entries and get those pointers removed: `content-inc-model` (follow-on `creator-flywheel`, critic `jay-clouse`), `ten-steps-blueprint` (follow-on `leveraged-learning`, critic `danny-iny`), and `complex-contagion-rollout` (follow-on `organizational-readiness`).
- `advisors/README.md`, `frameworks/README.md`, and the root README counts.
- `e2e/trigger-map.yaml`, and the eval scenarios `e2e/scenarios/use-advisor/joan-garry-consult.yaml` and `jonathan-baker-consult.yaml`, which are deleted.
- `skills/use-advisor/SKILL.md`, which names some of the leaving advisors.
- `GONE_IDS` in `e2e/tests/test_readme_freshness.py` gains all 13 advisor ids and 31 framework ids.
- `docs/advisor-catalog.html` and `docs/framework-catalog.html` are rebuilt with `scripts/generate-catalogs.py`. They were already stale: Cole Nussbaumer Knaflic is missing.
- Every other reference found by `git grep` across shipped folders.

### Wise Eric becomes Coach Eric

- The id changes from `wise-eric` to `coach-eric`, matching the name the Conscious OS app already uses. The prompt file moves to `advisors/prompts/coach-eric.md`.
- The summary changes to a CEO coach, in the pattern of Matt Mochary's. First draft: "CEO coach who pairs conscious leadership with systems thinking; finds the root cause, then the next step." Eric approves the wording on review.
- Every one of the 13 tracked files that names Wise Eric is updated, including the `advisor:` field on his six frameworks and `frameworks/_outliers.json`.
- `GONE_IDS` gains `wise-eric`.

## Part 2: The org charts

### Files

| Path | What it is |
|---|---|
| `skills/org-chart/SKILL.md` | The `/aligned:org-chart` skill. Opens `{base-directory}/pages/index.html`. |
| `skills/org-chart/seats.yaml` | The data file. The only file a person edits. |
| `skills/org-chart/pages/index.html` | Generated. The B2B chart, with a switch to B2C. |
| `skills/org-chart/pages/b2c.html` | Generated. The B2C chart, with a switch to B2B. |
| `skills/org-chart/pages/seats/<seat-id>.html` | Generated. One page per seat. A seat on both charts has one page. |
| `skills/org-chart/pages/style.css` | Copied from the templates folder by the build. |
| `scripts/generate-org-chart.py` | The build script. `--check` exits non-zero when the committed pages differ from a fresh build. |
| `scripts/org-chart-templates/` | `chart.html`, `seat.html`, `coverage.html`, `style.css`. |
| `docs/plans/org-chart-coverage.html` | Generated, git-ignored, never ships. Eric's gap list and holding list. |
| `e2e/tests/test_org_chart.py` | The test file. |

The pages live inside the skill folder so the skill finds them from its own base directory, and so sessions that copy only `skills/` still have them.

### The data file

```yaml
departments:          # list order sets column order on the charts
  - id: sales
    name: Sales

seats:                # list order sets order within a column and the previous/next links
  - id: head-of-sales
    dept: sales
    name: Head of sales
    people:           # typical headcount at 100 people, per chart; a seat appears only on the charts it lists
      b2b: 1
    reports_to: ceo
    coverage: covered # covered | thin | none, set by hand, checked by the test
    does: Builds the sales team, picks the sales motion, and owns the number.
    jobs:
      - do: Pick your sales motion
        framework: 5-gtm-motions-digital-health
      - do: Find where revenue leaks between first touch and renewal
        framework: bowtie-funnel
        also: [teach-tailor-take-control]   # other frameworks for the same job, shown as "Other ways to do this"
    also_ask: []      # advisors with no framework on this seat, shown with /aligned:use-advisor
    missing: >-       # required when coverage is thin or none
      Forecasting, quotas, and sales comp plans.

  - id: board
    dept: lead
    name: Board and fundraising
    people: {b2b: 0, b2c: 0}   # 0 means not on the payroll
    dotted: true               # drawn with a dotted line to the CEO
    # ...

holding:              # entries kept off the charts for now, listed only on the author page
  advisors:
    - id: james-gurney
      why: undecided
  frameworks: []
```

A seat's advisors are the advisors of every framework on it plus `also_ask`. The build fails if `also_ask` repeats one of them.

### The seats

The B2B chart keeps the 35 seats from the first artifact, renamed where a name hits a retired-advisor pattern: "QA and test" becomes "Quality and testing", and "Content and SEO" becomes "Content and search". The social seat loses all its advisors in Part 1 and becomes "Social and community", coverage none.

The B2C chart shares the leadership, product, engineering, people, and finance seats, with different headcounts. It drops the B2B sales and customer success seats and adds:

| B2C seat | People | Starting advisors |
|---|---|---|
| Paid acquisition and app stores | 3 | Sean Ellis, Julian Shapiro, Oli Gardner, Joanna Wiebe, Shirin Oreizy |
| Lifecycle and retention | 2 | Robbie Kellman Baxter, Kristen Berman, Patrick Campbell, Sean Ellis |
| Community | 2 | Seth Godin, Damon Centola |
| Head of customer experience | 1 | Kristen Berman, Robbie Kellman Baxter |
| Support | 10 | none |
| Trust and safety | 3 | Kristen Berman, Adam Shostack |
| Partnerships | 1 | Chris Voss |

Each chart's headcounts add up to 100. The builder sets the exact split and Eric reviews it on the rendered pages.

### Where the people and personal advisors sit

- Diana Chapman: CEO (100% Responsibility, Above/Below the Line) and Head of people (Clearing Model).
- Jim Loehr and Matt Chapman: Head of people, with Energy Audit, Personal Credo, Stress-Recovery Oscillation, and Presence Check-In. (Eric)
- Coach Eric: CEO, with all six of his frameworks.
- The other personal frameworks go where a CEO or a head of people would use them, as the builder's call: Living Into Values and Vulnerability Check (Brené Brown), Quadrinity (Jim Dethmer), and Pain + Reflection (Ray Dalio) to Head of people. Regret Minimization (Jeff Bezos), Personal Resource Allocation (Clayton Christensen), and Tim Ferriss's three frameworks to CEO.
- Holding list: James Gurney (Stage the Picture). He plans illustrations. Eric decides later.
- The Architect and Boris Cherny: engineering seats. (Eric)
- Julie Yoo: Head of sales. (Eric)

### The chart page

- Title, one-sentence lede, and four tiles: advisors on this chart, frameworks on this chart, seats, and seats with nothing yet.
- A two-way switch, B2B and B2C, as two links.
- The chart: the board (dotted line) above the CEO, then one column per department, each seat a link to its page. Each seat shows its name, typical headcount, a coverage pill, and its job count.
- A legend for the three coverage levels, and one line saying the headcounts are a typical split for 100 people, rounded.

### A seat page

- A breadcrumb back to the chart it was opened from. A seat on both charts links back to both.
- The seat name, its department, typical headcount on each chart, and its coverage pill.
- What the seat does, in one sentence.
- **Jobs.** For each job: what the CEO needs to do, the framework, its advisor, one line from the framework's registry purpose, and `/aligned:use-framework <framework-id>` with a copy button. Frameworks in `also` sit under "Other ways to do this."
- **Ask an advisor.** Every advisor on the seat with their registry summary and `/aligned:use-advisor <advisor-id>`.
- **Not covered yet.** The `missing` text, for thin and empty seats. An empty seat shows only this block.
- Previous and next seat links, in chart order.

### The author page

`docs/plans/org-chart-coverage.html` holds the gap table for each chart (seats with nothing first, then thin seats by headcount) and the holding list. The build writes it every run. It is git-ignored, so it never ships.

### The skill

`/aligned:org-chart` resolves its base directory per `skills/_shared/resolve-skill-path.md`, then opens `pages/index.html` with `open` on macOS, `xdg-open` on Linux, or `cmd /c start "" <file>` on Windows. If the file is missing it says the plugin install looks incomplete. It builds nothing.

### Keeping the pages current

- **Pre-commit hook.** When a commit stages `advisors/registry.yaml`, `frameworks/registry.yaml`, `skills/org-chart/seats.yaml`, or anything in `scripts/org-chart-templates/`, the hook runs the build and stages the pages, the same way it already bumps the version. If Python or PyYAML is missing, it prints a warning and lets the commit through, as it does when node is missing.
- **Author step.** Inside the existing plugin-only steps (add-advisor Step 8, add-framework Step 7), with no new step numbers: add-framework asks which seat and job the new framework belongs to; add-advisor handles only `also_ask` or the holding list, and only when it built no framework. Then the step runs the build and `pytest e2e/tests/test_org_chart.py`. The step is skipped when `scripts/generate-org-chart.py` doesn't exist, so it never runs in a client's project.

## Tests

New file `e2e/tests/test_org_chart.py`:

1. Every framework in the plugin registry is on at least one seat (as a job or in `also`) or in the holding list, never both.
2. Every advisor in the plugin registry is placed: one of their frameworks is placed, they are in some seat's `also_ask`, or they are in the holding list.
3. Every id in `seats.yaml` exists in a registry, every `dept` and `reports_to` exists, and every seat lists at least one chart.
4. Coverage rules: `none` means no frameworks and `missing` is set; `thin` means `missing` is set; `covered` means at least two advisors and three frameworks.
5. `also_ask` never repeats an advisor the seat already gets through a framework.
6. Each chart's headcounts add up to 100.
7. `generate-org-chart.py --check` passes: a fresh build matches the committed pages, including `style.css`. The build writes no timestamps.
8. Every seat on a chart links to an existing seat page, every seat page links back to each chart it is on, and the two charts link to each other.
9. Every command on a seat page names a real framework or advisor id.
10. No file under `skills/org-chart/` matches any of the six retired-advisor patterns.
11. Error paths: the build exits non-zero and names the id when `seats.yaml` names an unknown id, when a registry entry is unplaced, and when `also_ask` repeats an advisor.

Updated tests:

- `e2e/tests/test_readme_freshness.py`: `GONE_IDS` gains the 13 leaving advisors, their 31 frameworks, and `wise-eric`. Its headline counts follow the registries.
- Any test that names a leaving advisor or `wise-eric` (`e2e/tests/test_brainstorming_files.py` names Wise Eric).
- `e2e/tests/test_add_skills_checked.py` keeps passing with no step renumbering.

## Decided

- Pages are built ahead of time and shipped. (Eric)
- The reader is the client's CEO, covering seats they haven't hired. (Eric)
- Every CEO sees the same chart. (Eric)
- There is a B2B chart and a B2C chart. (Eric)
- The advisor moves, deletions, and the Coach Eric rename in Part 1. (Eric)
- Robb Wolf and Kate Bowler go to `~/Documents/aligned`, where Eric starts Vindara sessions. (Eric)
- Seat pages are organized by jobs, each with one framework and its command. (proposed to Eric, not objected to)
- The gap list and holding list live on an author page that never ships. (builder check and architect review)

## Left to the builder

- The exact wording of each seat's jobs and the B2C headcount split. Eric reviews the rendered pages.
- Where the remaining personal frameworks sit, within the rule above.
- Page styling within the tokens above.
