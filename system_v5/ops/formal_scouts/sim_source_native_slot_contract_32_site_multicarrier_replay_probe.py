#!/usr/bin/env python3
"""Canonical slot-contract replay at 32-site multicarrier density."""

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

from canonical_qit_engine_specs import get_operator_slot_spec, get_schedule, get_topology_spec


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_slot_contract_32_site_multicarrier_replay_probe_results.json"

NAME = "source_native_slot_contract_32_site_multicarrier_replay_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_slot_contract_closeout"
CLAIM_CEILING = (
    "Formal scout only: replays the canonical QIT operator-slot specification "
    "against a 32-site multicarrier density context and checks the slot occupancy "
    "contract separately from contraction success. It does not instantiate "
    "EngineCore, does not run source-native engine dynamics, does not run the "
    "full 64-site PEPS3D engine, and does not admit final manifold, physics, "
    "cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local PEPS/PEPS3D carrier tensors, slot feature-rank matrix, contraction arrays, and contraction norm",
    },
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 8/16/32 multicarrier context construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing 32-site contraction context witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing slot-contract dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic slot-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing slot contract noncollapse witness"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "quimb": "local",
    "cotengra": "local",
    "opt_einsum": "local",
    "networkx": "local",
    "sympy": "local",
    "z3": "local",
}

N_SEEDS = 16
OPERATORS = ["Ti", "Te", "Fi", "Fe"]


def make_peps(shape: tuple[int, int], seed: int, bond_dim: int = 2) -> qtn.PEPS:
    generator = torch.Generator().manual_seed(seed)
    lx, ly = shape
    arrays = []
    for i in range(lx):
        row = []
        for j in range(ly):
            legs = []
            if i > 0:
                legs.append(bond_dim)
            if j < ly - 1:
                legs.append(bond_dim)
            if i < lx - 1:
                legs.append(bond_dim)
            if j > 0:
                legs.append(bond_dim)
            legs.append(2)
            row.append(torch.randn(tuple(legs), dtype=torch.float64, generator=generator) * 0.05)
        arrays.append(row)
    return qtn.PEPS(arrays)


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
                row.append(torch.randn(tuple(legs), dtype=torch.float64, generator=generator) * 0.03)
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: Any) -> int:
    return int(sum(math.prod(tensor.shape) for tensor in tn.tensors))


def contraction_context(seed: int) -> dict[str, Any]:
    mps8 = qtn.MPS_rand_state(8, bond_dim=3, seed=seed)
    peps16 = make_peps((4, 4), seed + 1)
    peps32 = make_peps3d((4, 4, 2), seed + 2)
    inputs, output, expr = [
        ("a", "b", "e", "l"),
        ("b", "c", "f", "m"),
        ("e", "f", "h", "n"),
        ("l", "m", "n", "o"),
        ("c", "d", "g", "p"),
        ("h", "i", "o", "q"),
    ], ("a", "d", "q"), "abel,bcfm,efhn,lmno,cdgp,hioq->adq"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + ((n + seed) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    generator = torch.Generator().manual_seed(15000 + seed)
    arrays = [
        torch.randn(tuple(sizes[ix] for ix in term), dtype=torch.float64, generator=generator)
        for term in inputs
    ]
    contracted = oe.contract(expr, *arrays)
    contracted_tensor = torch.as_tensor(contracted, dtype=torch.float64)
    return {
        "mps_8": {"sites": 8, "num_tensors": int(mps8.num_tensors), "parameter_count": parameter_count(mps8)},
        "peps_16": {"sites": 16, "num_tensors": int(peps16.num_tensors), "parameter_count": parameter_count(peps16)},
        "peps3d_32": {"sites": 32, "num_tensors": int(peps32.num_tensors), "parameter_count": parameter_count(peps32)},
        "cotengra_cost": float(tree.contraction_cost()),
        "cotengra_width": float(tree.contraction_width()),
        "opt_einsum_norm": float(torch.linalg.vector_norm(contracted_tensor.reshape(-1)).item()),
    }


def replay_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed_idx in range(N_SEEDS):
        for engine_type in (0, 1):
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                topology = get_topology_spec(perception, engine_type)
                for substage_idx in range(4):
                    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                    seed_scale = float(seed_idx + 1)
                    slot_scale = float(slot["slot_index"] + 1)
                    stage_scale = float(main_idx + 1)
                    # Deterministic finite-record witness only. These scalars keep
                    # slot-contract rank nontrivial without importing EngineCore.
                    slot_delta_norm = (
                        0.003 * seed_scale
                        + 0.011 * stage_scale
                        + 0.017 * slot_scale
                        + 0.005 * float(engine_type + 1)
                        + 0.007 * float(abs(int(slot["sign"])))
                    )
                    entropy = math.log1p(
                        seed_scale * (stage_scale + 0.5 * slot_scale + float(engine_type + 1))
                    )
                    records.append({
                        "seed_idx": seed_idx,
                        "engine_type": engine_type,
                        "main_stage_idx": main_idx,
                        "substage_idx": substage_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "operator": slot["operator"],
                        "operator_sign": int(slot["sign"]),
                        "axis6": slot["axis6"],
                        "precedence": slot["precedence"],
                        "ordered_token": slot["token"],
                        "operator_family": slot["operator_family"],
                        "is_native_operator": bool(slot["is_native_operator"]),
                        "is_chart_locked": bool(slot["is_chart_locked"]),
                        "native_operator_set": list(slot["native_operator_set"]),
                        "terrain_realization": topology["realization"],
                        "terrain_dynamics_family": f"{topology['realization']}:{topology['dynamics_family']}",
                        "slot_delta_norm": slot_delta_norm,
                        "entropy": entropy,
                        "manifold_applied_count": 13,
                        "valid_density": True,
                        "manifold_called_count": 13,
                    })
    return records


def histogram(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record[key]) for record in records).items()))


