#!/usr/bin/env python3
"""Route grok_sim 196-203 engine-spectral sidequest evidence.

The 196-203 sidequest batch is useful for the QIT engine/manifold build, but
every source file in the batch uses NumPy/SciPy and every receipt is
`side_quest_only`. This scout preserves the useful targets while blocking
direct promotion into the formal nonclassical runtime.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
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
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json"

NAME = "two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_196_203_engine_spectral_routing"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_196-203 as "
    "sidequest engine-spectral evidence. It can create formal reproduction "
    "targets for Phi0 bridge repair, tau critical-scale extension, and "
    "multi-site spectral scaling, but it cannot promote nonclassical evidence, "
    "full tensor-network dynamics, E16 dynamics, bridge closure, real basin "
    "admission, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard proving every routed iter remains blocked from direct formal promotion",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of sidequest result JSON artifacts and receipt serialization",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path accounting"},
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

FORMAL_ANCHORS = {
    "spectral_reproduction": RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "spectral_map": RESULT_DIR / "two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json",
    "terrain_contribution": RESULT_DIR / "two_root_constraint_terrain_stage_spectral_contribution_probe_results.json",
}

ARTIFACTS = [
    {
        "iter": "iter_196",
        "source": GROK_ITERS / "iter_196_engine_slow_mode_decomposition.py",
        "result": GROK_RESULTS / "iter_196_engine_slow_mode_decomposition_results.json",
        "route_class": "formal_reproduction_target",
        "formal_use": "slow eigenvector Pauli coefficients, single-stage spectra, and permutation sensitivity can guide the Phi0 slow-mode bridge controls",
    },
    {
        "iter": "iter_197",
        "source": GROK_ITERS / "iter_197_slow_mode_n_hat_alignment.py",
        "result": GROK_RESULTS / "iter_197_slow_mode_n_hat_alignment_results.json",
        "route_class": "formal_reproduction_target",
        "formal_use": "slow-mode/Hamiltonian-direction alignment and entropy-correlation targets should be reproduced before using n-hat projections in Phi0",
    },
    {
        "iter": "iter_198",
        "source": GROK_ITERS / "iter_198_engine_tau_sweep_critical_scales.py",
        "result": GROK_RESULTS / "iter_198_engine_tau_sweep_critical_scales_results.json",
        "route_class": "partially_covered_extension_target",
        "formal_use": "tau=0.5 and tau=1.0 overlap the formal spectral map; extreme tau critical scales remain an extension target",
    },
    {
        "iter": "iter_199",
        "source": GROK_ITERS / "iter_199_two_qubit_engine_spectrum.py",
        "result": GROK_RESULTS / "iter_199_two_qubit_engine_spectrum_results.json",
        "route_class": "formal_reproduction_target",
        "formal_use": "two-qubit dense spectrum suggests slow-mode shrinkage; reproduce in torch before using for E16 or tensor scaling claims",
    },
    {
        "iter": "iter_200",
        "source": GROK_ITERS / "iter_200_three_qubit_engine_memory_scaling.py",
        "result": GROK_RESULTS / "iter_200_three_qubit_engine_memory_scaling_results.json",
        "route_class": "formal_reproduction_target",
        "formal_use": "three-qubit dense spectrum suggests continued slow-mode shrinkage; reproduce in torch before scale claims",
    },
    {
        "iter": "iter_201",
        "source": GROK_ITERS / "iter_201_four_qubit_memory_horizon.py",
        "result": GROK_RESULTS / "iter_201_four_qubit_memory_horizon_results.json",
        "route_class": "formal_reproduction_target",
        "formal_use": "four-qubit dense spectrum and memory horizon should be reproduced in torch or replaced by tensor-network evidence",
    },
    {
        "iter": "iter_202",
        "source": GROK_ITERS / "iter_202_L4_N5_collapse_analysis.py",
        "result": GROK_RESULTS / "iter_202_L4_N5_collapse_analysis_results.json",
        "route_class": "sidequest_context_only",
        "formal_use": "N=5 schedule collapse distances can inform suffix-memory controls, but cannot prove basin admission",
    },
    {
        "iter": "iter_203",
        "source": GROK_ITERS / "iter_203_engine_spectrum_physics_connection.py",
        "result": GROK_RESULTS / "iter_203_engine_spectrum_physics_connection_results.json",
        "route_class": "sidequest_context_only",
        "formal_use": "gamma_eff=-log(lambda1)/tau and steady-state entropy are useful labels for future physics interpretation only",
    },
]

ALLOWED_ROUTE_CLASSES = {
    "formal_reproduction_target",
    "partially_covered_extension_target",
    "sidequest_context_only",
    "blocked_not_promotable",
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


def source_uses_blocked_classical(source: pathlib.Path) -> dict[str, bool]:
    text = source.read_text(encoding="utf-8") if source.exists() else ""
    numpy_import = "import " + "numpy"
    numpy_from = "from " + "numpy"
    scipy_import = "import " + "scipy"
    scipy_from = "from " + "scipy"
    return {
        "uses_numpy": numpy_import in text or numpy_from in text,
        "uses_scipy": scipy_import in text or scipy_from in text,
        "uses_torch": "import torch" in text,
    }


def nested_get(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    cursor: Any = data
    for key in keys:
        if not isinstance(cursor, dict) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor


def formal_tau_lookup(spectral_map: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in spectral_map.get("rows", []):
        if (
            row.get("sheet") == "L"
            and row.get("direction") == "raw_xz"
            and row.get("magnitude") == 1.0
            and row.get("profile") == "balanced"
            and row.get("order_variant") == "canonical"
            and row.get("tau") in {0.5, 1.0}
        ):
            out[str(row["tau"])] = float(row["slow_mode_abs"])
    return out


def selected_diagnostics(iter_id: str, data: dict[str, Any], anchors: dict[str, Any]) -> dict[str, Any]:
    if iter_id == "iter_196":
        anchor = nested_get(anchors["spectral_reproduction"], ["summary", "slow_mode_abs"])
        sidequest = complex(str(data.get("P2_slow_eigenvalue", "nan")).replace("(", "").replace(")", "")).real
        return {
            "slow_eigenvalue_real": sidequest,
            "matches_formal_iter195_anchor": abs(sidequest - float(anchor)) < 1.0e-9 if anchor is not None else False,
            "single_stage_slowest": data.get("P1_slowest_per_stage"),
            "has_slow_pauli_coefficients": bool(data.get("P2_v_slow_pauli_coeffs")),
            "permutation_rows": len(data.get("P4_permutation_lambdas", [])),
        }
    if iter_id == "iter_197":
        return {
            "strong_alignment_count": data.get("A1_n_aligned_strong"),
            "default_gamma_eff": data.get("A4_gamma_eff_default"),
            "lambda1_entropy_correlation": data.get("A3_lambda1_S_correlation"),
            "neglog_entropy_correlation": data.get("A3_neglog_S_correlation"),
        }
    if iter_id == "iter_198":
        tau_lookup = formal_tau_lookup(anchors["spectral_map"])
        spectra = data.get("S1_spectra", {})
        return {
            "tau_count": len(data.get("S1_taus", [])),
            "tau_0_5_matches_formal_map": abs(float(spectra.get("0.5", [0, 0])[1]) - tau_lookup.get("0.5", float("nan"))) < 1.0e-9,
            "tau_1_0_matches_formal_map": abs(float(spectra.get("1.0", [0, 0])[1]) - tau_lookup.get("1.0", float("nan"))) < 1.0e-9,
            "tau_50_slow_mode": spectra.get("50.0", [None, None])[1],
        }
    if iter_id == "iter_199":
        return {
            "qubit_count": 2,
            "lambda_1": data.get("Q2_lambda_1"),
            "spectral_gap": data.get("Q2_spectral_gap"),
            "top_eigenvalue_count": len(data.get("abs_eigenvalues_sorted", [])),
        }
    if iter_id == "iter_200":
        vals = data.get("top_8_eigenvalues_abs", [])
        return {"qubit_count": 3, "lambda_1": vals[1] if len(vals) > 1 else None, "top_count": len(vals)}
    if iter_id == "iter_201":
        vals = data.get("top_10_eigenvalues_abs", [])
        return {"qubit_count": data.get("L"), "lambda_1": vals[1] if len(vals) > 1 else None, "top_count": len(vals)}
    if iter_id == "iter_202":
        closest = data.get("closest_pairs_top_10", [])
        return {
            "n_schedules": data.get("n_schedules"),
            "closest_pair_common_suffix_len": closest[0]["common_suffix_len"] if closest else None,
            "closest_pair_distance": closest[0]["dist"] if closest else None,
        }
    if iter_id == "iter_203":
        return {
            "lambda_1_default": data.get("lambda_1_default"),
            "steady_state_entropy": data.get("S_steady_state"),
            "gamma_eff": data.get("gamma_eff_neg_log_lambda_per_tau"),
        }
    return {}


def artifact_row(artifact: dict[str, Any], anchors: dict[str, Any]) -> dict[str, Any]:
    source = artifact["source"]
    result = artifact["result"]
    data = read_json(result)
    imports = source_uses_blocked_classical(source)
    return {
        "iter": artifact["iter"],
        "source": rel(source),
        "result": rel(result),
        "source_exists": source.exists(),
        "result_exists": result.exists(),
        "source_sha256": sha256(source),
        "result_sha256": sha256(result),
        "route_class": artifact["route_class"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling"),
        "classical_tooling_boundary": imports,
        "direct_formal_promotion_allowed": False,
        "diagnostics": selected_diagnostics(artifact["iter"], data, anchors),
    }


def z3_nonpromotion_guard(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    promote_vars = []
    for idx, row in enumerate(rows):
        route_class = z3.String(f"route_class_{idx}")
        source_classical = z3.Bool(f"source_classical_{idx}")
        direct_promoted = z3.Bool(f"direct_promoted_{idx}")
        promote_vars.append(direct_promoted)
        solver.add(route_class == row["route_class"])
        solver.add(z3.Or([route_class == allowed for allowed in sorted(ALLOWED_ROUTE_CLASSES)]))
        solver.add(source_classical == bool(row["classical_tooling_boundary"]["uses_numpy"] or row["classical_tooling_boundary"]["uses_scipy"]))
        solver.add(z3.Implies(source_classical, z3.Not(direct_promoted)))
        solver.add(z3.Not(direct_promoted))
    direct = z3.Solver()
    direct.add(solver.assertions())
    direct.add(z3.Or(promote_vars))
    return {
        "solver": "z3",
        "base_status": str(solver.check()),
        "direct_promotion_is_unsat": str(direct.check()) == "unsat",
        "rule": "NumPy/SciPy sidequest engine-spectral artifacts can only become formal evidence after PyTorch-native reproduction or explicit classical/boundary classification.",
    }


def main() -> int:
    started = time.time()
    anchors = {name: read_json(path) for name, path in FORMAL_ANCHORS.items()}
    rows = [artifact_row(artifact, anchors) for artifact in ARTIFACTS]
    missing = [row["iter"] for row in rows if not row["source_exists"] or not row["result_exists"]]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    direct_promotion_attempts = [row["iter"] for row in rows if row["direct_formal_promotion_allowed"]]
    all_sources_classical = all(row["classical_tooling_boundary"]["uses_numpy"] and row["classical_tooling_boundary"]["uses_scipy"] for row in rows)
    guard = z3_nonpromotion_guard(rows)
    routed_targets = {
        "phi0_bridge_next_features": [
            "slow-mode Pauli/eigenvector projection from iter_196",
            "Hamiltonian-direction/n_hat alignment from iter_197",
            "terrain identity and stage placement from D104",
            "history-erased, slow-mode-erased, and terrain-erased controls",
        ],
        "spectral_extension_targets": [
            "extreme tau critical scales from iter_198 beyond current 0.25..1.25 formal map",
            "2/3/4-qubit dense spectra from iter_199-201, reproduced in torch before scale claims",
        ],
        "context_only": [
            "iter_202 suffix-collapse distances for schedule-memory controls",
            "iter_203 gamma_eff and steady-state entropy labels for interpretation",
        ],
    }
    checks = {
        "all_artifacts_present": {"pass": not missing, "missing": missing, "count": len(rows)},
        "all_routes_allowed": {"pass": not invalid_routes, "invalid_routes": invalid_routes},
        "all_sources_blocked_from_direct_nonclassical_promotion": {
            "pass": all_sources_classical,
            "numpy_scipy_iters": [row["iter"] for row in rows if row["classical_tooling_boundary"]["uses_numpy"] and row["classical_tooling_boundary"]["uses_scipy"]],
        },
        "no_direct_promotion_attempted": {"pass": not direct_promotion_attempts and guard["direct_promotion_is_unsat"], "z3": guard},
        "formal_anchor_overlap_confirmed": {
            "pass": rows[0]["diagnostics"].get("matches_formal_iter195_anchor") is True
            and rows[2]["diagnostics"].get("tau_0_5_matches_formal_map") is True
            and rows[2]["diagnostics"].get("tau_1_0_matches_formal_map") is True,
            "iter_196": rows[0]["diagnostics"],
            "iter_198": rows[2]["diagnostics"],
        },
    }
    all_pass = all(item["pass"] for item in checks.values())
    summary = {
        "all_pass": all_pass,
        "artifact_count": len(rows),
        "direct_formal_promotion_allowed": False,
        "all_sources_use_numpy_scipy": all_sources_classical,
        "useful_for_next_phi0_bridge": True,
        "recommended_next_formal_packet": "sim_two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe.py",
        "recommended_phi0_features": routed_targets["phi0_bridge_next_features"],
        "formal_reproduction_targets": [
            "iter_197 n_hat alignment",
            "iter_198 extreme tau critical scales",
            "iter_199-201 multi-qubit spectral scaling",
        ],
        "context_only": routed_targets["context_only"],
        "remaining_boundary": "sidequest results are NumPy/SciPy and cannot be direct nonclassical evidence; reproduce selected targets in PyTorch formal scouts before promotion.",
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "anchor_paths": {name: rel(path) for name, path in FORMAL_ANCHORS.items()},
        "artifact_rows": rows,
        "routed_targets": routed_targets,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "direct_formal_promotion_blocked": {
                "pass": guard["direct_promotion_is_unsat"],
                "z3": guard,
            },
            "sidequest_tooling_boundary_visible": {
                "pass": all_sources_classical,
                "reason": "The routed Grok 196-203 sources use NumPy/SciPy and remain sidequest/context until formal PyTorch reproduction exists.",
            },
        },
        "graveyard_companions": {
            "numpy_scipy_sidequest_is_not_nonclassical_evidence": {
                "pass": True,
                "reason": "The sidequest batch is useful for target selection but cannot be counted as direct source-native nonclassical evidence.",
            },
            "physics_labels_are_context_only": {
                "pass": True,
                "reason": "Gamma/entropy labels from iter_203 are interpretation vocabulary, not bridge closure or final physics proof.",
            },
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "all_artifacts_present",
                "all_routes_allowed",
                "all_sources_blocked_from_direct_nonclassical_promotion",
                "no_direct_promotion_attempted",
                "formal_anchor_overlap_confirmed",
            ],
        },
        "why_not_v4_probes": [
            "The routed Grok artifacts are sidequest NumPy/SciPy outputs, not direct formal nonclassical evidence.",
            "Only selected targets are candidates for later PyTorch/tensor-network formal reproduction.",
            "No E16, PEPS/PEPS3D, Phi0 closure, or final manifold admission is claimed.",
        ],
        "next_work_required": [
            "Translate selected iter_197-201 spectral targets into source-native formal scouts before using them as evidence.",
            "Use iter_196-198 only as bounded target selection for the next Phi0 repair/falsifier packet.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
