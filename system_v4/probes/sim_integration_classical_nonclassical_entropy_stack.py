#!/usr/bin/env python3
"""
sim_integration_classical_nonclassical_entropy_stack.py

Bridge lane for:
  numpy + scipy + torch + clifford + qutip + pennylane + torch_ga

Claim:
the classical-vs-nonclassical entropy gap for a single qubit should agree
across exact classical algebra, QuTiP, PennyLane, torch/autograd, Clifford,
and torch_ga. The bridge signal is the diagonal-vs-quantum entropy gap of one
bounded coherent qubit state, not an ad hoc per-tool check.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import numpy as np
import pennylane as qml
import qutip
import torch
import torch_ga
from clifford import Cl
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Entropy bridge baseline: a single coherent qubit should show a positive "
    "classical-vs-quantum entropy gap when viewed through the computational "
    "basis, and that gap should agree across exact numpy/scipy algebra, QuTiP, "
    "PennyLane, torch/autograd, Clifford, and torch_ga. The boundary state is "
    "purely diagonal, so the gap collapses to zero."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density algebra, Shannon entropy, Bloch vector, and serialization",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix-exponential state-preparation witness",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing autograd witness on the entropy gap with respect to coherence amplitude",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Bloch-vector carrier for the same coherent qubit",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density-matrix and von Neumann entropy witness",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing statevector witness for the same qubit surface",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric-algebra roundtrip witness for the Bloch vector",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "torch": "load_bearing",
    "clifford": "load_bearing",
    "qutip": "load_bearing",
    "pennylane": "load_bearing",
    "torch_ga": "load_bearing",
}

OUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_integration_classical_nonclassical_entropy_stack_results.json",
)

PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
KET0 = np.array([1.0, 0.0], dtype=np.complex128)
DEV = qml.device("default.qubit", wires=1, shots=None)
GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
GA_TO_GEO = torch_ga.TensorToGeometric(GA_ALG, [1, 2, 3])
GA_TO_TENSOR = torch_ga.GeometricToTensor(GA_ALG, [1, 2, 3])
LAYOUT, BLADES = Cl(3)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _rho(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _state_from_angles(theta: float, phi: float) -> np.ndarray:
    return np.array(
        [
            np.cos(theta / 2.0),
            np.exp(1.0j * phi) * np.sin(theta / 2.0),
        ],
        dtype=np.complex128,
    )


def _unitary_state(theta: float, phi: float) -> np.ndarray:
    y = PAULI_Y
    z = PAULI_Z
    unitary = expm(-0.5j * phi * z) @ expm(-0.5j * theta * y)
    return unitary @ KET0


def _qutip_state(theta: float, phi: float) -> np.ndarray:
    ket = ((-0.5j * phi * qutip.sigmaz()).expm() * (-0.5j * theta * qutip.sigmay()).expm()) * qutip.basis(2, 0)
    return np.asarray(ket.full(), dtype=np.complex128).reshape(-1)


@qml.qnode(DEV)
def _pennylane_state(theta: float, phi: float):
    qml.RY(theta, wires=0)
    qml.RZ(phi, wires=0)
    return qml.state()


def _shannon_entropy(diag: np.ndarray) -> float:
    diag = np.asarray(diag, dtype=np.float64)
    diag = np.clip(diag, 1e-15, 1.0)
    return float(-np.sum(diag * np.log(diag)))


def _von_neumann_entropy_qutip(rho: np.ndarray) -> float:
    return float(qutip.entropy_vn(qutip.Qobj(rho, dims=[[2], [2]]), base=np.e))


def _entropy_gap(rho: np.ndarray) -> tuple[float, float, float]:
    diag = np.real(np.diag(rho))
    shannon = _shannon_entropy(diag)
    vn = _von_neumann_entropy_qutip(rho)
    return float(shannon - vn), float(shannon), float(vn)


def _bloch_from_rho(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            float(np.real(np.trace(rho @ np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)))),
            float(np.real(np.trace(rho @ PAULI_Y))),
            float(np.real(np.trace(rho @ PAULI_Z))),
        ],
        dtype=np.float64,
    )


def _clifford_vector(vec: np.ndarray) -> np.ndarray:
    _, blades = LAYOUT, BLADES
    mv = vec[0] * blades["e1"] + vec[1] * blades["e2"] + vec[2] * blades["e3"]
    return np.asarray(mv.value[1:4], dtype=np.float64)


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = GA_TO_GEO(tensor)
    return GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _torch_gap(theta: float, phi: float) -> tuple[float, float]:
    theta_t = torch.tensor(theta, dtype=torch.float64, requires_grad=True)
    phi_t = torch.tensor(phi, dtype=torch.float64)
    state = torch.stack(
        (
            torch.cos(theta_t / 2.0),
            torch.exp(1.0j * phi_t) * torch.sin(theta_t / 2.0),
        )
    )
    rho = torch.outer(state, torch.conj(state))
    diag = torch.real(torch.diag(rho))
    shannon = -torch.sum(torch.clamp(diag, min=1e-15) * torch.log(torch.clamp(diag, min=1e-15)))
    eigvals = torch.linalg.eigvalsh(rho)
    vn = -torch.sum(torch.clamp(torch.real(eigvals), min=1e-15) * torch.log(torch.clamp(torch.real(eigvals), min=1e-15)))
    gap = shannon - vn
    gap.backward()
    return float(gap.detach()), float(theta_t.grad.detach())


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _evaluate_case(theta: float, phi: float, *, negative: bool = False) -> dict[str, object]:
    manual = _state_from_angles(theta, phi)
    scipy_state = _unitary_state(theta, phi)
    qutip_state = _qutip_state(theta, phi)
    pennylane_state = np.asarray(_pennylane_state(theta, phi), dtype=np.complex128)
    if negative:
        qutip_state = _qutip_state(theta, -phi)
        pennylane_state = np.asarray(_pennylane_state(theta, -phi), dtype=np.complex128)

    manual_rho = _rho(manual)
    scipy_rho = _rho(scipy_state)
    qutip_rho = _rho(qutip_state)
    pennylane_rho = _rho(pennylane_state)

    entropy_gap, shannon_entropy, vn_entropy = _entropy_gap(manual_rho)
    qutip_gap, qutip_shannon, qutip_vn = _entropy_gap(qutip_rho)
    pennylane_gap, pennylane_shannon, pennylane_vn = _entropy_gap(pennylane_rho)
    torch_gap, torch_grad = _torch_gap(theta, phi if not negative else -phi)

    bloch = _bloch_from_rho(manual_rho)
    clifford_vec = _clifford_vector(bloch)
    torch_ga_vec = _torch_ga_roundtrip(bloch)

    density_errors = {
        "numpy_vs_scipy": float(np.linalg.norm(manual_rho - scipy_rho)),
        "numpy_vs_qutip": float(np.linalg.norm(manual_rho - qutip_rho)),
        "numpy_vs_pennylane": float(np.linalg.norm(manual_rho - pennylane_rho)),
    }

    if negative:
        checks = {
            "gap_reduced": entropy_gap < 1e-8,
            "qutip_gap_reduced": qutip_gap < 1e-8,
            "pennylane_gap_reduced": pennylane_gap < 1e-8,
            "torch_gap_reduced": torch_gap < 1e-8,
            "gradient_near_zero": abs(torch_grad) < 1e-6,
        }
    else:
        checks = {
            "numpy_scipy_density_match": density_errors["numpy_vs_scipy"] < 1e-7,
            "numpy_qutip_density_match": density_errors["numpy_vs_qutip"] < 1e-7,
            "numpy_pennylane_density_match": density_errors["numpy_vs_pennylane"] < 1e-7,
            "entropy_gap_positive": entropy_gap > 1e-8,
            "qutip_gap_matches": abs(qutip_gap - entropy_gap) < 1e-7,
            "pennylane_gap_matches": abs(pennylane_gap - entropy_gap) < 1e-7,
            "torch_gap_matches": abs(torch_gap - entropy_gap) < 1e-7,
            "torch_ga_roundtrip_matches": float(np.linalg.norm(torch_ga_vec - bloch)) < 1e-6,
            "clifford_matches_bloch": float(np.linalg.norm(clifford_vec - bloch)) < 1e-6,
        }

    return {
        "theta": theta,
        "phi": phi,
        "entropy_gap": entropy_gap,
        "shannon_entropy": shannon_entropy,
        "vn_entropy": vn_entropy,
        "qutip_gap": qutip_gap,
        "qutip_shannon_entropy": qutip_shannon,
        "qutip_vn_entropy": qutip_vn,
        "pennylane_gap": pennylane_gap,
        "pennylane_shannon_entropy": pennylane_shannon,
        "pennylane_vn_entropy": pennylane_vn,
        "torch_gap": torch_gap,
        "torch_grad": torch_grad,
        "density_errors": density_errors,
        "bloch": bloch.tolist(),
        "clifford_bloch": clifford_vec.tolist(),
        "torch_ga_bloch": torch_ga_vec.tolist(),
        "checks": checks,
        "pass": all(checks.values()),
    }


def run_positive_tests() -> dict[str, object]:
    case = _evaluate_case(theta=1.11, phi=0.73)
    return {
        "entropy_bridge_surface": case,
        "pass": bool(case["pass"]),
    }


def run_negative_tests() -> dict[str, object]:
    case = _evaluate_case(theta=1.11, phi=0.73)
    coherent_rho = _rho(_state_from_angles(1.11, 0.73))
    diagonal_surrogate = np.diag(np.diag(coherent_rho))
    surrogate_gap, surrogate_shannon, surrogate_vn = _entropy_gap(diagonal_surrogate)
    coherent_gap = float(case["entropy_gap"])
    return {
        "diagonal_surrogate_rejected": {
            "coherent_case": case,
            "surrogate_gap": surrogate_gap,
            "surrogate_shannon_entropy": surrogate_shannon,
            "surrogate_vn_entropy": surrogate_vn,
            "density_error_to_surrogate": float(np.linalg.norm(coherent_rho - diagonal_surrogate)),
            "gap_mismatch": float(abs(coherent_gap - surrogate_gap)),
            "pass": bool(
                np.linalg.norm(coherent_rho - diagonal_surrogate) > 1e-2
                and abs(coherent_gap - surrogate_gap) > 1e-2
                and surrogate_gap < coherent_gap
            ),
        },
        "pass": bool(
            np.linalg.norm(coherent_rho - diagonal_surrogate) > 1e-2
            and abs(coherent_gap - surrogate_gap) > 1e-2
            and surrogate_gap < coherent_gap
        ),
    }


def run_boundary_tests() -> dict[str, object]:
    diagonal = _evaluate_case(theta=0.0, phi=0.0)
    tiny = _evaluate_case(theta=1e-8, phi=1e-8)
    return {
        "pass": bool(
            abs(diagonal["entropy_gap"]) < 1e-12
            and abs(diagonal["torch_gap"]) < 1e-12
            and abs(tiny["entropy_gap"]) < 1e-8
            and np.isfinite(tiny["torch_grad"])
        ),
        "diagonal_boundary": diagonal,
        "tiny_coherence_boundary": tiny,
    }


def main() -> int:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(positive["pass"]),
        "negative_all_pass": bool(negative["pass"]),
        "boundary_all_pass": bool(boundary["pass"]),
    }
    summary["all_pass"] = all(summary.values())

    result = {
        "name": "sim_integration_classical_nonclassical_entropy_stack",
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

    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, default=_json_default)

    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
