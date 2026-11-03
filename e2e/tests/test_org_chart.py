"""Tests for the org chart seats file and its build script.

The script name has a hyphen, so every test calls it by subprocess.
"""
import copy
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-org-chart.py"
SEATS = ROOT / "skills" / "org-chart" / "seats.yaml"
ADVISORS = ROOT / "advisors" / "registry.yaml"
FRAMEWORKS = ROOT / "frameworks" / "registry.yaml"
CHARTS = ("b2b", "b2c")

# Copied from the six test_*_replaces_* / test_devex_engineer_retired.py files.
RETIRED_PATTERNS = [
    re.compile(r"the-qa-engineer|QA Engineer", re.IGNORECASE),
    re.compile(r"seo-expert|SEO Expert", re.IGNORECASE),
    re.compile(r"the-designer|The Designer", re.IGNORECASE),
    re.compile(r"the-pm\b|The PM\b", re.IGNORECASE),
    re.compile(r"the-devex-engineer|DevEx Engineer", re.IGNORECASE),
    re.compile(r"the-security-reviewer|Security Reviewer", re.IGNORECASE),
]


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def write_seats(tmp_path, data):
    path = tmp_path / "seats.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def load(path):
    return yaml.safe_load(Path(path).read_text())


def seats_data():
    return load(SEATS)


def framework_registry():
    return {f["id"]: f for f in load(FRAMEWORKS)["frameworks"]}


def advisor_registry():
    return {a["id"]: a for a in load(ADVISORS)["advisors"]}


def seat_frameworks(seat):
    out = []
    for job in seat.get("jobs") or []:
        out.append(job["framework"])
        out.extend(job.get("also") or [])
    return out


def seat_advisors(seat, fw_reg):
    advisors = {fw_reg[f]["advisor"] for f in seat_frameworks(seat)}
    return advisors | set(seat.get("also_ask") or [])


# ---------------------------------------------------------------- real data


def test_real_seats_file_validates(tmp_path):
    result = run("--out", tmp_path, "--author-out", tmp_path / "a.html")
    assert result.returncode == 0, result.stderr


def test_every_framework_placed_once():
    data = seats_data()
    on_seats = set()
    for seat in data["seats"]:
        fws = seat_frameworks(seat)
        assert len(fws) == len(set(fws)), f"{seat['id']} lists a framework twice"
        on_seats |= set(fws)
    held = {h["id"] for h in data["holding"].get("frameworks") or []}
    assert not (on_seats & held), f"both on a seat and in holding: {on_seats & held}"
    unplaced = set(framework_registry()) - on_seats - held
    assert not unplaced, f"unplaced frameworks: {sorted(unplaced)}"


def test_every_advisor_placed():
    data = seats_data()
    fw_reg = framework_registry()
    placed = set()
    for seat in data["seats"]:
        placed |= seat_advisors(seat, fw_reg)
    held = {h["id"] for h in data["holding"].get("advisors") or []}
    assert not (placed & held), f"both on a seat and in holding: {placed & held}"
    unplaced = set(advisor_registry()) - placed - held
    assert not unplaced, f"unplaced advisors: {sorted(unplaced)}"


def test_coverage_rules():
    fw_reg = framework_registry()
    for seat in seats_data()["seats"]:
        sid, cov = seat["id"], seat["coverage"]
        fws = seat_frameworks(seat)
        if cov == "none":
            assert not fws, f"{sid} is none but has frameworks"
            assert not seat.get("also_ask"), f"{sid} is none but has also_ask"
            assert seat.get("missing"), f"{sid} is none but has no missing"
        elif cov == "thin":
            assert seat.get("missing"), f"{sid} is thin but has no missing"
        elif cov == "covered":
            assert len(seat_advisors(seat, fw_reg)) >= 2, sid
            assert len(set(fws)) >= 3, sid
        else:
            raise AssertionError(f"{sid} has unknown coverage {cov!r}")


def test_also_ask_never_repeats_a_framework_advisor():
    fw_reg = framework_registry()
    for seat in seats_data()["seats"]:
        via_fw = {fw_reg[f]["advisor"] for f in seat_frameworks(seat)}
        repeats = via_fw & set(seat.get("also_ask") or [])
        assert not repeats, f"{seat['id']} repeats {repeats}"


def test_headcounts_total_100():
    seats = seats_data()["seats"]
    for chart in CHARTS:
        total = sum(s["people"][chart] for s in seats if chart in s["people"])
        assert total == 100, f"{chart} totals {total}"


