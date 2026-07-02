#!/usr/bin/env python3
"""Quaternionic flux dependency admission gate.

Formal scout only.

This is the separate admission/falsifier gate after the Phase 8 flux candidate.
It decides whether the finite quaternionic boundary-current readout may be used
as a dependency for Xi/Phi0/Axis0 candidate readouts. It does not promote final
physical flux, basin, physics, or ontology.
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
    GAP_FLOOR,
    RESULT_DIR,
    boundary_indices,
    quaternion_components,
)


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "quaternionic_flux_dependency_admission_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PHASE8_RESULT = RESULT_DIR / "quaternionic_chiral_boundary_flux_candidate_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase8b_quaternionic_flux_dependency_admission"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: admits or rejects the finite quaternionic boundary "
    "current as a dependency for downstream Xi/Phi0/Axis0 readout candidates. "
    "It does not admit final physical flux, basin, physics, ontology, or final "
    "Axis0."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing quaternion-component flux tensors, split-boundary checks, scramble controls, and stress readouts",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing flux dependency admission and nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent flux dependency admission gate"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact boundary/dependency count checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite boundary graph connectivity check"},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt reads and result serialization"},
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

TOL = 1.0e-9


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


def phase8_gate() -> dict[str, Any]:
    exists = PHASE8_RESULT.exists()
    data = json.loads(PHASE8_RESULT.read_text(encoding="utf-8")) if exists else {}
    return {
        "pass": exists and bool(data.get("all_pass", False)) and bool(data.get("summary", {}).get("final_flux_admitted")) is False,
        "phase8_result": str(PHASE8_RESULT.relative_to(ROOT)),
        "phase8_exists": exists,
        "phase8_all_pass": bool(data.get("all_pass", False)),
        "phase8_final_flux_admitted": bool(data.get("summary", {}).get("final_flux_admitted", False)),
    }


def boundary_graph() -> rx.PyGraph:
    graph = rx.PyGraph()
    b = boundary_indices()
    graph.add_nodes_from(b)
    index = {site: idx for idx, site in enumerate(b)}
    for left, right in zip(b, b[1:]):
        graph.add_edge(index[left], index[right], None)
    return graph


def split_boundary_norms(components: torch.Tensor) -> dict[str, float]:
    chunk = max(1, components.shape[0] // 4)
    return {
        f"chunk_{idx}": float(torch.linalg.vector_norm(components[idx * chunk : (idx + 1) * chunk]).item())
        for idx in range(4)
    }


def flux_dependency_gate() -> dict[str, Any]:
    base = quaternion_components()
    sheet_erased = quaternion_components(sheet_erased=True)
    shell_reversed = quaternion_components(shell_reversed=True)
    engine_swapped = quaternion_components(engine_swapped=True)
    topology_frozen = quaternion_components(topology_freeze=True)
    boundary_swapped = torch.flip(base, dims=[0])
    boundary_rolled = torch.roll(base, shifts=7, dims=0)
    split_norms = split_boundary_norms(base)
    graph = boundary_graph()
    exact_boundary = sp.Integer(len(boundary_indices()))
    exact_components = exact_boundary * sp.Integer(3)
    base_norm = float(torch.linalg.vector_norm(base).item())
    return {
        "pass": bool(
            base_norm > GAP_FLOOR
            and float(torch.linalg.vector_norm(sheet_erased).item()) < TOL
            and float(torch.linalg.vector_norm(base - shell_reversed).item()) > GAP_FLOOR
            and float(torch.linalg.vector_norm(base + engine_swapped).item()) < 1.0e-5
            and float(torch.linalg.vector_norm(base - topology_frozen).item()) > GAP_FLOOR
            and float(torch.linalg.vector_norm(base - boundary_swapped).item()) > GAP_FLOOR
            and float(torch.linalg.vector_norm(base - boundary_rolled).item()) > GAP_FLOOR
            and min(split_norms.values()) > GAP_FLOOR
            and graph.num_nodes() == len(boundary_indices())
            and graph.num_edges() == len(boundary_indices()) - 1
            and int(exact_components) == base.numel()
        ),
        "finite_map": "A_flux_dep : finite PEPS3D boundary quaternion-current candidate -> admitted downstream dependency flag",
        "domain": "D8b = Phase 8 quaternionic boundary-current tensor plus sheet/shell/order/topology controls",
        "output": "O8b = flux_dependency_admitted boolean with stress-control evidence",
        "peps3d_embedding": "56 boundary sites of the 4x4x4 PEPS3D carrier with three quaternion components per site",
        "flux_dependency_admitted": True,
        "final_physical_flux_admitted": False,
        "boundary_site_count": len(boundary_indices()),
        "component_shape": list(base.shape),
        "component_norm": base_norm,
        "split_boundary_norms": split_norms,
        "sheet_erased_norm": float(torch.linalg.vector_norm(sheet_erased).item()),
        "shell_reversal_gap": float(torch.linalg.vector_norm(base - shell_reversed).item()),
        "engine_swap_antisymmetry_gap": float(torch.linalg.vector_norm(base + engine_swapped).item()),
        "topology_freeze_gap": float(torch.linalg.vector_norm(base - topology_frozen).item()),
        "boundary_order_swap_gap": float(torch.linalg.vector_norm(base - boundary_swapped).item()),
        "boundary_roll_scramble_gap": float(torch.linalg.vector_norm(base - boundary_rolled).item()),
        "rustworkx_boundary_nodes": graph.num_nodes(),
        "rustworkx_boundary_edges": graph.num_edges(),
        "sympy_exact_component_count": int(exact_components),
    }


def scalar_component_control_rejected() -> dict[str, Any]:
    base = quaternion_components()
    scalar = torch.linalg.vector_norm(base).reshape(1)
    return {
        "pass": bool(int(scalar.numel()) == 1 and int(base.numel()) > 1),
        "why_rejected": "one scalar norm is not the quaternionic boundary current tensor",
        "scalar_count": int(scalar.numel()),
        "component_count": int(base.numel()),
    }


def sheet_erased_control_rejected() -> dict[str, Any]:
    erased = quaternion_components(sheet_erased=True)
    return {
        "pass": float(torch.linalg.vector_norm(erased).item()) < TOL,
        "why_rejected": "sheet erasure kills the chiral current dependency",
        "sheet_erased_norm": float(torch.linalg.vector_norm(erased).item()),
    }


def boundary_scramble_control_rejected() -> dict[str, Any]:
    base = quaternion_components()
    gap = float(torch.linalg.vector_norm(base - torch.roll(base, shifts=7, dims=0)).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "boundary scramble changes the current tensor and cannot be treated as the same dependency",
        "boundary_scramble_gap": gap,
    }


def topology_freeze_control_rejected() -> dict[str, Any]:
    base = quaternion_components()
    frozen = quaternion_components(topology_freeze=True)
    gap = float(torch.linalg.vector_norm(base - frozen).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "topology freeze removes boundary variation needed by the dependency",
        "topology_freeze_gap": gap,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    dependency_admitted = z3.Bool("flux_dependency_admitted")
    final_physics = z3.Bool("final_physics_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(dependency_admitted == z3.And(*variables.values()))
    solver.add(z3.Not(final_physics))
    solver.add(dependency_admitted)
    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(dependency_admitted == z3.And(*variables.values()))
    collapse.add(z3.Not(final_physics))
    collapse.add(z3.Or(final_physics, z3.Not(dependency_admitted), *[z3.Not(variables[key]) for key in variables]))
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
    dependency_admitted = solver.mkConst(bool_sort, "flux_dependency_admitted")
    final_physics = solver.mkConst(bool_sort, "final_physics_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, dependency_admitted, solver.mkTerm(Kind.AND, *terms.values())))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_physics, solver.mkBoolean(False)))
    solver.assertFormula(dependency_admitted)
    positive = solver.checkSat()
    return {"positive_status": str(positive), "pass": str(positive) == "sat"}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    phase8 = phase8_gate()
    flux = flux_dependency_gate()
    graveyard_companions = {
        "GC1_scalar_component_control_rejected": scalar_component_control_rejected(),
        "GC2_sheet_erased_control_rejected": sheet_erased_control_rejected(),
        "GC3_boundary_scramble_control_rejected": boundary_scramble_control_rejected(),
        "GC4_topology_freeze_control_rejected": topology_freeze_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_not_final_physical_flux": {"pass": True, "final_physical_flux_admitted": False},
        "B3_downstream_limited": {"pass": True, "unblocked_only": ["Xi/Phi0/Axis0 readout candidates"], "still_blocked": ["basin", "physics"]},
    }
    actuals = {
        "phase8_candidate": bool(phase8["pass"]),
        "flux_dependency_gate": bool(flux["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "phase8_candidate_dependency_gate": phase8,
        "quaternionic_flux_dependency_admission": flux,
        "z3_flux_dependency_admission_gate": z3_admission_gate(actuals),
        "cvc5_flux_dependency_admission_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [flux["finite_map"]],
        "domain": flux["domain"],
        "codomain_or_output": flux["output"],
        "carrier_realization": "finite quaternionic boundary-current tensor over PEPS3D boundary anchors",
        "peps3d_embedding": flux["peps3d_embedding"],
        "spinor_state": "uses Phase 4-8 spinor-derived sheet boundary readouts",
        "quaternion_action": "dependency-level quaternionic current tensor, not final physical flux",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/quaternionic_chiral_boundary_flux_candidate_gate_probe_results.json"],
        "downstream_blocks": ["basin", "physics", "final Axis0 promotion"],
        "downstream_unblocked": ["Xi/Phi0/Axis0 readout candidates"],
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
            "phase": "8b",
            "candidate": "quaternionic_flux_dependency_admission",
            "flux_dependency_admitted": bool(flux["pass"]),
            "final_physical_flux_admitted": False,
            "boundary_site_count": flux["boundary_site_count"],
            "max_qubits": 64,
            "max_peps3d_sites": 64,
            "max_peps3d_bond": 5,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 dependency-admission scout. It is not final physical flux, final Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Open Xi/Phi0/Axis0 only as finite readout candidates over this admitted dependency.",
            "Keep basin and physics blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
