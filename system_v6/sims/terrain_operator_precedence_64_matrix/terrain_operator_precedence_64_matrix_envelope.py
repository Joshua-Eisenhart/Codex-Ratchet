#!/usr/bin/env python3
"""Envelope for the terrain/operator precedence 64-cell chart matrix."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_operator_precedence_64_matrix"
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
TOL = 1.0e-6

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from three independent leg receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    record = {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "values": payload["shared_scalars"],
        "controls": payload["controls"],
    }
    for key in ["julia_reuse_mode", "source_backed_audit_choice", "f6_result_note"]:
        if key in payload:
            record[key] = payload[key]
    return record


def compare_shared_scalars(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key_sets = {engine: set(payload["shared_scalars"].keys()) for engine, payload in payloads.items()}
    common = sorted(set.intersection(*key_sets.values()))
    same_sets = all(keys == key_sets["julia"] for keys in key_sets.values())
    rows = []
    max_divergence = 0.0
    max_key = None
    for key in common:
        values = {engine: float(payload["shared_scalars"][key]) for engine, payload in payloads.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_divergence:
            max_divergence = diff
            max_key = key
    union = set.union(*key_sets.values())
    return {
        "same_named_observable_sets": same_sets,
        "common_observable_count": len(common),
        "missing_by_engine": {engine: sorted(union - keys) for engine, keys in key_sets.items()},
        "rows": rows,
        "max_divergence": max_divergence,
        "max_divergence_key": max_key,
        "within_tolerance": same_sets and max_divergence <= TOL,
    }


def collect_claim_tools(payloads: dict[str, dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for payload in payloads.values():
        tools.update(str(tool) for tool in payload.get("claim_path_tools", []))
    return sorted(tools)


def all_gate_fields_present(jax_payload: dict[str, Any]) -> bool:
    controls = jax_payload["controls"]
    return all(f"G{idx}_" in " ".join(controls.keys()) for idx in range(1, 9))


def build_result() -> dict[str, Any]:
    payloads = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    comparison = compare_shared_scalars(payloads)
    pin_strings = {payload["pin_block_canonical_json"] for payload in payloads.values()}
    pin_hashes = {payload["pin_block_sha256"] for payload in payloads.values()}
    jax = payloads["jax"]
    julia = payloads["julia"]
    jax_z3 = jax["crossover_proofs"]["z3"]
    jax_cvc5 = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    controls = {
        "legs_all_pass": all(payload["all_pass"] is True for payload in payloads.values()),
        "classification_ceiling_exact": CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False,
        "pin_blocks_byte_identical": len(pin_strings) == 1 and len(pin_hashes) == 1,
        "both_reuse_lineages_cited": all(
            "operator_packet" in payload["source_reuse_lineage"]
            and "terrain_packet" in payload["source_reuse_lineage"]
            and "carrier_packet" in payload["source_reuse_lineage"]
            for payload in payloads.values()
        ),
        "shared_scalars_within_tolerance": comparison["within_tolerance"],
        "matrix_rows_64_with_behavior_columns": jax["controls"]["G1_64_rows_behavior_columns"]["pass"] is True,
        "fingerprint_ladder_complete": all(
            set(payload["fingerprint_ladder"]) == set(jax["fingerprint_ladder"]) for payload in payloads.values()
        )
        and jax["controls"]["G2_ladder_complete_with_verdicts"]["pass"] is True,
        "all_G1_G8_receipt_fields_present": all_gate_fields_present(jax),
        "commuting_and_noncommuting_controls_fired": jax["controls"]["G3_commuting_and_noncommuting_controls"]["pass"] is True,
        "erased_precedence_merge_control_fired": jax["controls"]["G4_erased_precedence_merge"]["pass"] is True,
        "axis4_axis6_orthogonality_control_fired": jax["controls"]["G5_axis4_axis6_orthogonality"]["pass"] is True,
        "z3_cvc5_load_bearing_smt_controls_fired": jax["controls"]["G6_load_bearing_smt"]["pass"] is True,
        "boundary_statement_present": jax["controls"]["G7_boundary_statement"]["pass"] is True,
        "honest_distinctness_present": jax["controls"]["G8_honest_distinctness"]["pass"] is True,
        "label_shuffle_control_fired": jax["controls"]["label_shuffle_control"]["pass"] is True,
        "tolerance_sensitivity_present": "FP_TOL_sensitivity" in jax["controls"],
        "trivial_f0_excluded_from_behavior": jax["controls"]["trivial_F0_control"]["pass"] is True,
        "pytorch_graph_lane_present": all(
            graph["torch_geometric_Data"]["num_nodes"] == 64 for graph in payloads["pytorch"]["collapse_graphs"].values()
        ),
        "julia_z3_noncomm_unsat_control_sat": julia_z3["verdict"] == "unsat"
        and julia_z3["erased_symmetrized_control_verdict"] == "sat",
    }
    all_pass = bool(all(controls.values()))
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "reads_peer_result": False,
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "all_pass": all_pass,
        "claim_under_test": "chart lattice of 64 cells as measured behavior rows plus degeneracy diagnostic ladder",
        "claim_ceiling": "scratch_diagnostic only; no axis-level admission, no Axis-6 earned doctrine claim, no engine/runtime closure, no IGT",
        "pin_block_canonical_json": next(iter(pin_strings)),
        "pin_block_sha256": next(iter(pin_hashes)),
        "source_reuse_lineage": {engine: payload["source_reuse_lineage"] for engine, payload in payloads.items()},
        "object_boundary": jax["object_boundary"],
        "pinned_state_validation": jax["pinned_state_validation"],
        "generic_state_sweep_pin": jax["generic_state_sweep_pin"],
        "engines": {
            "julia": engine_record(payloads["julia"], JULIA_RESULT),
            "jax": engine_record(payloads["jax"], JAX_RESULT),
            "pytorch": engine_record(payloads["pytorch"], PYTORCH_RESULT),
        },
        "matrix_rows": jax["matrix_rows"],
        "fingerprint_ladder": jax["fingerprint_ladder"],
        "collapse_classification_verdicts": jax["collapse_classification_verdicts"],
        "intended_degeneracy_candidates": jax["intended_degeneracy_candidates"],
        "f8_zero_gap_classes": jax.get("f8_zero_gap_classes", []),
        "superseded_intended_degeneracy_candidates": jax.get("superseded_intended_degeneracy_candidates", []),
        "erased_precedence_class_maps": jax["erased_precedence_class_maps"],
        "f6_result_note": jax["f6_result_note"],
        "hardening_batch": {
            "scope": "terrain_operator_precedence_64_matrix audit_verdict.md named gaps 1-5",
            "gap_1_erased_precedence_class_maps_path": "erased_precedence_class_maps",
            "gap_2_f8_relabel_path": "f8_zero_gap_classes",
            "gap_3_source_backed_choice": jax["source_backed_audit_choice"],
            "gap_4_julia_reuse_mode": payloads["julia"]["julia_reuse_mode"],
            "gap_5_f6_result_note_path": "f6_result_note",
        },
        "pytorch_collapse_graphs": payloads["pytorch"]["collapse_graphs"],
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_z3["verdict"],
                "erased_symmetrized_control_verdict": jax_z3["erased_symmetrized_control_verdict"],
                "computed_noncommuting_cell": jax_z3["computed_noncommuting_cell"],
                "computed_field": jax_z3["computed_field"],
                "delta_entries_scaled_from_matrix": jax_z3["delta_entries_scaled_from_matrix"],
                "asserted_precomputed_boolean": jax_z3["asserted_precomputed_boolean"],
                "proof_kind": jax_z3["proof_kind"],
                "boundary": jax_z3["boundary"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_cvc5["verdict"],
                "erased_symmetrized_control_verdict": jax_cvc5["erased_symmetrized_control_verdict"],
                "computed_noncommuting_cell": jax_cvc5["computed_noncommuting_cell"],
                "computed_field": jax_cvc5["computed_field"],
                "delta_entries_scaled_from_matrix": jax_cvc5["delta_entries_scaled_from_matrix"],
                "asserted_precomputed_boolean": jax_cvc5["asserted_precomputed_boolean"],
                "proof_kind": jax_cvc5["proof_kind"],
                "boundary": jax_cvc5["boundary"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "erased_symmetrized_control_verdict": julia_z3["erased_symmetrized_control_verdict"],
                "computed_noncommuting_cell": julia_z3["computed_noncommuting_cell"],
                "computed_field": julia_z3["computed_field"],
                "asserted_precomputed_boolean": julia_z3["asserted_precomputed_boolean"],
                "proof_kind": julia_z3["proof_kind"],
                "symbolic_derivation_in_solver": julia_z3["symbolic_derivation_in_solver"],
                "entry_binding_honesty_label": julia_z3["entry_binding_honesty_label"],
            },
        },
        "claim_path_tools": collect_claim_tools(payloads),
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {engine: payload["shared_scalars"] for engine, payload in payloads.items()},
            "comparison": comparison,
            "max_divergence": comparison["max_divergence"],
            "max_divergence_key": comparison["max_divergence_key"],
        },
        "build_gates": {key: value for key, value in jax["controls"].items() if key.startswith("G")},
        "controls": controls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "envelope": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "max_divergence": result["divergence"]["max_divergence"],
                "n_distinct": {family: receipt["n_distinct"] for family, receipt in result["fingerprint_ladder"].items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
