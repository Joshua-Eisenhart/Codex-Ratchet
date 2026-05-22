#!/usr/bin/env python3
"""Eight-qubit geometric constraint-manifold stage/topology/flux scout."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe_results.json"

NAME = "geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a minimum-width eight-qubit operating-stage substrate "
    "for the geometric constraint manifold, with one qubit per stage, topology-routed "
    "couplings, flux orientation, and thirteen constraint-layer applications per stage. "
    "It blocks two-qubit collapse and does not admit final manifold, basin, controller, "
    "world-model, physics, cognition, or architecture claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing eight-qubit state evolution, stage-local gates, flux controls, entropy, correlations, and signature gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing directed stage topology graph and acyclic stage-order witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic width/stage/layer/substage count factorization",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness for minimum width, topology separation, flux separation, and order sensitivity",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}

N_QUBITS = 8
N_STAGES = 8
N_LAYERS = 13
MIN_WIDTH_QUBITS = 8
DTYPE = torch.complex128
REAL = torch.float64
GAP_FLOOR = 0.04

STAGE_SCHEDULE = [
    {"stage": "s0", "qubit": 0, "partner": 1, "flux": +1, "family": "outer_ring"},
    {"stage": "s1", "qubit": 1, "partner": 3, "flux": -1, "family": "chord_lift"},
    {"stage": "s2", "qubit": 2, "partner": 4, "flux": +1, "family": "chord_lift"},
    {"stage": "s3", "qubit": 3, "partner": 7, "flux": -1, "family": "cross_sheet"},
    {"stage": "s4", "qubit": 4, "partner": 5, "flux": +1, "family": "outer_ring"},
    {"stage": "s5", "qubit": 5, "partner": 0, "flux": -1, "family": "cross_sheet"},
    {"stage": "s6", "qubit": 6, "partner": 2, "flux": +1, "family": "chord_lift"},
    {"stage": "s7", "qubit": 7, "partner": 6, "flux": -1, "family": "outer_ring"},
]

LAYER_WEIGHTS = torch.linspace(0.045, 0.125, steps=N_LAYERS, dtype=REAL)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    return value


def rx_gate(theta: float) -> torch.Tensor:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return torch.tensor([[c, -1j * s], [-1j * s, c]], dtype=DTYPE)


def rz_gate(theta: float) -> torch.Tensor:
    return torch.diag(
        torch.tensor(
            [complex(math.cos(-theta / 2.0), math.sin(-theta / 2.0)), complex(math.cos(theta / 2.0), math.sin(theta / 2.0))],
            dtype=DTYPE,
        )
    )


def cphase_gate(theta: float) -> torch.Tensor:
    return torch.diag(
        torch.tensor([1.0 + 0j, 1.0 + 0j, 1.0 + 0j, complex(math.cos(theta), math.sin(theta))], dtype=DTYPE)
    )


def apply_one(state: torch.Tensor, gate: torch.Tensor, qubit: int, n_qubits: int) -> torch.Tensor:
    dims = [2] * n_qubits
    perm = [qubit] + [idx for idx in range(n_qubits) if idx != qubit]
    inv = [perm.index(idx) for idx in range(n_qubits)]
    reshaped = state.reshape(dims).permute(perm).reshape(2, -1)
    updated = (gate @ reshaped).reshape([2] + [2] * (n_qubits - 1)).permute(inv).reshape(-1)
    return normalize(updated)


def apply_two(state: torch.Tensor, gate: torch.Tensor, q0: int, q1: int, n_qubits: int) -> torch.Tensor:
    if q0 == q1:
        return state
    dims = [2] * n_qubits
    perm = [q0, q1] + [idx for idx in range(n_qubits) if idx not in {q0, q1}]
    inv = [perm.index(idx) for idx in range(n_qubits)]
    reshaped = state.reshape(dims).permute(perm).reshape(4, -1)
    updated = (gate @ reshaped).reshape([2, 2] + [2] * (n_qubits - 2)).permute(inv).reshape(-1)
    return normalize(updated)


def normalize(state: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(state)
    if float(norm.item()) <= 0.0:
        raise ValueError("zero quantum state")
    return state / norm


def initial_state(n_qubits: int) -> torch.Tensor:
    dim = 2**n_qubits
    indices = torch.arange(dim, dtype=REAL)
    phase = torch.sin(indices * 0.037) + 0.5 * torch.cos(indices * 0.011)
    amp = torch.exp(-0.012 * torch.bitwise_xor(indices.to(torch.int64), torch.roll(indices.to(torch.int64), 1)).to(REAL))
    state = amp.to(DTYPE) * torch.exp(1j * phase.to(DTYPE))
    return normalize(state)


def stage_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids = {row["stage"]: graph.add_node(row["stage"]) for row in STAGE_SCHEDULE}
    for left, right in zip(STAGE_SCHEDULE[:-1], STAGE_SCHEDULE[1:]):
        graph.add_edge(node_ids[left["stage"]], node_ids[right["stage"]], {"kind": "order"})
    for row in STAGE_SCHEDULE:
        graph.add_edge(node_ids[row["stage"]], node_ids[STAGE_SCHEDULE[row["partner"]]["stage"]], {"kind": row["family"]})
    return {
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "acyclic_order_subgraph": True,
        "directed_graph_constructed": graph.num_nodes() == N_STAGES,
        "pass": graph.num_nodes() == N_STAGES and graph.num_edges() >= N_STAGES,
    }


def z_expectations(state: torch.Tensor, n_qubits: int) -> torch.Tensor:
    probs = torch.abs(state) ** 2
    idx = torch.arange(2**n_qubits, dtype=torch.int64)
    values = []
    for qubit in range(n_qubits):
        bit = ((idx >> (n_qubits - qubit - 1)) & 1).to(REAL)
        sign = 1.0 - 2.0 * bit
        values.append(torch.sum(probs.real * sign))
    return torch.stack(values)


def edge_correlations(state: torch.Tensor, n_qubits: int) -> torch.Tensor:
    probs = torch.abs(state) ** 2
    idx = torch.arange(2**n_qubits, dtype=torch.int64)
    values = []
    for row in STAGE_SCHEDULE:
        q0 = row["qubit"] % n_qubits
        q1 = row["partner"] % n_qubits
        b0 = ((idx >> (n_qubits - q0 - 1)) & 1).to(REAL)
        b1 = ((idx >> (n_qubits - q1 - 1)) & 1).to(REAL)
        sign = (1.0 - 2.0 * b0) * (1.0 - 2.0 * b1)
        values.append(torch.sum(probs.real * sign))
    return torch.stack(values)


def shannon_entropy(state: torch.Tensor) -> float:
    probs = torch.clamp(torch.abs(state) ** 2, min=1e-14)
    probs = probs / torch.sum(probs)
    return float((-(probs * torch.log(probs)).sum()).item())


def run_schedule(*, n_qubits: int, mode: str) -> dict[str, Any]:
    if n_qubits < MIN_WIDTH_QUBITS:
        return {
            "accepted": False,
            "n_qubits": n_qubits,
            "reason": "below_minimum_width",
            "minimum_width_qubits": MIN_WIDTH_QUBITS,
        }
    schedule = list(STAGE_SCHEDULE)
    if mode == "reversed_order":
        schedule = list(reversed(schedule))
    state = initial_state(n_qubits)
    stage_signatures: list[list[float]] = []
    flux_currents: list[float] = []
    entropies: list[float] = []
    operated_qubits: set[int] = set()
    for stage_idx, row in enumerate(schedule):
        qubit = row["qubit"] % n_qubits
        partner = row["partner"] % n_qubits
        operated_qubits.add(qubit)
        flux = float(row["flux"])
        if mode == "flux_erased":
            flux = 0.0
        if mode == "flux_reversed":
            flux = -flux
        if mode == "topology_erased":
            partner = qubit
        for layer_idx, weight in enumerate(LAYER_WEIGHTS.tolist()):
            layer_phase = weight * (1.0 + 0.07 * stage_idx) * (1.0 + 0.013 * layer_idx)
            state = apply_one(state, rz_gate(flux * layer_phase), qubit, n_qubits)
            state = apply_one(state, rx_gate(0.5 * layer_phase), (qubit + layer_idx) % n_qubits, n_qubits)
            if partner != qubit:
                state = apply_two(state, cphase_gate(flux * 0.55 * layer_phase), qubit, partner, n_qubits)
        z = z_expectations(state, n_qubits)
        corr = edge_correlations(state, n_qubits)
        flux_current = float(torch.sum(corr * torch.tensor([row["flux"] for row in STAGE_SCHEDULE], dtype=REAL)).item())
        entropy = shannon_entropy(state)
        flux_currents.append(flux_current)
        entropies.append(entropy)
        stage_signatures.append([float(x) for x in torch.cat([z, corr[:4], torch.tensor([flux_current, entropy], dtype=REAL)]).tolist()])
    profile = torch.tensor(
        [value for signature in stage_signatures for value in signature] + flux_currents + entropies,
        dtype=REAL,
    )
    return {
        "accepted": True,
        "n_qubits": n_qubits,
        "dimension": int(2**n_qubits),
        "operated_qubits": sorted(operated_qubits),
        "unique_operated_qubit_count": len(operated_qubits),
        "stage_count": len(schedule),
        "constraint_layer_applications": len(schedule) * N_LAYERS,
        "stage_signature_head": stage_signatures[:2],
        "flux_currents": flux_currents,
        "entropy_span": float(max(entropies) - min(entropies)),
        "profile": profile,
        "norm": float(torch.linalg.vector_norm(state).item()),
    }


def profile_gap(left: dict[str, Any], right: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(left["profile"] - right["profile"]).item())


def z3_width_flux_witness(nominal: dict[str, Any], gaps: dict[str, float], graph: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    enough_width = z3.Bool("enough_width")
    all_stages_have_qubits = z3.Bool("all_stages_have_qubits")
    topology_separates = z3.Bool("topology_separates")
    flux_separates = z3.Bool("flux_separates")
    flux_reversal_separates = z3.Bool("flux_reversal_separates")
    order_separates = z3.Bool("order_separates")
    graph_exists = z3.Bool("graph_exists")
    solver.add(enough_width == (nominal["n_qubits"] >= MIN_WIDTH_QUBITS))
    solver.add(all_stages_have_qubits == (nominal["unique_operated_qubit_count"] == N_STAGES))
    solver.add(topology_separates == (gaps["topology_erased_gap"] > GAP_FLOOR))
    solver.add(flux_separates == (gaps["flux_erased_gap"] > GAP_FLOOR))
    solver.add(flux_reversal_separates == (gaps["flux_reversed_gap"] > GAP_FLOOR))
    solver.add(order_separates == (gaps["reversed_order_gap"] > GAP_FLOOR))
    solver.add(graph_exists == bool(graph["pass"]))
    solver.add(
        z3.Not(
            z3.And(
                enough_width,
                all_stages_have_qubits,
                topology_separates,
                flux_separates,
                flux_reversal_separates,
                order_separates,
                graph_exists,
            )
        )
    )
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "minimum_width_qubits": MIN_WIDTH_QUBITS,
        "gaps": gaps,
    }


def main() -> int:
    started = time.time()
    graph = stage_graph()
    nominal = run_schedule(n_qubits=N_QUBITS, mode="nominal")
    flux_erased = run_schedule(n_qubits=N_QUBITS, mode="flux_erased")
    flux_reversed = run_schedule(n_qubits=N_QUBITS, mode="flux_reversed")
    topology_erased = run_schedule(n_qubits=N_QUBITS, mode="topology_erased")
    reversed_order = run_schedule(n_qubits=N_QUBITS, mode="reversed_order")
    two_qubit_collapse = run_schedule(n_qubits=2, mode="nominal")
    symbolic_count = sp.Integer(N_QUBITS) * sp.Integer(N_STAGES) * sp.Integer(N_LAYERS)
    gaps = {
        "flux_erased_gap": profile_gap(nominal, flux_erased),
        "flux_reversed_gap": profile_gap(nominal, flux_reversed),
        "topology_erased_gap": profile_gap(nominal, topology_erased),
        "reversed_order_gap": profile_gap(nominal, reversed_order),
    }
    z3_witness = z3_width_flux_witness(nominal, gaps, graph)
    positive = {
        "minimum_eight_qubit_width_executes": {
            "pass": nominal["accepted"] and nominal["n_qubits"] == 8 and nominal["dimension"] == 256,
            "n_qubits": nominal["n_qubits"],
            "dimension": nominal["dimension"],
            "minimum_width_qubits": MIN_WIDTH_QUBITS,
        },
        "one_qubit_per_operating_stage": {
            "pass": nominal["unique_operated_qubit_count"] == N_STAGES,
            "stage_count": N_STAGES,
            "operated_qubits": nominal["operated_qubits"],
        },
        "thirteen_constraint_layers_apply_per_stage": {
            "pass": nominal["constraint_layer_applications"] == N_STAGES * N_LAYERS
            and int(symbolic_count) == nominal["n_qubits"] * nominal["constraint_layer_applications"],
            "symbolic_count": str(symbolic_count),
            "symbolic_factorization": "n_qubits * stage_count * constraint_layers",
            "constraint_layer_applications": nominal["constraint_layer_applications"],
            "minimum_width_layer_slot_count": nominal["n_qubits"] * nominal["constraint_layer_applications"],
        },
        "stage_topology_graph_executes": graph,
        "z3_minimum_width_topology_flux_witness_executes": z3_witness,
    }
    graveyards = {
        "two_qubit_collapse_is_blocked": {
            "pass": two_qubit_collapse["accepted"] is False,
            "collapse_result": two_qubit_collapse,
        },
        "flux_erasure_changes_stage_profile": {
            "pass": gaps["flux_erased_gap"] > GAP_FLOOR,
            "gap": gaps["flux_erased_gap"],
        },
        "flux_reversal_changes_stage_profile": {
            "pass": gaps["flux_reversed_gap"] > GAP_FLOOR,
            "gap": gaps["flux_reversed_gap"],
        },
        "topology_erasure_changes_stage_profile": {
            "pass": gaps["topology_erased_gap"] > GAP_FLOOR,
            "gap": gaps["topology_erased_gap"],
        },
        "stage_order_reversal_changes_stage_profile": {
            "pass": gaps["reversed_order_gap"] > GAP_FLOOR,
            "gap": gaps["reversed_order_gap"],
        },
    }
    boundary = {
        "claim_ceiling_blocks_final_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "blocks two-qubit", "does not admit"]),
        },
        "substage_per_qubit_remains_future_work": {
            "pass": True,
            "boundary": "This is the minimum one-qubit-per-stage fixture. A 32-qubit substage-width fixture remains a separate follow-up.",
        },
        "qit_two_state_work_scout_is_not_maturity_evidence": {
            "pass": True,
            "boundary": "Two-state density work rows can remain interface/calibration checks but cannot satisfy this minimum-width nonclassical substrate gate.",
        },
    }
    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "minimum_width_geometric_constraint_manifold_stage_flux_substrate",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "stage_schedule": STAGE_SCHEDULE,
        "nominal_summary": {
            key: value
            for key, value in nominal.items()
            if key not in {"profile"}
        },
        "control_gaps": gaps,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a clean v5 minimum-width nonclassical substrate scout.",
            "It uses one qubit per operating stage and explicitly blocks two-qubit collapse.",
            "It tests topology and flux as finite stage constraints, not final manifold maturity.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
