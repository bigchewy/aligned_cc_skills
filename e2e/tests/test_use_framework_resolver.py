from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_use_framework_step1_routes_through_resolver():
    text = read("skills/use-framework/SKILL.md")
    assert "skills/_shared/resolve-framework-source.md" in text


def test_use_framework_marks_local_frameworks():
    text = read("skills/use-framework/SKILL.md")
    assert "(local)" in text
    assert 'source: "local"' in text


def test_use_framework_passes_merged_list_to_recommendation():
    text = read("skills/use-framework/SKILL.md")
    assert "registry path: `frameworks/registry.yaml`" not in text
    assert "pre-merged" in text.lower()


def test_use_framework_runner_path_is_absolute_framework_dir():
    text = read("skills/use-framework/SKILL.md")
    assert "absolute_framework_dir" in text
    assert "<plugin-root>/frameworks/<id>/" not in text


def test_use_framework_first_line_parse_only_for_unregistered():
    text = read("skills/use-framework/SKILL.md")
    step2 = text.split("## Step 2", 1)[1].split("## Step 3", 1)[0]
    assert "registered: false" in step2
    assert "only" in step2
