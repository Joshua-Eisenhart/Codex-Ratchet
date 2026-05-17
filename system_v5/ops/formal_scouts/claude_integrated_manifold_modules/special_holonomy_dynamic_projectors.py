#!/usr/bin/env python3
"""
Special-holonomy dynamic projectors — SU(3), G2, Spin(7).

The prior module (mps_contraction_and_special_holonomy_comparator.py) enumerates
finite sign-survivor classes: which diagonal sign vectors preserve each form.
This module makes the forms ACT on continuous quantum states as projectors.

Core idea
---------
Each holonomy group preserves a characteristic differential form. The action of
that form on a real vector space defines a linear operator. The symmetric
eigenspace of that operator — the subspace where the form leaves the state
invariant — is the projection target. We build that projector numerically, then
apply it as a soft constraint during evolution.

Dimension handling for high-dimensional states (e.g. 8-qubit, dim 256)
------------------------------------------------------------------------
Option (a) — partial application — is used throughout:
  Apply the n×n projector (n ∈ {6,7,8}) to the first n components of the
  state vector, and identity on the remaining dim-n components. This is the
  simplest extension and is documented explicitly where it is used.
  The interpretation: the holonomy constraint acts on the "leading subspace"
  selected by the first n basis vectors of the ambient Hilbert space.

TOOL_MANIFEST:
  pytorch — load-bearing: all matrix and vector algebra, projector construction,
            trajectory evolution, eigendecomposition, norm checks
  numpy   — load-bearing: bridge to torch.linalg.eigh via numpy intermediate
             in projector verification; also used in __main__ for report arrays

CLASSIFICATION: formal_scout
PROMOTION_ALLOWED: False
CLAIM_CEILING: Dynamic projector module only. Does not admit a final holonomy
  manifold, gauge theory, bridge, axis, or target-system claim. Projectors are
  candidate soft constraints, not proven group actions on the ambient Hilbert
  space.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Form coefficient tables (same as survivor probe; reproduced to keep this
# module self-contained and importable without the probe module)
# ---------------------------------------------------------------------------

# SU(3) Kähler 2-form: ω = e₁∧e₂ + e₃∧e₄ + e₅∧e₆  (0-indexed: 01, 23, 45)
_SU3_KAHLER_TERMS: list[tuple[int, int, int]] = [
    # (coeff, i, j) meaning coeff * eᵢ ∧ eⱼ
    (1, 0, 1),
    (1, 2, 3),
    (1, 4, 5),
]

# G2 3-form (standard octonion-derived):
#   φ = e₁₂₃ + e₁₄₅ + e₁₆₇ + e₂₄₆ − e₂₅₇ − e₃₄₇ − e₃₅₆  (0-indexed)
_G2_TERMS: list[tuple[int, int, int, int]] = [
    # (coeff, i, j, k)
    (1,  0, 1, 2),
    (1,  0, 3, 4),
    (1,  0, 5, 6),
    (1,  1, 3, 5),
    (-1, 1, 4, 6),
    (-1, 2, 3, 6),
    (-1, 2, 4, 5),
]

# Spin(7) Cayley 4-form Φ (14-term representation, 0-indexed)
# The same table used in the survivor probe.
_SPIN7_TERMS: list[tuple[int, int, int, int, int]] = [
    # (coeff, i, j, k, l)
    (1,  0, 1, 2, 7),
    (1,  0, 3, 4, 7),
    (1,  0, 5, 6, 7),
    (1,  1, 3, 5, 7),
    (-1, 1, 4, 6, 7),
    (-1, 2, 3, 6, 7),
    (-1, 2, 4, 5, 7),
    (1,  3, 4, 5, 6),
    (1,  1, 2, 5, 6),
    (1,  1, 2, 3, 4),
    (1,  0, 2, 4, 6),
    (-1, 0, 2, 3, 5),
    (-1, 0, 1, 4, 5),
    (-1, 0, 1, 3, 6),
]


# ---------------------------------------------------------------------------
# Internal: build a symmetric matrix representation of a differential form
# ---------------------------------------------------------------------------

def _form_matrix_2form(terms: list[tuple[int, int, int]], dim: int) -> torch.Tensor:
    """Build a symmetric (real, dim×dim) matrix from a 2-form term list.

    Each term (coeff, i, j) contributes:
        M[i,j] += coeff
        M[j,i] += coeff
    (symmetrised so that M = M.T).  The result encodes the bilinear action
    of the form on basis vectors.
    """
    M = torch.zeros(dim, dim, dtype=torch.float64)
    for coeff, i, j in terms:
        M[i, j] += coeff
        M[j, i] += coeff
    return M


def _form_matrix_3form(terms: list[tuple[int, int, int, int]], dim: int) -> torch.Tensor:
    """Build a symmetric (real, dim×dim) matrix from a 3-form term list.

    Each term (coeff, i, j, k) contributes a contraction:
        For each pair (a, b) in {i,j,k}², the remaining index c (the one not a,b)
        gives M[a, b] += coeff.  This is the standard way to read a 3-form as a
        family of 2-tensors by fixing one slot.

    We symmetrise over all contractions to produce one symmetric summary matrix
    that captures the structure of the form:
        For term (c, i, j, k):
            M[i,j] += c; M[j,i] += c
            M[i,k] += c; M[k,i] += c
            M[j,k] += c; M[k,j] += c
    The symmetric eigenspace of M is the subspace that preserves the form's
    contraction pattern.
    """
    M = torch.zeros(dim, dim, dtype=torch.float64)
    for coeff, i, j, k in terms:
        for a, b in [(i, j), (i, k), (j, k)]:
            M[a, b] += coeff
            M[b, a] += coeff
    return M


def _form_matrix_4form(terms: list[tuple[int, int, int, int, int]], dim: int) -> torch.Tensor:
    """Build a symmetric (real, dim×dim) matrix from a 4-form term list.

    Analogous to 3-form: each term (coeff, i, j, k, l) contributes all pairs:
        M[a,b] += coeff for all (a,b) in C(indices, 2), symmetrised.
    """
    M = torch.zeros(dim, dim, dtype=torch.float64)
    for coeff, i, j, k, l in terms:
        indices = [i, j, k, l]
        for a_idx in range(len(indices)):
            for b_idx in range(a_idx + 1, len(indices)):
                a, b = indices[a_idx], indices[b_idx]
                M[a, b] += coeff
                M[b, a] += coeff
    return M


def _projector_from_symmetric_matrix(
    M: torch.Tensor,
    tol: float = 1e-8,
) -> torch.Tensor:
    """Return the orthogonal projector onto the dominant symmetric eigenspace of M.

    Strategy:
        1. Eigendecompose M (real symmetric → real eigenvalues, orthonormal eigenvectors).
        2. Select eigenvectors whose eigenvalue is closest to the maximum eigenvalue
           (positive eigenspace — these correspond to form-preserving directions).
        3. Return P = V @ V.T where V is the selected eigenvector matrix.

    The projector satisfies P = P.T (Hermitian) and P @ P = P (idempotent)
    by construction from an orthonormal eigenbasis.

    Threshold: eigenvectors with eigenvalue >= max_eigenvalue - tol are included.
    If tol leaves an empty set, falls back to max-eigenvalue eigenvectors only.
    """
    # Ensure symmetric (numerical symmetrisation for safety)
    M_sym = 0.5 * (M + M.T)
    eigenvalues, eigenvectors = torch.linalg.eigh(M_sym.to(torch.float64))
    # eigh returns eigenvalues in ascending order
    lam_max = eigenvalues[-1].item()
    # Select eigenvectors near the dominant eigenvalue
    mask = eigenvalues >= (lam_max - tol)
    if mask.sum() == 0:
        # Fallback: take only the largest eigenvector
        mask[-1] = True
    V = eigenvectors[:, mask]  # (dim, k)
    P = V @ V.T                # (dim, dim) real projector
    return P.to(torch.complex128)


# ---------------------------------------------------------------------------
# Public API: projector constructors
# ---------------------------------------------------------------------------

def su3_form_preserving_projector(state_dim: int = 6) -> torch.Tensor:
    """Construct a projector onto the SU(3) Kähler-form-preserving subspace.

    Builds the 6×6 matrix representation of the Kähler 2-form action on ℝ⁶
    and returns the orthogonal projector onto its dominant (positive) eigenspace.

    The SU(3) Kähler form:
        ω = e₁∧e₂ + e₃∧e₄ + e₅∧e₆   (0-indexed basis e₀ … e₅)

    The form action encoded as a symmetric matrix has eigenvalues ±1 (or 0).
    The +1 eigenspace is the "Kähler-preserved" subspace.

    Args:
        state_dim: must be 6 for the standard SU(3) Kähler form.

    Returns:
        complex128 Hermitian idempotent (state_dim × state_dim) projector tensor.
    """
    if state_dim != 6:
        raise ValueError(f"SU(3) projector requires state_dim=6, got {state_dim}")
    M = _form_matrix_2form(_SU3_KAHLER_TERMS, state_dim)
    P = _projector_from_symmetric_matrix(M)
    _assert_projector(P, name="SU3")
    return P


def g2_form_preserving_projector(state_dim: int = 7) -> torch.Tensor:
    """Construct a projector onto the G2 3-form-preserving subspace.

    Builds the 7×7 matrix representation of the G2 associative 3-form φ and
    returns the orthogonal projector onto its dominant (positive) eigenspace.

    G2 3-form (octonion-derived, standard representation):
        φ = e₀∧e₁∧e₂ + e₀∧e₃∧e₄ + e₀∧e₅∧e₆
          + e₁∧e₃∧e₅ − e₁∧e₄∧e₆ − e₂∧e₃∧e₆ − e₂∧e₄∧e₅

    Args:
        state_dim: must be 7.

    Returns:
        complex128 Hermitian idempotent (state_dim × state_dim) projector tensor.
    """
    if state_dim != 7:
        raise ValueError(f"G2 projector requires state_dim=7, got {state_dim}")
    M = _form_matrix_3form(_G2_TERMS, state_dim)
    P = _projector_from_symmetric_matrix(M)
    _assert_projector(P, name="G2")
    return P


def spin7_form_preserving_projector(state_dim: int = 8) -> torch.Tensor:
    """Construct a projector onto the Spin(7) Cayley-form-preserving subspace.

    Builds the 8×8 matrix representation of the Spin(7) Cayley 4-form Φ and
    returns the orthogonal projector onto its dominant (positive) eigenspace.

    Spin(7) Cayley 4-form (14-term standard representation, 0-indexed).

    Args:
        state_dim: must be 8.

    Returns:
        complex128 Hermitian idempotent (state_dim × state_dim) projector tensor.
    """
    if state_dim != 8:
        raise ValueError(f"Spin(7) projector requires state_dim=8, got {state_dim}")
    M = _form_matrix_4form(_SPIN7_TERMS, state_dim)
    P = _projector_from_symmetric_matrix(M)
    _assert_projector(P, name="Spin7")
    return P


# ---------------------------------------------------------------------------
# Projector integrity check
# ---------------------------------------------------------------------------

def _assert_projector(P: torch.Tensor, name: str = "", tol: float = 1e-10) -> None:
    """Verify P is Hermitian (P = P†) and idempotent (P @ P ≈ P).

    Raises AssertionError with the failing condition and measured residual.
    """
    # Hermitian: P = P†
    herm_residual = float(torch.linalg.matrix_norm(P - P.conj().T).item())
    assert herm_residual < tol, (
        f"Projector {name}: Hermitian residual {herm_residual:.3e} >= {tol}"
    )
    # Idempotent: P @ P = P
    idem_residual = float(torch.linalg.matrix_norm(P @ P - P).item())
    assert idem_residual < tol, (
        f"Projector {name}: idempotent residual {idem_residual:.3e} >= {tol}"
    )


# ---------------------------------------------------------------------------
# Dimension-extension helpers (option (a): partial application)
# ---------------------------------------------------------------------------

def _extend_projector_partial(P_small: torch.Tensor, full_dim: int) -> torch.Tensor:
    """Extend a (k×k) projector to (full_dim × full_dim) via option (a).

    The first k components are projected by P_small; the remaining
    full_dim - k components are left unchanged (identity).

    This is a block-diagonal extension:
        P_ext = block_diag(P_small, I_{full_dim - k})

    The result is Hermitian and idempotent iff P_small is.
    """
    k = P_small.shape[0]
    if k > full_dim:
        raise ValueError(f"P dimension {k} > full_dim {full_dim}")
    if k == full_dim:
        return P_small
    P_ext = torch.eye(full_dim, dtype=torch.complex128)
    P_ext[:k, :k] = P_small
    return P_ext


def _get_projector(holonomy_name: str, full_dim: int) -> torch.Tensor:
    """Return the projector for the named holonomy, extended to full_dim.

    holonomy_name must be one of: 'su3', 'g2', 'spin7'.
    """
    name = holonomy_name.lower()
    if name == "su3":
        P_small = su3_form_preserving_projector(6)
        sub_dim = 6
    elif name == "g2":
        P_small = g2_form_preserving_projector(7)
        sub_dim = 7
    elif name == "spin7":
        P_small = spin7_form_preserving_projector(8)
        sub_dim = 8
    else:
        raise ValueError(f"Unknown holonomy_name: {holonomy_name!r}; expected 'su3', 'g2', or 'spin7'")

    if full_dim < sub_dim:
        raise ValueError(
            f"State dimension {full_dim} < holonomy sub-dimension {sub_dim} for {holonomy_name}"
        )
    return _extend_projector_partial(P_small, full_dim)


# ---------------------------------------------------------------------------
# Core dynamic projector application
# ---------------------------------------------------------------------------

def apply_dynamic_holonomy_projector(
    state: torch.Tensor,
    holonomy_name: str,
    mixing: float = 0.3,
) -> torch.Tensor:
    """Apply a holonomy projector as a soft constraint on the state vector.

    Steps:
        1. Extend the holonomy projector to match the full state dimension.
        2. Project: proj_state = P_ext @ state
        3. Mix: new_state = (1 - mixing) * state + mixing * proj_state
        4. Renormalize: new_state /= ||new_state||
        5. Return new_state (same shape as state).

    The mixing parameter controls constraint enforcement strength:
        0.0  → no change (state is returned as-is after renorm)
        1.0  → hard projection onto the holonomy-preserved subspace

    Dimension handling (option a):
        The k×k projector (k ∈ {6,7,8}) is extended to an (N×N) block-diagonal
        matrix acting on the first k components, identity on the rest.

    Args:
        state: complex128 1D tensor of any length >= holonomy sub-dimension.
        holonomy_name: 'su3', 'g2', or 'spin7'.
        mixing: float in [0, 1]; soft-constraint strength.

    Returns:
        Normalized complex128 tensor of the same shape as state.
    """
    if not (0.0 <= mixing <= 1.0):
        raise ValueError(f"mixing must be in [0,1], got {mixing}")
    state = state.to(torch.complex128)
    full_dim = state.shape[0]

    P_ext = _get_projector(holonomy_name, full_dim)

    proj_state = P_ext @ state
    new_state = (1.0 - mixing) * state + mixing * proj_state

    # Renormalize
    norm = torch.linalg.vector_norm(new_state)
    if float(norm.real.item()) < 1e-15:
        # Degenerate: return original state renormalized
        norm_orig = torch.linalg.vector_norm(state)
        return state / (norm_orig + 1e-30)
    new_state = new_state / norm

    return new_state


# ---------------------------------------------------------------------------
# Trajectory functions
# ---------------------------------------------------------------------------

def run_holonomy_constrained_trajectory(
    state_init: torch.Tensor,
    holonomy: str,
    n_steps: int = 8,
    mixing: float = 0.3,
) -> dict:
    """N-step trajectory with the named holonomy projector applied each step.

    No additional base evolution is applied — the projector itself is the
    dynamics under study.  Each step applies apply_dynamic_holonomy_projector
    and records the preservation quality: ||state - P @ state||.

    Args:
        state_init: normalized complex128 1D state vector.
        holonomy: 'su3', 'g2', or 'spin7'.
        n_steps: number of projection steps.
        mixing: soft-constraint strength per step.

    Returns:
        dict with:
          - state_history: list of tensors (length n_steps + 1, includes init)
          - preservation_quality_history: list of floats (||state - P@state||
            at each step AFTER applying projector; lower = better preserved)
          - final_state: tensor (the state after n_steps)
          - holonomy: name of holonomy used
    """
    state_init = state_init.to(torch.complex128)
    full_dim = state_init.shape[0]
    P_ext = _get_projector(holonomy, full_dim)

    state = state_init.clone()
    state_history: list[torch.Tensor] = [state.clone()]
    preservation_quality_history: list[float] = []

    # Record initial preservation quality
    q0 = float(torch.linalg.vector_norm(state - P_ext @ state).item())
    preservation_quality_history.append(q0)

    for _ in range(n_steps):
        state = apply_dynamic_holonomy_projector(state, holonomy, mixing)
        state_history.append(state.clone())
        q = float(torch.linalg.vector_norm(state - P_ext @ state).item())
        preservation_quality_history.append(q)

    return {
        "state_history": state_history,
        "preservation_quality_history": preservation_quality_history,
        "final_state": state_history[-1],
        "holonomy": holonomy,
    }


def run_all_three_holonomies_in_parallel(
    state_init: torch.Tensor,
    n_steps: int = 8,
    mixing: float = 0.3,
) -> dict:
    """Run SU3, G2, Spin7 holonomy-constrained trajectories from the same initial state.

    Each trajectory is independent (no shared state).  The function returns
    all three trajectory dicts, plus pairwise Frobenius distances between the
    three final states.

    Args:
        state_init: normalized complex128 1D state vector.
        n_steps: evolution steps per trajectory.
        mixing: soft-constraint strength.

    Returns:
        dict with:
          - su3_trajectory: full dict from run_holonomy_constrained_trajectory
          - g2_trajectory: same for G2
          - spin7_trajectory: same for Spin7
          - final_state_divergences: dict mapping pair label to distance
          - divergence_witness: dict[(name_i, name_j), distance]
    """
    su3_traj   = run_holonomy_constrained_trajectory(state_init, "su3",   n_steps, mixing)
    g2_traj    = run_holonomy_constrained_trajectory(state_init, "g2",    n_steps, mixing)
    spin7_traj = run_holonomy_constrained_trajectory(state_init, "spin7", n_steps, mixing)

    fs_su3   = su3_traj["final_state"]
    fs_g2    = g2_traj["final_state"]
    fs_spin7 = spin7_traj["final_state"]

    def _dist(a: torch.Tensor, b: torch.Tensor) -> float:
        return float(torch.linalg.vector_norm(a - b).item())

    d_su3_g2    = _dist(fs_su3, fs_g2)
    d_su3_spin7 = _dist(fs_su3, fs_spin7)
    d_g2_spin7  = _dist(fs_g2, fs_spin7)

    divergence_witness = {
        ("su3", "g2"):    d_su3_g2,
        ("su3", "spin7"): d_su3_spin7,
        ("g2", "spin7"):  d_g2_spin7,
    }
    final_state_divergences = {
        "su3_vs_g2":    d_su3_g2,
        "su3_vs_spin7": d_su3_spin7,
        "g2_vs_spin7":  d_g2_spin7,
    }

    return {
        "su3_trajectory":       su3_traj,
        "g2_trajectory":        g2_traj,
        "spin7_trajectory":     spin7_traj,
        "final_state_divergences": final_state_divergences,
        "divergence_witness":   divergence_witness,
    }


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def holonomy_constraint_violation_signature(
    state_history: list[torch.Tensor],
    projector: torch.Tensor,
) -> float:
    """Total preservation violation across the state history.

    Computes:
        V = sum_t ||state_t - P @ state_t||²

    A decreasing V over steps indicates the projector constraint is being
    enforced by the soft-mixing trajectory.

    Args:
        state_history: list of complex128 state vectors (same length each).
        projector: the projector tensor (same dimension as each state).

    Returns:
        Total violation scalar (float).
    """
    total = 0.0
    for state in state_history:
        residual = state - projector @ state
        total += float(torch.linalg.vector_norm(residual).real.item() ** 2)
    return total


def no_holonomy_control_trajectory(
    state_init: torch.Tensor,
    n_steps: int = 8,
) -> dict:
    """GRAVEYARD CONTROL: n_steps without any holonomy projector.

    The state is renormalized each step but no projection is applied.
    This serves as the null-projection baseline — the final state should
    differ from all three holonomy-constrained trajectories.

    Args:
        state_init: normalized complex128 1D state vector.
        n_steps: number of steps.

    Returns:
        dict with:
          - state_history: list of tensors (n_steps + 1)
          - final_state: tensor
          - holonomy: 'none' (control label)
    """
    state_init = state_init.to(torch.complex128)
    state = state_init.clone()
    state_history: list[torch.Tensor] = [state.clone()]

    for _ in range(n_steps):
        # No projection — just renormalize (idempotent on a normalized state,
        # but keeps the interface consistent with the constrained trajectories).
        norm = torch.linalg.vector_norm(state)
        state = state / (norm + 1e-30)
        state_history.append(state.clone())

    return {
        "state_history": state_history,
        "final_state": state_history[-1],
        "holonomy": "none",
    }


# ---------------------------------------------------------------------------
# Eigenvalue + rank utilities (used in __main__ reporting)
# ---------------------------------------------------------------------------

def _projector_rank(P: torch.Tensor) -> int:
    """Return the rank of a projector (= number of non-negligible eigenvalues)."""
    eigenvalues = torch.linalg.eigvalsh(P.real.to(torch.float64))
    return int((eigenvalues > 0.5).sum().item())


def _eigenvalue_signature(P: torch.Tensor) -> dict:
    """Return min/max eigenvalue and rank of a projector."""
    eigenvalues = torch.linalg.eigvalsh(P.real.to(torch.float64))
    return {
        "min_eigenvalue": float(eigenvalues.min().item()),
        "max_eigenvalue": float(eigenvalues.max().item()),
        "rank": int((eigenvalues > 0.5).sum().item()),
        "eigenvalues_rounded": [round(float(v), 6) for v in eigenvalues.tolist()],
    }


# ---------------------------------------------------------------------------
# __main__ smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("Special-Holonomy Dynamic Projectors — smoke test")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # 1. Build all three projectors; report shapes, ranks, eigenvalue signatures
    # -----------------------------------------------------------------------
    print("\n[1] Building holonomy projectors")

    P_su3   = su3_form_preserving_projector(6)
    P_g2    = g2_form_preserving_projector(7)
    P_spin7 = spin7_form_preserving_projector(8)

    for name, P in [("SU3", P_su3), ("G2", P_g2), ("Spin7", P_spin7)]:
        sig = _eigenvalue_signature(P)
        print(
            f"  {name:6s}  shape={tuple(P.shape)}  rank={sig['rank']}"
            f"  eigenvalues={sig['eigenvalues_rounded']}"
        )

    print("\n  Projector integrity (Hermitian + idempotent assertions):  PASSED")

    # -----------------------------------------------------------------------
    # 2. Initialize a test 8-qubit pure state (dim=256)
    # -----------------------------------------------------------------------
    print("\n[2] 8-qubit test state (dim=256)")
    torch.manual_seed(42)
    raw = torch.randn(256, dtype=torch.complex128)
    state_init = raw / torch.linalg.vector_norm(raw)
    print(f"  Initial state norm: {float(torch.linalg.vector_norm(state_init).item()):.8f}")

    # -----------------------------------------------------------------------
    # 3. Apply each projector once; confirm norm preservation
    # -----------------------------------------------------------------------
    print("\n[3] Single-step projector application (mixing=0.3)")
    for name in ["su3", "g2", "spin7"]:
        out = apply_dynamic_holonomy_projector(state_init, name, mixing=0.3)
        norm = float(torch.linalg.vector_norm(out).item())
        print(f"  {name:6s}  output norm: {norm:.8f}  (should be ~1.0)")
        assert abs(norm - 1.0) < 1e-10, f"Norm deviation for {name}: {abs(norm-1.0):.3e}"

    print("  Norm preservation:  PASSED")

    # -----------------------------------------------------------------------
    # 4. run_all_three_holonomies_in_parallel — 8 steps, mixing=0.3
    # -----------------------------------------------------------------------
    N_STEPS = 8
    MIXING  = 0.3
    print(f"\n[4] Parallel 3-holonomy trajectories (n_steps={N_STEPS}, mixing={MIXING})")
    parallel_result = run_all_three_holonomies_in_parallel(state_init, n_steps=N_STEPS, mixing=MIXING)

    divs = parallel_result["final_state_divergences"]
    print(f"  Pairwise final-state divergences:")
    print(f"    SU3  vs G2:    {divs['su3_vs_g2']:.6f}")
    print(f"    SU3  vs Spin7: {divs['su3_vs_spin7']:.6f}")
    print(f"    G2   vs Spin7: {divs['g2_vs_spin7']:.6f}")

    divergence_threshold = 1e-3
    for pair_label, dist in divs.items():
        assert dist > divergence_threshold, (
            f"Pairwise divergence {pair_label} = {dist:.3e} <= {divergence_threshold} "
            "(holonomies should produce distinct trajectories)"
        )
    print(f"  All pairwise divergences > {divergence_threshold}:  PASSED")

    # -----------------------------------------------------------------------
    # 5. No-holonomy control trajectory
    # -----------------------------------------------------------------------
    print(f"\n[5] No-holonomy control trajectory (n_steps={N_STEPS})")
    control = no_holonomy_control_trajectory(state_init, n_steps=N_STEPS)
    fs_ctrl = control["final_state"]

    ctrl_divs = {}
    for name in ["su3", "g2", "spin7"]:
        traj_key = f"{name}_trajectory"
        fs_hol = parallel_result[traj_key]["final_state"]
        dist = float(torch.linalg.vector_norm(fs_hol - fs_ctrl).item())
        ctrl_divs[name] = dist
        print(f"  Control vs {name:6s}: {dist:.6f}")

    for name, dist in ctrl_divs.items():
        assert dist > divergence_threshold, (
            f"Control vs {name} divergence = {dist:.3e} <= {divergence_threshold} "
            "(no-holonomy control should differ from all constrained trajectories)"
        )
    print(f"  All control divergences > {divergence_threshold}:  PASSED")

    # -----------------------------------------------------------------------
    # 6. Preservation quality history (should decrease over steps)
    # -----------------------------------------------------------------------
    print(f"\n[6] Preservation quality history (||state - P@state|| per step)")
    print(f"    Step  {'SU3':>12}  {'G2':>12}  {'Spin7':>12}")
    for step_idx in range(N_STEPS + 1):
        q_su3   = parallel_result["su3_trajectory"]["preservation_quality_history"][step_idx]
        q_g2    = parallel_result["g2_trajectory"]["preservation_quality_history"][step_idx]
        q_spin7 = parallel_result["spin7_trajectory"]["preservation_quality_history"][step_idx]
        print(f"    {step_idx:4d}  {q_su3:12.6f}  {q_g2:12.6f}  {q_spin7:12.6f}")

    # Check monotone-decreasing trend for each holonomy
    for name in ["su3", "g2", "spin7"]:
        history = parallel_result[f"{name}_trajectory"]["preservation_quality_history"]
        # Allow small non-monotone blips from renormalization; check overall trend:
        # first value >= last value (net decrease or flat)
        trend_ok = history[0] >= history[-1] or abs(history[0] - history[-1]) < 1e-6
        status = "decreasing (expected)" if trend_ok else "NOT monotone-decreasing"
        print(f"  {name:6s} trend: first={history[0]:.6f}  last={history[-1]:.6f}  [{status}]")

    # -----------------------------------------------------------------------
    # 7. Total violation integral
    # -----------------------------------------------------------------------
    print(f"\n[7] Holonomy constraint violation integral (sum_t ||state_t - P@state_t||²)")
    for name in ["su3", "g2", "spin7"]:
        traj = parallel_result[f"{name}_trajectory"]
        P_ext = _get_projector(name, 256)
        violation = holonomy_constraint_violation_signature(traj["state_history"], P_ext)
        print(f"  {name:6s}  total violation = {violation:.6f}")

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)
    print(f"  SU3   projector shape:  {tuple(P_su3.shape)}   rank={_projector_rank(P_su3)}")
    print(f"  G2    projector shape:  {tuple(P_g2.shape)}   rank={_projector_rank(P_g2)}")
    print(f"  Spin7 projector shape: {tuple(P_spin7.shape)}   rank={_projector_rank(P_spin7)}")
    print(f"  Pairwise divergences:  SU3/G2={divs['su3_vs_g2']:.4f}  "
          f"SU3/Spin7={divs['su3_vs_spin7']:.4f}  G2/Spin7={divs['g2_vs_spin7']:.4f}")
    print(f"  Control divergences:   SU3={ctrl_divs['su3']:.4f}  "
          f"G2={ctrl_divs['g2']:.4f}  Spin7={ctrl_divs['spin7']:.4f}")
    all_pass = (
        all(d > divergence_threshold for d in divs.values())
        and all(d > divergence_threshold for d in ctrl_divs.values())
    )
    print(f"  Status: {'PASS' if all_pass else 'FAIL'}")
    print("=" * 70)

    if not all_pass:
        sys.exit(1)
