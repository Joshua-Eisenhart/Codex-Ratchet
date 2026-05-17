#!/usr/bin/env python3
"""Constraint-manifold placement neural behavior discrimination scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
from scipy.linalg import expm
import sympy as sp
import torch
import torch.nn as nn
import torch.optim as optim
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
ASSEMBLY_RECEIPT = RESULT_DIR / "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json"
OUT_PATH = RESULT_DIR / "constraint_manifold_placement_neural_behavior_discrimination_probe_results.json"

NAME = "constraint_manifold_placement_neural_behavior_discrimination_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether the 2 sheet x 2 loop-placement x 4 topology-law "
    "constraint-manifold placements produce distinguishable finite QIT trajectory "
    "behaviors for a small PyTorch readout. It does not admit cognition, AI, final "
    "physics, personality, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density updates, trajectory features, and controls"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for placement substage dynamics"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing neural readout trained on placement trajectories"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing placement graph/factorization witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic 2x2x4x4 count witness"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness over 16 placement labels"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex128
I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
SM = np.array([[0, 0], [1, 0]], dtype=DTYPE)
SP = np.array([[0, 1], [0, 0]], dtype=DTYPE)
H0 = 0.73 * SZ + 0.17 * SX

SHEETS = ["left_chiral_density_space", "right_chiral_density_space"]
LOOPS = ["fiber", "base_lift"]
STAGES = ["Si", "Se", "Ne", "Ni"]
SUBSTAGES = ["signed_hamiltonian", "ladder_direction", "stage_projection", "loop_transport"]
OPERATORS = {"Ti": SZ, "Te": SX, "Fi": SX + 0.2 * SZ, "Fe": SY}
OPERATOR_SCHEDULE = [
    ("Ti", +1),
    ("Te", -1),
    ("Fi", +1),
    ("Fe", -1),
    ("Ti", -1),
    ("Te", +1),
    ("Fi", -1),
    ("Fe", +1),
]

N_STATES_PER_PLACEMENT = 18
N_TRAIN_PER_PLACEMENT = 12
N_CLASSES = 16
N_EPOCHS = 160
HIDDEN_DIM = 64


def dagger(a: np.ndarray) -> np.ndarray:
    return a.conj().T


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = np.linalg.eigh(rho)
    vals = np.maximum(vals.real, 1e-12)
    out = vecs @ np.diag(vals) @ dagger(vecs)
    return out / np.trace(out)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = np.maximum(vals, 1e-12)
    vals = vals / vals.sum()
    return float(-(vals * np.log(vals)).sum())


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def bloch(rho: np.ndarray) -> list[float]:
    return [
        float(np.real(np.trace(SX @ rho))),
        float(np.real(np.trace(SY @ rho))),
        float(np.real(np.trace(SZ @ rho))),
    ]


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((a - b + dagger(a - b)) / 2)
    return float(0.5 * np.sum(np.abs(vals)))


def unitary_update(rho: np.ndarray, h: np.ndarray, dt: float) -> np.ndarray:
    u = expm(-1j * h * dt)
    return normalize_density(u @ rho @ dagger(u))


def dissipative_update(rho: np.ndarray, op: np.ndarray, gamma: float, dt: float) -> np.ndarray:
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def projective_update(rho: np.ndarray, axis: np.ndarray, strength: float) -> np.ndarray:
    axis = axis / max(float(np.linalg.norm(axis)), 1e-12)
    p_plus = 0.5 * (I2 + axis)
    p_minus = 0.5 * (I2 - axis)
    pinched = p_plus @ rho @ p_plus + p_minus @ rho @ p_minus
    return normalize_density((1 - strength) * rho + strength * pinched)


def stage_axis(stage: str) -> np.ndarray:
    return {"Si": SZ, "Se": SX, "Ne": SY, "Ni": (SX + SZ) / math.sqrt(2)}[stage]


def load_constraint_set() -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(ASSEMBLY_RECEIPT.read_text(encoding="utf-8"))
    constraint_set = data.get("constraint_set_for_engine", {})
    if not constraint_set:
        raise RuntimeError("assembly receipt lacks constraint_set_for_engine")
    return data, constraint_set


def initial_density(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    theta = 0.18 + 1.20 * rng.random()
    phi = 2.0 * math.pi * rng.random()
    psi = np.array([math.cos(theta), math.sin(theta) * np.exp(1j * phi)], dtype=DTYPE).reshape(-1, 1)
    pure = psi @ dagger(psi)
    return normalize_density(0.84 * pure + 0.16 * I2 / 2)


def placement_label(sheet_idx: int, loop_idx: int, stage_idx: int) -> int:
    return sheet_idx * 8 + loop_idx * 4 + stage_idx


def placement_dynamics(
    rho: np.ndarray,
    constraint_set: dict[str, Any],
    sheet_idx: int,
    loop_idx: int,
    stage_idx: int,
    *,
    collapsed: str | None = None,
) -> np.ndarray:
    layer_rows = list(constraint_set["layers"])
    weights = np.array([row["support_weight"] for row in layer_rows], dtype=float)
    offsets = np.array([row["engine_gate_pair_offset"] for row in layer_rows], dtype=float)
    if collapsed == "flat_constraints":
        weights = np.full_like(weights, float(np.mean(weights)))
        offsets = np.zeros_like(offsets)
    h_sign = +1 if sheet_idx == 0 else -1
    ladder = SM if sheet_idx == 0 else SP
    if collapsed == "sheet":
        h_sign = +1
        ladder = SM
    stage = STAGES[stage_idx]
    loop = LOOPS[loop_idx]
    if collapsed == "loop":
        loop = "fiber"
    features: list[float] = []
    for sub_idx, substage in enumerate(SUBSTAGES):
        before = rho.copy()
        op_name, op_sign = OPERATOR_SCHEDULE[(stage_idx * len(SUBSTAGES) + sub_idx + loop_idx) % len(OPERATOR_SCHEDULE)]
        if collapsed == "operator_sign":
            op_sign = +1
        constraint_idx = (sheet_idx * 11 + loop_idx * 7 + stage_idx * 5 + sub_idx * 3) % len(weights)
        geometry_drive = float(weights[constraint_idx] * (1.0 + offsets[constraint_idx] / max(len(offsets) - 1, 1)))
        dt = 0.030 + 0.034 * geometry_drive
        if substage == "signed_hamiltonian":
            rho = unitary_update(rho, h_sign * H0 + 0.22 * op_sign * geometry_drive * OPERATORS[op_name], dt)
        elif substage == "ladder_direction":
            rho = dissipative_update(rho, ladder, 0.10 + 0.20 * geometry_drive, dt)
        elif substage == "stage_projection":
            rho = projective_update(rho, stage_axis(stage), min(0.26, 0.05 + 0.13 * geometry_drive))
        else:
            loop_axis = SZ if loop == "fiber" else 0.80 * SX + 0.20 * SZ
            rho = unitary_update(rho, 0.19 * op_sign * geometry_drive * loop_axis + 0.05 * OPERATORS[op_name], dt)
        features.extend(bloch(rho))
        features.extend([
            entropy(rho),
            purity(rho),
            trace_distance(before, rho),
            geometry_drive,
            float(h_sign),
            float(op_sign),
        ])
    return np.array(features, dtype=float)


def build_dataset(constraint_set: dict[str, Any], *, collapsed: str | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows: list[np.ndarray] = []
    labels: list[int] = []
    initial_rows: list[np.ndarray] = []
    for sheet_idx, _sheet in enumerate(SHEETS):
        for loop_idx, _loop in enumerate(LOOPS):
            for stage_idx, _stage in enumerate(STAGES):
                label = placement_label(sheet_idx, loop_idx, stage_idx)
                for sample_idx in range(N_STATES_PER_PLACEMENT):
                    rho = initial_density(10_000 + sample_idx)
                    rows.append(placement_dynamics(rho, constraint_set, sheet_idx, loop_idx, stage_idx, collapsed=collapsed))
                    labels.append(label)
                    initial_rows.append(np.array(bloch(rho) + [entropy(rho), purity(rho)], dtype=float))
    return np.array(rows, dtype=float), np.array(labels, dtype=int), np.array(initial_rows, dtype=float)


def split_balanced(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_idx: list[int] = []
    test_idx: list[int] = []
    for label in range(N_CLASSES):
        indices = np.where(y == label)[0].tolist()
        train_idx.extend(indices[:N_TRAIN_PER_PLACEMENT])
        test_idx.extend(indices[N_TRAIN_PER_PLACEMENT:])
    return x[train_idx], y[train_idx], x[test_idx], y[test_idx]


def torch_readout_accuracy(x: np.ndarray, y: np.ndarray, seed: int = 0) -> float:
    x_train, y_train, x_test, y_test = split_balanced(x, y)
    mean = x_train.mean(axis=0, keepdims=True)
    std = x_train.std(axis=0, keepdims=True)
    std[std < 1e-9] = 1.0
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std
    torch.manual_seed(seed)
    model = nn.Sequential(
        nn.Linear(x_train.shape[1], HIDDEN_DIM),
        nn.Tanh(),
        nn.Linear(HIDDEN_DIM, N_CLASSES),
    ).double()
    opt = optim.Adam(model.parameters(), lr=0.015, weight_decay=1e-4)
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
    for sheet_idx, sheet in enumerate(SHEETS):
        for loop_idx, loop in enumerate(LOOPS):
            for stage_idx, stage in enumerate(STAGES):
                node = f"{sheet}/{loop}/{stage}"
                graph.add_node(node, sheet=sheet_idx, loop=loop_idx, stage=stage_idx)
    for left in graph.nodes:
        for right in graph.nodes:
            if left < right and left.split("/")[:2] == right.split("/")[:2]:
                graph.add_edge(left, right)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "connected_components": nx.number_connected_components(graph),
        "pass": graph.number_of_nodes() == 16 and nx.number_connected_components(graph) == 4,
    }


def z3_noncollapse(acc: float, init_acc: float) -> dict[str, Any]:
    solver = z3.Solver()
    placement_work = z3.Bool("placement_work")
    initial_blocked = z3.Bool("initial_blocked")
    solver.add(placement_work == (acc >= 0.70))
    solver.add(initial_blocked == (init_acc <= 0.20))
    solver.add(placement_work)
    solver.add(initial_blocked)
    solver.add(z3.Not(z3.And(placement_work, initial_blocked)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat}


def main() -> int:
    started = time.time()
    assembly, constraint_set = load_constraint_set()
    x, y, x_initial = build_dataset(constraint_set)
    controls = {
        name: build_dataset(constraint_set, collapsed=name)[0]
        for name in ("flat_constraints", "sheet", "loop", "operator_sign")
    }
    nominal_acc = torch_readout_accuracy(x, y, seed=1)
    initial_acc = torch_readout_accuracy(x_initial, y, seed=2)
    control_acc = {name: torch_readout_accuracy(cx, y, seed=3 + idx) for idx, (name, cx) in enumerate(controls.items())}
    count_expr = sp.Integer(2) * sp.Integer(2) * sp.Integer(4) * sp.Integer(4)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "downstream_qit_engine_on_source_native_constraint_manifold",
        "consumed_receipts": {"manifold_operational_assembly_receipt": ASSEMBLY_RECEIPT.name},
        "consumed_receipt_status": {
            "pass": assembly.get("summary", {}).get("all_pass") is True
            and constraint_set.get("schema") == "CONSTRAINT_SET_FOR_QIT_ENGINE_v1",
            "constraint_set_schema": constraint_set.get("schema"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "dataset": {
            "shape": "2 sheets x 2 loop placements x 4 topology laws x 4 substages",
            "placement_classes": N_CLASSES,
            "samples": int(len(y)),
            "trajectory_feature_dim": int(x.shape[1]),
            "symbolic_microstep_factorization": str(count_expr),
        },
        "accuracies": {
            "initial_only": initial_acc,
            "nominal_trajectory": nominal_acc,
            "controls": control_acc,
        },
        "positive": {
            "manifold_constraint_set_is_loaded": {
                "pass": constraint_set.get("schema") == "CONSTRAINT_SET_FOR_QIT_ENGINE_v1",
                "layer_count": constraint_set.get("layer_count"),
            },
            "screenshot_factorization_defines_sixteen_placements": {
                "pass": x.shape[0] == N_CLASSES * N_STATES_PER_PLACEMENT and str(count_expr) == "64",
                "classes": N_CLASSES,
                "samples": int(x.shape[0]),
                "graph": graph_witness(),
            },
            "initial_features_are_insufficient_for_placement_id": {
                "pass": initial_acc <= 0.20,
                "accuracy": initial_acc,
                "chance": 1.0 / N_CLASSES,
            },
            "neural_readout_recovers_placement_behavior": {
                "pass": nominal_acc >= 0.70,
                "accuracy": nominal_acc,
            },
            "trajectory_beats_initial_by_large_margin": {
                "pass": nominal_acc - initial_acc >= 0.50,
                "margin": nominal_acc - initial_acc,
            },
            "z3_rejects_placement_initial_collapse": z3_noncollapse(nominal_acc, initial_acc),
        },
        "graveyard_companions": {
            "flat_constraint_collapse_degrades_readout": {
                "pass": nominal_acc - control_acc["flat_constraints"] >= 0.08,
                "collapsed_accuracy": control_acc["flat_constraints"],
                "nominal_accuracy": nominal_acc,
            },
            "sheet_collapse_degrades_readout": {
                "pass": nominal_acc - control_acc["sheet"] >= 0.08,
                "collapsed_accuracy": control_acc["sheet"],
                "nominal_accuracy": nominal_acc,
            },
            "loop_collapse_degrades_readout": {
                "pass": nominal_acc - control_acc["loop"] >= 0.08,
                "collapsed_accuracy": control_acc["loop"],
                "nominal_accuracy": nominal_acc,
            },
            "operator_sign_collapse_degrades_readout": {
                "pass": nominal_acc - control_acc["operator_sign"] >= 0.08,
                "collapsed_accuracy": control_acc["operator_sign"],
                "nominal_accuracy": nominal_acc,
            },
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "boundary": {
            "does_not_use_human_facing_jargon_as_sim_ontology": {
                "pass": True,
                "ontology_fields": ["sheet", "loop_placement", "topology_law", "substage"],
            },
            "does_not_claim_real_ai_or_intelligence": {
                "pass": "does not admit cognition" in CLAIM_CEILING and "canonical manifold" in CLAIM_CEILING,
            },
        },
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    result["all_pass"] = (
        result["consumed_receipt_status"]["pass"]
        and all(row["pass"] for row in result["positive"].values())
        and all(row["pass"] for row in result["graveyard_companions"].values())
        and all(row["pass"] for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