def test_every_seat_lists_a_chart():
    for seat in seats_data()["seats"]:
        assert set(seat["people"]) & set(CHARTS), seat["id"]
        assert set(seat["people"]) <= set(CHARTS), seat["id"]


def test_seat_ids_are_unique_kebab_case():
    ids = [s["id"] for s in seats_data()["seats"]]
    assert len(ids) == len(set(ids))
    for sid in ids:
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", sid), sid


def test_board_is_dotted_and_unpaid():
    board = next(s for s in seats_data()["seats"] if s["id"] == "board")
    assert board["people"] == {"b2b": 0, "b2c": 0}
    assert board["dotted"] is True
    assert "reports_to" not in board


def test_seat_names_avoid_retired_patterns():
    text = SEATS.read_text()
    for pattern in RETIRED_PATTERNS:
        assert not pattern.search(text), pattern.pattern


def test_seats_text_has_no_dashes():
    text = SEATS.read_text()
    assert "—" not in text and "–" not in text


def test_missing_lines_talk_to_the_ceo_not_about_the_plugin():
    # A missing line says what the CEO has to get elsewhere. It never reads
    # like the plugin's backlog: no advisor names, frameworks, or coverage talk.
    names = [a["name"] for a in advisor_registry().values()]
    fw_names = [f["name"] for f in framework_registry().values()]
    banned = re.compile(r"\b(framework|frameworks|advisor|advisors|plugin|covered|nothing yet)\b", re.I)
    for seat in seats_data()["seats"]:
        missing = seat.get("missing") or ""
        assert not banned.search(missing), (seat["id"], missing)
        for name in names + fw_names:
            assert name not in missing, (seat["id"], name)


def test_healthcare_motion_job_is_scoped_and_last():
    seat = next(s for s in seats_data()["seats"] if s["id"] == "head-of-sales")
    last = seat["jobs"][-1]
    assert last["framework"] == "5-gtm-motions-digital-health"
    assert "healthcare" in last["do"]


def test_departments_in_order():
    ids = [d["id"] for d in seats_data()["departments"]]
    assert ids == ["lead", "product", "eng", "mkt", "sales", "cust", "people", "ops"]


# ---------------------------------------------------------------- error paths


def tiny_registries(tmp_path):
    advisors = {
        "advisors": [
            {"id": "a1", "name": "A One", "summary": "first"},
            {"id": "a2", "name": "A Two", "summary": "second"},
        ]
    }
    frameworks = {
        "frameworks": [
            {"id": "f1", "advisor": "a1", "name": "F1", "purpose": "p1"},
            {"id": "f2", "advisor": "a2", "name": "F2", "purpose": "p2"},
            {"id": "f3", "advisor": "a1", "name": "F3", "purpose": "p3"},
        ]
    }
    a = tmp_path / "advisors.yaml"
    f = tmp_path / "frameworks.yaml"
    a.write_text(yaml.safe_dump(advisors))
    f.write_text(yaml.safe_dump(frameworks))
    return a, f


BASE = {
    "departments": [{"id": "lead", "name": "Leadership team"}],
    "seats": [
        {
            "id": "ceo",
            "dept": "lead",
            "name": "CEO",
            "people": {"b2b": 99, "b2c": 99},
            "coverage": "covered",
            "does": "Runs the company.",
            "jobs": [
                {"do": "Set the strategy", "framework": "f1", "also": ["f2"]},
                {"do": "Make the call", "framework": "f3"},
            ],
            "also_ask": [],
        },
        {
            "id": "coo",
            "dept": "lead",
            "name": "COO",
            "people": {"b2b": 1, "b2c": 1},
            "reports_to": "ceo",
            "coverage": "none",
            "does": "Runs operations.",
            "jobs": [],
            "missing": "Everything.",
        },
    ],
    "holding": {"advisors": [], "frameworks": []},
}


def run_tiny(tmp_path, data):
    a, f = tiny_registries(tmp_path)
    seats = write_seats(tmp_path, data)
    return run(
        "--seats", seats, "--advisors", a, "--frameworks", f,
        "--out", tmp_path / "out", "--author-out", tmp_path / "a.html",
    )


def test_tiny_base_is_valid(tmp_path):
    result = run_tiny(tmp_path, BASE)
    assert result.returncode == 0, result.stderr


def test_unknown_framework_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][0]["jobs"][1]["also"] = ["nope"]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unknown framework 'nope' on seat 'ceo'" in result.stderr.splitlines()


def test_unknown_advisor_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][0]["also_ask"] = ["ghost"]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unknown advisor 'ghost' on seat 'ceo'" in result.stderr.splitlines()


