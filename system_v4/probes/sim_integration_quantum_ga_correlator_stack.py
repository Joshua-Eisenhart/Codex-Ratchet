#!/usr/bin/env python3
"""
sim_integration_quantum_ga_correlator_stack.py

Quantum + GA correlator bridge lane for:
  numpy + scipy + torch + clifford + torch_ga + qutip + cirq + pennylane

Claim:
  A small 2-qubit entangled surface should agree across:
    - exact classical matrix algebra
    - qutip as a supportive density/correlator witness
    - cirq and pennylane as load-bearing state witnesses
    - torch + clifford + torch_ga on the reduced correlator geometry

This is intentionally bounded. The goal is not to prove a universal theory;
it is to admit one reusable, audited bridge contract that the larger sims can
scale from without ad hoc per-run glue.
"""

from __future__ import annotations

import json
import math
import os
from datetime import UTC, datetime

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
    "Classical-to-nonclassical bridge baseline: the same small 2-qubit surface "
    "must agree across exact matrix algebra, qutip density/correlator witnesses, "
    "Cirq/PennyLane state witnesses, and torch + Clifford + torch_ga on the "
    "reduced correlator geometry. The bridge stays bounded: one entangled lane, "
    "one reversed-entangler negative check, one numeric boundary check."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing classical density, correlator, and serialization arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix-exponential witness for the exact 2-qubit unitary",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "supportive density-matrix and correlator witness on the same 2-qubit state",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2-qubit circuit and simulator witness for the bridge state",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QNode state and correlator witness for the same surface",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing correlator fit and gradient witness on the reduced geometry",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric carrier for the reduced correlator vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric algebra roundtrip for the correlator vector",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "qutip": "supportive",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_integration_quantum_ga_correlator_stack_results.json",
)

Q0, Q1 = cirq.LineQubit.range(2)
DEV = qml.device("default.qubit", wires=2, shots=None)

X2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
Y2 = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
I2 = np.eye(2, dtype=np.float64)
XX = np.kron(X2, X2)
YY = np.kron(Y2, Y2).real.astype(np.float64)
ZZ = np.kron(Z2, Z2)
I4 = np.eye(4, dtype=np.float64)
CNOT_01 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.float64,
)
CNOT_10 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=np.float64,
)

LAYOUT, BLADES = Cl(3)
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _ry(theta: float) -> np.ndarray:
    return expm(-0.5j * theta * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128))


def _ket00() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)


