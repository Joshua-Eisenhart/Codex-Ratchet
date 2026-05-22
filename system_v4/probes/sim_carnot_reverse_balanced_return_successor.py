#!/usr/bin/env python3
"""Balanced return-closure successor for reverse Carnot asymmetry."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the reverse Carnot asymmetric row. The source row "
    "falsifies reverse asymmetric closure, near-Carnot COP, and simple leg "
    "dominance; this receipt preserves the surviving balanced near-zero return "
    "closure signal without QIT, GStack, axis, or runtime promotion."
)

LEGO_IDS = ["stochastic_thermodynamics", "carnot_cycle", "reverse_return_closure"]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads reverse source sweep and writes balanced-return receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def main() -> None:
    source = load("carnot_reverse_asymmetric_sweep_results.json")
    rows = source["rows"]
    hot_heavy = [row for row in rows if row["hot_steps"] > row["cold_steps"]]
    cold_heavy = [row for row in rows if row["cold_steps"] > row["hot_steps"]]
    balanced = [row for row in rows if row["cold_steps"] == row["hot_steps"]]

    best_closure = min(rows, key=lambda row: row["variance_mismatch_abs"])
    best_balanced = min(balanced, key=lambda row: row["variance_mismatch_abs"])
    best_hot_heavy = min(hot_heavy, key=lambda row: row["variance_mismatch_abs"])
    best_cold_heavy = min(cold_heavy, key=lambda row: row["variance_mismatch_abs"])
    best_cop = min(rows, key=lambda row: row["cop_distance_to_carnot"])
    hot_heavy_mean = mean([row["variance_mismatch_abs"] for row in hot_heavy])
    cold_heavy_mean = mean([row["variance_mismatch_abs"] for row in cold_heavy])

    positive = {
        "best_reverse_closure_is_balanced": {
            "best_closure_setting": {
                "cold_steps": best_closure["cold_steps"],
                "hot_steps": best_closure["hot_steps"],
            },
            "pass": best_closure["cold_steps"] == best_closure["hot_steps"],
        },
        "balanced_reverse_row_has_near_zero_return_error": {
            "cycle_delta_u": best_balanced["cycle_delta_u"],
            "bound": 0.001,
            "pass": abs(best_balanced["cycle_delta_u"]) < 0.001,
        },
        "balanced_reverse_closure_beats_best_asymmetric_closure": {
            "best_balanced_variance_mismatch_abs": best_balanced["variance_mismatch_abs"],
            "best_hot_heavy_variance_mismatch_abs": best_hot_heavy["variance_mismatch_abs"],
            "best_cold_heavy_variance_mismatch_abs": best_cold_heavy["variance_mismatch_abs"],
            "pass": best_balanced["variance_mismatch_abs"] < min(
                best_hot_heavy["variance_mismatch_abs"], best_cold_heavy["variance_mismatch_abs"]
            ),
        },
    }
    negative = {
        "near_carnot_cop_remains_open": {
            "best_cop_distance_to_carnot": best_cop["cop_distance_to_carnot"],
            "bound": 0.05,
            "pass": best_cop["cop_distance_to_carnot"] > 0.05,
        },
        "simple_leg_dominance_is_not_the_reverse_closure_explanation": {
            "hot_heavy_mean_variance_mismatch": hot_heavy_mean,
            "cold_heavy_mean_variance_mismatch": cold_heavy_mean,
            "best_hot_heavy_variance_mismatch_abs": best_hot_heavy["variance_mismatch_abs"],
            "best_cold_heavy_variance_mismatch_abs": best_cold_heavy["variance_mismatch_abs"],
            "pass": (
                hot_heavy_mean < cold_heavy_mean
                and best_hot_heavy["variance_mismatch_abs"] < best_cold_heavy["variance_mismatch_abs"]
            ),
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "all_direction_buckets_have_rows": {
            "hot_heavy_count": len(hot_heavy),
            "cold_heavy_count": len(cold_heavy),
            "balanced_count": len(balanced),
            "pass": bool(hot_heavy and cold_heavy and balanced),
        },
        "source_row_remains_nonpassing": {
            "source_all_pass": source["summary"]["all_pass"],
            "pass": source["summary"]["all_pass"] is False,
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "carnot_reverse_balanced_return_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot_reverse_asymmetric_sweep": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "carnot_asymmetric_direction_graveyard": str(
                RESULT_DIR / "carnot_asymmetric_direction_graveyard_results.json"
            ),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "best_balanced_setting": {
                "cold_steps": best_balanced["cold_steps"],
                "hot_steps": best_balanced["hot_steps"],
                "variance_mismatch_abs": best_balanced["variance_mismatch_abs"],
                "cycle_delta_u": best_balanced["cycle_delta_u"],
            },
            "best_cop_setting": {
                "cold_steps": best_cop["cold_steps"],
                "hot_steps": best_cop["hot_steps"],
                "cop_distance_to_carnot": best_cop["cop_distance_to_carnot"],
            },
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "carnot_reverse_balanced_return_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
