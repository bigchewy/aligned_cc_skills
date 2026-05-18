from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_software_mode_has_parity_marker():
    text = read("skills/brainstorming/modes/software.md")
    assert "PARITY MARKER" in text or "DUPLICATED TO" in text or "DUPLICATED FROM/TO" in text, (
        "software.md Q&A dispatch template must carry a parity marker comment"
    )
    assert "modes/authoring.md" in text, "marker must point at the sibling duplication site"


def test_authoring_mode_dispatch_template_matches_software():
    sw = read("skills/brainstorming/modes/software.md")
    au = read("skills/brainstorming/modes/authoring.md")
    # The Architect-as-proxy dispatch sub-agent prompt body should appear in both files.
    # Stable anchor: the role-override sentence.
    anchor = "Your normal constraint of 'do not propose alternatives' is suspended"
    assert anchor in sw, "anchor sentence missing from software.md"
    assert anchor in au, (
        "authoring.md's no-framework Q&A must use the same Architect-as-proxy dispatch as software.md"
    )
