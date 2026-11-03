"""Playbook map file: skills/playbook/layers.yaml checked against the framework registry."""
import copy
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-playbook.py"
LAYERS = ROOT / "skills" / "playbook" / "layers.yaml"
FRAMEWORKS = ROOT / "frameworks" / "registry.yaml"

_spec = importlib.util.spec_from_file_location("generate_playbook", SCRIPT)
gp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gp)


def fake_registry(*ids):
    return {"frameworks": [{"id": i, "name": i} for i in ids]}


def fake_layers():
    return {
        "layers": [
            {
                "id": "i",
                "name": "I",
                "does": "Work on yourself.",
                "areas": [
                    {"id": "a1", "name": "A1", "note": "n", "start": "f1", "frameworks": ["f1", "f2"]},
                    {"id": "a2", "name": "A2", "note": "n", "start": "f3", "frameworks": ["f3"]},
                ],
            }
        ],
        "holding": [{"id": "f4", "why": "elsewhere"}],
    }


def write(tmp_path, layers, registry):
    lp = tmp_path / "layers.yaml"
    fp = tmp_path / "registry.yaml"
    lp.write_text(yaml.safe_dump(layers, sort_keys=False))
    fp.write_text(yaml.safe_dump(registry, sort_keys=False))
    return lp, fp


REG = fake_registry("f1", "f2", "f3", "f4")


def test_fake_file_is_valid(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), REG)
    data, errors = gp.load_and_validate(lp, fp)
    assert errors == []
    assert set(data) >= {"layers", "frameworks", "homes"}
    assert data["homes"]["f1"] == [("i", "a1")]
    assert set(data["frameworks"]) == {"f1", "f2", "f3", "f4"}


def test_homes_list_every_area_a_framework_sits_in(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][1]["frameworks"].append("f1")
    lp, fp = write(tmp_path, layers, REG)
    data, errors = gp.load_and_validate(lp, fp)
    assert errors == []
    assert data["homes"]["f1"] == [("i", "a1"), ("i", "a2")]


def test_unplaced_framework_errors(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), fake_registry("f1", "f2", "f3", "f4", "f5"))
    _, errors = gp.load_and_validate(lp, fp)
    assert "ERROR: unplaced framework 'f5'" in errors


def test_unknown_framework_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["frameworks"].append("ghost")
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'ghost'" in e for e in errors)


def test_unknown_held_framework_errors(tmp_path):
    layers = fake_layers()
    layers["holding"].append({"id": "ghost", "why": "x"})
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'ghost'" in e for e in errors)


def test_placed_and_held_errors(tmp_path):
    layers = fake_layers()
    layers["holding"].append({"id": "f1", "why": "x"})
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'f1'" in e and "holding" in e for e in errors)


def test_duplicate_area_id_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][1]["id"] = "a1"
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "'a1'" in e for e in errors)


def test_missing_start_errors(tmp_path):
    layers = fake_layers()
    del layers["layers"][0]["areas"][0]["start"]
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "start" in e and "'a1'" in e for e in errors)


def test_start_not_in_area_errors(tmp_path):
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["start"] = "f3"
    lp, fp = write(tmp_path, layers, REG)
    _, errors = gp.load_and_validate(lp, fp)
    assert any(e.startswith("ERROR:") and "start" in e and "'a1'" in e for e in errors)


def test_check_layers_does_not_mutate_input():
    layers = fake_layers()
    before = copy.deepcopy(layers)
    assert gp.check_layers(layers, REG) == []
    assert layers == before


def test_check_layers_rejects_duplicate_framework_in_one_area():
    layers = fake_layers()
    layers["layers"][0]["areas"][0]["frameworks"].append("f1")
    errors = gp.check_layers(layers, REG)
    assert any(e.startswith("ERROR:") and "'f1'" in e for e in errors)


def test_real_file_passes_with_5_5_10_areas():
    data, errors = gp.load_and_validate(LAYERS, FRAMEWORKS)
    assert errors == []
    counts = {layer["id"]: len(layer["areas"]) for layer in data["layers"]["layers"]}
    assert counts == {"i": 5, "we": 5, "it": 10}


