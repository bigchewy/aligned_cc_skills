#!/usr/bin/env python3
"""Build the org chart pages from skills/org-chart/seats.yaml and the two registries.

Steps: load -> validate -> render -> write. A data error stops the build before
anything is written: the script prints one ERROR line per problem to stderr and
exits 1.

A run writes skills/org-chart/pages/ (both charts, style.css, one page per seat)
and the author's gap page. --check builds in memory, compares with what is on
disk, and writes nothing. The build writes no timestamps, so the same input
gives the same bytes.
"""
import argparse
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "scripts" / "org-chart-templates"
CHARTS = ("b2b", "b2c")
CHART_FILE = {"b2b": "index.html", "b2c": "b2c.html"}
CHART_LABEL = {"b2b": "B2B", "b2c": "B2C"}
CHART_TITLE = {"b2b": "B2B Org Chart", "b2c": "B2C Org Chart"}
HEADCOUNT = 100
COVERAGE_LEVELS = ("covered", "thin", "none")
COVERAGE_LABEL = {"covered": "Covered", "thin": "Thin", "none": "Nothing yet"}
DASH = re.compile(r"\s*[–—]\s*")
PAGE_SUFFIXES = (".html", ".css")


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


# ---------------------------------------------------------------- render


def text(value):
    """Registry or seats-file text, made safe for HTML. Dashes become ", "."""
    return html.escape(DASH.sub(", ", str(value).strip()), quote=True)


def sentence(value):
    """Like text(), with the first letter capitalized (registry purposes start lowercase)."""
    raw = DASH.sub(", ", str(value).strip())
    return html.escape(raw[:1].upper() + raw[1:], quote=True)


def fill(template, **values):
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    left = re.search(r"\{\{\w+\}\}", out)
    if left:
        raise ValueError(f"template placeholder {left.group(0)} was not filled")
    return out


def _template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def people_text(n):
    return "1 person" if n == 1 else f"{n} people"


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def reports_to(seat, chart):
    value = seat.get("reports_to")
    if isinstance(value, dict):
        return value.get(chart)
    return value


def on_chart(seat, chart):
    return chart in (seat.get("people") or {})


def seat_advisor_ids(seat, frameworks):
    """Advisors on a seat: framework advisors in order of first use, then also_ask."""
    out = []
    for fid in seat_frameworks(seat):
        aid = frameworks[fid]["advisor"]
        if aid not in out:
            out.append(aid)
    for aid in seat.get("also_ask") or []:
        if aid not in out:
            out.append(aid)
    return out


def chart_layout(data, chart):
    """Return (top seats, [(department, seats)]) for one chart, in seats-file order."""
    seats = [s for s in data["seats"] if on_chart(s, chart)]
    dotted = [s for s in seats if s.get("dotted")]
    heads = [s for s in seats if not s.get("dotted") and not reports_to(s, chart)]
    top = dotted + heads
    top_ids = {s["id"] for s in top}
    columns = []
    for dept in data["departments"]:
        col = [s for s in seats if s["dept"] == dept["id"] and s["id"] not in top_ids]
        if col:
            columns.append((dept, col))
    return top, columns


def chart_order(data, chart):
    top, columns = chart_layout(data, chart)
    return top + [s for _, col in columns for s in col]


def pill(level):
    return f'<span class="pill {level}">{COVERAGE_LABEL[level]}</span>'


def seat_card(seat, chart, top_ids):
    classes = ["seat", seat["coverage"]]
    if seat.get("dotted"):
        classes.append("dotted")
    boss = reports_to(seat, chart)
    attrs = f'href="seats/{seat["id"]}.html"'
    if boss and seat["id"] not in top_ids:
        attrs += f' data-reports-to="{text(boss)}"'
        classes.append("head" if boss in top_ids else "report")
    n = seat["people"][chart]
    count = f'<span class="seat-n">×{n}</span>' if n else ""
    jobs = len(seat.get("jobs") or [])
    return (
        f'<a {attrs} class="{" ".join(classes)}">'
        f'<span class="seat-row"><span class="seat-name">{text(seat["name"])}</span>{count}</span>'
        f'<span class="seat-row start">{pill(seat["coverage"])}'
        f'<span class="seat-counts">{plural(jobs, "job")}</span></span></a>'
    )


