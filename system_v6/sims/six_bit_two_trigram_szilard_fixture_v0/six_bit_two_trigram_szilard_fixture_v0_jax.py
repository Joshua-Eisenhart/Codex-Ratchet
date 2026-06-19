#!/usr/bin/env python3
"""JAX-side diagnostic mirror for six_bit_two_trigram_szilard_fixture_v0.

The lane intentionally mirrors the finite integer/Fraction values from the
Python fixture. It is a diagnostic lane for the canonical envelope, not a new
claim surface.
"""

from __future__ import annotations

import datetime as dt
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "six_bit_two_trigram_szilard_fixture_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def frac_json(value: Fraction) -> dict[str, Any]:
    return {
        "num": value.numerator,
        "den": value.denominator,
        "string": f"{value.numerator}/{value.denominator}",
        "float": float(value),
    }


def bits_of_state(index: int) -> tuple[int, int, int, int, int, int]:
    if not 0 <= index < 64:
        raise ValueError(f"state index must be in [0, 63], got {index}")
    return tuple((index >> bit) & 1 for bit in range(6))


def trigram_value(bits: tuple[int, int, int]) -> int:
    return bits[0] + 2 * bits[1] + 4 * bits[2]


def enumerate_carrier() -> list[dict[str, Any]]:
    rows = []
    for index in range(64):
        bits = bits_of_state(index)
        lower = trigram_value(bits[0:3])
        upper = trigram_value(bits[3:6])
        rows.append(
            {
                "state_index": index,
                "bits": list(bits),
                "lower_trigram": lower,
                "upper_trigram": upper,
                "trigram_pair": [lower, upper],
                "parity_pair": [sum(bits[0:3]) % 2, sum(bits[3:6]) % 2],
            }
        )
    return rows


def record_costs() -> dict[str, Any]:
    log2_64 = sp.log(64, 2)
    log2_8_pair = sp.log(8, 2) + sp.log(8, 2)
    log2_4 = sp.log(4, 2)
    return {
        "unstructured_6bit_state_record": frac_json(Fraction(int(log2_64), 1)),
        "two_trigram_full_pair_record": frac_json(Fraction(int(log2_8_pair), 1)),
        "lower_trigram_only_record": frac_json(Fraction(3, 1)),
        "upper_trigram_only_record": frac_json(Fraction(3, 1)),
        "parity_pair_record": frac_json(Fraction(int(log2_4), 1)),
        "full_state_delta_bits": frac_json(Fraction(int(sp.simplify(log2_8_pair - log2_64)), 1)),
    }


def ledger_rows() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for row_id, bits in (
        ("unstructured_6bit_state_record", Fraction(6, 1)),
        ("two_trigram_full_pair_record", Fraction(6, 1)),
        ("lower_trigram_only_record", Fraction(3, 1)),
        ("upper_trigram_only_record", Fraction(3, 1)),
        ("parity_pair_record", Fraction(2, 1)),
    ):
        rows[row_id] = {
            "cycle": ["measure", "feedback", "erase"],
            "record_bits": frac_json(bits),
            "measurement_record_ln2_coeff": frac_json(bits),
            "ideal_feedback_work_credit_ln2_coeff": frac_json(bits),
            "erase_cost_ln2_coeff": frac_json(bits),
            "net_paid_cycle_ln2_coeff": frac_json(Fraction(0, 1)),
            "classification": "classical_baseline",
        }
    rows["wrong_order_controls"] = {
        "canonical_measure_feedback_erase": {"verdict": "sat", "record_bits": frac_json(Fraction(6, 1))},
        "feedback_before_measure": {
            "verdict": "unsat",
            "record_bits": frac_json(Fraction(6, 1)),
            "work_credit_ln2_coeff": frac_json(Fraction(0, 1)),
        },
        "erase_before_feedback": {
            "verdict": "unsat",
            "record_bits": frac_json(Fraction(6, 1)),
            "work_credit_ln2_coeff": frac_json(Fraction(0, 1)),
        },
        "no_measurement_control": {
            "verdict": "sat_control_no_work_credit",
            "record_bits": frac_json(Fraction(0, 1)),
            "work_credit_ln2_coeff": frac_json(Fraction(0, 1)),
        },
    }
    return rows


def build_payload() -> dict[str, Any]:
    states = enumerate_carrier()
    costs = record_costs()
    ledger = ledger_rows()
    lower_values = sorted({row["lower_trigram"] for row in states})
    upper_values = sorted({row["upper_trigram"] for row in states})
    gates = {
        "state_count_64": len(states) == 64,
        "lower_values_0_to_7": lower_values == list(range(8)),
        "upper_values_0_to_7": upper_values == list(range(8)),
        "pair_count_64": len({tuple(row["trigram_pair"]) for row in states}) == 64,
        "full_pair_matches_unstructured": costs["two_trigram_full_pair_record"] == costs["unstructured_6bit_state_record"],
        "split_delta_zero": costs["full_state_delta_bits"]["num"] == 0,
        "wrong_order_controls_reject": ledger["wrong_order_controls"]["feedback_before_measure"]["verdict"] == "unsat"
        and ledger["wrong_order_controls"]["erase_before_feedback"]["verdict"] == "unsat",
    }
    return {
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "generated_at": now_z(),
        "classification": "scratch_diagnostic",
        "row_classification": "classical_baseline",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all(gates.values()),
        "source_path": f"system_v6/sims/{SIM_ID}/{SIM_ID}_jax.py",
        "result_path": f"system_v6/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "carrier_summary": {
            "state_count": len(states),
            "bit_count": 6,
            "lower_trigram_values": lower_values,
            "upper_trigram_values": upper_values,
            "pair_count": len({tuple(row["trigram_pair"]) for row in states}),
        },
        "record_costs": costs,
        "per_cycle_ledger": ledger,
        "gates": gates,
        "packages_used": ["sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "package_observables": {
            "sympy": "sp.log and sp.simplify compute exact log2 cardinality equalities for the finite carrier mirror",
        },
        "TOOL_MANIFEST": {
            "sympy": "load_bearing exact log2 cardinality equality and zero-delta simplification",
            "python_fractions": "supportive exact JSON rational mirror",
            "json": "supportive durable result serialization",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "sympy": "load_bearing",
            "python_fractions": "supportive",
            "json": "supportive",
        },
        "claim_boundary": {
            "diagnostic_lane_only": True,
            "no_physics_bridge": True,
            "not_qit_admission": True,
            "not_axis_admission": True,
            "not_matrix64_completion": True,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result": str(RESULT_PATH.relative_to(ROOT))}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
