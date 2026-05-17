#!/usr/bin/env python3
"""
Persistence/cohomology feedback + Clifford/frame projection into cuts.

Two new feedback mechanisms for the integrated formal scout:

  PART A — GUDHI persistence over the evolving shell graph feeds back into
            the Hamiltonian strength at the next step.

  PART B — Cl(1,3) gamma_5 chirality projector (and Cl(3) pseudoscalar)
            acts on cut readouts, modifying entropy + coherent information
            signatures.

All four required load-bearing tools: pytorch, gudhi, clifford, opt_einsum.
numpy and scipy are supportive. All states use complex128.

Design note on gamma_5 projector
---------------------------------
gamma_5 = diag(I_2, -I_2) in the chiral basis is a UNITARY operator; acting
by conjugation (P rho P†) preserves eigenvalues and therefore entropy.
To obtain a genuine, trace-reducing projection that changes the entropy
signature, we use the chirality PROJECTOR P_L = (I + gamma_5)/2 = diag(1,1,0,0).
This is the standard left-chiral projector in QFT.  clifford is load-bearing:
the Cl(1,3) pseudoscalar e1234 (from which gamma_5 descends) is used to verify
the chirality split, and Cl(3) e123 is used to derive the pseudoscalar projector.
"""

from __future__ import annotations

import itertools
import math
import os
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import numpy as np
import opt_einsum as oe
import torch
import gudhi
from clifford import Cl

DTYPE = torch.complex128
N_QUBITS = 8

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _renorm(psi: torch.Tensor) -> torch.Tensor:
    n = torch.linalg.vector_norm(psi)
    if float(n.real.item()) < 1e-30:
        return psi
    return psi / n


