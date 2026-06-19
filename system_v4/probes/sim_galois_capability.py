#!/usr/bin/env python3
"""Capability probe for finite-field `galois` operations."""

from __future__ import annotations

import json
import os
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/galois_capability_results.json"

TOOL_MANIFEST = {
    "galois": {
        "tried": True,
        "used": True,
        "reason": "load-bearing GF(3) row-space, rank, and finite-field arithmetic checks decide all checks",
    }
}
TOOL_INTEGRATION_DEPTH = {"galois": "load_bearing"}


def main() -> int:
    import galois

    GF = galois.GF(3)
    mat = GF([[1, 0, 1, 2], [0, 1, 1, 1]])
    row_space = mat.row_space()
    rank = int(mat.row_space().shape[0])
    points = set()
    for a in GF.elements:
        for b in GF.elements:
            if int(a) == 0 and int(b) == 0:
                continue
            v = a * row_space[0] + b * row_space[1]
            if int(v[0]) == 2 or (int(v[0]) == 0 and any(int(x) == 2 for x in v[1:2])):
                v = GF(2) * v
            points.add(tuple(int(x) for x in v))
    positive = rank == 2 and len(points) == 4
    negative = int(GF(2) + GF(2)) == 1
    boundary = int(GF(0) * GF(2)) == 0
    all_pass = positive and negative and boundary
    payload = {
        "name": "sim_galois_capability",
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python_executable": os.sys.executable,
        "galois_version": galois.__version__,
        "positive": {"pg_line_has_q_plus_one_points": {"pass": positive, "rank": rank, "point_count": len(points)}},
        "negative": {"two_plus_two_mod_three_is_one": {"pass": negative}},
        "boundary": {"zero_absorbs": {"pass": boundary}},
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
