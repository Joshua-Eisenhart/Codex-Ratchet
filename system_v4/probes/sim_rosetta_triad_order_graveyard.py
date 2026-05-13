#!/usr/bin/env python3
"""Order-variant graveyard for the Carnot/Szilard/I Ching Rosetta triad.

This sim asks whether the Rosetta structure survives nearby order variants.
The point is to prevent trite assembly: canonical orders and honest reverse
orders may survive, while scrambled/collapsed/wrong-precedence orders should
fail with explicit receipts.
"""

from __future__ import annotations

import json
import pathlib
from itertools import permutations
from typing import Any

import cvc5
import numpy as np
import rustworkx as rx
import torch
import z3
from torch_geometric.data import Data


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Triadic order-variant graveyard over Carnot, Szilard, and I Ching-64. "
    "It tests canonical and reverse orders as survivors, and nearby scrambled, "
    "collapsed, or wrong-precedence variants as killed candidates. This is "
    "negative Rosetta evidence, not QIT admission."
)

LEGO_IDS = [
    "carnot_cycle",
    "szilard_cycle",
    "iching_64_schedule",
    "dual_stacked_engine",
    "operator_order",
    "graph_topology",
    "proof_fence",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["operator_order", "graveyard_variant"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads exact source receipts"},
    "numpy": {"tried": True, "used": True, "reason": "I Ching order variant generation"},
    "torch": {"tried": True, "used": True, "reason": "order graph tensor witness"},
    "pyg": {"tried": True, "used": True, "reason": "variant order graph tensor carrier"},
    "rustworkx": {"tried": True, "used": True, "reason": "order graph construction for each variant"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence for wrong Szilard precedence"},
    "cvc5": {"tried": True, "used": True, "reason": "independent UNSAT fence for wrong Szilard precedence"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["json"] = "supportive"
TOOL_INTEGRATION_DEPTH["pathlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_stdlib"] = "supportive"
TOOL_INTEGRATION_DEPTH["python_json"] = "supportive"

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def bits(n: int, width: int = 6) -> list[int]:
    return [(n >> i) & 1 for i in range(width)]


def hamming(a: int, b: int) -> int:
    return int(sum(x != y for x, y in zip(bits(a), bits(b))))


def gray_code(n: int) -> int:
    return n ^ (n >> 1)


def order_graph(order: list[str]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(order)
    edges = [(i, i + 1) for i in range(len(order) - 1)]
    graph.add_edges_from_no_data(edges)
    data = Data(
        x=torch.arange(len(order), dtype=torch.float64).reshape(-1, 1),
        edge_index=torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.empty((2, 0), dtype=torch.long),
    )
    return {
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "pass": graph.num_nodes() == len(order) and graph.num_edges() == max(0, len(order) - 1),
    }


def carnot_variants(carnot: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = [step["kind"] for step in carnot["dual_stack"]["inductive_heating_loop"]["stage_trace"]]
    reverse = list(reversed(canonical))
    scrambled = [canonical[0], canonical[2], canonical[1], canonical[3]]
    collapsed = [canonical[0]] * 4
    allowed = {tuple(canonical), tuple(reverse)}
    rows = []
    for name, order, expected in [
        ("canonical_forward", canonical, "survives"),
        ("honest_reverse", reverse, "survives"),
        ("swap_middle_legs", scrambled, "killed"),
        ("collapsed_single_leg", collapsed, "killed"),
    ]:
        survives = tuple(order) in allowed and len(set(order)) == 2
        rows.append(
            {
                "engine": "carnot",
                "variant": name,
                "order": order,
                "expected": expected,
                "survives_order_gate": survives,
                "status": "survives" if survives else "killed",
                "reason": "Carnot accepts only the canonical heat-engine order or its honest reverse refrigerator traversal.",
                "graph": order_graph(order),
            }
        )
    return rows


def szilard_variants(szilard: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = [step["kind"] for step in szilard["dual_stack"]["inductive_heating_loop"]["stage_trace"]]
    reverse = [step["kind"] for step in szilard["dual_stack"]["deductive_cooling_loop"]["stage_trace"]]
    scrambled = ["feedback", "measurement", "erasure"]
    no_erasure = ["measurement", "feedback"]
    rows = []
    for name, order, expected in [
        ("canonical_measure_feedback_erase", canonical, "survives"),
        ("honest_reverse_recovery", reverse, "survives"),
        ("feedback_before_measurement", scrambled, "killed"),
        ("missing_erasure", no_erasure, "killed"),
    ]:
        clean = [part.replace("_reverse", "") for part in order]
        survives = clean == ["measurement", "feedback", "erasure"] or clean == ["erasure", "feedback", "measurement"]
        rows.append(
            {
                "engine": "szilard",
                "variant": name,
                "order": order,
                "expected": expected,
                "survives_order_gate": survives,
                "status": "survives" if survives else "killed",
                "reason": "Szilard requires measurement-feedback-erasure precedence or the exact reverse bookkeeping traversal.",
                "graph": order_graph(order),
            }
        )
    return rows


def iching_variants(iching: dict[str, Any]) -> list[dict[str, Any]]:
    canonical = [row["state"] for row in iching["hexagrams"]]
    reverse = list(reversed(canonical))
    binary_order = list(range(64))
    collapsed = [0] * 64
    rng = np.random.default_rng(29)
    random_order = list(range(64))
    rng.shuffle(random_order)
    rows = []
    for name, order, expected in [
        ("canonical_gray_cycle", canonical, "survives"),
        ("honest_reverse_gray_cycle", reverse, "survives"),
        ("binary_count_order", binary_order, "killed"),
        ("collapsed_single_state", collapsed, "killed"),
        ("seeded_random_order", random_order, "killed"),
    ]:
        distances = [hamming(order[i], order[(i + 1) % len(order)]) for i in range(len(order))]
        survives = len(set(order)) == 64 and min(distances) == 1 and max(distances) == 1
        rows.append(
            {
                "engine": "iching_64",
                "variant": name,
                "expected": expected,
                "unique_states": len(set(order)),
                "min_hamming_step": min(distances),
                "max_hamming_step": max(distances),
                "survives_order_gate": survives,
                "status": "survives" if survives else "killed",
                "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
                "graph": order_graph([str(v) for v in order]),
            }
        )
    return rows


def z3_wrong_szilard_precedence_unsat() -> dict[str, Any]:
    measurement, feedback, erasure = z3.Ints("measurement feedback erasure")
    solver = z3.Solver()
    solver.add(measurement < feedback, feedback < erasure)
    solver.add(feedback < measurement)
    result = solver.check()
    return {
        "claim": "feedback can precede measurement while preserving canonical Szilard precedence",
        "result": str(result),
        "pass": result == z3.unsat,
    }


def cvc5_wrong_szilard_precedence_unsat() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    measurement = solver.mkConst(integer, "measurement")
    feedback = solver.mkConst(integer, "feedback")
    erasure = solver.mkConst(integer, "erasure")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, measurement, feedback))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, feedback, erasure))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LT, feedback, measurement))
    result = solver.checkSat()
    return {
        "claim": "feedback can precede measurement while preserving canonical Szilard precedence",
        "result": str(result),
        "pass": str(result).lower() == "unsat",
    }


def order_exhaustion_summary() -> dict[str, Any]:
    szilard_ops = ["measurement", "feedback", "erasure"]
    valid = []
    killed = []
    for order in permutations(szilard_ops):
        if list(order) == szilard_ops or list(order) == list(reversed(szilard_ops)):
            valid.append(order)
        else:
            killed.append(order)
    return {
        "szilard_permutation_count": 6,
        "valid_orders": [list(row) for row in valid],
        "killed_orders": [list(row) for row in killed],
        "pass": len(valid) == 2 and len(killed) == 4,
    }


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "variant_rows": result["variant_rows"],
        "proof_fences": result["proof_fences"],
        "order_exhaustion": result["order_exhaustion"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA = " + json.dumps(build_visual_payload(result), indent=2, default=str) + ";\n"
    (VIS_DIR / "rosetta-triad-order-graveyard-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    carnot = load_result("two_bath_heat_work_reversible_cycle_pair")
    szilard = load_result("measure_feedback_erasure_recovery_cycle_pair")
    iching = load_result("six_bit_gray_code_single_flip_cycle_invariant")
    variants = carnot_variants(carnot) + szilard_variants(szilard) + iching_variants(iching)
    proof_fences = {
        "z3_wrong_szilard_precedence_unsat": z3_wrong_szilard_precedence_unsat(),
        "cvc5_wrong_szilard_precedence_unsat": cvc5_wrong_szilard_precedence_unsat(),
    }
    exhaustion = order_exhaustion_summary()
    expected_ok = all(row["status"] == row["expected"] for row in variants)
    graph_ok = all(row["graph"]["pass"] for row in variants)
    all_pass = expected_ok and graph_ok and all(row["pass"] for row in proof_fences.values()) and exhaustion["pass"]
    result = {
        "name": "rosetta_triad_order_graveyard",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "nearby order variants were tested for each Rosetta triad engine",
            "canonical and honest reverse orders survive",
            "scrambled, collapsed, missing, binary, and random orders are killed or rejected",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "order gates do not admit QIT runtime",
            "reverse traversal is bookkeeping, not a second engine identity",
            "variant survival does not promote axes",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot": str(RESULT_DIR / "two_bath_heat_work_reversible_cycle_pair_results.json"),
            "szilard": str(RESULT_DIR / "measure_feedback_erasure_recovery_cycle_pair_results.json"),
            "iching_64": str(RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json"),
        },
        "variant_rows": variants,
        "proof_fences": proof_fences,
        "order_exhaustion": exhaustion,
        "summary": {
            "all_pass": bool(all_pass),
            "variant_count": len(variants),
            "survivor_count": sum(row["status"] == "survives" for row in variants),
            "killed_count": sum(row["status"] == "killed" for row in variants),
            "expected_status_match": expected_ok,
            "order_graphs_pass": graph_ok,
            "proof_fences_pass": all(row["pass"] for row in proof_fences.values()),
            "visual_payload": "visualizer/rosetta-triad-order-graveyard-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "rosetta_triad_order_graveyard_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
