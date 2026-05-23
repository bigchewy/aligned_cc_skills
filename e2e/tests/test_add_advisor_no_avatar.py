from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_add_advisor_has_no_avatar_generation_step():
    text = read("skills/add-advisor/SKILL.md")
    assert "Generate Avatar" not in text
    assert "avatar generation" not in text.lower()
    assert "Avatars:" not in text  # the Step 0 dashboard line
    assert "Review generated avatars" not in text


def test_add_advisor_steps_renumbered_contiguously():
    text = read("skills/add-advisor/SKILL.md")
    # After removing Step 5 (Generate Avatar), the remaining steps must renumber.
    # The framework step was Step 6 -> must now be a lower number; assert old labels gone.
    assert "### 5. Generate Avatar" not in text


def test_add_advisor_documents_two_file_convention():
    text = read("skills/add-advisor/SKILL.md")
    assert "advisors/registry.yaml" in text and "advisors/prompts/" in text
    assert "no glob fallback" in text.lower() or "silent no-op" in text.lower(), (
        "add-advisor must explain that a local advisor needs BOTH a registry entry and a prompt file"
    )


def test_add_advisor_notes_prompt_field_ignored_on_read():
    assert "ignored by the read side" in read("skills/add-advisor/SKILL.md"), (
        "add-advisor must note the read side ignores the prompt: field (it is metadata only)"
    )
