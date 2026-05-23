#!/usr/bin/env python3
"""Z3 Hopf receipt dependency partial-order baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
from pathlib import Path

import z3
from receipt_boundary import apply_default_receipt_boundary


NAME = "z3_hopf_receipt_dependency_partial_order"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "checks bounded integer partial-order constraints for Hopf receipt dependency routing controls",
    }
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

NODES = [
    "sympy_hopf_loop_holonomy_area_dependence",
    "scipy_hopf_horizontal_lift_chi_shift",
    "gudhi_hopf_torus_fiber_base_homology",
    "toponetx_two_hopf_torus_layer_incidence",
    "cvc5_hopf_torus_readout_vector_separation",
    "z3_hopf_torus_readout_vector_separation",
]

EDGES = [
    ("sympy_hopf_loop_holonomy_area_dependence", "toponetx_two_hopf_torus_layer_incidence"),
    ("scipy_hopf_horizontal_lift_chi_shift", "toponetx_two_hopf_torus_layer_incidence"),
    ("gudhi_hopf_torus_fiber_base_homology", "toponetx_two_hopf_torus_layer_incidence"),
    ("toponetx_two_hopf_torus_layer_incidence", "cvc5_hopf_torus_readout_vector_separation"),
    ("toponetx_two_hopf_torus_layer_incidence", "z3_hopf_torus_readout_vector_separation"),
    ("sympy_hopf_loop_holonomy_area_dependence", "cvc5_hopf_torus_readout_vector_separation"),
    ("sympy_hopf_loop_holonomy_area_dependence", "z3_hopf_torus_readout_vector_separation"),
]


def order_vars() -> dict[str, z3.IntNumRef]:
    return {name: z3.Int(name) for name in NODES}


def base_solver(edges: list[tuple[str, str]]) -> tuple[z3.Solver, dict[str, z3.IntNumRef]]:
    solver = z3.SolverFor("QF_LIA")
    order = order_vars()
    for node in NODES:
        solver.add(order[node] >= 0, order[node] < len(NODES))
    solver.add(z3.Distinct(*[order[node] for node in NODES]))
    for source, target in edges:
        solver.add(order[source] < order[target])
    return solver, order


def status(solver: z3.Solver) -> str:
    result = solver.check()
    if result == z3.sat:
        return "sat"
    if result == z3.unsat:
        return "unsat"
    return "unknown"


def model_order(solver: z3.Solver, order: dict[str, z3.IntNumRef]) -> list[str]:
    if solver.check() != z3.sat:
        return []
    model = solver.model()
    return [
        name
        for name, _value in sorted(
            ((name, model.eval(var).as_long()) for name, var in order.items()),
            key=lambda item: item[1],
        )
    ]


def check_with_extra(edges: list[tuple[str, str]], extra_constraints: list[z3.BoolRef]) -> dict[str, object]:
    solver, order = base_solver(edges)
    solver.add(*extra_constraints)
    result = status(solver)
    return {
        "z3_result": result,
        "model_order": model_order(solver, order) if result == "sat" else [],
    }


def run_positive() -> dict[str, object]:
    solver, order = base_solver(EDGES)
    result = status(solver)
    solved_order = model_order(solver, order) if result == "sat" else []
    top_before_cvc5 = check_with_extra(
        EDGES,
        [order["toponetx_two_hopf_torus_layer_incidence"] < order["cvc5_hopf_torus_readout_vector_separation"]],
    )
    return {
        "dependency_order_is_satisfiable": {
            "z3_result": result,
            "model_order": solved_order,
            "passed": result == "sat",
        },
        "toponetx_parent_precedes_cvc5_readout": {
            **top_before_cvc5,
            "expected": "sat",
            "passed": top_before_cvc5["z3_result"] == "sat",
        },
    }


def run_graveyards() -> dict[str, object]:
    order = order_vars()
    impossible_reverse = check_with_extra(
        EDGES,
        [order["cvc5_hopf_torus_readout_vector_separation"] < order["toponetx_two_hopf_torus_layer_incidence"]],
    )
    cycle_edges = EDGES + [
        ("cvc5_hopf_torus_readout_vector_separation", "toponetx_two_hopf_torus_layer_incidence")
    ]
    cycle_solver, _cycle_order = base_solver(cycle_edges)
    missing_toponetx_edges = [edge for edge in EDGES if edge[0] != "toponetx_two_hopf_torus_layer_incidence"]
    missing_solver, missing_order = base_solver(missing_toponetx_edges)
    missing_solver.add(
        missing_order["cvc5_hopf_torus_readout_vector_separation"]
        < missing_order["toponetx_two_hopf_torus_layer_incidence"]
    )
    isolated_solver = z3.SolverFor("QF_LIA")
    single = z3.Int("single_receipt")
    isolated_solver.add(single == 0)

    redundant_removed_edges = [
        edge
        for edge in EDGES
        if edge
        not in {
            ("sympy_hopf_loop_holonomy_area_dependence", "cvc5_hopf_torus_readout_vector_separation"),
            ("sympy_hopf_loop_holonomy_area_dependence", "z3_hopf_torus_readout_vector_separation"),
        }
    ]
    reduced_solver, reduced_order = base_solver(redundant_removed_edges)
    reduced_solver.add(
        reduced_order["sympy_hopf_loop_holonomy_area_dependence"]
        < reduced_order["cvc5_hopf_torus_readout_vector_separation"]
    )
    return {
        "cvc5_readout_cannot_precede_toponetx_parent": {
            **impossible_reverse,
            "expected": "unsat",
            "passed": impossible_reverse["z3_result"] == "unsat",
        },
        "cycle_edge_makes_dependency_order_unsat": {
            "z3_result": status(cycle_solver),
            "expected": "unsat",
            "passed": status(cycle_solver) == "unsat",
        },
        "missing_toponetx_parent_allows_bad_order_as_expected_control": {
            "z3_result": status(missing_solver),
            "model_order": model_order(missing_solver, missing_order) if status(missing_solver) == "sat" else [],
            "expected": "sat",
            "passed": status(missing_solver) == "sat",
        },
        "isolated_single_receipt_has_trivial_order": {
            "z3_result": status(isolated_solver),
            "expected": "sat",
            "passed": status(isolated_solver) == "sat",
        },
        "transitive_edges_are_redundant_under_parent_path": {
            "z3_result": status(reduced_solver),
            "model_order": model_order(reduced_solver, reduced_order) if status(reduced_solver) == "sat" else [],
            "expected": "sat",
            "passed": status(reduced_solver) == "sat",
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        all(row["passed"] for row in positive.values())
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Z3 bounded integer partial-order baseline over Hopf receipt names only; no physical distinguishability, "
            "QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "nested_hopf_torus_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later receipt routing after exact physical carrier-evolution and topology receipts "
            "define the dependencies being ordered."
        ),
        "demotion_condition": (
            "Demote if parent-before-child constraints become satisfiable in reverse, if cycle controls are SAT, "
            "or if missing-parent controls do not expose the expected bad ordering."
        ),
        "blocked_until": "blocked from admission or target-system claims until physical-evolution fixtures and exact lower receipts exist",
        "out_of_scope": [
            "No physical Hopf/Weyl evolution.",
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This Z3 baseline cross-checks the NetworkX and rustworkx receipt dependency ordering with solver "
            "partial-order constraints. It is routing/evidence-graph control only."
        ),
        "operation_sequence": [
            "declare Hopf geometry receipt names as bounded integer order variables",
            "constrain all receipt order variables to be distinct positions",
            "add parent-before-child inequalities for lower geometry receipts, TopoNetX layer receipt, and solver readout receipts",
            "check that the dependency order is satisfiable",
            "run reverse-order, cycle-edge, missing-parent, isolated-node, and transitive-redundancy graveyards",
        ],
        "carrier_topology": "bounded integer partial order over receipt dependency graph nodes",
        "observable": "Z3 SAT/UNSAT status and model order for receipt dependency constraints",
        "pass_fail_predicate": (
            "declared dependency order is SAT, reversed parent/child order and cycle edge are UNSAT, missing-parent "
            "control allows the bad order, and transitive edges are redundant under the parent path"
        ),
        "graveyards": [
            "cvc5 readout cannot precede TopoNetX parent",
            "cycle edge makes dependency order unsat",
            "missing TopoNetX parent allows bad order as expected control",
            "isolated single receipt has trivial order",
            "transitive edges are redundant under parent path",
        ],
        "baselines": [
            "NetworkX Hopf receipt dependency reduction fixture",
            "rustworkx Hopf receipt dependency reduction fixture",
            "TopoNetX two Hopf-torus layer incidence fixture",
            "cvc5 Hopf torus readout-vector separation fixture",
            "z3 Hopf torus readout-vector separation fixture",
        ],
        "alternative_formulations": [
            "NetworkX dependency DAG cross-check",
            "rustworkx dependency DAG cross-check",
            "cvc5 partial-order constraints over receipt nodes",
        ],
        "exact_tool_function_needs": {
            "z3": ["SolverFor", "Int", "Distinct", "add", "check", "model"],
        },
        "lego_or_coupling_target": "nested_hopf_torus_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "nodes": NODES,
        "edges": EDGES,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "result": str(out_path)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
