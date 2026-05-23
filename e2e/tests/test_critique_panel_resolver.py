from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_critique_panel_uses_resolver_for_advisor_list():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "resolve-advisor-source.md" in text, (
        "Round 1 must obtain the advisor list from the merged resolver"
    )


def test_critique_panel_takes_selection_guidelines_from_resolver_return():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "selection_guidelines" in text
    # the resolver return is the source for selection_guidelines now
    assert "return" in text.lower()


def test_critique_panel_resolves_prompt_via_absolute_path():
    text = read("skills/_shared/critique-panel-orchestration.md")
    assert "absolute_prompt_path" in text, (
        "critic prompt files must be resolved via the resolver's absolute_prompt_path, "
        "not the plugin-relative `prompt:` field"
    )
