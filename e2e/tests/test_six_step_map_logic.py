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


def item(id, text="", children=(), solutions=(), root=False):
    return {"id": id, "text": text, "root_cause": root,
            "solution_ids": list(solutions), "children": list(children)}


def make_map(**over):
    base = {
        "map_id": "m-1",
        "revision": 1,
        "person": "Pat",
        "goal": {"text": "g"},
        "obstacles": [
            item("o1", "a", [item("o3", "w1", [item("o4", "w2")])], ["s1", "s2"]),
            item("o2", "b", solutions=["s2"]),
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
    m = call("deleteItem", make_map(), "o1")["result"]
    assert [o["id"] for o in m["obstacles"]] == ["o2"]
    untied = call("untiedSolutionIds", m)["result"]
    assert "s1" in untied
    assert "s2" not in untied
    assert len(m["solutions"]) == 3


def test_set_root_cause_marks_an_item_with_no_children():
    m = call("setRootCause", make_map(), "o4", True)["result"]
    assert obstacle(m, "o4")["root_cause"] is True
    assert obstacle(m, "o3")["root_cause"] is False


def test_a_top_level_item_with_no_children_can_be_a_root_cause():
    m = call("setRootCause", make_map(), "o2", True)["result"]
    assert m["obstacles"][1]["root_cause"] is True


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


# The page says what it last loaded or wrote, so a file Claude rewrote can't slip past on its revision.

def test_save_refuses_a_lower_revision_with_other_content():
    # Page at rev 3, Claude read rev 1 and wrote rev 2.
    saved = make_map(revision=3, person="Page")
    claude = page(make_map(revision=2, person="Claude"))
    tab = make_map(revision=3, person="Edited")
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), handle={"content": claude})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == claude
    assert out["writes"] == 0


def test_save_refuses_the_same_revision_with_other_content():
    saved = make_map(revision=2, person="Page")
    claude = page(make_map(revision=2, person="Claude"))
    tab = make_map(revision=2, person="Edited")
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), handle={"content": claude})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == claude
    assert out["writes"] == 0


def test_connect_refuses_the_same_revision_with_other_content():
    saved = make_map(revision=2, person="Page")
    claude = page(make_map(revision=2, person="Claude"))
    out = call("connectToHandle", "__HANDLE__", saved, json.dumps(saved), handle={"content": claude})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == claude
    assert out["writes"] == 0


def test_save_with_the_file_the_page_knows_goes_through():
    saved = make_map(revision=2)
    tab = make_map(revision=2, person="Edited")
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), handle={"content": page(saved)})
    assert out["result"]["ok"] is True
    assert out["writes"] == 1
    assert call("parseMapData", out["file"])["result"]["person"] == "Edited"


def test_baseline_only_change_is_not_refused_when_the_page_says_what_it_knows():
    saved = make_map(revision=2, baseline={"person": "Old"})
    moved = {"person": "Read by Claude"}
    tab = make_map(revision=2, person="Edited", baseline={"person": "Old"})
    file_html = page(make_map(revision=2, baseline=moved))
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), handle={"content": file_html})
    assert out["result"] == {"ok": True, "revision": 3, "baseline": moved}
    assert call("parseMapData", out["file"])["result"]["baseline"] == moved
    assert call("connectToHandle", "__HANDLE__", saved, json.dumps(saved),
                handle={"content": file_html})["result"] == {"ok": True}


def test_formatting_and_key_order_do_not_count_as_a_change():
    saved = make_map(revision=2)
    reordered = {k: saved[k] for k in reversed(list(saved))}
    reordered["goal"] = {k: saved["goal"][k] for k in reversed(list(saved["goal"]))}
    file_html = page(make_map()).replace(
        json.dumps(make_map()), json.dumps(reordered, indent=2))
    assert call("parseMapData", file_html)["result"]["revision"] == 2
    out = call("connectToHandle", "__HANDLE__", saved, json.dumps(saved), handle={"content": file_html})
    assert out["result"] == {"ok": True}


def test_array_order_still_counts_as_a_change():
    saved = make_map(revision=2)
    moved = make_map(revision=2)
    moved["obstacles"].reverse()
    out = call("connectToHandle", "__HANDLE__", saved, json.dumps(saved), handle={"content": page(moved)})
    assert out["result"] == {"ok": False, "reason": "stale"}


def test_a_nested_baseline_field_is_still_content():
    # Only the top-level baseline is left out of the comparison.
    saved = make_map(revision=2, goal={"text": "g", "baseline": "40%"})
    other = make_map(revision=2, goal={"text": "g", "baseline": "50%"})
    out = call("connectToHandle", "__HANDLE__", saved, json.dumps(saved), handle={"content": page(other)})
    assert out["result"] == {"ok": False, "reason": "stale"}


def test_other_refusals_come_before_the_comparison():
    saved = make_map(revision=2)
    src = page(saved)
    cases = [
        ({"content": page(make_map(map_id="other"))}, "wrong-map"),
        ({"content": "not a map at all"}, "not-a-map"),
        ({"content": src, "permission": "denied"}, "permission"),
        ({"content": src, "permission": "throw"}, "permission"),
        ({"content": src, "getFileFails": True}, "unreadable"),
    ]
    for handle, reason in cases:
        out = call("saveToHandle", "__HANDLE__", src, saved, json.dumps(saved), handle=handle)
        assert out["result"] == {"ok": False, "reason": reason}, handle
        assert out["writes"] == 0


