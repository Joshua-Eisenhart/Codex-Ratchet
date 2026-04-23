"""Classical baseline: Weyl chirality extraction.

Mirrors Weyl spinor chirality with a classical analog using Pauli-z projection
on a single qubit-like complex 2-vector. Left-handed (psi = (1,0)) -> +1
eigenvalue of sigma_z; right-handed (psi = (0,1)) -> -1 eigenvalue. The
baseline checks sign extraction, orthogonality, and that superposition gives
|chirality| < 1.

scope_note: classical_baseline mirror of Weyl chirality
(ENGINE_MATH_REFERENCE.md Weyl/Clifford section).
"""
import numpy as np
from _common import write_results


SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def chirality(psi):
    psi = psi / np.linalg.norm(psi)
    return float(np.real(np.conjugate(psi) @ SIGMA_Z @ psi))


def run_positive():
    L = np.array([1, 0], dtype=complex)
    R = np.array([0, 1], dtype=complex)
    return {
        "left_plus1":  {"chi": chirality(L), "pass": abs(chirality(L) - 1.0) < 1e-12},
        "right_minus1": {"chi": chirality(R), "pass": abs(chirality(R) + 1.0) < 1e-12},
        "orthogonal":  {"inner": complex(np.vdot(L, R)), "pass": abs(np.vdot(L, R)) < 1e-12},
    }


def run_negative():
    # Equal superposition has zero chirality, NOT ±1.
    psi = (1 / np.sqrt(2)) * np.array([1, 1], dtype=complex)
    c = chirality(psi)
    return {"superposition_not_definite": {"chi": c, "pass": abs(c) < 1e-12}}


def run_boundary():
    # Phase-only change should not affect chirality.
    L = np.array([1, 0], dtype=complex)
    Lp = np.exp(1j * 0.7) * L
    return {"phase_invariant": {"chi_L": chirality(L), "chi_Lp": chirality(Lp),
                                 "pass": abs(chirality(L) - chirality(Lp)) < 1e-12}}


if __name__ == "__main__":
    write_results(
        "sim_classical_weyl_chirality_extraction",
        "classical_baseline mirror of Weyl chirality (ENGINE_MATH_REFERENCE.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_weyl_chirality_extraction_results.json",
    )
