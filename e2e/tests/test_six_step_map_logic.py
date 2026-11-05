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
EXAMPLE = REPO / "frameworks" / "6-step-process" / "example-map.html"

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


def item(id, text="", children=(), kind="obstacle", star=False):
    return {"id": id, "kind": kind, "text": text, "star": star, "children": list(children)}


def sol(id, text="", children=(), star=False):
    return item(id, text, children, kind="solution", star=star)


def make_map(**over):
    base = {
        "map_id": "m-1",
        "revision": 1,
        "person": "Pat",
        "goal": {"text": "g"},
        "obstacles": [
            item("o1", "a", [item("o3", "w1", [item("o4", "w2")]), sol("s1", "one"), sol("s2", "two", star=True)]),
            item("o2", "b", [sol("s4", "four")]),
            sol("s3", "three"),
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
    empty = make_map(obstacles=[])
    assert call("nextId", empty, "o")["result"] == "o1"


def test_set_goal_replaces_the_goal():
    goal = {"text": "80% attendance by Q2, up from 40%"}
    assert call("setGoal", make_map(), goal)["result"]["goal"] == goal


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
    empty = make_map(obstacles=[])
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
    assert call("mapProblem", m)["result"] == "Obstacle 2 is missing its list of what sits under it."


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
    m = make_map(obstacles=[item("o1", "a", [item("k%d" % i) for i in range(28)])])
    labels = call("itemLabels", m)["result"]
    assert labels["k25"] == "1Z"
    assert labels["k26"] == "1AA"
    assert labels["k27"] == "1AB"


def test_item_labels_past_z_at_a_deeper_letter_level():
    kids = [item("k%d" % i) for i in range(53)]
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b", [item("o3", "c", kids)])])])
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


def test_shape_check_is_not_fooled_by_an_id_like_a_built_in_name():
    m = make_map(obstacles=[item("constructor", "a"), item("__proto__", "b")])
    assert call("mapProblem", m)["result"] is None


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


def box_map(layout):
    return {b["key"]: b for b in layout["boxes"]}


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


def test_drawn_rows_give_each_item_its_label_and_depth():
    rows = call("drawnRows", labeled_tree())["result"]
    assert [(r["key"], r["label"], r["depth"]) for r in rows] == [
        ("o1", "1", 0), ("o3", "1A", 1), ("o4", "1B", 1), ("o5", "1B1", 2), ("o6", "1B2", 2),
        ("o7", "1B2A", 3), ("o2", "2", 0)]


# The one tree: every item has the same five fields, and everything hangs off the goal.

def label_case():
    """1B has a child obstacle, then a solution holding an obstacle."""
    return make_map(obstacles=[
        item("o1", "one", [
            item("oa", "1A"),
            item("ob", "1B", [
                item("c1", "child"),
                sol("sx", "fix", [item("c2", "in the way of fix")]),
            ]),
        ]),
    ])


def mixed_tree():
    """Deep and wide, with obstacles under solutions at several depths."""
    def deep(prefix, levels):
        kids = [deep(prefix, levels - 1)] if levels > 1 else []
        return item(prefix + str(levels), "deep", kids + [sol(prefix + "s" + str(levels), "fix")])

    wide_kids = [item("w%d" % i, "wide", [sol("ws%d" % i, "fix")] if i % 2 else []) for i in range(9)]
    branchy = item("b1", "branchy", [
        sol("bs1", "fix"),
        item("b2", "x", [
            item("b3", "y", [sol("bs2", "fix", [item("b7", "in the way", [sol("bs3", "fix")])])]),
            sol("bs4", "fix", [item("b8", "a"), item("b9", "b", [item("b10", "c")])]),
            item("b11", "after the solution"),
        ]),
        deep("d", 7),
        item("b6", "plain", [sol("bs5", "fix", [item("b12", "in the way of the fix")])]),
    ])
    return make_map(obstacles=[
        branchy,
        item("t2", "two", wide_kids),
        item("t3", "three", [sol("ts1", "fix"), sol("ts2", "fix"), sol("ts3", "fix")]),
        item("t4", "four", [item("t5", "kid", [sol("ts4", "fix")]), deep("e", 3)]),
        item("t6", "six"),
        sol("top1", "directly under the goal", [item("t7", "in its way", [sol("ts5", "fix")])]),
    ])


def test_labels_count_across_solutions():
    labels = call("itemLabels", label_case())["result"]
    assert labels["ob"] == "1B"
    assert labels["c1"] == "1B1"
    assert labels["c2"] == "1B2"


def test_labels_have_no_duplicates_on_a_deep_mixed_tree():
    labels = call("itemLabels", mixed_tree())["result"]
    assert len(set(labels.values())) == len(labels)
    assert len(labels) > 25


def test_labels_skip_solutions():
    m = make_map(obstacles=[
        item("o1", "a", [sol("s1", "fix"), item("o2", "b"), sol("s2", "fix"), item("o3", "c")]),
        item("o4", "d"),
    ])
    assert call("itemLabels", m)["result"] == {"o1": "1", "o2": "1A", "o3": "1B", "o4": "2"}


def test_label_under_a_solution_continues_the_obstacle_above_it():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "fix", [item("o2", "b")])])])
    assert call("itemLabels", m)["result"] == {"o1": "1", "o2": "1A"}


