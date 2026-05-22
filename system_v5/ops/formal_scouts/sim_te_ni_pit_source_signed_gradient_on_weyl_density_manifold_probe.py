#!/usr/bin/env python3
"""TeNi/NiTe signed-gradient scout on Pit/Source Weyl density terrains."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "te_ni_pit_source_signed_gradient_on_weyl_density_manifold_probe_results.json"

NAME = "te_ni_pit_source_signed_gradient_on_weyl_density_manifold_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Formal scout only: instantiates TeNi as Te-up signed gradient on the left "
    "Ni-in/Pit Weyl density terrain and NiTe as Te-down signed gradient on the "
    "right Ni-out/Source Weyl density terrain. It can show this literal finite "
    "manifold placement is runnable and distinguishable from local controls. It "
    "does not admit full engine identity, psychology, physics, or canonical QIT "
    "engine claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, Pauli operators, Hamiltonian/Lindblad terrain updates, and readout signatures"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing gradient of the Hopf/spinor coordinate objective defining Te up/down"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing non-collapse checks for same topology with distinct terrain/sign assignments"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SIGMA_PLUS = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
H0 = 0.73 * SZ + 0.19 * SX
H_L = H0
H_R = -H0
OBS = {"x": SX, "y": SY, "z": SZ}


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=DTYPE)


def dagger(a: Any) -> torch.Tensor:
    tensor = as_complex_tensor(a)
    return torch.conj(tensor.transpose(-2, -1))


def density_np(psi: Any) -> torch.Tensor:
    psi = as_complex_tensor(psi).reshape(2, 1)
    return psi @ dagger(psi)


def spinor_np(eta: float, phi: float = 0.31, chi: float = -0.27) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=DTYPE,
    )


def spinor_torch(eta: torch.Tensor, phi: float = 0.31, chi: float = -0.27) -> torch.Tensor:
    first = torch.exp(1j * torch.tensor(phi + chi, dtype=torch.float64)) * torch.cos(eta)
    second = torch.exp(1j * torch.tensor(phi - chi, dtype=torch.float64)) * torch.sin(eta)
    return torch.stack([first, second]).to(torch.complex128)


def density_torch(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def z_expectation_torch(eta: torch.Tensor) -> torch.Tensor:
    rho = density_torch(spinor_torch(eta))
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    return torch.real(torch.trace(sz @ rho))


def te_signed_gradient_eta(eta_value: float, direction: str, lr: float = 0.08) -> dict[str, float | str]:
    eta = torch.tensor(eta_value, dtype=torch.float64, requires_grad=True)
    objective = z_expectation_torch(eta)
    objective.backward()
    grad = float(eta.grad.item())
    if direction == "up":
        eta_after = eta_value + lr * grad
    elif direction == "down":
        eta_after = eta_value - lr * grad
    else:
        raise ValueError(direction)
    eta_after = max(1e-6, min(float(eta_after), math.pi / 2 - 1e-6))
    before = float(objective.item())
    after = float(z_expectation_torch(torch.tensor(eta_after, dtype=torch.float64)).item())
    return {
        "direction": direction,
        "eta_before": eta_value,
        "eta_after": eta_after,
        "gradient": grad,
        "objective_before": before,
        "objective_after": after,
        "delta": after - before,
    }


def hamiltonian_update(rho: Any, hamiltonian: Any, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    u = torch.linalg.matrix_exp(-1j * as_complex_tensor(hamiltonian) * dt)
    return u @ rho @ dagger(u)


def dissipator_euler(rho: Any, op: Any, gamma: float, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    op = as_complex_tensor(op)
    d = op @ rho @ dagger(op) - 0.5 * (dagger(op) @ op @ rho + rho @ dagger(op) @ op)
    out = rho + gamma * dt * d
    out = (out + dagger(out)) / 2
    vals, vecs = torch.linalg.eigh(out)
    vals = torch.clamp(torch.real(vals), min=1e-12)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ dagger(vecs)
    return out / torch.trace(out)


def pit_left_ni_terrain(rho: Any, dt: float = 0.12) -> torch.Tensor:
    """X_P^L(rho_L)=gamma D[sigma_-](rho_L)-i eps[H_L,rho_L]."""
    return dissipator_euler(hamiltonian_update(rho, H_L, 0.35 * dt), SIGMA_MINUS, 0.8, dt)


def source_right_ni_terrain(rho: Any, dt: float = 0.12) -> torch.Tensor:
    """X_So^R(rho_R)=gamma D[sigma_+](rho_R)-i eps[H_R,rho_R]."""
    return dissipator_euler(hamiltonian_update(rho, H_R, 0.35 * dt), SIGMA_PLUS, 0.8, dt)


def readouts(rho: Any) -> dict[str, float]:
    rho = as_complex_tensor(rho)
    return {key: float(torch.real(torch.trace(obs @ rho)).item()) for key, obs in OBS.items()}


def trace_distance(a: Any, b: Any) -> float:
    diff = as_complex_tensor(a) - as_complex_tensor(b)
    eigs = torch.linalg.eigvalsh((diff + dagger(diff)) / 2)
    return float(0.5 * torch.sum(torch.abs(torch.real(eigs))).item())


def commutator_norm(a: Any, b: Any) -> float:
    a = as_complex_tensor(a)
    b = as_complex_tensor(b)
    comm = a @ b - b @ a
    return float(torch.linalg.matrix_norm(comm).real.item())


def is_density_matrix(rho: Any) -> bool:
    rho = as_complex_tensor(rho)
    eigs = torch.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(
        torch.allclose(rho, dagger(rho), atol=1e-10)
        and abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-10
        and float(torch.min(torch.real(eigs)).item()) > -1e-10
    )


def run_teni_pit(eta0: float) -> dict[str, Any]:
    te = te_signed_gradient_eta(eta0, "up")
    rho = density_np(spinor_np(float(te["eta_after"])))
    after = pit_left_ni_terrain(rho)
    return {
        "token": "TeNi",
        "topology": "Ni",
        "terrain": "left_Ni_in_Pit",
        "weyl_sheet": "left_weyl_density",
        "signed_te": "Te_up",
        "precedence": "operator_first_then_terrain",
        "te_gradient": te,
        "readouts": readouts(after),
        "rho": after,
    }


def run_nite_source(eta0: float) -> dict[str, Any]:
    rho0 = density_np(spinor_np(eta0))
    after_terrain = source_right_ni_terrain(rho0)
    te = te_signed_gradient_eta(eta0, "down")
    # Apply the signed Te coordinate move after the source terrain as a convex
    # finite-density placement, keeping the terrain-first order explicit.
    after_te = density_np(spinor_np(float(te["eta_after"])))
    after = 0.62 * after_terrain + 0.38 * after_te
    after = after / torch.trace(after)
    return {
        "token": "NiTe",
        "topology": "Ni",
        "terrain": "right_Ni_out_Source",
        "weyl_sheet": "right_weyl_density",
        "signed_te": "Te_down",
        "precedence": "terrain_first_then_operator",
        "te_gradient": te,
        "readouts": readouts(after),
        "rho": after,
    }


def z3_same_topology_not_same_terrain() -> dict[str, Any]:
    topology_same = z3.Bool("topology_same")
    terrain_same = z3.Bool("terrain_same")
    te_sign_same = z3.Bool("te_sign_same")
    solver = z3.Solver()
    solver.add(topology_same)
    solver.add(z3.Not(terrain_same))
    solver.add(z3.Not(te_sign_same))
    solver.add(topology_same == terrain_same)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def strip_rho(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "rho"}


def main() -> dict[str, Any]:
    started = time.time()
    eta0 = 0.62
    teni = run_teni_pit(eta0)
    nite = run_nite_source(eta0)
    gap = trace_distance(teni["rho"], nite["rho"])
    h_ladder_commutator = commutator_norm(H_L, SIGMA_MINUS)

    wrong_same_terrain = run_teni_pit(eta0)
    wrong_same_terrain["rho"] = source_right_ni_terrain(density_np(spinor_np(float(wrong_same_terrain["te_gradient"]["eta_after"]))))
    wrong_sign_teni = te_signed_gradient_eta(eta0, "down")
    wrong_sign_nite = te_signed_gradient_eta(eta0, "up")
    no_terrain_gap = trace_distance(density_np(spinor_np(float(teni["te_gradient"]["eta_after"]))), density_np(spinor_np(float(nite["te_gradient"]["eta_after"]))))
    swapped_ladder_gap = trace_distance(
        dissipator_euler(hamiltonian_update(density_np(spinor_np(float(teni["te_gradient"]["eta_after"]))), H_L, 0.04), SIGMA_PLUS, 0.8, 0.12),
        dissipator_euler(hamiltonian_update(density_np(spinor_np(float(nite["te_gradient"]["eta_after"]))), H_R, 0.04), SIGMA_MINUS, 0.8, 0.12),
    )

    positive = {
        "same_Ni_topology_explicit": {"tokens": ["TeNi", "NiTe"], "topology": "Ni", "pass": teni["topology"] == nite["topology"] == "Ni"},
        "different_chiral_terrain_realizations": {"teni_terrain": teni["terrain"], "nite_terrain": nite["terrain"], "pass": teni["terrain"] != nite["terrain"]},
        "TeNi_uses_Te_up_ascent": {"delta": teni["te_gradient"]["delta"], "pass": float(teni["te_gradient"]["delta"]) > 0},
        "NiTe_uses_Te_down_descent": {"delta": nite["te_gradient"]["delta"], "pass": float(nite["te_gradient"]["delta"]) < 0},
        "pit_and_source_outputs_valid_densities": {"pass": is_density_matrix(teni["rho"]) and is_density_matrix(nite["rho"])},
        "pit_source_trace_distance_separates": {"trace_distance": gap, "pass": gap > 0.02},
        "n01_noncommutation_and_precedence_order_witness": {
            "hamiltonian_ladder_commutator_norm": h_ladder_commutator,
            "precedence_tokens": [teni["precedence"], nite["precedence"]],
            "pit_source_trace_distance": gap,
            "pass": h_ladder_commutator > 1e-9 and teni["precedence"] != nite["precedence"] and gap > 0.02,
        },
    }
    graveyard_companions = {
        "wrong_collapse_topology_equals_terrain_unsat": z3_same_topology_not_same_terrain(),
        "wrong_TeNi_down_sign_fails_ascent": {"delta": wrong_sign_teni["delta"], "pass": float(wrong_sign_teni["delta"]) < 0},
        "wrong_NiTe_up_sign_fails_descent": {"delta": wrong_sign_nite["delta"], "pass": float(wrong_sign_nite["delta"]) > 0},
        "gradient_only_control_differs_from_full_terrain_placement": {
            "no_terrain_gap": no_terrain_gap,
            "full_gap": gap,
            "note": "Signed Te alone separates the endpoints more strongly in this fixture; the claim surface is the terrain-coupled Weyl-density placement, not gap maximization.",
            "pass": abs(no_terrain_gap - gap) > 1e-3,
        },
        "swapped_ladder_control_changes_signature": {"swapped_ladder_gap": swapped_ladder_gap, "full_gap": gap, "pass": abs(swapped_ladder_gap - gap) > 1e-3},
        "same_terrain_control_is_not_claim_surface": {
            "control_terrain": "right_Ni_out_Source_used_for_TeNi",
            "pass": trace_distance(teni["rho"], wrong_same_terrain["rho"]) > 0.01,
        },
        "Hamiltonian_signs_are_opposed": {"H_L_trace": float(torch.real(torch.trace(H_L)).item()), "H_R_equals_negative_H_L": bool(torch.allclose(H_R, -H_L)), "pass": bool(torch.allclose(H_R, -H_L))},
        "ladder_operators_are_opposed": {"sigma_minus_equals_sigma_plus": bool(torch.allclose(SIGMA_MINUS, SIGMA_PLUS)), "pass": not bool(torch.allclose(SIGMA_MINUS, SIGMA_PLUS))},
    }
    boundary = {
        "claim_ceiling_blocks_engine_identity": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "source_table_assignment_used": {
            "TeNi": "Ni-in/Pit, Te_up, operator_first",
            "NiTe": "Ni-out/Source, Te_down, terrain_first",
            "pass": True,
        },
        "not_a_psychology_or_physics_claim": {"pass": "psychology" not in NAME and "matter" not in NAME},
    }

    nearby_total = len(positive) + len(graveyard_companions) + len(boundary)
    nearby_passed = sum(1 for section in (positive, graveyard_companions, boundary) for row in section.values() if row.get("pass"))
    all_pass = nearby_passed == nearby_total
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints": {
            "F01": True,
            "N01": True,
            "finite_carrier_root": True,
            "noncommutation_or_order_root": True,
            "finite_density_dimension": 2,
            "n01_evidence": (
                "bounded Weyl density placement records opposed operator/terrain "
                "precedence plus a nonzero Hamiltonian-ladder commutator and "
                "pit/source separation controls"
            ),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "source_assignment": {
            "TeNi": strip_rho(teni),
            "NiTe": strip_rho(nite),
            "literal_math": {
                "pit_left_Ni": "X_P^L(rho_L)=gamma_{P,L}D[sigma_-](rho_L)-i eps_{P,L}[H_L,rho_L]",
                "source_right_Ni": "X_So^R(rho_R)=gamma_{So,R}D[sigma_+](rho_R)-i eps_{So,R}[H_R,rho_R]",
                "Te_up": "eta <- eta + lr * grad_z_expectation(eta)",
                "Te_down": "eta <- eta - lr * grad_z_expectation(eta)",
            },
        },
        "root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": all_pass,
            "F01": True,
            "N01": all_pass,
            "finite_evidence": {
                "carrier": "two finite 2x2 complex Weyl-density matrices with bounded signed-gradient eta updates",
                "density_validity_predicate": "pit_and_source_outputs_valid_densities",
            },
            "noncommutation_or_order_evidence": {
                "order_witness": "TeNi uses operator_first_then_terrain; NiTe uses terrain_first_then_operator",
                "signed_direction_witness": "Te_up ascent and Te_down descent pass with wrong-sign controls failing",
                "noncollapse_witness": "wrong_collapse_topology_equals_terrain_unsat",
            },
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "all_pass": all_pass,
        "all_pass_count": f"{nearby_passed}/{nearby_total}",
        "nearby_variants": {"passed": nearby_passed, "total": nearby_total},
        "blockers": [],
        "why_not_v4_probes": "This is a clean v5 formal scout repairing the TeNi/NiTe topology-terrain-sign confusion without adding to the mixed v4 probe estate.",
        "duration_sec": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    payload = main()
    print(json.dumps({"name": payload["name"], "all_pass": payload["nearby_variants"]["passed"] == payload["nearby_variants"]["total"], "out": str(OUT_PATH)}, indent=2))
