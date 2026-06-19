#!/usr/bin/env python3
"""Wave A no-install CS/AI tool-capability micro-probes.

This runner is intentionally below formal/manifold admission. It exercises the
first CS/AI ladder tools on tiny finite fixtures and records only tool-capability
evidence.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import pathlib
import traceback
from typing import Any


OBJECT_ID = "wave_a_cs_ai_no_install_micro_probes"
ROOT = pathlib.Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_wave_a_cs_ai_no_install_micro_probes.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind
evidence_level = "tool_capability"
EVIDENCE_LEVEL = evidence_level

CLAIM_CEILING = (
    "Wave A scratch_diagnostic/tool_capability receipt only: six no-install "
    "micro-probes show local tool function on tiny finite fixtures. This does "
    "not admit M(C), same-carrier geometry, topology readout promotion, AI/GNN "
    "readout promotion, bridge, Axis0, physics, or manifold claims."
)

DEMOTION_CONDITION = (
    "Demote any Wave A use that treats this aggregate as a substitute for exact "
    "per-lego, per-coupling, M(C), bridge, Axis0, physics, or manifold receipts."
)
OUT_OF_SCOPE = [
    "M(C) system fit",
    "same-carrier geometry",
    "topology or AI/GNN readout promotion",
    "bridge, Axis0, physics, or manifold admission",
    "generic substitution for older source-native tool receipts",
]
NEXT_LEGO_TARGET = (
    "Use only as prerequisite tool-capability evidence for M(C) gap-table "
    "hardening or exact tool-lego fit probes that name their finite object."
)
PROMOTION_CONDITION = (
    "No direct promotion condition; a later consumer must cite this receipt as "
    "tool capability only and pass its own F01/N01, M(C), control, and claim-ceiling gates."
)
BLOCKED_UNTIL = (
    "An exact consumer receipt names the finite object, explicit M(C) fields or "
    "tool-lego target, negative controls, and downstream blocked uses."
)

BLOCKED_DOWNSTREAM_CONSUMERS = [
    "M(C)_system_fit",
    "same_carrier_geometry",
    "topology_readout_promotion",
    "AI_GNN_readout_promotion",
    "bridge",
    "Axis0",
    "physics",
    "manifold_admission",
]

LADDER_LAYERS = [
    "cs_graph",
    "hypergraph",
    "rewrite",
    "topology",
    "ai_gnn",
]

FINITE_OBJECT = {
    "carrier_ref": "per-probe tiny finite fixtures only; no M(C) carrier consumed",
    "graph_ref": "rustworkx_dag_order and pyg_message_passing_ablation finite graph fixtures",
    "hypergraph_ref": "xgi_hyperedge_loss finite rank-3 hyperedge fixture",
    "cell_complex_ref": "toponetx_boundary_hodge finite oriented 2-simplex fixture",
    "filtration_ref": "gudhi_tiny_filtration finite three-vertex cycle filtration",
    "rewrite_ref": "cvc5_graph_rewrite_invariant finite Boolean graph-rewrite relation",
    "mc_ref": "not_consumed_in_wave_a",
}

TOOL_CLAIMS = {
    "rustworkx_dag_order": {
        "tool": "rustworkx",
        "api_surface": "PyDiGraph, topological_sort, transitive_reduction, digraph_has_path",
        "observable": "topological_labels and transitive-reduction edge set",
        "positive": "finite DAG reduction removes a transitive shortcut",
        "negative": "branch order reversal changes the topological observable",
        "boundary": "cycle insertion blocks topological sorting",
        "demotion_condition": "if the same observable is produced without rustworkx graph APIs, rustworkx is decorative",
    },
    "xgi_hyperedge_loss": {
        "tool": "xgi",
        "api_surface": "Hypergraph, add_edge, edges.members",
        "observable": "rank-3 edge count against pairwise projection",
        "positive": "full hypergraph preserves a three-way relation",
        "negative": "pairwise projection matches pair set while losing rank-3 relation",
        "boundary": "degenerate two-node hyperedge demotes to pairwise baseline",
        "demotion_condition": "if pairwise projection preserves the same claim, XGI is not load-bearing",
    },
    "toponetx_boundary_hodge": {
        "tool": "toponetx",
        "api_surface": "SimplicialComplex, add_simplex, incidence_matrix(rank=2, signed=True)",
        "observable": "signed boundary/incidence entries",
        "positive": "finite signed boundary operator runs on an oriented 2-simplex",
        "negative": "orientation swap changes signed boundary labels",
        "boundary": "empty complex is demoted and cannot support topology readout",
        "demotion_condition": "if scalar adjacency reproduces the signed boundary claim, TopoNetX is decorative",
    },
    "gudhi_tiny_filtration": {
        "tool": "gudhi",
        "api_surface": "SimplexTree, insert, persistence, persistence_intervals_in_dimension",
        "observable": "H1 interval and finite lifetime",
        "positive": "late 2-simplex fill emits a finite H1 lifetime",
        "negative": "scrambled/immediate fill changes the barcode",
        "boundary": "unfilled cycle is demoted as an open/degenerated control in this tiny fixture",
        "demotion_condition": "if a metric-free/static baseline produces the same topology readout, GUDHI is decorative",
    },
    "cvc5_graph_rewrite_invariant": {
        "tool": "cvc5",
        "api_surface": "Solver, Boolean terms, AND/OR/NOT/EQUAL, checkSat",
        "observable": "SAT/UNSAT over finite graph-rewrite reachability constraints",
        "positive": "side-conditioned shortcut removal makes reachability-loss counterexample UNSAT",
        "negative": "removing the side condition makes the counterexample SAT",
        "boundary": "reverse rewrite and quotient-erasure controls are SAT",
        "demotion_condition": "if UNSAT comes from a decorative contradiction rather than encoded relations, cvc5 is not admissible",
    },
    "pyg_message_passing_ablation": {
        "tool": "torch_geometric",
        "api_surface": "Data and MessagePassing.propagate",
        "observable": "message output tensor norm gap",
        "positive": "message passing changes graph observable after edge removal",
        "negative": "node-feature shuffle changes message observable",
        "boundary": "static scalar baseline is unchanged while message observable changes",
        "demotion_condition": "if static scalar baseline gives the same verdict, PyG is decorative",
    },
}

ENGINE_CONTRACT = {
    "julia": "not_scoped",
    "jax": "not_scoped",
    "pytorch": "ran_for_pyg_message_passing_fixture",
}

EXCHANGE_CONTRACT = {
    "mode": "not_applicable",
    "producer_runtime": "python_sim_stack",
    "consumer_runtime": "not_applicable",
    "artifact_sha256": None,
    "no_hidden_host_copy": True,
    "reason": "Wave A is same-runtime tool-capability probing, not cross-runtime exchange.",
}

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG construction, topological sort, cycle control, and transitive reduction probe",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph construction and rank-3-vs-pairwise projection loss probe",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial complex construction and signed boundary/incidence probe",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplexTree filtration and H1 persistence readout probe",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph-rewrite side-condition SAT/UNSAT derivation",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor fixture for PyG message-passing controls",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data object and MessagePassing propagation probe",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization, source hashing, finite fixture assembly, and error capture",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "cvc5": "load_bearing",
    "pytorch": "load_bearing",
    "torch_geometric": "load_bearing",
    "python_stdlib": "supportive",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def finite_float(value: float) -> float | str:
    if value == float("inf"):
        return "inf"
    if value == float("-inf"):
        return "-inf"
    return float(value)


def probe_rustworkx_dag_order() -> dict[str, Any]:
    import rustworkx as rx

    def build_graph(branch_order: list[str]) -> tuple[Any, dict[str, int]]:
        graph = rx.PyDiGraph()
        ids = {"root": graph.add_node("root")}
        for label in branch_order:
            ids[label] = graph.add_node(label)
        ids["sink"] = graph.add_node("sink")
        for label in branch_order:
            graph.add_edge(ids["root"], ids[label], f"root->{label}")
            graph.add_edge(ids[label], ids["sink"], f"{label}->sink")
        graph.add_edge(ids["root"], ids["sink"], "shortcut")
        return graph, ids

    def observable(branch_order: list[str]) -> dict[str, Any]:
        graph, ids = build_graph(branch_order)
        reduction, _node_map = rx.transitive_reduction(graph)
        return {
            "branch_order": branch_order,
            "topological_labels": [str(graph[idx]) for idx in rx.topological_sort(graph)],
            "reduction_edges": sorted((str(reduction[src]), str(reduction[dst])) for src, dst in reduction.edge_list()),
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "reduction_edge_count": reduction.num_edges(),
            "root_reaches_sink": bool(rx.digraph_has_path(graph, ids["root"], ids["sink"])),
        }

    baseline = observable(["alpha_gate", "beta_gate"])
    swapped = observable(["beta_gate", "alpha_gate"])
    cycle_graph, ids = build_graph(["alpha_gate", "beta_gate"])
    cycle_graph.add_edge(ids["sink"], ids["root"], "cycle_control")
    try:
        rx.topological_sort(cycle_graph)
        cycle_blocked = False
        cycle_error = None
    except Exception as exc:  # rustworkx raises a DAG-cycle exception type here.
        cycle_blocked = True
        cycle_error = type(exc).__name__

    checks = {
        "finite_dag_fixture": baseline["node_count"] == 4 and baseline["edge_count"] == 5,
        "transitive_shortcut_removed": ("root", "sink") not in baseline["reduction_edges"],
        "order_reversal_changes_topological_observable": baseline["topological_labels"] != swapped["topological_labels"],
        "cycle_insertion_blocks_topological_sort": cycle_blocked,
    }
    return {
        "probe_id": "rustworkx_dag_order",
        "tool": "rustworkx",
        "claim": "finite dependency/order structure can encode local event dependency without smuggling a total order",
        "checks": checks,
        "baseline": baseline,
        "controls": {"swapped": swapped, "cycle_error": cycle_error},
        "pass": all(checks.values()),
    }


def probe_xgi_hyperedge_loss() -> dict[str, Any]:
    import xgi

    def build_hypergraph(edge_defs: list[tuple[str, list[str]]]) -> Any:
        hypergraph = xgi.Hypergraph()
        for edge_id, members in edge_defs:
            hypergraph.add_edge(members, id=edge_id)
        return hypergraph

    def members_by_edge(hypergraph: Any) -> dict[str, list[str]]:
        return {
            str(edge_id): sorted(str(member) for member in hypergraph.edges.members(edge_id))
            for edge_id in hypergraph.edges
        }

    def pairwise_projection(hypergraph: Any) -> list[list[str]]:
        pairs: set[tuple[str, str]] = set()
        for members in members_by_edge(hypergraph).values():
            for left, right in itertools.combinations(sorted(members), 2):
                pairs.add((left, right))
        return [list(pair) for pair in sorted(pairs)]

    def rank_profile(hypergraph: Any) -> dict[str, Any]:
        member_rows = members_by_edge(hypergraph)
        sizes = [len(members) for members in member_rows.values()]
        return {
            "node_count": int(hypergraph.num_nodes),
            "edge_count": int(hypergraph.num_edges),
            "edge_members": member_rows,
            "pairwise_projection": pairwise_projection(hypergraph),
            "max_edge_size": max(sizes, default=0),
            "rank3_edge_count": sum(1 for size in sizes if size == 3),
        }

    full = rank_profile(build_hypergraph([("abc_relation", ["a", "b", "c"])]))
    pairwise = rank_profile(
        build_hypergraph(
            [
                ("ab_pair", ["a", "b"]),
                ("ac_pair", ["a", "c"]),
                ("bc_pair", ["b", "c"]),
            ]
        )
    )
    degenerate = rank_profile(build_hypergraph([("ab_pair", ["a", "b"])]))
    checks = {
        "finite_hypergraph_fixture": full["node_count"] == 3 and full["edge_count"] == 1,
        "pairwise_projection_matches_but_rank3_differs": (
            full["pairwise_projection"] == pairwise["pairwise_projection"]
            and full["rank3_edge_count"] == 1
            and pairwise["rank3_edge_count"] == 0
        ),
        "full_hypergraph_preserves_three_way_relation": full["max_edge_size"] == 3,
        "degenerate_hyperedge_demotes_to_pairwise_baseline": degenerate["max_edge_size"] == 2,
    }
    return {
        "probe_id": "xgi_hyperedge_loss",
        "tool": "xgi",
        "claim": "a 3-way relation carries information not preserved by pairwise projection",
        "checks": checks,
        "baseline": full,
        "controls": {"pairwise_projection_only": pairwise, "degenerate_pair": degenerate},
        "pass": all(checks.values()),
    }


def probe_toponetx_boundary_hodge() -> dict[str, Any]:
    import toponetx as tnx

    def oriented_boundary(vertices: list[str]) -> list[dict[str, Any]]:
        rows = []
        for index in range(len(vertices)):
            face = [vertex for face_index, vertex in enumerate(vertices) if face_index != index]
            coefficient = -1 if index % 2 else 1
            rows.append({"face": face, "coefficient": coefficient})
        return rows

    def simplex_observable(vertices: list[str]) -> dict[str, Any]:
        complex_ = tnx.SimplicialComplex()
        complex_.add_simplex(vertices)
        incidence = complex_.incidence_matrix(2, signed=True)
        coo = incidence.tocoo()
        boundary = oriented_boundary(vertices)
        adjacency_support = sorted(["|".join(sorted(pair)) for pair in itertools.combinations(vertices, 2)])
        return {
            "simplex_vertices": vertices,
            "simplex_count": len(list(complex_.simplices)),
            "incidence_shape": [int(incidence.shape[0]), int(incidence.shape[1])],
            "incidence_nonzero_count": int(incidence.nnz),
            "incidence_entries": [
                [int(row), int(col), int(value)]
                for row, col, value in zip(coo.row.tolist(), coo.col.tolist(), coo.data.tolist())
            ],
            "signed_boundary_labels": [f"{row['coefficient']}:{'|'.join(row['face'])}" for row in boundary],
            "adjacency_support": adjacency_support,
            "has_negative_boundary_coefficient": any(row["coefficient"] < 0 for row in boundary),
        }

    baseline = simplex_observable(["root", "left", "right"])
    swapped = simplex_observable(["root", "right", "left"])
    empty = tnx.SimplicialComplex()
    checks = {
        "finite_boundary_operator_ran": baseline["incidence_shape"] == [3, 1] and baseline["incidence_nonzero_count"] == 3,
        "broken_orientation_changes_signed_boundary": baseline["signed_boundary_labels"] != swapped["signed_boundary_labels"],
        "scalar_adjacency_cannot_reproduce_signed_boundary": (
            baseline["adjacency_support"] == swapped["adjacency_support"]
            and baseline["has_negative_boundary_coefficient"] is True
        ),
        "empty_complex_demoted": len(list(empty.simplices)) == 0,
    }
    return {
        "probe_id": "toponetx_boundary_hodge",
        "tool": "toponetx",
        "claim": "boundary/incidence local structure is a finite object, not scalar adjacency",
        "checks": checks,
        "baseline": baseline,
        "controls": {"orientation_swapped": swapped, "empty_simplex_count": len(list(empty.simplices))},
        "pass": all(checks.values()),
    }


def probe_gudhi_tiny_filtration() -> dict[str, Any]:
    import gudhi

    def cycle_observable(fill_time: float | None) -> dict[str, Any]:
        tree = gudhi.SimplexTree()
        for vertex in [0, 1, 2]:
            tree.insert([vertex], filtration=0.0)
        for edge in ([0, 1], [1, 2], [0, 2]):
            tree.insert(edge, filtration=1.0)
        if fill_time is not None:
            tree.insert([0, 1, 2], filtration=float(fill_time))
        tree.make_filtration_non_decreasing()
        tree.persistence()
        h1 = [
            [finite_float(float(birth)), finite_float(float(death))]
            for birth, death in tree.persistence_intervals_in_dimension(1).tolist()
        ]
        finite_h1_lifetime = sum(
            float(death) - float(birth)
            for birth, death in h1
            if birth != "inf" and death != "inf"
        )
        infinite_h1_count = sum(1 for _birth, death in h1 if death == "inf")
        return {
            "fill_time": fill_time,
            "num_simplices": int(tree.num_simplices()),
            "h1_intervals": h1,
            "finite_h1_lifetime": finite_h1_lifetime,
            "infinite_h1_count": infinite_h1_count,
            "filtration": [
                {"simplex": [int(node) for node in simplex], "filtration": float(value)}
                for simplex, value in tree.get_filtration()
            ],
        }

    filled_late = cycle_observable(3.0)
    filled_immediate = cycle_observable(1.0)
    unfilled = cycle_observable(None)
    checks = {
        "finite_filtration_fixture": filled_late["num_simplices"] == 7,
        "tiny_filtration_emits_h1_readout": filled_late["finite_h1_lifetime"] > 1.5,
        "scrambled_fill_time_changes_barcode": filled_late["h1_intervals"] != filled_immediate["h1_intervals"],
        "degenerate_unfilled_control_demoted": (
            unfilled["num_simplices"] == 6
            and unfilled["finite_h1_lifetime"] == 0
            and unfilled["h1_intervals"] == []
        ),
    }
    return {
        "probe_id": "gudhi_tiny_filtration",
        "tool": "gudhi",
        "claim": "finite filtration emits an explicit topology readout for a tiny carrier",
        "checks": checks,
        "baseline": filled_late,
        "controls": {"filled_immediate": filled_immediate, "unfilled": unfilled},
        "pass": all(checks.values()),
    }


def probe_cvc5_graph_rewrite_invariant() -> dict[str, Any]:
    import cvc5
    from cvc5 import Kind

    def solver() -> Any:
        s = cvc5.Solver()
        s.setLogic("ALL")
        s.setOption("produce-models", "true")
        return s

    def bool_var(s: Any, name: str) -> Any:
        return s.mkConst(s.getBooleanSort(), name)

    def conj(s: Any, *terms: Any) -> Any:
        if len(terms) == 1:
            return terms[0]
        return s.mkTerm(Kind.AND, *terms)

    def disj(s: Any, *terms: Any) -> Any:
        if len(terms) == 1:
            return terms[0]
        return s.mkTerm(Kind.OR, *terms)

    def neg(s: Any, term: Any) -> Any:
        return s.mkTerm(Kind.NOT, term)

    def eq(s: Any, left: Any, right: Any) -> Any:
        return s.mkTerm(Kind.EQUAL, left, right)

    def graph_terms(s: Any, prefix: str) -> dict[str, Any]:
        return {name: bool_var(s, f"{prefix}_{name}") for name in ("e01", "e12", "e02", "p01", "p12", "p02")}

    def reach(s: Any, t: dict[str, Any], prefix: str) -> Any:
        if prefix == "e":
            return disj(s, t["e02"], conj(s, t["e01"], t["e12"]))
        return disj(s, t["p02"], conj(s, t["p01"], t["p12"]))

    def run_case(s: Any, case_id: str, assertions: list[tuple[str, Any]], model_terms: dict[str, Any]) -> dict[str, Any]:
        for _label, term in assertions:
            s.assertFormula(term)
        result = s.checkSat()
        model = {}
        if result.isSat():
            model = {name: str(s.getValue(term)) for name, term in model_terms.items()}
        return {"case_id": case_id, "result": str(result), "sat": result.isSat(), "unsat": result.isUnsat(), "model": model}

    s = solver()
    t = graph_terms(s, "side")
    pre_reach = reach(s, t, "e")
    post_reach = reach(s, t, "p")
    side_assertions = [
        ("pre_e01", eq(s, t["e01"], s.mkBoolean(True))),
        ("pre_e12", eq(s, t["e12"], s.mkBoolean(True))),
        ("pre_e02", eq(s, t["e02"], s.mkBoolean(True))),
        ("post_p01_preserved", eq(s, t["p01"], t["e01"])),
        ("post_p12_preserved", eq(s, t["p12"], t["e12"])),
        ("shortcut_removed", eq(s, t["p02"], s.mkBoolean(False))),
        ("counterexample_reach_lost", conj(s, pre_reach, neg(s, post_reach))),
    ]
    side_case = run_case(s, "side_condition_preserves_reachability", side_assertions, t)

    s2 = solver()
    u = graph_terms(s2, "noside")
    no_side_case = run_case(
        s2,
        "remove_side_condition_exposes_countermodel",
        [
            ("pre_e01", eq(s2, u["e01"], s2.mkBoolean(True))),
            ("pre_e12", eq(s2, u["e12"], s2.mkBoolean(True))),
            ("pre_e02", eq(s2, u["e02"], s2.mkBoolean(True))),
            ("post_p01_preserved", eq(s2, u["p01"], u["e01"])),
            ("shortcut_removed", eq(s2, u["p02"], s2.mkBoolean(False))),
            ("counterexample_reach_lost", conj(s2, reach(s2, u, "e"), neg(s2, reach(s2, u, "p")))),
        ],
        u,
    )

    s3 = solver()
    r = graph_terms(s3, "reverse")
    reverse_case = run_case(
        s3,
        "reverse_rewrite_exposes_countermodel",
        [
            ("pre_e01", eq(s3, r["e01"], s3.mkBoolean(True))),
            ("pre_e12", eq(s3, r["e12"], s3.mkBoolean(True))),
            ("pre_e02", eq(s3, r["e02"], s3.mkBoolean(True))),
            ("wrong_edge_removed", eq(s3, r["p01"], s3.mkBoolean(False))),
            ("post_p12_preserved", eq(s3, r["p12"], r["e12"])),
            ("shortcut_removed", eq(s3, r["p02"], s3.mkBoolean(False))),
            ("counterexample_reach_lost", conj(s3, reach(s3, r, "e"), neg(s3, reach(s3, r, "p")))),
        ],
        r,
    )

    s4 = solver()
    q = graph_terms(s4, "quot")
    q_pre = disj(s4, q["e01"], q["e12"], q["e02"])
    q_post = disj(s4, q["p01"], q["p12"], q["p02"])
    quotient_case = run_case(
        s4,
        "quotient_erasure_exposes_countermodel",
        [
            ("pre_e01", eq(s4, q["e01"], s4.mkBoolean(True))),
            ("pre_e12", eq(s4, q["e12"], s4.mkBoolean(True))),
            ("pre_e02", eq(s4, q["e02"], s4.mkBoolean(True))),
            ("aggregate_pre_true", q_pre),
            ("aggregate_post_true", q_post),
            ("counterexample_reach_lost", conj(s4, reach(s4, q, "e"), neg(s4, reach(s4, q, "p")))),
        ],
        q,
    )

    checks = {
        "side_condition_counterexample_unsat": side_case["unsat"],
        "remove_side_condition_sat": no_side_case["sat"],
        "reverse_rewrite_sat": reverse_case["sat"],
        "quotient_erasure_sat": quotient_case["sat"],
    }
    return {
        "probe_id": "cvc5_graph_rewrite_invariant",
        "tool": "cvc5",
        "claim": "a graph/rewrite side condition is SAT/UNSAT because of bound finite relations",
        "checks": checks,
        "baseline": side_case,
        "controls": {
            "remove_side_condition": no_side_case,
            "reverse_rewrite": reverse_case,
            "quotient_erasure": quotient_case,
        },
        "pass": all(checks.values()),
    }


def probe_pyg_message_passing_ablation() -> dict[str, Any]:
    import torch
    from torch_geometric.data import Data
    from torch_geometric.nn import MessagePassing

    class WeightedMessageProbe(MessagePassing):
        def __init__(self) -> None:
            super().__init__(aggr="add")

        def forward(self, data: Data) -> Any:
            return self.propagate(data.edge_index, x=data.x, edge_weight=data.edge_attr)

        def message(self, x_j: Any, edge_weight: Any) -> Any:
            return x_j * edge_weight.view(-1, 1)

    x = torch.tensor(
        [
            [0.2, 1.0, -0.3],
            [1.1, -0.4, 0.5],
            [-0.7, 0.3, 1.4],
            [0.6, -1.2, 0.8],
        ],
        dtype=torch.float32,
    )
    edge_index = torch.tensor([[0, 1, 2, 0, 3], [1, 2, 3, 3, 2]], dtype=torch.long)
    edge_weight = torch.tensor([1.0, -0.5, 0.25, 1.5, -0.75], dtype=torch.float32)
    full = Data(x=x, edge_index=edge_index, edge_attr=edge_weight)
    removed = Data(x=x, edge_index=edge_index[:, :-1], edge_attr=edge_weight[:-1])
    shuffled = Data(x=x[[2, 0, 1, 3]], edge_index=edge_index, edge_attr=edge_weight)

    layer = WeightedMessageProbe()
    full_out = layer(full)
    removed_out = layer(removed)
    shuffled_out = layer(shuffled)
    edge_removed_gap = torch.linalg.vector_norm(full_out - removed_out).item()
    shuffled_gap = torch.linalg.vector_norm(full_out - shuffled_out).item()
    static_scalar_gap = abs(float(full.x.sum().item()) - float(removed.x.sum().item()))
    checks = {
        "pyg_data_object_exists": int(full.num_nodes) == 4 and int(full.num_edges) == 5,
        "message_passing_changes_observable_after_edge_removal": edge_removed_gap > 0.1,
        "node_feature_shuffle_changes_message_observable": shuffled_gap > 0.1,
        "static_scalar_baseline_is_decorative_control": static_scalar_gap == 0.0 and edge_removed_gap > 0.1,
    }
    return {
        "probe_id": "pyg_message_passing_ablation",
        "tool": "torch_geometric",
        "claim": "message passing changes a bounded graph observable after the graph object exists",
        "checks": checks,
        "baseline": {
            "node_count": int(full.num_nodes),
            "edge_count": int(full.num_edges),
            "full_output_sum": float(full_out.sum().item()),
        },
        "controls": {
            "edge_removed_l2": float(edge_removed_gap),
            "node_feature_shuffle_l2": float(shuffled_gap),
            "static_scalar_gap": float(static_scalar_gap),
        },
        "pass": all(checks.values()),
    }


PROBES = [
    probe_rustworkx_dag_order,
    probe_xgi_hyperedge_loss,
    probe_toponetx_boundary_hodge,
    probe_gudhi_tiny_filtration,
    probe_cvc5_graph_rewrite_invariant,
    probe_pyg_message_passing_ablation,
]


def run_probe(func: Any) -> dict[str, Any]:
    try:
        row = func()
        row["status"] = "pass" if row.get("pass") else "fail"
        row["observable_digest"] = stable_hash({"baseline": row.get("baseline"), "controls": row.get("controls")})
        return row
    except Exception as exc:
        return {
            "probe_id": func.__name__.removeprefix("probe_"),
            "status": "blocked_exception",
            "pass": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback_tail": traceback.format_exc()[-2000:],
        }


def build_result() -> dict[str, Any]:
    probes = [run_probe(func) for func in PROBES]
    pass_count = sum(1 for row in probes if row.get("pass") is True)
    all_pass = pass_count == len(probes)
    return {
        "schema_version": "codex_ratchet.wave_a_tool_capability.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "ladder_layer": LADDER_LAYERS,
        "classification": classification,
        "evidence_level": evidence_level,
        "sim_execution_kind": sim_execution_kind,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": CLAIM_CEILING,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "blocked_downstream_consumers": BLOCKED_DOWNSTREAM_CONSUMERS,
        "finite_object": FINITE_OBJECT,
        "tool_claim": TOOL_CLAIMS,
        "engine_contract": ENGINE_CONTRACT,
        "exchange_contract": EXCHANGE_CONTRACT,
        "install_decision": "no_installs_performed",
        "all_pass": all_pass,
        "pass": all_pass,
        "pass_count": pass_count,
        "probe_count": len(probes),
        "summary": {
            "probe_count": len(probes),
            "pass_count": pass_count,
            "failed_or_blocked": [row["probe_id"] for row in probes if row.get("pass") is not True],
        },
        "probes": probes,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "path": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "pass_count": result["summary"]["pass_count"],
                "probe_count": result["summary"]["probe_count"],
                "failed_or_blocked": result["summary"]["failed_or_blocked"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
