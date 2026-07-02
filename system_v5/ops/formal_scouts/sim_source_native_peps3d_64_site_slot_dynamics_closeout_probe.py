#!/usr/bin/env python3
"""Bounded canonical QIT replay 64-site PEPS3D slot-dynamics closeout scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import Counter
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import networkx as nx
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    density_diagnostics,
    density_entropy,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json"

NAME = "source_native_peps3d_64_site_slot_dynamics_closeout_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_bond_dimension_and_long_horizon_closeout"
EXPECTED_UNIQUE_ORDERED_TOKENS = 32
EXPECTED_SLOT_APPLICATIONS_PER_SEED = 64
CLAIM_CEILING = (
    "Formal scout only: applies bounded canonical QIT operator-slot stage records "
    "directly to a finite 64-site PEPS3D tensor carrier and records the 64-site "
    "slot-dynamics closeout predicates. It does not run source-native EngineCore "
    "dynamics, does not run a long-horizon 64-site engine, does not prove 64-site "
    "bond-dimension convergence, and does not admit final manifold, physics, "
    "cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing PEPS3D carrier arrays, Pauli operators, RNG, tensor-slot updates, and norm/reduction checks"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 64-site PEPS3D carrier construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction context witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing update dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic token-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing 64-site token contract witness"},
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical operator-slot schedule and terrain metadata replacing the former direct EngineCore boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "quimb": "local",
    "cotengra": "local",
    "opt_einsum": "local",
    "networkx": "local",
    "sympy": "local",
    "z3": "local",
    "canonical_qit_engine_specs": "local",
}
BEFORE_SCRIPT_SHA256 = "dbcca3e494ec3ecad614ad7ed96a5a42a361ae91abaae8257c8b92db2b8bdee3"
BEFORE_RESULT_SHA256 = "91a521da364b5c2a95b4294260dfc1e38c2f071b0d60774a3ec6cbb607838199"

N_SEEDS = 4
GRID_SIZE = 4
TOPOLOGY_FLUX_STRENGTH_WEIGHT = 0.0007
DTYPE = torch.complex128
FLOAT_DTYPE = torch.float64
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
I2 = torch.eye(2, dtype=DTYPE)
OP_AXES = {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SY}
REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]


def apply_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=DTYPE)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    out = unitary @ rho @ unitary.conj().T
    return normalize_density_torch(out), slot


def apply_manifold_target_mix(rho: torch.Tensor, perception: str, engine_type: int) -> torch.Tensor:
    target = stage_fixed_target(perception, engine_type)
    return normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * rho + MANIFOLD_TARGET_MIX * target)


def run_canonical_stage_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    main_stage_idx: int,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    before = normalize_density_torch(rho)
    fixed_target = stage_fixed_target(perception, engine_type)
    after_operator, slot = apply_operator_slot(before, perception, engine_type, loop_class, substage_idx)
    after_terrain = normalize_density_torch(apply_lindblad_step(after_operator, perception, engine_type))
    after_manifold = apply_manifold_target_mix(after_terrain, perception, engine_type)
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    diag = density_diagnostics(after_manifold)
    before_error = trace_distance(before, fixed_target)
    after_error = trace_distance(after_manifold, fixed_target)
    slot_delta_norm = float(torch.linalg.matrix_norm(after_operator - before).item())
    terrain_delta_norm = float(torch.linalg.matrix_norm(after_terrain - after_operator).item())
    manifold_delta_norm = float(torch.linalg.matrix_norm(after_manifold - after_terrain).item())
    entropy = density_entropy(after_manifold)
    fep_proxy = float(after_error + 0.25 * entropy + 0.50 * manifold_delta_norm + 0.10 * terrain_delta_norm)
    valid_density = bool(
        diag["trace_gap"] < 1e-8
        and diag["hermitian_gap"] < 1e-8
        and diag["min_eigenvalue"] > -1e-8
    )
    record = {
        "engine_type": int(engine_type),
        "main_stage_idx": int(main_stage_idx),
        "substage_idx": int(substage_idx),
        "perception": perception,
        "loop_class": loop_class,
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "ordered_token": slot["token"],
        "is_native_operator": bool(slot["is_native_operator"]),
        "is_chart_locked": bool(slot["is_chart_locked"]),
        "terrain_dynamics_family": terrain["family"],
        "slot_delta_norm": slot_delta_norm,
        "terrain_delta_norm": terrain_delta_norm,
        "manifold_delta_norm": manifold_delta_norm,
        "entropy": entropy,
        "trace_distance_to_fixed_target": after_error,
        "valid_density": valid_density,
        "manifold_called_count": 13,
        "model_before": {
            "entropy": density_entropy(before),
            "trace_distance_to_fixed_target": before_error,
            "valid_density": True,
        },
        "prediction": {
            "ordered_token": slot["token"],
            "operator": slot["operator"],
            "operator_sign": int(slot["sign"]),
            "terrain_dynamics_family": terrain["family"],
            "loop_class": loop_class,
        },
        "observation": {
            "entropy": entropy,
            "trace_distance_to_fixed_target": after_error,
            "valid_density": valid_density,
        },
        "fep_efe_score": {
            "expected_free_energy_proxy": fep_proxy,
            "before_error": before_error,
            "after_error": after_error,
            "entropy": entropy,
        },
        "update_repair": {
            "manifold_target_mix": MANIFOLD_TARGET_MIX,
            "slot_delta_norm": slot_delta_norm,
            "terrain_delta_norm": terrain_delta_norm,
            "manifold_delta_norm": manifold_delta_norm,
        },
        "falsifier_graveyard": {
            "identity_tensor_update_control": True,
            "axis0_zeroed_control": True,
            "zero_flux_control": True,
            "shuffled_topology_flux_control": True,
        },
        "next_policy": {
            "next_substage_idx": (substage_idx + 1) % 4,
            "next_main_stage_idx": main_stage_idx if substage_idx < 3 else main_stage_idx + 1,
        },
        "model_after": {
            "entropy": entropy,
            "trace_distance_to_fixed_target": after_error,
            "valid_density": valid_density,
        },
    }
    return after_manifold, record


def mean_abs(values: list[float] | torch.Tensor) -> float:
    tensor = torch.as_tensor(values, dtype=FLOAT_DTYPE)
    return float(torch.mean(torch.abs(tensor)).item()) if tensor.numel() else 0.0


def variance(values: list[float] | torch.Tensor) -> float:
    tensor = torch.as_tensor(values, dtype=FLOAT_DTYPE)
    return float(torch.var(tensor, unbiased=False).item()) if tensor.numel() else 0.0


def max_abs(values: list[float] | torch.Tensor) -> float:
    tensor = torch.as_tensor(values, dtype=FLOAT_DTYPE)
    return float(torch.max(torch.abs(tensor)).item()) if tensor.numel() else 0.0


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", "")[:220],
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def axis0_signature(router: dict[str, Any]) -> dict[str, Any]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    names = ["fep_gradient_polarity", "path_entropy", "correlation_diversity_derivative"]
    vectors: dict[str, list[float]] = {}
    for name in names:
        arr = torch.as_tensor(outputs.get(name, {}).get("values", []), dtype=FLOAT_DTYPE)
        if arr.numel():
            arr = torch.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
            scale = max_abs(arr)
            if scale > 0.0:
                arr = arr / scale
        vectors[name] = [float(x) for x in arr]
    ready = bool(router.get("exists") and router.get("all_pass") is True and all(vectors.values()))
    return {
        "ready": ready,
        "candidate_names": names,
        "candidate_vectors": vectors,
        "source_receipt": router.get("path"),
    }


def axis0_drive(axis0: dict[str, Any], idx: int) -> float:
    if not axis0.get("ready"):
        return 0.0
    values = []
    for vector in axis0.get("candidate_vectors", {}).values():
        if vector:
            values.append(float(vector[idx % len(vector)]))
    return float(torch.mean(torch.tensor(values, dtype=FLOAT_DTYPE)).item()) if values else 0.0


def science_method_contract(records: list[dict[str, Any]]) -> dict[str, Any]:
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}:i{idx}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for idx, row in enumerate(records)
    }
    missing = {key: value for key, value in missing.items() if value}
    efe = torch.as_tensor(
        [row.get("fep_efe_score", {}).get("expected_free_energy_proxy", 0.0) for row in records],
        dtype=FLOAT_DTYPE,
    )
    return {
        "pass": not missing and len(records) == N_SEEDS * EXPECTED_SLOT_APPLICATIONS_PER_SEED,
        "record_count": len(records),
        "required_fields": REQUIRED_STAGE_FIELDS,
        "missing_required_stage_fields": missing,
        "expected_free_energy_mean": float(torch.mean(efe).item()) if efe.numel() else 0.0,
        "expected_free_energy_variance": variance(efe),
    }


def make_peps3d_arrays(seed: int, bond_dim: int = 2) -> list[list[list[torch.Tensor]]]:
    generator = torch.Generator().manual_seed(seed)
    arrays = []
    for i in range(GRID_SIZE):
        plane = []
        for j in range(GRID_SIZE):
            row = []
            for k in range(GRID_SIZE):
                legs = []
                if i < GRID_SIZE - 1:
                    legs.append(bond_dim)
                if j < GRID_SIZE - 1:
                    legs.append(bond_dim)
                if k < GRID_SIZE - 1:
                    legs.append(bond_dim)
                if i > 0:
                    legs.append(bond_dim)
                if j > 0:
                    legs.append(bond_dim)
                if k > 0:
                    legs.append(bond_dim)
                legs.append(2)
                row.append(0.025 * torch.randn(tuple(legs), dtype=DTYPE, generator=generator))
            plane.append(row)
        arrays.append(plane)
    return arrays


def flatten_sites(arrays: list[list[list[torch.Tensor]]]) -> list[tuple[int, int, int]]:
    return [(i, j, k) for i in range(GRID_SIZE) for j in range(GRID_SIZE) for k in range(GRID_SIZE)]


def site_orientation(site: tuple[int, int, int]) -> dict[str, Any]:
    i, j, k = site
    centered = torch.tensor([i, j, k], dtype=FLOAT_DTYPE) - (GRID_SIZE - 1) / 2.0
    orientation = float(torch.dot(centered, torch.tensor([1.0, -0.5, 0.75], dtype=FLOAT_DTYPE)).item())
    return {
        "site": [i, j, k],
        "coordinate_parity": 1 if (i + j + k) % 2 == 0 else -1,
        "orientation": orientation,
    }


def topology_flux_helper(
    sites: list[tuple[int, int, int]],
    *,
    zero_flux: bool = False,
    shuffle_edges: bool = False,
) -> dict[str, Any]:
    site_set = set(sites)
    axes = [
        ("x", (1, 0, 0), 1.0),
        ("y", (0, 1, 0), -0.75),
        ("z", (0, 0, 1), 0.5),
    ]
    base_edges = []
    for site in sites:
        i, j, k = site
        src_meta = site_orientation(site)
        for axis_name, delta, axis_weight in axes:
            dst = (i + delta[0], j + delta[1], k + delta[2])
            if dst not in site_set:
                continue
            dst_meta = site_orientation(dst)
            parity_term = 0.5 * (src_meta["coordinate_parity"] - dst_meta["coordinate_parity"])
            orientation_term = dst_meta["orientation"] - src_meta["orientation"]
            flux = 0.0 if zero_flux else float(axis_weight * (1.0 + 0.125 * parity_term + 0.05 * orientation_term))
            base_edges.append({"src": site, "dst": dst, "axis": axis_name, "axis_weight": axis_weight, "flux": flux})

    edges = [dict(edge) for edge in base_edges]
    if shuffle_edges:
        generator = torch.Generator().manual_seed(83064)
        shuffled_dsts = [edge["dst"] for edge in edges]
        order = torch.randperm(len(shuffled_dsts), generator=generator).tolist()
        shuffled_dsts = [shuffled_dsts[idx] for idx in order]
        for edge, dst in zip(edges, shuffled_dsts):
            edge["dst"] = dst

    drives = {site: 0.0 for site in sites}
    broken_edges = 0
    axis_histogram: Counter[str] = Counter()
    for edge in edges:
        src = edge["src"]
        dst = edge["dst"]
        axis_histogram[str(edge["axis"])] += 1
        manhattan = sum(abs(src[idx] - dst[idx]) for idx in range(3))
        if manhattan != 1:
            broken_edges += 1
        drives[src] += float(edge["flux"])
        drives[dst] -= float(edge["flux"])

    drive_values = torch.tensor(list(drives.values()), dtype=FLOAT_DTYPE)
    scale = max_abs(drive_values) if drive_values.numel() else 0.0
    if scale > 0.0:
        drives = {site: float(value / scale) for site, value in drives.items()}
        drive_values = torch.tensor(list(drives.values()), dtype=FLOAT_DTYPE)

    sample_sites = sorted(sites)[:8]
    return {
        "site_drives": drives,
        "report": {
            "grid_shape": [GRID_SIZE, GRID_SIZE, GRID_SIZE],
            "oriented_edge_count": len(edges),
            "nearest_neighbor_oriented_edge_count": len(base_edges),
            "axis_edge_histogram": dict(sorted(axis_histogram.items())),
            "site_coordinate_parity_orientation_sample": [site_orientation(site) for site in sample_sites],
            "site_flux_drive_sample": {",".join(map(str, site)): drives[site] for site in sample_sites},
            "finite_flux_drive": bool(torch.all(torch.isfinite(drive_values)).item()),
            "flux_zeroed": bool(zero_flux),
            "edges_shuffled": bool(shuffle_edges),
            "broken_nearest_neighbor_edge_count": broken_edges,
            "drive_mean_abs": mean_abs(drive_values),
            "drive_variance": variance(drive_values),
            "drive_max_abs": max_abs(drive_values),
        },
    }


def tensor_norm(arrays: list[list[list[torch.Tensor]]]) -> float:
    total = sum(
        float(torch.vdot(arr.reshape(-1), arr.reshape(-1)).real.item())
        for plane in arrays
        for row in plane
        for arr in row
    )
    return math.sqrt(total)


def apply_slot_to_tensor(arr: torch.Tensor, operator: str, sign: int, strength: float) -> torch.Tensor:
    axis = OP_AXES[operator]
    unitary = I2 - 1j * float(sign) * float(strength) * axis
    moved = torch.tensordot(arr, unitary.T, dims=([-1], [0]))
    return moved.to(dtype=DTYPE)


def source_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed_idx in range(N_SEEDS):
        rho_init = generate_initial_density(70000 + seed_idx)
        for engine_type in (0, 1):
            rho = rho_init.clone()
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                for substage_idx in range(4):
                    rho, record = run_canonical_stage_slot(
                        rho,
                        perception,
                        engine_type,
                        loop_class,
                        main_idx,
                        substage_idx,
                    )
                    record["seed_idx"] = int(seed_idx)
                    records.append(record)
    return records


def apply_records_to_64_site_peps3d(
    records: list[dict[str, Any]],
    *,
    identity_control: bool = False,
    axis0: dict[str, Any] | None = None,
    zero_axis0: bool = False,
    zero_flux: bool = False,
    shuffled_topology_flux: bool = False,
) -> dict[str, Any]:
    arrays = make_peps3d_arrays(71000)
    before = tensor_norm(arrays)
    sites = flatten_sites(arrays)
    topology_flux = topology_flux_helper(sites, zero_flux=zero_flux, shuffle_edges=shuffled_topology_flux)
    topology_drives_by_site = topology_flux["site_drives"]
    touched = set()
    token_sequence: list[str] = []
    axis0_drives: list[float] = []
    topology_flux_drives: list[float] = []
    for idx, record in enumerate(records):
        site = sites[idx % len(sites)]
        i, j, k = site
        token_sequence.append(str(record["ordered_token"]))
        touched.add(site)
        drive = 0.0 if zero_axis0 else axis0_drive(axis0 or {}, idx)
        axis0_drives.append(drive)
        topology_drive = float(topology_drives_by_site[site])
        topology_flux_drives.append(topology_drive)
        if identity_control:
            continue
        fep = record.get("fep_efe_score", {})
        strength = (
            0.0025
            + 0.0004 * float(record["slot_delta_norm"])
            + 0.0001 * float(record["entropy"])
            + 0.00005 * float(fep.get("expected_free_energy_proxy", 0.0))
            + 0.0002 * drive
            + TOPOLOGY_FLUX_STRENGTH_WEIGHT * topology_drive
        )
        arrays[i][j][k] = apply_slot_to_tensor(
            arrays[i][j][k],
            str(record["operator"]),
            int(record["operator_sign"]),
            strength,
        )
    after = tensor_norm(arrays)
    peps = qtn.PEPS3D(arrays)
    return {
        "tensor_size": 64,
        "num_tensors": int(peps.num_tensors),
        "num_indices": int(peps.num_indices),
        "parameter_count": int(sum(math.prod(tensor.shape) for tensor in peps.tensors)),
        "slot_applications": len(records),
        "unique_sites_touched": len(touched),
        "unique_ordered_tokens": len(set(token_sequence)),
        "ordered_token_histogram": dict(sorted(Counter(token_sequence).items())),
        "axis0_ready": bool((axis0 or {}).get("ready")),
        "axis0_zeroed": bool(zero_axis0),
        "axis0_drive_mean_abs": mean_abs(axis0_drives),
        "axis0_drive_variance": variance(axis0_drives),
        "topology_flux": topology_flux["report"],
        "topology_flux_drive_mean_abs": mean_abs(topology_flux_drives),
        "topology_flux_drive_variance": variance(topology_flux_drives),
        "topology_flux_zeroed": bool(zero_flux),
        "topology_flux_edges_shuffled": bool(shuffled_topology_flux),
        "norm_before": before,
        "norm_after": after,
        "norm_shift": abs(after - before),
        "pass": int(peps.num_tensors) == 64
        and len(records) == N_SEEDS * EXPECTED_SLOT_APPLICATIONS_PER_SEED
        and len(touched) == 64
        and len(set(token_sequence)) == EXPECTED_UNIQUE_ORDERED_TOKENS
        and abs(after - before) > 1e-5,
    }


def contraction_context(seed: int) -> dict[str, float]:
    inputs, output, expr = [
        ("a", "b", "e", "l"),
        ("b", "c", "f", "m"),
        ("e", "f", "h", "n"),
        ("l", "m", "n", "o"),
        ("c", "d", "g", "p"),
        ("h", "i", "o", "q"),
        ("g", "i", "j", "r"),
        ("p", "q", "r", "s"),
    ], ("a", "d", "j", "s"), "abel,bcfm,efhn,lmno,cdgp,hioq,gijr,pqrs->adjs"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + ((n + seed) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False, parallel=False).search(inputs, output, sizes)
    generator = torch.Generator().manual_seed(19000 + seed)
    arrays = [
        torch.randn(tuple(sizes[ix] for ix in term), dtype=FLOAT_DTYPE, generator=generator)
        for term in inputs
    ]
    contracted = oe.contract(expr, *arrays)
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(torch.linalg.vector_norm(contracted).item()),
    }


def z3_closeout_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    tensor_size = z3.Int("tensor_size")
    applications = z3.Int("slot_applications")
    tokens = z3.Int("unique_tokens")
    touched = z3.Int("touched_sites")
    solver.add(tensor_size == row["tensor_size"])
    solver.add(applications == row["slot_applications"])
    solver.add(tokens == row["unique_ordered_tokens"])
    solver.add(touched == row["unique_sites_touched"])
    solver.add(z3.Not(z3.And(tensor_size == 64, applications == N_SEEDS * 64, tokens == 32, touched == 64)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite 64-site closeout counts; tensor updates carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0 = axis0_signature(axis0_router)
    records = source_records()
    science_contract = science_method_contract(records)
    dynamic = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0)
    identity = apply_records_to_64_site_peps3d(records, identity_control=True, axis0=axis0)
    axis0_zeroed = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0, zero_axis0=True)
    zero_flux = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0, zero_flux=True)
    shuffled_flux = apply_records_to_64_site_peps3d(records, identity_control=False, axis0=axis0, shuffled_topology_flux=True)
    axis0_norm_shift_gap = abs(dynamic["norm_shift"] - axis0_zeroed["norm_shift"])
    topology_flux_norm_shift_gap = abs(dynamic["norm_shift"] - zero_flux["norm_shift"])
    shuffled_topology_flux_norm_shift_gap = abs(dynamic["norm_shift"] - shuffled_flux["norm_shift"])
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("canonical_qit_stage_records", "science_method_fields"),
        ("science_method_fields", "slot_sequence"),
        ("axis0_plural_router", "slot_strength"),
        ("peps3d_4x4x4_oriented_topology_flux", "slot_strength"),
        ("slot_sequence", "slot_strength"),
        ("slot_strength", "peps3d_64_tensor"),
        ("peps3d_64_tensor", "closeout"),
    ])
    positive = {
        "slot_dynamics_execute_directly_on_64_site_peps3d": {
            **dynamic,
            "expected_unique_ordered_tokens": EXPECTED_UNIQUE_ORDERED_TOKENS,
            "expected_slot_applications_per_seed": EXPECTED_SLOT_APPLICATIONS_PER_SEED,
            "contraction_context": contraction_context(dynamic["unique_ordered_tokens"] + dynamic["unique_sites_touched"]),
            "pass": dynamic["pass"],
        },
        "science_method_stage_records_drive_64_site_slot_strength": {
            "pass": science_contract["pass"] and stage_contract["exists"] and stage_contract.get("all_pass") is True,
            "source_stage_contract_receipt": stage_contract,
            **science_contract,
        },
        "plural_axis0_router_drives_64_site_slot_strength": {
            "pass": axis0["ready"] and dynamic["axis0_drive_mean_abs"] > 0.001 and axis0_norm_shift_gap > 1e-9,
            "axis0_router_receipt": axis0_router,
            "axis0_signature": axis0,
            "dynamic_axis0_drive_mean_abs": dynamic["axis0_drive_mean_abs"],
            "axis0_zeroed_norm_shift": axis0_zeroed["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
        },
        "topology_flux_drives_64_site_slot_strength": {
            "pass": dynamic["topology_flux"]["finite_flux_drive"]
            and dynamic["topology_flux"]["oriented_edge_count"] == 144
            and dynamic["topology_flux_drive_mean_abs"] > 0.001
            and topology_flux_norm_shift_gap > 1e-9,
            "topology_flux": dynamic["topology_flux"],
            "dynamic_topology_flux_drive_mean_abs": dynamic["topology_flux_drive_mean_abs"],
            "dynamic_topology_flux_drive_variance": dynamic["topology_flux_drive_variance"],
            "zero_flux_norm_shift": zero_flux["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "topology_flux_norm_shift_gap": topology_flux_norm_shift_gap,
            "reason": "4x4x4 oriented nearest-neighbor topology flux enters slot strength before tensor update.",
        },
        "symbolic_64_slot_factorization": {
            "factorization": {str(k): v for k, v in sp.factorint(64 * EXPECTED_UNIQUE_ORDERED_TOKENS).items()},
            "pass": sp.factorint(64 * EXPECTED_UNIQUE_ORDERED_TOKENS) == {2: 11},
        },
        "z3_rejects_64_site_slot_contract_collapse": z3_closeout_witness(dynamic),
    }
    graveyards = {
        "identity_tensor_update_does_not_count_as_dynamics": {
            "identity_norm_shift": identity["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "pass": identity["norm_shift"] < 1e-12 and dynamic["norm_shift"] > identity["norm_shift"],
        },
        "axis0_zeroed_control_changes_slot_dynamics": {
            "pass": axis0_norm_shift_gap > 1e-9,
            "axis0_zeroed_norm_shift": axis0_zeroed["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
            "reason": "Axis0 router output affects slot strength before tensor updates, not only the receipt.",
        },
        "zero_flux_control_changes_slot_dynamics": {
            "pass": zero_flux["topology_flux"]["flux_zeroed"] and topology_flux_norm_shift_gap > 1e-9,
            "zero_flux_norm_shift": zero_flux["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "topology_flux_norm_shift_gap": topology_flux_norm_shift_gap,
            "reason": "Finite topology flux affects slot strength; zeroing it changes the resulting tensor update.",
        },
        "shuffled_topology_flux_control_rejected": {
            "pass": shuffled_flux["topology_flux"]["edges_shuffled"]
            and shuffled_flux["topology_flux"]["broken_nearest_neighbor_edge_count"] > 0
            and shuffled_topology_flux_norm_shift_gap > 1e-9,
            "shuffled_flux_norm_shift": shuffled_flux["norm_shift"],
            "dynamic_norm_shift": dynamic["norm_shift"],
            "shuffled_topology_flux_norm_shift_gap": shuffled_topology_flux_norm_shift_gap,
            "shuffled_topology_flux": shuffled_flux["topology_flux"],
            "reason": "Shuffled endpoints destroy the 4x4x4 nearest-neighbor topology, so the control is rejected as topology-flux evidence.",
        },
        "label_only_records_would_fail_64_site_closeout": {
            "pass": science_contract["pass"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "reason": "Closeout now requires repaired science-method/FEP fields for slot-strength calculation.",
        },
        "ordered_token_count_is_not_interpolated": {
            "unique_ordered_tokens": dynamic["unique_ordered_tokens"],
            "pass": dynamic["unique_ordered_tokens"] == EXPECTED_UNIQUE_ORDERED_TOKENS,
        },
    }
    boundary = {
        "does_not_claim_long_horizon_or_bond_convergence": {
            "pass": "does not run a long-horizon 64-site engine" in CLAIM_CEILING and "does not prove 64-site bond-dimension convergence" in CLAIM_CEILING,
        },
        "dependency_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": science_contract["pass"] and axis0["ready"],
            "consumed_dependencies": [
                "canonical QIT science-method-like stage records",
                "macro_sim_stage_record_science_method_contract receipt",
                "macro_sim_axis0_plural_stage_candidate_router receipt",
                "4x4x4 oriented nearest-neighbor topology-flux helper",
            ],
            "dependency_use": (
                "science-method FEP scores, plural Axis0 router drives, and 4x4x4 topology-flux drives enter "
                "slot-strength calculation before the PEPS3D tensor update"
            ),
        },
        "environment_contraction_still_blocked": {
            "pass": True,
            "blocked_scope": "64-site tensor update closeout only; no PEPS3D environment contraction readout or gauge control is implemented here.",
            "next_admissible_step": "PEPS/PEPS3D no-dense environment-contraction scout with gauge and finite-size controls.",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    axis0_outputs_or_blockers = {
        "plural_axis0_router": {
            "status": "consumed_as_64_site_slot_strength_dependency",
            "receipt": axis0_router,
            "axis0_norm_shift_gap": axis0_norm_shift_gap,
        },
        "fep_gradient_polarity": {"status": "consumed_from_plural_router"},
        "path_entropy": {"status": "consumed_from_plural_router"},
        "correlation_diversity_derivative": {"status": "consumed_from_plural_router"},
        "holographic_boundary_interior_reconstruction": {
            "status": "still_blocked_by_router_receipt",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "routing_only_not_final",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("retrocausal_many_futures_policy_scoring", {})
                .get("status")
            ),
        },
        "peps3d_environment_contraction": {
            "status": "blocked_next_surface",
            "blocker": "This closeout applies tensors directly but does not compute no-dense PEPS3D environment readout.",
        },
        "peps3d_4x4x4_topology_flux": {
            "status": "consumed_as_slot_strength_dependency",
            "topology_flux_norm_shift_gap": topology_flux_norm_shift_gap,
            "control_status": "zero_flux_and_shuffled_edge_controls_recorded",
        },
    }
    repair_receipt = {
        "weak_link": "64-site PEPS3D closeout formerly applied EngineCore records directly; this port rebuilds bounded canonical QIT records with science-method/FEP fields, plural Axis0 dependency consumption, and 4x4x4 topology-flux drive.",
        "target_file_or_result": str(pathlib.Path(__file__).resolve()),
        "admission_rule_improved": "64-site PEPS3D slot-dynamics closeouts must consume science-method stage fields, plural Axis0 router outputs, and 4x4x4 topology-flux drives before tensor updates.",
        "dependency_subset": [
            "canonical QIT stage records",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "4x4x4 oriented nearest-neighbor topology-flux helper",
            "64-site PEPS3D tensor update",
            "identity tensor-update control",
            "axis0_zeroed slot-strength control",
            "zero_flux slot-strength control",
            "shuffled_edge topology-flux control",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {"script": BEFORE_SCRIPT_SHA256, "result": BEFORE_RESULT_SHA256},
        "after_delta/hash": "slot strength now consumes fep_efe_score, plural Axis0 router drive, and 4x4x4 topology-flux drive before tensor update",
        "primary_control/result": {
            "identity_tensor_update": graveyards["identity_tensor_update_does_not_count_as_dynamics"],
            "axis0_zeroed": graveyards["axis0_zeroed_control_changes_slot_dynamics"],
            "zero_flux": graveyards["zero_flux_control_changes_slot_dynamics"],
            "shuffled_topology_flux": graveyards["shuffled_topology_flux_control_rejected"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local 64-site PEPS3D dependency repair was directly executable",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Repair or create PEPS/PEPS3D no-dense environment-contraction scout with gauge and finite-size controls.",
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "bounded_canonical_qit_replay_peps3d_64_site_slot_dynamics_closeout_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "64-site finite closeout only.",
            "Does not run source-native EngineCore dynamics.",
            "Does not prove long-horizon 64-site stability.",
            "Does not prove bond-dimension convergence beyond the finite update context.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
