#!/usr/bin/env python3
"""JAX + z3/cvc5 structural proof leg for foundation R6 CTC loop admissibility."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import cvc5
import jax.numpy as jnp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_ctc_loop_admissibility"
OBJECT_ID = "foundation_foundation_r6_ctc_loop_admissibility_jax"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_ctc_loop_admissibility_jax.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
EVENTS = ["A_prepare", "B_apply", "C_measure", "D_record"]
BARE_EDGES = [(0, 1), (1, 2), (2, 3)]
RETRO_EDGE = (3, 0)

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 construction of finite adjacency matrices and closure readouts"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive matrix assembly for independent non-claim diagnostics"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing derivation of reachability and closed-loop satisfiability from bound edge variables"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent derivation of the same reachability/cycle flip from bound edge variables"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "supportive", "jax.numpy": "supportive", "z3": "load_bearing", "cvc5": "load_bearing"}


def edge_matrix(edges: list[tuple[int, int]], n: int = 4) -> jax.Array:
    mat = jnp.zeros((n, n), dtype=jnp.int64)
    for src, dst in edges:
        mat = mat.at[src, dst].set(1)
    return mat


def reachability_int(edge_mat: jax.Array) -> jax.Array:
    reach = edge_mat.astype(jnp.int64)
    for _ in range(edge_mat.shape[0] - 1):
        reach = jnp.where((reach + (reach @ edge_mat > 0).astype(jnp.int64)) > 0, 1, 0)
    return reach


def scenario_signature(edges: list[tuple[int, int]]) -> dict[str, Any]:
    mat = edge_matrix(edges)
    reach = reachability_int(mat)
    edge_probe_values = {}
    for idx, (src, dst) in enumerate(BARE_EDGES + [RETRO_EDGE], start=1):
        edge_probe_values[f"M_edge_{idx}_{EVENTS[src]}_to_{EVENTS[dst]}"] = bool(int(mat[src, dst]))
    return {
        "edge_probe_values": edge_probe_values,
        "closed_directed_loop_probe": bool(int(jnp.trace(reach)) > 0),
    }


def quotient_classes(scenarios: dict[str, list[tuple[int, int]]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = {}
    signatures: dict[str, dict[str, Any]] = {}
    for name, edges in scenarios.items():
        sig = scenario_signature(edges)
        signatures[name] = sig
        key = json.dumps(sig, sort_keys=True)
        groups.setdefault(key, []).append(name)
    classes = [
        {"class_id": f"M_q{idx}", "signature": json.loads(key), "members": sorted(members)}
        for idx, (key, members) in enumerate(sorted(groups.items()))
    ]
    loop_groups = {"loop_excluded": [], "loop_admissible": []}
    for name, sig in signatures.items():
        loop_groups["loop_admissible" if sig["closed_directed_loop_probe"] else "loop_excluded"].append(name)
    return {
        "full_M_class_count": len(classes),
        "classes": classes,
        "loop_admissibility_classes": [
            {"class_id": "loop_excluded", "loop_admissible": False, "members": sorted(loop_groups["loop_excluded"])},
            {"class_id": "loop_admissible", "loop_admissible": True, "members": sorted(loop_groups["loop_admissible"])},
        ],
    }


def z3_cycle_check(edges: list[tuple[int, int]], label: str) -> dict[str, Any]:
    n = len(EVENTS)
    solver = z3.Solver()
    edge_values = {(i, j): ((i, j) in edges) for i in range(n) for j in range(n)}
    edge = [[z3.Bool(f"{label}_edge_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            solver.add(edge[i][j] == edge_values[(i, j)])
    reach_layers = [edge]
    prev = edge
    for depth in range(2, n + 1):
        layer = [[z3.Bool(f"{label}_reach_{depth}_{i}_{j}") for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(n):
                extensions = [z3.And(edge[i][k], prev[k][j]) for k in range(n)]
                solver.add(layer[i][j] == z3.Or(prev[i][j], *extensions))
        reach_layers.append(layer)
        prev = layer
    solver.add(z3.Or(*[reach_layers[-1][i][i] for i in range(n)]))
    return {
        "label": label,
        "verdict": str(solver.check()),
        "asserted_edge_equalities": n * n,
        "derived_reachability_layers": len(reach_layers),
        "cycle_assertion": "exists event e with reachability[e,e] derived from bound directed edges",
        "version": z3.get_version_string(),
    }


def cv_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.OR, *terms)


def cv_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.AND, *terms)


def cv_eq(solver: cvc5.Solver, left: Any, right: Any) -> Any:
    return solver.mkTerm(cvc5.Kind.EQUAL, left, right)


def cvc5_cycle_check(edges: list[tuple[int, int]], label: str) -> dict[str, Any]:
    n = len(EVENTS)
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    edge_values = {(i, j): ((i, j) in edges) for i in range(n) for j in range(n)}
    edge = [[solver.mkConst(bool_sort, f"{label}_edge_{i}_{j}") for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            solver.assertFormula(cv_eq(solver, edge[i][j], solver.mkBoolean(edge_values[(i, j)])))
    reach_layers = [edge]
    prev = edge
    for depth in range(2, n + 1):
        layer = [[solver.mkConst(bool_sort, f"{label}_reach_{depth}_{i}_{j}") for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(n):
                extensions = [cv_and(solver, [edge[i][k], prev[k][j]]) for k in range(n)]
                solver.assertFormula(cv_eq(solver, layer[i][j], cv_or(solver, [prev[i][j], *extensions])))
        reach_layers.append(layer)
        prev = layer
    solver.assertFormula(cv_or(solver, [reach_layers[-1][i][i] for i in range(n)]))
    return {
        "label": label,
        "verdict": str(solver.checkSat()),
        "asserted_edge_equalities": n * n,
        "derived_reachability_layers": len(reach_layers),
        "cycle_assertion": "exists event e with reachability[e,e] derived from bound directed edges",
        "version": cvc5.__version__ if hasattr(cvc5, "__version__") else "unknown",
    }


def constraints_report() -> dict[str, Any]:
    details = []
    dim = len(EVENTS)
    for idx, event_id in enumerate(EVENTS):
        state = jnp.zeros((dim, 1), dtype=jnp.float64).at[idx, 0].set(1.0)
        rho = state @ state.T
        eigs = jnp.linalg.eigvalsh(rho)
        details.append(
            {
                "id": event_id,
                "trace_residual": float(abs(jnp.trace(rho) - 1.0)),
                "hermitian_residual": float(jnp.linalg.norm(rho - rho.T)),
                "min_eigenvalue": float(jnp.min(eigs)),
                "normalization_residual": float(abs((state.T @ state)[0, 0] - 1.0)),
                "psd": bool(float(jnp.min(eigs)) >= -1.0e-12),
            }
        )
    return {
        "trace_one": all(row["trace_residual"] <= 1.0e-12 for row in details),
        "hermitian": all(row["hermitian_residual"] <= 1.0e-12 for row in details),
        "psd": all(row["psd"] for row in details),
        "normalized": all(row["normalization_residual"] <= 1.0e-12 for row in details),
        "details": details,
    }


def build_result() -> dict[str, Any]:
    bare_edges = list(BARE_EDGES)
    retro_edges = [*BARE_EDGES, RETRO_EDGE]
    dropped_forward_edges = [(0, 1), (2, 3), RETRO_EDGE]
    forced_commutative_edges = sorted(set([*BARE_EDGES, *[(dst, src) for src, dst in BARE_EDGES]]))
    scenarios = {
        "bare_order": bare_edges,
        "retrocausal_edge_installed": retro_edges,
        "retro_edge_but_B_to_C_dropped": dropped_forward_edges,
        "forced_commutative_bare_edges": forced_commutative_edges,
    }
    constraints = constraints_report()
    quotient = quotient_classes(scenarios)
    signatures = {name: scenario_signature(edges) for name, edges in scenarios.items()}
    z3_bare = z3_cycle_check(bare_edges, "bare")
    z3_retro = z3_cycle_check(retro_edges, "retro")
    z3_drop = z3_cycle_check(dropped_forward_edges, "drop_forward")
    cvc5_bare = cvc5_cycle_check(bare_edges, "bare")
    cvc5_retro = cvc5_cycle_check(retro_edges, "retro")
    cvc5_drop = cvc5_cycle_check(dropped_forward_edges, "drop_forward")
    bare_loop = signatures["bare_order"]["closed_directed_loop_probe"]
    retro_loop = signatures["retrocausal_edge_installed"]["closed_directed_loop_probe"]
    drop_loop = signatures["retro_edge_but_B_to_C_dropped"]["closed_directed_loop_probe"]
    commutative_loop = signatures["forced_commutative_bare_edges"]["closed_directed_loop_probe"]
    all_pass = (
        READS_PEER_RESULT is False
        and constraints["trace_one"]
        and constraints["hermitian"]
        and constraints["psd"]
        and constraints["normalized"]
        and bare_loop is False
        and retro_loop is True
        and drop_loop is False
        and commutative_loop is True
        and z3_bare["verdict"] == cvc5_bare["verdict"] == "unsat"
        and z3_retro["verdict"] == cvc5_retro["verdict"] == "sat"
        and z3_drop["verdict"] == cvc5_drop["verdict"] == "unsat"
    )
    return {
        "schema_version": "engine_leg_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "claim_ceiling": "Finite directed constraint-order diagnostic only. No GR metric, cosmology, Godel, chronology-protection, or promotion claim.",
        "M": {
            "explicit_probe_family": [
                "edge(A_prepare,B_apply)",
                "edge(B_apply,C_measure)",
                "edge(C_measure,D_record)",
                "edge(D_record,A_prepare)",
                "closed_directed_loop_exists",
            ],
            "measurement_object": "finite directed graph of constraint-application events",
        },
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermiticity", "normalization"],
            "state_constraint_values": constraints,
            "rung_specific_constraint": "Bare admissibility order binds edges A->B->C->D and excludes a closed directed loop unless D->A is explicitly installed.",
        },
        "S": {"carrier": "finite directed causal-order scenarios over four events", "events": EVENTS, "scenario_ids": sorted(scenarios)},
        "S_quotient": quotient,
        "smt": {
            "z3": {"bare": z3_bare, "retrocausal_edge": z3_retro, "drop_forward_edge": z3_drop},
            "cvc5": {"bare": cvc5_bare, "retrocausal_edge": cvc5_retro, "drop_forward_edge": cvc5_drop},
        },
        "values": {
            "bare_loop_admissible": bare_loop,
            "retrocausal_edge_loop_admissible": retro_loop,
            "drop_forward_edge_loop_admissible": drop_loop,
            "forced_commutative_loop_admissible": commutative_loop,
            "bare_loop_int": int(bare_loop),
            "retro_loop_int": int(retro_loop),
            "full_M_class_count": quotient["full_M_class_count"],
            "loop_admissibility_class_count": len(quotient["loop_admissibility_classes"]),
        },
        "negative_control_flip": {
            "bare_assert_loop_z3": z3_bare["verdict"],
            "bare_assert_loop_cvc5": cvc5_bare["verdict"],
            "retrocausal_edge_assert_loop_z3": z3_retro["verdict"],
            "retrocausal_edge_assert_loop_cvc5": cvc5_retro["verdict"],
            "drop_forward_edge_after_retro_assert_loop_z3": z3_drop["verdict"],
            "drop_forward_edge_after_retro_assert_loop_cvc5": cvc5_drop["verdict"],
            "force_commutativity_loop_admissible": commutative_loop,
            "sat_unsat_flip": z3_bare["verdict"] == cvc5_bare["verdict"] == "unsat"
            and z3_retro["verdict"] == cvc5_retro["verdict"] == "sat"
            and z3_drop["verdict"] == cvc5_drop["verdict"] == "unsat",
            "quotient_changes_when_cycle_probe_dropped": quotient["full_M_class_count"] > len(quotient["loop_admissibility_classes"]),
        },
        "forced_vs_installed": "INSTALLED",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    values = result["values"]
    print(
        "FOUNDATION_R6_JAX_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"bare_loop={values['bare_loop_admissible']} "
        f"retro_loop={values['retrocausal_edge_loop_admissible']} "
        f"z3={result['smt']['z3']['bare']['verdict']}->{result['smt']['z3']['retrocausal_edge']['verdict']} "
        f"cvc5={result['smt']['cvc5']['bare']['verdict']}->{result['smt']['cvc5']['retrocausal_edge']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
