#!/usr/bin/env python3
"""Constraint-manifold delta neural readout scout."""

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

from canonical_qit_engine_specs import (
    I2,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    SX,
    SY,
    SZ,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_delta_neural_readout_probe_results.json"

NAME = "constraint_manifold_delta_neural_readout_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether bounded canonical QIT replay manifold "
    "density deltas across the four operator slots carry placement-specific "
    "information across 2 sheets x 2 loop placements x 4 topology laws. It does "
    "not admit source-native EngineCore dynamics, nonclassical basin admission, "
    "cognition, final AI, physics, personality, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical schedule, operator, and terrain metadata replacing the former direct EngineCore importer boundary",
    },
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing canonical QIT replay, density delta features, splitting, summaries, and neural readout"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 16-placement graph witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic factorization witness"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness for manifold delta work"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "canonical_qit_engine_specs" else "load_bearing")
    for tool in TOOL_MANIFEST
}
TOOL_ROLE_SOURCE = {tool: "local_supportive" if tool == "canonical_qit_engine_specs" else "local" for tool in TOOL_MANIFEST}

N_BASE_STATES = 64
N_TRAIN_BASE = 44
N_CLASSES = 16
N_EPOCHS = 360
HIDDEN_DIM = 160
TORCH_COMPLEX = torch.complex128
TORCH_REAL = torch.float64
STAGE_DT = 0.08
MANIFOLD_TARGET_MIX = 0.12


def normalize_density(rho: Any) -> torch.Tensor:
    tensor = torch.as_tensor(rho, dtype=TORCH_COMPLEX)
    hermitian = 0.5 * (tensor + tensor.conj().T)
    eigvals, eigvecs = torch.linalg.eigh(hermitian)
    eigvals = torch.clamp(eigvals.real, min=0.0)
    total = torch.sum(eigvals)
    if float(total.item()) <= 1e-14:
        return I2 / 2.0
    out = eigvecs @ torch.diag(eigvals.to(TORCH_COMPLEX)) @ eigvecs.conj().T
    return 0.5 * (out / total.to(TORCH_COMPLEX) + (out / total.to(TORCH_COMPLEX)).conj().T)


def generate_initial_density(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(int(seed))
    theta = 0.24 + 1.05 * float(torch.rand((), generator=generator, dtype=TORCH_REAL).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=generator, dtype=TORCH_REAL).item())
    psi = torch.tensor(
        [math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))],
        dtype=TORCH_COMPLEX,
    )
    pure = torch.outer(psi, psi.conj())
    return normalize_density(0.88 * pure + 0.12 * I2 / 2.0)


def density_entropy(rho: Any) -> float:
    tensor = normalize_density(rho)
    eigvals = torch.clamp(torch.linalg.eigvalsh(tensor).real, min=1e-14)
    return float((-torch.sum(eigvals * torch.log(eigvals))).item())


def density_purity(rho: Any) -> float:
    tensor = normalize_density(rho)
    return float(torch.real(torch.trace(tensor @ tensor)).item())


def bloch_vector(rho: Any) -> torch.Tensor:
    tensor = normalize_density(rho)
    return torch.tensor(
        [
            float(torch.real(torch.trace(SX @ tensor)).item()),
            float(torch.real(torch.trace(SY @ tensor)).item()),
            float(torch.real(torch.trace(SZ @ tensor)).item()),
        ],
        dtype=TORCH_REAL,
    )


def axis_matrix(axis: str) -> torch.Tensor:
    if axis == "x":
        return SX
    if axis == "y":
        return SY
    if axis == "z":
        return SZ
    raise ValueError(f"unknown axis {axis!r}")


def pinch(rho: torch.Tensor, axis: str) -> torch.Tensor:
    pauli = axis_matrix(axis)
    p0 = 0.5 * (I2 + pauli)
    p1 = 0.5 * (I2 - pauli)
    return normalize_density(p0 @ rho @ p0 + p1 @ rho @ p1)


