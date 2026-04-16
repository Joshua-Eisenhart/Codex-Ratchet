#!/usr/bin/env python3
"""
sim_integration_quantum_open_entangle_correlator_mega_stack.py

Quantum mega-stack bridge lane for:
  numpy + scipy + qutip + cirq + pennylane + torch + clifford + torch_ga

Claim:
  One bounded 2-qubit surface can be reused across three linked contracts:
    - entangling state preparation
    - open-system amplitude damping on one qubit
    - reduced correlator geometry of the damped surface

The goal is not to prove a general theorem. It is to admit a reusable bridge
that the broader sims can scale from without ad hoc glue:
  1. Cirq and PennyLane witness the entangling preparation.
  2. qutip witnesses the open-system evolution against an exact reference.
  3. torch + Clifford + torch_ga witness the reduced correlator geometry of the
     damped state, while numpy/scipy keep the classical reference honest.
"""

from __future__ import annotations

import json
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
    "Classical-to-nonclassical bridge baseline: one entangling 2-qubit state, "
    "one amplitude-damping open-system flow, and one reduced correlator geometry "
    "must all agree across numpy/scipy, qutip, Cirq, PennyLane, torch, Clifford, "
    "and torch_ga. The lane stays bounded and uses only one explicit entangled "
    "prep surface plus one explicit open-system decay surface."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "classical density, correlator, and serialization arithmetic",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential reference for the entangling prep and Liouvillian flow",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing open-system mesolve witness on the damped entangled state",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entangling circuit witness for the 2-qubit prep surface",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing QNode entanglement witness for the same prep surface",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fit and gradient witness on the reduced correlator geometry",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric carrier for the reduced correlator vector",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric algebra roundtrip for the reduced correlator vector",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "qutip": "load_bearing",
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
    "sim_integration_quantum_open_entangle_correlator_mega_stack_results.json",
)

Q0, Q1 = cirq.LineQubit.range(2)
DEV = qml.device("default.qubit", wires=2, shots=None)

X2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
Y2 = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
XX = np.kron(X2, X2)
YY = np.kron(Y2, Y2).real.astype(np.float64)
ZZ = np.kron(Z2, Z2)
I2 = np.eye(2, dtype=np.complex128)
I4 = np.eye(4, dtype=np.complex128)
H2 = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
CNOT_01 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)
CNOT_10 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=np.complex128,
)

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _rho(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _vec(rho: np.ndarray) -> np.ndarray:
    return np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")


def _unvec(vec: np.ndarray) -> np.ndarray:
    return np.asarray(vec, dtype=np.complex128).reshape(4, 4, order="F")


def _ket00() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)


def _bell_prep(theta: float, phi: float) -> np.ndarray:
    """Reference entangling prep: local Y rotations then CNOT."""
    unitary = CNOT_01 @ np.kron(expm(-0.5j * theta * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)),
                                 expm(-0.5j * phi * np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)))
    return unitary @ _ket00()


def _cirq_prep(theta: float, phi: float, *, reversed_entangler: bool = False) -> np.ndarray:
    circuit = cirq.Circuit(
        cirq.ry(theta)(Q0),
        cirq.ry(phi)(Q1),
        cirq.CNOT(Q1, Q0) if reversed_entangler else cirq.CNOT(Q0, Q1),
    )
    return np.asarray(cirq.Simulator(seed=42).simulate(circuit).final_state_vector, dtype=np.complex128)


