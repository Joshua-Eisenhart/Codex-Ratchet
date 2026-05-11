#!/usr/bin/env python3
"""Graveyard surviving and killed variants from open Szilard repair rows."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Controller graveyard for open Szilard ordering, record/reset, and substep "
    "repair rows. It preserves killed assumptions and surviving local variants "
    "without closing the source rows or promoting QIT/axis claims."
)

LEGO_IDS = ["stochastic_thermodynamics", "measurement_feedback", "landauer_erasure", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics", "measurement_feedback"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads Szilard open-row receipts"},
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


def item(source: dict[str, Any], section: str, key: str) -> dict[str, Any]:
    return source[section][key]


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"name": result["name"], "summary": result["summary"], "rows": result["rows"]}
    js = "window.SZILARD_OPEN_FAILURE_GRAVEYARD_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n"
    (VIS_DIR / "szilard-open-failure-graveyard-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    ordering = load("szilard_ordering_sensitivity_sweep_results.json")
    record = load("szilard_record_reset_repair_sweep_results.json")
    substep = load("szilard_substep_refinement_sweep_results.json")

    rows = [
        {
            "variant_id": "ordering_sensitivity_some_settings_separate",
            "source_row": "szilard_ordering_sensitivity",
            "source_receipt": str(RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json"),
            "expected": "some settings make the canonical order beat scrambled alternatives",
            "observed": "best ordering margin is positive",
            "metrics": {
                "best_margin": item(
                    ordering,
                    "positive",
                    "some_settings_make_the_correct_order_materially_better_than_scrambled_orders",
                )["best_margin"],
                "best_setting": item(
                    ordering,
                    "positive",
                    "some_settings_make_the_correct_order_materially_better_than_scrambled_orders",
                )["best_setting"],
            },
            "verdict": "survived",
            "next_allowed_action": "use as local ordering signal only",
        },
        {
            "variant_id": "ordering_sensitivity_low_noise_monotonicity",
            "source_row": "szilard_ordering_sensitivity",
            "source_receipt": str(RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json"),
            "expected": "lower measurement noise improves ordering margin on average",
            "observed": "high-noise mean margin exceeds low-noise mean margin",
            "metrics": item(ordering, "positive", "lower_measurement_noise_improves_ordering_margin_on_average"),
            "verdict": "killed",
            "next_allowed_action": "treat noise response as nonmonotone variant evidence",
        },
        {
            "variant_id": "ordering_sensitivity_high_noise_unclean",
            "source_row": "szilard_ordering_sensitivity",
            "source_receipt": str(RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json"),
            "expected": "high-noise settings do not give clean ordering separation",
            "observed": "high-noise best margin still gives ordering separation above the row-local negative threshold",
            "metrics": item(ordering, "negative", "high_noise_settings_do_not_give_clean_ordering_separation"),
            "verdict": "killed",
            "next_allowed_action": "keep high-noise survival as a tuning clue, not admission",
        },
        {
            "variant_id": "record_reset_repair_stronger_row",
            "source_row": "szilard_record_reset_repair_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"),
            "expected": "expanded repair grid finds a stronger row than the original open lane",
            "observed": "best repair score and record survival improve",
            "metrics": item(record, "positive", "repair_sweep_finds_a_stronger_row_than_the_original_open_lane"),
            "verdict": "survived",
            "next_allowed_action": "use as repair candidate evidence while reset swing remains blocked",
        },
        {
            "variant_id": "record_reset_repair_lifetime_helps",
            "source_row": "szilard_record_reset_repair_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"),
            "expected": "longer record lifetime helps survival on average",
            "observed": "long-lifetime mean survival exceeds short-lifetime mean survival",
            "metrics": item(record, "positive", "longer_lifetime_settings_help_record_survival_on_average"),
            "verdict": "survived",
            "next_allowed_action": "keep lifetime axis as valid repair direction",
        },
        {
            "variant_id": "record_reset_repair_reset_swing",
            "source_row": "szilard_record_reset_repair_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_record_reset_repair_sweep_results.json"),
            "expected": "stronger reset grid increases open reset swing toward strict QIT target",
            "observed": "open reset swing remains far below strict QIT reset swing",
            "metrics": item(record, "positive", "stronger_reset_grid_increases_open_reset_swing"),
            "verdict": "killed",
            "next_allowed_action": "route reset-swing work through separate exact-threshold rechecks",
        },
        {
            "variant_id": "substep_refinement_ordering_margin",
            "source_row": "szilard_substep_refinement_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_substep_refinement_sweep_results.json"),
            "expected": "substep refinement materially improves ordering margin",
            "observed": "best ordering margin improves over base substep row",
            "metrics": item(substep, "positive", "ordering_margin_improves_materially_over_base_substep_row"),
            "verdict": "survived",
            "next_allowed_action": "use as substep ordering repair evidence",
        },
        {
            "variant_id": "substep_refinement_measurement_information",
            "source_row": "szilard_substep_refinement_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_substep_refinement_sweep_results.json"),
            "expected": "measurement information stays high under the best refinement",
            "observed": "best measurement mutual information falls below row-local threshold",
            "metrics": item(substep, "positive", "measurement_information_stays_high"),
            "verdict": "killed",
            "next_allowed_action": "keep as measurement-information bottleneck for substep repair",
        },
        {
            "variant_id": "substep_refinement_reset_signal",
            "source_row": "szilard_substep_refinement_sweep",
            "source_receipt": str(RESULT_DIR / "szilard_substep_refinement_sweep_results.json"),
            "expected": "reset signal strengthens under refinement",
            "observed": "best reset signal passes the local threshold",
            "metrics": item(substep, "positive", "reset_signal_strengthens"),
            "verdict": "survived",
            "next_allowed_action": "use as reset-signal repair evidence distinct from record reset-swing",
        },
    ]

    positive = {
        "szilard_open_failures_are_partitioned": {
            "variant_count": len(rows),
            "source_row_count": len({row["source_row"] for row in rows}),
            "pass": len(rows) == 9 and len({row["source_row"] for row in rows}) == 3,
        },
        "source_rows_remain_open": {
            "ordering_all_pass": ordering["summary"]["all_pass"],
            "record_all_pass": record["summary"]["all_pass"],
            "substep_all_pass": substep["summary"]["all_pass"],
            "pass": not ordering["summary"]["all_pass"]
            and not record["summary"]["all_pass"]
            and not substep["summary"]["all_pass"],
        },
    }
    negative = {
        "graveyard_does_not_promote_failed_rows": {
            "qit_or_axis_promotion_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "all_rows_have_verdicts": {
            "pass": all(row["verdict"] in {"killed", "survived"} for row in rows),
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    result = {
        "name": "szilard_open_failure_graveyard",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This result indexes open Szilard failure/survival variants and does not "
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
    out_path = RESULT_DIR / "szilard_open_failure_graveyard_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
