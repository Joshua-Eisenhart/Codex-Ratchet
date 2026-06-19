#!/usr/bin/env python3
"""Packet-local validator for gcm_constraint_carve_floor_v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> dict:
    data = json.loads(path.read_text())
    errors: list[str] = []

    expected_top = {
        "object_id": "gcm_constraint_carve_floor_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "axis_claims_allowed": False,
        "engine_claims_allowed": False,
    }
    for key, expected in expected_top.items():
        if data.get(key) != expected:
            errors.append(f"{key} expected {expected!r}, got {data.get(key)!r}")

    if data.get("candidate_space", {}).get("state_count") != 24:
        errors.append("candidate_space.state_count must be 24")
    if data.get("constraint_carve", {}).get("survivor_count") != 6:
        errors.append("constraint_carve.survivor_count must be 6")
    if data.get("constraint_carve", {}).get("killed_count") != 18:
        errors.append("constraint_carve.killed_count must be 18")
    if data.get("quotient", {}).get("class_count") != 6:
        errors.append("quotient.class_count must be 6")

    controls = data.get("controls", {})
    expected_controls = {
        "empty_C": 24,
        "drop_C_history_consistency": 12,
        "drop_C_N01_order_visible": 12,
        "drop_C_closure_under_order_maps": 10,
        "overconstrained_orientation_one_only": 0,
    }
    for key, expected in expected_controls.items():
        if controls.get(key, {}).get("survivor_count") != expected:
            errors.append(f"control {key} survivor_count must be {expected}")

    rows = data.get("constraint_carve", {}).get("survivors", [])
    survivor_set = {tuple(row.get("state", [])) for row in rows}
    for row in rows:
        for map_key in ("R", "D", "R_after_D", "D_after_R"):
            if tuple(row.get(map_key, [])) not in survivor_set:
                errors.append(f"survivor {row.get('state')} maps outside M(C) under {map_key}")
        if row.get("order_gap_visible") is not True:
            errors.append(f"survivor {row.get('state')} lacks visible order gap")

    terrain_attempt = data.get("carved_structure", {}).get("terrain_readout_attempt", {})
    if terrain_attempt.get("verdict") != "no_8_terrain_regions_in_this_floor":
        errors.append("terrain readout verdict must stay negative for this floor")

    if not data.get("not_admitted") or "full geometric constraint manifold" not in data.get("not_admitted", []):
        errors.append("not_admitted must include full geometric constraint manifold")

    return {"ok": not errors, "errors": errors, "path": str(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate gcm_constraint_carve_floor_v0 result JSON")
    parser.add_argument("result_json", type=Path)
    args = parser.parse_args()
    report = validate(args.result_json)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
