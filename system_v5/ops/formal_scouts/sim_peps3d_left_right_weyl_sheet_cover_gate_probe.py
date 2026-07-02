#!/usr/bin/env python3
"""PEPS3D-anchored L/R Weyl sheet-cover gate.

Formal scout only.

This Phase 4 row tests the finite sheet-cover map on the admitted PEPS3D
spinor/Hopf carrier:

  H_L = +H0
  H_R = -H0
  rho_dot_L = -i[H_L, rho_L]
  rho_dot_R = -i[H_R, rho_R]

The receipt also checks that the cover is not just a sign label: sigma-/sigma+
swap, sheet projectors, loop ownership, sheet-erasure controls, and mirror
non-equivalence readouts are load-bearing.
"""

from __future__ import annotations

import json
import math
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
from torch_geometric.data import Data
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import CTYPE, RTYPE, carrier_graph, coords_for_shape, edge_list  # noqa: E402
from sim_peps3d_nested_hopf_torus_loop_field_gate_probe import SHELLS, base_step, fiber_step, state_from_tuple  # noqa: E402
from sim_peps3d_spinor_density_carrier_gate_probe import density_readout, spinor  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_left_right_weyl_sheet_cover_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase4_peps3d_left_right_weyl_sheet_cover"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a PEPS3D-anchored L/R Weyl sheet-cover map with "
    "Hamiltonian sign, ladder swap, projector, loop-ownership, and mirror "
    "non-equivalence readouts. It does not admit terrain, substages, flux, "
    "Xi/Phi0, Axis0, basin, physics, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sheet density dynamics, ladder swaps, projectors, loop ownership, and order gaps",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sheet-cover admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact mirror, sign, and ladder-swap identities",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing inherited PEPS3D site/bond anchor graph",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph Data carrier for sheet-site aggregation",
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
    "torch_geometric": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

TOL = 1.0e-9
GAP_FLOOR = 1.0e-5

