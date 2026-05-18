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


def test_advisor_runner_exists():
    assert (REPO / "skills/_shared/advisor-runner.md").is_file()


def test_advisor_runner_carries_persona_protocol():
    text = read("skills/_shared/advisor-runner.md")
    assert "Adopt the Persona" in text or "adopt the persona" in text.lower()
    assert "Core Frameworks" in text, "missing Core Frameworks reference"
    assert "Switching" in text and "Ending" in text, "missing persona lifecycle rules"
    assert "Composability" in text, "missing Composability rule"
    # Bidirectional dispatch hook
    assert "framework-runner.md" in text, (
        "advisor runner should reference framework-runner.md for mid-conversation dispatch"
    )


def test_advisor_runner_is_in_eval_surface():
    text = read("e2e/eval-surface.yaml")
    assert "skills/_shared/advisor-runner.md" in text


def test_use_advisor_invokes_shared_runner():
    text = read("skills/use-advisor/SKILL.md")
    assert "_shared/advisor-runner.md" in text, "use-advisor must invoke shared runner"
    # Behavior preservation: top-level invocation must explicitly pass greeting_mode=full,
    # since silent is the new code path introduced by this refactor.
    assert "greeting_mode" in text and "full" in text, (
        "use-advisor must pass greeting_mode=full to preserve top-level behavior"
    )
    # Behavior preservation: top-level invocation MUST NOT pass greeting_mode=silent,
    # which would suppress the brief greeting and Core Frameworks listing that
    # users expect from /aligned:use-advisor.
    assert "greeting_mode=silent" not in text and "greeting_mode: silent" not in text, (
        "top-level use-advisor must not pass silent — that path is reserved for runner composition"
    )
    # Anti-regression: inline persona protocol should be removed
    assert "Read the full advisor prompt file" not in text, (
        "persona adoption protocol must live in _shared/advisor-runner.md"
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


def test_framework_runner_documents_empty_prompt_error_path():
    """Design L207: framework runner with empty prompt.md."""
    text = read("skills/_shared/framework-runner.md")
    # "missing or empty" is the Step 1 contract sentence
    assert "empty" in text.lower(), "framework-runner must handle empty prompt.md as error"
    assert "report the error and stop" in text or "STOP" in text


def test_framework_runner_documents_broken_advisor_reference_path():
    """Design L208: framework with broken advisor field reference."""
    text = read("skills/_shared/framework-runner.md")
    # The runner must describe what happens when a framework references a non-existent advisor
    assert "advisor" in text.lower()
    # Either: the runner documents falling back to generic facilitator,
    # OR: the runner documents stopping with an error.
    # Both are acceptable contracts; assert at least one is present.
    assert (
        "fallback" in text.lower()
        or "generic facilitator" in text.lower()
        or "broken" in text.lower()
        or "missing advisor" in text.lower()
    ), "framework-runner must document broken-advisor-reference handling"


def test_advisor_runner_documents_missing_prompt_file_path():
    """Advisor runner must STOP when matched advisor path doesn't exist."""
    text = read("skills/_shared/advisor-runner.md")
    assert "STOP" in text or "does not exist" in text
    assert "Configuration Validation" in text, (
        "advisor-runner must have a fail-closed validation section"
    )
