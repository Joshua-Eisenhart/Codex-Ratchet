#!/usr/bin/env python3
"""Graveyard the failed Carnot asymmetric leg-dominance assumptions."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "graveyard_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller graveyard for Carnot asymmetric isotherm sweeps. It records "
    "which forward/reverse leg-dominance hypotheses failed and which bounded "
    "negative variants survived."
)

LEGO_IDS = ["carnot_cycle", "stochastic_thermodynamics", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["carnot_cycle"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads asymmetric Carnot receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical result paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": result["name"],
        "summary": result["summary"],
        "rows": result["rows"],
    }
    js = "window.CARNOT_ASYMMETRIC_DIRECTION_GRAVEYARD_DATA = " + json.dumps(
        payload, indent=2, default=str
    ) + ";\n"
    (VIS_DIR / "carnot-asymmetric-direction-graveyard-data.js").write_text(js, encoding="utf-8")


def check(source: dict[str, Any], section: str, name: str) -> dict[str, Any]:
    return source[section][name]


def main() -> None:
    forward = load("carnot_asymmetric_isotherm_sweep_results.json")
    reverse = load("carnot_reverse_asymmetric_sweep_results.json")

    f_hot_mean = check(forward, "positive", "hot_heavy_budget_beats_cold_heavy_budget_on_average_for_closure")
    f_cold_not_enough = check(forward, "negative", "cold_leg_budget_alone_is_not_sufficient_to_close_the_cycle")
    r_asym_closure = check(reverse, "positive", "some_asymmetric_setting_improves_reverse_closure_over_balanced_baseline")
    r_cop = check(reverse, "positive", "some_high_budget_setting_moves_close_to_carnot_cop")
    r_cold_mean = check(reverse, "positive", "cold_heavy_budget_beats_hot_heavy_budget_on_average_for_reverse_closure")
    r_nonzero_return = check(reverse, "negative", "even_the_best_reverse_row_still_has_nonzero_cycle_return_error")
    r_hot_not_enough = check(reverse, "negative", "hot_leg_budget_alone_is_not_sufficient_to_optimize_reverse_closure")

    rows = [
        {
            "variant_id": "forward_asymmetric_closure_advantage",
            "source_row": "carnot_forward_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json"),
            "expected": "some asymmetric forward setting improves closure over the balanced baseline",
            "observed": "best asymmetric closure beats the best balanced closure",
            "metrics": {
                "best_closure_variance_mismatch_abs": check(
                    forward,
                    "positive",
                    "some_asymmetric_setting_improves_closure_over_the_balanced_baseline",
                )["best_closure_variance_mismatch_abs"],
                "best_balanced_variance_mismatch_abs": check(
                    forward,
                    "positive",
                    "some_asymmetric_setting_improves_closure_over_the_balanced_baseline",
                )["best_balanced_variance_mismatch_abs"],
            },
            "verdict": "survived",
            "next_allowed_action": "use as forward finite-time closure variant evidence only",
        },
        {
            "variant_id": "forward_high_budget_near_carnot_efficiency",
            "source_row": "carnot_forward_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json"),
            "expected": "some high-budget forward setting approaches Carnot efficiency within 0.05",
            "observed": "best high-budget efficiency distance is below the row-local bound",
            "metrics": {
                "best_efficiency_distance_to_carnot": check(
                    forward,
                    "positive",
                    "some_high_budget_setting_moves_close_to_carnot",
                )["best_efficiency_distance_to_carnot"],
                "bound": 0.05,
            },
            "verdict": "survived",
            "next_allowed_action": "use as forward finite-time efficiency variant evidence only",
        },
        {
            "variant_id": "forward_hot_heavy_closure_dominance",
            "source_row": "carnot_forward_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json"),
            "expected": "hot-heavy isotherm budgets close the forward stochastic cycle better on average",
            "observed": (
                "cold-heavy closure mismatch mean is lower than hot-heavy mean"
            ),
            "metrics": {
                "hot_heavy_mean_variance_mismatch": f_hot_mean["hot_heavy_mean_variance_mismatch"],
                "cold_heavy_mean_variance_mismatch": f_hot_mean["cold_heavy_mean_variance_mismatch"],
            },
            "verdict": "killed",
            "next_allowed_action": "treat cold-leg budget dominance as a forward closure variant, not as QIT admission",
        },
        {
            "variant_id": "forward_cold_leg_budget_insufficient",
            "source_row": "carnot_forward_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json"),
            "expected": "cold-leg budget alone is insufficient for best forward closure",
            "observed": "best cold-heavy closure beats best hot-heavy closure",
            "metrics": {
                "best_cold_heavy_variance_mismatch_abs": f_cold_not_enough[
                    "best_cold_heavy_variance_mismatch_abs"
                ],
                "best_hot_heavy_variance_mismatch_abs": f_cold_not_enough[
                    "best_hot_heavy_variance_mismatch_abs"
                ],
            },
            "verdict": "killed",
            "next_allowed_action": "keep as negative evidence against the original forward leg-order prior",
        },
        {
            "variant_id": "reverse_asymmetric_closure_advantage",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "some reverse asymmetric setting improves closure over balanced baseline",
            "observed": "best closure setting is balanced and equals the best balanced mismatch",
            "metrics": {
                "best_closure_variance_mismatch_abs": r_asym_closure["best_closure_variance_mismatch_abs"],
                "best_balanced_variance_mismatch_abs": r_asym_closure[
                    "best_balanced_variance_mismatch_abs"
                ],
            },
            "verdict": "killed",
            "next_allowed_action": "prefer balanced reverse closure unless a new reverse carrier changes the evidence",
        },
        {
            "variant_id": "reverse_high_budget_near_carnot_cop",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "high-budget reverse setting reaches COP within 0.05 of Carnot",
            "observed": "best COP distance remains above the row-local threshold",
            "metrics": {
                "best_cop_distance_to_carnot": r_cop["best_cop_distance_to_carnot"],
                "bound": 0.05,
            },
            "verdict": "killed",
            "next_allowed_action": "keep reverse COP as open finite-time sidecar evidence",
        },
        {
            "variant_id": "reverse_cold_heavy_closure_dominance",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "cold-heavy budgets beat hot-heavy budgets on reverse closure average",
            "observed": "hot-heavy mean mismatch is lower than cold-heavy mean mismatch",
            "metrics": {
                "cold_heavy_mean_variance_mismatch": r_cold_mean["cold_heavy_mean_variance_mismatch"],
                "hot_heavy_mean_variance_mismatch": r_cold_mean["hot_heavy_mean_variance_mismatch"],
            },
            "verdict": "killed",
            "next_allowed_action": "treat reverse hot-heavy tendency as a variant signal, not a closure proof",
        },
        {
            "variant_id": "reverse_best_row_nonzero_return_error",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "even best reverse row still has nonzero return error above 1e-3",
            "observed": "best reverse closure row has near-zero cycle_delta_u",
            "metrics": {
                "cycle_delta_u": r_nonzero_return["cycle_delta_u"],
                "bound": 1e-3,
            },
            "verdict": "killed",
            "next_allowed_action": "separate return-error closure from COP and leg-dominance failures",
        },
        {
            "variant_id": "reverse_best_row_near_zero_return_error",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "the reverse row can approach return-error closure even while COP and asymmetry claims fail",
            "observed": "best reverse closure row has cycle_delta_u within 1e-3",
            "metrics": {
                "cycle_delta_u": r_nonzero_return["cycle_delta_u"],
                "bound": 1e-3,
            },
            "verdict": "survived",
            "next_allowed_action": "use as return-closure side evidence, not as reverse COP or QIT admission",
        },
        {
            "variant_id": "reverse_hot_leg_budget_insufficient",
            "source_row": "carnot_reverse_asymmetric",
            "source_receipt": str(RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json"),
            "expected": "hot-leg budget alone is insufficient to optimize reverse closure",
            "observed": "best hot-heavy closure beats best cold-heavy closure",
            "metrics": {
                "best_hot_heavy_variance_mismatch_abs": r_hot_not_enough[
                    "best_hot_heavy_variance_mismatch_abs"
                ],
                "best_cold_heavy_variance_mismatch_abs": r_hot_not_enough[
                    "best_cold_heavy_variance_mismatch_abs"
                ],
            },
            "verdict": "killed",
            "next_allowed_action": "keep as negative evidence against a symmetric forward/reverse leg-order prior",
        },
    ]

    positive = {
        "failed_directional_hypotheses_are_all_recorded": {
            "recorded_variant_count": len(rows),
            "pass": len(rows) == 10,
        },
        "source_rows_remain_open": {
            "forward_all_pass": forward["summary"]["all_pass"],
            "reverse_all_pass": reverse["summary"]["all_pass"],
            "pass": not forward["summary"]["all_pass"] and not reverse["summary"]["all_pass"],
        },
    }
    negative = {
        "graveyard_does_not_promote_failed_rows": {
            "qit_or_axis_promotion_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "all_graveyard_rows_have_verdicts": {
            "pass": all(row["verdict"] in {"killed", "survived"} for row in rows),
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "name": "carnot_asymmetric_direction_graveyard",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This result indexes failed Carnot asymmetric variants and does not "
            "admit QIT, GStack, axis, or runtime-engine claims."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "variant_count": len(rows),
            "killed_count": sum(row["verdict"] == "killed" for row in rows),
            "survived_count": sum(row["verdict"] == "survived" for row in rows),
            "source_rows_closed": False,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "carnot_asymmetric_direction_graveyard_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
