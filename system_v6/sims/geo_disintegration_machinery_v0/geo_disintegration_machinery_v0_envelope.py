#!/usr/bin/env python3
"""Envelope assembler for geo_disintegration_machinery_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from geo_disintegration_machinery_v0_common import (
    CLASSIFICATION,
    CONVENTION_PIN,
    ENGINE_MODE,
    FORMAL_ADMISSION_ALLOWED,
    JULIA_PROJECT,
    LINEAGE_CITATIONS,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SEEDS,
    SIM_DIR,
    SIM_ID,
    file_sha256,
    rel,
    sha256_text,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_PATH = SIM_DIR / f"{SIM_ID}_exact_strength_validator.py"

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh Julia and JAX receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source, result, and PIN hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "source_hash_current": file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"],
        "result_path": rel(result_path),
        "result_sha256": file_sha256(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "TOOL_MANIFEST": payload["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload.get("tool_calls", []),
        "capability_receipts": payload.get("capability_receipts", {}),
    }


def collect(payloads: dict[str, dict[str, Any]], key: str) -> list[Any]:
    out: list[Any] = []
    for payload in payloads.values():
        value = payload.get(key, [])
        if isinstance(value, list):
            out.extend(value)
    return out


def collect_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    out: set[str] = set()
    for payload in payloads.values():
        out.update(str(item) for item in payload.get("claim_path_tools", []))
    return sorted(out)


def source_hashes_current(payloads: dict[str, dict[str, Any]]) -> bool:
    return all(file_sha256(ROOT / payload["source_path"]) == payload["source_sha256"] for payload in payloads.values())


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payloads = {"julia": load_json(JULIA_RESULT), "jax": load_json(JAX_RESULT)}
    julia = payloads["julia"]
    jax = payloads["jax"]
    pin_hashes = {payload["pin_sha256"] for payload in payloads.values()}
    jax_receipts = jax["receipts"]
    julia_receipts = julia["receipts"]
    z3_row = jax["crossover_proofs"]["z3"]
    cvc5_row = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    gates = {
        "engine_legs_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "ceilings_preserved": all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is PROMOTION_ALLOWED
            and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
            for payload in payloads.values()
        ),
        "no_peer_result_reads": all(payload["reads_peer_result"] is READS_PEER_RESULT for payload in payloads.values()),
        "identical_pin_sha256": len(pin_hashes) == 1 and next(iter(pin_hashes)) == sha256_text(PIN_SPEC),
        "source_sha256_current": source_hashes_current(payloads),
        "sympy_eta_marginal_area_law": jax_receipts["R1_eta_marginal_area_law"]["pass"] is True,
        "sympy_disintegration_property": jax_receipts["R2_symbolic_disintegration_recovery"]["defect"] == "0",
        "julia_symbolics_disintegration_property": julia_receipts["J1_symbolics_recovery_identity"]["defect"] == "0",
        "naive_conditioning_failure_computed": jax_receipts["C1_naive_singleton_conditioning_fails"]["denominator_mass"] == "0"
        and jax_receipts["C1_naive_singleton_conditioning_fails"]["naive_quotient"] == "nan",
        "positive_measure_band_agrees": jax_receipts["C2_positive_eta_band_agrees"]["pass"] is True,
        "wrong_flat_marginal_fails": jax_receipts["C3_wrong_flat_marginal_fails"]["computed_nonzero_defect"] != "0"
        and julia_receipts["J3_wrong_flat_marginal_defect"]["computed_nonzero_defect"] != "0",
        "null_set_scope_exhibited": jax_receipts["C4_null_set_disintegration_scope"]["global_integrated_defect"] == "0"
        and jax_receipts["C4_null_set_disintegration_scope"]["pointwise_conditional_difference_for_cos_phi"] == 1,
        "volume_anchor_matches_committed": jax["jax_diagnostics"]["s3_volume_exact"] == jax["jax_diagnostics"]["clifford_torus_area_target"]
        and jax["jax_diagnostics"]["abs_diff_vs_committed_geomstats_probe"] < 1.0e-9,
        "double_cover_conditionals_honored": all(
            row["double_cover_honored"] and row["physical_points"] * 2 == row["chart_points"]
            for row in jax["jax_diagnostics"]["finite_grid_double_cover_rows"]
        ),
        "z3_cvc5_finite_recovery": z3_row["verdict"] == cvc5_row["verdict"] == "unsat"
        and z3_row["erased_controls_flip"]
        and cvc5_row["erased_controls_flip"],
        "julia_z3_finite_recovery": julia_z3["verdict"] == "unsat" and julia_z3["erased_controls_flip"],
        "pytorch_omission_declared": "no graph/network/autograd claim path" in jax["summary"]["pytorch_omission"],
        "summary_boundary_present": "mode-4 cards may cite" in jax["summary"]["enables"]
        and "no ratchet sim is run" in jax["summary"]["does_not_enable"],
    }
    all_pass = all(gates.values())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Mode-4 prerequisite disintegration machinery for conditioning round S3 measure on measure-zero Hopf torus leaves T_eta.",
        "stage": "mode4_prerequisite",
        "mode": "RATCHETED_prerequisite_disintegration_rule",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "validator_path": rel(VALIDATOR_PATH),
        "seed": SEEDS,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "lineage_citations": LINEAGE_CITATIONS,
        "engine_contract": {
            "mode": ENGINE_MODE,
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "pytorch": {
                "scoped": False,
                "reason": "No graph/network/autograd claim path; PyTorch would be decorative for this measure-disintegration prerequisite.",
            },
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project", JULIA_PROJECT),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "geo_disintegration_machinery_v0_julia_symbolics_z3",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_measure_disintegration_over_Hopf_eta_foliation",
            "consumer_policy": "independent Julia Symbolics/Z3 and Python SymPy/z3/cvc5 recovery; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project", JULIA_PROJECT), "packages": julia["packages_used"], "role": "Symbolics/Z3 semantic owner"},
            "jax": {"packages": jax["packages_used"], "role": "SymPy exact derivation, JAX x64 diagnostics, z3/cvc5 finite proof"},
            "pytorch": {"packages": [], "role": "omitted_no_graph_network_autograd_claim_path"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
        },
        "receipts": {
            **jax_receipts,
            **julia_receipts,
        },
        "finite_discretization_recovery": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "julia_z3": julia_z3,
        },
        "crossover_proofs": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "julia_z3": julia_z3,
        },
        "controls": {
            "naive_singleton_conditioning": jax_receipts["C1_naive_singleton_conditioning_fails"],
            "positive_eta_band": jax_receipts["C2_positive_eta_band_agrees"],
            "wrong_flat_marginal": jax_receipts["C3_wrong_flat_marginal_fails"],
            "null_set_pathology": jax_receipts["C4_null_set_disintegration_scope"],
            "finite_erased_controls": {
                "z3_flat": z3_row["erased_flat_marginal_control_verdict"],
                "z3_double_cover": z3_row["erased_double_cover_control_verdict"],
                "cvc5_flat": cvc5_row["erased_flat_marginal_control_verdict"],
                "cvc5_double_cover": cvc5_row["erased_double_cover_control_verdict"],
                "julia_z3_flat": julia_z3["erased_flat_marginal_control_verdict"],
                "julia_z3_double_cover": julia_z3["erased_double_cover_control_verdict"],
            },
        },
        "jax_diagnostics": jax["jax_diagnostics"],
        "capability_receipts": {
            "julia": julia["capability_receipts"],
            "jax": jax["capability_receipts"],
        },
        "tool_calls": collect(payloads, "tool_calls"),
        "build_gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 0.0 if julia_receipts["J1_symbolics_recovery_identity"]["defect"] == "0" else 1.0,
                "jax": 0.0 if jax_receipts["R2_symbolic_disintegration_recovery"]["defect"] == "0" else 1.0,
            },
            "max_divergence": 0.0,
            "basis": "Julia Symbolics and Python SymPy independently return zero recovery defect; solver rows agree on finite recovery.",
        },
        "summary": {
            "enables": "mode-4 cards may now cite the disintegration rule for conditioning on fixed-eta Hopf torus leaves T_eta, despite mu(T_eta)=0",
            "does_not_enable": "no ratchet sim is run here; no manifold, axis, bridge, physics, or canonical admission claim is made",
            "anchor_values": {
                "eta_marginal_density": "sin(2*eta)",
                "torus_layer_area": "2*pi^2*sin(2*eta)",
                "s3_volume": "2*pi^2",
                "committed_geomstats_probe_value": jax["jax_diagnostics"]["committed_geomstats_probe_value"],
                "conditional_chart_density": "1/(4*pi^2)",
                "finite_grid_physical_points": "N^2/2",
            },
            "ceiling": CLASSIFICATION,
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_canon_plus_jax_diagnostic",
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