def test_write_failure_with_a_known_file_keeps_the_file_intact():
    saved = make_map(revision=2)
    src = page(saved)
    out = call("saveToHandle", "__HANDLE__", src, make_map(revision=2, person="Edited"), json.dumps(saved),
               handle={"content": src, "writeFails": "close"})
    assert out["result"] == {"ok": False, "reason": "write-failed"}
    assert out["file"] == src


def test_a_copy_the_page_made_counts_as_known():
    # The person moved the page's own copy over the file, so nothing of Claude's is at risk.
    saved = make_map(revision=2)
    copied = make_map(revision=2, person="In the copy")
    file_html = page(copied)
    tab = make_map(revision=2, person="After the copy")
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), json.dumps(copied),
               handle={"content": file_html})
    assert out["result"]["ok"] is True
    assert call("connectToHandle", "__HANDLE__", copied, json.dumps(saved), json.dumps(copied),
                handle={"content": file_html})["result"] == {"ok": True}


def test_a_copy_the_page_made_does_not_excuse_other_content():
    saved = make_map(revision=2)
    copied = make_map(revision=2, person="In the copy")
    claude = page(make_map(revision=2, person="Claude"))
    tab = make_map(revision=2, person="Edited")
    out = call("saveToHandle", "__HANDLE__", page(saved), tab, json.dumps(saved), json.dumps(copied),
               handle={"content": claude})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == claude


def all_items(items):
    for it in items:
        yield it
        yield from all_items(it["children"])


def obstacle(m, oid):
    return next(o for o in all_items(m["obstacles"]) if o["id"] == oid)


def test_next_id_skips_ids_used_anywhere_in_the_file():
    m = make_map(execute=[{"solution_id": "s9"}], baseline={"obstacles": [{"id": "o7"}]})
    assert call("nextId", m, "s")["result"] == "s10"
    assert call("nextId", m, "o")["result"] == "o8"
    empty = make_map(obstacles=[], solutions=[])
    assert call("nextId", empty, "o")["result"] == "o1"


def test_add_obstacle():
    m = call("addObstacle", make_map(), "o5", "new")["result"]
    assert m["obstacles"][-1] == {
        "id": "o5", "text": "new", "root_cause": False, "solution_ids": [], "children": []}


def test_set_item_text_at_any_depth():
    m = call("setItemText", make_map(), {"kind": "obstacle", "oid": "o1"}, "A")["result"]
    assert obstacle(m, "o1")["text"] == "A"
    m = call("setItemText", make_map(), {"kind": "obstacle", "oid": "o4"}, "W")["result"]
    assert obstacle(m, "o4")["text"] == "W"
    assert obstacle(m, "o3")["text"] == "w1"


def test_set_goal_replaces_the_goal():
    goal = {"text": "80% attendance by Q2, up from 40%"}
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
    assert call("repeatCount", m, "s1")["result"] == 1
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
    assert rows["key_actions"] == [{"text": "k", "risk": "high", "solutions": ["one (1)"]}]
    assert rows["execute"] == [
        {"solution": "two (1, 2)", "first_move": "m", "owner": "o", "others_decide": "d"}]


