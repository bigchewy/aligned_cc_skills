"""Every eval scenario runs through the shared Claude Code login provider and judge prompt."""
import json
from pathlib import Path

import pytest
import yaml

E2E = Path(__file__).resolve().parents[1]
SCENARIOS = sorted((E2E / "scenarios").rglob("*.yaml"))
PROVIDER_REF = "file://../../providers/claude-login.yaml"
RUBRIC_REF = "file://../../providers/rubric-prompt.txt"
ARMS = {"full-stack", "vanilla", "aware", "single"}


def _ids(path):
    return str(path.relative_to(E2E))


def _load(path):
    return yaml.safe_load(path.read_text())


def test_all_scenarios_found():
    assert len(SCENARIOS) >= 58


def test_shared_provider_file():
    provider = yaml.safe_load((E2E / "providers" / "claude-login.yaml").read_text())
    assert provider == {
        "id": "anthropic:claude-agent-sdk",
        "config": {
            "apiKeyRequired": False,
            "model": "sonnet",
            "custom_system_prompt": "",
            "tools": [],
            "max_turns": 1,
        },
    }


def test_shared_rubric_prompt_is_plain_text_on_a_1_to_5_scale():
    text = (E2E / "providers" / "rubric-prompt.txt").read_text()
    assert "{{ output }}" in text
    assert "{{ rubric }}" in text
    assert "1 to 5" in text
    with pytest.raises(json.JSONDecodeError):
        json.loads(text)


def test_package_pins():
    pkg = json.loads((E2E / "package.json").read_text())
    assert pkg["devDependencies"]["promptfoo"] == "0.124.1"
    assert pkg["devDependencies"]["@anthropic-ai/claude-agent-sdk"] == "0.3.283"
    assert pkg["engines"]["node"] == ">=22.22.0"
    assert pkg["scripts"]["eval"] == ".venv/bin/python run_evals.py"


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_scenario_uses_shared_provider(path):
    assert _load(path)["providers"] == [PROVIDER_REF]
    assert (path.parent / "../../providers/claude-login.yaml").resolve().is_file()


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_judge_uses_shared_provider_and_prompt(path):
    options = _load(path)["defaultTest"]["options"]
    assert options["provider"] == PROVIDER_REF
    assert options["rubricPrompt"] == RUBRIC_REF


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_scenario_never_names_the_api_provider(path):
    assert "anthropic:messages" not in path.read_text()


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_every_test_has_a_kind_label(path):
    for test in _load(path)["tests"]:
        assert (test.get("metadata") or {}).get("arm") in ARMS, test.get("description")


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_paired_scenarios_have_one_full_stack_and_one_vanilla(path):
    arms = [t["metadata"]["arm"] for t in _load(path)["tests"]]
    if "single" in arms:
        assert set(arms) == {"single"}
    else:
        assert arms.count("full-stack") == 1
        assert arms.count("vanilla") == 1


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids)
def test_scenario_has_no_top_level_env(path):
    assert "env" not in _load(path)