def test_real_file_places_or_holds_every_registry_id():
    data, errors = gp.load_and_validate(LAYERS, FRAMEWORKS)
    assert errors == []
    held = {h["id"] for h in data["layers"]["holding"]}
    assert held == {"close-the-loop"}
    for fid in data["frameworks"]:
        assert fid in data["homes"] or fid in held


# --- Document links: each required/helpful document names the framework that writes it ---

LINK_FIXTURE = ROOT / "e2e" / "tests" / "fixtures" / "playbook" / "registry.yaml"


def link_fixture():
    return yaml.safe_load(LINK_FIXTURE.read_text())


def fixture_entry(fid):
    return next(f for f in link_fixture()["frameworks"] if f["id"] == fid)


def errors_about(errors, fid):
    return [e for e in errors if f"'{fid}'" in e]


def test_doc_links_reads_plain_string_as_outside():
    links = gp.doc_links(fixture_entry("plain"))
    assert links == [{"doc": "a plain string doc", "from": ["outside"], "kind": "helpful"}]


def test_doc_links_turns_single_id_into_list_and_keeps_order():
    links = gp.doc_links(fixture_entry("branch"))
    assert links == [
        {"doc": "doc x", "from": ["writer-a"], "kind": "required"},
        {"doc": "doc y", "from": ["writer-b"], "kind": "helpful"},
        {"doc": "doc z", "from": ["writer-a", "writer-b"], "kind": "helpful"},
    ]


def test_doc_links_on_framework_with_no_documents_is_empty():
    assert gp.doc_links(fixture_entry("writer-a")) == []


def test_good_fixture_cases_raise_no_errors():
    errors = gp.check_links(link_fixture())
    for fid in ("branch", "help-1", "help-2", "plain", "writer-a", "writer-b", "b2b-writer", "any-reader"):
        # Errors about a framework start with its id; a loop error names it after "needs".
        about = [e for e in errors if e.startswith(f"ERROR: '{fid}'") or ("needs" in e and f"'{fid}'" in e)]
        assert about == [], fid


def test_unknown_from_names_framework_doc_and_bad_id():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "'ghost'" in e]
    assert len(hits) == 1
    assert hits[0].startswith("ERROR:")
    assert "'unknown-from'" in hits[0] and "'list doc'" in hits[0]


def test_self_link_names_framework_doc_and_value():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "'self doc'" in e]
    assert len(hits) == 1
    assert hits[0].startswith("ERROR:") and "'self-link'" in hits[0] and "itself" in hits[0]


def test_required_loop_is_an_error_and_names_each_link():
    errors = gp.check_links(link_fixture())
    hits = [e for e in errors if "loop" in e and "'loop-1'" in e]
    assert len(hits) == 1
    msg = hits[0]
    assert msg.startswith("ERROR:")
    assert "'loop-2'" in msg and "'loop doc 1'" in msg and "'loop doc 2'" in msg


def test_helpful_loop_is_not_an_error():
    errors = gp.check_links(link_fixture())
    assert not any("'help-1'" in e or "'help-2'" in e for e in errors)


def test_b2c_writer_feeding_only_b2b_is_an_error():
    errors = gp.check_links(link_fixture())
    hits = errors_about(errors, "b2c-writer")
    assert len(hits) == 1
    msg = hits[0]
    assert msg.startswith("ERROR:") and "b2c" in msg and "'b2c doc'" in msg and "'b2b-reader'" in msg


def test_outside_inside_a_from_list_is_an_error():
    errors = gp.check_links(link_fixture())
    hits = errors_about(errors, "mixed-outside")
    assert len(hits) == 1
    msg = hits[0]
    assert msg.startswith("ERROR:") and "'mixed doc'" in msg and "'outside'" in msg


def test_doc_links_skips_outside_inside_a_list():
    assert gp.doc_links(fixture_entry("mixed-outside")) == []


def test_fixture_has_exactly_the_five_planted_errors():
    assert len(gp.check_links(link_fixture())) == 5


