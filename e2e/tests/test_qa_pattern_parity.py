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
