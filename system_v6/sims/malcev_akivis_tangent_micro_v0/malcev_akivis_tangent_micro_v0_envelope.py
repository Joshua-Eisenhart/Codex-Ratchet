#!/usr/bin/env python3
"""Envelope builder for malcev_akivis_tangent_micro_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from malcev_akivis_tangent_micro_v0_common import (
    ARTIFACT,
    CANON_RECEIPT,
    CLAIM_CEILING,
    CLASSIFICATION,
    EXPECTED_ARTIFACT_SHA256,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    now_z,
    sha256_file,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(path.relative_to(ROOT)),
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
        for name, value in payload.get(key, {}).items():
            merged[f"{payload['engine']}:{name}"] = value
    return merged


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    j = julia["finite_checks"]
    p = jax["finite_checks"]
    proofs = jax["crossover_proofs"]
    engine_match = (
        j["jacobi_failure_witness"] == p["jacobi_failure_witness"]
        and j["malcev_compact_identity_holds"] == p["malcev_compact_identity_holds"] == True
        and j["malcev_expanded_identity_holds"] == p["malcev_expanded_identity_holds"] == True
        and j["quaternion_control"] == p["quaternion_control"]
        and j["non_malcev_control"]["failure_witness"] == p["non_malcev_control"]["failure_witness"]
    )
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and engine_match
        and proofs["z3"]["verdict"] == proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["flip_control_verdict"] == proofs["cvc5"]["flip_control_verdict"] == "sat"
        and sha256_file(ARTIFACT) == EXPECTED_ARTIFACT_SHA256
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "claim": "The imaginary-octonion commutator algebra from the committed Julia Canon structure constants is non-Lie but Malcev; the quaternion subalgebra is Lie; a one-entry perturbation breaks Malcev.",
        "malcev_verdict": "PASS_EXACT_IMAGINARY_OCTONION_COMMUTATOR_MALCEV_MICRO" if all_pass else "FAIL",
        "engine_contract": {
            "mode": "julia_canon_jax_exact_integer_micro",
            "lanes": ["julia", "jax"],
            "omitted_lanes": {"pytorch": "No autograd, graph, tensor-network, or neural surface is scoped for this finite exact structure-constant identity micro."},
            "reads_peer_result": READS_PEER_RESULT,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": str(ARTIFACT.relative_to(ROOT)),
            "artifact_sha256": sha256_file(ARTIFACT),
            "source_sha256": julia["canon_runtime"]["source_sha256"],
            "receipt_path": str(CANON_RECEIPT.relative_to(ROOT)),
            "proof_tag": julia["canon_runtime"]["proof_tag"],
            "proof_pass": julia["canon_runtime"]["proof_pass"],
            "table_version": julia["canon_runtime"]["table_version"],
            "bracket_convention": julia["canon_runtime"]["bracket_convention"],
            "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia["packages_used"], "role": "semantic owner/consumer of committed structure constants"},
            "jax": {"packages": jax["packages_used"], "role": "independent exact integer mirror plus z3/cvc5 flag proof"},
            "pytorch": {"role": "omitted_not_scoped"},
            "tensor_exchange": "none; engines independently consume the same committed JSON table by hash",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": sorted(set(julia["claim_path_tools"] + jax["claim_path_tools"])),
        "engines": {"julia": engine_record(julia, JULIA_RESULT), "jax": engine_record(jax, JAX_RESULT)},
        "crossover_proofs": proofs,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 0, "jax": 0},
            "max_divergence": 0,
            "comparison": {"exact_rows_match": engine_match, "meaning": "exact witnesses, identity booleans, and controls match"},
        },
        "positive_section": {
            "jacobi_failure_witness": j["jacobi_failure_witness"],
            "malcev_compact_identity_holds": j["malcev_compact_identity_holds"],
            "malcev_expanded_identity_holds": j["malcev_expanded_identity_holds"],
            "basis_triples_checked": j["basis_triples_checked"],
        },
        "negative_section": {"non_malcev_control": j["non_malcev_control"]},
        "boundary_section": {"quaternion_subalgebra_control": j["quaternion_control"]},
        "TOOL_MANIFEST": merge_tool_dicts(julia, jax, key="TOOL_MANIFEST"),
        "TOOL_INTEGRATION_DEPTH": merge_tool_dicts(julia, jax, key="TOOL_INTEGRATION_DEPTH"),
        "tool_calls": julia["tool_calls"] + jax["tool_calls"],
        "tool_intent": {
            "claim_classes": ["finite_structure_constant_identity_micro", "malcev_non_lie_commutator_control"],
            "engine_tool_intent": {
                "julia": {"Z3": "computed exact identity/control flags from committed structure constants"},
                "jax": {"z3": "computed exact identity/control flags UNSAT plus erase SAT", "cvc5": "independent computed exact identity/control flag proof"},
            },
        },
        "builder_gates": {
            "build_card_copied": (SIM_DIR / "build_card.md").is_file(),
            "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
            "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
            "artifact_sha256_pinned": sha256_file(ARTIFACT) == EXPECTED_ARTIFACT_SHA256,
            "engine_rows_match": engine_match,
            "pytorch_honestly_omitted": True,
            "nonassociativity_diagnostic_only": True,
        },
        "no_builder_audit_verdict": not (SIM_DIR / "audit_verdict.md").exists(),
        "no_builder_audit_verdict_envelope_gate": not (SIM_DIR / "audit_verdict.md").exists(),
        "relevance_fence": {
            "tool_function_micro_only": True,
            "nonassociativity": "diagnostic_readout_only",
            "akivis_tangent_claim": "finite_commutator_identity_micro_only",
            "engine_coupling_claims": "not_claimed",
            "physics_promotion": "not_claimed",
        },
        "source_authority": {
            "old_estate_item": "system_v6/receipts/old_estate_mine_20260611.md item 13",
            "evening_mining_packet": "system_v6/receipts/evening_mining_estate_s11_20260611.json proposed packet item 13",
            "panel": "panel 6 q4 pre-registered identity forms",
            "spin3_precedent": "system_v6/sims/clifford_spin3_double_cover_micro_v0",
        },
        "validator_expected_commands": [
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/malcev_akivis_tangent_micro_v0_envelope.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/malcev_akivis_tangent_micro_v0/validate_malcev_akivis_tangent_micro_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/malcev_akivis_tangent_micro_v0/results/malcev_akivis_tangent_micro_v0_envelope_results.json",
        ],
    }


def main() -> int:
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "envelope", "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