def test_label_under_a_solution_on_the_goal_takes_the_next_top_level_number():
    m = make_map(obstacles=[item("o1", "a"), sol("s1", "fix", [item("o2", "b")]), item("o3", "c")])
    assert call("itemLabels", m)["result"] == {"o1": "1", "o2": "2", "o3": "3"}


def test_solutions_get_no_labels():
    rows = call("drawnRows", mixed_tree())["result"]
    assert all("label" not in r for r in rows if r["kind"] == "solution")
    assert all(r["label"] for r in rows if r["kind"] == "obstacle")


def rule_map():
    """A goal, two obstacles and a solution, with two items free to move onto them."""
    return make_map(obstacles=[
        item("holder", "holds the movers", [item("mo", "moving obstacle"), sol("ms", "moving solution")]),
        item("ob", "plain", [sol("so", "a solution")]),
        item("other", "other"),
    ])


def test_every_item_takes_both_pluses():
    m = make_map(obstacles=[
        item("o1", "a", [item("o2", "b", [sol("s1", "c", [sol("s2", "d", [item("o3", "e")])])])]),
        sol("s3", "on the goal", [sol("s4", "f")]),
    ])
    for parent in ("o1", "o2", "s1", "s2", "o3", "s3", "s4"):
        for kind in ("obstacle", "solution"):
            assert call("canAdd", m, parent, kind)["result"] is True, (parent, kind)
    added = call("addItem", m, "s2", "s9", "solution", "new")["result"]
    assert [c["id"] for c in obstacle(added, "s2")["children"]] == ["o3", "s9"]
    assert call("mapProblem", added)["result"] is None


def test_goal_takes_a_solution():
    m = make_map(obstacles=[item("o1", "a")])
    assert call("canAdd", m, "goal", "obstacle")["result"] is True
    assert call("canAdd", m, "goal", "solution")["result"] is True
    added = call("addItem", m, "goal", "s9", "solution", "new")["result"]
    assert added["obstacles"][-1] == sol("s9", "new")
    assert call("mapProblem", added)["result"] is None
    assert call("drawnRows", added)["result"][-1]["parent"] is None


def test_plus_refuses_unknown_items():
    m = rule_map()
    for kind in ("obstacle", "solution"):
        assert call("canAdd", m, "nope", kind)["result"] is False
    assert call("canAdd", m, "ob", "note")["result"] is False


def test_add_item_builds_all_five_fields_at_the_top_and_at_depth():
    m = call("addItem", make_map(), "goal", "o5", "obstacle", "new")["result"]
    assert m["obstacles"][-1] == {"id": "o5", "kind": "obstacle", "text": "new", "star": False, "children": []}
    m = call("addItem", rule_map(), "so", "o9", "obstacle", "new")["result"]
    assert obstacle(m, "so")["children"] == [item("o9", "new")]
    m = call("addItem", rule_map(), "other", "s9", "solution", "new")["result"]
    assert obstacle(m, "other")["children"] == [sol("s9", "new")]