def test_unplaced_framework_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][0]["jobs"].pop()  # f3 is now nowhere
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unplaced framework 'f3'" in result.stderr.splitlines()


def test_unplaced_advisor_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][0]["jobs"][0]["also"] = []
    data["holding"]["frameworks"] = [{"id": "f2", "why": "undecided"}]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unplaced advisor 'a2'" in result.stderr.splitlines()


def test_also_ask_repeat_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][0]["also_ask"] = ["a1"]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: also_ask repeats advisor 'a1' on seat 'ceo'" in result.stderr.splitlines()


def test_both_seat_and_holding_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["holding"]["frameworks"] = [{"id": "f2", "why": "undecided"}]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: 'f2' is both on a seat and in holding" in result.stderr.splitlines()


def test_coverage_rule_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][1]["missing"] = None
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    lines = result.stderr.splitlines()
    assert any(
        line.startswith("ERROR: seat 'coo' coverage 'none' breaks the rule: ")
        for line in lines
    ), lines


def test_bad_headcount_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][1]["people"]["b2c"] = 3
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: b2c headcount is 102, expected 100" in result.stderr.splitlines()


def test_unknown_dept_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][1]["dept"] = "nowhere"
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unknown dept 'nowhere' on seat 'coo'" in result.stderr.splitlines()


def test_unknown_reports_to_fails(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][1]["reports_to"] = "boss"
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    assert "ERROR: unknown reports_to 'boss' on seat 'coo'" in result.stderr.splitlines()


def test_errors_are_all_reported(tmp_path):
    data = copy.deepcopy(BASE)
    data["seats"][1]["dept"] = "nowhere"
    data["seats"][0]["also_ask"] = ["a1"]
    result = run_tiny(tmp_path, data)
    assert result.returncode == 1
    lines = result.stderr.splitlines()
    assert "ERROR: unknown dept 'nowhere' on seat 'coo'" in lines
    assert "ERROR: also_ask repeats advisor 'a1' on seat 'ceo'" in lines


# ---------------------------------------------------------------- rendered pages

PAGES = ROOT / "skills" / "org-chart" / "pages"
CHART_FILES = {"b2b": "index.html", "b2c": "b2c.html"}
HREF = re.compile(r'href="([^"]+)"')


def page_files():
    files = sorted(p for p in PAGES.rglob("*") if p.is_file())
    assert files, f"no pages in {PAGES}"
    return files


def html_pages():
    return [p for p in page_files() if p.suffix == ".html"]


def test_committed_pages_are_current():
    result = run("--check")
    assert result.returncode == 0, result.stderr


def test_check_detects_stale_page(tmp_path):
    out = tmp_path / "pages"
    shutil.copytree(PAGES, out)
    page = out / "seats" / "support.html"
    text = page.read_text(encoding="utf-8")
    page.write_text(text.replace("Support", "Supporx", 1), encoding="utf-8")
    result = run("--check", "--out", out)
    assert result.returncode == 1
    lines = result.stderr.splitlines()
    assert any(
        line.startswith("ERROR: stale page ") and "support.html" in line
        and line.endswith("; run scripts/generate-org-chart.py")
        for line in lines
    ), lines
    assert len(lines) == 1, lines


def test_check_detects_missing_and_extra_files(tmp_path):
    out = tmp_path / "pages"
    shutil.copytree(PAGES, out)
    (out / "style.css").unlink()
    (out / "seats" / "old-seat.html").write_text("old", encoding="utf-8")
    result = run("--check", "--out", out)
    assert result.returncode == 1
    assert "style.css" in result.stderr
    assert "old-seat.html" in result.stderr


def test_check_writes_nothing(tmp_path):
    out = tmp_path / "pages"
    result = run("--check", "--out", out, "--author-out", tmp_path / "a.html")
    assert result.returncode == 1
    assert not out.exists()
    assert not (tmp_path / "a.html").exists()


def test_chart_links_resolve():
    data = seats_data()
    for chart, name in CHART_FILES.items():
        page = PAGES / name
        text = page.read_text(encoding="utf-8")
        for href in HREF.findall(text):
            if href.endswith(".html"):
                assert (page.parent / href).exists(), f"{name} links missing {href}"
        for seat in data["seats"]:
            linked = f'href="seats/{seat["id"]}.html"' in text
            assert linked == (chart in seat["people"]), f"{name} and {seat['id']}"
    assert 'href="b2c.html"' in (PAGES / "index.html").read_text(encoding="utf-8")
    assert 'href="index.html"' in (PAGES / "b2c.html").read_text(encoding="utf-8")


