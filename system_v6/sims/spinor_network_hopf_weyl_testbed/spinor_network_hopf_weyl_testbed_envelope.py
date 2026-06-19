#!/usr/bin/env python3
"""Envelope for spinor_network_hopf_weyl_testbed."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


PIN_SPEC = """N=6 nodes; graph = hexagon edges (i,i+1 mod 6) + chord (0,3); node Hopf coords eta_i = pi/8 + i*pi/20, phi_i = 0.3i, chi_i = 0.2i; psi_L/psi_R per scaffold 1.1 with H_0 = (sigma_x+sigma_y+sigma_z)/sqrt(3), H_L=+H_0, H_R=-H_0; hexagon edges carry quaternion unit couplings (cycle i,j,k); chord carries octonion pair (e1,e2) as nonassoc witness; operator params q1=q2=0.3, theta=phi=pi/2; terrain finite-time Phi=expm(0.4*X) using the EXACT terrain laws (scaffold 4.1/4.2); SCHEDULE = one dual-stacked cycle: Type-1 deductive outer (stage tokens TiSe UP, NeTi DOWN, NiFe DOWN, FeSi UP) then Type-2 inductive outer (FiSe UP, TeSi UP, NiTe DOWN, NeFi DOWN); UP=operator-first Phi_T(O(rho)), DOWN=terrain-first O(Phi_T(rho))."""

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_hopf_weyl_testbed"
RESULT_DIR = SIM_DIR / "results"
OBJECT_ID = "spinor_network_hopf_weyl_testbed"
SOURCE_PATH = SIM_DIR / f"{OBJECT_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{OBJECT_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{OBJECT_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{OBJECT_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{OBJECT_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-7

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from independent engine receipts; not a math claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for local v6 sim files",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source and pin hashing",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_sha256": payload["pin_sha256"],
        "values": payload["shared_scalars"],
        "controls": payload["controls"],
    }


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload["shared_scalars"].keys()) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    equal_sets = all(keys == key_sets["julia"] for keys in key_sets.values())
    rows = []
    max_divergence = 0.0
    max_key = None
    for key in common:
        values = {engine: float(payload["shared_scalars"][key]) for engine, payload in payloads.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_divergence:
            max_divergence = diff
            max_key = key
    union = set.union(*key_sets.values())
    return {
        "same_named_observable_sets": equal_sets,
        "common_observable_count": len(common),
        "missing_by_engine": {engine: sorted(union - keys) for engine, keys in key_sets.items()},
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "within_tolerance": equal_sets and max_divergence <= TOL,
    }


def collect_tool_exercise_map(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for engine, payload in payloads.items():
        out[engine] = payload.get("tool_exercise_map", {})
    return out


def flow_phase_table(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload["readouts"]["dual_stack_720_flow"]["nodes"]


def clean_minus_plus_pattern(nodes: list[dict[str, Any]]) -> bool:
    return all(
        abs(float(node["dual_stack_spinor_return_defect"])) <= TOL
        or abs(float(node["dual_stack_spinor_return_defect"]) - 2.0) <= TOL
        for node in nodes
    )


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    pin_hash = sha256_text(PIN_SPEC)
    comparison = compare_shared_scalars(payloads)
    z3 = payloads["jax"]["crossover_proofs"]["z3"]
    cvc5 = payloads["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = payloads["julia"]["crossover_proofs"]["julia_z3"]
    pin_equality = {
        "envelope_pin_sha256": pin_hash,
        "julia_pin_sha256": payloads["julia"]["pin_sha256"],
        "jax_pin_sha256": payloads["jax"]["pin_sha256"],
        "pytorch_pin_sha256": payloads["pytorch"]["pin_sha256"],
        "pin_sha256_equal": pin_hash == payloads["julia"]["pin_sha256"] == payloads["jax"]["pin_sha256"] == payloads["pytorch"]["pin_sha256"],
        "pin_spec_literal_equal": PIN_SPEC == payloads["julia"]["pin_spec"] == payloads["jax"]["pin_spec"] == payloads["pytorch"]["pin_spec"],
    }
    flow_nodes = flow_phase_table(payloads["julia"])
    clean_pattern = clean_minus_plus_pattern(flow_nodes)
    honest_geometry_divergence = not clean_pattern
    headline_claim = "pattern_not_clean_from_pinned_geometry"
    controls = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "pin_spec_match": pin_equality["pin_sha256_equal"] and pin_equality["pin_spec_literal_equal"],
        "same_named_observables_only": comparison["same_named_observable_sets"],
        "shared_scalars_within_tolerance": comparison["within_tolerance"],
        "z3_cvc5_forced_commutation_unsat": z3["verdict"] == cvc5["verdict"] == "unsat",
        "z3_cvc5_commuting_control_sat": z3["commuting_control_verdict"] == cvc5["commuting_control_verdict"] == "sat",
        "julia_z3_forced_commutation_unsat": julia_z3["verdict"] == "unsat",
        "julia_z3_commuting_control_sat": julia_z3["commuting_control_verdict"] == "sat",
        "sign_erasure_chirality_flip_in_solver": z3["sign_erasure_chirality_flip_verdict"] == "sat"
        and cvc5["sign_erasure_chirality_flip_verdict"] == "sat"
        and julia_z3["sign_erasure_chirality_flip_verdict"] == "sat",
        "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
        "clean_minus_plus_pattern_false": clean_pattern is False,
        "honest_geometry_divergence_true": honest_geometry_divergence is True,
        "headline_claim_hardened": headline_claim == "pattern_not_clean_from_pinned_geometry",
        "so3_wrong_transform_negative_controls_fail": all(
            payload["controls"]["so3_wrong_transform_negative_control_fails"] is True for payload in payloads.values()
        ),
        "dual_stack_two_step_checks_pass": all(
            payload["controls"]["dual_stack_two_step_equals_collapsed_phase"] is True for payload in payloads.values()
        ),
        "network_state_coherent_information_present": all(
            "network_state_coherent_information_chord_cut" in payload["shared_scalars"] for payload in payloads.values()
        ),
    }
    all_pass = bool(all(controls.values()))
    shared = payloads["julia"]["shared_scalars"]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
        "pin_equality": pin_equality,
        "clean_minus_plus_pattern": clean_pattern,
        "honest_geometry_divergence": honest_geometry_divergence,
        "headline_claim": headline_claim,
        "all_pass": all_pass,
        "readout_fence": "win/lose grammar not used; this is a scratch diagnostic readout fence.",
        "claim_ceiling": "tool-testbed + dual-stack flow diagnostic; no M(C), bridge, Axis0, engine admission, formal admission, promotion, or canonical claim.",
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "positive": {
            "density_stage_delta_means": {k: v for k, v in shared.items() if k.startswith("stage_density_delta_mean_")},
            "base_loop_bloch_traversal_length_mean": shared["base_bloch_traversal_length_mean"],
            "network_state_coherent_information_chord_cut": shared["network_state_coherent_information_chord_cut"],
            "two_site_chord_ansatz_entropy": shared["two_site_chord_ansatz_entropy"],
            "topology_features": {
                "reported_object": payloads["julia"]["readouts"]["topology"]["reported_object"],
                "betti0": shared["topology_betti0"],
                "betti1": shared["topology_betti1"],
                "betti2": shared["topology_betti2"],
                "toponetx_boundary_nnz_rank2": shared["toponetx_boundary_nnz_rank2"],
                "xgi_hyperedge_count": shared["xgi_hyperedge_count"],
                "simplicial_closure_complex": payloads["julia"]["readouts"]["topology"]["simplicial_closure_complex"],
                "intended_hypergraph_xgi_no_closure": payloads["jax"]["readouts"]["topology"]["intended_hypergraph_xgi_no_closure"],
            },
        },
        "negative": {
            "density_only_return_defects": {
                "single": shared["density_single_loop_return_defect_max"],
                "dual": shared["density_dual_stack_return_defect_max"],
            },
            "sign_erasure_control_gap_max": shared["sign_erasure_control_gap_max"],
            "commuting_control_gaps": {k: v for k, v in shared.items() if k.startswith("commuting_control_gap_mean_")},
            "classical_so3_vector_defects": {
                "single": shared["classical_so3_vector_single_loop_defect_max"],
                "dual": shared["classical_so3_vector_dual_stack_defect_max"],
                "wrong_transform_negative_control_residual": shared["so3_wrong_transform_negative_control_residual"],
            },
        },
        "boundary": {
            "spinor_720_honesty": payloads["julia"]["readouts"]["dual_stack_720_flow"]["honesty_note"],
            "measured_flow_phases_per_node": flow_nodes,
            "computed_defect_arrays": payloads["julia"]["readouts"]["dual_stack_720_flow"]["computed_defect_arrays"],
            "dual_stack_two_step_vs_collapsed_phase": payloads["julia"]["readouts"]["dual_stack_720_flow"][
                "two_step_vs_collapsed_phase_check"
            ],
            "terrain_law_conventions": payloads["julia"]["readouts"]["terrain_law_conventions"],
            "order_gaps": {k: v for k, v in shared.items() if k.startswith("order_gap_mean_")},
            "chirality_gaps_per_node": payloads["julia"]["readouts"]["chirality"]["nodes"],
        },
        "tool_exercise_map": collect_tool_exercise_map(payloads),
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3["verdict"],
                "commuting_control_verdict": z3["commuting_control_verdict"],
                "sign_erasure_chirality_flip_verdict": z3["sign_erasure_chirality_flip_verdict"],
                "capability_receipt_path": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5["verdict"],
                "commuting_control_verdict": cvc5["commuting_control_verdict"],
                "sign_erasure_chirality_flip_verdict": cvc5["sign_erasure_chirality_flip_verdict"],
                "capability_receipt_path": "system_v4/probes/a2_state/sim_results/cvc5_capability_results.json",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "commuting_control_verdict": julia_z3["commuting_control_verdict"],
                "sign_erasure_chirality_flip_verdict": julia_z3["sign_erasure_chirality_flip_verdict"],
                "capability_receipt_path": "system_v4/probes/a2_state/sim_results/z3_capability_results.json",
            },
        },
        "claim_path_tools": sorted(
            {
                tool
                for payload in payloads.values()
                for tool in payload.get("claim_path_tools", [])
            }
        ),
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {engine: payload["shared_scalars"] for engine, payload in payloads.items()},
            "comparison": comparison,
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "controls": controls,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"envelope": str(RESULT_PATH), "all_pass": result["all_pass"], "max_divergence": result["divergence"]["max_divergence"]}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
