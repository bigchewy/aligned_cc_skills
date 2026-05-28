"""Lock the v0.4.1 -> Marley review-model cutover. Static text assertions."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REB = REPO_ROOT / "frameworks/reverse-engineered-brand"


def _read(rel):
    return (REB / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("token", [
    "display_groups", "provided_summary", "source_narratives",
    "group-bullets", "voice-rewrite", "input_asks",
])
def test_removed_machinery_absent_from_prompt(token):
    assert token not in _read("prompt.md"), f"{token} must be gone from prompt.md"


def test_removed_subagent_files_deleted():
    assert not (REB / "group-bullets.md").exists()
    assert not (REB / "voice-rewrite.md").exists()


def test_new_contracts_present_in_prompt():
    text = _read("prompt.md")
    for needle in ("curate_open_questions.py", "review-data.json",
                   "orchestrator_inline", "claims-ledger"):
        assert needle in text, f"prompt.md must reference {needle}"


def test_renderer_invokes_python_and_drops_legacy_fields():
    text = _read("render-review-html.md")
    assert "render_review.py" in text
    for token in ("source_narratives", "display_groups"):
        assert token not in text


def test_scripts_exist():
    assert (REB / "scripts/curate_open_questions.py").is_file()
    assert (REB / "scripts/render_review.py").is_file()


def test_no_standalone_open_questions_json_authoring():
    # The single source of truth is review-data.json; the dotfile authoring is gone.
    assert ".open-questions.json" not in _read("prompt.md")


# R4 confidence derivation: modal per-slice enum, even-split → compound string.
# These are pure unit tests against helper logic; the derivation algorithm is
# authored inline in prompt.md Task 11 Step 2 — no Python module to import, so
# we test the contract via a documented helper function in curate_open_questions.py.
def test_r4_modal_confidence_returns_dominant_level():
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("curate_oq",
        REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py")
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
    # modal_confidence(["low", "low", "medium"]) → "low"
    assert _mod.modal_confidence(["low", "low", "medium"]) == "low"
    # modal_confidence(["high", "high", "high"]) → "high"
    assert _mod.modal_confidence(["high", "high", "high"]) == "high"


def test_r4_even_split_produces_compound_string():
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("curate_oq",
        REPO_ROOT / "frameworks/reverse-engineered-brand/scripts/curate_open_questions.py")
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
    # even split between two adjacent levels → compound "level1-level2" (lower first)
    assert _mod.modal_confidence(["medium", "high"]) == "medium-high"
    assert _mod.modal_confidence(["low", "medium"]) == "low-medium"