def test_item_exists_for_each_kind():
    m = make_map()
    m["obstacles"][1]["solution_ids"].append("gone")
    obstacle(m, "o4")["solution_ids"].append("s3")
    present = [
        {"kind": "goal"},
        {"kind": "obstacle", "oid": "o1"},
        {"kind": "obstacle", "oid": "o4"},
        {"kind": "solution", "oid": "o1", "sid": "s1"},
        {"kind": "solution", "oid": "o4", "sid": "s3"},
        {"kind": "solution", "sid": "s3"},
        {"kind": "missing", "oid": "o2", "sid": "gone"},
    ]
    absent = [
        {"kind": "obstacle", "oid": "o9"},
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
    m = call("addChild", make_map(), "o4", "o5", "")["result"]
    ref = {"kind": "obstacle", "oid": "o5"}
    assert call("itemExists", m, ref)["result"] is True
    m = call("deleteItem", m, "o5")["result"]
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
    assert call("mapProblem", make_map(goal={}))["result"] == "The goal is missing its text."
    assert call("mapProblem", make_map(goal={"text": 3}))["result"] == "The goal is missing its text."


def test_map_with_only_goal_text_passes_the_shape_check():
    assert call("mapProblem", make_map(goal={"text": "80% attendance by Q2, up from 40%"}))["result"] is None


def test_the_logic_block_has_no_goal_line():
    assert "goalLine" not in TEMPLATE.read_text()


def test_map_problem_names_the_obstacle_missing_its_children():
    m = make_map()
    del m["obstacles"][1]["children"]
    assert call("mapProblem", m)["result"] == "Obstacle 2 is missing its list of sub-obstacles."


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
    assert out == "Choose step 3-pat-map.html in the Goals folder."


def test_pick_message_with_no_folder():
    assert call("pickMessage", "/m-map.html")["result"] == "Choose m-map.html."


def test_file_name_survives_a_bad_escape():
    assert call("fileName", "/a/100%-map.html")["result"] == "100%-map.html"


def test_file_name_falls_back_when_the_path_has_none():
    assert call("fileName", "/")["result"] == "map.html"


def test_copy_html_bumps_revision_in_the_copy_only():
    m = make_map(revision=4)
    out = call("copyHtml", page(m), m)["result"]
    assert call("parseMapData", out)["result"]["revision"] == 5
    assert m["revision"] == 4


# Labels: computed from position, never stored

def labeled_tree():
    return make_map(obstacles=[
        item("o1", "a", [
            item("o3", "b"),
            item("o4", "c", [
                item("o5", "d"),
                item("o6", "e", [item("o7", "f")]),
            ]),
        ]),
        item("o2", "g"),
    ])


def test_item_labels_alternate_by_depth():
    assert call("itemLabels", labeled_tree())["result"] == {
        "o1": "1", "o2": "2", "o3": "1A", "o4": "1B", "o5": "1B1", "o6": "1B2", "o7": "1B2A"}


def test_item_labels_past_z():
    m = make_map(obstacles=[item("o1", "a", [item("k%d" % i) for i in range(28)])], solutions=[])
    labels = call("itemLabels", m)["result"]
    assert labels["k25"] == "1Z"
    assert labels["k26"] == "1AA"
    assert labels["k27"] == "1AB"


def test_item_labels_past_z_at_a_deeper_letter_level():
    kids = [item("k%d" % i) for i in range(53)]
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b", [item("o3", "c", kids)])])], solutions=[])
    labels = call("itemLabels", m)["result"]
    assert labels["o3"] == "1A1"
    assert labels["k26"] == "1A1AA"
    assert labels["k51"] == "1A1AZ"
    assert labels["k52"] == "1A1BA"


def test_labels_are_never_stored_and_later_siblings_renumber():
    m = labeled_tree()
    m = call("deleteItem", m, "o5")["result"]
    assert "label" not in json.dumps(m)
    assert call("itemLabels", m)["result"]["o6"] == "1B1"
    assert call("itemLabels", m)["result"]["o7"] == "1B1A"


# Adding and removing branches

def test_add_child_goes_under_the_parent_at_any_depth():
    m = call("addChild", labeled_tree(), "o7", "o8", "new")["result"]
    assert obstacle(m, "o7")["children"] == [item("o8", "new")]
    assert call("itemLabels", m)["result"]["o8"] == "1B2A1"


def test_add_child_to_an_unknown_item_changes_nothing():
    m = labeled_tree()
    assert call("addChild", m, "nope", "o8", "new")["result"] == m


def test_delete_item_removes_the_branch_and_returns_lone_solutions_to_the_tray():
    m = make_map(obstacles=[
        item("o1", "a", [item("o2", "b", [item("o3", "c", solutions=["s1"])], ["s2"])]),
    ], solutions=[{"id": "s1", "text": "one"}, {"id": "s2", "text": "two"}])
    m = call("deleteItem", m, "o2")["result"]
    assert m["obstacles"] == [item("o1", "a")]
    assert len(m["solutions"]) == 2
    assert call("untiedSolutionIds", m)["result"] == ["s1", "s2"]


def test_delete_item_keeps_a_solution_tied_elsewhere():
    m = make_map(obstacles=[
        item("o1", "a", [item("o2", "b", solutions=["s1"])]),
        item("o3", "c", [item("o4", "d", solutions=["s1"])]),
    ], solutions=[{"id": "s1", "text": "one"}])
    m = call("deleteItem", m, "o1")["result"]
    assert call("untiedSolutionIds", m)["result"] == []
    assert call("repeatCount", m, "s1")["result"] == 1


def test_delete_a_top_level_item():
    m = call("deleteItem", make_map(), "o1")["result"]
    assert [o["id"] for o in m["obstacles"]] == ["o2"]


def test_sub_item_count_counts_everything_under_an_item():
    m = labeled_tree()
    assert call("subItemCount", m, "o1")["result"] == 5
    assert call("subItemCount", m, "o4")["result"] == 3
    assert call("subItemCount", m, "o7")["result"] == 0


def test_root_cause_cannot_have_children():
    # A root cause refuses a child.
    m = call("setRootCause", labeled_tree(), "o5", True)["result"]
    assert obstacle(m, "o5")["root_cause"] is True
    assert call("addChild", m, "o5", "o8", "new")["result"] == m
    # An item with children refuses to become a root cause.
    m = call("setRootCause", labeled_tree(), "o4", True)["result"]
    assert obstacle(m, "o4")["root_cause"] is False


def test_unmarking_a_root_cause_lets_it_take_children_again():
    m = call("setRootCause", labeled_tree(), "o5", True)["result"]
    m = call("setRootCause", m, "o5", False)["result"]
    assert obstacle(m, "o5")["root_cause"] is False
    m = call("addChild", m, "o5", "o8", "new")["result"]
    assert [c["id"] for c in obstacle(m, "o5")["children"]] == ["o8"]


def test_an_obstacle_can_have_several_root_causes_in_different_branches():
    m = call("setRootCause", labeled_tree(), "o3", True)["result"]
    m = call("setRootCause", m, "o5", True)["result"]
    assert call("mapProblem", m)["result"] is None


def test_a_tree_survives_a_save():
    m = labeled_tree()
    src = page(m)
    out = call("saveToHandle", "__HANDLE__", src, m, json.dumps(m), handle={"content": src})
    assert out["result"]["ok"] is True
    assert call("parseMapData", out["file"])["result"]["obstacles"] == m["obstacles"]


def test_a_file_changed_deep_in_the_tree_is_refused_as_stale():
    saved = labeled_tree()
    other = labeled_tree()
    obstacle(other, "o7")["text"] = "Claude changed this"
    src = page(other)
    out = call("saveToHandle", "__HANDLE__", page(saved), saved, json.dumps(saved), handle={"content": src})
    assert out["result"] == {"ok": False, "reason": "stale"}
    assert out["file"] == src


# Solutions anywhere in the tree

def on_two_levels():
    return make_map(obstacles=[
        item("o1", "a", [item("o2", "b", solutions=["s1"]), item("o3", "c", solutions=["s1", "s2"])]),
        item("o4", "d", [item("o5", "e", [item("o6", "f", solutions=["s1"])])]),
    ], solutions=[{"id": "s1", "text": "one"}, {"id": "s2", "text": "two"}, {"id": "s3", "text": "three"}])


def test_repeat_count_covers_the_whole_tree():
    m = on_two_levels()
    assert call("repeatCount", m, "s1")["result"] == 3
    assert call("repeatCount", m, "s2")["result"] == 1
    assert call("repeatCount", m, "s3")["result"] == 0
    assert call("untiedSolutionIds", m)["result"] == ["s3"]


def test_removing_a_repeated_solution_from_one_item_leaves_the_others():
    m = call("deleteSolutionFromObstacle", on_two_levels(), "o6", "s1")["result"]
    assert obstacle(m, "o6")["solution_ids"] == []
    assert obstacle(m, "o2")["solution_ids"] == ["s1"]
    assert call("repeatCount", m, "s1")["result"] == 2


def test_deleting_a_solution_removes_it_at_every_depth():
    m = call("deleteSolution", on_two_levels(), "s1")["result"]
    assert call("repeatCount", m, "s1")["result"] == 0
    assert obstacle(m, "o3")["solution_ids"] == ["s2"]
    assert all(s["id"] != "s1" for s in m["solutions"])


def test_move_solution_between_items_at_different_depths():
    m = call("moveSolution", on_two_levels(), "o3", "o6", "s2")["result"]
    assert obstacle(m, "o3")["solution_ids"] == ["s1"]
    assert obstacle(m, "o6")["solution_ids"] == ["s1", "s2"]


def test_move_targets_list_every_item_by_label_and_text():
    m = make_map(obstacles=[
        item("o1", "a", [item("o2", "b", solutions=["s1"]), item("o3", "c")]),
        item("o4", "d"),
    ], solutions=[{"id": "s1", "text": "one"}])
    targets = call("moveTargets", m, "s1")["result"]
    assert [t["id"] for t in targets] == ["o1", "o3", "o4"]
    assert [call("moveTargetName", t)["result"] for t in targets] == ["1 a", "1B c", "2 d"]


def test_move_targets_from_the_tray_list_every_item():
    targets = call("moveTargets", make_map(), "s3")["result"]
    assert [t["id"] for t in targets] == ["o1", "o3", "o4", "o2"]


def test_move_targets_leave_out_every_item_that_holds_it():
    assert [t["id"] for t in call("moveTargets", on_two_levels(), "s1")["result"]] == ["o1", "o4", "o5"]


def test_solutions_on_finds_an_item_at_depth():
    assert [s["id"] for s in call("solutionsOn", on_two_levels(), "o3")["result"]] == ["s1", "s2"]


def test_panel_rows_name_the_items_a_solution_sits_on_by_label():
    m = on_two_levels()
    m["key_actions"] = [{"text": "k", "risk": "low", "solution_ids": ["s1", "s3"]}]
    m["execute"] = [{"solution_id": "s2", "first_move": "m", "owner": "o", "others_decide": ""}]
    rows = call("panelRows", m)["result"]
    assert rows["key_actions"][0]["solutions"] == ["one (1A, 1B, 2A1)", "three"]
    assert rows["execute"][0]["solution"] == "two (1B)"


# Shape check

def test_shape_check_rejects_old_shape():
    m = make_map(obstacles=[
        {"id": "o1", "text": "a", "whys": ["w"], "root_cause": "r", "solution_ids": []}])
    problem = call("mapProblem", m)["result"]
    assert problem.startswith("Obstacle 1 ")
    assert "old" in problem


def test_shape_check_rejects_a_new_item_with_an_old_field():
    m = make_map()
    m["obstacles"][1]["whys"] = ["w"]
    assert "Obstacle 2 " in call("mapProblem", m)["result"]
    m = make_map()
    obstacle(m, "o4")["solution_at"] = {"s1": "why:0"}
    assert "Obstacle 1A1 " in call("mapProblem", m)["result"]


def test_shape_check_rejects_a_bad_child_at_depth():
    m = labeled_tree()
    del obstacle(m, "o7")["children"]
    assert call("mapProblem", m)["result"] == "Obstacle 1B2A is missing its list of sub-obstacles."
    m = labeled_tree()
    obstacle(m, "o6")["children"] = [None]
    assert call("mapProblem", m)["result"] == "Obstacle 1B2A is missing."
    m = labeled_tree()
    obstacle(m, "o5")["text"] = 3
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 is missing its text."
    m = labeled_tree()
    obstacle(m, "o5")["solution_ids"] = "s1"
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 is missing its list of solutions."
    m = labeled_tree()
    obstacle(m, "o5")["root_cause"] = "because"
    assert "Obstacle 1B1 " in call("mapProblem", m)["result"]
    assert "root cause" in call("mapProblem", m)["result"]
    m = labeled_tree()
    obstacle(m, "o5")["id"] = ""
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 is missing its id."


def test_shape_check_rejects_duplicate_ids():
    m = labeled_tree()
    obstacle(m, "o7")["id"] = "o2"
    assert call("mapProblem", m)["result"] == "Obstacles 1B2A and 2 both use the id o2."


def test_shape_check_is_not_fooled_by_an_id_like_a_built_in_name():
    m = make_map(obstacles=[item("constructor", "a"), item("__proto__", "b")], solutions=[])
    assert call("mapProblem", m)["result"] is None


def test_shape_check_rejects_a_root_cause_with_children():
    m = labeled_tree()
    obstacle(m, "o4")["root_cause"] = True
    assert call("mapProblem", m)["result"] == "Obstacle 1B is a root cause, so it can't have sub-obstacles."


# Sides

def test_sides_put_first_half_on_the_right():
    def sides(count):
        return [call("sideOf", i, count)["result"] for i in range(count)]
    assert sides(1) == ["right"]
    assert sides(2) == ["right", "left"]
    assert sides(3) == ["right", "right", "left"]
    assert sides(6) == ["right", "right", "right", "left", "left", "left"]
    assert sides(7) == ["right", "right", "right", "right", "left", "left", "left"]


# Wide layout. Every test here checks real positions, with boxes of uneven heights.

SIZES = {"boxW": 170, "goalW": 220, "goalH": 76, "colGap": 26, "goalGap": 56, "rowGap": 18, "stackGap": 8, "pad": 14}


def uneven_heights(m):
    rows = call("drawnRows", m)["result"]
    return {r["key"]: 30 + (i * 37) % 90 for i, r in enumerate(rows)}


def wide(m, heights=None):
    return call("wideLayout", m, heights or uneven_heights(m), SIZES)["result"]


def overlaps(rects):
    found = []
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            apart = (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"]
                     or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])
            if not apart:
                found.append((a["key"], b["key"]))
    return found


