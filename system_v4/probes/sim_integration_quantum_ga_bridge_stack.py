#!/usr/bin/env python3
"""
sim_integration_quantum_ga_bridge_stack.py

Bridge lane for:
  numpy + scipy + pytorch + clifford + torch_ga + qutip + cirq + pennylane

Claim:
one small qubit state surface should be representable consistently across
classical numeric algebra, torch-based Bloch geometry, Clifford/GA carriers,
and nonclassical quantum simulators. This is the admission lane for scaling
these tools into broader sims without ad hoc per-run glue.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip
import torch
import torch_ga
from clifford import Cl
from scipy.linalg import expm


classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: the same one-qubit state must "
    "agree across dense linear algebra, torch Bloch geometry, Clifford/GA "
    "carriers, and quantum simulators instead of being re-glued per sim."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing dense state and density algebra"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponential state construction"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Bloch vector carrier and analytic gradient"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Clifford multivector embedding of the Bloch vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "load-bearing torch geometric algebra roundtrip for the Bloch vector"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing ket and density witness on the same qubit state"},
    "cirq": {"tried": True, "used": True, "reason": "load-bearing circuit/statevector witness on the same qubit state"},
    "pennylane": {"tried": True, "used": True, "reason": "load-bearing qnode state and gradient witness on the same qubit state"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
}

PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
KET0 = np.array([1.0, 0.0], dtype=np.complex128)
QML_DEV = qml.device("default.qubit", wires=1)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _rho(state: np.ndarray) -> np.ndarray:
    return np.outer(state, np.conjugate(state))


def _bloch_from_state(state: np.ndarray) -> np.ndarray:
    a, b = state
    return np.array(
        [
            2.0 * np.real(np.conjugate(a) * b),
            2.0 * np.imag(np.conjugate(a) * b),
            np.abs(a) ** 2 - np.abs(b) ** 2,
        ],
        dtype=np.float64,
    )


def _manual_state(theta: float, phi: float) -> np.ndarray:
    return np.array(
        [
            np.cos(theta / 2.0),
            np.exp(1.0j * phi) * np.sin(theta / 2.0),
        ],
        dtype=np.complex128,
    )


def _scipy_state(theta: float, phi: float) -> np.ndarray:
    unitary = expm(-0.5j * phi * PAULI_Z) @ expm(-0.5j * theta * PAULI_Y)
    return unitary @ KET0


def _qutip_state(theta: float, phi: float) -> np.ndarray:
    ket = ((-0.5j * phi * qutip.sigmaz()).expm() * (-0.5j * theta * qutip.sigmay()).expm()) * qutip.basis(2, 0)
    return np.asarray(ket.full(), dtype=np.complex128).reshape(-1)


def _qutip_bloch(state: np.ndarray) -> np.ndarray:
    qobj = qutip.Qobj(state.reshape(2, 1), dims=[[2], [1]])
    return np.array(
        [
            float(qutip.expect(qutip.sigmax(), qobj)),
            float(qutip.expect(qutip.sigmay(), qobj)),
            float(qutip.expect(qutip.sigmaz(), qobj)),
        ],
        dtype=np.float64,
    )


def _cirq_state(theta: float, phi: float) -> np.ndarray:
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.ry(theta)(qubit), cirq.rz(phi)(qubit))
    return np.asarray(cirq.Simulator().simulate(circuit).final_state_vector, dtype=np.complex128)


@qml.qnode(QML_DEV)
def _pennylane_state(theta: float, phi: float):
    qml.RY(theta, wires=0)
    qml.RZ(phi, wires=0)
    return qml.state()


@qml.qnode(QML_DEV)
def _pennylane_z_expectation(theta):
    qml.RY(theta, wires=0)
    return qml.expval(qml.PauliZ(0))


def _torch_bloch(theta: float, phi: float) -> tuple[torch.Tensor, float]:
    theta_t = torch.tensor(theta, dtype=torch.float64, requires_grad=True)
    phi_t = torch.tensor(phi, dtype=torch.float64)
    bloch = torch.stack(
        (
            torch.sin(theta_t) * torch.cos(phi_t),
            torch.sin(theta_t) * torch.sin(phi_t),
            torch.cos(theta_t),
        )
    )
    grad = torch.autograd.grad(bloch[2], theta_t)[0]
    return bloch.detach(), float(grad)


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    _, blades = Cl(3)
    multivector = vec[0] * blades["e1"] + vec[1] * blades["e2"] + vec[2] * blades["e3"]
    return np.asarray(multivector.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    algebra = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
    to_geo = torch_ga.TensorToGeometric(algebra, [1, 2, 3])
    to_tensor = torch_ga.GeometricToTensor(algebra, [1, 2, 3])
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    return to_tensor(to_geo(tensor)).detach().numpy().reshape(-1).astype(np.float64)


def _evaluate_case(theta: float, phi: float, *, negative: bool = False) -> dict[str, object]:
    manual = _manual_state(theta, phi)
    scipy_state = _scipy_state(theta, phi)
    qutip_state = _qutip_state(theta, phi)
    pennylane_state = np.asarray(_pennylane_state(theta, phi), dtype=np.complex128)
    if negative:
        cirq_state = _cirq_state(-theta, phi)
    else:
        cirq_state = _cirq_state(theta, phi)

    manual_rho = _rho(manual)
    scipy_rho = _rho(scipy_state)
    qutip_rho = _rho(qutip_state)
    cirq_rho = _rho(cirq_state)
    pennylane_rho = _rho(pennylane_state)
    manual_bloch = _bloch_from_state(manual)
    qutip_bloch = _qutip_bloch(qutip_state)
    torch_bloch, torch_grad = _torch_bloch(theta, phi)
    clifford_vec = _clifford_vector(manual_bloch)
    torch_ga_vec = _torch_ga_roundtrip(manual_bloch)
    qml_theta = qml.numpy.array(theta, requires_grad=True)
    pennylane_grad = float(qml.grad(_pennylane_z_expectation)(qml_theta))

    density_errors = {
        "numpy_vs_scipy": float(np.linalg.norm(manual_rho - scipy_rho)),
        "numpy_vs_qutip": float(np.linalg.norm(manual_rho - qutip_rho)),
        "numpy_vs_cirq": float(np.linalg.norm(manual_rho - cirq_rho)),
        "numpy_vs_pennylane": float(np.linalg.norm(manual_rho - pennylane_rho)),
    }
    tol = 1e-7 if not negative else 5e-2
    positive_checks = {
        "numpy_scipy_density_match": density_errors["numpy_vs_scipy"] < tol,
        "numpy_qutip_density_match": density_errors["numpy_vs_qutip"] < tol,
        "numpy_cirq_density_match": density_errors["numpy_vs_cirq"] < tol,
        "numpy_pennylane_density_match": density_errors["numpy_vs_pennylane"] < tol,
        "qutip_bloch_matches_torch": float(np.linalg.norm(qutip_bloch - torch_bloch.numpy())) < tol,
        "clifford_matches_torch": float(np.linalg.norm(clifford_vec - torch_bloch.numpy())) < tol,
        "torch_ga_roundtrip_matches": float(np.linalg.norm(torch_ga_vec - manual_bloch)) < tol,
        "pennylane_grad_matches_torch": abs(pennylane_grad - torch_grad) < tol,
    }
    if negative:
        positive_checks = {
            "mismatch_detected": density_errors["numpy_vs_cirq"] > 0.5,
            "classical_surfaces_still_match": density_errors["numpy_vs_scipy"] < 1e-7 and density_errors["numpy_vs_qutip"] < 1e-7,
            "gradient_still_matches": abs(pennylane_grad - torch_grad) < 1e-7,
        }

    return {
        "theta": theta,
        "phi": phi,
        "density_errors": density_errors,
        "manual_bloch": manual_bloch.tolist(),
        "qutip_bloch": qutip_bloch.tolist(),
        "torch_bloch": torch_bloch.numpy().tolist(),
        "clifford_bloch": clifford_vec.tolist(),
        "torch_ga_bloch": torch_ga_vec.tolist(),
        "torch_grad": torch_grad,
        "pennylane_grad": pennylane_grad,
        "checks": positive_checks,
        "all_pass": all(positive_checks.values()),
    }


if __name__ == "__main__":
    positive = _evaluate_case(theta=1.1, phi=-0.7)
    negative = _evaluate_case(theta=1.1, phi=-0.7, negative=True)
    boundary = _evaluate_case(theta=1e-6, phi=np.pi - 1e-6)

    summary = {
        "positive_all_pass": bool(positive["all_pass"]),
        "negative_all_pass": bool(negative["all_pass"]),
        "boundary_all_pass": bool(boundary["all_pass"]),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_integration_quantum_ga_bridge_stack",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "quantum_ga_bridge_stack_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
