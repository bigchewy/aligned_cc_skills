"""Tests for the org chart seats file and its build script.

The script name has a hyphen, so every test calls it by subprocess.
"""
import copy
import re
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