def wide_rects(layout):
    rects = [{"key": b["key"], "x": b["x"], "y": b["y"], "w": SIZES["boxW"], "h": b["height"]}
             for b in layout["boxes"]]
    rects.append({"key": "the goal", "x": layout["goal"]["x"], "y": layout["goal"]["y"],
                  "w": SIZES["goalW"], "h": SIZES["goalH"]})
    return rects


def busy_tree():
    """Deep on one side and wide on both, with solutions on items with and without children."""
    def deep(prefix, levels, solutions=()):
        kids = [deep(prefix, levels - 1, solutions)] if levels > 1 else []
        return item(prefix + str(levels), "deep", kids, solutions)

    wide_kids = [item("w%d" % i, "wide", [], ["s1", "s2"] if i % 2 else []) for i in range(9)]
    branchy = item("b1", "branchy", [
        item("b2", "x", [item("b3", "y", [], ["s1", "s2", "s3"]), item("b4", "z", [item("b5", "q")], ["s3"])], ["s1"]),
        deep("d", 7, ["s2"]),
        item("b6", "plain", [], ["s3"]),
    ], ["s1", "s2", "s3"])
    return make_map(obstacles=[
        branchy,
        item("t2", "two", wide_kids, ["s1"]),
        item("t3", "three", solutions=["s1", "s2", "s3"]),
        item("t4", "four", [item("t5", "kid", [], ["s1"]), deep("e", 3)]),
        item("t6", "six"),
    ])


