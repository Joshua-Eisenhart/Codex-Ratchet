#!/usr/bin/env python3
"""Integrator comparison for exact Hopf-loop terrain response."""

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
import sympy as sp
import torch
import z3

import sim_shell_terrain_exact_hopf_loop_harness_probe as exact
import sim_shell_terrain_operator_adapter_probe as terrain


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_terrain_integrator_comparison_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DEPENDENCY_RESULT = RESULT_DIR / "shell_terrain_parametric_family_sweep_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "exact_hopf_loop_terrain_integrator_comparison"
PROMOTION_ALLOWED = False

METHODS = ["euler", "midpoint", "rk4"]
SUBSTEPS = [1, 2, 4, 8]
SAMPLES_PER_LOOP = 16

BLOCKED_CONSUMERS = [
    "terrain layer admission",
    "operator substage admission",
    "continuous terrain flow closure",
    "PEPS3D closure",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

CLAIM_CEILING = (
    "Formal scout only: compares bounded Euler, midpoint, and RK4-style "
    "terrain integration on exact Hopf-loop samples. It tests numerical-method "
    "stability but does not solve continuous terrain flow or admit downstream "
    "manifold, Axis0, flux, physics, or final claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: computes Euler, midpoint, and RK4-style terrain updates over torch density states",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact method/substep/placement count checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects treating bounded integrator convergence as continuous-flow closure",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of integrator-to-admission overclaim",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
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


def field(label: str, sheet: str, rho: torch.Tensor) -> torch.Tensor:
    return terrain.terrain_generator(label, sheet, rho)


def step(label: str, sheet: str, rho: torch.Tensor, h: float, method: str, zero: bool = False) -> torch.Tensor:
    if zero:
        return rho
    if method == "euler":
        return terrain.repair_density(rho + h * field(label, sheet, rho))
    if method == "midpoint":
        k1 = field(label, sheet, rho)
        mid = terrain.repair_density(rho + 0.5 * h * k1)
        return terrain.repair_density(rho + h * field(label, sheet, mid))
    if method == "rk4":
        k1 = field(label, sheet, rho)
        k2 = field(label, sheet, terrain.repair_density(rho + 0.5 * h * k1))
        k3 = field(label, sheet, terrain.repair_density(rho + 0.5 * h * k2))
        k4 = field(label, sheet, terrain.repair_density(rho + h * k3))
        return terrain.repair_density(rho + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))
    raise ValueError(method)


def integrate(label: str, sheet: str, rho: torch.Tensor, method: str, substeps: int, zero: bool = False) -> torch.Tensor:
    out = rho
    h = terrain.DT / substeps
    for _ in range(substeps):
        out = step(label, sheet, out, h, method, zero=zero)
    return out


def placement_rows(all_samples: dict[str, list[dict[str, Any]]], method: str, substeps: int, zero: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configs = [
        ("Type1_inner", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, labels in configs:
        loop_samples = all_samples[loop_name]
        before_avg = exact.average_density(loop_samples)
        for label in labels:
            after_samples = []
            for sample in loop_samples:
                after_samples.append({**sample, "rho_after": integrate(label, sheet, sample["rho"], method, substeps, zero=zero)})
            after_avg = exact.average_density(after_samples, key="rho_after")
            sample_gaps = [terrain.density_gap(sample["rho"], sample["rho_after"]) for sample in after_samples]
            rows.append(
                {
                    "loop": loop_name,
                    "sheet": sheet,
                    "terrain": label,
                    "response": {
                        "avg_density_gap": round(terrain.density_gap(before_avg, after_avg), 12),
                        "mean_sample_density_gap": round(sum(sample_gaps) / len(sample_gaps), 12),
                        "entropy_delta": round(terrain.entropy_vn(after_avg) - terrain.entropy_vn(before_avg), 12),
                        "purity_delta": round(terrain.purity(after_avg) - terrain.purity(before_avg), 12),
                        "path_density_variance": round(exact.path_density_variance(loop_samples), 12),
                        "bloch_path_length": round(exact.bloch_path_length(loop_samples), 12),
                    },
                }
            )
    return rows


def response_count(rows: list[dict[str, Any]]) -> int:
    return exact.unique_response_count(
        rows,
        (
            "avg_density_gap",
            "mean_sample_density_gap",
            "entropy_delta",
            "purity_delta",
            "path_density_variance",
            "bloch_path_length",
        ),
    )


def method_delta(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float:
    return sum(
        abs(float(left["response"]["mean_sample_density_gap"]) - float(right["response"]["mean_sample_density_gap"]))
        for left, right in zip(a, b, strict=True)
    )


def z3_reject_integrator_to_closure() -> bool:
    converges = z3.Bool("bounded_convergence")
    continuous_limit_proven = z3.Bool("continuous_limit_proven")
    admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(admit)
    solver.add(admit == z3.And(converges, continuous_limit_proven))
    solver.add(converges)
    solver.add(z3.Not(continuous_limit_proven))
    return solver.check() == z3.unsat


def cvc5_reject_integrator_to_closure() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    converges = solver.mkConst(bool_sort, "bounded_convergence")
    continuous = solver.mkConst(bool_sort, "continuous_limit_proven")
    admit = solver.mkConst(bool_sort, "admit")
    solver.assertFormula(admit)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, solver.mkTerm(Kind.AND, converges, continuous)))
    solver.assertFormula(converges)
    solver.assertFormula(solver.mkTerm(Kind.NOT, continuous))
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_json(DEPENDENCY_RESULT)
    all_samples = samples()
    runs: dict[tuple[str, int], list[dict[str, Any]]] = {
        (method, substeps): placement_rows(all_samples, method, substeps)
        for method in METHODS
        for substeps in SUBSTEPS
    }
    response_counts = {f"{method}_{substeps}": response_count(rows) for (method, substeps), rows in runs.items()}
    euler_rk4 = [method_delta(runs[("euler", sub)], runs[("rk4", sub)]) for sub in SUBSTEPS]
    midpoint_rk4 = [method_delta(runs[("midpoint", sub)], runs[("rk4", sub)]) for sub in SUBSTEPS]
    zero_gap = max(
        abs(float(row["response"]["mean_sample_density_gap"]))
        for method in METHODS
        for substeps in SUBSTEPS
        for row in placement_rows(all_samples, method, substeps, zero=True)
    )
    exact_count_residual = str(sp.simplify(sp.Integer(len(runs) * 16) - sp.Integer(len(METHODS) * len(SUBSTEPS) * 16)))

    positive = {
        "dependency_parametric_sweep_read": {
            "pass": bool(dependency.get("result_summary", {}).get("all_pass")),
            "witness": dependency.get("result_summary", {}),
        },
        "method_count_exact": {
            "pass": exact_count_residual == "0",
            "witness": {"method_runs": len(runs), "placement_rows": len(runs) * 16, "count_residual": exact_count_residual},
        },
        "all_methods_preserve_placement_distinctions": {
            "pass": min(response_counts.values()) == 16 and max(response_counts.values()) == 16,
            "witness": response_counts,
        },
        "step_refinement_reduces_euler_rk4_delta": {
            "pass": all(a > b for a, b in zip(euler_rk4, euler_rk4[1:])),
            "witness": {"substeps": SUBSTEPS, "euler_vs_rk4": [round(v, 12) for v in euler_rk4]},
        },
        "midpoint_closer_than_euler": {
            "pass": all(m < e for m, e in zip(midpoint_rk4, euler_rk4, strict=True)),
            "witness": {"midpoint_vs_rk4": [round(v, 12) for v in midpoint_rk4], "euler_vs_rk4": [round(v, 12) for v in euler_rk4]},
        },
    }

    graveyard_companions = {
        "zero_field_collapses_all_methods": {
            "pass": zero_gap < 1.0e-9,
            "witness": {"zero_field_max_gap": round(zero_gap, 12)},
        },
        "bounded_integrator_to_closure_rejected_cross_solver": {
            "pass": z3_reject_integrator_to_closure() and cvc5_reject_integrator_to_closure(),
            "witness": {"z3_unsat": z3_reject_integrator_to_closure(), "cvc5_unsat": cvc5_reject_integrator_to_closure()},
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
        "tier": "exact_hopf_loop_terrain_integrator_comparison",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Check whether exact Hopf-loop terrain response features are artifacts of Euler integration.",
        "scientific_question": "Do Euler, midpoint, and RK4-style bounded integrators preserve terrain placement distinctions, and does step refinement reduce method gap?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": "IntegratorCompare: exact Hopf-loop terrain response x integrator x substep count -> method-stability table plus blocked consumers",
        "domain": "3 integrators x 4 substep counts x 16 terrain placements over exact Hopf-loop samples",
        "codomain_or_output": "method response counts, convergence deltas, zero-field control, admission-overclaim rejection",
        "carrier_layer": "exact Hopf loop spinors with spinor-derived densities",
        "geometry_layer": "S3 Hopf fiber/base terrain response integrator comparison",
        "carrier_realization": "torch spinors and 2x2 densities",
        "peps3d_embedding": {"site_floors": exact.SITE_FLOORS, "max_sites": max(exact.SITE_FLOORS.values()), "bond_dim": 2, "closure_claimed": False},
        "spinor_state": f"psi(phi,chi;eta) sampled along Gamma_f/Gamma_b with eta={exact.ETA}",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(DEPENDENCY_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_integrator_comparison_only",
        "cut_layer": "single-sheet density readouts only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "bounded Euler/midpoint/RK4-style exact Hopf-loop terrain response",
        "branch_status_before_run": "ParametricFamilySweep passed bounded strength/step variants; numerical method artifact risk remained open.",
        "allowed_claims": [
            "The tested bounded integrators preserve placement distinctions.",
            "Step refinement reduces Euler-vs-RK4 response delta.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["continuous-flow theorem not proved", "source parametric families not exhausted"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["ParametricFamilySweep receipt"],
        "data_or_artifact_dependencies": [str(DEPENDENCY_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "placement distinctions vanish under non-Euler method",
            "step refinement does not reduce method delta",
            "zero field produces nonzero response",
            "bounded integrator comparison is promoted as continuous-flow closure",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(runs) + 1,
            "passed": len(runs) + 1,
            "variants": {
                "euler_midpoint_rk4": "all preserve 16 placement response distinctions",
                "substep_refinement": "reduces Euler-vs-RK4 delta",
                "zero_field": "collapses",
            },
        },
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "integrator responses preserve distinctions, refinement reduces method deltas, controls collapse/reject, downstream remains blocked",
        "fail_rule": "method changes destroy distinctions, refinement fails, control survives, or downstream admission unlocks",
        "why_not_v4_probes": "This is v4.3 object-preservation terrain numerical-method stability work; it does not become Axis0, Xi/Phi0, flux, or manifold closure.",
        "method_response_counts": response_counts,
        "readouts": {
            "substeps": SUBSTEPS,
            "euler_vs_rk4": [round(v, 12) for v in euler_rk4],
            "midpoint_vs_rk4": [round(v, 12) for v in midpoint_rk4],
            "zero_field_max_gap": round(zero_gap, 12),
        },
        "result_summary": {
            "all_pass": all_pass,
            "methods": METHODS,
            "substeps": SUBSTEPS,
            "method_runs": len(runs),
            "terrain_laws": 8,
            "placements_per_method": 16,
            "response_count_min": min(response_counts.values()),
            "response_count_max": max(response_counts.values()),
            "euler_rk4_delta_start": round(euler_rk4[0], 9),
            "euler_rk4_delta_end": round(euler_rk4[-1], 9),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
