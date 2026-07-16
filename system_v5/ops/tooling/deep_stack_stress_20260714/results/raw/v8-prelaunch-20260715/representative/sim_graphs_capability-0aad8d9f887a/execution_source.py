#!/usr/bin/env python3
"""Capability probe for Julia `Graphs`."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/graphs_capability_results.json"

TOOL_MANIFEST = {
    "Graphs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia SimpleDiGraph, add_edge!, outdegree, ne, nv, and connectivity checks decide all checks",
    }
}
TOOL_INTEGRATION_DEPTH = {"Graphs": "load_bearing"}


def main() -> int:
    code = r'''
using Graphs
g = SimpleDiGraph(4)
add_edge!(g, 1, 2)
add_edge!(g, 2, 3)
add_edge!(g, 3, 1)
positive = nv(g) == 4 && ne(g) == 3 && outdegree(g, 1) == 1 && indegree(g, 1) == 1
negative = !is_connected(g)
add_edge!(g, 3, 4)
boundary = is_connected(g) && outdegree(g, 4) == 0
println("{\"positive\":" * string(positive) * ",\"negative\":" * string(negative) * ",\"boundary\":" * string(boundary) * ",\"nv\":" * string(nv(g)) * ",\"ne\":" * string(ne(g)) * "}")
'''
    cmd = ["/opt/homebrew/bin/julia", "--startup-file=no", "--project=system_v5/julia_carrier", "-e", code]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    try:
        observed = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        observed = {"positive": False, "negative": False, "boundary": False, "stdout": proc.stdout, "stderr": proc.stderr}
    all_pass = proc.returncode == 0 and observed.get("positive") is True and observed.get("negative") is True and observed.get("boundary") is True
    payload = {
        "name": "sim_graphs_capability",
        "schema_version": "capability_probe_v1",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "python_executable": os.sys.executable,
        "julia_command": cmd,
        "julia_exit": proc.returncode,
        "observed": observed,
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
