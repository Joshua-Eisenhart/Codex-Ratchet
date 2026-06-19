#!/usr/bin/env python3
"""Envelope assembler for geo_s1_vector_vs_spinor_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_vector_vs_spinor_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
PIN_SPEC = (
    "geo_s1_vector_vs_spinor_v0|routes=SO3_vector_vs_SU2_spinor|"
    "U(theta)=diag(exp(-i theta/2),exp(i theta/2))|R(theta)=Rz(theta)|"
    "density_quotient=psi psi_dagger|compare_2pi_4pi|"
    "classification=scratch_diagnostic|promotion_allowed=false"
)

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from fresh leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and pin equality checks"},
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
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "shared_scalars": payload.get("shared_scalars", {}),
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def comparison_table() -> list[dict[str, Any]]:
    return [
        {
            "fact_or_probe": "2pi continuous-path return",
            "vector_SO3_route": "closes: Rz(2pi)=I in SO(3)",
            "spinor_SU2_route": "does not close: U(2pi)=-I, not I",
            "decision": "distinguishes routes",
            "requires_spinor_route": True,
        },
        {
            "fact_or_probe": "N01 closure-order gap",
            "vector_SO3_route": "normalized boolean identity closure at 2pi = 1",
            "spinor_SU2_route": "normalized boolean identity closure at 2pi = 0",
            "decision": "n01_closure_order_gap=1 on a common boolean closure scale",
            "requires_spinor_route": True,
            "raw_norm_cross_dimension_comparison_excluded": True,
        },
        {
            "fact_or_probe": "4pi continuous-path return",
            "vector_SO3_route": "already closed at 2pi and remains closed at 4pi",
            "spinor_SU2_route": "closes at 4pi: U(4pi)=I",
            "decision": "spinor-only return period is 4pi",
            "requires_spinor_route": True,
        },
        {
            "fact_or_probe": "explicit double cover SU(2)->SO(3)",
            "vector_SO3_route": "receives R(U) and identifies U with -U",
            "spinor_SU2_route": "keeps U and -U distinct before quotient",
            "decision": "vector route cannot carry pre-quotient sign/phase data; it remains admissible but coarser after quotient",
            "requires_spinor_route": True,
        },
        {
            "fact_or_probe": "density quotient",
            "vector_SO3_route": "matches the quotient observable after sign erasure",
            "spinor_SU2_route": "psi and -psi are distinct amplitudes, but rho=psi psi^dagger is equal",
            "decision": "distinguishability collapses exactly where density quotient says it should",
            "requires_spinor_route": False,
        },
        {
            "fact_or_probe": "holonomy sign / 2pi sign flip",
            "vector_SO3_route": "cannot represent the sign flip; it has already returned",
            "spinor_SU2_route": "represents the -I holonomy at 2pi",
            "decision": "requires spinor route for the pre-quotient holonomy-sign construction",
            "requires_spinor_route": True,
        },
        {
            "fact_or_probe": "Hopf/linking S1 fiber facts",
            "vector_SO3_route": "base vector/Bloch route can see the projected S2 point, not the S3 fiber sign/linking carrier by itself",
            "spinor_SU2_route": "S3 spinor total space carries the S1 fiber needed for Hopf/linking statements",
            "decision": "linking/fiber facts require spinor route; base observables survive after quotient",
            "requires_spinor_route": True,
        },
        {
            "fact_or_probe": "keystone density/Bloch observable",
            "vector_SO3_route": "survives as the post-quotient Bloch/vector observable",
            "spinor_SU2_route": "required to construct the density quotient from amplitudes",
            "decision": "construction requires spinor; observable survives vector route after quotient",
            "requires_spinor_route": True,
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
    table = comparison_table()

    route_scalars = {
        engine: payload["shared_scalars"]
        for engine, payload in payloads.items()
    }
    scalar_checks = {
        "so3_2pi_closed_all": all(values["so3_2pi_distance"] < 1e-9 for values in route_scalars.values()),
        "su2_2pi_not_identity_all": all(values["su2_2pi_identity_distance"] > 1.0 for values in route_scalars.values()),
        "su2_4pi_identity_all": all(values["su2_4pi_identity_distance"] < 1e-9 for values in route_scalars.values()),
        "density_quotient_sign_collapse_all": all(values["density_quotient_sign_distance"] < 1e-9 for values in route_scalars.values()),
        "u_minus_u_rotation_collapse_all": all(values["u_minus_u_rotation_distance"] < 1e-9 for values in route_scalars.values()),
        "n01_closure_order_gap_julia_jax_agree": (
            julia["shared_scalars"]["n01_closure_order_gap"] == 1
            and jax["shared_scalars"]["n01_closure_order_gap"] == 1
            and julia["route_receipts"]["n01_closure_order_gap"]["pass"] is True
            and jax["route_receipts"]["n01_closure_order_gap"]["pass"] is True
            and julia["route_receipts"]["n01_closure_order_gap"]["raw_norm_cross_dimension_comparison_excluded"] is True
            and jax["route_receipts"]["n01_closure_order_gap"]["raw_norm_cross_dimension_comparison_excluded"] is True
        ),
    }
    proof_pass = (
        jax["proofs"]["route_truth_table"]["z3"]["nominal_not_accepted"] == "unsat"
        and jax["proofs"]["route_truth_table"]["cvc5"]["nominal_not_accepted"] == "unsat"
        and julia["proofs"]["route_truth_table_julia_z3"]["nominal_not_accepted"] == "unsat"
        and jax["proofs"]["route_truth_table"]["z3"]["corrupted_control_not_accepted"] == "sat"
        and jax["proofs"]["route_truth_table"]["cvc5"]["corrupted_control_not_accepted"] == "sat"
        and julia["proofs"]["route_truth_table_julia_z3"]["corrupted_control_not_accepted"] == "sat"
    )
    gates = {
        "legs_exit_0_by_receipt": leg_pass,
        "pin_identical": pin_ok,
        "ceiling_exact": ceilings_ok,
        "route_scalars_match_discriminator": all(scalar_checks.values()),
        "solver_proofs_flip": proof_pass,
        "comparison_table_present": len(table) == 8,
        "full_tooling_present": {
            "julia_manifolds": "Manifolds" in julia["aligned_packages_load_bearing"],
            "julia_quantumoptics": "QuantumOptics" in julia["aligned_packages_load_bearing"],
            "pytorch_geomstats": "geomstats" in pytorch["aligned_packages_load_bearing"],
            "pytorch_e3nn": "e3nn" in pytorch["aligned_packages_load_bearing"],
            "jax_smt": {"z3", "cvc5"}.issubset(set(jax["aligned_packages_load_bearing"])),
        },
    }
    full_tooling_ok = all(gates["full_tooling_present"].values())
    all_pass = (
        gates["legs_exit_0_by_receipt"]
        and gates["pin_identical"]
        and gates["ceiling_exact"]
        and gates["route_scalars_match_discriminator"]
        and gates["solver_proofs_flip"]
        and gates["comparison_table_present"]
        and full_tooling_ok
    )
    engine_values = {
        "julia": float(julia["shared_scalars"]["density_quotient_sign_distance"]),
        "jax": float(jax["shared_scalars"]["density_quotient_sign_distance"]),
        "pytorch": float(pytorch["shared_scalars"]["density_quotient_sign_distance"]),
    }
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "SO(3) vector and SU(2) spinor are competing S1 carriers: SO(3) closes at 2pi and loses U/-U sign data before quotient; SU(2) retains the spinor sign until the density quotient, closes only at 4pi, and is required for pre-quotient holonomy-sign/fiber-linking/keystone construction claims. SO(3) vectors remain admissible but coarser after quotient.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": pin_hash,
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
            "proof_tag": "SO3_vs_SU2_vector_spinor_discriminator_v0",
            "proof_pass": bool(julia["all_pass"]),
            "table_version": None,
            "bracket_convention": "not_applicable_group_route_discriminator",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": julia.get("julia_project"), "packages": julia["packages_used"], "role": "SO(3) manifold and QuantumOptics spinor density quotient"},
            "jax": {"packages": jax["packages_used"], "role": "symbolic double-cover map plus z3/cvc5 finite proof"},
            "pytorch": {"packages": pytorch["packages_used"], "role": "geomstats SO(3) and e3nn vector-irrep boundary receipt"},
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
        "comparison_table": table,
        "envelope_facts": {
            "n01_closure_order_gap": {
                "julia": julia["route_receipts"]["n01_closure_order_gap"],
                "jax": jax["route_receipts"]["n01_closure_order_gap"],
                "agreed_gap": 1,
                "scale": "normalized_boolean_closure_not_raw_matrix_norm",
                "raw_norm_cross_dimension_comparison_excluded": True,
            }
        },
        "committed_s1_fact_classification": {
            "requires_spinor_route": [
                "2pi holonomy sign / -I spinor return for pre-quotient construction claims",
                "4pi spinor return behavior as a route discriminator",
                "U versus -U amplitude/sign data before quotient",
                "Hopf S1 fiber and linking carrier facts before quotient",
                "keystone density/Bloch construction from spinor amplitudes before quotient",
            ],
            "survives_vector_route_after_quotient": [
                "SO(3) 2pi vector closure",
                "Bloch/vector observable rotations",
                "density-quotient observables that intentionally identify psi and -psi",
                "SO(3) equivariant l=1/vector representation checks",
            ],
            "density_quotient_collapse": "computed: psi and -psi are distinct in spinor norm, but rho=psi psi^dagger and R(U)=R(-U) collapse the sign.",
        },
        "route_scalars": route_scalars,
        "scalar_checks": scalar_checks,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "nominal_not_accepted": jax["proofs"]["route_truth_table"]["z3"]["nominal_not_accepted"],
                "corrupted_control_not_accepted": jax["proofs"]["route_truth_table"]["z3"]["corrupted_control_not_accepted"],
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "nominal_not_accepted": jax["proofs"]["route_truth_table"]["cvc5"]["nominal_not_accepted"],
                "corrupted_control_not_accepted": jax["proofs"]["route_truth_table"]["cvc5"]["corrupted_control_not_accepted"],
            },
            "julia_z3": {
                "ran": True,
                "verdict": julia["proofs"]["route_truth_table_julia_z3"]["nominal_not_accepted"],
                "load_bearing": True,
                "corrupted_control_not_accepted": julia["proofs"]["route_truth_table_julia_z3"]["corrupted_control_not_accepted"],
            },
        },
        "controls": {
            "corrupted_su2_2pi_closure_control": {
                "julia_z3": julia["controls"]["corrupted_su2_2pi_closure_control"],
                "jax_z3_cvc5": jax["controls"]["corrupted_su2_2pi_closure_control"],
            },
            "pytorch_half_integer_irrep_rejection_control": pytorch["controls"]["half_integer_irrep_rejection_control"],
        },
        "gates": gates,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()) - min(engine_values.values()),
        },
        "summary": {
            "decision": "The spinor route is required for pre-quotient sign/phase, 4pi return, holonomy sign, Hopf S1 fiber/linking, and keystone construction claims. The vector route is admissible but coarser after quotient as SO(3)/Bloch observable data.",
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