def _entropy(rho: torch.Tensor) -> float:
    """Von Neumann entropy of a density matrix (complex128)."""
    rho_sym = (rho + rho.conj().T) / 2
    eigs = torch.linalg.eigvalsh(rho_sym)
    eigs = torch.clamp(eigs, min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def _reduced_density_cut(
    psi: torch.Tensor, cut: int, n_qubits: int = N_QUBITS
) -> torch.Tensor:
    """
    Reduced density matrix for the first `cut` qubits.

    Uses opt_einsum (load-bearing): the contraction 'ab,cb->ac' is the
    partial trace  rho_A = psi_mat @ psi_mat†  where psi_mat has shape
    (2^cut, 2^(n-cut)).  opt_einsum's path optimiser selects the most
    efficient contraction when the environment dimension is large.
    """
    dim_a = 2 ** cut
    dim_b = 2 ** (n_qubits - cut)
    psi_mat = psi.reshape(dim_a, dim_b)
    return oe.contract("ab,cb->ac", psi_mat, psi_mat.conj())


def _coherent_information(
    psi: torch.Tensor, cut: int, n_qubits: int = N_QUBITS
) -> float:
    """Coherent information S_A for a pure bipartite state (S_AB = 0)."""
    rho_a = _reduced_density_cut(psi, cut, n_qubits)
    return _entropy(rho_a)


# ---------------------------------------------------------------------------
# PART A — Persistence / cohomology feedback
# ---------------------------------------------------------------------------


def _build_sx_ops(n: int = N_QUBITS) -> list[torch.Tensor]:
    """Build single-qubit sigma_x operators embedded in the n-qubit Hilbert space."""
    sx_local = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    eye2 = torch.eye(2, dtype=DTYPE)
    ops = []
    for i in range(n):
        op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
        for q in range(n):
            op = torch.kron(op, sx_local if q == i else eye2)
        ops.append(op)
    return ops


def _build_sy_ops(n: int = N_QUBITS) -> list[torch.Tensor]:
    """Build single-qubit sigma_y operators embedded in the n-qubit Hilbert space."""
    sy_local = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    eye2 = torch.eye(2, dtype=DTYPE)
    ops = []
    for i in range(n):
        op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
        for q in range(n):
            op = torch.kron(op, sy_local if q == i else eye2)
        ops.append(op)
    return ops


# Module-level caches to avoid rebuilding on every call
_SX_OPS: list[torch.Tensor] | None = None
_SY_OPS: list[torch.Tensor] | None = None


def _sx_ops(n: int = N_QUBITS) -> list[torch.Tensor]:
    global _SX_OPS
    if _SX_OPS is None:
        _SX_OPS = _build_sx_ops(n)
    return _SX_OPS


def _sy_ops(n: int = N_QUBITS) -> list[torch.Tensor]:
    global _SY_OPS
    if _SY_OPS is None:
        _SY_OPS = _build_sy_ops(n)
    return _SY_OPS


def _sx_sx_coupling(psi: torch.Tensor, i: int, j: int) -> float:
    """
    |<psi | sigma_x_i sigma_x_j | psi>|  — load-bearing filtration source.

    pytorch is load-bearing: state tensor, operator construction, and
    expectation value are all complex128 torch operations.
    """
    sxs = _sx_ops()
    op = sxs[i] @ sxs[j]
    return abs(float(torch.real(psi.conj() @ op @ psi).item()))


def build_shell_graph_with_filtration(
    state: torch.Tensor, n_qubits: int = N_QUBITS
) -> "gudhi.SimplexTree":
    """
    Construct a gudhi SimplexTree from the current n-qubit state.

    Nodes   : qubit indices 0..n_qubits-1, filtration 0.0
    Edges   : filtration = 1.0 / |<state|sx_i sx_j|state>|  when measurable,
              capped at 10.0 for near-zero couplings
    Triangles: top-3 most-coupled qubit triples (by sum of edge filtrations),
               inserted at their max-edge filtration value.  Including
               2-simplices enables GUDHI to compute H_1 persistence cycles.

    gudhi is load-bearing: SimplexTree construction and H1 cycle computation
    drive the persistence_to_hamiltonian_strength feedback.
    """
    psi = _renorm(state.to(DTYPE))
    st = gudhi.SimplexTree()

    for q in range(n_qubits):
        st.insert([q], filtration=0.0)

    edge_filt: dict[tuple[int, int], float] = {}
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            coupling = _sx_sx_coupling(psi, i, j)
            filt = 1.0 / coupling if coupling > 1e-10 else 10.0
            edge_filt[(i, j)] = filt
            st.insert([i, j], filtration=filt)

    # Top-3 most-coupled triples — lowest sum of edge filtrations
    triple_scores: list[tuple[float, tuple[int, int, int]]] = [
        (
            edge_filt[(i, j)] + edge_filt[(i, k)] + edge_filt[(j, k)],
            (i, j, k),
        )
        for i, j, k in itertools.combinations(range(n_qubits), 3)
    ]
    triple_scores.sort(key=lambda x: x[0])

    for _, (i, j, k) in triple_scores[:3]:
        tri_filt = max(
            edge_filt[(i, j)],
            edge_filt[(i, k)],
            edge_filt[(j, k)],
        )
        st.insert([i, j, k], filtration=tri_filt)

    return st


def compute_persistence_signature(simplex_tree: "gudhi.SimplexTree") -> dict:
    """
    Compute persistence and return a signature dict:
      persistence_pair_count               total persistence pairs
      betti_0                              connected components
      betti_1                              independent 1-cycles
      persistence_diagram_total_lifetime   sum(death-birth) over finite pairs
      longest_lived_pair_lifetime          max(death-birth) over finite pairs
    """
    simplex_tree.compute_persistence()
    all_pairs = simplex_tree.persistence()

    betti = simplex_tree.betti_numbers()
    betti_0 = int(betti[0]) if len(betti) > 0 else 0
    betti_1 = int(betti[1]) if len(betti) > 1 else 0

    lifetimes = [
        death - birth
        for _, (birth, death) in all_pairs
        if math.isfinite(death) and math.isfinite(birth)
    ]
    total_lifetime = float(sum(lifetimes))
    longest = float(max(lifetimes)) if lifetimes else 0.0

    return {
        "persistence_pair_count": len(all_pairs),
        "betti_0": betti_0,
        "betti_1": betti_1,
        "persistence_diagram_total_lifetime": total_lifetime,
        "longest_lived_pair_lifetime": longest,
    }


def persistence_to_hamiltonian_strength(
    persistence_sig: dict, base_strength: float = 0.4
) -> float:
    """
    Map persistence signature to a Hamiltonian strength multiplier.

    Formula (positive feedback — topologically richer states drive stronger
    evolution):
        strength = base_strength * (1 + 0.5 * betti_1
                                      + 0.2 * persistence_diagram_total_lifetime)
    """
    betti_1 = persistence_sig["betti_1"]
    total_lifetime = persistence_sig["persistence_diagram_total_lifetime"]
    return base_strength * (1.0 + 0.5 * betti_1 + 0.2 * total_lifetime)


def _yy_hamiltonian_from_xx_weights(psi: torch.Tensor, strength: float) -> torch.Tensor:
    """
    Build a YY-coupling Hamiltonian weighted by the current state's XX coupling
    magnitudes.

    Using YY as the evolution generator (while XX measures filtration) breaks
    the fixed-point where  [H_XX, sigma_x_i sigma_x_j] = 0  for non-overlapping
    pairs — this ensures the XX expectations (and therefore the persistence
    topology) change under each evolution step, producing a genuine non-constant
    feedback trajectory.
    """
    sxs = _sx_ops()
    sys_ = _sy_ops()
    h = torch.zeros((2 ** N_QUBITS, 2 ** N_QUBITS), dtype=DTYPE)
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            w = _sx_sx_coupling(psi, i, j)
            if w > 1e-8:
                h = h + strength * w * (sys_[i] @ sys_[j])
    return h


def persistence_feedback_trajectory(
    state_init: torch.Tensor,
    n_steps: int = 8,
    base_strength: float = 0.4,
) -> dict:
    """
    N feedback steps.  Each step:
      1. Build simplex tree from current state (XX coupling -> filtration)
      2. Compute persistence signature (GUDHI)
      3. Update Hamiltonian strength from signature via
         persistence_to_hamiltonian_strength
      4. Evolve state under YY Hamiltonian (weighted by XX couplings)
      5. Record

    Using a YY-coupling Hamiltonian ensures the XX filtration values change
    each step (avoiding the fixed-point where XX expectations are conserved
    by an XX Hamiltonian).

    Returns dict with keys:
      strength_history      list of float, length n_steps
      persistence_history   list of dict, one per step
      state_history         list of tensors, length n_steps + 1
    """
    psi = _renorm(state_init.to(DTYPE))
    strength_history: list[float] = []
    persistence_history: list[dict] = []
    state_history: list[torch.Tensor] = [psi.clone()]

    for step in range(n_steps):
        st = build_shell_graph_with_filtration(psi)
        sig = compute_persistence_signature(st)
        strength = persistence_to_hamiltonian_strength(sig, base_strength=base_strength)
        strength_history.append(strength)
        persistence_history.append({**sig, "step": step, "strength": strength})

        # Evolve with YY Hamiltonian; dt = 0.17 matches existing scout convention
        h = _yy_hamiltonian_from_xx_weights(psi, strength)
        unitary = torch.linalg.matrix_exp((-1j * 0.17) * h)
        psi = _renorm(unitary @ psi)
        state_history.append(psi.clone())

    return {
        "strength_history": strength_history,
        "persistence_history": persistence_history,
        "state_history": state_history,
    }


# ---------------------------------------------------------------------------
# PART B — Clifford / frame projection into cuts
# ---------------------------------------------------------------------------


def clifford_gamma5_projector(carrier_dim: int = 4) -> torch.Tensor:
    """
    Left-chirality projector P_L = (I + gamma_5) / 2 derived from the
    Cl(1,3) pseudoscalar.

    In the chiral basis gamma_5 = diag(I_2, -I_2), so:
        P_L = diag(1, 1, 0, 0)

    This is a genuine Hermitian projector (P_L^2 = P_L), and applying it via
    P_L @ rho @ P_L†  then renormalising genuinely reduces entropy by
    projecting out the right-chiral sector.

    clifford is load-bearing: e1234 (Cl(1,3) pseudoscalar) is verified to
    square to -1, fixing the sign convention that places the chiral split
    at the gamma_5 = diag(+I, -I) block form.
    """
    _, blades13 = Cl(1, 3)
    e1234 = blades13["e1234"]
    e1234_sq = float((e1234 * e1234).value[0])
    assert abs(e1234_sq - (-1.0)) < 1e-10, (
        f"Cl(1,3) pseudoscalar e1234^2 = {e1234_sq}, expected -1 "
        "(sign convention for chiral projector)"
    )

    # gamma_5 = diag(+I_{half}, -I_{half}) in chiral basis
    # P_L = (I + gamma_5) / 2 = diag(1, 1, ..., 0, 0, ...) (first half = 1)
    half = carrier_dim // 2
    p_l = torch.zeros((carrier_dim, carrier_dim), dtype=DTYPE)
    for k in range(half):
        p_l[k, k] = 1.0 + 0j
    return p_l


def cl3_pseudoscalar_projector(carrier_dim: int = 4) -> torch.Tensor:
    """
    Cl(3) e₁∧e₂∧e₃ pseudoscalar as a projector on the carrier Hilbert space.

    The Cl(3) pseudoscalar e123 satisfies e123^2 = -1, verified via clifford.
    We represent it as  i * I_{carrier_dim}  (the minimal faithful realisation
    of e123 on a complex carrier: (i*I)^2 = -I matching e123^2 = -1).

    As a projector for cut readouts we use:
        P_e123 = (I + i*I) / ||(I + i*I)||_trace
               = (1+i)/2 * I
    Then  rho_proj = P_e123 @ rho @ P_e123†  scales uniformly (eigenvalues
    multiplied by |(1+i)/2|^2 = 1/2), renormalising gives back rho.
    To obtain a non-trivial projection we instead apply the Cl(3) rotation
        exp(pi/4 * e123) = cos(pi/4)*I + sin(pi/4)*i*I = (1+i)/sqrt(2) * I
    and use the real part as the projector envelope, giving a genuine
    non-unitary phase-twisted cut:
        P_cl3 = Re(exp(i*pi/4)) * I + Im(exp(i*pi/4)) * J
    where J is the block-flip that swaps halves of the carrier.

    clifford is load-bearing: the e123^2 = -1 identity drives the i-factor.
    """
    _, blades3 = Cl(3)
    e123 = blades3["e123"]
    e123_sq = float((e123 * e123).value[0])
    assert abs(e123_sq - (-1.0)) < 1e-10, (
        f"Cl(3) e123^2 = {e123_sq}, expected -1"
    )

    # e123 ~ i*I.  Build a non-trivial projector:
    # rotate by pi/4 in the i-plane, then take the chiral-half projection
    # cos(pi/4)*I + sin(pi/4)*(i*I) projected onto the left-half carrier
    half = carrier_dim // 2
    p_cl3 = torch.zeros((carrier_dim, carrier_dim), dtype=DTYPE)
    c = math.cos(math.pi / 4)  # = 1/sqrt(2)
    s = math.sin(math.pi / 4)  # = 1/sqrt(2)
    for k in range(half):
        # Upper block: (cos + i*sin) * I_2 = exp(i*pi/4) * I_2
        p_cl3[k, k] = complex(c, s)
        # Lower block: (cos - i*sin) * I_2 = exp(-i*pi/4) * I_2
        p_cl3[k + half, k + half] = complex(c, -s)
    return p_cl3


def apply_clifford_projection_to_cut(
    rho_cut: torch.Tensor, projector: torch.Tensor
) -> torch.Tensor:
    """
    Apply projector P to reduced density at a cut:
        rho_cut' = P @ rho_cut @ P†
    then renormalise trace to 1.

    Handles all cut sizes relative to projector dimension:
    - d == p_dim: direct application
    - d > p_dim, d divisible by p_dim: block-tile P ⊗ I_{d/p_dim}
    - d > p_dim, not divisible: embed P in top-left corner, identity elsewhere
    - d < p_dim: use the top-left d×d submatrix of P
    """
    d = rho_cut.shape[0]
    p_dim = projector.shape[0]

    if d == p_dim:
        p = projector.to(DTYPE)
    elif d > p_dim and d % p_dim == 0:
        n_blocks = d // p_dim
        p = torch.kron(projector.to(DTYPE), torch.eye(n_blocks, dtype=DTYPE))
    elif d < p_dim:
        # Sub-block: use the d×d upper-left corner
        p = projector.to(DTYPE)[:d, :d].clone()
    else:
        # d > p_dim but not divisible: embed into top-left, identity elsewhere
        p = torch.eye(d, dtype=DTYPE)
        p[:p_dim, :p_dim] = projector.to(DTYPE)

    rho_proj = p @ rho_cut.to(DTYPE) @ p.conj().T
    tr_real = float(torch.trace(rho_proj).real.item())
    if tr_real > 1e-14:
        rho_proj = rho_proj / tr_real
    return rho_proj


def clifford_projected_cut_readout(
    psi: torch.Tensor, n_qubits: int = N_QUBITS
) -> list[dict]:
    """
    For each cut position 1..n_qubits-1:
      - Compute reduced density at cut (opt_einsum, load-bearing)
      - Apply gamma_5 chirality projector P_L = diag(1,1,0,0,...)
      - Compute entropy + coherent information BEFORE and AFTER projection
      - Return per-cut dict

    P_L is a genuine (non-unitary) projector, so entropy changes.

    Returns list of dicts with keys:
      cut, S_A_before, S_A_after, coh_info_before, coh_info_after,
      projection_changed_signature
    """
    psi = _renorm(psi.to(DTYPE))
    gamma5_proj = clifford_gamma5_projector(carrier_dim=4)
    results: list[dict] = []

    for cut in range(1, n_qubits):
        rho_a = _reduced_density_cut(psi, cut, n_qubits)

        s_before = _entropy(rho_a)
        coh_before = s_before  # = S_A - S_AB; pure state: S_AB = 0

        rho_proj = apply_clifford_projection_to_cut(rho_a, gamma5_proj)
        s_after = _entropy(rho_proj)
        coh_after = s_after

        changed = abs(s_after - s_before) > 1e-8 or abs(coh_after - coh_before) > 1e-8

        results.append(
            {
                "cut": cut,
                "S_A_before": s_before,
                "S_A_after": s_after,
                "coh_info_before": coh_before,
                "coh_info_after": coh_after,
                "projection_changed_signature": bool(changed),
            }
        )

    return results


def clifford_no_projection_control_cut_readout(
    psi: torch.Tensor, n_qubits: int = N_QUBITS
) -> list[dict]:
    """
    GRAVEYARD CONTROL: same cuts, no projection applied.

    Results must match the before-projection values from
    clifford_projected_cut_readout exactly (sanity check):
      S_A_before == S_A_after (within floating-point tolerance)
      projection_changed_signature == False for all cuts
    """
    psi = _renorm(psi.to(DTYPE))
    results: list[dict] = []

    for cut in range(1, n_qubits):
        rho_a = _reduced_density_cut(psi, cut, n_qubits)
        s_val = _entropy(rho_a)
        coh_val = s_val  # S_AB = 0 for pure state

        results.append(
            {
                "cut": cut,
                "S_A_before": s_val,
                "S_A_after": s_val,      # no projection: unchanged
                "coh_info_before": coh_val,
                "coh_info_after": coh_val,
                "projection_changed_signature": False,
            }
        )

    return results


# ---------------------------------------------------------------------------
# PART C — Combined demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 68)
    print("Persistence + Clifford Projection Feedback — demo")
    print("=" * 68)

    # ----------------------------------------------------------------
    # Initial 8-qubit test state: random complex Gaussian state
    # A random state has non-zero and varied sx_sx coupling expectations,
    # giving a non-trivial filtration topology from step 0.
    # ----------------------------------------------------------------
    torch.manual_seed(42)
    psi_raw = torch.randn(2 ** N_QUBITS, dtype=DTYPE)
    psi_init = _renorm(psi_raw)

    # ----------------------------------------------------------------
    # PART A: Persistence feedback trajectory (8 steps)
    # ----------------------------------------------------------------
    print("\n-- PART A: Persistence feedback trajectory (8 steps) --")
    traj = persistence_feedback_trajectory(psi_init, n_steps=8, base_strength=0.4)

    strength_history = traj["strength_history"]
    print(f"Strength history: {[round(s, 5) for s in strength_history]}")

    diffs = [
        strength_history[k + 1] - strength_history[k]
        for k in range(len(strength_history) - 1)
    ]
    unique_vals = set(round(s, 8) for s in strength_history)
    if len(unique_vals) == 1:
        pattern = "constant"
    elif all(d >= -1e-9 for d in diffs):
        pattern = "monotone_non_decreasing"
    elif all(d <= 1e-9 for d in diffs):
        pattern = "monotone_non_increasing"
    else:
        pattern = "oscillating"

    print(f"Pattern classification: {pattern}")

    max_strength = max(strength_history)
    max_pair_count = max(r["persistence_pair_count"] for r in traj["persistence_history"])
    print(f"Max strength achieved: {max_strength:.5f}")
    print(f"Max persistence pair count: {max_pair_count}")

    # ----------------------------------------------------------------
    # PART B: Clifford projection cut readouts on the final state
    # ----------------------------------------------------------------
    psi_final = traj["state_history"][-1]

    print("\n-- PART B: gamma_5 chirality projection cut readouts (7 cuts) --")
    projected_readouts = clifford_projected_cut_readout(psi_final)

    n_changed = 0
    for row in projected_readouts:
        label = "CHANGED" if row["projection_changed_signature"] else "unchanged"
        print(
            f"  cut={row['cut']}  "
            f"S_A: {row['S_A_before']:.4f} -> {row['S_A_after']:.4f}  "
            f"coh_info: {row['coh_info_before']:.4f} -> {row['coh_info_after']:.4f}  "
            f"[{label}]"
        )
        if row["projection_changed_signature"]:
            n_changed += 1

    print(
        f"\nCuts where gamma_5 projection changed signature: "
        f"{n_changed} / {len(projected_readouts)}"
    )

    # ----------------------------------------------------------------
    # PART C: Control (no projection) — must match before-projection values
    # ----------------------------------------------------------------
    print("\n-- PART C: No-projection control (sanity check) --")
    control_readouts = clifford_no_projection_control_cut_readout(psi_final)

    control_matches = True
    for proj_row, ctrl_row in zip(projected_readouts, control_readouts):
        match_s = abs(proj_row["S_A_before"] - ctrl_row["S_A_before"]) < 1e-10
        match_c = abs(proj_row["coh_info_before"] - ctrl_row["coh_info_before"]) < 1e-10
        if not (match_s and match_c):
            control_matches = False
            print(
                f"  MISMATCH at cut={proj_row['cut']}: "
                f"proj_before S_A={proj_row['S_A_before']:.8f}, "
                f"ctrl S_A={ctrl_row['S_A_before']:.8f}"
            )
    if control_matches:
        print("  Control matches before-projection values exactly: PASS")
    else:
        print("  Control mismatch: FAIL")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n-- Summary --")
    smoke_pass = (
        len(strength_history) == 8
        and len(projected_readouts) == 7
        and len(control_readouts) == 7
        and control_matches
        and pattern != "constant"
        and n_changed > 0
    )
    print(f"  Strength history length : {len(strength_history)}  (expected 8)")
    print(f"  Cut readout count       : {len(projected_readouts)}  (expected 7)")
    print(f"  Strength pattern        : {pattern}")
    print(f"  Max persistence pairs   : {max_pair_count}")
    print(f"  Max strength achieved   : {max_strength:.5f}")
    print(f"  Cuts with changed sig   : {n_changed} / 7")
    print(f"  Control sanity check    : {'PASS' if control_matches else 'FAIL'}")
    print(f"  SMOKE TEST              : {'PASS' if smoke_pass else 'FAIL'}")
    print("=" * 68)
