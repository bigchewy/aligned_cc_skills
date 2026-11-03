"""Guard the markdown READMEs against the staleness that motivated their regeneration:
headline counts must match the registries, and no migrated/phantom advisor id may appear."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

GONE_IDS = [
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


def _registry_category_counts():
    from collections import Counter

    with open(REPO / "frameworks" / "registry.yaml") as f:
        entries = yaml.safe_load(f)["frameworks"]
    return Counter(e["category"] for e in entries)


def test_framework_readme_category_table_matches_registry():
    import re

    counts = _registry_category_counts()
    text = (REPO / "frameworks" / "README.md").read_text()
    table = dict(
        (m.group(1), int(m.group(2)))
        for m in re.finditer(r"^\| ([a-z-]+) \| (\d+) \|$", text, re.M)
    )
    assert table == dict(counts), "frameworks/README.md category table must match registry categories"
    assert f"across {len(counts)} categories" in text.splitlines()[2]


def test_framework_readme_category_sections_match_registry():
    import re

    counts = _registry_category_counts()
    text = (REPO / "frameworks" / "README.md").read_text()
    sections = {
        m.group(1).lower().replace(" ", "-"): int(m.group(2))
        for m in re.finditer(r"^### ([A-Za-z ]+) \((\d+)\)$", text, re.M)
    }
    assert sections == dict(counts), "frameworks/README.md section headers must match registry categories"
    assert _bullets_per_section(text) == dict(counts), "frameworks/README.md section lists must hold the registry's frameworks"


def _bullets_per_section(text):
    """Count '- **id**' bullets under each '### Title (n)' header."""
    import re

    result = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^### ([A-Za-z ]+) \((\d+)\)$", line)
        if m:
            current = m.group(1).lower().replace(" ", "-")
            result[current] = 0
        elif current and line.startswith("- **"):
            result[current] += 1
        elif line.startswith("---"):
            current = None
    return result


def test_readmes_drop_migrated_and_phantom_ids():
    adv = (REPO / "advisors" / "README.md").read_text()
    fw = (REPO / "frameworks" / "README.md").read_text()
    for gid in GONE_IDS:
        assert gid not in adv, f"advisors/README.md still references migrated/phantom id: {gid}"
        assert gid not in fw, f"frameworks/README.md still references migrated/phantom id: {gid}"