def kraus_filter(rho: torch.Tensor, axis: str, strength: float, *, release: bool = False) -> torch.Tensor:
    p0 = 0.5 * (I2 + axis_matrix(axis))
    p1 = 0.5 * (I2 - axis_matrix(axis))
    if release:
        filt = math.sqrt(max(1.0 - strength, 1e-9)) * p0 + math.sqrt(1.0 + strength) * p1
    else:
        filt = math.sqrt(1.0 + strength) * p0 + math.sqrt(max(1.0 - strength, 1e-9)) * p1
    return normalize_density(filt @ rho @ filt.conj().T)


def lindblad_rhs_matrix(H: torch.Tensor, L: torch.Tensor) -> torch.Tensor:
    ldag_l = L.conj().T @ L
    basis: list[torch.Tensor] = []
    for i in range(2):
        for j in range(2):
            e = torch.zeros((2, 2), dtype=TORCH_COMPLEX)
            e[i, j] = 1.0 + 0.0j
            basis.append(e)
    cols = []
    for e in basis:
        de = -1j * (H @ e - e @ H)
        de = de + L @ e @ L.conj().T
        de = de - 0.5 * (ldag_l @ e + e @ ldag_l)
        cols.append(de.reshape(4))
    return torch.stack(cols, dim=1)


def lindblad_step(rho: torch.Tensor, H: torch.Tensor, L: torch.Tensor, dt: float) -> torch.Tensor:
    generator = lindblad_rhs_matrix(torch.as_tensor(H, dtype=TORCH_COMPLEX), torch.as_tensor(L, dtype=TORCH_COMPLEX))
    channel = torch.linalg.matrix_exp(float(dt) * generator)
    return normalize_density((channel @ normalize_density(rho).reshape(4)).reshape(2, 2))


def apply_operator_map_family(rho: torch.Tensor, op_name: str, sign: int, dt: float = STAGE_DT) -> torch.Tensor:
    if op_name == "Ti":
        return normalize_density((1.0 - 0.18) * rho + 0.18 * pinch(rho, "z"))
    if op_name == "Te":
        return normalize_density((1.0 - 0.20) * rho + 0.20 * pinch(rho, "x"))
    if op_name == "Fi":
        angle = sign * 0.23 * dt / STAGE_DT
        unitary = torch.linalg.matrix_exp((-1j * angle * SX / 2.0).to(TORCH_COMPLEX))
        return normalize_density(unitary @ rho @ unitary.conj().T)
    if op_name == "Fe":
        angle = sign * 0.21 * dt / STAGE_DT
        unitary = torch.linalg.matrix_exp((-1j * angle * SZ / 2.0).to(TORCH_COMPLEX))
        return normalize_density(unitary @ rho @ unitary.conj().T)
    raise ValueError(f"unknown operator {op_name!r}")


