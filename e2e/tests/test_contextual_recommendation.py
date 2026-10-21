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


def test_stage1_accepts_premerged_advisor_list():
    text = read("skills/_shared/contextual-recommendation.md")
    # Stage 1 must document a dual contract: registry path OR pre-merged advisor entries
    assert "pre-merged" in text.lower() or "premerged" in text.lower(), (
        "Stage 1 must accept a pre-merged advisor entry list (from resolve-advisor-source)"
    )
    assert "resolve-advisor-source" in text, (
        "dual-contract must name resolve-advisor-source as the source of the merged list"
    )


def test_stage1_documents_which_branch_each_entity_uses():
    text = read("skills/_shared/contextual-recommendation.md").lower()
    # framework callers pass a path; advisor callers pass the merged list
    assert "framework" in text and "path" in text
    assert "advisor" in text and ("list" in text or "entries" in text)


def test_configuration_documents_advisor_input_variants():
    text = read("skills/_shared/contextual-recommendation.md")
    # After the dual-contract change, ## Configuration must document both input branches by name.
    # The old single "Registry path:" bullet must be updated to cover advisor callers explicitly.
    assert "advisor callers" in text.lower(), (
        "## Configuration must document the advisor-callers input variant by name"
    )
    assert "framework callers" in text.lower(), (
        "## Configuration must document the framework-callers input variant by name"
    )


def test_stage1_accepts_premerged_framework_list():
    text = read("skills/_shared/contextual-recommendation.md")
    assert "resolve-framework-source" in text, (
        "Stage 1 must name resolve-framework-source as the source of the merged framework list"
    )


def test_configuration_framework_callers_pass_merged_list():
    text = read("skills/_shared/contextual-recommendation.md")
    config = text.split("## Configuration", 1)[1].split("## Path 4", 1)[0]
    assert "Input (framework callers)" in config
    assert "pre-merged framework list" in config


def test_stage1_no_longer_says_framework_callers_always_use_path():
    text = read("skills/_shared/contextual-recommendation.md")
    assert "Framework callers always use the path branch" not in text


def test_unregistered_frameworks_excluded_from_scoring():
    text = read("skills/_shared/contextual-recommendation.md")
    assert "registered: false" in text
    assert "reachable by name only" in text


def test_path4_list_all_reply_is_not_scored_as_task_context():
    text = read("skills/_shared/contextual-recommendation.md")
    path4 = text.split("## Path 4", 1)[1].split("## Stage 1", 1)[0]
    assert '"list all"' in path4
    assert "not scored as task context" in path4
    assert "calling skill's full listing" in path4
