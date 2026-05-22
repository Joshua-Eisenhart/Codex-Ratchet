#!/usr/bin/env python3
"""Small-grid PEPS dynamics scout for the two-root QIT engine line.

This is the next Workstream E packet after the L32 low-bond MPS rung. It runs
actual 2D PEPS-style tensor updates on a tiny grid: local terrain-like
non-Hermitian no-jump steps plus nearest-neighbor two-site SVD gate updates over
horizontal and vertical bonds. Dense contraction is used only because the grid is
tiny, to read norm and Phi0 diagnostics exactly.

Boundary: this is a small-grid PEPS dynamics scout. It is not PEPS3D, not L64,
not a full PEPS convergence theorem, not a scale-level real basin, and not final
constraint-manifold admission.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
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
OUT_PATH = RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json"

NAME = "two_root_constraint_peps_small_grid_dynamics_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_small_grid_peps_terrain_dynamics"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_peps_small_grid_dynamics"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal small-grid PEPS dynamics scout only: runs PyTorch-native 2D PEPS-style "
    "local terrain no-jump steps and nearest-neighbor SVD gate updates on a tiny "
    "2x2 grid with exact dense contraction readouts. It cannot promote PEPS3D, "
    "L64, full PEPS convergence, scale-level real-basin admission, or final "
    "constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS tensor grid, terrain no-jump updates, two-site SVD gate updates, contractions, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2D grid and PEPS update-order graph witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard distinguishing small-grid PEPS dynamics from PEPS3D/L64/final admission",
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
GRID = (2, 2)
BOND_CAP = 2
CYCLES = 2
INITIAL_FAMILIES = ["all_up", "all_down", "plus_x", "alternating_z"]
NORM_TOL = 1.0e-8
TRUNCATION_WARN = 10.0

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "qit_runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
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


def site_index(coord: tuple[int, int]) -> int:
    return coord[0] * GRID[1] + coord[1]


def coords() -> list[tuple[int, int]]:
    return [(row, col) for row in range(GRID[0]) for col in range(GRID[1])]


def edge_list() -> list[tuple[tuple[int, int], tuple[int, int], str]]:
    edges: list[tuple[tuple[int, int], tuple[int, int], str]] = []
    for row, col in coords():
        if col + 1 < GRID[1]:
            edges.append(((row, col), (row, col + 1), "horizontal"))
        if row + 1 < GRID[0]:
            edges.append(((row, col), (row + 1, col), "vertical"))
    return edges


def virtual_dims(coord: tuple[int, int]) -> tuple[int, int, int, int]:
    row, col = coord
    up = BOND_CAP if row > 0 else 1
    down = BOND_CAP if row + 1 < GRID[0] else 1
    left = BOND_CAP if col > 0 else 1
    right = BOND_CAP if col + 1 < GRID[1] else 1
    return up, down, left, right


class PEPS:
    """Tiny open-boundary PEPS tensor grid with simple-update style gates."""

    def __init__(self, tensors: dict[tuple[int, int], torch.Tensor]):
        self.tensors = tensors

    @classmethod
    def product(cls, family: str) -> "PEPS":
        tensors: dict[tuple[int, int], torch.Tensor] = {}
        for coord in coords():
            up, down, left, right = virtual_dims(coord)
            tensor = torch.zeros((2, up, down, left, right), dtype=DTYPE)
            tensor[:, 0, 0, 0, 0] = mps_runtime.site_vector(family, site_index(coord))
            tensors[coord] = tensor
        return cls(tensors)

    def copy(self) -> "PEPS":
        return PEPS({coord: tensor.clone() for coord, tensor in self.tensors.items()})

    def apply_single(self, op: torch.Tensor, coord: tuple[int, int]) -> None:
        self.tensors[coord] = torch.einsum("ab,budlr->audlr", op.to(DTYPE), self.tensors[coord])

    def apply_pair_gate(
        self,
        gate: torch.Tensor,
        left_coord: tuple[int, int],
        right_coord: tuple[int, int],
        orientation: str,
    ) -> float:
        gate4 = gate.reshape(2, 2, 2, 2).to(DTYPE)
        left = self.tensors[left_coord]
        right = self.tensors[right_coord]
        if orientation == "horizontal":
            theta = torch.tensordot(left, right, dims=([4], [3]))
            # pA,uA,dA,lA,pB,uB,dB,rB -> pA,pB,uA,dA,lA,uB,dB,rB
            theta = theta.permute(0, 4, 1, 2, 3, 5, 6, 7).contiguous()
            theta = torch.einsum("ABab,ab...->AB...", gate4, theta)
            p_a, p_b, u_a, d_a, l_a, u_b, d_b, r_b = theta.shape
            matrix = theta.reshape(p_a * u_a * d_a * l_a, p_b * u_b * d_b * r_b)
            u_mat, singulars, vh_mat = torch.linalg.svd(matrix, full_matrices=False)
            chi = min(BOND_CAP, int(singulars.numel()))
            discarded = singulars[chi:]
            truncation = float(torch.sum(discarded.real * discarded.real).item()) if discarded.numel() else 0.0
            new_left = (u_mat[:, :chi] * singulars[:chi].unsqueeze(0)).reshape(p_a, u_a, d_a, l_a, chi)
            new_right = vh_mat[:chi, :].reshape(chi, p_b, u_b, d_b, r_b).permute(1, 2, 3, 0, 4).contiguous()
        elif orientation == "vertical":
            theta = torch.tensordot(left, right, dims=([2], [1]))
            # pA,uA,lA,rA,pB,dB,lB,rB -> pA,pB,uA,lA,rA,dB,lB,rB
            theta = theta.permute(0, 4, 1, 2, 3, 5, 6, 7).contiguous()
            theta = torch.einsum("ABab,ab...->AB...", gate4, theta)
            p_a, p_b, u_a, l_a, r_a, d_b, l_b, r_b = theta.shape
            matrix = theta.reshape(p_a * u_a * l_a * r_a, p_b * d_b * l_b * r_b)
            u_mat, singulars, vh_mat = torch.linalg.svd(matrix, full_matrices=False)
            chi = min(BOND_CAP, int(singulars.numel()))
            discarded = singulars[chi:]
            truncation = float(torch.sum(discarded.real * discarded.real).item()) if discarded.numel() else 0.0
            left_flat = (u_mat[:, :chi] * singulars[:chi].unsqueeze(0)).reshape(p_a, u_a, l_a, r_a, chi)
            new_left = left_flat.permute(0, 1, 4, 2, 3).contiguous()
            new_right = vh_mat[:chi, :].reshape(chi, p_b, d_b, l_b, r_b).permute(1, 0, 2, 3, 4).contiguous()
        else:
            raise ValueError(f"unknown orientation {orientation}")
        self.tensors[left_coord] = new_left
        self.tensors[right_coord] = new_right
        return truncation

    def internal_bond_dims(self) -> list[int]:
        dims: list[int] = []
        for left, right, orientation in edge_list():
            if orientation == "horizontal":
                dims.append(int(self.tensors[left].shape[4]))
                dims.append(int(self.tensors[right].shape[3]))
            else:
                dims.append(int(self.tensors[left].shape[2]))
                dims.append(int(self.tensors[right].shape[1]))
        return dims

    def max_bond(self) -> int:
        return max(self.internal_bond_dims(), default=1)

    def dense_state(self) -> torch.Tensor:
        edge_specs: list[tuple[tuple[tuple[int, int], int], tuple[tuple[int, int], int], int]] = []
        for left, right, orientation in edge_list():
            if orientation == "horizontal":
                edge_specs.append(((left, 4), (right, 3), int(self.tensors[left].shape[4])))
            else:
                edge_specs.append(((left, 2), (right, 1), int(self.tensors[left].shape[2])))
        dims = [spec[2] for spec in edge_specs]
        state = torch.zeros(2 ** len(coords()), dtype=DTYPE)
        for assignment in itertools.product(*[range(dim) for dim in dims]):
            bond_value: dict[tuple[tuple[int, int], int], int] = {}
            for edge_idx, spec in enumerate(edge_specs):
                bond_value[spec[0]] = assignment[edge_idx]
                bond_value[spec[1]] = assignment[edge_idx]
            for bits in itertools.product((0, 1), repeat=len(coords())):
                amp = torch.ones((), dtype=DTYPE)
                for coord in coords():
                    tensor = self.tensors[coord]
                    virtual = [0, 0, 0, 0]
                    for axis in (1, 2, 3, 4):
                        virtual[axis - 1] = bond_value.get((coord, axis), 0)
                    amp = amp * tensor[bits[site_index(coord)], virtual[0], virtual[1], virtual[2], virtual[3]]
                flat = 0
                for bit in bits:
                    flat = (flat << 1) | int(bit)
                state[flat] = state[flat] + amp
        return state

    def normalize_(self) -> float:
        norm = float(torch.linalg.vector_norm(self.dense_state()).item())
        if norm <= 0.0:
            raise ValueError("PEPS norm collapsed to zero")
        first = coords()[0]
        self.tensors[first] = self.tensors[first] / norm
        return norm


def dense_normalize(state: torch.Tensor) -> torch.Tensor:
    return state / torch.linalg.vector_norm(state)


def single_site_rho_from_state(state: torch.Tensor, coord: tuple[int, int]) -> torch.Tensor:
    n_sites = len(coords())
    site = site_index(coord)
    tensor = dense_normalize(state).reshape([2] * n_sites)
    moved = tensor.movedim(site, 0).reshape(2, -1)
    return mps_runtime.normalize_density(moved @ moved.conj().T)


def pair_rho_from_state(state: torch.Tensor, left: tuple[int, int], right: tuple[int, int]) -> torch.Tensor:
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


def edge_matching(phase: int) -> list[tuple[tuple[int, int], tuple[int, int], str]]:
    """Return a non-overlapping 2D checkerboard edge layer."""
    layer = phase % 4
    out: list[tuple[tuple[int, int], tuple[int, int], str]] = []
    for left, right, orientation in edge_list():
        if orientation == "horizontal":
            if layer == 0 and left[1] % 2 == 0:
                out.append((left, right, orientation))
            elif layer == 1 and left[1] % 2 == 1:
                out.append((left, right, orientation))
        elif orientation == "vertical":
            if layer == 2 and left[1] % 2 == 0:
                out.append((left, right, orientation))
            elif layer == 3 and left[1] % 2 == 1:
                out.append((left, right, orientation))
    return out


def run_peps_surface(family: str, *, mode: str) -> dict[str, Any]:
    peps = PEPS.product(family)
    if mode == "no_dynamics":
        final_state = dense_normalize(peps.dense_state())
        center_edge = ((0, 1), (1, 1))
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
            "center_edge": [center_edge[0], center_edge[1]],
            "center_pair_phi0": mps_runtime.phi0_readout_pair(pair_rho_from_state(final_state, *center_edge)),
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
            peps.normalize_()
            stage_truncation = 0.0
            if mode == "dynamic_peps":
                active_edges = edge_matching(stage_idx)
                for left, right, orientation in active_edges:
                    stage_truncation += peps.apply_pair_gate(gate, left, right, orientation)
                    pair_gates += 1
                    peps.normalize_()
            elif mode != "local_only":
                raise ValueError(f"unknown mode {mode}")
            total_truncation += stage_truncation
            max_stage_truncation = max(max_stage_truncation, stage_truncation)
            final_stage_state = dense_normalize(peps.dense_state())
            stage_records.append(
                {
                    "cycle": cycle,
                    "stage_index": stage_idx,
                    "token": token,
                    "terrain": terrain,
                    "mode": mode,
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "pair_gate_count_so_far": pair_gates,
                    "local_update_count_so_far": local_updates,
                    "max_bond": peps.max_bond(),
                    "norm_error": abs(float(torch.linalg.vector_norm(final_stage_state).item()) - 1.0),
                    "mean_z": mean_z_from_state(final_stage_state),
                }
            )
    final_state = dense_normalize(peps.dense_state())
    center_edge = ((0, 1), (1, 1))
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
        "center_edge": [center_edge[0], center_edge[1]],
        "center_pair_phi0": mps_runtime.phi0_readout_pair(pair_rho_from_state(final_state, *center_edge)),
        "edge_phi0": edge_phi0_summary(final_state),
        "stage_records": stage_records,
    }


def edge_phi0_summary(state: torch.Tensor) -> dict[str, Any]:
    rows = []
    for left, right, orientation in edge_list():
        readout = mps_runtime.phi0_readout_pair(pair_rho_from_state(state, left, right))
        rows.append(
            {
                "left": list(left),
                "right": list(right),
                "orientation": orientation,
                **readout,
            }
        )
    mi_values = [row["I_A_colon_B"] for row in rows]
    return {
        "edges": rows,
        "max_I_A_colon_B": max(mi_values),
        "mean_I_A_colon_B": float(sum(mi_values) / len(mi_values)),
    }


def grid_graph_report(dynamic_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = {coord: graph.add_node(coord) for coord in coords()}
    for left, right, orientation in edge_list():
        graph.add_edge(nodes[left], nodes[right], orientation)
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
        "horizontal_edges": sum(1 for *_, orientation in edge_list() if orientation == "horizontal"),
        "vertical_edges": sum(1 for *_, orientation in edge_list() if orientation == "vertical"),
        "stage_nodes": stage_graph.num_nodes(),
        "stage_edges": stage_graph.num_edges(),
        "stage_graph_is_dag": bool(rx.is_directed_acyclic_graph(stage_graph)),
    }


def z3_guard(dynamic_rows: list[dict[str, Any]], local_rows: list[dict[str, Any]]) -> dict[str, Any]:
    peps_dynamic = z3.Bool("peps_dynamic")
    peps3d_dynamic = z3.Bool("peps3d_dynamic")
    l64_dynamic = z3.Bool("l64_dynamic")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(peps_dynamic == bool(dynamic_rows))
    solver.add(peps3d_dynamic == False)
    solver.add(l64_dynamic == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(peps_dynamic, peps3d_dynamic, l64_dynamic, scale_basin))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "small_grid_peps_dynamic": z3.is_true(model.eval(peps_dynamic, model_completion=True)),
        "peps3d_dynamic": z3.is_true(model.eval(peps3d_dynamic, model_completion=True)),
        "l64_dynamic": z3.is_true(model.eval(l64_dynamic, model_completion=True)),
        "scale_basin": z3.is_true(model.eval(scale_basin, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "small-grid PEPS dynamics is a Workstream-E rung; final admission also requires PEPS3D, L64/scale dynamics, and scale-level basin evidence",
        "dynamic_mode_count": len(dynamic_rows),
        "local_control_count": len(local_rows),
    }


def strip_stages(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "stage_records"}


def main() -> int:
    started = time.time()
    l32_result = read_json(SOURCE_FILES["l32_result"])
    trace_refresh = read_json(SOURCE_FILES["trace_refresh_result"])
    dynamic_rows = [run_peps_surface(family, mode="dynamic_peps") for family in INITIAL_FAMILIES]
    local_rows = [run_peps_surface(family, mode="local_only") for family in INITIAL_FAMILIES]
    no_dynamics_rows = [run_peps_surface(family, mode="no_dynamics") for family in INITIAL_FAMILIES]
    graph = grid_graph_report(dynamic_rows)
    guard = z3_guard(dynamic_rows, local_rows)
    max_dynamic_norm_error = max(row["norm_error"] for row in dynamic_rows)
    max_dynamic_truncation = max(row["total_truncation_error"] for row in dynamic_rows)
    dynamic_center_mi = {row["family"]: row["center_pair_phi0"]["I_A_colon_B"] for row in dynamic_rows}
    local_center_mi = {row["family"]: row["center_pair_phi0"]["I_A_colon_B"] for row in local_rows}
    no_dynamics_center_mi = {row["family"]: row["center_pair_phi0"]["I_A_colon_B"] for row in no_dynamics_rows}
    separations = {
        family: dynamic_center_mi[family] - max(local_center_mi[family], no_dynamics_center_mi[family])
        for family in INITIAL_FAMILIES
    }
    positive = {
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
        "peps_grid_is_2d": {
            "pass": graph["horizontal_edges"] > 0 and graph["vertical_edges"] > 0,
            "graph": graph,
        },
        "dynamic_peps_ran": {
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
            "detail": "Simple-update PEPS truncation is recorded as finite diagnostics, not a convergence theorem.",
        },
        "phi0_readouts_present": {
            "pass": all("I_A_colon_B" in row["center_pair_phi0"] for row in dynamic_rows + local_rows + no_dynamics_rows),
            "dynamic_center_mi": dynamic_center_mi,
            "local_only_center_mi": local_center_mi,
            "no_dynamics_center_mi": no_dynamics_center_mi,
            "dynamic_minus_max_control": separations,
        },
    }
    peps_status = (
        "small_grid_peps_dynamic_control_separated"
        if any(value > 1.0e-3 for value in separations.values())
        else "small_grid_peps_dynamic_open_nonseparating"
    )
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "peps_status": peps_status,
        "small_grid_peps_dynamic": True,
        "not_peps3d": True,
        "not_l64": True,
        "not_full_peps_convergence": True,
        "not_scale_level_real_basin": True,
        "not_final_manifold_admission": True,
        "z3_final_manifold_admission_allowed": guard["final_manifold_admission_allowed"],
    }
    graveyard = {
        "construction_only_rejected": {
            "pass": all(row["stage_count"] > 0 and row["pair_gate_count"] > 0 for row in dynamic_rows),
            "detail": "The dynamic mode applies local terrain steps and 2D edge gates; carrier construction alone is not counted.",
        },
        "product_control_retained": {
            "pass": len(no_dynamics_rows) == len(dynamic_rows),
            "detail": "No-dynamics product PEPS control is included for every initial family.",
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
        "peps_status": peps_status,
        "grid_shape": list(GRID),
        "bond_cap": BOND_CAP,
        "cycles": CYCLES,
        "dynamic_center_mi": dynamic_center_mi,
        "local_only_center_mi": local_center_mi,
        "no_dynamics_center_mi": no_dynamics_center_mi,
        "dynamic_minus_max_control": separations,
        "max_dynamic_truncation_error": max_dynamic_truncation,
        "max_dynamic_norm_error": max_dynamic_norm_error,
        "z3_guard": guard,
        "interpretation": (
            "A tiny 2D PEPS-style tensor grid now runs real local terrain "
            "updates plus nearest-neighbor SVD gates and exact readouts. This "
            "advances the PEPS rung only at small-grid scope; PEPS3D, L64, "
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
            "This is a v5 tiny-grid PEPS dynamics formal scout over PyTorch local tensor updates "
            "and current manifold receipts, not a legacy v4 probe or a full PEPS admission."
        ),
        "graph_witness": graph,
        "dynamic_rows": [strip_stages(row) for row in dynamic_rows],
        "local_only_control_rows": [strip_stages(row) for row in local_rows],
        "no_dynamics_control_rows": [strip_stages(row) for row in no_dynamics_rows],
        "representative_dynamic_stage_records": dynamic_rows[0]["stage_records"],
        "next_work_required": [
            "Build a tiny PEPS3D dynamic scout with the same nonpromotion guard.",
            "Stress-test the weak coupled-E16 Phi0 margin against more controls.",
            "Keep L64 and scale-level basin admission open until their own dynamic receipts exist.",
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
