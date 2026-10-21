from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_authoring_engine_selection_uses_merged_advisor_list():
    text = read("skills/brainstorming/modes/authoring.md")
    assert "resolve-advisor-source.md" in text, (
        "authoring engine selection must feed contextual-recommendation the merged advisor list"
    )


def test_authoring_frameworks_input_is_merged_list():
    text = read("skills/brainstorming/modes/authoring.md")
    assert "resolve-framework-source.md" in text
    assert "the registry path `frameworks/registry.yaml`" not in text


def test_authoring_critic_override_reads_merged_entry():
    text = read("skills/brainstorming/modes/authoring.md")
    line = next(l for l in text.splitlines() if "default_critic_advisors" in l and "Critic pool override" in l)
    assert "merged" in line
    assert "`frameworks/registry.yaml`" not in line


def test_brainstorming_topic_tiebreaker_uses_merged_domains():
    text = read("skills/brainstorming/SKILL.md")
    assert "resolve-framework-source.md" in text
    assert "`domains:` entry in `frameworks/registry.yaml`" not in text


def test_critique_checklist_deliverable_type_from_merged_entry():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    assert "merged" in text
    assert "`deliverable_type` field from `frameworks/registry.yaml`" not in text