def test_every_seat_page_exists_and_links_resolve():
    for seat in seats_data()["seats"]:
        page = PAGES / "seats" / f"{seat['id']}.html"
        assert page.exists(), seat["id"]
        text = page.read_text(encoding="utf-8")
        for href in HREF.findall(text):
            if href.endswith(".html"):
                assert (page.parent / href).exists(), f"{seat['id']} links missing {href}"
        for chart, name in CHART_FILES.items():
            linked = f'href="../{name}"' in text
            assert linked == (chart in seat["people"]), f"{seat['id']} and {name}"


def test_shared_seat_links_both_charts():
    text = (PAGES / "seats" / "support.html").read_text(encoding="utf-8")
    assert 'href="../index.html"' in text
    assert 'href="../b2c.html"' in text
    assert re.search(r"\b5 people\b", text)
    assert re.search(r"\b10 people\b", text)


def test_partnerships_alone_in_b2c_sales_column():
    text = (PAGES / "b2c.html").read_text(encoding="utf-8")
    col = re.search(r'<section class="dept" id="dept-sales">(.*?)</section>', text, re.S)
    assert col, "b2c has no sales column"
    assert re.findall(r'href="seats/([^"]+)\.html"', col.group(1)) == ["partnerships"]


def test_columns_follow_seats_file_order():
    data = seats_data()
    for chart, name in CHART_FILES.items():
        text = (PAGES / name).read_text(encoding="utf-8")
        linked = re.findall(r'href="seats/([^"]+)\.html"', text)
        expected = [s["id"] for s in data["seats"] if chart in s["people"]]
        assert sorted(linked) == sorted(expected), name
        # Board and CEO sit above the columns; every column seat keeps file order.
        top = ("board", "ceo")
        assert linked[:2] == ["board", "ceo"], name
        assert [i for i in linked if i not in top] == [i for i in expected if i not in top], name


def test_support_reports_to_differs_by_chart():
    b2b = (PAGES / "index.html").read_text(encoding="utf-8")
    b2c = (PAGES / "b2c.html").read_text(encoding="utf-8")
    assert 'href="seats/support.html" data-reports-to="head-of-customer-success"' in b2b
    assert 'href="seats/support.html" data-reports-to="head-of-customer-experience"' in b2c


def test_commands_name_real_ids():
    fw = set(framework_registry())
    adv = set(advisor_registry())
    seen = 0
    for page in (PAGES / "seats").glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for fid in re.findall(r"/aligned:use-framework ([a-z0-9-]+)", text):
            assert fid in fw, f"{page.name} names {fid}"
            seen += 1
        for aid in re.findall(r"/aligned:use-advisor ([a-z0-9-]+)", text):
            assert aid in adv, f"{page.name} names {aid}"
            seen += 1
    assert seen > 0


def test_seat_page_lists_every_framework_and_advisor():
    fw_reg = framework_registry()
    adv_reg = advisor_registry()
    for seat in seats_data()["seats"]:
        text = (PAGES / "seats" / f"{seat['id']}.html").read_text(encoding="utf-8")
        for fid in seat_frameworks(seat):
            assert f"/aligned:use-framework {fid}<" in text, (seat["id"], fid)
        for aid in seat_advisors(seat, fw_reg):
            name = html.escape(adv_reg[aid]["name"], quote=False)
            assert f'<th scope="row">{name}</th>' in text, (seat["id"], aid)


def test_advisor_section_is_a_plain_table():
    fw_reg = framework_registry()
    adv_reg = advisor_registry()
    for seat in seats_data()["seats"]:
        text = (PAGES / "seats" / f"{seat['id']}.html").read_text(encoding="utf-8")
        advisors = seat_advisors(seat, fw_reg)
        if not advisors:
            assert "Ask an advisor" not in text
            continue
        section = text.split("<h2>Ask an advisor</h2>", 1)[1].split("</section>", 1)[0]
        assert "/aligned:use-advisor" not in section
        assert 'class="copy"' not in section
        assert '<table class="advisor-table">' in section
        names = {html.escape(adv_reg[a]["name"], quote=False) for a in advisors}
        example = re.search(r"Talk to my advisor, (.+?)\.”", section)
        assert example and example.group(1) in names, (seat["id"], example and example.group(1))


def test_missing_block_on_every_seat_with_missing():
    for seat in seats_data()["seats"]:
        text = (PAGES / "seats" / f"{seat['id']}.html").read_text(encoding="utf-8")
        has_block = "<h2>Not covered yet</h2>" in text or "<h2>Still missing</h2>" in text
        assert has_block == bool(seat.get("missing")), seat["id"]


