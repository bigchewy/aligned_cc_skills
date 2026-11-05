"""Tests for the flat data logic in the 6-step process mind map template.

The harness pulls <script id="map-logic"> and <script id="map-store"> out of the
template and runs a JS snippet under node. The snippet sees MapLogic as L,
MapStore as S and the test's JSON data as D, and returns a JSON value.
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
const store = %(store)s;
const D = %(data)s;
(new Function(logic))();
(new Function(store))();
const L = globalThis.MapLogic;
const S = globalThis.MapStore;
const body = %(code)s;
const result = (new Function('L', 'S', 'D', body))(L, S, D);
process.stdout.write(JSON.stringify(result === undefined ? null : result));
"""


def block(html, script_id):
    m = re.search(r'<script id="%s">(.*?)</script>' % script_id, html, re.S)
    assert m, "%s block not found" % script_id
    return m.group(1)


def run(code, **data):
    html = TEMPLATE.read_text()
    program = RUNNER % {
        "logic": json.dumps(block(html, "map-logic")),
        "store": json.dumps(block(html, "map-store")),
        "data": json.dumps(data),
        "code": json.dumps(code),
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
        "map_id": "",
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


def example_map():
    html = EXAMPLE.read_text()
    m = re.search(r'<script id="map-data" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))


def doc_of(**over):
    base = {
        "version": 1,
        "person": "Pat",
        "goal": {"text": "g"},
        "items": {},
        "key_actions": [],
        "execute": [],
        "feedback": {"number": "", "check_on": "", "redraw_if": ""},
    }
    base.update(over)
    return base


def entry(kind="obstacle", parent="goal", order=1, text="", star=False):
    return {"kind": kind, "text": text, "star": star, "parent": parent, "order": order}


def inflate(doc):
    return run("return S.inflate(D.doc);", doc=doc)


def ids_of(items):
    return [[i["id"], ids_of(i["children"])] for i in items]


def tree_ids(doc):
    return ids_of(inflate(doc)["obstacles"])


def test_flatten_then_inflate_keeps_the_example_tree():
    example = example_map()
    out = run(
        "const m = S.inflate(S.flatten(D.map)); m.map_id = 'x'; return {m: m, problem: L.mapProblem(m)};",
        map=example,
    )
    assert out["problem"] is None
    for key in ("obstacles", "goal", "person", "key_actions", "execute", "feedback"):
        assert out["m"][key] == example[key], key
    assert out["m"]["revision"] == 1
    assert out["m"]["baseline"] == {}


def test_flatten_orders_from_one_under_each_parent():
    doc = run("return S.flatten(D.map);", map=make_map())
    assert doc["version"] == 1
    assert doc["items"]["o1"] == {"kind": "obstacle", "text": "a", "star": False, "parent": "goal", "order": 1}
    assert doc["items"]["s3"]["order"] == 3
    assert doc["items"]["s2"]["parent"] == "o1" and doc["items"]["s2"]["order"] == 3
    assert doc["items"]["o4"]["parent"] == "o3"


def test_new_id_is_eight_lowercase_letters_and_digits():
    ids = run("const a = []; for (let i = 0; i < 50; i++) a.push(S.newId()); return a;")
    assert all(re.fullmatch(r"[a-z0-9]{8}", i) for i in ids)
    assert len(set(ids)) == 50
    assert run("return S.FORMAT_VERSION;") == 1


def test_inflate_orders_by_order_then_id():
    doc = doc_of(items={
        "c": entry(order=2),
        "b": entry(order=1),
        "a": entry(order=2),
    })
    assert tree_ids(doc) == [["b", []], ["a", []], ["c", []]]


def test_inflate_ignores_items_with_no_kind():
    doc = doc_of(items={
        "a": entry(),
        "b": {"star": True},
        "c": {"__delete__": True},
    })
    assert tree_ids(doc) == [["a", []]]


def test_inflate_ignores_bad_ids():
    text = '{"version":1,"items":{"__proto__":{"kind":"obstacle","text":"x","parent":"goal","order":1},"A1":{"kind":"obstacle","text":"x","parent":"goal","order":1},"a-b":{"kind":"obstacle","text":"x","parent":"goal","order":1},"ok":{"kind":"obstacle","text":"x","parent":"goal","order":1}}}'
    out = run(
        "const m = S.inflate(JSON.parse(D.text)); return {ids: m.obstacles.map(i => i.id), polluted: Object.prototype.kind !== undefined || ({}).kind !== undefined};",
        text=text,
    )
    assert out["ids"] == ["ok"]
    assert out["polluted"] is False


def test_inflate_puts_an_orphan_under_the_goal():
    doc = doc_of(items={"a": entry(), "b": entry(parent="gone", order=2)})
    assert tree_ids(doc) == [["a", []], ["b", []]]


def test_inflate_breaks_a_cycle_at_the_lowest_id():
    for pairs in (["a", "b"], ["b", "a"]):
        items = {}
        for i in pairs:
            items[i] = entry(parent="b" if i == "a" else "a")
        assert tree_ids(doc_of(items=items)) == [["a", [["b", []]]]]


def test_inflate_hides_plan_rows_naming_a_gone_solution():
    tree = make_map(
        key_actions=[{"text": "k", "risk": "high", "solution_ids": ["s1", "s4"]}],
        execute=[
            {"solution_id": "s1", "first_move": "", "owner": "", "others_decide": ""},
            {"solution_id": "s4", "first_move": "", "owner": "", "others_decide": ""},
        ],
    )
    expected = run("return L.deleteItem(D.map, 'o2');", map=tree)
    doc = run("const d = S.flatten(D.map); delete d.items.o2; delete d.items.s4; return d;", map=tree)
    got = inflate(doc)
    assert got["key_actions"] == expected["key_actions"]
    assert got["execute"] == expected["execute"]
    assert len(got["key_actions"]) == 1 and got["key_actions"][0]["solution_ids"] == ["s1"]
    assert [r["solution_id"] for r in got["execute"]] == ["s1"]


def test_inflate_survives_a_thin_document():
    m = inflate({"version": 1})
    assert m["obstacles"] == [] and m["goal"] == {"text": ""} and m["person"] == ""
    assert m["key_actions"] == [] and m["execute"] == []
    doc = doc_of(items={"a": {"kind": "obstacle", "text": 5, "star": True, "parent": 7, "order": "x"}})
    doc["goal"] = {"text": 3}
    doc["person"] = 9
    m = inflate(doc)
    assert m["obstacles"][0]["text"] == ""
    assert m["obstacles"][0]["star"] is False
    assert m["goal"]["text"] == "" and m["person"] == ""
    assert run("return S.inflate(null).obstacles;") == []
    assert run("return S.inflate({items: [1]}).obstacles;") == []


def test_overlay_merges_replaces_and_deletes():
    doc = doc_of(items={"a": entry(text="old"), "b": entry(order=2)})
    before = json.dumps(doc)
    out = run(
        "const copy = JSON.stringify(D.doc);"
        "const r = S.overlay(D.doc, [{items: {a: {text: 'new'}}}, {items: {b: {__delete__: true}}},"
        " {items: {c: {kind: 'solution', parent: 'a'}}}, {key_actions: [1]}]);"
        "return {r: r, same: copy === JSON.stringify(D.doc)};",
        doc=doc,
    )
    assert out["same"] and json.dumps(doc) == before
    r = out["r"]
    assert r["items"]["a"]["text"] == "new" and r["items"]["a"]["parent"] == "goal"
    assert "b" not in r["items"]
    assert r["items"]["c"] == {"kind": "solution", "parent": "a"}
    assert r["key_actions"] == [1]


def test_overlay_handles_the_marker_on_a_missing_item_and_a_nested_marker():
    doc = doc_of(items={"a": entry()})
    r = run(
        "return S.overlay(D.doc, [{items: {zz: {__delete__: true}}}, {items: {n: {x: {__delete__: true}, y: 1}}}, {items: {a: {star: true}}}]);",
        doc=doc,
    )
    assert "zz" not in r["items"]
    assert r["items"]["n"] == {"y": 1}
    assert r["items"]["a"]["star"] is True


def change(before, after, doc=None, skip=None):
    return run(
        "return S.changeBetween(D.doc, D.before, D.after, D.skip);",
        doc=doc if doc is not None else run("return S.flatten(D.map);", map=before),
        before=before,
        after=after,
        skip=skip,
    )


def test_change_for_text_names_one_field():
    before = make_map()
    after = run("return L.setItemText(D.map, 's1', 'new');", map=before)
    assert change(before, after) == {"items": {"s1": {"text": "new"}}}


def test_change_for_star_names_one_field():
    before = make_map()
    after = run("return L.setStar(D.map, 's1', true);", map=before)
    assert change(before, after) == {"items": {"s1": {"star": True}}}


def test_change_for_a_new_item_sends_all_its_fields():
    before = make_map()
    after = run("return L.addItem(D.map, 'o2', 'zz9', 'solution', 'hello');", map=before)
    assert change(before, after) == {
        "items": {"zz9": {"kind": "solution", "text": "hello", "star": False, "parent": "o2", "order": 2}}
    }
    after = run("return L.addItem(D.map, 'goal', 'zz9', 'obstacle', '');", map=before)
    assert change(before, after)["items"]["zz9"]["order"] == 4
    assert change(before, after)["items"]["zz9"]["parent"] == "goal"


def test_change_uses_the_stored_doc_for_order():
    before = make_map()
    doc = run("const d = S.flatten(D.map); d.items.other = {kind: 'obstacle', text: '', star: false, parent: 'o2', order: 40}; return d;", map=before)
    after = run("return L.addItem(D.map, 'o2', 'zz9', 'solution', '');", map=before)
    assert change(before, after, doc=doc)["items"]["zz9"]["order"] == 41


def test_change_for_a_move_sends_parent_and_order_only():
    kids = [item("n%d" % i, "t%d" % i) for i in range(100)]
    before = make_map(obstacles=[item("o1", "a", kids), item("o2", "b")])
    after = run("return L.moveItem(D.map, 'n5', 'o2');", map=before)
    assert change(before, after) == {"items": {"n5": {"parent": "o2", "order": 1}}}


def test_change_for_a_delete_marks_the_item_and_everything_under_it():
    before = make_map()
    after = run("return L.deleteItem(D.map, 'o1');", map=before)
    marks = change(before, after)["items"]
    assert marks == {i: {"__delete__": True} for i in ("o1", "o3", "o4", "s1", "s2")}


def test_change_never_names_the_plan():
    before = make_map(
        key_actions=[{"text": "k", "risk": "high", "solution_ids": ["s1"]}],
        execute=[{"solution_id": "s1", "first_move": "", "owner": "", "others_decide": ""}],
    )
    after = run("return L.deleteItem(D.map, 's1');", map=before)
    assert after["execute"] == [] or run("return L.deleteItem(D.map, 's1').execute;", map=before) == []
    c = change(before, after)
    assert list(c.keys()) == ["items"]


def test_change_skips_the_held_blank_item():
    before = make_map()
    after = run("return L.addItem(D.map, 'o2', 'zz9', 'solution', '');", map=before)
    assert change(before, after, skip="zz9") is None
    after2 = run("return L.setItemText(L.addItem(D.map, 'o2', 'zz9', 'solution', ''), 's1', 'x');", map=before)
    assert change(before, after2, skip="zz9") == {"items": {"s1": {"text": "x"}}}


def test_no_change_gives_null():
    before = make_map()
    assert change(before, json.loads(json.dumps(before))) is None


def test_goal_change_is_goal_text_only():
    before = make_map()
    after = run("return L.setGoal(D.map, {text: 'better'});", map=before)
    assert change(before, after) == {"goal": {"text": "better"}}


def test_odd_text_round_trips():
    odd = 'a <b> "q" \'s\' __proto__ </script> \\u003c'
    before = make_map()
    after = run("return L.setItemText(D.map, 's1', D.odd);", map=before, odd=odd)
    c = change(before, after)
    assert c == {"items": {"s1": {"text": odd}}}
    doc = run("return S.overlay(S.flatten(D.map), [D.c]);", map=before, c=c)
    back = run("return JSON.parse(JSON.stringify(S.inflate(D.doc)));", doc=doc)
    assert back["obstacles"][0]["children"][1]["text"] == odd


def test_unknown_version():
    assert run("return S.unknownVersion({version: 1});") is False
    assert run("return S.unknownVersion({version: 2});") is True
    assert run("return S.unknownVersion({});") is True
    assert run("return S.unknownVersion(null);") is True
