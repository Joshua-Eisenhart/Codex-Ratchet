#!/usr/bin/env python3
"""Capability probe for Julia Symbolics symbolic differentiation/substitution."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = REPO / "system_v5" / "julia_carrier"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULT_PATH = RESULTS_DIR / "symbolics_capability_results.json"

TOOL_MANIFEST = {
    "Symbolics": {
        "tried": True,
        "used": True,
        "reason": "load-bearing capability under test: symbolic variables, differentiation, derivative expansion, and substitution decide all_pass",
    }
}
TOOL_INTEGRATION_DEPTH = {"Symbolics": "load_bearing"}

JULIA_PROGRAM = r"""
using JSON
using Symbolics

@variables x y
Dx = Differential(x)
Dy = Differential(y)

expr = x^3 + x*y
dx_expr = expand_derivatives(Dx(expr))
dy_expr = expand_derivatives(Dy(expr))
dx_at_sample = Symbolics.value(substitute(dx_expr, Dict(x => 2.0, y => 5.0)))
dy_at_sample = Symbolics.value(substitute(dy_expr, Dict(x => 2.0, y => 5.0)))

positive = Dict(
    "pass" => dx_at_sample == 17.0 && dy_at_sample == 2.0,
    "api" => "Symbolics.@variables + Differential + expand_derivatives + substitute",
    "dx_expr" => string(dx_expr),
    "dy_expr" => string(dy_expr),
    "dx_at_x2_y5" => dx_at_sample,
    "dy_at_x2_y5" => dy_at_sample,
)
wrong_control = Dict(
    "pass" => dx_at_sample != dy_at_sample,
    "mutation" => "confuse d/dx with d/dy",
    "dx_at_x2_y5" => dx_at_sample,
    "dy_at_x2_y5" => dy_at_sample,
)

payload = Dict(
    "positive_symbolic_derivative_fixture" => positive,
    "wrong_derivative_control" => wrong_control,
    "summary" => Dict("all_pass" => positive["pass"] && wrong_control["pass"]),
)
JSON.print(stdout, payload)
"""


def main() -> int:
    proc = subprocess.run(
        [
            JULIA,
            "--startup-file=no",
            f"--project={JULIA_PROJECT}",
            "-e",
            JULIA_PROGRAM,
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = {
        "schema_version": "capability_probe_result_v1",
        "probe": "symbolics",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "julia_project": str(JULIA_PROJECT),
        "returncode": proc.returncode,
        "stderr": proc.stderr,
    }
    try:
        observed = json.loads(proc.stdout)
    except json.JSONDecodeError:
        observed = {"summary": {"all_pass": False}, "raw_stdout": proc.stdout}
    payload.update(observed)
    payload["summary"]["all_pass"] = bool(proc.returncode == 0 and payload["summary"].get("all_pass") is True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["summary"]["all_pass"], "result_path": str(RESULT_PATH.relative_to(REPO))}, sort_keys=True))
    return 0 if payload["summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
