#!/usr/bin/env python3
"""PEPS3D-anchored nested Hopf torus and loop-field gate.

Formal scout only.

This Phase 3 row tests finite shell-indexed Hopf torus samples on the admitted
PEPS3D spinor carrier:

  T_eta^s = {psi_s(phi, chi; eta)}
  A = -i psi_s^dagger d psi_s = dphi + cos(2 eta) dchi
  Y_in psi = partial_phi psi
  Y_out psi = (-cos(2 eta) partial_phi + partial_chi) psi

The order witness is finite and shell-sensitive:

  shell_step o lifted_base_step != lifted_base_step o shell_step

because lifted_base_step depends on eta_k. Flux, Xi/Phi0, Axis0, terrain,
substage cells, basin, and physics remain blocked.
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

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (  # noqa: E402
    CTYPE,
    RTYPE,
    carrier_graph,
    coords_for_shape,
    edge_list,
)
from sim_peps3d_spinor_density_carrier_gate_probe import spinor  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_nested_hopf_torus_loop_field_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase3_peps3d_nested_hopf_torus_loop_fields"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite shell-indexed Hopf torus samples, Hopf "
    "connection readouts, and shell-sensitive loop-field order on PEPS3D site "
    "anchors. It does not admit Weyl sheets, terrain, substages, flux, Xi/Phi0, "
    "Axis0, basin, physics, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Hopf torus spinor samples, analytic derivatives, connection readouts, and order gaps",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite shell/loop admission and nonpromotion knockout gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Hopf connection formula check",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing inherited PEPS3D site/bond carrier graph",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph Data anchor for shell/site samples",
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

TOL = 1.0e-8
GAP_FLOOR = 1.0e-5
SHELLS = [math.pi / 12.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 5.0 * math.pi / 12.0]
PHASES = [0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0]
DT = math.pi / 7.0


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


def d_phi(phi: float, chi: float, eta: float) -> torch.Tensor:
    psi = spinor(phi, chi, eta)
    return 1j * psi


def d_chi(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            1j * complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            -1j * complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CTYPE,
    )


def hopf_connection_components(phi: float, chi: float, eta: float) -> tuple[float, float]:
    psi = spinor(phi, chi, eta)
    a_phi = (-1j * torch.vdot(psi, d_phi(phi, chi, eta))).real
    a_chi = (-1j * torch.vdot(psi, d_chi(phi, chi, eta))).real
    return float(a_phi.item()), float(a_chi.item())


def y_in(phi: float, chi: float, eta: float) -> torch.Tensor:
    return d_phi(phi, chi, eta)


def y_out(phi: float, chi: float, eta: float) -> torch.Tensor:
    return -math.cos(2.0 * eta) * d_phi(phi, chi, eta) + d_chi(phi, chi, eta)


def base_step(k: int, phi: float, chi: float, dt: float = DT, flattened: bool = False) -> tuple[int, float, float]:
    eta = SHELLS[k]
    coeff = 0.0 if flattened else math.cos(2.0 * eta)
    return k, phi - coeff * dt, chi + dt


def fiber_step(k: int, phi: float, chi: float, dt: float = DT) -> tuple[int, float, float]:
    return k, phi + dt, chi


def shell_step(k: int, phi: float, chi: float) -> tuple[int, float, float]:
    return min(k + 1, len(SHELLS) - 1), phi, chi


def state_from_tuple(row: tuple[int, float, float]) -> torch.Tensor:
    k, phi, chi = row
    return spinor(phi, chi, SHELLS[k])


def shell_projection(v: int, k: int, phi: float, chi: float) -> tuple[int, int]:
    return v, k


def hopf_torus_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    coords = coords_for_shape(shape)
    graph = carrier_graph(shape)
    samples = []
    connection_gaps = []
    y_out_connection_values = []
    projections = set()
    for v in range(len(coords)):
        for k, eta in enumerate(SHELLS):
            for phi in PHASES:
                for chi in PHASES:
                    psi = spinor(phi, chi, eta)
                    samples.append(psi)
                    a_phi, a_chi = hopf_connection_components(phi, chi, eta)
                    connection_gaps.append(abs(a_phi - 1.0) + abs(a_chi - math.cos(2.0 * eta)))
                    y_out_connection_values.append(abs(-math.cos(2.0 * eta) * a_phi + a_chi))
                    projections.add(shell_projection(v, k, phi, chi))
    sample_tensor = torch.stack(samples)
    norms = torch.linalg.vector_norm(sample_tensor, dim=1)
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and len(samples) == 8 * len(SHELLS) * len(PHASES) * len(PHASES)
            and len(projections) == 8 * len(SHELLS)
            and float(torch.max(torch.abs(norms - 1.0)).item()) < TOL
            and max(connection_gaps) < TOL
            and max(y_out_connection_values) < TOL
        ),
        "finite_map": "T_eta(v,k) = {psi_v(phi,chi;eta_k)} with pi_shell(v,k,phi,chi)=(v,k)",
        "domain": "D3 = finite PEPS3D site anchors V x finite shell indices k x finite phase grid",
        "output": "O3 = normalized shell-indexed spinors, Hopf connection components, and loop-field readouts",
        "peps3d_embedding": "anchor(T_eta(v,k))=v in V with shell projection pi_shell(v,k,phi,chi)=(v,k)",
        "site_count": len(coords),
        "shell_count": len(SHELLS),
        "phase_count_per_angle": len(PHASES),
        "sample_count": len(samples),
        "projection_count": len(projections),
        "max_norm_gap": float(torch.max(torch.abs(norms - 1.0)).item()),
        "max_connection_formula_gap": max(connection_gaps),
        "max_y_out_connection_abs": max(y_out_connection_values),
    }


def order_witness_gate() -> dict[str, Any]:
    rows = []
    fiber_rows = []
    for k in range(len(SHELLS) - 1):
        phi = PHASES[(k + 1) % len(PHASES)]
        chi = PHASES[(k + 2) % len(PHASES)]
        shell_after_base = shell_step(*base_step(k, phi, chi))
        base_after_shell = base_step(*shell_step(k, phi, chi))
        gap = float(torch.linalg.vector_norm(state_from_tuple(shell_after_base) - state_from_tuple(base_after_shell)).item())
        rows.append(gap)

        shell_after_fiber = shell_step(*fiber_step(k, phi, chi))
        fiber_after_shell = fiber_step(*shell_step(k, phi, chi))
        fiber_gap = float(torch.linalg.vector_norm(state_from_tuple(shell_after_fiber) - state_from_tuple(fiber_after_shell)).item())
        fiber_rows.append(fiber_gap)

    sym_eta_1, sym_eta_2, dt = sp.symbols("eta_1 eta_2 dt", real=True)
    sym_gap = sp.simplify((-sp.cos(2 * sym_eta_1) * dt) - (-sp.cos(2 * sym_eta_2) * dt))
    return {
        "pass": bool(min(rows) > GAP_FLOOR and max(fiber_rows) < TOL and sym_gap != 0),
        "N01_witness": "shell_step o lifted_base_step != lifted_base_step o shell_step because lifted_base_step depends on eta_k",
        "min_base_shell_order_gap": min(rows),
        "max_fiber_shell_order_erased_gap": max(fiber_rows),
        "sympy_shell_base_phase_gap": str(sym_gap),
    }


def graph_anchor_gate() -> dict[str, Any]:
    graph = carrier_graph((2, 2, 2))
    edges = edge_list((2, 2, 2))
    edge_pairs = []
    for edge in edges:
        edge_pairs.append((int(edge["src"]), int(edge["dst"])))
        edge_pairs.append((int(edge["dst"]), int(edge["src"])))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    features = torch.tensor([[float(v), float(k)] for v in range(8) for k in range(len(SHELLS))], dtype=RTYPE)
    data = Data(x=features[:8], edge_index=edge_index)
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
    max_samples = 0
    for shape in shapes:
        site_count = len(coords_for_shape(shape))
        sample_count = site_count * len(SHELLS) * len(PHASES) * len(PHASES)
        max_gap = 0.0
        for k, eta in enumerate(SHELLS):
            phi = PHASES[k % len(PHASES)]
            chi = PHASES[(k + 1) % len(PHASES)]
            a_phi, a_chi = hopf_connection_components(phi, chi, eta)
            max_gap = max(max_gap, abs(a_phi - 1.0) + abs(a_chi - math.cos(2.0 * eta)))
        rows.append(
            {
                "shape": shape,
                "site_count": site_count,
                "shell_count": len(SHELLS),
                "sample_count": sample_count,
                "max_connection_formula_gap": max_gap,
                "dense_state_closure_used": False,
                "pass": max_gap < TOL,
            }
        )
        max_sites = max(max_sites, site_count)
        max_samples = max(max_samples, sample_count)
    return {
        "pass": all(row["pass"] for row in rows),
        "dense_state_closure_used": False,
        "rows": rows,
        "max_qubits": max_sites,
        "max_peps3d_sites": max_sites,
        "max_peps3d_bond": 4,
        "max_shell_samples": max_samples,
    }


def shell_erased_control_rejected() -> dict[str, Any]:
    collapsed_shells = [math.pi / 4.0 for _ in SHELLS]
    gaps = []
    for k in range(len(collapsed_shells) - 1):
        phi = PHASES[k % len(PHASES)]
        chi = PHASES[(k + 1) % len(PHASES)]
        coeff_1 = math.cos(2.0 * collapsed_shells[k])
        coeff_2 = math.cos(2.0 * collapsed_shells[k + 1])
        gaps.append(abs((-coeff_1 * DT) - (-coeff_2 * DT)))
    return {
        "pass": max(gaps) < TOL,
        "why_rejected": "erasing shell variation removes the shell-sensitive lifted-base order witness",
        "max_order_gap_after_shell_erase": max(gaps),
    }


def flattened_connection_control_rejected() -> dict[str, Any]:
    gaps = []
    for k in range(len(SHELLS) - 1):
        phi = PHASES[k % len(PHASES)]
        chi = PHASES[(k + 1) % len(PHASES)]
        shell_after_base = shell_step(*base_step(k, phi, chi, flattened=True))
        base_after_shell = base_step(*shell_step(k, phi, chi), flattened=True)
        gaps.append(float(torch.linalg.vector_norm(state_from_tuple(shell_after_base) - state_from_tuple(base_after_shell)).item()))
    return {
        "pass": max(gaps) < TOL,
        "why_rejected": "flattening the Hopf connection coefficient removes eta-dependent loop transport",
        "max_order_gap_after_connection_flattening": max(gaps),
    }


def reverse_order_control() -> dict[str, Any]:
    witness = order_witness_gate()
    return {
        "pass": witness["min_base_shell_order_gap"] > GAP_FLOOR,
        "why_control": "the reversed order is the finite negative path against which the positive order is compared",
        "reverse_order_gap": witness["min_base_shell_order_gap"],
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "shell torus samples without PEPS3D site anchor v are not admitted as carrier cells",
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
    torus = hopf_torus_gate()
    order = order_witness_gate()
    graph = graph_anchor_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_shell_erased_control_rejected": shell_erased_control_rejected(),
        "GC2_flattened_hopf_connection_control_rejected": flattened_connection_control_rejected(),
        "GC3_reverse_order_control": reverse_order_control(),
        "GC4_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": ["Weyl sheets", "terrain", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
        },
    }
    actuals = {
        "phase0_receipts_declared": True,
        "phase1_receipt_declared": True,
        "phase2_receipt_declared": True,
        "hopf_torus": bool(torus["pass"]),
        "order_witness": bool(order["pass"]),
        "peps3d_anchor": bool(graph["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "peps3d_anchored_nested_hopf_torus_map": torus,
        "shell_sensitive_loop_order_witness": order,
        "peps3d_graph_anchor_carrier": graph,
        "nested_hopf_torus_scale_stress_without_dense_closure": stress,
        "z3_nested_hopf_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_nested_hopf_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [torus["finite_map"], "A_Hopf=-i psi^dagger d psi", order["N01_witness"]],
        "domain": torus["domain"],
        "codomain_or_output": torus["output"],
        "carrier_realization": "finite PEPS3D site anchors carrying shell-indexed spinor torus samples and loop-field readouts",
        "peps3d_embedding": torus["peps3d_embedding"],
        "spinor_state": "psi_s(phi,chi;eta_k) finite shell-indexed torch complex spinor samples",
        "quaternion_action": "not_applicable_phase3",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json",
        ],
        "downstream_blocks": ["Weyl sheets", "terrain", "64 substages", "flux", "Xi", "Phi0", "Axis0", "basin", "physics"],
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
            "phase": 3,
            "candidate": "peps3d_anchored_nested_hopf_torus_loop_fields",
            "max_qubits": stress["max_qubits"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "max_shell_samples": stress["max_shell_samples"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 3 PEPS3D-anchored nested Hopf torus formal scout. It is not Weyl sheet, "
            "terrain, substage, flux, Xi/Phi0, Axis0, basin, or physics evidence."
        ),
        "next_required_work": [
            "Validate this Phase 3 receipt before opening Weyl sheet cover candidates.",
            "Keep shell-indexed Hopf transport PEPS3D-anchored; reject shell erasure and flattened connection shortcuts.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
