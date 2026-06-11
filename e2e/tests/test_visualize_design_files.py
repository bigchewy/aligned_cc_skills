from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_visualize_design_skill_exists_and_named():
    path = REPO / "skills/visualize-design/SKILL.md"
    assert path.is_file(), "visualize-design SKILL.md must exist"
    text = path.read_text()
    assert "name: visualize-design" in text, "frontmatter name must match directory"


def test_visualize_design_delegates_to_runner():
    text = read("skills/visualize-design/SKILL.md")
    assert "skills/_shared/visualization-runner.md" in text, "must delegate to the runner"
    assert "software-template.html" in text, "must resolve the brainstorming template by path"
    assert "docs/design-visualizations/" in text, "must use the standalone output convention"


def test_visualize_design_has_fixed_no_content_question():
    text = read("skills/visualize-design/SKILL.md")
    assert "No document path was given and this conversation has no renderable content yet" in text, (
        "the bare-invocation question must use the fixed wording"
    )


def test_visualize_design_states_anti_shortcut():
    text = read("skills/visualize-design/SKILL.md").lower()
    assert "never hand-write" in text or "do not hand-write" in text, (
        "the standalone caller must restate the anti-shortcut contract"
    )


def test_visualize_design_excludes_brainstorming_scaffolding():
    text = read("skills/visualize-design/SKILL.md")
    assert "critique panel" not in text.lower(), "general visualizer excludes the critique panel"
    assert "**Mockups:**" not in text, "general visualizer excludes the Mockups header field"
