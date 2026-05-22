#!/usr/bin/env python3
"""
engine_core.py — EngineCore class for operational QIT engine execution.

Runs the Lindblad ODE evolution per stage on a 2-dim density matrix carrier:
  dρ/dt = -i [H, ρ] + L ρ L† - ½ {L†L, ρ}

Each stage consists of:
  1. Apply operator unitary U = exp(-i * sign * theta * G_op) on the density.
  2. Apply Lindblad ODE evolution under (H, L) for stage duration dt.
  3. Apply 13-layer manifold constraints to the pure-state embedding of ρ
     (or the eigenvector embedding when ρ is mixed).
  4. Record substage row.

A full cycle = 8 main stages × 4 substages = 32 substages per engine.
A paired engine cycle = 64 substages across both engines.

Source alignment:
  - canonical_qit_engine_specs.py (all specs)
  - claude_integrated_manifold_modules/active_layer_constraint_enforcers.py
    (13-layer manifold enforcer chain)
  - sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py
    (substage layout reference)
  - sim_two_chiral_operating_spaces_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe.py
    (v4 engine sim reference, do not duplicate)
"""

from __future__ import annotations

import hashlib
import math
import os
import pathlib
import sys
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Path setup — import canonical specs + manifold enforcers
# ---------------------------------------------------------------------------

_ROOT = pathlib.Path(__file__).resolve().parent
_MODULE_DIR = _ROOT / "claude_integrated_manifold_modules"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from canonical_qit_engine_specs import (
    H_TYPE_ONE as CANON_H_TYPE_ONE,
    H_TYPE_TWO as CANON_H_TYPE_TWO,
    I2 as CANON_I2,
    MANIFOLD_LAYERS,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS as CANON_OPERATOR_GENERATORS,
    SIGMA_MINUS as CANON_SIGMA_MINUS,
    SIGMA_PLUS as CANON_SIGMA_PLUS,
    SX as CANON_SX,
    SY as CANON_SY,
    SZ as CANON_SZ,
    N_MAIN_STAGES_PER_ENGINE,
    N_SUBSTAGES_PER_MAIN,
    N_TOTAL_SUBSTAGES_PER_ENGINE,
    get_engine_spec,
    get_lindblad_params,
    get_operator_slot_spec,
    get_loop_class_op_sign,
    get_schedule,
    get_topology_spec,
    get_terrain_dynamics_spec,
)
from active_layer_constraint_enforcers import apply_all_layer_constraints

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TORCH_DTYPE = torch.complex128
NP_DTYPE = np.complex128
STAGE_DT = 0.08      # ODE integration duration per substage
RK4_STEPS_PER_STAGE = 8


def _np_matrix(value: Any) -> np.ndarray:
    """Convert canonical torch specs or local arrays into EngineCore's NumPy boundary."""
    if isinstance(value, np.ndarray):
        return value.astype(NP_DTYPE)
    return torch.as_tensor(value, dtype=TORCH_DTYPE).detach().cpu().numpy().astype(NP_DTYPE)


def _matrix_exp(value: Any) -> np.ndarray:
    """Small complex matrix exponential via torch, returned at the NumPy boundary."""
    tensor = torch.as_tensor(value, dtype=TORCH_DTYPE)
    return torch.linalg.matrix_exp(tensor).detach().cpu().numpy().astype(NP_DTYPE)


I2 = _np_matrix(CANON_I2)
SX = _np_matrix(CANON_SX)
SY = _np_matrix(CANON_SY)
SZ = _np_matrix(CANON_SZ)
SIGMA_MINUS = _np_matrix(CANON_SIGMA_MINUS)
SIGMA_PLUS = _np_matrix(CANON_SIGMA_PLUS)
H_TYPE_ONE = _np_matrix(CANON_H_TYPE_ONE)
H_TYPE_TWO = _np_matrix(CANON_H_TYPE_TWO)
OPERATOR_GENERATORS = {
    name: _np_matrix(generator)
    for name, generator in CANON_OPERATOR_GENERATORS.items()
}


# ---------------------------------------------------------------------------
# Density-matrix helpers
# ---------------------------------------------------------------------------

def _normalize_density(rho: np.ndarray) -> np.ndarray:
    """Project to Hermitian, clip negative eigenvalues, renormalize trace to 1."""
    rho = _np_matrix(rho)
    rho_h = (rho + rho.conj().T) / 2
    vals, vecs = np.linalg.eigh(rho_h)
    vals = np.maximum(vals.real, 1e-15)
    out = vecs @ np.diag(vals.astype(NP_DTYPE)) @ vecs.conj().T
    tr = np.trace(out).real
    if tr < 1e-30:
        return np.eye(2, dtype=NP_DTYPE) / 2
    return out / tr


def _is_valid_density(rho: np.ndarray) -> bool:
    rho = _np_matrix(rho)
    if not np.allclose(rho, rho.conj().T, atol=1e-9):
        return False
    if abs(np.trace(rho).real - 1.0) > 1e-8:
        return False
    eigs = np.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    return bool(np.min(eigs) > -1e-8)


