#!/usr/bin/env python3
"""
PennyLane classical-to-nonclassical bridge probe
=================================================

Bridge a classical parameter/observable surface to a PennyLane QNode on the
same 1-qubit system, then cross-check the QNode against direct linear algebra.

The probe is deliberately small:
  - a single qubit
  - a classical observable O = a X + b Z
  - a parameterized circuit with RY/RZ rotations
  - direct matrix evaluation using scipy.linalg.expm
  - PennyLane expectation values and gradients as the load-bearing witness

Positive: QNode expectation matches direct linear algebra for several cases.
Negative: the wrong observable and wrong rotation order do not match.
Boundary: zero-parameter circuit reduces to the known |0> expectation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np
import pennylane as qml
import pennylane.numpy as pnp
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: this probe connects classical "
    "parameter/observable handling to a PennyLane QNode and checks the same "
    "small system against direct linear algebra. PennyLane is a witness surface "
    "for the bridge, not a contract load-bearing baseline."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "classical parameter handling, matrix algebra, and result serialization",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "direct unitary construction with matrix exponentials for the bridge check",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "QNode and gradient witness for the classical-to-nonclassical bridge",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pennylane": "supportive",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state",
    "sim_results",
    "sim_pennylane_classical_qnode_bridge_results.json",
)

X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


@dataclass(frozen=True)
class BridgeCase:
    theta: float
    phi: float
    obs_a: float
    obs_b: float


def observable_matrix(a: float, b: float) -> np.ndarray:
    return a * X + b * Z


def direct_state(theta: float, phi: float) -> np.ndarray:
    """Classical linear-algebra state for the same circuit used by the QNode."""
    u_ry = expm(-0.5j * theta * Y)
    u_rz = expm(-0.5j * phi * Z)
    return u_rz @ u_ry @ np.array([1.0, 0.0], dtype=complex)


def direct_expectation(theta: float, phi: float, a: float, b: float) -> float:
    psi = direct_state(theta, phi)
    obs = observable_matrix(a, b)
    return float(np.real(np.vdot(psi, obs @ psi)))


DEV = qml.device("default.qubit", wires=1, shots=None)


@qml.qnode(DEV, interface="autograd", diff_method="parameter-shift")
def qnode_expectation(params, obs):
    qml.RY(params[0], wires=0)
    qml.RZ(params[1], wires=0)
    return qml.expval(qml.Hermitian(obs, wires=0))


def qnode_gradient(params, obs):
    grad_fn = qml.grad(lambda p: qnode_expectation(p, obs))
    trainable = pnp.array(params, requires_grad=True)
    return np.array(grad_fn(trainable), dtype=float)


def direct_gradient(theta: float, phi: float, a: float, b: float) -> np.ndarray:
    """Finite-difference gradient for the same circuit, used only as a sanity check."""
    eps = 1e-7
    base = direct_expectation(theta, phi, a, b)
    d_theta = (direct_expectation(theta + eps, phi, a, b) - base) / eps
    d_phi = (direct_expectation(theta, phi + eps, a, b) - base) / eps
    return np.array([d_theta, d_phi], dtype=float)


def run_positive_tests():
    cases = [
        BridgeCase(theta=0.37, phi=-0.22, obs_a=0.6, obs_b=-0.4),
        BridgeCase(theta=1.11, phi=0.48, obs_a=-0.3, obs_b=0.8),
        BridgeCase(theta=0.91, phi=1.27, obs_a=0.1, obs_b=0.9),
    ]

    rows = []
    ok = True
    for case in cases:
        params = pnp.array([case.theta, case.phi], requires_grad=True)
        obs = observable_matrix(case.obs_a, case.obs_b)
        qml_val = float(qnode_expectation(params, obs))
        direct_val = direct_expectation(case.theta, case.phi, case.obs_a, case.obs_b)
        grad_qml = qnode_gradient(params, obs)
        grad_direct = direct_gradient(case.theta, case.phi, case.obs_a, case.obs_b)
        row = {
            "case": case.__dict__,
            "qnode_expectation": qml_val,
            "direct_expectation": direct_val,
            "expectation_gap": abs(qml_val - direct_val),
            "qml_grad": grad_qml.tolist(),
            "direct_grad": grad_direct.tolist(),
            "grad_gap": float(np.max(np.abs(grad_qml - grad_direct))),
        }
        row["pass"] = bool(row["expectation_gap"] < 1e-9 and row["grad_gap"] < 5e-5)
        ok = ok and row["pass"]
        rows.append(row)

    return {"pass": ok, "cases": rows}


def run_negative_tests():
    case = BridgeCase(theta=0.52, phi=-0.73, obs_a=0.5, obs_b=-0.25)
    params = np.array([case.theta, case.phi], dtype=float)
    obs = observable_matrix(case.obs_a, case.obs_b)
    qml_val = float(qnode_expectation(params, obs))

    wrong_obs = observable_matrix(case.obs_b, case.obs_a)
    wrong_val = float(qnode_expectation(params, wrong_obs))

    swapped_params = np.array([case.phi, case.theta], dtype=float)
    swapped_val = float(qnode_expectation(swapped_params, obs))

    return {
        "wrong_observable_gap": abs(qml_val - wrong_val),
        "swapped_parameter_gap": abs(qml_val - swapped_val),
        "pass": bool(abs(qml_val - wrong_val) > 1e-3 and abs(qml_val - swapped_val) > 1e-3),
    }


def run_boundary_tests():
    params = np.array([0.0, 0.0], dtype=float)
    obs = observable_matrix(0.2, -0.7)
    qml_val = float(qnode_expectation(params, obs))
    direct_val = direct_expectation(0.0, 0.0, 0.2, -0.7)

    return {
        "zero_params_expectation": qml_val,
        "direct_zero_params_expectation": direct_val,
        "pass": bool(abs(qml_val - direct_val) < 1e-10 and abs(qml_val + 0.7) < 1e-10),
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    overall_pass = positive["pass"] and negative["pass"] and boundary["pass"]
    results = {
        "name": "sim_pennylane_classical_qnode_bridge",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)

    print(json.dumps(results, indent=2))
    print(f"Results written to {RESULTS_PATH}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