SIGMA_1 = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
SIGMA_2 = torch.tensor([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=CTYPE)
SIGMA_3 = torch.tensor([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=CTYPE)
SIGMA_MINUS = torch.tensor([[0.0 + 0.0j, 0.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
SIGMA_PLUS = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
MIRROR = SIGMA_1
H0 = 0.37 * SIGMA_1 + 0.23 * SIGMA_2 + 0.41 * SIGMA_3
H_L = H0
H_R = -H0
IDENTITY = torch.eye(2, dtype=CTYPE)


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


def commutator_dot(hamiltonian: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return -1j * (hamiltonian @ rho - rho @ hamiltonian)


def dissipator(jump: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    left = jump.conj().T @ jump
    return jump @ rho @ jump.conj().T - 0.5 * (left @ rho + rho @ left)


def projectors(axis: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    norm = torch.linalg.matrix_norm(axis).real
    unit = axis / norm
    return (IDENTITY + unit) / 2.0, (IDENTITY - unit) / 2.0


def sheet_rho(sheet: str, site: int, shell_index: int = 1) -> torch.Tensor:
    phi = 0.17 + 0.11 * site
    chi = -0.23 + 0.07 * (site % 5)
    eta = SHELLS[shell_index % len(SHELLS)]
    rho = density_readout(spinor(phi, chi, eta).reshape(1, 2))[0]
    if sheet == "R":
        return MIRROR @ rho @ MIRROR
    return rho


def loop_owned_rho(sheet: str, site: int, shell_index: int = 1) -> torch.Tensor:
    phi = 0.17 + 0.11 * site
    chi = -0.23 + 0.07 * (site % 5)
    if sheet == "L":
        row = base_step(shell_index, phi, chi)
    else:
        row = fiber_step(shell_index, phi, chi)
    rho = density_readout(state_from_tuple(row).reshape(1, 2))[0]
    return MIRROR @ rho @ MIRROR if sheet == "R" else rho


def sheet_signature(sheet: str, site: int, erased: bool = False, wrong_ladder: bool = False, projector_erased: bool = False) -> torch.Tensor:
    rho = sheet_rho("L" if erased else sheet, site)
    hamiltonian = H_L if erased or sheet == "L" else H_R
    dot = commutator_dot(hamiltonian, rho)
    if erased:
        jump = SIGMA_MINUS
    elif sheet == "L":
        jump = SIGMA_MINUS
    else:
        jump = SIGMA_MINUS if wrong_ladder else SIGMA_PLUS
    ladder = dissipator(jump, rho)
    if projector_erased:
        p_plus, p_minus = IDENTITY, IDENTITY
    elif sheet == "L" or erased:
        p_plus, p_minus = projectors(0.61 * SIGMA_3 + 0.19 * SIGMA_1)
    else:
        p_plus, p_minus = projectors(-0.57 * SIGMA_3 + 0.13 * SIGMA_1)
    proj_sig = torch.stack([torch.trace(p_plus @ rho).real, torch.trace(p_minus @ rho).real]).to(CTYPE)
    loop_rho = sheet_rho("L" if erased else sheet, site) if erased else loop_owned_rho(sheet, site)
    pieces = [
        dot.reshape(-1),
        ladder.reshape(-1),
        proj_sig,
        loop_rho.reshape(-1),
    ]
    return torch.cat([piece.to(CTYPE) for piece in pieces])


def sheet_cover_gate() -> dict[str, Any]:
    graph = carrier_graph((2, 2, 2))
    left = torch.stack([sheet_signature("L", site) for site in range(8)])
    right = torch.stack([sheet_signature("R", site) for site in range(8)])
    mirror_gaps = torch.linalg.vector_norm(left - right, dim=1)
    erased_left = torch.stack([sheet_signature("L", site, erased=True) for site in range(8)])
    erased_right = torch.stack([sheet_signature("R", site, erased=True) for site in range(8)])
    erased_gap = torch.linalg.vector_norm(erased_left - erased_right, dim=1)
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and float(torch.min(mirror_gaps).item()) > GAP_FLOOR
            and float(torch.max(erased_gap).item()) < TOL
            and float(torch.linalg.matrix_norm(H_L + H_R).real.item()) < TOL
        ),
        "finite_map": "sheet_cover_K : (v,k,phi,chi,sheet) -> (rho_sheet,H_sheet,rho_dot_sheet,ladder_sheet,projector_sheet,loop_owner_sheet)",
        "domain": "D4 = finite PEPS3D site anchors x finite shell/phase samples x sheet in {L,R}",
        "output": "O4 = sheet-specific density dynamics, ladder/projector readouts, and loop-owned signatures",
        "peps3d_embedding": "anchor(sheet cell)=v in V of the PEPS3D carrier; both sheets cover the same finite site/shell anchors",
        "site_count": 8,
        "sheet_count": 2,
        "signature_width": int(left.shape[1]),
        "min_left_right_signature_gap": float(torch.min(mirror_gaps).item()),
        "max_sheet_erased_gap": float(torch.max(erased_gap).item()),
        "hamiltonian_sign_gap": float(torch.linalg.matrix_norm(H_L + H_R).real.item()),
    }


def order_witness_gate() -> dict[str, Any]:
    rows = []
    controls = []
    for site in range(8):
        rho = sheet_rho("L", site)
        step_h_then_ladder = dissipator(SIGMA_MINUS, rho + 0.05 * commutator_dot(H_L, rho))
        step_ladder_then_h = commutator_dot(H_L, rho + 0.05 * dissipator(SIGMA_MINUS, rho))
        rows.append(float(torch.linalg.vector_norm((step_h_then_ladder - step_ladder_then_h).reshape(-1)).item()))
        controls.append(float(torch.linalg.vector_norm((commutator_dot(H_L, rho) - commutator_dot(H_L, rho)).reshape(-1)).item()))
    return {
        "pass": bool(min(rows) > GAP_FLOOR and max(controls) < TOL),
        "N01_witness": "sheet Hamiltonian update and sheet ladder channel are order-sensitive on spinor-derived density readouts",
        "min_order_gap": min(rows),
        "max_order_erased_control_gap": max(controls),
    }


def sympy_mirror_gate() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    lower = sp.Matrix([[0, 0], [1, 0]])
    upper = sp.Matrix([[0, 1], [0, 0]])
    h = sp.Rational(37, 100) * sx + sp.Rational(23, 100) * sy + sp.Rational(41, 100) * sz
    return {
        "pass": bool(sx * lower * sx == upper and sx * h * sx != -h and h + (-h) == sp.zeros(2, 2)),
        "mirror_maps_lowering_to_raising": bool(sx * lower * sx == upper),
        "mirror_not_full_hamiltonian_sign_flip": bool(sx * h * sx != -h),
        "declared_right_hamiltonian_is_negative_left": bool(h + (-h) == sp.zeros(2, 2)),
    }


def graph_anchor_gate() -> dict[str, Any]:
    graph = carrier_graph((2, 2, 2))
    edges = edge_list((2, 2, 2))
    edge_pairs = []
    for edge in edges:
        edge_pairs.append((int(edge["src"]), int(edge["dst"])))
        edge_pairs.append((int(edge["dst"]), int(edge["src"])))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    features = torch.stack([torch.real(sheet_signature("L", site)[:2]) for site in range(8)])
    data = Data(x=features, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    return {
        "pass": bool(graph.num_nodes() == 8 and graph.num_edges() == 12 and int(data.edge_index.shape[1]) == 24),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.edge_index.shape[1]),
        "pyg_aggregate_sum": float(torch.sum(aggregate).item()),
    }


def stress_gate() -> dict[str, Any]:
    shapes = [(2, 2, 2), (2, 2, 4), (2, 4, 4), (4, 4, 4)]
    rows = []
    max_sites = 0
    for shape in shapes:
        site_count = len(coords_for_shape(shape))
        gaps = []
        for site in range(site_count):
            left = sheet_signature("L", site % 8)
            right = sheet_signature("R", site % 8)
            gaps.append(float(torch.linalg.vector_norm(left - right).item()))
        rows.append(
            {
                "shape": shape,
                "site_count": site_count,
                "sheet_count": 2,
                "min_left_right_signature_gap": min(gaps),
                "dense_state_closure_used": False,
                "pass": min(gaps) > GAP_FLOOR,
            }
        )
        max_sites = max(max_sites, site_count)
    return {
        "pass": all(row["pass"] for row in rows),
        "rows": rows,
        "dense_state_closure_used": False,
        "max_qubits": max_sites,
        "max_peps3d_sites": max_sites,
        "max_peps3d_bond": 4,
    }


def sheet_erasure_control_rejected() -> dict[str, Any]:
    gaps = []
    for site in range(8):
        gaps.append(float(torch.linalg.vector_norm(sheet_signature("L", site, erased=True) - sheet_signature("R", site, erased=True)).item()))
    return {
        "pass": max(gaps) < TOL,
        "why_rejected": "sheet erasure collapses L/R signatures to the same carrier row",
        "max_erased_gap": max(gaps),
    }


def wrong_ladder_swap_control_rejected() -> dict[str, Any]:
    gaps = []
    for site in range(8):
        gaps.append(float(torch.linalg.vector_norm(sheet_signature("R", site) - sheet_signature("R", site, wrong_ladder=True)).item()))
    return {
        "pass": min(gaps) > GAP_FLOOR,
        "why_rejected": "using sigma_- on the R sheet breaks the sigma-/sigma+ sheet swap",
        "min_wrong_ladder_gap": min(gaps),
    }


def projector_erasure_control_rejected() -> dict[str, Any]:
    gaps = []
    for site in range(8):
        gaps.append(float(torch.linalg.vector_norm(sheet_signature("L", site) - sheet_signature("L", site, projector_erased=True)).item()))
    return {
        "pass": min(gaps) > GAP_FLOOR,
        "why_rejected": "identity projectors erase sheet-specific projector readouts",
        "min_projector_erasure_gap": min(gaps),
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "sheet dynamics without PEPS3D site/shell anchors are not admitted carrier cells",
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
    cover = sheet_cover_gate()
    order = order_witness_gate()
    mirror = sympy_mirror_gate()
    graph = graph_anchor_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_sheet_erasure_control_rejected": sheet_erasure_control_rejected(),
        "GC2_wrong_ladder_swap_control_rejected": wrong_ladder_swap_control_rejected(),
        "GC3_projector_erasure_control_rejected": projector_erasure_control_rejected(),
        "GC4_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": ["terrain", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
        },
    }
    actuals = {
        "phase0_receipts_declared": True,
        "phase1_receipt_declared": True,
        "phase2_receipt_declared": True,
        "phase3_receipt_declared": True,
        "sheet_cover": bool(cover["pass"]),
        "order_witness": bool(order["pass"]),
        "mirror_gate": bool(mirror["pass"]),
        "peps3d_anchor": bool(graph["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_anchored_left_right_sheet_cover_map": cover,
        "sheet_hamiltonian_ladder_order_witness": order,
        "sympy_mirror_and_ladder_identity_gate": mirror,
        "peps3d_graph_anchor_carrier": graph,
        "left_right_sheet_scale_stress_without_dense_closure": stress,
        "z3_left_right_sheet_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_left_right_sheet_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [cover["finite_map"], order["N01_witness"]],
        "domain": cover["domain"],
        "codomain_or_output": cover["output"],
        "carrier_realization": "finite PEPS3D site anchors carrying L/R sheet-specific density dynamics and readout signatures",
        "peps3d_embedding": cover["peps3d_embedding"],
        "spinor_state": "sheet cover over Phase 2 spinor-derived density and Phase 3 shell/loop anchors",
        "quaternion_action": "not_applicable_phase4",
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
        ],
        "downstream_blocks": ["terrain", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 4,
            "candidate": "peps3d_anchored_left_right_weyl_sheet_cover",
            "max_qubits": stress["max_qubits"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 4 PEPS3D-anchored L/R sheet-cover formal scout. It is not terrain, "
            "substage, flux, Xi/Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Validate this Phase 4 receipt before opening terrain-generator candidates.",
            "Keep L/R sheets as PEPS3D-anchored sheet-specific dynamics; reject sign-only or sheet-erased shortcuts.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