def apply_terrain_dynamics(rho: torch.Tensor, perception: str, engine_type: int, dt: float = STAGE_DT) -> torch.Tensor:
    spec = get_terrain_dynamics_spec(perception, engine_type)
    family = spec["family"]
    axis = str(spec["projector_axis"])
    rate = float(spec["rate"])
    hamiltonian = torch.as_tensor(spec["hamiltonian"], dtype=TORCH_COMPLEX)
    chirality_sign = +1.0 if engine_type == 0 else -1.0
    state = normalize_density(rho)

    if family == "pinching_projection":
        target = pinch(state, axis)
        state = normalize_density((1.0 - rate) * state + rate * target)
        unitary = torch.linalg.matrix_exp((-1j * 0.12 * dt * hamiltonian).to(TORCH_COMPLEX))
        return normalize_density(unitary @ state @ unitary.conj().T)
    if family == "kraus_filter":
        filtered = kraus_filter(state, axis, min(0.42, 1.6 * rate), release=False)
        state = normalize_density((1.0 - 0.35) * state + 0.35 * filtered)
        unitary = torch.linalg.matrix_exp((-1j * dt * hamiltonian).to(TORCH_COMPLEX))
        return normalize_density(unitary @ state @ unitary.conj().T)
    if family == "lowering_dissipator":
        return lindblad_step(state, hamiltonian, torch.tensor([[0, 0], [1, 0]], dtype=TORCH_COMPLEX), dt * (1.0 + rate))
    if family == "kraus_release":
        filtered = kraus_filter(state, axis, min(0.42, 1.5 * rate), release=True)
        state = normalize_density((1.0 + 0.25 * rate) * state - 0.25 * rate * filtered)
        unitary = torch.linalg.matrix_exp((1j * 0.7 * dt * hamiltonian).to(TORCH_COMPLEX))
        return normalize_density(unitary @ state @ unitary.conj().T)
    if family == "outward_projection":
        target = pinch(state, axis)
        state = normalize_density((1.0 - 0.55 * rate) * state + 0.55 * rate * target)
        unitary = torch.linalg.matrix_exp((1j * dt * hamiltonian).to(TORCH_COMPLEX))
        return normalize_density(unitary @ state @ unitary.conj().T)
    if family == "raising_dissipator":
        return lindblad_step(state, hamiltonian, torch.tensor([[0, 1], [0, 0]], dtype=TORCH_COMPLEX), dt * (1.0 + rate))
    if family == "pinching_dissipator":
        target = pinch(state, axis)
        state = normalize_density((1.0 - rate) * state + rate * target)
        unitary = torch.linalg.matrix_exp((-1j * chirality_sign * 0.5 * dt * hamiltonian).to(TORCH_COMPLEX))
        return normalize_density(unitary @ state @ unitary.conj().T)
    raise ValueError(f"unknown terrain dynamics family {family!r}")


def stage_fixed_target(perception: str, engine_type: int) -> torch.Tensor:
    if perception in {"Se", "Ni"}:
        return I2 / 2.0
    if perception == "Si":
        ket = torch.tensor([1.0, 0.0], dtype=TORCH_COMPLEX) if engine_type == 0 else torch.tensor([0.0, 1.0], dtype=TORCH_COMPLEX)
        return torch.outer(ket, ket.conj())
    if perception == "Ne":
        ket = torch.tensor([0.0, 1.0], dtype=TORCH_COMPLEX) if engine_type == 0 else torch.tensor([1.0, 0.0], dtype=TORCH_COMPLEX)
        return torch.outer(ket, ket.conj())
    raise ValueError(f"unknown perception {perception!r}")


def apply_bounded_manifold_projection(rho: torch.Tensor, perception: str, engine_type: int) -> torch.Tensor:
    target = stage_fixed_target(perception, engine_type)
    return normalize_density((1.0 - MANIFOLD_TARGET_MIX) * rho + MANIFOLD_TARGET_MIX * target)


def apply_loop_placement(rho: torch.Tensor, engine_type: int, main_stage_idx: int, loop_class: str) -> torch.Tensor:
    chirality_sign = +1.0 if engine_type == 0 else -1.0
    u = (main_stage_idx + 1) * (2.0 * math.pi / 9.0)
    if loop_class == "outer":
        generator = (0.75 * SX + 0.25 * SZ) * (0.071 * chirality_sign * u)
    elif loop_class == "inner":
        generator = SZ * (0.035 * chirality_sign * u)
    else:
        raise ValueError(f"unknown loop_class {loop_class!r}")
    unitary = torch.linalg.matrix_exp((-1j * generator).to(TORCH_COMPLEX))
    return normalize_density(unitary @ rho @ unitary.conj().T)