def test_wide_layout_never_overlaps_on_a_deep_and_wide_tree():
    m = busy_tree()
    assert overlaps(wide_rects(wide(m))) == []


def test_wide_layout_draws_every_item_and_every_solution_once():
    m = busy_tree()
    rows = call("drawnRows", m)["result"]
    assert sorted(b["key"] for b in wide(m)["boxes"]) == sorted(r["key"] for r in rows)


def test_wide_layout_stays_apart_when_one_box_is_very_tall():
    m = busy_tree()
    heights = uneven_heights(m)
    heights["b3"] = 700
    heights["w4"] = 500
    heights[call("drawnRows", m)["result"][1]["key"]] = 400
    assert overlaps(wide_rects(wide(m, heights))) == []


def test_wide_layout_keeps_the_goal_in_the_true_center():
    for m in (busy_tree(), make_map(), make_map(obstacles=[], solutions=[])):
        out = wide(m)
        assert out["goal"]["x"] + SIZES["goalW"] / 2 == out["width"] / 2
        assert out["goal"]["y"] + SIZES["goalH"] / 2 == out["height"] / 2


def test_wide_layout_fits_every_box_inside_the_canvas():
    out = wide(busy_tree())
    for b in out["boxes"]:
        assert b["x"] >= 0 and b["x"] + SIZES["boxW"] <= out["width"], b["key"]
        assert b["y"] >= 0 and b["y"] + b["height"] <= out["height"], b["key"]


