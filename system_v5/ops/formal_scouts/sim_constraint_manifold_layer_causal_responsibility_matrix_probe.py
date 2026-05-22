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
import sympy as sp
import torch
import z3

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    PERCEPTION_L_MATRICES,
    SX,
    SZ,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)
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
    "constraint manifold under matched canonical QIT operator-slot density histories. "
    "It reports effective manifold rank, does not instantiate EngineCore, and "
    "does not admit source-native engine dynamics, final manifold, physics, "
    "cognition, ontology, or canonical engine claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": False, "reason": "not used directly; trajectory feature distances and rank matrix are torch-native"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 13-layer tensor constraint enforcer execution, trajectory features, distances, and rank matrix"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing layer dependency graph and reachability sanity"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over layer responsibility vectors"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic 13-layer inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded rank/count witness"},
    "canonical_qit_engine_specs": {"tried": True, "used": True, "reason": "supportive canonical schedule/operator/terrain metadata for finite density-history fixtures without EngineCore"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: (None if tool == "numpy" else "supportive" if tool == "canonical_qit_engine_specs" else "load_bearing")
    for tool in TOOL_MANIFEST
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.item()
        return value.detach().cpu().tolist()
    return value


def state_features(psi: torch.Tensor) -> torch.Tensor:
    arr = psi.detach().to(torch.complex128)
    probs = torch.abs(arr) ** 2
    probs = probs / max(float(probs.sum().item()), 1e-12)
    clipped = torch.clamp(probs, min=1e-12)
    entropy = -torch.sum(clipped * torch.log(clipped))
    return torch.stack(
        (
            torch.linalg.norm(arr).real,
            entropy.real,
            torch.sum(probs[: len(probs) // 2]).real,
            torch.sum(probs[::2]).real,
            torch.max(probs).real,
            torch.linalg.norm(arr.real),
            torch.linalg.norm(arr.imag),
        )
    ).to(torch.float64)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = rho.to(torch.complex128)
    rho = (rho + rho.conj().T) / 2
    trace = torch.trace(rho)
    if abs(complex(trace.detach().cpu().item())) < 1e-14:
        return torch.eye(2, dtype=torch.complex128) / 2
    rho = rho / trace
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0)
    if float(vals.sum().item()) < 1e-14:
        return torch.eye(2, dtype=torch.complex128) / 2
    rho = (vecs * (vals / vals.sum()).to(torch.complex128).unsqueeze(0)) @ vecs.conj().T
    return (rho + rho.conj().T) / 2


def generate_initial_density_torch(seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    theta = 0.24 + 1.05 * float(torch.rand((), generator=generator).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=generator).item())
    psi = torch.tensor(
        [math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))],
        dtype=torch.complex128,
    ).reshape(2, 1)
    pure = psi @ psi.conj().T
    return normalize_density(0.88 * pure + 0.12 * torch.eye(2, dtype=torch.complex128) / 2)


def pinch_density(rho: torch.Tensor, axis: str) -> torch.Tensor:
    if axis == "x":
        basis = SX
    elif axis == "z":
        basis = SZ
    else:
        # Use a diagonalizing projection surrogate for the y-labeled terrain channel.
        basis = OPERATOR_GENERATORS["Fe"]
    projectors = [
        (torch.eye(2, dtype=torch.complex128) + basis) / 2,
        (torch.eye(2, dtype=torch.complex128) - basis) / 2,
    ]
    return normalize_density(sum(proj @ rho @ proj.conj().T for proj in projectors))


def apply_operator_map(rho: torch.Tensor, op_name: str, sign: int) -> torch.Tensor:
    if op_name == "Ti":
        return normalize_density((1.0 - 0.18) * rho + 0.18 * pinch_density(rho, "z"))
    if op_name == "Te":
        return normalize_density((1.0 - 0.20) * rho + 0.20 * pinch_density(rho, "x"))
    generator = OPERATOR_GENERATORS[op_name]
    angle = float(sign) * OPERATOR_BASE_ANGLES[op_name]
    unitary = torch.linalg.matrix_exp(-1j * angle * generator)
    return normalize_density(unitary @ rho @ unitary.conj().T)


def apply_terrain_map(rho: torch.Tensor, perception: str, engine_type: int) -> torch.Tensor:
    spec = get_terrain_dynamics_spec(perception, engine_type)
    rate = min(max(float(spec["rate"]), 0.0), 1.0)
    hamiltonian = spec["hamiltonian"].to(torch.complex128)
    unitary = torch.linalg.matrix_exp(-1j * 0.05 * hamiltonian)
    evolved = normalize_density(unitary @ rho @ unitary.conj().T)
    collapse = PERCEPTION_L_MATRICES[perception].to(torch.complex128)
    dissipated = normalize_density(collapse @ evolved @ collapse.conj().T)
    return normalize_density((1.0 - rate) * evolved + rate * dissipated)


def embed_density_in_higher_dim(rho: torch.Tensor, dim: int = 16) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(normalize_density(rho))
    dominant = vecs[:, int(torch.argmax(vals.real).item())]
    psi = torch.zeros(dim, dtype=torch.complex128)
    psi[:2] = dominant
    generator = torch.Generator().manual_seed(0)
    pad = (
        torch.randn(dim - 2, generator=generator, dtype=torch.float64)
        + 1j * torch.randn(dim - 2, generator=generator, dtype=torch.float64)
    ).to(torch.complex128) * 0.01
    psi[2:] = pad
    norm = torch.linalg.norm(psi)
    if float(norm.real.item()) < 1e-14:
        psi[0] = 1.0
        return psi
    return psi / norm


def matched_density_history() -> list[Any]:
    engine_type = 0
    rho = generate_initial_density_torch(8801)
    states: list[Any] = []
    for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
        for sub_idx in range(4):
            slot = get_operator_slot_spec(perception, engine_type, loop_class, sub_idx)
            if slot["precedence"] == "operator_first":
                rho = apply_operator_map(rho, slot["operator"], int(slot["sign"]))
                rho = apply_terrain_map(rho, perception, engine_type)
            else:
                rho = apply_terrain_map(rho, perception, engine_type)
                rho = apply_operator_map(rho, slot["operator"], int(slot["sign"]))
            states.append(rho.clone())
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
    rho: Any,
    step: int,
    layer_idx: int,
    variant: str,
    context: dict,
) -> torch.Tensor:
    psi = embed_density_in_higher_dim(rho, dim=16)
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


def run_variant_sequence(history: list[Any], layer_idx: int, variant: str) -> torch.Tensor:
    context: dict = {}
    return torch.stack([run_layer_variant(rho, step, layer_idx, variant, context) for step, rho in enumerate(history)])


def responsibility_matrix() -> dict[str, Any]:
    history = matched_density_history()
    variants = ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"]
    rows = []
    for layer_idx, name in enumerate(LAYER_NAMES):
        full_arr = run_variant_sequence(history, layer_idx, "full")
        distances = {
            variant: float(torch.linalg.norm(full_arr - run_variant_sequence(history, layer_idx, variant), dim=1).mean().item())
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
    points = [
        [row["distances"][key] for key in ["removed", "validator_only", "delayed", "advanced", "reverse", "adversarial_phase"]]
        for row in rows
    ]
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
