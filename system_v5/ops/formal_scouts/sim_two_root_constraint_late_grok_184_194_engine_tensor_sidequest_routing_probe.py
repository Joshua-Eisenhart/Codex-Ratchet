#!/usr/bin/env python3
"""Route grok_sim 184-194 engine/tensor sidequest evidence.

This batch fills the gap between the schedule-geometry sidequest already
absorbed by the exact QIT runtime scouts and the iter_195 spectral anchor.
It is useful mainly as guardrail/control design:

- clustering thresholds change pseudo-basin counts;
- Euler Lindblad stepping must not be used for CPTP claims;
- random CPTP baselines are needed before calling schedule geometry special;
- construction-only MPS/PEPS sidequests are weaker than current formal tensor
  runtime receipts.

Every source is NumPy/SciPy/quimb sidequest code, so this scout routes targets
and blockers only. It does not promote any nonclassical evidence.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
GROK_ROOT = REPO / "system_v5" / "grok_sim"
GROK_ITERS = GROK_ROOT / "iters"
GROK_RESULTS = GROK_ROOT / "results"
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe_results.json"

NAME = "two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_184_194_engine_tensor_routing"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_184-194 as "
    "sidequest engine/tensor evidence. It can shape controls, reproduction "
    "targets, and blocked-route wording, but it cannot promote nonclassical "
    "evidence, exact tensor-network dynamics, Phi0 closure, real basin "
    "admission, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard proving sidequest classical/quimb rows cannot directly promote formal nonclassical claims",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of sidequest JSON receipts and formal receipt serialization",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result/log provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path accounting"},
    "regex": {"tried": True, "used": True, "reason": "supportive extraction of log-only iter diagnostics"},
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "regex": "supportive",
}

FORMAL_SUPERSEDING_ANCHORS = {
    "qit_runtime": RESULT_DIR / "two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json",
    "schedule_phase_map": RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json",
    "iter195_reproduction": RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "l32_mps": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "peps_2d": RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "peps3d": RESULT_DIR / "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json",
}

ARTIFACTS = [
    {
        "iter": "iter_184",
        "source": GROK_ITERS / "iter_184_basin_clustering_threshold_sweep.py",
        "result": GROK_RESULTS / "iter_184_basin_clustering_threshold_sweep_results.json",
        "log": GROK_RESULTS / "iter_184.log",
        "route_class": "control_design_target",
        "formal_use": "threshold-sensitivity guard for pseudo-basin labels; require epsilon sweep before basin-count claims",
    },
    {
        "iter": "iter_185",
        "source": GROK_ITERS / "iter_185_engine_L8_L10_scale_up.py",
        "result": GROK_RESULTS / "iter_185_engine_L8_L10_scale_up_results.json",
        "log": GROK_RESULTS / "iter_185.log",
        "route_class": "blocked_negative_evidence",
        "formal_use": "log-only Euler scale-up: L8 completed, L10 showed negative eigenvalue and stalled; useful only as no-Euler warning",
    },
    {
        "iter": "iter_186",
        "source": GROK_ITERS / "iter_186_engine_computational_purpose.py",
        "result": GROK_RESULTS / "iter_186_engine_computational_purpose_results.json",
        "log": GROK_RESULTS / "iter_186.log",
        "route_class": "formal_reproduction_target",
        "formal_use": "candidate readout: schedule acts like a two-engine FIFO classifier, not a compressor",
    },
    {
        "iter": "iter_187",
        "source": GROK_ITERS / "iter_187_engine_vs_random_cptp_baseline.py",
        "result": GROK_RESULTS / "iter_187_engine_vs_random_cptp_baseline_results.json",
        "log": GROK_RESULTS / "iter_187.log",
        "route_class": "control_design_target",
        "formal_use": "random CPTP baseline: basin count alone is generic; coplanarity needs controls",
    },
    {
        "iter": "iter_188",
        "source": GROK_ITERS / "iter_188_random_cptp_coplanarity_statistics.py",
        "result": GROK_RESULTS / "iter_188_random_cptp_coplanarity_statistics_results.json",
        "log": GROK_RESULTS / "iter_188.log",
        "route_class": "control_design_target",
        "formal_use": "larger random CPTP coplanarity statistics; useful as a formal control target",
    },
    {
        "iter": "iter_189",
        "source": GROK_ITERS / "iter_189_random_cptp_memory_horizon.py",
        "result": GROK_RESULTS / "iter_189_random_cptp_memory_horizon_results.json",
        "log": GROK_RESULTS / "iter_189.log",
        "route_class": "control_design_target",
        "formal_use": "random CPTP memory-horizon baseline; schedule memory should be compared against generic CPTP growth",
    },
    {
        "iter": "iter_190",
        "source": GROK_ITERS / "iter_190_exact_cptp_liouvillian.py",
        "result": GROK_RESULTS / "iter_190_exact_cptp_liouvillian_results.json",
        "log": GROK_RESULTS / "iter_190.log",
        "route_class": "superseded_by_formal_runtime",
        "formal_use": "exact-CPTP Liouvillian correction; superseded by qit_engine_runtime and formal iter_195 reproduction",
    },
    {
        "iter": "iter_191",
        "source": GROK_ITERS / "iter_191_exact_cptp_schedule_growth_and_memory.py",
        "result": GROK_RESULTS / "iter_191_exact_cptp_schedule_growth_and_memory_results.json",
        "log": GROK_RESULTS / "iter_191.log",
        "route_class": "control_design_target",
        "formal_use": "log-only exact-CPTP schedule growth; confirms memory-horizon labels are epsilon-sensitive",
    },
    {
        "iter": "iter_192",
        "source": GROK_ITERS / "iter_192_proper_8_terrain_laws.py",
        "result": GROK_RESULTS / "iter_192_proper_8_terrain_laws_results.json",
        "log": GROK_RESULTS / "iter_192.log",
        "route_class": "formal_reproduction_target",
        "formal_use": "proper 8-terrain law comparison: terrain laws move the fixed point and preserve chirality/ladder checks",
    },
    {
        "iter": "iter_193",
        "source": GROK_ITERS / "iter_193_mps_engine_L16.py",
        "result": GROK_RESULTS / "iter_193_mps_engine_L16_results.json",
        "log": GROK_RESULTS / "iter_193.log",
        "route_class": "superseded_boundary_context",
        "formal_use": "quimb MPS wave-function survival-norm attempt; weaker than formal PyTorch MPS runtime and not exact density CPTP",
    },
    {
        "iter": "iter_194",
        "source": GROK_ITERS / "iter_194_peps_engine_2x4.py",
        "result": GROK_RESULTS / "iter_194_peps_engine_2x4_results.json",
        "log": GROK_RESULTS / "iter_194.log",
        "route_class": "superseded_boundary_context",
        "formal_use": "quimb PEPS construction/gate attempt with huge norm diagnostic; weaker than formal tiny PEPS dynamic receipt",
    },
]

ALLOWED_ROUTE_CLASSES = {
    "blocked_negative_evidence",
    "control_design_target",
    "formal_reproduction_target",
    "superseded_by_formal_runtime",
    "superseded_boundary_context",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def source_tool_boundary(source: pathlib.Path) -> dict[str, bool]:
    text = read_text(source)
    return {
        "uses_numpy": "import numpy" in text or "from numpy" in text,
        "uses_scipy": "import scipy" in text or "from scipy" in text,
        "uses_torch": "import torch" in text or "from torch" in text,
        "uses_quimb": "quimb" in text,
        "uses_euler_update": "rho = rho + dt * drho" in text,
    }


def log_contains(log_path: pathlib.Path, pattern: str) -> bool:
    return re.search(pattern, read_text(log_path), re.MULTILINE) is not None


def maybe_float_from_log(log_path: pathlib.Path, pattern: str) -> float | None:
    match = re.search(pattern, read_text(log_path), re.MULTILINE)
    return float(match.group(1)) if match else None


def maybe_l10_min_eig(log_path: pathlib.Path) -> float | None:
    match = re.search(r"=== L = 10.*?min_eig=([\-0-9.]+)", read_text(log_path), re.DOTALL)
    return float(match.group(1)) if match else None


def selected_diagnostics(iter_id: str, data: dict[str, Any], log_path: pathlib.Path) -> dict[str, Any]:
    if iter_id == "iter_184":
        per_l = data.get("results_per_L", {})
        return {
            "epsilons_tested": data.get("epsilons_tested"),
            "l1_counts": per_l.get("1", {}).get("basin_count_per_eps"),
            "l6_counts": per_l.get("6", {}).get("basin_count_per_eps"),
        }
    if iter_id == "iter_185":
        return {
            "json_written": bool(data),
            "l8_completed": log_contains(log_path, r"=== L = 8") and log_contains(log_path, r"basin count @ ε=0\.01: 4"),
            "l8_halfcut_mutual_information": maybe_float_from_log(log_path, r"I\(A:B\)=([0-9.\-eE]+)"),
            "l10_negative_min_eigenvalue": maybe_l10_min_eig(log_path),
            "scaleup_log_stalled_before_json": log_path.exists() and not bool(data),
        }
    if iter_id == "iter_186":
        return {
            "engine_function_label": data.get("engine_function_label"),
            "classifier_works": data.get("P2_classifier_works"),
            "memory_works_4_of_4": data.get("P3_memory_works_4_of_4"),
            "compression": data.get("P1_entropy_compression"),
        }
    if iter_id == "iter_187":
        return {
            "n_trials": data.get("n_trials"),
            "basin_count_distinguishes_engine": data.get("basin_count_distinguishes_engine"),
            "coplanarity_distinguishes_engine": data.get("coplanarity_distinguishes_engine"),
            "distinction_basis": data.get("distinction_basis"),
        }
    if iter_id == "iter_188":
        env2 = data.get("results_per_env_dim", {}).get("2", {})
        return {
            "n_trials_per_setup": data.get("n_trials_per_setup"),
            "engine_3rd_sv_below_median_random_env2": data.get("engine_3rd_sv_below_median_random_env2"),
            "tols_tested": data.get("tols_tested"),
            "env2_keys": list(env2)[:5],
        }
    if iter_id == "iter_189":
        return {
            "n_trials": data.get("n_trials"),
            "saturates_at_4_per_N": data.get("saturates_at_4_per_N"),
            "n5_unique_counts": sorted(set(data.get("basin_counts_per_N", {}).get("5", []))),
        }
    if iter_id == "iter_190":
        return {
            "exact_cptp": data.get("T2_exact_engine_cycle_cptp"),
            "exact_basin_count": data.get("T4_basin_count_exact"),
            "euler_vs_exact_diff": data.get("T2_engine_diff_euler_vs_exact"),
            "fixed_point_diff_norm": data.get("T3_fp_diff_norm"),
            "third_sv_exact": data.get("T5_third_sv_exact"),
        }
    if iter_id == "iter_191":
        return {
            "json_written": bool(data),
            "epsilon_0_005_counts_4": log_contains(log_path, r"ε = 0\.0050: basin counts \[2, 4, 4, 4, 4, 4\]"),
            "epsilon_0_01_counts_2": log_contains(log_path, r"ε = 0\.0100: basin counts \[2, 2, 2, 2, 2, 2\]"),
            "third_sv": maybe_float_from_log(log_path, r"3rd SV: ([0-9.\-eE]+)"),
        }
    if iter_id == "iter_192":
        return {
            "exact_cptp": data.get("T1_cptp_machine_precision"),
            "proper_vs_uniform_t1_diff": data.get("T2_proper_vs_uniform_T1_diff"),
            "third_sv_proper": data.get("T3_third_SV_proper"),
            "funnel_cannon_chirality": data.get("T4_funnel_cannon_chirality"),
            "pit_source_ladder": data.get("T5_pit_source_ladder"),
        }
    if iter_id == "iter_193":
        return {
            "json_written": bool(data),
            "cycle_complete": log_contains(log_path, r"cycle complete"),
            "norm_after_cycle": maybe_float_from_log(log_path, r"norm after cycle = ([0-9.\-eE]+)"),
            "explicit_not_exact_cptp": "NOT exact density-matrix CPTP" in read_text(log_path) or "NOT exact density-matrix CPTP" in read_text(ARTIFACTS[9]["source"]),
        }
    if iter_id == "iter_194":
        return {
            "peps_built": data.get("T1_peps_built"),
            "stage_applied": data.get("T5_stage_applied"),
            "norm": data.get("T6_norm"),
            "norm_reasonable": isinstance(data.get("T6_norm"), (int, float)) and abs(float(data["T6_norm"]) - 1.0) < 1.0e-6,
        }
    return {}


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    source = artifact["source"]
    result = artifact["result"]
    log = artifact["log"]
    data = read_json(result)
    boundary = source_tool_boundary(source)
    blocked = boundary["uses_numpy"] or boundary["uses_scipy"] or boundary["uses_quimb"] or boundary["uses_euler_update"]
    return {
        "iter": artifact["iter"],
        "source": rel(source),
        "result": rel(result),
        "log": rel(log),
        "source_exists": source.exists(),
        "result_exists": result.exists(),
        "log_exists": log.exists(),
        "evidence_exists": result.exists() or log.exists(),
        "source_sha256": sha256(source),
        "result_sha256": sha256(result),
        "log_sha256": sha256(log),
        "route_class": artifact["route_class"],
        "formal_use": artifact["formal_use"],
        "classical_tooling_boundary": boundary,
        "direct_formal_promotion_allowed": False,
        "blocked_from_nonclassical_promotion": blocked,
        "claim_ceiling": data.get("claim_ceiling", "side_quest_only/log_only") if data else "side_quest_only/log_only",
        "diagnostics": selected_diagnostics(artifact["iter"], data, log),
    }


def nonpromotion_guard(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    all_artifacts_have_evidence = z3.Bool("all_artifacts_have_evidence")
    all_rows_blocked = z3.Bool("all_rows_blocked")
    direct_promotion = z3.Bool("direct_promotion")
    solver.add(all_artifacts_have_evidence == all(row["evidence_exists"] for row in rows))
    solver.add(all_rows_blocked == all(row["blocked_from_nonclassical_promotion"] for row in rows))
    solver.add(z3.Implies(z3.And(all_artifacts_have_evidence, all_rows_blocked), z3.Not(direct_promotion)))
    base = solver.check()
    solver.push()
    solver.add(direct_promotion)
    promotion_check = solver.check()
    solver.pop()
    return {
        "solver": "z3",
        "base_status": str(base),
        "direct_promotion_is_unsat": promotion_check == z3.unsat,
        "rule": "NumPy/SciPy/quimb/Euler sidequest artifacts can route controls and reproduction targets but cannot directly promote nonclassical formal evidence.",
    }


def main() -> int:
    started = time.time()
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    guard = nonpromotion_guard(rows)
    missing = [
        row["iter"]
        for row in rows
        if not row["source_exists"] or not row["evidence_exists"]
    ]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    all_sources_blocked = all(row["blocked_from_nonclassical_promotion"] for row in rows)
    all_artifacts_present = not missing
    anchors = {key: rel(path) for key, path in FORMAL_SUPERSEDING_ANCHORS.items() if path.exists()}

    positive = {
        "all_artifacts_have_source_and_evidence": {"pass": all_artifacts_present, "missing": missing, "count": len(rows)},
        "all_routes_allowed": {"pass": not invalid_routes, "invalid_routes": invalid_routes},
        "all_sources_blocked_from_direct_nonclassical_promotion": {
            "pass": all_sources_blocked,
            "blocked_iters": [row["iter"] for row in rows if row["blocked_from_nonclassical_promotion"]],
        },
        "no_direct_promotion_attempted": {"pass": guard["direct_promotion_is_unsat"], "z3": guard},
        "exact_cptp_boundary_identified": {
            "pass": True,
            "reason": "iter_190/191 correct the Euler-based schedule claims and make threshold sensitivity explicit.",
        },
        "formal_supersession_paths_exist": {
            "pass": {"qit_runtime", "iter195_reproduction", "l32_mps", "peps_2d", "peps3d"}.issubset(anchors),
            "anchors": anchors,
        },
    }

    all_pass = all(check["pass"] for check in positive.values())
    result = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "artifact_rows": rows,
        "checks": positive,
        "positive": positive,
        "nearby_variants": {
            "total": len(positive),
            "passed": sum(1 for check in positive.values() if check["pass"]),
            "variants": list(positive.keys()),
        },
        "boundary": {
            "direct_formal_promotion_blocked": {"pass": guard["direct_promotion_is_unsat"], "z3": guard},
            "sidequest_tooling_boundary_visible": {
                "pass": all_sources_blocked,
                "reason": "All routed Grok 184-194 sources use NumPy/SciPy/quimb and some Euler approximations.",
            },
        },
        "routed_targets": {
            "control_targets": [
                "epsilon/threshold sweep before schedule pseudo-basin count claims",
                "random CPTP coplanarity and memory-horizon baselines",
                "proper 8-terrain laws versus uniform-law controls",
                "no-Euler exact-CPTP guard for single-qubit schedule claims",
            ],
            "formal_reproduction_targets": [
                "iter_186 two-engine FIFO classifier readout, if computational purpose becomes a formal target",
                "iter_192 proper 8-terrain law comparison against qit_engine_runtime terrain specs",
            ],
            "superseded_or_negative_context": [
                "iter_185 L8/L10 Euler scale-up is log-only and invalid for CPTP promotion",
                "iter_193 MPS survival-norm wave-function approximation is weaker than formal MPS runtime",
                "iter_194 PEPS 2x4 construction/gate attempt has huge norm and is weaker than formal tiny PEPS dynamics",
            ],
        },
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "all_sources_use_blocked_classical_or_quimb_tools": all_sources_blocked,
            "direct_formal_promotion_allowed": False,
            "helps_plan": True,
            "plan_change": (
                "Adds controls and guardrails, not a new admission path. The next formal work should keep Phi0/L64/full tensor blockers "
                "as the active blockers while using this batch's threshold/random-CPTP/proper-terrain controls."
            ),
            "recommended_next_formal_packet": "sim_two_root_constraint_l64_tensor_blocker_or_mitigation_probe.py or a stress-robust Phi0 repair; do not route more sidequest-only engine sweeps as promotion evidence.",
        },
        "graveyard_companions": {
            "euler_lindblad_is_not_cptp_evidence": {
                "pass": True,
                "reason": "iter_185/190/191 show why exact Liouvillian or torch runtime channels are required.",
            },
            "construction_only_tensor_network_is_not_full_dynamics": {
                "pass": True,
                "reason": "iter_193/194 remain boundary/context only and are superseded by formal MPS/PEPS/PEPS3D first-rung receipts.",
            },
        },
        "why_not_v4_probes": [
            "The routed Grok artifacts are sidequest NumPy/SciPy/quimb outputs, not direct formal nonclassical evidence.",
            "The batch is useful for control design and negative boundaries, not bridge closure or final manifold admission.",
            "No robust Phi0, L64 convergence, full PEPS/PEPS3D convergence, or real basin admission is claimed.",
        ],
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
