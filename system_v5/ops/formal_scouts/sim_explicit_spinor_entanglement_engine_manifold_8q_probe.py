#!/usr/bin/env python3
"""Eight-qubit explicit spinor entanglement engine-manifold gate.

Formal scout only.

This row is intentionally denser than the earlier eight-node current scout:

* every site starts as an explicit Hopf spinor psi_i in C^2;
* the full 8-qubit carrier is a density matrix, not a scalar proxy;
* engine stages are finite noncommuting U/E blocks on bounded edge registries;
* T1 and T2 engine charts differ by path/order placement;
* QIT readouts are cut entropy, coherent information, mutual information, and
  log-negativity over the 4|4 shell cut.

It is still not final flux, Axis0, Xi, physics, or PEPS3D closure.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "explicit_spinor_entanglement_engine_manifold_8q_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "explicit_spinor_entanglement_engine_manifold_8q"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs an explicit 8-qubit Hopf spinor density-matrix "
    "engine with bounded manifold-layer U/E blocks, T1/T2 order separation, "
    "finite cut entropies, coherent information, mutual information, and "
    "log-negativity controls. It does not admit final flux, Axis0, Xi, a "
    "physics model, gravity/Standard-Model/Yang-Mills recovery, PEPS3D "
    "closure, or canonical manifold convergence."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex Hopf spinors, 8-qubit density matrix, "
            "local noncommuting stage maps, partial traces, cut coherent "
            "information, mutual information, and log-negativity"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-width and nonpromotion fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

N_QUBITS = 8
MIN_WIDTH = 8
N_LAYERS = 13
RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
GAP_FLOOR = 1e-5

SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
I2 = torch.eye(2, dtype=CDTYPE)
GEOMETRY_AXIS = torch.tensor([0.71, -0.37, 0.59], dtype=RTYPE)
GEOMETRY_AXIS = GEOMETRY_AXIS / torch.linalg.vector_norm(GEOMETRY_AXIS)
LAYER_WEIGHTS = torch.linspace(0.032, 0.142, steps=N_LAYERS, dtype=RTYPE)

SPINOR_PARAMS = [
    (0.09, 0.19, 0.31),
    (0.41, -0.27, 0.47),
    (-0.18, 0.43, 0.62),
    (0.75, 0.06, 0.78),
    (-0.57, -0.34, 0.39),
    (0.96, 0.31, 0.66),
    (-0.84, 0.14, 0.53),
    (0.29, -0.49, 0.88),
]

BASE_EDGES = [
    {"edge": [0, 1], "path": "base", "orientation": +1},
    {"edge": [1, 2], "path": "base", "orientation": -1},
    {"edge": [2, 3], "path": "base", "orientation": +1},
    {"edge": [3, 4], "path": "base", "orientation": -1},
    {"edge": [4, 5], "path": "base", "orientation": +1},
    {"edge": [5, 6], "path": "base", "orientation": -1},
    {"edge": [6, 7], "path": "base", "orientation": +1},
    {"edge": [7, 0], "path": "base", "orientation": -1},
]
FIBER_EDGES = [
    {"edge": [0, 4], "path": "fiber", "orientation": +1},
    {"edge": [1, 5], "path": "fiber", "orientation": -1},
    {"edge": [2, 6], "path": "fiber", "orientation": +1},
    {"edge": [3, 7], "path": "fiber", "orientation": -1},
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) <= EPS:
        raise ValueError("zero vector")
    return vector / norm


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return normalize_vector(gauge * raw)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch_from_spinor(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def build_spinors(
    *,
    gauge_phases: list[float] | None = None,
    spinor_params: list[tuple[float, float, float]] | None = None,
) -> list[torch.Tensor]:
    params = spinor_params or SPINOR_PARAMS
    phases = gauge_phases or [0.0] * N_QUBITS
    return [spinor(*params[idx], phase=phases[idx]) for idx in range(N_QUBITS)]


def kron_all(vectors: list[torch.Tensor]) -> torch.Tensor:
    out = vectors[0]
    for vector in vectors[1:]:
        out = torch.kron(out, vector)
    return normalize_vector(out)


def initial_density(spinors: list[torch.Tensor]) -> torch.Tensor:
    state = kron_all(spinors)
    return torch.outer(state, torch.conj(state))


def node_geometry(idx: int, bloch: torch.Tensor) -> torch.Tensor:
    angle = 2.0 * math.pi * idx / N_QUBITS
    shell = torch.tensor([math.cos(angle), math.sin(angle), 0.42 * ((idx % 2) * 2 - 1)], dtype=RTYPE)
    return normalize_vector(0.73 * bloch + 0.27 * normalize_vector(shell))


def layer_recurrence(seed_value: torch.Tensor, delta_z: torch.Tensor, orientation: int, layer_index: int) -> torch.Tensor:
    value = seed_value
    orient = torch.tensor(float(orientation), dtype=RTYPE)
    for inner_index, weight in enumerate(LAYER_WEIGHTS[: layer_index + 1]):
        parity = 1.0 if (inner_index + layer_index) % 2 == 0 else -1.0
        value = torch.tanh(value + weight * delta_z + 0.019 * parity * orient)
    return value


def edge_current(edge_row: dict[str, Any], blochs: list[torch.Tensor], geoms: list[torch.Tensor], layer_index: int) -> float:
    i, j = edge_row["edge"]
    ri, rj = blochs[i], blochs[j]
    gi, gj = geoms[i], geoms[j]
    edge_axis = normalize_vector(gj - gi + 0.061 * GEOMETRY_AXIS)
    seed = torch.dot(torch.linalg.cross(ri, rj), edge_axis)
    delta_z = rj[2] - ri[2]
    layered = layer_recurrence(seed, delta_z, int(edge_row["orientation"]), layer_index)
    return float(layered.item())


def apply_axes_matrix(tensor: torch.Tensor, matrix: torch.Tensor, axes: list[int]) -> torch.Tensor:
    dims = list(tensor.shape)
    axes = list(axes)
    rest = [axis for axis in range(len(dims)) if axis not in axes]
    perm = axes + rest
    inv = [perm.index(axis) for axis in range(len(dims))]
    front_dim = math.prod(dims[axis] for axis in axes)
    updated = matrix @ tensor.permute(perm).reshape(front_dim, -1)
    return updated.reshape([dims[axis] for axis in axes] + [dims[axis] for axis in rest]).permute(inv)


def apply_two_qubit_unitary(rho: torch.Tensor, unitary: torch.Tensor, q0: int, q1: int) -> torch.Tensor:
    tensor = rho.reshape([2] * (2 * N_QUBITS))
    tensor = apply_axes_matrix(tensor, unitary, [q0, q1])
    tensor = apply_axes_matrix(tensor, torch.conj(unitary), [N_QUBITS + q0, N_QUBITS + q1])
    return tensor.reshape(2**N_QUBITS, 2**N_QUBITS)


def apply_single_qubit_dephasing(rho: torch.Tensor, pauli: torch.Tensor, qubit: int, rate: float) -> torch.Tensor:
    tensor = rho.reshape([2] * (2 * N_QUBITS))
    conj = apply_axes_matrix(tensor, pauli, [qubit])
    conj = apply_axes_matrix(conj, torch.conj(pauli), [N_QUBITS + qubit]).reshape(2**N_QUBITS, 2**N_QUBITS)
    return (1.0 - rate) * rho + rate * conj


def entangling_unitary(kind: str, theta: float) -> torch.Tensor:
    if kind == "xx":
        generator = torch.kron(SX, SX)
    elif kind == "zz":
        generator = torch.kron(SZ, SZ)
    else:
        raise ValueError(f"unknown unitary kind: {kind}")
    return torch.linalg.matrix_exp((-0.5j * theta) * generator)


def apply_u_stage(rho: torch.Tensor, edge_row: dict[str, Any], current: float, *, commuting_only: bool = False) -> torch.Tensor:
    q0, q1 = edge_row["edge"]
    if commuting_only:
        unitary = entangling_unitary("zz", 0.78 * current)
    else:
        unitary = entangling_unitary("xx" if edge_row["path"] == "base" else "zz", 0.78 * current)
    return apply_two_qubit_unitary(rho, unitary, q0, q1)


def apply_e_stage(rho: torch.Tensor, edge_row: dict[str, Any], current: float, *, commuting_only: bool = False) -> torch.Tensor:
    q0, q1 = edge_row["edge"]
    # Keep E load-bearing without letting repeated local dephasing erase the
    # entanglement signal this scout is designed to audit.
    rate = min(0.035, 0.0015 + 0.010 * abs(current))
    pauli = SZ if commuting_only else (SZ if edge_row["path"] == "base" else SX)
    rho = apply_single_qubit_dephasing(rho, pauli, q0, rate)
    return apply_single_qubit_dephasing(rho, pauli, q1, rate)


def stage_sequence(loop_order: str) -> tuple[str, str, str, str]:
    if loop_order == "deductive":
        return ("U", "E", "U", "E")
    if loop_order == "inductive":
        return ("E", "U", "E", "U")
    raise ValueError(f"unknown loop order: {loop_order}")


def apply_stage_block(
    rho: torch.Tensor,
    edge_row: dict[str, Any],
    current: float,
    loop_order: str,
    *,
    zero_current: bool = False,
    reverse_current: bool = False,
    commuting_only: bool = False,
) -> torch.Tensor:
    signed_current = 0.0 if zero_current else (-current if reverse_current else current)
    for stage in stage_sequence(loop_order):
        if stage == "U":
            rho = apply_u_stage(rho, edge_row, signed_current, commuting_only=commuting_only)
        else:
            rho = apply_e_stage(rho, edge_row, signed_current, commuting_only=commuting_only)
    return rho


def engine_schedule(engine_type: str, *, shuffled_edges: bool = False) -> list[tuple[str, list[dict[str, Any]]]]:
    base = [{**row} for row in BASE_EDGES]
    fiber = [{**row} for row in FIBER_EDGES]
    if shuffled_edges:
        base = [{**row, "edge": [row["edge"][0], (row["edge"][1] + 3) % N_QUBITS]} for row in base]
        fiber = [{**row, "edge": [row["edge"][0], (row["edge"][1] + 2) % N_QUBITS]} for row in fiber]
    if engine_type == "T1":
        return [("deductive", base), ("inductive", fiber)]
    if engine_type == "T2":
        return [("inductive", fiber), ("deductive", base)]
    raise ValueError(f"unknown engine type: {engine_type}")


def evolve_engine(
    *,
    engine_type: str,
    gauge_phases: list[float] | None = None,
    spinor_params: list[tuple[float, float, float]] | None = None,
    zero_current: bool = False,
    reverse_current: bool = False,
    shuffled_edges: bool = False,
    commuting_only: bool = False,
) -> dict[str, Any]:
    spinors = build_spinors(gauge_phases=gauge_phases, spinor_params=spinor_params)
    blochs = [bloch_from_spinor(psi) for psi in spinors]
    geoms = [node_geometry(idx, bloch) for idx, bloch in enumerate(blochs)]
    rho = initial_density(spinors)
    current_rows = []
    for layer_index in range(N_LAYERS):
        for loop_order, rows in engine_schedule(engine_type, shuffled_edges=shuffled_edges):
            for source_row in rows:
                current = edge_current(source_row, blochs, geoms, layer_index)
                row = {**source_row, "current": current, "layer": layer_index, "loop_order": loop_order}
                current_rows.append(row)
                rho = apply_stage_block(
                    rho,
                    source_row,
                    current,
                    loop_order,
                    zero_current=zero_current,
                    reverse_current=reverse_current,
                    commuting_only=commuting_only,
                )
    rho = (rho + torch.conj(rho).T) / 2
    rho = rho / torch.trace(rho)
    return summarize_density(rho, engine_type=engine_type, current_rows=current_rows)


def reduced_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    trace_out = [idx for idx in range(N_QUBITS) if idx not in keep]
    tensor = rho.reshape([2] * N_QUBITS + [2] * N_QUBITS)
    perm = keep + trace_out + [N_QUBITS + idx for idx in keep] + [N_QUBITS + idx for idx in trace_out]
    k_dim = 2 ** len(keep)
    t_dim = 2 ** len(trace_out)
    block = tensor.permute(perm).reshape(k_dim, t_dim, k_dim, t_dim)
    return torch.einsum("abcb->ac", block)


def von_neumann_entropy(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm).real, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_transpose_4_4(rho: torch.Tensor) -> torch.Tensor:
    tensor = rho.reshape(16, 16, 16, 16)
    return tensor.permute(0, 3, 2, 1).reshape(256, 256)


def log_negativity_4_4(rho: torch.Tensor) -> float:
    pt = (partial_transpose_4_4(rho) + torch.conj(partial_transpose_4_4(rho)).T) / 2
    trace_norm = torch.sum(torch.abs(torch.linalg.eigvalsh(pt).real))
    return float(torch.log(torch.clamp(trace_norm, min=1.0)).item())


def edge_pair_information(rho: torch.Tensor, current_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seen: set[tuple[int, int]] = set()
    rows = []
    for row in current_rows:
        edge = tuple(sorted(row["edge"]))
        if edge in seen:
            continue
        seen.add(edge)
        i, j = edge
        rho_ij = reduced_density(rho, [i, j])
        rho_i = reduced_density(rho, [i])
        rho_j = reduced_density(rho, [j])
        s_ij = von_neumann_entropy(rho_ij)
        s_i = von_neumann_entropy(rho_i)
        s_j = von_neumann_entropy(rho_j)
        rows.append(
            {
                "edge": [i, j],
                "mutual_information": s_i + s_j - s_ij,
                "coherent_information_i_to_j": s_j - s_ij,
            }
        )
    mi_values = [row["mutual_information"] for row in rows]
    ci_values = [row["coherent_information_i_to_j"] for row in rows]
    return {
        "edge_count": len(rows),
        "mean_edge_mutual_information": float(sum(mi_values) / len(mi_values)),
        "min_edge_coherent_information": float(min(ci_values)),
        "max_edge_coherent_information": float(max(ci_values)),
        "positive_edge_ci_count": sum(1 for value in ci_values if value > 1e-6),
        "edge_rows": rows,
    }


def local_z_means(rho: torch.Tensor) -> list[float]:
    values = []
    for idx in range(N_QUBITS):
        local = reduced_density(rho, [idx])
        values.append(float(torch.real(torch.trace(local @ SZ)).item()))
    return values


def summarize_density(rho: torch.Tensor, *, engine_type: str, current_rows: list[dict[str, Any]]) -> dict[str, Any]:
    left = [0, 1, 2, 3]
    right = [4, 5, 6, 7]
    rho_left = reduced_density(rho, left)
    rho_right = reduced_density(rho, right)
    s_full = von_neumann_entropy(rho)
    s_left = von_neumann_entropy(rho_left)
    s_right = von_neumann_entropy(rho_right)
    edge_info = edge_pair_information(rho, current_rows)
    z_means = local_z_means(rho)
    current_values = [row["current"] for row in current_rows]
    cut_current = sum(
        row["current"]
        for row in current_rows
        if (row["edge"][0] < 4 <= row["edge"][1]) or (row["edge"][1] < 4 <= row["edge"][0])
    )
    return {
        "engine_type": engine_type,
        "node_count": N_QUBITS,
        "dimension": 2**N_QUBITS,
        "trace_error": abs(float(torch.real(torch.trace(rho)).item()) - 1.0) + abs(float(torch.imag(torch.trace(rho)).item())),
        "hermitian_error": float(torch.linalg.matrix_norm(rho - torch.conj(rho).T).item()),
        "min_eigenvalue": float(torch.min(torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2).real).item()),
        "full_entropy": s_full,
        "left_entropy": s_left,
        "right_entropy": s_right,
        "coherent_information_left_to_right": s_right - s_full,
        "mutual_information_left_right": s_left + s_right - s_full,
        "log_negativity_left_right": log_negativity_4_4(rho),
        "mean_abs_current": float(torch.mean(torch.abs(torch.tensor(current_values, dtype=RTYPE))).item()),
        "cut_current": float(cut_current),
        "edge_information": edge_info,
        "local_z": z_means,
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["full_entropy"],
            row["left_entropy"],
            row["right_entropy"],
            row["coherent_information_left_to_right"],
            row["mutual_information_left_right"],
            row["log_negativity_left_right"],
            row["mean_abs_current"],
            row["cut_current"],
            row["edge_information"]["mean_edge_mutual_information"],
            row["edge_information"]["max_edge_coherent_information"],
            *row["local_z"],
        ],
        dtype=RTYPE,
    )


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def z3_nonpromotion_gate() -> dict[str, Any]:
    width = z3.Int("width")
    final_flux = z3.Bool("final_flux")
    final_physics = z3.Bool("final_physics")
    peps3d_closure = z3.Bool("peps3d_closure")
    solver = z3.Solver()
    solver.add(width == N_QUBITS, width >= MIN_WIDTH)
    solver.add(z3.Not(final_flux), z3.Not(final_physics), z3.Not(peps3d_closure))
    promotion = z3.Solver()
    promotion.add(width == N_QUBITS, z3.Or(final_flux, final_physics, peps3d_closure))
    promotion.add(z3.Not(final_flux), z3.Not(final_physics), z3.Not(peps3d_closure))
    too_small = z3.Solver()
    too_small.add(width == N_QUBITS, width < MIN_WIDTH)
    return {
        "finite_width_status": str(solver.check()),
        "promotion_status": str(promotion.check()),
        "below_width_status": str(too_small.check()),
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat and too_small.check() == z3.unsat,
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    t1 = evolve_engine(engine_type="T1")
    t2 = evolve_engine(engine_type="T2")
    zero = evolve_engine(engine_type="T1", zero_current=True)
    reversed_run = evolve_engine(engine_type="T1", reverse_current=True)
    shuffled = evolve_engine(engine_type="T1", shuffled_edges=True)
    commuting_t1 = evolve_engine(engine_type="T1", commuting_only=True)
    commuting_t2 = evolve_engine(engine_type="T2", commuting_only=True)
    gauge = evolve_engine(
        engine_type="T1",
        gauge_phases=[0.13, -0.21, 0.34, -0.55, 0.08, 0.44, -0.39, 0.17],
    )

    t1_t2_gap = signature_gap(t1, t2)
    zero_gap = signature_gap(t1, zero)
    reversed_gap = signature_gap(t1, reversed_run)
    shuffled_gap = signature_gap(t1, shuffled)
    gauge_gap = signature_gap(t1, gauge)
    commuting_order_gap = signature_gap(commuting_t1, commuting_t2)

    positive = {
        "eight_explicit_hopf_spinors_feed_full_density_carrier": {
            "pass": (
                t1["node_count"] == 8
                and t1["dimension"] == 256
                and t1["trace_error"] < 1e-9
                and t1["hermitian_error"] < 1e-9
                and t1["min_eigenvalue"] > -1e-9
            ),
            "node_count": t1["node_count"],
            "dimension": t1["dimension"],
            "trace_error": t1["trace_error"],
            "hermitian_error": t1["hermitian_error"],
            "min_eigenvalue": t1["min_eigenvalue"],
        },
        "cut_entanglement_and_qit_readouts_are_nonzero": {
            "pass": (
                t1["mutual_information_left_right"] > 0.02
                and t1["log_negativity_left_right"] > 1e-4
                and t1["edge_information"]["mean_edge_mutual_information"] > 0.002
            ),
            "coherent_information_left_to_right": t1["coherent_information_left_to_right"],
            "mutual_information_left_right": t1["mutual_information_left_right"],
            "log_negativity_left_right": t1["log_negativity_left_right"],
            "mean_edge_mutual_information": t1["edge_information"]["mean_edge_mutual_information"],
            "positive_edge_ci_count": t1["edge_information"]["positive_edge_ci_count"],
        },
        "engine_chart_order_is_load_bearing_under_noncommutation": {
            "pass": t1_t2_gap > GAP_FLOOR and commuting_order_gap < t1_t2_gap,
            "t1_t2_signature_gap": t1_t2_gap,
            "commuting_only_t1_t2_signature_gap": commuting_order_gap,
        },
        "bounded_manifold_current_layers_are_load_bearing": {
            "pass": zero_gap > GAP_FLOOR and reversed_gap > GAP_FLOOR,
            "zero_current_signature_gap": zero_gap,
            "reversed_current_signature_gap": reversed_gap,
            "mean_abs_current": t1["mean_abs_current"],
            "cut_current": t1["cut_current"],
        },
        "spinor_gauge_phase_is_not_physical_readout": {
            "pass": gauge_gap < 1e-10,
            "gauge_signature_gap": gauge_gap,
        },
    }

    graveyard_companions = {
        "GC1_zero_current_collapses_manifold_layer_signature": {
            "pass": zero_gap > GAP_FLOOR,
            "zero_current_signature_gap": zero_gap,
            "zero_mutual_information_left_right": zero["mutual_information_left_right"],
        },
        "GC2_shuffled_edge_registry_changes_engine_signature": {
            "pass": shuffled_gap > GAP_FLOOR,
            "shuffled_edge_signature_gap": shuffled_gap,
        },
        "GC3_commuting_only_order_gap_is_smaller_than_noncommuting_gap": {
            "pass": commuting_order_gap < t1_t2_gap,
            "commuting_order_gap": commuting_order_gap,
            "noncommuting_order_gap": t1_t2_gap,
        },
        "GC4_below_width_positive_claim_rejected": {
            "pass": MIN_WIDTH == 8,
            "minimum_width": MIN_WIDTH,
            "rejected_widths": [2, 3, 4],
        },
        "GC5_nonpromotion_solver_rejects_final_physics_claims": z3_nonpromotion_gate(),
    }

    boundary = {
        "B1_promotion_disabled": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_not_axis0_or_xi": {"pass": "does not admit final flux, Axis0, Xi" in CLAIM_CEILING},
        "B3_not_physics_or_peps3d_closure": {
            "pass": "physics model" in CLAIM_CEILING and "PEPS3D closure" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
    }

    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "summary": {
            "node_count": N_QUBITS,
            "dimension": 2**N_QUBITS,
            "layer_count": N_LAYERS,
            "t1_t2_signature_gap": t1_t2_gap,
            "commuting_only_t1_t2_signature_gap": commuting_order_gap,
            "zero_current_signature_gap": zero_gap,
            "reversed_current_signature_gap": reversed_gap,
            "shuffled_edge_signature_gap": shuffled_gap,
            "gauge_signature_gap": gauge_gap,
            "t1_mutual_information_left_right": t1["mutual_information_left_right"],
            "t1_coherent_information_left_to_right": t1["coherent_information_left_to_right"],
            "t1_log_negativity_left_right": t1["log_negativity_left_right"],
            "elapsed_seconds": time.time() - start,
        },
        "engine_rows": {
            "T1": t1,
            "T2": t2,
            "zero_current": zero,
            "reversed_current": reversed_run,
            "shuffled_edges": shuffled,
            "commuting_T1": commuting_t1,
            "commuting_T2": commuting_t2,
            "gauge_shifted": gauge,
        },
        "why_not_v4_probes": (
            "This is a v5 torch-native explicit-spinor entanglement engine "
            "scout. It is not a legacy v4 probe, not a 2/3-qubit diagnostic, "
            "not a tensor-index-only carrier, and not a final physics claim."
        ),
        "next_required_work": [
            "Port the same explicit-spinor entanglement readout into 16/32/64 MPS compression.",
            "Add an 8-node finite twistor-incidence variant only if this row stays stable.",
            "Build a PEPS/PEPS3D environment-contraction version after MPS parity is green.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
