#!/usr/bin/env python3
"""Capability probe for Julia Manifolds.jl in the strict carrier project."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path("/var/folders/59/jd7hbp413gn509q_fz_k6wgr0000gn/T/codex-ratchet-representative-ij_ic6zs/repo")
RESULT = ROOT / "system_v4/probes/a2_state/sim_results/manifolds_capability_results.json"
JULIA = "/opt/homebrew/bin/julia"
PROJECT = ROOT / "system_v5/julia_carrier"

TOOL_MANIFEST = {
    "Manifolds": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict-carrier probe for Sphere distance, shortest_geodesic, log/exp, and manifold_volume on S2/S3",
    }
}
TOOL_INTEGRATION_DEPTH = {"Manifolds": "load_bearing"}

JULIA_CODE = r'''
using JSON
using LinearAlgebra
using Manifolds

M2 = Sphere(2)
M3 = Sphere(3)
p2 = [0.0, 0.0, 1.0]
q2 = [1.0, 0.0, 0.0]
p3 = [1.0, 0.0, 0.0, 0.0]
q3 = [0.0, 1.0, 0.0, 0.0]
mid2 = Manifolds.shortest_geodesic(M2, p2, q2, 0.5)
log2 = Manifolds.log(M2, p2, q2)
exp2 = Manifolds.exp(M2, p2, log2)
vol2 = Manifolds.manifold_volume(M2)
vol3 = Manifolds.manifold_volume(M3)
payload = Dict(
    "active_project" => string(Base.active_project()),
    "manifolds_version" => string(pkgversion(Manifolds)),
    "distance_s2_orthogonal" => Manifolds.distance(M2, p2, q2),
    "distance_s3_orthogonal" => Manifolds.distance(M3, p3, q3),
    "shortest_geodesic_s2_midpoint" => mid2,
    "log_exp_s2_endpoint_residual" => norm(exp2 - q2),
    "volume_s2" => vol2,
    "volume_s3" => vol3,
    "pass" => abs(Manifolds.distance(M2, p2, q2) - pi/2) < 1.0e-12 &&
        abs(Manifolds.distance(M3, p3, q3) - pi/2) < 1.0e-12 &&
        norm(mid2 - [sqrt(0.5), 0.0, sqrt(0.5)]) < 1.0e-12 &&
        norm(exp2 - q2) < 1.0e-12 &&
        abs(vol2 - 4pi) < 1.0e-12 &&
        abs(vol3 - 2pi^2) < 1.0e-12,
)
JSON.print(stdout, payload)
'''


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        JULIA,
        "--startup-file=no",
        f"--project={PROJECT}",
        "-e",
        JULIA_CODE,
    ]
    proc = subprocess.run(
        cmd,
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
        "name": "sim_manifolds_capability",
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