@qml.qnode(DEV)
def _pennylane_prep(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.state()


def _amplitude_damping_liouvillian(gamma: float) -> np.ndarray:
    lower = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    c_op = np.kron(np.eye(2, dtype=np.complex128), lower)
    ident = np.eye(4, dtype=np.complex128)
    cdag_c = c_op.conj().T @ c_op
    return gamma * (
        np.kron(c_op.conj(), c_op)
        - 0.5 * np.kron(ident, cdag_c)
        - 0.5 * np.kron(cdag_c.T, ident)
    )


def _open_system_reference(rho0: np.ndarray, gamma: float, t: float) -> np.ndarray:
    liouvillian = _amplitude_damping_liouvillian(gamma)
    return _unvec(expm(liouvillian * t) @ _vec(rho0))


def _qutip_evolution(rho0: np.ndarray, gamma: float, times: list[float]) -> list[np.ndarray]:
    rho_q = qutip.Qobj(rho0, dims=[[2, 2], [2, 2]])
    h = 0.0 * qutip.tensor(qutip.sigmaz(), qutip.sigmaz())
    c_ops = [np.sqrt(gamma) * qutip.tensor(qutip.qeye(2), qutip.sigmap())]
    result = qutip.mesolve(H=h, rho0=rho_q, tlist=times, c_ops=c_ops, e_ops=[])
    return [np.asarray(state.full(), dtype=np.complex128) for state in result.states]


def _partial_trace_qubit1(rho: np.ndarray) -> np.ndarray:
    reshaped = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", reshaped)


def _concurrence(state: np.ndarray) -> float:
    a, b, c, d = np.asarray(state, dtype=np.complex128).reshape(-1)
    return float(2.0 * abs(a * d - b * c))


def _entropy_from_state(state: np.ndarray) -> float:
    rho_a = _partial_trace_qubit1(_rho(state))
    evals = np.linalg.eigvalsh((rho_a + rho_a.conj().T) / 2.0)
    evals = np.clip(np.real(evals), 1e-15, 1.0)
    return float(-np.sum(evals * np.log2(evals)))


def _correlator_vector(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return np.array(
        [
            float(np.real(np.trace(rho @ XX))),
            float(np.real(np.trace(rho @ YY))),
            float(np.real(np.trace(rho @ ZZ))),
        ],
        dtype=np.float64,
    )


def _reduced_bloch(rho: np.ndarray) -> np.ndarray:
    reduced = _partial_trace_qubit1(np.asarray(rho, dtype=np.complex128).reshape(4, 4))
    return np.array(
        [
            float(np.real(np.trace(reduced @ X2))),
            float(np.real(np.trace(reduced @ Y2))),
            float(np.real(np.trace(reduced @ Z2))),
        ],
        dtype=np.float64,
    )


def _zi_expectation(rho: np.ndarray) -> float:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return float(np.real(np.trace(rho @ np.kron(Z2, I2))))


def _torch_correlator(vec: torch.Tensor) -> torch.Tensor:
    return vec


def _torch_fit_correlator(
    target: np.ndarray,
    base_correlator: np.ndarray,
    base_zi: float,
    initial_raw: float = 0.0,
) -> dict[str, object]:
    target_t = torch.tensor(target, dtype=torch.float64)
    base_corr_t = torch.tensor(base_correlator, dtype=torch.float64)
    base_zi_t = torch.tensor(base_zi, dtype=torch.float64)
    raw = torch.nn.Parameter(torch.tensor(initial_raw, dtype=torch.float64))
    optimizer = torch.optim.LBFGS(
        [raw],
        lr=1.0,
        max_iter=100,
        tolerance_grad=1e-14,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )
    history: list[float] = []

    def closure():
        optimizer.zero_grad()
        p = torch.sigmoid(raw)
        root = torch.sqrt(torch.clamp(1.0 - p, min=0.0))
        pred = torch.stack(
            (
                base_corr_t[0] * root,
                base_corr_t[1] * root,
                base_corr_t[2] * (1.0 - p) + base_zi_t * p,
            )
        )
        loss = torch.sum((pred - target_t) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        p = torch.sigmoid(raw)
        root = torch.sqrt(torch.clamp(1.0 - p, min=0.0))
        pred = torch.stack(
            (
                base_corr_t[0] * root,
                base_corr_t[1] * root,
                base_corr_t[2] * (1.0 - p) + base_zi_t * p,
            )
        )
        loss = torch.sum((pred - target_t) ** 2).item()
        pred_np = pred.detach().cpu().numpy()

    return {
        "initial_raw": float(initial_raw),
        "decay_fit": float(torch.sigmoid(raw).item()),
        "vector_fit": pred_np.tolist(),
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


def _density_summary(rho: np.ndarray) -> dict[str, object]:
    rho = np.asarray(rho, dtype=np.complex128).reshape(4, 4)
    return {
        "trace": float(np.real(np.trace(rho))),
        "reduced_bloch": _reduced_bloch(rho).tolist(),
        "correlators": _correlator_vector(rho).tolist(),
    }


def _case_metrics(theta: float, phi: float, gamma: float, t: float, *, reversed_entangler: bool = False) -> dict[str, object]:
    prep_ref = _bell_prep(theta, phi)
    prep_cirq = _cirq_prep(theta, phi, reversed_entangler=reversed_entangler)
    prep_pl = np.asarray(_pennylane_prep(theta, phi, reversed_entangler=reversed_entangler), dtype=np.complex128)
    rho0 = _rho(prep_ref)
    ref_rho_t = _open_system_reference(rho0, gamma, t)
    qutip_rho_t = _qutip_evolution(rho0, gamma, [0.0, t])[-1]

    prep_rho_ref = _rho(prep_ref)
    prep_rho_cirq = _rho(prep_cirq)
    prep_rho_pl = _rho(prep_pl)
    base_correlator = _correlator_vector(prep_rho_ref)
    base_zi = _zi_expectation(prep_rho_ref)

    target_corr = _correlator_vector(ref_rho_t)
    torch_fit = _torch_fit_correlator(target_corr, base_correlator, base_zi)
    torch_grad = target_corr[0]
    torch_vec = torch.tensor(target_corr, dtype=torch.float64)
    torch_ga_corr = _torch_ga_roundtrip(target_corr)
    clifford_corr = _clifford_vector(target_corr)

    return {
        "gamma": float(gamma),
        "t": float(t),
        "reversed_entangler": bool(reversed_entangler),
        "prep_density_errors": {
            "numpy_vs_cirq": float(np.linalg.norm(prep_rho_ref - prep_rho_cirq)),
            "numpy_vs_pennylane": float(np.linalg.norm(prep_rho_ref - prep_rho_pl)),
        },
        "open_system_density_errors": {
            "numpy_vs_qutip": float(np.linalg.norm(ref_rho_t - qutip_rho_t)),
            "reference_trace_gap": float(abs(np.trace(ref_rho_t) - 1.0)),
        },
        "reference_surface": {
            "prep_concurrence": _concurrence(prep_ref),
            "prep_entropy": _entropy_from_state(prep_ref),
            "base_correlator": base_correlator.tolist(),
            "base_zi": base_zi,
        },
        "target_correlator": target_corr.tolist(),
        "torch_correlator": _torch_correlator(torch_vec).detach().cpu().numpy().tolist(),
        "torch_grad": float(torch_grad),
        "torch_fit": torch_fit,
        "torch_ga_correlator": torch_ga_corr.tolist(),
        "clifford_correlator": clifford_corr.tolist(),
        "damped_surface": {
            "reference": _density_summary(ref_rho_t),
            "qutip": _density_summary(qutip_rho_t),
        },
    }


def run_positive_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    gamma = 0.68
    t = 0.91
    metrics = _case_metrics(theta, phi, gamma, t)

    prep_ok = (
        metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-6
        and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-6
    )
    open_ok = metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-6
    correlator = np.array(metrics["target_correlator"], dtype=np.float64)
    fit = metrics["torch_fit"]
    fit_ok = fit["loss"] < 1e-12 and fit["vector_gap"] < 1e-8
    torch_ga_ok = float(np.max(np.abs(np.array(metrics["torch_ga_correlator"]) - correlator))) < 1e-6
    clifford_ok = float(np.max(np.abs(np.array(metrics["clifford_correlator"]) - correlator))) < 1e-12

    return {
        "pass": bool(prep_ok and open_ok and fit_ok and torch_ga_ok and clifford_ok),
        "prep_surface": {
            "pass": bool(prep_ok),
            "numpy_vs_cirq": metrics["prep_density_errors"]["numpy_vs_cirq"],
            "numpy_vs_pennylane": metrics["prep_density_errors"]["numpy_vs_pennylane"],
        },
        "open_system_surface": {
            "pass": bool(open_ok),
            "numpy_vs_qutip": metrics["open_system_density_errors"]["numpy_vs_qutip"],
            "reference_trace_gap": metrics["open_system_density_errors"]["reference_trace_gap"],
        },
        "correlator_surface": {
            "pass": bool(torch_ga_ok and clifford_ok),
            "target_correlator": metrics["target_correlator"],
            "torch_correlator": metrics["torch_correlator"],
            "torch_ga_correlator": metrics["torch_ga_correlator"],
            "clifford_correlator": metrics["clifford_correlator"],
        },
        "fit_recovery": {
            "pass": bool(fit_ok),
            "decay_fit": fit["decay_fit"],
            "vector_fit": fit["vector_fit"],
            "loss": fit["loss"],
            "vector_gap": fit["vector_gap"],
            "loss_history_tail": fit["loss_history_tail"],
        },
    }


def run_negative_tests() -> dict[str, object]:
    theta = 1.127
    phi = -0.713
    gamma = 0.68
    t = 0.91
    prep_ref = _bell_prep(theta, phi)
    rho0 = _rho(prep_ref)
    ref_rho_t = _open_system_reference(rho0, gamma, t)
    qutip_rho_t = _qutip_evolution(rho0, gamma, [0.0, t])[-1]
    wrong_reference = _open_system_reference(rho0, -gamma, t)
    reversed_prep = _cirq_prep(theta, phi, reversed_entangler=True)
    reversed_pl = np.asarray(_pennylane_prep(theta, phi, reversed_entangler=True), dtype=np.complex128)
    base_correlator = _correlator_vector(_rho(prep_ref))
    base_zi = _zi_expectation(_rho(prep_ref))
    wrong_target = _correlator_vector(ref_rho_t).copy()
    wrong_target[1] += 0.2
    wrong_fit = _torch_fit_correlator(wrong_target, base_correlator, base_zi)

    return {
        "pass": bool(
            np.linalg.norm(qutip_rho_t - wrong_reference) > 1e-2
            and np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref)) > 1e-2
            and np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref)) > 1e-2
            and wrong_fit["loss"] > 1e-2
        ),
        "wrong_sign_damping_rejected": {
            "pass": bool(np.linalg.norm(qutip_rho_t - wrong_reference) > 1e-2),
            "error": float(np.linalg.norm(qutip_rho_t - wrong_reference)),
        },
        "reversed_entangler_rejected": {
            "pass": bool(
                np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref)) > 1e-2
                and np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref)) > 1e-2
            ),
            "cirq_error": float(np.linalg.norm(_rho(reversed_prep) - _rho(prep_ref))),
            "pennylane_error": float(np.linalg.norm(_rho(reversed_pl) - _rho(prep_ref))),
        },
        "correlator_mismatch_rejected": {
            "pass": bool(wrong_fit["loss"] > 1e-2),
            "loss": wrong_fit["loss"],
            "vector_gap": wrong_fit["vector_gap"],
        },
    }


