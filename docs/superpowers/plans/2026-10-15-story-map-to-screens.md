# Story Map to Screens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the User Story Map framework into one session that goes Patton story map (one timeline, three tiers) → Ryan Singer breadboard of Slice 1 → Brad Frost's `breadboard-to-pages` → link back.

**Architecture:** The framework is prompt files plus one HTML template whose only per-map inputs are `:root` tokens and a `map-data` JSON block, rebuilt from a Markdown source. This plan changes the JSON shape and renderer, rebuilds the worked example, rewrites the prompt's phases, updates examples, advisor files, registry, and adds one eval scenario.

**Tech Stack:** Markdown prompts, a single static HTML template with inline vanilla JS (ES5 style, no libraries), pytest (`e2e/.venv/bin/python -m pytest`), Node for a render check, promptfoo-style YAML eval scenarios.

**Spec:** `docs/superpowers/specs/2026-10-15-story-map-to-screens-design.md` (read it before any task).

## Global Constraints

- Run tests with `/path/to/worktree/e2e/.venv/bin/python -m pytest e2e/tests/test_user_story_map_picture.py -q` (the venv lives in the main checkout at `/Users/ericpage/software/aligned_cc_skills/e2e/.venv`; use that interpreter with the worktree's test path).
- Never bump the version by hand. The pre-commit hook does it on commit.
- Do not edit anything under `frameworks/breadboard-to-pages/`.
- The template's per-map changes are only the `:root` tokens and the JSON inside `<script type="application/json" id="map-data">`. Everything else in the template is fixed layout.
- The Markdown map is the source; the HTML is a build output. The worked example's HTML must equal the template with only the JSON block changed.
- Quote Jeff Patton only from the Story Mapping Quick Reference, his articles, and lines he has said in his own voice. Verified 2005 line: "dividing the model into something that looks a bit like swim lanes".
- Quote Ryan Singer only with these verified *Shape Up* chapter 4 lines: "Places: These are things you can navigate to, like screens, dialogs, or menus that pop up." / "Affordances: These are things the user can act on, like buttons and fields." / "Connection lines: These show how the affordances take the user from place to place." Source: https://basecamp.com/shapeup/1.3-chapter-04. Do not use his archived Claude Code shaping skills as a source.
- Eric builds small apps alone. No step asks who else should hear the walk or tells the user to walk it with a team.
- Plugin portability: nothing depends on superpowers or the author's environment.
- Write prompt prose in the voice `frameworks/user-story-map/prompt.md` already uses: plain, short sentences, define each term the first time.
- Commit messages: plain `-m "..."`, no heredoc, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Shared names (every task uses these exactly)

JSON in `map-data`:

```json
{
  "title": "", "subtitle": "",
  "frame": { "user": "", "outcome": "", "problem": "", "why": "" },
  "roles": [ { "name": "", "about": "" } ],
  "slices": [ { "id": 1, "name": "", "outcome": "", "measure": "" } ],
  "activities": [
    { "name": "",
      "tasks": [
        { "text": "", "role": "", "slice": 1, "gap": false, "workaround": false, "note": "",
          "details": [ { "text": "", "kind": "detail", "slice": 1, "gap": false } ] } ] } ],
  "questions": [],
  "breadboard": [ { "place": "", "role": "", "affordances": [ { "text": "", "to": "", "card": "" } ] } ],
  "screens": ""
}
```

- `slice` is an integer slice id or `null` (Later). `detail.kind` is one of `detail`, `rule`, `alternative`, `exception`. `gap`, `workaround`, `note`, `details`, `to` are optional.
- An activity's roles are the distinct `role` values of its tasks, in task order.
- `screens` is a URL or relative path; empty until Phase 10.

Markdown source sections, in order: `# {title}`, subtitle line, `## Frame` (bullets **User:**, **Outcome:**, **Problem:**, **Why:**), `## Roles` (table Role | Who they are), `## Slices` (table Slice | Name | Outcome | Measure), `## Map` then one `### {Activity}` per activity with a table Card | Tier | Kind | Role | Slice | Gap | Note (Tier is `task` or `detail`; for a task Kind is `step` or `workaround`; for a detail Kind is `detail`, `rule`, `alternative`, or `exception`; detail rows follow their task; Slice is a number or `Later`; Gap is `yes` or empty), `## Open questions` (numbered), `## Slice 1 breadboard` then one `### {Place} ({Role})` per place with a table Affordance | Leads to | Card, and optionally `## Screens` with one line holding the link.

Prompt phase headings (exact):
`### PHASE 1: Frame It`, `### PHASE 2: Map the Big Picture`, `### PHASE 3: Tasks and Details`, `### PHASE 4: Walk the Map`, `### PHASE 5: Other Roles on the Same Timeline`, `### PHASE 6: Slice Releases`, `### PHASE 7: Write the Result`, `### PHASE 8: Breadboard Slice 1`, `### PHASE 9: Screens`, `### PHASE 10: Link Back`.

Template tab buttons: `data-tab="map"` (Map) and `data-tab="breadboard"` (Breadboard); a Screens link `<a id="screens-link">` shown only when `screens` is non-empty.

## Review Focus

1. A map drawn after Phase 2 has activities but no tasks. Every activity card must still draw, each over one empty column. (Test in Task 1.)
2. Before Phase 6 there are no slices. The map draws one uncut band labeled "Not sliced yet". (Test in Task 1.)
3. A map with a single role. Activity role chips still show; nothing breaks without a second role. (Test in Task 1.)
4. A breadboard affordance whose `to` names a place that isn't on the breadboard. (Test in Task 2, on the example.)
5. A detail placed in an earlier slice than its own task, which reads as "build the detail before the step." (Test in Task 2; rule stated in Task 3's Phase 6.)

---

### Task 1: Template renders the new map shape

**Files:**
- Modify: `frameworks/user-story-map/story-map-template.html`
- Modify: `frameworks/user-story-map/story-map-template.md`
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the JSON shape, Markdown shape, tab ids, and CSS class names below; a test helper `_render_counts(html: str, data: dict | None = None) -> dict` in the test file that runs the template script in Node against a DOM stub and returns `{"classes": {className: count}, "tabs_hidden": bool, "screens_hidden": bool}`, counting each space-separated class once per element. Task 2 uses it.

CSS class names the renderer must emit (tests count them): `activity`, `task`, `detail`, `gap`, `workaround`, `role-chip`, `role-card`, `slice-name`, `slice-outcome`, `slice-measure`, `place`, `affordance`, and `cut` on each band row that draws a slice line. Map table wrapped in a `div.scroll`.

Render rules:
- Columns are tasks, in order. An activity cell spans its task count (`colSpan`); an activity with no tasks spans one empty column.
- Bands: one per slice in order, then `Later` (only if something is in Later), or a single uncut `Not sliced yet` band when `slices` is empty. A task card sits in its own column, in the band of its slice. Details sit in their task's column in the band of their own slice, below the task when they share a band.
- Band label shows `slice-name`, `slice-outcome`, and `slice-measure` ("Measure: …") when present.
- Frame tiles: User, Outcome, Problem, Why (skip empty ones). Roles strip: one `role-card` per role with name and `about`.
- Activity card shows one `role-chip` per role. Task card shows its role in small text. Gap cards dashed border; workaround cards get their own mark using existing tokens; details are smaller and quieter than tasks.
- Columns about 150px; activity cards in the backbone row equal height (keep the existing `tr.backbone td { height: 1px }` / `height: 100%` approach).
- Tabs row hidden until `breadboard` has entries. Breadboard tab: one `place` per breadboard place (place name, role), one `affordance` per affordance showing text, "→ {to}" when present, and "card: {card}".
- `#screens-link` hidden unless `screens` is non-empty; when shown, `href` is `screens`, text "Screens".
- Script uses only: `document.createElement`, `createTextNode`, `getElementById`, `querySelectorAll`, `appendChild`, `textContent`, `className`, `hidden`, `setAttribute`, `getAttribute`, `addEventListener`, and plain property assignment (`colSpan`, `href`). The Node stub supports exactly these.
- Template sample JSON: two roles, one slice with a measure, two activities, three tasks (one gap, one workaround), one detail of kind `rule`, one breadboard place with two affordances, `screens` empty.

- [ ] **Step 1: Write the failing tests**

Remove the old classes `TestTemplate`, `TestMarkdownTemplate` and the test `test_template_renders_with_no_activities`; add:

```python
class TestTemplateShape:
    def test_json_has_the_new_fields(self):
        d = _template_data()
        assert set(d["frame"]) == {"user", "outcome", "problem", "why"}
        assert d["roles"] and "about" in d["roles"][0]
        assert "measure" in d["slices"][0]
        t = d["activities"][0]["tasks"][0]
        assert {"text", "role", "slice"} <= set(t)
        assert any(det["kind"] == "rule" for a in d["activities"] for t in a["tasks"] for det in t.get("details", []))
        assert d["breadboard"][0]["affordances"][0]["card"]
        assert d["screens"] == ""
        assert "lanes" not in d and "wireframes" not in d

    def test_tabs_are_map_and_breadboard(self):
        html = _read(TEMPLATE)
        assert 'data-tab="map"' in html and 'data-tab="breadboard"' in html
        assert 'data-tab="wireframes"' not in html
        assert 'id="screens-link"' in html

    def test_only_one_template(self):
        assert sorted(p.name for p in FRAMEWORK.glob("*.html")) == ["story-map-template.html"]

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_template_sample_renders(self):
        r = _render_counts(_read(TEMPLATE))
        c = r["classes"]
        assert c["activity"] == 2 and c["task"] == 3 and c["detail"] == 1
        assert c["gap"] >= 1 and c["workaround"] >= 1
        assert c["role-card"] == 2 and c["slice-measure"] == 1
        assert c["place"] == 1 and c["affordance"] == 2
        assert r["tabs_hidden"] is False and r["screens_hidden"] is True


class TestTemplateEdgeCases:
    pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

    def _base(self):
        return {"title": "T", "subtitle": "", "frame": {"user": "u", "outcome": "", "problem": "", "why": ""},
                "roles": [{"name": "Owner", "about": "Runs it"}], "slices": [], "questions": [],
                "breadboard": [], "screens": ""}

    def test_activities_without_tasks_still_draw(self):
        d = self._base() | {"activities": [{"name": "Do A", "tasks": []}, {"name": "Do B", "tasks": []}]}
        assert _render_counts(_read(TEMPLATE), d)["classes"]["activity"] == 2

    def test_no_slices_draws_one_uncut_band(self):
        d = self._base() | {"activities": [{"name": "Do A", "tasks": [{"text": "Step", "role": "Owner", "slice": None}]}]}
        r = _render_counts(_read(TEMPLATE), d)
        assert r["classes"].get("cut", 0) == 0 and r["classes"]["task"] == 1
        assert r["tabs_hidden"] is True

    def test_single_role_map_shows_role_chip(self):
        d = self._base() | {"slices": [{"id": 1, "name": "Slice 1", "outcome": "o", "measure": ""}],
                            "activities": [{"name": "Do A", "tasks": [{"text": "Step", "role": "Owner", "slice": 1}]}]}
        c = _render_counts(_read(TEMPLATE), d)["classes"]
        assert c["role-chip"] == 1 and c.get("slice-measure", 0) == 0

    def test_map_sits_in_a_scroll_container(self):
        assert re.search(r'class="scroll"|\'scroll\'', _read(TEMPLATE))


class TestMarkdownTemplate:
    def test_sections_in_order(self):
        md = _read(MD_TEMPLATE)
        heads = ["## Frame", "## Roles", "## Slices", "## Map", "## Open questions", "## Slice 1 breadboard"]
        positions = [md.index(h) for h in heads]
        assert positions == sorted(positions)
        assert "**Why:**" in md
        assert "| Card | Tier | Kind | Role | Slice | Gap | Note |" in md
        assert "| Affordance | Leads to | Card |" in md

    def test_comment_maps_markdown_to_json(self):
        md = _read(MD_TEMPLATE)
        for field in ('"why"', '"roles"', '"measure"', '"activities"', '"tasks"', '"details"',
                      '"workaround"', '"breadboard"', '"affordances"', '"screens"'):
            assert field in md, field
```

Implement `_render_counts` next to `_template_data`: extract `map-data` JSON (or use `data` when given), extract the inline `<script>` (not the JSON one), write a JS file with a stub `document` whose elements record `className` per `appendChild`, splitting on spaces, and whose `getElementById` returns persistent stub elements (`map-data` returns `{textContent: JSON}`); after running, print `{"classes":…, "tabs_hidden": byId.tabs.hidden, "screens_hidden": byId["screens-link"].hidden}`. Count a class whenever an element carrying it is appended anywhere. `cut` counts band rows with a slice line.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.../e2e/.venv/bin/python -m pytest e2e/tests/test_user_story_map_picture.py -q -k "Template"`
Expected: FAIL on missing fields, tabs, and classes. Note: `TestWorkedExample` will also fail after this task changes the template; that is fixed in Task 2. Mark the old `TestWorkedExample` class `@pytest.mark.skip(reason="rebuilt in Task 2")` in this task so the suite stays green.

- [ ] **Step 3: Rewrite the template's JSON sample, CSS, and script; rewrite `story-map-template.md`** to the shapes in "Shared names" and the render rules above. Keep the existing tokens, dark-mode blocks, header comment (updated for the new tabs), and legend (add task, detail, workaround).

- [ ] **Step 4: Run tests to verify they pass**

Run: `.../e2e/.venv/bin/python -m pytest e2e/tests/test_user_story_map_picture.py -q`
Expected: PASS except tests for prompt/examples/advisor that later tasks change (none should fail yet; if one does, it means this task broke it).

- [ ] **Step 5: Screenshot check.** Build a throwaway copy of the template, open it with headless Chrome (`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --hide-scrollbars --window-size=1500,1100 --screenshot=<scratch>/t1.png file://<copy>`), view it, and fix anything visibly broken (overlap, unequal activity heights, clipped text). One pass.

- [ ] **Step 6: Commit**

```bash
git add frameworks/user-story-map/story-map-template.html frameworks/user-story-map/story-map-template.md e2e/tests/test_user_story_map_picture.py
git commit -m "feat: story map template draws one timeline with tasks, details, slices with measures, and a breadboard tab"
```

---

### Task 2: Rebuild the worked team-course example

**Files:**
- Modify: `frameworks/user-story-map/example/team-course.md`
- Modify: `frameworks/user-story-map/example/team-course.html`
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: Task 1's JSON shape, Markdown shape, and `_render_counts`.
- Produces: the example files that Tasks 3 and 4 point to.

Content (from the current example and `examples.md`, reshaped):
- Frame adds **Why:** "Teams that finish a unit sign up for the next".
- Roles: Facilitator ("Runs one team through the course"), Member ("Does each week's lesson and joins the weekly session").
- One timeline, in story order: Get the team set up (F), Join the course (M), Prepare the week's lesson (F), Do the week's lesson (M), Check who's ready (F), Run the session (F and M: "Join from the calendar link" and "Take part in the live exercise" are Member tasks here), Follow up after (F), Practice during the week (M), Wrap up the unit (F).
- "Lesson visible to facilitator before members" becomes a `rule` detail under "Read the lesson".
- Slice 1 "Run a week", measure "Facilitators stop using the spreadsheet by week three". Slice 2 "Run a unit", outcome unchanged, measure "Facilitators talk with every member who fell behind before the next unit opens".
- "Wrap up the unit" gets a Slice 1 workaround task "Wrap up the unit by hand, as today" (Kind `workaround`); its other tasks stay in Slice 2. Open question 3 changes to point at that card.
- Gaps found on the walk stay marked: "Mark someone excused" (Later), "Join from the calendar link" (Slice 1).
- `## Slice 1 breadboard`: one place per Slice 1 screen the old wireframes had, as places with affordances, each affordance naming a Slice 1 task or detail as its card, `to` naming another place on the breadboard or empty. Workaround tasks get no affordance.
- Build the HTML by copying the template and replacing only the JSON. A parser like `/private/tmp/claude-501/-Users-ericpage-software-aligned-cc-skills/b0a8409c-b5ed-4f9b-9ce5-8ed758402b90/scratchpad/build_story_map.py` (old shape; adapt it in your own scratch space, don't commit it) keeps the Markdown and JSON in sync.

- [ ] **Step 1: Write the failing tests.** Replace the old `TestWorkedExample` with:

```python
class TestWorkedExample:
    def test_built_from_template(self):
        assert MAP_DATA.sub(r"\1\3", _read(EXAMPLE_HTML)) == MAP_DATA.sub(r"\1\3", _read(TEMPLATE))

    def test_one_timeline_two_roles(self):
        d = _example_data()
        assert "lanes" not in d
        assert [r["name"] for r in d["roles"]] == ["Facilitator", "Member"]
        roles = {t["role"] for a in d["activities"] for t in a["tasks"]}
        assert roles == {"Facilitator", "Member"}
        run = next(a for a in d["activities"] if a["name"] == "Run the session")
        assert {t["role"] for t in run["tasks"]} == {"Facilitator", "Member"}

    def test_slice_one_reaches_every_activity(self):
        for a in _example_data()["activities"]:
            assert any(t.get("slice") == 1 for t in a["tasks"]), a["name"]

    def test_wrap_up_uses_a_workaround(self):
        wrap = next(a for a in _example_data()["activities"] if a["name"] == "Wrap up the unit")
        assert any(t.get("workaround") and t.get("slice") == 1 for t in wrap["tasks"])

    def test_every_slice_has_a_measure_and_why_is_set(self):
        d = _example_data()
        assert all(s["measure"] for s in d["slices"])
        assert d["frame"]["why"] == "Teams that finish a unit sign up for the next"

    def test_rule_hangs_under_read_the_lesson(self):
        tasks = {t["text"]: t for a in _example_data()["activities"] for t in a["tasks"]}
        assert any(x["kind"] == "rule" for x in tasks["Read the lesson"]["details"])

    def test_no_detail_in_an_earlier_slice_than_its_task(self):
        order = lambda s: 10**6 if s is None else s
        for a in _example_data()["activities"]:
            for t in a["tasks"]:
                for x in t.get("details", []):
                    assert order(x.get("slice")) >= order(t.get("slice")), x["text"]

    def test_every_slice_one_task_has_an_affordance(self):
        d = _example_data()
        cards = {aff["card"] for p in d["breadboard"] for aff in p["affordances"]}
        for a in d["activities"]:
            for t in a["tasks"]:
                if t.get("slice") == 1 and not t.get("workaround"):
                    assert t["text"] in cards, t["text"]

    def test_every_affordance_names_a_slice_one_card_and_a_real_place(self):
        d = _example_data()
        s1 = {t["text"] for a in d["activities"] for t in a["tasks"] if t.get("slice") == 1 and not t.get("workaround")}
        s1 |= {x["text"] for a in d["activities"] for t in a["tasks"] for x in t.get("details", []) if x.get("slice") == 1}
        s1 |= {a["name"] for a in d["activities"]}
        places = {p["place"] for p in d["breadboard"]}
        for p in d["breadboard"]:
            for aff in p["affordances"]:
                assert aff["card"] in s1, aff
                assert aff.get("to", "") in places | {""}, aff

    def test_markdown_holds_every_json_string(self):
        md, d = _read(EXAMPLE_MD), _example_data()
        strings = [d["title"], *[v for v in d["frame"].values() if v], *d["questions"]]
        strings += [r["name"] for r in d["roles"]] + [r["about"] for r in d["roles"]]
        strings += [s[k] for s in d["slices"] for k in ("name", "outcome", "measure")]
        for a in d["activities"]:
            strings.append(a["name"])
            for t in a["tasks"]:
                strings.append(t["text"])
                strings += [x["text"] for x in t.get("details", [])]
        for p in d["breadboard"]:
            strings.append(p["place"])
            for aff in p["affordances"]:
                strings += [aff["text"], aff["card"]] + ([aff["to"]] if aff.get("to") else [])
        assert [s for s in strings if s not in md] == []

    def test_examples_md_points_to_the_finished_page(self):
        assert "example/team-course.html" in _read(EXAMPLES)

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_example_renders(self):
        d = _example_data()
        r = _render_counts(_read(EXAMPLE_HTML))
        assert r["classes"]["activity"] == 9
        assert r["classes"]["task"] == sum(len(a["tasks"]) for a in d["activities"])
        assert r["classes"]["place"] == len(d["breadboard"])
        assert r["tabs_hidden"] is False and r["screens_hidden"] is True
```

- [ ] **Step 2: Run to verify they fail.** `... -k WorkedExample` → FAIL (old example shape).
- [ ] **Step 3: Rewrite `team-course.md` and rebuild `team-course.html`** per the content list.
- [ ] **Step 4: Run the whole story map test file.** Expected: PASS.
- [ ] **Step 5: Screenshot check** of `team-course.html` with headless Chrome as in Task 1; fix anything visibly broken in the Markdown (not the template) or report a template defect.
- [ ] **Step 6: Commit** `git add frameworks/user-story-map/example e2e/tests/test_user_story_map_picture.py` with message "feat: team-course example on one timeline with a Slice 1 breadboard".

---

### Task 3: Rewrite the framework prompt

**Files:**
- Modify: `frameworks/user-story-map/prompt.md`
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: Task 1's names (JSON fields, Markdown sections, tabs), Task 2's example path `example/team-course.md` / `.html`.
- Produces: the phase headings listed in "Shared names", which Tasks 4 and 6 reference.

What each part must say (write the prose; keep everything else in the current prompt that this list doesn't change, including "The map on screen" picture rules and the design-principles lookup):
- Line 1 purpose: building a shared map on one timeline, walking it, slicing by outcome, breadboarding Slice 1 with Ryan Singer, and handing it to Brad Frost for screens, in one session.
- Practice intro: names the three advisors and which phases each runs.
- **Terms:** add **Task** (a step the user takes under an activity; the top row of tasks in Slice 1 is the walking skeleton) and **Detail** (sub-tasks, alternatives, exceptions, rules, hanging under a task); **Workaround card**; Phase 8 terms Place, Affordance, Connection with the three verified Singer quotes.
- **Other roles** paragraph replaced: the Quick Reference places other users along the backbone where they enter; Patton's 2005 article draws vertical lines at role changes, "dividing the model into something that looks a bit like swim lanes"; so this framework keeps every role on one timeline and tags each task with its role. Remove "That follows the swim lanes Patton described at role changes in 2005" and "its own lane".
- Setup step 2 points to `story-map-template.md`; step 3 to `example/team-course.md` and `.html`; tabs are Map and Breadboard.
- Phase 1 asks for **Why** (what the business gets) and a chooser if one exists; lock includes Why.
- Phase 3 = Tasks and Details: tasks left to right under each activity; details under each task ranked by necessity; rules go here as details.
- Phase 4: no "who else should hear this walk" and no suggestion to bring in other people.
- Phase 5: other roles join the same timeline; tasks carry their role; when two roles act at the same point, their tasks share the activity.
- Phase 6: slices with name, outcome, measure; Slice 1 runs start to finish; an activity may be empty above the Slice 1 line only when a workaround card in Slice 1 says how the user gets by today; a detail is never in an earlier slice than its task.
- Phase 7: write the result; then Patton hands off in one line: Ryan Singer takes it from here to wire up Slice 1.
- Phase 8 (`### PHASE 8: Breadboard Slice 1`): read `advisors/prompts/ryan-singer.md` for voice; speak as Singer; breadboard Slice 1 as places, affordances, connections, words only, no visual design; every Slice 1 task that isn't a workaround has at least one affordance; every affordance names the card it serves; an affordance with no card is a gap (add the card or drop the affordance); write it to the Markdown under `## Slice 1 breadboard`; draw the Breadboard tab; walk the breadboard against the map; WAIT; Lock.
- Phase 9 (`### PHASE 9: Screens`): check for `design-principles.md` with the same lookup as setup; if none, run `/aligned:create-design-principles` in the same conversation first; then Singer hands off in one line to Brad Frost and invoke `/aligned:use-framework breadboard-to-pages` in the same conversation; that framework runs its own phases and WAIT points; it reads the breadboard from the story map Markdown.
- Phase 10 (`### PHASE 10: Link Back`): after `breadboard-to-pages` returns, write the screens page link into `## Screens` and `screens` (the artifact URL if the screens page was published as one, else the relative path to `{slug}-screens.html`), rebuild and republish the map, give both links. No WAIT.
- Closing line: no team walk; points to Steve Krug for usability.
- Key Rules updated to match: one timeline, three tiers, workaround rule, Phase 8 Singer, Phase 9 Frost same conversation, Phase 10 link. Remove every mention of wireframes.

- [ ] **Step 1: Write the failing tests.** Replace `TestPhaseEight`, `TestPictureStartsAtPhaseOne`'s setup test if it conflicts, and add:

```python
class TestPromptPhases:
    def test_phase_headings(self):
        p = _read(PROMPT)
        for h in ("### PHASE 1: Frame It", "### PHASE 3: Tasks and Details", "### PHASE 5: Other Roles on the Same Timeline",
                  "### PHASE 8: Breadboard Slice 1", "### PHASE 9: Screens", "### PHASE 10: Link Back"):
            assert re.search("^" + re.escape(h) + "$", p, flags=re.MULTILINE), h

    def test_citation_fixed(self):
        p = _read(PROMPT)
        assert "That follows the swim lanes Patton described" not in p
        assert "looks a bit like swim lanes" in p and "one timeline" in p

    def test_no_wireframes_and_no_team_walk(self):
        p = _read(PROMPT).lower()
        assert "wirefram" not in p
        assert "who else should hear" not in p and "people who'll build it" not in p

    def test_phase_one_asks_why(self):
        assert "**Why" in _phase(_read(PROMPT), 1)

    def test_phase_six_workaround_rule(self):
        ph = _phase(_read(PROMPT), 6)
        assert "workaround" in ph.lower() and "measure" in ph.lower()

    def test_phase_eight_is_singer_breadboard(self):
        ph = _phase(_read(PROMPT), 8)
        for s in ("Ryan Singer", "Shape Up", "ryan-singer.md", "## Slice 1 breadboard",
                  "These are things you can navigate to, like screens, dialogs, or menus that pop up.",
                  "These are things the user can act on, like buttons and fields.",
                  "These show how the affordances take the user from place to place."):
            assert s in ph, s
        assert "card" in ph and "workaround" in ph.lower()
        assert "**WAIT for the user to respond.**" in ph

    def test_phase_nine_hands_to_frost_same_conversation(self):
        ph = _phase(_read(PROMPT), 9)
        for s in ("Brad Frost", "/aligned:use-framework breadboard-to-pages", "same conversation",
                  "/aligned:create-design-principles", "design-principles.md"):
            assert s in ph, s

    def test_phase_ten_links_back(self):
        ph = _phase(_read(PROMPT), 10)
        assert "screens" in ph and "republish" in ph.lower()
        assert "**WAIT" not in ph

    def test_key_rules_name_all_three_advisors(self):
        rules = _read(PROMPT).split("## Key Rules")[1]
        for s in ("one timeline", "Ryan Singer", "Brad Frost", "workaround"):
            assert s in rules, s

    def test_setup_points_to_templates_and_example(self):
        section = _read(PROMPT).split("### The map on screen")[1].split("### PHASE 1")[0]
        for s in ("story-map-template.md", "story-map-template.html", "example/team-course", "Breadboard tab"):
            assert s in section, s
```

Keep `TestPictureCannotBeTurnedOff`, `TestDesignPrinciplesLookup`, and `test_phase_one_draws_after_the_frame_locks`. Delete `test_prompt_points_to_markdown_template_and_example` (superseded).

- [ ] **Step 2: Run to verify they fail.** `... -k "PromptPhases"` → FAIL.
- [ ] **Step 3: Rewrite `prompt.md`** per the list above.
- [ ] **Step 4: Run the whole story map test file.** Expected: PASS except `TestAdvisor` and example/anti-example tests that Tasks 4–5 change; mark none skipped. If an examples.md test now fails because examples still say "wireframe," leave it for Task 4 and note it in your report.
- [ ] **Step 5: Commit** `git add frameworks/user-story-map/prompt.md e2e/tests/test_user_story_map_picture.py`, message "feat: story map prompt runs Patton, then Singer's breadboard, then Brad Frost's screens in one session".

---

### Task 4: Examples and anti-examples

**Files:**
- Modify: `frameworks/user-story-map/examples.md`
- Modify: `frameworks/user-story-map/anti-examples.md`
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: Task 3 phase headings and rules; Task 2 example content (same cards, same breadboard).
- Produces: nothing new.

Content:
- `examples.md` phases follow the new prompt: Phase 3 shows tasks and details (the Phase 3 table becomes activities → tasks → details); Phase 5 shows the member joining the same timeline; Phase 6 adds the "Wrap up the unit by hand, as today" workaround and the new Slice 2 measure; Phase 7 ends with Patton's one-line hand-off to Ryan Singer; `## PHASE 8: Breadboard Slice 1` golden path in Singer's voice, using two or three places from the example's breadboard, plus one struggle where the user adds an affordance with no card; `## PHASE 9: Screens` shows the design-principles check and the hand-off to Brad Frost; `## PHASE 10: Link Back` shows both links. Remove the old wireframe Phase 8. "The finished page" section stays and still names `example/team-course.html`.
- `anti-examples.md`: update #4 so the Right side sends screens to Phase 8–9 (breadboard, then Brad Frost) instead of wireframes; add `## 8. Stacked role lanes` (Wrong: a lane per role with its own backbone; Right: one timeline, tasks tagged by role, citing the Quick Reference); add `## 9. A breadboard affordance with no card` (Wrong: Singer adds "Export to CSV" with no card; Right: add the card to the map first or drop it). Keep #7 as is.

- [ ] **Step 1: Write the failing tests.** Replace `test_examples_have_a_phase_eight_golden_path` with:

```python
class TestExamples:
    def test_new_phases_have_golden_paths(self):
        ex = _read(EXAMPLES)
        for h in ("## PHASE 8: Breadboard Slice 1", "## PHASE 9: Screens", "## PHASE 10: Link Back"):
            assert h in ex, h
        p8 = ex.split("## PHASE 8: Breadboard Slice 1")[1].split("## PHASE 9")[0]
        assert "### Golden path" in p8 and "Ryan Singer" in p8 and "Who's ready for Thursday" in p8
        p9 = ex.split("## PHASE 9: Screens")[1].split("## PHASE 10")[0]
        assert "Brad Frost" in p9 and "breadboard-to-pages" in p9

    def test_examples_drop_wireframes_and_team_walks(self):
        ex = _read(EXAMPLES).lower()
        assert "wirefram" not in ex and "who else should hear" not in ex

    def test_phase_six_has_the_workaround(self):
        p6 = _read(EXAMPLES).split("## PHASE 6")[1].split("## PHASE 7")[0]
        assert "Wrap up the unit by hand, as today" in p6


class TestAntiExamples:
    def _block(self, title_pattern):
        anti = _read(ANTI)
        m = re.search(r"^## \d+\. " + title_pattern + r".*$", anti, flags=re.IGNORECASE | re.MULTILINE)
        assert m, title_pattern
        return anti[m.end():].split("\n## ")[0]

    def test_stacked_lanes(self):
        b = self._block("Stacked role lanes")
        assert "**Wrong:**" in b and "one timeline" in b.split("**Right:**")[1]

    def test_affordance_with_no_card(self):
        b = self._block("A breadboard affordance with no card")
        assert "**Wrong:**" in b and "card" in b.split("**Right:**")[1]
```

Keep `TestAntiExample.test_map_as_text_before_screens_anti_example`.

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Rewrite `examples.md` and update `anti-examples.md`.**
- [ ] **Step 4: Run the whole story map test file.** Expected: PASS except `TestAdvisor` (Task 5).
- [ ] **Step 5: Commit** both files and the test file, message "feat: story map examples walk the breadboard and the hand-off to Brad Frost".

---

### Task 5: Advisor files, registry, and README

**Files:**
- Modify: `advisors/prompts/jeff-patton.md` (lines 53–54 rules, line 78 Core Frameworks entry)
- Modify: `advisors/prompts/ryan-singer.md` (line 81 and Core Frameworks list)
- Modify: `frameworks/registry.yaml` (`user-story-map` entry, around line 2379)
- Modify: `frameworks/README.md` (line 168 row)
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: Task 3 phase names.
- Produces: nothing new.

Content:
- `jeff-patton.md`: line 54 becomes: once Slice 1 is agreed, Ryan Singer breadboards it and Brad Frost turns it into screens, in the same session; Patton doesn't draw screens himself. Line 78: the framework draws the map on one timeline with tasks and details, slices with measures, then Phase 8 Singer's breadboard, Phase 9 Brad Frost's Breadboard to Pages, Phase 10 the link back. Remove "second tab" and "one wireframe per Slice 1 activity".
- `ryan-singer.md`: remove "breadboarding" from the "not yet as guided frameworks" list; add a line that breadboarding runs as Phase 8 of `user-story-map`, after Jeff Patton's slices, and hands to Brad Frost.
- `frameworks/registry.yaml` `user-story-map`: purpose "building a shared, visual map of what a user does start to finish on one timeline, walking it aloud to find the holes, slicing it into releases by outcome, then breadboarding Slice 1 with Ryan Singer and handing it to Brad Frost for screens, in one session"; `use_when` ends "...or someone needs a story map built and agreed before any screens". Mirror the new `use_when` in `frameworks/README.md` line 168.

- [ ] **Step 1: Write the failing tests.** Replace `TestAdvisor` with:

```python
class TestAdvisorsAndRegistry:
    def test_patton_core_names_breadboard_and_frost(self):
        core = _read(ADVISOR).split("## Core Frameworks")[1].split("\n## ")[0]
        assert "breadboard" in core.lower() and "Brad Frost" in core and "Slice 1" in core
        assert "second tab" not in core and "wirefram" not in core.lower()

    def test_patton_rule_hands_off_after_slice_one(self):
        a = _read(ADVISOR)
        assert "Sketch one screen per Slice 1 activity" not in a
        assert "Ryan Singer breadboards" in a

    def test_singer_runs_phase_eight(self):
        s = _read(REPO_ROOT / "advisors" / "prompts" / "ryan-singer.md")
        assert "user-story-map" in s
        line = next(l for l in s.splitlines() if "not yet as guided frameworks" in l)
        assert "breadboarding" not in line

    def test_registry_entry(self):
        import yaml
        reg = yaml.safe_load(_read(REPO_ROOT / "frameworks" / "registry.yaml"))
        e = next(f for f in reg["frameworks"] if f["id"] == "user-story-map")
        assert "Ryan Singer" in e["purpose"] and "Brad Frost" in e["purpose"]
        assert "wirefram" not in (e["purpose"] + e["use_when"]).lower()
        assert e["use_when"] in _read(REPO_ROOT / "frameworks" / "README.md")
```

- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Edit the four files.**
- [ ] **Step 4: Run the full suite** `.../e2e/.venv/bin/python -m pytest e2e/tests -q`. Expected: all pass.
- [ ] **Step 5: Commit** the four files and the test file, message "feat: Patton, Singer, and the registry describe the story map's breadboard and hand-off".

---

### Task 6: Eval scenario for Phases 8–10

**Files:**
- Create: `e2e/scenarios/use-framework/user-story-map-handoff.yaml`
- Modify: `e2e/trigger-map.yaml` (the `user-story-map` paths entry near line 386)
- Test: `e2e/tests/test_user_story_map_picture.py`

**Interfaces:**
- Consumes: Task 3 phase names; follows the format of `e2e/scenarios/use-framework/user-story-map-picture.yaml` (providers, `defaultTest` with `llm-rubric` asserts and weights, `system_context: file://../../../frameworks/user-story-map/prompt.md`, the "Test harness note" paragraph).
- Produces: scenario path `scenarios/use-framework/user-story-map-handoff.yaml`.

Two tests in the scenario:
1. "map agreed, go to the breadboard": the task prompt gives the locked team-course map (frame, timeline activities with Slice 1 tasks including the workaround, slices) and says "The map's agreed. Keep going." Rubrics: HAND-OFF (Patton hands off in one line and the reply continues in Ryan Singer's voice), BREADBOARD (places, affordances, and where each leads, in words; every non-workaround Slice 1 task has an affordance; every affordance names its card; no workaround affordance; no visual design or screen sketch), DISCIPLINE (stops and waits after the breadboard; does not start Phase 9 or draw screens).
2. "breadboard agreed, no design principles": the prompt says the breadboard is locked and the project has no `design-principles.md`. Rubrics: DESIGN PRINCIPLES FIRST (runs or starts `/aligned:create-design-principles` in this conversation before screens, without telling the user to open another session), FROST HAND-OFF (names Brad Frost and `breadboard-to-pages` as next, in the same conversation).

- [ ] **Step 1: Write the failing test**

```python
HANDOFF_SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "user-story-map-handoff.yaml"

class TestHandoffEval:
    def test_scenario_exists_with_two_tests_and_is_triggered(self):
        import yaml
        sc = yaml.safe_load(_read(HANDOFF_SCENARIO))
        assert len(sc["tests"]) == 2
        assert sc["tests"][0]["vars"]["system_context"].endswith("frameworks/user-story-map/prompt.md")
        assert "scenarios/use-framework/user-story-map-handoff.yaml" in _read(TRIGGER_MAP)
```

- [ ] **Step 2: Run to verify it fails.**
- [ ] **Step 3: Write the scenario and the trigger-map line.**
- [ ] **Step 4: Run the full suite** (includes `test_eval_scenario_config.py` and `test_trigger_map_paths.py`). Expected: all pass.
- [ ] **Step 5: Commit** both files and the test file, message "test: eval for the story map's breadboard and Brad Frost hand-off".

---

### Task 7 (controller): Evals

Not a subagent task. After the final branch review:
- Estimate the run's cost from recorded token use in `e2e/output/runs/` for `user-story-map`, `user-story-map-picture`, and `jeff-patton-consult`, plus the new scenario at the same per-call size; tell Eric the number.
- Run only those four scenarios with `e2e/run_evals.py` through the Claude Code login.
- Report each score; any FAIL goes back to the task that owns the prompt text.
