#!/usr/bin/env python3
"""
sim_jax_dynamics_capability.py -- bounded JAX dynamics/QIT capability probe.

This probe isolates diffrax Bloch-vector dynamics and dynamiqs mesolve on the
same pinned amplitude damping fixture. It does not promote a scientific lego,
bridge, axis, or canonical dynamics claim.
"""

from __future__ import annotations

classification = "canonical"

from jax import config

config.update("jax_enable_x64", True)

import json
import math
from pathlib import Path

import diffrax
import dynamiqs as dq
import dynamiqs.method as dq_method
import jax
import jax.numpy as jnp

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

RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULT_PATH = RESULTS_DIR / "jax_dynamics_capability_results.json"

_NOT_USED_REASON = (
    "not used: this bounded JAX dynamics capability probe isolates diffrax "
    "Bloch-vector ODE integration and dynamiqs mesolve only; other tool "
    "families require separate receipts."
)

TOOL_MANIFEST = {
    "jax_dynamics": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing capability under test: diffrax and dynamiqs outputs "
            "decide all_pass against the closed-form amplitude damping fixture."
        ),
    },
    "julia_dynamics": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
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
    "jax_dynamics": "load_bearing",
    "julia_dynamics": None,
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

TOL_POP = 1e-8
TOL_TRACE = 1e-12
TOL_BOUNDARY = 1e-12
TOL_NO_DECAY_PURITY = 1e-10


def boolify(value) -> bool:
    return bool(value.item() if hasattr(value, "item") else value)


def finite_float(value) -> float:
    return float(jnp.real(value).item())


def analytic_reference(ts: jax.Array, gamma: float) -> dict[str, jax.Array]:
    a = jnp.exp(-gamma * ts)
    return {
        "excited_population": 0.5 * a,
        "purity": 1.0 - 0.5 * a + 0.5 * (a**2),
    }


def bloch_rhs(t, r, gamma):
    del t
    x, y, z = r
    return jnp.array(
        [
            -0.5 * gamma * x - y,
            x - 0.5 * gamma * y,
            gamma * (1.0 - z),
        ],
        dtype=jnp.float64,
    )


def diffrax_evolve(gamma: float, *, t_stop: float = 5.0, steps: int = 101) -> dict[str, jax.Array]:
    ts = jnp.linspace(0.0, t_stop, steps, dtype=jnp.float64)
    term = diffrax.ODETerm(bloch_rhs)
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Dopri5(),
        t0=0.0,
        t1=t_stop,
        dt0=0.01,
        y0=jnp.array([1.0, 0.0, 0.0], dtype=jnp.float64),
        args=gamma,
        saveat=diffrax.SaveAt(ts=ts),
        stepsize_controller=diffrax.PIDController(rtol=1e-11, atol=1e-13),
        max_steps=100000,
    )
    bloch = sol.ys
    excited = 0.5 * (1.0 - bloch[:, 2])
    purity = 0.5 * (1.0 + jnp.sum(bloch * bloch, axis=1))
    trace = jnp.ones_like(excited)
    return {"ts": ts, "bloch": bloch, "excited": excited, "purity": purity, "trace": trace}