def test_entry_that_is_neither_string_nor_mapping_errors():
    reg = {"frameworks": [{"id": "x", "helpful_documents": [{"doc": "d"}]}]}
    errors = gp.check_links(reg)
    assert len(errors) == 1 and errors[0].startswith("ERROR:") and "'x'" in errors[0]


def test_outside_required_lists_required_outside_docs_only():
    reg = {"frameworks": [
        {"id": "a", "required_documents": ["plain need", {"doc": "own", "from": "outside"},
                                           {"doc": "linked", "from": "b"}],
         "helpful_documents": [{"doc": "nice", "from": "outside"}]},
        {"id": "b"},
    ]}
    assert gp.outside_required(reg) == [("a", "plain need"), ("a", "own")]


def test_load_and_validate_includes_link_errors(tmp_path):
    lp, fp = write(tmp_path, fake_layers(), link_fixture())
    _, errors = gp.load_and_validate(lp, fp)
    assert any("'ghost'" in e for e in errors)


def real_registry():
    return yaml.safe_load(FRAMEWORKS.read_text())


def test_real_registry_links_pass():
    assert gp.check_links(real_registry()) == []


def test_real_registry_entries_are_all_doc_from_mappings():
    for f in real_registry()["frameworks"]:
        for key in ("required_documents", "helpful_documents"):
            for entry in f.get(key) or []:
                assert isinstance(entry, dict), f"{f['id']} {key}: {entry!r}"
                assert set(entry) == {"doc", "from"}, f"{f['id']} {key}: {entry!r}"
                assert isinstance(entry["doc"], str) and entry["doc"]


def test_real_registry_single_writer_is_plain_id_not_one_item_list():
    for f in real_registry()["frameworks"]:
        for key in ("required_documents", "helpful_documents"):
            for entry in f.get(key) or []:
                if isinstance(entry["from"], list):
                    assert len(entry["from"]) > 1, f"{f['id']}: {entry!r}"


def test_check_ins_take_quarterly_goals_from_proximate_objectives():
    by_id = {f["id"]: f for f in real_registry()["frameworks"]}
    for fid, doc in (("mochary-weekly-check-in", "OKRs or quarterly goals (if set)"),
                     ("chj-operating-review", "OKRs or quarterly priorities (if set)")):
        links = {l["doc"]: l for l in gp.doc_links(by_id[fid])}
        assert links[doc]["from"] == ["proximate-objectives"]


# --- Task 5: the pages, the report, the skill and the hook ---

import re
import subprocess
import sys

FIX = ROOT / "e2e" / "tests" / "fixtures" / "playbook"
PAGES_LAYERS = FIX / "pages-layers.yaml"
PAGES_REGISTRY = FIX / "pages-registry.yaml"
PAGES_ADVISORS = FIX / "pages-advisors.yaml"
CLOSING = "Put the result into your Top Goal or your next check-in."
SKILL_MD = ROOT / "skills" / "playbook" / "SKILL.md"
HOOK = ROOT / "scripts" / "hooks" / "pre-commit"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True, text=True, cwd=ROOT,
    )


def pages_data():
    data, errors = gp.load_and_validate(PAGES_LAYERS, PAGES_REGISTRY, PAGES_ADVISORS)
    assert errors == []
    return data


def pages():
    return gp.build(pages_data())


def items(index_html):
    """Every map item as (opening <li> tag, inner html)."""
    return re.findall(r'(<li class="item[^"]*"[^>]*>)(.*?)</li>', index_html, re.S)


def visible_text(page):
    body = page.split("<body>")[1].split("<script>")[0]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def test_unknown_advisor_is_an_error(tmp_path):
    reg = yaml.safe_load(PAGES_REGISTRY.read_text())
    reg["frameworks"][0]["advisor"] = "nobody"
    fp = tmp_path / "registry.yaml"
    fp.write_text(yaml.safe_dump(reg, sort_keys=False))
    _, errors = gp.load_and_validate(PAGES_LAYERS, fp, PAGES_ADVISORS)
    assert any("'nobody'" in e and "'solo'" in e for e in errors)


