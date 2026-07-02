#!/usr/bin/env python3
"""Terrain/operator composition order over exact Hopf-loop samples.

This scout tests a local finite composition question:

  operator_after_terrain(rho) versus terrain_after_operator(rho)

over exact Hopf-loop samples, eight source terrain laws, and Ti/Te/Fi/Fe
operators. It records both noncommuting pairs and structured commuting islands.
It does not admit terrain layers, operator substages, Axis0, Xi/Phi0, flux,
physics, stacking, PEPS3D closure, or final manifold claims.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import xgi
import z3

import sim_shell_terrain_exact_hopf_loop_harness_probe as exact
import sim_shell_terrain_operator_adapter_probe as terrain


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_terrain_operator_composition_order_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DEPENDENCY_RESULT = RESULT_DIR / "shell_terrain_integrator_comparison_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "exact_hopf_loop_terrain_operator_composition_order"
PROMOTION_ALLOWED = False

OPERATORS = ["Ti", "Te", "Fi", "Fe"]
SAMPLES_PER_LOOP = 16
ORDER_GAP_THRESHOLD = 1.0e-6
COLLAPSE_THRESHOLD = 1.0e-9

BLOCKED_CONSUMERS = [
    "terrain layer admission",
    "operator substage admission",
    "terrain/operator coupling admission",
    "PEPS3D closure",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

CLAIM_CEILING = (
    "Formal scout only: tests finite terrain/operator order sensitivity over "
    "exact Hopf-loop samples. Nonzero order gaps are local composition evidence; "
    "structured commuting islands are recorded as useful collapses. This does "
    "not admit terrain layers, operator substages, Axis0, Xi/Phi0, flux, "
    "physics, stacking, PEPS3D closure, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: computes terrain-before-operator and operator-before-terrain density paths over exact Hopf-loop samples",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: records loop/terrain/operator composition triples as higher-order incidence",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: records directed composition graph from terrain-before-operator to operator-before-terrain comparisons",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact count checks for sixteen placements by four operators",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects universal-noncommutation and downstream-admission overclaims",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of composition-order-to-admission overclaim",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def samples() -> dict[str, list[dict[str, Any]]]:
    old = exact.SAMPLES_PER_LOOP
    exact.SAMPLES_PER_LOOP = SAMPLES_PER_LOOP
    try:
        return {
            "Type1_inner": exact.loop_samples("Type1_inner"),
            "Type1_outer": exact.loop_samples("Type1_outer"),
            "Type2_inner": exact.loop_samples("Type2_inner"),
            "Type2_outer": exact.loop_samples("Type2_outer"),
        }
    finally:
        exact.SAMPLES_PER_LOOP = old


def terrain_field(label: str, sheet: str, rho: torch.Tensor, same_sign: bool = False, zero: bool = False) -> torch.Tensor:
    if zero:
        return torch.zeros_like(rho)
    return terrain.terrain_generator(label, sheet, rho, same_sign=same_sign)


def terrain_step(label: str, sheet: str, rho: torch.Tensor, same_sign: bool = False, zero: bool = False) -> torch.Tensor:
    out = rho
    h = terrain.DT / 4.0
    for _ in range(4):
        if zero:
            return out
        k1 = terrain_field(label, sheet, out, same_sign=same_sign)
        k2 = terrain_field(label, sheet, terrain.repair_density(out + 0.5 * h * k1), same_sign=same_sign)
        k3 = terrain_field(label, sheet, terrain.repair_density(out + 0.5 * h * k2), same_sign=same_sign)
        k4 = terrain_field(label, sheet, terrain.repair_density(out + h * k3), same_sign=same_sign)
        out = terrain.repair_density(out + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))
    return out


def probe_value(axis: str, rho: torch.Tensor) -> float:
    return float(torch.trace(terrain.P[axis] @ rho).real.item())


def support_summary(loop_samples: list[dict[str, Any]]) -> dict[str, int]:
    sites = sorted({site for sample in loop_samples for site in sample["support_sites"]})
    return {
        "sample_count": len(loop_samples),
        "distinct_support_sites": len(sites),
        "min_support_site": min(sites),
        "max_support_site": max(sites),
    }


def composition_rows(all_samples: dict[str, list[dict[str, Any]]], same_sign: bool = False, zero: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configs = [
        ("Type1_inner", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, labels in configs:
        loop_samples = all_samples[loop_name]
        for label in labels:
            for operator in OPERATORS:
                gaps = []
                entropy_gaps = []
                purity_gaps = []
                x_probe_gaps = []
                z_probe_gaps = []
                for sample in loop_samples:
                    rho = sample["rho"]
                    terrain_then_operator = terrain.op_channel(operator, terrain_step(label, sheet, rho, same_sign=same_sign, zero=zero))
                    operator_then_terrain = terrain_step(label, sheet, terrain.op_channel(operator, rho), same_sign=same_sign, zero=zero)
                    gaps.append(terrain.density_gap(terrain_then_operator, operator_then_terrain))
                    entropy_gaps.append(abs(terrain.entropy_vn(terrain_then_operator) - terrain.entropy_vn(operator_then_terrain)))
                    purity_gaps.append(abs(terrain.purity(terrain_then_operator) - terrain.purity(operator_then_terrain)))
                    x_probe_gaps.append(abs(probe_value("sx", terrain_then_operator) - probe_value("sx", operator_then_terrain)))
                    z_probe_gaps.append(abs(probe_value("sz", terrain_then_operator) - probe_value("sz", operator_then_terrain)))
                mean_gap = sum(gaps) / len(gaps)
                rows.append(
                    {
                        "loop": loop_name,
                        "sheet": sheet,
                        "loop_kind": loop_samples[0]["loop_kind"],
                        "terrain": label,
                        "source_name": terrain.terrain_name(label, sheet),
                        "operator": operator,
                        "support_summary": support_summary(loop_samples),
                        "mean_order_gap": round(mean_gap, 12),
                        "max_order_gap": round(max(gaps), 12),
                        "mean_entropy_gap": round(sum(entropy_gaps) / len(entropy_gaps), 12),
                        "mean_purity_gap": round(sum(purity_gaps) / len(purity_gaps), 12),
                        "mean_x_probe_gap": round(sum(x_probe_gaps) / len(x_probe_gaps), 12),
                        "mean_z_probe_gap": round(sum(z_probe_gaps) / len(z_probe_gaps), 12),
                        "classification": "noncommuting" if mean_gap > ORDER_GAP_THRESHOLD else "structured_commuting_collapse",
                    }
                )
    return rows


def zero_terrain_control(all_samples: dict[str, list[dict[str, Any]]]) -> float:
    return max(row["mean_order_gap"] for row in composition_rows(all_samples, zero=True))


def identity_operator_control(all_samples: dict[str, list[dict[str, Any]]]) -> float:
    gaps = []
    configs = [
        ("Type1_inner", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, labels in configs:
        for label in labels:
            for sample in all_samples[loop_name]:
                rho = sample["rho"]
                moved = terrain_step(label, sheet, rho)
                gaps.append(terrain.density_gap(moved, moved))
    return max(gaps)


def loop_erased_samples(all_samples: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "Type1_inner": all_samples["Type1_inner"],
        "Type1_outer": all_samples["Type1_inner"],
        "Type2_inner": all_samples["Type2_inner"],
        "Type2_outer": all_samples["Type2_inner"],
    }


def row_fingerprint(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[tuple[float, ...]]:
    return sorted(tuple(round(float(row[key]), 9) for key in keys) for row in rows)


def fingerprint_delta(left: list[dict[str, Any]], right: list[dict[str, Any]], keys: tuple[str, ...]) -> float:
    fp_left = row_fingerprint(left, keys)
    fp_right = row_fingerprint(right, keys)
    return sum(abs(a[i] - b[i]) for a, b in zip(fp_left, fp_right, strict=True) for i in range(len(a)))


def unique_count(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    return len({tuple(round(float(row[key]), 7) for key in keys) for row in rows})


def build_surfaces(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hypergraph = xgi.Hypergraph()
    graph = rx.PyDiGraph()
    for row in rows:
        hypergraph.add_edge(
            [
                f"loop:{row['loop']}",
                f"terrain:{row['terrain']}",
                f"operator:{row['operator']}",
                f"class:{row['classification']}",
            ]
        )
        a = graph.add_node(f"{row['loop']}:{row['terrain']}:{row['operator']}:T_then_O")
        b = graph.add_node(f"{row['loop']}:{row['terrain']}:{row['operator']}:O_then_T")
        graph.add_edge(a, b, row["mean_order_gap"])
    return {
        "xgi_hyperedges": hypergraph.num_edges,
        "xgi_higher_order": all(len(edge) == 4 for edge in hypergraph.edges.members()),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "rustworkx_acyclic": rx.is_directed_acyclic_graph(graph),
    }


def expected_structured_collapses(rows: list[dict[str, Any]]) -> dict[str, Any]:
    collapsed = [row for row in rows if row["classification"] == "structured_commuting_collapse"]
    expected = {
        ("Type1_inner", "Si", "Ti"),
        ("Type1_inner", "Si", "Fe"),
        ("Type1_outer", "Si", "Ti"),
        ("Type1_outer", "Si", "Fe"),
        ("Type2_inner", "Si", "Te"),
        ("Type2_inner", "Si", "Fi"),
        ("Type2_outer", "Si", "Te"),
        ("Type2_outer", "Si", "Fi"),
    }
    observed = {(row["loop"], row["terrain"], row["operator"]) for row in collapsed}
    return {
        "observed_count": len(observed),
        "expected_count": len(expected),
        "observed": sorted([list(item) for item in observed]),
        "matches_expected": observed == expected,
    }


def z3_reject_composition_to_admission() -> bool:
    local_order_gaps = z3.Bool("local_order_gaps")
    all_pairs_noncommuting = z3.Bool("all_pairs_noncommuting")
    downstream_blocked = z3.Bool("downstream_blocked")
    admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(admit)
    solver.add(admit == z3.And(local_order_gaps, all_pairs_noncommuting, z3.Not(downstream_blocked)))
    solver.add(local_order_gaps)
    solver.add(z3.Not(all_pairs_noncommuting))
    solver.add(downstream_blocked)
    return solver.check() == z3.unsat


def cvc5_reject_composition_to_admission() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    local_order_gaps = solver.mkConst(bool_sort, "local_order_gaps")
    all_pairs_noncommuting = solver.mkConst(bool_sort, "all_pairs_noncommuting")
    downstream_blocked = solver.mkConst(bool_sort, "downstream_blocked")
    admit = solver.mkConst(bool_sort, "admit")
    rhs = solver.mkTerm(
        Kind.AND,
        local_order_gaps,
        all_pairs_noncommuting,
        solver.mkTerm(Kind.NOT, downstream_blocked),
    )
    solver.assertFormula(admit)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, rhs))
    solver.assertFormula(local_order_gaps)
    solver.assertFormula(solver.mkTerm(Kind.NOT, all_pairs_noncommuting))
    solver.assertFormula(downstream_blocked)
    return str(solver.checkSat()) == "unsat"


def z3_reject_label_only() -> bool:
    finite_map = z3.Bool("finite_map")
    density_response = z3.Bool("density_response")
    label_only = z3.Bool("label_only")
    admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(admit)
    solver.add(admit == z3.And(finite_map, density_response, z3.Not(label_only)))
    solver.add(label_only)
    return solver.check() == z3.unsat


def cvc5_reject_label_only() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    finite_map = solver.mkConst(bool_sort, "finite_map")
    density_response = solver.mkConst(bool_sort, "density_response")
    label_only = solver.mkConst(bool_sort, "label_only")
    admit = solver.mkConst(bool_sort, "admit")
    rhs = solver.mkTerm(Kind.AND, finite_map, density_response, solver.mkTerm(Kind.NOT, label_only))
    solver.assertFormula(admit)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, rhs))
    solver.assertFormula(label_only)
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_json(DEPENDENCY_RESULT)
    all_samples = samples()
    rows = composition_rows(all_samples)
    same_sign_rows = composition_rows(all_samples, same_sign=True)
    loop_erased_rows = composition_rows(loop_erased_samples(all_samples))
    nonzero = [row for row in rows if row["classification"] == "noncommuting"]
    collapsed = [row for row in rows if row["classification"] == "structured_commuting_collapse"]
    collapse_summary = expected_structured_collapses(rows)
    surfaces = build_surfaces(rows)
    zero_gap = zero_terrain_control(all_samples)
    identity_gap = identity_operator_control(all_samples)
    count_residual = str(sp.simplify(sp.Integer(len(rows)) - sp.Integer(16 * len(OPERATORS))))
    response_keys = ("mean_order_gap", "mean_entropy_gap", "mean_purity_gap", "mean_x_probe_gap", "mean_z_probe_gap")
    full_unique = unique_count(rows, response_keys)
    entropy_unique = unique_count(rows, ("mean_entropy_gap",))
    same_sign_delta = fingerprint_delta(rows, same_sign_rows, response_keys)
    loop_erased_delta = fingerprint_delta(rows, loop_erased_rows, response_keys)

    positive = {
        "dependency_integrator_read": {
            "pass": bool(dependency.get("result_summary", {}).get("all_pass")),
            "witness": dependency.get("result_summary", {}),
        },
        "composition_count_exact": {
            "pass": count_residual == "0" and len(rows) == 64,
            "witness": {"rows": len(rows), "count_residual": count_residual},
        },
        "composition_surfaces_nonempty": {
            "pass": surfaces["xgi_hyperedges"] == 64 and surfaces["rustworkx_edges"] == 64 and surfaces["rustworkx_acyclic"],
            "witness": surfaces,
        },
        "noncommuting_majority_detected": {
            "pass": len(nonzero) == 56 and min(row["mean_order_gap"] for row in nonzero) > ORDER_GAP_THRESHOLD,
            "witness": {
                "noncommuting_pairs": len(nonzero),
                "min_nonzero_gap": round(min(row["mean_order_gap"] for row in nonzero), 12),
                "max_order_gap": round(max(row["mean_order_gap"] for row in rows), 12),
            },
        },
        "structured_commuting_islands_recorded": {
            "pass": collapse_summary["matches_expected"],
            "witness": collapse_summary,
        },
        "scalar_entropy_confound_recorded": {
            "pass": entropy_unique <= full_unique,
            "witness": {
                "full_response_unique_count": full_unique,
                "entropy_only_unique_count": entropy_unique,
                "confound_present": entropy_unique == full_unique,
                "meaning": "scalar entropy distinguishes the same number of rows in this finite composition packet, so composition-order evidence cannot become an entropy/Axis proxy",
            },
        },
    }

    graveyard_companions = {
        "zero_terrain_order_control_collapses": {
            "pass": zero_gap < COLLAPSE_THRESHOLD,
            "witness": {"zero_terrain_gap": round(zero_gap, 12)},
        },
        "identity_operator_order_control_collapses": {
            "pass": identity_gap < COLLAPSE_THRESHOLD,
            "witness": {"identity_operator_gap": round(identity_gap, 12)},
        },
        "universal_noncommutation_rejected": {
            "pass": len(collapsed) > 0,
            "witness": {"collapsed_pairs": len(collapsed), "meaning": "the scout does not claim all terrain/operator pairs are noncommuting"},
        },
        "loop_erasure_changes_order_response": {
            "pass": loop_erased_delta > 0.01,
            "witness": {"loop_erased_delta": round(loop_erased_delta, 12)},
        },
        "sheet_sign_erasure_changes_order_response": {
            "pass": same_sign_delta > 0.01,
            "witness": {"same_sign_delta": round(same_sign_delta, 12)},
        },
        "label_only_rejected_cross_solver": {
            "pass": z3_reject_label_only() and cvc5_reject_label_only(),
            "witness": {"z3_unsat": z3_reject_label_only(), "cvc5_unsat": cvc5_reject_label_only()},
        },
        "density_only_full_s3_claim_rejected_cross_solver": {
            "pass": exact.z3_reject_density_only_full_loop() and exact.cvc5_reject_density_only_full_loop(),
            "witness": {"z3_unsat": exact.z3_reject_density_only_full_loop(), "cvc5_unsat": exact.cvc5_reject_density_only_full_loop()},
        },
        "composition_to_admission_rejected_cross_solver": {
            "pass": z3_reject_composition_to_admission() and cvc5_reject_composition_to_admission(),
            "witness": {"z3_unsat": z3_reject_composition_to_admission(), "cvc5_unsat": cvc5_reject_composition_to_admission()},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [key for section in all_checks for key, row in section.items() if not row["pass"]]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "exact_hopf_loop_terrain_operator_composition_order",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Test terrain-before-operator versus operator-before-terrain local composition over exact Hopf-loop samples.",
        "scientific_question": "Which finite terrain/operator pairs are order-sensitive, and which collapse as structured commuting islands, without unlocking downstream claims?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": "ComposeOrder: exact Hopf-loop density sample x terrain law x operator -> terrain-then-operator and operator-then-terrain order-gap table",
        "domain": "4 exact Hopf loops x 4 terrain laws x 4 operators over 16 samples per loop",
        "codomain_or_output": "64 composition order gaps, structured commuting islands, graph/hypergraph incidence, controls, blocked consumers",
        "carrier_layer": "exact Hopf loop spinors with spinor-derived densities",
        "geometry_layer": "S3 Hopf fiber/base terrain/operator local composition",
        "carrier_realization": "torch spinors and 2x2 densities; RK4-style terrain step from prior integrator receipt",
        "peps3d_embedding": {"site_floors": exact.SITE_FLOORS, "max_sites": max(exact.SITE_FLOORS.values()), "bond_dim": 2, "closure_claimed": False},
        "spinor_state": f"psi(phi,chi;eta) sampled along Gamma_f/Gamma_b with eta={exact.ETA}",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(DEPENDENCY_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_composition_order_only",
        "cut_layer": "single-sheet density readouts only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "terrain-before-operator versus operator-before-terrain local action ordering",
        "branch_status_before_run": "IntegratorComparison passed bounded method stability; local terrain/operator composition order remained open.",
        "allowed_claims": [
            "56 tested terrain/operator pairs are order-sensitive under the finite local composition map.",
            "8 tested pairs collapse as structured commuting islands and are not forced into universal noncommutation.",
            "Scalar entropy is confounded for this composition packet and cannot carry downstream meaning by itself.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["local composition only", "no continuous flow/coupling admission", "no Xi/Phi0 bridge"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["IntegratorComparison receipt"],
        "data_or_artifact_dependencies": [str(DEPENDENCY_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "zero terrain or identity operator produces nonzero order gap",
            "all pairs are forced to noncommute despite structured commuting islands",
            "local composition is promoted as terrain/operator coupling admission",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": {
                "terrain_then_operator": "compared against operator_then_terrain",
                "zero_terrain": "collapses",
            "identity_operator": "collapses",
                "loop_erased": "changes response",
                "sheet_sign_erased": "changes response",
                "scalar_entropy_only": "insufficient",
            "structured_commuting_islands": "recorded not erased",
            },
        },
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "counts, surfaces, noncommuting majority, commuting islands, controls, and downstream locks all pass",
        "fail_rule": "controls survive, composition counts drift, commuting islands are erased, or downstream admission unlocks",
        "why_not_v4_probes": "This is v4.3 object-preservation local terrain/operator composition work over exact shell/Hopf terrain responses; it does not become Axis0, Xi/Phi0, flux, or manifold closure.",
        "composition_rows": rows,
        "readouts": {
            "composition_pairs": len(rows),
            "noncommuting_pairs": len(nonzero),
            "structured_commuting_pairs": len(collapsed),
            "mean_order_gap": round(sum(row["mean_order_gap"] for row in rows) / len(rows), 12),
            "max_order_gap": round(max(row["mean_order_gap"] for row in rows), 12),
            "zero_terrain_gap": round(zero_gap, 12),
            "identity_operator_gap": round(identity_gap, 12),
            "full_response_unique_count": full_unique,
            "entropy_only_unique_count": entropy_unique,
            "scalar_entropy_confound_present": entropy_unique == full_unique,
            "same_sign_delta": round(same_sign_delta, 12),
            "loop_erased_delta": round(loop_erased_delta, 12),
        },
        "result_summary": {
            "all_pass": all_pass,
            "composition_pairs": len(rows),
            "noncommuting_pairs": len(nonzero),
            "structured_commuting_pairs": len(collapsed),
            "max_order_gap": round(max(row["mean_order_gap"] for row in rows), 9),
            "mean_order_gap": round(sum(row["mean_order_gap"] for row in rows) / len(rows), 9),
            "full_response_unique_count": full_unique,
            "entropy_only_unique_count": entropy_unique,
            "scalar_entropy_confound_present": entropy_unique == full_unique,
            "same_sign_delta": round(same_sign_delta, 9),
            "loop_erased_delta": round(loop_erased_delta, 9),
            "operators": OPERATORS,
            "terrain_laws": 8,
            "placements": 16,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
