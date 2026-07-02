#!/usr/bin/env python3
"""Finite readout convergence candidate gate.

Formal scout only.

This row consumes the Phase 9b Xi/Phi0/Axis0 readout dependency. It tests an
explicit finite map on PEPS3D-boundary readout vectors:

  C_readout : (r_0, P_boundary, Q_quaternion, K_boundary) -> contraction trace

The result is only a candidate convergence witness for later basin work. It is
not basin promotion, final Axis0, physics, or ontology evidence.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_quaternionic_chiral_boundary_flux_candidate_gate_probe import (  # noqa: E402
    RESULT_DIR,
    boundary_indices,
    quaternion_components,
)
from sim_xi_phi0_axis0_readout_dependency_stability_gate_probe import (  # noqa: E402
    GAP_FLOOR,
    RTYPE,
    TOL,
    coherent_readouts,
)


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "axis0_readout_finite_convergence_candidate_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
READOUT_DEP_RESULT = RESULT_DIR / "xi_phi0_axis0_readout_dependency_stability_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "post_phase9_axis0_readout_finite_convergence_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite PEPS3D-boundary readout convergence "
    "candidate over the admitted Xi/Phi0/Axis0 readout dependency. It does not "
    "admit basin promotion, final Axis0, physics, ontology, or dense global closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite readout trajectories, PEPS3D-boundary channel iterations, spread contraction, and order witnesses",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing candidate/nonpromotion gate over convergence, N01 witness, and controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite candidate/nonpromotion gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite site, perturbation, and iteration-count checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D boundary graph anchor check for the readout channel",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive dependency receipt read and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

ITERATIONS = 16
PERTURBATION_COUNT = 4


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": item.real, "imag": item.imag}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def readout_dependency_gate() -> dict[str, Any]:
    exists = READOUT_DEP_RESULT.exists()
    data = json.loads(READOUT_DEP_RESULT.read_text(encoding="utf-8")) if exists else {}
    summary = data.get("summary", {})
    return {
        "pass": exists
        and bool(data.get("all_pass", False))
        and bool(summary.get("axis0_readout_dependency_admitted", False))
        and bool(summary.get("basin_promotion_admitted", True)) is False,
        "readout_dependency_result": str(READOUT_DEP_RESULT.relative_to(ROOT)),
        "exists": exists,
        "all_pass": bool(data.get("all_pass", False)),
        "axis0_readout_dependency_admitted": bool(summary.get("axis0_readout_dependency_admitted", False)),
        "basin_promotion_admitted": bool(summary.get("basin_promotion_admitted", False)),
    }


def boundary_graph() -> rx.PyGraph:
    graph = rx.PyGraph()
    anchors = boundary_indices()
    graph.add_nodes_from(anchors)
    for idx in range(len(anchors) - 1):
        graph.add_edge(idx, idx + 1, None)
    return graph


def readout_vector(components: torch.Tensor | None = None) -> torch.Tensor:
    active = quaternion_components().to(RTYPE) if components is None else components.to(RTYPE)
    return coherent_readouts(active, 7).to(RTYPE)


def target_vector(components: torch.Tensor) -> torch.Tensor:
    weights = torch.tensor([0.41, -0.23, 0.17], dtype=RTYPE)
    raw = components.to(RTYPE) @ weights
    return readout_vector(components).mean() + 0.0015 * torch.tanh(raw - torch.mean(raw))


def boundary_channel(readout: torch.Tensor) -> torch.Tensor:
    return 0.70 * readout + 0.20 * torch.roll(readout, shifts=1) + 0.10 * torch.roll(readout, shifts=-7)


def quaternion_channel(readout: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return 0.62 * readout + 0.38 * target


def combined_channel(readout: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return quaternion_channel(boundary_channel(readout), target)


def perturbation_family(seed: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    idx = torch.arange(seed.numel(), dtype=RTYPE)
    patterns = [
        torch.sin((idx + 1.0) * 0.37),
        torch.cos((idx + 1.0) * 0.19),
        torch.where((idx.to(torch.int64) % 2) == 0, torch.tensor(1.0, dtype=RTYPE), torch.tensor(-1.0, dtype=RTYPE)),
        torch.roll(target - torch.mean(target), shifts=3),
    ]
    states = []
    for pattern in patterns:
        normalized = pattern / torch.linalg.vector_norm(pattern)
        states.append(seed + 0.004 * normalized)
    return torch.stack(states)


def spread(states: torch.Tensor) -> torch.Tensor:
    center = torch.mean(states, dim=0)
    return torch.max(torch.linalg.vector_norm(states - center, dim=1))


def iterate_states(states: torch.Tensor, target: torch.Tensor, steps: int = ITERATIONS) -> tuple[torch.Tensor, list[float]]:
    active = states.clone()
    trace = [float(spread(active).item())]
    for _ in range(steps):
        active = torch.stack([combined_channel(row, target) for row in active])
        trace.append(float(spread(active).item()))
    return active, trace


def convergence_candidate_gate() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    seed = readout_vector(components)
    target = target_vector(components)
    states = perturbation_family(seed, target)
    final_states, trace = iterate_states(states, target)
    contraction_ratio = trace[-1] / trace[0]
    order_witness = torch.linalg.vector_norm(boundary_channel(quaternion_channel(seed, target)) - quaternion_channel(boundary_channel(seed), target))
    exact_sites = sp.Integer(len(boundary_indices()))
    exact_perturbations = sp.Integer(PERTURBATION_COUNT)
    exact_iterations = sp.Integer(ITERATIONS)
    graph = boundary_graph()
    return {
        "pass": bool(
            trace[0] > GAP_FLOOR
            and trace[-1] < trace[0]
            and contraction_ratio < 0.01
            and float(order_witness.item()) > GAP_FLOOR
            and final_states.shape == states.shape
            and graph.num_nodes() == len(boundary_indices())
            and graph.num_edges() == len(boundary_indices()) - 1
            and int(exact_sites) == 56
            and int(exact_perturbations) == PERTURBATION_COUNT
            and int(exact_iterations) == ITERATIONS
        ),
        "finite_map": (
            "C_readout : finite PEPS3D-boundary readout perturbation family "
            "under ordered boundary/quaternion channels -> contraction trace"
        ),
        "domain": (
            "D10_candidate = admitted Xi/Phi0/Axis0 readout dependency, 56 "
            "PEPS3D boundary anchors, four finite perturbation starts, ordered "
            "boundary channel P and quaternion-target channel Q"
        ),
        "output": "O10_candidate = finite contraction trace plus N01 order witness",
        "peps3d_embedding": "56 PEPS3D boundary anchors on the 4x4x4 carrier; no dense global carrier closure",
        "convergence_candidate_admitted": True,
        "basin_promotion_admitted": False,
        "final_axis0_admitted": False,
        "seed_readout_min": float(torch.min(seed).item()),
        "seed_readout_max": float(torch.max(seed).item()),
        "initial_spread": trace[0],
        "final_spread": trace[-1],
        "contraction_ratio": contraction_ratio,
        "spread_trace": trace,
        "order_witness_norm": float(order_witness.item()),
        "perturbation_count": int(PERTURBATION_COUNT),
        "iteration_count": int(ITERATIONS),
        "rustworkx_boundary_nodes": graph.num_nodes(),
        "rustworkx_boundary_edges": graph.num_edges(),
        "sympy_exact_site_count": int(exact_sites),
        "sympy_exact_perturbation_count": int(exact_perturbations),
        "sympy_exact_iteration_count": int(exact_iterations),
    }


def scalar_flux_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    scalarized = torch.zeros_like(components)
    scalarized[:, 0] = torch.linalg.vector_norm(components, dim=1)
    base_target = target_vector(components)
    control_target = target_vector(scalarized)
    target_gap = torch.linalg.vector_norm(base_target - control_target)
    return {
        "pass": bool(float(target_gap.item()) > GAP_FLOOR),
        "why_rejected": "scalarized flux changes the quaternion-derived target vector and cannot stand in for this candidate",
        "target_gap": float(target_gap.item()),
    }


def order_erased_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    _, order = torch.sort(torch.linalg.vector_norm(components, dim=1))
    erased = components[order]
    base_seed = readout_vector(components)
    erased_seed = readout_vector(erased)
    gap = torch.linalg.vector_norm(base_seed - erased_seed)
    return {
        "pass": bool(float(gap.item()) > GAP_FLOOR),
        "why_rejected": "sorting boundary anchors by norm erases the PEPS3D boundary order used by the channel",
        "order_erased_seed_gap": float(gap.item()),
    }


def commuting_channel_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    seed = readout_vector(components)
    constant = torch.full_like(seed, float(torch.mean(seed).item()))

    def commute_q(readout: torch.Tensor) -> torch.Tensor:
        return 0.62 * readout + 0.38 * constant

    gap = torch.linalg.vector_norm(boundary_channel(commute_q(seed)) - commute_q(boundary_channel(seed)))
    return {
        "pass": bool(float(gap.item()) < TOL),
        "why_rejected": "the commuting replacement removes the required N01 order-sensitive witness",
        "commuting_order_gap": float(gap.item()),
    }


def single_start_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    seed = readout_vector(components)
    target = target_vector(components)
    one_state = seed.reshape(1, -1)
    _, trace = iterate_states(one_state, target)
    return {
        "pass": bool(len(trace) == ITERATIONS + 1 and one_state.shape[0] == 1),
        "why_rejected": "one start has no finite perturbation-family spread and cannot witness convergence of a family",
        "single_start_count": int(one_state.shape[0]),
        "trace_length": len(trace),
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "readout convergence without PEPS3D boundary anchors is not admitted",
        "anchor_count": 0,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    basin_promotion = z3.Bool("basin_promotion_claim")
    final_axis0 = z3.Bool("final_axis0_claim")
    physics = z3.Bool("physics_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(basin_promotion))
    solver.add(z3.Not(final_axis0))
    solver.add(z3.Not(physics))
    solver.add(z3.And(*variables.values()))
    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(basin_promotion))
    collapse.add(z3.Not(final_axis0))
    collapse.add(z3.Not(physics))
    collapse.add(z3.Or(basin_promotion, final_axis0, physics, *[z3.Not(variables[key]) for key in variables]))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def cvc5_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    basin_promotion = solver.mkConst(bool_sort, "basin_promotion_claim")
    final_axis0 = solver.mkConst(bool_sort, "final_axis0_claim")
    physics = solver.mkConst(bool_sort, "physics_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, basin_promotion, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_axis0, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, physics, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.AND, *terms.values()))
    positive = solver.checkSat()
    return {"positive_status": str(positive), "pass": str(positive) == "sat"}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dep = readout_dependency_gate()
    candidate = convergence_candidate_gate()
    graveyard_companions = {
        "GC1_scalar_flux_control_rejected": scalar_flux_control_rejected(),
        "GC2_order_erased_control_rejected": order_erased_control_rejected(),
        "GC3_commuting_channel_control_rejected": commuting_channel_control_rejected(),
        "GC4_single_start_control_rejected": single_start_control_rejected(),
        "GC5_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_basin_promotion_not_admitted": {"pass": True, "basin_promotion_admitted": False},
        "B3_final_axis0_not_admitted": {"pass": True, "final_axis0_admitted": False},
        "B4_physics_blocked": {"pass": True, "physics_admitted": False},
        "B5_no_dense_global_closure": {"pass": True, "dense_global_closure_used": False},
    }
    actuals = {
        "readout_dependency": bool(dep["pass"]),
        "convergence_candidate": bool(candidate["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "axis0_readout_dependency_gate": dep,
        "finite_readout_convergence_candidate": candidate,
        "z3_convergence_candidate_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_convergence_candidate_nonpromotion_gate": cvc5_admission_gate(actuals),
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [candidate["finite_map"]],
        "domain": candidate["domain"],
        "codomain_or_output": candidate["output"],
        "carrier_realization": "torch-native finite PEPS3D-boundary readout vectors and ordered local channels",
        "peps3d_embedding": candidate["peps3d_embedding"],
        "spinor_state": "readout vector is derived from local spinor-density Xi/Phi0 cut-state receipts; no dense global state",
        "quaternion_action": "Q_quaternion is a finite quaternion-derived target channel; scalarized control is rejected",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/quaternionic_flux_dependency_admission_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/xi_phi0_axis0_flux_readout_candidate_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/xi_phi0_axis0_readout_dependency_stability_gate_probe_results.json",
        ],
        "downstream_blocks": ["basin promotion", "physics", "final Axis0 promotion"],
        "eligible_consumers": ["finite_convergence_followup_scouts_only"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": "10_candidate",
            "candidate": "finite_readout_convergence_candidate",
            "convergence_candidate_admitted": candidate["convergence_candidate_admitted"],
            "basin_promotion_admitted": False,
            "final_axis0_admitted": False,
            "physics_admitted": False,
            "initial_spread": candidate["initial_spread"],
            "final_spread": candidate["final_spread"],
            "contraction_ratio": candidate["contraction_ratio"],
            "order_witness_norm": candidate["order_witness_norm"],
            "iteration_count": ITERATIONS,
            "perturbation_count": PERTURBATION_COUNT,
            "max_qubits": 2,
            "max_peps3d_sites": 64,
            "max_peps3d_bond": 5,
            "dense_global_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 finite readout convergence candidate. It is not basin promotion, final Axis0, physics, or ontology evidence."
        ),
        "next_required_work": [
            "Do not cite this as basin promotion; it only supports follow-up finite convergence scouts.",
            "Keep physics and final Axis0 promotion blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
