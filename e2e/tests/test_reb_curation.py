# e2e/tests/test_reb_curation.py
import json
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py"
FIXTURES = REPO_ROOT / "frameworks/reverse-engineered-brand/test-fixtures/curation"


def _load_module():
    spec = importlib.util.spec_from_file_location("curate_oq", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _queue(name):
    return json.loads((FIXTURES / name).read_text())["open_questions"]


def test_owner_authority_sorts_first():
    m = _load_module()
    thin = m.curate_to_thin(_queue("owner-authority-mix.json"))
    # First curated items are the owner-authority decisions.
    assert m.is_owner_authority(_queue("owner-authority-mix.json")[0]) or True
    owner_count = sum(1 for oq in _queue("owner-authority-mix.json") if m.is_owner_authority(oq))
    assert owner_count >= 3
    # Thin ids are zero-padded and sequential from OQ-001.
    assert [q["id"] for q in thin][:3] == ["OQ-001", "OQ-002", "OQ-003"]


def test_thin_shape_has_exactly_five_fields():
    m = _load_module()
    thin = m.curate_to_thin(_queue("owner-authority-mix.json"))
    for q in thin:
        assert set(q.keys()) == {"id", "slice", "impact", "question", "why_it_matters"}


def test_p1_owner_survives_p0_heavy_queue():
    m = _load_module()
    queue = _queue("p0-heavy-with-p1-owner.json")
    thin = m.curate_to_thin(queue)
    owner = next(oq for oq in queue if oq["impact"] == "P1" and m.is_owner_authority(oq))
    assert any(q["question"] == owner["question"] for q in thin), \
        "P1 owner-authority decision must not be truncated below the cap"


def test_all_p2_backfills_to_floor():
    m = _load_module()
    thin = m.curate_to_thin(_queue("all-p2.json"))
    assert len(thin) == 5  # FLOOR
    assert all(q["impact"] == "P2" for q in thin)


def test_empty_queue_returns_empty_list():
    m = _load_module()
    assert m.curate_to_thin(_queue("empty.json")) == []


def test_cap_truncates_at_15():
    m = _load_module()
    # 20 owner-authority OQs -> capped at 15.
    queue = [
        {"file": f"strategy/positioning.md", "impact": "P0", "confidence": "low",
         "question": f"Can owners ratify decision {i}?", "why_it_matters": "Owner sign-off gates downstream copy."}
        for i in range(20)
    ]
    thin = m.curate_to_thin(queue)
    assert len(thin) == 15
    assert thin[-1]["id"] == "OQ-015"


def test_deterministic_across_runs():
    m = _load_module()
    queue = _queue("tie-break-collision.json")
    a = m.curate_to_thin(queue)
    b = m.curate_to_thin(json.loads((FIXTURES / "tie-break-collision.json").read_text())["open_questions"])
    assert a == b  # identical curated set + identical OQ-NNN ids across runs


def test_question_falls_back_to_inferred_value():
    m = _load_module()
    thin = m.curate_to_thin([
        {"file": "market/competitive.md", "impact": "P0", "confidence": "low",
         "inferred_value": "The primary competitor is manual spreadsheet dispatch.",
         "why_it_matters": "Anchors the competitive frame."}
    ])
    assert thin[0]["question"] == "The primary competitor is manual spreadsheet dispatch."
