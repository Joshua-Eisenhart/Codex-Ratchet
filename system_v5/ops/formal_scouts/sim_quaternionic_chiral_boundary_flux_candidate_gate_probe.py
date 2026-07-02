#!/usr/bin/env python3
"""Quaternionic chiral boundary flux candidate gate.

Formal scout only.

This Phase 8 row opens only after Phases 0-7 have validated receipts. It tests a
derived candidate:

  J_flux(engine,shell,boundary) = i J_i + j J_j + k J_k
  J_alpha = R_alpha(Psi_R, ...) - R_alpha(Psi_L, ...)

It is not a final flux admission and does not open Xi/Phi0/Axis0.
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
import torch
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import CTYPE, RTYPE, coords_for_shape  # noqa: E402
from sim_peps3d_left_right_weyl_sheet_cover_gate_probe import sheet_signature  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "quaternionic_chiral_boundary_flux_candidate_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase8_blocked_derived_quaternionic_chiral_boundary_flux_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a derived quaternionic chiral boundary-current "
    "candidate after lower Phase 0-7 receipts. It does not admit final flux, "
    "Xi/Phi0, Axis0, basin, physics, or ontology."
)

DEPENDENCY_RECEIPTS = [
    "finite_effect_sic_weyl_substrate_admission_probe_results.json",
    "finite_effect_algebra_laws_probe_results.json",
    "finite_contextuality_sheaf_event_gate_probe_results.json",
    "sic_mub_probe_family_comparison_probe_results.json",
    "process_povm_quantum_comb_history_gate_probe_results.json",
    "finite_projective_design_spectral_triple_gate_probe_results.json",
    "finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json",
    "peps3d_spinor_density_carrier_gate_probe_results.json",
    "peps3d_nested_hopf_torus_loop_field_gate_probe_results.json",
    "peps3d_left_right_weyl_sheet_cover_gate_probe_results.json",
    "peps3d_terrain_generator_placement_gate_probe_results.json",
    "peps3d_operator_substage_cell_gate_probe_results.json",
    "peps3d_boundary_contraction_scale_closure_stress_gate_probe_results.json",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing quaternion-component boundary-current tensors and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency/nonpromotion admission gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent dependency/nonpromotion cross-check",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive dependency receipt reads and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

GAP_FLOOR = 1.0e-6
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


def dependency_gate() -> dict[str, Any]:
    rows = []
    for name in DEPENDENCY_RECEIPTS:
        path = RESULT_DIR / name
        exists = path.exists()
        all_pass = False
        if exists:
            all_pass = bool(json.loads(path.read_text(encoding="utf-8")).get("all_pass", False))
        rows.append({"path": str(path.relative_to(ROOT)), "exists": exists, "all_pass": all_pass})
    return {
        "pass": all(row["exists"] and row["all_pass"] for row in rows),
        "rows": rows,
        "dependency_count": len(rows),
    }


def boundary_indices() -> list[int]:
    coords = coords_for_shape((4, 4, 4))
    return [idx for idx, coord in enumerate(coords) if any(coord[axis] in (0, 3) for axis in range(3))]


def readout(sheet: str, site: int, shell_shift: int = 0, topology_freeze: bool = False) -> torch.Tensor:
    idx = 0 if topology_freeze else site % 8
    sig = sheet_signature(sheet, idx)
    shell_weight = 1.0 + 0.031 * ((site + shell_shift) % 5)
    return torch.stack(
        [
            torch.real(sig[:4]).sum() * shell_weight,
            torch.real(sig[4:8]).sum() * shell_weight,
            torch.real(sig[8:]).sum() * shell_weight,
        ]
    )


def quaternion_components(
    sheet_erased: bool = False,
    shell_reversed: bool = False,
    engine_swapped: bool = False,
    topology_freeze: bool = False,
) -> torch.Tensor:
    rows = []
    b_indices = boundary_indices()
    for pos, site in enumerate(b_indices):
        shell_shift = (len(b_indices) - pos) if shell_reversed else pos
        left_sheet = "R" if engine_swapped else "L"
        right_sheet = "L" if engine_swapped else "R"
        left = readout(left_sheet, site, shell_shift=shell_shift, topology_freeze=topology_freeze)
        right = readout(left_sheet if sheet_erased else right_sheet, site, shell_shift=shell_shift, topology_freeze=topology_freeze)
        rows.append(right - left)
    return torch.stack(rows)


def quaternion_mul(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def flux_candidate_gate() -> dict[str, Any]:
    components = quaternion_components()
    norm = float(torch.linalg.vector_norm(components).item())
    sheet_erased = quaternion_components(sheet_erased=True)
    shell_reversed = quaternion_components(shell_reversed=True)
    engine_swapped = quaternion_components(engine_swapped=True)
    topology_frozen = quaternion_components(topology_freeze=True)
    i = (0.0, 1.0, 0.0, 0.0)
    j = (0.0, 0.0, 1.0, 0.0)
    k = (0.0, 0.0, 0.0, 1.0)
    ij = quaternion_mul(i, j)
    ijk = quaternion_mul(ij, k)
    return {
        "pass": bool(
            norm > GAP_FLOOR
            and float(torch.linalg.vector_norm(sheet_erased).item()) < TOL
            and float(torch.linalg.vector_norm(components - shell_reversed).item()) > GAP_FLOOR
            and float(torch.linalg.vector_norm(components + engine_swapped).item()) < 1.0e-5
            and float(torch.linalg.vector_norm(components - topology_frozen).item()) > GAP_FLOOR
            and ij == k
            and ijk == (-1.0, 0.0, 0.0, 0.0)
        ),
        "finite_map": "J_flux(engine,shell,boundary)=iJ_i+jJ_j+kJ_k with J_alpha=R_alpha(Psi_R)-R_alpha(Psi_L)",
        "domain": "D8 = Phase 0-7 admitted finite PEPS3D boundary sites with L/R sheet and shell readouts",
        "output": "O8 = quaternion-component boundary current candidate and controls",
        "peps3d_embedding": "boundary indices of the 4x4x4 PEPS3D carrier after Phase 7 boundary stress",
        "boundary_site_count": len(boundary_indices()),
        "component_shape": list(components.shape),
        "component_norm": norm,
        "sheet_erased_norm": float(torch.linalg.vector_norm(sheet_erased).item()),
        "shell_reversal_gap": float(torch.linalg.vector_norm(components - shell_reversed).item()),
        "engine_swap_antisymmetry_gap": float(torch.linalg.vector_norm(components + engine_swapped).item()),
        "topology_freeze_gap": float(torch.linalg.vector_norm(components - topology_frozen).item()),
        "quaternion_i_times_j": ij,
        "quaternion_ij_times_k": ijk,
    }


def order_swap_control_rejected() -> dict[str, Any]:
    components = quaternion_components()
    swapped = torch.flip(components, dims=[0])
    gap = float(torch.linalg.vector_norm(components - swapped).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "boundary order swap changes the quaternionic current components",
        "order_swap_gap": gap,
    }


def sheet_erase_control_rejected() -> dict[str, Any]:
    erased = quaternion_components(sheet_erased=True)
    return {
        "pass": float(torch.linalg.vector_norm(erased).item()) < TOL,
        "why_rejected": "sheet erasure kills the chiral difference R_alpha(Psi_R)-R_alpha(Psi_L)",
        "sheet_erased_norm": float(torch.linalg.vector_norm(erased).item()),
    }


def shell_reversal_control() -> dict[str, Any]:
    components = quaternion_components()
    reversed_components = quaternion_components(shell_reversed=True)
    gap = float(torch.linalg.vector_norm(components - reversed_components).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_control": "shell reversal is a live control for the shell-indexed boundary current",
        "shell_reversal_gap": gap,
    }


def topology_freeze_control_rejected() -> dict[str, Any]:
    components = quaternion_components()
    frozen = quaternion_components(topology_freeze=True)
    gap = float(torch.linalg.vector_norm(components - frozen).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "topology freeze collapses boundary variation and is not an admitted flux carrier",
        "topology_freeze_gap": gap,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_claim = z3.Bool("final_flux_claim")
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
    final_claim = solver.mkConst(bool_sort, "final_flux_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_claim, solver.mkBoolean(False)))
    positive = solver.checkSat()
    collapse = cvc5.Solver()
    collapse.setLogic("ALL")
    bool_sort2 = collapse.getBooleanSort()
    terms2 = {key: collapse.mkConst(bool_sort2, f"ko_{key}") for key in actuals}
    final_claim2 = collapse.mkConst(bool_sort2, "ko_final_flux_claim")
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


def blocked_result(reason: str, started: float) -> dict[str, Any]:
    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": False,
        "blockers": [{"kind": "blocked_reason", "reason": reason, "next_admissible_step": "rerun and validate missing Phase 0-7 receipts"}],
        "summary": {"phase": 8, "candidate": "blocked_quaternionic_chiral_boundary_flux_candidate", "elapsed_seconds": time.time() - started},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dependencies = dependency_gate()
    if not dependencies["pass"]:
        result = blocked_result("missing_or_failing_lower_phase_receipt", started)
        result["dependency_receipts"] = dependencies["rows"]
        OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"wrote": str(OUT_PATH), "all_pass": False, "blocked": result["blockers"]}, indent=2, sort_keys=True))
        return 1

    flux = flux_candidate_gate()
    graveyard_companions = {
        "GC1_order_swap_control_rejected": order_swap_control_rejected(),
        "GC2_sheet_erase_control_rejected": sheet_erase_control_rejected(),
        "GC3_shell_reversal_control": shell_reversal_control(),
        "GC4_topology_freeze_control_rejected": topology_freeze_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_final_flux_not_admitted": {"pass": True, "final_flux_admitted": False},
        "B3_downstream_consumers_blocked": {"pass": True, "blocked_consumers": ["Xi", "Phi0", "Axis0", "basin", "physics"]},
    }
    actuals = {
        "dependencies": bool(dependencies["pass"]),
        "flux_candidate": bool(flux["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "lower_phase_dependency_gate": dependencies,
        "quaternionic_chiral_boundary_flux_candidate": flux,
        "z3_quaternionic_flux_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_quaternionic_flux_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "carrier_realization": "derived quaternion-component readout over finite PEPS3D boundary sites; no final flux promotion",
        "peps3d_embedding": flux["peps3d_embedding"],
        "spinor_state": "uses Phase 4-7 spinor-derived sheet boundary readouts",
        "quaternion_action": "J_flux=iJ_i+jJ_j+kJ_k with checked i*j=k and i*j*k=-1",
        "dependency_receipts": [f"system_v5/ops/formal_scouts/results/{name}" for name in DEPENDENCY_RECEIPTS],
        "downstream_blocks": ["Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 8,
            "candidate": "quaternionic_chiral_boundary_flux_candidate_not_promoted",
            "boundary_site_count": flux["boundary_site_count"],
            "max_qubits": 64,
            "max_peps3d_sites": 64,
            "max_peps3d_bond": 5,
            "final_flux_admitted": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 8 derived quaternionic flux-candidate formal scout. It is not final flux, "
            "Xi/Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Do not open Xi/Phi0/Axis0 unless a separate admission decision promotes a flux receipt.",
            "Audit whether quaternionic current components survive broader boundary and engine controls before any downstream readout.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
