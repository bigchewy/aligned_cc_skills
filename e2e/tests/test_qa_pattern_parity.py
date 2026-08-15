from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_authoring_mode_carries_canonical_dispatch_template():
    """The Architect-as-proxy dispatch template was formerly duplicated between
    modes/software.md and modes/authoring.md with a parity test keeping them in
    sync. The 3-mode rescope retired software mode (routed to the superpowers
    plugin), making authoring.md the canonical — and only — home of the pattern."""
    au = read("skills/brainstorming/modes/authoring.md")
    # Stable anchor: the role-override sentence of the dispatch sub-agent prompt.
    anchor = "Your normal constraint of 'do not propose alternatives' is suspended"
    assert anchor in au, "authoring.md must carry the Architect-as-proxy dispatch anchor"
    assert "CANONICAL Q&A PATTERN" in au, (
        "authoring.md must mark the dispatch template as the canonical pattern"
    )
    assert "modes/software.md" not in au, (
        "software mode is retired; the marker must not point at the deleted file"
    )
    assert not (REPO / "skills/brainstorming/modes/software.md").exists(), (
        "modes/software.md must stay deleted after the 3-mode rescope"
    )
