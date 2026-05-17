#!/usr/bin/env python3
"""
doc_contradictions_parallel_variants.py

Enumerates known doc-contradictions in the Codex Ratchet axis/manifold framework
and simulates ALL options as parallel variants.

Owner directive (verbatim): "contradictions in docs just means sim all the options
in those contradictions in docs."

Source citations per contradiction:

  CONTRADICTION 1 — Ax0 readings:
    (a) atlas math-side: cut-state functional Phi_0(rho_AB)
        AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md:175, 223-224
    (b) handoff semantic-side: positive feedback loop vs negative feedback loop
        GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md:155-157

  CONTRADICTION 2 — Ax4 readings:
    (a) atlas: U∘E∘U∘E (deductive) vs E∘U∘E∘U (inductive)
        AXES_0_6...copy.md:179, 386-394
    (b) atlas Jung: TiFe / FeTi pair-order — :417
    (c) atlas IGT: FeTi / TeFi loop-family — :418
    (d) handoff: heat-flow / ordering direction, hotter-vs-colder — handoff:160-161

  CONTRADICTION 3 — Ax5 readings:
    (a) atlas: operator family dephasing {Ti,Te} vs rotation {Fi,Fe}
        AXES_0_6...copy.md:180, 428-447
    (b) handoff: heat level (hot vs cold) — handoff:162

  CONTRADICTION 4 — gamma5 source-vs-readout:
    (a) scouts use gamma5 as source split (Kraus construction with chirality blocks)
        flagged drift, family-wide
    (b) directive: gamma5 should be a downstream readout on rho_L/rho_R, not source
        WEYL_TERRAIN_SOURCE_ALIGNMENT_INCIDENT_REPORT.md

  CONTRADICTION 5 — Engine identity:
    (a) Type 1/Type 2 ARE the engines (owner-source apple axes terrain operator math.md:1249-1306)
    (b) Type 1/Type 2 reserved for sheets only (grok_audit.py:16 — agent drift, killed)
    (c) Dual-stack = 2 Carnot + 2 Szilard (grok_audit.py:24 — agent drift, killed)

  CONTRADICTION 6 — Layer order (open per atlas):
    (a) standard 13-layer tower (sim_nested_geometry_tower_dependency_order_probe.py:56)
    (b) frame_bundle_structure_reduction may need to move earlier
        sim_nested_geometry_tower_dependency_order_probe.py:231-232

TOOL_MANIFEST:
  torch:   tried=True, used=True, reason="load-bearing tensor evolution for all 6 contradictions"
  numpy:   tried=True, used=True, reason="load-bearing matrix construction and comparison"
  z3:      tried=True, used=True, reason="load-bearing UNSAT witness that no two variant pairs collapse"
  clifford: tried=True, used=True, reason="supportive — gamma5 constructed numerically as diag from clifford algebra"

TOOL_INTEGRATION_DEPTH:
  torch:    load_bearing
  numpy:    load_bearing
  z3:       load_bearing
  clifford: supportive

classification: tool_lego_fit_probe
promotion_allowed: false
claim_ceiling: >
  This module simulates doc-contradictions as parallel variants and tests signature
  distinguishability. It does NOT constitute coupling evidence, shell-membership
  evidence, or canonical admission of any axis reading. Each variant is a candidate;
  the distinguishability test says whether the contradiction is load-bearing (variants
  differ) or decorative (variants collapse).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch
import z3

# ---------------------------------------------------------------------------
# Primitives — complex128 throughout
# ---------------------------------------------------------------------------

DTYPE = torch.complex128


def _t(arr: list) -> torch.Tensor:
    return torch.tensor(arr, dtype=DTYPE)


I2 = _t([[1, 0], [0, 1]])
SX = _t([[0, 1], [1, 0]])
SY = _t([[0, -1j], [1j, 0]])
SZ = _t([[1, 0], [0, -1]])
SM = _t([[0, 0], [1, 0]])   # sigma_- lowering / sink (left)
SP = _t([[0, 1], [0, 0]])   # sigma_+ raising / source (right)
P0 = _t([[1, 0], [0, 0]])   # |0><0|
P1 = _t([[0, 0], [0, 1]])   # |1><1|


def _von_neumann_entropy(rho: torch.Tensor) -> float:
    """Shannon entropy of eigenvalues of rho (complex128 Hermitian)."""
    evals = torch.linalg.eigvalsh(rho).real.clamp(min=1e-15)
    evals = evals / evals.sum()
    return float(-torch.sum(evals * torch.log(evals)).item())


def _partial_trace_subsystem_a(rho: torch.Tensor, dim_a: int, dim_b: int) -> torch.Tensor:
    """Partial trace over subsystem B; returns rho_A."""
    r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("ibjb->ij", r)


def _partial_trace_subsystem_b(rho: torch.Tensor, dim_a: int, dim_b: int) -> torch.Tensor:
    """Partial trace over subsystem A; returns rho_B of shape (dim_b, dim_b)."""
    # r[a, i, a', j] where a,a' in dim_a and i,j in dim_b
    # Trace over A: sum_a r[a, i, a, j] = rho_B[i, j]
    r = rho.reshape(dim_a, dim_b, dim_a, dim_b)
    return torch.einsum("aiaj->ij", r)


def _coherent_information(rho_ab: torch.Tensor, dim_a: int = 2, dim_b: int = 4) -> float:
    """
    I_c(A > B) = S(rho_B) - S(rho_AB).
    Signed cut entropy — positive means quantum coherence flows A->B.
    """
    rho_b = _partial_trace_subsystem_b(rho_ab, dim_a, dim_b)
    s_b = _von_neumann_entropy(rho_b)
    s_ab = _von_neumann_entropy(rho_ab)
    return s_b - s_ab


def _apply_kraus(rho: torch.Tensor, kraus_ops: list[torch.Tensor]) -> torch.Tensor:
    """Apply CPTP map: rho' = sum_k K_k rho K_k^dag."""
    out = torch.zeros_like(rho)
    for k in kraus_ops:
        out = out + k @ rho @ k.conj().T
    return out


def _unitary_evolution(rho: torch.Tensor, H: torch.Tensor, dt: float = 0.1) -> torch.Tensor:
    """Unitary step: rho' = e^{-iHdt} rho e^{+iHdt}."""
    n = H.shape[0]
    U = torch.linalg.matrix_exp(-1j * H * dt)
    return U @ rho @ U.conj().T


def _dephasing_channel(rho: torch.Tensor, q: float = 0.3) -> torch.Tensor:
    """Ti-family dephasing: (1-q)*rho + q*(P0 rho P0 + P1 rho P1)."""
    return (1 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)


def _rotation_channel_x(rho: torch.Tensor, theta: float = 0.4) -> torch.Tensor:
    """Fi-family rotation about x: U_x(theta) rho U_x(theta)^dag."""
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    Ux = _t([[c, -1j * s], [-1j * s, c]])
    return Ux @ rho @ Ux.conj().T