def test_missing_block_title_follows_coverage():
    seen = set()
    for seat in seats_data()["seats"]:
        if not seat.get("missing"):
            continue
        text = (PAGES / "seats" / f"{seat['id']}.html").read_text(encoding="utf-8")
        if seat["coverage"] == "covered":
            assert "<h2>Still missing</h2>" in text, seat["id"]
            assert "Not covered yet" not in text, seat["id"]
        else:
            assert "<h2>Not covered yet</h2>" in text, seat["id"]
            assert "Still missing" not in text, seat["id"]
        seen.add(seat["coverage"])
    assert seen == {"covered", "thin", "none"}


def test_empty_seat_shows_only_missing_block():
    text = (PAGES / "seats" / "devops.html").read_text(encoding="utf-8")
    assert "Not covered yet" in text
    assert "Ask an advisor" not in text
    assert "/aligned:use-" not in text


def test_registry_text_is_escaped():
    text = (PAGES / "seats" / "head-of-people.html").read_text(encoding="utf-8")
    assert "Pain + Reflection" in text
    tttc = (PAGES / "seats" / "head-of-sales.html").read_text(encoding="utf-8")
    assert "Teach-Tailor-Take Control (TTTC)" in tttc
    for page in html_pages():
        body = page.read_text(encoding="utf-8")
        # Every '<' opens a tag or comment; registry text never leaks one raw.
        for m in re.finditer(r"<", body):
            nxt = body[m.end():m.end() + 1]
            assert re.match(r"[a-zA-Z/!]", nxt), f"{page.name}: raw '<' at {m.start()}"


def test_escaping_with_hostile_registry(tmp_path):
    a, f = tiny_registries(tmp_path)
    reg = load(f)
    reg["frameworks"][0]["name"] = 'Fish & <Chips> "Quoted"'
    reg["frameworks"][0]["purpose"] = "uses <script>alert(1)</script> here"
    f.write_text(yaml.safe_dump(reg))
    seats = write_seats(tmp_path, BASE)
    out = tmp_path / "out"
    result = run(
        "--seats", seats, "--advisors", a, "--frameworks", f,
        "--out", out, "--author-out", tmp_path / "a.html",
    )
    assert result.returncode == 0, result.stderr
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert "Fish &amp; &lt;Chips&gt; &quot;Quoted&quot;" in text
    assert "<script>alert" not in text
    assert "Uses &lt;script&gt;" in text


def test_registry_dashes_become_commas(tmp_path):
    a, f = tiny_registries(tmp_path)
    reg = load(f)
    reg["frameworks"][0]["purpose"] = "pick one motion — then commit for 18–24 months"
    f.write_text(yaml.safe_dump(reg))
    seats = write_seats(tmp_path, BASE)
    out = tmp_path / "out"
    result = run(
        "--seats", seats, "--advisors", a, "--frameworks", f,
        "--out", out, "--author-out", tmp_path / "a.html",
    )
    assert result.returncode == 0, result.stderr
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert "Pick one motion, then commit for 18 to 24 months" in text


def build_tiny(tmp_path, data=None, frameworks=None, advisors=None):
    """Build the tiny fixture with registry edits; return the out dir."""
    a, f = tiny_registries(tmp_path)
    if frameworks:
        reg = load(f)
        for i, changes in frameworks.items():
            reg["frameworks"][i].update(changes)
        f.write_text(yaml.safe_dump(reg))
    if advisors:
        reg = load(a)
        for i, changes in advisors.items():
            reg["advisors"][i].update(changes)
        a.write_text(yaml.safe_dump(reg))
    seats = write_seats(tmp_path, data or BASE)
    out = tmp_path / "out"
    result = run(
        "--seats", seats, "--advisors", a, "--frameworks", f,
        "--out", out, "--author-out", tmp_path / "a.html",
    )
    assert result.returncode == 0, result.stderr
    return out


def test_number_ranges_read_as_to(tmp_path):
    out = build_tiny(tmp_path, frameworks={
        0: {"purpose": "teams of 3–10 people"},
        1: {"purpose": "runs 3 – 10 weeks — then stops"},
    })
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert "Teams of 3 to 10 people." in text
    assert "Runs 3 to 10 weeks, then stops." in text


def test_framework_names_drop_leading_lowercase_article(tmp_path):
    out = build_tiny(tmp_path, frameworks={
        0: {"name": "the Bowtie Funnel"},
        1: {"name": "an 80/20 Audit"},
        2: {"name": "a Weekly Review"},
    })
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert '<div class="who">Bowtie Funnel <span' in text
    assert '<div class="who">80/20 Audit <span' in text
    assert '<div class="who">Weekly Review <span' in text