def test_add_item_changes_nothing_when_the_plus_rule_says_no():
    m = rule_map()
    assert call("addItem", m, "nope", "o9", "obstacle", "new")["result"] == m
    assert call("addItem", m, "goal", "x9", "note", "new")["result"] == m


def test_an_item_can_move_onto_the_goal_or_any_other_item():
    m = rule_map()
    for mover in ("mo", "ms"):
        for target in ("goal", "ob", "other", "so"):
            assert call("canMove", m, mover, target)["result"] is True, (mover, target)
    assert call("canMove", m, "mo", "ms")["result"] is True
    assert call("canMove", m, "ms", "mo")["result"] is True


def test_the_goal_cannot_move():
    m = rule_map()
    for target in ("ob", "goal", "mo"):
        assert call("canMove", m, "goal", target)["result"] is False, target


def test_move_refuses_self_descendant_and_current_parent():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b", [sol("s1", "fix", [item("o3", "c")])])]), item("o4", "d")])
    assert call("canMove", m, "o2", "o2")["result"] is False
    assert call("canMove", m, "o2", "s1")["result"] is False
    assert call("canMove", m, "o2", "o3")["result"] is False
    assert call("canMove", m, "o2", "o1")["result"] is False
    assert call("canMove", m, "o1", "goal")["result"] is False
    assert call("canMove", m, "o2", "o4")["result"] is True


def test_move_refuses_unknown_items():
    m = rule_map()
    assert call("canMove", m, "nope", "ob")["result"] is False
    assert call("canMove", m, "ms", "nope")["result"] is False


def test_move_item_changes_nothing_when_refused():
    m = rule_map()
    assert call("moveItem", m, "mo", "holder")["result"] == m
    assert call("moveItem", m, "holder", "mo")["result"] == m
    assert call("moveItem", m, "nope", "ob")["result"] == m


def test_move_attaches_last():
    m = call("moveItem", rule_map(), "mo", "ob")["result"]
    assert [c["id"] for c in obstacle(m, "ob")["children"]] == ["so", "mo"]
    assert [c["id"] for c in obstacle(m, "holder")["children"]] == ["ms"]
    m = call("moveItem", rule_map(), "mo", "goal")["result"]
    assert [o["id"] for o in m["obstacles"]] == ["holder", "ob", "other", "mo"]


def test_move_takes_what_sits_under_the_item_with_it():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b", [sol("s1", "fix")])]), item("o3", "c")])
    m = call("moveItem", m, "o2", "o3")["result"]
    assert obstacle(m, "o3")["children"] == [item("o2", "b", [sol("s1", "fix")])]


def test_a_solution_moves_onto_the_goal_and_back():
    m = call("moveItem", rule_map(), "ms", "goal")["result"]
    assert m["obstacles"][-1] == sol("ms", "moving solution")
    assert call("mapProblem", m)["result"] is None
    m = call("moveItem", m, "ms", "other")["result"]
    assert obstacle(m, "other")["children"] == [sol("ms", "moving solution")]
    assert [o["id"] for o in m["obstacles"]] == ["holder", "ob", "other"]


EVERY_MOVE = r"""
const logic = %(logic)s;
const data = %(data)s;
(new Function(logic))();
const L = globalThis.MapLogic;
function places(map) {
  const out = {};
  (function walk(items, parent) {
    items.forEach((it, i) => { out[it.id] = { parent, i }; walk(it.children, it.id); });
  })(map.obstacles, 'goal');
  return out;
}
const before = places(data);
const ids = Object.keys(before);
let allowed = 0;
const bad = [];
ids.forEach((moved) => ['goal'].concat(ids).forEach((target) => {
  if (!L.canMove(data, moved, target)) return;
  allowed += 1;
  const name = moved + ' onto ' + target + ': ';
  const after = places(L.moveItem(data, moved, target));
  if (Object.keys(after).length !== ids.length) bad.push(name + 'the item count changed');
  ids.forEach((id) => {
    if (!after[id]) bad.push(name + 'lost ' + id);
    else if (id === moved) { if (after[id].parent !== target) bad.push(name + 'landed under ' + after[id].parent); }
    else if (after[id].parent !== before[id].parent) bad.push(name + id + ' changed parent');
  });
  const siblings = Object.values(after).filter((place) => place.parent === target).length;
  if (after[moved] && after[moved].i !== siblings - 1) bad.push(name + 'not last under its target');
}));
process.stdout.write(JSON.stringify({ allowed, bad }));
"""


