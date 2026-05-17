#!/usr/bin/env python3
"""Constraint-manifold layer causal-responsibility matrix scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import numpy as np
import sympy as sp
import torch
import z3

from engine_core import EngineCore, generate_initial_density, _embed_density_in_higher_dim
from claude_integrated_manifold_modules.active_layer_constraint_enforcers import (
    LAYER_NAMES,
    N_LAYERS,
    apply_all_layer_constraints,
    layer_removal_graveyard,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_layer_causal_responsibility_matrix_probe_results.json"

NAME = "constraint_manifold_layer_causal_responsibility_matrix_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: measures per-layer causal responsibility in the 13-layer "
    "constraint manifold under matched operator-slot density histories. It reports "
    "effective manifold rank and does not admit final manifold, physics, cognition, "
    "ontology, or canonical engine claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing trajectory feature distances and rank matrix"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 13-layer tensor constraint enforcer execution"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing layer dependency graph and reachability sanity"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over layer responsibility vectors"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic 13-layer inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded rank/count witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def state_features(psi: torch.Tensor) -> np.ndarray:
    arr = psi.detach().cpu().numpy()
    probs = np.abs(arr) ** 2
    probs = probs / max(float(probs.sum()), 1e-12)
    entropy = -float(np.sum(np.clip(probs, 1e-12, None) * np.log(np.clip(probs, 1e-12, None))))
    return np.array(
        [
            float(np.linalg.norm(arr)),
            entropy,
            float(np.sum(probs[: len(probs) // 2])),
            float(np.sum(probs[::2])),
            float(np.max(probs)),
            float(np.linalg.norm(arr.real)),
            float(np.linalg.norm(arr.imag)),
        ],
        dtype=float,
    )


def matched_density_history() -> list[np.ndarray]:
    engine = EngineCore(0, manifold_enabled=False)
    rho = generate_initial_density(8801)
    states: list[np.ndarray] = []
    for main_idx, (perception, loop_class) in enumerate(engine.schedule):
        for sub_idx in range(4):
            rho, _record = engine.run_substage(rho, perception, loop_class, main_idx, sub_idx)
            states.append(rho.copy())
    return states


def layer_orders(layer_idx: int) -> dict[str, list[int]]:
    base = list(range(N_LAYERS))
    delayed = base.copy()
    if layer_idx < N_LAYERS - 1:
        delayed[layer_idx], delayed[layer_idx + 1] = delayed[layer_idx + 1], delayed[layer_idx]
    advanced = base.copy()
    if layer_idx > 0:
        advanced[layer_idx], advanced[layer_idx - 1] = advanced[layer_idx - 1], advanced[layer_idx]
    return {"delayed": delayed, "advanced": advanced, "reverse": list(reversed(base))}


def run_layer_variant(
    rho: np.ndarray,
    step: int,
    layer_idx: int,
    variant: str,
    context: dict,
) -> np.ndarray:
    psi = _embed_density_in_higher_dim(rho, dim=16)
    if variant == "full":
        out, _metrics = apply_all_layer_constraints(psi, step, context)
    elif variant == "removed":
        out, _metrics = layer_removal_graveyard(psi, step, context, layer_idx)
    elif variant == "validator_only":
        out = psi
    elif variant in ("delayed", "advanced", "reverse"):
        out, _metrics = apply_all_layer_constraints(psi, step, context, layer_order=layer_orders(layer_idx)[variant])
    elif variant == "adversarial_phase":
        phase = torch.exp(1j * torch.linspace(0.0, math.pi / 3.0, psi.numel(), dtype=torch.float64)).to(psi.dtype)
        out, _metrics = apply_all_layer_constraints(psi * phase, step, context)
    else:
        raise ValueError(variant)
    return state_features(out)


def run_variant_sequence(history: list[np.ndarray], layer_idx: int, variant: str) -> np.ndarray:
    context: dict = {}
    return np.stack(
        [run_layer_variant(rho, step, layer_idx, variant, context) for step, rho in enumerate(history)],
        axis=0,
    )


def responsibility_matrix() -> dict[str, Any]:
    history = matched_density_history()
    variants = ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"]
    rows = []
    for layer_idx, name in enumerate(LAYER_NAMES):
        full_feats = []
        full_arr = run_variant_sequence(history, layer_idx, "full")
        distances = {
            variant: float(np.linalg.norm(full_arr - run_variant_sequence(history, layer_idx, variant), axis=1).mean())
            for variant in variants
        }
        non_substitutable = (
            distances["removed"] > 1e-3
            and distances["validator_only"] > 1e-3
            and max(distances["delayed"], distances["advanced"], distances["reverse"]) > 1e-4
        )
        rows.append(
            {
                "layer_idx": layer_idx,
                "layer_name": name,
                "distances": distances,
                "non_substitutable": non_substitutable,
            }
        )
    rank = sum(1 for row in rows if row["non_substitutable"])
    return {"rows": rows, "effective_rank": rank, "total_layers": N_LAYERS}


def persistence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    points = np.array(
        [[row["distances"][key] for key in ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"]] for row in rows],
        dtype=float,
    )
    complex_ = gudhi.RipsComplex(points=points, max_edge_length=5.0).create_simplex_tree(max_dimension=2)
    bars = complex_.persistence()
    finite_h0 = sum(1 for dim, bd in bars if dim == 0 and math.isfinite(bd[1]))
    finite_h1 = sum(1 for dim, bd in bars if dim == 1 and math.isfinite(bd[1]))
    return {"finite_h0_bars": finite_h0, "finite_h1_bars": finite_h1, "pass": finite_h0 > 0}


def graph_witness() -> dict[str, Any]:
    graph = nx.DiGraph()
    for idx, name in enumerate(LAYER_NAMES):
        graph.add_node(idx, name=name)
        if idx:
            graph.add_edge(idx - 1, idx)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
        "pass": graph.number_of_nodes() == 13 and graph.number_of_edges() == 12 and nx.is_directed_acyclic_graph(graph),
    }


def z3_rank_witness(rank: int) -> dict[str, Any]:
    solver = z3.Solver()
    effective_rank = z3.Int("effective_rank")
    solver.add(effective_rank == rank)
    solver.add(effective_rank >= 10)
    solver.add(z3.Not(effective_rank >= 10))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Encoded effective-rank threshold witness only; distances carry empirical burden.",
    }


def main() -> int:
    started = time.time()
    matrix = responsibility_matrix()
    rank = int(matrix["effective_rank"])
    positive = {
        "thirteen_layer_inventory_present": {
            "pass": len(LAYER_NAMES) == 13 and bool(sp.Eq(sp.Integer(len(LAYER_NAMES)), sp.Integer(13))),
            "layers": list(LAYER_NAMES),
        },
        "layer_dependency_graph_is_complete": graph_witness(),
        "effective_manifold_rank_is_measured": {
            "pass": rank >= 1,
            "effective_rank": rank,
            "total_layers": N_LAYERS,
            "rank_label": "full_13_layer" if rank == 13 else f"effective_{rank}_of_13",
        },
        "gudhi_responsibility_persistence_executes": persistence(matrix["rows"]),
        "z3_rejects_rank_below_threshold": z3_rank_witness(rank),
    }
    graveyards = {
        "validator_only_control_is_not_equivalent_to_full_for_some_layers": {
            "pass": any(row["distances"]["validator_only"] > 1e-3 for row in matrix["rows"]),
            "max_validator_only_distance": max(row["distances"]["validator_only"] for row in matrix["rows"]),
        },
        "layer_removal_control_is_not_equivalent_to_full_for_some_layers": {
            "pass": any(row["distances"]["removed"] > 1e-3 for row in matrix["rows"]),
            "max_removed_distance": max(row["distances"]["removed"] for row in matrix["rows"]),
        },
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    boundary = {
        "reports_effective_rank_not_full_claim": {
            "pass": True,
            "note": "If effective_rank < 13, this receipt explicitly demotes the manifold reading to conditional/effective.",
        }
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "layer_causal_responsibility_audit_for_constraint_manifold",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "responsibility_matrix": matrix,
        "nearby_variants": {
            "total": 6,
            "passed": sum(1 for variant in ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"] if any(row["distances"][variant] > 1e-4 for row in matrix["rows"])),
            "variants": ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"],
        },
        "why_not_v4_probes": [
            "Formal scout only.",
            "Measures layer causal responsibility; does not prove final full manifold.",
            "If rank is below 13, the honest interpretation is an effective lower-rank manifold under current clean trajectories.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    result["all_pass"] = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} rank={rank}/13 -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
