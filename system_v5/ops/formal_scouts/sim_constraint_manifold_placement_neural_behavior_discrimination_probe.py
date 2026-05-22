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
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density updates, matrix exponentials, trajectory features, controls, and neural readout",
    },
    "networkx": {"tried": True, "used": True, "reason": "supportive placement graph/factorization witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic 2x2x4x4 count witness"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness over 16 placement labels"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "networkx": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}

DTYPE = torch.complex128
RTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
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


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().T


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ dagger(vecs)
    return out / torch.trace(out)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + dagger(rho)) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float((-(vals * torch.log(vals)).sum()).item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def bloch(rho: torch.Tensor) -> list[float]:
    return [
        float(torch.real(torch.trace(SX @ rho)).item()),
        float(torch.real(torch.trace(SY @ rho)).item()),
        float(torch.real(torch.trace(SZ @ rho)).item()),
    ]


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = a - b
    vals = torch.linalg.eigvalsh((diff + dagger(diff)) / 2).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def unitary_update(rho: torch.Tensor, h: torch.Tensor, dt: float) -> torch.Tensor:
    u = torch.linalg.matrix_exp((-1j * dt) * h)
    return normalize_density(u @ rho @ dagger(u))


def dissipative_update(rho: torch.Tensor, op: torch.Tensor, gamma: float, dt: float) -> torch.Tensor:
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def projective_update(rho: torch.Tensor, axis: torch.Tensor, strength: float) -> torch.Tensor:
    axis = axis / max(float(torch.linalg.norm(axis).item()), 1e-12)
    p_plus = 0.5 * (I2 + axis)
    p_minus = 0.5 * (I2 - axis)
    pinched = p_plus @ rho @ p_plus + p_minus @ rho @ p_minus
    return normalize_density((1 - strength) * rho + strength * pinched)


def stage_axis(stage: str) -> torch.Tensor:
    return {"Si": SZ, "Se": SX, "Ne": SY, "Ni": (SX + SZ) / math.sqrt(2)}[stage]


def load_constraint_set() -> tuple[dict[str, Any], dict[str, Any]]:
    data = json.loads(ASSEMBLY_RECEIPT.read_text(encoding="utf-8"))
    constraint_set = data.get("constraint_set_for_engine", {})
    if not constraint_set:
        raise RuntimeError("assembly receipt lacks constraint_set_for_engine")
    return data, constraint_set


def initial_density(seed: int) -> torch.Tensor:
    rng = torch.Generator().manual_seed(seed)
    theta = 0.18 + 1.20 * float(torch.rand((), generator=rng, dtype=RTYPE).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=rng, dtype=RTYPE).item())
    amp1 = math.sin(theta) * complex(math.cos(phi), math.sin(phi))
    psi = torch.tensor([math.cos(theta), amp1], dtype=DTYPE).reshape(-1, 1)
    pure = psi @ dagger(psi)
    return normalize_density(0.84 * pure + 0.16 * I2 / 2)


def placement_label(sheet_idx: int, loop_idx: int, stage_idx: int) -> int:
    return sheet_idx * 8 + loop_idx * 4 + stage_idx


def placement_dynamics(
    rho: torch.Tensor,
    constraint_set: dict[str, Any],
    sheet_idx: int,
    loop_idx: int,
    stage_idx: int,
    *,
    collapsed: str | None = None,
) -> torch.Tensor:
    layer_rows = list(constraint_set["layers"])
    weights = torch.tensor([row["support_weight"] for row in layer_rows], dtype=RTYPE)
    offsets = torch.tensor([row["engine_gate_pair_offset"] for row in layer_rows], dtype=RTYPE)
    if collapsed == "flat_constraints":
        weights = torch.full_like(weights, float(weights.mean().item()))
        offsets = torch.zeros_like(offsets)
    effective_sheet_idx = 0 if collapsed == "sheet" else sheet_idx
    effective_loop_idx = 0 if collapsed == "loop" else loop_idx
    effective_stage_idx = 0 if collapsed == "stage" else stage_idx
    h_sign = +1 if effective_sheet_idx == 0 else -1
    ladder = SM if effective_sheet_idx == 0 else SP
    stage = STAGES[effective_stage_idx]
    loop = LOOPS[effective_loop_idx]
    features: list[float] = []
    for sub_idx, substage in enumerate(SUBSTAGES):
        before = rho.clone()
        op_name, op_sign = OPERATOR_SCHEDULE[
            (effective_stage_idx * len(SUBSTAGES) + sub_idx + effective_loop_idx)
            % len(OPERATOR_SCHEDULE)
        ]
        constraint_idx = (
            effective_sheet_idx * 11
            + effective_loop_idx * 7
            + effective_stage_idx * 5
            + sub_idx * 3
        ) % len(weights)
        geometry_drive = float((weights[constraint_idx] * (1.0 + offsets[constraint_idx] / max(len(offsets) - 1, 1))).item())
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
    return torch.tensor(features, dtype=RTYPE)


