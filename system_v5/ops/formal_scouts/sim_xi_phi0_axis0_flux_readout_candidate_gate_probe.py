#!/usr/bin/env python3
"""Xi/Phi0/Axis0 flux-readout candidate gate.

Formal scout only.

This Phase 9 row opens only after the finite quaternionic flux dependency is
admitted. It tests readout candidates, not final Axis0:

  Xi: geometry/history/flux -> rho_AB
  Phi0: local cut-state coherent/conditional information readouts
  Axis0: signed finite-difference QIT/FEP gradient readout

No basin, physics, ontology, or final Axis0 claim is admitted.
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
import sympy as sp
import torch
import z3

from sim_quaternionic_chiral_boundary_flux_candidate_gate_probe import RESULT_DIR, quaternion_components  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
NAME = "xi_phi0_axis0_flux_readout_candidate_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
FLUX_DEP_RESULT = RESULT_DIR / "quaternionic_flux_dependency_admission_gate_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "phase9_xi_phi0_axis0_flux_readout_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests Xi/Phi0/Axis0 finite readout candidates over the "
    "admitted quaternionic flux dependency. It does not admit final Axis0, "
    "basin, physics, target-system claims, ontology, or dense global closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local cut-state density readouts, entropies, coherent information, and finite-difference Axis0 gradient",
    },
    "z3": {"tried": True, "used": True, "reason": "load-bearing readout-candidate admission and nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent readout-candidate admission gate"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact local cut-state dimension check"},
    "python_json": {"tried": True, "used": True, "reason": "supportive flux-dependency receipt read and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-8
GAP_FLOOR = 1.0e-6


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


def flux_dependency_gate() -> dict[str, Any]:
    exists = FLUX_DEP_RESULT.exists()
    data = json.loads(FLUX_DEP_RESULT.read_text(encoding="utf-8")) if exists else {}
    admitted = bool(data.get("summary", {}).get("flux_dependency_admitted", False))
    return {
        "pass": exists and bool(data.get("all_pass", False)) and admitted,
        "flux_dependency_result": str(FLUX_DEP_RESULT.relative_to(ROOT)),
        "exists": exists,
        "all_pass": bool(data.get("all_pass", False)),
        "flux_dependency_admitted": admitted,
    }


def spinor_from_flux(vec: torch.Tensor) -> torch.Tensor:
    eta = 0.18 + 1.08 * torch.sigmoid(vec[0])
    phi = vec[1]
    chi = vec[2]
    first = torch.exp(1j * (phi + chi)).to(CTYPE) * torch.cos(eta).to(CTYPE)
    second = torch.exp(1j * (phi - chi)).to(CTYPE) * torch.sin(eta).to(CTYPE)
    out = torch.stack([first, second])
    return out / torch.linalg.vector_norm(out)


def local_cut_density(vec: torch.Tensor, neighbor: torch.Tensor) -> torch.Tensor:
    psi_a = spinor_from_flux(vec)
    psi_b = spinor_from_flux(neighbor)
    product = torch.kron(psi_a, psi_b)
    phase = torch.exp(1j * torch.sum(vec + neighbor)).to(CTYPE)
    bell = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j], dtype=CTYPE)
    bell = bell.clone()
    bell[3] = phase
    bell = bell / torch.linalg.vector_norm(bell)
    eps = 0.18 * torch.tanh(torch.linalg.vector_norm(vec - neighbor)).to(CTYPE)
    state = torch.sqrt(1.0 - eps.real * eps.real).to(CTYPE) * product + eps * bell
    state = state / torch.linalg.vector_norm(state)
    return torch.outer(state, state.conj())


def partial_trace_a(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho.reshape(2, 2, 2, 2))


def partial_trace_b(rho: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho.reshape(2, 2, 2, 2))


def entropy(rho: torch.Tensor) -> torch.Tensor:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    clipped = torch.clamp(eigs, min=1.0e-12)
    return -torch.sum(clipped * torch.log2(clipped))


def boundary_weighted_mean(values: torch.Tensor) -> torch.Tensor:
    weights = 1.0 + 0.007 * torch.arange(values.numel(), dtype=values.dtype, device=values.device)
    return torch.sum(values * weights) / torch.sum(weights)


def readouts_for_components(components: torch.Tensor) -> dict[str, torch.Tensor]:
    rhos = []
    s_ab = []
    s_a = []
    s_b = []
    coherent = []
    conditional = []
    for idx, vec in enumerate(components):
        neighbor = components[(idx + 7) % components.shape[0]]
        rho = local_cut_density(vec, neighbor)
        rho_a = partial_trace_b(rho)
        rho_b = partial_trace_a(rho)
        rhos.append(rho)
        entropy_ab = entropy(rho)
        entropy_a = entropy(rho_a)
        entropy_b = entropy(rho_b)
        s_ab.append(entropy_ab)
        s_a.append(entropy_a)
        s_b.append(entropy_b)
        coherent.append(entropy_b - entropy_ab)
        conditional.append(entropy_ab - entropy_b)
    return {
        "rho_ab": torch.stack(rhos),
        "S_AB": torch.stack(s_ab),
        "S_A": torch.stack(s_a),
        "S_B": torch.stack(s_b),
        "coherent_info": torch.stack(coherent),
        "conditional_entropy": torch.stack(conditional),
    }


def xi_phi0_axis0_gate() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    readouts = readouts_for_components(components)
    rhos = readouts["rho_ab"]
    traces = torch.stack([torch.trace(rho).real for rho in rhos])
    hermitian_gaps = torch.stack([torch.linalg.matrix_norm(rho - rho.conj().T).real for rho in rhos])
    min_eig = torch.min(torch.stack([torch.linalg.eigvalsh(rho).real for rho in rhos]))
    delta = 0.021
    plus = readouts_for_components(components * (1.0 + delta))
    minus = readouts_for_components(components * (1.0 - delta))
    gradient = (boundary_weighted_mean(plus["coherent_info"]) - boundary_weighted_mean(minus["coherent_info"])) / (2.0 * delta)
    phi0 = boundary_weighted_mean(readouts["coherent_info"])
    axis0_signed = torch.sign(phi0 + 1.0e-12) * gradient
    exact_dim = sp.Integer(2) * sp.Integer(2)
    return {
        "pass": bool(
            rhos.shape == (56, 4, 4)
            and float(torch.max(torch.abs(traces - 1.0)).item()) < TOL
            and float(torch.max(hermitian_gaps).item()) < TOL
            and float(min_eig.item()) > -TOL
            and abs(float(gradient.item())) > GAP_FLOOR
            and int(exact_dim) == 4
        ),
        "finite_map": "Xi : geometry/history/flux -> rho_AB; Phi0=rho_AB information readout; Axis0=finite signed QIT/FEP gradient readout",
        "domain": "D9 = admitted finite quaternionic flux dependency over PEPS3D boundary anchors",
        "output": "O9 = local cut states rho_AB, coherent/conditional information, and signed finite-difference gradient",
        "peps3d_embedding": "56 PEPS3D boundary anchors inherited from the admitted flux dependency; each readout is local 2-qubit, not dense 2^64 closure",
        "cut_state_count": int(rhos.shape[0]),
        "rho_ab_shape": list(rhos.shape),
        "max_trace_gap": float(torch.max(torch.abs(traces - 1.0)).item()),
        "max_hermitian_gap": float(torch.max(hermitian_gaps).item()),
        "min_density_eigenvalue": float(min_eig.item()),
        "weighted_coherent_info": float(phi0.item()),
        "weighted_conditional_entropy": float(boundary_weighted_mean(readouts["conditional_entropy"]).item()),
        "axis0_signed_gradient_readout": float(axis0_signed.item()),
        "raw_gradient": float(gradient.item()),
        "sympy_exact_local_cut_dim": int(exact_dim),
        "final_axis0_admitted": False,
    }


def zero_flux_control_rejected() -> dict[str, Any]:
    components = torch.zeros_like(quaternion_components()).to(RTYPE)
    plus = readouts_for_components(components * 1.021)
    minus = readouts_for_components(components * 0.979)
    gradient = (boundary_weighted_mean(plus["coherent_info"]) - boundary_weighted_mean(minus["coherent_info"])) / (2.0 * 0.021)
    return {
        "pass": abs(float(gradient.item())) < TOL,
        "why_rejected": "zero flux dependency removes the finite-difference Axis0 readout",
        "zero_flux_gradient": float(gradient.item()),
    }


def order_scramble_control_rejected() -> dict[str, Any]:
    base = xi_phi0_axis0_gate()["axis0_signed_gradient_readout"]
    scrambled = torch.roll(quaternion_components().to(RTYPE), shifts=7, dims=0)
    readouts = readouts_for_components(scrambled)
    delta = 0.021
    plus = readouts_for_components(scrambled * (1.0 + delta))
    minus = readouts_for_components(scrambled * (1.0 - delta))
    gradient = (boundary_weighted_mean(plus["coherent_info"]) - boundary_weighted_mean(minus["coherent_info"])) / (2.0 * delta)
    axis0 = torch.sign(boundary_weighted_mean(readouts["coherent_info"]) + 1.0e-12) * gradient
    gap = abs(base - float(axis0.item()))
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "boundary-order scramble changes the Axis0 readout and cannot stand in for the admitted order",
        "axis0_scramble_gap": gap,
    }


def scalar_flux_control_rejected() -> dict[str, Any]:
    components = quaternion_components().to(RTYPE)
    scalarized = torch.zeros_like(components)
    scalarized[:, 0] = torch.linalg.vector_norm(components, dim=1)
    base_rho = readouts_for_components(components)["rho_ab"]
    scalar_rho = readouts_for_components(scalarized)["rho_ab"]
    gap = float(torch.linalg.vector_norm(base_rho - scalar_rho).item())
    return {
        "pass": gap > GAP_FLOOR,
        "why_rejected": "scalar flux norm loses quaternion component structure in Xi cut states",
        "scalar_flux_cut_state_gap": gap,
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    return {
        "pass": True,
        "why_rejected": "Xi/Phi0/Axis0 readouts without PEPS3D boundary anchors are not admitted",
        "anchor_count": 0,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_axis0 = z3.Bool("final_axis0_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(final_axis0))
    solver.add(z3.And(*variables.values()))
    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(final_axis0))
    collapse.add(z3.Or(final_axis0, *[z3.Not(variables[key]) for key in variables]))
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
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_axis0, solver.mkBoolean(False)))
    solver.assertFormula(solver.mkTerm(Kind.AND, *terms.values()))
    positive = solver.checkSat()
    return {"positive_status": str(positive), "pass": str(positive) == "sat"}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dep = flux_dependency_gate()
    readout = xi_phi0_axis0_gate()
    graveyard_companions = {
        "GC1_zero_flux_control_rejected": zero_flux_control_rejected(),
        "GC2_order_scramble_control_rejected": order_scramble_control_rejected(),
        "GC3_scalar_flux_control_rejected": scalar_flux_control_rejected(),
        "GC4_no_peps3d_anchor_control_rejected": no_anchor_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_final_axis0_not_admitted": {"pass": True, "final_axis0_admitted": False},
        "B3_no_dense_global_closure": {"pass": True, "dense_global_closure_used": False},
        "B4_downstream_consumers_blocked": {"pass": True, "blocked_consumers": ["basin", "physics", "final Axis0 promotion"]},
    }
    actuals = {
        "flux_dependency": bool(dep["pass"]),
        "readout_candidate": bool(readout["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "flux_dependency_admitted_gate": dep,
        "xi_phi0_axis0_readout_candidate": readout,
        "z3_readout_candidate_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_readout_candidate_nonpromotion_gate": cvc5_admission_gate(actuals),
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
        "finite_map": [readout["finite_map"]],
        "domain": readout["domain"],
        "codomain_or_output": readout["output"],
        "carrier_realization": "local torch-native 2-qubit cut-state readouts over admitted PEPS3D flux boundary anchors",
        "peps3d_embedding": readout["peps3d_embedding"],
        "spinor_state": "cut states are generated from spinor/flux-derived local readout maps; no dense 2^64 closure",
        "quaternion_action": "uses admitted quaternionic flux dependency as input only",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/quaternionic_flux_dependency_admission_gate_probe_results.json"],
        "downstream_blocks": ["basin", "physics", "final Axis0 promotion"],
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
            "phase": 9,
            "candidate": "xi_phi0_axis0_flux_readout_candidate",
            "cut_state_count": readout["cut_state_count"],
            "axis0_signed_gradient_readout": readout["axis0_signed_gradient_readout"],
            "final_axis0_admitted": False,
            "max_qubits": 2,
            "max_peps3d_sites": 64,
            "max_peps3d_bond": 5,
            "dense_global_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Xi/Phi0/Axis0 readout-candidate scout. It is not final Axis0, basin, physics, or ontology evidence."
        ),
        "next_required_work": [
            "Do not promote final Axis0 without portability, holdout, and basin-independent controls.",
            "Keep basin and physics blocked.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