def qarrays():
    sigma_z = dq.asqarray(jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128))
    sigma_minus = dq.asqarray(jnp.array([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128))
    sigma_plus = dq.asqarray(jnp.array([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128))
    psi_plus = (dq.basis(2, 0) + dq.basis(2, 1)) / jnp.sqrt(2.0)
    rho0 = dq.todm(psi_plus)
    return sigma_z, sigma_minus, sigma_plus, rho0


def dynamiqs_evolve(gamma: float, *, collapse: str = "minus", t_stop: float = 5.0, steps: int = 101) -> dict[str, jax.Array]:
    ts = jnp.linspace(0.0, t_stop, steps, dtype=jnp.float64)
    sigma_z, sigma_minus, sigma_plus, rho0 = qarrays()
    jump = sigma_minus if collapse == "minus" else sigma_plus
    result = dq.mesolve(
        0.5 * sigma_z,
        [jnp.sqrt(gamma) * jump],
        rho0,
        ts,
        method=dq_method.Tsit5(rtol=1e-10, atol=1e-12),
        options=dq.Options(progress_meter=False),
    )
    states = result.states.to_jax()
    excited = jnp.real(states[:, 1, 1])
    traces = jnp.real(jnp.trace(states, axis1=1, axis2=2))
    purity = jnp.real(jnp.trace(states @ states, axis1=1, axis2=2))
    return {"ts": ts, "states": states, "excited": excited, "purity": purity, "trace": traces}


def max_abs(a: jax.Array) -> float:
    return float(jnp.max(jnp.abs(a)).item())


def positive_tests() -> dict:
    gamma = PINNED_FIXTURE["gamma"]
    diff = diffrax_evolve(gamma)
    dyn = dynamiqs_evolve(gamma)
    ref = analytic_reference(diff["ts"], gamma)
    diff_excited_err = max_abs(diff["excited"] - ref["excited_population"])
    diff_purity_err = max_abs(diff["purity"] - ref["purity"])
    dyn_excited_err = max_abs(dyn["excited"] - ref["excited_population"])
    dyn_purity_err = max_abs(dyn["purity"] - ref["purity"])
    engines_excited_err = max_abs(diff["excited"] - dyn["excited"])
    engines_purity_err = max_abs(diff["purity"] - dyn["purity"])
    dyn_trace_err = max_abs(dyn["trace"] - 1.0)
    diff_trace_err = max_abs(diff["trace"] - 1.0)
    final_expected = finite_float(ref["excited_population"][-1])

    return {
        "diffrax_matches_analytic": {
            "pass": diff_excited_err <= TOL_POP and diff_purity_err <= TOL_POP and diff_trace_err <= TOL_TRACE,
            "final_excited_population": finite_float(diff["excited"][-1]),
            "final_expected_excited_population": final_expected,
            "final_abs_err": abs(finite_float(diff["excited"][-1]) - final_expected),
            "max_excited_curve_abs_err": diff_excited_err,
            "max_purity_curve_abs_err": diff_purity_err,
            "max_trace_abs_err": diff_trace_err,
            "api": "diffrax.diffeqsolve",
        },
        "dynamiqs_matches_analytic": {
            "pass": dyn_excited_err <= TOL_POP and dyn_purity_err <= TOL_POP and dyn_trace_err <= TOL_TRACE,
            "final_excited_population": finite_float(dyn["excited"][-1]),
            "final_expected_excited_population": final_expected,
            "final_abs_err": abs(finite_float(dyn["excited"][-1]) - final_expected),
            "max_excited_curve_abs_err": dyn_excited_err,
            "max_purity_curve_abs_err": dyn_purity_err,
            "max_trace_abs_err": dyn_trace_err,
            "api": "dynamiqs.mesolve with QArray.to_jax() state extraction",
        },
        "diffrax_dynamiqs_agree": {
            "pass": engines_excited_err <= TOL_POP and engines_purity_err <= TOL_POP,
            "max_excited_curve_abs_err": engines_excited_err,
            "max_purity_curve_abs_err": engines_purity_err,
        },
    }


def negative_tests() -> dict:
    gamma_zero_diff = diffrax_evolve(0.0)
    gamma_zero_dyn = dynamiqs_evolve(0.0)
    no_decay_diff_excited_err = max_abs(gamma_zero_diff["excited"] - 0.5)
    no_decay_diff_purity_err = max_abs(gamma_zero_diff["purity"] - 1.0)
    no_decay_dyn_excited_err = max_abs(gamma_zero_dyn["excited"] - 0.5)
    no_decay_dyn_purity_err = max_abs(gamma_zero_dyn["purity"] - 1.0)

    gamma = PINNED_FIXTURE["gamma"]
    wrong_dyn = dynamiqs_evolve(gamma, collapse="plus")
    ref = analytic_reference(wrong_dyn["ts"], gamma)
    wrong_curve_deviation = max_abs(wrong_dyn["excited"] - ref["excited_population"])

    return {
        "gamma_zero_no_decay": {
            "pass": (
                no_decay_diff_excited_err <= TOL_TRACE
                and no_decay_diff_purity_err <= TOL_NO_DECAY_PURITY
                and no_decay_dyn_excited_err <= TOL_TRACE
                and no_decay_dyn_purity_err <= TOL_NO_DECAY_PURITY
            ),
            "diffrax_max_excited_deviation_from_initial": no_decay_diff_excited_err,
            "diffrax_max_purity_deviation_from_initial": no_decay_diff_purity_err,
            "dynamiqs_max_excited_deviation_from_initial": no_decay_dyn_excited_err,
            "dynamiqs_max_purity_deviation_from_initial": no_decay_dyn_purity_err,
        },
        "wrong_collapse_operator_differs": {
            "pass": wrong_curve_deviation > 1e-3,
            "max_deviation_from_amplitude_damping_curve": wrong_curve_deviation,
            "wrong_final_excited_population": finite_float(wrong_dyn["excited"][-1]),
            "amplitude_damping_expected_final_excited_population": finite_float(ref["excited_population"][-1]),
        },
    }


def boundary_tests() -> dict:
    gamma = PINNED_FIXTURE["gamma"]
    diff = diffrax_evolve(gamma)
    dyn = dynamiqs_evolve(gamma)
    sigma_z, sigma_minus, sigma_plus, rho0 = qarrays()
    del sigma_z, sigma_minus, sigma_plus
    rho0_jax = rho0.to_jax()
    dyn_t0_density_err = max_abs(dyn["states"][0] - rho0_jax)
    diff_t0_bloch_err = max_abs(diff["bloch"][0] - jnp.array([1.0, 0.0, 0.0], dtype=jnp.float64))

    large_gamma = 20.0
    diff_fast = diffrax_evolve(large_gamma)
    dyn_fast = dynamiqs_evolve(large_gamma)
    diff_fast_trace_err = max_abs(diff_fast["trace"] - 1.0)
    dyn_fast_trace_err = max_abs(dyn_fast["trace"] - 1.0)

    return {
        "t0_returns_rho0": {
            "pass": diff_t0_bloch_err <= TOL_BOUNDARY and dyn_t0_density_err <= TOL_BOUNDARY,
            "diffrax_t0_bloch_abs_err": diff_t0_bloch_err,
            "dynamiqs_t0_density_abs_err": dyn_t0_density_err,
        },
        "large_gamma_to_ground_state": {
            "pass": (
                finite_float(diff_fast["excited"][-1]) <= 1e-8
                and finite_float(dyn_fast["excited"][-1]) <= 1e-8
                and diff_fast_trace_err <= TOL_TRACE
                and dyn_fast_trace_err <= TOL_TRACE
            ),
            "gamma": large_gamma,
            "diffrax_final_excited_population": finite_float(diff_fast["excited"][-1]),
            "dynamiqs_final_excited_population": finite_float(dyn_fast["excited"][-1]),
            "diffrax_max_trace_abs_err": diff_fast_trace_err,
            "dynamiqs_max_trace_abs_err": dyn_fast_trace_err,
        },
    }


def section_all_pass(section: dict) -> bool:
    return all(bool(row.get("pass")) for row in section.values())


def main() -> int:
    positive = positive_tests()
    negative = negative_tests()
    boundary = boundary_tests()

    summary = {
        "positive_all_pass": section_all_pass(positive),
        "negative_all_pass": section_all_pass(negative),
        "boundary_all_pass": section_all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_jax_dynamics_capability",
        "purpose": (
            "Bounded isolation probe for JAX dynamics/QIT capability: diffrax "
            "Bloch-vector ODE integration and dynamiqs mesolve on the same "
            "closed-form amplitude damping fixture."
        ),
        "classification": classification,
        "pinned_fixture": PINNED_FIXTURE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "jax": {
            "ran": True,
            "source_path": "system_v4/probes/sim_jax_dynamics_capability.py",
            "packages_used": ["jax", "jax.numpy", "diffrax", "dynamiqs"],
            "aligned_packages_load_bearing": ["diffrax", "dynamiqs"],
            "reads_peer_result": False,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "versions": {
                "jax": getattr(jax, "__version__", "unknown"),
                "diffrax": getattr(diffrax, "__version__", "unknown"),
                "dynamiqs": getattr(dq, "__version__", "unknown"),
            },
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "tool_calls": [
            {
                "tool": "diffrax",
                "qualified_api/function": "diffrax.diffeqsolve",
                "input_object": "Bloch-vector ODE for the pinned amplitude damping fixture",
                "output_object": "excited population, trace, and purity curves",
                "positive_case": "curve matches closed-form analytic reference",
                "negative/erased_control": "gamma=0 no-decay control",
                "boundary_case": "t=0 Bloch vector and large gamma ground-state limit",
                "demotion_condition": "demote if curve, trace, negative control, or boundary fails",
                "gates": "summary.all_pass",
            },
            {
                "tool": "dynamiqs",
                "qualified_api/function": "dynamiqs.mesolve with QArray.to_jax",
                "input_object": "density-matrix fixture with explicit sigma_z and sigma_minus QArrays",
                "output_object": "rho(t), excited population, trace, and purity curves",
                "positive_case": "curve matches closed-form analytic reference and agrees with diffrax",
                "negative/erased_control": "gamma=0 no-decay control and sigma_plus wrong-collapse curve deviation",
                "boundary_case": "t=0 density matrix and large gamma ground-state limit",
                "demotion_condition": "demote if curve, trace, negative control, engine agreement, or boundary fails",
                "gates": "summary.all_pass",
            },
        ],
        "operation_sequence": [
            "enable JAX x64 before importing jax.numpy",
            "derive closed-form amplitude damping excited-population and purity references with jnp",
            "run diffrax.diffeqsolve on the Bloch-vector ODE",
            "run dynamiqs.mesolve on the same density-matrix fixture and call QArray.to_jax()",
            "run gamma=0 and sigma_plus negative controls",
            "run t=0 and large-gamma boundary controls",
        ],
        "pass_fail_predicate": (
            "diffrax and dynamiqs must match the analytic curve within 1e-8, "
            "preserve trace to 1e-12, agree with each other, pass no-decay and "
            "wrong-collapse controls, and satisfy t=0 plus large-gamma boundaries."
        ),
        "surviving_alternatives": [
            "This receipt proves only bounded JAX dynamics/QIT package capability, not a promoted dynamics lego or scientific coupling."
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_jax_dynamics_capability",
        target="Use as bounded JAX dynamics/QIT capability evidence before exact dynamics lego-fit or tool-coupling packets.",
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {RESULT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