def test_wide_layout_reads_1_2_3_down_the_right_and_4_5_6_down_the_left():
    m = make_map(obstacles=[item("o%d" % i, "x") for i in range(1, 7)], solutions=[])
    out = wide(m)
    boxes = {b["key"]: b for b in out["boxes"]}
    goal_x = out["goal"]["x"]
    for key in ("o1", "o2", "o3"):
        assert boxes[key]["x"] > goal_x, key
    for key in ("o4", "o5", "o6"):
        assert boxes[key]["x"] < goal_x, key
    assert boxes["o1"]["y"] < boxes["o2"]["y"] < boxes["o3"]["y"]
    assert boxes["o4"]["y"] < boxes["o5"]["y"] < boxes["o6"]["y"]


def box_map(layout):
    return {b["key"]: b for b in layout["boxes"]}


def test_a_solution_on_an_item_with_children_sits_directly_under_it():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b")], ["s1", "s2"])])
    out = wide(m)
    boxes = box_map(out)
    first, second = boxes["o1|0"], boxes["o1|1"]
    assert first["x"] == boxes["o1"]["x"] == second["x"]
    assert first["y"] >= boxes["o1"]["y"] + boxes["o1"]["height"]
    assert second["y"] >= first["y"] + first["height"]


def test_a_solution_on_an_item_with_no_children_sits_in_the_next_column_out():
    for side_count, sign in ((1, 1), (2, -1)):
        obstacles = [item("o%d" % i, "x") for i in range(1, side_count)] + [item("o9", "a", [], ["s1"])]
        out = wide(make_map(obstacles=obstacles))
        boxes = box_map(out)
        assert boxes["o9|0"]["x"] - boxes["o9"]["x"] == sign * (SIZES["boxW"] + SIZES["colGap"])


def test_both_sides_get_the_width_of_the_deeper_side():
    deep = item("o1", "a", [item("o2", "b", [item("o3", "c", [item("o4", "d")])])])
    out = wide(make_map(obstacles=[deep, item("o5", "e")]))
    step = SIZES["boxW"] + SIZES["colGap"]
    assert out["width"] == 2 * (SIZES["pad"] + 4 * step - SIZES["colGap"] + SIZES["goalGap"]) + SIZES["goalW"]


def line_points(d):
    """The points a line passes through. Curves count only their two ends."""
    points = []
    for command, rest in re.findall(r"([MCVH])([^MCVH]*)", d):
        numbers = [float(n) for n in rest.split()]
        if command == "V":
            points.append((points[-1][0], numbers[0]))
        elif command == "H":
            points.append((numbers[0], points[-1][1]))
        else:
            points.append((numbers[-2], numbers[-1]))
    return points


def line_ends(d):
    points = line_points(d)
    return points[0], points[-1]


def test_wide_layout_connects_every_box_to_its_parent():
    m = busy_tree()
    out = wide(m)
    boxes = box_map(out)
    goal = out["goal"]
    rows = call("drawnRows", m)["result"]
    lines = {line["to"]: line for line in out["lines"]}
    assert len(out["lines"]) == len(rows)
    for row in rows:
        key = row["key"]
        line = lines[key]
        assert line["from"] == (row["parent"] or "goal")
        start, end = line_ends(line["d"])
        box = boxes[key]
        goes_right = box["x"] > goal["x"]
        if " V" in line["d"]:
            # A short line down a column, into the top of the box.
            assert end == (box["x"] + SIZES["boxW"] / 2, box["y"]), key
            continue
        near = box["x"] if goes_right else box["x"] + SIZES["boxW"]
        assert end == (near, box["y"] + box["height"] / 2), key
        if row["parent"]:
            parent = boxes[row["parent"]]
            far = parent["x"] + SIZES["boxW"] if goes_right else parent["x"]
            assert start == (far, parent["y"] + parent["height"] / 2), key
        else:
            far = goal["x"] + SIZES["goalW"] if goes_right else goal["x"]
            assert start == (far, goal["y"] + SIZES["goalH"] / 2), key


def test_a_stack_line_starts_on_the_box_above_it():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b")], ["s1", "s2"])])
    out = wide(m)
    boxes = box_map(out)
    lines = {line["to"]: line for line in out["lines"]}
    start, _ = line_ends(lines["o1|0"]["d"])
    assert start[1] == boxes["o1"]["y"] + boxes["o1"]["height"]
    start, _ = line_ends(lines["o1|1"]["d"])
    assert start[1] == boxes["o1|0"]["y"] + boxes["o1|0"]["height"]


