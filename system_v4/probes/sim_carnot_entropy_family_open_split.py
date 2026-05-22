#!/usr/bin/env python3
"""Open-carrier readout split for the Carnot entropy-family row."""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "diagnostic_only"
classification = CLASSIFICATION
divergence_log = (
    "Open-carrier successor for the Carnot entropy-family readout split. The "
    "source row compared exact QIT anchors and open stochastic/topology rows; "
    "this recheck asks only whether open carriers disagree across performance, "
    "closure, return, and bath-entropy readouts. It does not claim QIT, GStack, "
    "axis, or engine admission."
)

LEGO_IDS = ["stochastic_thermodynamics", "carnot_cycle", "readout_family_split"]
PRIMARY_LEGO_IDS = ["stochastic_thermodynamics"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads source receipt and writes recheck result"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def best(rows: list[dict], key: str) -> dict:
    return min(rows, key=lambda row: abs(float(row[key])))


def split_summary(rows: list[dict]) -> dict:
    performance = best(rows, "performance_distance")
    closure = best(rows, "closure_proxy")
    returns = best(rows, "return_proxy")
    bath = best(rows, "bath_entropy_proxy")
    distinct_readout_rows = {
        performance["row_id"],
        closure["row_id"],
        returns["row_id"],
        bath["row_id"],
    }
    return {
        "best_performance_row": performance["row_id"],
        "best_closure_row": closure["row_id"],
        "best_return_row": returns["row_id"],
        "best_bath_entropy_row": bath["row_id"],
        "distinct_readout_row_count": len(distinct_readout_rows),
        "performance_distance": performance["performance_distance"],
        "closure_proxy": closure["closure_proxy"],
        "return_proxy": returns["return_proxy"],
        "bath_entropy_proxy_abs": abs(float(bath["bath_entropy_proxy"])),
    }


def main() -> None:
    source = load("carnot_entropy_family_array_results.json")
    open_rows = [row for row in source["rows"] if row["carrier"] != "qubit_working_substance"]
    forward_open = [row for row in open_rows if row["mode"] == "forward_engine"]
    reverse_open = [row for row in open_rows if row["mode"] == "reverse_refrigerator"]
    forward = split_summary(forward_open)
    reverse = split_summary(reverse_open)

    positive = {
        "open_forward_has_nontrivial_readout_family_split": {
            **forward,
            "pass": forward["distinct_readout_row_count"] > 1,
        },
        "open_reverse_has_nontrivial_readout_family_split": {
            **reverse,
            "pass": reverse["distinct_readout_row_count"] > 1,
        },
        "open_readout_split_has_close_performance_candidate": {
            "best_open_performance_distance": min(row["performance_distance"] for row in open_rows),
            "bound": 0.1,
            "pass": min(row["performance_distance"] for row in open_rows) < 0.1,
        },
    }
    negative = {
        "forward_performance_and_closure_can_align_while_bath_entropy_splits": {
            "best_performance_row": forward["best_performance_row"],
            "best_closure_row": forward["best_closure_row"],
            "best_bath_entropy_row": forward["best_bath_entropy_row"],
            "pass": (
                forward["best_performance_row"] == forward["best_closure_row"]
                and forward["best_bath_entropy_row"] != forward["best_performance_row"]
            ),
        },
        "exact_anchor_exclusion_changes_the_question": {
            "source_forward_performance_row": source["negative"]["best_engine_performance_row_is_not_the_best_closure_row"][
                "best_performance_row"
            ],
            "source_forward_closure_row": source["negative"]["best_engine_performance_row_is_not_the_best_closure_row"][
                "best_closure_row"
            ],
            "pass": (
                source["negative"]["best_engine_performance_row_is_not_the_best_closure_row"]["best_performance_row"]
                == "exact_qit_forward"
                and source["negative"]["best_engine_performance_row_is_not_the_best_closure_row"]["best_closure_row"]
                == "exact_qit_forward"
            ),
        },
        "successor_not_qit_gstack_or_axis_admission": {"pass": True},
    }
    boundary = {
        "open_rows_exist_for_both_modes": {
            "forward_open_count": len(forward_open),
            "reverse_open_count": len(reverse_open),
            "pass": bool(forward_open and reverse_open),
        },
        "all_open_metrics_are_numeric": {
            "pass": all(
                isinstance(row.get(key), (int, float))
                for row in open_rows
                for key in ["performance_distance", "bath_entropy_proxy", "closure_proxy", "return_proxy"]
            )
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "carnot_entropy_family_open_split",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot_entropy_family_array": str(RESULT_DIR / "carnot_entropy_family_array_results.json")
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "open_row_count": len(open_rows),
            "forward_open_split": forward,
            "reverse_open_split": reverse,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": open_rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "carnot_entropy_family_open_split_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
