#!/usr/bin/env python3
"""Envelope builder for clifford_spin3_double_cover_micro_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "clifford_spin3_double_cover_micro_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
    }


def merge_tool_dicts(*payloads: dict[str, Any], key: str) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for payload in payloads:
        merged.update(payload.get(key, {}))
    return merged


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pi2_julia = julia["double_cover_rows"]["theta_pi_over_2_vs_theta_plus_2pi"]
    pi2_jax = jax["double_cover_rows"]["theta_pi_over_2_vs_theta_plus_2pi"]
    boundary_julia = julia["boundary_rows"]
    controls_julia = julia["controls"]
    controls_jax = jax["controls"]
    proofs = {
        "z3": jax["crossover_proofs"]["z3"],
        "cvc5": jax["crossover_proofs"]["cvc5"],
        "julia_z3": julia["crossover_proofs"]["julia_z3"],
    }
    engine_match = (
        pi2_julia["action_matrix_theta"] == pi2_jax["action_matrix_theta"]
        and pi2_julia["action_matrix_theta_plus_2pi"] == pi2_jax["action_matrix_theta_plus_2pi"]
        and boundary_julia == jax["boundary_rows"]
    )
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and engine_match
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == proofs["julia_z3"]["verdict"] == "unsat"
        and proofs["z3"]["flip_control_verdict"] == proofs["cvc5"]["flip_control_verdict"] == proofs["julia_z3"]["flip_control_verdict"] == "sat"
        and controls_julia["single_cover_matrix_cannot_distinguish_2pi"]["pass"] is True
        and controls_julia["non_unit_even_multivector_fails_rotor_predicate"]["pass"] is True
        and controls_julia["odd_grade_element_fails_rotor_predicate"]["pass"] is True
        and controls_jax["single_cover_matrix_cannot_distinguish_2pi"]["pass"] is True
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "tool_function_micro_only",
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "claim": "In fixed finite Cl(3,0), R(theta) and R(theta+2pi) differ by Spin(3) sign while inducing identical computed SO(3) vector sandwich action; theta=4pi closes exactly.",
        "double_cover_verdict": "PASS_EXACT_SPIN3_DOUBLE_COVER_MICRO" if all_pass else "FAIL",
        "engine_contract": {
            "mode": "julia_canon_jax_exact_symbolic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "controller_comparison"],
            "omitted_lanes": {"pytorch": "No graph/network/autograd/existing torch machinery is scoped for this finite Cl(3) exact double-cover micro; adding PyTorch would be decorative."},
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "julia_project": "system_v5/julia_carrier",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia["source_sha256"],
            "receipt_path": julia["result_path"],
            "proof_tag": "spin3_double_cover_exact_flags_z3",
            "proof_pass": proofs["julia_z3"]["verdict"] == "unsat",
            "table_version": "inline_Cl3_bitmask_geometric_product_v0",
            "bracket_convention": "Euclidean Cl(3,0), blade masks e1/e2/e3, B=e12, R=cos(theta/2)-sin(theta/2)B, action v -> Rv~R",
            "consumer_policy": "JAX recomputes exact symbolic rows independently; no peer result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "semantic owner with CliffordAlgebras fixed-object receipt and Julia Z3 proof"},
            "jax": {"packages": jax["packages_used"], "role": "independent exact symbolic mirror plus z3/cvc5 proof"},
            "pytorch": {"role": "omitted_not_scoped"},
            "tensor_exchange": "none; engines independently compute the same finite rows",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted(set(julia["claim_path_tools"] + jax["claim_path_tools"])),
        "engines": {"julia": engine_record(julia, JULIA_RESULT), "jax": engine_record(jax, JAX_RESULT)},
        "crossover_proofs": proofs,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0, "jax": 0},
            "max_divergence": 0,
            "comparison": {"exact_rows_match": engine_match, "meaning": "exact integer SO(3) matrices and boundary rows match; no numeric promotion metric"},
        },
        "positive_section": {
            "fixed_object": julia["fixed_dimension"],
            "double_cover_row": pi2_julia,
            "basis_expectation": "For B=e12 and R=(1-e12)/sqrt(2), e1->e2, e2->-e1, e3->e3.",
        },
        "negative_section": {
            "single_cover_control": controls_julia["single_cover_matrix_cannot_distinguish_2pi"],
            "non_rotor_controls": {
                "non_unit_even_multivector": controls_julia["non_unit_even_multivector_fails_rotor_predicate"],
                "odd_grade_pin_not_spin": controls_julia["odd_grade_element_fails_rotor_predicate"],
            },
            "smt_erased_sign_flip_controls": {"z3": proofs["z3"]["flip_control_verdict"], "cvc5": proofs["cvc5"]["flip_control_verdict"], "julia_z3": proofs["julia_z3"]["flip_control_verdict"]},
        },
        "boundary_section": boundary_julia,
        "pinned_angles": julia["pinned_angles"],
        "controls": {"julia": controls_julia, "jax": controls_jax},
        "TOOL_MANIFEST": merge_tool_dicts(julia, jax, key="TOOL_MANIFEST"),
        "TOOL_INTEGRATION_DEPTH": merge_tool_dicts(julia, jax, key="TOOL_INTEGRATION_DEPTH"),
        "tool_calls": julia["tool_calls"] + jax["tool_calls"],
        "tool_intent": {
            "claim_classes": ["finite_clifford_spin3_double_cover_micro", "smt_computed_sign_action_flags"],
            "engine_tool_intent": {
                "julia": {"CliffordAlgebras": "fixed Cl(3,0) package object receipt", "Z3": "computed sign/action/control flags UNSAT plus erased sign SAT"},
                "jax": {"sympy": "exact rational/surd rotor coefficients and symbolic products", "z3": "computed flag proof", "cvc5": "independent computed flag proof"},
            },
        },
        "TOOL_INTENT_MATRIX": {
            "CliffordAlgebras": "load-bearing for fixed finite Cl(3,0) object receipt",
            "sympy": "load-bearing exact symbolic mirror",
            "Z3/z3/cvc5": "load-bearing proof checks over computed flags",
            "jax/jax.numpy": "supportive mirror only",
        },
        "builder_gates": {
            "build_card_copied": (SIM_DIR / "build_card.md").is_file(),
            "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
            "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "pytorch_honestly_omitted": True,
            "engine_rows_match": engine_match,
            "no_engine_or_coupling_claim": True,
        },
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "no_builder_audit_verdict_envelope_gate": not (SIM_DIR / "audit_verdict.md").exists(),
        "relevance_fence": {
            "o6_720_coupling_candidate": "background_only_not_claimed",
            "engine_coupling_claims": "not_claimed",
            "lego_promotion": "not_claimed",
            "physics_promotion": "not_claimed",
        },
        "source_authority": {
            "old_estate_item": "system_v6/receipts/old_estate_mine_20260611.md item 12",
            "evening_mining_packet": "system_v6/receipts/evening_mining_estate_s11_20260611.json queue item 12",
            "legacy_probe": "system_v4/probes/sim_clifford_spinor_double_cover_micro.py",
        },
        "validator_expected_commands": [
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/clifford_spin3_double_cover_micro_v0/clifford_spin3_double_cover_micro_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/clifford_spin3_double_cover_micro_v0/clifford_spin3_double_cover_micro_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/clifford_spin3_double_cover_micro_v0/clifford_spin3_double_cover_micro_v0_envelope.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/clifford_spin3_double_cover_micro_v0/validate_clifford_spin3_double_cover_micro_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/clifford_spin3_double_cover_micro_v0/results/clifford_spin3_double_cover_micro_v0_envelope_results.json",
        ],
    }


def main() -> int:
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "envelope", "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