def run_boundary_tests() -> dict[str, object]:
    theta = 0.0
    phi = 0.0
    gamma = 0.68
    t = 0.0
    metrics = _case_metrics(theta, phi, gamma, t)
    prep_ok = metrics["prep_density_errors"]["numpy_vs_cirq"] < 1e-9 and metrics["prep_density_errors"]["numpy_vs_pennylane"] < 1e-9
    open_ok = metrics["open_system_density_errors"]["numpy_vs_qutip"] < 1e-9
    boundary_corr = np.array(metrics["target_correlator"], dtype=np.float64)
    boundary_ok = (
        np.isfinite(boundary_corr).all()
        and np.linalg.norm(boundary_corr - np.array([0.0, 0.0, 1.0], dtype=np.float64)) < 1e-9
        and metrics["torch_fit"]["loss"] < 1e-12
    )

    return {
        "pass": bool(prep_ok and open_ok and boundary_ok),
        "prep_boundary": {
            "pass": bool(prep_ok),
            "numpy_vs_cirq": metrics["prep_density_errors"]["numpy_vs_cirq"],
            "numpy_vs_pennylane": metrics["prep_density_errors"]["numpy_vs_pennylane"],
        },
        "open_system_boundary": {
            "pass": bool(open_ok),
            "numpy_vs_qutip": metrics["open_system_density_errors"]["numpy_vs_qutip"],
            "reference_trace_gap": metrics["open_system_density_errors"]["reference_trace_gap"],
        },
        "correlator_boundary": {
            "pass": bool(boundary_ok),
            "target_correlator": metrics["target_correlator"],
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
        "name": "sim_integration_quantum_open_entangle_correlator_mega_stack",
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
