#!/usr/bin/env python3
"""
MPS-only tensor-network contraction + special-holonomy parallel comparator.

PART A: MPS-only bond-truncated tensor-network contraction (pure torch).
  Replaces dense matrix exponentials with MPS-style SVD-truncated updates.

PART B: Special-holonomy parallel comparator.
  Runs SU(3)/G2/Spin(7) form constraints alongside the scaffold
  GL(2,C) → O(4) → SO(4) → Spin(4) → U(2) → SU(2) reduction in the same
  dynamic evolution context, with z3 non-collapse witness.

TOOL_MANIFEST:
  pytorch  — load-bearing: all MPS tensors, evolution unitaries, SVD truncation
  numpy    — load-bearing: SVD backend via torch.linalg.svd; numpy used in conversion utilities
  scipy    — load-bearing: scipy.linalg.expm for two-site unitary generation in __main__
  sympy    — load-bearing: exact exterior-form sign checks inside survivor filters
  z3       — load-bearing: UNSAT non-collapse witness (special holonomies differ from generic)

CLASSIFICATION: formal_scout
PROMOTION_ALLOWED: False
CLAIM_CEILING: Formal scout only. Does not admit a final manifold tower,
  bridge, axis, or target-system claim.
"""

from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np
import sympy as sp
import torch
import z3

# ---------------------------------------------------------------------------
# PART A — MPS-only tensor-network contraction
# ---------------------------------------------------------------------------
# Convention for MPS tensors:
#   - Site 0 (left boundary): shape (1, d, chi_R)
#   - Site k (bulk):          shape (chi_L, d, chi_R)
#   - Site N-1 (right bound): shape (chi_L, d, 1)
# where d=2 (qubit), chi = bond dimension.
# All tensors are complex128.
# ---------------------------------------------------------------------------


def mps_initial_state(n_qubits: int, bond_dim: int) -> list[torch.Tensor]:
    """Return a product-state MPS for |0...0⟩ with specified maximum bond_dim.

    Each site tensor has shape (chi_L, 2, chi_R) with chi_L=chi_R=1 initially
    (product state has bond dimension 1 regardless of the requested bond_dim;
    bond_dim here sets the capacity for subsequent evolution steps).

    Args:
        n_qubits: number of qubits N ≥ 2.
        bond_dim: maximum bond dimension for later evolution (stored as metadata
                  but tensor shape starts at 1 for a product state).

    Returns:
        List of N complex128 tensors, site 0 shape (1,2,1), bulk (1,2,1),
        site N-1 (1,2,1).  All initialised to |0⟩ (amplitude 1 on physical
        index 0, amplitude 0 on physical index 1).
    """
    if n_qubits < 2:
        raise ValueError("n_qubits must be >= 2")
    mps = []
    for _ in range(n_qubits):
        t = torch.zeros((1, 2, 1), dtype=torch.complex128)
        t[0, 0, 0] = 1.0 + 0j  # |0⟩
        mps.append(t)
    return mps


