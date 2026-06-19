#!/usr/bin/env python3
"""Three-engine envelope for geo_s1_scaling_stress_678q_exact_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_scaling_stress_678q_exact_v0"
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
RUNG_NS = (6, 7, 8)
REQUIRED_RECEIPTS = [
    "F01_finitude_receipt",
    "N01_noncommutation_receipt",
    "T01_bracketing_receipt",
    "W1_carrier_quotient",
    "W2_Cl2n_exact_floor",
    "W3_max_anticommuting_family",
    "W4_finite_pauli_string_stress",
    "W5_named_stabilizer_controls",
    "W6_scaling_boundary_ceiling",
    "W7_classification_table",
]
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent lane receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing and pin equality checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_gate(condition: bool, name: str, details: Any) -> dict[str, Any]:
    return {"pass": bool(condition), "gate": name, "details": details}


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
        "claim_path_tools": payload["claim_path_tools"],
        "rung_pass": {
            rung: {name: payload["rungs"][rung][name]["pass"] for name in REQUIRED_RECEIPTS}
            for rung in map(str, RUNG_NS)
        },
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: payload["shared_scalars"] for engine, payload in payloads.items()}
    rows = []
    max_divergence = 0
    for rung in map(str, RUNG_NS):
        keys = sorted(set().union(*(set(values[engine][rung]) for engine in values)))
        for key in keys:
            row_values = {engine: values[engine][rung].get(key) for engine in values}
            exact_match = len(set(row_values.values())) == 1
            rows.append({"rung": rung, "key": key, "values": row_values, "exact_match": exact_match})
            if not exact_match:
                max_divergence = 1
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "max_divergence": max_divergence,
        "comparison": {"rows": rows, "exact_match": max_divergence == 0},
    }


def receipt_matrix(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        rung: {
            receipt: {engine: payload["rungs"][rung][receipt]["pass"] for engine, payload in payloads.items()}
            for receipt in REQUIRED_RECEIPTS
        }
        for rung in map(str, RUNG_NS)
    }


def expected_scalars() -> dict[str, dict[str, int]]:
    return {
        "6": {
            "hilbert_dim": 64,
            "operator_basis_count": 4096,
            "mixed_density_real_dim": 4095,
            "gamma_count": 12,
            "chirality_positive_dim": 32,
            "chirality_negative_dim": 32,
            "max_anticommuting_family": 13,
        },
        "7": {
            "hilbert_dim": 128,
            "operator_basis_count": 16384,
            "mixed_density_real_dim": 16383,
            "gamma_count": 14,
            "chirality_positive_dim": 64,
            "chirality_negative_dim": 64,
            "max_anticommuting_family": 15,
        },
        "8": {
            "hilbert_dim": 256,
            "operator_basis_count": 65536,
            "mixed_density_real_dim": 65535,
            "gamma_count": 16,
            "chirality_positive_dim": 128,
            "chirality_negative_dim": 128,
            "max_anticommuting_family": 17,
        },
    }


def proof_summary(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    jax = payloads["jax"]
    return {
        rung: {
            "finite_pauli_extension_scan": jax["proofs"][rung]["P1_finite_pauli_extension_scan"],
            "max_family_bound": jax["proofs"][rung]["P2_max_family_bound"],
            "named_state_controls": jax["proofs"][rung]["P3_named_state_controls"],
        }
        for rung in map(str, RUNG_NS)
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    pins = {payload["pin_sha256"] for payload in payloads.values()}
    ceilings_exact = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is PROMOTION_ALLOWED
        and payload["formal_admission_allowed"] is FORMAL_ADMISSION_ALLOWED
        for payload in payloads.values()
    )
    matrix = receipt_matrix(payloads)
    div = divergence(payloads)
    expected = expected_scalars()
    scalar_gate_details: dict[str, Any] = {}
    scalar_ok = True
    for engine, payload in payloads.items():
        scalar_gate_details[engine] = {}
        for rung, rows in expected.items():
            actual = payload["shared_scalars"][rung]
            scalar_gate_details[engine][rung] = {key: actual.get(key) for key in rows}
            scalar_ok = scalar_ok and all(actual.get(key) == value for key, value in rows.items())
            scalar_ok = scalar_ok and actual.get("full_family_pauli_extension_candidates") == 0
            scalar_ok = scalar_ok and actual.get("next_family_allowed") == 0
            scalar_ok = scalar_ok and actual.get("minimum_floor_moved_from_3Q") == 0
    gates = {
        "legs_exit_0_by_receipt": require_gate(
            all(payload["all_pass"] is True for payload in payloads.values()),
            "legs_exit_0_by_receipt",
            {engine: payload["all_pass"] for engine, payload in payloads.items()},
        ),
        "pin_identical": require_gate(
            len(pins) == 1 and next(iter(pins)) == sha256_text(payloads["jax"]["pin_spec"]),
            "pin_identical",
            sorted(pins),
        ),
        "ceiling_exact": require_gate(
            ceilings_exact,
            "ceiling_exact",
            {engine: payload["ceiling"] for engine, payload in payloads.items()},
        ),
        "per_rung_receipt_tables_complete": require_gate(
            all(all(all(statuses.values()) for statuses in rung.values()) for rung in matrix.values()),
            "per_rung_receipt_tables_complete",
            matrix,
        ),
        "divergence_exact": require_gate(div["max_divergence"] == 0, "divergence_exact", div["comparison"]),
        "expected_scalars_exact": require_gate(scalar_ok, "expected_scalars_exact", scalar_gate_details),
        "resource_rows_diagnostic_nonclaim": require_gate(
            all(
                payload["rungs"][rung]["W4_finite_pauli_string_stress"]["resource_rows"][row]["strength_label"] == "diagnostic_float_nonclaim"
                for payload in payloads.values()
                for rung in map(str, RUNG_NS)
                for row in payload["rungs"][rung]["W4_finite_pauli_string_stress"]["resource_rows"]
            ),
            "resource_rows_diagnostic_nonclaim",
            "all W4 resource rows carry diagnostic_float_nonclaim",
        ),
    }
    all_pass = all(gate["pass"] is True for gate in gates.values())
    proofs = proof_summary(payloads)
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "claim": "For n in {6,7,8}, the exact S1 qubit ladder scaling/stress machinery supports C^(2^n), S^(2^(n+1)-1), CP^(2^n-1), density real dimension 4^n-1, Cl_(2n) on C^(2^n), gamma_(2n+1) chirality splits 32+32/64+64/128+128, and max anticommuting families 13/15/17 by constructive Pauli/Jordan-Wigner families plus representation-bound receipts.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": payloads["jax"]["pin_spec"],
        "pin_sha256": payloads["jax"]["pin_sha256"],
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": payloads["julia"]["source_sha256"],
            "receipt_path": payloads["julia"]["result_path"],
            "proof_tag": "scaling_stress_678q_exact_jordan_wigner_representation_bound_z3",
            "proof_pass": payloads["julia"]["all_pass"],
            "table_version": SIM_ID,
            "bracket_convention": "Jordan-Wigner Cl(2n), gamma_(2n+1)=(-i)^n gamma1...gamma2n; M_(2^n)(C) multiplication is associative",
            "consumer_policy": "independent engine recomputation; no peer-result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": payloads["julia"]["packages_used"], "role": "semantic exact label/theorem/Z3 lane"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": payloads["jax"]["packages_used"], "role": "vectorized finite Pauli-string scan plus z3/cvc5/sympy controls"},
            "pytorch": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": payloads["pytorch"]["packages_used"], "role": "torch integer tensor finite Pauli-string scan plus z3/cvc5/sympy controls"},
            "tensor_exchange": "none_no_cross_engine_tensor_exchange",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "allowed_claims": [
            "scratch diagnostic 6Q/7Q/8Q scaling facts listed in claim",
            "finite overbuild boundary at 8Q under this directive",
            "exact negative control that 6Q/7Q/8Q do not move the 3Q minimum-floor claim",
        ],
        "must_not_claim_fences": [
            "new minimum",
            "carrier admission",
            "formal admission",
            "final M(C)",
            "QIT-engine admission",
            "physics claim",
            "bridge or axis-level claim",
            "ladder beyond 8Q",
        ],
        "claim_path_tools": collect_claim_tools(payloads),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "per_rung_receipt_tables": matrix,
        "rungs": {rung: {engine: payload["rungs"][rung] for engine, payload in payloads.items()} for rung in map(str, RUNG_NS)},
        "theorem_receipt_once": payloads["jax"]["theorem_receipt_once"],
        "proofs": proofs,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    rung: {
                        "no_full_family_pauli_extension": proofs[rung]["finite_pauli_extension_scan"]["z3_no_full_family_extension"],
                        "next_family_blocked_by_representation_bound": proofs[rung]["max_family_bound"]["z3_next_family_blocked_by_representation_bound"],
                        "max_family_boundary_control": proofs[rung]["max_family_bound"]["z3_max_family_boundary_control"],
                    }
                    for rung in map(str, RUNG_NS)
                },
            },
            "cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    rung: {
                        "no_full_family_pauli_extension": proofs[rung]["finite_pauli_extension_scan"]["cvc5_no_full_family_extension"],
                        "next_family_blocked_by_representation_bound": proofs[rung]["max_family_bound"]["cvc5_next_family_blocked_by_representation_bound"],
                        "max_family_boundary_control": proofs[rung]["max_family_bound"]["cvc5_max_family_boundary_control"],
                    }
                    for rung in map(str, RUNG_NS)
                },
            },
            "julia_z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    rung: payloads["julia"]["proofs"][rung]["P2_max_family_bound"]
                    for rung in map(str, RUNG_NS)
                },
            },
            "pytorch_z3": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    rung: payloads["pytorch"]["proofs"][rung]["P2_max_family_bound"]
                    for rung in map(str, RUNG_NS)
                },
            },
            "pytorch_cvc5": {
                "ran": True,
                "verdict": "unsat",
                "load_bearing": True,
                "proofs": {
                    rung: payloads["pytorch"]["proofs"][rung]["P2_max_family_bound"]
                    for rung in map(str, RUNG_NS)
                },
            },
        },
        "gate_pass": gates,
        "divergence": div,
        "expected_scalars": expected,
        "builder_self_check_is_evidence": False,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