def every_move_problems(html):
    data = re.search(r'<script id="map-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    program = EVERY_MOVE % {"logic": json.dumps(logic_block(html)), "data": data}
    proc = subprocess.run(["node", "-"], input=program, capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_every_allowed_move_on_the_example_moves_only_that_item_and_lands_it_last():
    out = every_move_problems(EXAMPLE.read_text())
    assert out["allowed"] > 0
    assert out["bad"] == []


def test_drag_distance_threshold():
    for dx, dy in ((5, 0), (0, 5), (-5, 0), (0, -5), (3, 4), (-3, -4), (100, 100)):
        assert call("isDragDistance", dx, dy)["result"] is True, (dx, dy)
    for dx, dy in ((0, 0), (4, 0), (0, -4), (3, 3), (-3, 3)):
        assert call("isDragDistance", dx, dy)["result"] is False, (dx, dy)


def plan_map():
    return make_map(
        obstacles=[
            item("o1", "a", [
                sol("s1", "one", [item("o2", "b", [sol("s2", "two", star=True)])], star=True),
                sol("s4", "stays"),
            ]),
            sol("s3", "on the goal"),
        ],
        key_actions=[
            {"text": "both", "risk": "high", "solution_ids": ["s1", "s2", "s4"]},
            {"text": "only two", "risk": "low", "solution_ids": ["s2"]},
            {"text": "stays whole", "risk": "low", "solution_ids": ["s4"]},
        ],
        execute=[
            {"solution_id": "s1", "first_move": "move one", "owner": "", "others_decide": ""},
            {"solution_id": "s2", "first_move": "move two", "owner": "", "others_decide": ""},
            {"solution_id": "s4", "first_move": "move four", "owner": "", "others_decide": ""},
        ],
    )


def test_delete_removes_rows_and_ids_but_keeps_key_actions():
    m = call("deleteItem", plan_map(), "s1")["result"]
    assert obstacle(m, "o1")["children"] == [sol("s4", "stays")]
    assert [e["solution_id"] for e in m["execute"]] == ["s4"]
    assert [(k["text"], k["solution_ids"]) for k in m["key_actions"]] == [
        ("both", ["s4"]), ("only two", []), ("stays whole", ["s4"])]


def test_delete_of_an_obstacle_takes_the_solutions_under_it():
    m = call("deleteItem", plan_map(), "o2")["result"]
    assert [e["solution_id"] for e in m["execute"]] == ["s1", "s4"]
    assert m["key_actions"][1]["solution_ids"] == []
    assert obstacle(m, "s1")["children"] == []


def test_delete_works_on_a_solution_on_the_goal_and_clears_its_ids():
    m = plan_map()
    m["key_actions"][0]["solution_ids"].append("s3")
    m["execute"].append({"solution_id": "s3", "first_move": "its move", "owner": "", "others_decide": ""})
    out = call("deleteItem", m, "s3")["result"]
    assert [o["id"] for o in out["obstacles"]] == ["o1"]
    assert "s3" not in out["key_actions"][0]["solution_ids"]
    assert all(e["solution_id"] != "s3" for e in out["execute"])


def test_delete_a_top_level_item_and_an_unknown_one():
    m = call("deleteItem", plan_map(), "o1")["result"]
    assert m["obstacles"] == [sol("s3", "on the goal")]
    m = plan_map()
    assert call("deleteItem", m, "nope")["result"] == m


def test_delete_effects_name_picks_and_rows():
    out = call("deleteEffects", plan_map(), "s1")["result"]
    assert "subItems" not in out
    assert out["picks"] == ["one", "two"]
    assert out["rows"] == ["move one", "move two"]
    assert out["keyActions"] == ["both", "only two"]


def test_delete_effects_name_a_row_with_a_blank_first_move_by_its_solution():
    m = plan_map()
    m["execute"][1]["first_move"] = ""
    out = call("deleteEffects", m, "s1")["result"]
    assert out["rows"] == ["move one", "two"]


def test_delete_effects_of_an_item_with_nothing_to_lose():
    m = plan_map()
    nothing = {"picks": [], "rows": [], "keyActions": []}
    assert call("deleteEffects", m, "s3")["result"] == nothing
    assert call("deleteEffects", m, "nope")["result"] == nothing


def test_star_changes_only_that_solution():
    m = make_map()
    out = call("setStar", m, "s1", True)["result"]
    assert obstacle(out, "s1")["star"] is True
    assert obstacle(out, "s2")["star"] is True
    out = call("setStar", out, "s2", False)["result"]
    assert obstacle(out, "s2")["star"] is False


def test_star_works_on_every_solution():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "b", [sol("s2", "c")])]), sol("s3", "on the goal")])
    for sid in ("s1", "s2", "s3"):
        assert call("canPick", m, sid)["result"] is True, sid
        assert obstacle(call("setStar", m, sid, True)["result"], sid)["star"] is True, sid


