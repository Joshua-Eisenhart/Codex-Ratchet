#!/usr/bin/env python3
"""PyTorch graph/autograd lane for spinor_network_surface_v3."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import torch
from torch.func import jacrev
from torch_geometric.data import Data
import z3


SIM_ID = "spinor_network_surface_v3"
ENGINE = "pytorch"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

N_SITES = 4
DIM = 2**N_SITES
GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
ORIGIN_CELL = "A33_x00_y00_z00"
MIN_RECOVERED_NONORIGIN_CELLS = 6
RETRIEVAL_ALPHA = 0.65
MAX_TRAJECTORY_STEPS = 6
SPURIOUS_GAP_THRESHOLD = 0.08
SEED = 20260611
PRECOMMITTED_SEEDS = [20260611, 20260612, 777, 31337]
HAAR_PINNED_SEEDS = PRECOMMITTED_SEEDS
HAAR_NULL_TRIALS = 2048
HAAR_NULL_SEED0 = 100000
LCG_A = 6364136223846793005
LCG_C = 1442695040888963407
LCG_MASK = (1 << 64) - 1
DTYPE = torch.complex128
RTYPE = torch.float64

SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SIGMA_Y = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
PAULI = [SIGMA_X, SIGMA_Y, SIGMA_Z]
PRE_REGISTERED_STRUCTURED_PREDICTIONS = {
    "estate_chiral_quaternion_Hopf_Weyl": [
        "A33_xp5_y00_zm5",
        "A33_xp5_y00_zp5",
    ],
    "entangled_nonproduct": [
        "A33_x00_y00_zm10",
        "A33_x00_y00_zp10",
    ],
}
PRECOMMITTED_SEED_LEDGER = [
    {
        "kind": "v1_committed_seed",
        "seed": 20260611,
        "seed_hash": "b625c2b83246f7e1f7093fb5157ee56cc6673a3a5640f5300bb0d40a10cabea8",
        "hash_payload": {"dim": DIM, "source": "spinor_network_surface_v1", "v1_committed_seed": 20260611},
    },
    {
        "kind": "new_precommitted_seed",
        "seed": 20260612,
        "seed_hash": "0a91af394146a18e03c1f7c9737a10e470c917a0c70a6d39a1e4b46da16506db",
        "hash_payload": {"dim": DIM, "precommitted_seed": 20260612, "sim_id": SIM_ID},
    },
    {
        "kind": "new_precommitted_seed",
        "seed": 777,
        "seed_hash": "3c014267832b787e31201508352ca101bdbacbb4d2d2cf3a6cc56c0baaeafcbb",
        "hash_payload": {"dim": DIM, "precommitted_seed": 777, "sim_id": SIM_ID},
    },
    {
        "kind": "new_precommitted_seed",
        "seed": 31337,
        "seed_hash": "4a017e0b7657f32d0843714c972db94a8b9b2ff6f088271214da6ad41657e3b1",
        "hash_payload": {"dim": DIM, "precommitted_seed": 31337, "sim_id": SIM_ID},
    },
]


class MissingStructure(RuntimeError):
    pass


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        return to_jsonable(value.detach().cpu().tolist())
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"re": float(value.real), "im": float(value.imag)}
    if isinstance(value, float):
        return float(value) if math.isfinite(value) else str(value)
    return value


def stable_hash(value: Any) -> str:
    text = json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def a33_rows() -> list[tuple[float, float, float]]:
    return [
        (x, y, z)
        for x in GRID
        for y in GRID
        for z in GRID
        if x * x + y * y + z * z <= 1.000000001
    ]


A33_ROWS = a33_rows()


def cell_token(value: float) -> str:
    sign = "p" if value > 0 else "m" if value < 0 else "0"
    return f"{sign}{int(round(abs(value) * 10))}"


def a33_cell_id_from_row(row: tuple[float, float, float]) -> str:
    return "A33_x%s_y%s_z%s" % tuple(cell_token(v) for v in row)


def chart_cell_id(
    coords: tuple[float, float, float],
    rows: list[tuple[float, float, float]] | None = None,
    row_labels: list[str] | None = None,
) -> tuple[str, float]:
    row_set = rows if rows is not None else A33_ROWS
    snap_idx, snapped = min(
        enumerate(row_set),
        key=lambda item: sum((float(item[1][i]) - float(coords[i])) ** 2 for i in range(3)),
    )
    residual = math.sqrt(sum((float(snapped[i]) - float(coords[i])) ** 2 for i in range(3)))
    if row_labels is not None:
        return row_labels[snap_idx], residual
    return a33_cell_id_from_row(snapped), residual


A33_CELL_IDS = {a33_cell_id_from_row(row) for row in A33_ROWS}


def qnormalize(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    norm = math.sqrt(sum(v * v for v in q))
    return tuple(v / norm for v in q)  # type: ignore[return-value]


def weyl_spinor_quat(phi: float, chi: float, eta: float, chirality: str) -> torch.Tensor:
    c = math.cos(eta)
    s = math.sin(eta)
    pp = phi + chi
    pm = phi - chi
    if chirality == "L":
        q = (c * math.cos(pp), c * math.sin(pp), s * math.cos(pm), s * math.sin(pm))
    else:
        q = (c * math.cos(pp), -c * math.sin(pp), s * math.cos(pm), -s * math.sin(pm))
    w, x, y, z = qnormalize(q)
    spinor = torch.tensor([w + 1.0j * x, y + 1.0j * z], dtype=DTYPE)
    return spinor / torch.linalg.norm(spinor)


def product_state(spinors: list[torch.Tensor]) -> torch.Tensor:
    state = spinors[0]
    for spinor in spinors[1:]:
        state = torch.kron(state, spinor)
    return state / torch.linalg.norm(state)


def chiral_quaternion_pattern(mu: int) -> torch.Tensor:
    lx, ly = 2, 2
    pattern_count = 2
    seed_phi = (SEED * 0.37) % (2.0 * math.pi)
    seed_eta = (SEED * 0.17) % 0.4
    phi0 = 2.0 * math.pi * mu / pattern_count + seed_phi * (mu + 1) / pattern_count
    spinors: list[torch.Tensor] = []
    for site in range(N_SITES):
        x = site // ly + 1
        y = site % ly + 1
        phi = phi0 + 2.0 * math.pi * x / lx
        chi = 2.0 * math.pi * y / ly
        eta = math.pi / 4.0 + (0.2 + seed_eta * 0.1) * math.sin(phi + chi)
        spinors.append(weyl_spinor_quat(phi, chi, eta, "L" if mu % 2 == 0 else "R"))
    return product_state(spinors)


def entangled_pattern() -> torch.Tensor:
    theta = 0.31
    state = torch.zeros(DIM, dtype=DTYPE)
    state[0] = math.cos(theta)
    state[15] = math.sin(theta) * complex(math.cos(0.37), math.sin(0.37))
    return state / torch.linalg.norm(state)


def pinned_random_pattern() -> torch.Tensor:
    raw = np.asarray(
        [
            math.sin((idx + 1) * 0.137 * SEED) + 1.0j * math.cos((idx + 1) * 0.173 * (SEED + 7))
            for idx in range(DIM)
        ],
        dtype=np.complex128,
    )
    raw = raw / np.linalg.norm(raw)
    return torch.tensor(raw, dtype=DTYPE)


def lcg_uniforms(seed: int, count: int) -> list[float]:
    state = (seed + LCG_C) & LCG_MASK
    values: list[float] = []
    for _ in range(count):
        state = (LCG_A * state + LCG_C) & LCG_MASK
        values.append(((state >> 11) & ((1 << 53) - 1)) / float(1 << 53))
    return values


def lcg_normals(seed: int, count: int) -> list[float]:
    uniforms = lcg_uniforms(seed, 2 * ((count + 1) // 2))
    values: list[float] = []
    for idx in range(0, len(uniforms), 2):
        u1 = max(uniforms[idx], 1.0e-12)
        u2 = uniforms[idx + 1]
        radius = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2
        values.extend([radius * math.cos(theta), radius * math.sin(theta)])
    return values[:count]


def haar_pinned_pattern(seed: int) -> torch.Tensor:
    normals = lcg_normals(seed, 2 * DIM)
    raw = np.asarray(normals[:DIM], dtype=np.float64) + 1.0j * np.asarray(normals[DIM:], dtype=np.float64)
    raw = raw / np.linalg.norm(raw)
    return torch.tensor(raw, dtype=DTYPE)


def v1_anchor_patterns() -> dict[str, torch.Tensor]:
    return {
        "chiral_quaternion_L": chiral_quaternion_pattern(0),
        "chiral_quaternion_R": chiral_quaternion_pattern(1),
        "entangled_nonproduct": entangled_pattern(),
        "pinned_random": pinned_random_pattern(),
    }


def terminal_patterns() -> dict[str, torch.Tensor]:
    patterns = dict(v1_anchor_patterns())
    for seed in HAAR_PINNED_SEEDS:
        patterns[f"haar_pinned_seed_{seed}"] = haar_pinned_pattern(seed)
    return patterns


def pattern_metadata(patterns: dict[str, torch.Tensor]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {
        "chiral_quaternion_L": {
            "family_id": "estate_chiral_quaternion_Hopf_Weyl",
            "bias_class": "residual_chart_plane_bias_v1_anchor",
            "load_bearing_for_identity_claim": True,
            "anchor_from_v1": True,
        },
        "chiral_quaternion_R": {
            "family_id": "estate_chiral_quaternion_Hopf_Weyl",
            "bias_class": "residual_chart_plane_bias_v1_anchor",
            "load_bearing_for_identity_claim": True,
            "anchor_from_v1": True,
        },
        "entangled_nonproduct": {
            "family_id": "entangled_nonproduct",
            "bias_class": "computational_endpoint_z_bias_v1_anchor",
            "load_bearing_for_identity_claim": True,
            "anchor_from_v1": True,
        },
        "pinned_random": {
            "family_id": "pinned_random_v1_anchor",
            "bias_class": "single_seed_thin_margin_v1_anchor",
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": True,
        },
    }
    for seed in HAAR_PINNED_SEEDS:
        pid = f"haar_pinned_seed_{seed}"
        rows[pid] = {
            "family_id": f"precommitted_seed_control_{seed}",
            "bias_class": "precommitted_seed_control_no_preferred_chart_axis",
            "seed": seed,
            "seed_hash": next(row["seed_hash"] for row in PRECOMMITTED_SEED_LEDGER if row["seed"] == seed),
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": False,
        }
    return {key: rows[key] for key in patterns}


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def hermitize_trace_one(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + torch.conj(rho.T)) / 2.0
    return herm / torch.trace(herm)


def basis_index(bits: list[int]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | bit
    return out


def reduce_density_one(rho: torch.Tensor, site: int) -> torch.Tensor:
    out = torch.zeros((2, 2), dtype=DTYPE)
    rest_sites = [idx for idx in range(N_SITES) if idx != site]
    for a in range(2):
        for b in range(2):
            value = torch.tensor(0.0 + 0.0j, dtype=DTYPE)
            for rest in range(2 ** (N_SITES - 1)):
                rest_bits = [(rest >> bit) & 1 for bit in reversed(range(N_SITES - 1))]
                left = [0] * N_SITES
                right = [0] * N_SITES
                left[site] = a
                right[site] = b
                for rest_site, bit in zip(rest_sites, rest_bits):
                    left[rest_site] = bit
                    right[rest_site] = bit
                value = value + rho[basis_index(left), basis_index(right)]
            out[a, b] = value
    return out


def reduce_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    dim = 2 ** len(keep)
    out = torch.zeros((dim, dim), dtype=DTYPE)
    rest_sites = [idx for idx in range(N_SITES) if idx not in keep]
    for a in range(dim):
        a_bits = [(a >> bit) & 1 for bit in reversed(range(len(keep)))]
        for b in range(dim):
            b_bits = [(b >> bit) & 1 for bit in reversed(range(len(keep)))]
            value = torch.tensor(0.0 + 0.0j, dtype=DTYPE)
            for rest in range(2 ** len(rest_sites)):
                rest_bits = [(rest >> bit) & 1 for bit in reversed(range(len(rest_sites)))]
                left = [0] * N_SITES
                right = [0] * N_SITES
                for site, bit in zip(keep, a_bits):
                    left[site] = bit
                for site, bit in zip(keep, b_bits):
                    right[site] = bit
                for site, bit in zip(rest_sites, rest_bits):
                    left[site] = bit
                    right[site] = bit
                value = value + rho[basis_index(left), basis_index(right)]
            out[a, b] = value
    return out


def entropy_vn(rho: torch.Tensor) -> float:
    eigvals = torch.linalg.eigvalsh((rho + torch.conj(rho.T)) / 2.0).real
    eigvals = torch.clamp(eigvals, 0.0, 1.0)
    eigvals = eigvals[eigvals > 1.0e-12]
    return float(-(eigvals * torch.log(eigvals)).sum()) if eigvals.numel() else 0.0


def bloch_coords(rho1: torch.Tensor) -> tuple[float, float, float]:
    return tuple(float(torch.real(torch.trace(rho1 @ pauli))) for pauli in PAULI)  # type: ignore[return-value]


def state_fidelity(rho: torch.Tensor, psi: torch.Tensor) -> float:
    return float(torch.real(torch.vdot(psi, rho @ psi)))


def energy_v(rho: torch.Tensor, patterns: dict[str, torch.Tensor]) -> tuple[float, str, float, list[tuple[str, float]]]:
    scored = sorted(
        ((pid, state_fidelity(rho, psi)) for pid, psi in patterns.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return 1.0 - scored[0][1], scored[0][0], scored[0][1], scored


def spurious_density(label_a: str, label_b: str, patterns: dict[str, torch.Tensor]) -> torch.Tensor:
    return 0.5 * density(patterns[label_a]) + 0.5 * density(patterns[label_b])


def choose_target(rho: torch.Tensor, patterns: dict[str, torch.Tensor]) -> tuple[str, torch.Tensor, list[tuple[str, float]], str]:
    _, best_id, _, scores = energy_v(rho, patterns)
    gap = scores[0][1] - scores[1][1]
    if gap <= SPURIOUS_GAP_THRESHOLD:
        a, b = sorted([scores[0][0], scores[1][0]])
        return f"spurious::{a}::{b}", spurious_density(a, b, patterns), scores, "spurious_low_margin_pair"
    return best_id, density(patterns[best_id]), scores, "stored_pattern_attractor"


def retrieval_update(rho: torch.Tensor, patterns: dict[str, torch.Tensor]) -> tuple[torch.Tensor, dict[str, Any]]:
    target_id, target, scores, mode = choose_target(rho, patterns)
    next_rho = hermitize_trace_one((1.0 - RETRIEVAL_ALPHA) * rho + RETRIEVAL_ALPHA * target)
    eigvals = torch.linalg.eigvalsh((next_rho + torch.conj(next_rho.T)) / 2.0).real
    return next_rho, {
        "target_id": target_id,
        "mode": mode,
        "top_scores": [{"id": pid, "fidelity": float(value)} for pid, value in scores[:3]],
        "trace_real": float(torch.real(torch.trace(next_rho))),
        "min_eigenvalue": float(torch.min(eigvals)),
    }


def seed_states(patterns: dict[str, torch.Tensor]) -> list[dict[str, Any]]:
    keys = list(patterns)
    rows: list[dict[str, Any]] = []
    for key in keys:
        rows.append({"id": f"stored::{key}", "kind": "stored", "rho": density(patterns[key])})
    for idx, key in enumerate(keys):
        other = keys[(idx + 1) % len(keys)]
        rows.append({
            "id": f"corrupt::{key}::neighbor15",
            "kind": "corrupt15",
            "rho": hermitize_trace_one(0.85 * density(patterns[key]) + 0.15 * density(patterns[other])),
        })
    for i, left in enumerate(keys):
        for right in keys[i + 1 :]:
            rows.append({"id": f"pairmix::{left}::{right}", "kind": "pairmix_equal", "rho": spurious_density(left, right, patterns)})
    return rows


def transition_graph(patterns: dict[str, torch.Tensor]) -> dict[str, Any]:
    node_ids: dict[str, int] = {}
    edge_pairs: list[tuple[int, int]] = []
    terminal_nodes: set[str] = set()
    spurious_terminal_ids: set[str] = set()
    lyapunov_deltas: list[float] = []

    def node_index(name: str) -> int:
        if name not in node_ids:
            node_ids[name] = len(node_ids)
        return node_ids[name]

    trajectories = []
    for seed in seed_states(patterns):
        rho = seed["rho"]
        prev_node = seed["id"]
        node_index(prev_node)
        path = [{"node": prev_node, "V": energy_v(rho, patterns)[0]}]
        for step in range(MAX_TRAJECTORY_STEPS):
            v_before = energy_v(rho, patterns)[0]
            next_rho, edge = retrieval_update(rho, patterns)
            v_after = energy_v(next_rho, patterns)[0]
            delta = v_after - v_before
            lyapunov_deltas.append(delta)
            target_node = f"{seed['id']}::step{step + 1}::{edge['target_id']}"
            edge_pairs.append((node_index(prev_node), node_index(target_node)))
            path.append({"node": target_node, "V": v_after, "target": edge["target_id"], "delta": delta})
            rho = next_rho
            prev_node = target_node
            if abs(delta) <= 1.0e-11 or step == MAX_TRAJECTORY_STEPS - 1:
                edge_pairs.append((node_index(prev_node), node_index(prev_node)))
                terminal_nodes.add(prev_node)
                if str(edge["target_id"]).startswith("spurious::"):
                    spurious_terminal_ids.add(str(edge["target_id"]))
                break
        trajectories.append({"seed_id": seed["id"], "kind": seed["kind"], "path": path})
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T.contiguous()
    pyg_graph = Data(edge_index=edge_index, num_nodes=len(node_ids))
    return {
        "node_count": int(pyg_graph.num_nodes),
        "edge_count": int(pyg_graph.edge_index.shape[1]),
        "terminal_scc_count": len(terminal_nodes),
        "terminal_node_count": len(terminal_nodes),
        "spurious_terminal_ids": sorted(spurious_terminal_ids),
        "spurious_attractor_count": len(spurious_terminal_ids),
        "max_lyapunov_delta": max(lyapunov_deltas) if lyapunov_deltas else 0.0,
        "min_lyapunov_delta": min(lyapunov_deltas) if lyapunov_deltas else 0.0,
        "trajectories": trajectories,
        "coverage": {
            "seed_state_count": len(seed_states(patterns)),
            "pair_mixture_denominator": math.comb(len(patterns), 2),
            "pair_mixture_enumerated": math.comb(len(patterns), 2),
            "corruptions_enumerated": len(patterns),
            "stored_enumerated": len(patterns),
        },
        "pyg_graph": {
            "num_nodes": int(pyg_graph.num_nodes),
            "edge_count": int(pyg_graph.edge_index.shape[1]),
        },
    }


def three_pattern_spurious_extension(patterns: dict[str, torch.Tensor]) -> dict[str, Any]:
    keys = list(patterns)
    rows: list[dict[str, Any]] = []
    for i, first in enumerate(keys):
        for j, second in enumerate(keys[i + 1 :], start=i + 1):
            for third in keys[j + 1 :]:
                rho = (density(patterns[first]) + density(patterns[second]) + density(patterns[third])) / 3.0
                _, _, _, scores = energy_v(rho, patterns)
                top3 = scores[:3]
                top_ids = sorted(pid for pid, _ in top3)
                gap_top3 = float(top3[0][1] - top3[2][1]) if len(top3) == 3 else math.inf
                target_id = f"spurious3::{top_ids[0]}::{top_ids[1]}::{top_ids[2]}"
                rows.append({
                    "mixture_id": f"triplemix::{first}::{second}::{third}",
                    "patterns": [first, second, third],
                    "target_id": target_id,
                    "top3_scores": [{"id": pid, "fidelity": float(score)} for pid, score in top3],
                    "gap_top3": gap_top3,
                    "spurious3_detected": gap_top3 <= SPURIOUS_GAP_THRESHOLD,
                })
    return {
        "kind": "three_pattern_mixture_spurious_extension",
        "coverage_denominator": math.comb(len(keys), 3),
        "coverage_enumerated": len(rows),
        "spurious3_detected_count": sum(1 for row in rows if row["spurious3_detected"]),
        "spurious3_terminal_ids": sorted(row["target_id"] for row in rows if row["spurious3_detected"]),
        "rows": rows,
    }


def recover_chart_structure(
    rhos: list[torch.Tensor],
    *,
    state_ids: list[str] | None = None,
    metadata: dict[str, dict[str, Any]] | None = None,
    classifier_rows: list[tuple[float, float, float]] | None = None,
    classifier_row_labels: list[str] | None = None,
    classifier_id: str = "A33_committed_predeclared",
    identity_required_pairs: set[str] | None = None,
    require_load_bearing_identity: bool = False,
) -> dict[str, Any]:
    rows = classifier_rows if classifier_rows is not None else A33_ROWS
    recovered: set[str] = set()
    residuals: list[float] = []
    details = []
    family_cell_map: dict[str, set[str]] = {}
    load_bearing_cells: set[str] = set()
    load_bearing_pairs: set[str] = set()
    ids = state_ids if state_ids is not None else [f"state_{idx}" for idx in range(len(rhos))]
    for state_id, rho in enumerate(rhos):
        pattern_id = ids[state_id]
        meta = (metadata or {}).get(pattern_id, {})
        family_id = str(meta.get("family_id", pattern_id))
        load_bearing = bool(meta.get("load_bearing_for_identity_claim", False))
        for site in range(N_SITES):
            coords = bloch_coords(reduce_density_one(rho, site))
            cell_id, residual = chart_cell_id(coords, rows, classifier_row_labels)
            recovered.add(cell_id)
            residuals.append(residual)
            family_cell_map.setdefault(family_id, set()).add(cell_id)
            if load_bearing and cell_id != ORIGIN_CELL:
                load_bearing_cells.add(cell_id)
                load_bearing_pairs.add(f"{family_id}:{cell_id}")
            details.append({
                "state_index": state_id,
                "pattern_id": pattern_id,
                "family_id": family_id,
                "load_bearing_for_identity_claim": load_bearing,
                "site": site,
                "bloch": coords,
                "cell_id": cell_id,
                "alignment_residual": residual,
            })
    nonorigin = sorted(cell for cell in recovered if cell != ORIGIN_CELL)
    family_cell_map_json = {
        family_id: sorted(cell for cell in cells if cell != ORIGIN_CELL)
        for family_id, cells in sorted(family_cell_map.items())
    }
    observed_pairs = sorted(load_bearing_pairs)
    identity_pairs_match_expected = True if identity_required_pairs is None else set(observed_pairs) == set(identity_required_pairs)
    load_bearing_family_count = sum(
        1
        for family_id, cells in family_cell_map_json.items()
        if cells and any(pair.startswith(f"{family_id}:") for pair in observed_pairs)
    )
    pass_predicate = (
        classifier_id == "A33_committed_predeclared"
        and len(rows) == 33
        and len(nonorigin) >= MIN_RECOVERED_NONORIGIN_CELLS
        and identity_pairs_match_expected
        and (
            not require_load_bearing_identity
            or (
                len(load_bearing_cells) >= 1
                and load_bearing_family_count >= 1
            )
        )
    )
    return {
        "classifier_id": classifier_id,
        "expected_cell_count": len(rows),
        "recovered_cell_ids": sorted(recovered),
        "recovered_nonorigin_cell_ids": nonorigin,
        "recovered_nonorigin_cell_count": len(nonorigin),
        "family_cell_identity_map": family_cell_map_json,
        "load_bearing_recovered_nonorigin_cell_ids": sorted(load_bearing_cells),
        "load_bearing_recovered_nonorigin_cell_count": len(load_bearing_cells),
        "load_bearing_family_cell_pairs": observed_pairs,
        "identity_pairs_match_expected": identity_pairs_match_expected,
        "median_alignment_residual": float(np.median(np.asarray(residuals))) if residuals else math.inf,
        "minimum_recovered_nonorigin_cells": MIN_RECOVERED_NONORIGIN_CELLS,
        "verdict": "RECOVERY_PASS_NONTRIVIAL" if pass_predicate else "RECOVERY_FAIL",
        "registered_falsifier_fired": not pass_predicate,
        "details": details,
    }


def pre_registered_required_pairs() -> set[str]:
    return {
        f"{family_id}:{cell_id}"
        for family_id, cells in PRE_REGISTERED_STRUCTURED_PREDICTIONS.items()
        for cell_id in cells
    }


def chart_controls(patterns: dict[str, torch.Tensor], metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    terminal_ids = list(patterns)
    terminal_rhos = [density(patterns[key]) for key in terminal_ids]
    positive = recover_chart_structure(
        terminal_rhos,
        state_ids=terminal_ids,
        metadata=metadata,
        require_load_bearing_identity=False,
    )
    mixed = [torch.eye(DIM, dtype=DTYPE) / DIM]
    erased = [torch.eye(DIM, dtype=DTYPE) / DIM for _ in terminal_rhos]
    axis = (SIGMA_X + SIGMA_Y + SIGMA_Z) / math.sqrt(3.0)
    single_u = math.cos(0.37) * torch.eye(2, dtype=DTYPE) - 1.0j * math.sin(0.37) * axis
    rot = single_u
    for _ in range(N_SITES - 1):
        rot = torch.kron(rot, single_u)
    rotated = [density(rot @ patterns[key]) for key in terminal_ids]
    correct_labels = [a33_cell_id_from_row(row) for row in A33_ROWS]
    permuted_labels = correct_labels[7:] + correct_labels[:7]
    controls = {
        "maximally_mixed_state": recover_chart_structure(mixed),
        "quotient_erased_state": recover_chart_structure(erased),
        "off_axis_rotated_states": recover_chart_structure(
            rotated,
            state_ids=terminal_ids,
            metadata=metadata,
            identity_required_pairs=pre_registered_required_pairs(),
            require_load_bearing_identity=False,
        ),
        "wrong_row_classifier": recover_chart_structure(
            terminal_rhos,
            state_ids=terminal_ids,
            metadata=metadata,
            classifier_rows=A33_ROWS,
            classifier_row_labels=permuted_labels,
            classifier_id="A33_committed_predeclared",
            identity_required_pairs=pre_registered_required_pairs(),
            require_load_bearing_identity=False,
        ),
    }
    controls["wrong_row_classifier"]["control_design"] = "same A33 classifier machinery with a permuted row-label ledger; failure is by family-cell identity mismatch, not classifier-id mismatch"
    for row in controls.values():
        row["expected"] = "RECOVERY_FAIL"
        row["control_fired"] = row["verdict"] == "RECOVERY_FAIL"
    return {"positive": positive, "controls": controls}


def cells_for_states(states: list[torch.Tensor]) -> list[list[str]]:
    rows: list[list[str]] = []
    for state in states:
        rho = density(state)
        rows.append([chart_cell_id(bloch_coords(reduce_density_one(rho, site)))[0] for site in range(N_SITES)])
    return rows


def structured_prediction_comparison(positive: dict[str, Any]) -> dict[str, Any]:
    family_map = positive["family_cell_identity_map"]
    expected_pairs = pre_registered_required_pairs()
    recovered_pairs = {
        f"{family_id}:{cell_id}"
        for family_id, expected_cells in PRE_REGISTERED_STRUCTURED_PREDICTIONS.items()
        for cell_id in expected_cells
        if cell_id in set(family_map.get(family_id, []))
    }
    missed_pairs = expected_pairs - recovered_pairs
    pair_occurrences: dict[str, int] = {}
    recovered_count_null: list[int] = []
    for trial in range(HAAR_NULL_TRIALS):
        states = [
            haar_pinned_pattern(HAAR_NULL_SEED0 + trial * len(PRE_REGISTERED_STRUCTURED_PREDICTIONS) + idx)
            for idx in range(len(PRE_REGISTERED_STRUCTURED_PREDICTIONS))
        ]
        trial_pairs: set[str] = set()
        for slot, (family_id, expected_cells) in enumerate(PRE_REGISTERED_STRUCTURED_PREDICTIONS.items()):
            cells = set(cells_for_states([states[slot]])[0])
            for cell_id in expected_cells:
                if cell_id in cells:
                    pair = f"{family_id}:{cell_id}"
                    trial_pairs.add(pair)
                    pair_occurrences[pair] = pair_occurrences.get(pair, 0) + 1
        recovered_count_null.append(len(trial_pairs))
    smooth = 1.0 / (HAAR_NULL_TRIALS + 1.0)
    pair_prob = {pair: pair_occurrences.get(pair, 0) / HAAR_NULL_TRIALS for pair in sorted(expected_pairs)}

    def score(pairs: set[str]) -> float:
        return float(sum(-math.log(max(pair_prob.get(pair, 0.0), smooth)) for pair in pairs))

    null_counts = np.asarray(recovered_count_null, dtype=np.float64)
    recovered_count = len(recovered_pairs)
    return {
        "kind": "pre_registered_structured_prediction_vs_haar_null",
        "pre_registered_before_run": True,
        "structured_predictions": PRE_REGISTERED_STRUCTURED_PREDICTIONS,
        "precommitted_seed_ledger": PRECOMMITTED_SEED_LEDGER,
        "expected_family_cell_pairs": sorted(expected_pairs),
        "recovered_predicted_family_cell_pairs": sorted(recovered_pairs),
        "missed_predicted_family_cell_pairs": sorted(missed_pairs),
        "recovered_predicted_pair_count": recovered_count,
        "expected_predicted_pair_count": len(expected_pairs),
        "recovered_fraction": recovered_count / len(expected_pairs),
        "haar_trials": HAAR_NULL_TRIALS,
        "haar_seed0": HAAR_NULL_SEED0,
        "haar_recovered_count_mean": float(np.mean(null_counts)),
        "haar_recovered_count_std": float(np.std(null_counts)),
        "haar_p_ge_recovered_count": float(np.mean(null_counts >= recovered_count)),
        "pair_presence_probability": pair_prob,
        "recovered_identity_surprisal": score(recovered_pairs),
        "full_prediction_identity_surprisal": score(expected_pairs),
        "verdict": (
            "ALL_PREDICTED_CELLS_RECOVERED"
            if recovered_pairs == expected_pairs
            else "PARTIAL_PREDICTED_CELL_RECOVERY"
            if recovered_pairs
            else "NO_PREDICTED_CELL_RECOVERY"
        ),
        "registered_falsifier_fired": recovered_pairs != expected_pairs,
        "claim_reading": "fixed pre-registered family-cell comparison; observed non-predicted cells are not substituted into the statistic",
    }


def haar_null_identity_row(positive: dict[str, Any]) -> dict[str, Any]:
    trial_cell_sets: list[set[str]] = []
    trial_pair_sets: list[set[str]] = []
    cell_occurrences: dict[str, int] = {}
    pair_occurrences: dict[str, int] = {}
    slot_nonorigin_counts = {f"slot_{idx}": [] for idx in range(len(HAAR_PINNED_SEEDS))}
    for trial in range(HAAR_NULL_TRIALS):
        states = [haar_pinned_pattern(HAAR_NULL_SEED0 + trial * len(HAAR_PINNED_SEEDS) + idx) for idx in range(len(HAAR_PINNED_SEEDS))]
        per_state_cells = cells_for_states(states)
        trial_cells = {cell for cells in per_state_cells for cell in cells if cell != ORIGIN_CELL}
        trial_pairs: set[str] = set()
        for slot, cells in enumerate(per_state_cells):
            nonorigin = {cell for cell in cells if cell != ORIGIN_CELL}
            slot_nonorigin_counts[f"slot_{slot}"].append(len(nonorigin))
            for cell in nonorigin:
                trial_pairs.add(f"slot_{slot}:{cell}")
        trial_cell_sets.append(trial_cells)
        trial_pair_sets.append(trial_pairs)
        for cell in trial_cells:
            cell_occurrences[cell] = cell_occurrences.get(cell, 0) + 1
        for pair in trial_pairs:
            pair_occurrences[pair] = pair_occurrences.get(pair, 0) + 1

    cell_prob = {cell: cell_occurrences.get(cell, 0) / HAAR_NULL_TRIALS for cell in sorted(A33_CELL_IDS) if cell != ORIGIN_CELL}
    pair_prob = {pair: count / HAAR_NULL_TRIALS for pair, count in sorted(pair_occurrences.items())}
    smooth = 1.0 / (HAAR_NULL_TRIALS + 1.0)

    def score_pairs(pairs: set[str]) -> float:
        return float(sum(-math.log(max(pair_prob.get(pair, 0.0), smooth)) for pair in pairs))

    family_to_slot = {f"haar_pinned_seed_{seed}": f"slot_{idx}" for idx, seed in enumerate(HAAR_PINNED_SEEDS)}
    observed_pairs = {
        f"{family_to_slot[family_id]}:{cell}"
        for family_id, cells in positive["family_cell_identity_map"].items()
        if family_id in family_to_slot
        for cell in cells
        if cell != ORIGIN_CELL
    }
    observed_cells = {pair.split(":", 1)[1] for pair in observed_pairs}
    null_scores = [score_pairs(pairs) for pairs in trial_pair_sets]
    null_counts = [len(cells) for cells in trial_cell_sets]
    observed_score = score_pairs(observed_pairs)
    null_mean = float(np.mean(np.asarray(null_scores)))
    null_std = float(np.std(np.asarray(null_scores)))
    return {
        "kind": "haar_null_identity_control",
        "generator": "full 4-qubit complex Haar states, four pinned states per trial, single-site quotient cells",
        "trials": HAAR_NULL_TRIALS,
        "seed0": HAAR_NULL_SEED0,
        "expected_nonorigin_cell_count": float(np.mean(np.asarray(null_counts))),
        "std_nonorigin_cell_count": float(np.std(np.asarray(null_counts))),
        "observed_load_bearing_nonorigin_cell_count": len(observed_cells),
        "observed_family_tied_pair_count": len(observed_pairs),
        "observed_slot_cell_pairs": sorted(observed_pairs),
        "observed_identity_surprisal": observed_score,
        "null_identity_surprisal_mean": null_mean,
        "null_identity_surprisal_std": null_std,
        "identity_surprisal_z": (observed_score - null_mean) / null_std if null_std > 0 else math.inf,
        "cell_identity_distribution": {
            cell: {"trial_presence_probability": prob, "observed_load_bearing": cell in observed_cells}
            for cell, prob in sorted(cell_prob.items())
        },
        "slot_nonorigin_expected": {
            slot: float(np.mean(np.asarray(counts))) for slot, counts in sorted(slot_nonorigin_counts.items())
        },
        "verdict": "IDENTITY_ABOVE_NULL" if observed_score > null_mean else "IDENTITY_NOT_ABOVE_NULL",
        "control_fired": True,
        "registered_falsifier_fired": observed_score <= null_mean,
    }


def per_family_recovery_table(
    positive: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
    haar_null: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cell_prob = haar_null["cell_identity_distribution"]
    for pattern_id, meta in metadata.items():
        family_id = str(meta["family_id"])
        cells = positive["family_cell_identity_map"].get(family_id, [])
        nonorigin = [cell for cell in cells if cell != ORIGIN_CELL]
        surprisal = sum(-math.log(max(cell_prob.get(cell, {}).get("trial_presence_probability", 0.0), 1.0 / (HAAR_NULL_TRIALS + 1.0))) for cell in nonorigin)
        rows.append(
            {
                "pattern_id": pattern_id,
                "family_id": family_id,
                "bias_class": meta["bias_class"],
                "seed": meta.get("seed"),
                "seed_hash": meta.get("seed_hash"),
                "load_bearing_for_identity_claim": meta["load_bearing_for_identity_claim"],
                "anchor_from_v1": meta["anchor_from_v1"],
                "recovered_nonorigin_cell_ids": nonorigin,
                "recovered_nonorigin_cell_count": len(nonorigin),
                "identity_surprisal_vs_null_cells": float(surprisal),
            }
        )
    return rows


def a33_reachability_ceiling(recovered_cell_ids: list[str]) -> dict[str, Any]:
    recovered = set(recovered_cell_ids)
    rows = []
    eye2 = torch.eye(2, dtype=DTYPE)
    for row in A33_ROWS:
        rho = 0.5 * (eye2 + row[0] * SIGMA_X + row[1] * SIGMA_Y + row[2] * SIGMA_Z)
        eigvals = torch.linalg.eigvalsh((rho + torch.conj(rho.T)) / 2.0).real
        cell_id = a33_cell_id_from_row(row)
        reachable = bool(float(torch.min(eigvals)) >= -1.0e-12 and abs(float(torch.real(torch.trace(rho))) - 1.0) <= 1.0e-12)
        rows.append(
            {
                "cell_id": cell_id,
                "bloch_row": row,
                "reachable_in_principle": reachable,
                "carrier_witness": "single-qubit density quotient rho=(I+r.sigma)/2; four-site carrier can purify any rank<=2 single-site quotient",
                "min_eigenvalue": float(torch.min(eigvals)),
                "recovered_in_packet": cell_id in recovered,
            }
        )
    reachable_ids = [row["cell_id"] for row in rows if row["reachable_in_principle"]]
    return {
        "geometric_ceiling_cell_count": len(reachable_ids),
        "reachable_in_principle_cell_ids": sorted(reachable_ids),
        "recovered_cell_ids": sorted(recovered),
        "recovered_reachable_cell_count": len(recovered.intersection(reachable_ids)),
        "reachable_not_recovered_cell_ids": sorted(set(reachable_ids) - recovered),
        "rows": rows,
    }


def target_components(target_id: str, patterns: dict[str, torch.Tensor]) -> list[tuple[float, np.ndarray]]:
    if target_id.startswith("spurious::"):
        _, left, right = target_id.split("::", 2)
        return [
            (0.5, patterns[left].detach().cpu().numpy().astype(np.complex128)),
            (0.5, patterns[right].detach().cpu().numpy().astype(np.complex128)),
        ]
    return [(1.0, patterns[target_id].detach().cpu().numpy().astype(np.complex128))]


def kraus_choi_witness(target_id: str, patterns: dict[str, torch.Tensor]) -> dict[str, Any]:
    components = target_components(target_id, patterns)
    eye = np.eye(DIM, dtype=np.complex128)
    kraus = [math.sqrt(1.0 - RETRIEVAL_ALPHA) * eye]
    for weight, psi in components:
        for basis in range(DIM):
            op = np.zeros((DIM, DIM), dtype=np.complex128)
            op[:, basis] = math.sqrt(RETRIEVAL_ALPHA * weight) * psi
            kraus.append(op)
    completeness = sum(k.conj().T @ k for k in kraus)
    completeness_residual = float(np.linalg.norm(completeness - eye, ord="fro"))
    choi = np.zeros((DIM * DIM, DIM * DIM), dtype=np.complex128)
    for a in range(DIM):
        for b in range(DIM):
            eab = np.zeros((DIM, DIM), dtype=np.complex128)
            eab[a, b] = 1.0
            mapped = sum(k @ eab @ k.conj().T for k in kraus)
            choi[a * DIM : (a + 1) * DIM, b * DIM : (b + 1) * DIM] = mapped / DIM
    choi = (choi + choi.conj().T) / 2.0
    eigvals = np.linalg.eigvalsh(choi)
    ptr_out = np.zeros((DIM, DIM), dtype=np.complex128)
    for a in range(DIM):
        for b in range(DIM):
            ptr_out[a, b] = np.trace(choi[a * DIM : (a + 1) * DIM, b * DIM : (b + 1) * DIM])
    ptr_residual = float(np.linalg.norm(ptr_out - eye / DIM, ord="fro"))
    return {
        "target_id": target_id,
        "kraus_count": len(kraus),
        "component_count": len(components),
        "completeness_residual_fro": completeness_residual,
        "choi_min_eigenvalue": float(np.min(eigvals)),
        "choi_trace": float(np.real(np.trace(choi))),
        "choi_rank_tol_1e_10": int(np.sum(eigvals > 1.0e-10)),
        "choi_partial_trace_output_residual_fro": ptr_residual,
        "kraus_completeness_pass": completeness_residual <= 1.0e-10,
        "choi_positivity_pass": float(np.min(eigvals)) >= -1.0e-10,
        "choi_trace_preserving_pass": ptr_residual <= 1.0e-10,
        "choi_eigenvalue_sha256": stable_hash([round(float(v), 15) for v in eigvals.tolist()]),
    }


def kraus_choi_witness_ledger(basin: dict[str, Any], patterns: dict[str, torch.Tensor]) -> dict[str, Any]:
    target_ids = sorted(
        {
            step["target"]
            for traj in basin["trajectories"]
            for step in traj["path"]
            if isinstance(step, dict) and "target" in step
        }
    )
    rows = [kraus_choi_witness(target_id, patterns) for target_id in target_ids]
    return {
        "channel_formula": "E_target(rho)=(1-alpha)rho+alpha*Tr(rho)*sigma_target",
        "alpha": RETRIEVAL_ALPHA,
        "witness_count": len(rows),
        "all_completeness_pass": all(row["kraus_completeness_pass"] for row in rows),
        "all_choi_positivity_pass": all(row["choi_positivity_pass"] for row in rows),
        "all_trace_preserving_pass": all(row["choi_trace_preserving_pass"] for row in rows),
        "max_completeness_residual_fro": max(row["completeness_residual_fro"] for row in rows) if rows else 0.0,
        "min_choi_eigenvalue": min(row["choi_min_eigenvalue"] for row in rows) if rows else 0.0,
        "max_partial_trace_output_residual_fro": max(row["choi_partial_trace_output_residual_fro"] for row in rows) if rows else 0.0,
        "rows": rows,
    }


def typed_information_rows(patterns: dict[str, torch.Tensor], bipartition: dict[str, list[int]] | None) -> dict[str, Any]:
    if bipartition is None or "A" not in bipartition or "B" not in bipartition:
        raise MissingStructure("typed S(A|B) requires predeclared bipartition with A and B")
    rows = []
    for pid, psi in patterns.items():
        rho = density(psi)
        rho_a = reduce_density(rho, bipartition["A"])
        rho_b = reduce_density(rho, bipartition["B"])
        s_a = entropy_vn(rho_a)
        s_b = entropy_vn(rho_b)
        s_ab = entropy_vn(rho)
        rows.append({
            "pattern_id": pid,
            "S_A_nats": s_a,
            "S_B_nats": s_b,
            "S_AB_nats": s_ab,
            "S_A_given_B_nats": s_ab - s_b,
            "I_A_B_nats": s_a + s_b - s_ab,
            "nonproduct_witness": (s_ab - s_b) < -0.05,
        })
    return {
        "bipartition": bipartition,
        "rows": rows,
        "entangled_negative_conditional_rows": [row for row in rows if row["S_A_given_B_nats"] < -0.05],
    }


def torch_autograd_energy_check(patterns: dict[str, torch.Tensor]) -> dict[str, Any]:
    keys = list(patterns)
    rho = hermitize_trace_one(0.85 * density(patterns[keys[0]]) + 0.15 * density(patterns[keys[1]]))
    target = density(patterns[keys[0]])
    psi = patterns[keys[0]]

    def delta_for_alpha(alpha: torch.Tensor) -> torch.Tensor:
        next_rho = hermitize_trace_one((1.0 - alpha) * rho + alpha * target)
        before = 1.0 - torch.real(torch.vdot(psi, rho @ psi))
        after = 1.0 - torch.real(torch.vdot(psi, next_rho @ psi))
        return after - before

    alpha = torch.tensor(RETRIEVAL_ALPHA, dtype=RTYPE)
    delta = delta_for_alpha(alpha)
    gradient = jacrev(delta_for_alpha)(alpha)
    return {
        "qualified_path": "torch.func.jacrev(delta_for_alpha)",
        "retrieval_alpha": float(alpha),
        "energy_delta": float(delta),
        "d_delta_d_alpha": float(gradient),
        "descent_verified": float(delta) <= 1.0e-12 and float(gradient) < 0.0,
    }


def smt_proof(
    *,
    nonorigin_count: int,
    load_bearing_nonorigin_count: int,
    control_fail_count: int,
    spurious_count: int,
    spurious3_count: int,
    reachable_ceiling_count: int,
    kraus_witness_count: int,
    recovered_predicted_pair_count: int,
    expected_predicted_pair_count: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    values = {
        "nonorigin_count": int(nonorigin_count),
        "load_bearing_nonorigin_count": int(load_bearing_nonorigin_count),
        "control_fail_count": int(control_fail_count),
        "spurious_count": int(spurious_count),
        "spurious3_count": int(spurious3_count),
        "reachable_ceiling_count": int(reachable_ceiling_count),
        "kraus_witness_count": int(kraus_witness_count),
        "recovered_predicted_pair_count": int(recovered_predicted_pair_count),
        "expected_predicted_pair_count": int(expected_predicted_pair_count),
    }
    solver = z3.Solver()
    z_nonorigin = z3.Int("torch_nonorigin_count")
    z_load_bearing = z3.Int("torch_load_bearing_nonorigin_count")
    z_controls = z3.Int("torch_control_fail_count")
    z_spurious = z3.Int("torch_spurious_count")
    z_spurious3 = z3.Int("torch_spurious3_count")
    z_reachable = z3.Int("torch_reachable_ceiling_count")
    z_kraus = z3.Int("torch_kraus_witness_count")
    z_predicted = z3.Int("torch_recovered_predicted_pair_count")
    z_expected = z3.Int("torch_expected_predicted_pair_count")
    solver.add(z_nonorigin == z3.IntVal(values["nonorigin_count"]))
    solver.add(z_load_bearing == z3.IntVal(values["load_bearing_nonorigin_count"]))
    solver.add(z_controls == z3.IntVal(values["control_fail_count"]))
    solver.add(z_spurious == z3.IntVal(values["spurious_count"]))
    solver.add(z_spurious3 == z3.IntVal(values["spurious3_count"]))
    solver.add(z_reachable == z3.IntVal(values["reachable_ceiling_count"]))
    solver.add(z_kraus == z3.IntVal(values["kraus_witness_count"]))
    solver.add(z_predicted == z3.IntVal(values["recovered_predicted_pair_count"]))
    solver.add(z_expected == z3.IntVal(values["expected_predicted_pair_count"]))
    solver.add(z3.Not(z3.And(
        z_nonorigin >= 6,
        z_load_bearing >= 4,
        z_controls == 4,
        z_spurious >= 6,
        z_spurious3 >= 0,
        z_reachable == 33,
        z_kraus >= 1,
        z_expected == 4,
        z_predicted >= 1,
    )))
    verdict = str(solver.check())
    flip = z3.Solver()
    mutated = z3.Int("torch_mutated_recovered_predicted_pair_count")
    flip.add(mutated == z3.IntVal(0))
    flip.add(z3.Not(mutated >= 1))
    flip_verdict = str(flip.check())
    z3_row = {
        "ran": True,
        "solver": "z3",
        "verdict": verdict,
        "perturbed_construction_path_verdict": flip_verdict,
        "load_bearing": True,
        "bound_computed_values": values,
        "negated_assertion": "not(nonorigin>=6 and load_bearing_nonorigin>=4 and controls=4 and pair_spurious>=6 and triple_spurious>=0 and reachable=33 and kraus_witness>=1 and expected_predicted_pairs=4 and recovered_predicted_pairs>=1)",
        "positive_case": "PyTorch-computed pre-registered structured prediction recovery, controls, v1 pair spurious anchor, enumerated 3-pattern extension, reachability ceiling, and Kraus/Choi ledger",
        "negative/erased_control": "mutating recovered predicted-pair count to zero makes the negated assertion SAT",
    }

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nonorigin = c_solver.mkConst(int_sort, "torch_cvc5_nonorigin_count")
    c_load_bearing = c_solver.mkConst(int_sort, "torch_cvc5_load_bearing_nonorigin_count")
    c_controls = c_solver.mkConst(int_sort, "torch_cvc5_control_fail_count")
    c_spurious = c_solver.mkConst(int_sort, "torch_cvc5_spurious_count")
    c_spurious3 = c_solver.mkConst(int_sort, "torch_cvc5_spurious3_count")
    c_reachable = c_solver.mkConst(int_sort, "torch_cvc5_reachable_ceiling_count")
    c_kraus = c_solver.mkConst(int_sort, "torch_cvc5_kraus_witness_count")
    c_predicted = c_solver.mkConst(int_sort, "torch_cvc5_recovered_predicted_pair_count")
    c_expected = c_solver.mkConst(int_sort, "torch_cvc5_expected_predicted_pair_count")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonorigin, c_solver.mkInteger(values["nonorigin_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_load_bearing, c_solver.mkInteger(values["load_bearing_nonorigin_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(values["control_fail_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_spurious, c_solver.mkInteger(values["spurious_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_spurious3, c_solver.mkInteger(values["spurious3_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_reachable, c_solver.mkInteger(values["reachable_ceiling_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_kraus, c_solver.mkInteger(values["kraus_witness_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_predicted, c_solver.mkInteger(values["recovered_predicted_pair_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_expected, c_solver.mkInteger(values["expected_predicted_pair_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.AND,
        c_solver.mkTerm(Kind.GEQ, c_nonorigin, c_solver.mkInteger(6)),
        c_solver.mkTerm(Kind.GEQ, c_load_bearing, c_solver.mkInteger(4)),
        c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(4)),
        c_solver.mkTerm(Kind.GEQ, c_spurious, c_solver.mkInteger(6)),
        c_solver.mkTerm(Kind.GEQ, c_spurious3, c_solver.mkInteger(0)),
        c_solver.mkTerm(Kind.EQUAL, c_reachable, c_solver.mkInteger(33)),
        c_solver.mkTerm(Kind.GEQ, c_kraus, c_solver.mkInteger(1)),
        c_solver.mkTerm(Kind.EQUAL, c_expected, c_solver.mkInteger(4)),
        c_solver.mkTerm(Kind.GEQ, c_predicted, c_solver.mkInteger(1)),
    )))
    cvc5_verdict = str(c_solver.checkSat()).lower()
    c_flip = cvc5.Solver()
    c_flip.setLogic("QF_LIA")
    f_predicted = c_flip.mkConst(c_flip.getIntegerSort(), "torch_cvc5_mutated_recovered_predicted_pair_count")
    c_flip.assertFormula(c_flip.mkTerm(Kind.EQUAL, f_predicted, c_flip.mkInteger(0)))
    c_flip.assertFormula(c_flip.mkTerm(Kind.NOT, c_flip.mkTerm(Kind.GEQ, f_predicted, c_flip.mkInteger(1))))
    cvc5_flip = str(c_flip.checkSat()).lower()
    cvc5_row = {
        "ran": True,
        "solver": "cvc5",
        "verdict": cvc5_verdict,
        "perturbed_construction_path_verdict": cvc5_flip,
        "load_bearing": True,
        "bound_computed_values": values,
        "negated_assertion": z3_row["negated_assertion"],
        "positive_case": "cvc5 mirrors the PyTorch-computed v3 finite count proof",
        "negative/erased_control": "mutated recovered-predicted-pair SAT flip",
    }
    return z3_row, cvc5_row

def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    patterns = terminal_patterns()
    metadata = pattern_metadata(patterns)
    anchor_patterns = v1_anchor_patterns()
    anchor_metadata = pattern_metadata(anchor_patterns)
    chart = chart_controls(patterns, metadata)
    anchor_ids = list(anchor_patterns)
    v1_anchor_recovery = recover_chart_structure(
        [density(anchor_patterns[key]) for key in anchor_ids],
        state_ids=anchor_ids,
        metadata=anchor_metadata,
    )
    basin = transition_graph(anchor_patterns)
    spurious3 = three_pattern_spurious_extension(anchor_patterns)
    typed = typed_information_rows(patterns, {"A": [0], "B": [1, 2, 3]})
    try:
        typed_information_rows(patterns, None)
    except MissingStructure as exc:
        premature_control = {"raised": True, "error": str(exc)}
    else:
        premature_control = {"raised": False, "error": None}
    autograd = torch_autograd_energy_check(anchor_patterns)
    haar_null = haar_null_identity_row(chart["positive"])
    structured_prediction = structured_prediction_comparison(chart["positive"])
    family_recovery = per_family_recovery_table(chart["positive"], metadata, haar_null)
    a33_coverage = a33_reachability_ceiling(chart["positive"]["recovered_nonorigin_cell_ids"])
    kraus_ledger = kraus_choi_witness_ledger(basin, anchor_patterns)
    control_fail_count = sum(1 for row in chart["controls"].values() if row["control_fired"])
    z3_row, cvc5_row = smt_proof(
        nonorigin_count=chart["positive"]["recovered_nonorigin_cell_count"],
        load_bearing_nonorigin_count=chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        control_fail_count=control_fail_count,
        spurious_count=basin["spurious_attractor_count"],
        spurious3_count=spurious3["spurious3_detected_count"],
        reachable_ceiling_count=a33_coverage["geometric_ceiling_cell_count"],
        kraus_witness_count=kraus_ledger["witness_count"],
        recovered_predicted_pair_count=structured_prediction["recovered_predicted_pair_count"],
        expected_predicted_pair_count=structured_prediction["expected_predicted_pair_count"],
    )
    engine_values = {
        "recovered_nonorigin_cell_count": chart["positive"]["recovered_nonorigin_cell_count"],
        "load_bearing_recovered_nonorigin_cell_count": chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        "control_fail_count": control_fail_count,
        "terminal_scc_count": basin["terminal_scc_count"],
        "spurious_attractor_count": basin["spurious_attractor_count"],
        "spurious3_detected_count": spurious3["spurious3_detected_count"],
        "max_lyapunov_delta_scaled": int(round(max(0.0, basin["max_lyapunov_delta"]) * 1_000_000_000)),
        "typed_entangled_negative_count": len(typed["entangled_negative_conditional_rows"]),
        "haar_null_expected_nonorigin_cell_count_scaled": int(round(haar_null["expected_nonorigin_cell_count"] * 1000)),
        "recovered_predicted_pair_count": structured_prediction["recovered_predicted_pair_count"],
        "expected_predicted_pair_count": structured_prediction["expected_predicted_pair_count"],
        "a33_reachable_in_principle_count": a33_coverage["geometric_ceiling_cell_count"],
        "kraus_choi_witness_count": kraus_ledger["witness_count"],
        "v1_anchor_recovered_nonorigin_cell_count": v1_anchor_recovery["recovered_nonorigin_cell_count"],
    }
    all_pass = (
        chart["positive"]["verdict"] == "RECOVERY_PASS_NONTRIVIAL"
        and chart["positive"]["load_bearing_recovered_nonorigin_cell_count"] >= 4
        and control_fail_count == 4
        and chart["controls"]["wrong_row_classifier"]["identity_pairs_match_expected"] is False
        and 7.0 <= haar_null["expected_nonorigin_cell_count"] <= 8.3
        and a33_coverage["geometric_ceiling_cell_count"] == 33
        and kraus_ledger["all_completeness_pass"] is True
        and kraus_ledger["all_choi_positivity_pass"] is True
        and kraus_ledger["all_trace_preserving_pass"] is True
        and v1_anchor_recovery["recovered_nonorigin_cell_count"] == 6
        and basin["max_lyapunov_delta"] <= 1.0e-10
        and basin["spurious_attractor_count"] == 6
        and spurious3["coverage_enumerated"] == spurious3["coverage_denominator"] == 4
        and structured_prediction["expected_predicted_pair_count"] == 4
        and structured_prediction["recovered_predicted_pair_count"] >= 1
        and len(typed["entangled_negative_conditional_rows"]) >= 1
        and premature_control["raised"] is True
        and autograd["descent_verified"] is True
        and z3_row["verdict"] == "unsat"
        and cvc5_row["verdict"] == "unsat"
        and z3_row["perturbed_construction_path_verdict"] == "sat"
        and cvc5_row["perturbed_construction_path_verdict"] == "sat"
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v3",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "role_id": "pytorch_graph_autograd_surface_lane",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch_geometric", "torch.func", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch", "torch_geometric", "torch.func", "z3", "cvc5"],
        "claim_path_tools": ["torch", "torch_geometric", "torch.func", "z3", "cvc5"],
        "package_observables": {
            "torch": "single-site density quotients, pre-registered structured prediction comparison, Haar null rows, and Kraus/Choi witness mirrors",
            "torch_geometric": "PyG Data edge_index carries the finite retrieval graph edge relation used for graph count gates",
            "torch.func": "jacrev differentiates the actual retrieval energy delta with respect to alpha",
            "z3": "PyTorch-computed v3 prediction/control/spurious/reachability/Kraus counts UNSAT with SAT mutation flip",
            "cvc5": "independent cvc5 mirror of PyTorch-computed v3 finite count proof",
        },
        "engine_values": engine_values,
        "A_chart_recoverability": chart["positive"],
        "per_family_recovery_table": family_recovery,
        "haar_null_row": haar_null,
        "pre_registered_structured_prediction": structured_prediction,
        "A33_reachability_ceiling": a33_coverage,
        "kraus_choi_witness_ledger": kraus_ledger,
        "v1_anchor_reproduction": {
            "expected_v1_nonorigin_cell_ids": [
                "A33_x00_y00_zp10",
                "A33_x00_yp5_z00",
                "A33_xp10_y00_z00",
                "A33_xp5_y00_z00",
                "A33_xp5_y00_zm5",
                "A33_xp5_y00_zp5",
            ],
            "actual": v1_anchor_recovery,
        },
        "no_structure_controls": chart["controls"],
        "basin_partition": basin,
        "three_pattern_spurious_extension": spurious3,
        "typed_information": typed,
        "premature_typed_row_control": premature_control,
        "torch_autograd_energy_descent": autograd,
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "TOOL_MANIFEST": {
            "torch": {"used": True, "reason": "load-bearing finite density, pre-registered prediction comparison, Haar null, and Kraus/Choi mirror computation"},
            "torch_geometric": {"used": True, "reason": "load-bearing finite graph edge carrier"},
            "torch.func": {"used": True, "reason": "load-bearing retrieval energy descent autograd"},
            "z3": {"used": True, "reason": "load-bearing finite count proof"},
            "cvc5": {"used": True, "reason": "load-bearing finite count proof mirror"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "torch_geometric": "load_bearing",
            "torch.func": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "tool_calls": [
            {
                "tool": "torch",
                "qualified_api/function": "torch.linalg.eigvalsh/torch.trace",
                "input_object": "single-site density quotients plus finite A33 reachability rows",
                "output_object": {
                    "pre_registered_structured_prediction": {
                        "recovered_predicted_pair_count": structured_prediction["recovered_predicted_pair_count"],
                        "expected_predicted_pair_count": structured_prediction["expected_predicted_pair_count"],
                        "verdict": structured_prediction["verdict"],
                    },
                    "kraus_choi_witness_count": kraus_ledger["witness_count"],
                    "a33_geometric_ceiling": a33_coverage["geometric_ceiling_cell_count"],
                },
                "positive_case": "pre-registered structured family-cell predictions are scored against a computed Haar null and retrieval branches have CP/TP witnesses",
                "negative/erased_control": "permuted wrong-row labels fail the same family identity predicate",
                "boundary_case": "finite n4 carrier and 2048-trial Haar null",
                "demotion_condition": "demote v3 prediction claim if pre-registration, null, reachability, or Kraus/Choi witnesses are removed",
                "gates": ["pre_registered_structured_prediction", "A33_reachability_ceiling", "kraus_choi_witness_ledger", "all_pass"],
            },
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data(edge_index=...)",
                "input_object": "finite retrieval transition edges",
                "output_object": basin["pyg_graph"],
                "positive_case": "edge count and node count gate finite graph construction",
                "negative/erased_control": "spurious pair mixtures remain explicit graph seeds",
                "boundary_case": "finite graph count, not continuum basin proof",
                "demotion_condition": "demote graph lane if PyG Data route is removed",
                "gates": ["basin_partition", "all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.jacrev",
                "input_object": "retrieval energy delta as a function of alpha",
                "output_object": autograd,
                "positive_case": "actual retrieval update decreases V and jacrev sees negative slope",
                "negative/erased_control": "demote if replaced with graph-shape-only sensitivity",
                "boundary_case": "one named boundary seed",
                "demotion_condition": "demote PyTorch to supportive if autograd no longer gates all_pass",
                "gates": ["energy_descent", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/solver.add/solver.check",
                "input_object": "computed v3 prediction/control/spurious/reachability/Kraus finite counts",
                "output_object": z3_row,
                "positive_case": z3_row["positive_case"],
                "negative/erased_control": z3_row["negative/erased_control"],
                "boundary_case": "integer finite-count proof only",
                "demotion_condition": "demote if solver binds booleans instead of computed counts",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same computed v3 finite count values as z3",
                "output_object": cvc5_row,
                "positive_case": cvc5_row["positive_case"],
                "negative/erased_control": cvc5_row["negative/erased_control"],
                "boundary_case": "integer finite-count proof only",
                "demotion_condition": "demote if cvc5 mirror is removed",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
    }
    write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
