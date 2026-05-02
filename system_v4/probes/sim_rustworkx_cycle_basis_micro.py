#!/usr/bin/env python3
"""
sim_rustworkx_cycle_basis_micro.py

Tool-stage MICRO probe for one rustworkx function surface:
PyGraph plus rustworkx.cycle_basis over tiny undirected non-DAG fixtures.

This is pre-lego evidence. It isolates whether rustworkx can expose bounded
cycle-basis witnesses and acyclic exclusions before later graph-stage work
relies on that surface. It does not claim hypergraph, cell-complex, bridge,
or downstream lego semantics.
"""

from __future__ import annotations

import json
import os


classification = "canonical"
NAME = "sim_rustworkx_cycle_basis_micro"
PROBE_FAMILY = "rustworkx_pygraph_cycle_basis_micro"
CONSTRAINT_SET = "tiny_undirected_cycle_basis_detection"

_NOT_USED_REASON = (
    "not used: this MICRO isolates rustworkx PyGraph cycle_basis only; "
    "cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "under test: PyGraph plus rustworkx.cycle_basis over tiny undirected fixtures",
    },
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"

try:
    import rustworkx as rx

    RX_AVAILABLE = True
    RX_VERSION = getattr(rx, "__version__", "unknown")
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except Exception as exc:  # pragma: no cover - runner records dependency absence
    rx = None
    RX_AVAILABLE = False
    RX_VERSION = None
    TOOL_MANIFEST["rustworkx"]["reason"] = f"not installed: {exc}"


def _build_graph(nodes: list[str], edges: list[tuple[str, str]]):
    assert rx is not None, "rustworkx is required"
    graph = rx.PyGraph()
    node_ids = {name: graph.add_node(name) for name in nodes}
    for left, right in edges:
        graph.add_edge(node_ids[left], node_ids[right], {"edge": f"{left}-{right}"})
    return graph, node_ids, {idx: name for name, idx in node_ids.items()}


def _cycle_basis_names(nodes: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    graph, _node_ids, id_to_name = _build_graph(nodes, edges)
    return [sorted(id_to_name[node_id] for node_id in cycle) for cycle in rx.cycle_basis(graph)]


def _has_named_cycle(cycles: list[list[str]], expected: set[str]) -> bool:
    return any(set(cycle) == expected for cycle in cycles)


def run_positive_tests():
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"passed": False, "detail": "rustworkx missing"}}

    triangle_cycles = _cycle_basis_names(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c"), ("c", "a")],
    )
    square_cycles = _cycle_basis_names(
        ["north", "east", "south", "west"],
        [("north", "east"), ("east", "south"), ("south", "west"), ("west", "north")],
    )

    return {
        "triangle_cycle_basis_detects_one_3_cycle": {
            "passed": len(triangle_cycles) == 1 and _has_named_cycle(triangle_cycles, {"a", "b", "c"}),
            "expected": "one cycle-basis witness containing the three triangle nodes",
            "cycle_basis": triangle_cycles,
            "admission_note": "The undirected triangle is the smallest non-DAG cycle fixture.",
        },
        "square_cycle_basis_detects_one_4_cycle": {
            "passed": (
                len(square_cycles) == 1
                and _has_named_cycle(square_cycles, {"north", "east", "south", "west"})
            ),
            "expected": "one cycle-basis witness containing the four square nodes",
            "cycle_basis": square_cycles,
            "admission_note": "The square checks a longer simple cycle without adding chords.",
        },
    }


def run_negative_tests():
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"passed": False, "detail": "rustworkx missing"}}

    tree_cycles = _cycle_basis_names(
        ["root", "left", "right", "leaf"],
        [("root", "left"), ("root", "right"), ("right", "leaf")],
    )
    path_cycles = _cycle_basis_names(
        ["a", "b", "c"],
        [("a", "b"), ("b", "c")],
    )

    return {
        "tree_excluded_as_acyclic": {
            "passed": tree_cycles == [],
            "expected": "cycle_basis returns no cycles for a connected tree",
            "cycle_basis": tree_cycles,
            "exclusion_note": "A branching tree has no undirected cycle witness.",
        },
        "path_excluded_as_acyclic": {
            "passed": path_cycles == [],
            "expected": "cycle_basis returns no cycles for a simple path",
            "cycle_basis": path_cycles,
            "exclusion_note": "A length-two path checks the minimal non-singleton acyclic case.",
        },
    }


def run_boundary_tests():
    if not RX_AVAILABLE:
        return {"rustworkx_available": {"passed": False, "detail": "rustworkx missing"}}

    singleton_cycles = _cycle_basis_names(["only"], [])
    self_loop_cycles = _cycle_basis_names(["loop"], [("loop", "loop")])

    return {
        "singleton_has_empty_cycle_basis": {
            "passed": singleton_cycles == [],
            "expected": "single isolated node has no cycle-basis witness",
            "cycle_basis": singleton_cycles,
            "boundary_note": "The singleton boundary is explicit and remains acyclic.",
        },
        "self_loop_reports_single_node_cycle": {
            "passed": len(self_loop_cycles) == 1 and self_loop_cycles[0] == ["loop"],
            "expected": "a self-loop is reported as a one-node cycle by rustworkx 0.17.x",
            "cycle_basis": self_loop_cycles,
            "boundary_note": "This records rustworkx's stable observed self-loop boundary, not a bridge claim.",
        },
    }


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    if RX_AVAILABLE:
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "load-bearing: PyGraph and rustworkx.cycle_basis produce every cycle "
            "admission, acyclic exclusion, and singleton/self-loop boundary result"
        )

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "rustworkx_version": RX_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "NetworkX can independently cross-check tiny undirected cycle bases.",
            "Other rustworkx graph algorithms may be useful later, but this receipt covers only cycle_basis.",
        ],
        "demotion_condition": (
            "Demote rustworkx for this surface if PyGraph plus cycle_basis fails "
            "to report the triangle or square cycle, reports a cycle for the tree "
            "or path fixtures, or changes the explicit singleton/self-loop boundary "
            "without a corresponding probe update."
        ),
        "out_of_scope": [
            "no lego promotion",
            "no tool-tool coupling",
            "no hypergraph incidence",
            "no cell-complex boundary operator",
            "no bridge semantics",
            "no directed DAG reachability claim",
            "no proof of the whole rustworkx library",
        ],
        "criteria_checked": [
            "C1 triangle cycle_basis witness exists",
            "C2 square cycle_basis witness exists",
            "C3 tree and path fixtures are excluded as acyclic",
            "C4 singleton and self-loop boundaries are explicit",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
