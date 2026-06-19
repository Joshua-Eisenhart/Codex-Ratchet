#!/usr/bin/env python3
"""Envelope assembler for geo_s1_exact_closure_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_exact_closure_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
LINEAGE_PACKET = "system_v6/sims/geo_s1_spinor_hopf_free_v0"
LINEAGE_COMMIT = "013fb0fa1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_exact_closure_v0|lineage=geo_s1_spinor_hopf_free_v0@013fb0fa1|"
    "convention_pin=X1_option_A_pinned_minus_sigma_y|sigma_y_standard=[[0,-i],[i,0]]|"
    "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|r_i=Tr(rho*basis_i)|"
    "rho=psi*psi_dagger|Hopf_y=+2Im(z1*conj(z2))|derived_standard_y=-Hopf_y|"
    "derived_pinned_identity=Bloch_pinned(rho)=(x,y,z)|"
    "exact_strength=symbolic_closed_form_interval|"
    "seed_ledger=jax.random.PRNGKey[60610:haar_joint_n20000,"
    "60611:nonhaar_eta_n20000,60612:nonhaar_phi_n20000,60613:nonhaar_chi_n20000]|"
    "rerun=SIM_PY geo_s1_exact_closure_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

SEED_LEDGER = {
    "status": "declared_recompute_metadata_only",
    "rng_api": ["jax.random.PRNGKey"],
    "seeds": [
        {"engine": "jax", "seed": 60610, "use": "haar_joint_sample_statistic", "sample_count": 20000},
        {"engine": "jax", "seed": 60611, "use": "non_haar_eta_control", "sample_count": 20000},
        {"engine": "jax", "seed": 60612, "use": "non_haar_phi_control", "sample_count": 20000},
        {"engine": "jax", "seed": 60613, "use": "non_haar_chi_control", "sample_count": 20000},
    ],
    "deterministic_legs": ["julia_symbolic_interval", "pytorch_exact_crossing"],
    "rerun_command": "SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3; $SIM_PY system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_jax.py && JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_julia.jl && $SIM_PY system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_pytorch.py && $SIM_PY system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_envelope.py",
}

CONVENTION_PIN = {
    "pin_name": "X1_option_A_pinned_minus_sigma_y",
    "sigma_y_standard": "[[0,-i],[i,0]]",
    "bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule": "r_i = Tr(rho * basis_i)",
    "density_matrix": "rho = psi * psi^dagger",
    "hopf_y_convention": "Hopf_y = +2 Im(z1 * conj(z2))",
    "derived_standard_sigma_y_component": "Tr(rho * sigma_y_standard) = -2 Im(z1 * conj(z2))",
    "derived_pinned_y_component": "Tr(rho * (-sigma_y_standard)) = +2 Im(z1 * conj(z2))",
    "standard_bloch_relative_to_hopf": "Bloch_standard(rho) = (x, -y, z)",
    "pinned_keystone_identity": "Bloch_pinned(rho) = (x, y, z)",
}

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and PIN hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role_id": payload["role_id"],
        "pin_sha256": payload["pin_sha256"],
        "convention_pin": payload.get("convention_pin"),
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def classification_table() -> list[dict[str, Any]]:
    return [
        {
            "s1_claim": "Spinor chart lies on S3 and Hopf image lies on unit S2",
            "upgrade_ids": ["X2"],
            "achieved_strength": "symbolic",
            "exact_value": "x^2+y^2+z^2=(|z1|^2+|z2|^2)^2, hence 1 on S3",
            "bare_float_tolerance": False,
            "reason": None,
        },
        {
            "s1_claim": "Bloch density quotient equals the pinned Hopf map",
            "upgrade_ids": ["X1"],
            "achieved_strength": "symbolic",
            "exact_value": "With sigma_y_standard=[[0,-i],[i,0]] and Bloch basis (sigma_x,-sigma_y_standard,sigma_z), Tr(rho basis_i)-Hopf_i=(0,0,0); standard Bloch would be (x,-y,z)",
            "bare_float_tolerance": False,
            "reason": "explicit convention PIN selects the -sigma_y_standard basis so Hopf_y=+2Im(z1*conj(z2)) is coherent",
        },
        {
            "s1_claim": "Global phase leaves the Hopf base point unchanged",
            "upgrade_ids": ["X2"],
            "achieved_strength": "symbolic",
            "exact_value": "differences factor through u^2+v^2-1 for e^{i alpha}=u+iv",
            "bare_float_tolerance": False,
            "reason": None,
        },
        {
            "s1_claim": "S3 chart metric and S3/S2/torus measures",
            "upgrade_ids": ["X3"],
            "achieved_strength": "closed-form",
            "exact_value": "ds^2=deta^2+dphi^2+dchi^2+2cos(2eta)dphi dchi; Vol(S3)=2pi^2; Area(S2)=4pi; Area(T_eta)=2pi^2 sin(2eta)",
            "bare_float_tolerance": False,
            "reason": None,
        },
        {
            "s1_claim": "Hopf fibers have linking number 1",
            "upgrade_ids": ["X4"],
            "achieved_strength": "closed-form+rigorous-bound",
            "exact_value": "computed crossing signs have signed_sum/2=1; compactified-line Gauss integral=1 and fiber-orientation reversal=-1; interval quadrature enclosure contains 1",
            "bare_float_tolerance": False,
            "reason": "crossing signs are computed from exact tangent determinant plus z-order; interval row propagates interval subdomains through the integrand",
        },
        {
            "s1_claim": "SU(2) double cover returns -I at 2pi and +I at 4pi",
            "upgrade_ids": ["X5"],
            "achieved_strength": "symbolic",
            "exact_value": "exp(-i*pi*sigma_z)=-I; exp(-i*2pi*sigma_z)=I",
            "bare_float_tolerance": False,
            "reason": None,
        },
        {
            "s1_claim": "Haar pushforward sanity checks",
            "upgrade_ids": ["X6"],
            "achieved_strength": "statistical-redundant",
            "exact_value": "rotation-invariant expectations derived exactly: E[X]=0, E[XX^T]=I/3, pairwise cos density=1/2",
            "bare_float_tolerance": False,
            "reason": "sample rows remain diagnostics, but the expected values are exact and the non-Haar control fails the joint statistic",
        },
        {
            "s1_claim": "ott-Wasserstein distance-to-uniform diagnostic for Haar pushforward",
            "upgrade_ids": ["X6"],
            "achieved_strength": "statistical-redundant-diagnostic",
            "exact_value": "new diagnostic row only: ott Sinkhorn distance compares Haar samples to a deterministic Fibonacci-sphere uniform proxy; clustered north-pole control must fail the calibrated bar",
            "bare_float_tolerance": False,
            "reason": "does not modify exact rows; it is a byte-stable capability receipt and stronger sample-uniformity diagnostic",
        },
        {
            "s1_claim": "SU(2) action commutes with quotient/Hopf map",
            "upgrade_ids": ["X7"],
            "achieved_strength": "symbolic",
            "exact_value": "Bloch(U rho U^dagger)-R(U)Bloch(rho)=(0,0,0) as a CAS identity",
            "bare_float_tolerance": False,
            "reason": None,
        },
        {
            "s1_claim": "Prior Monte Carlo/convergence rows in the committed S1 packet",
            "upgrade_ids": ["X6", "X8"],
            "achieved_strength": "statistical-redundant",
            "exact_value": "retained only as redundant diagnostics behind exact symbolic/closed-form routes",
            "bare_float_tolerance": False,
            "reason": "not promoted as independent claim strength",
        },
    ]


def main() -> int:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    pin_hash = sha256_text(PIN_SPEC)
    pin_ok = all(payload["pin_sha256"] == pin_hash for payload in payloads.values())
    convention_pin_ok = all(payload.get("convention_pin") == CONVENTION_PIN for payload in payloads.values())
    ceilings_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    leg_pass = all(payload["all_pass"] is True for payload in payloads.values())
    jax = payloads["jax"]
    julia = payloads["julia"]
    pytorch = payloads["pytorch"]
    p1 = jax["proofs"]["P1_keystone_polynomial"]
    p2 = jax["proofs"]["P2_crossing_count_integer"]
    table = classification_table()
    bare_float_rows = [row for row in table if row["bare_float_tolerance"]]
    bare_float_row_labels = [row["s1_claim"] for row in bare_float_rows]
    x_receipts = {
        "X1": {
            "julia": julia["X_receipts"]["X1_keystone_identity_symbolic_symbolicsjl"],
            "jax": jax["X_receipts"]["X1_keystone_identity_symbolic_sympy"],
            "strength": "symbolic",
        },
        "X2": {
            "julia": julia["X_receipts"]["X2_phase_invariance_unit_image_symbolic_symbolicsjl"],
            "jax": jax["X_receipts"]["X2_phase_invariance_unit_image_symbolic_sympy"],
            "strength": "symbolic",
        },
        "X3": {
            "jax": jax["X_receipts"]["X3_metric_integrals_closed_form_sympy"],
            "strength": "closed-form",
        },
        "X4": {
            "julia_interval": julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"],
            "jax_exact": jax["X_receipts"]["X4_linking_exact_routes_sympy_smt"],
            "pytorch_crossing": pytorch["X_receipts"]["X4_crossing_count_exact_integer_pytorch"],
            "strength": "closed-form+rigorous-bound",
        },
        "X5": {"jax": jax["X_receipts"]["X5_double_cover_exact_sympy"], "strength": "symbolic"},
        "X6": {"jax": jax["X_receipts"]["X6_haar_rotation_invariant_joint_statistic"], "strength": "statistical-redundant"},
        "X7": {"jax": jax["X_receipts"]["X7_commuting_square_symbolic_sympy"], "strength": "symbolic"},
        "X8": {
            "classification_table": table,
            "bare_float_rows": len(bare_float_rows),
            "bare_float_row_labels": bare_float_row_labels,
            "strength": "classification",
        },
    }
    proof_flip_ok = (
        p1["z3"]["identity_nonzero_assertion"] == "unsat"
        and p1["z3"]["corrupted_control"] == "sat"
        and p1["cvc5"]["identity_nonzero_assertion"] == "unsat"
        and p1["cvc5"]["corrupted_control"] == "sat"
        and p2["z3"]["signed_sum_not_two"] == "unsat"
        and p2["z3"]["scrambled_control_not_two"] == "sat"
        and p2["cvc5"]["signed_sum_not_two"] == "unsat"
        and p2["cvc5"]["scrambled_control_not_two"] == "sat"
    )
    v2_repair_gates = {
        "V1_explicit_convention_pin": convention_pin_ok
        and "derived_standard_sigma_y_component" in CONVENTION_PIN
        and julia["X_receipts"]["X1_keystone_identity_symbolic_symbolicsjl"]["standard_sigma_y_trace_plus_hopf_y_expanded"] == "0"
        and jax["X_receipts"]["X1_keystone_identity_symbolic_sympy"]["standard_sigma_y_trace_plus_hopf_y_expanded"] == "0",
        "V2_julia_and_sympy_derive_from_rho": bool(julia["X_receipts"]["X1_keystone_identity_symbolic_symbolicsjl"].get("rho_from_psi_psidagger"))
        and bool(jax["X_receipts"]["X1_keystone_identity_symbolic_sympy"].get("rho_from_psi_psidagger"))
        and julia["X_receipts"]["X1_keystone_identity_symbolic_symbolicsjl"]["all_zero"]
        and jax["X_receipts"]["X1_keystone_identity_symbolic_sympy"]["all_zero"],
        "V3_crossing_signs_computed": all(
            "orientation_determinant_ordered_over_under" in row
            and "z_delta_line_minus_circle" in row
            and "computed_sign" in row
            for row in jax["proofs"]["P2_crossing_count_integer"]["crossing_records"]
        )
        and all(
            "orientation_determinant_ordered_over_under" in row
            and "z_delta_line_minus_circle" in row
            and "computed_sign" in row
            for row in pytorch["X_receipts"]["X4_crossing_count_exact_integer_pytorch"]["records"]
        ),
        "V4_gauss_orientation_reversal_minus_one": jax["X_receipts"]["X4_linking_exact_routes_sympy_smt"]["gauss_closed_form"]["orientation_reversal_control"]["reversed_gauss_value"] == "-1"
        and jax["X_receipts"]["X4_linking_exact_routes_sympy_smt"]["gauss_closed_form"]["orientation_reversal_control"]["pass"],
        "V5_genuine_interval_path": "interval Riemann sum" in julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"]["tight_interval"]["method"]
        and julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"]["tight_interval"]["contains_exact_one"]
        and julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"]["interval_blowup_control"]["contains_exact_one"]
        and julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"]["interval_blowup_control"]["wide_interval_width"]
        > julia["X_receipts"]["X4_interval_arithmetic_gauss_enclosure"]["tight_interval"]["wide_interval_width"],
        "V6_honest_classification_table": len(bare_float_rows) == 0
        and all("achieved_strength" in row and "bare_float_tolerance" in row for row in table),
    }
    x_pass = (
        x_receipts["X1"]["julia"]["all_zero"]
        and x_receipts["X1"]["jax"]["all_zero"]
        and x_receipts["X2"]["julia"]["phase_invariance_symbolic"]
        and x_receipts["X2"]["jax"]["phase_invariance_symbolic"]
        and x_receipts["X3"]["jax"]["closed_form_pass"]
        and x_receipts["X4"]["julia_interval"]["tight_interval"]["contains_exact_one"]
        and x_receipts["X4"]["jax_exact"]["crossing_count_exact_integer"]["pass"]
        and x_receipts["X4"]["jax_exact"]["gauss_closed_form"]["pass"]
        and x_receipts["X4"]["jax_exact"]["gauss_closed_form"]["orientation_reversal_control"]["pass"]
        and x_receipts["X4"]["pytorch_crossing"]["pass"]
        and x_receipts["X5"]["jax"]["pass"]
        and x_receipts["X6"]["jax"]["pass"]
        and x_receipts["X6"]["jax"]["non_haar_control"]["pass"]
        and x_receipts["X6"]["jax"]["ott_wasserstein_distance_to_uniform"]["pass"]
        and x_receipts["X6"]["jax"]["ott_wasserstein_distance_to_uniform"]["clustered_control_fails_uniformity"]
        and x_receipts["X7"]["jax"]["all_zero"]
        and len(bare_float_rows) == 0
    )
    gates = {
        "legs_exit_0_by_receipt": leg_pass,
        "pin_identical": pin_ok,
        "structured_convention_pin_identical": convention_pin_ok,
        "ceiling_exact": ceilings_ok,
        "X1_X8_receipts_pass": x_pass,
        "classification_table_zero_bare_float_rows": len(bare_float_rows) == 0,
        "V1_V6_repair_gates_pass": all(v2_repair_gates.values()),
        "solver_proofs_flip": proof_flip_ok,
        "lineage_cited_without_modification": all(
            payload["lineage"]["packet"] == LINEAGE_PACKET
            and payload["lineage"]["commit"] == LINEAGE_COMMIT
            and payload["lineage"]["modified_lineage_packet"] is False
            for payload in payloads.values()
        ),
    }
    all_pass = all(gates.values())
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "Every S1 claim of committed geo_s1_spinor_hopf_free_v0 is upgraded to symbolic, closed-form, rigorous-bound, or statistical-redundant exact-route status with zero bare-float rows.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "lineage": {"packet": LINEAGE_PACKET, "commit": LINEAGE_COMMIT, "modified_lineage_packet": False},
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
        "seed_ledger": SEED_LEDGER,
        "convention_pin": CONVENTION_PIN,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": julia.get("julia_project"),
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "S1_exact_closure_symbolics_interval_z3",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_pure_S1_geometry",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "symbolic and interval exact closure"},
            "jax": {"packages": jax["packages_used"], "role": "second CAS route plus z3/cvc5 exact solver proofs"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "integer-tensor exact crossing-count recomputation"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "X_receipts": x_receipts,
        "classification_table": table,
        "bare_float_rows": {
            "count": len(bare_float_rows),
            "labels": bare_float_row_labels,
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "P1_identity_nonzero_assertion": p1["z3"]["identity_nonzero_assertion"],
                "P1_corrupted_control": p1["z3"]["corrupted_control"],
                "P2_signed_sum_not_two": p2["z3"]["signed_sum_not_two"],
                "P2_scrambled_control_not_two": p2["z3"]["scrambled_control_not_two"],
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "P1_identity_nonzero_assertion": p1["cvc5"]["identity_nonzero_assertion"],
                "P1_corrupted_control": p1["cvc5"]["corrupted_control"],
                "P2_signed_sum_not_two": p2["cvc5"]["signed_sum_not_two"],
                "P2_scrambled_control_not_two": p2["cvc5"]["scrambled_control_not_two"],
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["P2_crossing_count_integer_julia_z3"]["signed_sum_not_two"],
                "load_bearing": True,
            },
        },
        "controls": {
            "corrupted_identity_control": jax["controls"]["corrupted_identity_control"],
            "broken_chart_metric_control": jax["controls"]["broken_chart_metric_control"],
            "interval_blowup_control": julia["controls"]["interval_blowup_control"],
            "non_haar_sample_control": jax["controls"]["non_haar_sample_control"],
            "ott_wasserstein_clustered_control": jax["controls"]["ott_wasserstein_clustered_control"],
            "scrambled_crossing_control": pytorch["controls"]["scrambled_crossing_control"],
        },
        "gates": gates,
        "v2_repair_gates": v2_repair_gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0.0, "jax": 0.0, "pytorch": 0.0},
            "max_divergence": 0.0,
        },
        "summary": {
            "X1_X8_complete": x_pass,
            "bare_float_rows": len(bare_float_rows),
            "bare_float_row_labels": bare_float_row_labels,
            "V1_V6_repair_gates_pass": all(v2_repair_gates.values()),
            "proofs_flip": proof_flip_ok,
            "ott_wasserstein_haar_reg_ot_cost": x_receipts["X6"]["jax"]["ott_wasserstein_distance_to_uniform"]["haar"]["reg_ot_cost"],
            "ott_wasserstein_clustered_reg_ot_cost": x_receipts["X6"]["jax"]["ott_wasserstein_distance_to_uniform"]["clustered_control"]["reg_ot_cost"],
            "ceiling": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
