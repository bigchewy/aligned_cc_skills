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


def test_authoring_phase2a_passes_absolute_dir_and_entry():
    text = read("skills/brainstorming/modes/authoring.md")
    phase = text.split("### Phase 2a", 1)[1].split("### Phase 2b", 1)[0]
    assert "absolute_framework_dir" in phase
    assert "framework_entry" in phase
    assert "from Phase 1" not in phase.split("framework_entry")[0]


def test_authoring_deliverable_type_and_critics_read_merged_entry():
    text = read("skills/brainstorming/modes/authoring.md")
    assert "from the framework registry" not in text
    assert "registry's `default_critic_advisors`" not in text
    drift = text.split("**Registry drift fallback:**", 1)[1].split("\n", 1)[0]
    assert 'source: "plugin"' in drift
    assert 'source: "local"' in drift


def test_brainstorming_topic_tiebreaker_uses_merged_domains():
    text = read("skills/brainstorming/SKILL.md")
    assert "resolve-framework-source.md" in text
    assert "`domains:` entry in `frameworks/registry.yaml`" not in text


def test_critique_checklist_deliverable_type_from_merged_entry():
    text = read("skills/brainstorming/authoring-critique-checklist.md")
    para = text.split("## Conditional sections", 1)[1].split("\n\n", 2)[1]
    assert "merged" in para
    assert "`deliverable_type` field from `frameworks/registry.yaml`" not in text
