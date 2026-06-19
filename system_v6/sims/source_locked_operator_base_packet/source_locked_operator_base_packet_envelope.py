#!/usr/bin/env python3
"""Composite envelope for the source-locked four-operator base packet."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "source_locked_operator_base_packet"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULTS_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-9

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result-path binding"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload.get("all_pass") is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "tool_exercise_map": payload.get("tool_exercise_map", {}),
    }


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload.get("shared_scalars", {}).keys()) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    rows: list[dict[str, Any]] = []
    max_divergence = 0.0
    max_key = None
    per_engine_vs_julia = {engine: 0.0 for engine in payloads}
    for key in common:
        values = {engine: float(payloads[engine]["shared_scalars"][key]) for engine in payloads}
        spread = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": spread, "within_tolerance": spread <= TOL})
        if spread > max_divergence:
            max_divergence = spread
            max_key = key
        for engine, value in values.items():
            per_engine_vs_julia[engine] = max(per_engine_vs_julia[engine], abs(value - values["julia"]))
    union = set.union(*key_sets.values())
    return {
        "common_scalar_count": len(common),
        "common_keys": common,
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "within_tolerance": max_divergence <= TOL,
        "engine_values_vs_julia_max_abs": per_engine_vs_julia,
        "engine_specific_scalar_keys": {engine: sorted(keys - set(common)) for engine, keys in key_sets.items()},
        "missing_common_by_engine": {engine: sorted(union - keys) for engine, keys in key_sets.items()},
    }


def pin_match(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    specs = {engine: payload["pin_spec"] for engine, payload in payloads.items()}
    identities = {engine: payload["pin_identity"] for engine, payload in payloads.items()}
    return {
        "pin_spec_equal": len(set(specs.values())) == 1,
        "pin_identity_equal": identities["julia"] == identities["jax"] == identities["pytorch"],
        "pin_spec": specs["julia"],
        "pin_identity": identities["julia"],
    }


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    comparison = compare_shared_scalars(payloads)
    pin = pin_match(payloads)
    z3 = payloads["jax"]["smt"]["z3"]
    cvc5 = payloads["jax"]["smt"]["cvc5"]
    julia_z3 = payloads["julia"]["smt"]["julia_z3"]
    controls = {
        "legs_all_pass": all(payload.get("all_pass") is True for payload in payloads.values()),
        "reads_peer_result_false": all(payload.get("reads_peer_result") is False for payload in payloads.values()),
        "pin_spec_equal": pin["pin_spec_equal"],
        "pin_identity_equal": pin["pin_identity_equal"],
        "like_for_like_scalar_divergence_within_tolerance": comparison["within_tolerance"],
        "source_citations_present": all(bool(payload.get("source_citations")) for payload in payloads.values()),
        "operator_backlog_present": all(bool(payload.get("operator_backlog")) for payload in payloads.values()),
        "z3_forced_Ti_Fi_equality_unsat": z3["verdict"] == "unsat",
        "cvc5_forced_Ti_Fi_equality_unsat": cvc5["verdict"] == "unsat",
        "julia_z3_forced_Ti_Fi_equality_unsat": julia_z3["verdict"] == "unsat",
        "z3_Ti_Fe_commuting_control_sat": z3["commuting_control_verdict"] == "sat",
        "cvc5_Ti_Fe_commuting_control_sat": cvc5["commuting_control_verdict"] == "sat",
        "julia_z3_Ti_Fe_commuting_control_sat": julia_z3["commuting_control_verdict"] == "sat",
        "classification_ceiling_held": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
    }
    all_pass = bool(all(controls.values()))
    commutator_table = payloads["julia"]["commutator_table"]["table"]
    property_certificates = {engine: payload["property_certificates"] for engine, payload in payloads.items()}
    representation_consistency = {engine: payload["representation_consistency"] for engine, payload in payloads.items()}
    cptp_certificates = {engine: payload["cptp_certificates"] for engine, payload in payloads.items()}
    negative_controls = {engine: payload["negative_controls"] for engine, payload in payloads.items()}
    return {
        "schema_version": "three_engine_sim_result_v1",
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "scratch_diagnostic source-lock check for Ti/Te/Fi/Fe only; no canonical/admission/operator-family completion claim",
        "all_pass": all_pass,
        "pin": pin,
        "source_citations": payloads["julia"]["source_citations"],
        "operator_forms": payloads["julia"]["operator_forms"],
        "operator_backlog": payloads["julia"]["operator_backlog"],
        "commutator_table_trace_norm_rho0": commutator_table,
        "commutator_known_zeros": payloads["julia"]["commutator_table"]["known_zeros"],
        "commutator_known_nonzeros": payloads["julia"]["commutator_table"]["known_nonzeros"],
        "property_certificates": property_certificates,
        "representation_consistency": representation_consistency,
        "cptp_certificates": cptp_certificates,
        "negative_controls": negative_controls,
        "smt_verdicts": {
            "z3": {"Ti_Fi_forced_equality": z3["verdict"], "Ti_Fe_forced_equality": z3["commuting_control_verdict"]},
            "cvc5": {"Ti_Fi_forced_equality": cvc5["verdict"], "Ti_Fe_forced_equality": cvc5["commuting_control_verdict"]},
            "julia_z3": {"Ti_Fi_forced_equality": julia_z3["verdict"], "Ti_Fe_forced_equality": julia_z3["commuting_control_verdict"]},
        },
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3["verdict"],
                "claim": z3["claim"],
                "commuting_control_verdict": z3["commuting_control_verdict"],
                "source_entry_binding": z3["source_entry_binding"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5["verdict"],
                "claim": cvc5["claim"],
                "commuting_control_verdict": cvc5["commuting_control_verdict"],
                "source_entry_binding": cvc5["source_entry_binding"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "claim": julia_z3["claim"],
                "commuting_control_verdict": julia_z3["commuting_control_verdict"],
                "source_entry_binding": julia_z3["source_entry_binding"],
            },
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "jax", "jax.numpy", "torch", "torch.func"],
        "control_only_tools": [],
        "like_for_like_comparison": comparison,
        "divergence": {
            "julia_authoritative": True,
            "engine_values": comparison["engine_values_vs_julia_max_abs"],
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "controls": controls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"envelope": str(RESULT_PATH), "all_pass": result["all_pass"], "max_divergence": result["divergence"]["max_divergence"]}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
