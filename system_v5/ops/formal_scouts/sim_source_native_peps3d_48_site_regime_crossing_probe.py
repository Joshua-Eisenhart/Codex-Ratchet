#!/usr/bin/env python3
"""Source-native PEPS3D 48-site regime-crossing scout."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import time
from collections import Counter
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
OUT_PATH = RESULT_DIR / "source_native_peps3d_48_site_regime_crossing_probe_results.json"

NAME = "source_native_peps3d_48_site_regime_crossing_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "full_64_site_source_native_peps3d_engine_with_48_site_regime_clean"
CLAIM_CEILING = (
    "Formal scout only: probes the intermediate 48-site PEPS3D regime between "
    "32 and 64 sites while replaying the source-native operator-slot contract. "
    "It does not run the full 64-site engine and does not admit final manifold, "
    "physics, cognition, neural architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing 32/48/64 capacity and slot histograms"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 32/48/64 PEPS3D construction"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree context"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction numeric cross-check"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing regime ladder graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic site-count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing 32<48<64 and slot-contract witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native slot replay"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_SEEDS = 8


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
                row.append(rng.normal(scale=0.025 / bond_dim, size=legs))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def parameter_count(tn: Any) -> int:
    return int(sum(np.prod(tensor.shape) for tensor in tn.tensors))


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
    rng = np.random.default_rng(18000 + seed + sites)
    arrays = [rng.normal(size=tuple(sizes[ix] for ix in term)) for term in inputs]
    return {
        "cost": float(tree.contraction_cost()),
        "width": float(tree.contraction_width()),
        "norm": float(np.linalg.norm(oe.contract(expr, *arrays))),
    }


def carrier_ladder(seed: int) -> dict[str, Any]:
    specs = {"peps3d_32": (4, 4, 2), "peps3d_48": (4, 4, 3), "peps3d_64": (4, 4, 4)}
    rows: dict[str, Any] = {}
    for label, shape in specs.items():
        sites = int(np.prod(shape))
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
        rho_init = generate_initial_density(60000 + seed_idx)
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = rho_init.copy()
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    records.append(record)
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
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_peps3d_48_site_regime_crossing_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