def test_a_missing_solution_still_gets_a_box_and_keeps_its_mark():
    m = make_map(obstacles=[item("o1", "a", solutions=["gone"])])
    rows = call("drawnRows", m)["result"]
    assert rows[1]["key"] == "o1|0"
    assert rows[1]["solution"] == {"id": "gone", "missing": True}
    assert "o1|0" in box_map(wide(m))


def test_drawn_rows_give_each_item_its_label_and_depth():
    rows = call("drawnRows", labeled_tree())["result"]
    assert [(r["key"], r["label"], r["depth"]) for r in rows] == [
        ("o1", "1", 0), ("o3", "1A", 1), ("o4", "1B", 1), ("o5", "1B1", 2), ("o6", "1B2", 2),
        ("o7", "1B2A", 3), ("o2", "2", 0)]


def test_solutions_get_no_labels():
    rows = call("drawnRows", on_two_levels())["result"]
    assert all("label" not in r for r in rows if r["kind"] == "solution")


# Phone width: one column, indented by depth

def narrow(m, width=320, heights=None):
    places = call("narrowPlaces", m, width)["result"]
    h = heights or uneven_heights(m)
    return places, call("narrowLayout", places, h, 70)["result"]


def narrow_rects(places, layout):
    width_of = {row["key"]: row["width"] for row in places["rows"]}
    rects = [{"key": b["key"], "x": b["x"], "y": b["y"], "w": width_of[b["key"]], "h": b["height"]}
             for b in layout["boxes"]]
    rects.append({"key": "the goal", "x": layout["goal"]["x"], "y": layout["goal"]["y"],
                  "w": places["goal"]["width"], "h": 70})
    return rects


def test_narrow_layout_never_overlaps_and_stays_inside_the_width():
    places, out = narrow(busy_tree(), 320)
    rects = narrow_rects(places, out)
    assert overlaps(rects) == []
    for r in rects:
        assert r["x"] + r["w"] <= 320, r["key"]
        assert r["w"] >= 180, r["key"]
    assert out["height"] >= max(r["y"] + r["h"] for r in rects)


def test_narrow_layout_indents_by_depth():
    places, _ = narrow(labeled_tree())
    x = {row["key"]: row["x"] for row in places["rows"]}
    assert x["o1"] == x["o2"]
    assert x["o1"] < x["o3"] == x["o4"] < x["o5"] == x["o6"] < x["o7"]


def test_narrow_layout_puts_a_solution_right_after_its_item_and_before_its_children():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b")], ["s1"])])
    places, _ = narrow(m)
    assert [row["key"] for row in places["rows"]] == ["o1", "o1|0", "o2"]


def test_narrow_layout_connects_every_row_to_its_parent_without_crossing_a_box():
    m = busy_tree()
    places, out = narrow(m)
    boxes = {b["key"]: b for b in out["boxes"]}
    lines = {line["to"]: line for line in out["lines"]}
    rects = narrow_rects(places, out)
    assert len(out["lines"]) == len(places["rows"])
    for row in places["rows"]:
        line = lines[row["key"]]
        box = boxes[row["key"]]
        assert line["from"] == (row["parent"] or "goal")
        start, end = line_ends(line["d"])
        assert end == (box["x"], box["y"] + box["height"] / 2), row["key"]
        parent = boxes[row["parent"]] if row["parent"] else {**out["goal"], "height": 70}
        parent_width = places["goal"]["width"] if not row["parent"] else next(
            r["width"] for r in places["rows"] if r["key"] == row["parent"])
        # The line starts on the parent's box.
        assert parent["x"] <= start[0] <= parent["x"] + parent_width, row["key"]
        assert parent["y"] <= start[1] <= parent["y"] + parent["height"], row["key"]
        # The vertical run stays clear of every box.
        points = line_points(line["d"])
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            if x1 != x2:
                continue
            for r in rects:
                crosses_x = r["x"] < x1 < r["x"] + r["w"]
                crosses_y = r["y"] < y2 and y1 < r["y"] + r["h"]
                assert not (crosses_x and crosses_y), (row["key"], r["key"])


def test_narrow_layout_handles_an_empty_map():
    places, out = narrow(make_map(obstacles=[], solutions=[]))
    assert places["rows"] == []
    assert out["boxes"] == []
    assert out["lines"] == []
    assert out["height"] >= out["goal"]["y"] + 70