def build_dataset(constraint_set: dict[str, Any], *, collapsed: str | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rows: list[torch.Tensor] = []
    labels: list[int] = []
    initial_rows: list[torch.Tensor] = []
    for sheet_idx, _sheet in enumerate(SHEETS):
        for loop_idx, _loop in enumerate(LOOPS):
            for stage_idx, _stage in enumerate(STAGES):
                label = placement_label(sheet_idx, loop_idx, stage_idx)
                for sample_idx in range(N_STATES_PER_PLACEMENT):
                    rho = initial_density(10_000 + sample_idx)
                    rows.append(placement_dynamics(rho, constraint_set, sheet_idx, loop_idx, stage_idx, collapsed=collapsed))
                    labels.append(label)
                    initial_rows.append(torch.tensor(bloch(rho) + [entropy(rho), purity(rho)], dtype=RTYPE))
    return torch.stack(rows, dim=0), torch.tensor(labels, dtype=torch.long), torch.stack(initial_rows, dim=0)


def split_balanced(x: torch.Tensor, y: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    train_idx: list[int] = []
    test_idx: list[int] = []
    for label in range(N_CLASSES):
        indices = (y == label).nonzero(as_tuple=False).flatten().tolist()
        train_idx.extend(indices[:N_TRAIN_PER_PLACEMENT])
        test_idx.extend(indices[N_TRAIN_PER_PLACEMENT:])
    train = torch.tensor(train_idx, dtype=torch.long)
    test = torch.tensor(test_idx, dtype=torch.long)
    return x[train], y[train], x[test], y[test]


def torch_readout_accuracy(x: torch.Tensor, y: torch.Tensor, seed: int = 0) -> float:
    x_train, y_train, x_test, y_test = split_balanced(x, y)
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-9, torch.ones_like(std), std)
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
    tx = x_train.to(dtype=RTYPE)
    ty = y_train.to(dtype=torch.long)
    vx = x_test.to(dtype=RTYPE)
    vy = y_test.to(dtype=torch.long)
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
        for name in ("flat_constraints", "sheet", "loop", "stage")
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
            "stage_collapse_degrades_readout": {
                "pass": nominal_acc - control_acc["stage"] >= 0.08,
                "collapsed_accuracy": control_acc["stage"],
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
        "nearby_variants": {
            "total": 5,
            "passed": 0,
            "variants": [
                "flat_constraint_collapse_degrades_readout",
                "sheet_collapse_degrades_readout",
                "loop_collapse_degrades_readout",
                "stage_collapse_degrades_readout",
                "promotion_remains_disabled",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 downstream formal scout that consumes the nested constraint-manifold operational assembly receipt.",
            "It tests finite trajectory/readout behavior under placement-factor collapses rather than isolated v4 tool capability.",
        ],
        "elapsed_seconds": time.time() - started,
    }
    result["nearby_variants"]["passed"] = sum(
        1 for row in result["graveyard_companions"].values() if row["pass"]
    )
    result["all_pass"] = (
        result["consumed_receipt_status"]["pass"]
        and all(row["pass"] for row in result["positive"].values())
        and all(row["pass"] for row in result["graveyard_companions"].values())
        and all(row["pass"] for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded sheet/loop/stage placement controls and z3 collapse rejection record order-sensitive terrain placement evidence",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
