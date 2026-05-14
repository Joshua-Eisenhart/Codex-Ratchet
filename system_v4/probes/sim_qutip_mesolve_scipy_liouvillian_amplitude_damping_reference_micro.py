#!/usr/bin/env python3
"""QuTiP mesolve vs SciPy Liouvillian amplitude-damping reference micro.

Claim:
  A one-qubit Lindblad amplitude-damping evolution should agree between
  qutip.mesolve and a direct SciPy/Numpy Liouvillian matrix-exponential
  reference on the same density matrix.

This is a classical-baseline tool-function reference. It does not admit a
bridge, GStack, axis, QIT, or nonclassical claim.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import numpy as np
import qutip
from scipy.linalg import expm

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"
NAME = "sim_qutip_mesolve_scipy_liouvillian_amplitude_damping_reference_micro"
divergence_log = (
    "Classical open-system baseline: a single-qubit amplitude-damping Lindblad "
    "evolution should agree between qutip.mesolve and a direct SciPy/Numpy "
    "Liouvillian exponential, without re-gluing the evolution rule per sim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "classical density algebra, vectorization, and tolerances",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "classical Liouvillian matrix exponential reference",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing open-system mesolve witness on the same qubit",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "qutip": "load_bearing",
}

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "construct a one-qubit initial density matrix",
        "define an amplitude-damping Lindblad generator with one lowering collapse operator",
        "evolve the density matrix at several times using qutip.mesolve",
        "construct the matching SciPy/Numpy Liouvillian superoperator",
        "evolve the vectorized density matrix with scipy.linalg.expm",
        "compare QuTiP and SciPy density matrices, density validity, coherence monotonicity, and boundary limits",
    ],
    "carrier_topology": (
        "Finite two-dimensional complex Hilbert-space density matrix fixture with one "
        "amplitude-damping Lindblad collapse operator; this is a classical-baseline "
        "open-system reference, not a bridge or nonclassical admission."
    ),
    "observable": {
        "primary": "Frobenius norm error between qutip.mesolve states and SciPy Liouvillian reference states",
        "secondary": [
            "Hermitian trace-one positive-semidefinite density checks",
            "ground-state fidelity over time",
            "off-diagonal coherence nonincrease",
            "zero-time identity error",
            "long-time ground-state limit error",
        ],
    },
    "pass_fail_predicate": (
        "Pass iff QuTiP and SciPy reference states agree below tolerance, all QuTiP "
        "states remain valid density matrices, coherence is nonincreasing, closed-system "
        "and wrong-sign controls are rejected, and zero-time and long-time boundaries pass."
    ),
    "graveyards": [
        "closed-system identity surrogate should not match the dissipative evolution",
        "wrong-sign Liouvillian should not match the dissipative evolution",
        "zero-time evolution should collapse to the initial density matrix",
        "long-time evolution should approach the ground-state density matrix",
    ],
    "baselines": [
        "SciPy/Numpy Liouvillian matrix-exponential reference",
        "closed-system identity surrogate baseline",
        "wrong-sign Liouvillian baseline",
        "zero-time identity boundary baseline",
        "long-time ground-state boundary baseline",
    ],
    "alternative_formulations": [
        "compare qutip.mesolve to an explicit Kraus amplitude-damping channel at matched times",
        "replace amplitude damping with dephasing and compare to a diagonal Liouvillian reference",
        "sample additional initial density matrices while preserving the same mesolve-vs-Liouvillian predicate",
    ],
    "tool_function_needs": [
        "qutip.Qobj for density-matrix construction",
        "qutip.mesolve for Lindblad open-system evolution",
        "qutip.sigmap and qutip.sigmaz for collapse and zero Hamiltonian construction",
        "scipy.linalg.expm for the Liouvillian matrix-exponential reference",
        "numpy vectorization and density-matrix validation",
    ],
    "lego_coupling_target": "bounded open-system channel reference before channel-local fit packets",
    "claim_ceiling": (
        "classical_baseline_only_qutip_mesolve_vs_scipy_liouvillian_reference; "
        "no bridge, GStack, axis, QIT, or nonclassical admission"
    ),
}


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _rho(state: np.ndarray) -> np.ndarray:
    return np.outer(state, np.conjugate(state))


def _vec(rho: np.ndarray) -> np.ndarray:
    return np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")


def _unvec(vec: np.ndarray) -> np.ndarray:
    return np.asarray(vec, dtype=np.complex128).reshape(2, 2, order="F")


def _amplitude_damping_liouvillian(gamma: float) -> np.ndarray:
    lower = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    ident = np.eye(2, dtype=np.complex128)
    ldag_l = lower.conj().T @ lower
    return gamma * (
        np.kron(lower.conj(), lower)
        - 0.5 * np.kron(ident, ldag_l)
        - 0.5 * np.kron(ldag_l.T, ident)
    )


def _classical_reference(rho0: np.ndarray, gamma: float, t: float) -> np.ndarray:
    liouvillian = _amplitude_damping_liouvillian(gamma)
    rho_t = expm(liouvillian * t) @ _vec(rho0)
    return _unvec(rho_t)


def _qutip_evolution(rho0: np.ndarray, gamma: float, times: list[float]) -> list[np.ndarray]:
    rho_q = qutip.Qobj(rho0, dims=[[2], [2]])
    h = 0.0 * qutip.sigmaz()
    c_ops = [np.sqrt(gamma) * qutip.sigmap()]
    result = qutip.mesolve(H=h, rho0=rho_q, tlist=times, c_ops=c_ops, e_ops=[])
    return [np.asarray(state.full(), dtype=np.complex128) for state in result.states]


def _is_density(rho: np.ndarray, tol: float = 1e-10) -> tuple[bool, dict[str, object]]:
    hermitian = np.allclose(rho, rho.conjugate().T, atol=tol)
    trace_one = abs(np.trace(rho) - 1.0) < tol
    eigs = np.linalg.eigvalsh((rho + rho.conjugate().T) / 2.0)
    psd = bool(np.all(eigs >= -tol))
    return bool(hermitian and trace_one and psd), {
        "hermitian": bool(hermitian),
        "trace_one": bool(trace_one),
        "psd": bool(psd),
        "min_eig": float(np.min(eigs)),
    }


def _fidelity_with_ground(rho: np.ndarray) -> float:
    ground = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    return float(np.real(np.trace(ground @ rho)))


def run_positive_tests() -> dict[str, dict[str, object]]:
    gamma = 0.73
    times = [0.0, 0.31, 0.95, 1.7]
    rho0 = _rho(np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0))
    qutip_states = _qutip_evolution(rho0, gamma, times)

    case_rows = []
    max_error = 0.0
    all_density_ok = True
    all_trace_ok = True
    all_psd_ok = True
    coherence_decay_ok = True
    initial_coherence = abs(rho0[0, 1])
    for t, rho_q in zip(times, qutip_states, strict=True):
        rho_ref = _classical_reference(rho0, gamma, t)
        error = float(np.linalg.norm(rho_q - rho_ref))
        max_error = max(max_error, error)
        density_ok, density_detail = _is_density(rho_q)
        case_rows.append(
            {
                "t": t,
                "pass": error < 1e-6 and density_ok,
                "error": error,
                "density": density_detail,
                "ground_fidelity": _fidelity_with_ground(rho_q),
            }
        )
        all_density_ok = all_density_ok and density_ok
        all_trace_ok = all_trace_ok and abs(np.trace(rho_q) - 1.0) < 1e-10
        all_psd_ok = all_psd_ok and density_detail["psd"] is True
        coherence_decay_ok = coherence_decay_ok and abs(rho_q[0, 1]) <= initial_coherence + 1e-12

    return {
        "reference_match": {
            "pass": bool(max_error < 1e-6),
            "max_error": max_error,
            "cases": case_rows,
        },
        "density_structure_preserved": {
            "pass": bool(all_density_ok and all_trace_ok and all_psd_ok),
            "trace_preserved": bool(all_trace_ok),
            "psd_preserved": bool(all_psd_ok),
        },
        "coherence_nonincreasing": {
            "pass": bool(coherence_decay_ok),
            "note": "amplitude damping should not increase off-diagonal magnitude",
        },
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    gamma = 0.73
    rho0 = _rho(np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0))
    t = 1.0
    qutip_state = _qutip_evolution(rho0, gamma, [0.0, t])[-1]
    wrong_closed_system = rho0.copy()
    wrong_sign_reference = _classical_reference(rho0, -gamma, t)

    return {
        "closed_system_surrogate_rejected": {
            "pass": bool(np.linalg.norm(qutip_state - wrong_closed_system) > 1e-3),
            "error": float(np.linalg.norm(qutip_state - wrong_closed_system)),
            "claim": "zero-dissipation identity evolution is not a valid substitute here",
        },
        "wrong_sign_liouvillian_rejected": {
            "pass": bool(np.linalg.norm(qutip_state - wrong_sign_reference) > 1e-2),
            "error": float(np.linalg.norm(qutip_state - wrong_sign_reference)),
            "claim": "reversing the Lindblad sign should not match the open-system witness",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    gamma = 0.73
    rho0 = _rho(np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0))

    t0_qutip = _qutip_evolution(rho0, gamma, [0.0])[0]
    t0_ref = _classical_reference(rho0, gamma, 0.0)
    large_t = 8.0 / gamma
    steady_qutip = _qutip_evolution(rho0, gamma, [0.0, large_t])[-1]
    ground = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)

    return {
        "zero_time_identity": {
            "pass": bool(np.linalg.norm(t0_qutip - rho0) < 1e-12 and np.linalg.norm(t0_ref - rho0) < 1e-12),
            "qutip_error": float(np.linalg.norm(t0_qutip - rho0)),
            "reference_error": float(np.linalg.norm(t0_ref - rho0)),
        },
        "steady_state_ground_limit": {
            "pass": bool(
                np.linalg.norm(steady_qutip - ground) < 2e-2
                and _fidelity_with_ground(steady_qutip) > 0.999
            ),
            "ground_error": float(np.linalg.norm(steady_qutip - ground)),
            "ground_fidelity": _fidelity_with_ground(steady_qutip),
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": all(bool(row["pass"]) for row in positive.values()),
        "negative_all_pass": all(bool(row["pass"]) for row in negative.values()),
        "boundary_all_pass": all(bool(row["pass"]) for row in boundary.values()),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": NAME,
        "classification": classification,
        **CANDIDATE_SIM_SPEC,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded classical-baseline QuTiP mesolve open-system reference evidence before channel-local fit packets.",
    )
    results["claim_ceiling"] = (
        "classical_baseline_only_qutip_mesolve_vs_scipy_liouvillian_reference; "
        "no bridge, GStack, axis, QIT, or nonclassical admission"
    )
    results["nonclassical_claim_ceiling"] = "baseline_only_no_nonclassical_promotion"
    results["blocked_until"] = "separate nonclassical-suitable canonical receipt and explicit stage-gate approval"

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
