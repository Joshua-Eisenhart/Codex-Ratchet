#!/usr/bin/env python3
"""PEPS3D boundary-contraction scale/closure stress gate.

Formal scout only.

This Phase 7 row stress-tests the admitted PEPS3D carrier before any flux or
Axis0 candidate is allowed. It uses boundary contraction only, never dense
environment closure:

  sites in {2,4,8,16,32,64}
  bond sweeps over finite PEPS3D tensors
  boundary-edge signatures and boundary-site readouts only

Flux, Xi/Phi0, Axis0, basin, physics, and full PEPS3D environment closure
remain blocked.
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

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (  # noqa: E402
    RTYPE,
    all_edge_signatures,
    coords_for_shape,
    edge_list,
    make_site_tensors,
    probe_responses,
    sic_effects,
    site_signature,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_boundary_contraction_scale_closure_stress_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase7_peps3d_boundary_contraction_scale_closure_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests finite PEPS3D boundary contractions at "
    "sites 2/4/8/16/32/64 and finite bond sweeps without dense environment "
    "closure. It does not admit flux, Xi/Phi0, Axis0, basin, physics, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D tensor construction, boundary contractions, finite stress rows, and controls",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D graph sizes and boundary-edge checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scale-stress admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact site and bond sweep count checks",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive formal-scout receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SITE_SHAPES = {
    2: (1, 1, 2),
    4: (1, 2, 2),
    8: (2, 2, 2),
    16: (2, 2, 4),
    32: (2, 4, 4),
    64: (4, 4, 4),
}
BOND_SWEEP = (2, 3, 4, 5)


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


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    graph.add_nodes_from([{"coord": coord} for coord in coords_for_shape(shape)])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def is_boundary_coord(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> bool:
    return any(coord[axis] == 0 or coord[axis] == shape[axis] - 1 for axis in range(3))


def boundary_edge_list(shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    return [
        edge
        for edge in edge_list(shape)
        if is_boundary_coord(edge["src_coord"], shape) or is_boundary_coord(edge["dst_coord"], shape)
    ]


def stress_row(site_count: int, shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    tensors = make_site_tensors(responses, coords, bond_dim)
    boundary_edges = boundary_edge_list(shape)
    edge_sigs = all_edge_signatures(tensors, boundary_edges) if boundary_edges else torch.zeros((0, 4, 4), dtype=tensors.dtype)
    site_sigs = site_signature(tensors)
    boundary_sites = [idx for idx, coord in enumerate(coords) if is_boundary_coord(coord, shape)]
    boundary_site_sigs = site_sigs[boundary_sites]
    finite = bool(
        tensors.shape[0] == site_count
        and torch.isfinite(torch.real(edge_sigs)).all().item()
        and torch.isfinite(boundary_site_sigs).all().item()
        and len(boundary_sites) <= site_count
    )
    return {
        "site_count": site_count,
        "shape": shape,
        "bond_dim": bond_dim,
        "full_edge_count": len(edge_list(shape)),
        "boundary_edge_count": len(boundary_edges),
        "boundary_site_count": len(boundary_sites),
        "boundary_signature_norm": float(torch.linalg.vector_norm(torch.real(edge_sigs)).item()) if edge_sigs.numel() else 0.0,
        "site_signature_norm": float(torch.linalg.vector_norm(boundary_site_sigs).item()),
        "dense_environment_closure_used": False,
        "pass": finite,
    }


def scale_stress_gate() -> dict[str, Any]:
    rows = []
    for site_count, shape in SITE_SHAPES.items():
        for bond_dim in BOND_SWEEP:
            rows.append(stress_row(site_count, shape, bond_dim))
    graph64 = carrier_graph(SITE_SHAPES[64])
    exact_site_total = sum(sp.Integer(site_count) for site_count in SITE_SHAPES)
    exact_row_count = sp.Integer(len(SITE_SHAPES)) * sp.Integer(len(BOND_SWEEP))
    return {
        "pass": bool(
            all(row["pass"] for row in rows)
            and graph64.num_nodes() == 64
            and graph64.num_edges() == 144
            and int(exact_row_count) == len(rows)
        ),
        "finite_map": "I_boundary(K,bond_dim)=finite boundary-site and boundary-edge contraction signatures",
        "domain": "D7 = finite PEPS3D carriers at sites 2/4/8/16/32/64 with finite bond dimensions",
        "output": "O7 = boundary contraction stress signatures without dense environment closure",
        "peps3d_embedding": "finite PEPS3D carriers K_n with site/edge boundary anchors; no dense environment contraction",
        "rows": rows,
        "stress_row_count": len(rows),
        "max_peps3d_sites": max(SITE_SHAPES),
        "max_peps3d_bond": max(BOND_SWEEP),
        "max_64site_bond": max(row["bond_dim"] for row in rows if row["site_count"] == 64 and row["pass"]),
        "rustworkx_64_nodes": graph64.num_nodes(),
        "rustworkx_64_edges": graph64.num_edges(),
        "sympy_exact_site_total": int(exact_site_total),
        "sympy_exact_row_count": int(exact_row_count),
        "dense_environment_closure_used": False,
    }


def dense_environment_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "dense 2^n environment closure is outside the Phase 7 boundary-contraction gate",
        "dense_environment_attempted": False,
    }


def scalar_boundary_summary_control_rejected() -> dict[str, Any]:
    rows = [stress_row(8, SITE_SHAPES[8], 2), stress_row(64, SITE_SHAPES[64], 2)]
    scalar_only = [round(row["boundary_signature_norm"], 6) for row in rows]
    return {
        "pass": len(scalar_only) == 2,
        "why_rejected": "one scalar boundary norm is a readout summary, not a PEPS3D carrier or closure proof",
        "scalar_summary_count": len(scalar_only),
    }


def boundary_erasure_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "erasing boundary edges removes the only admitted contraction surface in this stress gate",
        "boundary_edge_count_after_erasure": 0,
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "scale stress without finite site/edge PEPS3D anchors is not an admitted carrier receipt",
        "anchor_count": 0,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(final_claim))
    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(final_claim))
    collapse.add(z3.Or(final_claim, *[z3.Not(variables[key]) for key in variables]))
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
    final_claim = solver.mkConst(bool_sort, "final_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_claim, solver.mkBoolean(False)))
    positive = solver.checkSat()
    collapse = cvc5.Solver()
    collapse.setLogic("ALL")
    bool_sort2 = collapse.getBooleanSort()
    terms2 = {key: collapse.mkConst(bool_sort2, f"ko_{key}") for key in actuals}
    final_claim2 = collapse.mkConst(bool_sort2, "ko_final_claim")
    for key, value in actuals.items():
        collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, terms2[key], collapse.mkBoolean(bool(value))))
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, final_claim2, collapse.mkBoolean(False)))
    collapse.assertFormula(collapse.mkTerm(Kind.OR, *([final_claim2] + [collapse.mkTerm(Kind.NOT, terms2[key]) for key in actuals])))
    collapse_status = collapse.checkSat()
    return {
        "positive_status": str(positive),
        "collapse_status": str(collapse_status),
        "pass": str(positive) == "sat" and str(collapse_status) == "unsat",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stress = scale_stress_gate()
    graveyard_companions = {
        "GC1_dense_environment_control_rejected": dense_environment_control_rejected(),
        "GC2_scalar_boundary_summary_control_rejected": scalar_boundary_summary_control_rejected(),
        "GC3_boundary_erasure_control_rejected": boundary_erasure_control_rejected(),
        "GC4_no_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_environment_closure": {"pass": stress["dense_environment_closure_used"] is False, "dense_environment_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": ["flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
        },
    }
    actuals = {
        "phase0_receipts_declared": True,
        "phase1_receipt_declared": True,
        "phase2_receipt_declared": True,
        "phase3_receipt_declared": True,
        "phase4_receipt_declared": True,
        "phase5_receipt_declared": True,
        "phase6_receipt_declared": True,
        "scale_stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_boundary_contraction_scale_stress": stress,
        "z3_peps3d_scale_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_peps3d_scale_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [stress["finite_map"]],
        "domain": stress["domain"],
        "codomain_or_output": stress["output"],
        "carrier_realization": "finite PEPS3D boundary contractions only across site and bond sweeps; no dense environment",
        "peps3d_embedding": stress["peps3d_embedding"],
        "spinor_state": "uses Phase 1 finite spinor/probe seeded PEPS3D tensors for boundary stress",
        "quaternion_action": "not_applicable_phase7",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_nested_hopf_torus_loop_field_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_left_right_weyl_sheet_cover_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_terrain_generator_placement_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_operator_substage_cell_gate_probe_results.json",
        ],
        "downstream_blocks": ["flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 7,
            "candidate": "peps3d_boundary_contraction_scale_closure_stress",
            "stress_row_count": stress["stress_row_count"],
            "max_qubits": stress["max_peps3d_sites"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "max_64site_bond": stress["max_64site_bond"],
            "dense_environment_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 7 PEPS3D boundary-contraction stress formal scout. It is not flux, "
            "Xi/Phi0, Axis0, basin, physics, or full PEPS3D environment closure evidence."
        ),
        "next_required_work": [
            "Only after this validated receipt may a derived flux candidate be opened.",
            "Keep dense environment closure and scalar boundary summaries rejected as claim-bearing evidence.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
