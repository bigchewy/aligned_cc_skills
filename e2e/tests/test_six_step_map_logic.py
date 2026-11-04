"""Tests for the logic block in the 6-step process mind map template.

The harness pulls <script id="map-logic"> out of the template and runs it
under node with a JSON test case. The logic touches no DOM.
"""

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO / "frameworks" / "6-step-process" / "mind-map-template.html"

RUNNER = r"""
const logic = %(logic)s;
const kase = %(kase)s;
(new Function(logic))();
const L = globalThis.MapLogic;

function makeHandle(spec) {
  const state = { content: spec.content, writes: 0 };
  const handle = {
    state,
    async requestPermission(opts) {
      state.permissionMode = opts && opts.mode;
      if (spec.permission === 'throw') throw new Error('boom');
      return spec.permission || 'granted';
    },
    async getFile() {
      if (spec.getFileFails) throw new Error('cannot read');
      return { text: async () => state.content };
    },
    async createWritable() {
      let buffer = '';
      const writable = {
        async write(data) {
          if (spec.writeFails === 'write') throw new Error('disk full');
          buffer += data;
        },
        async close() {
          if (spec.writeFails === 'close') throw new Error('disk full');
          state.content = buffer;
          state.writes += 1;
        },
      };
      if (spec.abort !== 'missing') {
        writable.abort = async () => {
          state.aborted = true;
          if (spec.abort === 'throw') throw new Error('abort failed');
        };
      }
      return writable;
    },
  };
  return handle;
}

(async () => {
  let handle = null;
  if (kase.handle) handle = makeHandle(kase.handle);
  const stand_ins = {
    __HANDLE__: handle,
    __THROWS__: () => { throw new Error('commit failed'); },
    __NOOP__: () => {},
    __TRUE__: () => true,
    __FALSE__: () => false,
  };
  const args = kase.args.map(a => (typeof a === 'string' && a in stand_ins ? stand_ins[a] : a));
  const result = await L[kase.fn](...args);
  process.stdout.write(JSON.stringify({
    result,
    file: handle ? handle.state.content : null,
    writes: handle ? handle.state.writes : null,
    permissionMode: handle ? handle.state.permissionMode : null,
    aborted: handle ? Boolean(handle.state.aborted) : null,
  }));
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def logic_block(html):
    m = re.search(r'<script id="map-logic">(.*?)</script>', html, re.S)
    assert m, "map-logic block not found"
    return m.group(1)


def logic_source():
    return logic_block(TEMPLATE.read_text())


def call(fn, *args, handle=None):
    program = RUNNER % {
        "logic": json.dumps(logic_source()),
        "kase": json.dumps({"fn": fn, "args": list(args), "handle": handle}),
    }
    proc = subprocess.run(
        ["node", "-"], input=program, capture_output=True, text=True, cwd=REPO
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def make_map(**over):
    base = {
        "map_id": "m-1",
        "revision": 1,
        "person": "Pat",
        "goal": {"text": "g", "from": "", "to": "", "by": ""},
        "obstacles": [
            {"id": "o1", "text": "a", "whys": ["w1", "w2"], "root_cause": "", "solution_ids": ["s1", "s2"]},
            {"id": "o2", "text": "b", "whys": [], "root_cause": "", "solution_ids": ["s2"]},
        ],
        "solutions": [
            {"id": "s1", "text": "one", "star": False},
            {"id": "s2", "text": "two", "star": True},
            {"id": "s3", "text": "three", "star": False},
        ],
        "key_actions": [],
        "execute": [],
        "feedback": {"number": "", "check_on": "", "redraw_if": ""},
        "baseline": {},
    }
    base.update(over)
    return base


def page(map_obj, extra=""):
    data = json.dumps(map_obj).replace("<", "\\u003c")
    return (
        "<html><body>" + extra + '<script id="map-data" type="application/json">'
        + data + "</script></body></html>"
    )


def test_untied_ids():
    out = call("untiedSolutionIds", make_map())["result"]
    assert out == ["s3"]


def test_repeat_count():
    m = make_map()
    assert call("repeatCount", m, "s2")["result"] == 2
    assert call("repeatCount", m, "s1")["result"] == 1
    assert call("repeatCount", m, "s3")["result"] == 0


def test_delete_repeated_solution_only_leaves_that_obstacle():
    m = call("deleteSolutionFromObstacle", make_map(), "o1", "s2")["result"]
    by_id = {o["id"]: o for o in m["obstacles"]}
    assert by_id["o1"]["solution_ids"] == ["s1"]
    assert by_id["o2"]["solution_ids"] == ["s2"]
    assert any(s["id"] == "s2" for s in m["solutions"])
    assert "s2" not in call("untiedSolutionIds", m)["result"]


def test_delete_last_tie_sends_solution_to_tray():
    m = call("deleteSolutionFromObstacle", make_map(), "o1", "s1")["result"]
    assert any(s["id"] == "s1" for s in m["solutions"])
    assert "s1" in call("untiedSolutionIds", m)["result"]


def test_delete_obstacle_keeps_solution_shared_elsewhere():
    m = call("deleteObstacle", make_map(), "o1")["result"]
    assert [o["id"] for o in m["obstacles"]] == ["o2"]
    untied = call("untiedSolutionIds", m)["result"]
    assert "s1" in untied
    assert "s2" not in untied
    assert len(m["solutions"]) == 3


def test_mark_root_cause_moves_last_why():
    m = call("markRootCause", make_map(), "o1")["result"]
    o1 = m["obstacles"][0]
    assert o1["whys"] == ["w1"]
    assert o1["root_cause"] == "w2"


def test_mark_root_cause_without_whys_changes_nothing():
    m = call("markRootCause", make_map(), "o2")["result"]
    assert m["obstacles"][1]["whys"] == []
    assert m["obstacles"][1]["root_cause"] == ""


def test_script_close_tag_round_trips():
    m = make_map(person="</script><b>x")
    ser = call("serializeMap", m)["result"]
    assert "<" not in ser
    html = call("replaceMapData", page(make_map()), m)["result"]
    assert html.count("</script>") == page(make_map()).count("</script>")
    parsed = call("parseMapData", html)["result"]
    assert parsed["person"] == "</script><b>x"


def test_dollar_patterns_round_trip():
    text = "cost $& and $1 and $` and $' and $$"
    m = make_map(person=text)
    html = call("replaceMapData", page(make_map()), m)["result"]
    parsed = call("parseMapData", html)["result"]
    assert parsed["person"] == text


def test_replace_keeps_surrounding_page():
    src = page(make_map(), extra="<h1>Keep me</h1>")
    html = call("replaceMapData", src, make_map(person="New"))["result"]
    assert "<h1>Keep me</h1>" in html
    assert call("parseMapData", html)["result"]["person"] == "New"


def test_parse_returns_null_without_slot_or_bad_json():
    assert call("parseMapData", "<html></html>")["result"] is None
    bad = '<script id="map-data" type="application/json">{nope</script>'
    assert call("parseMapData", bad)["result"] is None


def test_check_target_ok_when_same_revision():
    out = call("checkTarget", page(make_map()), make_map())["result"]
    assert out == {"ok": True}


def test_check_target_stale_when_file_revision_newer():
    out = call("checkTarget", page(make_map(revision=5)), make_map(revision=3))["result"]
    assert out == {"ok": False, "reason": "stale"}


def test_check_target_wrong_map_id():
    out = call("checkTarget", page(make_map(map_id="other")), make_map())["result"]
    assert out == {"ok": False, "reason": "wrong-map"}


def test_check_target_not_a_map():
    assert call("checkTarget", "<html>nothing</html>", make_map())["result"] == {
        "ok": False, "reason": "not-a-map"}
    assert call("checkTarget", page(make_map(map_id="")), make_map())["result"] == {
        "ok": False, "reason": "not-a-map"}


def test_check_target_takes_no_file_name():
    # Identity comes from map_id in the data, so the check gets only html and map.
    m = make_map()
    out = call("checkTarget", page(m), m)["result"]
    assert out["ok"] is True


def test_check_target_non_numeric_revision_is_not_a_map():
    for bad in ("5", None, {}, []):
        out = call("checkTarget", page(make_map(revision=bad)), make_map())["result"]
        assert out == {"ok": False, "reason": "not-a-map"}


def test_replace_in_real_template_leaves_logic_block_byte_identical():
    template = TEMPLATE.read_text()
    html = call("replaceMapData", template, make_map(person="</script>$&"))["result"]
    assert logic_block(html) == logic_block(template)
    slot = re.compile(r'(<script id="map-data"[^>]*>).*?(</script>)', re.S)
    assert slot.sub("", html) == slot.sub("", template)
    assert call("parseMapData", html)["result"]["person"] == "</script>$&"


def test_save_bumps_revision():
    baseline = {"person": "Pat", "obstacles": [{"id": "o1"}]}
    m = make_map(revision=2, baseline=baseline)
    src = page(m)
    new = make_map(revision=2, person="Edited", baseline=baseline)
    out = call("saveToHandle", "__HANDLE__", src, new, handle={"content": src})
    assert out["result"] == {"ok": True, "revision": 3, "baseline": baseline}
    assert out["permissionMode"] == "readwrite"
    saved = call("parseMapData", out["file"])["result"]
    assert saved["revision"] == 3
    assert saved["person"] == "Edited"
    assert saved["baseline"] == baseline
    assert out["writes"] == 1


def test_save_after_a_baseline_only_update_keeps_that_baseline_and_is_not_refused():
    # Claude moved baseline in the file and left revision alone. The open tab has the old one.
    old = {"person": "Pat"}
    new = {"person": "Read by Claude"}
    file_html = page(make_map(revision=2, person="Read by Claude", baseline=new))
    tab = make_map(revision=2, person="Edited again", baseline=old)
    out = call("saveToHandle", "__HANDLE__", page(tab), tab, handle={"content": file_html})
    assert out["result"] == {"ok": True, "revision": 3, "baseline": new}
    saved = call("parseMapData", out["file"])["result"]
    assert saved["person"] == "Edited again"
    assert saved["baseline"] == new
    assert saved["revision"] == 3


def test_second_save_keeps_the_file_baseline():
    old = {"person": "Pat"}
    new = {"person": "Read by Claude"}
    tab = make_map(revision=2, person="First save", baseline=old)
    first = call("saveToHandle", "__HANDLE__", page(tab), tab,
                 handle={"content": page(make_map(revision=2, baseline=new))})
    tab.update(revision=first["result"]["revision"], baseline=first["result"]["baseline"], person="Second")
    second = call("saveToHandle", "__HANDLE__", page(tab), tab, handle={"content": first["file"]})
    assert second["result"] == {"ok": True, "revision": 4, "baseline": new}
    assert call("parseMapData", second["file"])["result"]["baseline"] == new


def test_save_keeps_the_page_baseline_when_the_file_has_none():
    page_baseline = {"person": "Pat"}
    file_map = make_map()
    del file_map["baseline"]
    tab = make_map(baseline=page_baseline)
    out = call("saveToHandle", "__HANDLE__", page(tab), tab, handle={"content": page(file_map)})
    assert out["result"]["ok"] is True
    assert out["result"]["baseline"] == page_baseline
    assert call("parseMapData", out["file"])["result"]["baseline"] == page_baseline


def test_refused_save_leaves_the_file_baseline_alone():
    new = {"person": "Read by Claude"}
    newer = page(make_map(revision=9, baseline=new))
    tab = make_map(revision=2, baseline={"person": "Pat"})
    out = call("saveToHandle", "__HANDLE__", page(tab), tab, handle={"content": newer})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == newer


def test_save_permission_denied():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(),
               handle={"content": src, "permission": "denied"})
    assert out["result"] == {"ok": False, "reason": "permission"}
    assert out["file"] == src
    assert out["writes"] == 0


def test_save_permission_request_throws():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(),
               handle={"content": src, "permission": "throw"})
    assert out["result"] == {"ok": False, "reason": "permission"}
    assert out["file"] == src


def test_save_unreadable_file():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(),
               handle={"content": src, "getFileFails": True})
    assert out["result"] == {"ok": False, "reason": "unreadable"}
    assert out["writes"] == 0


def test_save_refuses_wrong_file_and_stale_file():
    src = page(make_map())
    wrong = page(make_map(map_id="other"))
    out = call("saveToHandle", "__HANDLE__", src, make_map(), handle={"content": wrong})
    assert out["result"] == {"ok": False, "reason": "wrong-map"}
    assert out["file"] == wrong
    newer = page(make_map(revision=9))
    out = call("saveToHandle", "__HANDLE__", src, make_map(), handle={"content": newer})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == newer
    junk = "not a map at all"
    out = call("saveToHandle", "__HANDLE__", src, make_map(), handle={"content": junk})
    assert out["result"] == {"ok": False, "reason": "not-a-map"}
    assert out["file"] == junk


def test_save_write_failure_keeps_file_intact():
    src = page(make_map())
    for mode in ("write", "close"):
        out = call("saveToHandle", "__HANDLE__", src, make_map(),
                   handle={"content": src, "writeFails": mode})
        assert out["result"] == {"ok": False, "reason": "write-failed"}
        assert out["file"] == src
        assert out["writes"] == 0
        assert out["aborted"] is True


def test_save_write_failure_without_abort_still_reports_write_failed():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(),
               handle={"content": src, "writeFails": "write", "abort": "missing"})
    assert out["result"] == {"ok": False, "reason": "write-failed"}
    assert out["file"] == src


def test_save_write_failure_when_abort_throws_still_reports_write_failed():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(),
               handle={"content": src, "writeFails": "write", "abort": "throw"})
    assert out["result"] == {"ok": False, "reason": "write-failed"}
    assert out["aborted"] is True


def test_save_success_does_not_abort():
    src = page(make_map())
    out = call("saveToHandle", "__HANDLE__", src, make_map(), handle={"content": src})
    assert out["result"]["ok"] is True
    assert out["aborted"] is False


def obstacle(m, oid):
    return next(o for o in m["obstacles"] if o["id"] == oid)


def test_next_id_skips_ids_used_anywhere_in_the_file():
    m = make_map(execute=[{"solution_id": "s9"}], baseline={"obstacles": [{"id": "o7"}]})
    assert call("nextId", m, "s")["result"] == "s10"
    assert call("nextId", m, "o")["result"] == "o8"
    empty = make_map(obstacles=[], solutions=[])
    assert call("nextId", empty, "o")["result"] == "o1"


def test_add_obstacle():
    m = call("addObstacle", make_map(), "o3", "new")["result"]
    assert obstacle(m, "o3") == {
        "id": "o3", "text": "new", "whys": [], "root_cause": "", "solution_ids": []}


def test_add_why_appends_and_stops_after_root_cause():
    m = call("addWhy", make_map(), "o1", "w3")["result"]
    assert obstacle(m, "o1")["whys"] == ["w1", "w2", "w3"]
    marked = call("markRootCause", make_map(), "o1")["result"]
    m = call("addWhy", marked, "o1", "w3")["result"]
    assert obstacle(m, "o1")["whys"] == ["w1"]


def test_delete_why_and_root_cause():
    m = call("deleteWhy", make_map(), "o1", 0)["result"]
    assert obstacle(m, "o1")["whys"] == ["w2"]
    marked = call("markRootCause", make_map(), "o1")["result"]
    m = call("deleteRootCause", marked, "o1")["result"]
    assert obstacle(m, "o1")["root_cause"] == ""
    assert obstacle(m, "o1")["whys"] == ["w1"]


def test_set_item_text_for_each_kind():
    m = call("setItemText", make_map(), {"kind": "obstacle", "oid": "o1"}, "A")["result"]
    assert obstacle(m, "o1")["text"] == "A"
    m = call("setItemText", make_map(), {"kind": "why", "oid": "o1", "index": 1}, "W")["result"]
    assert obstacle(m, "o1")["whys"] == ["w1", "W"]
    m = call("setItemText", make_map(), {"kind": "root", "oid": "o1"}, "R")["result"]
    assert obstacle(m, "o1")["root_cause"] == "R"


def test_set_goal_replaces_all_goal_fields():
    goal = {"text": "t", "from": "", "to": "80%", "by": "Q2"}
    assert call("setGoal", make_map(), goal)["result"]["goal"] == goal


def test_editing_a_repeated_solution_edits_it_everywhere():
    m = call("setItemText", make_map(), {"kind": "solution", "sid": "s2"}, "changed")["result"]
    assert [s["text"] for s in m["solutions"] if s["id"] == "s2"] == ["changed"]
    assert call("repeatCount", m, "s2")["result"] == 2


def test_add_solution_with_and_without_obstacle():
    m = call("addSolution", make_map(), "o2", "s4", "four")["result"]
    assert {"id": "s4", "text": "four", "star": False} in m["solutions"]
    assert "s4" in obstacle(m, "o2")["solution_ids"]
    m = call("addSolution", make_map(), None, "s4", "four")["result"]
    assert "s4" in call("untiedSolutionIds", m)["result"]


def test_move_solution_between_obstacles():
    m = call("moveSolution", make_map(), "o1", "o2", "s1")["result"]
    assert obstacle(m, "o1")["solution_ids"] == ["s2"]
    assert obstacle(m, "o2")["solution_ids"] == ["s2", "s1"]


def test_move_solution_out_of_the_tray():
    m = call("moveSolution", make_map(), None, "o2", "s3")["result"]
    assert "s3" in obstacle(m, "o2")["solution_ids"]
    assert call("untiedSolutionIds", m)["result"] == []


def test_move_solution_onto_an_obstacle_that_has_it_does_not_repeat_it():
    m = call("moveSolution", make_map(), "o1", "o2", "s2")["result"]
    assert obstacle(m, "o1")["solution_ids"] == ["s1"]
    assert obstacle(m, "o2")["solution_ids"] == ["s2"]


def test_delete_solution_removes_it_from_the_map():
    m = call("deleteSolution", make_map(), "s3")["result"]
    assert all(s["id"] != "s3" for s in m["solutions"])
    assert call("untiedSolutionIds", m)["result"] == []


def test_panel_rows_ignore_ids_that_no_longer_exist():
    m = make_map(
        key_actions=[{"text": "k", "risk": "high", "solution_ids": ["s1", "gone"]}],
        execute=[
            {"solution_id": "gone", "first_move": "x", "owner": "y", "others_decide": ""},
            {"solution_id": "s2", "first_move": "m", "owner": "o", "others_decide": "d"},
        ],
    )
    rows = call("panelRows", m)["result"]
    assert rows["key_actions"] == [{"text": "k", "risk": "high", "solutions": ["one"]}]
    assert rows["execute"] == [
        {"solution": "two", "first_move": "m", "owner": "o", "others_decide": "d"}]


def test_item_exists_for_each_kind():
    m = call("markRootCause", make_map(), "o1")["result"]
    m["obstacles"][1]["solution_ids"].append("gone")
    present = [
        {"kind": "goal"},
        {"kind": "obstacle", "oid": "o1"},
        {"kind": "why", "oid": "o1", "index": 0},
        {"kind": "root", "oid": "o1"},
        {"kind": "solution", "oid": "o1", "sid": "s1"},
        {"kind": "solution", "sid": "s3"},
        {"kind": "missing", "oid": "o2", "sid": "gone"},
    ]
    absent = [
        {"kind": "obstacle", "oid": "o9"},
        {"kind": "why", "oid": "o1", "index": 1},
        {"kind": "why", "oid": "o9", "index": 0},
        {"kind": "root", "oid": "o2"},
        {"kind": "solution", "oid": "o1", "sid": "s9"},
        {"kind": "solution", "oid": "o2", "sid": "s1"},
        {"kind": "solution", "sid": "s9"},
        {"kind": "missing", "oid": "o1", "sid": "gone"},
    ]
    for ref in present:
        assert call("itemExists", m, ref)["result"] is True, ref
    for ref in absent:
        assert call("itemExists", m, ref)["result"] is False, ref


def test_item_exists_is_false_after_a_blank_new_item_is_removed():
    m = call("addWhy", make_map(), "o1", "")["result"]
    ref = {"kind": "why", "oid": "o1", "index": 2}
    assert call("itemExists", m, ref)["result"] is True
    m = call("deleteWhy", m, "o1", 2)["result"]
    assert call("itemExists", m, ref)["result"] is False


def test_close_warning_still_runs_when_the_commit_throws():
    assert call("shouldWarnOnClose", "__THROWS__", "__FALSE__")["result"] is True


def test_close_warning_follows_unsaved_changes_after_a_good_commit():
    assert call("shouldWarnOnClose", "__NOOP__", "__TRUE__")["result"] is True
    assert call("shouldWarnOnClose", "__NOOP__", "__FALSE__")["result"] is False


def test_move_copy_message_names_the_folder_and_file():
    out = call("moveCopyMessage", "/Users/pat/Goals/a-pat-map.html")["result"]
    assert out == ("Your browser should have saved a copy to Downloads. Move it into the Goals folder "
                   "as a-pat-map.html, replacing the old one.")


def test_move_copy_message_with_no_folder():
    out = call("moveCopyMessage", "/a-map.html")["result"]
    assert out == ("Your browser should have saved a copy to Downloads. Move it into the map's folder "
                   "as a-map.html, replacing the old one.")


def test_stale_copy_message_says_not_to_replace_the_newer_map():
    out = call("copyMessage", "/Users/pat/Goals/a-pat-map.html", "stale")["result"]
    assert out == ("Your browser should have saved a copy to Downloads. The map has newer changes, "
                   "so don't replace it. Put the copy in the Goals folder under another name, "
                   "such as a-pat-copy-map.html, and tell Claude.")
    assert "replacing" not in out


def test_stale_copy_name_stays_a_name_claude_skips():
    # A name ending in -map.html keeps the copy out of Claude's document reading.
    out = call("copyMessage", "/Goals/a-pat-map (1).html", "stale")["result"]
    assert "such as a-pat-copy-map.html," in out
    out = call("copyMessage", "/Goals/notes.html", "stale")["result"]
    assert "such as notes-copy-map.html," in out


def test_stale_copy_message_with_no_folder():
    out = call("copyMessage", "/a-map.html", "stale")["result"]
    assert "Put the copy in the map's folder under another name" in out


def test_other_refusals_keep_the_move_message():
    path = "/Users/pat/Goals/a-pat-map.html"
    move = call("moveCopyMessage", path)["result"]
    for reason in ("wrong-map", "not-a-map", "permission", "unreadable", "write-failed"):
        assert call("copyMessage", path, reason)["result"] == move, reason


def goal(**over):
    base = {"text": "t", "from": "", "to": "", "by": ""}
    base.update(over)
    return base


def test_goal_line_with_nothing_is_empty():
    assert call("goalLine", goal())["result"] == ""


def test_goal_line_with_only_by_reads_naturally():
    assert call("goalLine", goal(by="March"))["result"] == "By March"


def test_goal_line_with_every_part():
    out = call("goalLine", goal(**{"from": "40%", "to": "80%", "by": "Q2"}))["result"]
    assert out == "From 40% to 80% by Q2"


def test_goal_line_says_from_is_unknown_only_when_there_is_a_target():
    assert call("goalLine", goal(to="80%"))["result"] == "From: not known yet. To 80%"
    assert call("goalLine", goal(to="80%", by="Q2"))["result"] == "From: not known yet. To 80% by Q2"


def test_goal_line_with_from_and_no_target():
    assert call("goalLine", goal(**{"from": "40%"}))["result"] == "From 40%"
    assert call("goalLine", goal(**{"from": "40%", "by": "Q2"}))["result"] == "From 40%, by Q2"


def test_goal_line_with_from_and_target_only():
    assert call("goalLine", goal(**{"from": "40%", "to": "80%"}))["result"] == "From 40% to 80%"


def test_map_problem_is_null_for_a_good_map():
    assert call("mapProblem", make_map())["result"] is None
    empty = make_map(obstacles=[], solutions=[])
    assert call("mapProblem", empty)["result"] is None


def test_map_problem_passes_the_shipped_example():
    example = TEMPLATE.parent / "example-map.html"
    data = call("parseMapData", example.read_text())["result"]
    assert call("mapProblem", data)["result"] is None


def test_map_problem_refuses_data_that_is_not_a_map():
    for bad in (None, [], "text", 3):
        assert call("mapProblem", bad)["result"] == "The data in this file can't be read as a map."


def test_map_problem_refuses_an_empty_or_missing_map_id():
    assert call("mapProblem", make_map(map_id=""))["result"] == "The map has no id."
    m = make_map()
    del m["map_id"]
    assert call("mapProblem", m)["result"] == "The map has no id."


def test_map_problem_refuses_a_revision_that_is_not_a_number():
    assert call("mapProblem", make_map(revision="3"))["result"] == "The map has no revision number."


def test_map_problem_refuses_a_broken_goal():
    assert call("mapProblem", make_map(goal=None))["result"] == "The goal is missing."
    assert call("mapProblem", make_map(goal={"text": "t"}))["result"] == "The goal is missing its from."


def test_map_problem_names_the_obstacle_missing_its_whys():
    m = make_map()
    del m["obstacles"][1]["whys"]
    assert call("mapProblem", m)["result"] == "Obstacle 2 is missing its list of whys."


def test_map_problem_refuses_a_row_of_the_wrong_kind():
    assert call("mapProblem", make_map(solutions=[None]))["result"] == "Solution 1 is missing."
    m = make_map()
    m["obstacles"][0]["solution_ids"] = "s1"
    assert call("mapProblem", m)["result"] == "Obstacle 1 is missing its list of solutions."


def test_map_problem_refuses_each_missing_list():
    for field, label in (("obstacles", "obstacles"), ("solutions", "solutions"),
                         ("key_actions", "key actions"), ("execute", "execute rows")):
        m = make_map()
        del m[field]
        assert call("mapProblem", m)["result"] == "The map is missing its list of " + label + ".", field


def test_map_problem_checks_key_action_and_execute_rows():
    m = make_map(key_actions=[{"text": "k", "risk": "low"}])
    assert call("mapProblem", m)["result"] == "Key action 1 is missing its list of solutions."
    m = make_map(execute=[{"first_move": "x"}])
    assert call("mapProblem", m)["result"] == "Execute row 1 is missing its solution."


def test_map_problem_refuses_missing_feedback():
    m = make_map()
    del m["feedback"]
    assert call("mapProblem", m)["result"] == "The feedback section is missing."


def test_serialize_writes_the_six_character_escape():
    assert "\\u003c" in call("serializeMap", make_map(person="<b>"))["result"]


def test_refusal_copy_moved_into_the_folder_does_not_refuse_the_page():
    # The copy keeps the page's revision, so the file can't look newer than this page.
    m = make_map(revision=3, person="Edited")
    copy_html = call("replaceMapData", page(make_map(revision=3)), m)["result"]
    assert call("checkTarget", copy_html, m)["result"] == {"ok": True}


def test_refusal_copy_leaves_a_newer_file_refused():
    # A copy changes nothing on the page, so a stale refusal stays until the page reloads.
    m = make_map(revision=3)
    out = call("checkTarget", page(make_map(revision=4)), m)["result"]
    assert out == {"ok": False, "reason": "stale"}


def test_side_of_alternates_by_obstacle_order():
    # The first obstacle is odd, so it goes left.
    sides = [call("sideOf", i)["result"] for i in range(4)]
    assert sides == ["left", "right", "left", "right"]


def test_solutions_on_returns_the_solutions_in_order():
    out = call("solutionsOn", make_map(), "o1")["result"]
    assert [s["id"] for s in out] == ["s1", "s2"]
    assert not any(s.get("missing") for s in out)


def test_solutions_on_keeps_an_id_with_no_solution_as_a_missing_item():
    m = make_map()
    m["obstacles"][1]["solution_ids"] = ["s2", "gone"]
    out = call("solutionsOn", m, "o2")["result"]
    assert [s["id"] for s in out] == ["s2", "gone"]
    assert out[1]["missing"] is True


def test_missing_item_can_be_deleted_from_its_obstacle():
    m = make_map()
    m["obstacles"][1]["solution_ids"] = ["s2", "gone"]
    m = call("deleteSolutionFromObstacle", m, "o2", "gone")["result"]
    assert call("solutionsOn", m, "o2")["result"] == [{"id": "s2", "text": "two", "star": True}]


def test_panel_rows_still_ignore_an_id_drawn_as_missing_on_the_map():
    m = make_map(key_actions=[{"text": "k", "risk": "low", "solution_ids": ["gone"]}])
    m["obstacles"][1]["solution_ids"] = ["gone"]
    assert call("panelRows", m)["result"]["key_actions"][0]["solutions"] == []


def test_fit_scale_shrinks_to_the_tighter_of_width_and_height():
    assert call("fitScale", 2000, 500, 1000, 1000, 0.1)["result"] == 0.5
    assert call("fitScale", 500, 2000, 1000, 1000, 0.1)["result"] == 0.5


def test_fit_scale_never_enlarges():
    assert call("fitScale", 500, 500, 1000, 1000, 0.8)["result"] == 1


def test_fit_scale_stops_at_the_floor():
    assert call("fitScale", 4000, 500, 1000, 1000, 0.8)["result"] == 0.8


def test_step_scale_moves_by_a_tenth_and_stays_in_range():
    assert call("stepScale", 0.8, 1)["result"] == 0.9
    assert call("stepScale", 0.8, -1)["result"] == 0.7
    assert call("stepScale", 1.5, 1)["result"] == 1.5
    assert call("stepScale", 0.4, -1)["result"] == 0.4


def test_pick_message_names_file_and_folder():
    out = call("pickMessage", "/Users/pat/Goals/step%203-pat-map.html")["result"]
    assert out == "Pick step 3-pat-map.html in the Goals folder."


def test_pick_message_with_no_folder():
    assert call("pickMessage", "/m-map.html")["result"] == "Pick m-map.html."


def test_file_name_survives_a_bad_escape():
    assert call("fileName", "/a/100%-map.html")["result"] == "100%-map.html"


def test_file_name_falls_back_when_the_path_has_none():
    assert call("fileName", "/")["result"] == "map.html"


def test_copy_html_bumps_revision_in_the_copy_only():
    m = make_map(revision=4)
    out = call("copyHtml", page(m), m)["result"]
    assert call("parseMapData", out)["result"]["revision"] == 5
    assert m["revision"] == 4


# Where a solution sits in its chain

def rooted(**over):
    """o1 has two whys and a root cause, o2 is plain, and s2 sits on both."""
    m = make_map()
    m["obstacles"][0]["root_cause"] = "r"
    m["obstacles"][0].update(over)
    return m


def by_item(m, oid):
    """Where each solution sits in the chain, with the column counted as the last item."""
    out = call("solutionSpots", m, oid)["result"]
    items = [[s["id"] for s in item] for item in out["under"]]
    items[-1] += [s["id"] for s in out["tail"]]
    return items


def test_old_map_with_no_places_draws_solutions_at_the_end_of_the_chain():
    assert by_item(rooted(), "o1") == [[], [], [], ["s1", "s2"]]
    assert by_item(make_map(), "o1") == [[], [], ["s1", "s2"]]
    assert by_item(make_map(), "o2") == [["s2"]]


def test_a_placed_solution_draws_under_its_item_and_the_rest_stay_at_the_end():
    m = rooted(solution_at={"s1": "why:0"})
    assert by_item(m, "o1") == [[], ["s1"], [], ["s2"]]
    m = rooted(solution_at={"s1": "obstacle", "s2": "why:1"})
    assert by_item(m, "o1") == [["s1"], [], ["s2"], []]


def test_a_place_pointing_at_a_gone_why_draws_at_the_end_and_is_not_refused():
    m = rooted(solution_at={"s1": "why:7"})
    assert by_item(m, "o1") == [[], [], [], ["s1", "s2"]]
    assert call("mapProblem", m)["result"] is None


def test_places_of_the_wrong_kind_draw_at_the_end_and_are_not_refused():
    for bad in ("why:0", ["s1"], 3, None, {"s1": 4}, {"s1": "root"}, {"s1": "why:-1"}, {"s1": "why:x"},
                {"s1": "why:0 "}):
        m = rooted(solution_at=bad)
        assert by_item(m, "o1") == [[], [], [], ["s1", "s2"]], bad
        assert call("mapProblem", m)["result"] is None, bad


def test_place_for_each_kind_of_selected_item():
    assert call("placeForItem", {"kind": "obstacle", "oid": "o1"})["result"] == "obstacle"
    assert call("placeForItem", {"kind": "why", "oid": "o1", "index": 2})["result"] == "why:2"
    assert call("placeForItem", {"kind": "root", "oid": "o1"})["result"] is None


def test_add_solution_records_the_place():
    m = call("addSolution", rooted(), "o1", "s4", "four", "why:0")["result"]
    assert obstacle(m, "o1")["solution_at"] == {"s4": "why:0"}
    assert by_item(m, "o1") == [[], ["s4"], [], ["s1", "s2"]]


def test_add_solution_to_a_root_cause_records_no_place():
    m = call("addSolution", rooted(), "o1", "s4", "four", None)["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert by_item(m, "o1") == [[], [], [], ["s1", "s2", "s4"]]


def test_a_solution_on_a_plain_obstacle_stays_there_when_a_why_gets_added():
    m = call("addSolution", make_map(), "o2", "s4", "four", "obstacle")["result"]
    assert obstacle(m, "o2")["solution_at"] == {"s4": "obstacle"}
    m = call("addWhy", m, "o2", "because")["result"]
    assert by_item(m, "o2") == [["s4"], ["s2"]]


def test_a_stale_place_does_not_come_alive_when_a_why_gets_added():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s1": "why:2"}
    m = call("addWhy", m, "o1", "w3")["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert by_item(m, "o1") == [[], [], [], ["s1", "s2"]]


def test_move_solution_records_the_place_on_the_new_obstacle():
    m = rooted(solution_at={"s1": "why:0"})
    m = call("moveSolution", m, "o1", "o2", "s1", "obstacle")["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert obstacle(m, "o2")["solution_at"] == {"s1": "obstacle"}


def test_move_solution_out_of_the_tray_records_the_place():
    m = call("moveSolution", rooted(), None, "o1", "s3", "why:1")["result"]
    assert obstacle(m, "o1")["solution_at"] == {"s3": "why:1"}


def test_move_solution_to_a_root_cause_clears_the_place():
    m = rooted(solution_at={"s1": "why:0"})
    m = call("moveSolution", m, "o1", "o1", "s1", None)["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert by_item(m, "o1") == [[], [], [], ["s1", "s2"]]


def test_move_within_an_obstacle_changes_only_the_place():
    m = call("moveSolution", rooted(), "o1", "o1", "s1", "obstacle")["result"]
    o1 = obstacle(m, "o1")
    assert o1["solution_ids"] == ["s1", "s2"]
    assert o1["solution_at"] == {"s1": "obstacle"}
    assert call("repeatCount", m, "s1")["result"] == 1


def test_move_onto_an_obstacle_that_has_it_takes_the_new_place_without_repeating_it():
    m = rooted()
    m = call("moveSolution", m, "o2", "o1", "s2", "why:0")["result"]
    assert obstacle(m, "o1")["solution_ids"] == ["s1", "s2"]
    assert obstacle(m, "o1")["solution_at"] == {"s2": "why:0"}


def test_delete_why_sends_its_solutions_to_the_end_and_shifts_later_places_down():
    m = rooted(solution_at={"s1": "why:0", "s2": "why:1"})
    m = call("deleteWhy", m, "o1", 0)["result"]
    o1 = obstacle(m, "o1")
    assert o1["whys"] == ["w2"]
    assert o1["solution_at"] == {"s2": "why:0"}
    assert by_item(m, "o1") == [[], ["s2"], ["s1"]]


def test_delete_why_leaves_earlier_places_and_the_obstacle_place_alone():
    m = rooted(solution_at={"s1": "why:0", "s2": "obstacle"})
    m = call("deleteWhy", m, "o1", 1)["result"]
    assert obstacle(m, "o1")["solution_at"] == {"s1": "why:0", "s2": "obstacle"}


def test_delete_the_only_placed_why_removes_the_field():
    m = rooted(solution_at={"s1": "why:1"})
    m = call("deleteWhy", m, "o1", 1)["result"]
    assert "solution_at" not in obstacle(m, "o1")


def test_delete_why_on_a_map_with_no_places_adds_no_field():
    m = call("deleteWhy", make_map(), "o1", 0)["result"]
    assert "solution_at" not in obstacle(m, "o1")


def test_mark_root_cause_clears_places_on_that_why_only():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s1": "why:1", "s2": "why:0"}
    m = call("markRootCause", m, "o1")["result"]
    o1 = obstacle(m, "o1")
    assert o1["root_cause"] == "w2"
    assert o1["solution_at"] == {"s2": "why:0"}
    assert by_item(m, "o1") == [[], ["s2"], ["s1"]]


def test_mark_root_cause_without_whys_keeps_the_obstacle_place():
    m = make_map()
    m["obstacles"][1]["solution_at"] = {"s2": "obstacle"}
    m = call("markRootCause", m, "o2")["result"]
    assert obstacle(m, "o2")["solution_at"] == {"s2": "obstacle"}


def test_removing_a_solution_from_an_obstacle_removes_its_place():
    m = rooted(solution_at={"s1": "why:0"})
    m = call("deleteSolutionFromObstacle", m, "o1", "s1")["result"]
    assert "solution_at" not in obstacle(m, "o1")


def test_deleting_a_solution_removes_its_place_on_every_obstacle():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s2": "why:0"}
    m["obstacles"][1]["solution_at"] = {"s2": "obstacle"}
    m = call("deleteSolution", m, "s2")["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert "solution_at" not in obstacle(m, "o2")


def test_a_repeated_solution_has_its_own_place_on_each_obstacle():
    m = make_map()
    m = call("moveSolution", m, "o1", "o1", "s2", "why:0")["result"]
    assert by_item(m, "o1") == [[], ["s2"], ["s1"]]
    assert by_item(m, "o2") == [["s2"]]
    m = call("deleteSolutionFromObstacle", m, "o1", "s2")["result"]
    assert call("repeatCount", m, "s2")["result"] == 1
    assert by_item(m, "o2") == [["s2"]]


def test_places_do_not_change_the_counts():
    m = rooted(solution_at={"s1": "why:0", "s2": "obstacle"})
    assert call("untiedSolutionIds", m)["result"] == ["s3"]
    assert call("repeatCount", m, "s2")["result"] == 2


def test_places_survive_a_save():
    m = rooted(solution_at={"s1": "why:0"})
    src = page(m)
    out = call("saveToHandle", "__HANDLE__", src, m, handle={"content": src})
    assert out["result"]["ok"] is True
    assert obstacle(call("parseMapData", out["file"])["result"], "o1")["solution_at"] == {"s1": "why:0"}


def targets(m, sid, from_oid):
    return call("moveTargets", m, sid, from_oid)["result"]


def test_move_targets_list_every_item_and_the_end_on_every_other_obstacle():
    out = targets(rooted(), "s3", None)
    assert [(t["oid"], t["place"], t["kind"]) for t in out] == [
        ("o1", "obstacle", "obstacle"),
        ("o1", "why:0", "why"),
        ("o1", "why:1", "why"),
        ("o1", None, "end"),
        ("o2", "obstacle", "obstacle"),
        ("o2", None, "end"),
    ]
    assert [t["text"] for t in out] == ["a", "w1", "w2", "r", "b", "b"]
    assert [t["after"] for t in out if t["kind"] == "end"] == ["root", "obstacle"]


def test_move_targets_on_a_chain_with_no_root_cause_offer_the_last_why_and_the_end():
    out = targets(make_map(), "s3", None)
    o1 = [(t["place"], t["kind"]) for t in out if t["oid"] == "o1"]
    assert o1 == [("obstacle", "obstacle"), ("why:0", "why"), ("why:1", "why"), (None, "end")]
    assert [t["after"] for t in out if t["oid"] == "o1" and t["kind"] == "end"] == ["why"]


def test_a_column_solution_can_move_directly_under_the_last_why():
    m = make_map()
    places = [t["place"] for t in targets(m, "s1", "o1") if t["oid"] == "o1"]
    assert "why:1" in places
    assert None not in places
    m = call("moveSolution", m, "o1", "o1", "s1", "why:1")["result"]
    assert spots(m, "o1") == ([[], [], ["s1"]], ["s2"])


def test_a_column_solution_can_move_directly_under_a_plain_obstacle():
    m = make_map()
    assert [t["place"] for t in targets(m, "s2", "o2")] == ["obstacle"]
    m = call("moveSolution", m, "o2", "o2", "s2", "obstacle")["result"]
    assert spots(m, "o2") == ([["s2"]], [])


def test_a_solution_under_the_last_why_can_move_back_to_the_column():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s1": "why:1"}
    places = [t["place"] for t in targets(m, "s1", "o1") if t["oid"] == "o1"]
    assert None in places
    assert "why:1" not in places
    m = call("moveSolution", m, "o1", "o1", "s1", None)["result"]
    assert "solution_at" not in obstacle(m, "o1")
    assert spots(m, "o1") == ([[], [], []], ["s1", "s2"])


def test_a_solution_under_a_plain_obstacle_can_move_back_to_the_column():
    m = make_map()
    m["obstacles"][1]["solution_at"] = {"s2": "obstacle"}
    assert [t["place"] for t in targets(m, "s2", "o2")] == [None]
    m = call("moveSolution", m, "o2", "o2", "s2", None)["result"]
    assert spots(m, "o2") == ([[]], ["s2"])


def names(m, sid, from_oid, oid):
    return [call("moveTargetName", t)["result"] for t in targets(m, sid, from_oid) if t["oid"] == oid]


def test_move_target_names_tell_under_this_item_from_at_the_end():
    assert names(rooted(), "s3", None, "o1") == [
        "Directly under the obstacle",
        "Directly under the why: w1",
        "Directly under the why: w2",
        "At the end, past the root cause: r",
    ]
    assert names(make_map(), "s3", None, "o1") == [
        "Directly under the obstacle",
        "Directly under the why: w1",
        "Directly under the why: w2",
        "At the end, past the last why",
    ]
    assert names(make_map(), "s3", None, "o2") == [
        "Directly under the obstacle",
        "At the end, past the obstacle",
    ]


def test_the_page_logic_has_no_solutions_by_item():
    assert "solutionsByItem" not in logic_source()


def test_move_targets_leave_out_where_the_solution_is_now():
    out = targets(rooted(solution_at={"s1": "why:0"}), "s1", "o1")
    assert ("o1", "why:0") not in [(t["oid"], t["place"]) for t in out]
    assert ("o1", None) in [(t["oid"], t["place"]) for t in out]
    out = targets(rooted(), "s1", "o1")
    assert ("o1", None) not in [(t["oid"], t["place"]) for t in out]
    assert ("o1", "obstacle") in [(t["oid"], t["place"]) for t in out]


def test_move_targets_leave_out_other_obstacles_that_already_hold_it():
    out = targets(rooted(), "s2", "o1")
    assert {t["oid"] for t in out} == {"o1"}


def test_move_targets_treat_a_stale_place_as_the_end_of_the_chain():
    out = targets(rooted(solution_at={"s1": "why:9"}), "s1", "o1")
    assert ("o1", None) not in [(t["oid"], t["place"]) for t in out]


def test_row_layout_with_no_solutions_is_just_the_tallest_box():
    out = call("rowLayout", [40, 60], [[], []], 10)["result"]
    assert out["height"] == 60
    assert out["lineY"] == 30
    assert [i["top"] for i in out["items"]] == [10, 0]
    assert [i["solutionTops"] for i in out["items"]] == [[], []]


def test_row_layout_puts_solutions_under_their_own_item():
    out = call("rowLayout", [40, 60, 40], [[], [30, 20], []], 10)["result"]
    assert out["lineY"] == 30
    assert out["items"][1]["solutionTops"] == [70, 110]
    assert out["height"] == 130


def test_row_layout_height_covers_the_tallest_column_even_under_a_short_box():
    out = call("rowLayout", [40, 100], [[90], []], 10)["result"]
    # The 40px box sits centered on the 100px one, so its stack starts at 80.
    assert out["items"][0]["solutionTops"] == [80]
    assert out["height"] == 170


def test_row_layout_never_lets_boxes_in_a_column_touch():
    chain = [40, 90, 55]
    stacks = [[70, 25], [33], [60, 60, 60]]
    gap = 10
    out = call("rowLayout", chain, stacks, gap)["result"]
    for item, chain_h, stack in zip(out["items"], chain, stacks):
        bottom = item["top"] + chain_h
        for top, h in zip(item["solutionTops"], stack):
            assert top == bottom + gap
            bottom = top + h
        assert bottom <= out["height"]


# Solutions with no place stay in the column past the end of the chain

def spots(m, oid):
    out = call("solutionSpots", m, oid)["result"]
    return [[s["id"] for s in item] for item in out["under"]], [s["id"] for s in out["tail"]]


def test_solutions_with_no_place_go_in_the_tail_column():
    assert spots(rooted(), "o1") == ([[], [], [], []], ["s1", "s2"])
    assert spots(make_map(), "o2") == ([[]], ["s2"])


def test_a_recorded_place_draws_under_its_item_and_not_in_the_tail():
    m = rooted(solution_at={"s1": "why:0"})
    assert spots(m, "o1") == ([[], ["s1"], [], []], ["s2"])


def test_a_place_on_the_last_item_still_draws_under_it():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s1": "why:1"}
    m["obstacles"][1]["solution_at"] = {"s2": "obstacle"}
    assert spots(m, "o1") == ([[], [], ["s1"]], ["s2"])
    assert spots(m, "o2") == ([["s2"]], [])


def test_a_place_that_points_at_nothing_goes_in_the_tail():
    for bad in ({"s1": "why:7"}, {"s1": "root"}, {"s1": 4}, "why:0", ["s1"], None):
        assert spots(rooted(solution_at=bad), "o1") == ([[], [], [], []], ["s1", "s2"]), bad


def test_a_missing_solution_keeps_its_spot_and_its_mark():
    m = rooted(solution_ids=["gone", "lost"], solution_at={"gone": "why:0"})
    out = call("solutionSpots", m, "o1")["result"]
    assert out["under"][1] == [{"id": "gone", "missing": True}]
    assert out["tail"] == [{"id": "lost", "missing": True}]


def test_solution_spots_for_an_unknown_obstacle_is_empty():
    assert call("solutionSpots", make_map(), "o9")["result"] == {"under": [], "tail": []}


def test_a_solution_added_on_a_root_cause_joins_the_tail():
    m = call("addSolution", rooted(), "o1", "s4", "four", None)["result"]
    assert spots(m, "o1") == ([[], [], [], []], ["s1", "s2", "s4"])


def test_marking_the_last_why_as_root_cause_sends_its_solutions_to_the_tail():
    m = make_map()
    m["obstacles"][0]["solution_at"] = {"s1": "why:1", "s2": "why:0"}
    m = call("markRootCause", m, "o1")["result"]
    assert spots(m, "o1") == ([[], ["s2"], []], ["s1"])


def test_deleting_a_placed_why_sends_its_solutions_to_the_tail():
    m = rooted(solution_at={"s1": "why:0"})
    m = call("deleteWhy", m, "o1", 0)["result"]
    assert spots(m, "o1") == ([[], [], []], ["s1", "s2"])


def test_row_layout_with_only_a_tail_matches_the_old_row():
    # The old row: height is the taller of chain and tail, and both center on one line.
    out = call("rowLayout", [40, 60], [[], []], 10, [50, 50, 50])["result"]
    assert out["height"] == 170
    assert out["lineY"] == 85
    assert [i["top"] for i in out["items"]] == [65, 55]
    assert out["tailTops"] == [0, 60, 120]
    out = call("rowLayout", [40, 60], [[], []], 10, [30])["result"]
    assert out["height"] == 60
    assert out["lineY"] == 30
    assert out["tailTops"] == [15]


def test_row_layout_with_no_tail_has_no_tail_tops():
    assert call("rowLayout", [40], [[]], 10)["result"]["tailTops"] == []
    assert call("rowLayout", [40], [[]], 10, [])["result"]["height"] == 40


def test_row_layout_makes_room_for_a_tail_and_a_stack_together():
    chain = [40, 60]
    stacks = [[100], []]
    tail = [50, 50, 50]
    gap = 10
    out = call("rowLayout", chain, stacks, gap, tail)["result"]
    # The tail reaches 85 above the line. The stack reaches 20 + 10 + 100 below it.
    assert out["lineY"] == 85
    assert out["height"] == 215
    assert out["tailTops"] == [0, 60, 120]
    assert out["items"][0]["solutionTops"] == [115]
    assert out["items"][0]["top"] == 65
