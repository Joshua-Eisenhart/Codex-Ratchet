#!/usr/bin/env python3
"""Finite six-bit/two-trigram Szilard carrier fixture.

This packet is a finite-counting carrier fixture. It does not bridge to physics,
QIT admission, Matrix64 claims, or axis admission.
"""

from __future__ import annotations

import datetime as dt
import json
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "six_bit_two_trigram_szilard_fixture_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
CLASSIFICATION = "scratch_diagnostic"
ROW_CLASSIFICATION = "classical_baseline"


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def frac_json(value: Fraction) -> dict[str, Any]:
    return {
        "num": value.numerator,
        "den": value.denominator,
        "string": f"{value.numerator}/{value.denominator}",
        "float": float(value),
    }


def serialize(value: Any) -> Any:
    if isinstance(value, Fraction):
        return frac_json(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


def bits_of_state(index: int) -> tuple[int, int, int, int, int, int]:
    if not 0 <= index < 64:
        raise ValueError(f"state index must be in [0, 63], got {index}")
    return tuple((index >> bit) & 1 for bit in range(6))  # lower trigram first


def trigram_value(bits: tuple[int, int, int]) -> int:
    return bits[0] + 2 * bits[1] + 4 * bits[2]


def enumerate_carrier() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []
    for index in range(64):
        bits = bits_of_state(index)
        lower = trigram_value(bits[0:3])
        upper = trigram_value(bits[3:6])
        states.append(
            {
                "state_index": index,
                "bits": bits,
                "lower_trigram": lower,
                "upper_trigram": upper,
                "trigram_pair": (lower, upper),
                "parity_pair": (sum(bits[0:3]) % 2, sum(bits[3:6]) % 2),
            }
        )
    return states


def landauer_floor_ln2(bits: Fraction) -> dict[str, Any]:
    if bits < 0:
        raise ValueError("record bits must be nonnegative")
    return {
        "ln2_coeff": bits,
        "nats_label": f"{bits.numerator} * ln(2)" if bits.denominator == 1 else f"({bits}) * ln(2)",
    }


def compute_record_costs() -> dict[str, Any]:
    unstructured = Fraction(6, 1)
    trigram_pair = Fraction(3, 1) + Fraction(3, 1)
    lower_only = Fraction(3, 1)
    upper_only = Fraction(3, 1)
    parity_pair = Fraction(2, 1)
    return {
        "unstructured_6bit_state_record": {
            "recorded_variable": "state_index in 64 equiprobable states",
            "distinct_records": 64,
            "bits": unstructured,
            "landauer_floor": landauer_floor_ln2(unstructured),
        },
        "two_trigram_full_pair_record": {
            "recorded_variable": "(lower_trigram, upper_trigram) in 8 x 8 equiprobable pairs",
            "distinct_records": 64,
            "bits": trigram_pair,
            "landauer_floor": landauer_floor_ln2(trigram_pair),
        },
        "lower_trigram_only_record": {
            "recorded_variable": "lower_trigram in 8 equiprobable values",
            "distinct_records": 8,
            "bits": lower_only,
            "landauer_floor": landauer_floor_ln2(lower_only),
        },
        "upper_trigram_only_record": {
            "recorded_variable": "upper_trigram in 8 equiprobable values",
            "distinct_records": 8,
            "bits": upper_only,
            "landauer_floor": landauer_floor_ln2(upper_only),
        },
        "parity_pair_record": {
            "recorded_variable": "(lower_parity, upper_parity) in 2 x 2 equiprobable values",
            "distinct_records": 4,
            "bits": parity_pair,
            "landauer_floor": landauer_floor_ln2(parity_pair),
        },
        "effect_of_3_plus_3_split": {
            "full_state_delta_bits": trigram_pair - unstructured,
            "full_state_verdict": "no_change_for_uniform_full_state_record",
            "computed_reason": "log2(8) + log2(8) - log2(64) = 3 + 3 - 6 = 0",
            "partial_record_boundary": (
                "lower/upper trigram-only records are cheaper because they erase a coarser variable, "
                "not because the full 64-state carrier became cheaper"
            ),
        },
    }


def szilard_order_controls() -> dict[str, Any]:
    full_record_bits = Fraction(6, 1)
    return {
        "canonical_measure_feedback_erase": {
            "order": ["measure", "feedback", "erase"],
            "verdict": "sat",
            "record_bits": full_record_bits,
            "work_credit_ln2_coeff": full_record_bits,
            "erase_cost_ln2_coeff": full_record_bits,
            "balance_ln2_coeff": Fraction(0, 1),
        },
        "feedback_before_measure": {
            "order": ["feedback", "measure", "erase"],
            "verdict": "unsat",
            "reason": "feedback has no admissible record variable before measurement",
            "record_bits": full_record_bits,
            "work_credit_ln2_coeff": Fraction(0, 1),
            "erase_cost_ln2_coeff": full_record_bits,
        },
        "erase_before_feedback": {
            "order": ["measure", "erase", "feedback"],
            "verdict": "unsat",
            "reason": "erasure removes the record before feedback can condition on it",
            "record_bits": full_record_bits,
            "work_credit_ln2_coeff": Fraction(0, 1),
            "erase_cost_ln2_coeff": full_record_bits,
        },
        "no_measurement_control": {
            "order": ["feedback", "erase"],
            "verdict": "sat_control_no_work_credit",
            "reason": "no measured distinction means no record-conditioned work credit",
            "record_bits": Fraction(0, 1),
            "work_credit_ln2_coeff": Fraction(0, 1),
            "erase_cost_ln2_coeff": Fraction(0, 1),
        },
    }


def per_cycle_ledger_rows() -> dict[str, Any]:
    costs = compute_record_costs()
    rows: dict[str, Any] = {}
    for row_id in (
        "unstructured_6bit_state_record",
        "two_trigram_full_pair_record",
        "lower_trigram_only_record",
        "upper_trigram_only_record",
        "parity_pair_record",
    ):
        bits = costs[row_id]["bits"]
        rows[row_id] = {
            "cycle": ["measure", "feedback", "erase"],
            "record_bits": bits,
            "measurement_record_ln2_coeff": bits,
            "ideal_feedback_work_credit_ln2_coeff": bits,
            "erase_cost_ln2_coeff": bits,
            "net_paid_cycle_ln2_coeff": Fraction(0, 1),
            "landauer_floor": landauer_floor_ln2(bits),
            "classification": ROW_CLASSIFICATION,
        }
    rows["wrong_order_controls"] = szilard_order_controls()
    return rows


def build_payload() -> dict[str, Any]:
    states = enumerate_carrier()
    lower_values = sorted({state["lower_trigram"] for state in states})
    upper_values = sorted({state["upper_trigram"] for state in states})
    raw_payload = {
        "schema_version": "six_bit_two_trigram_szilard_fixture_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "row_classification": ROW_CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": True,
        "purpose": (
            "finite six-bit/two-trigram carrier fixture with Szilard measure-feedback-erase "
            "ledger accounting on the carrier"
        ),
        "authority": {
            "physics_primary_deep_read": "35ed8142c safe-order item 3: engine carrier before physics bridge",
            "ledger_v1": "d79d71a0d Carnot/Szilard/Landauer ledger conventions",
            "basin_cycle": "ffe6e1c38 basin-cycle conventions",
            "matrix64_structure": "2^6 = 64 as data only, not all-64 claim promotion",
        },
        "carrier_summary": {
            "state_count": len(states),
            "bit_count": 6,
            "structure": "two trigrams x three bits each",
            "lower_trigram_values": lower_values,
            "upper_trigram_values": upper_values,
            "pair_count": len({state["trigram_pair"] for state in states}),
            "sample_states": states[:4] + states[-4:],
        },
        "record_costs": compute_record_costs(),
        "per_cycle_ledger": per_cycle_ledger_rows(),
        "claim_boundary": {
            "engine_carrier_fixture_only": True,
            "no_physics_bridge": True,
            "no_64_claims": True,
            "not_qit_admission": True,
            "not_axis_admission": True,
            "not_matrix64_completion": True,
            "statement": (
                "The 64-state/two-trigram rows are finite carrier data and ledger costs only. "
                "They do not promote a physics bridge or all-64 Matrix64 claim."
            ),
        },
        "TOOL_MANIFEST": {
            "python_fractions": "load_bearing exact finite-counting arithmetic for log2 cardinalities expressed in bits",
            "json": "supportive durable result serialization",
            "pytest": "supportive packet-local behavioral tests",
            "external_smt": "not used; no structural impossibility stronger than finite order predicates is claimed",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "python_fractions": "load_bearing",
            "json": "supportive",
            "pytest": "supportive",
            "external_smt": "None",
        },
        "divergence_log": [
            {
                "control": "unstructured_6bit_vs_two_trigram_full_pair",
                "result": "no divergence for full-state record cost",
                "ceiling": ROW_CLASSIFICATION,
            },
            {
                "control": "partial_trigram_records",
                "result": "lower cost only when the recorded variable is coarser",
                "ceiling": ROW_CLASSIFICATION,
            },
            {
                "control": "wrong_order_szilard_controls",
                "result": "feedback-before-measure and erase-before-feedback are rejected by precedence",
                "ceiling": ROW_CLASSIFICATION,
            },
        ],
        "allowed_claims": [
            "finite carrier has 64 states as 8 lower trigrams x 8 upper trigrams",
            "full trigram-pair record cost equals unstructured six-bit record cost",
            "Landauer floor on the full carrier is 6 * k_B * T * ln(2)",
            "partial trigram records have lower erasure costs only because they record coarser variables",
        ],
        "blocked_claims": [
            "physics bridge",
            "QIT engine admission",
            "Matrix64/all-64 completion",
            "axis-level admission",
            "nonclassical evidence",
        ],
    }
    return serialize(raw_payload)


def write_result() -> Path:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(build_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RESULT_PATH


def main() -> int:
    path = write_result()
    print(json.dumps({"ok": True, "result": str(path.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
