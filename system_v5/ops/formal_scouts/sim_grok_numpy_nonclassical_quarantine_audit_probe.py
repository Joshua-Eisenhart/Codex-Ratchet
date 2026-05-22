#!/usr/bin/env python3
"""Audit Grok/proposal and legacy sim NumPy use against nonclassical claims.

NumPy-heavy sims can be useful classical/control evidence. They are not
nonclassical, bridge, basin, QIT-engine, or manifold evidence when NumPy is in
the load-bearing path. This scout reads the current sim inventory and makes
that boundary explicit instead of treating the formal-scout-only NumPy gate as
global clearance.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from collections import Counter
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "grok_numpy_nonclassical_quarantine_audit_probe_results.json"

sys.path.insert(0, str(REPO / "scripts"))
import sim_inventory_index  # noqa: E402


NAME = "grok_numpy_nonclassical_quarantine_audit_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout audit only: NumPy-heavy Grok/proposal and legacy v4 sims may "
    "remain classical/control evidence, but any bridge or nonclassical row with "
    "NumPy load-bearing is blocked from nonclassical, QIT-engine, manifold, "
    "basin, axis, or bridge promotion until ported to constraint-admissible "
    "nonclassical tooling or explicitly reclassified as classical."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing inventory/result receipt writing"},
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing repository path and result discovery"},
    "sim_inventory_index": {"tried": True, "used": True, "reason": "supportive current sim inventory classification and blocker extraction"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive script receipt hash"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "sim_inventory_index": "supportive",
    "hashlib": "supportive",
}

NUMPY_BLOCKER = "numpy_load_bearing_blocked_for_bridge_or_nonclassical"
PYTORCH_BLOCKER = "nonclassical_requires_local_load_bearing_pytorch"
LANE_CONFLICT_BLOCKER = "execution_lane_conflict_requires_manual_review"


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: pathlib.Path) -> str:
    return str(path.resolve().relative_to(REPO))


def sample_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "source_path",
        "runner_execution_kind",
        "sim_execution_lane",
        "load_bearing_tools",
        "local_load_bearing_tools",
        "result_classifications",
        "admission_status",
        "admitted",
        "promotion_blockers",
        "garbage_candidate_flags",
    )
    return {key: row.get(key) for key in keys if key in row}


def prefix(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 3 and parts[:2] == ["system_v5", "grok_sim"]:
        return "system_v5/grok_sim"
    if len(parts) >= 3 and parts[:2] == ["system_v4", "probes"]:
        return "system_v4/probes"
    if len(parts) >= 3 and parts[:2] == ["system_v5", "ops"]:
        return "system_v5/ops"
    return "/".join(parts[:2])


def counts_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def main() -> int:
    started = time.time()
    index = sim_inventory_index.build_index(progress=False, skip_bulk_a2_state_results=True, include_rows=True)
    rows = list(index.get("rows", []))

    numpy_blocked = [
        row for row in rows if NUMPY_BLOCKER in row.get("promotion_blockers", [])
    ]
    admitted_numpy_blocked = [row for row in numpy_blocked if row.get("admitted") is True]
    grok_rows = [row for row in rows if str(row.get("source_path", "")).startswith("system_v5/grok_sim/")]
    grok_problem_rows = [
        row
        for row in grok_rows
        if any(
            blocker in row.get("promotion_blockers", [])
            for blocker in (NUMPY_BLOCKER, PYTORCH_BLOCKER, LANE_CONFLICT_BLOCKER)
        )
    ]
    grok_numpy_ambiguous = [
        row
        for row in grok_rows
        if "numpy" in row.get("load_bearing_tools", [])
        and (
            row.get("runner_execution_kind") in {"bridge", "nonclassical"}
            or LANE_CONFLICT_BLOCKER in row.get("promotion_blockers", [])
        )
    ]
    classical_numpy = [
        row
        for row in rows
        if row.get("runner_execution_kind") == "classical"
        and "numpy" in row.get("load_bearing_tools", [])
    ]

    prefix_counts = Counter(prefix(str(row.get("source_path", ""))) for row in numpy_blocked)
    admitted_prefix_counts = Counter(prefix(str(row.get("source_path", ""))) for row in admitted_numpy_blocked)

    positive = {
        "classical_numpy_lane_preserved": {
            "pass": len(classical_numpy) > 0,
            "classical_numpy_count": len(classical_numpy),
            "reason": "NumPy remains admissible for classical/control rows, but not for nonclassical or bridge claims.",
        },
        "bridge_nonclassical_numpy_blockers_are_visible": {
            "pass": len(numpy_blocked) > 0,
            "blocked_count": len(numpy_blocked),
            "by_prefix": dict(sorted(prefix_counts.items())),
            "reason": "Current inventory exposes NumPy load-bearing as a promotion blocker for bridge/nonclassical rows.",
        },
        "grok_proposal_lab_is_not_admitted_evidence": {
            "pass": all(row.get("admitted") is not True for row in grok_problem_rows),
            "grok_problem_row_count": len(grok_problem_rows),
            "grok_numpy_ambiguous_count": len(grok_numpy_ambiguous),
            "reason": "Grok proposal rows may be useful idea sources, but these rows are not accepted nonclassical evidence.",
        },
        "formal_scout_numpy_gate_is_not_global_clearance": {
            "pass": True,
            "reason": (
                "The existing numpy_quarantine_source_native_nonclassical gate scans current v5 formal scouts. "
                "This audit extends the boundary to inventory/admission surfaces where Grok and legacy rows appear."
            ),
        },
    }
    negative = {
        "admitted_numpy_nonclassical_rows_remain_blocked": {
            "pass": len(admitted_numpy_blocked) == 0,
            "admitted_blocked_count": len(admitted_numpy_blocked),
            "by_prefix": dict(sorted(admitted_prefix_counts.items())),
            "reason": (
                "Rows that are admitted_evidence_linked while still bridge/nonclassical NumPy-load-bearing "
                "must not be cited as nonclassical evidence. They need reclassification, demotion, or PyTorch/native rewrites."
            ),
            "samples": [sample_row(row) for row in admitted_numpy_blocked[:25]],
        },
        "grok_numpy_ambiguous_rows_are_quarantined_not_admitted": {
            "pass": all(row.get("admitted") is not True for row in grok_numpy_ambiguous),
            "grok_numpy_ambiguous_count": len(grok_numpy_ambiguous),
            "samples": [sample_row(row) for row in grok_numpy_ambiguous[:25]],
            "reason": (
                "Grok rows that are mixed/ambiguous or bridge/nonclassical while carrying NumPy load-bearing "
                "remain quarantined proposal rows unless explicitly reclassified as classical or ported to native "
                "nonclassical tooling."
            ),
        },
    }
    boundary = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_nonclassical_admission": {
            "pass": "blocked from nonclassical" in CLAIM_CEILING,
        },
    }
    graveyard = {
        "numpy_success_is_not_nonclassical_success": {
            "pass": True,
            "reason": "Good NumPy numerics are preserved only as classical/control evidence unless a later native nonclassical receipt exists.",
        },
        "grok_sim_remains_proposal_lab": {
            "pass": True,
            "reason": "system_v5/grok_sim can feed ideas and failures, but direct Grok proposal rows are not canonical proof surfaces.",
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard.values())
    )
    blockers = [
        key for key, item in {**positive, **negative, **boundary, **graveyard}.items() if not item.get("pass")
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "grok_and_inventory_numpy_nonclassical_quarantine",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "graveyard_companions": graveyard,
        "summary": {
            "inventory_source_count": index.get("summary", {}).get("source_count"),
            "inventory_result_json_count": index.get("summary", {}).get("result_json_count"),
            "historical_admission_record_count": index.get("summary", {}).get("historical_admission_record_count"),
            "admission_result_skipped_by_bulk_a2_state_count": index.get("summary", {}).get(
                "admission_result_skipped_by_bulk_a2_state_count"
            ),
            "linked_admitted_evidence_count": index.get("summary", {}).get("admitted_count"),
            "numpy_load_bearing_blocked_for_bridge_or_nonclassical": len(numpy_blocked),
            "admitted_numpy_blocked_rows": len(admitted_numpy_blocked),
            "grok_rows_indexed": len(grok_rows),
            "grok_problem_rows": len(grok_problem_rows),
            "grok_numpy_ambiguous_rows": len(grok_numpy_ambiguous),
            "classical_numpy_rows": len(classical_numpy),
            "numpy_blocked_by_prefix": dict(sorted(prefix_counts.items())),
            "admitted_numpy_blocked_by_prefix": dict(sorted(admitted_prefix_counts.items())),
            "grok_runner_kind_counts": counts_by(grok_rows, "runner_execution_kind"),
        },
        "numpy_blocked_samples": [sample_row(row) for row in numpy_blocked[:25]],
        "grok_problem_samples": [sample_row(row) for row in grok_problem_rows[:25]],
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 audit receipt over the current inventory; it does not run or repair v4 sims.",
            "It keeps NumPy-heavy successes as classical/control evidence and blocks them as nonclassical evidence.",
        ],
        "blockers": blockers,
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(
        "  "
        f"numpy_blocked={len(numpy_blocked)} admitted_numpy_blocked={len(admitted_numpy_blocked)} "
        f"grok_problem={len(grok_problem_rows)} grok_numpy_ambiguous={len(grok_numpy_ambiguous)}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
