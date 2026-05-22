#!/usr/bin/env python3
"""Corrected cold-leg dominance successor for forward Carnot asymmetry."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Bounded successor for the forward Carnot asymmetric isotherm row. The "
    "source row falsified the hot-heavy closure prior; this receipt records the "
    "surviving cold-leg closure dominance as a corrected local variant without "
    "QIT, GStack, axis, or runtime promotion."
)

LEGO_IDS = ["stochastic_thermodynamics", "carnot_cycle", "finite_time_closure"]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads source sweep and writes corrected successor receipt"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values))


def main() -> None:
    source = load("carnot_asymmetric_isotherm_sweep_results.json")
    rows = source["rows"]
    hot_heavy = [row for row in rows if row["hot_steps"] > row["cold_steps"]]
    cold_heavy = [row for row in rows if row["cold_steps"] > row["hot_steps"]]
    balanced = [row for row in rows if row["cold_steps"] == row["hot_steps"]]

    hot_heavy_mean = mean([row["variance_mismatch_abs"] for row in hot_heavy])
    cold_heavy_mean = mean([row["variance_mismatch_abs"] for row in cold_heavy])
    best_hot_heavy = min(hot_heavy, key=lambda row: row["variance_mismatch_abs"])
    best_cold_heavy = min(cold_heavy, key=lambda row: row["variance_mismatch_abs"])
    best_balanced = min(balanced, key=lambda row: row["variance_mismatch_abs"])
    best_efficiency = min(rows, key=lambda row: row["efficiency_distance_to_carnot"])

    positive = {
        "cold_heavy_mean_closure_beats_hot_heavy_mean_closure": {
            "hot_heavy_mean_variance_mismatch": hot_heavy_mean,
            "cold_heavy_mean_variance_mismatch": cold_heavy_mean,
            "pass": cold_heavy_mean < hot_heavy_mean,
        },
        "best_cold_heavy_closure_beats_best_hot_heavy_closure": {
            "best_cold_heavy_variance_mismatch_abs": best_cold_heavy["variance_mismatch_abs"],
            "best_hot_heavy_variance_mismatch_abs": best_hot_heavy["variance_mismatch_abs"],
            "pass": best_cold_heavy["variance_mismatch_abs"] < best_hot_heavy["variance_mismatch_abs"],
        },
        "best_cold_heavy_closure_beats_best_balanced_closure": {
            "best_cold_heavy_variance_mismatch_abs": best_cold_heavy["variance_mismatch_abs"],
            "best_balanced_variance_mismatch_abs": best_balanced["variance_mismatch_abs"],
            "pass": best_cold_heavy["variance_mismatch_abs"] < best_balanced["variance_mismatch_abs"],
        },
        "forward_family_still_has_near_carnot_performance_candidate": {
            "best_efficiency_distance_to_carnot": best_efficiency["efficiency_distance_to_carnot"],
            "bound": 0.05,
            "pass": best_efficiency["efficiency_distance_to_carnot"] < 0.05,
        },
    }
    negative = {
        "original_hot_heavy_prior_is_killed": {
            "source_hot_heavy_check_pass": source["positive"]["hot_heavy_budget_beats_cold_heavy_budget_on_average_for_closure"][
                "pass"
            ],
            "source_cold_leg_insufficient_check_pass": source["negative"]["cold_leg_budget_alone_is_not_sufficient_to_close_the_cycle"][
                "pass"
            ],
            "pass": (
                source["positive"]["hot_heavy_budget_beats_cold_heavy_budget_on_average_for_closure"]["pass"] is False
                and source["negative"]["cold_leg_budget_alone_is_not_sufficient_to_close_the_cycle"]["pass"] is False
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
        "name": "carnot_forward_cold_leg_dominance_successor",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot_asymmetric_isotherm_sweep": str(RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json"),
            "carnot_asymmetric_direction_graveyard": str(
                RESULT_DIR / "carnot_asymmetric_direction_graveyard_results.json"
            ),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "hot_heavy_mean_variance_mismatch": hot_heavy_mean,
            "cold_heavy_mean_variance_mismatch": cold_heavy_mean,
            "best_hot_heavy_setting": {
                "hot_steps": best_hot_heavy["hot_steps"],
                "cold_steps": best_hot_heavy["cold_steps"],
                "variance_mismatch_abs": best_hot_heavy["variance_mismatch_abs"],
            },
            "best_cold_heavy_setting": {
                "hot_steps": best_cold_heavy["hot_steps"],
                "cold_steps": best_cold_heavy["cold_steps"],
                "variance_mismatch_abs": best_cold_heavy["variance_mismatch_abs"],
            },
            "best_efficiency_setting": {
                "hot_steps": best_efficiency["hot_steps"],
                "cold_steps": best_efficiency["cold_steps"],
                "efficiency_distance_to_carnot": best_efficiency["efficiency_distance_to_carnot"],
            },
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "carnot_forward_cold_leg_dominance_successor_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
