"""The eval scorer for Claude's writes to a shared 6-step map.

The scorer applies Claude's batch to a fake store seeded from a fixture, runs the template's
own MapStore.inflate on the result, and checks the labels, the plan rows and the reply.
No Claude call here: each test hands it a written-out reply.
"""

import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

E2E = Path(__file__).resolve().parents[1]
SCORER = E2E / "scorers" / "six_step_map_write.js"
SEED = json.loads((E2E / "fixtures" / "six-step-map" / "seed.json").read_text())
SCENARIO = E2E / "scenarios" / "use-framework" / "6-step-process-artifact-write.yaml"

LABELS = [
    ("1", "People don't want to commute"),
    ("1A", "The value of the office hasn't kept up"),
    ("1A1", "We haven't defined what the office is for"),
    ("2", "Expectations are unclear"),
    ("2A", "Nobody has said which days count"),
    ("3", "The open-plan floor is too noisy"),
    ("4", "Some managers aren't enforcing the policy"),
    ("5", "The commute got longer"),
]
NEW_ID = "q7x2m9pa"


def good_writes():
    change = {
        "items": {
            NEW_ID: {"kind": "obstacle", "text": "Nobody has said which days count", "star": False, "parent": "aa2", "order": 2},
            "bb1": {"parent": "goal", "order": 4},
            "cc1": {"__delete__": True},
            "dd1": {"__delete__": True},
            "xx1": {"__delete__": True},
        },
        "key_actions": [
            {"text": "Say what the office is for", "risk": "high", "solution_ids": ["ee1"]},
            {"text": "Give each team a reason to meet in person", "risk": "medium", "solution_ids": []},
            {"text": "Hear how people feel each month", "risk": "low", "solution_ids": []},
        ],
        "execute": [SEED["main"]["execute"][0]],
    }
    baseline = copy.deepcopy(SEED["main"])
    baseline["items"][NEW_ID] = change["items"][NEW_ID]
    baseline["items"]["bb1"].update(change["items"]["bb1"])
    for gone in ("cc1", "dd1", "xx1"):
        del baseline["items"][gone]
    baseline["key_actions"] = change["key_actions"]
    baseline["execute"] = change["execute"]
    return [
        {"op": "update", "collection": "maps", "doc_id": "main", "if_version": SEED["main_version"], "data": change},
        {"op": "set", "collection": "maps", "doc_id": "baseline", "if_version": SEED["baseline_version"], "data": baseline},
    ]


def good_labels():
    return "\n".join(f"- {label}: {text}" for label, text in LABELS)


def reply(writes=None, labels=None, note=None):
    call = {"action": "batch", "url": SEED["link"], "writes": good_writes() if writes is None else writes}
    labels = good_labels() if labels is None else labels
    note = "Someone renamed The office is loud and deleted Run a monthly pulse survey." if note is None else note
    return f"```json\n{json.dumps(call)}\n```\n\n{note}\n\n{labels}\n"


def score(output):
    program = (
        "const scorer = require(%s);"
        "process.stdout.write(JSON.stringify(scorer(%s, {})));"
    ) % (json.dumps(str(SCORER)), json.dumps(output))
    proc = subprocess.run(["node", "-e", program], capture_output=True, text=True, cwd=E2E)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def writes_with(change):
    writes = good_writes()
    change(writes)
    return writes


def assert_fails(result, words):
    assert result["pass"] is False
    assert result["score"] == 1
    assert words in result["reason"], result["reason"]


def test_a_correct_reply_passes():
    result = score(reply())
    assert result == {"pass": True, "score": 5, "reason": "All checks passed."}


def test_a_baseline_sent_as_an_update_also_passes_when_it_ends_up_matching():
    def change(writes):
        data = copy.deepcopy(writes[0]["data"])
        data["items"]["aa3"] = {"text": "The open-plan floor is too noisy"}
        data["items"]["gg1"] = {"__delete__": True}
        data["items"]["zz9"] = {"parent": "gone1"}
        data["items"]["xx1"] = {"__delete__": True}
        writes[1] = {"op": "update", "collection": "maps", "doc_id": "baseline", "if_version": SEED["baseline_version"], "data": data}
    assert score(reply(writes_with(change)))["pass"] is True


def test_no_json_block_fails():
    assert_fails(score("I changed the map."), "no JSON block")


def test_broken_json_fails():
    assert_fails(score("```json\n{not json\n```"), "no JSON block")


def test_a_call_that_is_not_a_batch_fails():
    assert_fails(score('```json\n{"action": "update"}\n```'), "not a batch")


def test_a_write_with_no_data_is_refused_and_does_not_throw():
    def change(writes):
        del writes[0]["data"]
    assert_fails(score(reply(writes_with(change))), "no data")


def test_a_write_with_no_pin_is_refused():
    def change(writes):
        del writes[0]["if_version"]
    assert_fails(score(reply(writes_with(change))), "no if_version")


def test_an_old_pin_is_refused():
    def change(writes):
        writes[0]["if_version"] = SEED["main_version"] - 1
    assert_fails(score(reply(writes_with(change))), "version_mismatch")


def test_a_format_version_used_as_the_pin_is_refused():
    def change(writes):
        writes[0]["if_version"] = 1
    assert_fails(score(reply(writes_with(change))), "version_mismatch")


def test_a_delete_marker_in_a_set_is_refused():
    def change(writes):
        writes[1]["data"]["items"]["cc1"] = {"__delete__": True}
    assert_fails(score(reply(writes_with(change))), "__delete__ in a set")