def test_framework_names_keep_capitalized_article(tmp_path):
    out = build_tiny(tmp_path, frameworks={0: {"name": "The Algorithm"}})
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert '<div class="who">The Algorithm <span' in text


def test_real_cards_have_no_lowercase_article():
    for page in (PAGES / "seats").glob("*.html"):
        text = page.read_text(encoding="utf-8")
        assert not re.search(r'<div class="who">(the|an|a) ', text), page.name


def test_purpose_and_summary_end_with_period(tmp_path):
    out = build_tiny(
        tmp_path,
        frameworks={0: {"purpose": "plain purpose"}, 1: {"purpose": "asks why?"}},
        advisors={0: {"summary": "plain summary"}},
    )
    text = (out / "seats" / "ceo.html").read_text(encoding="utf-8")
    assert '<p class="why">Plain purpose.</p>' in text
    assert '<p class="why">Asks why?</p>' in text
    assert "<td>Plain summary.</td>" in text


def test_real_why_lines_end_in_punctuation():
    for page in (PAGES / "seats").glob("*.html"):
        for line in re.findall(r'<p class="why">(.*?)</p>', page.read_text(encoding="utf-8")):
            assert re.search(r"[.!?][\"')\]]*$", html_unescape(line)), (page.name, line)


def html_unescape(value):
    import html
    return html.unescape(value)


def test_empty_chart_cards_skip_job_count():
    for name in CHART_FILES.values():
        text = (PAGES / name).read_text(encoding="utf-8")
        assert "0 jobs" not in text, name
        assert re.search(r"\b[1-9]\d* jobs?<", text), name


def test_column_totals_sum_to_headcount():
    for name in CHART_FILES.values():
        text = (PAGES / name).read_text(encoding="utf-8")
        heads = re.findall(
            r'<div class="dept-head"><h3>[^<]*</h3><span class="seat-n">(\d+) (?:person|people)</span>',
            text,
        )
        assert heads, name
        assert sum(int(n) for n in heads) == 100, (name, heads)


def test_purpose_first_letter_capitalized():
    text = (PAGES / "seats" / "head-of-people.html").read_text(encoding="utf-8")
    assert "Transforming failure and pain into progress" in text


def test_no_network_scripts():
    for page in html_pages():
        text = page.read_text(encoding="utf-8")
        assert "<script src=" not in text, page.name
        for link in re.findall(r"<link\b[^>]*>", text):
            for url in re.findall(r'href="(https?://[^"]+)"', link):
                assert url.startswith("https://fonts.googleapis.com/"), (page.name, url)
    css = (PAGES / "style.css").read_text(encoding="utf-8")
    assert "@import" not in css
    assert "system-ui" in css


def test_pages_avoid_retired_patterns():
    for path in (ROOT / "skills" / "org-chart").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for pattern in RETIRED_PATTERNS:
                assert not pattern.search(text), (path.name, pattern.pattern)


def test_no_dashes_in_pages():
    for path in page_files():
        text = path.read_text(encoding="utf-8")
        assert "–" not in text and "—" not in text, path.name


def test_page_titles():
    assert "<title>B2B Org Chart</title>" in (PAGES / "index.html").read_text(encoding="utf-8")
    assert "<title>B2C Org Chart</title>" in (PAGES / "b2c.html").read_text(encoding="utf-8")
    support = (PAGES / "seats" / "support.html").read_text(encoding="utf-8")
    assert "<title>Support</title>" in support


def test_chart_fixed_text():
    for name in CHART_FILES.values():
        text = (PAGES / name).read_text(encoding="utf-8")
        assert '<p class="sub">Aligned advisors and frameworks by role</p>' in text


def test_charts_have_no_tiles():
    for name in CHART_FILES.values():
        text = (PAGES / name).read_text(encoding="utf-8")
        assert 'class="tiles"' not in text
        assert "Headcounts are a typical split" not in text


def test_chart_legend_is_a_footer():
    for name in CHART_FILES.values():
        text = (PAGES / name).read_text(encoding="utf-8")
        footer = text.split('<footer class="legend-foot"', 1)
        assert len(footer) == 2, f"{name} has no legend footer"
        assert 'class="legend"' not in footer[0], f"{name} shows the legend above the footer"
        for level in ("covered", "thin", "none"):
            assert f'class="pill {level}"' in footer[1]