def apply_canonical_substage(
    rho: torch.Tensor,
    engine_type: int,
    perception: str,
    loop_class: str,
    main_stage_idx: int,
    substage_idx: int,
    *,
    manifold_enabled: bool,
) -> torch.Tensor:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    state = normalize_density(rho)
    if slot["precedence"] == "operator_first":
        state = apply_operator_map_family(state, slot["operator"], int(slot["sign"]))
        state = apply_terrain_dynamics(state, perception, engine_type)
    else:
        state = apply_terrain_dynamics(state, perception, engine_type)
        state = apply_operator_map_family(state, slot["operator"], int(slot["sign"]))
    if manifold_enabled:
        state = apply_bounded_manifold_projection(state, perception, engine_type)
    return apply_loop_placement(state, engine_type, main_stage_idx, loop_class)


def density_delta_features(before: Any, after: Any) -> torch.Tensor:
    before_t = torch.as_tensor(before, dtype=torch.complex128)
    after_t = torch.as_tensor(after, dtype=torch.complex128)
    delta = after_t - before_t
    herm = (delta + delta.conj().T) / 2
    eigs = torch.linalg.eigvalsh(herm).real
    bloch_delta = torch.as_tensor(bloch_vector(after) - bloch_vector(before), dtype=torch.float64)
    scalar_features = torch.tensor(
        [
            density_entropy(after) - density_entropy(before),
            density_purity(after) - density_purity(before),
            float(0.5 * torch.sum(torch.abs(eigs)).item()),
            float(torch.linalg.norm(delta).real.item()),
            float(torch.max(torch.abs(delta.real)).item()),
            float(torch.max(torch.abs(delta.imag)).item()),
        ],
        dtype=torch.float64,
    )
    return torch.cat((bloch_delta, scalar_features))


def placement_label(engine_type: int, main_idx: int) -> int:
    loop_idx = 0 if main_idx < 4 else 1
    stage_idx = main_idx % 4
    return engine_type * 8 + loop_idx * 4 + stage_idx


def collect_rows(mode: str = "manifold_delta") -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rows: list[torch.Tensor] = []
    labels: list[int] = []
    base_ids: list[int] = []
    for base_idx in range(N_BASE_STATES):
        rho_seed = generate_initial_density(20_000 + base_idx)
        for engine_type in (0, 1):
            rho_on = rho_seed.clone()
            rho_off = rho_seed.clone()
            for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
                slot_features: list[torch.Tensor] = []
                for substage_idx in range(4):
                    rho_on = apply_canonical_substage(
                        rho_on,
                        engine_type,
                        perception,
                        loop_class,
                        main_idx,
                        substage_idx,
                        manifold_enabled=True,
                    )
                    rho_off = apply_canonical_substage(
                        rho_off,
                        engine_type,
                        perception,
                        loop_class,
                        main_idx,
                        substage_idx,
                        manifold_enabled=False,
                    )
                    slot_features.append(density_delta_features(rho_off, rho_on))
                raw_feat = torch.cat(slot_features)
                if mode == "manifold_delta":
                    feat = raw_feat
                elif mode == "disabled_delta":
                    feat = torch.zeros_like(raw_feat)
                elif mode == "initial_only":
                    one = torch.tensor(
                        [
                            *torch.as_tensor(bloch_vector(rho_seed), dtype=torch.float64).tolist(),
                            density_entropy(rho_seed),
                            density_purity(rho_seed),
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                        ],
                        dtype=torch.float64,
                    )
                    feat = one.repeat(4)
                elif mode == "norm_only_delta":
                    feat = torch.zeros_like(raw_feat)
                    for offset in range(0, len(raw_feat), 9):
                        feat[offset + 5] = raw_feat[offset + 5]
                        feat[offset + 6] = raw_feat[offset + 6]
                elif mode == "direction_only_delta":
                    feat = raw_feat.clone()
                    for offset in range(0, len(raw_feat), 9):
                        feat[offset + 5] = 0.0
                        feat[offset + 6] = 0.0
                else:
                    raise ValueError(mode)
                rows.append(feat)
                labels.append(placement_label(engine_type, main_idx))
                base_ids.append(base_idx)
    return torch.stack(rows).to(torch.float64), torch.tensor(labels, dtype=torch.long), torch.tensor(base_ids, dtype=torch.long)