def _state_to_density(psi: np.ndarray) -> np.ndarray:
    """Pure state |ψ⟩ → ρ = |ψ⟩⟨ψ|."""
    psi = _np_matrix(psi)
    psi = psi.reshape(-1, 1).astype(NP_DTYPE)
    norm = float(np.linalg.norm(psi))
    if norm < 1e-30:
        return np.eye(2, dtype=NP_DTYPE) / 2
    psi = psi / norm
    return psi @ psi.conj().T


def _density_to_state(rho: np.ndarray) -> np.ndarray:
    """ρ → dominant eigenvector (for mixed ρ, returns the highest-weight pure component)."""
    rho = _np_matrix(rho)
    rho_h = (rho + rho.conj().T) / 2
    vals, vecs = np.linalg.eigh(rho_h)
    # Highest eigenvalue is last
    return vecs[:, -1].astype(NP_DTYPE)


def _bloch_vector(rho: np.ndarray) -> np.ndarray:
    """Real Bloch vector (r_x, r_y, r_z) for a 2-dim density matrix."""
    return np.array([
        float(np.real(np.trace(SX @ rho))),
        float(np.real(np.trace(SY @ rho))),
        float(np.real(np.trace(SZ @ rho))),
    ], dtype=np.float64)


def _von_neumann_entropy(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    eigs = np.clip(eigs, 1e-15, 1.0)
    eigs = eigs / eigs.sum()
    return float(-(eigs * np.log(eigs)).sum())


def _purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def _density_hash(rho: np.ndarray) -> str:
    """Stable short hash for a 2x2 density, rounded before hashing."""
    rho = _normalize_density(rho)
    payload = np.round(
        np.concatenate([rho.real.reshape(-1), rho.imag.reshape(-1)]),
        decimals=12,
    ).astype(np.float64)
    return hashlib.sha256(payload.tobytes()).hexdigest()[:16]


def _density_model_payload(rho: np.ndarray) -> dict[str, Any]:
    """JSON-safe executable density payload for science-method stage records.

    Patch B (wizard auto-loop iter 1): exposes carrier_rank to make the
    rank-1 Bloch sub-block reality (per Opus rank-1 audit) visible at every
    emit point. Additive change — existing consumers unaffected.
    """
    rho = _normalize_density(rho)
    eigs = np.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    carrier_rank = int(np.sum(eigs > 1e-10))
    return {
        "density_real": rho.real.tolist(),
        "density_imag": rho.imag.tolist(),
        "density_hash": _density_hash(rho),
        "bloch": _bloch_vector(rho).tolist(),
        "entropy": _von_neumann_entropy(rho),
        "purity": _purity(rho),
        "eigenvalues": eigs.tolist(),
        "valid_density": _is_valid_density(rho),
        "carrier_dim": int(rho.shape[0]),
        "carrier_rank": carrier_rank,
        "is_rank_one": bool(carrier_rank == 1),
    }


def _pauli_observation_distribution(rho: np.ndarray) -> list[float]:
    """Finite sensory projection over +/- Z, +/- X, +/- Y projectors."""
    rho = _normalize_density(rho)
    projectors = []
    for sigma in (SZ, SX, SY):
        projectors.append(0.5 * (I2 + sigma))
        projectors.append(0.5 * (I2 - sigma))
    probs = np.array([float(np.real(np.trace(p @ rho))) for p in projectors], dtype=float)
    probs = np.clip(probs, 1e-12, None)
    probs = probs / float(np.sum(probs))
    return probs.tolist()


def _kl_prob(p: list[float] | np.ndarray, q: list[float] | np.ndarray) -> float:
    p_arr = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    q_arr = np.clip(np.asarray(q, dtype=float), 1e-12, None)
    p_arr = p_arr / float(np.sum(p_arr))
    q_arr = q_arr / float(np.sum(q_arr))
    return float(np.sum(p_arr * (np.log(p_arr) - np.log(q_arr))))


def _entropy_prob(p: list[float] | np.ndarray) -> float:
    p_arr = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    p_arr = p_arr / float(np.sum(p_arr))
    return float(-np.sum(p_arr * np.log(p_arr)))


def _next_policy_payload(
    engine_type: int,
    schedule: list[tuple[str, str]],
    main_stage_idx: int,
    substage_idx: int,
) -> dict[str, Any]:
    """Finite next-slot policy pointer; future is schedule-local, not primitive time."""
    if substage_idx + 1 < N_SUBSTAGES_PER_MAIN:
        next_main = main_stage_idx
        next_substage = substage_idx + 1
    else:
        next_main = (main_stage_idx + 1) % len(schedule)
        next_substage = 0
    perception, loop_class = schedule[next_main]
    next_slot = get_operator_slot_spec(perception, engine_type, loop_class, next_substage)
    return {
        "policy_id": f"E{engine_type}:stage_{next_main:02d}:slot_{next_substage}",
        "engine_type": engine_type,
        "main_stage_idx": next_main,
        "substage_idx": next_substage,
        "perception": perception,
        "loop_class": loop_class,
        "operator": next_slot["operator"],
        "operator_sign": int(next_slot["sign"]),
        "ordered_token": next_slot["token"],
        "selection_rule": "deterministic_source_native_schedule_next_slot",
    }


def _science_method_fields(
    *,
    model_before: np.ndarray,
    predicted_pre_manifold: np.ndarray,
    model_after: np.ndarray,
    after_manifold: np.ndarray,
    before_loop: np.ndarray,
    slot: dict[str, Any],
    engine_type: int,
    schedule: list[tuple[str, str]],
    main_stage_idx: int,
    substage_idx: int,
    manifold_called_count: int,
    manifold_applied_count: int,
    manifold_satisfied_count: int,
) -> dict[str, Any]:
    """Executable science-method/FEP payload attached to every substage.

    Patch A (wizard auto-loop iter 2): decomposes surprise into manifold-step
    vs loop-placement-step so EFE can be attributed to the right transformation.
    Previously prediction was pre-manifold and observation was post-manifold-AND-post-loop,
    conflating two factors in a single KL.
    """
    predicted_obs = _pauli_observation_distribution(predicted_pre_manifold)
    observed_obs = _pauli_observation_distribution(model_after)
    manifold_only_obs = _pauli_observation_distribution(after_manifold)
    prediction_l2 = float(np.linalg.norm(np.asarray(observed_obs) - np.asarray(predicted_obs)))
    surprise_kl = _kl_prob(observed_obs, predicted_obs)
    surprise_kl_manifold_step = _kl_prob(manifold_only_obs, predicted_obs)
    surprise_kl_loop_step = _kl_prob(observed_obs, manifold_only_obs)
    ambiguity = _entropy_prob(observed_obs)
    correction_delta = float(np.linalg.norm(after_manifold - predicted_pre_manifold))
    loop_delta = float(np.linalg.norm(model_after - before_loop))
    return {
        "model_before": _density_model_payload(model_before),
        "prediction": {
            "kind": "operator_terrain_pre_manifold_counterfactual",
            "model": _density_model_payload(predicted_pre_manifold),
            "observation_distribution": predicted_obs,
            "observable_basis": ["Z+", "Z-", "X+", "X-", "Y+", "Y-"],
        },
        "observation": {
            "kind": "post_manifold_loop_placement_observation",
            "model": _density_model_payload(model_after),
            "observation_distribution": observed_obs,
            "observable_basis": ["Z+", "Z-", "X+", "X-", "Y+", "Y-"],
        },
        "manifold_intermediate": {
            "kind": "post_manifold_pre_loop_intermediate",
            "model": _density_model_payload(after_manifold),
            "observation_distribution": manifold_only_obs,
            "observable_basis": ["Z+", "Z-", "X+", "X-", "Y+", "Y-"],
            "note": "Patch C (iter 4a): expose post-manifold-pre-loop density so rank-collapse-at-manifold predicates are testable directly without relying on loop-rank-preservation",
        },
        "fep_efe_score": {
            "formula": "KL(observation || prediction) + H(observation)",
            "surprise_kl": surprise_kl,
            "surprise_kl_manifold_step": surprise_kl_manifold_step,
            "surprise_kl_loop_step": surprise_kl_loop_step,
            "surprise_decomposition_note": "manifold_step + loop_step may differ from total_surprise because KL is not additive over composed channels; both are non-negative and attribute surprise to manifold vs loop_placement separately",
            "ambiguity_entropy": ambiguity,
            "expected_free_energy_proxy": float(surprise_kl + ambiguity),
            "prediction_error_l2": prediction_l2,
            "load_bearing_observable": "finite_scalar_boundary_pauli_projection_distribution",
            "boundary_evidence_scope": "EngineCore finite-scalar boundary evidence only; not source-native nonclassical proof.",
        },
        "update_repair": {
            "kind": "manifold_projection_then_loop_placement",
            "manifold_projection_delta_norm": correction_delta,
            "loop_placement_delta_norm": loop_delta,
            "manifold_called_count": manifold_called_count,
            "manifold_applied_count": manifold_applied_count,
            "manifold_satisfied_count": manifold_satisfied_count,
            "correction_active": correction_delta > 1e-12 or loop_delta > 1e-12,
        },
        "falsifier_graveyard": {
            "matched_controls_required_downstream": [
                "manifold_disabled_control",
                "operator_sign_collapse_control",
                "identity_history_control",
            ],
            "slot_contract": {
                "operator": slot["operator"],
                "operator_sign": int(slot["sign"]),
                "precedence": slot["precedence"],
                "ordered_token": slot["token"],
                "is_native_operator": bool(slot["is_native_operator"]),
            },
        },
        "next_policy": _next_policy_payload(engine_type, schedule, main_stage_idx, substage_idx),
        "model_after": _density_model_payload(model_after),
        "science_method_fields_version": "science_method_stage_record_v1",
    }


# ---------------------------------------------------------------------------
# Lindblad ODE right-hand side
# ---------------------------------------------------------------------------

def _lindblad_rhs(t: float, rho_flat: np.ndarray, H: np.ndarray, L: np.ndarray) -> np.ndarray:
    """
    Right-hand side of the Lindblad equation in vectorized form.
        dρ/dt = -i [H, ρ] + L ρ L† - ½ {L†L, ρ}

    rho_flat is a length-4 complex vector (2x2 density flattened row-major).
    Returns the flattened derivative (length-4 complex).
    """
    rho = rho_flat.reshape(2, 2).astype(NP_DTYPE)
    Ldag_L = L.conj().T @ L
    commutator = H @ rho - rho @ H
    dissipator = L @ rho @ L.conj().T - 0.5 * (Ldag_L @ rho + rho @ Ldag_L)
    drho = -1j * commutator + dissipator
    return drho.reshape(-1)


def lindblad_step(
    rho: np.ndarray,
    H: np.ndarray,
    L: np.ndarray,
    dt: float,
) -> np.ndarray:
    """
    Integrate dρ/dt = -i[H,ρ] + LρL† - ½{L†L,ρ} for time dt.

    Uses a fixed-step RK4 integrator for the finite 2x2 stage carrier. Returns
    the evolved and renormalized density matrix.
    """
    rho = _np_matrix(rho)
    H = _np_matrix(H)
    L = _np_matrix(L)
    y = rho.reshape(-1).astype(NP_DTYPE)
    n_steps = max(1, int(math.ceil(abs(float(dt)) / STAGE_DT * RK4_STEPS_PER_STAGE)))
    h = float(dt) / float(n_steps)
    t = 0.0
    for _ in range(n_steps):
        k1 = _lindblad_rhs(t, y, H, L)
        k2 = _lindblad_rhs(t + 0.5 * h, y + 0.5 * h * k1, H, L)
        k3 = _lindblad_rhs(t + 0.5 * h, y + 0.5 * h * k2, H, L)
        k4 = _lindblad_rhs(t + h, y + h * k3, H, L)
        y = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += h
    rho_final = y.reshape(2, 2)
    return _normalize_density(rho_final)


# ---------------------------------------------------------------------------
# Operator unitary
# ---------------------------------------------------------------------------

def _operator_unitary(op_name: str, sign: int) -> np.ndarray:
    """
    Build the 2x2 operator unitary U = exp(-i * sign * theta_base * G_op).
    """
    G = OPERATOR_GENERATORS[op_name]
    theta = OPERATOR_BASE_ANGLES[op_name] * float(sign)
    U = _matrix_exp(-1j * theta * G)
    return U.astype(NP_DTYPE)


def apply_operator_to_density(
    rho: np.ndarray,
    op_name: str,
    sign: int,
) -> np.ndarray:
    """Apply U ρ U† for the named operator."""
    U = _operator_unitary(op_name, sign)
    return _normalize_density(U @ rho @ U.conj().T)


def apply_operator_map_family_to_density(
    rho: np.ndarray,
    op_name: str,
    sign: int,
    dt: float = STAGE_DT,
) -> np.ndarray:
    """Apply the finite operator map family, not just a unitary kick."""
    if op_name == "Ti":
        return _normalize_density((1.0 - 0.18) * rho + 0.18 * _pinch(rho, "z"))
    if op_name == "Te":
        return _normalize_density((1.0 - 0.20) * rho + 0.20 * _pinch(rho, "x"))
    if op_name == "Fi":
        angle = sign * 0.23 * dt / STAGE_DT
        U = _matrix_exp(-1j * angle * SX / 2)
        return _normalize_density(U @ rho @ U.conj().T)
    if op_name == "Fe":
        angle = sign * 0.21 * dt / STAGE_DT
        U = _matrix_exp(-1j * angle * SZ / 2)
        return _normalize_density(U @ rho @ U.conj().T)
    raise ValueError(f"unknown operator {op_name!r}")


def _projectors_for_axis(axis: str) -> tuple[np.ndarray, np.ndarray]:
    if axis == "x":
        return 0.5 * (I2 + SX), 0.5 * (I2 - SX)
    if axis == "y":
        return 0.5 * (I2 + SY), 0.5 * (I2 - SY)
    if axis == "z":
        return 0.5 * (I2 + SZ), 0.5 * (I2 - SZ)
    raise ValueError(f"Unknown projector axis: {axis}")


def _pinch(rho: np.ndarray, axis: str) -> np.ndarray:
    p0, p1 = _projectors_for_axis(axis)
    return _normalize_density(p0 @ rho @ p0 + p1 @ rho @ p1)


def _kraus_filter(rho: np.ndarray, axis: str, strength: float, release: bool = False) -> np.ndarray:
    p0, p1 = _projectors_for_axis(axis)
    if release:
        filt = math.sqrt(max(1.0 - strength, 1e-9)) * p0 + math.sqrt(1.0 + strength) * p1
    else:
        filt = math.sqrt(1.0 + strength) * p0 + math.sqrt(max(1.0 - strength, 1e-9)) * p1
    return _normalize_density(filt @ rho @ filt.conj().T)


def apply_terrain_dynamics_to_density(
    rho: np.ndarray,
    perception: str,
    engine_type: int,
    dt: float = STAGE_DT,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Apply the topology-law dynamical family for one main stage.

    This is deliberately richer than a single Lindblad dispatch:
      - pinching_projection: convex flow toward Π_P(ρ)
      - kraus_filter / kraus_release: normalized Kraus filtering
      - lowering_dissipator / raising_dissipator: σ_- / σ_+ Lindblad flow
      - outward_projection: reversed-H projection flow
      - pinching_dissipator: dissipator toward the pinched state under H_S
    """
    spec = get_terrain_dynamics_spec(perception, engine_type)
    family = spec["family"]
    axis = spec["projector_axis"]
    rate = float(spec["rate"])
    H = _np_matrix(spec["hamiltonian"])
    chirality_sign = +1.0 if engine_type == 0 else -1.0
    before = rho.copy()

    if family == "pinching_projection":
        target = _pinch(rho, axis)
        rho = _normalize_density((1.0 - rate) * rho + rate * target)
        U = _matrix_exp(-1j * 0.12 * dt * H)
        rho = _normalize_density(U @ rho @ U.conj().T)
    elif family == "kraus_filter":
        filtered = _kraus_filter(rho, axis, min(0.42, 1.6 * rate), release=False)
        rho = _normalize_density((1.0 - 0.35) * rho + 0.35 * filtered)
        U = _matrix_exp(-1j * dt * H)
        rho = _normalize_density(U @ rho @ U.conj().T)
    elif family == "lowering_dissipator":
        rho = lindblad_step(rho, H, SIGMA_MINUS, dt * (1.0 + rate))
    elif family == "kraus_release":
        filtered = _kraus_filter(rho, axis, min(0.42, 1.5 * rate), release=True)
        rho = _normalize_density((1.0 + 0.25 * rate) * rho - 0.25 * rate * filtered)
        U = _matrix_exp(1j * 0.7 * dt * H)
        rho = _normalize_density(U @ rho @ U.conj().T)
    elif family == "outward_projection":
        target = _pinch(rho, axis)
        rho = _normalize_density((1.0 - 0.55 * rate) * rho + 0.55 * rate * target)
        U = _matrix_exp(1j * dt * H)
        rho = _normalize_density(U @ rho @ U.conj().T)
    elif family == "raising_dissipator":
        rho = lindblad_step(rho, H, SIGMA_PLUS, dt * (1.0 + rate))
    elif family == "pinching_dissipator":
        target = _pinch(rho, axis)
        rho = _normalize_density((1.0 - rate) * rho + rate * target)
        U = _matrix_exp(-1j * chirality_sign * 0.5 * dt * H)
        rho = _normalize_density(U @ rho @ U.conj().T)
    else:
        raise ValueError(f"unknown terrain dynamics family {family!r}")

    return rho, {
        "terrain_realization": spec["realization"],
        "terrain_dynamics_family": family,
        "hamiltonian_key": spec["hamiltonian_key"],
        "terrain_rate": rate,
        "terrain_delta_norm": float(np.linalg.norm(rho - before)),
    }


# ---------------------------------------------------------------------------
# Manifold constraint application — bridge ρ ↔ ψ embedding
# ---------------------------------------------------------------------------

def _embed_density_in_higher_dim(rho: np.ndarray, dim: int = 16) -> torch.Tensor:
    """
    Embed the 2-dim density's dominant eigenvector into a higher-dim pure state
    for the 13-layer manifold enforcers (which expect higher-dim states for some
    layers, especially layer 11 tensor product coupling).

    dim must be a power of 2 (here 16 = 4 qubits).
    The 2-dim eigenvector occupies the first 2 components; the rest is small
    random padding (deterministic via fixed seed for reproducibility).
    """
    psi_2 = _density_to_state(rho)
    psi = np.zeros(dim, dtype=NP_DTYPE)
    psi[:2] = psi_2
    # Small padding to keep dim well-defined (deterministic, small magnitude)
    rng = np.random.default_rng(0)
    pad = (rng.normal(size=dim - 2) + 1j * rng.normal(size=dim - 2)) * 0.01
    psi[2:] = pad
    norm = float(np.linalg.norm(psi))
    if norm < 1e-30:
        psi[0] = 1.0
    else:
        psi = psi / norm
    return torch.tensor(psi, dtype=TORCH_DTYPE)


def _project_back_to_density(psi_higher: torch.Tensor) -> np.ndarray:
    """
    Extract the 2-dim density from a higher-dim pure state by tracing out
    all but the first 2 components, then normalizing.
    """
    psi_np = psi_higher.detach().cpu().numpy().astype(NP_DTYPE)
    # Take the first 2 components, normalize, build density
    psi_2 = psi_np[:2]
    norm = float(np.linalg.norm(psi_2))
    if norm < 1e-30:
        return np.eye(2, dtype=NP_DTYPE) / 2
    psi_2 = psi_2 / norm
    return _normalize_density(psi_2.reshape(-1, 1) @ psi_2.reshape(1, -1).conj())


def apply_manifold_to_density(
    rho: np.ndarray,
    global_step: int,
    context: dict,
) -> tuple[np.ndarray, dict[str, dict]]:
    """
    Apply all 13 manifold layer constraints to a 2-dim density.
    Bridges via higher-dim embedding to satisfy layer 11 (tensor product
    coupling) which requires a power-of-2-dim qubit state.
    """
    psi_higher = _embed_density_in_higher_dim(rho, dim=16)
    psi_constrained, metrics = apply_all_layer_constraints(psi_higher, global_step, context)
    rho_constrained = _project_back_to_density(psi_constrained)
    return rho_constrained, metrics


# ---------------------------------------------------------------------------
# EngineCore class
# ---------------------------------------------------------------------------

class EngineCore:
    """
    Operational QIT engine running 4 operator slots on each topology-loop stage
    with topology dynamics, loop placement, and 13-layer manifold constraints
    on a 2-dim density carrier.

    engine_type: 0 (Type 1 / left Weyl) or 1 (Type 2 / right Weyl)

    Per main stage (4 substages):
      substage 0..3: Ti/Te/Fi/Fe operator slot over the same topology-loop
      placement. Each slot applies operator and topology dynamics in the slot's
      precedence order, then manifold constraints, then loop placement.

    8 main stages per engine = 32 substages per engine.
    """

    def __init__(self, engine_type: int, *, manifold_enabled: bool = True):
        if engine_type not in (0, 1):
            raise ValueError(f"engine_type must be 0 or 1, got {engine_type}")
        self.engine_type = engine_type
        self.spec = get_engine_spec(engine_type)
        self.schedule = self.spec["schedule"]
        self.manifold_enabled = manifold_enabled
        self.manifold_context: dict = {}
        self.global_step = 0

    # -- run a single substage -----------------------------------------------

    def _apply_terrain_dephase(self, rho: np.ndarray, perception: str) -> np.ndarray:
        """Terrain-projection dephase along the topology's projector axis."""
        topo = get_topology_spec(perception, self.engine_type)
        axis = topo["projector_axis"]
        rate = float(topo["rate"])
        if axis == "x":
            P0, P1 = 0.5 * (I2 + SX), 0.5 * (I2 - SX)
        elif axis == "y":
            P0, P1 = 0.5 * (I2 + SY), 0.5 * (I2 - SY)
        elif axis == "z":
            P0, P1 = 0.5 * (I2 + SZ), 0.5 * (I2 - SZ)
        else:
            raise ValueError(f"Unknown axis: {axis}")
        pinched = P0 @ rho @ P0 + P1 @ rho @ P1
        return _normalize_density((1 - rate) * rho + rate * pinched)

    def _apply_loop_placement(
        self,
        rho: np.ndarray,
        main_stage_idx: int,
        loop_class: str,
    ) -> np.ndarray:
        """Apply a Hopf loop-placement rotation (outer = base_lift, inner = fiber)."""
        chirality_sign = self.spec["chirality_sign"]
        u = (main_stage_idx + 1) * (2.0 * math.pi / 9.0)
        if loop_class == "outer":
            # base_lift_loop: SX-dominated mixing
            G = (0.75 * SX + 0.25 * SZ) * (0.071 * chirality_sign * u)
        else:
            # fiber_loop: SZ-dominated phase
            G = SZ * (0.035 * chirality_sign * u)
        U = _matrix_exp(-1j * G)
        return _normalize_density(U @ rho @ U.conj().T)

    def run_substage(
        self,
        rho: np.ndarray,
        perception: str,
        loop_class: str,
        main_stage_idx: int,
        substage_idx: int,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Run one operator slot within a topology-loop stage.
        """
        slot = get_operator_slot_spec(perception, self.engine_type, loop_class, substage_idx)
        op_name = slot["operator"]
        sign = int(slot["sign"])
        action = ""
        manifold_metrics: dict[str, dict] = {}
        terrain_metrics: dict[str, Any] = {}

        action = "operator_terrain_manifold_slot"
        before_slot = rho.copy()
        if slot["precedence"] == "operator_first":
            rho = apply_operator_map_family_to_density(rho, op_name, sign, STAGE_DT)
            rho, terrain_metrics = apply_terrain_dynamics_to_density(
                rho, perception, self.engine_type, STAGE_DT
            )
        else:
            rho, terrain_metrics = apply_terrain_dynamics_to_density(
                rho, perception, self.engine_type, STAGE_DT
            )
            rho = apply_operator_map_family_to_density(rho, op_name, sign, STAGE_DT)
        predicted_pre_manifold = rho.copy()
        if self.manifold_enabled:
            rho, manifold_metrics = apply_manifold_to_density(
                rho, self.global_step, self.manifold_context
            )
        else:
            manifold_metrics = {name: {"applied": False, "skipped": True}
                                for name in MANIFOLD_LAYERS}
        after_manifold = rho.copy()
        before_loop = rho.copy()
        rho = self._apply_loop_placement(rho, main_stage_idx, loop_class)
        slot_delta = float(np.linalg.norm(rho - before_slot))
        manifold_called_count = len(manifold_metrics)
        manifold_applied_count = sum(
            1 for m in manifold_metrics.values()
            if isinstance(m, dict) and m.get("applied", False)
        ) if manifold_metrics else 0
        manifold_satisfied_count = sum(
            1 for m in manifold_metrics.values()
            if isinstance(m, dict) and m.get("constraint_satisfied", False)
        ) if manifold_metrics else 0

        self.global_step += 1
        science_method_fields = _science_method_fields(
            model_before=before_slot,
            predicted_pre_manifold=predicted_pre_manifold,
            model_after=rho,
            after_manifold=after_manifold,
            before_loop=before_loop,
            slot=slot,
            engine_type=self.engine_type,
            schedule=self.schedule,
            main_stage_idx=main_stage_idx,
            substage_idx=substage_idx,
            manifold_called_count=manifold_called_count,
            manifold_applied_count=manifold_applied_count,
            manifold_satisfied_count=manifold_satisfied_count,
        )
        record = {
            "engine_type": self.engine_type,
            "type_label": self.spec["type_label"],
            "main_stage_idx": main_stage_idx,
            "substage_idx": substage_idx,
            "perception": perception,
            "loop_class": loop_class,
            "action": action,
            "operator": op_name,
            "operator_sign": sign,
            "axis6": slot["axis6"],
            "precedence": slot["precedence"],
            "ordered_token": slot["token"],
            "operator_family": slot["operator_family"],
            "is_native_operator": bool(slot["is_native_operator"]),
            "is_chart_locked": bool(slot["is_chart_locked"]),
            "native_operator_set": list(slot["native_operator_set"]),
            "slot_delta_norm": slot_delta,
            "global_step": self.global_step - 1,
            **terrain_metrics,
            "bloch": _bloch_vector(rho).tolist(),
            "entropy": _von_neumann_entropy(rho),
            "purity": _purity(rho),
            "valid_density": _is_valid_density(rho),
            "manifold_metrics": {
                name: {k: float(v) if isinstance(v, (int, float, np.floating, np.integer))
                       else (None if v is None else (str(v) if not isinstance(v, dict) else v))
                       for k, v in (m.items() if isinstance(m, dict) else [])}
                for name, m in manifold_metrics.items()
            },
            "manifold_applied": all(
                bool(m.get("applied", False) or m.get("constraint_satisfied", False))
                for m in manifold_metrics.values()
            ) if manifold_metrics else False,
            "manifold_called_count": manifold_called_count,
            "manifold_applied_count": manifold_applied_count,
            "manifold_satisfied_count": manifold_satisfied_count,
            "n_manifold_layers_active": manifold_applied_count,
            **science_method_fields,
        }
        return rho, record

    # -- run a main stage (4 substages) --------------------------------------

    def run_main_stage(
        self,
        rho: np.ndarray,
        perception: str,
        loop_class: str,
        main_stage_idx: int,
    ) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """Run 4 substages for one main stage."""
        records = []
        for substage_idx in range(N_SUBSTAGES_PER_MAIN):
            rho, record = self.run_substage(
                rho, perception, loop_class, main_stage_idx, substage_idx
            )
            records.append(record)
        return rho, records

    # -- run a full cycle (8 main stages = 32 substages) ---------------------

    def run_full_cycle(
        self,
        rho_init: np.ndarray,
    ) -> dict[str, Any]:
        """
        Run all 8 main stages × 4 substages = 32 substages.

        Returns:
          dict with keys:
            engine_type, type_label, initial_rho, final_rho,
            trajectory (list of 32 records), schedule_walked
        """
        rho = _normalize_density(rho_init.copy())
        trajectory: list[dict[str, Any]] = []
        schedule_walked = []
        for main_idx, (perception, loop_class) in enumerate(self.schedule):
            rho, records = self.run_main_stage(rho, perception, loop_class, main_idx)
            trajectory.extend(records)
            schedule_walked.append((perception, loop_class))

        assert len(trajectory) == N_TOTAL_SUBSTAGES_PER_ENGINE, (
            f"expected {N_TOTAL_SUBSTAGES_PER_ENGINE} substages, got {len(trajectory)}"
        )
        return {
            "engine_type": self.engine_type,
            "type_label": self.spec["type_label"],
            "initial_rho": rho_init.tolist(),
            "final_rho": rho.tolist(),
            "trajectory": trajectory,
            "schedule_walked": schedule_walked,
            "manifold_enabled": self.manifold_enabled,
            "n_substages": len(trajectory),
            "final_bloch": _bloch_vector(rho).tolist(),
            "final_entropy": _von_neumann_entropy(rho),
            "final_purity": _purity(rho),
            "final_valid_density": _is_valid_density(rho),
        }


# ---------------------------------------------------------------------------
# Initial-state generator helper
# ---------------------------------------------------------------------------

def generate_initial_density(seed: int) -> np.ndarray:
    """Generate a deterministic 2-dim density matrix from a seed."""
    rng = np.random.default_rng(seed)
    theta = 0.24 + 1.05 * rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = np.array([
        math.cos(theta),
        math.sin(theta) * np.exp(1j * phi),
    ], dtype=NP_DTYPE).reshape(-1, 1)
    pure = psi @ psi.conj().T
    return _normalize_density(0.88 * pure + 0.12 * I2 / 2)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("engine_core.py — smoke test")
    print("=" * 70)

    # 1. Test Lindblad step preserves trace and PSD
    print("\n1. Lindblad ODE step smoke test")
    rho0 = generate_initial_density(7)
    H = H_TYPE_ONE
    L = SIGMA_MINUS
    rho1 = lindblad_step(rho0, H, L, 0.08)
    print(f"   trace before: {np.trace(rho0).real:.6f}  "
          f"trace after: {np.trace(rho1).real:.6f}")
    print(f"   valid before: {_is_valid_density(rho0)}  "
          f"valid after: {_is_valid_density(rho1)}")
    assert _is_valid_density(rho1), "Lindblad step broke density validity"

    # 2. Test operator unitary application
    print("\n2. Operator unitary smoke test")
    for op_name in ["Ti", "Te", "Fi", "Fe"]:
        rho_op = apply_operator_to_density(rho0, op_name, +1)
        print(f"   {op_name}: trace={np.trace(rho_op).real:.6f}  "
              f"valid={_is_valid_density(rho_op)}")
        assert _is_valid_density(rho_op), f"Operator {op_name} broke density validity"

    # 3. Test manifold layer application
    print("\n3. Manifold-layer application smoke test")
    context = {}
    rho_m, metrics = apply_manifold_to_density(rho0, 0, context)
    n_applied = sum(1 for m in metrics.values() if m.get("applied", False))
    print(f"   {n_applied}/{len(metrics)} layers reported applied")
    print(f"   valid after manifold: {_is_valid_density(rho_m)}")
    assert _is_valid_density(rho_m), "Manifold broke density validity"

    # 4. Test EngineCore full cycle
    print("\n4. EngineCore full cycle smoke test (Type 1)")
    eng = EngineCore(engine_type=0)
    result = eng.run_full_cycle(rho0)
    print(f"   n_substages: {result['n_substages']} (expected 32)")
    print(f"   manifold_enabled: {result['manifold_enabled']}")
    print(f"   final_valid: {result['final_valid_density']}")
    print(f"   final_bloch: {[round(x, 4) for x in result['final_bloch']]}")
    print(f"   final_entropy: {result['final_entropy']:.4f}")
    n_valid = sum(1 for r in result["trajectory"] if r["valid_density"])
    print(f"   valid_substages: {n_valid}/32")

    # 5. Test EngineCore Type 2 full cycle
    print("\n5. EngineCore full cycle smoke test (Type 2)")
    eng2 = EngineCore(engine_type=1)
    result2 = eng2.run_full_cycle(rho0)
    print(f"   n_substages: {result2['n_substages']}")
    print(f"   final_bloch: {[round(x, 4) for x in result2['final_bloch']]}")

    # 6. Confirm Type 1 vs Type 2 produce different trajectories on same init
    diff = float(np.linalg.norm(
        np.array(result["final_rho"]) - np.array(result2["final_rho"]),
        "fro"
    ))
    print(f"\n6. Type 1 vs Type 2 final density diff (Frobenius): {diff:.6f}")
    assert diff > 1e-6, "Type 1 and Type 2 should differ after a full cycle"

    # 7. Confirm operator names in trajectory cover the expected set
    ops_walked = sorted({r["operator"] for r in result["trajectory"]})
    print(f"\n7. Operators walked in Type 1 trajectory: {ops_walked}")
    assert set(ops_walked) == {"Ti", "Te", "Fi", "Fe"}, f"Missing operators: {ops_walked}"

    # 8. Verify 8 unique (op, sign) pairs per engine via run records
    sub0_records = [r for r in result["trajectory"] if r["substage_idx"] == 0]
    op_sign_pairs = sorted({(r["operator"], r["operator_sign"]) for r in sub0_records})
    print(f"\n8. Unique (op,sign) pairs in Type 1 substage_0 records: "
          f"{len(op_sign_pairs)} (expected 8)")
    assert len(op_sign_pairs) == 8, f"expected 8 unique (op,sign), got {len(op_sign_pairs)}"
    print(f"   pairs: {op_sign_pairs}")

    print("\n" + "=" * 70)
    print("engine_core.py SMOKE TEST PASS")
    print("=" * 70)
