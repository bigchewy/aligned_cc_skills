"""Guard the markdown READMEs against the staleness that motivated their regeneration:
headline counts must match the registries, and no migrated/phantom advisor id may appear."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

GONE_IDS = [
    # removed on 2026-11-02 (frameworks with no flow)
    "personal-context-intake", "professional-context-intake", "the-story-so-far", "idiot-index",
    # removed on 2026-11-02: his only framework, landing-page-assembly, was cut
    "oli-gardner",
    # moved to the moments repo on 2026-11-02
    "james-gurney", "stage-the-picture",
    "benjamin-levine", "copywriter",
    "andreo-spina", "blair-grubb", "italo-biaggioni", "kelly-starrett",
    "patrick-mckeown", "roy-freeman", "shirley-sahrmann", "stuart-mcgill",
    "deb-dana", "irene-lyon", "akiko-iwasaki", "david-putrino", "david-systrom",
    "byron-katie", "gabor-mate", "marsha-linehan", "martin-seligman",
    "richard-schwartz", "steven-hayes", "wise-eric",
    # moved to client repos
    "jonathan-baker", "robb-wolf", "kate-bowler", "danny-iny",
    "sellability-index", "permission-blessing", "audience-first-business-model",
    "integrative-piloting-process", "leveraged-learning", "pilot-program-methodology",
    # deleted: Joan Garry and eight solo-creator advisors, with their frameworks
    "joan-garry", "elise-darma", "jasmine-star", "sue-b-zimmerman", "rachel-pedersen",
    "jenna-kutcher", "arielle-nissenblatt", "jeremy-enns", "jay-clouse",
    "batched-content-system", "bio-promise-alignment", "cec-method",
    "community-amplification", "creator-experimentation-protocol", "creator-flywheel",
    "depth-over-breadth-strategy", "dm-relationship-cultivation",
    "earbuds-recommendation-model", "ears-framework", "engagement-pyramid",
    "first-seven-reels", "four-neighborhoods", "jk5-content-pillars",
    "message-magic-system", "one-one-one-one-method", "podcast-brand-strategy",
    "podcast-marketing-systems", "problem-solver-positioning",
    "recommendation-readiness-checklist", "social-media-queen-method",
    "thirty-minute-daily-instagram", "three-by-three-content-batching",
    "big-bat-board-assessment", "organizational-readiness",
    # removed or moved to ~/Documents/aligned on 2026-11-02 (framework overlap cleanup)
    "lara-hogan", "shirin-oreizy", "chris-voss",
    "5-step-process", "positioning-canvas", "start-with-experience",
    "leadership-pipeline-passages", "management-level-progression",
    "landing-page-assembly", "past-year-review",
    "science-of-design", "homer-vs-spock", "cognitive-friction-audit",
    "accusation-audit", "calibrated-questions", "tactical-empathy-labeling",
    # retired archetype, replaced by brad-frost
    "the-designer",
    # retired archetype, replaced by jason-fried
    "the-pm",
    # retired archetype, replaced by aleyda-solis
    "seo-expert",
    # retired archetype, replaced by michael-bolton
    "the-qa-engineer",
    # retired archetype, replaced by adam-shostack
    "the-security-reviewer",
    # retired archetype, removed with no replacement (its CI and SDK hand-off went to the-architect)
    "the-devex-engineer",
    # phantom framework IDs — benjamin-levine's 4 frameworks (folders already absent, still in README)
    "autonomic-fatigue-vs-training-fatigue", "cardiac-deconditioning-model",
    "heart-rate-reserve-training-zones", "levine-protocol",
]


def _count(rel, key):
    with open(REPO / rel) as f:
        return len(yaml.safe_load(f)[key])


def test_advisor_readme_headline_count_matches_registry():
    n = _count("advisors/registry.yaml", "advisors")
    text = (REPO / "advisors" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"advisors/README.md headline must show {n} advisors"


def test_framework_readme_headline_count_matches_registry():
    n = _count("frameworks/registry.yaml", "frameworks")
    text = (REPO / "frameworks" / "README.md").read_text()
    assert str(n) in text.splitlines()[2], f"frameworks/README.md headline must show {n} frameworks"


def _layers():
    with open(REPO / "skills" / "playbook" / "layers.yaml") as f:
        return yaml.safe_load(f)


def _readme_sections(text):
    """Map (layer name, area name) -> (count in header, ids in the table rows); 'held' -> same for Held."""
    import re

    ids = set()
    with open(REPO / "frameworks" / "registry.yaml") as f:
        ids = {e["id"] for e in yaml.safe_load(f)["frameworks"]}
    result = {}
    layer = area = None
    for line in text.splitlines():
        m = re.match(r"^### (.+?)(?: \((\d+)\))?$", line)
        if m:
            layer, area = m.group(1), None
            if layer == "Held":
                area = "held"
                result[("held",)] = (int(m.group(2)), [])
            continue
        m = re.match(r"^#### (.+) \((\d+)\)$", line)
        if m and layer:
            area = m.group(1)
            result[(layer, area)] = (int(m.group(2)), [])
            continue
        if line.startswith("---"):
            layer = area = None
            continue
        m = re.match(r"^\| ([a-z0-9-]+) \|", line)
        if m and area and m.group(1) in ids:
            key = ("held",) if area == "held" else (layer, area)
            result[key][1].append(m.group(1))
    return result


def test_framework_readme_headline_counts_layers_and_areas():
    data = _layers()
    n_areas = sum(len(layer["areas"]) for layer in data["layers"])
    text = (REPO / "frameworks" / "README.md").read_text()
    headline = text.splitlines()[2]
    assert f"across {len(data['layers'])} layers and {n_areas} areas" in headline
    assert "| Category |" not in text and "## By Category" not in text, "README must not group by category"


def test_framework_readme_groups_by_layer_and_area_in_layers_yaml_order():
    data = _layers()
    text = (REPO / "frameworks" / "README.md").read_text()
    sections = _readme_sections(text)
    expected = {}
    for layer in data["layers"]:
        for area in layer["areas"]:
            expected[(layer["name"], area["name"])] = (len(area["frameworks"]), list(area["frameworks"]))
    got = {k: v for k, v in sections.items() if k != ("held",)}
    assert got == expected, "frameworks/README.md layer and area tables must match layers.yaml, in order"
    order = [k for k in sections if k != ("held",)]
    assert order == list(expected), "areas must appear in layers.yaml order"


def test_framework_readme_lists_every_placed_framework():
    data = _layers()
    text = (REPO / "frameworks" / "README.md").read_text()
    with open(REPO / "frameworks" / "registry.yaml") as f:
        all_ids = {e["id"] for e in yaml.safe_load(f)["frameworks"]}
    placed = {i for layer in data["layers"] for a in layer["areas"] for i in a["frameworks"]}
    held = {h["id"] for h in data["holding"]}
    sections = _readme_sections(text)
    listed = {i for ids in (v[1] for k, v in sections.items() if k != ("held",)) for i in ids}
    assert listed == placed
    assert placed | held == all_ids


def test_framework_readme_held_section_lists_the_holding_list():
    data = _layers()
    text = (REPO / "frameworks" / "README.md").read_text()
    sections = _readme_sections(text)
    count, ids = sections[("held",)]
    assert ids == [h["id"] for h in data["holding"]]
    assert count == len(ids)


def test_readmes_drop_migrated_and_phantom_ids():
    adv = (REPO / "advisors" / "README.md").read_text()
    fw = (REPO / "frameworks" / "README.md").read_text()
    for gid in GONE_IDS:
        assert gid not in adv, f"advisors/README.md still references migrated/phantom id: {gid}"
        assert gid not in fw, f"frameworks/README.md still references migrated/phantom id: {gid}"