def test_helpful_loop_graph_ends_with_each_edge_once():
    edges = gp.upstream_edges("help-1", pages_data())
    assert sorted(edges) == [("help-1", "help-2", "helpful"), ("help-2", "help-1", "helpful")]


def test_we_framework_has_no_edges():
    assert gp.upstream_edges("we-reader", pages_data()) == []
    assert gp.upstream_edges("twice", pages_data()) == []


def test_it_framework_fed_by_we_writer_stops_at_the_writer():
    assert gp.upstream_edges("it-fed", pages_data()) == [("we-writer", "it-fed", "helpful")]


def test_it_chain_walks_writers_in_it_and_never_outside():
    edges = gp.upstream_edges("it-reader", pages_data())
    assert sorted(edges) == sorted([
        ("it-mid", "it-reader", "required"),
        ("we-writer", "it-reader", "helpful"),
        ("help-1", "it-mid", "helpful"),
        ("help-2", "help-1", "helpful"),
        ("help-1", "help-2", "helpful"),
    ])
    assert all("outside" not in (w, r) for w, r, _ in edges)
    assert len(edges) == len(set(edges))


def test_build_makes_index_style_and_a_page_per_placed_framework():
    files = pages()
    placed = set(pages_data()["homes"])
    assert {"index.html", "style.css"} <= set(files)
    assert {f"frameworks/{f}.html" for f in placed} == {k for k in files if k.startswith("frameworks/")}
    assert "frameworks/held.html" not in files


def test_index_columns_and_filters_in_order():
    index = pages()["index.html"]
    assert index.index('data-filter="stage"') < index.index('data-filter="market"')
    for stage in ("idea", "pilot", "nail-it", "scale-it", "milk-it"):
        assert f'value="{stage}"' in index
    assert index.index(">I<") < index.index(">We<") < index.index(">It<")
    assert "<script src" not in index


def test_two_area_framework_appears_in_both_boxes_and_page_names_both():
    files = pages()
    links = re.findall(r'href="frameworks/twice.html"', files["index.html"])
    assert len(links) == 2
    page = visible_text(files["frameworks/twice.html"])
    assert "I · Self" in page and "We · Team" in page


def test_every_area_start_item_carries_data_start_and_comes_first():
    index = pages()["index.html"]
    data = pages_data()
    boxes = re.findall(r'<section class="area" id="area-([^"]+)"', index)
    assert len(boxes) == 4
    for layer in data["layers"]["layers"]:
        for area in layer["areas"]:
            box = index.split(f'id="area-{area["id"]}"')[1].split("</section>")[0]
            first = items(box)[0]
            assert "data-start" in first[0]
            assert f'frameworks/{area["start"]}.html' in first[1]
            assert "Start here" in first[1]
            assert sum("data-start" in tag for tag, _ in items(box)) == 1


def test_every_item_carries_stages_and_market():
    found = items(pages()["index.html"])
    assert len(found) == 10
    for tag, _ in found:
        assert "data-stages=" in tag and "data-market=" in tag
    tags = {re.search(r'frameworks/([\w-]+)\.html', inner).group(1): tag for tag, inner in found}
    assert 'data-stages="idea pilot"' in tags["twice"]
    assert 'data-stages=""' in tags["solo"]
    assert 'data-market="b2b"' in tags["it-fed"]
    assert 'data-market=""' in tags["solo"]


def test_it_pages_end_with_the_closing_line_and_others_do_not():
    files = pages()
    for fid in ("it-reader", "it-mid", "it-fed", "help-1", "help-2"):
        assert visible_text(files[f"frameworks/{fid}.html"]).endswith(CLOSING), fid
    for fid in ("solo", "twice", "we-writer", "we-reader"):
        assert CLOSING not in files[f"frameworks/{fid}.html"], fid


