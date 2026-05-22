#!/usr/bin/env python3
"""Tiny PEPS3D dynamics scout for the two-root QIT engine line.

This is the Workstream E packet after the small-grid 2D PEPS rung. It runs
actual 3D PEPS-style tensor updates on a 2x2x2 open cube: local terrain-like
non-Hermitian no-jump steps plus nearest-neighbor two-site SVD gate updates over
x, y, and z bonds. Dense contraction is used only because the cube is tiny, to
read norm and Phi0 diagnostics exactly.

Boundary: this is a tiny PEPS3D dynamics scout. It is not L64, not a full
PEPS3D convergence theorem, not scale-level real-basin admission, and not final
constraint-manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import string
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json"

NAME = "two_root_constraint_peps3d_tiny_grid_dynamics_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_tiny_grid_peps3d_terrain_dynamics"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_peps3d_tiny_grid_dynamics"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tiny-grid PEPS3D dynamics scout only: runs PyTorch-native 3D "
    "PEPS-style local terrain no-jump steps and x/y/z nearest-neighbor SVD gate "
    "updates on a 2x2x2 cube with exact dense contraction readouts. It cannot "
    "promote L64, full PEPS3D convergence, scale-level real-basin admission, or "
    "final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D tensor cube, terrain no-jump updates, x/y/z two-site SVD gate updates, contractions, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 3D cube graph and PEPS3D update-order graph witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard distinguishing tiny PEPS3D dynamics from L64/scale/final admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

DTYPE = qit.DTYPE
GRID = (2, 2, 2)
BOND_CAP = 2
CYCLES = 1
INITIAL_FAMILIES = ["all_up", "all_down", "plus_x", "alternating_z"]
NORM_TOL = 1.0e-8
TRUNCATION_WARN = 50.0

VIRTUAL_NEG_AXIS = {0: 1, 1: 3, 2: 5}
VIRTUAL_POS_AXIS = {0: 2, 1: 4, 2: 6}

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "qit_runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "peps_result": RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "l32_result": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "trace_refresh_result": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def coords() -> list[tuple[int, int, int]]:
    return [(x, y, z) for x in range(GRID[0]) for y in range(GRID[1]) for z in range(GRID[2])]


def site_index(coord: tuple[int, int, int]) -> int:
    return coord[0] * GRID[1] * GRID[2] + coord[1] * GRID[2] + coord[2]


def edge_list() -> list[tuple[tuple[int, int, int], tuple[int, int, int], int]]:
    edges: list[tuple[tuple[int, int, int], tuple[int, int, int], int]] = []
    for coord in coords():
        for axis in range(3):
            nxt = list(coord)
            nxt[axis] += 1
            if nxt[axis] < GRID[axis]:
                edges.append((coord, tuple(nxt), axis))
    return edges


def virtual_dims(coord: tuple[int, int, int]) -> tuple[int, int, int, int, int, int]:
    x, y, z = coord
    xm = BOND_CAP if x > 0 else 1
    xp = BOND_CAP if x + 1 < GRID[0] else 1
    ym = BOND_CAP if y > 0 else 1
    yp = BOND_CAP if y + 1 < GRID[1] else 1
    zm = BOND_CAP if z > 0 else 1
    zp = BOND_CAP if z + 1 < GRID[2] else 1
    return xm, xp, ym, yp, zm, zp


class PEPS3D:
    """Tiny open-boundary PEPS3D tensor cube with simple-update style gates."""

    def __init__(self, tensors: dict[tuple[int, int, int], torch.Tensor]):
        self.tensors = tensors

    @classmethod
    def product(cls, family: str) -> "PEPS3D":
        tensors: dict[tuple[int, int, int], torch.Tensor] = {}
        for coord in coords():
            dims = virtual_dims(coord)
            tensor = torch.zeros((2, *dims), dtype=DTYPE)
            tensor[(slice(None), 0, 0, 0, 0, 0, 0)] = mps_runtime.site_vector(family, site_index(coord))
            tensors[coord] = tensor
        return cls(tensors)

    def apply_single(self, op: torch.Tensor, coord: tuple[int, int, int]) -> None:
        self.tensors[coord] = torch.einsum("ab,buvwxyz->auvwxyz", op.to(DTYPE), self.tensors[coord])

    def apply_pair_gate(
        self,
        gate: torch.Tensor,
        left_coord: tuple[int, int, int],
        right_coord: tuple[int, int, int],
        axis: int,
    ) -> float:
        gate4 = gate.reshape(2, 2, 2, 2).to(DTYPE)
        left = self.tensors[left_coord]
        right = self.tensors[right_coord]
        left_contract = VIRTUAL_POS_AXIS[axis]
        right_contract = VIRTUAL_NEG_AXIS[axis]
        left_keep = [idx for idx in range(left.ndim) if idx != left_contract]
        right_keep = [idx for idx in range(right.ndim) if idx != right_contract]
        theta = torch.tensordot(left, right, dims=([left_contract], [right_contract]))
        p_b_pos = len(left_keep)
        perm = [0, p_b_pos] + [
            idx for idx in range(len(left_keep) + len(right_keep))
            if idx not in {0, p_b_pos}
        ]
        theta = theta.permute(*perm).contiguous()
        theta = torch.einsum("ABab,ab...->AB...", gate4, theta)
        left_rest_shape = [left.shape[idx] for idx in left_keep if idx != 0]
        right_rest_shape = [right.shape[idx] for idx in right_keep if idx != 0]
        left_dim = 2 * math.prod(left_rest_shape)
        right_dim = 2 * math.prod(right_rest_shape)
        matrix = theta.reshape(left_dim, right_dim)
        u_mat, singulars, vh_mat = torch.linalg.svd(matrix, full_matrices=False)
        chi = min(BOND_CAP, int(singulars.numel()))
        discarded = singulars[chi:]
        truncation = float(torch.sum(discarded.real * discarded.real).item()) if discarded.numel() else 0.0
        left_temp = (u_mat[:, :chi] * singulars[:chi].unsqueeze(0)).reshape(
            2,
            *left_rest_shape,
            chi,
        )
        left_temp_axes = left_keep + [left_contract]
        left_perm = [left_temp_axes.index(idx) for idx in range(left.ndim)]
        new_left = left_temp.permute(*left_perm).contiguous()
        right_temp = vh_mat[:chi, :].reshape(
            chi,
            2,
            *right_rest_shape,
        )
        right_temp_axes = [right_contract] + right_keep
        right_perm = [right_temp_axes.index(idx) for idx in range(right.ndim)]
        new_right = right_temp.permute(*right_perm).contiguous()
        self.tensors[left_coord] = new_left
        self.tensors[right_coord] = new_right
        return truncation

    def internal_bond_dims(self) -> list[int]:
        dims: list[int] = []
        for left, right, axis in edge_list():
            dims.append(int(self.tensors[left].shape[VIRTUAL_POS_AXIS[axis]]))
            dims.append(int(self.tensors[right].shape[VIRTUAL_NEG_AXIS[axis]]))
        return dims

    def max_bond(self) -> int:
        return max(self.internal_bond_dims(), default=1)

    def dense_state(self) -> torch.Tensor:
        labels = iter(string.ascii_letters)
        physical_labels = {coord: next(labels) for coord in coords()}
        bond_labels: dict[tuple[tuple[int, int, int], int], str] = {}
        for left, right, axis in edge_list():
            left_axis = VIRTUAL_POS_AXIS[axis]
            right_axis = VIRTUAL_NEG_AXIS[axis]
            label = next(labels)
            bond_labels[(left, left_axis)] = label
            bond_labels[(right, right_axis)] = label
        operands = []
        tensors = []
        for coord in coords():
            axis_labels = [physical_labels[coord]]
            for axis_idx in range(1, 7):
                if (coord, axis_idx) in bond_labels:
                    axis_labels.append(bond_labels[(coord, axis_idx)])
                else:
                    axis_labels.append(next(labels))
            operands.append("".join(axis_labels))
            tensors.append(self.tensors[coord])
        output = "".join(physical_labels[coord] for coord in coords())
        contracted = torch.einsum(",".join(operands) + "->" + output, *tensors)
        return contracted.reshape(-1)

    def normalize_(self) -> float:
        norm = float(torch.linalg.vector_norm(self.dense_state()).item())
        if norm <= 0.0:
            raise ValueError("PEPS3D norm collapsed to zero")
        first = coords()[0]
        self.tensors[first] = self.tensors[first] / norm
        return norm


def dense_normalize(state: torch.Tensor) -> torch.Tensor:
    return state / torch.linalg.vector_norm(state)


def single_site_rho_from_state(state: torch.Tensor, coord: tuple[int, int, int]) -> torch.Tensor:
    n_sites = len(coords())
    site = site_index(coord)
    tensor = dense_normalize(state).reshape([2] * n_sites)
    moved = tensor.movedim(site, 0).reshape(2, -1)
    return mps_runtime.normalize_density(moved @ moved.conj().T)


def pair_rho_from_state(
    state: torch.Tensor,
    left: tuple[int, int, int],
    right: tuple[int, int, int],
) -> torch.Tensor:
    n_sites = len(coords())
    left_idx = site_index(left)
    right_idx = site_index(right)
    tensor = dense_normalize(state).reshape([2] * n_sites)
    moved = tensor.movedim((left_idx, right_idx), (0, 1)).reshape(4, -1)
    return mps_runtime.normalize_density(moved @ moved.conj().T)


def mean_z_from_state(state: torch.Tensor) -> float:
    values = [qit.bloch(single_site_rho_from_state(state, coord))[2] for coord in coords()]
    return float(sum(values) / len(values))


def two_site_gate() -> torch.Tensor:
    return mps_runtime.two_site_gate()


def edge_matching(phase: int) -> list[tuple[tuple[int, int, int], tuple[int, int, int], int]]:
    active_axis = phase % 3
    return [(left, right, axis) for left, right, axis in edge_list() if axis == active_axis]


def edge_phi0_summary(state: torch.Tensor) -> dict[str, Any]:
    rows = []
    for left, right, axis in edge_list():
        readout = mps_runtime.phi0_readout_pair(pair_rho_from_state(state, left, right))
        rows.append({"left": list(left), "right": list(right), "axis": axis, **readout})
    mi_values = [row["I_A_colon_B"] for row in rows]
    return {
        "edges": rows,
        "max_I_A_colon_B": max(mi_values),
        "mean_I_A_colon_B": float(sum(mi_values) / len(mi_values)),
    }


def selected_edge() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    return (0, 0, 0), (1, 0, 0)


def run_peps3d_surface(family: str, *, mode: str) -> dict[str, Any]:
    peps = PEPS3D.product(family)
    if mode == "no_dynamics":
        final_state = dense_normalize(peps.dense_state())
        center_edge = selected_edge()
        return {
            "family": family,
            "mode": mode,
            "stage_count": 0,
            "pair_gate_count": 0,
            "local_update_count": 0,
            "total_truncation_error": 0.0,
            "max_stage_truncation_error": 0.0,
            "max_bond": peps.max_bond(),
            "norm_error": abs(float(torch.linalg.vector_norm(final_state).item()) - 1.0),
            "mean_z": mean_z_from_state(final_state),
            "selected_edge": [center_edge[0], center_edge[1]],
            "selected_pair_phi0": mps_runtime.phi0_readout_pair(pair_rho_from_state(final_state, *center_edge)),
            "edge_phi0": edge_phi0_summary(final_state),
            "stage_records": [],
        }
    token_prev: str | None = "1"
    gate = two_site_gate()
    total_truncation = 0.0
    max_stage_truncation = 0.0
    local_updates = 0
    pair_gates = 0
    stage_records: list[dict[str, Any]] = []
    for cycle in range(CYCLES):
        state_before = dense_normalize(peps.dense_state())
        token = mps_runtime.choose_hysteresis(mean_z_from_state(state_before), token_prev)
        token_prev = token
        for stage_idx, terrain in enumerate(mps_runtime.TERRAIN_ORDER_BY_TOKEN[token]):
            H = mps_runtime.local_hamiltonian(token)
            collapses = mps_runtime.collapse_ops(token, terrain)
            op = mps_runtime.no_jump_operator(H, collapses)
            for coord in coords():
                peps.apply_single(op, coord)
                local_updates += 1
            stage_truncation = 0.0
            if mode == "dynamic_peps3d":
                for left, right, axis in edge_matching(stage_idx):
                    stage_truncation += peps.apply_pair_gate(gate, left, right, axis)
                    pair_gates += 1
            elif mode != "local_only":
                raise ValueError(f"unknown mode {mode}")
            total_truncation += stage_truncation
            max_stage_truncation = max(max_stage_truncation, stage_truncation)
            stage_records.append(
                {
                    "cycle": cycle,
                    "stage_index": stage_idx,
                    "token": token,
                    "terrain": terrain,
                    "mode": mode,
                    "active_axis": stage_idx % 3 if mode == "dynamic_peps3d" else None,
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "pair_gate_count_so_far": pair_gates,
                    "local_update_count_so_far": local_updates,
                    "max_bond": peps.max_bond(),
                    "norm_error": None,
                    "mean_z": None,
                    "diagnostic_note": "Dense PEPS3D contraction is deferred to final readout for runtime control.",
                }
            )
    peps.normalize_()
    final_state = dense_normalize(peps.dense_state())
    center_edge = selected_edge()
    return {
        "family": family,
        "mode": mode,
        "stage_count": len(stage_records),
        "pair_gate_count": pair_gates,
        "local_update_count": local_updates,
        "total_truncation_error": total_truncation,
        "max_stage_truncation_error": max_stage_truncation,
        "max_bond": peps.max_bond(),
        "norm_error": abs(float(torch.linalg.vector_norm(final_state).item()) - 1.0),
        "mean_z": mean_z_from_state(final_state),
        "selected_edge": [center_edge[0], center_edge[1]],
        "selected_pair_phi0": mps_runtime.phi0_readout_pair(pair_rho_from_state(final_state, *center_edge)),
        "edge_phi0": edge_phi0_summary(final_state),
        "stage_records": stage_records,
    }


def cube_graph_report(dynamic_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = {coord: graph.add_node(coord) for coord in coords()}
    for left, right, axis in edge_list():
        graph.add_edge(nodes[left], nodes[right], axis)
    stage_graph = rx.PyDiGraph()
    previous = None
    for record in dynamic_rows[0]["stage_records"]:
        node = stage_graph.add_node(f"{record['cycle']}:{record['token']}:{record['terrain']}")
        if previous is not None:
            stage_graph.add_edge(previous, node, "next")
        previous = node
    return {
        "grid_shape": list(GRID),
        "grid_nodes": graph.num_nodes(),
        "grid_edges": graph.num_edges(),
        "x_edges": sum(1 for *_, axis in edge_list() if axis == 0),
        "y_edges": sum(1 for *_, axis in edge_list() if axis == 1),
        "z_edges": sum(1 for *_, axis in edge_list() if axis == 2),
        "stage_nodes": stage_graph.num_nodes(),
        "stage_edges": stage_graph.num_edges(),
        "stage_graph_is_dag": bool(rx.is_directed_acyclic_graph(stage_graph)),
    }


def z3_guard(dynamic_rows: list[dict[str, Any]], local_rows: list[dict[str, Any]]) -> dict[str, Any]:
    peps3d_dynamic = z3.Bool("peps3d_dynamic")
    l64_dynamic = z3.Bool("l64_dynamic")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(peps3d_dynamic == bool(dynamic_rows))
    solver.add(l64_dynamic == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(peps3d_dynamic, l64_dynamic, scale_basin))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "tiny_peps3d_dynamic": z3.is_true(model.eval(peps3d_dynamic, model_completion=True)),
        "l64_dynamic": z3.is_true(model.eval(l64_dynamic, model_completion=True)),
        "scale_basin": z3.is_true(model.eval(scale_basin, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "tiny PEPS3D dynamics is a Workstream-E rung; final admission also requires L64/scale dynamics and scale-level basin evidence",
        "dynamic_mode_count": len(dynamic_rows),
        "local_control_count": len(local_rows),
    }


def strip_stages(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "stage_records"}


def main() -> int:
    started = time.time()
    peps_result = read_json(SOURCE_FILES["peps_result"])
    l32_result = read_json(SOURCE_FILES["l32_result"])
    trace_refresh = read_json(SOURCE_FILES["trace_refresh_result"])
    dynamic_rows = [run_peps3d_surface(family, mode="dynamic_peps3d") for family in INITIAL_FAMILIES]
    local_rows = [run_peps3d_surface(family, mode="local_only") for family in INITIAL_FAMILIES]
    no_dynamics_rows = [run_peps3d_surface(family, mode="no_dynamics") for family in INITIAL_FAMILIES]
    graph = cube_graph_report(dynamic_rows)
    guard = z3_guard(dynamic_rows, local_rows)
    max_dynamic_norm_error = max(row["norm_error"] for row in dynamic_rows)
    max_dynamic_truncation = max(row["total_truncation_error"] for row in dynamic_rows)
    dynamic_selected_mi = {row["family"]: row["selected_pair_phi0"]["I_A_colon_B"] for row in dynamic_rows}
    local_selected_mi = {row["family"]: row["selected_pair_phi0"]["I_A_colon_B"] for row in local_rows}
    no_dynamics_selected_mi = {row["family"]: row["selected_pair_phi0"]["I_A_colon_B"] for row in no_dynamics_rows}
    dynamic_edge_max_mi = {row["family"]: row["edge_phi0"]["max_I_A_colon_B"] for row in dynamic_rows}
    local_edge_max_mi = {row["family"]: row["edge_phi0"]["max_I_A_colon_B"] for row in local_rows}
    no_dynamics_edge_max_mi = {row["family"]: row["edge_phi0"]["max_I_A_colon_B"] for row in no_dynamics_rows}
    selected_separations = {
        family: dynamic_selected_mi[family] - max(local_selected_mi[family], no_dynamics_selected_mi[family])
        for family in INITIAL_FAMILIES
    }
    edge_max_separations = {
        family: dynamic_edge_max_mi[family] - max(local_edge_max_mi[family], no_dynamics_edge_max_mi[family])
        for family in INITIAL_FAMILIES
    }
    positive = {
        "small_peps_baseline_exists": {
            "pass": bool(peps_result.get("all_pass")),
            "source": rel(SOURCE_FILES["peps_result"]),
            "peps_status": peps_result.get("summary", {}).get("peps_status"),
        },
        "l32_baseline_exists": {
            "pass": bool(l32_result.get("all_pass")),
            "source": rel(SOURCE_FILES["l32_result"]),
            "l32_status": l32_result.get("summary", {}).get("l32_status"),
        },
        "trace_refresh_exists": {
            "pass": bool(trace_refresh.get("all_pass")),
            "source": rel(SOURCE_FILES["trace_refresh_result"]),
            "manifold_admitted": trace_refresh.get("summary", {}).get("manifold_admitted"),
        },
        "peps3d_grid_is_3d": {
            "pass": graph["x_edges"] > 0 and graph["y_edges"] > 0 and graph["z_edges"] > 0,
            "graph": graph,
        },
        "dynamic_peps3d_ran": {
            "pass": all(row["stage_count"] == CYCLES * len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"]) for row in dynamic_rows)
            and all(row["pair_gate_count"] > 0 for row in dynamic_rows)
            and all(row["local_update_count"] > 0 for row in dynamic_rows),
            "stages_per_family": {row["family"]: row["stage_count"] for row in dynamic_rows},
            "pair_gates_per_family": {row["family"]: row["pair_gate_count"] for row in dynamic_rows},
            "local_updates_per_family": {row["family"]: row["local_update_count"] for row in dynamic_rows},
        },
        "norms_and_truncation_diagnostic_finite": {
            "pass": (
                max_dynamic_norm_error < NORM_TOL
                and math.isfinite(max_dynamic_truncation)
                and max_dynamic_truncation < TRUNCATION_WARN
            ),
            "max_dynamic_norm_error": max_dynamic_norm_error,
            "max_dynamic_truncation_error": max_dynamic_truncation,
            "norm_threshold": NORM_TOL,
            "truncation_diagnostic_warning_threshold": TRUNCATION_WARN,
            "detail": "Tiny PEPS3D simple-update truncation is recorded as finite diagnostics, not a convergence theorem.",
        },
        "phi0_readouts_present": {
            "pass": all("I_A_colon_B" in row["selected_pair_phi0"] for row in dynamic_rows + local_rows + no_dynamics_rows),
            "dynamic_selected_mi": dynamic_selected_mi,
            "local_only_selected_mi": local_selected_mi,
            "no_dynamics_selected_mi": no_dynamics_selected_mi,
            "selected_dynamic_minus_max_control": selected_separations,
            "dynamic_edge_max_mi": dynamic_edge_max_mi,
            "edge_max_dynamic_minus_max_control": edge_max_separations,
        },
    }
    peps3d_status = (
        "tiny_peps3d_dynamic_control_separated"
        if any(value > 1.0e-3 for value in selected_separations.values())
        or any(value > 1.0e-3 for value in edge_max_separations.values())
        else "tiny_peps3d_dynamic_open_nonseparating"
    )
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "peps3d_status": peps3d_status,
        "tiny_peps3d_dynamic": True,
        "not_l64": True,
        "not_full_peps3d_convergence": True,
        "not_scale_level_real_basin": True,
        "not_final_manifold_admission": True,
        "z3_final_manifold_admission_allowed": guard["final_manifold_admission_allowed"],
    }
    graveyard = {
        "construction_only_rejected": {
            "pass": all(row["stage_count"] > 0 and row["pair_gate_count"] > 0 for row in dynamic_rows),
            "detail": "The dynamic mode applies local terrain steps and 3D x/y/z edge gates; carrier construction alone is not counted.",
        },
        "product_control_retained": {
            "pass": len(no_dynamics_rows) == len(dynamic_rows),
            "detail": "No-dynamics product PEPS3D control is included for every initial family.",
        },
        "local_only_control_retained": {
            "pass": len(local_rows) == len(dynamic_rows),
            "detail": "Local terrain no-jump updates without pair gates are included for every initial family.",
        },
        "final_admission_blocked": {
            "pass": not guard["final_manifold_admission_allowed"],
            "z3_guard": guard,
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard.values())
        and not guard["final_manifold_admission_allowed"]
    )
    summary = {
        "all_pass": all_pass,
        "peps3d_status": peps3d_status,
        "grid_shape": list(GRID),
        "bond_cap": BOND_CAP,
        "cycles": CYCLES,
        "dynamic_selected_mi": dynamic_selected_mi,
        "local_only_selected_mi": local_selected_mi,
        "no_dynamics_selected_mi": no_dynamics_selected_mi,
        "selected_dynamic_minus_max_control": selected_separations,
        "dynamic_edge_max_mi": dynamic_edge_max_mi,
        "edge_max_dynamic_minus_max_control": edge_max_separations,
        "max_dynamic_truncation_error": max_dynamic_truncation,
        "max_dynamic_norm_error": max_dynamic_norm_error,
        "z3_guard": guard,
        "interpretation": (
            "A tiny 3D PEPS-style tensor cube now runs real local terrain "
            "updates plus x/y/z nearest-neighbor SVD gates and exact readouts. "
            "This advances the PEPS3D rung only at tiny-grid scope; L64, "
            "scale-level basin admission, and final manifold admission remain blocked."
        ),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "summary": summary,
        "positive": positive,
        "positive_findings": positive,
        "graveyard_companions": graveyard,
        "graveyard_controls": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "variants": sorted(graveyard),
        },
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 tiny-grid PEPS3D dynamics formal scout over PyTorch local tensor "
            "updates and current manifold receipts, not a legacy v4 probe or a full PEPS3D admission."
        ),
        "graph_witness": graph,
        "dynamic_rows": [strip_stages(row) for row in dynamic_rows],
        "local_only_control_rows": [strip_stages(row) for row in local_rows],
        "no_dynamics_control_rows": [strip_stages(row) for row in no_dynamics_rows],
        "representative_dynamic_stage_records": dynamic_rows[0]["stage_records"],
        "next_work_required": [
            "Stress-test the weak coupled-E16 Phi0 margin against more controls.",
            "Attempt L64 tensor-network dynamics or write an exact blocked receipt.",
            "Do not call scale-level basin admission until L64 and bridge/Phi0 controls are strong enough.",
        ],
        "source_hashes": source_hashes(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
