"""Classical baseline: Bell-state partial trace.

Mirrors the Bell/entanglement primitive at classical-matrix level: construct
|Phi+> = (|00> + |11>)/sqrt(2), form its density matrix, partial-trace out
qubit B, and check that the reduced density is I/2 (maximally mixed) with
von Neumann entropy ln(2). This is a purely linear-algebra baseline.

scope_note: classical_baseline mirror of entanglement/partial-trace primitive
(ENGINE_MATH_REFERENCE.md density-matrix baseline).
"""
import numpy as np
from _common import write_results


def bell_phi_plus():
    v = np.zeros(4, dtype=complex)
    v[0] = 1 / np.sqrt(2)
    v[3] = 1 / np.sqrt(2)
    return v


def partial_trace_B(rho):
    # rho is 4x4 indexed as (a,b)(a',b'); trace over B.
    rho_r = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", rho_r)


def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = np.clip(w.real, 1e-15, None)
    return float(-np.sum(w * np.log(w)))


def run_positive():
    v = bell_phi_plus()
    rho = np.outer(v, np.conjugate(v))
    rA = partial_trace_B(rho)
    target = 0.5 * np.eye(2)
    S = vn_entropy(rA)
    return {
        "reduced_is_I_over_2": {"err": float(np.max(np.abs(rA - target))), "pass": np.allclose(rA, target, atol=1e-12)},
        "vn_entropy_ln2":      {"S": S, "ln2": float(np.log(2)), "pass": abs(S - np.log(2)) < 1e-10},
        "full_trace_unity":    {"tr": float(np.trace(rho).real), "pass": abs(np.trace(rho).real - 1) < 1e-12},
    }


def run_negative():
    # Product state |0>|0> is NOT maximally entangled; reduced is pure -> S=0.
    v = np.zeros(4, dtype=complex); v[0] = 1.0
    rho = np.outer(v, np.conjugate(v))
    rA = partial_trace_B(rho)
    S = vn_entropy(rA)
    return {"product_state_pure_reduced": {"S": S, "pass": S < 1e-10}}


def run_boundary():
    # Hermiticity and trace-1 preserved for Bell reduced density.
    v = bell_phi_plus()
    rho = np.outer(v, np.conjugate(v))
    rA = partial_trace_B(rho)
    return {"reduced_hermitian_trace1": {
        "herm_err": float(np.max(np.abs(rA - rA.conj().T))),
        "trace": float(np.trace(rA).real),
        "pass": np.allclose(rA, rA.conj().T) and abs(np.trace(rA).real - 1) < 1e-12,
    }}


if __name__ == "__main__":
    write_results(
        "sim_classical_bell_state_partial_trace",
        "classical_baseline for Bell-state partial trace (ENGINE_MATH_REFERENCE.md density-matrix baseline)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_bell_state_partial_trace_results.json",
    )
