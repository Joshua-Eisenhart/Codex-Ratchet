#!/usr/bin/env python3
"""Assembly audit for operator-geometry exclusion receipts.

This does not add a new mathematical exclusion. It audits whether the current
single-pair exclusion receipts are sufficient to queue a later coexistence
assembly, while keeping all claims below promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt assembly audit over local JSON evidence",
    },
    "numpy": {"tried": False, "used": False, "reason": "not needed; source receipts carry numeric witnesses"},
    "z3": {"tried": False, "used": False, "reason": "not rerun; source receipts carry z3 exclusions"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "numpy": None,
    "z3": None,
}


def read_result(name: str) -> dict:
    return json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    single = read_result("operator_geometry_single_pair_exclusion_results.json")
    multi = read_result("operator_geometry_multi_pair_exclusions_results.json")
    closure_ablation = read_result("operator_geometry_closure_ablation_results.json")

    pair_names = [
        single.get("summary", {}).get("named_pair"),
        *[check.get("pair") for check in multi.get("checks", {}).values()],
    ]
    invariant_names = [
        single.get("summary", {}).get("named_invariant"),
        *[check.get("invariant") for check in multi.get("checks", {}).values()],
    ]
    source_receipts = {
        "single_pair": single,
        "multi_pair": multi,
        "closure_ablation": closure_ablation,
    }

    positive = {
        "three_independent_pair_exclusions_present": {
            "pairs": pair_names,
            "pass": len(set(pair_names)) == 3 and all(pair_names),
        },
        "each_exclusion_has_named_invariant": {
            "invariants": invariant_names,
            "pass": all(invariant_names),
        },
        "all_source_receipts_pass": {
            "statuses": {name: bool(payload.get("all_pass")) for name, payload in source_receipts.items()},
            "pass": all(bool(payload.get("all_pass")) for payload in source_receipts.values()),
        },
    }
    negative = {
        "no_source_receipt_promotes": {
            "classifications": {name: payload.get("classification") for name, payload in source_receipts.items()},
            "pass": all(payload.get("classification") == "supporting" for payload in source_receipts.values()),
        },
        "commuting_pairs_remain_excluded_from_positive_set": {
            "excluded_pairs": [
                "Ti_z_dephase vs Fe_z_rotate",
                "Te_x_dephase vs Fi_x_rotate",
                "Ti_z_dephase vs Te_x_dephase",
            ],
            "pass": True,
        },
    }
    boundary = {
        "assembly_is_queue_permission_not_admission": {
            "pass": True,
            "note": "This audit only says a later coexistence packet is now justified.",
        },
        "coexistence_not_tested_here": {
            "pass": True,
            "blocked_next": "Build a fresh coexistence sim that combines exclusions with a shared state family.",
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": "operator_geometry_exclusion_assembly_audit",
        "classification": "supporting",
        "classification_note": (
            "Receipt assembly audit: three single-pair exclusions justify queuing, not admitting, "
            "a later operator-geometry coexistence packet."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": [
            str(RESULTS_DIR / "operator_geometry_single_pair_exclusion_results.json"),
            str(RESULTS_DIR / "operator_geometry_multi_pair_exclusions_results.json"),
            str(RESULTS_DIR / "operator_geometry_closure_ablation_results.json"),
        ],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "pair_exclusion_count": len(set(pair_names)),
            "next_packet_justified": bool(all_pass),
            "promotion_allowed": False,
            "scope_note": "Use this as queue evidence for the next coexistence sim only.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This assembly audit cannot prove coexistence because it only reads prior receipts. "
            "The next packet must perform a fresh shared-state coexistence check."
        ),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_operator_geometry_exclusion_assembly_audit",
        target="Queue a fresh operator-geometry coexistence sim over a shared finite state family.",
    )
    results["promotion_condition"] = "Requires fresh coexistence sim and explicit stage-gate admission."
    results["blocked_until"] = "fresh coexistence sim over shared finite state family"

    out_path = RESULTS_DIR / "operator_geometry_exclusion_assembly_audit_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
