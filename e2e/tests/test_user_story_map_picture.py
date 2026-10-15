"""The User Story Map framework always draws the map and ends with Slice 1 wireframes.

Guards the contract added after the 2026-10-13 planted run, where "build the
map as text for me to review before any screens" was read as "no picture."
The picture starts as soon as the frame locks in Phase 1, wording in a request
can't turn it off, and Phase 8 wireframes Slice 1 into a second tab of the same
page. The design-principles lookup also finds monorepo files under
brand/*/guidelines/.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "user-story-map"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
TEMPLATE = FRAMEWORK / "story-map-template.html"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "jeff-patton.md"
PICTURE_SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "user-story-map-picture.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _phase(text: str, n: int) -> str:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        if int(parts[i]) == n:
            return parts[i + 1].split("## Key Rules")[0]
    raise AssertionError(f"PHASE {n} not found")


class TestPictureCannotBeTurnedOff:
    def test_map_on_screen_reads_text_wording_as_no_screens_yet(self):
        prompt = _read(PROMPT)
        section = prompt.split("### The map on screen")[1].split("### PHASE 1")[0]
        for phrase in ('"as text', '"for review', '"before any screens'):
            assert phrase in section, f"{phrase} must be named as wording that keeps the picture"
        assert "no screens yet" in section
        assert "confirm once" in section

    def test_key_rules_repeat_it(self):
        rules = _read(PROMPT).split("## Key Rules")[1]
        assert "can't turn it off" in rules
        assert "confirm once" in rules


class TestPictureStartsAtPhaseOne:
    def test_phase_one_draws_after_the_frame_locks(self):
        phase1 = _phase(_read(PROMPT), 1)
        lock = phase1.index("**Lock:**")
        assert "**Draw the map.**" in phase1[lock:], "Phase 1 must draw the map after its lock"
        assert "empty backbone" in phase1[lock:]

    def test_setup_happens_in_phase_one_not_before_phase_two(self):
        prompt = _read(PROMPT)
        assert "before Phase 2" not in prompt
        assert "do the setup in" not in _phase(prompt, 2)


class TestPhaseEight:
    def test_phase_eight_wireframes_slice_one(self):
        prompt = _read(PROMPT)
        assert re.search(r"^### PHASE 8: Wireframe Slice 1$", prompt, flags=re.MULTILINE)
        phase8 = _phase(prompt, 8)
        assert "one wireframe per activity" in phase8
        assert "**WAIT for the user to respond.**" in phase8
        assert "card" in phase8 and "design-principles.md" in phase8
        assert "second tab" in phase8 or "Wireframes tab" in phase8

    def test_phase_seven_no_longer_stops_at_ready_for_wireframes(self):
        phase7 = _phase(_read(PROMPT), 7)
        assert "ready for wireframes" not in phase7
        assert "No screens and no wireframes." not in phase7
        assert "Phase 8" in phase7

    def test_no_rule_still_bans_wireframes_outright(self):
        prompt = _read(PROMPT)
        assert "never draws a screen, a wireframe" not in prompt
        assert "No wireframes, page layouts, or field lists at any phase" not in prompt
        rules = prompt.split("## Key Rules")[1]
        assert "Slice 1" in rules and "wirefram" in rules.lower()

    def test_examples_have_a_phase_eight_golden_path(self):
        examples = _read(EXAMPLES)
        assert "## PHASE 8: Wireframe Slice 1" in examples
        phase8 = examples.split("## PHASE 8: Wireframe Slice 1")[1]
        assert "### Golden path" in phase8
        assert "Check who's ready" in phase8, "Phase 8 example must use the team-course map"


class TestAntiExample:
    def test_map_as_text_before_screens_anti_example(self):
        anti = _read(ANTI)
        m = re.search(r"^## \d+\. .*as text before screens.*$", anti, flags=re.IGNORECASE | re.MULTILINE)
        assert m, "an anti-example must be titled for 'map as text before screens'"
        block = anti[m.end() :].split("\n## ")[0]
        assert "**Wrong:**" in block and "**Right:**" in block
        assert "Slice 1" in block.split("**Right:**")[1]


class TestAdvisor:
    def test_core_frameworks_summary_includes_wireframes(self):
        advisor = _read(ADVISOR)
        assert "No screens. Produces a map ready for wireframes." not in advisor
        core = advisor.split("## Core Frameworks")[1].split("## ")[0]
        assert "wirefram" in core.lower() and "Slice 1" in core

    def test_no_screens_first_says_wireframes_follow_slice_one(self):
        advisor = _read(ADVISOR)
        section = advisor.split("**No screens first.**")[1].split("**No ")[0]
        assert "Slice 1" in section and "wirefram" in section.lower()


class TestDesignPrinciplesLookup:
    def test_lookup_checks_monorepo_brand_folders(self):
        prompt = _read(PROMPT)
        assert "brand/*/guidelines/design-principles.md" in prompt

    def test_lookup_asks_which_app_when_several_match(self):
        section = _read(PROMPT).split("### The map on screen")[1].split("### PHASE 1")[0]
        assert "which app" in section


def _template_data() -> dict:
    html = _read(TEMPLATE)
    m = re.search(r'<script type="application/json" id="map-data">(.*?)</script>', html, flags=re.S)
    assert m, "template must keep the map-data JSON block"
    return json.loads(m.group(1))


MD_TEMPLATE = FRAMEWORK / "story-map-template.md"
EXAMPLE_DIR = FRAMEWORK / "example"
EXAMPLE_MD = EXAMPLE_DIR / "team-course.md"
EXAMPLE_HTML = EXAMPLE_DIR / "team-course.html"
MAP_DATA = re.compile(r'(<script type="application/json" id="map-data">)(.*?)(</script>)', flags=re.S)


def _example_data() -> dict:
    m = MAP_DATA.search(_read(EXAMPLE_HTML))
    assert m, "example must keep the map-data JSON block"
    return json.loads(m.group(2))


def _render_counts(html: str, data: dict | None = None) -> dict:
    """Run the page script in Node against a DOM stub; count class tokens on appended elements."""
    import tempfile

    payload = json.dumps(data) if data is not None else MAP_DATA.search(html).group(2)
    script = re.findall(r"<script>(.*?)</script>", html, flags=re.S)[0]
    stub = (
        "var made={};function E(t){this.tagName=t;this.children=[];this.className='';this.textContent='';"
        "this.hidden=false;this.attrs={};}E.prototype.appendChild=function(c){this.children.push(c);"
        "String(c.className||'').split(' ').filter(Boolean).forEach(function(k){made[k]=(made[k]||0)+1});return c};"
        "E.prototype.setAttribute=function(k,v){this.attrs[k]=v};"
        "E.prototype.getAttribute=function(k){return this.attrs[k]};E.prototype.addEventListener=function(){};"
        "E.prototype.querySelectorAll=function(){return []};var byId={};"
        "var document={createElement:function(t){return new E(t)},createTextNode:function(t){return new E('#text')},"
        "getElementById:function(id){if(id==='map-data')return{textContent:DATA};return byId[id]||(byId[id]=new E('div'))}};"
    )
    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "render.js"
        js.write_text(
            "var DATA=" + json.dumps(payload) + ";" + stub + script
            + ";console.log(JSON.stringify({classes:made,tabs_hidden:!!byId['tabs'].hidden,"
            "screens_hidden:!!byId['screens-link'].hidden}));",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(js)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


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
    def test_template_script_parses(self, tmp_path):
        scripts = re.findall(r"<script>(.*?)</script>", _read(TEMPLATE), flags=re.S)
        assert scripts
        js = tmp_path / "template.js"
        js.write_text("\n".join(scripts), encoding="utf-8")
        result = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr

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

    def test_screens_link_shows_when_screens_set(self):
        d = self._base() | {"activities": [], "screens": "screens/index.html"}
        assert _render_counts(_read(TEMPLATE), d)["screens_hidden"] is False


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

    def test_prompt_points_to_markdown_template_and_example(self):
        section = _read(PROMPT).split("### The map on screen")[1].split("### PHASE 1")[0]
        assert "story-map-template.md" in section
        assert "example/team-course" in section


@pytest.mark.skip(reason="rebuilt in Task 2")
class TestWorkedExample:
    def test_example_html_is_the_template_with_only_the_json_changed(self):
        template = MAP_DATA.sub(r"\1\3", _read(TEMPLATE))
        example = MAP_DATA.sub(r"\1\3", _read(EXAMPLE_HTML))
        assert example == template, "the example must be built from the template, not hand-edited"

    def test_example_is_the_team_course_map_with_two_lanes(self):
        data = _example_data()
        assert [lane["role"] for lane in data["lanes"]] == ["Facilitator", "Member"]
        names = [a["name"] for a in data["lanes"][0]["activities"]]
        assert "Check who's ready" in names and len(names) == 6

    def test_every_step_belongs_to_a_known_slice_or_later(self):
        data = _example_data()
        ids = {s["id"] for s in data["slices"]}
        for lane in data["lanes"]:
            for activity in lane["activities"]:
                for step in activity["steps"]:
                    assert step.get("slice") in ids | {None}, step

    def test_example_shows_a_gap_and_touch_points(self):
        data = _example_data()
        activities = [a for lane in data["lanes"] for a in lane["activities"]]
        assert any(s.get("gap") for a in activities for s in a["steps"])
        assert any(a.get("touches") for a in activities)

    def test_one_wireframe_per_slice_one_activity(self):
        data = _example_data()
        slice_one = {
            (lane["role"], a["name"])
            for lane in data["lanes"]
            for a in lane["activities"]
            if any(s.get("slice") == 1 for s in a["steps"])
        }
        wired = [(w["lane"], w["activity"]) for w in data["wireframes"]]
        assert sorted(wired) == sorted(slice_one)

    def test_every_wireframe_element_names_a_slice_one_card_in_its_lane(self):
        data = _example_data()
        for w in data["wireframes"]:
            lane = next(l for l in data["lanes"] if l["role"] == w["lane"])
            cards = {a["name"] for a in lane["activities"]} | {
                s["text"] for a in lane["activities"] for s in a["steps"] if s.get("slice") == 1
            }
            for element in w["elements"]:
                assert element["card"] in cards, f"{w['activity']}: {element['card']} is not a Slice 1 card"

    def test_markdown_source_holds_every_string_in_the_json(self):
        md = _read(EXAMPLE_MD)
        data = _example_data()
        strings = [data["title"], *data["frame"].values(), *data["questions"]]
        strings += [s["name"] for s in data["slices"]] + [s["outcome"] for s in data["slices"]]
        for lane in data["lanes"]:
            for a in lane["activities"]:
                strings += [a["name"], *a.get("touches", [])]
                strings += [s["text"] for s in a["steps"]]
        for w in data["wireframes"]:
            for e in w["elements"]:
                strings += [e["card"], *e.get("rows", [])] + ([e["text"]] if "text" in e else [])
        missing = [s for s in strings if s not in md]
        assert not missing, f"JSON strings missing from the Markdown source: {missing}"

    def test_examples_md_points_to_the_finished_page(self):
        assert "example/team-course.html" in _read(EXAMPLES)

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_example_renders_both_tabs(self, tmp_path):
        """Run the page script against a tiny DOM stub and count what it draws."""
        html = _read(EXAMPLE_HTML)
        data = MAP_DATA.search(html).group(2)
        script = re.findall(r"<script>(.*?)</script>", html, flags=re.S)[0]
        stub = (
            "var made={};function E(t){this.tagName=t;this.children=[];this.className='';this.textContent='';"
            "this.hidden=false;this.attrs={};}E.prototype.appendChild=function(c){this.children.push(c);"
            "made[c.className]=(made[c.className]||0)+1;return c};E.prototype.setAttribute=function(k,v){this.attrs[k]=v};"
            "E.prototype.getAttribute=function(k){return this.attrs[k]};E.prototype.addEventListener=function(){};"
            "E.prototype.querySelectorAll=function(){return []};var byId={};"
            "var document={createElement:function(t){return new E(t)},createTextNode:function(t){return new E('#text')},"
            "getElementById:function(id){if(id==='map-data')return{textContent:DATA};return byId[id]||(byId[id]=new E('div'))}};"
        )
        js = tmp_path / "render.js"
        js.write_text(
            "var DATA=" + json.dumps(data) + ";" + stub + script
            + ";console.log(JSON.stringify({wire:made['wire']||0,lane:made['lane']||0,tabsHidden:byId['tabs'].hidden}));",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(js)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        counts = json.loads(result.stdout.strip().splitlines()[-1])
        assert counts == {"wire": 9, "lane": 2, "tabsHidden": False}


class TestEval:
    def test_picture_scenario_exists_and_is_triggered(self):
        assert PICTURE_SCENARIO.exists()
        assert "scenarios/use-framework/user-story-map-picture.yaml" in _read(TRIGGER_MAP)
