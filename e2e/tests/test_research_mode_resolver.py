from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_research_mode_resolves_advisor_prompt_via_resolver():
    text = read("skills/brainstorming/modes/research.md")
    assert "resolve-advisor-source.md" in text, (
        "research-mode advisor dispatch must resolve prompt paths through the merged resolver, "
        "since migrating advisors leave the plugin"
    )


def test_research_mode_keeps_registry_authoritative_note():
    text = read("skills/brainstorming/modes/research.md")
    assert "registry.yaml` is authoritative" in text or "registry is authoritative" in text.lower()
