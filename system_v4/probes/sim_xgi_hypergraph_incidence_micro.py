#!/usr/bin/env python3
"""XGI hypergraph incidence micro probe.

Tool-stage scope:
  - one tool: XGI
  - one API surface: Hypergraph construction plus node-edge incidence and
    edge membership queries
  - one tiny claim: XGI distinguishes incidence, non-incidence, edge size,
    node degree, singleton-edge boundary, and empty/no-edge boundary on a
    tiny hypergraph fixture.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import xgi

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_xgi_hypergraph_incidence_micro"
PROBE_FAMILY = "xgi_hypergraph_incidence_micro"
CONSTRAINT_SET = "tiny_hypergraph_node_edge_incidence_membership"

_NOT_USED_REASON = (
    "not used: this micro probe isolates XGI Hypergraph incidence and edge "
    "membership queries only; cross-tool coupling and lego promotion are out "
    "of scope."
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
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {
        "tried": True,
        "used": True,
        "reason": (
            "XGI is load-bearing: Hypergraph construction, edges.members, "
            "nodes.memberships, edges.size, and nodes.degree produce the "
            "incidence and membership verdicts."
        ),
    },
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["xgi"] = "load_bearing"


def build_fixture():
    """Build a tiny labeled hypergraph with one 3-edge and one singleton."""
    hypergraph = xgi.Hypergraph()
    hypergraph.add_edge(["alpha", "beta", "gamma"], idx="triple")
    hypergraph.add_edge(["gamma"], idx="singleton")
    return hypergraph


def _members(hypergraph, edge_id):
    return set(hypergraph.edges.members(edge_id))


def _memberships(hypergraph, node_id):
    return set(hypergraph.nodes.memberships(node_id))


def run_positive_tests():
    hypergraph = build_fixture()
    triple_members = _members(hypergraph, "triple")
    gamma_memberships = _memberships(hypergraph, "gamma")
    edge_sizes = hypergraph.edges.size.asdict()
    node_degrees = hypergraph.nodes.degree.asdict()

    return {
        "edge_membership_recovers_triple": {
            "passed": triple_members == {"alpha", "beta", "gamma"},
            "expected": ["alpha", "beta", "gamma"],
            "observed": sorted(triple_members),
            "admission_note": (
                "The constructed hyperedge preserves a three-node membership "
                "set without collapsing it to pairwise graph edges."
            ),
        },
        "node_incidence_recovers_two_edges": {
            "passed": gamma_memberships == {"triple", "singleton"},
            "expected": ["singleton", "triple"],
            "observed": sorted(gamma_memberships),
        },
        "edge_size_and_degree_are_distinguished": {
            "passed": edge_sizes == {"triple": 3, "singleton": 1}
            and node_degrees == {"alpha": 1, "beta": 1, "gamma": 2},
            "expected_edge_sizes": {"triple": 3, "singleton": 1},
            "observed_edge_sizes": edge_sizes,
            "expected_node_degrees": {"alpha": 1, "beta": 1, "gamma": 2},
            "observed_node_degrees": node_degrees,
        },
    }


def run_negative_tests():
    hypergraph = build_fixture()
    triple_members = _members(hypergraph, "triple")
    beta_memberships = _memberships(hypergraph, "beta")
    edge_members = hypergraph.edges.members(dtype=dict)

    nonexistent_pair = {"alpha", "gamma"}

    return {
        "non_member_excluded_from_triple": {
            "passed": "delta" not in triple_members,
            "excluded_node": "delta",
            "observed_triple_members": sorted(triple_members),
            "exclusion_note": (
                "XGI edge membership queries do not admit nodes absent from "
                "the constructed hyperedge."
            ),
        },
        "node_not_incident_to_singleton_is_excluded": {
            "passed": "singleton" not in beta_memberships,
            "node": "beta",
            "excluded_edge": "singleton",
            "observed_incident_edges": sorted(beta_memberships),
        },
        "implicit_pair_edge_is_not_created": {
            "passed": frozenset(nonexistent_pair)
            not in {frozenset(members) for members in edge_members.values()},
            "excluded_edge_members": sorted(nonexistent_pair),
            "observed_edges": {
                edge_id: sorted(members) for edge_id, members in edge_members.items()
            },
            "exclusion_note": (
                "Membership inside a 3-node hyperedge is not evidence that "
                "the two-node subset was separately constructed as an edge."
            ),
        },
    }


def run_boundary_tests():
    hypergraph = build_fixture()
    empty = xgi.Hypergraph()

    singleton_members = _members(hypergraph, "singleton")
    singleton_memberships = _memberships(hypergraph, "gamma")

    return {
        "singleton_edge_boundary": {
            "passed": singleton_members == {"gamma"}
            and hypergraph.edges.size.asdict()["singleton"] == 1
            and "singleton" in singleton_memberships,
            "expected_members": ["gamma"],
            "observed_members": sorted(singleton_members),
            "observed_gamma_incidence": sorted(singleton_memberships),
            "boundary_note": (
                "A singleton hyperedge remains a valid one-node edge and still "
                "contributes to the incident node degree."
            ),
        },
        "empty_hypergraph_no_edge_boundary": {
            "passed": empty.num_nodes == 0
            and empty.num_edges == 0
            and list(empty.nodes) == []
            and list(empty.edges) == [],
            "expected": {"num_nodes": 0, "num_edges": 0, "nodes": [], "edges": []},
            "observed": {
                "num_nodes": empty.num_nodes,
                "num_edges": empty.num_edges,
                "nodes": list(empty.nodes),
                "edges": list(empty.edges),
            },
            "boundary_note": (
                "The no-edge boundary stays empty and does not fabricate "
                "incidence records."
            ),
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
        "operation_sequence": [
            "construct an XGI Hypergraph with one labeled three-node hyperedge and one labeled singleton hyperedge",
            "query edge members for the three-node hyperedge and singleton edge",
            "query node memberships for a node shared by both edges and a node incident to only one edge",
            "query edge sizes and node degrees",
            "run non-member, non-incident edge, and implicit pair-edge graveyards",
            "run singleton-edge and empty-hypergraph boundary controls",
        ],
        "carrier_topology": (
            "finite labeled hypergraph incidence fixture; no simplicial complex, "
            "cell complex, manifold, bridge, axis, GStack, QIT engine, or nonclassical claim"
        ),
        "observable": (
            "edge membership sets, node incident-edge sets, edge-size map, "
            "node-degree map, empty graph counts, and absent-edge membership predicates"
        ),
        "pass_fail_predicate": (
            "constructed edge memberships and node incidences match the declared "
            "fixture; absent nodes, non-incident singleton membership, and implicit "
            "pair edges are excluded; singleton and empty boundaries behave as declared"
        ),
        "graveyards": [
            "absent node delta must not appear in the triple hyperedge",
            "node beta must not be incident to the singleton edge",
            "membership of alpha and gamma inside a triple must not fabricate a separate pair edge",
        ],
        "baselines": [
            "declared Python set membership for the tiny hyperedge fixture",
            "singleton edge as a one-node incidence boundary",
            "empty Hypergraph as a no-node/no-edge boundary",
        ],
        "alternative_formulations": [
            "NetworkX bipartite incidence graph projection as a lossy baseline",
            "TopoNetX cell-complex incidence only after a separate tool-tool coupling receipt",
            "manual incidence matrix construction from the same edge dictionary",
        ],
        "tool_function_needs": {
            "xgi": [
                "Hypergraph",
                "add_edge",
                "edges.members",
                "nodes.memberships",
                "edges.size.asdict",
                "nodes.degree.asdict",
            ],
        },
        "lego_coupling_target": "bounded XGI hypergraph incidence function evidence before hypergraph or graph-cell lego fit packets",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other XGI hypergraph APIs may remain useful; this micro receipt "
            "only covers construction plus node-edge incidence and edge "
            "membership queries."
        ],
        "demotion_condition": (
            "Demote XGI for this function surface if Hypergraph construction "
            "cannot preserve explicit edge membership sets, if node "
            "memberships fail to distinguish incident from non-incident edges, "
            "if edge size or node degree disagrees with the tiny fixture, or "
            "if singleton and empty/no-edge boundaries fabricate or drop "
            "incidence records."
        ),
        "out_of_scope": [
            "no higher-order contagion or dynamics claim",
            "no simplicial complex or cell complex lifting claim",
            "no hypergraph Laplacian claim",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole XGI library",
        ],
        "criteria_checked": [
            "XGI Hypergraph construction from labeled tiny fixtures",
            "edge membership recovery for a three-node hyperedge",
            "node-edge incidence recovery for a shared node",
            "non-incidence and absent-edge exclusion",
            "edge size and node degree queries",
            "singleton edge and empty/no-edge boundary behavior",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_xgi_hypergraph_incidence_micro",
        target="Use as bounded XGI hypergraph incidence function evidence before hypergraph or graph-cell lego fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
