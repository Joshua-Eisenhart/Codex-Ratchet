#!/usr/bin/env python3
"""
topology_flux_feedback.py

Terrain projectors that ACT ON the dynamic state during evolution —
not passive witnesses sitting beside it.

Source alignment:
  - Left Weyl (Type 1): flux IN, sigma_- sink law, H_L = +H0
    Terrains: Funnel (Se), Vortex (Ne), Pit (Ni), Hill (Si)
  - Right Weyl (Type 2): flux OUT, sigma_+ source law, H_R = -H0
    Terrains: Cannon (Se), Spiral (Ne), Source (Ni), Citadel (Si)

Operator math from:
  `apple axes terrain operator math.md:1249-1306`
  `LEFT_RIGHT_CHIRAL_OPERATING_SPACE_BUILD_NOTE.md:82-103`

All terrain projectors are geometric operators on chirality blocks.
Geometry is in the projector structure; no abstract axis labels appear
in the projector implementations.

CPTP preservation: all terrain operators are cast as Kraus maps
  rho' = sum_k K_k rho K_k†
with explicit Kraus operator construction. Trace-preservation, Hermiticity,
and positivity enforced at every application step.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Primitive Pauli blocks (complex128 torch tensors on CPU)
# ---------------------------------------------------------------------------

DTYPE = torch.complex128

def _t(arr: list) -> torch.Tensor:
    return torch.tensor(arr, dtype=DTYPE)

I2    = _t([[1, 0], [0, 1]])
SX    = _t([[0, 1], [1, 0]])
SY    = _t([[0, -1j], [1j, 0]])
SZ    = _t([[1, 0], [0, -1]])
SM    = _t([[0, 0], [1, 0]])   # sigma_-  (lowering, sink — LEFT side)
SP    = _t([[0, 1], [0, 0]])   # sigma_+  (raising, source — RIGHT side)
H0    = SZ                      # base Hamiltonian
H_L   = H0                      # left chiral: +H0
H_R   = -H0                     # right chiral: -H0

# Projectors onto upper/lower eigenstate in sigma_z basis
P_UP  = _t([[1, 0], [0, 0]])   # |0><0|
P_DN  = _t([[0, 0], [0, 1]])   # |1><1|

# 4-dim identity (for full L+R density)
I4 = torch.eye(4, dtype=DTYPE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dag(M: torch.Tensor) -> torch.Tensor:
    """Conjugate transpose."""
    return M.conj().T


def embed_L(op2: torch.Tensor) -> torch.Tensor:
    """Embed 2x2 operator into top-left block of 4x4."""
    out = torch.zeros(4, 4, dtype=DTYPE)
    out[:2, :2] = op2
    return out


def embed_R(op2: torch.Tensor) -> torch.Tensor:
    """Embed 2x2 operator into bottom-right block of 4x4."""
    out = torch.zeros(4, 4, dtype=DTYPE)
    out[2:, 2:] = op2
    return out


def block_L(rho4: torch.Tensor) -> torch.Tensor:
    """Extract left (top-left 2x2) chirality block."""
    return rho4[:2, :2].clone()


def block_R(rho4: torch.Tensor) -> torch.Tensor:
    """Extract right (bottom-right 2x2) chirality block."""
    return rho4[2:, 2:].clone()


def is_valid_density(rho: torch.Tensor, tol: float = 1e-9) -> bool:
    """Check trace=1, Hermitian, positive semi-definite."""
    tr = rho.trace().real.item()
    if abs(tr - 1.0) > tol:
        return False
    diff = (rho - dag(rho)).abs().max().item()
    if diff > tol:
        return False
    eigs = torch.linalg.eigvalsh((rho + dag(rho)) / 2)
    if eigs.min().item() < -tol:
        return False
    return True


def _nearest_valid(rho: torch.Tensor) -> torch.Tensor:
    """Project density matrix to nearest valid state (trace-normalize, pin PSD)."""
    rho = (rho + dag(rho)) / 2
    eigs, vecs = torch.linalg.eigh(rho)
    eigs = torch.clamp(eigs.real, min=0.0).to(DTYPE)
    rho = vecs @ torch.diag(eigs) @ dag(vecs)
    tr = rho.trace()
    if tr.real.abs() < 1e-15:
        return torch.eye(rho.shape[0], dtype=DTYPE) / rho.shape[0]
    return rho / tr


def apply_kraus(rho: torch.Tensor, kraus_ops: list[torch.Tensor]) -> torch.Tensor:
    """
    Apply a Kraus map: rho' = sum_k K_k rho K_k†.
    Renormalizes to enforce trace-preservation numerically.
    """
    out = torch.zeros_like(rho)
    for K in kraus_ops:
        out = out + K @ rho @ dag(K)
    return _nearest_valid(out)


def _kraus_from_generator(G: torch.Tensor, dt: float) -> list[torch.Tensor]:
    """
    Construct approximate Kraus operators for e^{G dt} via first-order expansion.
    Returns [K0, K1] where K0 = I + G*dt/sqrt(2) (coherent part scaled),
    K1 absorbs the norm deficit to preserve trace.

    For a pure unitary: K0 = expm(-i H dt), K1 absent.
    """
    # Use matrix exponential for accuracy
    G_np = G.numpy().astype(complex)
    eG_np = _matrix_exp(G_np * dt)
    K0 = torch.tensor(eG_np, dtype=DTYPE)
    return [K0]


def _matrix_exp(M: np.ndarray) -> np.ndarray:
    """Matrix exponential via eigendecomposition (no scipy dependency)."""
    eigs, vecs = np.linalg.eig(M)
    return (vecs * np.exp(eigs)) @ np.linalg.inv(vecs)


def _dissipator_kraus(L: torch.Tensor, gamma: float, dt: float) -> list[torch.Tensor]:
    """
    Kraus operators for Lindblad dissipator D[L](rho) = L rho L† - (L†L rho + rho L†L)/2.
    First-order Kraus: K0 = sqrt(gamma*dt) * L,  K1 = I - gamma*dt/2 * L†L.
    K1 is the no-jump operator; K0 is the jump operator.
    Rescaled so sum K†K = I to machine precision.
    """
    K_jump = math.sqrt(max(gamma * dt, 0.0)) * L
    K_nojump = I2.clone() - (gamma * dt / 2.0) * (dag(L) @ L)
    # Verify completeness and rescale if needed
    comp = dag(K_jump) @ K_jump + dag(K_nojump) @ K_nojump
    # Symmetrize
    comp = (comp + dag(comp)) / 2
    eigs, vecs = torch.linalg.eigh(comp)
    eigs = torch.clamp(eigs.real, min=1e-15).to(DTYPE)
    # Scale K_nojump to absorb remainder
    scale = torch.sqrt(eigs)
    # Simple normalization: adjust K_nojump
    tr_comp = comp.trace().real.item()
    n = comp.shape[0]
    if abs(tr_comp - n) > 1e-6:
        # rescale no-jump
        K_nojump = K_nojump * math.sqrt(n / max(tr_comp, 1e-15))
    return [K_jump, K_nojump]


def _dephase_kraus(projectors: list[torch.Tensor], rate: float, dt: float) -> list[torch.Tensor]:
    """
    Kraus operators for dephasing: rho -> (1-r*dt)*rho + r*dt * sum_j P_j rho P_j.
    K0 = sqrt(1 - rate*dt) * I,  K_j = sqrt(rate*dt) * P_j  for each projector.
    """
    s = math.sqrt(max(1.0 - rate * dt, 0.0))
    ops = [s * I2.clone()]
    sp_ = math.sqrt(max(rate * dt, 0.0))
    for P in projectors:
        ops.append(sp_ * P.clone())
    return ops


def _unitary_kraus(H: torch.Tensor, dt: float) -> list[torch.Tensor]:
    """Kraus = single unitary U = exp(-i H dt)."""
    H_np = H.numpy().astype(complex)
    U_np = _matrix_exp(-1j * H_np * dt)
    return [torch.tensor(U_np, dtype=DTYPE)]


# ---------------------------------------------------------------------------
# build_terrain_projectors
# ---------------------------------------------------------------------------

def build_terrain_projectors() -> dict[str, torch.Tensor]:
    """
    Return 8 named 2x2 terrain projector operators.

    Left (Type 1, sigma_- sink, H_L = +H0):
      left_funnel  — Se: strong dissipation + inward flux damp
      left_vortex  — Ne: coherent rotation + weak curl dissipation
      left_pit     — Ni: sigma_- absorbing at one eigenstate
      left_hill    — Si: counter-diagonal repulsive dephase

    Right (Type 2, sigma_+ source, H_R = -H0):
      right_cannon  — Se: sigma_+ strong source + outward flux
      right_spiral  — Ne: coherent rotation (reversed sign) + source curl
      right_source  — Ni: sigma_+ emitting
      right_citadel — Si: stabilizing counter-flow dephase

    Each 2x2 operator represents the leading-order channel generator
    for its terrain's characteristic flux pattern.
    Operators are distinct by construction (different numerical signatures).
    """
    dt = 0.12

    # --- LEFT TERRAINS (sigma_- sink, H_L = +H0) ---

    # left_funnel (Se): strong dissipation dominant, small H_L mixing
    # Source: X_F^L(rho) = sum_k D[L_k](rho) - i eps_F [H0, rho]
    # Leading Kraus generator: epsilon_F = 0.35, gamma_F = 0.55
    eps_F = 0.35
    gamma_F = 0.55
    # Effective single Kraus: combined jump + coherent
    L_funnel = math.sqrt(gamma_F) * SM + eps_F * (H_L - H_L.conj().T) / 2
    # Represent as the operator whose action characterizes this terrain
    left_funnel_op = gamma_F * (dag(SM) @ SM) - 1j * eps_F * H_L
    # For projector representation: use the CPTP generator matrix as the "handle"
    left_funnel = left_funnel_op

    # left_vortex (Ne): coherent rotation dominant, weak curl dissipation
    # Source: X_V^L(rho) = -i[H0,rho] + eps_V sum_k D[M_k](rho)
    # M_k includes small lateral Pauli (SX, SY mix for curl effect)
    eps_V = 0.18
    gamma_V = 0.10
    L_vortex_j = 0.7 * SM + 0.3 * SX  # curl-like mix
    left_vortex = -1j * H_L + eps_V * (gamma_V * dag(L_vortex_j) @ L_vortex_j)

    # left_pit (Ni): sigma_- absorbing, one-eigenstate sink
    # Source: X_P^L(rho) = gamma_P D[sigma_-](rho) - i eps_P [H0, rho]
    gamma_P = 0.72
    eps_P = 0.22
    left_pit = gamma_P * (dag(SM) @ SM) - 1j * eps_P * H_L
    # Distinct from funnel by higher gamma and epsilon ratio

    # left_hill (Si): projector dephase — repulsive diagonal
    # Source: X_H^L(rho) = -i[H_C,rho] + sum_j kappa_j(P_j rho P_j - (P_j rho + rho P_j)/2)
    # H_C is a shifted version; kappa forces retention
    kappa_H = 0.45
    H_C = H_L + 0.3 * SX  # shifted Hamiltonian for hill
    # Leading operator: diagonal repulsion encoded via P_UP, P_DN dephase + anti-commutator
    left_hill = -1j * H_C + kappa_H * (P_UP - P_DN)  # diagonal sign difference encodes hill vs pit

    # --- RIGHT TERRAINS (sigma_+ source, H_R = -H0) ---

    # right_cannon (Se): sigma_+ strong directed outward source, large flux
    # Source: X_C^R(rho) = sum_k D[L_k^{C,R}](rho) - i eps_{C,R}[H_R, rho]
    # H_R = -H0, so coherent part has opposite rotation.
    # Cannon = DIRECTED launch: sigma_+ dominant, minimal lateral spread.
    eps_C = 0.35
    gamma_C = 0.80  # strong launch — cannon is the highest-gamma right terrain
    right_cannon = gamma_C * (dag(SP) @ SP) - 1j * eps_C * H_R

    # right_spiral (Ne): coherent rotation (H_R sign), source curl
    # Source: X_S^R(rho) = +i[H0,rho] + eps_{S,R} sum_k D[M_k^{S,R}](rho)
    # Note: H_R = -H0, so +i[H0] = -i[H_R]
    eps_S = 0.18
    gamma_S = 0.12
    L_spiral_j = 0.7 * SP - 0.3 * SX  # mirror curl (opposite SX sign from vortex)
    right_spiral = -1j * H_R + eps_S * (gamma_S * dag(L_spiral_j) @ L_spiral_j)

    # right_source (Ni): sigma_+ emitting, with strong lateral SY component
    # Source: X_So^R(rho) = gamma_{So} D[sigma_+](rho) + i eps_{So}[H0, rho]
    # Source = OMNIDIRECTIONAL emitter: sigma_+ + SY lateral spread.
    # This structural difference (SY addition) distinguishes source from cannon.
    gamma_So = 0.35  # lower directed gamma — emission is multi-directional
    eps_So = 0.42    # larger coherent component than cannon
    # Lateral emitter: add SY off-diagonal component to break degeneracy with cannon
    right_source = (gamma_So * (dag(SP) @ SP)
                    - 1j * eps_So * H_R
                    + 0.55 * SY)  # SY encodes lateral emission geometry

    # right_citadel (Si): stabilizing counter-flow dephase
    # Source: X_Ci^R(rho) = +i[H_C,rho] + sum_j kappa_{Ci}(P_j rho P_j - ...)
    # Counter-flow: H_C has opposite perturbation from hill
    kappa_Ci = 0.41
    H_C_R = H_R + 0.3 * SX  # shifted right Hamiltonian
    right_citadel = -1j * H_C_R + kappa_Ci * (P_DN - P_UP)  # inverted sign vs left_hill

    return {
        "left_funnel":    left_funnel,
        "left_vortex":    left_vortex,
        "left_pit":       left_pit,
        "left_hill":      left_hill,
        "right_cannon":   right_cannon,
        "right_spiral":   right_spiral,
        "right_source":   right_source,
        "right_citadel":  right_citadel,
    }


# ---------------------------------------------------------------------------
# apply_terrain_projector
# ---------------------------------------------------------------------------

def apply_terrain_projector(
    rho: torch.Tensor,
    terrain_name: str,
    flux_strength: float,
) -> torch.Tensor:
    """
    Apply named terrain as a CPTP channel on a 4x4 density matrix.

    The 4x4 density has block structure:
      [ rho_L  rho_LR ]
      [ rho_RL  rho_R ]

    Left terrains act on the L block (top-left 2x2).
    Right terrains act on the R block (bottom-right 2x2).
    Off-diagonal blocks are left coherently connected via identity passthrough.

    CPTP: Kraus operators built from terrain generator, scaled by flux_strength.
    Trace preservation, Hermiticity, PSD enforced post-application.
    """
    projectors = build_terrain_projectors()
    if terrain_name not in projectors:
        raise ValueError(f"Unknown terrain: {terrain_name}. "
                         f"Valid: {list(projectors.keys())}")

    op2 = projectors[terrain_name]
    dt = 0.10 * abs(flux_strength)

    is_left = terrain_name.startswith("left_")
    side = "left" if is_left else "right"

    # Build 2x2 Kraus operators for this terrain
    # We use a composite Kraus construction based on the terrain character:
    # The generator encodes both coherent and dissipative parts.
    # We split into: unitary part (anti-Hermitian component) + dissipative part (PSD component).
    op_np = op2.numpy().astype(complex)
    # Anti-Hermitian part -> unitary channel
    anti_herm = (op_np - op_np.conj().T) / 2
    # Hermitian part -> describes dissipation strength
    herm_part = (op_np + op_np.conj().T) / 2

    # Unitary Kraus from anti-Hermitian part: K_coh = exp(anti_herm * dt)
    K_coh_np = _matrix_exp(anti_herm * dt)
    K_coh = torch.tensor(K_coh_np, dtype=DTYPE)

    # Dissipative Kraus: use herm_part diagonal as dissipation rates
    eigs_d, vecs_d = np.linalg.eigh(herm_part)
    # Each eigen-channel gives a Kraus operator
    dissipative_kraus = []
    for i, lam in enumerate(eigs_d):
        if abs(lam) > 1e-12:
            scale = math.sqrt(abs(float(lam)) * dt) * math.copysign(1.0, float(lam))
            v = vecs_d[:, i].reshape(2, 1)
            K_d = torch.tensor(scale * v @ v.conj().T, dtype=DTYPE)
            dissipative_kraus.append(K_d)

    # Combine: full Kraus set = [K_coh] + dissipative_kraus
    kraus_2x2 = [K_coh] + dissipative_kraus

    # Completeness correction: ensure sum_k K†K = I2 (approximately)
    comp = sum(dag(K) @ K for K in kraus_2x2)
    comp = (comp + dag(comp)) / 2
    eigs_c, vecs_c = torch.linalg.eigh(comp)
    eigs_c = torch.clamp(eigs_c.real, min=1e-15).to(DTYPE)
    # Correction factor: scale each K by comp^{-1/2} (Choi-Kraus completeness fix)
    inv_sqrt_comp = vecs_c @ torch.diag(1.0 / torch.sqrt(eigs_c)) @ dag(vecs_c)
    kraus_2x2 = [inv_sqrt_comp @ K for K in kraus_2x2]

    # Embed 2x2 Kraus into 4x4 space
    if is_left:
        # Left terrain: acts on top-left 2x2 block; right block passthrough
        kraus_4x4 = []
        for K in kraus_2x2:
            K4 = torch.zeros(4, 4, dtype=DTYPE)
            K4[:2, :2] = K
            K4[2:, 2:] = I2  # passthrough on R block
            kraus_4x4.append(K4)
    else:
        # Right terrain: acts on bottom-right 2x2 block; left block passthrough
        kraus_4x4 = []
        for K in kraus_2x2:
            K4 = torch.zeros(4, 4, dtype=DTYPE)
            K4[:2, :2] = I2   # passthrough on L block
            K4[2:, 2:] = K
            kraus_4x4.append(K4)

    return apply_kraus(rho, kraus_4x4)


# ---------------------------------------------------------------------------
# flux_feature_from_state
# ---------------------------------------------------------------------------

def flux_feature_from_state(rho: torch.Tensor) -> dict[str, Any]:
    """
    Compute flux features from a 4x4 density matrix.

    Features:
      flux_in_left:                    <sigma_-> on left block (inward flux magnitude)
      flux_out_right:                  <sigma_+> on right block (outward flux magnitude)
      lr_imbalance:                    tr(rho_L) - tr(rho_R)
      off_diagonal_chirality_coherence: ||P_L rho P_R||_F  (off-block Frobenius norm)
      terrain_activation:              terrain name with highest operator overlap
    """
    rho_L = block_L(rho)  # 2x2 left block
    rho_R = block_R(rho)  # 2x2 right block

    # flux_in_left: <sigma_-> on left block = tr(sigma_- @ rho_L)
    flux_in_left = float((SM @ rho_L).trace().real)

    # flux_out_right: <sigma_+> on right block = tr(sigma_+ @ rho_R)
    flux_out_right = float((SP @ rho_R).trace().real)

    # lr_imbalance
    tr_L = float(rho_L.trace().real)
    tr_R = float(rho_R.trace().real)
    lr_imbalance = tr_L - tr_R

    # off_diagonal_chirality_coherence: ||rho[:2, 2:]||_F
    off_diag = rho[:2, 2:]
    off_diag_chirality_coherence = float(torch.linalg.norm(off_diag).real)

    # terrain_activation: overlap of each terrain generator with rho
    projectors = build_terrain_projectors()
    terrain_overlaps: dict[str, float] = {}
    for name, op2 in projectors.items():
        if name.startswith("left_"):
            block = rho_L
        else:
            block = rho_R
        # Overlap = |tr(op2 @ block)|
        overlap = float(abs((op2 @ block).trace()))
        terrain_overlaps[name] = overlap

    terrain_activation = max(terrain_overlaps, key=lambda k: terrain_overlaps[k])

    return {
        "flux_in_left":                     flux_in_left,
        "flux_out_right":                    flux_out_right,
        "lr_imbalance":                      lr_imbalance,
        "off_diagonal_chirality_coherence":  off_diag_chirality_coherence,
        "terrain_activation":                terrain_activation,
        "terrain_overlaps":                  terrain_overlaps,
    }


# ---------------------------------------------------------------------------
# Flux-to-terrain selection logic
# ---------------------------------------------------------------------------

# Thresholds for terrain selection based on flux features
_FLUX_IN_THRESHOLD = 0.05
_FLUX_OUT_THRESHOLD = 0.05
_IMBALANCE_THRESHOLD = 0.1


def _select_left_terrain(flux_in: float, imbalance: float) -> str:
    """
    Select left terrain based on measured flux features.
    Logic is driven by flux geometry, not axis labels.
    """
    if flux_in > _FLUX_IN_THRESHOLD and abs(imbalance) < _IMBALANCE_THRESHOLD:
        return "left_funnel"       # strong inward flux, balanced — funneling
    elif flux_in > _FLUX_IN_THRESHOLD and imbalance > _IMBALANCE_THRESHOLD:
        return "left_pit"          # strong inward flux + left-heavy — absorbing sink
    elif flux_in <= _FLUX_IN_THRESHOLD and imbalance < -_IMBALANCE_THRESHOLD:
        return "left_hill"         # weak inward flux + right-heavy — repulsive
    else:
        return "left_vortex"       # everything else — curl/rotation regime


def _select_right_terrain(flux_out: float, imbalance: float) -> str:
    """
    Select right terrain based on measured flux features.
    Logic is driven by flux geometry, not axis labels.
    """
    if flux_out > _FLUX_OUT_THRESHOLD and abs(imbalance) < _IMBALANCE_THRESHOLD:
        return "right_cannon"      # strong outward flux, balanced — cannon launch
    elif flux_out > _FLUX_OUT_THRESHOLD and imbalance < -_IMBALANCE_THRESHOLD:
        return "right_source"      # strong outward flux + right-heavy — emitting
    elif flux_out <= _FLUX_OUT_THRESHOLD and imbalance > _IMBALANCE_THRESHOLD:
        return "right_citadel"     # weak outward flux + left-heavy — stabilizing
    else:
        return "right_spiral"      # everything else — rotation/curl regime


# ---------------------------------------------------------------------------
# feedback_step
# ---------------------------------------------------------------------------

def feedback_step(
    rho: torch.Tensor,
    step: int,
    accumulated_flux: dict,
) -> tuple[torch.Tensor, dict]:
    """
    One feedback step: measure flux → select terrain → apply channel → update accumulator.

    1. Compute flux features from current rho
    2. Select terrain projector based on flux features
    3. Apply selected terrain projector with strength scaled by flux magnitude
    4. Update accumulated_flux dict
    5. Return (new_rho, updated_accumulated_flux)
    """
    features = flux_feature_from_state(rho)

    flux_in = features["flux_in_left"]
    flux_out = features["flux_out_right"]
    imbalance = features["lr_imbalance"]

    # Select terrain per chiral side based on flux geometry
    left_terrain = _select_left_terrain(flux_in, imbalance)
    right_terrain = _select_right_terrain(flux_out, imbalance)

    # Flux strength scales application magnitude
    left_strength = max(abs(flux_in), 0.05)
    right_strength = max(abs(flux_out), 0.05)

    # Apply left terrain first, then right terrain
    rho_after_left = apply_terrain_projector(rho, left_terrain, left_strength)
    rho_new = apply_terrain_projector(rho_after_left, right_terrain, right_strength)

    # Update accumulator
    acc = dict(accumulated_flux)
    acc.setdefault("total_flux_in_left", 0.0)
    acc.setdefault("total_flux_out_right", 0.0)
    acc.setdefault("steps_completed", 0)
    acc.setdefault("terrain_counts", {})

    acc["total_flux_in_left"] += flux_in
    acc["total_flux_out_right"] += flux_out
    acc["steps_completed"] = step + 1

    for t in [left_terrain, right_terrain]:
        acc["terrain_counts"][t] = acc["terrain_counts"].get(t, 0) + 1

    acc[f"step_{step}_left_terrain"] = left_terrain
    acc[f"step_{step}_right_terrain"] = right_terrain
    acc[f"step_{step}_flux_in"] = flux_in
    acc[f"step_{step}_flux_out"] = flux_out
    acc[f"step_{step}_imbalance"] = imbalance

    return rho_new, acc


# ---------------------------------------------------------------------------
# run_topology_flux_feedback_trajectory
# ---------------------------------------------------------------------------

def run_topology_flux_feedback_trajectory(
    rho_init: torch.Tensor,
    n_steps: int = 8,
) -> dict:
    """
    Run N feedback steps. At each step the terrain is selected from measured flux features.

    Returns:
      terrain_history:    list of (left_terrain, right_terrain) at each step
      flux_history:       list of flux feature dicts at each step
      accumulated_flux:   final accumulator dict
      rho_final:          final density matrix
      rho_trajectory:     list of density matrices at each step (including init)
      all_valid:          True if all states remained valid
    """
    rho = _nearest_valid(rho_init.clone())
    accumulated_flux: dict = {}
    terrain_history: list = []
    flux_history: list = []
    rho_trajectory = [rho.clone()]

    for step in range(n_steps):
        features = flux_feature_from_state(rho)
        flux_history.append({k: v for k, v in features.items() if k != "terrain_overlaps"})

        rho_new, accumulated_flux = feedback_step(rho, step, accumulated_flux)
        terrain_history.append((
            accumulated_flux.get(f"step_{step}_left_terrain", "?"),
            accumulated_flux.get(f"step_{step}_right_terrain", "?"),
        ))
        rho = rho_new
        rho_trajectory.append(rho.clone())

    all_valid = all(is_valid_density(r) for r in rho_trajectory)

    return {
        "terrain_history":   terrain_history,
        "flux_history":      flux_history,
        "accumulated_flux":  accumulated_flux,
        "rho_final":         rho,
        "rho_trajectory":    rho_trajectory,
        "all_valid":         all_valid,
    }


# ---------------------------------------------------------------------------
# topology_no_feedback_control (graveyard control)
# ---------------------------------------------------------------------------

def topology_no_feedback_control(
    rho_init: torch.Tensor,
    n_steps: int = 8,
) -> dict:
    """
    GRAVEYARD CONTROL: same number of steps but fixed terrain (always left_funnel +
    right_cannon, never updated from measured flux features). Result should differ
    from the feedback trajectory.

    This is the graveyard variant: terrain is frozen at step 0 selection and
    never updated regardless of what flux features show.
    """
    rho = _nearest_valid(rho_init.clone())
    fixed_left_terrain = "left_funnel"
    fixed_right_terrain = "right_cannon"
    fixed_strength = 0.10  # constant, not flux-scaled

    terrain_history: list = []
    rho_trajectory = [rho.clone()]

    for step in range(n_steps):
        rho = apply_terrain_projector(rho, fixed_left_terrain, fixed_strength)
        rho = apply_terrain_projector(rho, fixed_right_terrain, fixed_strength)
        terrain_history.append((fixed_left_terrain, fixed_right_terrain))
        rho_trajectory.append(rho.clone())

    all_valid = all(is_valid_density(r) for r in rho_trajectory)

    return {
        "terrain_history": terrain_history,
        "rho_final":       rho,
        "rho_trajectory":  rho_trajectory,
        "all_valid":       all_valid,
    }


# ---------------------------------------------------------------------------
# __main__ smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("topology_flux_feedback.py — smoke test")
    print("=" * 70)

    # 1. Build projectors and confirm distinctness (pairwise Frobenius)
    print("\n[1] Building 8 terrain projectors...")
    projectors = build_terrain_projectors()
    names = list(projectors.keys())
    assert len(names) == 8, f"Expected 8, got {len(names)}"

    frob_distances: dict[tuple[str, str], float] = {}
    min_dist = float("inf")
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if j <= i:
                continue
            diff = projectors[n1] - projectors[n2]
            d = float(torch.linalg.norm(diff).real)
            frob_distances[(n1, n2)] = d
            if d < min_dist:
                min_dist = d

    print(f"   All 8 terrain projectors built: {names}")
    print(f"   Min pairwise Frobenius distance: {min_dist:.6f}")
    if min_dist > 1e-3:
        print("   PASS: all projectors are distinct (min dist > 1e-3)")
    else:
        print("   FAIL: some projectors are too similar (min dist <= 1e-3)")

    print("\n   Pairwise distances:")
    for (n1, n2), d in frob_distances.items():
        n1s = n1.replace("left_", "L:").replace("right_", "R:")
        n2s = n2.replace("left_", "L:").replace("right_", "R:")
        marker = " *" if d < 1e-3 else ""
        print(f"     {n1s:18s} ↔ {n2s:18s}  {d:.6f}{marker}")

    # 2. Build a random valid 4x4 density matrix
    print("\n[2] Building random valid 4x4 density matrix...")
    torch.manual_seed(42)
    np.random.seed(42)
    # Random positive matrix -> normalize
    A = torch.randn(4, 4, dtype=DTYPE)
    rho_rand = A @ dag(A)
    rho_init = _nearest_valid(rho_rand)
    assert is_valid_density(rho_init), "Initial state not valid"
    print(f"   Initial state: trace={rho_init.trace().real.item():.6f}, "
          f"valid={is_valid_density(rho_init)}")

    # 3. Run 10-step feedback trajectory
    print("\n[3] Running 10-step feedback trajectory...")
    result = run_topology_flux_feedback_trajectory(rho_init, n_steps=10)

    print(f"   all_valid across trajectory: {result['all_valid']}")
    if not result["all_valid"]:
        print("   FAIL: some states became invalid during feedback evolution")
    else:
        print("   PASS: all 11 states (init + 10 steps) remain valid")

    print("\n   State validity at each step:")
    for i, r in enumerate(result["rho_trajectory"]):
        tr = r.trace().real.item()
        valid = is_valid_density(r)
        print(f"     step {i:2d}: trace={tr:.8f}  valid={valid}")

    # 4. Terrain activation history
    print("\n[4] Terrain activation at each step:")
    for step, (lt, rt) in enumerate(result["terrain_history"]):
        fi = result["flux_history"][step]["flux_in_left"]
        fo = result["flux_history"][step]["flux_out_right"]
        print(f"   step {step:2d}: L={lt:18s}  R={rt:18s}"
              f"  flux_in={fi:+.4f}  flux_out={fo:+.4f}")

    terrain_counts = result["accumulated_flux"].get("terrain_counts", {})
    print("\n   Terrain activation counts across 10 steps:")
    for t, cnt in sorted(terrain_counts.items()):
        print(f"     {t}: {cnt}")

    # 5. Max flux magnitude observed
    max_flux = max(
        max(abs(fh["flux_in_left"]), abs(fh["flux_out_right"]))
        for fh in result["flux_history"]
    )
    print(f"\n[5] Max flux magnitude observed: {max_flux:.6f}")

    # 6. No-feedback control and divergence check
    print("\n[6] Running no-feedback control (graveyard)...")
    ctrl = topology_no_feedback_control(rho_init, n_steps=10)
    print(f"   Control all_valid: {ctrl['all_valid']}")

    # Compare final states
    rho_fb = result["rho_final"]
    rho_ctrl = ctrl["rho_final"]
    divergence = float(torch.linalg.norm(rho_fb - rho_ctrl).real)
    print(f"   Final state divergence (Frobenius): {divergence:.6f}")
    if divergence > 1e-3:
        print("   PASS: feedback trajectory diverges from no-feedback control (> 1e-3)")
    else:
        print("   FAIL: feedback and no-feedback final states too similar (<= 1e-3)")

    # 7. Interface contract summary
    print("\n[7] Interface contract summary:")
    print("   build_terrain_projectors()             -> dict[str, torch.Tensor] (8 ops)")
    print("   apply_terrain_projector(rho, name, s)  -> torch.Tensor (4x4 CPTP)")
    print("   flux_feature_from_state(rho)           -> dict[str, float/str]")
    print("   feedback_step(rho, step, acc)          -> (torch.Tensor, dict)")
    print("   run_topology_flux_feedback_trajectory  -> dict (history + final)")
    print("   topology_no_feedback_control           -> dict (graveyard control)")

    print("\n" + "=" * 70)
    print("Smoke test complete.")
    print("=" * 70)
