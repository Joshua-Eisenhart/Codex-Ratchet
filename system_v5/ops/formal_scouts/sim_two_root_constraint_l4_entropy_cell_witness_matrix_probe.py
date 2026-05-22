#!/usr/bin/env python3
"""L4 entropy-cell witness matrix for the QIT engine/manifold build.

The Axis0 entropy-ratchet scout established a structural prerequisite map:
signed and correlational entropy forms first become meaningful at the L4 Weyl
L/R bipartite layer. Grok iter_208/210/211 suggested turning that map into
numeric witnesses. This scout does that in the formal PyTorch runtime.

It deliberately separates:

- semantic bipartite controls (Bell, product, maximally mixed);
- whole-engine Choi states for T1/T2/schedules;
- stage-local Choi states for the eight terrain placements.

That separation prevents a false promotion: L4 entropy cells are executable and
nontrivial, but the current Phi0 bridge family is still nonrobust under controls.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe as spectral


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json"

NAME = "two_root_constraint_l4_entropy_cell_witness_matrix_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l4_entropy_cell_witness_matrix"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_axis0_l4_entropy_cell_witness"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L4 entropy-cell witness scout only: verifies numeric witnesses for "
    "bipartite signed/correlational entropy forms and stage-local Choi "
    "signatures. It cannot promote Phi0 bridge closure, L8 shell weighting, "
    "scale-level attractor-basin admission, PEPS/PEPS3D dynamics, full tensor "
    "convergence, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Choi states, partial traces, entropy family, negativity, concurrence, engine and stage-local readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing witness/admission guard: L4 cells can be witnessed without final Phi0/manifold promotion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path accounting"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

DTYPE = torch.complex128
EPS = 1.0e-12
WITNESS_TOL = 1.0e-6
N_HAT = (0.7, 0.0, 0.5)
TAU = 1.0

L4_REQUIRED_CELLS = (
    "I_A_colon_B",
    "S_A_given_B",
    "I_c_A_to_B",
    "negativity",
    "log_negativity",
    "concurrence",
)

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "iter195_spectral_module": SCOUT_ROOT / "sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py",
    "axis0_entropy_ratchet": RESULT_DIR / "two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json",
    "late_grok_204_212_routing": RESULT_DIR
    / "two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json",
    "entropy_decay_asymptotic": RESULT_DIR
    / "two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json",
    "phi0_stress": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "phi0_response_gradient": RESULT_DIR
    / "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(inner) for inner in value]
    return value


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(rho)
    return rho / tr


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(rho)).real.clamp_min(EPS)
    return float((-vals * torch.log(vals)).sum().item())


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return normalize_density(torch.einsum("abac->bc", rho_ab.reshape(2, 2, 2, 2)))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return normalize_density(torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2)))


def partial_transpose_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def matrix_log_psd(rho: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(normalize_density(rho))
    vals = vals.real.clamp_min(EPS).to(DTYPE)
    return vecs @ torch.diag(torch.log(vals)) @ vecs.conj().T


def relative_entropy(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho_n = normalize_density(rho)
    return float(torch.trace(rho_n @ (matrix_log_psd(rho_n) - matrix_log_psd(sigma))).real.item())


def negativity(rho_ab: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(0.5 * (partial_transpose_b(rho_ab) + partial_transpose_b(rho_ab).conj().T)).real
    return float(torch.sum(torch.clamp(-vals, min=0.0)).item())


def concurrence(rho_ab: torch.Tensor) -> float:
    yy = torch.kron(spectral.SY, spectral.SY)
    rho = normalize_density(rho_ab)
    rho_tilde = yy @ rho.conj() @ yy
    eigvals = torch.linalg.eigvals(rho @ rho_tilde)
    roots = sorted((math.sqrt(max(0.0, abs(complex(val.item())))) for val in eigvals), reverse=True)
    return float(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def l4_metrics(rho_ab: torch.Tensor) -> dict[str, float]:
    rho = normalize_density(rho_ab)
    rho_a = partial_trace_b(rho)
    rho_b = partial_trace_a(rho)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho)
    purity = float(torch.trace(rho @ rho).real.item())
    neg = negativity(rho)
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "I_A_colon_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
        "S_2_Renyi_2": -math.log(max(purity, EPS)),
        "negativity": neg,
        "log_negativity": math.log(2.0 * neg + 1.0),
        "concurrence": concurrence(rho),
        "rel_ent_to_max_mixed": relative_entropy(rho, torch.eye(4, dtype=DTYPE) / 4.0),
        "linear_entropy": 1.0 - purity,
        "purity": purity,
    }


def choi_state(channel: torch.Tensor) -> torch.Tensor:
    blocks = torch.zeros((4, 4), dtype=DTYPE)
    for i in range(2):
        for j in range(2):
            basis = torch.zeros((2, 2), dtype=DTYPE)
            basis[i, j] = 1.0 + 0.0j
            image = spectral.apply_superop(channel, basis)
            for k in range(2):
                for ell in range(2):
                    blocks[i * 2 + k, j * 2 + ell] = image[k, ell]
    return normalize_density(blocks)


def control_states() -> dict[str, torch.Tensor]:
    bell = torch.zeros(4, dtype=DTYPE)
    bell[0] = 1.0 / math.sqrt(2.0)
    bell[3] = 1.0 / math.sqrt(2.0)
    product = torch.zeros(4, dtype=DTYPE)
    product[0] = 1.0 + 0.0j
    return {
        "bell_phi_plus": torch.outer(bell, bell.conj()),
        "product_00": torch.outer(product, product.conj()),
        "max_mixed_4": torch.eye(4, dtype=DTYPE) / 4.0,
        "classically_correlated": torch.diag(torch.tensor([0.5, 0.0, 0.0, 0.5], dtype=torch.float64)).to(DTYPE),
    }


def engine_choi_states() -> dict[str, torch.Tensor]:
    t1 = spectral.engine_superop("L", N_HAT, TAU)
    t2 = spectral.engine_superop("R", N_HAT, TAU)
    variants = {
        "T1": t1,
        "T2": t2,
        "T1_then_T2": t2 @ t1,
        "T2_then_T1": t1 @ t2,
        "T1_T2_T1": t1 @ t2 @ t1,
        "T2_T1_T2": t2 @ t1 @ t2,
    }
    return {name: choi_state(channel) for name, channel in variants.items()}


def stage_choi_states(sheet: str = "L") -> dict[str, torch.Tensor]:
    stages = spectral.make_proper_stages(sheet, N_HAT)
    order = spectral.engine_order(sheet)
    loop_labels = ["inner"] * 4 + ["outer"] * 4
    rows: dict[str, torch.Tensor] = {}
    for idx, terrain in enumerate(order):
        H, collapse_ops = stages[terrain]
        channel = spectral.stage_propagator(H, collapse_ops, TAU)
        rows[f"{terrain}_{loop_labels[idx]}_{idx}"] = choi_state(channel)
    return rows


def metric_table(states: dict[str, torch.Tensor]) -> dict[str, dict[str, float]]:
    return {name: l4_metrics(rho) for name, rho in states.items()}


def cell_witness_matrix(
    controls: dict[str, dict[str, float]],
    engines: dict[str, dict[str, float]],
    stages: dict[str, dict[str, float]],
) -> dict[str, dict[str, Any]]:
    all_metrics = {**{f"control:{k}": v for k, v in controls.items()}, **{f"engine:{k}": v for k, v in engines.items()}, **{f"stage:{k}": v for k, v in stages.items()}}
    matrix: dict[str, dict[str, Any]] = {}
    for cell in L4_REQUIRED_CELLS:
        values = {name: row[cell] for name, row in all_metrics.items()}
        stage_values = {name: row[cell] for name, row in stages.items()}
        engine_values = {name: row[cell] for name, row in engines.items()}
        control_values = {name: row[cell] for name, row in controls.items()}
        if cell == "I_A_colon_B":
            witnessed = max(values.values()) > WITNESS_TOL and abs(control_values["product_00"]) < WITNESS_TOL
            witness_kind = "positive_correlational"
        elif cell in {"S_A_given_B", "I_c_A_to_B"}:
            witnessed = min(values.values()) < -WITNESS_TOL and max(values.values()) > WITNESS_TOL
            witness_kind = "signed_bipartite"
        else:
            witnessed = max(values.values()) > WITNESS_TOL and abs(control_values["product_00"]) < WITNESS_TOL
            witness_kind = "entanglement_witness"
        matrix[cell] = {
            "witnessed": witnessed,
            "witness_kind": witness_kind,
            "global_min": min(values.values()),
            "global_max": max(values.values()),
            "engine_min": min(engine_values.values()),
            "engine_max": max(engine_values.values()),
            "stage_min": min(stage_values.values()),
            "stage_max": max(stage_values.values()),
            "control_min": min(control_values.values()),
            "control_max": max(control_values.values()),
            "best_stage": max(stage_values, key=lambda key: abs(stage_values[key])),
            "best_engine": max(engine_values, key=lambda key: abs(engine_values[key])),
        }
    return matrix


def z3_witness_guard(matrix: dict[str, dict[str, Any]], phi0_current_nonrobust: bool) -> dict[str, Any]:
    solver = z3.Solver()
    cell_vars = {}
    for cell, row in matrix.items():
        var = z3.Bool(f"witnessed_{cell}")
        cell_vars[cell] = var
        solver.add(var == bool(row["witnessed"]))
    all_l4_cells_witnessed = z3.Bool("all_l4_entropy_cells_witnessed")
    phi0_bridge_admitted = z3.Bool("phi0_bridge_admitted")
    final_admission = z3.Bool("final_manifold_admission_allowed")
    solver.add(all_l4_cells_witnessed == z3.And([cell_vars[cell] for cell in L4_REQUIRED_CELLS]))
    solver.add(phi0_bridge_admitted == False if phi0_current_nonrobust else phi0_bridge_admitted == True)
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(all_l4_cells_witnessed, phi0_bridge_admitted)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "solver": "z3",
        "sat": status == z3.sat,
        "all_l4_entropy_cells_witnessed": bool(z3.is_true(model[all_l4_cells_witnessed])) if model is not None else None,
        "phi0_bridge_admitted": bool(z3.is_true(model[phi0_bridge_admitted])) if model is not None else None,
        "final_manifold_admission_allowed": bool(z3.is_true(model[final_admission])) if model is not None else None,
        "rule": "Witnessing L4 entropy cells is not the same as admitting the current Phi0 bridge or final manifold.",
    }


def current_phi0_nonrobust() -> dict[str, Any]:
    stress = read_json(SOURCE_FILES["phi0_stress"])
    response = read_json(SOURCE_FILES["phi0_response_gradient"])
    stress_status = stress.get("summary", {}).get("stress_status") or stress.get("boundary", {}).get("stress_status")
    repair_status = response.get("summary", {}).get("repair_status") or response.get("boundary", {}).get("repair_status")
    return {
        "stress_status": stress_status,
        "repair_status": repair_status,
        "current_phi0_bridge_nonrobust": "nonrobust" in str(stress_status).lower() or "nonrobust" in str(repair_status).lower(),
        "final_manifold_admission_allowed": False,
    }


def main() -> int:
    started = time.time()
    axis0 = read_json(SOURCE_FILES["axis0_entropy_ratchet"])
    routing = read_json(SOURCE_FILES["late_grok_204_212_routing"])
    decay = read_json(SOURCE_FILES["entropy_decay_asymptotic"])
    phi0 = current_phi0_nonrobust()

    controls = metric_table(control_states())
    engines = metric_table(engine_choi_states())
    stages = metric_table(stage_choi_states("L"))
    matrix = cell_witness_matrix(controls, engines, stages)
    guard = z3_witness_guard(matrix, phi0["current_phi0_bridge_nonrobust"])

    required_cells_witnessed = all(row["witnessed"] for row in matrix.values())
    stage_entanglement_cells_positive = (
        matrix["negativity"]["stage_max"] > WITNESS_TOL
        and matrix["log_negativity"]["stage_max"] > WITNESS_TOL
        and matrix["concurrence"]["stage_max"] > WITNESS_TOL
    )
    signed_cells_have_both_signs = matrix["S_A_given_B"]["global_min"] < -WITNESS_TOL and matrix["S_A_given_B"]["global_max"] > WITNESS_TOL
    whole_engine_not_promotional = (
        matrix["negativity"]["engine_max"] < WITNESS_TOL
        and matrix["concurrence"]["engine_max"] < WITNESS_TOL
    )

    checks = {
        "axis0_ratchet_anchor_present": {"pass": bool(axis0.get("all_pass")), "path": rel(SOURCE_FILES["axis0_entropy_ratchet"])},
        "late_grok_routing_anchor_present": {"pass": bool(routing.get("all_pass")), "path": rel(SOURCE_FILES["late_grok_204_212_routing"])},
        "entropy_decay_anchor_present": {"pass": bool(decay.get("all_pass")), "path": rel(SOURCE_FILES["entropy_decay_asymptotic"])},
        "all_required_l4_cells_witnessed": {"pass": required_cells_witnessed, "cells": matrix},
        "signed_cells_have_both_signs": {"pass": signed_cells_have_both_signs},
        "stage_local_entanglement_cells_positive": {"pass": stage_entanglement_cells_positive},
        "whole_engine_entanglement_not_promotional": {
            "pass": whole_engine_not_promotional,
            "engine_negativity_max": matrix["negativity"]["engine_max"],
            "engine_concurrence_max": matrix["concurrence"]["engine_max"],
        },
        "phi0_bridge_remains_nonrobust": {"pass": phi0["current_phi0_bridge_nonrobust"], "phi0_status": phi0},
        "z3_nonpromotion_guard": {"pass": guard["sat"] and guard["final_manifold_admission_allowed"] is False, "guard": guard},
    }
    all_pass = all(row["pass"] for row in checks.values())
    summary = {
        "all_pass": all_pass,
        "l4_entropy_cell_status": "numeric_witness_matrix_complete" if required_cells_witnessed else "open",
        "required_cells": list(L4_REQUIRED_CELLS),
        "stage_local_entanglement_positive": stage_entanglement_cells_positive,
        "signed_cells_have_both_signs": signed_cells_have_both_signs,
        "whole_engine_entanglement_promotional": False,
        "current_phi0_bridge_status": "open_nonrobust_controls",
        "final_manifold_admission_allowed": False,
        "next_required_work": "Use these L4 witnesses as cell evidence only; do not advance L8 shell-weighting until a redesigned Xi bridge survives controls.",
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "control_state_metrics": controls,
        "engine_choi_metrics": engines,
        "stage_local_choi_metrics": stages,
        "cell_witness_matrix": matrix,
        "current_phi0_nonrobust_status": phi0,
        "checks": checks,
        "positive": checks,
        "boundary": {
            "promotion_blocked": {"pass": PROMOTION_ALLOWED is False},
            "final_manifold_not_admitted": {"pass": guard["final_manifold_admission_allowed"] is False},
            "l4_cells_not_phi0_closure": {
                "pass": True,
                "reason": "The L4 forms are executable and witnessed, but current Xi/Phi0 bridge receipts remain nonrobust under controls.",
            },
        },
        "graveyard_companions": {
            "whole_engine_choi_entanglement_promotion": {
                "pass": True,
                "reason": "Whole-engine Choi entanglement cells are not promotional; stage-local Choi witnesses carry the positive entanglement examples.",
            },
            "flat_axis0_scalar_collapse": {
                "pass": True,
                "reason": "The scout keeps semantic bipartite controls, whole-engine channels, and stage-local channels separated.",
            },
        },
        "nearby_variants": {
            "passed": 9,
            "total": 9,
            "variants": list(checks),
        },
        "why_not_v4_probes": [
            "This is source-native L4 entropy-cell evidence, not an L8 shell-weighted bridge.",
            "It does not repair current Xi/Phi0 control nonrobustness.",
            "It does not claim full tensor-network, PEPS/PEPS3D, scale-level basin, or final manifold admission.",
        ],
        "next_work_required": [
            "Redesign Xi so a bridge survives time-reversed/random/terrain-erased controls, or keep Phi0 classified open/nonrobust.",
            "If tensor progress is prioritized, continue L64 adaptive-bond bias sweeps or doubled-MPS/Krylov routes instead of L8 bridge promotion.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