def test_a_delete_marker_in_a_list_is_refused():
    def change(writes):
        writes[0]["data"]["execute"] = [{"__delete__": True}]
    assert_fails(score(reply(writes_with(change))), "__delete__ inside a list")


def test_rewriting_main_whole_fails():
    def change(writes):
        writes[0] = {"op": "set", "collection": "maps", "doc_id": "main", "if_version": SEED["main_version"],
                     "data": copy.deepcopy(writes[1]["data"])}
    assert_fails(score(reply(writes_with(change))), "update")


def test_touching_an_item_that_did_not_change_fails():
    def change(writes):
        writes[0]["data"]["items"]["aa1"] = {"text": "People don't want to commute"}
    assert_fails(score(reply(writes_with(change))), "unchanged")


def test_leaving_the_sub_item_behind_fails():
    def change(writes):
        del writes[0]["data"]["items"]["dd1"]
        writes[1]["data"]["items"]["dd1"] = SEED["main"]["items"]["dd1"]
    assert_fails(score(reply(writes_with(change))), "dd1")


def test_no_baseline_in_the_batch_fails():
    assert_fails(score(reply(good_writes()[:1])), "baseline")


def test_a_baseline_that_does_not_match_fails():
    def change(writes):
        writes[1]["data"]["goal"]["text"] = "Something else"
    assert_fails(score(reply(writes_with(change))), "baseline")


def test_plan_rows_left_for_the_removed_solution_fail():
    def change(writes):
        rows = [SEED["main"]["execute"][0], SEED["main"]["execute"][1]]
        writes[0]["data"]["execute"] = rows
        writes[1]["data"]["execute"] = rows
    assert_fails(score(reply(writes_with(change))), "execute")


def test_plan_rows_left_for_a_colleagues_delete_fail():
    def change(writes):
        rows = [SEED["main"]["execute"][0], SEED["main"]["execute"][2]]
        writes[0]["data"]["execute"] = rows
        writes[1]["data"]["execute"] = rows
    assert_fails(score(reply(writes_with(change))), "execute")


def test_a_key_action_dropped_with_its_last_solution_fails():
    def change(writes):
        rows = writes[0]["data"]["key_actions"][:1]
        writes[0]["data"]["key_actions"] = rows
        writes[1]["data"]["key_actions"] = rows
    assert_fails(score(reply(writes_with(change))), "key_actions")


def test_a_moved_item_not_placed_last_fails():
    def change(writes):
        writes[0]["data"]["items"]["bb1"]["order"] = 1
        writes[1]["data"]["items"]["bb1"]["order"] = 1
    assert_fails(score(reply(writes_with(change))), "labels")


def test_a_new_item_with_a_bad_id_fails():
    def change(writes):
        for write, path in ((writes[0], "data"), (writes[1], "data")):
            write[path]["items"]["New-One"] = write[path]["items"].pop(NEW_ID)
    assert_fails(score(reply(writes_with(change))), "id")


def test_a_new_item_missing_a_field_fails():
    def change(writes):
        # The two writes share this item, so one delete covers both.
        del writes[0]["data"]["items"][NEW_ID]["star"]
    assert_fails(score(reply(writes_with(change))), "star")


def test_changing_the_format_version_fails():
    def change(writes):
        writes[0]["data"]["version"] = 2
        writes[1]["data"]["version"] = 2
    assert_fails(score(reply(writes_with(change))), "version")


def test_old_labels_in_the_reply_fail():
    stale = good_labels().replace("1A1:", "1B2:")
    assert_fails(score(reply(labels=stale)), "1A1")


def test_a_label_left_out_of_the_reply_fails():
    missing = "\n".join(line for line in good_labels().splitlines() if "days count" not in line)
    assert_fails(score(reply(labels=missing)), "2A")


def test_a_label_on_a_solution_is_not_checked_but_a_reply_without_the_edits_it_did_not_make_fails():
    assert_fails(score(reply(note="I made your changes.")), "did not make")


def test_labels_inside_the_json_block_do_not_count():
    assert_fails(score(reply(labels="See the JSON above.")), "labels")


def test_expected_labels_match_the_page_for_the_good_writes():
    # A good reply passing already runs the page's own labels against this list.
    assert score(reply())["pass"] is True


def test_scorer_uses_the_page_code_and_the_fixture():
    text = SCORER.read_text()
    assert "mind-map-template.html" in text
    assert "seed.json" in text
    assert "MapStore" in text and ".inflate(" in text
    assert "itemLabels" in text


def test_scenario_uses_the_real_prompt_and_the_scorer():
    data = yaml.safe_load(SCENARIO.read_text())
    assert data["defaultTest"]["assert"][0]["type"] == "javascript"
    assert data["defaultTest"]["assert"][0]["value"] == "file://../../scorers/six_step_map_write.js"
    test = data["tests"][0]
    assert test["metadata"]["arm"] == "single"
    assert test["vars"]["system_context"] == "file://../../../frameworks/6-step-process/prompt.md"
    assert test["vars"]["seed"] == "file://../../fixtures/six-step-map/seed.json"
    assert "{{seed}}" in data["prompts"][0]


def test_scenario_is_in_the_trigger_map():
    triggers = yaml.safe_load((E2E / "trigger-map.yaml").read_text())["triggers"]
    entry = next(t for t in triggers if "frameworks/6-step-process/prompt.md" in t["paths"])
    assert "frameworks/6-step-process/examples.md" in entry["paths"]
    assert "frameworks/6-step-process/anti-examples.md" in entry["paths"]
    assert "scenarios/use-framework/6-step-process-artifact-write.yaml" in entry["scenarios"]
