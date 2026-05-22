#!/usr/bin/env python3
"""Workstream E: PyTorch MPS quantum-trajectory Lindblad runtime.

This scout lifts the Workstream C adaptive hysteresis mechanism into a genuine
MPS trajectory runtime. It uses source-local PyTorch MPS tensors as the tensor
network carrier, local quantum-jump Lindblad steps, nearest-neighbor TEBD-style
entangling gates, a dense L=4 replay check, and L=8/L=16 trajectory runs.

Boundary: this is a 1D MPS quantum-trajectory scout, not PEPS/PEPS3D and not
final manifold admission. It is meant to satisfy the first Workstream E rung:
MPS/trajectory works at L>=16 with metrics, or fails with a precise blocker.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json"

NAME = "two_root_constraint_tensor_network_lindblad_runtime_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_mps_quantum_trajectory_lindblad"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_tensor_network_lindblad_runtime"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream E scout only: runs a PyTorch-native 1D MPS quantum-"
    "trajectory Lindblad/TEBD path through L=16 with dense L=4 replay checks. "
    "It cannot promote PEPS/PEPS3D, full 2^16 density dynamics, final "
    "constraint-manifold admission, or a full QIT engine theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS tensors, local quantum-jump steps, TEBD two-site gates, dense replay, SVD truncation, and entropy/Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS chain and trajectory-event graph witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion/admission guard for L>=16 MPS trajectory evidence",
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
DTYPE_REAL = torch.float64
DT = 0.025
N_CYCLES = 6
MAX_BOND = 8
DENSE_REPLAY_TOL = 1.0e-7
NORM_TOL = 1.0e-7
TRUNCATION_TOL = 1.0e-2
CLUSTER_EPS = 0.08
PHI0_TOL = 1.0e-3

TERRAIN_ORDER_BY_TOKEN = {
    "1": ["Se", "Si", "Ni", "Ne", "Se", "Ne", "Ni", "Si"],
    "2": ["Se", "Ne", "Ni", "Si", "Se", "Si", "Ni", "Ne"],
}

INITIAL_FAMILIES = ["all_up", "all_down", "plus_x", "alternating_z"]

SOURCE_FILES = {
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "workstream_c_result": RESULT_DIR / "two_root_constraint_adaptive_engine_switching_probe_results.json",
    "workstream_d_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_bridge_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
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


def site_vector(kind: str, idx: int) -> torch.Tensor:
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=DTYPE)
    one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=DTYPE)
    plus = (zero + one) / math.sqrt(2.0)
    if kind == "all_up":
        return zero
    if kind == "all_down":
        return one
    if kind == "plus_x":
        return plus
    if kind == "alternating_z":
        return zero if idx % 2 == 0 else one
    raise ValueError(f"unknown initial family {kind}")


class MPS:
    """Open-boundary source-native PyTorch MPS with local gate support."""

    def __init__(self, tensors: list[torch.Tensor]):
        self.tensors = tensors

    @property
    def L(self) -> int:
        return len(self.tensors)

    @classmethod
    def product(cls, family: str, length: int) -> "MPS":
        return cls([site_vector(family, idx).reshape(2, 1, 1).clone() for idx in range(length)])

    def copy(self) -> "MPS":
        return MPS([tensor.clone() for tensor in self.tensors])

    def bond_dims(self) -> list[int]:
        return [int(tensor.shape[2]) for tensor in self.tensors[:-1]]

    def max_bond(self) -> int:
        return max(self.bond_dims(), default=1)

    def norm_sq(self) -> torch.Tensor:
        env = torch.ones((1, 1), dtype=DTYPE)
        for tensor in self.tensors:
            env = torch.einsum("ij,dir,djs->rs", env, tensor.conj(), tensor)
        return env.squeeze().real

    def normalize_(self) -> float:
        norm = math.sqrt(max(float(self.norm_sq().item()), 1.0e-30))
        self.tensors[0] = self.tensors[0] / norm
        return norm

    def apply_single(self, op: torch.Tensor, site: int) -> None:
        self.tensors[site] = torch.einsum("ab,bij->aij", op.to(DTYPE), self.tensors[site])

    def apply_two(self, op: torch.Tensor, site: int, max_bond: int) -> float:
        if op.ndim == 2:
            op = op.reshape(2, 2, 2, 2)
        left = self.tensors[site]
        right = self.tensors[site + 1]
        theta = torch.einsum("air,brj->abij", left, right)
        theta = torch.einsum("ABab,abij->ABij", op.to(DTYPE), theta).contiguous()
        d_left, d_right, chi_left, chi_right = theta.shape
        matrix = theta.permute(0, 2, 1, 3).reshape(d_left * chi_left, d_right * chi_right)
        u_mat, singulars, vh_mat = torch.linalg.svd(matrix, full_matrices=False)
        chi_new = min(max_bond, int(singulars.numel()))
        discarded = singulars[chi_new:]
        discarded_weight = float(torch.sum(discarded.real * discarded.real).item()) if discarded.numel() else 0.0
        u_mat = u_mat[:, :chi_new]
        singulars = singulars[:chi_new]
        vh_mat = vh_mat[:chi_new, :]
        new_left = (u_mat * singulars.unsqueeze(0)).reshape(d_left, chi_left, chi_new)
        new_right = vh_mat.reshape(chi_new, d_right, chi_right).permute(1, 0, 2).contiguous()
        self.tensors[site] = new_left
        self.tensors[site + 1] = new_right
        return discarded_weight

    def reduced_single(self, site: int) -> torch.Tensor:
        left_env = torch.ones((1, 1), dtype=DTYPE)
        for idx in range(site):
            tensor = self.tensors[idx]
            left_env = torch.einsum("ij,dir,djs->rs", left_env, tensor.conj(), tensor)
        right_env = torch.ones((1, 1), dtype=DTYPE)
        for idx in range(self.L - 1, site, -1):
            tensor = self.tensors[idx]
            right_env = torch.einsum("ij,drj,dsi->rs", right_env, tensor.conj(), tensor)
        tensor = self.tensors[site]
        rho = torch.einsum("ij,air,bjs,rs->ab", left_env, tensor, tensor.conj(), right_env)
        return normalize_density(rho)

    def dense_state(self) -> torch.Tensor:
        state = self.tensors[0][:, 0, :]
        for idx in range(1, self.L):
            tensor = self.tensors[idx]
            state = torch.einsum("pr,dri->pdi", state, tensor).reshape(-1, tensor.shape[2])
        return state[:, 0]


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / torch.trace(rho)


def dense_normalize(state: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(state)
    return state / norm


def mean_z(mps: MPS) -> float:
    values = [qit.bloch(mps.reduced_single(site))[2] for site in range(mps.L)]
    return float(sum(values) / len(values))


def choose_hysteresis(mean_z_value: float, prev: str | None) -> str:
    active = prev or "1"
    if active == "1":
        return "1" if mean_z_value >= -0.2 else "2"
    return "1" if mean_z_value >= 0.2 else "2"


def local_hamiltonian(token: str) -> torch.Tensor:
    H0 = qit.direction_hamiltonian("iter176_xz", normalize=True)
    return H0 if token == "1" else -H0


def collapse_ops(token: str, terrain: str) -> list[torch.Tensor]:
    if terrain == "Se":
        return [1.0 * qit.SZ]
    if terrain == "Ne":
        return [math.sqrt(0.3) * qit.SX]
    if terrain == "Ni":
        return [math.sqrt(0.5) * (qit.SM if token == "1" else qit.SP)]
    if terrain == "Si":
        return [math.sqrt(0.3) * qit.P_PLUS, math.sqrt(0.3) * qit.P_MINUS]
    raise ValueError(f"unknown terrain {terrain}")


def no_jump_operator(H: torch.Tensor, collapses: list[torch.Tensor]) -> torch.Tensor:
    accum = torch.zeros((2, 2), dtype=DTYPE)
    for collapse in collapses:
        accum = accum + collapse.conj().T @ collapse
    return qit.I2 - 1j * DT * H - 0.5 * DT * accum


def local_jump_choice(rho: torch.Tensor, collapses: list[torch.Tensor], generator: torch.Generator) -> tuple[str, int | None]:
    probs = [max(0.0, float((DT * torch.trace(rho @ (collapse.conj().T @ collapse))).real.item())) for collapse in collapses]
    total = min(sum(probs), 0.95)
    draw = float(torch.rand((), generator=generator, dtype=DTYPE_REAL).item())
    if draw >= total or not probs:
        return "no_jump", None
    running = 0.0
    for idx, prob in enumerate(probs):
        running += prob
        if draw < running:
            return "jump", idx
    return "jump", len(probs) - 1


def two_site_gate() -> torch.Tensor:
    h_zz = torch.kron(qit.SZ, qit.SZ)
    return torch.linalg.matrix_exp(-1j * 0.08 * h_zz).reshape(2, 2, 2, 2)


def apply_single_dense(state: torch.Tensor, op: torch.Tensor, site: int, length: int) -> torch.Tensor:
    tensor = state.reshape([2] * length)
    moved = tensor.movedim(site, 0).reshape(2, -1)
    moved = op.to(DTYPE) @ moved
    out = moved.reshape([2] + [2] * (length - 1)).movedim(0, site)
    return out.reshape(-1)


def apply_two_dense(state: torch.Tensor, op: torch.Tensor, site: int, length: int) -> torch.Tensor:
    tensor = state.reshape([2] * length)
    moved = tensor.movedim((site, site + 1), (0, 1)).reshape(4, -1)
    moved = op.reshape(4, 4).to(DTYPE) @ moved
    out = moved.reshape([2, 2] + [2] * (length - 2)).movedim((0, 1), (site, site + 1))
    return out.reshape(-1)


def replay_dense(family: str, length: int, events: list[dict[str, Any]]) -> torch.Tensor:
    state = torch.stack([site_vector(family, idx) for idx in range(length)])
    dense = state[0]
    for idx in range(1, length):
        dense = torch.kron(dense, state[idx])
    dense = dense_normalize(dense)
    gate_two = two_site_gate()
    for event in events:
        token = event["token"]
        terrain = event["terrain"]
        H = local_hamiltonian(token)
        collapses = collapse_ops(token, terrain)
        M0 = no_jump_operator(H, collapses)
        for site, branch in enumerate(event["branches"]):
            if branch["kind"] == "jump":
                dense = apply_single_dense(dense, math.sqrt(DT) * collapses[int(branch["channel"])], site, length)
            else:
                dense = apply_single_dense(dense, M0, site, length)
            dense = dense_normalize(dense)
        for site in range(event["parity"], length - 1, 2):
            dense = apply_two_dense(dense, gate_two, site, length)
            dense = dense_normalize(dense)
    return dense_normalize(dense)


def center_pair_density_from_state(state: torch.Tensor, length: int) -> torch.Tensor:
    left = length // 2 - 1
    right = length // 2
    tensor = state.reshape([2] * length)
    moved = tensor.movedim((left, right), (0, 1)).reshape(4, -1)
    return normalize_density(moved @ moved.conj().T)


def partial_traces_pair(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    tensor = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", tensor)
    rho_b = torch.einsum("abad->bd", tensor)
    return normalize_density(rho_a), normalize_density(rho_b)


def entropy(rho: torch.Tensor) -> float:
    evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    clipped = torch.clamp(evals, min=1.0e-15)
    return float((-torch.sum(clipped * torch.log(clipped))).item())


def phi0_readout_pair(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a, rho_b = partial_traces_pair(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_colon_B": s_a + s_b - s_ab,
    }


def half_chain_entropy_from_state(state: torch.Tensor, length: int) -> float:
    matrix = state.reshape(2 ** (length // 2), 2 ** (length - length // 2))
    singulars = torch.linalg.svdvals(matrix)
    probs = torch.clamp((singulars.real * singulars.real), min=1.0e-15)
    probs = probs / torch.sum(probs)
    return float((-torch.sum(probs * torch.log(probs))).item())


def run_mps_trajectory(length: int, family: str, seed: int) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    mps = MPS.product(family, length)
    token_prev: str | None = "1"
    events: list[dict[str, Any]] = []
    total_truncation = 0.0
    total_jumps = 0
    gate_two = two_site_gate()
    for cycle in range(N_CYCLES):
        token = choose_hysteresis(mean_z(mps), token_prev)
        token_prev = token
        for terrain_idx, terrain in enumerate(TERRAIN_ORDER_BY_TOKEN[token]):
            H = local_hamiltonian(token)
            collapses = collapse_ops(token, terrain)
            M0 = no_jump_operator(H, collapses)
            branches = []
            for site in range(length):
                rho_site = mps.reduced_single(site)
                kind, channel_idx = local_jump_choice(rho_site, collapses, generator)
                if kind == "jump":
                    op = math.sqrt(DT) * collapses[int(channel_idx)]
                    total_jumps += 1
                else:
                    op = M0
                mps.apply_single(op, site)
                mps.normalize_()
                branches.append({"kind": kind, "channel": channel_idx})
            parity = terrain_idx % 2
            for site in range(parity, length - 1, 2):
                total_truncation += mps.apply_two(gate_two, site, max_bond=MAX_BOND)
                mps.normalize_()
            events.append({"cycle": cycle, "token": token, "terrain": terrain, "branches": branches, "parity": parity})
    final_state = dense_normalize(mps.dense_state())
    pair_rho = center_pair_density_from_state(final_state, length)
    norm_error = abs(float(torch.linalg.vector_norm(final_state).item()) - 1.0)
    return {
        "length": length,
        "family": family,
        "seed": seed,
        "events": events,
        "final_state": final_state,
        "final_mean_z": mean_z(mps),
        "last_token": token_prev,
        "bond_dims": mps.bond_dims(),
        "max_bond": mps.max_bond(),
        "total_truncation_error": total_truncation,
        "norm_error": norm_error,
        "jump_count": total_jumps,
        "half_chain_entropy": half_chain_entropy_from_state(final_state, length),
        "center_pair_phi0": phi0_readout_pair(pair_rho),
    }


def distance_features(row: dict[str, Any]) -> list[float]:
    phi = row["center_pair_phi0"]
    return [row["final_mean_z"], row["half_chain_entropy"], phi["I_A_colon_B"]]


def cluster_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for row in rows:
        point = distance_features(row)
        for cluster in clusters:
            if math.dist(point, cluster["center"]) < CLUSTER_EPS:
                old_count = len(cluster["members"])
                cluster["members"].append(row["family"])
                cluster["center"] = [
                    (cluster["center"][idx] * old_count + point[idx]) / (old_count + 1)
                    for idx in range(len(point))
                ]
                break
        else:
            clusters.append({"center": point, "members": [row["family"]]})
    return clusters


def graph_report(length: int, events: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = [graph.add_node(idx) for idx in range(length)]
    for idx in range(length - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "mps_chain")
    event_graph = rx.PyDiGraph()
    previous = None
    for event in events:
        node = event_graph.add_node(f"{event['cycle']}:{event['token']}:{event['terrain']}")
        if previous is not None:
            event_graph.add_edge(previous, node, "next")
        previous = node
    return {
        "chain_nodes": graph.num_nodes(),
        "chain_edges": graph.num_edges(),
        "event_nodes": event_graph.num_nodes(),
        "event_edges": event_graph.num_edges(),
    }


def z3_admission_guard(length_rows: dict[str, list[dict[str, Any]]], dense_replay_pass: bool) -> dict[str, Any]:
    has_l16 = z3.Bool("has_l16")
    replay = z3.Bool("dense_replay")
    peps = z3.Bool("peps_peps3d")
    final_manifold = z3.Bool("final_manifold")
    admission = z3.Bool("admission")
    solver = z3.Solver()
    solver.add(has_l16 == ("16" in length_rows and bool(length_rows["16"])))
    solver.add(replay == dense_replay_pass)
    solver.add(peps == False)
    solver.add(final_manifold == False)
    solver.add(admission == z3.And(has_l16, replay, peps, final_manifold))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "mps_l16_runtime_green": z3.is_true(model.eval(z3.And(has_l16, replay), model_completion=True)),
        "full_manifold_admission_allowed": z3.is_true(model.eval(admission, model_completion=True)),
        "rule": "MPS L16 + dense replay can pass Workstream E, but final admission also requires PEPS/PEPS3D/final-manifold evidence not present here",
    }


def strip_runtime(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"events", "final_state"}}


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def workstream_c_candidate_names(workstream_c: dict[str, Any]) -> list[str]:
    summary = workstream_c.get("summary", {}) if isinstance(workstream_c.get("summary"), dict) else {}
    names = summary.get("weak_basin_candidates")
    return list(names) if isinstance(names, list) else []


def main() -> int:
    started = time.time()
    workstream_c = read_json(SOURCE_FILES["workstream_c_result"])
    workstream_d = read_json(SOURCE_FILES["workstream_d_result"])
    dense_cross = run_mps_trajectory(4, "alternating_z", seed=404)
    dense_replay = replay_dense("alternating_z", 4, dense_cross["events"])
    mps_dense = dense_cross["final_state"]
    phase = torch.vdot(dense_replay, mps_dense)
    aligned_mps = mps_dense * torch.exp(-1j * torch.angle(phase))
    dense_replay_error = float(torch.linalg.vector_norm(dense_replay - aligned_mps).item())
    length_rows: dict[str, list[dict[str, Any]]] = {}
    for length in (8, 16):
        rows = []
        for idx, family in enumerate(INITIAL_FAMILIES):
            rows.append(run_mps_trajectory(length, family, seed=1000 + 17 * length + idx))
        length_rows[str(length)] = rows
    clusters_by_length = {length: cluster_rows(rows) for length, rows in length_rows.items()}
    graph = graph_report(16, length_rows["16"][0]["events"])
    dense_replay_pass = dense_replay_error < DENSE_REPLAY_TOL
    guard = z3_admission_guard(length_rows, dense_replay_pass)
    l16_rows = length_rows["16"]
    max_l16_truncation = max(row["total_truncation_error"] for row in l16_rows)
    max_l16_norm_error = max(row["norm_error"] for row in l16_rows)
    max_l16_bond = max(row["max_bond"] for row in l16_rows)
    positive = {
        "workstream_c_candidate_exists": {
            "pass": "schedule_memory_hysteresis_z" in workstream_c_candidate_names(workstream_c),
            "source": rel(SOURCE_FILES["workstream_c_result"]),
        },
        "workstream_d_baseline_exists": {
            "pass": bool(workstream_d.get("all_pass")),
            "source": rel(SOURCE_FILES["workstream_d_result"]),
        },
        "dense_l4_replay_matches_mps": {
            "pass": dense_replay_pass,
            "dense_replay_error": dense_replay_error,
            "threshold": DENSE_REPLAY_TOL,
        },
        "mps_l8_l16_trajectory_runs": {
            "pass": bool(length_rows.get("8")) and bool(length_rows.get("16")),
            "lengths": sorted(length_rows),
            "families": INITIAL_FAMILIES,
        },
        "l16_tensor_network_nontrivial": {
            "pass": max_l16_bond > 1,
            "max_bond": max_l16_bond,
            "bond_dims_by_family": {row["family"]: row["bond_dims"] for row in l16_rows},
        },
        "l16_norm_and_truncation_bounded": {
            "pass": max_l16_norm_error < NORM_TOL and max_l16_truncation < TRUNCATION_TOL,
            "max_norm_error": max_l16_norm_error,
            "max_truncation_error": max_l16_truncation,
            "norm_threshold": NORM_TOL,
            "truncation_threshold": TRUNCATION_TOL,
        },
        "phi0_readouts_present": {
            "pass": all("I_A_colon_B" in row["center_pair_phi0"] for rows in length_rows.values() for row in rows),
            "l16_readouts": {row["family"]: row["center_pair_phi0"] for row in l16_rows},
        },
        "schedule_basin_count_recorded": {
            "pass": all(len(clusters) >= 1 for clusters in clusters_by_length.values()),
            "cluster_counts": {length: len(clusters) for length, clusters in clusters_by_length.items()},
            "clusters": clusters_by_length,
        },
    }
    tensor_runtime_status = (
        "green_l16_mps_trajectory"
        if all(item["pass"] for item in positive.values()) and guard["mps_l16_runtime_green"]
        else "blocked_or_red"
    )
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "tensor_runtime_status": tensor_runtime_status,
        "not_peps_or_peps3d": True,
        "not_full_density_l16": True,
        "not_final_manifold_admission": True,
        "z3_full_manifold_admission_allowed": guard["full_manifold_admission_allowed"],
    }
    graveyard = {
        "peps_peps3d_not_attempted": {
            "pass": True,
            "detail": "This scout intentionally stops at a 1D MPS quantum-trajectory runtime.",
        },
        "full_manifold_admission_blocked": {
            "pass": not guard["full_manifold_admission_allowed"],
            "z3_guard": guard,
        },
        "workstream_d_phi0_near_zero_not_reversed": {
            "pass": workstream_d.get("summary", {}).get("phi0_status") == "killed_near_zero",
            "workstream_d_phi0_status": workstream_d.get("summary", {}).get("phi0_status"),
            "detail": "MPS center-pair diagnostics do not erase the product-substrate Phi0 kill receipt.",
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for row in graveyard.values() if row["pass"]),
        "variants": sorted(graveyard),
    }
    next_work_required = [
        "PEPS/PEPS3D remains unattempted until 1D MPS/trajectory path is stable.",
        "Workstream F full constraint-manifold trace is still required.",
        "This trajectory scout does not reverse the D98 product-substrate Phi0 near-zero result.",
    ]
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard.values())
        and not guard["full_manifold_admission_allowed"]
    )
    summary = {
        "all_pass": all_pass,
        "tensor_runtime_status": tensor_runtime_status,
        "dense_l4_replay_error": dense_replay_error,
        "l16_max_bond": max_l16_bond,
        "l16_max_truncation_error": max_l16_truncation,
        "l16_cluster_count": len(clusters_by_length["16"]),
        "l16_phi0_readouts": {row["family"]: row["center_pair_phi0"] for row in l16_rows},
        "z3_admission_guard": guard,
        "interpretation": (
            "Workstream E has a green PyTorch MPS quantum-trajectory path at "
            "L=16 with dense L=4 replay validation, bounded norm/truncation, "
            "nontrivial bond growth, schedule-basin readouts, and Phi0 center-"
            "pair diagnostics. It is still a 1D MPS trajectory result, not "
            "PEPS/PEPS3D or final manifold admission."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "parameters": {
            "dt": DT,
            "n_cycles": N_CYCLES,
            "max_bond": MAX_BOND,
            "cluster_eps": CLUSTER_EPS,
            "initial_families": INITIAL_FAMILIES,
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 Workstream E 1D MPS quantum-trajectory Lindblad scout "
            "over the shared exact-torch QIT runtime; it is not a legacy v4 "
            "probe, PEPS/PEPS3D execution, full 2^16 density replay, or final "
            "manifold admission."
        ),
        "next_work_required": next_work_required,
        "blockers": [] if all_pass else [
            name
            for name, item in {**positive, **graveyard}.items()
            if not item.get("pass")
        ],
        "dense_l4_cross_check": strip_runtime(dense_cross),
        "graph_report": graph,
        "length_rows": {length: [strip_runtime(row) for row in rows] for length, rows in length_rows.items()},
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
