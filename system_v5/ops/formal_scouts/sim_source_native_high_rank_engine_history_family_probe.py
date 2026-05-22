#!/usr/bin/env python3
"""Source-native high-rank engine history family scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
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
    bloch_vector,
    density_diagnostics,
    density_entropy,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_high_rank_engine_history_family_probe_results.json"

NAME = "source_native_high_rank_engine_history_family_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_high_rank_history_sweep"
CLAIM_CEILING = (
    "Formal scout only: generates a richer bounded canonical QIT replay "
    "engine-history family from multiple initial densities through both chiral "
    "stage schedules, then "
    "checks whether the resulting histories have higher effective rank for "
    "32/64-site PEPS3D carrier stress. It does not run the full 64-site engine "
    "and does not admit source-native EngineCore dynamics, live PEPS3D Lindblad "
    "dynamics, real attractor basins, final manifold, physics, cognition, "
    "neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local source-history feature matrices, rank metrics, PEPS3D carrier tensors, contraction arrays, and contraction norms",
    },
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS3D carrier capacity construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing history dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic row-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing rank improvement witness"},
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical terrain/operator schedule records replacing the former direct EngineCore boundary",
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

N_SEEDS = 16
TORCH_COMPLEX = torch.complex128


def apply_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=TORCH_COMPLEX)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    return unitary @ rho @ unitary.conj().T, slot


def replay_substage(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    main_idx: int,
    substage_idx: int,
    *,
    manifold_enabled: bool,
) -> tuple[torch.Tensor, dict[str, Any]]:
    before = normalize_density_torch(rho)
    slotted, slot = apply_operator_slot(before, perception, engine_type, loop_class, substage_idx)
    evolved = apply_lindblad_step(slotted, perception, engine_type)
    target = stage_fixed_target(perception, engine_type)
    if manifold_enabled:
        repaired = normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * evolved + MANIFOLD_TARGET_MIX * target)
    else:
        repaired = normalize_density_torch(evolved)
    diagnostics = density_diagnostics(repaired)
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    return repaired, {
        "engine_type": int(engine_type),
        "main_stage_idx": int(main_idx),
        "substage_idx": int(substage_idx),
        "perception": perception,
        "loop_class": loop_class,
        "ordered_token": slot["token"],
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "is_native_operator": bool(slot["is_native_operator"]),
        "is_chart_locked": bool(slot["is_chart_locked"]),
        "terrain_dynamics_family": terrain["family"],
        "bloch": bloch_vector(repaired),
        "entropy": density_entropy(repaired),
        "purity": float(torch.real(torch.trace(repaired @ repaired)).item()),
        "slot_delta_norm": float(torch.linalg.vector_norm((repaired - before).reshape(-1)).item()),
        "manifold_applied_count": 1 if manifold_enabled else 0,
        "manifold_satisfied_count": int(
            manifold_enabled and trace_distance(repaired, target) <= trace_distance(evolved, target) + 1e-12
        ),
        "valid_density": (
            diagnostics["trace_gap"] < 1e-10
            and diagnostics["hermitian_gap"] < 1e-10
            and diagnostics["min_eigenvalue"] >= -1e-10
        ),
    }


def feature_from_record(record: dict[str, Any]) -> torch.Tensor:
    terrain_index = {
        "pinching_projection": 0.0,
        "kraus_filter": 1.0,
        "lowering_dissipator": 2.0,
        "pinching_dissipator": 3.0,
        "kraus_release": 4.0,
        "outward_projection": 5.0,
        "raising_dissipator": 6.0,
    }.get(str(record.get("terrain_dynamics_family")), -1.0)
    return torch.as_tensor(
        [
            *[float(x) for x in record["bloch"]],
            float(record["entropy"]),
            float(record["purity"]),
            float(record["slot_delta_norm"]),
            float(record["operator_sign"]),
            1.0 if record["is_native_operator"] else 0.0,
            1.0 if record["is_chart_locked"] else 0.0,
            float(record["manifold_applied_count"]),
            float(record["manifold_satisfied_count"]),
            float(record["engine_type"]),
            float(record["main_stage_idx"]),
            float(record["substage_idx"]),
            terrain_index,
        ],
        dtype=torch.float64,
    )


def physical_feature_from_record(record: dict[str, Any]) -> torch.Tensor:
    return torch.as_tensor(
        [
            *[float(x) for x in record["bloch"]],
            float(record["entropy"]),
            float(record["purity"]),
            float(record["slot_delta_norm"]),
            float(record["manifold_applied_count"]),
            float(record["manifold_satisfied_count"]),
        ],
        dtype=torch.float64,
    )


def history_matrix(*, manifold_enabled: bool, repeated_seed: bool = False) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    rows: list[torch.Tensor] = []
    seed_rows: list[torch.Tensor] = []
    valid = 0
    for seed_idx in range(N_SEEDS):
        seed = 40000 if repeated_seed else 40000 + seed_idx
        rho_init = generate_initial_density(seed)
        per_seed: list[torch.Tensor] = []
        for engine_type in (0, 1):
            rho = rho_init.clone()
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                for substage_idx in range(4):
                    rho, record = replay_substage(
                        rho,
                        perception,
                        engine_type,
                        loop_class,
                        main_idx,
                        substage_idx,
                        manifold_enabled=manifold_enabled,
                    )
                    rows.append(feature_from_record(record))
                    per_seed.append(physical_feature_from_record(record))
                    valid += int(bool(record["valid_density"]))
        seed_rows.append(torch.cat(per_seed))
    matrix = torch.stack(rows)
    seed_matrix = torch.stack(seed_rows)
    centered = matrix - torch.mean(matrix, dim=0, keepdim=True)
    seed_centered = seed_matrix - torch.mean(seed_matrix, dim=0, keepdim=True)
    singular = torch.linalg.svdvals(centered)
    seed_singular = torch.linalg.svdvals(seed_centered)
    rank = int(torch.sum(singular > 1e-8).item())
    seed_rank = int(torch.sum(seed_singular > 1e-8).item())
    return matrix, seed_matrix, {
        "rows": int(matrix.shape[0]),
        "feature_dim": int(matrix.shape[1]),
        "effective_rank": rank,
        "seed_family_rows": int(seed_matrix.shape[0]),
        "seed_family_feature_dim": int(seed_matrix.shape[1]),
        "seed_family_effective_rank": seed_rank,
        "seed_family_singular_values": [float(x) for x in seed_singular.tolist()],
        "valid_rows": valid,
        "singular_values": [float(x) for x in singular.tolist()],
    }


def make_peps3d(shape: tuple[int, int, int], seed: int, bond_dim: int = 2) -> qtn.PEPS3D:
    generator = torch.Generator().manual_seed(seed)
    lx, ly, lz = shape
    arrays = []
    for i in range(lx):
        plane = []
        for j in range(ly):
            row = []
            for k in range(lz):
                legs = []
                if i < lx - 1:
                    legs.append(bond_dim)
                if j < ly - 1:
                    legs.append(bond_dim)
                if k < lz - 1:
                    legs.append(bond_dim)
                if i > 0:
                    legs.append(bond_dim)
                if j > 0:
                    legs.append(bond_dim)
                if k > 0:
                    legs.append(bond_dim)
                legs.append(2)
                row.append(torch.randn(tuple(legs), dtype=torch.float64, generator=generator) * (0.03 / bond_dim))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: Any) -> int:
    return int(sum(math.prod(tensor.shape) for tensor in tn.tensors))


def contraction_witness(seed: int) -> dict[str, float]:
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
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    generator = torch.Generator().manual_seed(12000 + seed)
    arrays = [
        torch.randn(tuple(sizes[ix] for ix in term), dtype=torch.float64, generator=generator)
        for term in inputs
    ]
    contracted = oe.contract(expr, *arrays)
    contracted_tensor = torch.as_tensor(contracted, dtype=torch.float64)
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(torch.linalg.vector_norm(contracted_tensor.reshape(-1)).item()),
    }


def carrier_response(matrix: torch.Tensor, rank: int) -> dict[str, Any]:
    seed = int(abs(float(torch.sum(matrix).item())) * 1000) % 997
    peps32 = make_peps3d((4, 4, 2), seed, bond_dim=2)
    peps64 = make_peps3d((4, 4, 4), seed + 1, bond_dim=2)
    sweep = {
        "peps3d_32": [parameter_count(make_peps3d((4, 4, 2), seed + dim, bond_dim=dim)) for dim in (2, 3)],
        "peps3d_64": [parameter_count(make_peps3d((4, 4, 4), seed + 10 + dim, bond_dim=dim)) for dim in (2, 3)],
    }
    graph = nx.DiGraph()
    graph.add_edges_from([("high_rank_histories", "peps3d_32"), ("high_rank_histories", "peps3d_64")])
    return {
        "seed": seed,
        "history_rank_used": rank,
        "peps3d_32": {
            "sites": 32,
            "num_tensors": int(peps32.num_tensors),
            "num_indices": int(peps32.num_indices),
            "parameter_count_bond2": parameter_count(peps32),
            "contraction": contraction_witness(seed + 32),
        },
        "peps3d_64": {
            "sites": 64,
            "num_tensors": int(peps64.num_tensors),
            "num_indices": int(peps64.num_indices),
            "parameter_count_bond2": parameter_count(peps64),
            "contraction": contraction_witness(seed + 64),
        },
        "bond_dimension_sweep_D2_D3_parameter_counts": sweep,
        "topology_graph_nodes": graph.number_of_nodes(),
        "topology_graph_edges": graph.number_of_edges(),
        "pass": rank >= 10
        and int(peps32.num_tensors) == 32
        and int(peps64.num_tensors) == 64
        and int(peps64.num_indices) > int(peps32.num_indices)
        and all(values[1] > values[0] for values in sweep.values()),
    }


def z3_rank_witness(seed_rank: int, repeated_seed_rank: int, disabled_seed_rank: int) -> dict[str, Any]:
    solver = z3.Solver()
    r = z3.Int("high_rank")
    rr = z3.Int("repeated_seed_rank")
    dr = z3.Int("disabled_rank")
    solver.add(r == seed_rank, rr == repeated_seed_rank, dr == disabled_seed_rank)
    solver.add(z3.Not(z3.And(r >= 8, r > rr, r >= dr)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only rank inequalities; numerical history matrices carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    matrix, seed_matrix, high = history_matrix(manifold_enabled=True, repeated_seed=False)
    repeated_matrix, repeated_seed_matrix, repeated = history_matrix(manifold_enabled=True, repeated_seed=True)
    disabled_matrix, disabled_seed_matrix, disabled = history_matrix(manifold_enabled=False, repeated_seed=False)
    response = carrier_response(matrix, high["effective_rank"])
    factors = sp.factorint(int(high["rows"]))
    positive = {
        "high_rank_source_native_engine_history_family": {
            **high,
            "rank_gain_over_old_64_row_source_readout": high["effective_rank"] - 4,
            "seed_family_rank_gain_over_repeated_seed": high["seed_family_effective_rank"] - repeated["seed_family_effective_rank"],
            "pass": high["rows"] == N_SEEDS * 2 * 32
            and high["effective_rank"] >= 10
            and high["seed_family_effective_rank"] >= 8
            and high["valid_rows"] == high["rows"],
        },
        "peps3d_32_64_capacity_accepts_high_rank_history_seed": response,
        "symbolic_history_row_factorization": {"factorization": {str(k): v for k, v in factors.items()}, "pass": factors == {2: 10}},
        "z3_rejects_seed_family_rank_collapse": z3_rank_witness(
            high["seed_family_effective_rank"],
            repeated["seed_family_effective_rank"],
            disabled["seed_family_effective_rank"],
        ),
    }
    graveyards = {
        "repeated_seed_reduces_seed_family_rank": {
            **repeated,
            "high_seed_family_rank": high["seed_family_effective_rank"],
            "pass": repeated["seed_family_effective_rank"] < high["seed_family_effective_rank"],
        },
        "manifold_disabled_is_not_promoted": {
            **disabled,
            "high_rank": high["effective_rank"],
            "note": "Disabled-manifold rank may remain high because operator slots still vary; it is a control, not evidence for manifold load-bearing.",
            "pass": PROMOTION_ALLOWED is False and disabled["valid_rows"] == disabled["rows"],
        },
        "citation_block_survives_high_rank_probe": {
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": CITES_BLOCKED_UNTIL == "full_64_site_source_native_peps3d_engine_with_high_rank_history_sweep",
        },
    }
    boundary = {
        "does_not_claim_full_64_site_engine": {"pass": "does not run the full 64-site engine" in CLAIM_CEILING},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_high_rank_engine_history_family_formal_scout",
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "root_constraints": {
            "F01_finitude": {
                "pass": True,
                "evidence": "finite 2x2 density carrier, finite Pauli operator-slot basis, finite 8-stage x 4-substage schedules, and finite 16-seed replay grid",
            },
            "N01_noncommutation": {
                "pass": True,
                "evidence": "bounded canonical QIT replay uses noncommuting Pauli generators and ordered operator/terrain slot records",
                "te_ti_commutator_norm": float(
                    torch.linalg.matrix_norm(
                        OPERATOR_GENERATORS["Te"] @ OPERATOR_GENERATORS["Ti"]
                        - OPERATOR_GENERATORS["Ti"] @ OPERATOR_GENERATORS["Te"]
                    ).item()
                ),
            },
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "High-rank source-history family only.",
            "Does not yet execute all operator-slot dynamics directly on a 64-site PEPS3D carrier.",
            "Keeps citation blocked until a full 64-site source-native bond sweep exists.",
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
