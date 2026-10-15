"""Breadboard to Pages: Brad Frost turns a breadboard into exact static screens.

The last step of the story map session hands Slice 1's breadboard to this
framework. It builds each place from the project's design-principles.md tokens
as a template, then a page with real content, then the variations that break
it, at phone and desktop widths. Every element names the breadboard item it
comes from, no value on a screen comes from outside the tokens, and the
screens are walked against the story map at the end.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRAMEWORK = REPO_ROOT / "frameworks" / "breadboard-to-pages"
PROMPT = FRAMEWORK / "prompt.md"
EXAMPLES = FRAMEWORK / "examples.md"
ANTI = FRAMEWORK / "anti-examples.md"
TEMPLATE_HTML = FRAMEWORK / "screens-template.html"
TEMPLATE_MD = FRAMEWORK / "screens-template.md"
ADVISOR = REPO_ROOT / "advisors" / "prompts" / "brad-frost.md"
SCENARIO = REPO_ROOT / "e2e" / "scenarios" / "use-framework" / "breadboard-to-pages.yaml"
TRIGGER_MAP = REPO_ROOT / "e2e" / "trigger-map.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _entry():
    with open(REPO_ROOT / "frameworks" / "registry.yaml") as f:
        return {e["id"]: e for e in yaml.safe_load(f)["frameworks"]}["breadboard-to-pages"]


def _phases(text: str) -> dict:
    parts = re.split(r"^### PHASE (\d+):", text, flags=re.MULTILINE)
    return {int(parts[i]): parts[i + 1].split("## Key Rules")[0] for i in range(1, len(parts), 2)}


def test_framework_files_exist():
    for p in (PROMPT, EXAMPLES, ANTI, TEMPLATE_HTML, TEMPLATE_MD):
        assert p.is_file(), f"missing {p.relative_to(REPO_ROOT)}"


def test_registry_entry():
    e = _entry()
    assert e["advisor"] == "brad-frost"
    assert e["name"] == "Breadboard to Pages"
    assert e["category"] == "product-design"
    assert e["deliverable_type"] == "plan"


def test_prompt_opens_in_the_standard_form():
    first = [l for l in _read(PROMPT).split("---", 2)[2].splitlines() if l.strip()][0]
    assert first.startswith("You are Brad Frost, guiding someone through Breadboard to Pages - ")


def test_every_phase_waits_for_the_user():
    phases = _phases(_read(PROMPT))
    assert len(phases) >= 6
    for n, body in phases.items():
        assert "**WAIT for the user to respond.**" in body, f"PHASE {n} has no WAIT"


def test_prompt_states_the_contract():
    text = _read(PROMPT)
    # Input: a breadboard and the project's tokens, found where the story map finds them.
    assert "breadboard" in text.lower()
    for place in ("brand/guidelines/design-principles.md", "brand/*/guidelines/design-principles.md",
                  "docs/design/design-principles.md"):
        assert place in text
    # Every element is traced to its breadboard item.
    assert "data-from" in text
    # Both widths.
    assert "phone" in text and "desktop" in text
    # Only tokens: raw values are counted, missing values go back to the principles skill.
    assert "/aligned:create-design-principles" in text
    assert "var(--" in text
    # Atomic Design stages, real content, and the cases that break a page.
    for term in ("template", "real", "variation", "empty", "long", "role", "snowflake"):
        assert term in text.lower(), f"prompt should cover {term}"
    # The walk against the story map.
    assert "story map" in text.lower()
    assert re.search(r"walk", text, re.I)


def test_hierarchy_rules_are_credited_to_their_authors():
    text = _read(PROMPT)
    assert "De-emphasize to emphasize" in text
    assert "Refactoring UI" in text


def test_output_sits_beside_the_story_map():
    text = _read(PROMPT)
    assert "docs/story-maps/{slug}-screens.md" in text
    assert "docs/story-maps/{slug}-screens.html" in text


def test_template_has_tokens_frames_and_trace_toggle():
    html = _read(TEMPLATE_HTML)
    assert ":root" in html
    assert "prefers-color-scheme: dark" in html
    assert 'data-theme="dark"' in html or "[data-theme=\"dark\"]" in html or "data-theme=dark" in html
    assert "data-from" in html
    for width in ("390", "1280"):
        assert width in html, f"template should show a {width}px frame"


def test_examples_and_anti_examples_cover_the_failure_modes():
    ex = _read(EXAMPLES).lower()
    anti = _read(ANTI).lower()
    assert "data-from" in ex
    for failure in ("lorem ipsum", "one-off", "happy path"):
        assert failure in anti, f"anti-examples should cover {failure}"


def test_advisor_prompt_lists_the_framework():
    assert "`breadboard-to-pages`" in _read(ADVISOR)


def test_scenario_exists_and_is_wired():
    assert SCENARIO.is_file()
    flat = yaml.safe_dump(yaml.safe_load(_read(TRIGGER_MAP)))
    for p in ("frameworks/breadboard-to-pages/prompt.md", "frameworks/breadboard-to-pages/examples.md",
              "frameworks/breadboard-to-pages/anti-examples.md"):
        assert p in flat
    assert "scenarios/use-framework/breadboard-to-pages.yaml" in flat