def test_star_refused_on_obstacles():
    m = make_map()
    assert call("setStar", m, "o1", True)["result"] == m
    assert call("setStar", m, "nope", True)["result"] == m


def test_next_id_is_unique_across_the_tree():
    m = make_map(obstacles=[item("o3", "a", [sol("s2", "fix")]), sol("s7", "on the goal")])
    assert call("nextId", m, "s")["result"] == "s8"
    assert call("nextId", m, "o")["result"] == "o4"


def test_set_item_text_at_any_depth_and_on_the_goal():
    m = call("setItemText", make_map(), "o1", "A")["result"]
    assert obstacle(m, "o1")["text"] == "A"
    m = call("setItemText", make_map(), "o4", "W")["result"]
    assert obstacle(m, "o4")["text"] == "W"
    assert obstacle(m, "o3")["text"] == "w1"
    m = call("setItemText", make_map(), "s1", "changed")["result"]
    assert obstacle(m, "s1")["text"] == "changed"
    m = call("setItemText", make_map(), "s3", "changed")["result"]
    assert obstacle(m, "s3")["text"] == "changed"


def test_item_exists_for_each_kind():
    m = make_map()
    for ref in ({"kind": "goal"}, {"kind": "obstacle", "id": "o1"}, {"kind": "obstacle", "id": "o4"},
                {"kind": "solution", "id": "s1"}, {"kind": "solution", "id": "s3"}):
        assert call("itemExists", m, ref)["result"] is True, ref
    for ref in ({"kind": "obstacle", "id": "o9"}, {"kind": "solution", "id": "s9"}):
        assert call("itemExists", m, ref)["result"] is False, ref


def test_item_exists_is_false_after_a_blank_new_item_is_removed():
    m = call("addItem", make_map(), "o4", "o5", "obstacle", "")["result"]
    ref = {"kind": "obstacle", "id": "o5"}
    assert call("itemExists", m, ref)["result"] is True
    m = call("deleteItem", m, "o5")["result"]
    assert call("itemExists", m, ref)["result"] is False


def test_panel_rows_name_a_solution_by_the_obstacle_it_sits_under():
    m = make_map(
        obstacles=[item("o1", "a", [item("o2", "b", [sol("s1", "one")]), sol("s2", "two")]), sol("s3", "three")],
        key_actions=[{"text": "k", "risk": "low", "solution_ids": ["s1", "s3"]}],
        execute=[{"solution_id": "s2", "first_move": "m", "owner": "o", "others_decide": "d"}],
    )
    rows = call("panelRows", m)["result"]
    assert rows["key_actions"] == [{"text": "k", "risk": "low", "solutions": ["one (1A)", "three"]}]
    assert rows["execute"] == [{"solution": "two (1)", "first_move": "m", "owner": "o", "others_decide": "d"}]


def test_panel_rows_name_a_nested_solution_by_the_nearest_obstacle():
    m = make_map(
        obstacles=[
            item("o1", "a", [sol("s1", "one", [sol("s2", "two")])]),
            sol("s3", "three", [sol("s4", "four")]),
        ],
        key_actions=[{"text": "k", "risk": "low", "solution_ids": ["s2", "s3", "s4"]}],
    )
    rows = call("panelRows", m)["result"]
    assert rows["key_actions"][0]["solutions"] == ["two (1)", "three", "four"]