def test_framework_page_lists_documents_writers_and_command():
    page = pages()["frameworks/it-reader.html"]
    text = visible_text(page)
    assert "/aligned:use-framework it-reader" in text
    assert "Advisor B" in text
    must = text.split("Must have")[1].split("Helps to have")[0]
    assert "mid doc" in must and "It Mid" in must
    assert "bank statements" in must and "from outside" in must
    helps = text.split("Helps to have")[1]
    assert "team doc" in helps and "We Writer" in helps
    assert 'href="it-mid.html"' in page and 'href="we-writer.html"' in page


def test_graph_draws_solid_required_dashed_helpful_and_links_boxes():
    page = pages()["frameworks/it-reader.html"]
    assert "What comes before it" in page
    svg = page.split("<svg")[1].split("</svg>")[0]
    assert "currentColor" in svg and "<marker" in svg
    lines = re.findall(r'<path class="edge (required|helpful)"[^>]*>', svg)
    assert sorted(lines) == sorted(["required", "helpful", "helpful", "helpful", "helpful"])
    for tag in re.findall(r'<path class="edge helpful"[^>]*>', svg):
        assert "stroke-dasharray" in tag
    for tag in re.findall(r'<path class="edge required"[^>]*>', svg):
        assert "stroke-dasharray" not in tag
    for fid in ("it-mid", "we-writer", "help-1", "help-2"):
        assert f'href="{fid}.html"' in svg
    assert "bank statements" not in svg


def test_every_graph_box_has_a_title_with_the_full_name():
    data = pages_data()
    long = "A Very Long Framework Name That Will Not Fit In Two Short Lines"
    data["frameworks"]["help-2"]["name"] = long
    svg = gp.build(data)["frameworks/it-reader.html"].split("<svg")[1].split("</svg>")[0]
    assert "…" in svg
    assert f"<title>{long}</title>" in svg
    boxes = re.findall(r"<rect class=\"node", svg)
    assert len(re.findall(r"<title>[^<]+</title>", svg)) == len(boxes) == 5


def test_no_graph_without_upstream_edges():
    files = pages()
    for fid in ("solo", "we-writer", "we-reader"):
        assert "<svg" not in files[f"frameworks/{fid}.html"]
        assert "What comes before it" not in files[f"frameworks/{fid}.html"]


def test_writers_on_held_frameworks_are_not_linked():
    data = pages_data()
    data["frameworks"]["it-fed"]["helpful_documents"].append({"doc": "held doc", "from": "held"})
    page = gp.build(data)["frameworks/it-fed.html"]
    assert "Held" in page and 'href="held.html"' not in page


def test_build_is_deterministic():
    assert pages() == pages()


def test_report_lists_two_area_frameworks_and_outside_required():
    text = gp.report(pages_data())
    two, outside = text.split("\n\n")[:2]
    assert "Twice" in two and "It Reader" not in two
    assert "It Reader" in outside and "bank statements" in outside


def test_report_on_real_repo_lists_the_two_area_frameworks():
    data, errors = gp.load_and_validate(LAYERS, FRAMEWORKS)
    assert errors == []
    two = gp.report(data).split("\n\n")[0]
    for fid in ("6-step-process", "type-1-type-2-decisions"):
        assert data["frameworks"][fid]["name"] in two


def test_cli_report_prints_report():
    result = run("--report")
    assert result.returncode == 0, result.stderr
    assert "6-Step Process" in result.stdout


