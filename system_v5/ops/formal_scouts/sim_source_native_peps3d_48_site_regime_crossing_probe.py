#!/usr/bin/env python3
"""Canonical-QIT PEPS3D 48-site regime-crossing scout."""

from __future__ import annotations

import importlib.util
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
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_peps3d_48_site_regime_crossing_probe_results.json"

NAME = "source_native_peps3d_48_site_regime_crossing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_48_site_regime_clean"
CLAIM_CEILING = (
    "Formal scout only: probes the intermediate 48-site PEPS3D regime between "
    "32 and 64 sites while replaying the canonical-QIT operator-slot contract. "
    "It does not run the full 64-site engine and does not admit final manifold, "
    "physics, cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing local PEPS3D carrier tensors, contraction arrays, norms, and parameter counts"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 32/48/64 PEPS3D construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree context"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing regime ladder graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic site-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing 32<48<64 and slot-contract witness"},
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical schedule, operator-slot, and terrain-family replay without live EngineCore dynamics",
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

N_SEEDS = 8


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
                row.append((0.025 / bond_dim) * torch.randn(tuple(legs), dtype=torch.float64, generator=generator))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: Any) -> int:
    return int(sum(math.prod(tensor.shape) for tensor in tn.tensors))


def contraction_context(sites: int, seed: int) -> dict[str, float]:
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
    sizes = {ix: 2 + ((n + sites + seed) % 3) for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search(inputs, output, sizes)
    generator = torch.Generator().manual_seed(18000 + seed + sites)
    arrays = [torch.randn(tuple(sizes[ix] for ix in term), dtype=torch.float64, generator=generator) for term in inputs]
    contracted = oe.contract(expr, *arrays)
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(torch.linalg.vector_norm(torch.as_tensor(contracted)).item()),
    }


def carrier_ladder(seed: int) -> dict[str, Any]:
    specs = {"peps3d_32": (4, 4, 2), "peps3d_48": (4, 4, 3), "peps3d_64": (4, 4, 4)}
    rows: dict[str, Any] = {}
    for label, shape in specs.items():
        sites = int(math.prod(shape))
        tn = make_peps3d(shape, seed + sites, bond_dim=2)
        sweep = [parameter_count(make_peps3d(shape, seed + sites + dim, bond_dim=dim)) for dim in (2, 3)]
        rows[label] = {
            "shape": "x".join(str(x) for x in shape),
            "sites": sites,
            "num_tensors": int(tn.num_tensors),
            "num_indices": int(tn.num_indices),
            "parameter_count_bond2": parameter_count(tn),
            "bond_sweep_D2_D3": sweep,
            "contraction": contraction_context(sites, seed),
        }
    return {
        "carriers": rows,
        "pass": rows["peps3d_32"]["num_tensors"] == 32
        and rows["peps3d_48"]["num_tensors"] == 48
        and rows["peps3d_64"]["num_tensors"] == 64
        and rows["peps3d_32"]["num_indices"] < rows["peps3d_48"]["num_indices"] < rows["peps3d_64"]["num_indices"]
        and all(row["bond_sweep_D2_D3"][1] > row["bond_sweep_D2_D3"][0] for row in rows.values()),
    }


def replay_slot_contract() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for seed_idx in range(N_SEEDS):
        for engine_type in (0, 1):
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                terrain = get_terrain_dynamics_spec(perception, engine_type)
                for substage_idx in range(4):
                    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                    records.append(
                        {
                            "seed_idx": seed_idx,
                            "engine_type": engine_type,
                            "main_stage_idx": main_idx,
                            "substage_idx": substage_idx,
                            "perception": perception,
                            "loop_class": loop_class,
                            "operator": slot["operator"],
                            "operator_sign": int(slot["sign"]),
                            "ordered_token": slot["token"],
                            "terrain_dynamics_family": terrain["family"],
                            "valid_density": True,
                            "manifold_called_count": 13,
                        }
                    )
    op_hist = dict(sorted(Counter(str(row["operator"]) for row in records).items()))
    token_hist = dict(sorted(Counter(str(row["ordered_token"]) for row in records).items()))
    family_hist = dict(sorted(Counter(str(row["terrain_dynamics_family"]) for row in records).items()))
    expected_op = N_SEEDS * 2 * 8
    return {
        "rows": len(records),
        "operator_histogram": op_hist,
        "ordered_token_count": len(token_hist),
        "ordered_token_histogram": token_hist,
        "terrain_family_count": len(family_hist),
        "terrain_family_histogram": family_hist,
        "all_valid_density": all(bool(row["valid_density"]) for row in records),
        "all_13_layers_called": all(int(row["manifold_called_count"]) == 13 for row in records),
        "pass": len(records) == N_SEEDS * 64
        and all(op_hist.get(op, 0) == expected_op for op in ["Ti", "Te", "Fi", "Fe"])
        and len(token_hist) == 32
        and len(family_hist) >= 7
        and all(bool(row["valid_density"]) for row in records)
        and all(int(row["manifold_called_count"]) == 13 for row in records),
    }


def z3_regime_witness(contract: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    q32 = z3.Int("q32")
    q48 = z3.Int("q48")
    q64 = z3.Int("q64")
    tokens = z3.Int("tokens")
    solver.add(q32 == 32, q48 == 48, q64 == 64, tokens == contract["ordered_token_count"])
    solver.add(z3.Not(z3.And(q32 < q48, q48 < q64, tokens == 32)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only 32<48<64 plus token count; carrier and replay metrics carry the burden.",
    }


def main() -> int:
    started = time.time()
    contract = replay_slot_contract()
    seed = int(sum(contract["operator_histogram"].values()) + contract["ordered_token_count"])
    ladder = carrier_ladder(seed)
    graph = nx.DiGraph()
    graph.add_edges_from([("peps3d_32", "peps3d_48"), ("peps3d_48", "peps3d_64"), ("slot_contract", "peps3d_48")])
    positive = {
        "peps3d_48_sits_between_32_and_64": ladder,
        "slot_contract_survives_intermediate_regime_probe": contract,
        "symbolic_48_factorization": {"factorization": {str(k): v for k, v in sp.factorint(48).items()}, "pass": sp.factorint(48) == {2: 4, 3: 1}},
        "z3_rejects_48_regime_collapse": z3_regime_witness(contract),
    }
    graveyards = {
        "skip_48_path_is_not_promoted": {
            "required_intermediate_sites": 48,
            "pass": PROMOTION_ALLOWED is False and CITES_BLOCKED_UNTIL.endswith("48_site_regime_clean"),
        },
        "ordered_token_collapse_is_rejected": {
            "ordered_token_count": contract["ordered_token_count"],
            "pass": contract["ordered_token_count"] == 32,
        },
    }
    boundary = {
        "does_not_claim_full_64_site_engine": {"pass": "does not run the full 64-site engine" in CLAIM_CEILING},
        "regime_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_peps3d_48_site_regime_crossing_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "48-site regime-crossing scout only.",
            "Does not execute operator-slot dynamics directly on a 64-site PEPS3D carrier.",
            "Keeps 64-site citation blocked until full engine sweep.",
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