def test_panel_rows_handle_ids_like_built_in_names():
    m = make_map(
        obstacles=[item("constructor", "a", [sol("__proto__", "one", [sol("toString", "two")])])],
        key_actions=[{"text": "k", "risk": "low", "solution_ids": ["__proto__", "toString"]}],
    )
    assert call("panelRows", m)["result"]["key_actions"][0]["solutions"] == ["one (1)", "two (1)"]


# The check. Each case the spec lists, with a plain sentence naming the item.

def test_check_passes_a_good_map_with_every_rule_in_play():
    assert call("mapProblem", mixed_tree())["result"] is None


def test_check_refuses_a_repeated_id_in_the_tree():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "fix")]), item("o2", "b", [sol("s1", "fix")])])
    assert "both use the id s1" in call("mapProblem", m)["result"]


def test_check_refuses_root_cause_and_unplaced_fields():
    m = make_map()
    m["unplaced"] = []
    assert call("mapProblem", m)["result"] == "The map uses the old map shape."
    m = make_map()
    obstacle(m, "o4")["root_cause"] = False
    assert call("mapProblem", m)["result"] == "Obstacle 1A1 uses the old map shape."
    m = make_map()
    obstacle(m, "s1")["root_cause"] = True
    assert call("mapProblem", m)["result"] == 'Solution "one" uses the old map shape.'


def test_check_accepts_a_solution_directly_under_the_goal():
    m = make_map(obstacles=[sol("s1", "the fix", [item("o1", "in the way")])])
    assert call("mapProblem", m)["result"] is None


def test_check_refuses_each_missing_field():
    names = {"id": "its id", "kind": "its kind", "text": "its text", "children": "its list of what sits under it"}
    for field, words in names.items():
        m = make_map(obstacles=[item("o1", "a"), item("o2", "b")])
        del m["obstacles"][1][field]
        assert call("mapProblem", m)["result"] == "Obstacle 2 is missing " + words + ".", field
    m = make_map(obstacles=[item("o1", "a")])
    del m["obstacles"][0]["star"]
    assert call("mapProblem", m)["result"] == "Obstacle 1 needs true or false for its star."


def test_check_refuses_a_missing_field_on_a_solution_on_the_goal():
    m = make_map(obstacles=[sol("s1", "top")])
    del m["obstacles"][0]["star"]
    assert call("mapProblem", m)["result"] == 'Solution "top" needs true or false for its star.'


def test_check_refuses_any_other_kind():
    m = make_map(obstacles=[item("o1", "a", kind="note")])
    assert call("mapProblem", m)["result"] == "Obstacle 1 needs a kind of obstacle or solution."


def test_check_refuses_the_old_solutions_list():
    m = make_map(solutions=[])
    assert call("mapProblem", m)["result"] == "The map uses the old map shape."


def test_check_refuses_an_item_with_old_solution_ids():
    m = make_map(obstacles=[item("o1", "a")])
    m["obstacles"][0]["solution_ids"] = []
    assert call("mapProblem", m)["result"] == "Obstacle 1 uses the old map shape."


def test_check_accepts_a_solution_directly_under_a_solution():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "the fix", [sol("s2", "other")])])])
    assert call("mapProblem", m)["result"] is None


def test_add_item_puts_a_solution_under_a_solution():
    m = call("addItem", rule_map(), "so", "s9", "solution", "new")["result"]
    assert obstacle(m, "so")["children"] == [sol("s9", "new")]


def test_move_puts_a_solution_under_a_solution_but_not_under_itself_or_its_parent():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "x", [sol("s2", "y")]), sol("s3", "z")])])
    assert call("canMove", m, "s3", "s1")["result"] is True
    assert call("canMove", m, "s1", "s1")["result"] is False
    assert call("canMove", m, "s1", "s2")["result"] is False
    assert call("canMove", m, "s2", "s1")["result"] is False
    moved = call("moveItem", m, "s3", "s1")["result"]
    assert [c["id"] for c in obstacle(moved, "s1")["children"]] == ["s2", "s3"]


