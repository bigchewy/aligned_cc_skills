#!/usr/bin/env python3
"""Build the org chart pages from skills/org-chart/seats.yaml and the two registries.

Steps: load -> validate -> render -> write. A data error stops the build before
anything is written: the script prints one ERROR line per problem to stderr and
exits 1.

This file holds load and validate. Rendering and the real --check comparison
come next; until then a valid run writes nothing and exits 0.
"""
import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ("b2b", "b2c")
HEADCOUNT = 100
COVERAGE_LEVELS = ("covered", "thin", "none")


def _read_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def seat_frameworks(seat):
    """Every framework id on a seat, job frameworks first, in file order."""
    out = []
    for job in seat.get("jobs") or []:
        if job.get("framework"):
            out.append(job["framework"])
        out.extend(job.get("also") or [])
    return out


def _reports_to_targets(seat):
    """reports_to is a seat id, or a map of chart -> seat id when it differs by chart."""
    value = seat.get("reports_to")
    if value is None:
        return []
    if isinstance(value, dict):
        return list(value.values())
    return [value]


def _check_coverage(seat, frameworks, advisors):
    """Return the reason a seat breaks its coverage rule, or None."""
    level = seat.get("coverage")
    missing = (seat.get("missing") or "").strip()
    if level not in COVERAGE_LEVELS:
        return "coverage must be covered, thin, or none"
    if level == "none":
        if frameworks:
            return "a seat with nothing yet has no frameworks"
        if seat.get("also_ask"):
            return "a seat with nothing yet has no also_ask"
        if not missing:
            return "missing must say what is not covered"
    elif level == "thin":
        if not missing:
            return "missing must say what is not covered"
    elif level == "covered":
        if len(advisors) < 2:
            return f"covered needs at least 2 advisors, has {len(advisors)}"
        if len(set(frameworks)) < 3:
            return f"covered needs at least 3 frameworks, has {len(set(frameworks))}"
    return None


def load_and_validate(seats_path, advisors_path, frameworks_path):
    """Load the seats file and registries. Return (data, errors)."""
    seats_doc = _read_yaml(seats_path)
    advisor_reg = {a["id"]: a for a in _read_yaml(advisors_path).get("advisors") or []}
    framework_reg = {f["id"]: f for f in _read_yaml(frameworks_path).get("frameworks") or []}

    departments = seats_doc.get("departments") or []
    seats = seats_doc.get("seats") or []
    holding = seats_doc.get("holding") or {}
    held_advisors = [h["id"] for h in holding.get("advisors") or []]
    held_frameworks = [h["id"] for h in holding.get("frameworks") or []]

    errors = []
    dept_ids = {d["id"] for d in departments}
    seat_ids = [s["id"] for s in seats]

    seen = set()
    for sid in seat_ids:
        if sid in seen:
            errors.append(f"ERROR: seat id '{sid}' is used twice")
        seen.add(sid)

    placed_frameworks = set()
    placed_advisors = set()
    totals = {chart: 0 for chart in CHARTS}

    for seat in seats:
        sid = seat["id"]

        if seat.get("dept") not in dept_ids:
            errors.append(f"ERROR: unknown dept '{seat.get('dept')}' on seat '{sid}'")
        for target in _reports_to_targets(seat):
            if target not in seen:
                errors.append(f"ERROR: unknown reports_to '{target}' on seat '{sid}'")

        people = seat.get("people") or {}
        charts = [c for c in people if c in CHARTS]
        if not charts:
            errors.append(f"ERROR: seat '{sid}' lists no chart")
        for chart in people:
            if chart not in CHARTS:
                errors.append(f"ERROR: unknown chart '{chart}' on seat '{sid}'")
            else:
                totals[chart] += people[chart]

        frameworks = seat_frameworks(seat)
        counted = set()
        fw_advisors = set()
        for fid in frameworks:
            if fid not in framework_reg:
                errors.append(f"ERROR: unknown framework '{fid}' on seat '{sid}'")
                continue
            if fid in counted:
                errors.append(f"ERROR: framework '{fid}' is on seat '{sid}' twice")
            counted.add(fid)
            fw_advisors.add(framework_reg[fid]["advisor"])
        placed_frameworks |= counted

        also_ask = seat.get("also_ask") or []
        for aid in also_ask:
            if aid not in advisor_reg:
                errors.append(f"ERROR: unknown advisor '{aid}' on seat '{sid}'")
            elif aid in fw_advisors:
                errors.append(f"ERROR: also_ask repeats advisor '{aid}' on seat '{sid}'")
        seat_advisors = fw_advisors | {a for a in also_ask if a in advisor_reg}
        placed_advisors |= seat_advisors

        reason = _check_coverage(seat, frameworks, seat_advisors)
        if reason:
            errors.append(
                f"ERROR: seat '{sid}' coverage '{seat.get('coverage')}' breaks the rule: {reason}"
            )

    for chart in CHARTS:
        if totals[chart] != HEADCOUNT:
            errors.append(f"ERROR: {chart} headcount is {totals[chart]}, expected {HEADCOUNT}")

    for fid in held_frameworks:
        if fid not in framework_reg:
            errors.append(f"ERROR: unknown framework '{fid}' on seat 'holding'")
        if fid in placed_frameworks:
            errors.append(f"ERROR: '{fid}' is both on a seat and in holding")
    for aid in held_advisors:
        if aid not in advisor_reg:
            errors.append(f"ERROR: unknown advisor '{aid}' on seat 'holding'")
        if aid in placed_advisors:
            errors.append(f"ERROR: '{aid}' is both on a seat and in holding")

    for fid in framework_reg:
        if fid not in placed_frameworks and fid not in held_frameworks:
            errors.append(f"ERROR: unplaced framework '{fid}'")
    for aid in advisor_reg:
        if aid not in placed_advisors and aid not in held_advisors:
            errors.append(f"ERROR: unplaced advisor '{aid}'")

    data = {
        "departments": departments,
        "seats": seats,
        "holding": holding,
        "advisors": advisor_reg,
        "frameworks": framework_reg,
    }
    return data, errors


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seats", default=ROOT / "skills" / "org-chart" / "seats.yaml")
    parser.add_argument("--advisors", default=ROOT / "advisors" / "registry.yaml")
    parser.add_argument("--frameworks", default=ROOT / "frameworks" / "registry.yaml")
    parser.add_argument("--out", default=ROOT / "skills" / "org-chart" / "pages")
    parser.add_argument("--author-out", default=ROOT / "docs" / "plans" / "org-chart-coverage.html")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when the committed pages differ from a fresh build",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    data, errors = load_and_validate(args.seats, args.advisors, args.frameworks)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    # Rendering and writing slot in here: render(data) -> write(args.out, args.author_out),
    # and --check compares the fresh build with what is on disk.
    return 0


if __name__ == "__main__":
    sys.exit(main())
