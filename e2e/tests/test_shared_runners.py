from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def read(rel):
    return (REPO / rel).read_text()


def test_framework_runner_exists():
    assert (REPO / "skills/_shared/framework-runner.md").is_file()


def test_framework_runner_has_intake_gate_parameter():
    text = read("skills/_shared/framework-runner.md")
    assert "intake_gate_mode" in text, "missing intake_gate_mode parameter"
    assert "strict" in text and "advisory" in text, "missing intake gate modes"
    assert "default" in text.lower() and "advisory" in text, "default mode not documented"


def test_framework_runner_carries_runner_protocol():
    text = read("skills/_shared/framework-runner.md")
    assert "Load Framework Content" in text or "load the framework content" in text.lower()
    assert "WAIT" in text, "missing WAIT discipline rule"
    assert "examples.md" in text and "anti-examples.md" in text
    assert "Composability" in text, "missing Composability rule"


def test_framework_runner_strict_mode_prompts_on_missing_required_documents():
    text = read("skills/_shared/framework-runner.md")
    assert "required_documents" in text
    assert "strict" in text
    # Strict mode must describe the prompt-user flow
    assert "prompt" in text.lower() or "ask" in text.lower()


def test_framework_runner_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/framework-runner.md" in text, (
        "new LLM behavior surface must be listed in eval-surface.yaml"
    )


def test_use_framework_invokes_shared_runner():
    text = read("skills/use-framework/SKILL.md")
    assert "_shared/framework-runner.md" in text, "use-framework must invoke shared runner"
    assert "intake_gate_mode" in text and "advisory" in text, (
        "use-framework must pass intake_gate_mode=advisory to preserve behavior"
    )
    # Anti-regression: inline runner protocol should be removed from use-framework
    assert "Inject all loaded content as operating instructions" not in text, (
        "runner protocol must live in _shared/framework-runner.md, not here"
    )