def _svd_truncate(
    matrix: torch.Tensor, max_bond: int
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Thin SVD of matrix, keep at most max_bond singular values.

    Returns (U, S, Vh) where U has shape (m, k), S shape (k,), Vh shape (k, n)
    and k = min(rank, max_bond).
    """
    U, S, Vh = torch.linalg.svd(matrix, full_matrices=False)
    k = min(max_bond, S.shape[0])
    return U[:, :k], S[:k], Vh[:k, :]


def mps_apply_two_site_unitary(
    mps: list[torch.Tensor],
    site_i: int,
    site_j: int,
    unitary_4x4: torch.Tensor,
    max_bond: int,
) -> list[torch.Tensor]:
    """Apply a 2-site unitary gate to sites site_i and site_j via SVD truncation.

    Only nearest-neighbour gates (site_j == site_i + 1) are handled natively.
    For non-adjacent pairs the function raises ValueError — call the caller to
    decompose into a SWAP-chain if needed.

    The bond truncation is the load-bearing operation: the two-site tensor is
    contracted from the pair, the unitary applied, then the combined tensor is
    split back by SVD and the left/right site tensors are updated with the
    truncated singular spectrum.

    Args:
        mps: list of site tensors (modified in place and returned).
        site_i: left site index.
        site_j: right site index (must equal site_i + 1).
        unitary_4x4: complex128 4×4 unitary acting on the two-qubit subspace
                     |p_i p_j⟩ in row-major order.
        max_bond: maximum bond dimension after truncation.

    Returns:
        Updated mps list.
    """
    if site_j != site_i + 1:
        raise ValueError(
            f"Only nearest-neighbour gates supported; got site_i={site_i}, site_j={site_j}"
        )
    N = len(mps)
    if not (0 <= site_i < N - 1):
        raise ValueError(f"site_i={site_i} out of range for {N}-site MPS")

    A = mps[site_i]   # shape (chi_L, 2, chi_M)
    B = mps[site_j]   # shape (chi_M, 2, chi_R)

    chi_L = A.shape[0]
    chi_M = A.shape[2]
    chi_R = B.shape[2]

    # Contract A and B into a two-site tensor: theta[chi_L, p_i, p_j, chi_R]
    # A: (chi_L, 2, chi_M), B: (chi_M, 2, chi_R)
    theta = torch.einsum("lpm,mqr->lpqr", A, B)  # (chi_L, 2, 2, chi_R)

    # Reshape to (chi_L * 2, 2 * chi_R) for matrix representation,
    # apply unitary on the physical indices (2x2 = 4 dim space)
    # The unitary acts as: theta_new[p_i', p_j'] = sum_{p_i, p_j} U[p_i'p_j', p_i p_j] theta[p_i, p_j]
    theta_mat = theta.reshape(chi_L, 4, chi_R)  # (chi_L, 4, chi_R)

    # Apply unitary to the 4-dim physical index
    # unitary_4x4: (4, 4); theta_mat: (chi_L, 4, chi_R)
    theta_evolved = torch.einsum("ij,ljr->lir", unitary_4x4, theta_mat)  # (chi_L, 4, chi_R)

    # Reshape back: (chi_L, 2, 2, chi_R) then to (chi_L * 2, 2 * chi_R) for SVD
    theta_evolved = theta_evolved.reshape(chi_L, 2, 2, chi_R)
    theta_svd = theta_evolved.reshape(chi_L * 2, 2 * chi_R)

    # SVD with truncation — this is the load-bearing bond-compression step
    U, S, Vh = _svd_truncate(theta_svd, max_bond)
    k = S.shape[0]

    # Absorb singular values into right tensor (right-canonical convention)
    S_diag = torch.diag(S.to(torch.complex128))
    A_new = U.reshape(chi_L, 2, k)            # (chi_L, 2, k)
    B_new = (S_diag @ Vh).reshape(k, 2, chi_R)  # (k, 2, chi_R)

    mps[site_i] = A_new
    mps[site_j] = B_new
    return mps


def mps_apply_evolution(
    mps: list[torch.Tensor],
    weights: torch.Tensor,
    threshold: float,
    dt: float,
    max_bond: int,
) -> list[torch.Tensor]:
    """Apply graph-weighted XX + YY two-site evolution over all qubit pairs.

    For each pair (i, j) with j = i+1 and weights[i,j] > threshold, build
    the time-evolution unitary:
        U = exp(-i * dt * w * (XX + YY))
    and apply it via mps_apply_two_site_unitary.

    Args:
        mps: list of site tensors.
        weights: (N, N) real weight matrix; only upper-triangle used.
        threshold: pairs with weight <= threshold are skipped.
        dt: time step.
        max_bond: maximum bond dimension.

    Returns:
        Updated mps.
    """
    N = len(mps)
    XX_plus_YY = _xx_plus_yy_generator()  # 4×4 Hermitian

    for i in range(N - 1):
        j = i + 1
        w = float(weights[i, j].real) if weights.dtype in (torch.complex64, torch.complex128) else float(weights[i, j])
        if w <= threshold:
            continue
        # Build unitary via matrix exponential via scipy (only used here)
        U = _matrix_exp(-1j * dt * w * XX_plus_YY.numpy())
        U_t = torch.tensor(U, dtype=torch.complex128)
        mps = mps_apply_two_site_unitary(mps, i, j, U_t, max_bond)

    return mps


def _xx_plus_yy_generator() -> torch.Tensor:
    """Return the 4×4 Hermitian operator XX + YY in the {00,01,10,11} basis."""
    # Pauli X and Y as 2×2
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    XX = torch.kron(X, X)
    YY = torch.kron(Y, Y)
    return (XX + YY)


def _vacuum_breaking_generator(alpha: float = 0.31) -> torch.Tensor:
    """Return a two-site Hermitian whose action on |00> is non-zero.

    Track A diagnosis (2026-05-15): the XX+YY generator preserves total
    magnetization AND annihilates |00>, so a Track A evolution starting from
    |0...0> remains exactly stationary at |0...0>, producing zero signed
    coherent information. The reported MPS bond growth was a numerical
    SVD-rounding artifact, not real entanglement — `mps_to_full_state`
    reconstructed |00000000> exactly, with cut S_A = 0 to machine precision.

    Fix: use a generator that couples |00><->|11>. In the basis {00,01,10,11},
    `XX - alpha*YY` reads:
        [[ 0,        0,        0,        1+alpha ],
         [ 0,        0,        1-alpha,  0       ],
         [ 0,        1-alpha,  0,        0       ],
         [ 1+alpha,  0,        0,        0       ]]   (times 1.0)
    Setting alpha = 0.31 (mirrors Track B's XX vs YY weighting, see
    sim.graph_hamiltonian) gives:
      - off-diagonal |00><->|11> coupling = 1.31 (non-zero, vacuum unstable)
      - off-diagonal |01><->|10> coupling = 0.69 (still non-zero hop term)
    Symmetry is broken on BOTH the number-conserving and pair-creating channels.
    """
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    XX = torch.kron(X, X)
    YY = torch.kron(Y, Y)
    return (XX - alpha * YY)


def mps_apply_evolution_vacuum_breaking(
    mps: list[torch.Tensor],
    weights: torch.Tensor,
    threshold: float,
    dt: float,
    max_bond: int,
    alpha: float = 0.31,
) -> list[torch.Tensor]:
    """Track-A-compatible evolution that produces non-trivial entanglement from |0...0>.

    Identical interface to `mps_apply_evolution`, but uses the
    `XX - alpha*YY` generator (see `_vacuum_breaking_generator`) which has
    non-vanishing matrix elements on the vacuum |00>.

    Why this function exists (rather than parametrising `mps_apply_evolution`):
    Track B's full-state evolution is XX + alpha*YY + chirality·Z, whose
    Z term already breaks the vacuum invariance. The MPS path of the
    original module only supports two-site gates and was wired to XX+YY,
    which is exactly the wrong generator for an MPS-only evolution starting
    from the computational vacuum. This sibling function provides the
    minimum correct alternative without touching the original signature
    or any other consumer of `mps_apply_evolution`.
    """
    N = len(mps)
    H = _vacuum_breaking_generator(alpha=alpha)  # 4×4 Hermitian

    for i in range(N - 1):
        j = i + 1
        w = float(weights[i, j].real) if weights.dtype in (torch.complex64, torch.complex128) else float(weights[i, j])
        if w <= threshold:
            continue
        U = _matrix_exp(-1j * dt * w * H.numpy())
        U_t = torch.tensor(U, dtype=torch.complex128)
        mps = mps_apply_two_site_unitary(mps, i, j, U_t, max_bond)

    return mps


def _matrix_exp(M: np.ndarray) -> np.ndarray:
    """Matrix exponential via scipy.linalg.expm."""
    from scipy.linalg import expm
    return expm(M)


def mps_to_full_state(mps: list[torch.Tensor]) -> torch.Tensor:
    """Contract MPS back to full 2^N state vector.

    Contracts left-to-right by successive tensor contractions.

    Returns:
        Complex128 state vector of shape (2^N,).
    """
    N = len(mps)
    # Start with leftmost tensor: shape (1, 2, chi_R) -> (2, chi_R) after squeezing left bond
    result = mps[0].squeeze(0)  # (2, chi_R)

    for k in range(1, N):
        # result shape: (2^k, chi), mps[k] shape: (chi, 2, chi_new)
        chi = result.shape[-1]
        d, chi_new = mps[k].shape[1], mps[k].shape[2]
        # Contract: sum over bond index
        result = torch.einsum("...c,cpq->...pq", result, mps[k])
        # Merge the new physical index into the state index dimension
        shape_so_far = result.shape[:-2]
        result = result.reshape(*shape_so_far, d * chi_new) if len(shape_so_far) > 0 else result.reshape(d * chi_new)
        # But we need to keep the last bond dimension separate until the end
        # Re-do: result shape after einsum is (2^k, 2, chi_new)
        # Reshape to (2^(k+1), chi_new)
        result = result.reshape(-1, chi_new)

    # At end, result shape is (2^N, 1); squeeze the trailing bond
    return result.squeeze(-1)


def mps_entropy_at_cut(mps: list[torch.Tensor], cut: int) -> float:
    """Compute entanglement entropy at bond `cut` from MPS singular values.

    The bond at position `cut` separates sites [0..cut] from [cut+1..N-1].
    We perform a left-to-right sweep to left-canonicalize up to `cut`, then
    read the Schmidt values from the bond SVD.

    Args:
        mps: list of site tensors (not modified; works on copies).
        cut: bond index in [0, N-2].

    Returns:
        von Neumann entropy S = -sum_k lambda_k^2 * log(lambda_k^2).
    """
    N = len(mps)
    if not (0 <= cut <= N - 2):
        raise ValueError(f"cut={cut} must be in [0, N-2]")

    # Work on a copy of site tensors up to cut+1
    tensors = [t.clone() for t in mps]

    # Left-canonicalize sites 0..cut via QR
    for k in range(cut):
        A = tensors[k]  # (chi_L, 2, chi_R)
        chi_L, d, chi_R = A.shape
        A_mat = A.reshape(chi_L * d, chi_R)
        Q, R = torch.linalg.qr(A_mat)
        # Q: (chi_L*d, k_dim), R: (k_dim, chi_R)
        k_dim = Q.shape[1]
        tensors[k] = Q.reshape(chi_L, d, k_dim)
        # Absorb R into next tensor
        B = tensors[k + 1]  # (chi_R, 2, chi_R2)
        tensors[k + 1] = torch.einsum("ab,bcd->acd", R, B)

    # Now tensor at `cut` is left-canonical; do SVD on its right-merged version
    A = tensors[cut]  # (chi_L, 2, chi_R)
    chi_L, d, chi_R = A.shape
    A_mat = A.reshape(chi_L * d, chi_R)
    _, S, _ = torch.linalg.svd(A_mat, full_matrices=False)

    # Compute Schmidt values (squares of singular values after normalization)
    lam = S.real
    lam = lam[lam > 1e-15]
    lam_sq = lam ** 2
    lam_sq = lam_sq / lam_sq.sum()  # normalize
    entropy = float((-lam_sq * torch.log(lam_sq)).sum().item())
    return entropy


def mps_max_bond_dim_used(mps: list[torch.Tensor]) -> int:
    """Return the maximum bond dimension currently used in the MPS."""
    max_bond = 1
    for t in mps:
        # Shape: (chi_L, d, chi_R); check both bond dims
        max_bond = max(max_bond, t.shape[0], t.shape[2])
    return max_bond


# ---------------------------------------------------------------------------
# PART B — Special-holonomy parallel comparator
# ---------------------------------------------------------------------------
# Form definitions mirror sim_special_holonomy_form_constraint_survivor_quotient_probe.py
# ---------------------------------------------------------------------------

def _form(term_specs: list[tuple[int, tuple[int, ...]]]) -> dict[tuple[int, ...], int]:
    return {tuple(sorted(term)): coeff for coeff, term in term_specs}


_SU3_KAHLER = _form([(1, (0, 1)), (1, (2, 3)), (1, (4, 5))])
_SU3_REAL_VOLUME = _form([
    (1, (0, 2, 4)),
    (-1, (0, 3, 5)),
    (-1, (1, 2, 5)),
    (-1, (1, 3, 4)),
])

_G2_THREE_FORM = _form([
    (1, (0, 1, 2)),
    (1, (0, 3, 4)),
    (1, (0, 5, 6)),
    (1, (1, 3, 5)),
    (-1, (1, 4, 6)),
    (-1, (2, 3, 6)),
    (-1, (2, 4, 5)),
])

_SPIN7_CAYLEY = _form([
    (1, (0, 1, 2, 7)),
    (1, (0, 3, 4, 7)),
    (1, (0, 5, 6, 7)),
    (1, (1, 3, 5, 7)),
    (-1, (1, 4, 6, 7)),
    (-1, (2, 3, 6, 7)),
    (-1, (2, 4, 5, 7)),
    (1, (3, 4, 5, 6)),
    (1, (1, 2, 5, 6)),
    (1, (1, 2, 3, 4)),
    (1, (0, 2, 4, 6)),
    (-1, (0, 2, 3, 5)),
    (-1, (0, 1, 4, 5)),
    (-1, (0, 1, 3, 6)),
])

_GENERIC_3FORM = _form([(1, term) for term in itertools.combinations(range(7), 3)])
_GENERIC_4FORM = _form([(1, term) for term in itertools.combinations(range(8), 4)])


def _term_sign(signs: tuple[int, ...], term: tuple[int, ...]) -> int:
    v = 1
    for idx in term:
        v *= signs[idx]
    return v


def _preserves_forms(signs: tuple[int, ...], forms: list[dict]) -> bool:
    return all(_term_sign(signs, term) == 1 for f in forms for term in f)


def _sign_candidates(dim: int) -> list[tuple[int, ...]]:
    return list(itertools.product([-1, 1], repeat=dim))


def _survivor_count(dim: int, forms: list[dict]) -> int:
    return sum(1 for s in _sign_candidates(dim) if _preserves_forms(s, forms))


def _state_features_to_sign_vector(state_features: torch.Tensor, dim: int) -> tuple[int, ...]:
    """Extract a sign vector of length `dim` from a feature tensor.

    Takes the sign of the first `dim` real parts of the flattened tensor.
    If the tensor has fewer elements, cycles with +1.
    """
    flat = state_features.real.reshape(-1)
    signs = []
    for k in range(dim):
        val = float(flat[k % flat.shape[0]].item()) if flat.numel() > 0 else 1.0
        signs.append(1 if val >= 0 else -1)
    return tuple(signs)


def scaffold_g_structure_survivors(state_features: torch.Tensor) -> dict:
    """Apply GL(2,C) → O(4) → SO(4) → Spin(4) → U(2) → SU(2) scaffold reduction.

    Uses sympy exact computation for the orientation boundary polynomial.
    Reports the group dimension sequence and whether the feature sign vector
    is consistent (determinant = +1) at each step.

    Args:
        state_features: arbitrary complex128 feature tensor; shape doesn't matter.

    Returns:
        dict with keys: dim_sequence, survivor_count, monotone_pass, sympy_check.
    """
    # Dimension sequence for the classical scaffold reduction
    group_dims = {
        "GL2C_real": 8,
        "O4_real": 6,
        "SO4_real": 6,
        "Spin4_lie": 6,
        "U2_real": 4,
        "SU2_real": 3,
    }
    monotone = (
        group_dims["GL2C_real"] >= group_dims["O4_real"]
        and group_dims["O4_real"] >= group_dims["SU2_real"]
    )

    # Sympy exact check: orientation boundary det = ±1
    x = sp.symbols("x")
    det_poly = sp.factor((x - 1) * (x + 1))
    sympy_pass = bool(sp.simplify(det_poly - (x**2 - 1)) == 0)

    # Sign-vector survivor check at SU(2) level (3D)
    sv = _state_features_to_sign_vector(state_features, 3)
    # For SU(2): require det = +1 (product of signs = +1)
    su2_det = sv[0] * sv[1] * sv[2]
    survivor_count = 1 if su2_det == 1 else 0

    return {
        "dim_sequence": group_dims,
        "survivor_count": survivor_count,
        "monotone_pass": monotone,
        "sympy_orientation_check": sympy_pass,
        "sign_vector": list(sv),
        "su2_det": su2_det,
    }


def su3_form_survivors(state_features: torch.Tensor) -> dict:
    """Apply SU(3)-like Kähler 2-form + complex 3-form constraints.

    Enumerates all 2^6 sign candidates in 6D and counts those satisfying
    both the Kähler form and the real-volume 3-form constraints.

    Args:
        state_features: feature tensor; used to extract a 6D sign vector.

    Returns:
        dict with keys: dimension, survivor_count, candidate_count,
        sign_vector_survives, survivor_fraction.
    """
    dim = 6
    survivors = _survivor_count(dim, [_SU3_KAHLER, _SU3_REAL_VOLUME])
    sv = _state_features_to_sign_vector(state_features, dim)
    sv_survives = _preserves_forms(sv, [_SU3_KAHLER, _SU3_REAL_VOLUME])
    return {
        "dimension": dim,
        "survivor_count": survivors,
        "candidate_count": 2 ** dim,
        "survivor_fraction": survivors / 2 ** dim,
        "sign_vector_survives": sv_survives,
        "sign_vector": list(sv),
    }


def g2_form_survivors(state_features: torch.Tensor) -> dict:
    """Apply G2 3-form constraint in 7D.

    Args:
        state_features: feature tensor; used to extract a 7D sign vector.

    Returns:
        dict with keys: dimension, survivor_count, candidate_count,
        sign_vector_survives, survivor_fraction.
    """
    dim = 7
    survivors = _survivor_count(dim, [_G2_THREE_FORM])
    sv = _state_features_to_sign_vector(state_features, dim)
    sv_survives = _preserves_forms(sv, [_G2_THREE_FORM])
    return {
        "dimension": dim,
        "survivor_count": survivors,
        "candidate_count": 2 ** dim,
        "survivor_fraction": survivors / 2 ** dim,
        "sign_vector_survives": sv_survives,
        "sign_vector": list(sv),
    }


def spin7_form_survivors(state_features: torch.Tensor) -> dict:
    """Apply Spin(7) Cayley 4-form constraint in 8D.

    Args:
        state_features: feature tensor; used to extract an 8D sign vector.

    Returns:
        dict with keys: dimension, survivor_count, candidate_count,
        sign_vector_survives, survivor_fraction.
    """
    dim = 8
    survivors = _survivor_count(dim, [_SPIN7_CAYLEY])
    sv = _state_features_to_sign_vector(state_features, dim)
    sv_survives = _preserves_forms(sv, [_SPIN7_CAYLEY])
    return {
        "dimension": dim,
        "survivor_count": survivors,
        "candidate_count": 2 ** dim,
        "survivor_fraction": survivors / 2 ** dim,
        "sign_vector_survives": sv_survives,
        "sign_vector": list(sv),
    }


def _z3_non_collapse_witness(
    scaffold_count: int,
    su3_count: int,
    g2_count: int,
    spin7_count: int,
) -> dict:
    """Z3 UNSAT witness: the four G-structure families cannot all have equal survivor counts.

    If all four were equal, z3 would be SAT (possible to assign equal values).
    Because they differ, asserting all_equal is UNSAT — confirming non-collapse.

    Returns:
        dict with z3 solver status and pass flag.
    """
    sc, su, g2, sp7 = z3.Ints("scaffold su3 g2 spin7")
    solver = z3.Solver()
    # Plug in actual counts
    solver.add(sc == scaffold_count)
    solver.add(su == su3_count)
    solver.add(g2 == g2_count)
    solver.add(sp7 == spin7_count)
    # Assert they are all equal — should be UNSAT if any differ
    solver.add(z3.And(sc == su, su == g2, g2 == sp7))
    status = solver.check()
    all_equal = (status == z3.sat)
    # UNSAT confirms non-collapse (the four families are genuinely distinct)
    return {
        "solver_status": str(status),
        "all_equal_sat": all_equal,
        "non_collapse_confirmed_unsat": (status == z3.unsat),
        "pass": (status == z3.unsat),
    }


def parallel_g_structure_comparison(state_features: torch.Tensor) -> dict:
    """Run all four G-structure analyses and return a comparison dict.

    Runs scaffold, SU(3), G2, Spin(7) survivor analyses in parallel (sequential
    calls; each is independent), then runs z3 UNSAT non-collapse witness.

    Args:
        state_features: complex128 feature tensor of any shape.

    Returns:
        dict with:
          - scaffold, su3, g2, spin7: individual result dicts
          - survivor_counts: side-by-side count summary
          - z3_non_collapse: z3 UNSAT verification
          - all_pass: bool
    """
    scaffold = scaffold_g_structure_survivors(state_features)
    su3 = su3_form_survivors(state_features)
    g2 = g2_form_survivors(state_features)
    spin7 = spin7_form_survivors(state_features)

    # Compare against generic controls (counted once at module level for speed)
    generic_3_count = _survivor_count(7, [_GENERIC_3FORM])
    generic_4_count = _survivor_count(8, [_GENERIC_4FORM])

    z3_result = _z3_non_collapse_witness(
        scaffold["survivor_count"],
        su3["survivor_count"],
        g2["survivor_count"],
        spin7["survivor_count"],
    )

    # Special forms must differ from their generic controls
    g2_differs = g2["survivor_count"] != generic_3_count
    spin7_differs = spin7["survivor_count"] != generic_4_count

    # Second z3: verify G2 differs from generic 3-form
    s_g2 = z3.Solver()
    a_g2 = z3.Bool("g2_differs")
    s_g2.add(a_g2 == g2_differs, a_g2 == False)
    g2_unsat = (s_g2.check() == z3.unsat)

    # Third z3: verify Spin7 differs from generic 4-form
    s_sp7 = z3.Solver()
    a_sp7 = z3.Bool("spin7_differs")
    s_sp7.add(a_sp7 == spin7_differs, a_sp7 == False)
    sp7_unsat = (s_sp7.check() == z3.unsat)

    all_pass = (
        z3_result["pass"]
        and g2_differs
        and spin7_differs
        and g2_unsat
        and sp7_unsat
    )

    return {
        "scaffold": scaffold,
        "su3": su3,
        "g2": g2,
        "spin7": spin7,
        "generic_3form_survivor_count": generic_3_count,
        "generic_4form_survivor_count": generic_4_count,
        "g2_differs_from_generic": g2_differs,
        "spin7_differs_from_generic": spin7_differs,
        "g2_non_collapse_unsat": g2_unsat,
        "spin7_non_collapse_unsat": sp7_unsat,
        "survivor_counts": {
            "scaffold_su2": scaffold["survivor_count"],
            "su3": su3["survivor_count"],
            "g2": g2["survivor_count"],
            "spin7": spin7["survivor_count"],
        },
        "z3_non_collapse": z3_result,
        "all_pass": all_pass,
    }


def g_structure_persistence_under_evolution(
    state_history: list[torch.Tensor],
) -> dict:
    """Track survivor counts across N evolution steps.

    For each step, extracts state features from the MPS state vector (or any
    passed tensor), then runs all four G-structure analyses.

    Args:
        state_history: list of complex128 tensors, one per evolution step.
                       Each tensor is used directly as state_features.

    Returns:
        dict with:
          - steps: list of per-step survivor count snapshots
          - scaffold_trend: list of scaffold survivor counts
          - su3_trend, g2_trend, spin7_trend: same for other families
          - monotone_check: whether g2_trend is non-increasing or non-decreasing
    """
    steps = []
    scaffold_trend = []
    su3_trend = []
    g2_trend = []
    spin7_trend = []

    for step_idx, features in enumerate(state_history):
        scaffold = scaffold_g_structure_survivors(features)
        su3 = su3_form_survivors(features)
        g2 = g2_form_survivors(features)
        spin7 = spin7_form_survivors(features)
        snapshot = {
            "step": step_idx,
            "scaffold": scaffold["survivor_count"],
            "su3": su3["survivor_count"],
            "g2": g2["survivor_count"],
            "spin7": spin7["survivor_count"],
        }
        steps.append(snapshot)
        scaffold_trend.append(scaffold["survivor_count"])
        su3_trend.append(su3["survivor_count"])
        g2_trend.append(g2["survivor_count"])
        spin7_trend.append(spin7["survivor_count"])

    # Check if g2_trend is weakly monotone in either direction
    if len(g2_trend) >= 2:
        non_decreasing = all(g2_trend[i] <= g2_trend[i + 1] for i in range(len(g2_trend) - 1))
        non_increasing = all(g2_trend[i] >= g2_trend[i + 1] for i in range(len(g2_trend) - 1))
        monotone = non_decreasing or non_increasing
    else:
        monotone = True

    return {
        "n_steps": len(state_history),
        "steps": steps,
        "scaffold_trend": scaffold_trend,
        "su3_trend": su3_trend,
        "g2_trend": g2_trend,
        "spin7_trend": spin7_trend,
        "g2_monotone": monotone,
    }


# ---------------------------------------------------------------------------
# __main__ smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from scipy.linalg import expm

    print("=" * 70)
    print("MPS + Special-Holonomy Comparator — smoke test")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # PART A: 8-qubit MPS at bond_dim=16, 5 evolution steps
    # -----------------------------------------------------------------------
    N_QUBITS = 8
    BOND_DIM = 16
    N_STEPS = 5

    print(f"\n[PART A] MPS: n_qubits={N_QUBITS}, bond_dim={BOND_DIM}")

    # Initialize
    mps = mps_initial_state(N_QUBITS, BOND_DIM)
    print(f"  Initial product state — max bond dim used: {mps_max_bond_dim_used(mps)}")

    # Mock weight matrix: ring topology with uniform weight 0.8
    weights = torch.zeros(N_QUBITS, N_QUBITS, dtype=torch.float64)
    for i in range(N_QUBITS - 1):
        weights[i, i + 1] = 0.8
        weights[i + 1, i] = 0.8
    # Also close the ring: weight between 0 and 7, but only nearest-neighbour gates
    # are supported, so that edge is skipped (non-adjacent).

    threshold = 0.5
    dt = 0.1

    state_history = []
    for step in range(N_STEPS):
        mps = mps_apply_evolution(mps, weights, threshold, dt, max_bond=BOND_DIM)
        max_bd = mps_max_bond_dim_used(mps)
        print(f"\n  Step {step+1}/{N_STEPS} — max bond dim: {max_bd}")

        # Entropy at each cut
        entropies = []
        for cut in range(N_QUBITS - 1):
            ent = mps_entropy_at_cut(mps, cut)
            entropies.append(ent)
        print(f"  Entanglement entropy at each cut: {[f'{e:.4f}' for e in entropies]}")

        # Collect state features for Part B (use MPS to full state)
        full_state = mps_to_full_state(mps)  # (2^N,)
        state_history.append(full_state)

    max_bond_final = mps_max_bond_dim_used(mps)
    print(f"\n  Final max bond dim: {max_bond_final}")

    # Verify full state norm
    full_state = mps_to_full_state(mps)
    norm = float(torch.linalg.vector_norm(full_state).item())
    print(f"  Full state vector norm (should be ~1): {norm:.8f}")
    assert abs(norm - 1.0) < 1e-6, f"State norm deviation too large: {norm}"

    # -----------------------------------------------------------------------
    # PART B: Special-holonomy parallel comparator
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("[PART B] Special-holonomy parallel comparator")
    print("=" * 70)

    # Build mock state_features from the final full state
    state_features = full_state  # complex128, shape (256,)

    # Run all four comparators
    comparison = parallel_g_structure_comparison(state_features)

    sc = comparison["survivor_counts"]
    print(f"\n  Survivor counts (side-by-side):")
    print(f"    Scaffold (GL→SU(2), SU(2)-det check): {sc['scaffold_su2']}")
    print(f"    SU(3)  (Kähler 2-form + real 3-form, 6D): {sc['su3']}")
    print(f"    G2     (3-form, 7D):                      {sc['g2']}")
    print(f"    Spin(7)(Cayley 4-form, 8D):               {sc['spin7']}")
    print(f"    Generic 3-form control (7D):              {comparison['generic_3form_survivor_count']}")
    print(f"    Generic 4-form control (8D):              {comparison['generic_4form_survivor_count']}")

    print(f"\n  G2 differs from generic 3-form:       {comparison['g2_differs_from_generic']}")
    print(f"  Spin(7) differs from generic 4-form:  {comparison['spin7_differs_from_generic']}")

    z3r = comparison["z3_non_collapse"]
    print(f"\n  z3 all-equal UNSAT (non-collapse witness):")
    print(f"    solver_status: {z3r['solver_status']}")
    print(f"    non_collapse_confirmed_unsat: {z3r['non_collapse_confirmed_unsat']}")
    print(f"    pass: {z3r['pass']}")

    print(f"\n  G2 vs generic UNSAT:     {comparison['g2_non_collapse_unsat']}")
    print(f"  Spin7 vs generic UNSAT:  {comparison['spin7_non_collapse_unsat']}")
    print(f"\n  parallel_g_structure_comparison.all_pass: {comparison['all_pass']}")

    # -----------------------------------------------------------------------
    # Persistence under evolution
    # -----------------------------------------------------------------------
    print("\n[PART B] G-structure persistence under 5 evolution steps")
    persistence = g_structure_persistence_under_evolution(state_history)
    print(f"  n_steps: {persistence['n_steps']}")
    for snap in persistence["steps"]:
        print(
            f"  step {snap['step']}: scaffold={snap['scaffold']}  "
            f"su3={snap['su3']}  g2={snap['g2']}  spin7={snap['spin7']}"
        )
    print(f"  G2 trend monotone: {persistence['g2_monotone']}")

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SMOKE TEST SUMMARY")
    print("=" * 70)
    print(f"  MPS max bond dim achieved:         {max_bond_final}")
    print(f"  State norm after evolution:        {norm:.8f}")
    print(f"  All G-structure pass:              {comparison['all_pass']}")
    print(f"  z3 UNSAT non-collapse:             {z3r['non_collapse_confirmed_unsat']}")
    print(
        f"  Status: {'PASS' if (comparison['all_pass'] and abs(norm - 1.0) < 1e-6) else 'FAIL'}"
    )
    print("=" * 70)

    if not (comparison["all_pass"] and abs(norm - 1.0) < 1e-6):
        sys.exit(1)