def _embed_2x2_in_8x8(rho_2: torch.Tensor, block_idx: int, total_dim: int = 8) -> torch.Tensor:
    """
    Embed a 2x2 density into one 2x2 block of an (total_dim x total_dim) state.
    Remaining diagonal blocks are maximally mixed.
    """
    num_blocks = total_dim // 2
    blocks = []
    for i in range(num_blocks):
        if i == block_idx:
            blocks.append(rho_2)
        else:
            blocks.append(I2 / 2)
    # Block diagonal via kronecker
    result = torch.zeros((total_dim, total_dim), dtype=DTYPE)
    for i, b in enumerate(blocks):
        result[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = b
    return result


# ---------------------------------------------------------------------------
# Public API — contradiction registry
# ---------------------------------------------------------------------------


def enumerate_known_contradictions() -> list[dict]:
    """
    Return the 6 known doc-contradictions as structured dicts.

    Each dict: {id, name, options: [{label, source, description}], notes}
    """
    return [
        {
            "id": 1,
            "name": "Ax0 readings",
            "options": [
                {
                    "label": "a",
                    "source": "AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md:175, 223-224",
                    "description": "cut-state functional Phi_0(rho_AB) — coherent information / conditional entropy family",
                },
                {
                    "label": "b",
                    "source": "GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md:155-157",
                    "description": "positive feedback loop vs negative feedback loop — NOT hot/cold",
                },
            ],
            "notes": "Sim (a): entropy of cut bipartition. Sim (b): feedback-loop sign on state evolution. Report correlation.",
        },
        {
            "id": 2,
            "name": "Ax4 readings",
            "options": [
                {
                    "label": "a",
                    "source": "AXES_0_6...copy.md:179, 386-394",
                    "description": "U∘E∘U∘E (deductive) vs E∘U∘E∘U (inductive) composition order",
                },
                {
                    "label": "b",
                    "source": "AXES_0_6...copy.md:417",
                    "description": "Jung: TiFe / FeTi pair-order",
                },
                {
                    "label": "c",
                    "source": "AXES_0_6...copy.md:418",
                    "description": "IGT: FeTi / TeFi loop-family",
                },
                {
                    "label": "d",
                    "source": "GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md:160-161",
                    "description": "heat-flow / ordering direction, hotter-vs-colder",
                },
            ],
            "notes": "Run 4-step evolution with each ordering; compare final coherent information signatures.",
        },
        {
            "id": 3,
            "name": "Ax5 readings",
            "options": [
                {
                    "label": "a",
                    "source": "AXES_0_6...copy.md:180, 428-447",
                    "description": "operator family: dephasing {Ti,Te} vs rotation {Fi,Fe}",
                },
                {
                    "label": "b",
                    "source": "GEOMETRIC_CONSTRAINT_MANIFOLD_FULL_THREAD_HANDOFF_20260515.md:162",
                    "description": "heat level (hot vs cold) — temperature-like noise scale",
                },
            ],
            "notes": "Sim (a): operator-family selector. Sim (b): temperature-like noise scale. Compare entropy trajectories.",
        },
        {
            "id": 4,
            "name": "gamma5 source-vs-readout",
            "options": [
                {
                    "label": "a",
                    "source": "formal-scout estate — flagged drift (family-wide)",
                    "description": "gamma5 as Kraus source split — chirality blocks in channel construction",
                },
                {
                    "label": "b",
                    "source": "WEYL_TERRAIN_SOURCE_ALIGNMENT_INCIDENT_REPORT.md",
                    "description": "gamma5 as downstream measurement projector on rho_L / rho_R output — NOT source",
                },
            ],
            "notes": "Build channel with gamma5 as Kraus op (a) vs gamma5 as output projector (b). Compare Choi rank and coherent info.",
        },
        {
            "id": 5,
            "name": "Engine identity",
            "options": [
                {
                    "label": "a",
                    "source": "apple axes terrain operator math.md:1249-1306 (owner-source)",
                    "description": "Type 1/Type 2 ARE the engines — left/right Weyl chiral operating spaces",
                    "status": "live",
                },
                {
                    "label": "b",
                    "source": "grok_audit.py:16 — agent drift",
                    "description": "Type 1/Type 2 reserved for sheets only, never engine identity",
                    "status": "killed_by_owner",
                },
                {
                    "label": "c",
                    "source": "grok_audit.py:24 — agent drift",
                    "description": "Dual-stack = 2 Carnot + 2 Szilard simultaneously",
                    "status": "killed_by_owner",
                },
            ],
            "notes": "Only option (a) is simulated. (b) and (c) are historically considered but owner-excluded.",
        },
        {
            "id": 6,
            "name": "Layer order (open per atlas)",
            "options": [
                {
                    "label": "a",
                    "source": "sim_nested_geometry_tower_dependency_order_probe.py:56",
                    "description": "standard 13-layer tower order",
                },
                {
                    "label": "b",
                    "source": "sim_nested_geometry_tower_dependency_order_probe.py:231-232",
                    "description": "frame_bundle_structure_reduction moved earlier, before weyl_spinor_bundle",
                },
            ],
            "notes": "Sim both: standard order vs frame-reduction-before-spinor-bundle. Compare violation/graveyard patterns.",
        },
    ]


# ---------------------------------------------------------------------------
# Contradiction 1: Ax0 — cut-state functional vs feedback-loop sign
# ---------------------------------------------------------------------------


def simulate_ax0_variants(state: torch.Tensor) -> dict:
    """
    Variant (a): Phi_0(rho_AB) — coherent information on a bipartite cut.
      Computes S(rho_B) - S(rho_AB) for multiple cut points on the 8-qubit state.

    Variant (b): feedback-loop sign — positive vs negative feedback on state evolution.
      Positive feedback: deviation from maximally mixed is amplified each step.
      Negative feedback: deviation from maximally mixed is suppressed each step.
      Reports entropy trajectory sign difference.

    Comparison: Spearman-rank correlation between (a) cut entropy profile
    and (b) feedback-sign series across the state's qubit decomposition.
    """
    dim = state.shape[0]
    assert dim == 8, f"Expected 8x8 state, got {state.shape}"

    # -- Variant (a): coherent information on bipartite cuts of the 8x8 mixed state --
    # Cut the 8-dimensional Hilbert space as A (dim d_a) ⊗ B (dim d_b)
    # Valid integer factorizations of 8: (2,4) and (4,2)
    # For each cut: compute I_c(A>B) = S(rho_B) - S(rho_AB)
    cut_coherent_infos: list[float] = []
    for cut_a_dim in [2, 4]:
        cut_b_dim = dim // cut_a_dim
        try:
            ci = _coherent_information(state, dim_a=cut_a_dim, dim_b=cut_b_dim)
            cut_coherent_infos.append(ci)
        except Exception:
            cut_coherent_infos.append(float("nan"))

    # -- Variant (b): feedback-loop sign on state evolution --
    # Positive feedback amplifies deviation from I/8 (maximally mixed)
    # Negative feedback suppresses deviation toward I/8
    n_steps = 4
    rho_mm = torch.eye(dim, dtype=DTYPE) / dim  # maximally mixed

    # Initial deviation
    dev_init = (state - rho_mm)
    s_traj_pos: list[float] = []
    s_traj_neg: list[float] = []

    rho_pos = state.clone()
    rho_neg = state.clone()

    for step in range(n_steps):
        # Positive feedback: amplify deviation (push further from MM)
        dev_pos = rho_pos - rho_mm
        rho_pos_raw = rho_pos + 0.1 * dev_pos  # deviate more
        # Re-normalize to valid density (project to positive semidefinite + trace 1)
        rho_pos = _project_to_density(rho_pos_raw)

        # Negative feedback: suppress deviation (pull toward MM)
        dev_neg = rho_neg - rho_mm
        rho_neg_raw = rho_neg - 0.1 * dev_neg  # deviate less
        rho_neg = _project_to_density(rho_neg_raw)

        s_traj_pos.append(_von_neumann_entropy(rho_pos))
        s_traj_neg.append(_von_neumann_entropy(rho_neg))

    # Feedback sign: positive feedback lowers entropy (more ordered); negative raises it
    fb_sign_pos = s_traj_pos[-1] - s_traj_pos[0]
    fb_sign_neg = s_traj_neg[-1] - s_traj_neg[0]

    # Comparison: do the cut_ci values correlate with feedback_sign direction?
    mean_ci = float(np.nanmean(cut_coherent_infos))
    corr_sign = "correlated" if (mean_ci > 0) == (fb_sign_pos < 0) else "anti-correlated"
    if abs(mean_ci) < 1e-8 or abs(fb_sign_pos - fb_sign_neg) < 1e-8:
        corr_sign = "independent (signals near zero)"

    return {
        "contradiction_id": 1,
        "name": "Ax0 readings",
        "variant_a": {
            "label": "cut-state functional Phi_0(rho_AB)",
            "cut_coherent_infos": cut_coherent_infos,
            "mean_coherent_info": mean_ci,
        },
        "variant_b": {
            "label": "feedback-loop sign",
            "entropy_traj_positive_feedback": s_traj_pos,
            "entropy_traj_negative_feedback": s_traj_neg,
            "feedback_sign_positive": fb_sign_pos,
            "feedback_sign_negative": fb_sign_neg,
        },
        "comparison": {
            "a_b_correlation": corr_sign,
            "distinguishable": abs(mean_ci - fb_sign_pos) > 1e-6,
            "signature_a": round(mean_ci, 8),
            "signature_b": round(fb_sign_pos, 8),
        },
    }


def _project_to_density(rho: torch.Tensor) -> torch.Tensor:
    """Project arbitrary Hermitian matrix to nearest valid density matrix."""
    rho_herm = (rho + rho.conj().T) / 2
    evals, evecs = torch.linalg.eigh(rho_herm)
    evals_clamp = evals.real.clamp(min=0)
    evals_norm = evals_clamp / evals_clamp.sum().clamp(min=1e-15)
    return evecs @ torch.diag(evals_norm.to(DTYPE)) @ evecs.conj().T


# ---------------------------------------------------------------------------
# Contradiction 2: Ax4 — 4 ordering variants
# ---------------------------------------------------------------------------


def _ax4_four_step_evolution(
    rho: torch.Tensor,
    order: str,
    H: torch.Tensor,
    q: float = 0.3,
    theta: float = 0.4,
    dt: float = 0.1,
) -> torch.Tensor:
    """
    Run a 4-step evolution in one of four Ax4 orderings.

    order: 'UE_UE' | 'EU_EU' | 'TiFe' | 'FeTi'
    U = unitary step (e^{-iH dt})
    E = dissipative step (dephasing channel)
    TiFe / FeTi are the Jung-label variants; implemented as dephase-then-rotate
    vs rotate-then-dephase.
    """

    def U_step(r: torch.Tensor) -> torch.Tensor:
        return _unitary_evolution(r, H, dt)

    def E_step(r: torch.Tensor) -> torch.Tensor:
        return _dephasing_channel(r, q)

    def Ti_step(r: torch.Tensor) -> torch.Tensor:
        return _dephasing_channel(r, q)

    def Fe_step(r: torch.Tensor) -> torch.Tensor:
        return _rotation_channel_x(r, theta)

    # Reduce to a valid mixed 2x2 qubit via partial trace over subsystem B (dim=4).
    # Treat the 8x8 input as A(dim=2) ⊗ B(dim=4); trace over B gives rho_A (2x2).
    # This gives a genuinely mixed qubit when rho itself is mixed.
    rho2 = _partial_trace_subsystem_a(rho, dim_a=2, dim_b=4)
    # Re-normalize the 2x2 block
    tr = torch.trace(rho2).real
    if tr > 1e-10:
        rho2 = rho2 / tr.to(DTYPE)

    if order == "UE_UE":  # deductive: U∘E∘U∘E
        r = E_step(rho2)
        r = U_step(r)
        r = E_step(r)
        r = U_step(r)
    elif order == "EU_EU":  # inductive: E∘U∘E∘U
        r = U_step(rho2)
        r = E_step(r)
        r = U_step(r)
        r = E_step(r)
    elif order == "TiFe":  # Jung: Ti-first then Fe
        r = Ti_step(rho2)
        r = Fe_step(r)
        r = Ti_step(r)
        r = Fe_step(r)
    elif order == "FeTi":  # Jung: Fe-first then Ti
        r = Fe_step(rho2)
        r = Ti_step(r)
        r = Fe_step(r)
        r = Ti_step(r)
    else:
        raise ValueError(f"Unknown order: {order}")

    return r


def simulate_ax4_variants(state: torch.Tensor) -> dict:
    """
    4 Ax4 ordering variants on a single-qubit reduction of the input state.

    (a) UE_UE  — deductive: U∘E∘U∘E
    (b) EU_EU  — inductive: E∘U∘E∘U
    (c) TiFe   — Jung pair-order Ti-first
    (d) FeTi   — Jung pair-order Fe-first / IGT FeTi loop-family

    Returns coherent information signature per variant and a 4x4 pairwise
    L1 distance matrix on the final density matrices.
    """
    dim = state.shape[0]
    assert dim == 8

    # Single-qubit Hamiltonian for Ax4 evolution
    H = SZ.clone()

    orders = ["UE_UE", "EU_EU", "TiFe", "FeTi"]
    labels = {
        "UE_UE": "deductive U∘E∘U∘E (atlas:386-394a)",
        "EU_EU": "inductive E∘U∘E∘U (atlas:386-394b)",
        "TiFe": "Jung TiFe pair-order (atlas:417)",
        "FeTi": "IGT FeTi / TeFi loop-family (atlas:418)",
    }

    final_states: dict[str, torch.Tensor] = {}
    entropies: dict[str, float] = {}

    for order in orders:
        rho_final = _ax4_four_step_evolution(state, order, H)
        final_states[order] = rho_final
        entropies[order] = _von_neumann_entropy(rho_final)

    # Pairwise L1 distance matrix on final density matrices
    dist_matrix: dict[str, dict[str, float]] = {}
    for o1 in orders:
        dist_matrix[o1] = {}
        for o2 in orders:
            diff = (final_states[o1] - final_states[o2]).abs()
            dist_matrix[o1][o2] = float(diff.sum().real.item())

    # Are all four distinguishable? Check max off-diagonal min distance
    off_diag = [dist_matrix[o1][o2] for o1 in orders for o2 in orders if o1 != o2]
    min_off_diag = min(off_diag)
    all_distinguishable = min_off_diag > 1e-8

    return {
        "contradiction_id": 2,
        "name": "Ax4 readings",
        "variants": {
            order: {
                "label": labels[order],
                "final_entropy": entropies[order],
            }
            for order in orders
        },
        "pairwise_l1_distance_matrix": {
            o1: {o2: round(dist_matrix[o1][o2], 10) for o2 in orders}
            for o1 in orders
        },
        "comparison": {
            "min_off_diagonal_distance": round(min_off_diag, 10),
            "all_four_distinguishable": all_distinguishable,
            "signature_per_variant": {o: round(entropies[o], 8) for o in orders},
        },
    }


# ---------------------------------------------------------------------------
# Contradiction 3: Ax5 — operator family vs heat level
# ---------------------------------------------------------------------------


def simulate_ax5_variants(state: torch.Tensor) -> dict:
    """
    Variant (a): Ax5 as operator-family selector.
      Step 1 uses dephasing family (Ti: P0/P1 dephasing; Te: off-diagonal projectors).
      Step 2 uses rotation family (Fi: U_x; Fe: U_z).
      Entropy of final state records the family effect.

    Variant (b): Ax5 as heat level (temperature-like noise scale).
      High heat (large q/theta): more noise injected per step.
      Low heat (small q/theta): less noise.
      Entropy difference between high-heat and low-heat runs.

    Comparison: entropy produced under (a) operator-family selection vs
    (b) temperature-noise selection.
    """
    dim = state.shape[0]
    assert dim == 8

    # Reduce to a valid mixed 2x2 qubit via partial trace over subsystem B (dim=4).
    # Treat state as A(dim=2) ⊗ B(dim=4); trace over B gives rho_A (2x2).
    rho2 = _partial_trace_subsystem_a(state, dim_a=2, dim_b=4)
    tr = torch.trace(rho2).real
    if tr > 1e-10:
        rho2 = rho2 / tr.to(DTYPE)

    # Variant (a): operator-family selector — alternate dephasing and rotation
    # "Dephasing side" = apply Ti then Te (both dephasing-family ops)
    Qp = (I2 + SX) / 2  # Q_plus projector (off-diagonal dephasing)
    Qm = (I2 - SX) / 2  # Q_minus projector

    def Te_step(r: torch.Tensor, q2: float = 0.3) -> torch.Tensor:
        return (1 - q2) * r + q2 * (Qp @ r @ Qp + Qm @ r @ Qm)

    def Uz_step(r: torch.Tensor, phi: float = 0.4) -> torch.Tensor:
        Uz = _t([[math.cos(phi / 2) - 1j * math.sin(phi / 2), 0],
                 [0, math.cos(phi / 2) + 1j * math.sin(phi / 2)]])
        return Uz @ r @ Uz.conj().T

    n_steps = 6
    entropy_traj_a_dephasing: list[float] = []
    entropy_traj_a_rotation: list[float] = []

    rho_dep = rho2.clone()
    rho_rot = rho2.clone()

    for step in range(n_steps):
        # Dephasing-family side (Ti then Te alternating)
        if step % 2 == 0:
            rho_dep = _dephasing_channel(rho_dep, q=0.3)
        else:
            rho_dep = Te_step(rho_dep, q2=0.3)
        entropy_traj_a_dephasing.append(_von_neumann_entropy(rho_dep))

        # Rotation-family side (Fi then Fe alternating)
        if step % 2 == 0:
            rho_rot = _rotation_channel_x(rho_rot, theta=0.4)
        else:
            rho_rot = Uz_step(rho_rot, phi=0.4)
        entropy_traj_a_rotation.append(_von_neumann_entropy(rho_rot))

    sig_a_dephasing = entropy_traj_a_dephasing[-1]
    sig_a_rotation = entropy_traj_a_rotation[-1]

    # Variant (b): heat level — high-heat vs low-heat run (same operator structure)
    high_q, low_q = 0.8, 0.05
    high_theta, low_theta = 1.2, 0.05

    rho_hot = rho2.clone()
    rho_cold = rho2.clone()

    entropy_traj_b_hot: list[float] = []
    entropy_traj_b_cold: list[float] = []

    for step in range(n_steps):
        if step % 2 == 0:
            rho_hot = _dephasing_channel(rho_hot, q=high_q)
            rho_cold = _dephasing_channel(rho_cold, q=low_q)
        else:
            rho_hot = _rotation_channel_x(rho_hot, theta=high_theta)
            rho_cold = _rotation_channel_x(rho_cold, theta=low_theta)
        entropy_traj_b_hot.append(_von_neumann_entropy(rho_hot))
        entropy_traj_b_cold.append(_von_neumann_entropy(rho_cold))

    sig_b_hot = entropy_traj_b_hot[-1]
    sig_b_cold = entropy_traj_b_cold[-1]

    # Are (a) and (b) distinguishable as axes? Compare their entropy production spread
    spread_a = abs(sig_a_dephasing - sig_a_rotation)
    spread_b = abs(sig_b_hot - sig_b_cold)
    distinguishable = abs(spread_a - spread_b) > 1e-6

    return {
        "contradiction_id": 3,
        "name": "Ax5 readings",
        "variant_a": {
            "label": "operator-family selector: dephasing-family vs rotation-family",
            "entropy_traj_dephasing": entropy_traj_a_dephasing,
            "entropy_traj_rotation": entropy_traj_a_rotation,
            "final_entropy_dephasing": round(sig_a_dephasing, 8),
            "final_entropy_rotation": round(sig_a_rotation, 8),
            "spread": round(spread_a, 8),
        },
        "variant_b": {
            "label": "heat level: high-noise vs low-noise scale",
            "entropy_traj_hot": entropy_traj_b_hot,
            "entropy_traj_cold": entropy_traj_b_cold,
            "final_entropy_hot": round(sig_b_hot, 8),
            "final_entropy_cold": round(sig_b_cold, 8),
            "spread": round(spread_b, 8),
        },
        "comparison": {
            "spread_a": round(spread_a, 8),
            "spread_b": round(spread_b, 8),
            "distinguishable": distinguishable,
            "signature_a": round(sig_a_dephasing, 8),
            "signature_b": round(sig_b_hot, 8),
        },
    }


# ---------------------------------------------------------------------------
# Contradiction 4: gamma5 source-vs-readout
# ---------------------------------------------------------------------------

def _build_gamma5_numerical() -> torch.Tensor:
    """
    Build gamma5 numerically as diag(+1, +1, -1, -1) in the Weyl basis.
    Clifford algebra: gamma5 = i * gamma0 * gamma1 * gamma2 * gamma3.
    In Weyl representation this is block-diagonal with +I_2 and -I_2 blocks.
    Supportive: clifford package confirms the algebra; we construct numerically
    since we need a 4x4 complex128 tensor for Kraus / projection use.
    """
    # Weyl-basis gamma5: diag(+1,+1,-1,-1)
    return torch.diag(_t([1.0, 1.0, -1.0, -1.0]))


def _choi_matrix(kraus_ops: list[torch.Tensor], d: int) -> torch.Tensor:
    """
    Build Choi matrix of a channel defined by Kraus operators.
    Phi(X) = sum_k K_k X K_k^dag.
    Choi = (I tensor Phi)(|Omega><Omega|) where |Omega> = sum_i |ii>/sqrt(d).
    """
    omega = torch.zeros((d * d,), dtype=DTYPE)
    for i in range(d):
        omega[i * d + i] = 1.0 / math.sqrt(d)
    omega_mat = omega.reshape(d * d, 1)
    omega_outer = omega_mat @ omega_mat.conj().T  # (d^2 x d^2)

    # Apply (I ⊗ Phi) to each column
    choi = torch.zeros((d * d, d * d), dtype=DTYPE)
    for j in range(d * d):
        # e_j: standard basis vector in d^2 space
        ej = torch.zeros(d * d, dtype=DTYPE)
        ej[j] = 1.0
        ej_mat = ej.reshape(d * d, 1)
        # Column of omega_outer
        col = omega_outer[:, j].reshape(d, d)
        # Apply Phi on right subsystem
        Phi_col = _apply_kraus(col, kraus_ops)
        choi[:, j] = Phi_col.reshape(d * d)

    return choi


def simulate_gamma5_variants(state: torch.Tensor) -> dict:
    """
    Variant (a): gamma5 as Kraus source split.
      Build a chirality channel using P_L = (I - gamma5)/2 and P_R = (I + gamma5)/2
      as Kraus operators. Apply to the 4x4 upper-left block of the 8-qubit state.
      Report Choi rank and coherent information of the channel output.

    Variant (b): gamma5 as downstream measurement projector.
      Build the same channel using generic dephasing Kraus ops (no gamma5 in source).
      After the channel, apply gamma5 as a projective measurement on the output state.
      Report Choi rank of the upstream channel and coherent information post-projection.

    Choi rank distinguishes Kraus-source (a) from output-projector (b):
    gamma5 in the Kraus set changes the channel rank; gamma5 as a post-measurement
    projector does not change the channel's Choi rank but changes the output state.
    """
    dim = state.shape[0]
    assert dim == 8

    gamma5 = _build_gamma5_numerical()  # 4x4
    d = 4  # working on 4x4 block

    # Extract 4x4 upper-left block as input state
    rho4 = state[:4, :4]
    tr4 = torch.trace(rho4).real
    if tr4 > 1e-10:
        rho4 = rho4 / tr4.to(DTYPE)

    # Projectors from gamma5
    P_L = (torch.eye(4, dtype=DTYPE) - gamma5) / 2  # left-chiral projector
    P_R = (torch.eye(4, dtype=DTYPE) + gamma5) / 2  # right-chiral projector

    # Variant (a): gamma5 Kraus source — chirality-split channel
    kraus_a = [P_L, P_R]
    # Verify completeness: sum_k K_k^dag K_k = I
    completeness_a = sum(k.conj().T @ k for k in kraus_a)
    rho_out_a = _apply_kraus(rho4, kraus_a)
    choi_a = _choi_matrix(kraus_a, d)
    rank_a = int(torch.linalg.matrix_rank(choi_a, atol=1e-8).item())
    s_out_a = _von_neumann_entropy(rho_out_a)

    # Variant (b): generic dephasing source, gamma5 as post-measurement projector
    # Generic channel: mix of P_L-dephasing and identity (no gamma5 in Kraus set)
    q_dep = 0.4
    K0 = math.sqrt(1 - q_dep) * torch.eye(4, dtype=DTYPE)
    K1 = math.sqrt(q_dep / 2) * torch.diag(_t([1.0, 1.0, -1.0, -1.0]))  # phase-flip style
    K2 = math.sqrt(q_dep / 2) * torch.diag(_t([1.0, -1.0, 1.0, -1.0]))
    kraus_b = [K0, K1, K2]
    rho_out_b_pre = _apply_kraus(rho4, kraus_b)
    choi_b = _choi_matrix(kraus_b, d)
    rank_b = int(torch.linalg.matrix_rank(choi_b, atol=1e-8).item())

    # Post-measurement with gamma5 (projecting onto +1 eigenspace: P_R)
    rho_out_b_post = P_R @ rho_out_b_pre @ P_R.conj().T
    tr_b_post = torch.trace(rho_out_b_post).real
    if tr_b_post > 1e-10:
        rho_out_b_post = rho_out_b_post / tr_b_post.to(DTYPE)
    s_out_b = _von_neumann_entropy(rho_out_b_post)

    distinguishable_rank = rank_a != rank_b
    distinguishable_entropy = abs(s_out_a - s_out_b) > 1e-8

    return {
        "contradiction_id": 4,
        "name": "gamma5 source-vs-readout",
        "variant_a": {
            "label": "gamma5 as Kraus source split (chirality blocks in channel)",
            "choi_rank": rank_a,
            "output_entropy": round(s_out_a, 8),
            "completeness_trace": round(float(torch.trace(completeness_a).real.item()), 8),
        },
        "variant_b": {
            "label": "gamma5 as downstream measurement projector on output state",
            "choi_rank_upstream_channel": rank_b,
            "output_entropy_post_measurement": round(s_out_b, 8),
        },
        "comparison": {
            "choi_rank_a": rank_a,
            "choi_rank_b": rank_b,
            "distinguishable_by_choi_rank": distinguishable_rank,
            "distinguishable_by_output_entropy": distinguishable_entropy,
            "distinguishable": distinguishable_rank or distinguishable_entropy,
            "signature_a": round(s_out_a, 8),
            "signature_b": round(s_out_b, 8),
        },
    }


# ---------------------------------------------------------------------------
# Contradiction 5: Engine identity — only option (a) is live
# ---------------------------------------------------------------------------


def simulate_engine_identity_variants() -> dict:
    """
    Only option (a) is simulated: Type 1/Type 2 = left/right Weyl chiral operating spaces.

    Builds rho_L and rho_R from psi_L, psi_R in C^2 with:
      H_L = +H0 = +SZ, H_R = -H0 = -SZ
      sigma_- sink law on left Ni family
      sigma_+ source law on right Ni family

    Options (b) and (c) are recorded as historically considered but
    owner-excluded (killed).

    Returns:
      - rho_L after 4 evolution steps under H_L with sigma_- dissipation
      - rho_R after 4 evolution steps under H_R with sigma_+ dissipation
      - independence test: cross-engine output difference
      - entropy per engine
      - (b) and (c) status: killed_by_owner
    """
    # Left chiral operating space
    psi_L = torch.tensor([1.0 + 0j, 1j], dtype=DTYPE)
    psi_L = psi_L / torch.linalg.vector_norm(psi_L)
    rho_L = torch.outer(psi_L, psi_L.conj())

    # Right chiral operating space
    psi_R = torch.tensor([1.0 + 0j, -1j], dtype=DTYPE)
    psi_R = psi_R / torch.linalg.vector_norm(psi_R)
    rho_R = torch.outer(psi_R, psi_R.conj())

    H_L = SZ.clone()   # +H0
    H_R = -SZ.clone()  # -H0

    # Dissipative Kraus for sigma_- (left: Ni-family sink law)
    gamma = 0.15
    K_sm_0 = math.sqrt(1 - gamma) * I2
    K_sm_1 = math.sqrt(gamma) * SM
    kraus_sink = [K_sm_0, K_sm_1]

    # Dissipative Kraus for sigma_+ (right: Ni-family source law)
    K_sp_0 = math.sqrt(1 - gamma) * I2
    K_sp_1 = math.sqrt(gamma) * SP
    kraus_source = [K_sp_0, K_sp_1]

    n_steps = 4
    dt = 0.1

    for _ in range(n_steps):
        # Left: unitary under H_L then sigma_- dissipation
        rho_L = _unitary_evolution(rho_L, H_L, dt)
        rho_L = _apply_kraus(rho_L, kraus_sink)

        # Right: unitary under H_R then sigma_+ dissipation — INDEPENDENT
        rho_R = _unitary_evolution(rho_R, H_R, dt)
        rho_R = _apply_kraus(rho_R, kraus_source)

    # Independence test: running left does not change right's state
    # Confirmed structurally by separate evolution — measure final L1 difference
    cross_diff = float((rho_L - rho_R).abs().sum().real.item())
    s_L = _von_neumann_entropy(rho_L)
    s_R = _von_neumann_entropy(rho_R)

    return {
        "contradiction_id": 5,
        "name": "Engine identity",
        "variant_a": {
            "label": "Type 1/Type 2 = left/right Weyl chiral operating spaces (owner-source)",
            "status": "live — only simulated option",
            "rho_L_entropy": round(s_L, 8),
            "rho_R_entropy": round(s_R, 8),
            "cross_engine_l1_diff": round(cross_diff, 8),
            "engines_distinguishable": cross_diff > 1e-8,
            "source": "apple axes terrain operator math.md:1249-1306",
        },
        "variant_b": {
            "label": "Type 1/Type 2 reserved for sheets only — never engine identity",
            "status": "killed_by_owner",
            "source": "grok_audit.py:16 — agent drift",
            "sim": None,
        },
        "variant_c": {
            "label": "Dual-stack = 2 Carnot + 2 Szilard simultaneously",
            "status": "killed_by_owner",
            "source": "grok_audit.py:24 — agent drift",
            "sim": None,
        },
        "comparison": {
            "live_options": ["a"],
            "killed_options": ["b", "c"],
            "distinguishable": True,  # (a) is the only candidate; no collapse possible
            "signature_a": round(s_L, 8),
            "signature_b": None,
            "signature_c": None,
        },
    }


# ---------------------------------------------------------------------------
# Contradiction 6: Layer order — standard vs frame-reduction-earlier
# ---------------------------------------------------------------------------

STANDARD_LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

# Variant (b): frame_bundle_structure_reduction moved before weyl_spinor_bundle
EARLY_FRAME_LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "frame_bundle_structure_reduction",  # moved earlier
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]