def test_an_obstacle_under_a_nested_solution_continues_the_numbering():
    m = make_map(obstacles=[item("o1", "a", [item("o2", "b", [
        sol("s1", "x", [sol("s2", "y", [item("o3", "c")])]), item("o4", "d")])])])
    labels = call("itemLabels", m)["result"]
    assert labels["o2"] == "1A" and labels["o3"] == "1A1" and labels["o4"] == "1A2"


def test_check_refuses_a_non_solution_with_a_star():
    m = make_map(obstacles=[item("o1", "a", star=True)])
    assert call("mapProblem", m)["result"] == "Obstacle 1 has a star, but only a solution can be a pick."


def test_check_refuses_a_plan_row_naming_a_missing_solution():
    m = make_map(execute=[{"solution_id": "gone", "first_move": "x", "owner": "", "others_decide": ""}])
    assert call("mapProblem", m)["result"] == "Execute row 1 names a solution that isn't on the map (gone)."
    m = make_map(key_actions=[{"text": "k", "risk": "low", "solution_ids": ["s1", "gone"]}])
    assert call("mapProblem", m)["result"] == "Key action 1 names a solution that isn't on the map (gone)."


def test_check_refuses_a_plan_row_naming_an_obstacle():
    m = make_map(execute=[{"solution_id": "o1", "first_move": "x", "owner": "", "others_decide": ""}])
    assert call("mapProblem", m)["result"] == "Execute row 1 names a solution that isn't on the map (o1)."


def test_check_lets_a_plan_row_name_a_solution_on_the_goal():
    m = make_map(execute=[{"solution_id": "s3", "first_move": "x", "owner": "", "others_decide": ""}])
    assert call("mapProblem", m)["result"] is None


def test_check_names_a_solution_with_no_text_and_no_id_plainly():
    m = make_map(obstacles=[item("o1", "a", [sol("", "")])])
    assert call("mapProblem", m)["result"] == "A solution is missing its id."
    del m["obstacles"][0]["children"][0]["id"]
    assert call("mapProblem", m)["result"] == "A solution is missing its id."


def test_check_names_a_solution_with_no_text_by_its_id():
    m = make_map(obstacles=[item("o1", "a", [sol("s1", "")])])
    obstacle(m, "s1")["star"] = "yes"
    assert call("mapProblem", m)["result"] == "Solution s1 needs true or false for its star."


def test_map_problem_refuses_each_missing_list():
    for field, label in (("obstacles", "obstacles"), ("key_actions", "key actions"), ("execute", "execute rows")):
        m = make_map()
        del m[field]
        assert call("mapProblem", m)["result"] == "The map is missing its list of " + label + ".", field


def test_map_problem_refuses_a_row_of_the_wrong_kind():
    assert call("mapProblem", make_map(execute=[None]))["result"] == "Execute row 1 is missing."


def test_shape_check_rejects_a_bad_child_at_depth():
    m = labeled_tree()
    del obstacle(m, "o7")["children"]
    assert call("mapProblem", m)["result"] == "Obstacle 1B2A is missing its list of what sits under it."
    m = labeled_tree()
    obstacle(m, "o6")["children"] = [None]
    assert call("mapProblem", m)["result"] == "Obstacle 1B2A is missing."
    m = labeled_tree()
    obstacle(m, "o5")["text"] = 3
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 is missing its text."
    m = labeled_tree()
    obstacle(m, "o5")["star"] = "because"
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 needs true or false for its star."
    m = labeled_tree()
    obstacle(m, "o5")["id"] = ""
    assert call("mapProblem", m)["result"] == "Obstacle 1B1 is missing its id."


def test_shape_check_rejects_duplicate_ids():
    m = labeled_tree()
    obstacle(m, "o7")["id"] = "o2"
    assert call("mapProblem", m)["result"] == "Obstacle 1B2A and Obstacle 2 both use the id o2."


# The wide layout: the goal on the left, and every item one column out from its parent.

def test_layout_has_no_overlaps_on_a_deep_mixed_tree():
    assert overlaps(wide_rects(wide(mixed_tree()))) == []


def test_layout_stays_apart_when_one_box_is_very_tall():
    m = mixed_tree()
    heights = uneven_heights(m)
    heights["b3"] = 700
    heights["w4"] = 500
    heights["bs1"] = 400
    assert overlaps(wide_rects(wide(m, heights))) == []


