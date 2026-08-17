#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import digest_obj


def project(kernel: dict, lanes: list[dict]) -> dict:
    required = ("object_hash", "hard_constraints", "claim_ceiling")
    missing = [key for key in required if not kernel.get(key)]
    if missing:
        return {"schema": "constraintbox.context-projection.v1", "status": "HOLD", "reason": "HOLD_KERNEL_INCOMPLETE", "missing": missing}
    roots = [digest_obj(lane.get("source_roots") or []) for lane in lanes]
    if len(roots) != len(set(roots)):
        return {"schema": "constraintbox.context-projection.v1", "status": "REFUSE", "reason": "REFUSE_SHARED_SOURCE_ROOTS", "promotion_allowed": False}
    packets = []
    for lane in lanes:
        packets.append(
            {
                "lane": lane.get("id"),
                "kernel": {key: kernel[key] for key in required},
                "source_roots": lane.get("source_roots") or [],
                "source_root_digest": digest_obj(lane.get("source_roots") or []),
                "role": lane.get("role"),
            }
        )
    matrix = []
    for left in lanes:
        left_roots = set(left.get("source_roots") or [])
        row = []
        for right in lanes:
            right_roots = set(right.get("source_roots") or [])
            row.append(sorted(left_roots & right_roots))
        matrix.append(row)
    return {
        "schema": "constraintbox.context-projection.v1",
        "status": "PROJECTED",
        "kernel_digest": digest_obj({key: kernel[key] for key in required}),
        "lane_count": len(packets),
        "packets": packets,
        "correlated_root_matrix": matrix,
        "promotion_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--lanes", type=Path, required=True)
    args = parser.parse_args()
    kernel = json.loads(args.kernel.read_text(encoding="utf-8"))
    lanes = json.loads(args.lanes.read_text(encoding="utf-8"))
    if isinstance(lanes, dict):
        lanes = lanes.get("lanes") or []
    receipt = project(kernel, lanes)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "PROJECTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
