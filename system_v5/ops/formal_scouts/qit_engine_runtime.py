#!/usr/bin/env python3
"""Shared QIT terrain/engine/schedule runtime helpers.

This module centralizes the exact torch single-qubit Liouvillian runtime used by
the D90-D92 two-root QIT engine scouts. It is intentionally small: it owns the
terrain-stage channels, Type-1/Type-2 engine composition, schedule composition,
fixed-point readouts, spectra, and clustering utilities. Higher-level scouts own
their receipts, controls, and claim ceilings.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Iterable

import torch

import canonical_qit_engine_specs as specs


DTYPE = torch.complex128
I2 = specs.I2
SX = specs.SX
SY = specs.SY
SZ = specs.SZ
SM = specs.SIGMA_MINUS
SP = specs.SIGMA_PLUS
P_PLUS = 0.5 * (I2 + SZ)
P_MINUS = 0.5 * (I2 - SZ)

DEFAULT_TAU = 1.0
FIXED_TOL = 1.0e-7
SPREAD_TOL = 1.0e-4
GAP_TOL = 1.0e-7
DEFAULT_CYCLES = 80
DEFAULT_FIXED_ITERATIONS = 240

DEFAULT_DIRECTIONS: dict[str, tuple[float, float, float]] = {
    "iter176_xz": (0.7, 0.0, 0.5),
    "x": (1.0, 0.0, 0.0),
    "y": (0.0, 1.0, 0.0),
    "z": (0.0, 0.0, 1.0),
    "xy": (1.0, 1.0, 0.0),
    "xz": (1.0, 0.0, 1.0),
    "yz": (0.0, 1.0, 1.0),
    "xyz": (1.0, 1.0, 1.0),
}

ENGINE_STAGE_ORDERS: dict[str, dict[str, list[str]]] = {
    "L": {
        "inner": ["Se", "Si", "Ni", "Ne"],
        "outer": ["Se", "Ne", "Ni", "Si"],
    },
    "R": {
        "inner": ["Se", "Ne", "Ni", "Si"],
        "outer": ["Se", "Si", "Ni", "Ne"],
    },
}


def row_major_liouvillian(H: torch.Tensor, collapse_ops: list[torch.Tensor]) -> torch.Tensor:
    eye = torch.eye(2, dtype=DTYPE)
    Ht = H.T.contiguous()
    superop = -1j * (torch.kron(H, eye) - torch.kron(eye, Ht))
    for collapse in collapse_ops:
        K = collapse.conj().T @ collapse
        Kt = K.T.contiguous()
        superop = superop + torch.kron(collapse, collapse.conj()) - 0.5 * (
            torch.kron(K, eye) + torch.kron(eye, Kt)
        )
    return superop


def stage_channel(
    H: torch.Tensor,
    collapse_ops: list[torch.Tensor],
    tau: float = DEFAULT_TAU,
) -> torch.Tensor:
    return torch.linalg.matrix_exp(float(tau) * row_major_liouvillian(H, collapse_ops))


def compose(channels: Iterable[torch.Tensor]) -> torch.Tensor:
    out = torch.eye(4, dtype=DTYPE)
    for channel in channels:
        out = channel @ out
    return out


def bloch(rho: torch.Tensor) -> list[float]:
    return [
        float(torch.trace(rho @ SX).real.item()),
        float(torch.trace(rho @ SY).real.item()),
        float(torch.trace(rho @ SZ).real.item()),
    ]


def rho_from_bloch(vector: tuple[float, float, float]) -> torch.Tensor:
    return 0.5 * (I2 + vector[0] * SX + vector[1] * SY + vector[2] * SZ)


INITIAL_STATES: list[torch.Tensor] = [
    rho_from_bloch((1.0, 0.0, 0.0)),
    rho_from_bloch((-1.0, 0.0, 0.0)),
    rho_from_bloch((0.0, 1.0, 0.0)),
    rho_from_bloch((0.0, -1.0, 0.0)),
    rho_from_bloch((0.0, 0.0, 1.0)),
    rho_from_bloch((0.0, 0.0, -1.0)),
    0.5 * I2,
]


def vec(rho: torch.Tensor) -> torch.Tensor:
    return rho.reshape(4)


def mat(vector: torch.Tensor) -> torch.Tensor:
    return vector.reshape(2, 2)


def normalize_direction(raw: tuple[float, float, float]) -> torch.Tensor:
    tensor = torch.tensor(raw, dtype=torch.float64)
    norm = torch.linalg.vector_norm(tensor)
    if float(norm.item()) == 0.0:
        raise ValueError("zero direction not allowed")
    tensor = tensor / norm
    return tensor[0] * SX + tensor[1] * SY + tensor[2] * SZ


def direction_hamiltonian(
    direction: str | tuple[float, float, float],
    *,
    normalize: bool = True,
    directions: dict[str, tuple[float, float, float]] | None = None,
) -> torch.Tensor:
    direction_map = directions or DEFAULT_DIRECTIONS
    raw = direction_map[direction] if isinstance(direction, str) else direction
    if normalize:
        return normalize_direction(raw)
    return raw[0] * SX + raw[1] * SY + raw[2] * SZ


def terrain_stage_channels(
    sheet: str,
    H0: torch.Tensor,
    *,
    tau: float = DEFAULT_TAU,
    rate_scale: float = 1.0,
    ladder_scale: float = 1.0,
    dephase_scale: float = 1.0,
) -> dict[str, torch.Tensor]:
    if sheet not in ENGINE_STAGE_ORDERS:
        raise ValueError(f"sheet must be one of {sorted(ENGINE_STAGE_ORDERS)}, got {sheet!r}")
    H = H0 if sheet == "L" else -H0
    ladder = SM if sheet == "L" else SP
    eps_f = 0.1
    eps_v = 0.3
    eps_p = 0.1
    gamma_p = 0.5 * rate_scale * ladder_scale
    kappa_h = 0.3 * rate_scale * dephase_scale
    se_rate = 1.0 * rate_scale * dephase_scale
    ne_rate = eps_v * rate_scale * dephase_scale
    return {
        "Se": stage_channel(eps_f * H, [math.sqrt(se_rate) * SZ] if se_rate > 0 else [], tau=tau),
        "Ne": stage_channel(H, [math.sqrt(ne_rate) * SX] if ne_rate > 0 else [], tau=tau),
        "Ni": stage_channel(eps_p * H, [math.sqrt(gamma_p) * ladder] if gamma_p > 0 else [], tau=tau),
        "Si": stage_channel(
            H,
            [math.sqrt(kappa_h) * P_PLUS, math.sqrt(kappa_h) * P_MINUS] if kappa_h > 0 else [],
            tau=tau,
        ),
    }


def engine_stage_order(sheet: str) -> list[str]:
    order = ENGINE_STAGE_ORDERS[sheet]
    return [*order["inner"], *order["outer"]]


def engine_channel(
    sheet: str,
    direction: str | tuple[float, float, float] = "iter176_xz",
    *,
    tau: float = DEFAULT_TAU,
    normalize: bool = True,
    rate_scale: float = 1.0,
    ladder_scale: float = 1.0,
    dephase_scale: float = 1.0,
) -> torch.Tensor:
    H0 = direction_hamiltonian(direction, normalize=normalize)
    stages = terrain_stage_channels(
        sheet,
        H0,
        tau=tau,
        rate_scale=rate_scale,
        ladder_scale=ladder_scale,
        dephase_scale=dephase_scale,
    )
    return compose([stages[name] for name in engine_stage_order(sheet)])


def schedule_channel(word: Iterable[str], engines: dict[str, torch.Tensor]) -> torch.Tensor:
    return compose([engines[token] for token in word])


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / torch.trace(rho)


def fixed_density(channel: torch.Tensor, *, cycles: int = DEFAULT_FIXED_ITERATIONS) -> torch.Tensor:
    state = vec(0.5 * I2)
    for _ in range(cycles):
        state = channel @ state
    return normalize_density(mat(state))


def fixed_bloch(channel: torch.Tensor, *, cycles: int = DEFAULT_FIXED_ITERATIONS) -> list[float]:
    return bloch(fixed_density(channel, cycles=cycles))


def channel_spectrum(
    channel: torch.Tensor,
    *,
    fixed_tol: float = FIXED_TOL,
) -> dict[str, Any]:
    eigvals = torch.linalg.eigvals(channel)
    fixed_dim = int(torch.sum(torch.abs(eigvals - 1.0) < fixed_tol).item())
    nonfixed = [complex(value.item()) for value in eigvals if abs(complex(value.item()) - 1.0) >= fixed_tol]
    spectral_radius_nonfixed = max((abs(value) for value in nonfixed), default=0.0)
    spectral_gap = 1.0 - spectral_radius_nonfixed
    return {
        "eigvals": eigvals,
        "fixed_eig_dim": fixed_dim,
        "spectral_gap": float(spectral_gap),
        "spectral_radius_nonfixed": float(spectral_radius_nonfixed),
    }


def channel_diagnostics(
    channel: torch.Tensor,
    *,
    initial_states: list[torch.Tensor] | None = None,
    cycles: int = DEFAULT_CYCLES,
    fixed_tol: float = FIXED_TOL,
    spread_tol: float = SPREAD_TOL,
    gap_tol: float = GAP_TOL,
) -> dict[str, Any]:
    spectrum = channel_spectrum(channel, fixed_tol=fixed_tol)
    finals: list[list[float]] = []
    for rho0 in initial_states or INITIAL_STATES:
        state = vec(rho0)
        for _ in range(cycles):
            state = channel @ state
        finals.append(bloch(normalize_density(mat(state))))
    max_spread = 0.0
    for left, right in itertools.combinations(finals, 2):
        max_spread = max(max_spread, math.dist(left, right))
    mean_final = [sum(point[idx] for point in finals) / len(finals) for idx in range(3)]
    fixed_dim = spectrum["fixed_eig_dim"]
    spectral_gap = spectrum["spectral_gap"]
    return {
        "fixed_eig_dim": fixed_dim,
        "spectral_gap": spectral_gap,
        "spectral_radius_nonfixed": spectrum["spectral_radius_nonfixed"],
        "max_final_bloch_spread": float(max_spread),
        "max_final_bloch_spread_at_80": float(max_spread),
        "mean_final_bloch": mean_final,
        "single_basin_by_trajectory_at_80": max_spread < spread_tol,
        "asymptotic_single_basin": fixed_dim == 1 and spectral_gap > gap_tol,
        "finite_time_slow_convergence": fixed_dim == 1 and spectral_gap > gap_tol and max_spread >= spread_tol,
        "multi_fixed_candidate": fixed_dim > 1,
        "asymptotic_multibasin_or_nonmixing_candidate": fixed_dim > 1 or spectral_gap <= gap_tol,
    }


def cluster_points(
    rows: list[dict[str, Any]],
    *,
    point_key: str = "fixed_bloch",
    label_key: str = "label",
    eps: float = 0.05,
) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for row in rows:
        point = row[point_key]
        label = row[label_key]
        for cluster in clusters:
            if math.dist(point, cluster["center"]) < eps:
                old_count = len(cluster["members"])
                cluster["members"].append(label)
                cluster["center"] = [
                    (cluster["center"][idx] * old_count + point[idx]) / (old_count + 1)
                    for idx in range(3)
                ]
                break
        else:
            clusters.append({"center": list(point), "members": [label]})
    return clusters


def assign_suffix_cluster(
    rows: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    *,
    suffix_len: int,
    point_key: str = "fixed_bloch",
    word_key: str = "word",
) -> list[str]:
    suffix_to_cluster: dict[str, int] = {}
    mismatches: list[str] = []
    for row in rows:
        point = row[point_key]
        cluster_idx = min(range(len(clusters)), key=lambda idx: math.dist(point, clusters[idx]["center"]))
        word = row[word_key]
        suffix = "".join(word[-suffix_len:]) if isinstance(word, list) else str(word)[-suffix_len:]
        previous = suffix_to_cluster.setdefault(suffix, cluster_idx)
        if previous != cluster_idx:
            mismatches.append("".join(word) if isinstance(word, list) else str(word))
    return mismatches


def jsonable(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(inner) for inner in value]
    return value