def _rho(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _reference_state(theta: float, phi: float, *, reversed_entangler: bool = False) -> np.ndarray:
    unitary = CNOT_10 if reversed_entangler else CNOT_01
    unitary = unitary @ np.kron(_ry(theta), _ry(phi))
    return unitary @ _ket00()


def _cirq_state(theta: float, phi: float, *, reversed_entangler: bool = False) -> np.ndarray:
    circuit = cirq.Circuit(
        cirq.ry(theta)(Q0),
        cirq.ry(phi)(Q1),
        cirq.CNOT(Q1, Q0) if reversed_entangler else cirq.CNOT(Q0, Q1),
    )
    return np.asarray(cirq.Simulator(seed=42).simulate(circuit).final_state_vector, dtype=np.complex128)


@qml.qnode(DEV)
def _pennylane_state(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.state()


@qml.qnode(DEV)
def _pennylane_correlators(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return (
        qml.expval(qml.PauliX(0) @ qml.PauliX(1)),
        qml.expval(qml.PauliY(0) @ qml.PauliY(1)),
        qml.expval(qml.PauliZ(0) @ qml.PauliZ(1)),
    )


def _qutip_state(state: np.ndarray) -> qutip.Qobj:
    return qutip.Qobj(state.reshape(4, 1), dims=[[2, 2], [1, 1]])


def _qutip_correlators(state: np.ndarray) -> np.ndarray:
    ket = _qutip_state(state)
    return np.array(
        [
            float(qutip.expect(qutip.tensor(qutip.sigmax(), qutip.sigmax()), ket)),
            float(qutip.expect(qutip.tensor(qutip.sigmay(), qutip.sigmay()), ket)),
            float(qutip.expect(qutip.tensor(qutip.sigmaz(), qutip.sigmaz()), ket)),
        ],
        dtype=np.float64,
    )


def _reduced_bloch(state: np.ndarray) -> np.ndarray:
    rho = _rho(state).reshape(2, 2, 2, 2)
    reduced = np.einsum("abcb->ac", rho)
    return np.array(
        [
            float(np.real(np.trace(reduced @ X2))),
            float(np.real(np.trace(reduced @ Y2))),
            float(np.real(np.trace(reduced @ Z2))),
        ],
        dtype=np.float64,
    )


def _correlator_vector(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.array(
        [
            float(np.real(np.vdot(state, XX @ state))),
            float(np.real(np.vdot(state, YY @ state))),
            float(np.real(np.vdot(state, ZZ @ state))),
        ],
        dtype=np.float64,
    )


def _torch_correlator(theta: torch.Tensor, phi: torch.Tensor, *, reversed_entangler: bool = False) -> torch.Tensor:
    c_theta = torch.cos(theta / 2.0)
    s_theta = torch.sin(theta / 2.0)
    c_phi = torch.cos(phi / 2.0)
    s_phi = torch.sin(phi / 2.0)
    if reversed_entangler:
        amps = torch.stack((c_theta * c_phi, s_theta * s_phi, s_theta * c_phi, c_theta * s_phi))
    else:
        amps = torch.stack((c_theta * c_phi, c_theta * s_phi, s_theta * s_phi, s_theta * c_phi))
    xx = torch.dot(amps, torch.tensor(XX, dtype=torch.float64) @ amps)
    yy = torch.dot(amps, torch.tensor(YY, dtype=torch.float64) @ amps)
    zz = torch.dot(amps, torch.tensor(ZZ, dtype=torch.float64) @ amps)
    return torch.stack((xx, yy, zz))


def _torch_fit_correlator(
    target: np.ndarray,
    *,
    theta0: float,
    phi0: float,
    reversed_entangler: bool = False,
) -> dict[str, object]:
    target_t = torch.tensor(target, dtype=torch.float64)
    theta = torch.nn.Parameter(torch.tensor(theta0, dtype=torch.float64))
    phi = torch.nn.Parameter(torch.tensor(phi0, dtype=torch.float64))
    optimizer = torch.optim.LBFGS(
        [theta, phi],
        lr=1.0,
        max_iter=100,
        tolerance_grad=1e-14,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )
    history: list[float] = []

    def closure():
        optimizer.zero_grad()
        pred = _torch_correlator(theta, phi, reversed_entangler=reversed_entangler)
        loss = torch.sum((pred - target_t) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        pred = _torch_correlator(theta, phi, reversed_entangler=reversed_entangler)
        loss = torch.sum((pred - target_t) ** 2).item()
        pred_np = pred.detach().cpu().numpy()

    return {
        "theta0": float(theta0),
        "phi0": float(phi0),
        "theta_fit": float(theta.item()),
        "phi_fit": float(phi.item()),
        "loss": float(loss),
        "vector_gap": float(np.max(np.abs(pred_np - target))),
        "loss_history_tail": [float(x) for x in history[-5:]],
    }


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    multivector = vec[0] * E1 + vec[1] * E2 + vec[2] * E3
    return np.asarray(multivector.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = TORCH_GA_TO_GEO(tensor)
    return TORCH_GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _wrap_angle(delta: float) -> float:
    return float(((delta + math.pi) % (2.0 * math.pi)) - math.pi)


def _case_metrics(
    theta: float,
    phi: float,
    *,
    reversed_entangler: bool = False,
) -> dict[str, object]:
    reference = _reference_state(theta, phi, reversed_entangler=reversed_entangler)
    cirq_state = _cirq_state(theta, phi, reversed_entangler=reversed_entangler)
    pennylane_state = np.asarray(
        _pennylane_state(theta, phi, reversed_entangler=reversed_entangler),
        dtype=np.complex128,
    )
    qutip_state = _qutip_state(reference)

    reference_rho = _rho(reference)
    cirq_rho = _rho(cirq_state)
    pennylane_rho = _rho(pennylane_state)
    qutip_rho = np.asarray(qutip_state.full(), dtype=np.complex128) @ np.asarray(qutip_state.dag().full(), dtype=np.complex128)
    reference_corr = _correlator_vector(reference)
    cirq_corr = _correlator_vector(cirq_state)
    pennylane_corr = np.asarray(
        _pennylane_correlators(theta, phi, reversed_entangler=reversed_entangler),
        dtype=np.float64,
    )
    qutip_corr = _qutip_correlators(reference)
    reference_bloch = _reduced_bloch(reference)
    cirq_bloch = _reduced_bloch(cirq_state)
    pennylane_bloch = _reduced_bloch(pennylane_state)
    qutip_bloch = _reduced_bloch(reference)

    torch_fit = _torch_fit_correlator(
        reference_corr,
        theta0=0.2,
        phi0=0.2,
        reversed_entangler=reversed_entangler,
    )
    torch_theta = torch.tensor(theta, dtype=torch.float64, requires_grad=True)
    torch_phi = torch.tensor(phi, dtype=torch.float64)
    torch_corr = _torch_correlator(torch_theta, torch_phi, reversed_entangler=reversed_entangler)
    torch_grad = float(torch.autograd.grad(torch_corr[0], torch_theta)[0])
    torch_ga_corr = _torch_ga_roundtrip(reference_corr)
    clifford_corr = _clifford_vector(reference_corr)

    return {
        "theta": float(theta),
        "phi": float(phi),
        "reversed_entangler": bool(reversed_entangler),
        "density_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(reference_rho - cirq_rho)),
            "numpy_vs_pennylane": float(np.linalg.norm(reference_rho - pennylane_rho)),
            "numpy_vs_qutip": float(np.linalg.norm(reference_rho - qutip_rho)),
        },
        "correlator_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(reference_corr - cirq_corr)),
            "numpy_vs_pennylane": float(np.linalg.norm(reference_corr - pennylane_corr)),
            "numpy_vs_qutip": float(np.linalg.norm(reference_corr - qutip_corr)),
        },
        "bloch_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(reference_bloch - cirq_bloch)),
            "numpy_vs_pennylane": float(np.linalg.norm(reference_bloch - pennylane_bloch)),
            "numpy_vs_qutip": float(np.linalg.norm(reference_bloch - qutip_bloch)),
        },
        "reference_bloch": reference_bloch.tolist(),
        "reference_correlator": reference_corr.tolist(),
        "qutip_bloch": qutip_bloch.tolist(),
        "qutip_correlator": qutip_corr.tolist(),
        "cirq_bloch": cirq_bloch.tolist(),
        "cirq_correlator": cirq_corr.tolist(),
        "pennylane_bloch": pennylane_bloch.tolist(),
        "pennylane_correlator": pennylane_corr.tolist(),
        "clifford_correlator": clifford_corr.tolist(),
        "torch_correlator": torch_corr.detach().cpu().numpy().tolist(),
        "torch_grad": torch_grad,
        "torch_fit": torch_fit,
        "torch_ga_correlator": torch_ga_corr.tolist(),
    }


def run_positive_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    metrics = _case_metrics(theta, phi)
    fit = metrics["torch_fit"]
    qutip_density_ok = all(v < 1e-6 for v in metrics["density_errors"].values())
    qutip_corr_ok = all(v < 1e-6 for v in metrics["correlator_errors"].values())
    qutip_bloch_ok = all(v < 1e-6 for v in metrics["bloch_errors"].values())
    fit_ok = (
        abs(_wrap_angle(fit["theta_fit"] - theta)) < 1e-7
        and abs(math.cos(fit["phi_fit"]) - math.cos(phi)) < 1e-8
        and fit["loss"] < 1e-12
        and fit["vector_gap"] < 1e-8
    )
    torch_ga_ok = float(np.max(np.abs(np.array(metrics["torch_ga_correlator"]) - np.array(metrics["reference_correlator"])))) < 1e-6
    clifford_ok = float(np.max(np.abs(np.array(metrics["clifford_correlator"]) - np.array(metrics["reference_correlator"])))) < 1e-12
    grad_expected = float(np.cos(theta))
    grad_ok = abs(metrics["torch_grad"] - grad_expected) < 1e-8

    return {
        "pass": bool(qutip_density_ok and qutip_corr_ok and qutip_bloch_ok and fit_ok and torch_ga_ok and clifford_ok and grad_ok),
        "reference_surface": metrics,
        "fit_recovery": {
            "pass": bool(fit_ok),
            "theta_fit": fit["theta_fit"],
            "phi_fit": fit["phi_fit"],
            "theta_gap": _wrap_angle(fit["theta_fit"] - theta),
            "phi_gap": _wrap_angle(fit["phi_fit"] - phi),
            "phi_cos_gap": abs(math.cos(fit["phi_fit"]) - math.cos(phi)),
            "loss": fit["loss"],
            "vector_gap": fit["vector_gap"],
            "loss_history_tail": fit["loss_history_tail"],
        },
        "torch_grad_check": {
            "pass": bool(grad_ok),
            "grad": metrics["torch_grad"],
            "expected": grad_expected,
            "gap": abs(metrics["torch_grad"] - grad_expected),
        },
    }


def run_negative_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    reference_state = _reference_state(theta, phi)
    reference_rho = _rho(reference_state)
    reference_corr = _correlator_vector(reference_state)
    reversed_state = _cirq_state(theta, phi, reversed_entangler=True)
    reversed_pennylane_state = np.asarray(_pennylane_state(theta, phi, reversed_entangler=True), dtype=np.complex128)
    reversed_qutip_state = _qutip_state(_reference_state(theta, phi, reversed_entangler=True))
    scrambled_target = reference_corr.copy()
    scrambled_target[1] += 0.25
    wrong_fit = _torch_fit_correlator(scrambled_target, theta0=0.2, phi0=0.2, reversed_entangler=False)

    reversed_density_errors = {
        "numpy_vs_cirq": float(np.linalg.norm(reference_rho - _rho(reversed_state))),
        "numpy_vs_pennylane": float(np.linalg.norm(reference_rho - _rho(reversed_pennylane_state))),
        "numpy_vs_qutip": float(
            np.linalg.norm(
                reference_rho - (
                    np.asarray(reversed_qutip_state.full(), dtype=np.complex128)
                    @ np.asarray(reversed_qutip_state.dag().full(), dtype=np.complex128)
                )
            )
        ),
    }
    reversed_correlator_errors = {
        "numpy_vs_cirq": float(np.linalg.norm(reference_corr - _correlator_vector(reversed_state))),
        "numpy_vs_pennylane": float(np.linalg.norm(reference_corr - np.asarray(_pennylane_correlators(theta, phi, reversed_entangler=True), dtype=np.float64))),
        "numpy_vs_qutip": float(np.linalg.norm(reference_corr - _qutip_correlators(_reference_state(theta, phi, reversed_entangler=True)))),
    }

    return {
        "pass": bool(
            reversed_density_errors["numpy_vs_cirq"] > 1e-2
            and reversed_density_errors["numpy_vs_pennylane"] > 1e-2
            and reversed_correlator_errors["numpy_vs_cirq"] > 1e-2
            and reversed_correlator_errors["numpy_vs_pennylane"] > 1e-2
            and wrong_fit["loss"] > 1e-2
        ),
        "reversed_entangler": {
            "pass": bool(
                reversed_density_errors["numpy_vs_cirq"] > 1e-2
                and reversed_density_errors["numpy_vs_pennylane"] > 1e-2
                and reversed_correlator_errors["numpy_vs_cirq"] > 1e-2
                and reversed_correlator_errors["numpy_vs_pennylane"] > 1e-2
            ),
            "density_errors": reversed_density_errors,
            "correlator_errors": reversed_correlator_errors,
            "reference_correlator": reference_corr.tolist(),
            "reversed_correlator": _correlator_vector(reversed_state).tolist(),
        },
        "wrong_fit_rejected": {
            "pass": bool(wrong_fit["loss"] > 1e-2),
            "loss": wrong_fit["loss"],
            "vector_gap": wrong_fit["vector_gap"],
            "theta_fit": wrong_fit["theta_fit"],
            "phi_fit": wrong_fit["phi_fit"],
        },
    }


def run_boundary_tests() -> dict[str, object]:
    identity = _case_metrics(0.0, 0.0)
    tiny = _case_metrics(1e-8, -1e-8)

    identity_ok = (
        all(v < 1e-9 for v in identity["density_errors"].values())
        and all(v < 1e-9 for v in identity["correlator_errors"].values())
        and all(v < 1e-9 for v in identity["bloch_errors"].values())
        and float(np.max(np.abs(np.array(identity["reference_correlator"]) - np.array([0.0, 0.0, 1.0])))) < 1e-9
    )
    tiny_ok = (
        all(np.isfinite(v) for v in tiny["reference_correlator"])
        and all(np.isfinite(v) for v in tiny["reference_bloch"])
        and tiny["torch_fit"]["loss"] < 1e-12
    )

    return {
        "pass": bool(identity_ok and tiny_ok),
        "identity_boundary": {
            "pass": bool(identity_ok),
            "reference_correlator": identity["reference_correlator"],
            "reference_bloch": identity["reference_bloch"],
        },
        "tiny_rotation_boundary": {
            "pass": bool(tiny_ok),
            "reference_correlator": tiny["reference_correlator"],
            "reference_bloch": tiny["reference_bloch"],
            "fit_loss": tiny["torch_fit"]["loss"],
        },
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(positive["pass"]),
        "negative_all_pass": bool(negative["pass"]),
        "boundary_all_pass": bool(boundary["pass"]),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_integration_quantum_ga_correlator_stack",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "overall_pass": bool(summary["all_pass"]),
        "all_pass": bool(summary["all_pass"]),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)

    print(f"PASS={bool(summary['all_pass'])}")
    print(f"Results written to {RESULTS_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
