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
EXAMPLE = REPO / "e2e" / "fixtures" / "six-step-example-map.json"

RUNNER = r"""
const logic = %(logic)s;
const kase = %(kase)s;
(new Function(logic))();
const L = globalThis.MapLogic;

(async () => {
  const stand_ins = {
    __THROWS__: () => { throw new Error('commit failed'); },
    __NOOP__: () => {},
    __TRUE__: () => true,
    __FALSE__: () => false,
  };
  const args = kase.args.map(a => (typeof a === 'string' && a in stand_ins ? stand_ins[a] : a));
  const result = await L[kase.fn](...args);
  process.stdout.write(JSON.stringify({ result }));
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
"""


def logic_block(html):
    m = re.search(r'<script id="map-logic">(.*?)</script>', html, re.S)
    assert m, "map-logic block not found"
    return m.group(1)


def logic_source():
    return logic_block(TEMPLATE.read_text())


def call(fn, *args):
    program = RUNNER % {
        "logic": json.dumps(logic_source()),
        "kase": json.dumps({"fn": fn, "args": list(args)}),
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
    }
    base.update(over)
    return base


def all_items(items):
    for it in items:
        yield it
        yield from all_items(it["children"])


def obstacle(m, oid):
    return next(o for o in all_items(m["obstacles"]) if o["id"] == oid)


def test_set_goal_replaces_the_goal():
    goal = {"text": "80% attendance by Q2, up from 40%"}
    assert call("setGoal", make_map(), goal)["result"]["goal"] == goal


def test_close_warning_still_runs_when_the_commit_throws():
    assert call("shouldWarnOnClose", "__THROWS__", "__FALSE__")["result"] is True


def test_close_warning_follows_unsaved_changes_after_a_good_commit():
    assert call("shouldWarnOnClose", "__NOOP__", "__TRUE__")["result"] is True
    assert call("shouldWarnOnClose", "__NOOP__", "__FALSE__")["result"] is False


def test_the_logic_block_has_no_goal_line():
    assert "goalLine" not in TEMPLATE.read_text()


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


def test_goal_takes_a_solution():
    m = make_map(obstacles=[item("o1", "a")])
    assert call("canAdd", m, "goal", "obstacle")["result"] is True
    assert call("canAdd", m, "goal", "solution")["result"] is True
    added = call("addItem", m, "goal", "s9", "solution", "new")["result"]
    assert added["obstacles"][-1] == sol("s9", "new")
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
    m = call("moveItem", m, "ms", "other")["result"]
    assert obstacle(m, "other")["children"] == [sol("ms", "moving solution")]
    assert [o["id"] for o in m["obstacles"]] == ["holder", "ob", "other"]


EVERY_MOVE = r"""
const logic = %(logic)s;
const store = %(store)s;
const doc = %(doc)s;
(new Function(logic))();
(new Function(store))();
const L = globalThis.MapLogic;
const data = globalThis.MapStore.inflate(doc);
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


def every_move_problems(doc):
    html = TEMPLATE.read_text()
    store = re.search(r'<script id="map-store">(.*?)</script>', html, re.S).group(1)
    program = EVERY_MOVE % {"logic": json.dumps(logic_block(html)), "store": json.dumps(store), "doc": doc}
    proc = subprocess.run(["node", "-"], input=program, capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_every_allowed_move_on_the_example_moves_only_that_item_and_lands_it_last():
    out = every_move_problems(EXAMPLE.read_text())
    # Every item onto the goal and every other item, less the moves the rules refuse.
    assert out["allowed"] == 516
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


def test_the_delete_card_has_no_list_of_effects_behind_it():
    page = TEMPLATE.read_text()
    for gone in ("deleteEffects", "listOf", "delete-keep", "delete-question"):
        assert gone not in page, gone


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
