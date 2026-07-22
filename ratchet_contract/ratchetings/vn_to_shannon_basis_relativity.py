#!/usr/bin/env python3
"""Basis-relativity disclosure for vn_to_shannon.py's one-way dephasing arrow.

vn_to_shannon.py's committed claim: dephasing D(rho)=diag(rho) in the
COMPUTATIONAL basis is one-way (S(D(rho)) >= S(rho), non-invertible). This
probe checks whether that one-way-ness is a BASIS-FREE structural fact about
dephasing, or whether it is relative to the FIXED reference (pointer) basis
vn_to_shannon actually uses.

Result: dephasing in rho's OWN eigenbasis, D_eigen(rho) = sum_i lambda_i
|v_i><v_i|, reconstructs rho EXACTLY (that is what an eigendecomposition is),
so S(D_eigen(rho)) - S(rho) == 0 and the map is trivially invertible at that
state. The one-way drop only appears once the reference basis is FIXED
independently of the state -- the computational basis, chosen by the Layer-2
carrier Delta^1's z-axis.

This is NOT a refutation of vn_to_shannon's RATCHETED_ONE_WAY verdict: that
arrow holds exactly as claimed relative to the fixed pointer basis it
actually uses, which is the physical content of decoherence relative to a
fixed measurement basis. It IS a disclosure the receipt should carry: the
one-way claim is basis-relative, not basis-free.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". Eased formality per instruction:
numpy-only, single plain rerun + one post_receipt_gate.sh pass (honest exit 3
acceptable); full ClaimGate tier0-4 not pushed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-10

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True,
              "reason": "Bloch-ball sampled states, eigendecomposition-based dephasing, entropy and invertibility checks."},
    "sympy": {"tried": False, "used": False,
              "reason": "Eased formality per instruction: the numeric numpy witness is sufficient for this disclosure probe."},
    "z3": {"tried": False, "used": False, "reason": "Eased formality per instruction: not run."},
    "cvc5": {"tried": False, "used": False, "reason": "Eased formality per instruction: not run."},
    "qutip": {"tried": False, "used": False, "reason": "Eased formality per instruction: not run."},
    "jax": {"tried": False, "used": False, "reason": "Eased formality per instruction: not run."},
    "julia": {"tried": False, "used": False, "reason": "Eased formality per instruction: not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "sympy": None, "z3": None, "cvc5": None, "qutip": None, "jax": None, "julia": None,
}


def density_from_bloch(x: float, y: float, z: float) -> np.ndarray:
    return np.array([[1.0 + z, x - 1j * y], [x + 1j * y, 1.0 - z]], dtype=complex) / 2.0


def vn_entropy(rho: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh(rho)
    eigenvalues = np.clip(np.real(eigenvalues), 0.0, 1.0)
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def dephase_computational(rho: np.ndarray) -> np.ndarray:
    """Pinch rho in the FIXED computational (pointer) basis. This is the
    channel vn_to_shannon.py commits its RATCHETED_ONE_WAY verdict to."""
    return np.diag(np.diag(rho)).astype(complex)


def dephase_eigenbasis(rho: np.ndarray) -> np.ndarray:
    """Pinch rho in ITS OWN eigenbasis: D_eigen(rho) = sum_i lambda_i |v_i><v_i|.
    By definition of the eigendecomposition of a Hermitian rho this reconstructs
    rho exactly -- confirmed numerically below, not assumed."""
    eigenvalues, eigenvectors = np.linalg.eigh(rho)
    reconstructed = np.zeros_like(rho, dtype=complex)
    for lam, vec in zip(eigenvalues, eigenvectors.T):
        reconstructed += lam * np.outer(vec, vec.conj())
    return reconstructed


def sampled_states() -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Same interior grid + pure-boundary sweep as vn_to_shannon.py's sampler."""
    states: list[tuple[str, np.ndarray, np.ndarray]] = []
    grid = np.arange(-0.75, 0.751, 0.25)
    for x in grid:
        for y in grid:
            for z in grid:
                vector = np.array([x, y, z], dtype=float)
                if float(np.dot(vector, vector)) < 1.0 - 1.0e-12:
                    states.append(("interior", vector, density_from_bloch(x, y, z)))
    for theta in np.linspace(0.0, math.pi, 7):
        for phi in np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False):
            vector = np.array([
                math.sin(theta) * math.cos(phi),
                math.sin(theta) * math.sin(phi),
                math.cos(theta),
            ])
            states.append(("pure_boundary", vector, density_from_bloch(*vector)))
    return states


