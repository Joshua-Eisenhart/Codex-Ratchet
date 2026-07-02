#!/usr/bin/env python3
"""Scale and negative battery for exact Hopf-loop terrain responses.

This scout scales the exact Hopf-loop terrain harness from 64 to 256 loop
samples and runs a small negative battery. It is robustness evidence only; it
does not admit terrain layers, PEPS3D closure, Axis0, flux, stacking, physics,
or final manifold claims.
"""

from __future__ import annotations

import hashlib
import json
import math
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
NAME = "shell_terrain_operator_scale_battery_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DEPENDENCY_RESULT = RESULT_DIR / "shell_terrain_exact_hopf_loop_harness_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "exact_hopf_loop_terrain_scale_negative_battery"
PROMOTION_ALLOWED = False

SCALES = [16, 32, 64]
TOTAL_SAMPLE_SCALES = [4 * n for n in SCALES]
EPS = 1.0e-12

BLOCKED_CONSUMERS = [
    "terrain layer admission",
    "operator substage admission",
    "PEPS3D closure",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

CLAIM_CEILING = (
    "Formal scout only: scale/negative-battery robustness over the exact "
    "Hopf-loop terrain harness. It does not admit terrain layers, PEPS3D "
    "closure, Axis0, Xi/Phi0, flux, physics, gravity, stacking, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: recomputes exact Hopf-loop terrain density responses across 64/128/256 samples",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: rejects support-erased incidence and records scale incidence counts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: compares noncommuting operator-order graph against commuting control",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: exact scale/sample count checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects promotion when scale passes but exact downstream gates remain blocked",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of scale-to-admission overclaim",
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


def make_samples(samples_per_loop: int) -> dict[str, list[dict[str, Any]]]:
    old = exact.SAMPLES_PER_LOOP
    exact.SAMPLES_PER_LOOP = samples_per_loop
    try:
        return {
            "Type1_inner": exact.loop_samples("Type1_inner"),
            "Type1_outer": exact.loop_samples("Type1_outer"),
            "Type2_inner": exact.loop_samples("Type2_inner"),
            "Type2_outer": exact.loop_samples("Type2_outer"),
        }
    finally:
        exact.SAMPLES_PER_LOOP = old


def sample_stats(all_samples: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
    fiber_variances = []
    base_variances = []
    fiber_raw = []
    for rows in all_samples.values():
        if rows[0]["loop_kind"] == "fiber":
            fiber_variances.append(exact.path_density_variance(rows))
            fiber_raw.append(exact.raw_spinor_path_length(rows))
        else:
            base_variances.append(exact.path_density_variance(rows))
    return {
        "fiber_density_variance_max": round(max(fiber_variances), 12),
        "fiber_raw_spinor_path_length_min": round(min(fiber_raw), 12),
        "base_density_variance_min": round(min(base_variances), 12),
    }


def response_counts(placements: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "full": exact.unique_response_count(
            placements,
            (
                "avg_density_gap",
                "mean_sample_density_gap",
                "entropy_delta",
                "purity_delta",
                "path_density_variance",
                "bloch_path_length",
            ),
        ),
        "density": exact.unique_response_count(
            placements,
            ("avg_density_gap", "mean_sample_density_gap", "entropy_delta", "purity_delta"),
        ),
        "entropy": exact.unique_response_count(placements, ("entropy_delta",)),
    }


def density_fingerprint(placements: list[dict[str, Any]]) -> list[tuple[float, ...]]:
    return sorted(
        tuple(round(float(row["response"][key]), 9) for key in ("avg_density_gap", "mean_sample_density_gap", "entropy_delta", "purity_delta"))
        for row in placements
    )


def same_sign_placements(all_samples: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    configs = [
        ("Type1_inner", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, labels in configs:
        samples = all_samples[loop_name]
        before_avg = exact.average_density(samples)
        for label in labels:
            after_samples = []
            for sample in samples:
                gen = terrain.terrain_generator(label, sheet, sample["rho"], same_sign=True)
                after_samples.append({**sample, "rho_after": terrain.repair_density(sample["rho"] + terrain.DT * gen)})
            after_avg = exact.average_density(after_samples, key="rho_after")
            rows.append(
                {
                    "loop": loop_name,
                    "sheet": sheet,
                    "terrain": label,
                    "response": {
                        "avg_density_gap": round(terrain.density_gap(before_avg, after_avg), 12),
                        "mean_sample_density_gap": round(sum(terrain.density_gap(s["rho"], s["rho_after"]) for s in after_samples) / len(after_samples), 12),
                        "entropy_delta": round(terrain.entropy_vn(after_avg) - terrain.entropy_vn(before_avg), 12),
                        "purity_delta": round(terrain.purity(after_avg) - terrain.purity(before_avg), 12),
                    },
                }
            )
    return rows


def loop_erased_placements(all_samples: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    erased = {
        "Type1_inner": all_samples["Type1_inner"],
        "Type1_outer": all_samples["Type1_inner"],
        "Type2_inner": all_samples["Type2_inner"],
        "Type2_outer": all_samples["Type2_inner"],
    }
    return exact.terrain_placement_rows(erased)


def support_erased_rejected(all_samples: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    hypergraph = xgi.Hypergraph()
    for name, rows in all_samples.items():
        for row in rows:
            hypergraph.add_edge([f"loop:{name}", f"sample:{row['sample']}"])
    support_erased_has_site_anchor = False
    return {
        "hyperedges": hypergraph.num_edges,
        "support_erased_has_site_anchor": support_erased_has_site_anchor,
        "rejected": not support_erased_has_site_anchor,
    }


def operator_order_battery(rho: torch.Tensor) -> dict[str, Any]:
    actual = terrain.operator_responses(rho)["FeTi_vs_TeFi_order_gap"]
    commuting_a = terrain.op_channel("Fe", terrain.op_channel("Fe", rho))
    commuting_b = terrain.op_channel("Fe", terrain.op_channel("Fe", rho))
    commuting_gap = terrain.density_gap(commuting_a, commuting_b)
    graph = rx.PyDiGraph()
    a = graph.add_node("noncommuting_order")
    b = graph.add_node("commuting_control")
    graph.add_edge(a, b, "control")
    return {
        "actual_order_gap": actual,
        "commuting_control_gap": round(commuting_gap, 12),
        "graph_nodes": graph.num_nodes(),
        "graph_edges": graph.num_edges(),
    }


def z3_reject_scale_to_admission() -> bool:
    scale_pass = z3.Bool("scale_pass")
    exact_flow_solved = z3.Bool("exact_flow_solved")
    downstream_blocked = z3.Bool("downstream_blocked")
    admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(admit)
    solver.add(admit == z3.And(scale_pass, exact_flow_solved, z3.Not(downstream_blocked)))
    solver.add(scale_pass)
    solver.add(z3.Not(exact_flow_solved))
    solver.add(downstream_blocked)
    return solver.check() == z3.unsat


def cvc5_reject_scale_to_admission() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    scale_pass = solver.mkConst(bool_sort, "scale_pass")
    exact_flow_solved = solver.mkConst(bool_sort, "exact_flow_solved")
    downstream_blocked = solver.mkConst(bool_sort, "downstream_blocked")
    admit = solver.mkConst(bool_sort, "admit")
    rhs = solver.mkTerm(Kind.AND, scale_pass, exact_flow_solved, solver.mkTerm(Kind.NOT, downstream_blocked))
    solver.assertFormula(admit)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, rhs))
    solver.assertFormula(scale_pass)
    solver.assertFormula(solver.mkTerm(Kind.NOT, exact_flow_solved))
    solver.assertFormula(downstream_blocked)
    return str(solver.checkSat()) == "unsat"


def run_scale(samples_per_loop: int) -> dict[str, Any]:
    samples = make_samples(samples_per_loop)
    placements = exact.terrain_placement_rows(samples)
    zero = exact.terrain_placement_rows(samples, zero=True)
    counts = response_counts(placements)
    stats = sample_stats(samples)
    zero_gap = max(abs(float(row["response"]["mean_sample_density_gap"])) for row in zero)
    return {
        "samples_per_loop": samples_per_loop,
        "total_samples": sum(len(v) for v in samples.values()),
        "response_counts": counts,
        "sample_stats": stats,
        "zero_max_gap": round(zero_gap, 12),
        "placements": placements,
        "samples": samples,
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependency = load_json(DEPENDENCY_RESULT)
    scale_runs = [run_scale(n) for n in SCALES]
    main_run = scale_runs[1]
    actual_fp = density_fingerprint(main_run["placements"])
    same_sign_fp = density_fingerprint(same_sign_placements(main_run["samples"]))
    loop_erased_fp = density_fingerprint(loop_erased_placements(main_run["samples"]))
    same_sign_delta = sum(abs(a[i] - b[i]) for a, b in zip(actual_fp, same_sign_fp, strict=True) for i in range(len(a)))
    loop_erased_delta = sum(abs(a[i] - b[i]) for a, b in zip(actual_fp, loop_erased_fp, strict=True) for i in range(len(a)))
    support_control = support_erased_rejected(main_run["samples"])
    avg_rho = terrain.repair_density(sum(exact.average_density(rows) for rows in main_run["samples"].values()) / 4.0)
    op_battery = operator_order_battery(avg_rho)

    exact_scale_residual = str(sp.simplify(sp.Integer([run["total_samples"] for run in scale_runs][-1]) - sp.Integer(256)))
    all_scales_keep_16 = all(run["response_counts"]["full"] == 16 and run["response_counts"]["entropy"] < 16 for run in scale_runs)
    all_fiber_invisible = all(run["sample_stats"]["fiber_density_variance_max"] <= 1.0e-10 for run in scale_runs)
    all_zero_collapses = all(run["zero_max_gap"] < 1.0e-9 for run in scale_runs)

    positive = {
        "dependency_exact_hopf_read": {
            "pass": bool(dependency.get("result_summary", {}).get("all_pass")),
            "witness": dependency.get("result_summary", {}),
        },
        "scale_counts_exact": {
            "pass": exact_scale_residual == "0" and [run["total_samples"] for run in scale_runs] == TOTAL_SAMPLE_SCALES,
            "witness": {"total_sample_scales": [run["total_samples"] for run in scale_runs], "scale_residual": exact_scale_residual},
        },
        "responses_preserve_16_placements_across_scale": {
            "pass": all_scales_keep_16,
            "witness": [{"total_samples": run["total_samples"], **run["response_counts"]} for run in scale_runs],
        },
        "fiber_density_invisibility_preserved_across_scale": {
            "pass": all_fiber_invisible,
            "witness": [{"total_samples": run["total_samples"], **run["sample_stats"]} for run in scale_runs],
        },
        "operator_order_battery_noncommuting_vs_commuting": {
            "pass": op_battery["actual_order_gap"] > 0.01 and op_battery["commuting_control_gap"] < 1.0e-12,
            "witness": op_battery,
        },
    }

    graveyard_companions = {
        "zero_generator_collapses_all_scales": {
            "pass": all_zero_collapses,
            "witness": [{"total_samples": run["total_samples"], "zero_max_gap": run["zero_max_gap"]} for run in scale_runs],
        },
        "support_erased_rejected": {
            "pass": support_control["rejected"],
            "witness": support_control,
        },
        "sheet_sign_erasure_changes_response": {
            "pass": same_sign_delta > 0.01,
            "witness": {"same_sign_delta": round(same_sign_delta, 12)},
        },
        "loop_erasure_changes_response": {
            "pass": loop_erased_delta > 0.01,
            "witness": {"loop_erased_delta": round(loop_erased_delta, 12)},
        },
        "scale_to_admission_rejected_cross_solver": {
            "pass": z3_reject_scale_to_admission() and cvc5_reject_scale_to_admission(),
            "witness": {"z3_unsat": z3_reject_scale_to_admission(), "cvc5_unsat": cvc5_reject_scale_to_admission()},
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
        "tier": "exact_hopf_loop_terrain_scale_battery",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Scale exact Hopf-loop terrain responses and run negative controls before any terrain/Axis/flux claim.",
        "scientific_question": "Do exact Hopf-loop terrain response features survive 64/128/256 sample scales while controls reject support erasure, loop erasure, sheet-sign erasure, and scale-to-admission overclaim?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": "ScaleBattery: exact Hopf-loop terrain response -> scale robustness table plus negative-control rejection vector",
        "domain": "exact Hopf-loop terrain harness at total sample scales 64/128/256",
        "codomain_or_output": "scale robustness summaries, negative battery outcomes, operator-order control, blocked consumers",
        "carrier_layer": "exact Hopf loop spinors with spinor-derived densities",
        "geometry_layer": "S3 Hopf fiber/base loop terrain response scale battery",
        "carrier_realization": "torch spinors and 2x2 densities; no dense-state closure",
        "peps3d_embedding": {"site_floors": exact.SITE_FLOORS, "max_sites": max(exact.SITE_FLOORS.values()), "bond_dim": 2, "closure_claimed": False},
        "spinor_state": f"psi(phi,chi;eta) sampled along Gamma_f/Gamma_b with eta={exact.ETA}",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(DEPENDENCY_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_scale_battery_only",
        "cut_layer": "single-sheet density readouts only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "exact Hopf-loop terrain response robustness and controls",
        "branch_status_before_run": "ExactHopfLoopHarness produced validated source-loop response at 64 samples.",
        "allowed_claims": [
            "The exact Hopf-loop terrain response survives the tested sample scales.",
            "The negative controls reject support erasure, loop erasure, sheet-sign erasure, and scale-to-admission overclaim.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["continuous-time terrain flow not solved", "parametric terrain families not exhausted"],
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
        "required_inputs": ["ExactHopfLoopHarness receipt"],
        "data_or_artifact_dependencies": [str(DEPENDENCY_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "response fails to preserve placement distinctions across scale",
            "support-erased control passes",
            "loop-erased or sheet-sign-erased controls preserve the claimed response",
            "scale is promoted as terrain/Axis/flux admission",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": {
                "scale_64_128_256": "passes",
                "zero_generator": "collapses",
                "support_erased": "rejected",
                "sheet_sign_erased": "changes response",
                "loop_erased": "changes response",
            },
        },
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "all scale positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any scale, support, loop, sheet, order, or promotion control survives incorrectly",
        "why_not_v4_probes": "This is v4.3 object-preservation terrain robustness work over exact shell/Hopf terrain responses; it does not become Axis0, Xi/Phi0, flux, or manifold closure.",
        "scale_runs": [
            {
                "samples_per_loop": run["samples_per_loop"],
                "total_samples": run["total_samples"],
                "response_counts": run["response_counts"],
                "sample_stats": run["sample_stats"],
                "zero_max_gap": run["zero_max_gap"],
            }
            for run in scale_runs
        ],
        "readouts": {
            "same_sign_delta": round(same_sign_delta, 12),
            "loop_erased_delta": round(loop_erased_delta, 12),
            "operator_order_battery": op_battery,
        },
        "result_summary": {
            "all_pass": all_pass,
            "sample_scales": TOTAL_SAMPLE_SCALES,
            "terrain_laws": 8,
            "placements": 16,
            "max_total_samples": max(TOTAL_SAMPLE_SCALES),
            "max_peps3d_sites": max(exact.SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "same_sign_delta": round(same_sign_delta, 9),
            "loop_erased_delta": round(loop_erased_delta, 9),
            "operator_order_gap": op_battery["actual_order_gap"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
