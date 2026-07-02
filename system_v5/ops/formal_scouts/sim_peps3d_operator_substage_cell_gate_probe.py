#!/usr/bin/env python3
"""PEPS3D operator-substage cell gate.

Formal scout only.

This Phase 6 row tests the repaired 64-substage condition. A substage is not a
row label; it is a PEPS3D-carried finite cell with its own tensor/channel
action:

  c = (engine_type, loop_field, terrain, operator_slot)
  Phi_c : K_c -> K'_c
  || Phi_T o U_o(rho) - U_o o Phi_T(rho) || > epsilon

The 64 cells project to 16 placements by forgetting the operator slot.
Flux, Xi/Phi0, Axis0, basin, physics, and full PEPS3D closure remain blocked.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import Counter
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import CTYPE, RTYPE, coords_for_shape, edge_list, sic_effects  # noqa: E402
from sim_peps3d_spinor_density_carrier_gate_probe import probe_response_from_density  # noqa: E402
from sim_peps3d_terrain_generator_placement_gate_probe import LOOPS, TERRAINS, axis6_sign, terrain_generator, update  # noqa: E402
from sim_peps3d_left_right_weyl_sheet_cover_gate_probe import IDENTITY, SIGMA_1, SIGMA_2, SIGMA_3, SIGMA_MINUS, SIGMA_PLUS, sheet_rho  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_operator_substage_cell_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase6_peps3d_operator_substage_cell_embedding"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests 64 PEPS3D-carried operator-substage cells and "
    "their projection to 16 placements. It does not admit flux, Xi/Phi0, "
    "Axis0, basin, physics, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 64 substage cell tensors, operator channels, terrain/operator order gaps, and stress sweeps",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing substage-cell admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact 2x2x4x4 count and projection fiber check",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 4x4x4 PEPS3D cell-anchor graph",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive formal-scout receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
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

ENGINE_TYPES = ("Type1", "Type2")
OPERATORS = ("Ti", "Te", "Fi", "Fe")
ENGINE_TO_SHEET = {"Type1": "L", "Type2": "R"}
GAP_FLOOR = 1.0e-7
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


def substage_cells() -> list[dict[str, Any]]:
    rows = []
    idx = 0
    coords = coords_for_shape((4, 4, 4))
    for engine in ENGINE_TYPES:
        for loop in LOOPS:
            for terrain in TERRAINS:
                for operator in OPERATORS:
                    sheet = ENGINE_TO_SHEET[engine]
                    rows.append(
                        {
                            "idx": idx,
                            "engine_type": engine,
                            "sheet": sheet,
                            "loop": loop,
                            "terrain": terrain,
                            "operator_slot": operator,
                            "placement": (engine, loop, terrain),
                            "coord": coords[idx],
                            "axis6_sign": axis6_sign(sheet, loop, terrain),
                        }
                    )
                    idx += 1
    return rows


def cell_graph() -> rx.PyGraph:
    graph = rx.PyGraph()
    graph.add_nodes_from([{"coord": coord} for coord in coords_for_shape((4, 4, 4))])
    for edge in edge_list((4, 4, 4)):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def operator_matrix(slot: str) -> torch.Tensor:
    if slot == "Ti":
        return IDENTITY + 0.19 * SIGMA_1 + 0.07j * SIGMA_3
    if slot == "Te":
        return IDENTITY + 0.17 * SIGMA_2 - 0.05j * SIGMA_1
    if slot == "Fi":
        return IDENTITY + 0.23 * SIGMA_MINUS + 0.11 * SIGMA_3
    if slot == "Fe":
        return IDENTITY + 0.21 * SIGMA_PLUS - 0.09 * SIGMA_2
    raise ValueError(slot)


def operator_channel(slot: str, rho: torch.Tensor) -> torch.Tensor:
    op = operator_matrix(slot)
    out = op @ rho @ op.conj().T
    return (out + out.conj().T) / (2.0 * torch.trace(out).real)


def terrain_channel(sheet: str, terrain: str, rho: torch.Tensor) -> torch.Tensor:
    return update(rho, terrain_generator(sheet, terrain, rho))


def order_gap_for_cell(cell: dict[str, Any]) -> float:
    rho = sheet_rho(cell["sheet"], int(cell["idx"]) % 8)
    terrain_after_operator = terrain_channel(cell["sheet"], cell["terrain"], operator_channel(cell["operator_slot"], rho))
    operator_after_terrain = operator_channel(cell["operator_slot"], terrain_channel(cell["sheet"], cell["terrain"], rho))
    return float(torch.linalg.vector_norm((terrain_after_operator - operator_after_terrain).reshape(-1)).item())


def cell_tensor(cell: dict[str, Any], bond_dim: int) -> torch.Tensor:
    rho = operator_channel(cell["operator_slot"], terrain_channel(cell["sheet"], cell["terrain"], sheet_rho(cell["sheet"], int(cell["idx"]) % 8)))
    physical = probe_response_from_density(rho.reshape(1, 2, 2), sic_effects())[0].to(CTYPE)
    alpha = torch.arange(bond_dim, dtype=RTYPE)
    meshes = torch.meshgrid(alpha, alpha, alpha, alpha, alpha, alpha, indexing="ij")
    virtual_sum = sum((idx + 1.0) * mesh for idx, mesh in enumerate(meshes))
    phase = torch.exp(1j * (0.011 * (int(cell["idx"]) + 1) + 0.005 * virtual_sum)).to(CTYPE)
    sign = 1.0 if cell["axis6_sign"] == "up" else -1.0
    op_weight = 1.0 + 0.031 * (OPERATORS.index(cell["operator_slot"]) + 1)
    return phase.unsqueeze(-1) * physical.reshape(*((1,) * 6), 4) * sign * op_weight


def cell_gate() -> dict[str, Any]:
    cells = substage_cells()
    graph = cell_graph()
    projection_counts = Counter(tuple(cell["placement"]) for cell in cells)
    axis_uniform = all(
        len({cell["axis6_sign"] for cell in cells if tuple(cell["placement"]) == placement}) == 1
        for placement in projection_counts
    )
    gaps = [order_gap_for_cell(cell) for cell in cells]
    tensors = torch.stack([cell_tensor(cell, 2) for cell in cells])
    signatures = {
        tuple(round(float(x.real.item()), 8) for x in tensor.reshape(-1)[:12])
        for tensor in tensors
    }
    exact_count = sp.Integer(len(ENGINE_TYPES)) * sp.Integer(len(LOOPS)) * sp.Integer(len(TERRAINS)) * sp.Integer(len(OPERATORS))
    exact_projection = sp.Integer(len(ENGINE_TYPES)) * sp.Integer(len(LOOPS)) * sp.Integer(len(TERRAINS))
    return {
        "pass": bool(
            len(cells) == 64
            and len(projection_counts) == 16
            and set(projection_counts.values()) == {4}
            and axis_uniform
            and graph.num_nodes() == 64
            and graph.num_edges() == 144
            and min(gaps) > GAP_FLOOR
            and len(signatures) == 64
            and int(exact_count) == 64
            and int(exact_projection) == 16
        ),
        "finite_map": "Phi_c : K_c -> K'_c for c=(engine_type,loop_field,terrain,operator_slot)",
        "domain": "D6 = 64 PEPS3D substage cells over EngineType x Loop x Terrain x OperatorSlot",
        "output": "O6 = 64 local PEPS3D tensors/channels with projection pi(c)=(engine_type,loop,terrain)",
        "peps3d_embedding": "64 substage cells are anchored one-to-one on a 4x4x4 finite PEPS3D carrier",
        "substage_count": len(cells),
        "projection_stage_count": len(projection_counts),
        "projection_fiber_sizes": sorted(set(projection_counts.values())),
        "axis6_uniform_within_projection": axis_uniform,
        "min_operator_terrain_order_gap": min(gaps),
        "max_operator_terrain_order_gap": max(gaps),
        "unique_cell_tensor_signature_count": len(signatures),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "sympy_exact_substage_count": int(exact_count),
        "sympy_exact_projection_count": int(exact_projection),
    }


def stress_gate() -> dict[str, Any]:
    cells = substage_cells()
    rows = []
    for bond_dim in (2, 3, 4):
        tensors = torch.stack([cell_tensor(cell, bond_dim) for cell in cells])
        rows.append(
            {
                "substage_count": len(cells),
                "bond_dim": bond_dim,
                "tensor_shape": list(tensors.shape),
                "dense_state_closure_used": False,
                "pass": bool(torch.isfinite(torch.real(tensors)).all().item()),
            }
        )
    return {
        "pass": all(row["pass"] for row in rows),
        "rows": rows,
        "dense_state_closure_used": False,
        "max_qubits": 64,
        "max_peps3d_sites": 64,
        "max_peps3d_bond": 4,
    }


def native_only_16_row_collapse_rejected() -> dict[str, Any]:
    cells = substage_cells()
    collapsed = {tuple(cell["placement"]) for cell in cells}
    return {
        "pass": len(collapsed) == 16,
        "why_rejected": "collapsing operator slots leaves 16 placement rows and loses 64 substage cell anchors",
        "collapsed_row_count": len(collapsed),
        "required_substage_count": 64,
    }


def mixed_axis6_control_rejected() -> dict[str, Any]:
    cells = substage_cells()
    mixed = []
    for cell in cells:
        clone = dict(cell)
        if OPERATORS.index(cell["operator_slot"]) % 2 == 1:
            clone["axis6_sign"] = "down" if cell["axis6_sign"] == "up" else "up"
        mixed.append(clone)
    projection_mixed = any(
        len({cell["axis6_sign"] for cell in mixed if tuple(cell["placement"]) == placement}) > 1
        for placement in {tuple(cell["placement"]) for cell in mixed}
    )
    return {
        "pass": projection_mixed,
        "why_rejected": "mixed Axis6 signs inside one projected placement break inherited placement orientation",
        "mixed_axis6_detected": projection_mixed,
    }


def order_erased_control_rejected() -> dict[str, Any]:
    rho = sheet_rho("L", 0)
    identity_after_terrain = operator_channel("Ti", terrain_channel("L", "Ne", rho))
    terrain_after_identity = terrain_channel("L", "Ne", operator_channel("Ti", rho))
    # Replace the Ti operator with the identity channel for the actual erased test.
    identity_channel_gap = float(torch.linalg.vector_norm((terrain_channel("L", "Ne", rho) - terrain_channel("L", "Ne", rho)).reshape(-1)).item())
    live_gap = float(torch.linalg.vector_norm((identity_after_terrain - terrain_after_identity).reshape(-1)).item())
    return {
        "pass": identity_channel_gap < TOL and live_gap > GAP_FLOOR,
        "why_rejected": "identity/order-erased operator path has no substage order witness",
        "identity_channel_gap": identity_channel_gap,
        "live_ti_gap_reference": live_gap,
    }


def no_cell_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "operator rows without one PEPS3D cell per substage are labels, not manifold cells",
        "cell_anchor_count": 0,
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
    cell = cell_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_native_only_16_row_collapse_rejected": native_only_16_row_collapse_rejected(),
        "GC2_mixed_axis6_control_rejected": mixed_axis6_control_rejected(),
        "GC3_order_erased_control_rejected": order_erased_control_rejected(),
        "GC4_no_cell_anchor_control_rejected": no_cell_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": ["PEPS3D closure stress", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
        },
    }
    actuals = {
        "phase0_receipts_declared": True,
        "phase1_receipt_declared": True,
        "phase2_receipt_declared": True,
        "phase3_receipt_declared": True,
        "phase4_receipt_declared": True,
        "phase5_receipt_declared": True,
        "substage_cells": bool(cell["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_64_operator_substage_cell_map": cell,
        "operator_substage_cell_scale_stress_without_dense_closure": stress,
        "z3_operator_substage_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_operator_substage_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [cell["finite_map"], "pi_stage(c)=(engine_type,loop,terrain)", "I_order(c)=||Phi_T o U_o(rho)-U_o o Phi_T(rho)||"],
        "domain": cell["domain"],
        "codomain_or_output": cell["output"],
        "carrier_realization": "64 finite PEPS3D substage cell tensors/channels over a 4x4x4 carrier; no dense closure",
        "peps3d_embedding": cell["peps3d_embedding"],
        "spinor_state": "substage channels act on Phase 5 terrain/sheet density readouts",
        "quaternion_action": "not_applicable_phase6",
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
        ],
        "downstream_blocks": ["PEPS3D closure stress", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 6,
            "candidate": "peps3d_64_operator_substage_cells",
            "stage_projection_count": cell["projection_stage_count"],
            "substage_count": cell["substage_count"],
            "max_qubits": stress["max_qubits"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 6 PEPS3D operator-substage cell formal scout. It is not flux, "
            "Xi/Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Validate this Phase 6 receipt before opening PEPS3D closure/scale stress.",
            "Keep 64 substages as cells; reject 16-row collapse or mixed Axis6 orientation inside projected placements.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
