#!/usr/bin/env python3
"""
sim_julia_dynamics_capability.py -- bounded Julia dynamics/QIT capability probe.

This probe isolates QuantumOptics.jl master-equation evolution and
Attractors.jl basin counting. It does not promote a scientific lego, bridge,
axis, or canonical dynamics claim.
"""

from __future__ import annotations

classification = "canonical"

import json
import os
import subprocess
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary

PINNED_FIXTURE = {
    "name": "single qubit amplitude damping",
    "hamiltonian": "H = 0.5*sigma_z",
    "collapse_operator": "sqrt(gamma)*sigma_minus",
    "gamma": 0.15,
    "rho0": "|+><+|",
    "t_start": 0.0,
    "t_stop": 5.0,
    "analytic_reference": "excited_population = 0.5*exp(-gamma*t); purity = 1 - 0.5*exp(-gamma*t) + 0.5*exp(-2*gamma*t)",
}

REPO = Path(__file__).resolve().parents[2]
JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = str(REPO / "system_v5" / "julia_carrier")
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULT_PATH = RESULTS_DIR / "julia_dynamics_capability_results.json"

_NOT_USED_REASON = (
    "not used: this bounded Julia dynamics capability probe isolates "
    "QuantumOptics.jl master-equation evolution and Attractors.jl basin "
    "counting only; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "julia_dynamics": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing capability under test: strict-carrier Julia "
            "QuantumOptics.jl and Attractors.jl API outputs decide all_pass."
        ),
    },
    "jax_dynamics": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
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
    "julia_dynamics": "load_bearing",
    "jax_dynamics": None,
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
using JSON3
using QuantumOptics
using Attractors
using DynamicalSystems
using StaticArrays

const TOL_POP = 1e-8
const TOL_TRACE = 1e-12
const TOL_BOUNDARY = 1e-12
const TOL_NO_DECAY_PURITY = 1e-10

function analytic_reference(tspan, gamma)
    a = exp.(-gamma .* tspan)
    Dict(
        "excited_population" => 0.5 .* a,
        "purity" => 1 .- 0.5 .* a .+ 0.5 .* (a .^ 2),
    )
end

