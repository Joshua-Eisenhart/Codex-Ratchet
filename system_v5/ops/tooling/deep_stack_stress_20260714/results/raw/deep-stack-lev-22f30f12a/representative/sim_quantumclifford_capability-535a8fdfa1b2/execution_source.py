#!/usr/bin/env python3
"""Capability probe for Julia QuantumClifford.jl in the strict carrier project."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path("/var/folders/59/jd7hbp413gn509q_fz_k6wgr0000gn/T/codex-ratchet-representative-grdkqpeb/repo")
RESULT = ROOT / "system_v4/probes/a2_state/sim_results/quantumclifford_capability_results.json"
JULIA = "/opt/homebrew/bin/julia"
PROJECT = ROOT / "system_v5/julia_carrier"

TOOL_MANIFEST = {
    "QuantumClifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing strict-carrier probe for PauliOperator, Stabilizer, stab_to_gf2, and commutation predicates",
    }
}
TOOL_INTEGRATION_DEPTH = {"QuantumClifford": "load_bearing"}

JULIA_CODE = r'''
using JSON
using QuantumClifford

x = PauliOperator(UInt8(0), Bool[1, 0, 0, 0, 0, 0], Bool[0, 0, 0, 0, 0, 0])
z = PauliOperator(UInt8(0), Bool[0, 0, 0, 0, 0, 0], Bool[1, 0, 0, 0, 0, 0])
xx = PauliOperator(UInt8(0), trues(6), falses(6))
zz = PauliOperator(UInt8(0), falses(6), trues(6))
stab = Stabilizer([xx, zz])
gf2 = stab_to_gf2(stab)
payload = Dict(
    "active_project" => string(Base.active_project()),
    "quantumclifford_version" => string(pkgversion(QuantumClifford)),
    "single_site_xz_anticommutes" => comm(x, z),
    "six_qubit_stabilizer_qubits" => nqubits(stab),
    "six_qubit_stabilizer_generators" => length(stab),
    "six_qubit_stabilizer_commutes" => comm(stab[1], stab[2]),
    "gf2_shape" => collect(size(gf2)),
    "gf2_row_sums" => [sum(gf2[i, :]) for i in axes(gf2, 1)],
    "pass" => comm(x, z) == 1 &&
        nqubits(stab) == 6 &&
        length(stab) == 2 &&
        comm(stab[1], stab[2]) == 0 &&
        collect(size(gf2)) == [2, 12] &&
        all(sum(gf2[i, :]) == 6 for i in axes(gf2, 1)),
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
        "name": "sim_quantumclifford_capability",
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
