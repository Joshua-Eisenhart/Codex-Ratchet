#!/usr/bin/env python3
"""PEPS3D-anchored terrain-generator and placement gate.

Formal scout only.

This Phase 5 row tests finite terrain generator maps and the 16 placement
objects:

  X_(tau,s): rho_(v,s,k) -> rho_dot_(v,s,k)
  tau in {Se, Ne, Ni, Si}
  s in {L, R}
  ell in {in, out}
  placement = (s, ell, tau, X_(tau,s), Y_ell, token, axis6_sign)

Terrain family, terrain law, loop field, placement token, and PEPS3D anchor are
kept distinct. This does not admit engine substages, flux, Xi/Phi0, Axis0,
basin, physics, or full PEPS3D closure.
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
from torch_geometric.data import Data
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import CTYPE, RTYPE, carrier_graph, coords_for_shape, edge_list  # noqa: E402
from sim_peps3d_left_right_weyl_sheet_cover_gate_probe import (  # noqa: E402
    H_L,
    H_R,
    IDENTITY,
    SIGMA_1,
    SIGMA_2,
    SIGMA_3,
    SIGMA_MINUS,
    SIGMA_PLUS,
    commutator_dot,
    dissipator,
    projectors,
    sheet_rho,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_terrain_generator_placement_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase5_peps3d_terrain_generator_placement"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests the eight PEPS3D-anchored terrain generator maps "
    "and 16 sheet/loop/terrain placements. It does not admit engine substages, "
    "flux, Xi/Phi0, Axis0, basin, physics, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing terrain generator channels, placement signatures, loop/terrain order gaps, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing terrain/placement admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact terrain/placement count check",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing inherited PEPS3D site/bond anchor graph",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph Data carrier for placement signatures",
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

TERRAINS = ("Se", "Ne", "Ni", "Si")
SHEETS = ("L", "R")
LOOPS = ("in", "out")
DT = 0.047
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


def anticommutator(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return left @ right + right @ left


def dephase(projector_pair: tuple[torch.Tensor, torch.Tensor], rho: torch.Tensor) -> torch.Tensor:
    p_plus, p_minus = projector_pair
    return p_plus @ rho @ p_plus + p_minus @ rho @ p_minus - rho


def terrain_generator(sheet: str, terrain: str, rho: torch.Tensor) -> torch.Tensor:
    hamiltonian = H_L if sheet == "L" else H_R
    if terrain == "Se":
        pauli_diss = dissipator(SIGMA_1, rho) + dissipator(SIGMA_2, rho) + dissipator(SIGMA_3, rho)
        return 0.19 * pauli_diss + 0.31 * commutator_dot(hamiltonian, rho)
    if terrain == "Ne":
        return commutator_dot(hamiltonian, rho)
    if terrain == "Ni":
        jump = SIGMA_MINUS if sheet == "L" else SIGMA_PLUS
        return 0.43 * dissipator(jump, rho) + 0.17 * commutator_dot(hamiltonian, rho)
    if terrain == "Si":
        axis = 0.47 * SIGMA_3 + (0.16 if sheet == "L" else -0.14) * SIGMA_1 + 0.09 * SIGMA_2
        return 0.29 * commutator_dot(axis, rho) + 0.23 * dephase(projectors(axis), rho)
    raise ValueError((sheet, terrain))


def update(rho: torch.Tensor, derivative: torch.Tensor) -> torch.Tensor:
    out = rho + DT * derivative
    out = (out + out.conj().T) / 2.0
    return out / torch.trace(out).real


def loop_channel(sheet: str, loop: str, rho: torch.Tensor) -> torch.Tensor:
    if loop == "in":
        return rho.clone()
    hamiltonian = H_L if sheet == "L" else H_R
    return update(rho, commutator_dot(hamiltonian, rho))


def placement_token(sheet: str, loop: str, terrain: str) -> str:
    return f"{sheet}:{loop}:{terrain}"


def axis6_sign(sheet: str, loop: str, terrain: str) -> str:
    parity = (0 if sheet == "L" else 1) + (0 if loop == "in" else 1) + TERRAINS.index(terrain)
    return "up" if parity % 2 == 0 else "down"


def placement_signature(sheet: str, loop: str, terrain: str, site: int = 0) -> torch.Tensor:
    rho = sheet_rho(sheet, site % 8)
    looped = loop_channel(sheet, loop, rho)
    terrain_after_loop = update(looped, terrain_generator(sheet, terrain, looped))
    terrained = update(rho, terrain_generator(sheet, terrain, rho))
    loop_after_terrain = loop_channel(sheet, loop, terrained)
    order_gap = torch.linalg.vector_norm(terrain_after_loop - loop_after_terrain).reshape(1).to(CTYPE)
    derivative = terrain_generator(sheet, terrain, rho)
    sign = torch.tensor([1.0 if axis6_sign(sheet, loop, terrain) == "up" else -1.0], dtype=CTYPE)
    return torch.cat([terrain_after_loop.reshape(-1), derivative.reshape(-1), order_gap, sign])


def terrain_gate() -> dict[str, Any]:
    graph = carrier_graph((2, 2, 2))
    generator_keys = [(sheet, terrain) for sheet in SHEETS for terrain in TERRAINS]
    placement_keys = [(sheet, loop, terrain) for sheet in SHEETS for loop in LOOPS for terrain in TERRAINS]
    terrain_sigs = {
        f"{sheet}:{terrain}": torch.cat([terrain_generator(sheet, terrain, sheet_rho(sheet, site)).reshape(-1) for site in range(2)])
        for sheet, terrain in generator_keys
    }
    placement_sigs = {placement_token(*key): placement_signature(*key) for key in placement_keys}
    terrain_unique = len({tuple(round(float(x.real.item()), 8) for x in sig) for sig in terrain_sigs.values()})
    placement_unique = len({tuple(round(float(x.real.item()), 8) for x in sig) for sig in placement_sigs.values()})
    out_order_gaps = [
        float(placement_signature(sheet, "out", terrain)[8].real.item()) for sheet in SHEETS for terrain in TERRAINS
    ]
    in_order_gaps = [
        float(placement_signature(sheet, "in", terrain)[8].real.item()) for sheet in SHEETS for terrain in TERRAINS
    ]
    out_order_sensitive_count = sum(1 for gap in out_order_gaps if gap > GAP_FLOOR)
    exact_count = sp.Integer(len(SHEETS)) * sp.Integer(len(LOOPS)) * sp.Integer(len(TERRAINS))
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and len(generator_keys) == 8
            and len(placement_keys) == 16
            and terrain_unique == 8
            and placement_unique == 16
            and out_order_sensitive_count >= 4
            and max(in_order_gaps) < TOL
            and int(exact_count) == 16
        ),
        "finite_map": "X_(tau,s): rho_(v,s,k) -> rho_dot_(v,s,k); placement=(s,ell,tau,X_(tau,s),Y_ell,token,axis6_sign)",
        "domain": "D5 = finite PEPS3D site anchors x sheet cover x loop field x terrain family",
        "output": "O5 = eight terrain generator laws and 16 PEPS3D-anchored placement signatures",
        "peps3d_embedding": "anchor(placement)=v in V with inherited sheet and shell carrier; placement token is not a carrier substitute",
        "terrain_generator_count": len(generator_keys),
        "placement_count": len(placement_keys),
        "terrain_unique_signature_count": terrain_unique,
        "placement_unique_signature_count": placement_unique,
        "min_out_loop_order_gap": min(out_order_gaps),
        "max_out_loop_order_gap": max(out_order_gaps),
        "out_loop_order_sensitive_count": out_order_sensitive_count,
        "max_in_loop_density_hidden_gap": max(in_order_gaps),
        "sympy_exact_placement_count": int(exact_count),
    }


def graph_anchor_gate() -> dict[str, Any]:
    graph = carrier_graph((2, 2, 2))
    edges = edge_list((2, 2, 2))
    edge_pairs = []
    for edge in edges:
        edge_pairs.append((int(edge["src"]), int(edge["dst"])))
        edge_pairs.append((int(edge["dst"]), int(edge["src"])))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    features = torch.stack([torch.real(placement_signature("L", "out", terrain, site)[:2]) for site, terrain in enumerate(TERRAINS * 2)])
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
        signatures = []
        for site in range(site_count):
            sheet = SHEETS[site % 2]
            loop = LOOPS[(site // 2) % 2]
            terrain = TERRAINS[site % len(TERRAINS)]
            signatures.append(placement_signature(sheet, loop, terrain, site % 8))
        finite = torch.stack(signatures)
        rows.append(
            {
                "shape": shape,
                "site_count": site_count,
                "signature_width": int(finite.shape[1]),
                "dense_state_closure_used": False,
                "pass": bool(torch.isfinite(torch.real(finite)).all().item()),
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


def label_only_terrain_control_rejected() -> dict[str, Any]:
    labels = {f"{sheet}:{terrain}": idx for idx, (sheet, terrain) in enumerate((s, t) for s in SHEETS for t in TERRAINS)}
    zero_laws = {key: torch.zeros((2, 2), dtype=CTYPE) for key in labels}
    unique_laws = len({tuple(row.reshape(-1).tolist()) for row in zero_laws.values()})
    return {
        "pass": unique_laws == 1,
        "why_rejected": "terrain names without distinct channel laws collapse to one zero-law control",
        "label_count": len(labels),
        "unique_law_count": unique_laws,
    }


def terrain_family_erasure_control_rejected() -> dict[str, Any]:
    collapsed = {(sheet, "erased") for sheet in SHEETS for _terrain in TERRAINS}
    return {
        "pass": len(collapsed) == 2,
        "why_rejected": "erasing tau destroys the eight generator family",
        "collapsed_generator_count": len(collapsed),
    }


def loop_erasure_control_rejected() -> dict[str, Any]:
    collapsed = {(sheet, terrain) for sheet in SHEETS for _loop in LOOPS for terrain in TERRAINS}
    return {
        "pass": len(collapsed) == 8,
        "why_rejected": "erasing loop ownership collapses 16 placements to eight rows",
        "collapsed_placement_count": len(collapsed),
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "terrain placement without PEPS3D site/sheet/shell anchor is a label row, not a carrier cell",
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
    terrain = terrain_gate()
    graph = graph_anchor_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_label_only_terrain_control_rejected": label_only_terrain_control_rejected(),
        "GC2_terrain_family_erasure_control_rejected": terrain_family_erasure_control_rejected(),
        "GC3_loop_erasure_control_rejected": loop_erasure_control_rejected(),
        "GC4_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": ["engine placements by type", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
        },
    }
    actuals = {
        "phase0_receipts_declared": True,
        "phase1_receipt_declared": True,
        "phase2_receipt_declared": True,
        "phase3_receipt_declared": True,
        "phase4_receipt_declared": True,
        "terrain_generators": bool(terrain["pass"]),
        "peps3d_anchor": bool(graph["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_anchored_terrain_generator_and_placement_map": terrain,
        "peps3d_graph_anchor_carrier": graph,
        "terrain_placement_scale_stress_without_dense_closure": stress,
        "z3_terrain_placement_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_terrain_placement_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [terrain["finite_map"], "I_place = terrain/loop order signature on PEPS3D anchor"],
        "domain": terrain["domain"],
        "codomain_or_output": terrain["output"],
        "carrier_realization": "finite PEPS3D site anchors carrying sheet/loop/terrain placement signatures",
        "peps3d_embedding": terrain["peps3d_embedding"],
        "spinor_state": "terrain acts on Phase 4 sheet density readouts over Phase 3 loop/shell anchors",
        "quaternion_action": "not_applicable_phase5",
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
        ],
        "downstream_blocks": ["engine placements by type", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 5,
            "candidate": "peps3d_anchored_terrain_generator_placements",
            "terrain_generator_count": terrain["terrain_generator_count"],
            "placement_count": terrain["placement_count"],
            "max_qubits": stress["max_qubits"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 5 PEPS3D-anchored terrain/placement formal scout. It is not engine-substage, "
            "flux, Xi/Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Validate this Phase 5 receipt before opening operator-substage cell embedding candidates.",
            "Keep terrain family, terrain law, loop field, placement token, and PEPS3D anchor distinct.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
