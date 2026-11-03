"""Advisors moved to client repos (and, later, deleted) leave nothing behind.

MOVED maps an advisor id to the repo that now holds it. DELETED lists advisors
removed outright. The shared tests below cover both.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
FW_REGISTRY = REPO_ROOT / "frameworks" / "registry.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

HOME = Path.home()
MOVED = {
    "jonathan-baker": HOME / "Documents" / "nextstep",
    "robb-wolf": HOME / "Documents" / "aligned",
    "kate-bowler": HOME / "Documents" / "aligned",
    "danny-iny": HOME / "software" / "planted",
    "james-gurney": HOME / "software" / "moments",
    "shirin-oreizy": HOME / "Documents" / "aligned",
    "chris-voss": HOME / "Documents" / "aligned",
}
DELETED = [
    "lara-hogan",
    "joan-garry",
    "elise-darma",
    "jasmine-star",
    "sue-b-zimmerman",
    "rachel-pedersen",
    "jenna-kutcher",
    "arielle-nissenblatt",
    "jeremy-enns",
    "jay-clouse",
]

DELETED_FRAMEWORKS = [
    "batched-content-system",
    "bio-promise-alignment",
    "cec-method",
    "community-amplification",
    "creator-experimentation-protocol",
    "creator-flywheel",
    "depth-over-breadth-strategy",
    "dm-relationship-cultivation",
    "earbuds-recommendation-model",
    "ears-framework",
    "engagement-pyramid",
    "first-seven-reels",
    "four-neighborhoods",
    "jk5-content-pillars",
    "message-magic-system",
    "one-one-one-one-method",
    "podcast-brand-strategy",
    "podcast-marketing-systems",
    "problem-solver-positioning",
    "recommendation-readiness-checklist",
    "social-media-queen-method",
    "thirty-minute-daily-instagram",
    "three-by-three-content-batching",
    "big-bat-board-assessment",
    "organizational-readiness",
    "5-step-process",
    "positioning-canvas",
    "start-with-experience",
    "leadership-pipeline-passages",
    "management-level-progression",
    "landing-page-assembly",
    "past-year-review",
]

MOVED_FRAMEWORKS = {
    "jonathan-baker": ["sellability-index"],
    "robb-wolf": [],
    "kate-bowler": ["permission-blessing"],
    "danny-iny": [
        "audience-first-business-model",
        "integrative-piloting-process",
        "leveraged-learning",
        "pilot-program-methodology",
    ],
    "james-gurney": ["stage-the-picture"],
    "shirin-oreizy": ["science-of-design", "homer-vs-spock", "cognitive-friction-audit"],
    "chris-voss": ["accusation-audit", "calibrated-questions", "tactical-empathy-labeling"],
}
ALL_MOVED_FRAMEWORKS = [f for fs in MOVED_FRAMEWORKS.values() for f in fs] + DELETED_FRAMEWORKS
REMOVED_ADVISORS = list(MOVED) + list(DELETED)

SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    TRIGGER_MAP,
]


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts:
                continue
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            yield p


def _advisors():
    return {a["id"]: a for a in yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["advisors"]}


def _frameworks():
    return {f["id"]: f for f in yaml.safe_load(FW_REGISTRY.read_text(encoding="utf-8"))["frameworks"]}


@pytest.mark.parametrize("advisor_id", REMOVED_ADVISORS)
def test_removed_advisors_gone_from_plugin(advisor_id):
    assert advisor_id not in _advisors()
    assert not (REPO_ROOT / "advisors" / "prompts" / f"{advisor_id}.md").exists()
    for fid, fw in _frameworks().items():
        assert fw["advisor"] != advisor_id, fid


@pytest.mark.parametrize("fid", ALL_MOVED_FRAMEWORKS)
def test_moved_frameworks_gone_from_plugin(fid):
    assert fid not in _frameworks()
    assert not (REPO_ROOT / "frameworks" / fid).exists()


def test_no_framework_points_at_a_removed_entry():
    advisors = _advisors()
    fws = _frameworks()
    for fid, fw in fws.items():
        for f in fw.get("follow_on_frameworks") or []:
            assert f in fws, f"{fid} follows on to missing framework {f}"
        for a in fw.get("default_critic_advisors") or []:
            assert a in advisors, f"{fid} names missing critic {a}"


def test_removed_ids_absent_from_shipped_files():
    ids = REMOVED_ADVISORS + ALL_MOVED_FRAMEWORKS
    pattern = re.compile(r"(?<![\w-])(" + "|".join(re.escape(i) for i in ids) + r")(?![\w-])")
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names removed ids:\n" + "\n".join(hits)


@pytest.mark.parametrize("advisor_id,target", sorted(MOVED.items()))
def test_moved_advisors_present_in_target(advisor_id, target):
    root = Path(target)
    if not root.exists():
        pytest.skip(f"{target} not present on this machine")
    reg = yaml.safe_load((root / "advisors" / "registry.yaml").read_text(encoding="utf-8"))
    assert advisor_id in {a["id"] for a in reg["advisors"]}
    assert (root / "advisors" / "prompts" / f"{advisor_id}.md").is_file()
    for fid in MOVED_FRAMEWORKS[advisor_id]:
        freg = yaml.safe_load((root / "frameworks" / "registry.yaml").read_text(encoding="utf-8"))
        entries = {f["id"]: f for f in freg["frameworks"]}
        assert fid in entries
        assert entries[fid]["advisor"] == advisor_id
        assert (root / "frameworks" / fid / "prompt.md").is_file()


@pytest.mark.parametrize("advisor_id", DELETED)
def test_deleted_advisors_gone(advisor_id):
    assert advisor_id not in _advisors()
    assert not (REPO_ROOT / "advisors" / "prompts" / f"{advisor_id}.md").exists()
    assert not any(fw["advisor"] == advisor_id for fw in _frameworks().values())


REMOVED_NAMES = [
    "Joan Garry",
    "Jonathan Baker",
    "Robb Wolf",
    "Kate Bowler",
    "Danny Iny",
    "Elise Darma",
    "Jasmine Star",
    "Sue B. Zimmerman",
    "Rachel Pedersen",
    "Jenna Kutcher",
    "Arielle Nissenblatt",
    "Jeremy Enns",
    "Jay Clouse",
    "James Gurney",
    "Wise Eric",
    "creator-economy",
    "Shirin Oreizy",
    "Chris Voss",
    "Lara Hogan",
]

NAME_SCANNED = [
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    TRIGGER_MAP,
]


def test_removed_names_absent_from_shipped_files():
    pattern = re.compile("|".join(re.escape(n) for n in REMOVED_NAMES), re.IGNORECASE)
    hits = []
    for root in NAME_SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts or not p.is_file():
                continue
            if p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names removed advisors:\n" + "\n".join(hits)