def basis_relativity_report() -> dict[str, Any]:
    states = sampled_states()

    comp_gaps: list[float] = []
    comp_offdiag_gaps: list[float] = []
    eigen_gaps: list[float] = []
    eigen_recon_errors: list[float] = []
    for kind, vector, rho in states:
        s_rho = vn_entropy(rho)
        d_comp = dephase_computational(rho)
        d_eigen = dephase_eigenbasis(rho)
        comp_gap = vn_entropy(d_comp) - s_rho
        eigen_gap = vn_entropy(d_eigen) - s_rho
        comp_gaps.append(comp_gap)
        eigen_gaps.append(eigen_gap)
        eigen_recon_errors.append(float(np.max(np.abs(d_eigen - rho))))
        if abs(rho[0, 1]) > TOL:
            comp_offdiag_gaps.append(comp_gap)

    comp_basis_drop = float(min(comp_offdiag_gaps)) if comp_offdiag_gaps else 0.0
    eigenbasis_gap = float(max(abs(g) for g in eigen_gaps))
    eigenbasis_recon_max_error = float(max(eigen_recon_errors))

    # Invertibility witness, FIXED computational basis (same pair vn_to_shannon.py uses):
    rho = np.array([[0.5, 0.25], [0.25, 0.5]], dtype=complex)
    rho_prime = np.array([[0.5, 0.25j], [-0.25j, 0.5]], dtype=complex)
    d_comp_rho, d_comp_rho_prime = dephase_computational(rho), dephase_computational(rho_prime)
    comp_noninvertible = bool(
        (not np.allclose(rho, rho_prime, atol=TOL))
        and np.allclose(d_comp_rho, d_comp_rho_prime, atol=TOL)
    )

    # Eigenbasis-dephasing invertibility: D_eigen(rho) reconstructs rho exactly at
    # every sampled state (the map is the identity ON that state, by construction
    # of its own eigendecomposition) -- confirmed numerically, not assumed.
    eigen_invertible_on_samples = bool(eigenbasis_recon_max_error < TOL)

    comp_basis_monotone_always_geq = bool(min(comp_gaps) >= -TOL)
    eigen_basis_always_zero = bool(eigenbasis_gap < TOL)

    disclosure = (
        "The vn_to_shannon one-way dephasing arrow is BASIS-RELATIVE, not basis-free. "
        f"Relative to the FIXED computational (pointer) basis, D_comp raises entropy on every "
        f"off-diagonal sampled state (min gap {comp_basis_drop:.6f} > 0) and is NOT invertible "
        f"(the witness pair rho, rho_prime share a computational-basis diagonal but differ in "
        f"off-diagonal coherence, and both collapse to the same D_comp image). Relative to EACH "
        f"state's OWN eigenbasis, dephasing is the identity on that state: D_eigen(rho) = rho "
        f"exactly (max entropy gap over all sampled states = {eigenbasis_gap:.3e}, reconstruction "
        f"error = {eigenbasis_recon_max_error:.3e}), and is trivially invertible there. This is the "
        "physical content of decoherence relative to a fixed pointer basis, not a refutation of "
        "the committed arrow -- but it IS a disclosure: the committed one-way claim smuggles the "
        "computational basis as its reference, and does not hold basis-free."
    )

    verdict = ("BASIS_RELATIVE_DISCLOSURE"
               if (comp_basis_monotone_always_geq and comp_noninvertible
                   and eigen_basis_always_zero and eigen_invertible_on_samples)
               else "FAILED")

    return {
        "schema_version": "1.0",
        "object": ("Same Layer-1/Layer-2 pair as vn_to_shannon.py: 2x2 density operators "
                   "(Bloch ball) -> diagonal simplex Delta^1, dephasing/pinching channel D."),
        "sampled_state_count": len(states),
        "comp_basis_drop": comp_basis_drop,
        "comp_basis_monotone_always_geq": comp_basis_monotone_always_geq,
        "comp_basis_noninvertible_witness": comp_noninvertible,
        "eigenbasis_gap": eigenbasis_gap,
        "eigenbasis_gap_is_zero": eigen_basis_always_zero,
        "eigenbasis_reconstruction_max_error": eigenbasis_recon_max_error,
        "eigenbasis_invertible_on_samples": eigen_invertible_on_samples,
        "disclosure": disclosure,
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{"key": "ratcheting.vn_to_shannon_basis_relativity.eigenbasis_gap",
                          "value": eigenbasis_gap, "direction": "lower_is_better"}],
        "notes": [
            "This does NOT refute vn_to_shannon's committed RATCHETED_ONE_WAY verdict -- the "
            "arrow holds exactly as claimed relative to the fixed computational/pointer basis "
            "vn_to_shannon actually uses (the Layer-2 carrier Delta^1's z-axis).",
            "It DOES disclose that the arrow is basis-relative: a differently-chosen reference "
            "basis (the state's own eigenbasis) makes the SAME channel act as the identity, "
            "entropy-preserving and invertible, on that state.",
            "Eased formality per instruction: numpy-only, single plain rerun + one "
            "post_receipt_gate.sh pass (honest exit 3 acceptable); full ClaimGate tier0-4 not pushed.",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "engines_ran": {"numpy": True, "sympy": False, "z3": False, "cvc5": False,
                        "qutip": False, "jax": False, "julia": False},
    }


def main() -> None:
    report = basis_relativity_report()
    output = Path(__file__).resolve().parent / "results" / "vn_to_shannon_basis_relativity.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(output),
        "verdict": report["verdict"],
        "comp_basis_drop": report["comp_basis_drop"],
        "eigenbasis_gap": report["eigenbasis_gap"],
    }, indent=2))


if __name__ == "__main__":
    main()
