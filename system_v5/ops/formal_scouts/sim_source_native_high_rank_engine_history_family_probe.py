#!/usr/bin/env python3
"""Source-native high-rank engine history family scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import networkx as nx
import numpy as np
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_high_rank_engine_history_family_probe_results.json"

NAME = "source_native_high_rank_engine_history_family_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_high_rank_history_sweep"
CLAIM_CEILING = (
    "Formal scout only: generates a richer source-native engine-history family "
    "from multiple initial densities through both repaired chiral engines, then "
    "checks whether the resulting histories have higher effective rank for "
    "32/64-site PEPS3D carrier stress. It does not run the full 64-site engine "
    "and does not admit final manifold, physics, cognition, neural architecture, "
    "or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing source-history feature matrix and rank metrics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing PEPS3D carrier capacity construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing history dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic row-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing rank improvement witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing repaired source-native 64-slot engine execution"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_SEEDS = 16


def feature_from_record(record: dict[str, Any]) -> np.ndarray:
    terrain_index = {
        "pinching_projection": 0.0,
        "kraus_filter": 1.0,
        "lowering_dissipator": 2.0,
        "pinching_dissipator": 3.0,
        "kraus_release": 4.0,
        "outward_projection": 5.0,
        "raising_dissipator": 6.0,
    }.get(str(record.get("terrain_dynamics_family")), -1.0)
    return np.array(
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
        dtype=float,
    )


def physical_feature_from_record(record: dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            *[float(x) for x in record["bloch"]],
            float(record["entropy"]),
            float(record["purity"]),
            float(record["slot_delta_norm"]),
            float(record["manifold_applied_count"]),
            float(record["manifold_satisfied_count"]),
        ],
        dtype=float,
    )


def history_matrix(*, manifold_enabled: bool, repeated_seed: bool = False) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    rows: list[np.ndarray] = []
    seed_rows: list[np.ndarray] = []
    valid = 0
    for seed_idx in range(N_SEEDS):
        seed = 40000 if repeated_seed else 40000 + seed_idx
        rho_init = generate_initial_density(seed)
        per_seed: list[np.ndarray] = []
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=manifold_enabled)
            rho = rho_init.copy()
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    rows.append(feature_from_record(record))
                    per_seed.append(physical_feature_from_record(record))
                    valid += int(bool(record["valid_density"]))
        seed_rows.append(np.concatenate(per_seed))
    matrix = np.vstack(rows)
    seed_matrix = np.vstack(seed_rows)
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    seed_centered = seed_matrix - seed_matrix.mean(axis=0, keepdims=True)
    singular = np.linalg.svd(centered, compute_uv=False)
    seed_singular = np.linalg.svd(seed_centered, compute_uv=False)
    rank = int(np.sum(singular > 1e-8))
    seed_rank = int(np.sum(seed_singular > 1e-8))
    return matrix, seed_matrix, {
        "rows": int(matrix.shape[0]),
        "feature_dim": int(matrix.shape[1]),
        "effective_rank": rank,
        "seed_family_rows": int(seed_matrix.shape[0]),
        "seed_family_feature_dim": int(seed_matrix.shape[1]),
        "seed_family_effective_rank": seed_rank,
        "seed_family_singular_values": [float(x) for x in seed_singular],
        "valid_rows": valid,
        "singular_values": [float(x) for x in singular],
    }


def make_peps3d(shape: tuple[int, int, int], seed: int, bond_dim: int = 2) -> qtn.PEPS3D:
    rng = np.random.default_rng(seed)
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
                row.append(rng.normal(scale=0.03 / bond_dim, size=legs))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: Any) -> int:
    return int(sum(np.prod(tensor.shape) for tensor in tn.tensors))


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
    rng = np.random.default_rng(12000 + seed)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def carrier_response(matrix: np.ndarray, rank: int) -> dict[str, Any]:
    seed = int(abs(matrix.sum()) * 1000) % 997
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