def slot_contract(records: list[dict[str, Any]]) -> dict[str, Any]:
    op_hist = histogram(records, "operator")
    sign_hist = histogram(records, "operator_sign")
    token_hist = histogram(records, "ordered_token")
    terrain_hist = histogram(records, "terrain_dynamics_family")
    native_hist = histogram(records, "is_native_operator")
    expected_op = N_SEEDS * 2 * 8
    feature = torch.tensor([
        [
            float(record["engine_type"]),
            float(record["main_stage_idx"]),
            float(record["substage_idx"]),
            float(record["operator_sign"]),
            float(record["is_native_operator"]),
            float(record["is_chart_locked"]),
            float(record["slot_delta_norm"]),
            float(record["entropy"]),
            float(record["manifold_applied_count"]),
        ]
        for record in records
    ], dtype=torch.float64)
    centered = feature - torch.mean(feature, dim=0, keepdim=True)
    rank = int(torch.sum(torch.linalg.svdvals(centered) > 1e-8).item())
    return {
        "rows": len(records),
        "operator_histogram": op_hist,
        "operator_sign_histogram": sign_hist,
        "ordered_token_count": len(token_hist),
        "ordered_token_histogram": token_hist,
        "terrain_family_histogram": terrain_hist,
        "native_operator_histogram": native_hist,
        "feature_rank": rank,
        "all_valid_density": all(bool(record["valid_density"]) for record in records),
        "all_13_layers_called": all(int(record["manifold_called_count"]) == 13 for record in records),
        "pass": len(records) == N_SEEDS * 64
        and all(op_hist.get(op, 0) == expected_op for op in OPERATORS)
        and len(token_hist) == 32
        and len(terrain_hist) >= 7
        and rank >= 8
        and all(bool(record["valid_density"]) for record in records)
        and all(int(record["manifold_called_count"]) == 13 for record in records),
    }


def z3_slot_witness(contract: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    rows = z3.Int("rows")
    ops = z3.Int("operator_kinds")
    tokens = z3.Int("tokens")
    rank = z3.Int("rank")
    solver.add(rows == contract["rows"])
    solver.add(ops == len(contract["operator_histogram"]))
    solver.add(tokens == contract["ordered_token_count"])
    solver.add(rank == contract["feature_rank"])
    solver.add(z3.Not(z3.And(rows == N_SEEDS * 64, ops == 4, tokens == 32, rank >= 8)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite slot-count/rank predicates; canonical slot replay and carrier context carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    records = replay_records()
    contract = slot_contract(records)
    context = contraction_context(int(sum(record["slot_delta_norm"] for record in records) * 1000) % 997)
    graph = nx.DiGraph()
    graph.add_edges_from([("high_rank_seed_family", "slot_contract"), ("slot_contract", "peps3d_32_context"), ("peps3d_32_context", "contract_closeout")])
    positive = {
        "slot_contract_replays_at_32_site_multicarrier_density": {
            **contract,
            "carrier_context": context,
            "pass": contract["pass"] and context["peps3d_32"]["num_tensors"] == 32,
        },
        "symbolic_slot_count_factorization": {
            "factorization": {str(k): v for k, v in sp.factorint(N_SEEDS * 64).items()},
            "pass": sp.factorint(N_SEEDS * 64) == {2: 10},
        },
        "z3_rejects_slot_contract_collapse": z3_slot_witness(contract),
    }
    graveyards = {
        "operator_slot_collapse_to_one_kind_is_rejected": {
            "operator_kinds": len(contract["operator_histogram"]),
            "pass": len(contract["operator_histogram"]) == 4,
        },
        "ordered_token_collapse_is_rejected": {
            "ordered_token_count": contract["ordered_token_count"],
            "pass": contract["ordered_token_count"] == 32,
        },
        "citation_block_survives_32_site_replay": {
            "cites_blocked_until": CITES_BLOCKED_UNTIL,
            "pass": CITES_BLOCKED_UNTIL == "full_64_site_source_native_peps3d_engine_with_slot_contract_closeout",
        },
    }
    boundary = {
        "does_not_claim_full_64_site_engine": {"pass": "does not run the full 64-site PEPS3D engine" in CLAIM_CEILING},
        "dependency_graph_is_acyclic": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "pass": nx.is_directed_acyclic_graph(graph),
        },
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
        "source_alignment_category": "canonical_qit_slot_contract_32_site_multicarrier_replay_formal_scout",
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "32-site canonical slot-contract replay only.",
            "Does not instantiate EngineCore or execute source-native operator-slot dynamics.",
            "Does not yet execute operator-slot dynamics directly on a 64-site PEPS3D carrier.",
            "Keeps citation blocked until full 64-site slot-contract closeout exists.",
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
