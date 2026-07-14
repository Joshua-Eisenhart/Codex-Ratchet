#!/usr/bin/env python3
"""Capability probe for Julia DifferentialEquations ODEProblem/solve."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = REPO / "system_v5" / "julia_carrier"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULT_PATH = RESULTS_DIR / "differentialequations_capability_results.json"

TOOL_MANIFEST = {
    "DifferentialEquations": {
        "tried": True,
        "used": True,
        "reason": "load-bearing capability under test: ODEProblem plus solve(Tsit5) decides all_pass against analytic ODE fixtures",
    }
}
TOOL_INTEGRATION_DEPTH = {"DifferentialEquations": "load_bearing"}

JULIA_PROGRAM = r"""
using DifferentialEquations
using JSON

function decay_fixture()
    problem = DifferentialEquations.ODEProblem((u, p, t) -> -2.0 .* u, [1.0], (0.0, 1.0))
    solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
    got = solution(1.0)[1]
    expected = exp(-2.0)
    Dict(
        "pass" => abs(got - expected) <= 1e-8,
        "api" => "DifferentialEquations.ODEProblem + solve(Tsit5)",
        "got" => got,
        "expected" => expected,
        "abs_error" => abs(got - expected),
    )
end

function affine_fixture()
    problem = DifferentialEquations.ODEProblem((u, p, t) -> [-u[1] + 0.25], [0.75], (0.0, 1.0))
    solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
    got = solution(1.0)[1]
    expected = 0.25 + (0.75 - 0.25) * exp(-1.0)
    Dict(
        "pass" => abs(got - expected) <= 1e-8,
        "api" => "DifferentialEquations.ODEProblem + solve(Tsit5)",
        "got" => got,
        "expected" => expected,
        "abs_error" => abs(got - expected),
    )
end

function boundary_fixture()
    problem = DifferentialEquations.ODEProblem((u, p, t) -> -2.0 .* u, [1.0], (0.0, 0.0))
    solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
    got = solution(0.0)[1]
    Dict(
        "pass" => abs(got - 1.0) <= 1e-12,
        "api" => "DifferentialEquations.ODEProblem + solve(Tsit5)",
        "got" => got,
        "expected" => 1.0,
        "abs_error" => abs(got - 1.0),
    )
end

function wrong_control()
    problem = DifferentialEquations.ODEProblem((u, p, t) -> 2.0 .* u, [1.0], (0.0, 1.0))
    solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(), abstol=1e-10, reltol=1e-10)
    got = solution(1.0)[1]
    expected_decay = exp(-2.0)
    Dict(
        "pass" => abs(got - expected_decay) > 1e-3,
        "api" => "DifferentialEquations.ODEProblem + solve(Tsit5)",
        "got_wrong_sign" => got,
        "expected_decay" => expected_decay,
        "abs_difference" => abs(got - expected_decay),
    )
end

decay = decay_fixture()
affine = affine_fixture()
boundary = boundary_fixture()
wrong = wrong_control()
payload = Dict(
    "decay_fixture" => decay,
    "affine_fixture" => affine,
    "boundary_fixture" => boundary,
    "wrong_sign_control" => wrong,
    "summary" => Dict("all_pass" => decay["pass"] && affine["pass"] && boundary["pass"] && wrong["pass"]),
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
        "probe": "differentialequations",
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
