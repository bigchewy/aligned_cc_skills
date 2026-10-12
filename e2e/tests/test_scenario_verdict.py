import json

from scorers.scenario_verdict import Verdict, is_rate_limited, score_file, score_results


def result(arm, score, description=None, error=None, failure_reason=0, components=None, model=None):
    response = {"metadata": {"modelUsage": {model: {}}}} if model else {}
    return {
        "testCase": {"description": description or arm, "metadata": {"arm": arm}},
        "error": error,
        "failureReason": failure_reason,
        "score": score,
        "gradingResult": {"score": score, "componentResults": components or []},
        "response": response,
    }


def test_paired_pass():
    v = score_results([result("full-stack", 4.5, model="claude-sonnet-x"), result("vanilla", 2.0), result("aware", 3.0)])
    assert v.verdict == "PASS"
    assert v.full_stack == 4.5
    assert v.gap_vanilla == 2.5
    assert v.gap_aware == 1.5
    assert v.model == "claude-sonnet-x"


def test_paired_fails_when_full_stack_below_3_5():
    v = score_results([result("full-stack", 3.25), result("vanilla", 1.0)])
    assert v.verdict == "FAIL"
    assert "full-stack 3.25 below 3.5" in v.reason


def test_paired_fails_when_vanilla_gap_below_1():
    v = score_results([result("full-stack", 4.0), result("vanilla", 3.5)])
    assert v.verdict == "FAIL"
    assert "vanilla gap 0.50 below 1.0" in v.reason


def test_paired_fails_when_aware_gap_below_0_5():
    v = score_results([result("full-stack", 4.0), result("vanilla", 2.0), result("aware", 3.75)])
    assert v.verdict == "FAIL"
    assert "aware gap 0.25 below 0.5" in v.reason


def test_paired_without_aware_ignores_that_bar():
    v = score_results([result("full-stack", 4.0), result("vanilla", 2.5)])
    assert v.verdict == "PASS"
    assert v.gap_aware is None


def test_routing_pass_and_fail():
    assert score_results([result("single", 4.0), result("single", 3.5)]).verdict == "PASS"
    v = score_results([result("single", 4.0, "a"), result("single", 3.0, "b")])
    assert v.verdict == "FAIL"
    assert "1 of 2 tests below 3.5" in v.reason


def test_judge_error_is_error():
    judge_failed = {"pass": False, "score": 0, "reason": "Could not parse JSON", "metadata": {"graderError": True}}
    v = score_results([result("full-stack", 4.0, components=[judge_failed]), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "judge failed" in v.reason


def test_provider_error_is_error():
    v = score_results([result("full-stack", 0, error="spawn claude ENOENT", failure_reason=2), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "spawn claude ENOENT" in v.reason
    assert v.rate_limited is False


def test_rate_limit_error_is_flagged():
    v = score_results([result("full-stack", 0, error="Claude AI usage limit reached", failure_reason=2)])
    assert v.verdict == "ERROR"
    assert v.rate_limited is True


def test_missing_kind_label_is_error():
    bad = result("full-stack", 4.0)
    bad["testCase"]["metadata"] = {}
    v = score_results([bad, result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "kind label" in v.reason


def test_paired_without_vanilla_is_error():
    assert score_results([result("full-stack", 4.0)]).verdict == "ERROR"


def test_empty_results_is_error():
    assert score_results([]).verdict == "ERROR"


def test_score_file_reads_promptfoo_output(tmp_path):
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"results": {"results": [result("single", 4.0)]}}))
    assert score_file(path).verdict == "PASS"


def test_score_file_missing_file_is_error(tmp_path):
    v = score_file(tmp_path / "nope.json")
    assert v.verdict == "ERROR"
    assert "cannot read promptfoo output" in v.reason


def test_score_file_unreadable_json_is_error(tmp_path):
    path = tmp_path / "out.json"
    path.write_text("{not json")
    assert score_file(path).verdict == "ERROR"


def test_score_file_wrong_shape_is_error(tmp_path):
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"results": []}))
    v = score_file(path)
    assert v.verdict == "ERROR"
    assert "no results list" in v.reason


def test_verdict_defaults():
    assert Verdict("PASS", "").model == "unknown"


def test_missing_numeric_score_is_error():
    bad = result("full-stack", None)
    v = score_results([bad, result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert "no numeric score" in v.reason


def test_null_nested_score_falls_back_to_top_level():
    r = result("single", 4.0)
    r["gradingResult"]["score"] = None
    v = score_results([r])
    assert v.verdict == "PASS"
    assert v.full_stack == 4.0


def test_non_dict_result_is_error(tmp_path):
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"results": {"results": [1, result("single", 4.0)]}}))
    v = score_file(path)
    assert v.verdict == "ERROR"
    assert "not an object" in v.reason


def test_description_with_429_is_not_rate_limit():
    v = score_results([result("full-stack", 0, description="case 429", error="spawn claude ENOENT", failure_reason=2), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert v.rate_limited is False


def test_judge_reason_429_is_rate_limit():
    judge_failed = {"pass": False, "score": 0, "reason": "429 Too Many Requests", "metadata": {"graderError": True}}
    v = score_results([result("full-stack", 4.0, components=[judge_failed]), result("vanilla", 1.0)])
    assert v.verdict == "ERROR"
    assert v.rate_limited is True


def test_is_rate_limited_matches_429_as_whole_word_only():
    assert is_rate_limited("HTTP 429") is True
    assert is_rate_limited("error code 1429 from server") is False
    assert is_rate_limited("Usage Limit reached") is True