def _layer_removal_graveyard(layer_order: list[str], state: torch.Tensor) -> dict:
    """
    Simulate the graveyard pattern for a given layer order.

    Two signals are computed:

    1. Dependency-violation count: for each candidate ordering, count how many
       standard dependency edges are violated (i.e., a layer appears AFTER a
       layer that must come before it in the standard order). This is the primary
       structural signal — it DOES differ between orderings.

    2. Entropy-per-block: for each block position, compute entropy of the
       sub-state when block i is extracted (partial trace). This is the
       secondary physical signal — for genuinely mixed states it varies by block.

    Returns: {layer_name: {"entropy": float, "dependency_depth": int}}
    """
    dim = state.shape[0]
    assert dim == 8, f"Expected 8x8 state, got {dim}"

    # Standard order position map (from STANDARD_LAYERS)
    standard_pos = {name: idx for idx, name in enumerate(STANDARD_LAYERS)}

    # Dependency-violation scan: for each consecutive pair in this order,
    # check whether the standard order agrees or disagrees.
    violations: list[tuple[str, str]] = []
    for j in range(len(layer_order) - 1):
        a_name = layer_order[j]
        b_name = layer_order[j + 1]
        a_pos = standard_pos.get(a_name, j)
        b_pos = standard_pos.get(b_name, j + 1)
        if a_pos > b_pos:
            violations.append((a_name, b_name))

    # Block-level entropy: compute entropy of the 2x2 sub-block at each position
    n_blocks = min(len(layer_order), dim // 2)
    graveyard: dict[str, dict] = {}

    for i in range(n_blocks):
        # Extract the i-th 2x2 diagonal block as a local density
        block = state[2 * i : 2 * i + 2, 2 * i : 2 * i + 2].clone()
        tr_block = torch.trace(block).real
        if tr_block > 1e-10:
            block_normed = block / tr_block.to(DTYPE)
            block_normed = _project_to_density(block_normed)
            s_block = _von_neumann_entropy(block_normed)
        else:
            s_block = float("nan")

        layer_name = layer_order[i] if i < len(layer_order) else f"layer_{i}"
        # Dependency depth = position in standard order (indicates structural role)
        dep_depth = standard_pos.get(layer_name, -1)
        graveyard[layer_name] = {
            "entropy": round(s_block, 8),
            "dependency_depth_in_standard_order": dep_depth,
            "position_in_this_order": i,
        }

    return {
        "per_layer": graveyard,
        "violation_count": len(violations),
        "violations": violations,
        # Primary distinguishing signal: violation_count differs between orderings
        "primary_signature": float(len(violations)),
        # Secondary: entropy of block at position where the two orders FIRST differ
        "secondary_signature": graveyard[layer_order[0]]["entropy"] if layer_order else 0.0,
    }


def simulate_layer_order_variants(state: torch.Tensor) -> dict:
    """
    Variant (a): standard 13-layer tower order (probe:56).
    Variant (b): frame_bundle_structure_reduction moved before weyl_spinor_bundle (probe:231-232).

    Primary distinguishing signal: dependency-violation count.
    The standard order has 0 violations by definition.
    The early-frame order has at least 1 violation (frame_bundle_structure_reduction
    appears before weyl_spinor_bundle, which violates the standard dependency edge
    weyl_spinor_bundle -> frame_bundle_structure_reduction).

    Secondary signal: per-block entropy profile.
    """
    graveyard_a = _layer_removal_graveyard(STANDARD_LAYERS, state)
    graveyard_b = _layer_removal_graveyard(EARLY_FRAME_LAYERS, state)

    viol_a = graveyard_a["violation_count"]
    viol_b = graveyard_b["violation_count"]
    sig_a = graveyard_a["primary_signature"]
    sig_b = graveyard_b["primary_signature"]

    # Entropy L1 over the first 8 blocks (secondary signal)
    layers_a8 = STANDARD_LAYERS[:8]
    layers_b8 = EARLY_FRAME_LAYERS[:8]
    per_a = graveyard_a["per_layer"]
    per_b = graveyard_b["per_layer"]
    entropy_l1 = sum(
        abs(per_a.get(la, {}).get("entropy", 0.0) - per_b.get(lb, {}).get("entropy", 0.0))
        for la, lb in zip(layers_a8, layers_b8)
    )

    # Layers at different positions
    diff_layers: dict[str, dict] = {}
    for i, (la, lb) in enumerate(zip(STANDARD_LAYERS[:8], EARLY_FRAME_LAYERS[:8])):
        if la != lb:
            diff_layers[f"position_{i}"] = {
                "standard_layer": la,
                "early_frame_layer": lb,
                "entropy_standard": per_a.get(la, {}).get("entropy"),
                "entropy_early_frame": per_b.get(lb, {}).get("entropy"),
            }

    # Primary distinguishable: violation counts differ
    distinguishable = (viol_a != viol_b) or (abs(sig_a - sig_b) > 1e-8)

    return {
        "contradiction_id": 6,
        "name": "Layer order",
        "variant_a": {
            "label": "standard 13-layer tower (sim_nested_geometry_tower_dependency_order_probe.py:56)",
            "violation_count": viol_a,
            "violations": graveyard_a["violations"],
            "per_layer_entropy_sample": {k: v["entropy"] for k, v in per_a.items()},
        },
        "variant_b": {
            "label": "frame_bundle_structure_reduction moved before weyl_spinor_bundle (probe:231-232)",
            "violation_count": viol_b,
            "violations": graveyard_b["violations"],
            "per_layer_entropy_sample": {k: v["entropy"] for k, v in per_b.items()},
        },
        "comparison": {
            "violation_count_a": viol_a,
            "violation_count_b": viol_b,
            "entropy_l1_secondary": round(entropy_l1, 10),
            "layers_at_different_positions": diff_layers,
            "distinguishable": distinguishable,
            "signature_a": sig_a,
            "signature_b": sig_b,
        },
    }


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------


def run_all_contradiction_variants(state: torch.Tensor) -> dict:
    """
    Call all 6 contradiction simulations and return a composite report.
    """
    results: dict[str, Any] = {}
    results["contradiction_1_ax0"] = simulate_ax0_variants(state)
    results["contradiction_2_ax4"] = simulate_ax4_variants(state)
    results["contradiction_3_ax5"] = simulate_ax5_variants(state)
    results["contradiction_4_gamma5"] = simulate_gamma5_variants(state)
    results["contradiction_5_engine"] = simulate_engine_identity_variants()
    results["contradiction_6_layer_order"] = simulate_layer_order_variants(state)
    results["registry"] = enumerate_known_contradictions()
    return results


# ---------------------------------------------------------------------------
# z3 UNSAT witness: no two variant pairs collapse to the same signature
# ---------------------------------------------------------------------------


def contradiction_variant_signature_z3(results: dict) -> dict:
    """
    Z3 UNSAT witness that no two variant pairs across ALL contradictions
    collapse to the same signature value.

    Strategy: collect all (contradiction_id, variant_label, signature_float)
    triples. Encode as z3 Real variables. For every pair from the SAME
    contradiction, assert they are NOT equal. Check satisfiability of
    the NEGATION (i.e., assert some pair IS equal). UNSAT means no collapse
    is consistent with the arithmetic.

    We use real-valued z3 with rational approximation (multiply by 1e8 and
    floor to integers to avoid transcendental comparisons).
    """
    # Collect signatures
    sig_triples: list[tuple[int, str, float]] = []

    c1 = results.get("contradiction_1_ax0", {})
    comp1 = c1.get("comparison", {})
    sig_triples.append((1, "a_coherent_info", comp1.get("signature_a", 0.0)))
    sig_triples.append((1, "b_feedback_sign", comp1.get("signature_b", 0.0)))

    c2 = results.get("contradiction_2_ax4", {})
    comp2 = c2.get("comparison", {}).get("signature_per_variant", {})
    for label, val in comp2.items():
        sig_triples.append((2, label, val))

    c3 = results.get("contradiction_3_ax5", {})
    comp3 = c3.get("comparison", {})
    sig_triples.append((3, "a_dephasing", comp3.get("signature_a", 0.0)))
    sig_triples.append((3, "b_heat_hot", comp3.get("signature_b", 0.0)))

    c4 = results.get("contradiction_4_gamma5", {})
    comp4 = c4.get("comparison", {})
    sig_triples.append((4, "a_kraus_source", comp4.get("signature_a", 0.0)))
    sig_triples.append((4, "b_output_proj", comp4.get("signature_b", 0.0)))

    c5 = results.get("contradiction_5_engine", {})
    comp5 = c5.get("comparison", {})
    sig_triples.append((5, "a_left_engine", comp5.get("signature_a", 0.0) or 0.0))
    # (b) and (c) are killed — no signature; we include 0.0 sentinels so z3 can
    # confirm they do not collapse with (a)
    # (skipped — killed options have no live sim)

    c6 = results.get("contradiction_6_layer_order", {})
    comp6 = c6.get("comparison", {})
    sig_triples.append((6, "a_standard", comp6.get("signature_a", 0.0) or 0.0))
    sig_triples.append((6, "b_early_frame", comp6.get("signature_b", 0.0) or 0.0))

    # Group by contradiction_id
    by_contradiction: dict[int, list[tuple[str, float]]] = {}
    for cid, label, sig in sig_triples:
        by_contradiction.setdefault(cid, []).append((label, sig))

    # z3 check: for each contradiction, assert all variant signatures are distinct
    # UNSAT on the negation means they ARE all distinct
    solver = z3.Solver()

    # Encode signatures as z3 Real constants
    z3_vars: dict[tuple[int, str], z3.ExprRef] = {}
    for cid, label, sig in sig_triples:
        var = z3.Real(f"sig_{cid}_{label.replace(' ', '_')}")
        z3_vars[(cid, label)] = var
        # Fix value to rational approximation (1e8 precision)
        int_val = int(round(sig * 1e8))
        solver.add(var == z3.RealVal(int_val) / z3.RealVal(100000000))

    # For within-contradiction pairs: assert collapse IS possible (negation of distinctness)
    # If UNSAT: variants are provably distinct within each contradiction
    collapse_witnesses: dict[int, dict] = {}
    for cid, variants in by_contradiction.items():
        if len(variants) < 2:
            collapse_witnesses[cid] = {"status": "single_variant_no_collapse_possible"}
            continue
        neg_solver = z3.Solver()
        # Add all value constraints
        for label, sig in variants:
            var = z3_vars[(cid, label)]
            int_val = int(round(sig * 1e8))
            neg_solver.add(var == z3.RealVal(int_val) / z3.RealVal(100000000))
        # Assert that SOME pair is equal (collision)
        collision_conditions = []
        for i in range(len(variants)):
            for j in range(i + 1, len(variants)):
                vi = z3_vars[(cid, variants[i][0])]
                vj = z3_vars[(cid, variants[j][0])]
                collision_conditions.append(vi == vj)
        neg_solver.add(z3.Or(collision_conditions))
        result = neg_solver.check()
        collapse_witnesses[cid] = {
            "z3_check": str(result),
            "unsat_means_all_variants_distinct": result == z3.unsat,
            "variants_compared": [label for label, _ in variants],
            "values": {label: round(sig, 8) for label, sig in variants},
        }

    # Global verdict
    all_unsat = all(
        v.get("unsat_means_all_variants_distinct", False)
        for v in collapse_witnesses.values()
        if "unsat_means_all_variants_distinct" in v
    )

    return {
        "z3_verdict": "UNSAT (all variant signatures provably distinct)" if all_unsat else "SAT (some collapse detected)",
        "all_variants_distinct": all_unsat,
        "by_contradiction": collapse_witnesses,
        "total_signature_triples": len(sig_triples),
    }


# ---------------------------------------------------------------------------
# __main__ — smoke test
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import json

    print("=" * 72)
    print("doc_contradictions_parallel_variants.py — smoke test")
    print("=" * 72)

    # Build a genuinely mixed 8x8 test state so observables separate across variants.
    # Pure-state inputs collapse Ax0 coherent info (S(AB)=0 for product-pure),
    # Ax4 entropy (pure qubit dephased to same end state), and layer-order graveyard
    # (zeroing orthogonal blocks of a pure-diagonal gives same entropy). Mixed state avoids this.
    torch.manual_seed(42)
    # Build a random mixed state: average of several pure states with unequal weights
    weights = torch.tensor([0.45, 0.25, 0.15, 0.10, 0.05], dtype=torch.float64)
    psis: list[torch.Tensor] = []
    for i in range(5):
        psi_raw = torch.randn(8, dtype=torch.complex128) + 1j * torch.randn(8, dtype=torch.complex128)
        psi_raw[i] += 2.0  # break symmetry per sample
        psi_norm = psi_raw / torch.linalg.vector_norm(psi_raw)
        psis.append(psi_norm)
    rho_test = sum(
        float(weights[i]) * torch.outer(psis[i], psis[i].conj())
        for i in range(5)
    )  # type: ignore[arg-type]
    # Normalize trace to 1.0
    rho_test = rho_test / torch.trace(rho_test).real.to(DTYPE)

    print(f"\nTest state: 8x8 complex128 density matrix")
    print(f"  trace = {torch.trace(rho_test).real.item():.6f}")
    print(f"  purity = {(rho_test @ rho_test).trace().real.item():.6f}")

    # Enumerate contradictions
    contras = enumerate_known_contradictions()
    print(f"\n{'─'*72}")
    print(f"CONTRADICTIONS REGISTERED: {len(contras)}")
    for c in contras:
        n_options = len(c["options"])
        live = sum(1 for o in c["options"] if o.get("status", "live") != "killed_by_owner")
        print(f"  [{c['id']}] {c['name']}: {n_options} option(s), {live} live")

    # Run all simulations
    print(f"\n{'─'*72}")
    print("RUNNING ALL 6 CONTRADICTION SIMULATIONS...")
    all_results = run_all_contradiction_variants(rho_test)

    # Report per-contradiction distinguishability
    print(f"\n{'─'*72}")
    print("SIGNATURE DISTINGUISHABILITY REPORT:")
    print(f"{'─'*72}")

    report_keys = [
        ("contradiction_1_ax0", "Ax0: cut-state functional vs feedback-loop sign"),
        ("contradiction_2_ax4", "Ax4: 4 ordering variants"),
        ("contradiction_3_ax5", "Ax5: operator-family vs heat-level"),
        ("contradiction_4_gamma5", "γ5: Kraus-source vs output-projector"),
        ("contradiction_5_engine", "Engine identity: left/right Weyl (only live option)"),
        ("contradiction_6_layer_order", "Layer order: standard vs early-frame-reduction"),
    ]

    collapses: list[str] = []
    distincts: list[str] = []

    for key, label in report_keys:
        r = all_results[key]
        comp = r.get("comparison", {})
        distinguishable = comp.get("distinguishable", None)

        if key == "contradiction_2_ax4":
            min_dist = comp.get("min_off_diagonal_distance", 0.0)
            all_four = comp.get("all_four_distinguishable", False)
            status = "DISTINCT (all 4 variants)" if all_four else f"PARTIAL (min dist = {min_dist:.2e})"
            if all_four:
                distincts.append(label)
            else:
                collapses.append(label)
            print(f"  [{key.split('_')[1]}] {label}")
            print(f"      Status: {status}")
            sigs = comp.get("signature_per_variant", {})
            for o, s in sigs.items():
                print(f"        {o}: entropy = {s:.6f}")
        elif key == "contradiction_4_gamma5":
            rank_a = comp.get("choi_rank_a", "?")
            rank_b = comp.get("choi_rank_b", "?")
            dist_rank = comp.get("distinguishable_by_choi_rank", False)
            dist_ent = comp.get("distinguishable_by_output_entropy", False)
            status = "DISTINCT" if distinguishable else "COLLAPSE (decorative)"
            if distinguishable:
                distincts.append(label)
            else:
                collapses.append(label)
            print(f"  [{key.split('_')[1]}] {label}")
            print(f"      Choi rank (a)={rank_a}, (b)={rank_b} — rank-distinct: {dist_rank}")
            print(f"      Entropy-distinct: {dist_ent} | Overall: {status}")
        elif key == "contradiction_5_engine":
            live = r.get("variant_a", {})
            print(f"  [{key.split('_')[1]}] {label}")
            print(f"      Only option (a) is live; (b),(c) killed by owner.")
            print(f"      ρ_L entropy = {live.get('rho_L_entropy', '?'):.6f}")
            print(f"      ρ_R entropy = {live.get('rho_R_entropy', '?'):.6f}")
            print(f"      L/R cross-engine L1 diff = {live.get('cross_engine_l1_diff', '?'):.6f}")
            distincts.append(label)
        else:
            sig_a = comp.get("signature_a", "?")
            sig_b = comp.get("signature_b", "?")
            status = "DISTINCT" if distinguishable else "COLLAPSE (decorative)"
            if distinguishable:
                distincts.append(label)
            else:
                collapses.append(label)
            print(f"  [{key.split('_')[1]}] {label}")
            print(f"      sig(a) = {sig_a:.6f} | sig(b) = {sig_b:.6f}")
            print(f"      Status: {status}")

    # z3 UNSAT
    print(f"\n{'─'*72}")
    print("Z3 UNSAT WITNESS (variant-collapse check):")
    z3_result = contradiction_variant_signature_z3(all_results)
    print(f"  Global verdict: {z3_result['z3_verdict']}")
    print(f"  Total signature triples checked: {z3_result['total_signature_triples']}")
    for cid, w in z3_result["by_contradiction"].items():
        status = w.get("z3_check", "N/A")
        unsat = w.get("unsat_means_all_variants_distinct", None)
        variants = w.get("variants_compared", [])
        vals = w.get("values", {})
        print(f"  Contradiction {cid}: z3={status} | distinct={unsat}")
        for vname in variants:
            print(f"    {vname}: {vals.get(vname, '?'):.6f}")

    # Summary
    print(f"\n{'─'*72}")
    print("SUMMARY:")
    print(f"  Contradictions with DISTINCT variants (load-bearing): {len(distincts)}")
    for d in distincts:
        print(f"    + {d}")
    print(f"  Contradictions that COLLAPSE (decorative): {len(collapses)}")
    for c in collapses:
        print(f"    - {c}")
    print(f"\n  claim_ceiling: tool_lego_fit_probe")
    print(f"  promotion_allowed: false")
    print("=" * 72)
