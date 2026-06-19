#!/usr/bin/env python3
"""Envelope for compression_flow_radiated_record_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "compression_flow_radiated_record_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
ENGINES = ["julia", "jax", "pytorch"]
REQUIRED_GATES = {f"G{idx}" for idx in range(1, 9)}
REQUIRED_CONTROLS = {
    "erasure variant",
    "lossy-record variant",
    "record-shuffle",
    "injected conservation violation",
    "label shuffle",
    "trivial-predicate control",
}


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
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "result_path": payload["result_path"],
        "all_pass": payload["all_pass"],
    }


def max_abs_delta(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values) - min(values)


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ENGINES}
    pins = {engine: legs[engine]["pin_block_sha256"] for engine in ENGINES}
    pin_identical = len(set(pins.values())) == 1
    pin_specs_identical = legs["julia"]["PIN_SPEC"] == legs["jax"]["PIN_SPEC"] == legs["pytorch"]["PIN_SPEC"]
    value_keys = [
        "support_size",
        "P_T_size",
        "total_emitted_rows",
        "raw_reconstruction_mismatch_count",
        "quotient_raw_reconstruction_mismatch_count",
        "quotient_level_mismatch_count",
        "max_conservation_defect",
        "injected_conservation_defect",
        "erasure_environment_charge_nats",
    ]
    comparator_value_keys = [
        "charge_full_support_identity",
        "charge_remaining_live_after_step",
        "charge_pre_step_live",
        "charge_emitted_step_register",
    ]
    shared_values = {key: {engine: legs[engine]["values"][key] for engine in ENGINES} for key in value_keys}
    shared_comparator_values = {key: {engine: legs[engine]["values"][key] for engine in ENGINES} for key in comparator_value_keys}
    erasure_register_basis = {engine: legs[engine]["values"]["erasure_register_basis"] for engine in ENGINES}
    shared_value_deltas = {
        key: max_abs_delta([float(legs[engine]["values"][key]) for engine in ENGINES]) for key in value_keys
    }
    shared_comparator_value_deltas = {
        key: max_abs_delta([float(legs[engine]["values"][key]) for engine in ENGINES]) for key in comparator_value_keys
    }
    all_shared_values_match = all(delta == 0.0 for delta in shared_value_deltas.values())
    all_shared_comparator_values_match = all(delta == 0.0 for delta in shared_comparator_value_deltas.values())
    gate_matrix = {engine: legs[engine]["gate_pass"] for engine in ENGINES}
    all_gates_present = all(REQUIRED_GATES <= set(legs[engine]["gates"]) for engine in ENGINES)
    all_gates_pass = all(all(legs[engine]["gate_pass"].get(gate, False) for gate in REQUIRED_GATES) for engine in ENGINES)
    controls = {
        engine: {name: legs[engine]["controls"].get(name, {}) for name in REQUIRED_CONTROLS}
        for engine in ENGINES
    }
    all_controls_fired = all(
        bool(legs[engine]["controls"].get(name, {}).get("fired", False))
        for engine in ENGINES
        for name in REQUIRED_CONTROLS
    )
    candidate_math_labels_present = all(
        "CANDIDATE MATH" in legs[engine]["candidate_math_labels"]["conservation"]
        and "CANDIDATE MATH" in legs[engine]["candidate_math_labels"]["reconstruction"]
        for engine in ENGINES
    )
    ceilings_exact = all(
        legs[engine]["classification"] == "scratch_diagnostic"
        and legs[engine]["promotion_allowed"] is False
        and legs[engine]["formal_admission_allowed"] is False
        for engine in ENGINES
    )
    z3 = legs["jax"]["crossover_proofs"]["raw_uniqueness"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["raw_uniqueness"]["cvc5"]
    erased_z3 = legs["jax"]["crossover_proofs"]["erased_control"]["z3"]
    erased_cvc5 = legs["jax"]["crossover_proofs"]["erased_control"]["cvc5"]
    payload_bound_z3 = {
        "jax": legs["jax"]["proof_payload_bound_z3"],
        "julia": legs["julia"]["proof_payload_bound_z3"],
        "pytorch": legs["pytorch"]["proof_payload_bound_z3"],
    }
    payload_bound_cvc5 = {
        "jax": legs["jax"]["proof_payload_bound_cvc5"],
        "pytorch": legs["pytorch"]["proof_payload_bound_cvc5"],
    }
    payload_bound_ok = all(
        proof["full_record"]["verdict"] == "unsat"
        and proof["dropped_record"]["verdict"] == "sat"
        and bool(proof["dropped_record"]["model_false_state_ids_sample"])
        for proof in [payload_bound_z3["jax"], payload_bound_z3["julia"], payload_bound_z3["pytorch"], payload_bound_cvc5["jax"], payload_bound_cvc5["pytorch"]]
    )
    raw_reconstruction_value = {engine: legs[engine]["values"]["raw_reconstruction_mismatch_count"] for engine in ENGINES}
    all_pass = all(
        [
            all(legs[engine]["all_pass"] for engine in ENGINES),
            pin_identical,
            pin_specs_identical,
            all_shared_values_match,
            all_gates_present,
            all_gates_pass,
            all_controls_fired,
            candidate_math_labels_present,
            ceilings_exact,
            z3["verdict"] == "unsat",
            cvc5["verdict"] == "unsat",
            erased_z3["verdict"] == "sat",
            erased_cvc5["verdict"] == "sat",
            all_shared_comparator_values_match,
            all(value == "full_support_identity" for value in erasure_register_basis.values()),
            payload_bound_ok,
            legs["pytorch"].get("pytorch_independence_receipt", {}).get("imports_jax_core") is False,
        ]
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "compression_flow_radiated_record_envelope_v0",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ENGINES,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "claim": "a first finite compression-flow/radiated-record packet",
        "allowed_claims": [
            "scratch_diagnostic finite set/record conservation receipt",
            "candidate-math conservation/reconstruction receipt",
            "record-granularity killed-information measurement",
        ],
        "disallowed_claims": [
            "manifold algorithm proven",
            "QIT separation",
            "axis/bridge/physics claim",
            "formal admission",
        ],
        "candidate_math_labels": legs["jax"]["candidate_math_labels"],
        "PIN_SPEC": legs["jax"]["PIN_SPEC"],
        "pin_block_sha256": legs["jax"]["pin_block_sha256"],
        "pin_identical_across_legs": pin_identical,
        "pin_specs_identical_across_legs": pin_specs_identical,
        "carrier_lineage": legs["jax"]["carrier_lineage"],
        "carrier_support_table_hash": legs["jax"]["carrier_support_table_hash"],
        "carrier_support_hash_recomputation_citation": {
            engine: legs[engine]["carrier_support_hash_recomputation_citation"] for engine in ENGINES
        },
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "engines": {engine: engine_record(legs[engine]) for engine in ENGINES},
        "claim_path_tools": ["QuantumOptics", "Z3", "jax", "z3", "cvc5", "torch", "torch_geometric"],
        "crossover_proofs": {
            "z3": z3,
            "cvc5": cvc5,
            "julia_z3": legs["julia"]["crossover_proofs"]["raw_uniqueness"]["z3"],
            "erased_control": {"z3": erased_z3, "cvc5": erased_cvc5},
        },
        "proof_rowset_coverage": {engine: legs[engine]["proof_rowset_coverage"] for engine in ENGINES},
        "proof_payload_bound_z3": payload_bound_z3,
        "proof_payload_bound_cvc5": payload_bound_cvc5,
        "payload_bound_proof_ok": payload_bound_ok,
        "divergence": {
            "julia_authoritative": True,
            "observable": "raw_reconstruction_mismatch_count",
            "engine_values": raw_reconstruction_value,
            "max_divergence": max_abs_delta([float(v) for v in raw_reconstruction_value.values()]),
            "shared_value_deltas": shared_value_deltas,
            "shared_comparator_value_deltas": shared_comparator_value_deltas,
        },
        "shared_values": shared_values,
        "erasure_register_basis": erasure_register_basis,
        "shared_comparator_values": shared_comparator_values,
        "all_shared_values_match": all_shared_values_match,
        "all_shared_comparator_values_match": all_shared_comparator_values_match,
        "gate_matrix": gate_matrix,
        "all_gates_present": all_gates_present,
        "all_gates_pass": all_gates_pass,
        "controls": controls,
        "all_controls_fired": all_controls_fired,
        "record_mode_comparison": legs["jax"]["reconstruction"],
        "variants": legs["jax"]["variants"],
        "pytorch_graph_receipt": legs["pytorch"].get("pytorch_graph_receipt"),
        "pytorch_independence_receipt": legs["pytorch"].get("pytorch_independence_receipt"),
        "julia_native_checks": legs["julia"].get("julia_native_checks"),
        "jax_batched_receipt": legs["jax"].get("jax_batched_receipt"),
        "candidate_math_labels_present": candidate_math_labels_present,
        "ceilings_exact": ceilings_exact,
        "acceptance_summary": {
            "legs_exit_0_when_run": {engine: legs[engine]["all_pass"] for engine in ENGINES},
            "PIN_identical": pin_identical,
            "carrier_lineage_cited": bool(legs["jax"]["PIN_SPEC"]["carrier"]["carrier_lineage"]),
            "G1_G8_named_computed_fields": all_gates_present,
            "controls_fired": all_controls_fired,
            "candidate_math_labels_present": candidate_math_labels_present,
            "ceiling_fields_exact": ceilings_exact,
            "erasure_register_basis_pinned": all(value == "full_support_identity" for value in erasure_register_basis.values()),
            "payload_bound_z3_cvc5_flip": payload_bound_ok,
            "pytorch_independent_of_jax_core": legs["pytorch"].get("pytorch_independence_receipt", {}).get("imports_jax_core") is False,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