def render_chart(data, chart):
    top, columns = chart_layout(data, chart)
    top_ids = {s["id"] for s in top}
    indent = "        "

    top_parts = []
    dotted = [s for s in top if s.get("dotted")]
    heads = [s for s in top if not s.get("dotted")]
    for seat in dotted:
        top_parts.append(seat_card(seat, chart, top_ids))
    if dotted and heads:
        top_parts.append('<div class="v-line dotted"></div>')
    for seat in heads:
        top_parts.append(seat_card(seat, chart, top_ids))
    if columns:
        top_parts.append('<div class="v-line"></div>')

    col_parts = []
    for dept, seats in columns:
        total = sum(s["people"][chart] for s in seats)
        cards = "\n".join(indent + "  " + seat_card(s, chart, top_ids) for s in seats)
        col_parts.append(
            f'{indent}<section class="dept" id="dept-{text(dept["id"])}">\n'
            f'{indent}  <div class="dept-head"><h3>{text(dept["name"])}</h3>'
            f'<span class="seat-n">{people_text(total)}</span></div>\n'
            f"{cards}\n"
            f"{indent}</section>"
        )

    chart_seats = [s for s in data["seats"] if on_chart(s, chart)]
    frameworks, advisors = set(), set()
    for seat in chart_seats:
        frameworks |= set(seat_frameworks(seat))
        advisors |= set(seat_advisor_ids(seat, data["frameworks"]))

    current = ' aria-current="page"'
    switch = "".join(
        f'<a href="{CHART_FILE[c]}"{current if c == chart else ""}>{CHART_LABEL[c]}</a>'
        for c in CHARTS
    )
    return fill(
        _template("chart.html"),
        title=CHART_TITLE[chart],
        switch=switch,
        advisor_count=str(len(advisors)),
        framework_count=str(len(frameworks)),
        seat_count=str(len(chart_seats)),
        none_count=str(sum(1 for s in chart_seats if s["coverage"] == "none")),
        top="\n".join(indent + p for p in top_parts),
        columns="\n".join(col_parts),
    )


def command(kind, ident):
    return (
        f'<div class="cmd"><code>/aligned:use-{kind} {text(ident)}</code>'
        f'<button type="button" class="copy">Copy</button></div>'
    )


def framework_block(fid, data):
    fw = data["frameworks"][fid]
    advisor = data["advisors"][fw["advisor"]]
    return (
        f'<div class="who">{text(fw["name"])} <span class="by">· {text(advisor["name"])}</span></div>'
        f'<p class="why">{sentence(fw.get("purpose", ""))}</p>'
        f"{command('framework', fid)}"
    )


def seat_headcount(seat):
    charts = [c for c in CHARTS if on_chart(seat, c)]
    if all(seat["people"][c] == 0 for c in charts):
        return "<span>Not on the payroll</span>"
    if len(charts) == 1:
        return f"<span>{people_text(seat['people'][charts[0]])}</span>"
    return "".join(
        f"<span>{CHART_LABEL[c]}: {people_text(seat['people'][c])}</span>" for c in charts
    )


def pager(seat, data):
    charts = [c for c in CHARTS if on_chart(seat, c)]
    pairs = {}
    for chart in charts:
        order = chart_order(data, chart)
        i = next(n for n, s in enumerate(order) if s["id"] == seat["id"])
        prev = order[i - 1] if i > 0 else None
        nxt = order[i + 1] if i + 1 < len(order) else None
        pairs[chart] = (prev, nxt)

    def link(target, before, after):
        if not target:
            return "<span></span>"
        return f'<a href="{text(target["id"])}.html">{before}{text(target["name"])}{after}</a>'

    def ids(pair):
        return tuple(s["id"] if s else None for s in pair)

    same = len({ids(p) for p in pairs.values()}) == 1
    rows = []
    for chart in charts[:1] if same else charts:
        prev, nxt = pairs[chart]
        label = "" if same else f'<span class="label">{CHART_LABEL[chart]} chart</span>'
        back = link(prev, "← Previous: ", "")
        forward = link(nxt, "Next: ", " →")
        rows.append(f'    <div class="pager-row">{label}{back}{forward}</div>')
    return "\n".join(rows)