def test_committed_pages_are_current():
    result = run("--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_flags_a_stale_page_and_write_fixes_it(tmp_path):
    out = tmp_path / "pages"
    args = ("--layers", PAGES_LAYERS, "--frameworks", PAGES_REGISTRY,
            "--advisors", PAGES_ADVISORS, "--out", out)
    assert run(*args).returncode == 0
    assert run("--check", *args).returncode == 0
    (out / "frameworks" / "solo.html").write_text("old", encoding="utf-8")
    (out / "frameworks" / "gone.html").write_text("old", encoding="utf-8")
    result = run("--check", *args)
    assert result.returncode == 1
    assert "ERROR: stale page" in result.stderr and "solo.html" in result.stderr
    assert "gone.html" in result.stderr
    assert "run scripts/generate-playbook.py" in result.stderr
    assert run(*args).returncode == 0
    assert not (out / "frameworks" / "gone.html").exists()
    assert run("--check", *args).returncode == 0


def test_cli_data_error_writes_nothing(tmp_path):
    out = tmp_path / "pages"
    result = run("--layers", PAGES_LAYERS, "--frameworks", LINK_FIXTURE, "--out", out)
    assert result.returncode == 1
    assert "ERROR:" in result.stderr
    assert not out.exists()


def test_skill_frontmatter():
    text = SKILL_MD.read_text()
    fm = yaml.safe_load(text.split("---")[1])
    assert fm["name"] == "playbook"
    assert fm["description"].startswith("Use when")
    assert "skills/_shared/resolve-skill-path.md" in text
    for cmd in ("open", "xdg-open", 'cmd /c start ""'):
        assert cmd in text
    assert "pages/index.html" in text
    assert "—" not in text and "–" not in text


def test_readme_lists_playbook():
    assert "/aligned:playbook" in (ROOT / "README.md").read_text()


def test_hook_rebuilds_playbook_on_its_inputs():
    text = HOOK.read_text()
    start = text.index("PLAYBOOK_INPUTS=")
    block = text[start : text.index("rebuild_playbook\n", start)]
    for path in ("frameworks/registry.yaml", "advisors/registry.yaml", "skills/playbook/layers.yaml",
                 "scripts/generate-playbook.py", "scripts/playbook-templates",
                 "scripts/org-chart-templates/style.css", "scripts/generate-org-chart.py"):
        assert path in block, path


def _fake_repo(tmp_path, generator_body):
    """A repo root whose venv python is the real one and whose generator is a stub."""
    fake_root = tmp_path / "repo"
    (fake_root / "e2e" / ".venv" / "bin").mkdir(parents=True)
    py = fake_root / "e2e" / ".venv" / "bin" / "python"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    py.chmod(0o755)
    (fake_root / "scripts").mkdir()
    (fake_root / "scripts" / "generate-playbook.py").write_text(generator_body)
    return fake_root


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                          env={"PATH": "/usr/bin:/bin", "HOME": str(cwd),
                               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


def _source_hook(fake_root, cwd):
    return subprocess.run(
        ["/bin/bash", "-c", f'source "{HOOK}"; rebuild_playbook; echo "after=$?"'],
        capture_output=True, text=True, cwd=cwd,
        env={"PATH": "/usr/bin:/bin", "REPO_ROOT": str(fake_root), "HOME": str(cwd)},
    )


def test_hook_rebuilds_and_stages_playbook_pages(tmp_path):
    stub = (
        "from pathlib import Path\n"
        "root = Path(__file__).resolve().parent.parent\n"
        "out = root / 'skills' / 'playbook' / 'pages'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "(out / 'index.html').write_text('built')\n"
    )
    fake_root = _fake_repo(tmp_path, stub)
    _git(fake_root, "init", "-q")
    result = _source_hook(fake_root, fake_root)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "after=0" in result.stdout
    assert "Playbook pages rebuilt" in out
    staged = _git(fake_root, "diff", "--cached", "--name-only").stdout
    assert "skills/playbook/pages/index.html" in staged


def test_hook_warns_and_returns_0_when_playbook_build_fails(tmp_path):
    stub = "import sys\nprint('ERROR: boom', file=sys.stderr)\nsys.exit(1)\n"
    fake_root = _fake_repo(tmp_path, stub)
    result = _source_hook(fake_root, tmp_path)
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert "after=0" in result.stdout
    assert "playbook build failed" in out and "ERROR: boom" in out


def test_hook_warns_when_no_python_for_playbook(tmp_path):
    empty_bin = tmp_path / "bin"
    empty_bin.mkdir()
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    result = subprocess.run(
        ["/bin/bash", "-c", f'source "{HOOK}"; rebuild_playbook'],
        capture_output=True, text=True,
        env={"PATH": str(empty_bin), "REPO_ROOT": str(fake_root)},
    )
    assert result.returncode == 0
    assert "playbook NOT rebuilt" in result.stdout + result.stderr
