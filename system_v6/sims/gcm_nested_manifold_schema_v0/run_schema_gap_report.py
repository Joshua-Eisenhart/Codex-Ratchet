#!/usr/bin/env python3
"""Run the nested schema checker against current GCM tower/geometry packets."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
RESULT_PATH = SIM_DIR / "results" / "gcm_nested_schema_gap_report.json"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gcm_nested_schema_check import REQUIRED_FIELDS, gcm_nested_schema_check  # noqa: E402


TARGET_PACKET_PATHS = [
    "system_v6/sims/gcm_nesting_tower_le3q_v0/results/gcm_nesting_tower_le3q_v0_results.json",
    "system_v6/sims/gcm_nesting_tower_le3q_v0/results/gcm_nesting_tower_le3q_v0_envelope_results.json",
    "system_v6/sims/gcm_nesting_tower_le2q_v0/results/gcm_nesting_tower_le2q_v0_results.json",
    "system_v6/sims/gcm_nesting_tower_le2q_v0/results/gcm_nesting_tower_le2q_v0_envelope_results.json",
    "system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_results.json",
    "system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_envelope_results.json",
    "system_v6/sims/gcm_geometry_attach_2q_v0/results/gcm_geometry_attach_2q_v0_results.json",
    "system_v6/sims/gcm_geometry_attach_2q_v0/results/gcm_geometry_attach_2q_v0_envelope_results.json",
    "system_v6/sims/gcm_geometry_attach_2q_v1/results/gcm_geometry_attach_2q_v1_results.json",
    "system_v6/sims/gcm_geometry_attach_2q_v1/results/gcm_geometry_attach_2q_v1_envelope_results.json",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    packets: list[dict[str, Any]] = []
    pass_count = 0
    fail_count = 0
    for rel_path in TARGET_PACKET_PATHS:
        path = ROOT / rel_path
        if not path.exists():
            fail_count += 1
            packets.append(
                {
                    "payload_path": rel_path,
                    "schema_status": "FAIL",
                    "error_codes": ["GCM_NESTED_PAYLOAD_MISSING"],
                    "missing_fields": list(REQUIRED_FIELDS),
                }
            )
            continue
        result = gcm_nested_schema_check(load_json(path), path)
        status = "PASS" if result["ok"] else "FAIL"
        pass_count += int(result["ok"])
        fail_count += int(not result["ok"])
        packets.append(
            {
                "payload_path": rel_path,
                "schema_status": status,
                "missing_fields": result["missing_fields"],
                "error_codes": result["error_codes"],
                "geometry_delta_claimed": result["geometry_delta_claimed"],
                "geometry_delta_claim_paths": result["geometry_delta_claim_paths"],
                "claim_ceiling": result.get("claim_ceiling"),
            }
        )
    report = {
        "sim_id": "gcm_nested_manifold_schema_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "schema_helper": "scripts/gcm_nested_schema_check.py",
        "authority": {
            "tribunal_adoption_commit": "f65a81010",
            "tribunal_receipt": "system_v6/receipts/nesting_plan_tribunal_adopted_20260612.md",
            "nesting_law_commit": "afe7aa57b",
            "nesting_law_receipt": "system_v6/receipts/nesting_law_final_object_spec_20260612.md",
        },
        "required_fields": list(REQUIRED_FIELDS),
        "summary": {
            "packet_count": len(packets),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "honest_gap_map": "Existing tower/geometry packets predate the tribunal schema; failures are backfill targets, not mathematical refutations.",
        },
        "packets": packets,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
