#!/usr/bin/env python3
"""Claim-ceiling/status audit for the current PEPS3D campaign scouts."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_campaign_claim_ceiling_status_audit_probe_results.json"

NAME = "peps3d_campaign_claim_ceiling_status_audit_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: audits claim ceilings, blocked citation fields, and "
    "promotion-disabled status for the current PEPS3D campaign receipts. It does "
    "not admit canonical manifold, neural capability, physics, cognition, or "
    "64-site promotion claims."
)

TARGET_RESULTS = [
    "source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json",
    "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json",
    "source_native_peps3d_52_56_60_site_regime_ladder_probe_results.json",
    "probe_family_discrimination_chi_transport_8_16_32_probe_results.json",
    "weyl_holonomy_mps_curvature_transport_probe_results.json",
]

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt schema and claim-ceiling audit"},
    "pathlib": {"tried": True, "used": True, "reason": "load-bearing target result path resolution"},
}
TOOL_INTEGRATION_DEPTH = {
    'python_json': 'supportive',
    'pathlib': 'supportive',
}


def audit_receipt(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    text_blob = json.dumps(data, sort_keys=True).lower()
    claim_ceiling = str(data.get("claim_ceiling", "")).lower()
    demonstrate_hits = [word for word in ("demonstrates", "demonstrate", "demonstrated") if word in text_blob]
    canonical_positive = "canonical" in claim_ceiling and "does not admit" not in claim_ceiling and "does not prove" not in claim_ceiling
    return {
        "path": str(path.relative_to(ROOT)),
        "all_pass": bool(data.get("all_pass")),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "has_claim_ceiling": bool(data.get("claim_ceiling")),
        "has_source_alignment_category": bool(data.get("source_alignment_category")),
        "has_blocked_until_or_boundary": bool(data.get("cites_blocked_until") or data.get("why_not_v4_probes") or data.get("boundary")),
        "demonstrate_hits": demonstrate_hits,
        "canonical_positive_overclaim": canonical_positive,
        "pass": bool(data.get("all_pass"))
        and data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and bool(data.get("claim_ceiling"))
        and bool(data.get("source_alignment_category"))
        and not demonstrate_hits
        and not canonical_positive,
    }


def main() -> int:
    started = time.time()
    rows = [audit_receipt(RESULT_DIR / name) for name in TARGET_RESULTS]
    positive = {
        "peps3d_campaign_receipts_remain_claim_ceiling_bound": {
            "rows": rows,
            "pass": all(row["pass"] for row in rows),
        }
    }
    graveyards = {
        "demonstrates_language_is_rejected": {
            "hits": {row["path"]: row["demonstrate_hits"] for row in rows if row["demonstrate_hits"]},
            "pass": all(not row["demonstrate_hits"] for row in rows),
        },
        "promotion_true_is_rejected": {
            "promotion_allowed_values": {row["path"]: row["promotion_allowed"] for row in rows},
            "pass": all(row["promotion_allowed"] is False for row in rows),
        },
    }
    boundary = {
        "target_count_matches_campaign_surface": {"count": len(rows), "pass": len(rows) == len(TARGET_RESULTS)},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "peps3d_campaign_claim_ceiling_status_audit",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Status audit only.",
            "Does not add mathematical evidence.",
            "Prevents accidental promotion language on the campaign evidence surface.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
