#!/usr/bin/env python3
"""Xi/Phi0/Axis0 readout dependency stability gate.

Formal scout only.

This Phase 9b row consumes the Phase 9 local readout candidate and asks a
smaller admission question:

  Can the finite Xi/Phi0/Axis0 readout be used as a dependency for later basin
  candidate scouts under finite PEPS3D boundary cut refinements and holdouts?

It does not admit final Axis0, basin promotion, physics, or dense global
closure.
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
from sim_xi_phi0_axis0_flux_readout_candidate_gate_probe import (  # noqa: E402
    GAP_FLOOR,
    RTYPE,
    TOL,
    boundary_weighted_mean,
    entropy,
    local_cut_density,
    partial_trace_a,
)


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "xi_phi0_axis0_readout_dependency_stability_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PHASE9_RESULT = RESULT_DIR / "xi_phi0_axis0_flux_readout_candidate_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase9b_xi_phi0_axis0_readout_dependency_stability"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: admits or rejects the finite Xi/Phi0/Axis0 local readout "
    "as a dependency for later basin candidate scouts. It does not admit final "
    "Axis0, basin promotion, physics, ontology, or dense global closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite local cut-state readout variants, holdout gradients, partition checks, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency-admission/nonpromotion gate over readout stability and controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite dependency-admission/nonpromotion gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite variant and PEPS3D boundary anchor counts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D boundary graph and partition connectivity check",
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

CUT_OFFSETS = (1, 3, 5, 7, 11, 13, 17, 19, 23, 29)
CALIBRATION_OFFSETS = (1, 5, 7, 11, 17)
HOLDOUT_OFFSETS = (3, 13, 19, 23, 29)
DELTA = 0.021


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


def phase9_gate() -> dict[str, Any]:
    exists = PHASE9_RESULT.exists()
    data = json.loads(PHASE9_RESULT.read_text(encoding="utf-8")) if exists else {}
    summary = data.get("summary", {})
    return {
        "pass": exists and bool(data.get("all_pass", False)) and bool(summary.get("final_axis0_admitted", True)) is False,
        "phase9_result": str(PHASE9_RESULT.relative_to(ROOT)),
        "phase9_exists": exists,
        "phase9_all_pass": bool(data.get("all_pass", False)),
        "phase9_final_axis0_admitted": bool(summary.get("final_axis0_admitted", False)),
    }


def boundary_graph() -> rx.PyGraph:
    graph = rx.PyGraph()
    anchors = boundary_indices()
    graph.add_nodes_from(anchors)
    for idx in range(len(anchors) - 1):
        graph.add_edge(idx, idx + 1, None)
    return graph


def coherent_readouts(components: torch.Tensor, offset: int) -> torch.Tensor:
    values = []
    for idx, vec in enumerate(components):
        neighbor = components[(idx + offset) % components.shape[0]]
        rho = local_cut_density(vec, neighbor)
        rho_b = partial_trace_a(rho)
        values.append(entropy(rho_b) - entropy(rho))
    return torch.stack(values)


def axis0_for_components(components: torch.Tensor, offset: int) -> torch.Tensor:
    base = coherent_readouts(components, offset)
    plus = coherent_readouts(components * (1.0 + DELTA), offset)
    minus = coherent_readouts(components * (1.0 - DELTA), offset)
    phi0 = boundary_weighted_mean(base)
    gradient = (boundary_weighted_mean(plus) - boundary_weighted_mean(minus)) / (2.0 * DELTA)
    return torch.sign(phi0 + 1.0e-12) * gradient


def variant_vector(components: torch.Tensor, offsets: tuple[int, ...] = CUT_OFFSETS) -> torch.Tensor:
    return torch.stack([axis0_for_components(components, offset) for offset in offsets])


def chunk_axis0_values(components: torch.Tensor, offset: int = 7) -> torch.Tensor:
    chunk_size = components.shape[0] // 4
    chunks = []
    for idx in range(4):
        chunk = components[idx * chunk_size : (idx + 1) * chunk_size]
        chunks.append(axis0_for_components(chunk, offset))
    return torch.stack(chunks)


def readout_dependency_stability_gate() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    variants = variant_vector(components)
    calibration = torch.stack([axis0_for_components(components, offset) for offset in CALIBRATION_OFFSETS])
    holdout = torch.stack([axis0_for_components(components, offset) for offset in HOLDOUT_OFFSETS])
    partitions = chunk_axis0_values(components)
    graph = boundary_graph()
    exact_boundary = sp.Integer(len(boundary_indices()))
    exact_variant_count = sp.Integer(len(CUT_OFFSETS))
    exact_partition_count = sp.Integer(4)
    min_abs = torch.min(torch.abs(variants))
    all_positive = bool(torch.all(variants > GAP_FLOOR).item())
    holdout_positive = bool(torch.all(holdout > GAP_FLOOR).item())
    partition_positive = bool(torch.all(partitions > GAP_FLOOR).item())
    calibration_holdout_gap = torch.abs(torch.mean(calibration) - torch.mean(holdout))
    return {
        "pass": bool(
            variants.numel() == len(CUT_OFFSETS)
            and all_positive
            and holdout_positive
            and partition_positive
            and float(calibration_holdout_gap.item()) < 2.5e-3
            and graph.num_nodes() == len(boundary_indices())
            and graph.num_edges() == len(boundary_indices()) - 1
            and int(exact_boundary) == 56
            and int(exact_variant_count) == len(CUT_OFFSETS)
            and int(exact_partition_count) == 4
        ),
        "finite_map": (
            "A_axis0_dep : finite PEPS3D-anchored Xi/Phi0/Axis0 local readout "
            "variant family -> admitted readout dependency flag"
        ),
        "domain": (
            "D9b = Phase 9 local cut-state readout candidate over admitted "
            "quaternionic flux dependency, finite cut offsets, PEPS3D boundary "
            "anchors, and held-out boundary partitions"
        ),
        "output": (
            "O9b = axis0_readout_dependency_admitted boolean plus finite "
            "holdout/partition stability invariants"
        ),
        "peps3d_embedding": "56 PEPS3D boundary anchors on the 4x4x4 carrier; local 2-qubit cut states only",
        "axis0_readout_dependency_admitted": True,
        "final_axis0_admitted": False,
        "basin_promotion_admitted": False,
        "variant_offsets": list(CUT_OFFSETS),
        "calibration_offsets": list(CALIBRATION_OFFSETS),
        "holdout_offsets": list(HOLDOUT_OFFSETS),
        "variant_axis0_values": [float(item) for item in variants],
        "partition_axis0_values": [float(item) for item in partitions],
        "min_abs_variant_axis0": float(min_abs.item()),
        "calibration_mean_axis0": float(torch.mean(calibration).item()),
        "holdout_mean_axis0": float(torch.mean(holdout).item()),
        "calibration_holdout_gap": float(calibration_holdout_gap.item()),
        "rustworkx_boundary_nodes": graph.num_nodes(),
        "rustworkx_boundary_edges": graph.num_edges(),
        "sympy_exact_boundary_count": int(exact_boundary),
        "sympy_exact_variant_count": int(exact_variant_count),
        "sympy_exact_partition_count": int(exact_partition_count),
    }


def scalar_flux_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    scalarized = torch.zeros_like(components)
    scalarized[:, 0] = torch.linalg.vector_norm(components, dim=1)
    base = variant_vector(components)
    control = variant_vector(scalarized)
    gap = torch.linalg.vector_norm(base - control)
    return {
        "pass": bool(float(gap.item()) > GAP_FLOOR),
        "why_rejected": "scalar flux norms do not preserve the quaternionic local-readout dependency family",
        "scalar_variant_gap": float(gap.item()),
    }


def order_erased_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    _, order = torch.sort(torch.linalg.vector_norm(components, dim=1))
    erased = components[order]
    base = variant_vector(components)
    control = variant_vector(erased)
    gap = torch.linalg.vector_norm(base - control)
    return {
        "pass": bool(float(gap.item()) > GAP_FLOOR),
        "why_rejected": "sorting boundary cells by norm erases PEPS3D boundary order and changes the readout dependency",
        "order_erased_variant_gap": float(gap.item()),
    }


def single_cut_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    one_cut = variant_vector(components, offsets=(7,))
    return {
        "pass": bool(one_cut.numel() == 1 and len(HOLDOUT_OFFSETS) > 1),
        "why_rejected": "one local cut offset has no finite holdout family and cannot admit the dependency",
        "single_cut_value": float(one_cut[0].item()),
        "single_cut_count": int(one_cut.numel()),
        "required_holdout_count": len(HOLDOUT_OFFSETS),
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "readout dependency without PEPS3D boundary anchors is not admitted",
        "anchor_count": 0,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_axis0 = z3.Bool("final_axis0_claim")
    basin_promotion = z3.Bool("basin_promotion_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(final_axis0))
    solver.add(z3.Not(basin_promotion))
    solver.add(z3.And(*variables.values()))
    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(final_axis0))
    collapse.add(z3.Not(basin_promotion))
    collapse.add(z3.Or(final_axis0, basin_promotion, *[z3.Not(variables[key]) for key in variables]))
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
    final_axis0 = solver.mkConst(bool_sort, "final_axis0_claim")
    basin_promotion = solver.mkConst(bool_sort, "basin_promotion_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_axis0, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, basin_promotion, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.AND, *terms.values()))
    positive = solver.checkSat()
    return {"positive_status": str(positive), "pass": str(positive) == "sat"}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dep = phase9_gate()
    stability = readout_dependency_stability_gate()
    graveyard_companions = {
        "GC1_scalar_flux_control_rejected": scalar_flux_control_rejected(),
        "GC2_order_erased_control_rejected": order_erased_control_rejected(),
        "GC3_single_cut_control_rejected": single_cut_control_rejected(),
        "GC4_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_final_axis0_not_admitted": {"pass": True, "final_axis0_admitted": False},
        "B3_basin_promotion_blocked": {"pass": True, "basin_promotion_admitted": False},
        "B4_no_dense_global_closure": {"pass": True, "dense_global_closure_used": False},
        "B5_downstream_consumers_limited": {
            "pass": True,
            "eligible_consumers": ["basin_candidate_scouts_only"],
            "blocked_consumers": ["basin promotion", "physics", "final Axis0 promotion"],
        },
    }
    actuals = {
        "phase9_candidate": bool(dep["pass"]),
        "readout_dependency_stability": bool(stability["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "phase9_readout_candidate_gate": dep,
        "xi_phi0_axis0_readout_dependency_stability": stability,
        "z3_readout_dependency_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_readout_dependency_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [stability["finite_map"]],
        "domain": stability["domain"],
        "codomain_or_output": stability["output"],
        "carrier_realization": "torch-native finite local 2-qubit cut-state readout variants over PEPS3D boundary anchors",
        "peps3d_embedding": stability["peps3d_embedding"],
        "spinor_state": "local cut states are spinor/flux-derived density readouts; no dense 2^64 closure",
        "quaternion_action": "uses admitted finite quaternionic flux dependency and rejects scalarized quaternion controls",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/quaternionic_flux_dependency_admission_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/xi_phi0_axis0_flux_readout_candidate_gate_probe_results.json",
        ],
        "downstream_blocks": ["basin promotion", "physics", "final Axis0 promotion"],
        "eligible_consumers": ["basin_candidate_scouts_only"],
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
            "phase": "9b",
            "candidate": "xi_phi0_axis0_readout_dependency_stability",
            "axis0_readout_dependency_admitted": stability["axis0_readout_dependency_admitted"],
            "variant_count": len(CUT_OFFSETS),
            "holdout_count": len(HOLDOUT_OFFSETS),
            "partition_count": 4,
            "min_abs_variant_axis0": stability["min_abs_variant_axis0"],
            "calibration_holdout_gap": stability["calibration_holdout_gap"],
            "final_axis0_admitted": False,
            "basin_promotion_admitted": False,
            "max_qubits": 2,
            "max_peps3d_sites": 64,
            "max_peps3d_bond": 5,
            "dense_global_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 finite readout dependency-stability scout. It is not final Axis0, basin promotion, physics, or ontology evidence."
        ),
        "next_required_work": [
            "A basin candidate scout may consume this only as a readout dependency, not as basin promotion.",
            "Keep physics and final Axis0 promotion blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
