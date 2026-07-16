#!/usr/bin/env python3
"""Capability probe for Julia `Grassmann` exterior algebra."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

classification = "canonical"
promotion_allowed = False

ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = ROOT / "system_v4/probes/a2_state/sim_results/grassmann_capability_results.json"

TOOL_MANIFEST = {
    "Grassmann": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Julia Grassmann basis and wedge products decide all checks",
    }
}
TOOL_INTEGRATION_DEPTH = {"Grassmann": "load_bearing"}


def main() -> int:
    code = r'''
using Grassmann
@basis S"++"
positive = Grassmann.wedge(v1, v2) == v12
negative = iszero(Grassmann.wedge(v1, v1))
boundary = Grassmann.wedge(2v1, 3v2) == 6v12
println("{\"positive\":" * string(positive) * ",\"negative\":" * string(negative) * ",\"boundary\":" * string(boundary) * "}")
'''
    cmd = ["/opt/homebrew/bin/julia", "--startup-file=no", "--project=system_v5/julia_carrier", "-e", code]
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    try:
        observed = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        observed = {"positive": False, "negative": False, "boundary": False, "stdout": proc.stdout, "stderr": proc.stderr}
    all_pass = proc.returncode == 0 and observed.get("positive") is True and observed.get("negative") is True and observed.get("boundary") is True
    payload = {
        "name": "sim_grassmann_capability",
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