def test_switch_has_three_choices():
    for name in list(CHART_FILES.values()) + ["background.html"]:
        text = (PAGES / name).read_text(encoding="utf-8")
        switch = text.split('<nav class="switch"', 1)[1].split("</nav>", 1)[0]
        assert 'href="index.html"' in switch
        assert 'href="b2c.html"' in switch
        assert 'href="background.html"' in switch
        assert switch.count('aria-current="page"') == 1


def test_background_page():
    text = (PAGES / "background.html").read_text(encoding="utf-8")
    assert "<title>Background</title>" in text
    assert "Headcounts are a typical split for 100 people, rounded." in text
    for label in ("Advisors", "Frameworks", "Seats", "Seats with nothing yet"):
        assert f"<th scope=\"row\">{label}</th>" in text
    data = seats_data()
    for chart in ("b2b", "b2c"):
        seats = [s for s in data["seats"] if chart in s["people"]]
        none = sum(1 for s in seats if s["coverage"] == "none")
        assert f'data-chart="{chart}" data-row="seats">{len(seats)}<' in text
        assert f'data-chart="{chart}" data-row="none">{none}<' in text


def test_build_is_deterministic(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    assert run("--out", one, "--author-out", tmp_path / "a1.html").returncode == 0
    assert run("--out", two, "--author-out", tmp_path / "a2.html").returncode == 0
    files_one = sorted(p.relative_to(one) for p in one.rglob("*") if p.is_file())
    files_two = sorted(p.relative_to(two) for p in two.rglob("*") if p.is_file())
    assert files_one and files_one == files_two
    for rel in files_one:
        assert (one / rel).read_bytes() == (two / rel).read_bytes(), rel
    assert (tmp_path / "a1.html").read_bytes() == (tmp_path / "a2.html").read_bytes()


def test_author_page_lists_gaps_and_holding(tmp_path):
    author = tmp_path / "a.html"
    assert run("--out", tmp_path / "out", "--author-out", author).returncode == 0
    text = author.read_text(encoding="utf-8")
    assert "<h2>Holding list</h2>" in text
    held = seats_data().get("holding") or {}
    names = {**{a["id"]: a["name"] for a in load(ADVISORS)["advisors"]},
             **{f["id"]: f["name"] for f in load(FRAMEWORKS)["frameworks"]}}
    for entry in (held.get("advisors") or []) + (held.get("frameworks") or []):
        assert names[entry["id"]] in text
    # Nothing first, then thin by headcount.
    b2b = text.split('id="gaps-b2b"')[1].split("</table>")[0]
    assert b2b.index("Support") < b2b.index("Software engineers")
    assert b2b.index("Software engineers") < b2b.index("Security")
    assert "Head of product" not in b2b


def test_build_removes_stale_pages(tmp_path):
    out = tmp_path / "out"
    (out / "seats").mkdir(parents=True)
    (out / "seats" / "old-seat.html").write_text("old", encoding="utf-8")
    assert run("--out", out, "--author-out", tmp_path / "a.html").returncode == 0
    assert not (out / "seats" / "old-seat.html").exists()
    assert run("--check", "--out", out).returncode == 0


# ---- Task 6: skill, hook, add-skill steps, README ----

SKILL_MD = ROOT / "skills" / "org-chart" / "SKILL.md"
HOOK = ROOT / "scripts" / "hooks" / "pre-commit"
README = ROOT / "README.md"


def _section(text, heading):
    """Text from the heading up to the next '### ' heading."""
    start = text.index(heading)
    nxt = text.find("\n### ", start + 1)
    return text[start : nxt if nxt != -1 else len(text)]


def test_skill_frontmatter():
    text = SKILL_MD.read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["name"] == "org-chart"
    assert fm["description"].startswith("Use when")
    assert "**Path Resolution:**" in text
    assert "skills/_shared/resolve-skill-path.md" in text
    for cmd in ("open", "xdg-open", 'cmd /c start ""'):
        assert cmd in text
    assert "pages/index.html" in text
    assert "—" not in text and "–" not in text


def test_skill_description_stays_on_org_chart_requests():
    fm = yaml.safe_load(SKILL_MD.read_text().split("---")[1])
    desc = fm["description"]
    assert "org chart" in desc
    assert "not hired" in desc
    assert "use-framework" in desc
    assert "such as sales, marketing, hiring, or strategy" not in desc


def test_add_framework_offers_holding():
    fw = _section((ROOT / "skills/add-framework/SKILL.md").read_text(), "### 7.")
    assert "fits no seat" in fw
    assert "`holding`" in fw


def test_authoring_mode_has_no_stale_counts():
    text = (ROOT / "skills/brainstorming/modes/authoring.md").read_text()
    assert not re.search(r"\b\d+ frameworks \+ \d+ advisors\b", text)


def test_readme_lists_org_chart():
    assert "/aligned:org-chart" in README.read_text()


def test_hook_rebuilds_org_chart():
    text = HOOK.read_text()
    assert "generate-org-chart.py" in text
    for path in (
        "advisors/registry.yaml",
        "frameworks/registry.yaml",
        "skills/org-chart/seats.yaml",
        "scripts/org-chart-templates",
    ):
        assert path in text


def test_hook_tolerates_missing_python(tmp_path):
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    result = subprocess.run(
        ["/bin/bash", "-c", f'source "{HOOK}"; rebuild_org_chart'],
        capture_output=True,
        text=True,
        env={"PATH": str(empty_bin), "REPO_ROOT": str(fake_root)},
    )
    assert result.returncode == 0
    assert "org chart NOT rebuilt" in result.stdout + result.stderr


def _fake_repo(tmp_path, generator_body):
    """A repo root whose venv python is the real one and whose generator is a stub."""
    fake_root = tmp_path / "repo"
    (fake_root / "e2e" / ".venv" / "bin").mkdir(parents=True)
    py = fake_root / "e2e" / ".venv" / "bin" / "python"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    py.chmod(0o755)
    (fake_root / "scripts").mkdir()
    (fake_root / "scripts" / "generate-org-chart.py").write_text(generator_body)
    return fake_root


def _source_hook(fake_root, tmp_path):
    return subprocess.run(
        ["/bin/bash", "-c", f'source "{HOOK}"; rebuild_org_chart; echo "after=$?"'],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "REPO_ROOT": str(fake_root), "HOME": str(tmp_path)},
    )