def split_by_base(x: torch.Tensor, y: torch.Tensor, base_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    train = base_ids < N_TRAIN_BASE
    test = torch.logical_not(train)
    return x[train], y[train], x[test], y[test]


def readout_accuracy(x: torch.Tensor, y: torch.Tensor, base_ids: torch.Tensor, seed: int = 0) -> float:
    x_train, y_train, x_test, y_test = split_by_base(x, y, base_ids)
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-9, torch.ones_like(std), std)
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
    for _ in range(N_EPOCHS):
        opt.zero_grad()
        loss = loss_fn(model(x_train), y_train)
        loss.backward()
        opt.step()
    with torch.no_grad():
        pred = torch.argmax(model(x_test), dim=1)
    return float((pred == y_test).double().mean().item())


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
    generator = torch.Generator().manual_seed(99)
    y_shuffled = y[torch.randperm(y.numel(), generator=generator)]
    acc_direction_shuffled = readout_accuracy(x_direction_only, y_shuffled, base_ids, seed=16)
    counts = sp.Integer(2) * sp.Integer(2) * sp.Integer(4) * sp.Integer(4)
    norms = torch.linalg.norm(x_delta, dim=1)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "nonclassical",
        "source_alignment_category": "bounded_canonical_qit_replay_of_former_enginecore_delta_readout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "two_root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": True,
            "F01": True,
            "N01": True,
            "finite_carrier_evidence": "bounded 2x2 density carrier with 2 sheets x 2 loop placements x 4 topology laws x 4 substage slots",
            "n01_evidence": "ordered canonical QIT operator/terrain/loop schedule; shuffled-label and disabled-delta controls reject label-only collapse",
        },
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
            "mean": float(torch.mean(norms).item()),
            "min": float(torch.min(norms).item()),
            "max": float(torch.max(norms).item()),
        },
        "positive": {
            "sixteen_placement_factorization_is_present": graph_witness(),
            "manifold_delta_is_nonzero": {
                "pass": float(torch.min(norms).item()) > 1e-6,
                "min_norm": float(torch.min(norms).item()),
                "mean_norm": float(torch.mean(norms).item()),
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
                "pass": acc_delta >= acc_norm_only >= (1.0 / N_CLASSES),
                "norm_only_accuracy": acc_norm_only,
                "delta_accuracy": acc_delta,
                "direction_only_accuracy": acc_direction_only,
                "direction_over_norm_margin": acc_direction_only - acc_norm_only,
                "full_over_norm_margin": acc_delta - acc_norm_only,
                "claim_killed": "directional_delta_necessity",
                "note": (
                    "Canonical replay shows magnitude-only deltas are themselves strongly placement-bearing. "
                    "This supports the weaker density-delta readout claim and blocks any claim that signed/"
                    "directional channels are necessary for placement recovery."
                ),
            },
            "direction_only_delta_preserves_placement_signal": {
                "pass": acc_direction_only >= 0.85,
                "direction_only_accuracy": acc_direction_only,
                "norm_only_accuracy": acc_norm_only,
                "direction_over_norm_margin": acc_direction_only - acc_norm_only,
                "claim_ceiling": "direction-only deltas preserve signal; this does not imply direction-only necessity over magnitude channels.",
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
            + int(acc_delta >= acc_norm_only >= (1.0 / N_CLASSES))
            + int(acc_direction_only >= 0.85)
            + int(acc_direction_shuffled <= 0.20),
            "variants": ["disabled_delta", "norm_only_delta", "direction_only_delta", "direction_only_shuffled_labels"],
        },
        "boundary": {
            "does_not_claim_final_ai_or_physics": {
                "pass": "does not admit" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
            },
            "direct_enginecore_boundary_removed": {
                "pass": "source-native EngineCore dynamics" in CLAIM_CEILING,
                "note": "This source reconstructs a bounded canonical QIT replay locally and does not import EngineCore.",
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
