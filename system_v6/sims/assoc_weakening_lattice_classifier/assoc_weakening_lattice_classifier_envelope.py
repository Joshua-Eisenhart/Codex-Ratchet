#!/usr/bin/env python3
"""Composite envelope for the associativity weakening lattice classifier."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "assoc_weakening_lattice_classifier"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULTS_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive matrix digest comparison"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result-path binding"},
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload.get("packages_used", []),
        "aligned_packages_load_bearing": payload.get("aligned_packages_load_bearing", []),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "matrix_hash": stable_hash(payload.get("classification_matrix")),
        "positions_hash": stable_hash(payload.get("lattice_positions")),
    }


def matrix_mismatches(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base = payloads["julia"]["classification_matrix"]
    rows: dict[str, Any] = {}
    for engine, payload in payloads.items():
        rows[engine] = {
            "matches_julia": payload["classification_matrix"] == base,
            "matrix_hash": stable_hash(payload["classification_matrix"]),
        }
    return rows


def position_mismatches(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base = payloads["julia"]["lattice_positions"]
    rows: dict[str, Any] = {}
    for engine, payload in payloads.items():
        rows[engine] = {
            "matches_julia": payload["lattice_positions"] == base,
            "positions_hash": stable_hash(payload["lattice_positions"]),
        }
    return rows


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    matrix_compare = matrix_mismatches(payloads)
    position_compare = position_mismatches(payloads)
    matrices_agree = all(row["matches_julia"] for row in matrix_compare.values())
    positions_agree = all(row["matches_julia"] for row in position_compare.values())
    matrix = julia["classification_matrix"]
    positions = julia["lattice_positions"]
    identity_order = julia["identity_order"]

    jax_smt = jax["smt"]
    julia_smt = julia["smt"]["julia_z3"]
    decisive_smt = {
        "O_associativity": {
            "claim": "There exists a basis triple with (xy)z != x(yz) in O.",
            "z3": jax_smt["z3"]["O_associativity_violation"]["verdict"],
            "cvc5": jax_smt["cvc5"]["O_associativity_violation"]["verdict"],
            "julia_z3": julia_smt["O_associativity_violation"]["verdict"],
            "H_control_z3": jax_smt["z3"]["H_associativity_violation_control"]["verdict"],
            "H_control_cvc5": jax_smt["cvc5"]["H_associativity_violation_control"]["verdict"],
            "H_control_julia_z3": julia_smt["H_associativity_violation_control"]["verdict"],
            "passes": jax_smt["z3"]["O_associativity_violation"]["verdict"] == jax_smt["cvc5"]["O_associativity_violation"]["verdict"] == julia_smt["O_associativity_violation"]["verdict"] == "sat"
            and jax_smt["z3"]["H_associativity_violation_control"]["verdict"] == jax_smt["cvc5"]["H_associativity_violation_control"]["verdict"] == julia_smt["H_associativity_violation_control"]["verdict"] == "unsat",
        },
        "S_alternativity": {
            "claim": "There exists a sampled generic x,y with (xx)y != x(xy) in S.",
            "z3": jax_smt["z3"]["S_alternativity_violation"]["verdict"],
            "cvc5": jax_smt["cvc5"]["S_alternativity_violation"]["verdict"],
            "H_control_z3": jax_smt["z3"]["H_alternativity_violation_control"]["verdict"],
            "H_control_cvc5": jax_smt["cvc5"]["H_alternativity_violation_control"]["verdict"],
            "passes": jax_smt["z3"]["S_alternativity_violation"]["verdict"] == jax_smt["cvc5"]["S_alternativity_violation"]["verdict"] == "sat"
            and jax_smt["z3"]["H_alternativity_violation_control"]["verdict"] == jax_smt["cvc5"]["H_alternativity_violation_control"]["verdict"] == "unsat",
        },
    }

    column_has_fail = julia["controls"]["column_has_at_least_one_fail"]
    permuted_controls = {engine: payload["controls"]["permuted_output_axis_O"] for engine, payload in payloads.items()}
    engine_values = {
        engine: {
            "matrix_mismatch_count": 0 if matrix_compare[engine]["matches_julia"] else 1,
            "position_mismatch_count": 0 if position_compare[engine]["matches_julia"] else 1,
        }
        for engine in payloads
    }
    max_divergence = max(value for row in engine_values.values() for value in row.values())
    expected = {
        "O_passes_2_3_4_5_6_7_fails_1": matrix["O"]["associativity"] is False
        and all(matrix["O"][key] is True for key in ["alternativity", "artin_diassociativity_basis_pairs", "moufang", "flexibility", "power_associativity", "third_power_associativity"]),
        "S_fails_2_flex_power_third_checked": matrix["S"]["alternativity"] is False
        and matrix["S"]["flexibility"] is True
        and matrix["S"]["power_associativity"] is True
        and matrix["S"]["third_power_associativity"] is True,
        "kill_control_fails_5": matrix["K"]["flexibility"] is False,
        "every_identity_column_has_fail": all(column_has_fail.values()),
        "permuted_table_control_shifts_all_engines": all(row["shifted"] for row in permuted_controls.values()),
    }

    all_pass = bool(
        all(payload.get("all_pass") is True for payload in payloads.values())
        and matrices_agree
        and positions_agree
        and all(row["passes"] for row in decisive_smt.values())
        and all(expected.values())
        and max_divergence == 0
        and all(payload.get("reads_peer_result") is False for payload in payloads.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": f"{SIM_ID}_envelope",
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "finite structure-constant classifier harness only; scratch diagnostic, not canonical algebra admission",
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": None,
            "artifact_sha256": None,
            "source_sha256": julia.get("source_sha256"),
            "receipt_path": str(JULIA_RESULT),
            "proof_tag": "generated_cayley_dickson_structure_constants_with_julia_z3_associator_control",
            "proof_pass": decisive_smt["O_associativity"]["passes"],
            "table_version": "assoc_weakening_lattice_classifier_v1",
            "bracket_convention": "explicit left/right parenthesized products over C[k,i,j]",
            "consumer_policy": "engines compute local tables independently; no peer result reads",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": julia.get("packages_used", []), "role": "semantic_owner"},
            "jax": {"packages": jax.get("packages_used", []), "role": "batched_exhaustive_worker_and_smt_sidecar"},
            "pytorch": {"packages": pytorch.get("packages_used", []), "role": "torch_tensor_and_torch_func_consumer"},
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "identity_order": identity_order,
        "classification_matrix": matrix,
        "lattice_positions": positions,
        "failure_witnesses": julia["failure_witnesses"],
        "table_sha256": julia["table_sha256"],
        "matrix_comparison": matrix_compare,
        "position_comparison": position_compare,
        "controls": {
            "column_has_at_least_one_fail": column_has_fail,
            "permuted_table_control": permuted_controls,
        },
        "smt_verdicts": decisive_smt,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": decisive_smt["O_associativity"]["z3"],
                "claim": "O associativity violation and S alternativity violation derived from bound structure constants; H controls are UNSAT.",
                "O_associativity": decisive_smt["O_associativity"],
                "S_alternativity": decisive_smt["S_alternativity"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": decisive_smt["O_associativity"]["cvc5"],
                "claim": "Independent cvc5 derivation matches z3 on the O/S decisive cells and H controls.",
                "O_associativity": decisive_smt["O_associativity"],
                "S_alternativity": decisive_smt["S_alternativity"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": decisive_smt["O_associativity"]["julia_z3"],
                "claim": "Julia Z3 binds the O/H structure constants and derives the O SAT versus H UNSAT associativity flip.",
                "O_associativity": decisive_smt["O_associativity"],
            },
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "jax", "jax.numpy", "torch", "torch.func"],
        "control_only_tools": [],
        "expected_checks": expected,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_divergence,
            "comparison_rule": "exact classification matrix and lattice-position equality",
        },
        "ledger_result_paths": {"julia": str(JULIA_RESULT), "jax": str(JAX_RESULT), "pytorch": str(PYTORCH_RESULT)},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ASSOC_WEAKENING_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"O={result['lattice_positions']['O']} "
        f"S={result['lattice_positions']['S']} "
        f"K={result['lattice_positions']['K']} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"z3_O={result['smt_verdicts']['O_associativity']['z3']} "
        f"cvc5_S={result['smt_verdicts']['S_alternativity']['cvc5']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