def test_hook_tolerates_build_failure(tmp_path):
    stub = "import sys\nprint('ERROR: boom', file=sys.stderr)\nsys.exit(1)\n"
    fake_root = _fake_repo(tmp_path, stub)
    result = _source_hook(fake_root, tmp_path)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "after=0" in result.stdout
    assert "org chart build failed" in out
    assert "ERROR: boom" in out


def test_hook_tolerates_staging_failure(tmp_path):
    # The stub build succeeds, but tmp_path is not a repository, so staging fails.
    fake_root = _fake_repo(tmp_path, "pass\n")
    result = _source_hook(fake_root, tmp_path)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "after=0" in result.stdout
    assert "NOT staged" in out


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={"PATH": "/usr/bin:/bin", "HOME": str(cwd),
                        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def test_hook_uses_main_checkout_venv_from_a_worktree(tmp_path):
    # A worktree has no e2e/.venv of its own. The hook must find the main
    # checkout's venv instead of falling back to system python3.
    main = _fake_repo(tmp_path, "pass\n")
    (main / "skills" / "org-chart" / "pages").mkdir(parents=True)
    (main / "skills" / "org-chart" / "pages" / "index.html").write_text("x")
    _git(main, "init", "-q")
    # Commit everything but the venv: like the real repo, e2e/.venv is untracked.
    _git(main, "add", "scripts", "skills")
    _git(main, "commit", "-q", "-m", "init")
    wt = tmp_path / "wt"
    _git(main, "worktree", "add", "-q", str(wt))
    (wt / "scripts" / "generate-org-chart.py").write_text("pass\n")
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    (empty_bin / "git").symlink_to("/usr/bin/git")
    result = subprocess.run(
        ["/bin/bash", "-c", f'source "{HOOK}"; rebuild_org_chart'],
        capture_output=True, text=True, cwd=wt,
        env={"PATH": str(empty_bin), "REPO_ROOT": str(wt), "HOME": str(tmp_path)},
    )
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "Org chart pages rebuilt" in out


def test_hook_skips_python_that_cannot_parse_the_generator(tmp_path):
    # An interpreter that has PyYAML but is too old for the generator's syntax
    # must be skipped with a warning, not run into a SyntaxError.
    fake_root = _fake_repo(tmp_path, "def broken(:\n")
    result = _source_hook(fake_root, tmp_path)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "after=0" in result.stdout
    assert "SyntaxError" not in out
    assert "org chart NOT rebuilt" in out


def test_add_skills_place_new_entries():
    adv = _section((ROOT / "skills/add-advisor/SKILL.md").read_text(), "### 8.")
    fw = _section((ROOT / "skills/add-framework/SKILL.md").read_text(), "### 7.")
    for step in (adv, fw):
        assert "skills/org-chart/seats.yaml" in step
        assert "generate-org-chart.py" in step
        assert "skip when `scripts/generate-org-chart.py` does not exist" in step
        assert "e2e/tests/test_org_chart.py" in step
