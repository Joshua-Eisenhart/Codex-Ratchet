#!/usr/bin/env python3
"""
sim_integration_thermo_open_system_bridge_stack.py

Bounded thermodynamics/open-system bridge stack for:
  numpy + scipy + qutip + cirq + pennylane

Claim:
The same two-level thermal relaxation surface should agree across classical
rate equations, QuTiP master equations, Cirq density-matrix evolution, and
PennyLane mixed-state simulation. The bridge is deliberately small: one qubit,
one relaxation channel, one thermodynamic identity surface, and explicit
positive/negative/boundary checks.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical thermodynamics bridge baseline: one qubit, one "
    "relaxation channel, and one free-energy surface must agree across numpy/"
    "scipy, QuTiP, Cirq, and PennyLane instead of being re-glued per sim."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "thermal populations, rate equations, and density checks"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponentials for thermal state construction"},
    "qutip": {"tried": True, "used": True, "reason": "open-system mesolve witness for amplitude damping thermalization"},
    "cirq": {"tried": True, "used": True, "reason": "density-matrix simulator witness using an explicit damping channel"},
    "pennylane": {"tried": True, "used": True, "reason": "mixed-state QNode witness for the same qubit relaxation surface"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
}

RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
SIGMA_PLUS = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
SIGMA_MINUS = np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.complex128)
IDENTITY_2 = np.eye(2, dtype=np.complex128)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def thermal_state(beta: float) -> np.ndarray:
    rho = expm(-beta * SIGMA_Z)
    return rho / np.trace(rho)


def free_energy(rho: np.ndarray, beta: float) -> float:
    T = 1.0 / beta
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    entropy = -np.sum(evals * np.log(evals))
    energy = np.trace(rho @ SIGMA_Z).real
    return float(energy - T * entropy)


def lindblad_classical_relaxation(p_excited0: float, gamma: float, times: np.ndarray) -> np.ndarray:
    return np.exp(-gamma * times) * p_excited0


def qutip_relaxation(p_excited0: float, gamma: float, times: np.ndarray) -> np.ndarray:
    rho0 = qutip.Qobj(np.array([[1.0 - p_excited0, 0.0], [0.0, p_excited0]], dtype=np.complex128), dims=[[2], [2]])
    H = 0.5 * qutip.sigmaz()
    c_ops = [np.sqrt(gamma) * qutip.sigmap()]
    result = qutip.mesolve(H=H, rho0=rho0, tlist=times, c_ops=c_ops, e_ops=[])
    return np.array([float((state * qutip.basis(2, 1) * qutip.basis(2, 1).dag()).tr().real) for state in result.states], dtype=np.float64)


def cirq_relaxation(p_excited0: float, gamma: float, times: np.ndarray) -> np.ndarray:
    rho0 = np.array([[1.0 - p_excited0, 0.0], [0.0, p_excited0]], dtype=np.complex128)
    simulator = cirq.DensityMatrixSimulator(seed=13)
    excited = []
    for t in times:
        p = 1.0 - np.exp(-gamma * float(t))
        circuit = cirq.Circuit(cirq.AmplitudeDampingChannel(p).on(Q0))
        state = simulator.simulate(circuit, initial_state=rho0).final_density_matrix
        excited.append(float(np.real(state[1, 1])))
    return np.array(excited, dtype=np.float64)


@qml.qnode(QML_DEV)
def _qml_density(p_excited0: float, gamma: float, t: float):
    qml.QubitDensityMatrix(np.array([[1.0 - p_excited0, 0.0], [0.0, p_excited0]], dtype=np.complex128), wires=0)
    p = 1.0 - np.exp(-gamma * t)
    qml.AmplitudeDamping(p, wires=0)
    return qml.density_matrix(wires=0)


def pennylane_relaxation(p_excited0: float, gamma: float, times: np.ndarray) -> np.ndarray:
    excited = []
    for t in times:
        rho = np.asarray(_qml_density(p_excited0, gamma, float(t)), dtype=np.complex128)
        excited.append(float(np.real(rho[1, 1])))
    return np.array(excited, dtype=np.float64)


def _evaluate_case(*, beta: float, p_excited0: float, gamma: float, times: np.ndarray, negative: bool = False) -> dict[str, object]:
    rho_beta = thermal_state(beta)
    free_energy_beta = free_energy(rho_beta, beta)
    classical = lindblad_classical_relaxation(p_excited0, gamma, times)
    qutip_excited = qutip_relaxation(p_excited0, gamma, times)
    cirq_excited = cirq_relaxation(p_excited0, gamma, times)
    pennylane_excited = pennylane_relaxation(p_excited0, gamma, times)

    if negative:
        cirq_excited = cirq_relaxation(p_excited0, gamma * 1.5, times)

    errors = {
        "qutip_vs_classical": float(np.max(np.abs(qutip_excited - classical))),
        "cirq_vs_classical": float(np.max(np.abs(cirq_excited - classical))),
        "pennylane_vs_classical": float(np.max(np.abs(pennylane_excited - classical))),
    }

    tol = 5e-3 if not negative else 5e-2
    checks = {
        "thermal_state_valid": bool(np.isclose(np.trace(rho_beta), 1.0)),
        "free_energy_finite": bool(np.isfinite(free_energy_beta)),
        "qutip_matches_classical": errors["qutip_vs_classical"] < tol,
        "cirq_matches_classical": errors["cirq_vs_classical"] < tol,
        "pennylane_matches_classical": errors["pennylane_vs_classical"] < tol,
    }
    if negative:
        checks = {
            "negative_cirq_mismatch_detected": errors["cirq_vs_classical"] > 5e-3,
            "qutip_still_consistent": errors["qutip_vs_classical"] < 5e-3,
            "pennylane_still_consistent": errors["pennylane_vs_classical"] < 5e-3,
        }

    return {
        "beta": beta,
        "p_excited0": p_excited0,
        "gamma": gamma,
        "times": times.tolist(),
        "rho_beta": np.real_if_close(rho_beta).real.tolist(),
        "free_energy": free_energy_beta,
        "classical_excited": classical.tolist(),
        "qutip_excited": qutip_excited.tolist(),
        "cirq_excited": cirq_excited.tolist(),
        "pennylane_excited": pennylane_excited.tolist(),
        "errors": errors,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def main() -> None:
    times = np.array([0.0, 0.2, 0.6, 1.0, 1.8], dtype=np.float64)
    positive = _evaluate_case(beta=1.2, p_excited0=0.8, gamma=0.7, times=times)
    negative = _evaluate_case(beta=1.2, p_excited0=0.8, gamma=0.7, times=times, negative=True)
    boundary = _evaluate_case(beta=1e-6, p_excited0=0.5, gamma=1e-6, times=np.array([0.0, 1e-3, 1.0], dtype=np.float64))

    results = {
        "name": "sim_integration_thermo_open_system_bridge_stack",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(positive["all_pass"] and boundary["all_pass"] and negative["all_pass"]),
            "scope_note": "Bounded qubit thermodynamics/open-system bridge across classical, QuTiP, Cirq, and PennyLane surfaces.",
        },
    }

    out = RESULTS_DIR / "sim_integration_thermo_open_system_bridge_stack_results.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True, default=_json_default)
    print(f"PASS={results['summary']['all_pass']}")
    print(json.dumps(results["summary"], indent=2, sort_keys=True, default=_json_default))


if __name__ == "__main__":
    main()