def render_seat(seat, data):
    charts = [c for c in CHARTS if on_chart(seat, c)]
    dept = next(d for d in data["departments"] if d["id"] == seat["dept"])
    crumbs = "".join(
        f'<a href="../{CHART_FILE[c]}">← {CHART_LABEL[c]} chart</a>' for c in charts
    )

    body = []
    jobs = seat.get("jobs") or []
    if jobs:
        items = []
        for job in jobs:
            other = ""
            also = job.get("also") or []
            if also:
                lis = "".join(f"<li>{framework_block(fid, data)}</li>" for fid in also)
                other = (
                    '<div class="other"><span class="label">Other ways to do this</span>'
                    f"<ul>{lis}</ul></div>"
                )
            items.append(
                f'      <li class="card"><h3>{text(job["do"])}</h3>'
                f'{framework_block(job["framework"], data)}{other}</li>'
            )
        body.append(
            '  <section>\n    <h2>Jobs</h2>\n    <ol class="jobs">\n'
            + "\n".join(items)
            + "\n    </ol>\n  </section>"
        )

    advisor_ids = seat_advisor_ids(seat, data["frameworks"])
    if advisor_ids:
        items = []
        for aid in advisor_ids:
            advisor = data["advisors"][aid]
            items.append(
                f'      <li class="card"><div class="who">{text(advisor["name"])}</div>'
                f'<p class="why">{sentence(advisor.get("summary", ""))}</p>'
                f"{command('advisor', aid)}</li>"
            )
        body.append(
            '  <section>\n    <h2>Ask an advisor</h2>\n    <ul class="advisors">\n'
            + "\n".join(items)
            + "\n    </ul>\n  </section>"
        )

    missing = (seat.get("missing") or "").strip()
    if missing:
        level = " none" if seat["coverage"] == "none" else ""
        body.append(
            f'  <section class="missing{level}">\n    <h2>Not covered yet</h2>\n'
            f"    <p>{text(missing)}</p>\n  </section>"
        )

    return fill(
        _template("seat.html"),
        title=text(seat["name"]),
        crumbs=crumbs,
        dept=text(dept["name"]),
        headcount=seat_headcount(seat),
        pill=pill(seat["coverage"]),
        does=text(seat.get("does", "")),
        body="\n".join(body),
        pager=pager(seat, data),
    )


def render_author_page(data):
    rank = {"none": 0, "thin": 1}
    sections = []
    for chart in CHARTS:
        gaps = [
            s for s in data["seats"]
            if on_chart(s, chart) and s["coverage"] in rank
        ]
        gaps.sort(key=lambda s: (rank[s["coverage"]], -s["people"][chart]))
        rows = "\n".join(
            f'        <tr><td>{text(s["name"])}</td><td class="num">{s["people"][chart]}</td>'
            f'<td>{pill(s["coverage"])}</td><td>{text(s.get("missing") or "")}</td></tr>'
            for s in gaps
        )
        sections.append(
            f"  <section>\n    <h2>{CHART_LABEL[chart]} gaps</h2>\n"
            f'    <div class="table-scroll"><table id="gaps-{chart}">\n'
            '      <thead><tr><th>Seat</th><th class="num">People</th><th>Status</th>'
            "<th>Missing</th></tr></thead>\n"
            f"      <tbody>\n{rows}\n      </tbody>\n    </table></div>\n  </section>"
        )

    holding = data["holding"] or {}
    rows = []
    for entry in holding.get("advisors") or []:
        name = data["advisors"][entry["id"]]["name"]
        rows.append((name, entry))
    for entry in holding.get("frameworks") or []:
        name = data["frameworks"][entry["id"]]["name"]
        rows.append((name, entry))
    holding_rows = "\n".join(
        f'        <tr><td>{text(name)}</td><td><code>{text(e["id"])}</code></td>'
        f'<td>{text(e.get("why") or "")}</td></tr>'
        for name, e in rows
    )
    return fill(
        _template("coverage.html"),
        css=_template("style.css"),
        gaps="\n".join(sections),
        holding=holding_rows,
    )


def build(data):
    """Return {path relative to the pages dir: file text} for every shipped file."""
    files = {"style.css": _template("style.css")}
    for chart in CHARTS:
        files[CHART_FILE[chart]] = render_chart(data, chart)
    for seat in data["seats"]:
        files[f"seats/{seat['id']}.html"] = render_seat(seat, data)
    return files


# ---------------------------------------------------------------- write and check


def _on_disk(out):
    """Every page file under out, as paths relative to out (posix strings)."""
    if not out.is_dir():
        return set()
    return {
        p.relative_to(out).as_posix()
        for p in out.rglob("*")
        if p.is_file() and p.suffix in PAGE_SUFFIXES
    }


def _shown(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def check(files, out):
    """Return one ERROR line per page that differs from the fresh build."""
    errors = []
    names = sorted(set(files) | _on_disk(out))
    for rel in names:
        path = out / rel
        fresh = files.get(rel)
        if fresh is None or not path.is_file() or path.read_bytes() != fresh.encode("utf-8"):
            errors.append(
                f"ERROR: stale page {_shown(path)}; run scripts/generate-org-chart.py"
            )
    return errors


def write(files, out, author_text, author_out):
    out.mkdir(parents=True, exist_ok=True)
    for rel in sorted(_on_disk(out) - set(files)):
        (out / rel).unlink()
    for rel, body in sorted(files.items()):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = body.encode("utf-8")
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
    author_out.parent.mkdir(parents=True, exist_ok=True)
    author_out.write_bytes(author_text.encode("utf-8"))


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
    files = build(data)
    out = Path(args.out)
    if args.check:
        stale = check(files, out)
        for line in stale:
            print(line, file=sys.stderr)
        return 1 if stale else 0
    write(files, out, render_author_page(data), Path(args.author_out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
