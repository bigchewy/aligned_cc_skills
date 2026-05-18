"""Parse-validate the v0.4.0 fixture against the v0.4.0 schema fields.

Schema reference: frameworks/reverse-engineered-brand/open-questions-schema.md
"""
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = (
    REPO_ROOT
    / "frameworks/reverse-engineered-brand/test-fixtures/oq-schema/valid-v040-minimal.json"
)

VALID_TIERS = {"critical", "recommended", "optional"}


def _load() -> dict:
    return json.loads(FIXTURE.read_text())


def test_schema_version_is_v040():
    assert _load()["schema_version"] == "0.4.0"


def test_each_folder_has_provided_summary_and_input_asks():
    data = _load()
    assert data["folders"], "fixture must include at least one folder"
    for folder in data["folders"]:
        assert isinstance(folder.get("provided_summary"), str) and folder["provided_summary"].strip(), (
            f"folder {folder.get('id')}: provided_summary must be a non-empty string"
        )
        asks = folder.get("input_asks")
        assert isinstance(asks, list) and asks, (
            f"folder {folder.get('id')}: input_asks must be a non-empty list"
        )
        for i, entry in enumerate(asks):
            assert entry.get("tier") in VALID_TIERS, (
                f"folder {folder.get('id')} input_asks[{i}].tier: invalid"
            )
            assert isinstance(entry.get("ask"), str) and entry["ask"].strip(), (
                f"folder {folder.get('id')} input_asks[{i}].ask: must be non-empty"
            )


def test_provided_summary_is_one_sentence_under_25_words():
    """Mirrors the v0.4.0 schema constraint: 1 sentence, ≤25 words."""
    for folder in _load()["folders"]:
        summary = folder["provided_summary"]
        words = summary.split()
        assert len(words) <= 25, (
            f"folder {folder['id']}: provided_summary is {len(words)} words (max 25)"
        )
