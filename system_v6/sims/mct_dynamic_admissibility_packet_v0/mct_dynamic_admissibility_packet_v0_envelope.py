#!/usr/bin/env python3
"""Envelope for mct_dynamic_admissibility_packet_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "mct_dynamic_admissibility_packet_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
DISPOSITION_STATUS = "derived_default_under_current_doctrine"
PASS_CONDITION_DEFAULT = "non_isomorphic_diff"
SELF_LOOP_POLICY_DEFAULT = "retain"
COMMON_VALUE_KEYS = [
    "support_size",
    "q_without_phase",
    "q_with_phase",
    "phi_blind_pairs",
    "phase_separated_pairs",
    "max_order_gap_noncommuting",
    "max_order_gap_commuting",
    "full_relation_components",
    "ablated_relation_components",
    "sidecar_E3_erase",
    "sidecar_E3_retain",
    "z3_density_unsat",
    "cvc5_density_unsat",
]
REQUIRED_CONTROLS = [
    "drop-F01",
    "drop-N01",
    "wrong-order update",
    "invalid fold attempt",
    "relation-ablation",
    "local-only baseline",
    "product/null relation",
    "label-shuffle null",
    "commuting-pair zero-gap",
    "phase-probe-included control",
    "shell-nesting erasure",
    "fiber-coordinate erasure",
    "flat presentation-disagreement",
    "spherical presentation-disagreement",
    "ring presentation-disagreement",
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
        "axis0_status": payload["axis0_status"],
        "support_table_hash": payload["support_table_hash"],
        "pin_block_sha256": payload["pin_block_sha256"],
        "pin_block_extended_sha256": payload["pin_block_extended_sha256"],
        "pin_extended_from": payload["pin_extended_from"],
        "presentation_ids": payload["presentation_ids"],
        "gate_pass": payload["gate_pass"],
        "values": payload["values"],
        "chart_agreement_receipt": payload["chart_agreement_receipt"],
        "q_without_phase_computed_sheet": payload["q_without_phase_computed_sheet"],
        "sheet_sensitive_probe_receipt": payload["sheet_sensitive_probe_receipt"],
        "literal_table_diff": payload["literal_table_diff"],
        "non_isomorphic_diff": payload["non_isomorphic_diff"],
        "variant_ledger": payload["variant_ledger"],
        "controls_fired": {name: payload["controls"].get(name, {}).get("fired", False) for name in REQUIRED_CONTROLS},
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
        "comparison": {
            "common_observable_count": len(COMMON_VALUE_KEYS),
            "rows": rows,
            "same_named_observable_sets": True,
            "within_tolerance": max_div <= 1.0e-8,
        },
    }


def build_result() -> dict[str, Any]:
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    pin_strings = {payload["pin_block_canonical_json"] for payload in legs.values()}
    pin_hashes = {payload["pin_block_sha256"] for payload in legs.values()}
    extended_pin_strings = {payload["pin_block_extended_canonical_json"] for payload in legs.values()}
    extended_pin_hashes = {payload["pin_block_extended_sha256"] for payload in legs.values()}
    support_hashes = {payload["support_table_hash"] for payload in legs.values()}
    gate_names = {f"G{i}" for i in range(1, 9)}
    all_gates_present = all(gate_names <= set(payload["gates"].keys()) for payload in legs.values())
    all_gate_pass = all(all(payload["gate_pass"].get(gate, False) for gate in gate_names) for payload in legs.values())
    controls = {
        engine: {name: legs[engine]["controls"].get(name, {}) for name in REQUIRED_CONTROLS}
        for engine in legs
    }
    all_controls_fired = all(
        bool(legs[engine]["controls"].get(name, {}).get("fired", False))
        for engine in legs
        for name in REQUIRED_CONTROLS
    )
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["axis0_status"] == "readout_only_no_closure"
        for payload in legs.values()
    )
    pin_ok = len(pin_strings) == 1 and len(pin_hashes) == 1
    extended_pin_ok = len(extended_pin_strings) == 1 and len(extended_pin_hashes) == 1
    support_ok = len(support_hashes) == 1
    presentation_ok = len({json.dumps(payload["presentation_ids"], sort_keys=True) for payload in legs.values()}) == 1
    presentation_receipts_ok = all(
        len(payload["presentation_receipts"]["presentation_coordinate_receipts"]["flat"]) == 384
        and len(payload["presentation_receipts"]["presentation_coordinate_receipts"]["spherical_shell"]) == 384
        and len(payload["presentation_receipts"]["presentation_coordinate_receipts"]["nested_ring"]) == 384
        and payload["presentation_receipts"]["agreement_by_readout"]["all_presentations_same_support_count"]
        and payload["presentation_receipts"]["agreement_by_readout"]["all_presentations_same_adjacency_edge_count"]
        and payload["presentation_receipts"]["agreement_by_readout"]["all_presentations_same_axis0_rows"]
        and payload["presentation_receipts"]["agreement_by_readout"]["all_presentations_same_quotient_class_count"]
        and payload["presentation_receipts"]["agreement_by_readout"]["all_presentations_same_phi_blindness_density"]
        for payload in legs.values()
    )
    derived_defaults_ok = all(
        payload["owner_pending"]["self_loop_policy"] == SELF_LOOP_POLICY_DEFAULT
        and payload["owner_pending"]["pass_condition"] == PASS_CONDITION_DEFAULT
        and payload["owner_pending"]["disposition_status"] == DISPOSITION_STATUS
        and payload["owner_pending"]["status"] == "superseded_by_choice_point_dispositions"
        and payload["PIN_SPEC_EXTENDED"]["choice_points"]["self_loop_policy_default"] == SELF_LOOP_POLICY_DEFAULT
        and payload["PIN_SPEC_EXTENDED"]["choice_points"]["pass_condition"] == PASS_CONDITION_DEFAULT
        and payload["PIN_SPEC_EXTENDED"]["choice_points"]["self_loop_policy_disposition_status"] == DISPOSITION_STATUS
        and payload["PIN_SPEC_EXTENDED"]["choice_points"]["pass_condition_disposition_status"] == DISPOSITION_STATUS
        for payload in legs.values()
    )
    sidecar_ok = all(
        payload["values"]["sidecar_E3_erase"] == 4.0 and payload["values"]["sidecar_E3_retain"] == 8.0
        for payload in legs.values()
    )
    lr_separable = all(
        any(row["P_chirality"] == 1 for row in payload["probe_row_table"])
        and any(row["P_chirality"] == -1 for row in payload["probe_row_table"])
        for payload in legs.values()
    )
    chart_agreement_ok = all(payload["chart_agreement_receipt"]["agreement"] and payload["chart_agreement_receipt"]["divergence"] == [] for payload in legs.values())
    computed_sheet_probe_ok = all(
        payload["sheet_sensitive_probe_receipt"]["matched_LR_pairs_with_distinct_dynamic_gap"] == 192
        and payload["q_without_phase_computed_sheet"] == payload["sheet_sensitive_probe_receipt"]["q_without_phase_computed_sheet"]
        and payload["sheet_sensitive_probe_receipt"]["P_chirality_metadata"] == "label_transcription"
        for payload in legs.values()
    )
    distinct_commuting_ok = all(
        payload["controls"]["commuting-pair zero-gap"]["distinct_commuting_control"]["zero_gap_pass"]
        and payload["controls"]["commuting-pair zero-gap"]["noncommuting_flip_partner"]["nonzero_gap_pass"]
        and payload["controls"]["commuting-pair zero-gap"]["legacy_self_pair_diagnostic"]["max_gap"] == payload["values"]["max_order_gap_commuting"]
        for payload in legs.values()
    )
    ratchet_diff_ok = all(
        payload["literal_table_diff"]["computed"]
        and payload["literal_table_diff"]["pass_condition"] == PASS_CONDITION_DEFAULT
        and payload["literal_table_diff"]["pass_condition_disposition_status"] == DISPOSITION_STATUS
        and payload["non_isomorphic_diff"]["computed"]
        and payload["non_isomorphic_diff"]["pass_condition"] == PASS_CONDITION_DEFAULT
        and payload["non_isomorphic_diff"]["pass_condition_disposition_status"] == DISPOSITION_STATUS
        for payload in legs.values()
    )
    variant_ledger_ok = all(
        payload["variant_ledger"]["Var_t"]["active_variant"] == "nested_hopf_tori_finite_support"
        and payload["variant_ledger"]["ring_checkerboard_live_readings_conflict_note"]["status"] == "preserved_open_conflict"
        for payload in legs.values()
    )
    smt_ok = (
        legs["jax"]["crossover_proofs"]["z3"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["verdict"] == "unsat"
        and legs["jax"]["crossover_proofs"]["z3"]["phase_probe_injected_control"] == "sat"
        and legs["jax"]["crossover_proofs"]["cvc5"]["phase_probe_injected_control"] == "sat"
        and legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
    )
    div = divergence(legs)
    all_pass = all(
        [
            all(payload["all_pass"] for payload in legs.values()),
            all_gates_present,
            all_gate_pass,
            all_controls_fired,
            ceiling_ok,
            pin_ok,
            extended_pin_ok,
            support_ok,
            presentation_ok,
            presentation_receipts_ok,
            derived_defaults_ok,
            sidecar_ok,
            lr_separable,
            chart_agreement_ok,
            computed_sheet_probe_ok,
            distinct_commuting_ok,
            ratchet_diff_ok,
            variant_ledger_ok,
            smt_ok,
            div["comparison"]["within_tolerance"],
        ]
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "jax", "cvc5", "torch", "torch_geometric"],
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "crossover_proofs": {
            "z3": legs["jax"]["crossover_proofs"]["z3"],
            "cvc5": legs["jax"]["crossover_proofs"]["cvc5"],
            "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": div,
        "packet_receipt": {
            "pin_blocks_byte_identical": pin_ok,
            "pin_block_sha256": sorted(pin_hashes)[0],
            "pin_block_extended_byte_identical": extended_pin_ok,
            "pin_block_extended_sha256": sorted(extended_pin_hashes)[0],
            "pin_extended_from": legs["julia"]["pin_extended_from"],
            "support_table_hash_match": support_ok,
            "support_table_hash": sorted(support_hashes)[0],
            "presentation_ids_match": presentation_ok,
            "presentation_coordinate_receipts_emitted": presentation_receipts_ok,
            "axis0_status": "readout_only_no_closure",
            "derived_default_dispositions_emitted": derived_defaults_ok,
            "sidecar_fixture_E3_erase_retain": sidecar_ok,
            "lr_sheets_separable_by_P_chirality": lr_separable,
            "lr_sheets_separable_by_computed_P_weyl_gap": computed_sheet_probe_ok,
            "chart_agreement_receipts_emitted": chart_agreement_ok,
            "distinct_pair_commuting_control_emitted": distinct_commuting_ok,
            "ratchet_diff_receipts_emitted": ratchet_diff_ok,
            "variant_ledger_emitted": variant_ledger_ok,
            "all_gates_present": all_gates_present,
            "all_gates_pass": all_gate_pass,
            "all_controls_fired": all_controls_fired,
            "ceiling_ok": ceiling_ok,
            "smt_phi_blindness_ok": smt_ok,
        },
        "gate_summary": {engine: legs[engine]["gate_pass"] for engine in legs},
        "controls": controls,
        "pin_block_canonical_json": next(iter(pin_strings)),
        "pin_block_extended_canonical_json": next(iter(extended_pin_strings)),
        "pin_block_extended_sha256": sorted(extended_pin_hashes)[0],
        "pin_extended_from": legs["julia"]["pin_extended_from"],
        "PIN_SPEC": legs["julia"]["PIN_SPEC"],
        "PIN_SPEC_EXTENDED": legs["julia"]["PIN_SPEC_EXTENDED"],
        "source_refs": legs["julia"]["source_refs"],
        "chart_agreement_receipts": {engine: legs[engine]["chart_agreement_receipt"] for engine in legs},
        "sheet_sensitive_probe_receipts": {engine: legs[engine]["sheet_sensitive_probe_receipt"] for engine in legs},
        "q_without_phase_computed_sheet": {engine: legs[engine]["q_without_phase_computed_sheet"] for engine in legs},
        "presentation_receipts": {engine: legs[engine]["presentation_receipts"] for engine in legs},
        "literal_table_diff": {engine: legs[engine]["literal_table_diff"] for engine in legs},
        "non_isomorphic_diff": {engine: legs[engine]["non_isomorphic_diff"] for engine in legs},
        "variant_ledger": {engine: legs[engine]["variant_ledger"] for engine in legs},
        "ring_checkerboard_live_readings_conflict_note": legs["julia"]["ring_checkerboard_live_readings_conflict_note"],
        "out_of_scope_recommendations": [
            "Add a future validator rule for self-pair commuting controls, missing presentation coordinate receipts, missing literal_table_diff/non_isomorphic_diff, and missing Var_t ledger; not edited in this hardening batch."
        ],
        "values": {
            "support_size": legs["julia"]["values"]["support_size"],
            "q_without_phase": legs["julia"]["values"]["q_without_phase"],
            "q_with_phase": legs["julia"]["values"]["q_with_phase"],
            "phi_blind_pairs": legs["julia"]["values"]["phi_blind_pairs"],
            "phase_separated_pairs": legs["julia"]["values"]["phase_separated_pairs"],
            "max_order_gap_noncommuting": legs["julia"]["values"]["max_order_gap_noncommuting"],
            "max_order_gap_commuting": legs["julia"]["values"]["max_order_gap_commuting"],
            "full_relation_components": legs["julia"]["values"]["full_relation_components"],
            "ablated_relation_components": legs["julia"]["values"]["ablated_relation_components"],
            "sidecar_E3_erase": legs["julia"]["values"]["sidecar_E3_erase"],
            "sidecar_E3_retain": legs["julia"]["values"]["sidecar_E3_retain"],
            "z3_density_unsat": legs["julia"]["values"]["z3_density_unsat"],
            "cvc5_density_unsat": legs["julia"]["values"]["cvc5_density_unsat"],
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "MCT_DYNAMIC_ADMISSIBILITY_PACKET_V0_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"pin_match={str(result['packet_receipt']['pin_blocks_byte_identical']).lower()} "
        f"support_match={str(result['packet_receipt']['support_table_hash_match']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
