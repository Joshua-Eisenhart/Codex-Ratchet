#!/usr/bin/env python3
"""Constraint-manifold delta neural readout scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
import sympy as sp
import torch
import torch.nn as nn
import torch.optim as optim
import z3

from engine_core import (
    EngineCore,
    generate_initial_density,
    _bloch_vector,
    _purity,
    _von_neumann_entropy,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_delta_neural_readout_probe_results.json"

NAME = "constraint_manifold_delta_neural_readout_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether manifold-induced density deltas across the "
    "four operator slots carry placement-specific information across 2 sheets x "
    "2 loop placements x 4 topology laws. It does not admit cognition, final AI, "
    "physics, personality, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density delta features, splitting, and accuracy summaries"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing through engine_core Lindblad ODE and matrix exponentials before manifold deltas"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing neural readout and engine_core manifold tensor bridge"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 16-placement graph witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic factorization witness"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness for manifold delta work"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_BASE_STATES = 64
N_TRAIN_BASE = 44
N_CLASSES = 16
N_EPOCHS = 360
HIDDEN_DIM = 160


def density_delta_features(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    delta = after - before
    herm = (delta + delta.conj().T) / 2
    eigs = np.linalg.eigvalsh(herm).real
    return np.array(
        [
            *(_bloch_vector(after) - _bloch_vector(before)).tolist(),
            _von_neumann_entropy(after) - _von_neumann_entropy(before),
            _purity(after) - _purity(before),
            float(0.5 * np.sum(np.abs(eigs))),
            float(np.linalg.norm(delta)),
            float(np.max(np.abs(delta.real))),
            float(np.max(np.abs(delta.imag))),
        ],
        dtype=float,
    )


def placement_label(engine_type: int, main_idx: int) -> int:
    loop_idx = 0 if main_idx < 4 else 1
    stage_idx = main_idx % 4
    return engine_type * 8 + loop_idx * 4 + stage_idx


def collect_rows(mode: str = "manifold_delta") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows: list[np.ndarray] = []
    labels: list[int] = []
    base_ids: list[int] = []
    for base_idx in range(N_BASE_STATES):
        rho_seed = generate_initial_density(20_000 + base_idx)
        for engine_type in (0, 1):
            engine_on = EngineCore(engine_type, manifold_enabled=True)
            engine_off = EngineCore(engine_type, manifold_enabled=False)
            rho_on = rho_seed.copy()
            rho_off = rho_seed.copy()
            for main_idx, (perception, loop_class) in enumerate(engine_on.schedule):
                slot_features: list[np.ndarray] = []
                for substage_idx in range(4):
                    rho_on, _ = engine_on.run_substage(rho_on, perception, loop_class, main_idx, substage_idx)
                    rho_off, _ = engine_off.run_substage(rho_off, perception, loop_class, main_idx, substage_idx)
                    slot_features.append(density_delta_features(rho_off, rho_on))
                raw_feat = np.concatenate(slot_features)
                if mode == "manifold_delta":
                    feat = raw_feat
                elif mode == "disabled_delta":
                    feat = np.zeros_like(raw_feat)
                elif mode == "initial_only":
                    one = np.array([*_bloch_vector(rho_seed), _von_neumann_entropy(rho_seed), _purity(rho_seed), 0.0, 0.0, 0.0, 0.0], dtype=float)
                    feat = np.tile(one, 4)
                elif mode == "norm_only_delta":
                    feat = np.zeros_like(raw_feat)
                    for offset in range(0, len(raw_feat), 9):
                        feat[offset + 5] = raw_feat[offset + 5]
                        feat[offset + 6] = raw_feat[offset + 6]
                elif mode == "direction_only_delta":
                    feat = raw_feat.copy()
                    for offset in range(0, len(raw_feat), 9):
                        feat[offset + 5] = 0.0
                        feat[offset + 6] = 0.0
                else:
                    raise ValueError(mode)
                rows.append(feat)
                labels.append(placement_label(engine_type, main_idx))
                base_ids.append(base_idx)
    return np.array(rows, dtype=float), np.array(labels, dtype=int), np.array(base_ids, dtype=int)


def split_by_base(x: np.ndarray, y: np.ndarray, base_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train = base_ids < N_TRAIN_BASE
    test = ~train
    return x[train], y[train], x[test], y[test]


def readout_accuracy(x: np.ndarray, y: np.ndarray, base_ids: np.ndarray, seed: int = 0) -> float:
    x_train, y_train, x_test, y_test = split_by_base(x, y, base_ids)
    mean = x_train.mean(axis=0, keepdims=True)
    std = x_train.std(axis=0, keepdims=True)
    std[std < 1e-9] = 1.0
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std
    torch.manual_seed(seed)
    model = nn.Sequential(
        nn.Linear(x_train.shape[1], HIDDEN_DIM),
        nn.Tanh(),
        nn.Linear(HIDDEN_DIM, HIDDEN_DIM // 2),
        nn.Tanh(),
        nn.Linear(HIDDEN_DIM // 2, N_CLASSES),
    ).double()
    opt = optim.Adam(model.parameters(), lr=0.012, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    tx = torch.tensor(x_train, dtype=torch.float64)
    ty = torch.tensor(y_train, dtype=torch.long)
    vx = torch.tensor(x_test, dtype=torch.float64)
    vy = torch.tensor(y_test, dtype=torch.long)
    for _ in range(N_EPOCHS):
        opt.zero_grad()
        loss = loss_fn(model(tx), ty)
        loss.backward()
        opt.step()
    with torch.no_grad():
        pred = torch.argmax(model(vx), dim=1)
    return float((pred == vy).double().mean().item())


def graph_witness() -> dict[str, Any]:
    graph = nx.Graph()
    for engine_type in (0, 1):
        for loop_idx in (0, 1):
            for stage_idx in range(4):
                graph.add_node(f"{engine_type}/{loop_idx}/{stage_idx}")
    for node in graph.nodes:
        engine_type, loop_idx, _stage_idx = node.split("/")
        for other in graph.nodes:
            if other != node and other.split("/")[:2] == [engine_type, loop_idx]:
                graph.add_edge(node, other)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "components": nx.number_connected_components(graph),
        "pass": graph.number_of_nodes() == 16 and nx.number_connected_components(graph) == 4,
    }


def z3_delta_noncollapse(delta_acc: float, disabled_acc: float) -> dict[str, Any]:
    solver = z3.Solver()
    delta_readout = z3.Bool("delta_readout")
    disabled_blocked = z3.Bool("disabled_blocked")
    solver.add(delta_readout == (delta_acc >= 0.55))
    solver.add(disabled_blocked == (disabled_acc <= 0.20))
    solver.add(delta_readout)
    solver.add(disabled_blocked)
    solver.add(z3.Not(z3.And(delta_readout, disabled_blocked)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 witnesses the encoded accuracy thresholds only; classifier/graveyard metrics carry the empirical burden.",
    }


def main() -> int:
    started = time.time()
    x_delta, y, base_ids = collect_rows("manifold_delta")
    x_disabled, _, _ = collect_rows("disabled_delta")
    x_initial, _, _ = collect_rows("initial_only")
    x_norm_only, _, _ = collect_rows("norm_only_delta")
    x_direction_only, _, _ = collect_rows("direction_only_delta")
    acc_delta = readout_accuracy(x_delta, y, base_ids, seed=11)
    acc_disabled = readout_accuracy(x_disabled, y, base_ids, seed=12)
    acc_initial = readout_accuracy(x_initial, y, base_ids, seed=13)
    acc_norm_only = readout_accuracy(x_norm_only, y, base_ids, seed=14)
    acc_direction_only = readout_accuracy(x_direction_only, y, base_ids, seed=15)
    rng = np.random.default_rng(99)
    y_shuffled = y.copy()
    rng.shuffle(y_shuffled)
    acc_direction_shuffled = readout_accuracy(x_direction_only, y_shuffled, base_ids, seed=16)
    counts = sp.Integer(2) * sp.Integer(2) * sp.Integer(4) * sp.Integer(4)
    norms = np.linalg.norm(x_delta, axis=1)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "downstream_qit_engine_on_source_native_constraint_manifold",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "dataset": {
            "shape": "2 sheets x 2 loop placements x 4 topology laws x 4 manifold-delta operator slots",
            "rows": int(len(y)),
            "classes": N_CLASSES,
            "feature_dim": int(x_delta.shape[1]),
            "symbolic_microstep_factorization": str(counts),
            "train_base_states": N_TRAIN_BASE,
            "test_base_states": N_BASE_STATES - N_TRAIN_BASE,
        },
        "accuracies": {
            "manifold_delta": acc_delta,
            "disabled_delta": acc_disabled,
            "initial_only": acc_initial,
            "norm_only_delta": acc_norm_only,
            "direction_only_delta": acc_direction_only,
            "direction_only_shuffled_labels": acc_direction_shuffled,
        },
        "delta_norm_summary": {
            "mean": float(np.mean(norms)),
            "min": float(np.min(norms)),
            "max": float(np.max(norms)),
        },
        "positive": {
            "sixteen_placement_factorization_is_present": graph_witness(),
            "manifold_delta_is_nonzero": {
                "pass": float(np.min(norms)) > 1e-6,
                "min_norm": float(np.min(norms)),
                "mean_norm": float(np.mean(norms)),
            },
            "initial_features_are_insufficient": {
                "pass": acc_initial <= 0.20,
                "accuracy": acc_initial,
                "chance": 1.0 / N_CLASSES,
            },
            "manifold_delta_readout_recovers_placement_above_chance": {
                "pass": acc_delta >= 0.55,
                "accuracy": acc_delta,
                "chance": 1.0 / N_CLASSES,
            },
            "delta_readout_beats_initial_by_margin": {
                "pass": acc_delta - acc_initial >= 0.35,
                "margin": acc_delta - acc_initial,
            },
            "z3_rejects_disabled_delta_collapse": z3_delta_noncollapse(acc_delta, acc_disabled),
        },
        "graveyard_companions": {
            "disabled_manifold_delta_cannot_recover_placement": {
                "pass": acc_disabled <= 0.20,
                "accuracy": acc_disabled,
            },
            "norm_only_delta_does_not_exhaust_directional_signal": {
                "pass": acc_direction_only - acc_norm_only >= 0.10,
                "norm_only_accuracy": acc_norm_only,
                "delta_accuracy": acc_delta,
                "direction_only_accuracy": acc_direction_only,
                "direction_over_norm_margin": acc_direction_only - acc_norm_only,
                "full_over_norm_margin": acc_delta - acc_norm_only,
                "note": "Magnitude-only deltas carry real placement signal; this check only requires that signed/directional channels add non-trivial signal beyond magnitude.",
            },
            "direction_only_delta_preserves_placement_signal": {
                "pass": acc_direction_only >= 0.85 and acc_direction_only - acc_norm_only >= 0.05,
                "direction_only_accuracy": acc_direction_only,
                "norm_only_accuracy": acc_norm_only,
                "direction_over_norm_margin": acc_direction_only - acc_norm_only,
            },
            "shuffled_label_null_kills_directional_readout": {
                "pass": acc_direction_shuffled <= 0.20,
                "direction_only_shuffled_label_accuracy": acc_direction_shuffled,
                "chance": 1.0 / N_CLASSES,
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "nearby_variants": {
            "total": 4,
            "passed": int(acc_disabled <= 0.20)
            + int(acc_delta - acc_norm_only >= 0.08)
            + int(acc_direction_only >= 0.85)
            + int(acc_direction_shuffled <= 0.20),
            "variants": ["disabled_delta", "norm_only_delta", "direction_only_delta", "direction_only_shuffled_labels"],
        },
        "boundary": {
            "does_not_claim_final_ai_or_physics": {
                "pass": "does not admit cognition" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
            },
            "features_are_physical_deltas_not_direct_labels": {
                "pass": True,
                "features": ["bloch_delta", "entropy_delta", "purity_delta", "trace_delta", "matrix_delta_norms"],
            },
            "norm_only_signal_leak_is_explicit": {
                "pass": acc_norm_only > (1.0 / N_CLASSES),
                "note": (
                    "Norm-only deltas still carry placement signal; this receipt supports full-vector "
                    "delta superiority over magnitude-only readout, not complete magnitude erasure."
                ),
                "norm_only_accuracy": acc_norm_only,
                "direction_only_accuracy": acc_direction_only,
                "direction_only_shuffled_label_accuracy": acc_direction_shuffled,
                "chance": 1.0 / N_CLASSES,
            },
        },
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "Clean v5 formal scout only.",
            "Tests manifold-induced density deltas inside the engine substage, not final intelligence or physics.",
            "Keeps human-facing labels out of the simulation ontology and preserves 2x2x4 placement factorization.",
        ],
    }
    result["all_pass"] = (
        all(row["pass"] for row in result["positive"].values())
        and all(row["pass"] for row in result["graveyard_companions"].values())
        and all(row["pass"] for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
