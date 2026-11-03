"""Wise Eric is renamed Coach Eric, a CEO coach.

Six frameworks are voiced by this persona. Nothing shipped may still use the
old name or id.
"""

import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = REPO_ROOT / "advisors" / "registry.yaml"
FW_REGISTRY = REPO_ROOT / "frameworks" / "registry.yaml"
OUTLIERS = REPO_ROOT / "frameworks" / "_outliers.json"
PROMPT = REPO_ROOT / "advisors" / "prompts" / "coach-eric.md"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"

SUMMARY = (
    "CEO coach who pairs conscious leadership with systems thinking; "
    "finds the root cause, then the next step"
)

# The intakes and the-story-so-far were removed on 2026-11-02 (built for va-web-app).
SIX = [
    "6-step-process",
    "root-cause-analysis",
    "zone-of-genius",
]

SCANNED = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "advisors",
    REPO_ROOT / "frameworks",
    REPO_ROOT / "skills",
    REPO_ROOT / "agents",
    REPO_ROOT / "e2e" / "scenarios",
    TRIGGER_MAP,
]

OLD_NAME = re.compile(r"wise-eric|Wise Eric", re.IGNORECASE)


def _files():
    for root in SCANNED:
        paths = [root] if root.is_file() else root.rglob("*")
        for p in paths:
            if "node_modules" in p.parts:
                continue
            if not p.is_file() or p.suffix not in {".md", ".yaml", ".yml", ".html", ".json"}:
                continue
            yield p


def test_coach_eric_registered():
    advisors = {a["id"]: a for a in yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["advisors"]}
    assert "wise-eric" not in advisors
    entry = advisors["coach-eric"]
    assert entry["name"] == "Coach Eric"
    assert entry["summary"] == SUMMARY
    assert PROMPT.is_file()


def test_six_frameworks_point_at_coach_eric():
    fws = {x["id"]: x for x in yaml.safe_load(FW_REGISTRY.read_text(encoding="utf-8"))["frameworks"]}
    outliers = json.loads(OUTLIERS.read_text(encoding="utf-8"))
    flat = json.dumps(outliers)
    for fid in SIX:
        assert fws[fid]["advisor"] == "coach-eric", fid
    assert "wise-eric" not in flat
    assert "coach-eric" in flat


def test_no_wise_eric_in_shipped_files():
    hits = []
    for p in _files():
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if OLD_NAME.search(line):
                hits.append(f"{p.relative_to(REPO_ROOT)}:{n}: {line.strip()}")
    assert not hits, "Still names Wise Eric:\n" + "\n".join(hits)