AUTOSAVER_RUNNER = r"""
const logic = %(logic)s;
const script = %(script)s;
(new Function(logic))();
const L = globalThis.MapLogic;
const tick = () => new Promise(r => setImmediate(r));

(async () => {
  const pending = [];
  const log = [];
  let count = 0;
  const write = async () => {
    const n = ++count;
    log.push('start' + n);
    await new Promise(res => pending.push(res));
    log.push('end' + n);
    const outcome = script.outcomes[n - 1] || 'ok';
    if (outcome === 'throw') throw new Error('boom');
    if (outcome === 'fail') return { ok: false, reason: 'write-failed' };
    return { ok: true };
  };
  const saver = L.createAutosaver(write);
  const results = [];
  const settleAll = async () => {
    for (let i = 0; i < 50; i++) {
      await tick();
      while (pending.length) { pending.shift()(); await tick(); }
    }
  };
  for (const step of script.steps) {
    if (step === 'request') {
      const slot = results.length;
      results.push(null);
      saver.request().then(r => { results[slot] = r; });
    } else if (step === 'release') {
      await tick();
      if (pending.length) pending.shift()();
    } else if (step === 'settle') {
      await settleAll();
    }
    await tick();
  }
  await settleAll();
  process.stdout.write(JSON.stringify({ writes: count, log, results }));
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def run_autosaver(script):
    """script: {"outcomes": [...per write: ok|fail|throw], "steps": [request|release|settle]}.

    Each write stays open until a release step (or the final settle) frees it.
    """
    program = AUTOSAVER_RUNNER % {
        "logic": json.dumps(logic_source()),
        "script": json.dumps(script),
    }
    proc = subprocess.run(
        ["node", "-"], input=program, capture_output=True, text=True, cwd=REPO
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


SAVE_DOWNLOADS = "Save to Downloads"
NOT_SAVING = "Changes aren't being saved yet."
PAUSED = "Saving is paused."


def status(**state):
    full = {"picker": True, "connected": False, "remembered": False,
            "dirty": False, "writing": False, "failed": False}
    full.update(state)
    return call("saveStatus", full)["result"]


def test_save_status_table():
    rows = [
        (dict(picker=False, dirty=False), "", "", SAVE_DOWNLOADS),
        (dict(picker=False, dirty=True), "Not saved yet.", "unsaved", SAVE_DOWNLOADS),
        (dict(dirty=False), NOT_SAVING, "", "Turn on saving"),
        (dict(dirty=True), NOT_SAVING, "unsaved", "Turn on saving"),
        (dict(remembered=True, dirty=False), PAUSED, "", "Turn saving back on"),
        (dict(remembered=True, dirty=True), PAUSED, "unsaved", "Turn saving back on"),
        (dict(connected=True, dirty=False, writing=False, failed=False), "All changes saved", "saved", ""),
        (dict(connected=True, dirty=True, writing=False, failed=False), "Saving...", "", ""),
        (dict(connected=True, dirty=False, writing=True, failed=False), "Saving...", "", ""),
        (dict(connected=True, dirty=True, writing=False, failed=True), "Not saved", "unsaved", ""),
    ]
    for state, text, tone, button in rows:
        assert status(**state) == {"text": text, "tone": tone, "button": button}, state


def test_handle_key_differs_by_folder():
    a = call("handleKey", "/a/m-map.html", "id1")["result"]
    b = call("handleKey", "/b/m-map.html", "id1")["result"]
    c = call("handleKey", "/a/m-map.html", "id2")["result"]
    assert a != b
    assert a != c
    assert a == call("handleKey", "/a/m-map.html", "id1")["result"]


def test_connect_never_writes():
    out = call("connectToHandle", "__HANDLE__", make_map(),
               handle={"content": page(make_map())})
    assert out["result"] == {"ok": True}
    assert out["writes"] == 0
    assert out["permissionMode"] == "readwrite"


def test_connect_refusals():
    src = page(make_map())
    cases = [
        ({"content": page(make_map(map_id="other"))}, "wrong-map"),
        ({"content": "not a map at all"}, "not-a-map"),
        ({"content": page(make_map(revision=9))}, "stale"),
        ({"content": src, "permission": "denied"}, "permission"),
        ({"content": src, "permission": "throw"}, "permission"),
        ({"content": src, "getFileFails": True}, "unreadable"),
    ]
    for handle, reason in cases:
        out = call("connectToHandle", "__HANDLE__", make_map(), handle=handle)
        assert out["result"] == {"ok": False, "reason": reason}, handle
        assert out["writes"] in (0, None)


def test_autosaver_runs_one_write_at_a_time():
    out = run_autosaver({"outcomes": [], "steps": ["request", "request", "request", "release"]})
    assert out["writes"] == 2
    assert out["log"] == ["start1", "end1", "start2", "end2"]


def test_autosaver_writes_again_for_edits_made_during_a_write():
    out = run_autosaver({"outcomes": [], "steps": ["request", "request"]})
    assert out["writes"] == 2
    assert out["results"] == [{"ok": True}, {"ok": True}]


def test_autosaver_drops_the_queued_write_after_a_failure():
    out = run_autosaver({"outcomes": ["fail"], "steps": ["request", "request"]})
    assert out["writes"] == 1
    assert out["results"][0]["ok"] is False


def test_autosaver_retries_on_the_next_request_after_a_failure():
    out = run_autosaver({"outcomes": ["fail", "ok"],
                         "steps": ["request", "settle", "request", "settle"]})
    assert out["writes"] == 2
    assert out["results"][0]["ok"] is False
    assert out["results"][1] == {"ok": True}


def test_autosaver_reports_a_thrown_write_as_write_failed():
    out = run_autosaver({"outcomes": ["throw", "ok"],
                         "steps": ["request", "settle", "request", "settle"]})
    assert out["results"][0] == {"ok": False, "reason": "write-failed"}
    assert out["writes"] == 2
    assert out["results"][1] == {"ok": True}
