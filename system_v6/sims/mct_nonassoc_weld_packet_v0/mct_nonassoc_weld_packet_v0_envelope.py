#!/usr/bin/env python3
"""Envelope for mct_nonassoc_weld_packet_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "mct_nonassoc_weld_packet_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
COMMON_VALUE_KEYS = [
    "witness_residual_norm",
    "witness_residual_norm_sq",
    "active_bracketing_class_count",
    "dropped_bracketing_class_count",
    "O_dim_der",
    "O_corrupted_dim_der",
    "full_sweep_nonzero_count",
    "density_gap_norm",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "carrier_provenance": payload["carrier_provenance"],
        "W_checks_present": sorted(payload["W_checks"].keys()),
        "W_pass": {name: row.get("pass", False) for name, row in payload["W_checks"].items()},
        "controls_fired": {name: row.get("fired", False) for name, row in payload["controls"].items()},
        "values": payload["values"],
        "all_pass": payload["all_pass"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_div = 0.0
    max_key = None
    for key in COMMON_VALUE_KEYS:
        values = {engine: float(payload["values"][key]) for engine, payload in legs.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": {engine: payload["values"] for engine, payload in legs.items()},
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"common_observable_count": len(COMMON_VALUE_KEYS), "rows": rows, "within_tolerance": max_div <= 1.0e-8},
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    pin_hashes = {payload["pin_block_sha256"] for payload in legs.values()}
    carrier_provenance_json = {json.dumps(payload["carrier_provenance"], sort_keys=True) for payload in legs.values()}
    w_names = {f"W{i}" for i in range(1, 9)}
    all_w_present = all(w_names <= set(payload["W_checks"].keys()) for payload in legs.values())
    all_w_pass = all(all(payload["W_checks"][name].get("pass", False) for name in w_names) for payload in legs.values())
    all_controls_fired = all(all(row.get("fired", False) for row in payload["controls"].values()) for payload in legs.values())
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["carrier_provenance"]["branches"]["branch_b_three_spinor_floor"] == "main_support"
        for payload in legs.values()
    )
    provenance_ok = len(carrier_provenance_json) == 1
    pin_ok = len(pin_hashes) == 1
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    smt_ok = (
        z3["ran"]
        and cvc5["ran"]
        and z3["verdict"] == cvc5["verdict"] == "unsat"
        and z3["erased_control_verdict"] == cvc5["erased_control_verdict"] == "sat"
        and z3["quaternion_control_verdict"] == cvc5["quaternion_control_verdict"] == "sat"
        and julia_z3["verdict"] == "unsat"
    )
    div = divergence(legs)
    all_pass = (
        all(payload["all_pass"] for payload in legs.values())
        and all_w_present
        and all_w_pass
        and all_controls_fired
        and ceiling_ok
        and provenance_ok
        and pin_ok
        and smt_ok
        and div["comparison"]["within_tolerance"]
    )
    carrier_provenance = legs["julia"]["carrier_provenance"]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": carrier_provenance["artifact_path"],
            "artifact_sha256": carrier_provenance["artifact_sha256"],
            "source_sha256": carrier_provenance["artifact_source_sha256"],
            "receipt_path": "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
            "proof_tag": carrier_provenance["proof_tag"],
            "proof_pass": carrier_provenance["proof_pass"],
            "table_version": carrier_provenance["table_version"],
            "bracket_convention": carrier_provenance["bracket_convention"],
            "consumer_policy": "compute_from_exported_C_tensor_with_fixed_parenthesization_then_apply_recorded_whole_table_basis_lift_for_committed_classifier_convention",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": legs["julia"]["packages_used"], "role": "semantic_owner"},
            "jax": {"packages": legs["jax"]["packages_used"], "role": "batched_sweep_and_raw_value_smt"},
            "pytorch": {"packages": legs["pytorch"]["packages_used"], "role": "independent_torch_tensor_scalar_path"},
            "tensor_exchange": "none; engines read the same source artifact independently",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "crossover_proofs": {"z3": z3, "cvc5": cvc5, "julia_z3": julia_z3},
        "divergence": div,
        "carrier_provenance": carrier_provenance,
        "packet_receipt": {
            "pin_blocks_byte_identical": pin_ok,
            "pin_block_sha256": sorted(pin_hashes)[0],
            "carrier_provenance_byte_identical": provenance_ok,
            "all_W1_W8_present": all_w_present,
            "all_W1_W8_pass": all_w_pass,
            "all_controls_fired": all_controls_fired,
            "ceiling_ok": ceiling_ok,
            "raw_value_smt_ok": smt_ok,
            "source_artifact_raw_residual": legs["julia"]["W_checks"]["W1"]["artifact_raw_residual"]["residual_vector"],
            "committed_lift_residual": legs["julia"]["W_checks"]["W1"]["committed_lift_residual"]["residual_vector"],
            "drop_bracketing_counts": {
                engine: {
                    "active": payload["W_checks"]["W4"]["active_bracketing_class_count"],
                    "dropped": payload["W_checks"]["W4"]["dropped_bracketing_class_count"],
                }
                for engine, payload in legs.items()
            },
            "g2_language": "installed_only_not_root_forced",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        },
        "W_checks": {engine: legs[engine]["W_checks"] for engine in legs},
        "controls": {engine: legs[engine]["controls"] for engine in legs},
        "kill_conditions": {engine: legs[engine]["kill_conditions"] for engine in legs},
        "probe_families": legs["julia"]["probe_families"],
        "operations": legs["julia"]["operations"],
        "values": legs["julia"]["values"],
        "tool_calls": legs["julia"]["tool_calls"] + legs["jax"]["tool_calls"] + legs["pytorch"]["tool_calls"],
        "TOOL_MANIFEST": {
            "julia": legs["julia"]["TOOL_MANIFEST"],
            "jax": legs["jax"]["TOOL_MANIFEST"],
            "pytorch": legs["pytorch"]["TOOL_MANIFEST"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "julia": legs["julia"]["TOOL_INTEGRATION_DEPTH"],
            "jax": legs["jax"]["TOOL_INTEGRATION_DEPTH"],
            "pytorch": legs["pytorch"]["TOOL_INTEGRATION_DEPTH"],
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_NONASSOC_WELD_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"divergence={result['divergence']['max_divergence']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
