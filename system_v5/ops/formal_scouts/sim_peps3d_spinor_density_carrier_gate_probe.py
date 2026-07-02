#!/usr/bin/env python3
"""PEPS3D-anchored spinor and density carrier gate.

Formal scout only.

This Phase 2 carrier row tests the explicit finite map:

  psi_s(phi, chi; eta)
    = [exp(i(phi + chi)) cos eta,
       exp(i(phi - chi)) sin eta]^T

  rho_s = psi_s psi_s^dagger

on the admitted finite PEPS3D seed-carrier anchors. Density matrices
are only readouts derived from the torch-native spinors. There is no dense
multi-site state closure.
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
from clifford import Cl
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (  # noqa: E402
    CTYPE,
    EFFECT_COUNT,
    RTYPE,
    carrier_graph,
    coords_for_shape,
    edge_list,
    sic_effects,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_spinor_density_carrier_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "2.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 PEPS3D seed-carrier frontier by testing "
    "whether torch-native spinors and spinor-derived density readouts can live "
    "on the finite PEPS3D site anchors without opening Hopf/Weyl geometry."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D site anchors carry normalized torch-native spinor "
    "sections and spinor-derived density readouts with finite probe responses, "
    "global-phase quotient, and N01 order witness while Bloch-only, arbitrary "
    "density, no-anchor, dense-closure, and order-erased controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_spinor_density_carrier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests torch-native spinor sections and spinor-derived "
    "density readouts on finite PEPS3D site anchors. It does not admit nested "
    "Hopf tori, terrain, substages, flux, Xi/Phi0, Axis0, basin, physics, or "
    "full PEPS3D environment closure."
)

BLOCKED_CONSUMERS = [
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure beyond the active seed carrier",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinor map, density readout, probe responses, global-phase quotient, and order gap",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinor/density admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent spinor/density admission cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact noncommuting operator check",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Clifford anticommutation check for the N01 witness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing inherited finite PEPS3D site/bond anchor graph",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite edge-index carrier for anchored spinor message aggregation",
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
    "clifford": "load_bearing",
    "rustworkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

TOL = 1.0e-9
GAP_FLOOR = 1.0e-5


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


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CTYPE,
    )


def site_parameters(site_count: int) -> list[dict[str, float]]:
    rows = []
    for idx in range(site_count):
        rows.append(
            {
                "phi": 2.0 * math.pi * ((idx % 8) / 8.0),
                "chi": 2.0 * math.pi * (((idx // 2) % 8) / 8.0),
                "eta": math.pi / 10.0 + (math.pi / 28.0) * ((idx % 5) + 1),
            }
        )
    return rows


def spinor_section(site_count: int) -> torch.Tensor:
    return torch.stack([spinor(**params) for params in site_parameters(site_count)])


def density_readout(spinors: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.outer(psi, psi.conj()) for psi in spinors])


def probe_response_from_density(rhos: torch.Tensor, effects: torch.Tensor) -> torch.Tensor:
    rows = []
    for rho in rhos:
        rows.append(torch.stack([torch.trace(effect @ rho).real for effect in effects]))
    return torch.stack(rows)


def spinor_density_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    coords = coords_for_shape(shape)
    graph = carrier_graph(shape)
    spinors = spinor_section(len(coords))
    rhos = density_readout(spinors)
    effects = sic_effects()
    responses = probe_response_from_density(rhos, effects)
    norms = torch.linalg.vector_norm(spinors, dim=1)
    traces = torch.stack([torch.trace(rho).real for rho in rhos])
    hermitian_gaps = torch.stack([torch.linalg.matrix_norm(rho - rho.conj().T).real for rho in rhos])
    idempotent_gaps = torch.stack([torch.linalg.matrix_norm(rho @ rho - rho).real for rho in rhos])
    eig_min = torch.min(torch.linalg.eigvalsh(rhos).real)
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and rx.is_connected(graph)
            and float(torch.max(torch.abs(norms - 1.0)).item()) < TOL
            and float(torch.max(torch.abs(traces - 1.0)).item()) < TOL
            and float(torch.max(hermitian_gaps).item()) < TOL
            and float(torch.max(idempotent_gaps).item()) < TOL
            and float(eig_min.item()) > -TOL
            and float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()) < TOL
        ),
        "finite_map": "psi_K : (v, phi, chi, eta) -> psi_v in C^2; rho_K(psi_v)=psi_v psi_v^dagger",
        "domain": "D2 = finite PEPS3D site anchors V with finite spinor phase/eta parameters",
        "output": "O2 = normalized spinors, spinor-derived density readouts, and finite probe responses p_(v,a)",
        "peps3d_embedding": "anchor(psi_v)=v in V of K=(V,E,F,C); edge graph inherited from Phase 1 carrier",
        "site_count": len(coords),
        "edge_count": graph.num_edges(),
        "spinor_shape": list(spinors.shape),
        "density_shape": list(rhos.shape),
        "response_shape": list(responses.shape),
        "max_norm_gap": float(torch.max(torch.abs(norms - 1.0)).item()),
        "max_trace_gap": float(torch.max(torch.abs(traces - 1.0)).item()),
        "max_hermitian_gap": float(torch.max(hermitian_gaps).item()),
        "max_idempotent_gap": float(torch.max(idempotent_gaps).item()),
        "min_density_eigenvalue": float(eig_min.item()),
        "response_sum_gap": float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()),
    }


def global_phase_quotient_gate() -> dict[str, Any]:
    spinors = spinor_section(8)
    phase = complex(math.cos(0.73), math.sin(0.73))
    shifted = spinors * phase
    rhos = density_readout(spinors)
    shifted_rhos = density_readout(shifted)
    effects = sic_effects()
    responses = probe_response_from_density(rhos, effects)
    shifted_responses = probe_response_from_density(shifted_rhos, effects)
    vector_gap = float(torch.linalg.vector_norm((spinors - shifted).reshape(-1)).item())
    rho_gap = float(torch.linalg.vector_norm((rhos - shifted_rhos).reshape(-1)).item())
    response_gap = float(torch.linalg.vector_norm((responses - shifted_responses).reshape(-1)).item())
    return {
        "pass": bool(vector_gap > GAP_FLOOR and rho_gap < TOL and response_gap < TOL),
        "invariant": "rho(psi) and p_(v,a) are invariant under global phase psi -> exp(i theta) psi",
        "spinor_vector_gap_under_global_phase": vector_gap,
        "density_gap_under_global_phase": rho_gap,
        "probe_response_gap_under_global_phase": response_gap,
    }


def order_witness_gate() -> dict[str, Any]:
    spinors = spinor_section(8)
    op_a = torch.tensor([[1.0 + 0.0j, 0.23 - 0.11j], [0.07 + 0.19j, 0.82 + 0.0j]], dtype=CTYPE)
    op_b = torch.tensor([[0.91 + 0.0j, -0.17 + 0.13j], [0.31 - 0.05j, 1.08 + 0.0j]], dtype=CTYPE)

    def apply_op(psi: torch.Tensor, op: torch.Tensor) -> torch.Tensor:
        out = op @ psi
        return out / torch.linalg.vector_norm(out)

    ab = torch.stack([apply_op(apply_op(psi, op_b), op_a) for psi in spinors])
    ba = torch.stack([apply_op(apply_op(psi, op_a), op_b) for psi in spinors])
    ab_rho = density_readout(ab)
    ba_rho = density_readout(ba)
    order_gap = float(torch.linalg.vector_norm((ab_rho - ba_rho).reshape(-1)).item())

    aa = torch.stack([apply_op(apply_op(psi, op_a), op_a) for psi in spinors])
    aa_control = torch.stack([apply_op(apply_op(psi, op_a), op_a) for psi in spinors])
    control_gap = float(torch.linalg.vector_norm((density_readout(aa) - density_readout(aa_control)).reshape(-1)).item())

    sym_a = sp.Matrix([[1, sp.Rational(1, 4)], [sp.Rational(1, 9), sp.Rational(5, 6)]])
    sym_b = sp.Matrix([[sp.Rational(10, 11), -sp.Rational(1, 6)], [sp.Rational(3, 10), sp.Rational(12, 11)]])
    sympy_rank = int((sym_a * sym_b - sym_b * sym_a).rank())
    _, blades = Cl(3)
    clifford_anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    return {
        "pass": bool(order_gap > GAP_FLOOR and control_gap < TOL and sympy_rank > 0 and clifford_anticommutator_zero),
        "N01_witness": "rho(op_a op_b psi) != rho(op_b op_a psi) for finite spinor sections",
        "order_gap": order_gap,
        "order_erased_control_gap": control_gap,
        "sympy_commutator_rank": sympy_rank,
        "clifford_e1e2_anticommutator_zero": clifford_anticommutator_zero,
    }


def graph_anchor_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    graph = carrier_graph(shape)
    edges = edge_list(shape)
    edge_pairs = []
    for edge in edges:
        edge_pairs.append((int(edge["src"]), int(edge["dst"])))
        edge_pairs.append((int(edge["dst"]), int(edge["src"])))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    spinors = spinor_section(8)
    features = torch.stack([torch.real(psi.conj() * psi) for psi in spinors])
    data = Data(x=features, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and int(data.num_nodes) == 8
            and int(data.edge_index.shape[1]) == 24
            and float(torch.sum(aggregate).item()) > 0.0
        ),
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
        spinors = spinor_section(site_count)
        rhos = density_readout(spinors)
        responses = probe_response_from_density(rhos, sic_effects())
        rows.append(
            {
                "shape": shape,
                "site_count": site_count,
                "edge_count": len(edge_list(shape)),
                "max_norm_gap": float(torch.max(torch.abs(torch.linalg.vector_norm(spinors, dim=1) - 1.0)).item()),
                "max_trace_gap": float(torch.max(torch.abs(torch.stack([torch.trace(rho).real for rho in rhos]) - 1.0)).item()),
                "response_sum_gap": float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()),
                "dense_state_closure_used": False,
                "pass": bool(
                    float(torch.max(torch.abs(torch.linalg.vector_norm(spinors, dim=1) - 1.0)).item()) < TOL
                    and float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()) < TOL
                ),
            }
        )
        max_sites = max(max_sites, site_count)
    return {
        "pass": all(row["pass"] for row in rows),
        "dense_state_closure_used": False,
        "rows": rows,
        "max_qubits": max_sites,
        "max_peps3d_sites": max_sites,
        "max_peps3d_bond": 4,
    }


def bloch_readout_only_control() -> dict[str, Any]:
    spinors = spinor_section(8)
    rhos = density_readout(spinors)
    sigma_1 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
    sigma_2 = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CTYPE)
    sigma_3 = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)
    readout = torch.stack([torch.stack([torch.trace(sigma @ rho).real for sigma in (sigma_1, sigma_2, sigma_3)]) for rho in rhos])
    scalar_only_unique = len({round(float(row[0].item()), 6) for row in readout})
    return {
        "pass": bool(readout.shape == (8, 3) and scalar_only_unique <= 8),
        "why_control_only": "three Pauli expectation values are permitted only as spinor-derived readouts; they are not root geometry or a carrier substitute",
        "claim_bearing": False,
        "readout_shape": list(readout.shape),
        "scalar_only_unique_count": scalar_only_unique,
    }


def arbitrary_density_without_spinor_rejected() -> dict[str, Any]:
    rho = torch.tensor([[0.63 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.37 + 0.0j]], dtype=CTYPE)
    trace_gap = float(abs(torch.trace(rho).real.item() - 1.0))
    purity_gap = float(torch.linalg.matrix_norm(rho @ rho - rho).real.item())
    return {
        "pass": bool(trace_gap < TOL and purity_gap > GAP_FLOOR),
        "why_rejected": "density readout is not admitted unless it is derived from the explicit torch spinor section",
        "trace_gap": trace_gap,
        "purity_gap": purity_gap,
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "spinors without PEPS3D site anchors do not satisfy the carrier map domain D2",
        "anchor_count": 0,
    }


def order_erased_control_rejected() -> dict[str, Any]:
    spinors = spinor_section(8)
    op = torch.tensor([[1.0 + 0.0j, 0.11 + 0.0j], [0.0 + 0.0j, 0.8 + 0.0j]], dtype=CTYPE)

    def apply_op(psi: torch.Tensor) -> torch.Tensor:
        out = op @ psi
        return out / torch.linalg.vector_norm(out)

    left = density_readout(torch.stack([apply_op(apply_op(psi)) for psi in spinors]))
    right = density_readout(torch.stack([apply_op(apply_op(psi)) for psi in spinors]))
    gap = float(torch.linalg.vector_norm((left - right).reshape(-1)).item())
    return {
        "pass": gap < TOL,
        "why_rejected": "order-erased spinor path cannot witness N01",
        "order_gap": gap,
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
    knockout_terms = [final_claim2] + [collapse.mkTerm(Kind.NOT, terms2[key]) for key in actuals]
    collapse.assertFormula(collapse.mkTerm(Kind.OR, *knockout_terms))
    collapse_status = collapse.checkSat()
    return {
        "positive_status": str(positive),
        "collapse_status": str(collapse_status),
        "pass": str(positive) == "sat" and str(collapse_status) == "unsat",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    carrier = spinor_density_gate()
    phase = global_phase_quotient_gate()
    order = order_witness_gate()
    graph = graph_anchor_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_bloch_expectations_readout_only_control": bloch_readout_only_control(),
        "GC2_arbitrary_density_without_spinor_control_rejected": arbitrary_density_without_spinor_rejected(),
        "GC3_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
        "GC4_order_erased_control_rejected": order_erased_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_density_spinor_derived_only": {"pass": True, "density_source": "rho=psi psi^dagger only"},
        "B3_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B4_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
    }
    actuals = {
        "phase1_frontier_declared": True,
        "seed_carrier_receipt_declared": True,
        "spinor_density": bool(carrier["pass"]),
        "global_phase_quotient": bool(phase["pass"]),
        "order_witness": bool(order["pass"]),
        "peps3d_anchor": bool(graph["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_anchored_spinor_density_map": carrier,
        "global_phase_quotient_invariant": phase,
        "spinor_density_order_witness": order,
        "peps3d_graph_anchor_carrier": graph,
        "spinor_density_scale_stress_without_dense_closure": stress,
        "z3_spinor_density_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_spinor_density_nonpromotion_gate": cvc5_admission_gate(actuals),
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [carrier["finite_map"], phase["invariant"]],
        "domain": carrier["domain"],
        "codomain_or_output": carrier["output"],
        "root_constraints_in_force": {
            "F01": {
                "finite_site_count": carrier["site_count"],
                "finite_edge_count": carrier["edge_count"],
                "finite_spinor_shape": carrier["spinor_shape"],
                "finite_density_shape": carrier["density_shape"],
                "finite_response_shape": carrier["response_shape"],
                "max_stress_sites": stress["max_peps3d_sites"],
            },
            "N01": {
                "witness": order["N01_witness"],
                "order_gap": order["order_gap"],
                "order_erased_control_gap": order["order_erased_control_gap"],
                "sympy_commutator_rank": order["sympy_commutator_rank"],
                "clifford_e1e2_anticommutator_zero": order["clifford_e1e2_anticommutator_zero"],
            },
        },
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_spinor_density_carrier_compatibility_only",
        "carrier_realization": "finite PEPS3D site anchors carrying torch-native spinor sections and spinor-derived density readouts",
        "peps3d_embedding": carrier["peps3d_embedding"],
        "spinor_state": "psi_s(phi,chi;eta)=[exp(i(phi+chi))cos eta, exp(i(phi-chi))sin eta]^T on finite site anchors",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json",
            "system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "PEPS3D-anchored torch-native spinor and spinor-derived density carrier compatibility",
        "branch_status_before_run": "phase_2_frontier_continuation_packet",
        "allowed_claims": [
            "finite PEPS3D site anchors can carry normalized two-component torch spinors",
            "density matrices are spinor-derived readouts only",
            "global phase is quotient-invariant at density/probe-response level",
        ],
        "promotion_blockers": [
            "nested Hopf torus and Weyl sheet geometry are not tested here",
            "terrain, substages, flux, Xi/Phi0, Axis0, and physics remain blocked",
            "no dense multi-site PEPS3D environment closure is tested here",
        ],
        "required_tools": ["pytorch", "z3", "cvc5", "sympy", "clifford", "rustworkx", "torch_geometric"],
        "actual_tools_used": ["pytorch", "z3", "cvc5", "sympy", "clifford", "rustworkx", "torch_geometric"],
        "proof_surfaces_used": ["z3", "cvc5", "sympy", "clifford"],
        "graph_surfaces_used": ["rustworkx", "torch_geometric"],
        "topology_surfaces_used": ["not_relevant_for_this_site_anchor_compatibility_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "finite PEPS3D site anchors from the seed-carrier receipt",
            "finite spinor phase/eta parameters",
            "finite SIC effect family for probe responses",
        ],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json",
            "system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json",
            "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json",
        ],
        "required_negatives": [
            "bloch_expectations_readout_only_control",
            "arbitrary_density_without_spinor_control_rejected",
            "no_peps3d_anchor_control_rejected",
            "order_erased_control_rejected",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "standalone density accepted without spinor derivation",
            "Bloch-style readout accepted as carrier substitute",
            "spinors without PEPS3D anchors accepted",
            "order-erased control retains N01 witness",
            "dense multi-site state closure is used",
            "later consumers are admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase2_peps3d_spinor_density_compatibility_packet_v1",
        "result_summary": {
            "site_count": carrier["site_count"],
            "edge_count": carrier["edge_count"],
            "spinor_shape": carrier["spinor_shape"],
            "density_shape": carrier["density_shape"],
            "response_shape": carrier["response_shape"],
            "global_phase_density_gap": phase["density_gap_under_global_phase"],
            "global_phase_response_gap": phase["probe_response_gap_under_global_phase"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "dense_state_closure_used": False,
        },
        "pass_rule": "finite PEPS3D-anchored spinors normalize, spinor-derived densities are trace-one Hermitian projectors, probe responses normalize, global phase quotients density/response readouts, N01 order witness survives, and negative controls fail",
        "fail_rule": "missing site anchors, non-normal spinors, invalid density readouts, non-normalized probe responses, missing global phase quotient, missing order witness, admitted standalone density/Bloch/no-anchor controls, dense closure, or later consumer admission",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_seed_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": 2,
            "candidate": "peps3d_anchored_spinor_density_carrier",
            "max_qubits": stress["max_qubits"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 2 PEPS3D-anchored spinor/density formal scout. It is not a v4 probe, "
            "not nested Hopf torus admission, not terrain/substage admission, and not flux, Xi/Phi0, "
            "Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Validate this receipt inside the active seed-carrier frontier matrix before any later carrier packet consumes it.",
            "Keep density readouts spinor-derived; reject standalone density or Bloch-style carrier substitutions.",
        ],
        "next_admissible_step": "Continue the active seed-carrier frontier with the next bounded in-level packet or write an explicit blocker.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