function density_fixture(gamma)
    basis = SpinBasis(1//2)
    sigma_z = Operator(basis, ComplexF64[1 0; 0 -1])
    sigma_minus = Operator(basis, ComplexF64[0 1; 0 0])
    H = 0.5 * sigma_z
    psi_plus = (basisstate(basis, 1) + basisstate(basis, 2)) / sqrt(2)
    rho0 = dm(psi_plus)
    return basis, H, sigma_minus, rho0, sqrt(gamma) * sigma_minus
end

function evolve(gamma; collapse=:minus, t_stop=5.0, steps=101)
    basis, H, sigma_minus, rho0, L_minus = density_fixture(gamma)
    sigma_plus = dagger(sigma_minus)
    L = collapse == :plus ? sqrt(gamma) * sigma_plus : L_minus
    tspan = collect(range(0.0, t_stop; length=steps))
    tout, rhos = timeevolution.master(tspan, rho0, H, [L]; abstol=1e-12, reltol=1e-12)
    excited = [Float64(real(rho.data[2, 2])) for rho in rhos]
    traces = [Float64(abs(real(tr(rho)) - 1.0)) for rho in rhos]
    purities = [Float64(real(tr(rho * rho))) for rho in rhos]
    return tspan, rhos, rho0, excited, traces, purities
end

function quantumoptics_positive()
    gamma = 0.15
    tspan, rhos, rho0, excited, traces, purities = evolve(gamma)
    ref = analytic_reference(tspan, gamma)
    excited_errs = abs.(excited .- ref["excited_population"])
    purity_errs = abs.(purities .- ref["purity"])
    final_expected = ref["excited_population"][end]
    Dict(
        "pass" => maximum(excited_errs) <= TOL_POP &&
                  maximum(purity_errs) <= TOL_POP &&
                  maximum(traces) <= TOL_TRACE,
        "final_excited_population" => excited[end],
        "final_expected_excited_population" => final_expected,
        "final_abs_err" => abs(excited[end] - final_expected),
        "max_excited_curve_abs_err" => maximum(excited_errs),
        "max_purity_curve_abs_err" => maximum(purity_errs),
        "max_trace_abs_err" => maximum(traces),
        "api" => "QuantumOptics.timeevolution.master",
    )
end

function quantumoptics_negative()
    tspan0, rhos0, rho00, excited0, traces0, purities0 = evolve(0.0)
    no_decay_excited_err = maximum(abs.(excited0 .- 0.5))
    no_decay_purity_err = maximum(abs.(purities0 .- 1.0))

    gamma = 0.15
    tspan_wrong, rhos_wrong, rho0_wrong, excited_wrong, traces_wrong, purities_wrong = evolve(gamma; collapse=:plus)
    ref = analytic_reference(tspan_wrong, gamma)
    wrong_curve_deviation = maximum(abs.(excited_wrong .- ref["excited_population"]))

    Dict(
        "gamma_zero_no_decay" => Dict(
            "pass" => no_decay_excited_err <= TOL_TRACE &&
                      no_decay_purity_err <= TOL_NO_DECAY_PURITY &&
                      maximum(traces0) <= TOL_TRACE,
            "max_excited_deviation_from_initial" => no_decay_excited_err,
            "max_purity_deviation_from_initial" => no_decay_purity_err,
            "max_trace_abs_err" => maximum(traces0),
        ),
        "wrong_collapse_operator_differs" => Dict(
            "pass" => wrong_curve_deviation > 1e-3,
            "max_deviation_from_amplitude_damping_curve" => wrong_curve_deviation,
            "wrong_final_excited_population" => excited_wrong[end],
            "amplitude_damping_expected_final_excited_population" => ref["excited_population"][end],
        ),
    )
end

function quantumoptics_boundary()
    gamma = 0.15
    tspan, rhos, rho0, excited, traces, purities = evolve(gamma)
    t0_density_err = maximum(abs.(rhos[1].data .- rho0.data))

    large_gamma = 20.0
    tspan_fast, rhos_fast, rho0_fast, excited_fast, traces_fast, purities_fast = evolve(large_gamma; t_stop=5.0)
    Dict(
        "t0_returns_rho0" => Dict(
            "pass" => t0_density_err <= TOL_BOUNDARY,
            "max_density_abs_err" => t0_density_err,
        ),
        "large_gamma_to_ground_state" => Dict(
            "pass" => excited_fast[end] <= 1e-8 && maximum(traces_fast) <= TOL_TRACE,
            "gamma" => large_gamma,
            "final_excited_population" => excited_fast[end],
            "max_trace_abs_err" => maximum(traces_fast),
        ),
    )
end

function dissipative_map(z, p, n)
    x, y = z
    return x >= 0 ? SVector(1.0, 1.0) : SVector(-1.0, -1.0)
end

function attractors_positive()
    ds = DeterministicIteratedMap(dissipative_map, SVector(0.0, 0.0), nothing)
    attractor_sets = Dict(
        1 => StateSpaceSet([SVector(-1.0, -1.0)]),
        2 => StateSpaceSet([SVector(1.0, 1.0)]),
    )
    mapper = AttractorsViaProximity(ds, attractor_sets; Ttr=0)
    grid = (range(-1.5, 1.5; length=5), range(-1.5, 1.5; length=5))
    basins, attractors = basins_of_attraction(mapper, grid; show_progress=false)
    labels = unique(vec(basins))
    counts = Dict(string(Int(label)) => count(==(label), vec(basins)) for label in labels)
    Dict(
        "pass" => length(attractors) == 2 && length(labels) == 2,
        "api" => "Attractors.basins_of_attraction with DynamicalSystems.DeterministicIteratedMap",
        "basins_count" => length(attractors),
        "unique_basin_labels" => [Int(label) for label in labels],
        "basin_counts" => counts,
    )
end

function section_all_pass(section)
    return all(Bool(v["pass"]) for v in values(section))
end

positive = Dict(
    "quantumoptics_master_amplitude_damping" => quantumoptics_positive(),
    "attractors_two_fixed_point_basins" => attractors_positive(),
)
negative = quantumoptics_negative()
boundary = quantumoptics_boundary()

summary = Dict(
    "positive_all_pass" => section_all_pass(positive),
    "negative_all_pass" => section_all_pass(negative),
    "boundary_all_pass" => section_all_pass(boundary),
)
summary["all_pass"] = all(Bool(v) for v in values(summary))

result = Dict(
    "julia" => Dict(
        "ran" => true,
        "source_path" => "system_v4/probes/sim_julia_dynamics_capability.py",
        "active_project" => Base.active_project(),
        "load_path" => join(Base.LOAD_PATH, ":"),
        "packages_used" => ["JSON3", "QuantumOptics", "Attractors", "DynamicalSystems", "StaticArrays"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Attractors"],
        "reads_peer_result" => false,
    ),
    "package_versions" => Dict(
        "QuantumOptics" => string(pkgversion(QuantumOptics)),
        "Attractors" => string(pkgversion(Attractors)),
        "DynamicalSystems" => string(pkgversion(DynamicalSystems)),
        "StaticArrays" => string(pkgversion(StaticArrays)),
    ),
    "positive" => positive,
    "negative" => negative,
    "boundary" => boundary,
    "summary" => summary,
    "all_pass" => summary["all_pass"],
)

println("RESULT_JSON:" * JSON3.write(result))
'''


def run_julia_probe() -> dict:
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = "@:@stdlib"
    cmd = [
        JULIA,
        "--startup-file=no",
        f"--project={JULIA_PROJECT}",
        "-e",
        JULIA_PROGRAM,
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            payload = json.loads(line[len("RESULT_JSON:"):])
    if proc.returncode != 0 or payload is None:
        return {
            "ran": False,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
    payload["subprocess"] = {
        "command": "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier -e <embedded probe>",
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-1000:],
    }
    return payload


def main() -> int:
    julia_payload = run_julia_probe()
    ran = bool(julia_payload.get("julia", {}).get("ran"))
    if ran:
        positive = julia_payload["positive"]
        negative = julia_payload["negative"]
        boundary = julia_payload["boundary"]
        summary = julia_payload["summary"]
    else:
        positive = {}
        negative = {}
        boundary = {}
        summary = {
            "positive_all_pass": False,
            "negative_all_pass": False,
            "boundary_all_pass": False,
            "all_pass": False,
        }

    results = {
        "name": "sim_julia_dynamics_capability",
        "purpose": (
            "Bounded isolation probe for Julia dynamics/QIT capability: "
            "QuantumOptics.jl master-equation evolution on a closed-form "
            "amplitude damping fixture plus Attractors.jl two-basin map."
        ),
        "classification": classification,
        "pinned_fixture": PINNED_FIXTURE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "julia_payload": julia_payload,
        "tool_calls": [
            {
                "tool": "QuantumOptics",
                "qualified_api/function": "QuantumOptics.timeevolution.master",
                "input_object": "single-qubit amplitude damping density-matrix fixture",
                "output_object": "rho(t), excited population, trace, purity curve",
                "positive_case": "final excited population and full purity curve match closed-form analytic reference",
                "negative/erased_control": "gamma=0 no-decay control and sigma_plus wrong-collapse curve deviation",
                "boundary_case": "t=0 returns rho0 and large gamma reaches ground state",
                "demotion_condition": "demote if analytic curve, trace, negative controls, or boundaries fail on rerun",
                "gates": "summary.all_pass",
            },
            {
                "tool": "Attractors",
                "qualified_api/function": "Attractors.basins_of_attraction",
                "input_object": "separate pinned 2D dissipative map with two fixed points",
                "output_object": "two basin labels and basin counts",
                "positive_case": "basins count equals 2",
                "negative/erased_control": "not coupled to the QIT fixture; separate bounded dynamics capability surface",
                "boundary_case": "5x5 finite grid resolves both basins",
                "demotion_condition": "demote if basin count is not exactly 2",
                "gates": "summary.all_pass",
            },
        ],
        "operation_sequence": [
            "run strict-carrier Julia subprocess with JULIA_LOAD_PATH=@:@stdlib",
            "derive closed-form amplitude damping excited-population and purity references inside Julia",
            "run QuantumOptics.timeevolution.master on the pinned fixture",
            "run gamma=0 and sigma_plus negative controls",
            "run t=0 and large-gamma boundary controls",
            "run Attractors.basins_of_attraction on a separate pinned 2D dissipative map",
        ],
        "pass_fail_predicate": (
            "QuantumOptics positive, negative, and boundary controls must pass; "
            "Attractors must return exactly two basins; summary.all_pass must be true."
        ),
        "surviving_alternatives": [
            "This receipt proves only bounded Julia dynamics/QIT package capability, not a promoted dynamics lego or scientific coupling."
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_julia_dynamics_capability",
        target="Use as bounded Julia dynamics/QIT capability evidence before exact dynamics lego-fit or tool-coupling packets.",
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {RESULT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
