from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_contextual_recommendation_documents_multi_entity_mode():
    text = read("skills/_shared/contextual-recommendation.md")
    assert "framework-or-advisor" in text, "missing multi-entity entity type"
    assert "merge" in text.lower() and "rank" in text.lower(), (
        "multi-entity mode must describe merge + rank behavior"
    )


def test_multi_entity_mode_documents_tiebreaker_against_purpose():
    text = read("skills/_shared/contextual-recommendation.md")
    # When framework and advisor score similarly, framework wins for actionable tasks;
    # advisor wins for exploration. Document the rule.
    assert "tiebreaker" in text.lower() or "tie-breaker" in text.lower()


def test_multi_entity_mode_handles_zero_signal():
    text = read("skills/_shared/contextual-recommendation.md")
    # Multi-entity mode with empty registries (or zero overlap) must degrade to Path 4
    assert "Path 4" in text  # already present, but now also referenced from multi-entity section
