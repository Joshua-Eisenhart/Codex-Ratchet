#!/usr/bin/env python3
"""
sim_quantumoptics_capability.py -- Tool-capability isolation sim for QuantumOptics.jl.

This is a bounded strict-carrier Julia subprocess probe. It isolates
QuantumOptics state, density-operator, observable, trace-distance, fidelity,
and superoperator/channel APIs before S3/S4 packets can claim QuantumOptics as
load-bearing.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"

REPO = Path(__file__).resolve().parents[2]
PROBE_PATH = Path(__file__).resolve()
RESULTS_DIR = PROBE_PATH.parent / "a2_state" / "sim_results"
RESULT_PATH = RESULTS_DIR / "sim_quantumoptics_capability_results.json"
MATRIX_PATH = RESULTS_DIR / "quantumoptics_capability_results.json"
JULIA = Path("/opt/homebrew/bin/julia")
JULIA_PROJECT = REPO / "system_v5" / "julia_carrier"

_NOT_USED_REASON = (
    "not used: this bounded QuantumOptics capability receipt isolates "
    "QuantumOptics.jl one-qubit state, density, observable, fidelity, "
    "trace-distance, and superoperator APIs; other tool families require "
    "separate receipts."
)

TOOL_MANIFEST = {
    "QuantumOptics": {
        "tried": True,
        "used": True,
        "reason": "load-bearing capability under test: strict-carrier Julia QuantumOptics APIs decide every pass/fail verdict",
    },
    "qutip": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "QuantumOptics": "load_bearing",
    "qutip": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

JULIA_PROGRAM = r'''
using JSON
using LinearAlgebra
using QuantumOptics

const TOL = 1.0e-10

function section_all_pass(section)
    all(Bool(row["pass"]) for row in values(section))
end

basis = QuantumOptics.SpinBasis(1//2)
ket0 = QuantumOptics.basisstate(basis, 1)
ket1 = QuantumOptics.basisstate(basis, 2)
rho0 = QuantumOptics.dm(ket0)
rho1 = QuantumOptics.dm(ket1)
ket_plus = (ket0 + ket1) / sqrt(2)
rho_plus = QuantumOptics.dm(ket_plus)

sx = QuantumOptics.sigmax(basis)
sy = QuantumOptics.sigmay(basis)
sz = QuantumOptics.sigmaz(basis)
eye = QuantumOptics.identityoperator(basis)
p0 = 0.5 * (eye + sz)
p1 = 0.5 * (eye - sz)
pinch_z = QuantumOptics.sprepost(p0, p0) + QuantumOptics.sprepost(p1, p1)
identity_super = QuantumOptics.sprepost(eye, eye)

rho_plus_pinched = pinch_z * rho_plus
rho0_identity = identity_super * rho0

positive = Dict(
    "density_trace" => Dict(
        "pass" => abs(real(QuantumOptics.tr(rho0)) - 1.0) <= TOL,
        "value" => real(QuantumOptics.tr(rho0)),
        "api" => "QuantumOptics.dm + QuantumOptics.tr",
    ),
    "z_expectation_zero" => Dict(
        "pass" => abs(real(QuantumOptics.expect(sz, rho0)) - 1.0) <= TOL,
        "value" => real(QuantumOptics.expect(sz, rho0)),
        "api" => "QuantumOptics.expect(sigmaz, rho)",
    ),
    "x_expectation_plus" => Dict(
        "pass" => abs(real(QuantumOptics.expect(sx, rho_plus)) - 1.0) <= TOL,
        "value" => real(QuantumOptics.expect(sx, rho_plus)),
        "api" => "QuantumOptics.expect(sigmax, rho_plus)",
    ),
    "z_pinching_channel" => Dict(
        "pass" => abs(real(QuantumOptics.expect(sx, rho_plus_pinched))) <= TOL &&
                  abs(real(QuantumOptics.tr(rho_plus_pinched)) - 1.0) <= TOL,
        "x_after_pinching" => real(QuantumOptics.expect(sx, rho_plus_pinched)),
        "trace_after_pinching" => real(QuantumOptics.tr(rho_plus_pinched)),
        "api" => "QuantumOptics.sprepost superoperator applied to density operator",
    ),
)

negative = Dict(
    "ket_one_z_not_plus_one" => Dict(
        "pass" => abs(real(QuantumOptics.expect(sz, rho1)) + 1.0) <= TOL,
        "value" => real(QuantumOptics.expect(sz, rho1)),
    ),
    "pinching_not_identity_on_plus_state" => Dict(
        "pass" => QuantumOptics.tracedistance(rho_plus, rho_plus_pinched) > 0.49,
        "trace_distance" => QuantumOptics.tracedistance(rho_plus, rho_plus_pinched),
    ),
)

boundary = Dict(
    "identity_superoperator_preserves_state" => Dict(
        "pass" => QuantumOptics.tracedistance(rho0, rho0_identity) <= TOL,
        "trace_distance" => QuantumOptics.tracedistance(rho0, rho0_identity),
    ),
    "fidelity_self_boundary" => Dict(
        "pass" => abs(QuantumOptics.fidelity(rho0, rho0) - 1.0) <= TOL,
        "fidelity" => QuantumOptics.fidelity(rho0, rho0),
    ),
)

summary = Dict(
    "positive_all_pass" => section_all_pass(positive),
    "negative_all_pass" => section_all_pass(negative),
    "boundary_all_pass" => section_all_pass(boundary),
)
summary["all_pass"] = all(Bool(v) for v in values(summary))

result = Dict(
    "julia" => Dict(
        "ran" => true,
        "source_path" => "system_v4/probes/sim_quantumoptics_capability.py",
        "active_project" => Base.active_project(),
        "load_path" => join(Base.LOAD_PATH, ":"),
        "packages_used" => ["QuantumOptics", "JSON", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["QuantumOptics"],
        "reads_peer_result" => false,
    ),
    "package_versions" => Dict("QuantumOptics" => string(pkgversion(QuantumOptics))),
    "positive" => positive,
    "negative" => negative,
    "boundary" => boundary,
    "summary" => summary,
    "all_pass" => summary["all_pass"],
    "operation_sequence" => [
        "construct SpinBasis(1//2), basisstate kets, and density operators with QuantumOptics.dm",
        "compute sigmax/sigmaz expectations with QuantumOptics.expect",
        "construct a z-pinching superoperator with QuantumOptics.sprepost",
        "apply the superoperator to a density operator and check trace/expectation rows",
        "check trace-distance and fidelity boundary controls",
    ],
    "tool_function_needs" => [
        "QuantumOptics.SpinBasis",
        "QuantumOptics.basisstate",
        "QuantumOptics.dm",
        "QuantumOptics.sigmax",
        "QuantumOptics.sigmay",
        "QuantumOptics.sigmaz",
        "QuantumOptics.expect",
        "QuantumOptics.tr",
        "QuantumOptics.sprepost",
        "QuantumOptics.tracedistance",
        "QuantumOptics.fidelity",
    ],
)

println(JSON.json(result))
'''


def run_julia_probe() -> dict:
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = "@:@stdlib"
    proc = subprocess.run(
        [
            str(JULIA),
            "--startup-file=no",
            f"--project={JULIA_PROJECT}",
            "-e",
            JULIA_PROGRAM,
        ],
        cwd=REPO,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    parsed = json.loads(lines[-1]) if lines else {}
    parsed["subprocess"] = {
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
        "stdout_line_count": len(lines),
    }
    if proc.returncode != 0:
        parsed["summary"] = parsed.get("summary") or {"all_pass": False}
        parsed["all_pass"] = False
    return parsed


def main() -> int:
    result = run_julia_probe()
    result.update(
        {
            "name": "sim_quantumoptics_capability",
            "classification": classification,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "divergence_log": (
                "Capability isolation witness for QuantumOptics.jl: one-qubit "
                "states, density operators, observables, trace distance, "
                "fidelity, and superoperator channels are exercised here so "
                "S3/S4 packet routes can treat QuantumOptics as an admitted "
                "Julia QIT tool rather than a decorative import."
            ),
            "carrier_topology": "finite two-level Hilbert-space carrier represented by QuantumOptics SpinBasis kets, density operators, and superoperators",
            "pass_fail_predicate": "positive_all_pass, negative_all_pass, and boundary_all_pass must all be true; Julia subprocess must exit 0",
            "demotion_condition": "Demote QuantumOptics load-bearing claims if strict-carrier state, density, expectation, superoperator, trace-distance, or fidelity rows fail on rerun.",
        }
    )
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_quantumoptics_capability",
        target="Use as bounded QuantumOptics capability evidence before exact QuantumOptics state/channel packet routes.",
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in (RESULT_PATH, MATRIX_PATH):
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(result.get("summary", {}).get("all_pass")), "result_path": str(RESULT_PATH.relative_to(REPO))}, sort_keys=True))
    return 0 if result.get("summary", {}).get("all_pass") is True else 1


if __name__ == "__main__":
    sys.exit(main())
