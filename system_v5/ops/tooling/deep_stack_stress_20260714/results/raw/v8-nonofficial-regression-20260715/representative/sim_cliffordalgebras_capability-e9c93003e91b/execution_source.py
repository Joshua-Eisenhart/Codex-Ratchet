#!/usr/bin/env python3
"""Capability probe for Julia CliffordAlgebras.jl in the strict carrier project."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path("/var/folders/59/jd7hbp413gn509q_fz_k6wgr0000gn/T/codex-ratchet-representative-k6k8ral9/repo")
RESULT = ROOT / "system_v4/probes/a2_state/sim_results/cliffordalgebras_capability_results.json"
JULIA = "/opt/homebrew/bin/julia"
PROJECT = ROOT / "system_v5/julia_carrier"

TOOL_MANIFEST = {
    "CliffordAlgebras": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict-carrier probe for CliffordAlgebra construction and bounded Cl(2,0) metadata",
    }
}
TOOL_INTEGRATION_DEPTH = {"CliffordAlgebras": "load_bearing"}

JULIA_CODE = r'''
using CliffordAlgebras
using JSON

C2 = CliffordAlgebra(2, 0)
payload = Dict(
    "active_project" => string(Base.active_project()),
    "cliffordalgebras_version" => string(pkgversion(CliffordAlgebras)),
    "object_type" => string(typeof(C2)),
    "dimension" => CliffordAlgebras.dimension(C2),
    "pass" => CliffordAlgebras.dimension(C2) == 4,
)
JSON.print(stdout, payload)
'''


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [JULIA, "--startup-file=no", f"--project={PROJECT}", "-e", JULIA_CODE],
        cwd=ROOT,
        env={**os.environ, "JULIA_LOAD_PATH": "@:@stdlib"},
        text=True,
        capture_output=True,
        check=False,
    )
    details = None
    if proc.stdout.strip():
        try:
            details = json.loads(proc.stdout)
        except json.JSONDecodeError:
            details = {"raw_stdout": proc.stdout}
    summary = {
        "all_pass": proc.returncode == 0 and isinstance(details, dict) and details.get("pass") is True,
        "returncode": proc.returncode,
    }
    payload = {
        "name": "sim_cliffordalgebras_capability",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "details": details,
        "stderr": proc.stderr,
    }
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": summary["all_pass"], "result_path": str(RESULT.relative_to(ROOT))}, sort_keys=True))
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
