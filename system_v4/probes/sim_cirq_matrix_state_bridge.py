#!/usr/bin/env python3
"""
sim_cirq_matrix_state_bridge.py
===============================

Small classical-to-nonclassical bridge probe that compares an explicit
matrix/state calculation against a Cirq circuit/simulator on the same
2-qubit system.

The bridge is intentionally bounded:
  - build a Bell pair with local phase rotations
  - compare a numpy/scipy matrix reference against Cirq simulation
  - show a controlled contrast when the circuit wiring is intentionally
    altered
  - verify the identity boundary case
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import cirq
import numpy as np
from scipy.linalg import expm, sqrtm

classification = "canonical"
divergence_log = (
    "Bridge baseline: this probe compares explicit matrix-state evolution "
    "against Cirq circuit simulation on the same 2-qubit system, so the "
    "matrix reference and the circuit simulator must agree for the intended "
    "wiring and intentionally contrast for the control-target swap case."
)
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "statevector, density-matrix, and overlap arithmetic for the matrix reference",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential and square-root routines for the reference unitary and fidelity checks",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "circuit construction and simulator readout for the bridge comparison",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "cirq": "load_bearing",
}

OUT_PATH = (
    os.path.dirname(os.path.abspath(__file__))
    + "/a2_state/sim_results/cirq_matrix_state_bridge_results.json"
)

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
CNOT_01 = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=complex,
)

Q0, Q1 = cirq.LineQubit.range(2)


def _rz(theta: float) -> np.ndarray:
    return expm(-0.5j * theta * Z)


def _rx(theta: float) -> np.ndarray:
    return expm(-0.5j * theta * X)


def _density(vec: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=complex).reshape(-1)
    return np.outer(vec, vec.conj())


def _fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    root = sqrtm(rho)
    inner = root @ sigma @ root
    vals = np.linalg.eigvalsh((inner + inner.conj().T) / 2.0)
    vals = np.maximum(np.real(vals), 0.0)
    return float(np.real(np.trace(sqrtm((inner + inner.conj().T) / 2.0)))) ** 2 if vals.size else 0.0


def _concurrence(rho: np.ndarray) -> float:
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    yy = np.kron(sy, sy)
    rho_tilde = yy @ rho.conj() @ yy
    evals = np.linalg.eigvals(rho @ rho_tilde)
    evals = np.sort(np.real(evals))[::-1]
    evals = np.maximum(evals, 0.0)
    roots = np.sqrt(evals)
    return float(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def matrix_reference(theta: float, phi: float) -> np.ndarray:
    psi = np.array([1, 0, 0, 0], dtype=complex)
    psi = np.kron(H, I2) @ psi
    psi = CNOT_01 @ psi
    psi = np.kron(_rz(theta), _rx(phi)) @ psi
    return psi


def cirq_reference(theta: float, phi: float, swapped: bool = False) -> np.ndarray:
    if swapped:
        circuit = cirq.Circuit(
            cirq.H(Q0),
            cirq.CNOT(Q1, Q0),
            cirq.rz(theta).on(Q0),
            cirq.rx(phi).on(Q1),
        )
    else:
        circuit = cirq.Circuit(
            cirq.H(Q0),
            cirq.CNOT(Q0, Q1),
            cirq.rz(theta).on(Q0),
            cirq.rx(phi).on(Q1),
        )
    sim = cirq.Simulator(seed=42)
    result = sim.simulate(circuit)
    return np.asarray(result.final_state_vector, dtype=complex)


def _metrics(theta: float, phi: float, swapped: bool = False) -> dict:
    psi_matrix = matrix_reference(theta, phi)
    psi_cirq = cirq_reference(theta, phi, swapped=swapped)
    rho_matrix = _density(psi_matrix)
    rho_cirq = _density(psi_cirq)
    fid = _fidelity(rho_matrix, rho_cirq)
    trace_dist = float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(rho_matrix - rho_cirq))))
    return {
        "theta": float(theta),
        "phi": float(phi),
        "swapped": bool(swapped),
        "statevector_overlap": float(abs(np.vdot(psi_matrix, psi_cirq)) ** 2),
        "fidelity": float(fid),
        "trace_distance": trace_dist,
        "concurrence": _concurrence(rho_matrix),
        "matrix_state": [complex(v) for v in psi_matrix],
        "cirq_state": [complex(v) for v in psi_cirq],
    }


def run_positive_tests() -> dict:
    theta = np.pi / 3
    phi = np.pi / 5
    data = _metrics(theta, phi, swapped=False)
    data["pass"] = bool(data["fidelity"] > 0.999999 and data["trace_distance"] < 1e-6)
    return {"bell_phase_bridge": data}


def run_negative_tests() -> dict:
    theta = np.pi / 3
    phi = np.pi / 5
    data = _metrics(theta, phi, swapped=True)
    data["pass"] = bool(data["fidelity"] < 0.95 and data["trace_distance"] > 0.05)
    return {"control_target_swap_contrast": data}


def run_boundary_tests() -> dict:
    theta = 0.0
    phi = 0.0
    data = _metrics(theta, phi, swapped=False)
    data["pass"] = bool(
        data["fidelity"] > 0.999999
        and data["trace_distance"] < 1e-6
        and abs(data["concurrence"] - 1.0) < 1e-6
    )
    data["boundary_nonclassical"] = True
    return {"identity_boundary_bell_state": data}


def _all_pass(section: dict) -> bool:
    return all(bool(v.get("pass", False)) for v in section.values())


def run() -> dict:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())
    result = {
        "name": "sim_cirq_matrix_state_bridge",
        "purpose": "Compare matrix-state evolution against Cirq simulator output on the same 2-qubit bridge.",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "overall_pass": bool(summary["all_pass"]),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)
    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return result


if __name__ == "__main__":
    run()