def test_layout_draws_every_item_once():
    m = mixed_tree()
    rows = call("drawnRows", m)["result"]
    keys = sorted(b["key"] for b in wide(m)["boxes"])
    assert keys == sorted(r["key"] for r in rows)
    assert "top1" in keys


def test_layout_keeps_a_line_per_item_with_its_kind():
    m = mixed_tree()
    out = wide(m)
    rows = {r["key"]: r for r in call("drawnRows", m)["result"]}
    assert sorted(line["to"] for line in out["lines"]) == sorted(rows)
    for line in out["lines"]:
        assert line["kind"] == rows[line["to"]]["kind"], line["to"]
        assert line["d"].startswith("M")


def test_layout_puts_the_goal_on_the_left_and_everything_to_its_right():
    for m in (mixed_tree(), make_map()):
        out = wide(m)
        assert out["goal"]["x"] == SIZES["pad"]
        assert out["goal"]["y"] + SIZES["goalH"] / 2 == out["height"] / 2
        first = SIZES["pad"] + SIZES["goalW"] + SIZES["goalGap"]
        assert all(b["x"] >= first for b in out["boxes"])


def test_layout_of_an_empty_map_is_the_goal_alone():
    out = wide(make_map(obstacles=[]))
    assert out["boxes"] == [] and out["lines"] == []
    assert out["width"] == SIZES["pad"] * 2 + SIZES["goalW"]
    assert out["height"] == SIZES["pad"] * 2 + SIZES["goalH"]


def test_layout_sits_every_item_one_column_out_from_its_parent():
    m = mixed_tree()
    out = wide(m)
    boxes = box_map(out)
    step = SIZES["boxW"] + SIZES["colGap"]
    first = SIZES["pad"] + SIZES["goalW"] + SIZES["goalGap"]
    for row in call("drawnRows", m)["result"]:
        if row["parent"]:
            assert boxes[row["key"]]["x"] - boxes[row["parent"]]["x"] == step, row["key"]
        else:
            assert boxes[row["key"]]["x"] == first, row["key"]


def test_layout_reads_top_level_order_straight_down():
    m = make_map(obstacles=[item("o%d" % i, "x") for i in range(1, 7)])
    boxes = box_map(wide(m))
    assert len({boxes["o%d" % i]["x"] for i in range(1, 7)}) == 1
    ys = [boxes["o%d" % i]["y"] for i in range(1, 7)]
    assert ys == sorted(ys)


def test_layout_width_fits_the_deepest_column():
    deep = item("o1", "a", [item("o2", "b", [sol("s1", "c", [item("o4", "d")])])])
    out = wide(make_map(obstacles=[deep, item("o5", "e")]))
    step = SIZES["boxW"] + SIZES["colGap"]
    assert out["width"] == SIZES["pad"] * 2 + SIZES["goalW"] + SIZES["goalGap"] + 4 * step - SIZES["colGap"]


def test_layout_fits_every_box_inside_the_canvas():
    out = wide(mixed_tree())
    for b in out["boxes"]:
        assert b["x"] >= 0 and b["x"] + SIZES["boxW"] <= out["width"], b["key"]
        assert b["y"] >= 0 and b["y"] + b["height"] <= out["height"], b["key"]


def test_layout_connects_every_item_to_its_parent():
    m = mixed_tree()
    out = wide(m)
    boxes = box_map(out)
    goal = out["goal"]
    lines = {line["to"]: line for line in out["lines"]}
    for row in call("drawnRows", m)["result"]:
        key = row["key"]
        line = lines[key]
        assert line["from"] == (row["parent"] or "goal")
        start, end = line_ends(line["d"])
        assert end == (boxes[key]["x"], boxes[key]["y"] + boxes[key]["height"] / 2), key
        if row["parent"]:
            parent = boxes[row["parent"]]
            assert start == (parent["x"] + SIZES["boxW"], parent["y"] + parent["height"] / 2), key
        else:
            assert start == (goal["x"] + SIZES["goalW"], goal["y"] + SIZES["goalH"] / 2), key


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
