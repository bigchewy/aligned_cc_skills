from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_authoring_engine_selection_uses_merged_advisor_list():
    text = read("skills/brainstorming/modes/authoring.md")
    assert "resolve-advisor-source.md" in text, (
        "authoring engine selection must feed contextual-recommendation the merged advisor list"
    )
