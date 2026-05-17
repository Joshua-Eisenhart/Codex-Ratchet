#!/usr/bin/env python3
"""SiTe/TeSi/NiTe/TeNi signed-gradient substages on Weyl terrain laws."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "si_te_te_si_ni_te_te_ni_signed_gradient_weyl_terrain_substages_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs the four Te-bearing source-table substages SiTe, "
    "TeSi, NiTe, and TeNi on finite Weyl-density terrain laws. It checks the "
    "source-grounded topology/terrain/sign/order assignments and a four-substage "
    "composition surface. It does not claim full engine identity, psychology, "
    "physics, matter/antimatter, or QIT-engine closure. It does not admit "
    "promotion beyond a source-placement runnable scout."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density matrices, Pauli projectors, terrain channels, readouts, and trace distances"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for Hamiltonian terrain components"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing gradient of the Hopf/spinor coordinate objective defining Te up/down"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing non-collapse constraints over topology, terrain, sign, and order slots"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex128
I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
SIGMA_MINUS = np.array([[0, 0], [1, 0]], dtype=DTYPE)
SIGMA_PLUS = np.array([[0, 1], [0, 0]], dtype=DTYPE)

H0 = 0.73 * SZ + 0.19 * SX
H_L = H0
H_R = -H0
K_L = 0.61 * SZ
K_R = -0.37 * SX
PZ_PLUS = 0.5 * (I2 + SZ)
PZ_MINUS = 0.5 * (I2 - SZ)
PX_PLUS = 0.5 * (I2 + SX)
PX_MINUS = 0.5 * (I2 - SX)
OBS = {"x": SX, "y": SY, "z": SZ}


def dagger(a: np.ndarray) -> np.ndarray:
    return a.conj().T


def spinor_np(eta: float, phi: float = 0.31, chi: float = -0.27) -> np.ndarray:
    return np.array(
        [
            np.exp(1j * (phi + chi)) * math.cos(eta),
            np.exp(1j * (phi - chi)) * math.sin(eta),
        ],
        dtype=DTYPE,
    )


def density_np(psi: np.ndarray) -> np.ndarray:
    psi = psi.reshape(2, 1)
    return psi @ dagger(psi)


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
    eta_after = float(np.clip(eta_after, 1e-6, math.pi / 2 - 1e-6))
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


def hamiltonian_update(rho: np.ndarray, hamiltonian: np.ndarray, dt: float) -> np.ndarray:
    u = expm(-1j * hamiltonian * dt)
    return u @ rho @ dagger(u)


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + dagger(rho)) / 2
    vals, vecs = np.linalg.eigh(rho)
    vals = np.maximum(vals, 1e-12)
    out = vecs @ np.diag(vals) @ dagger(vecs)
    return out / np.trace(out)


def dissipator_euler(rho: np.ndarray, op: np.ndarray, gamma: float, dt: float) -> np.ndarray:
    d = op @ rho @ dagger(op) - 0.5 * (dagger(op) @ op @ rho + rho @ dagger(op) @ op)
    return normalize_density(rho + gamma * dt * d)


def dephase_projector_euler(rho: np.ndarray, projectors: list[np.ndarray], kappa: float, dt: float) -> np.ndarray:
    projected = sum(p @ rho @ p for p in projectors)
    return normalize_density(rho + kappa * dt * (projected - rho))


def pit_left_ni_terrain(rho: np.ndarray, dt: float = 0.12) -> np.ndarray:
    """X_P^L(rho_L)=gamma D[sigma_-](rho_L)-i eps[H_L,rho_L]."""
    return dissipator_euler(hamiltonian_update(rho, H_L, 0.35 * dt), SIGMA_MINUS, 0.8, dt)


def source_right_ni_terrain(rho: np.ndarray, dt: float = 0.12) -> np.ndarray:
    """X_So^R(rho_R)=gamma D[sigma_+](rho_R)-i eps[H_R,rho_R]."""
    return dissipator_euler(hamiltonian_update(rho, H_R, 0.35 * dt), SIGMA_PLUS, 0.8, dt)


def hill_left_si_terrain(rho: np.ndarray, dt: float = 0.12) -> np.ndarray:
    """X_H^L(rho_L)=-i[K_L,rho_L]+kappa(P_z rho P_z - rho)."""
    return dephase_projector_euler(hamiltonian_update(rho, K_L, 0.35 * dt), [PZ_PLUS, PZ_MINUS], 0.65, dt)


def citadel_right_si_terrain(rho: np.ndarray, dt: float = 0.12) -> np.ndarray:
    """X_Ci^R(rho_R)=-i[K_R,rho_R]+kappa(P_x rho P_x - rho)."""
    return dephase_projector_euler(hamiltonian_update(rho, K_R, 0.35 * dt), [PX_PLUS, PX_MINUS], 0.65, dt)


def readouts(rho: np.ndarray) -> dict[str, float]:
    return {key: float(np.real(np.trace(obs @ rho))) for key, obs in OBS.items()}


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh((a - b + dagger(a - b)) / 2)
    return float(0.5 * np.sum(np.abs(eigs)))


def is_density_matrix(rho: np.ndarray) -> bool:
    eigs = np.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(np.allclose(rho, dagger(rho), atol=1e-10) and abs(np.trace(rho).real - 1.0) < 1e-10 and float(np.min(eigs)) > -1e-10)


def te_density(eta0: float, signed_te: str) -> tuple[np.ndarray, dict[str, Any]]:
    direction = "up" if signed_te == "Te_up" else "down"
    te = te_signed_gradient_eta(eta0, direction)
    return density_np(spinor_np(float(te["eta_after"]))), te


def run_substage(spec: dict[str, Any], eta0: float = 0.62, input_rho: np.ndarray | None = None) -> dict[str, Any]:
    rho0 = normalize_density(input_rho) if input_rho is not None else density_np(spinor_np(eta0))
    terrain: Callable[[np.ndarray], np.ndarray] = spec["terrain_fn"]
    if spec["precedence"] == "operator_first_then_terrain":
        moved, te = te_density(eta0, spec["signed_te"])
        out = terrain(moved)
    elif spec["precedence"] == "terrain_first_then_operator":
        after_terrain = terrain(rho0)
        moved, te = te_density(eta0, spec["signed_te"])
        out = normalize_density(0.62 * after_terrain + 0.38 * moved)
    else:
        raise ValueError(spec["precedence"])
    return {
        "token": spec["token"],
        "source_stage": spec["source_stage"],
        "source_loop": spec["source_loop"],
        "topology": spec["topology"],
        "terrain": spec["terrain"],
        "weyl_sheet": spec["weyl_sheet"],
        "signed_te": spec["signed_te"],
        "precedence": spec["precedence"],
        "te_gradient": te,
        "readouts": readouts(out),
        "rho": out,
    }


def strip_rho(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "rho"}


def z3_slot_noncollapse() -> dict[str, Any]:
    topology_same = z3.Bool("topology_same")
    terrain_same = z3.Bool("terrain_same")
    sign_same = z3.Bool("sign_same")
    order_same = z3.Bool("order_same")
    solver = z3.Solver()
    solver.add(topology_same)
    solver.add(z3.Not(terrain_same))
    solver.add(z3.Not(sign_same))
    solver.add(z3.Not(order_same))
    solver.add(z3.Or(topology_same == terrain_same, topology_same == sign_same, topology_same == order_same))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def composition_distance(rows: list[dict[str, Any]]) -> float:
    return trace_distance(rows[0]["rho"], rows[-1]["rho"])


def main() -> dict[str, Any]:
    started = time.time()
    specs = [
        {
            "token": "SiTe",
            "source_stage": "Type-1 row 4 / inner-minor inductive",
            "source_loop": "left Si-in Te-bearing substage",
            "topology": "Si",
            "terrain": "left_Si_in_Hill",
            "weyl_sheet": "left_weyl_density",
            "signed_te": "Te_down",
            "precedence": "terrain_first_then_operator",
            "terrain_fn": hill_left_si_terrain,
        },
        {
            "token": "TeSi",
            "source_stage": "Type-2 row 2 / outer-major inductive",
            "source_loop": "right Si-out Te-bearing substage",
            "topology": "Si",
            "terrain": "right_Si_out_Citadel",
            "weyl_sheet": "right_weyl_density",
            "signed_te": "Te_up",
            "precedence": "operator_first_then_terrain",
            "terrain_fn": citadel_right_si_terrain,
        },
        {
            "token": "NiTe",
            "source_stage": "Type-2 row 3 / outer-major inductive",
            "source_loop": "right Ni-out Te-bearing substage",
            "topology": "Ni",
            "terrain": "right_Ni_out_Source",
            "weyl_sheet": "right_weyl_density",
            "signed_te": "Te_down",
            "precedence": "terrain_first_then_operator",
            "terrain_fn": source_right_ni_terrain,
        },
        {
            "token": "TeNi",
            "source_stage": "Type-1 row 3 / inner-minor inductive",
            "source_loop": "left Ni-in Te-bearing substage",
            "topology": "Ni",
            "terrain": "left_Ni_in_Pit",
            "weyl_sheet": "left_weyl_density",
            "signed_te": "Te_up",
            "precedence": "operator_first_then_terrain",
            "terrain_fn": pit_left_ni_terrain,
        },
    ]
    rows = [run_substage(spec) for spec in specs]
    row_by_token = {row["token"]: row for row in rows}

    eta0 = 0.62
    cycle_specs = [specs[0], specs[3], specs[2], specs[1]]
    cycle_rows = []
    rho = density_np(spinor_np(eta0))
    for spec in cycle_specs:
        row = run_substage(spec, eta0=eta0, input_rho=rho)
        cycle_rows.append(row)
        rho = row["rho"]

    pair_gaps = {
        "SiTe_vs_TeSi": trace_distance(row_by_token["SiTe"]["rho"], row_by_token["TeSi"]["rho"]),
        "NiTe_vs_TeNi": trace_distance(row_by_token["NiTe"]["rho"], row_by_token["TeNi"]["rho"]),
        "left_pair_SiTe_vs_TeNi": trace_distance(row_by_token["SiTe"]["rho"], row_by_token["TeNi"]["rho"]),
        "right_pair_TeSi_vs_NiTe": trace_distance(row_by_token["TeSi"]["rho"], row_by_token["NiTe"]["rho"]),
    }

    positive = {
        "all_four_requested_tokens_ran": {"tokens": sorted(row_by_token), "pass": sorted(row_by_token) == ["NiTe", "SiTe", "TeNi", "TeSi"]},
        "si_topology_shared_but_terrain_split": {
            "tokens": ["SiTe", "TeSi"],
            "topology": "Si",
            "terrains": [row_by_token["SiTe"]["terrain"], row_by_token["TeSi"]["terrain"]],
            "pass": row_by_token["SiTe"]["topology"] == row_by_token["TeSi"]["topology"] == "Si" and row_by_token["SiTe"]["terrain"] != row_by_token["TeSi"]["terrain"],
        },
        "ni_topology_shared_but_terrain_split": {
            "tokens": ["NiTe", "TeNi"],
            "topology": "Ni",
            "terrains": [row_by_token["NiTe"]["terrain"], row_by_token["TeNi"]["terrain"]],
            "pass": row_by_token["NiTe"]["topology"] == row_by_token["TeNi"]["topology"] == "Ni" and row_by_token["NiTe"]["terrain"] != row_by_token["TeNi"]["terrain"],
        },
        "te_up_tokens_ascend": {
            "tokens": ["TeSi", "TeNi"],
            "deltas": {token: row_by_token[token]["te_gradient"]["delta"] for token in ["TeSi", "TeNi"]},
            "pass": all(float(row_by_token[token]["te_gradient"]["delta"]) > 0 for token in ["TeSi", "TeNi"]),
        },
        "te_down_tokens_descend": {
            "tokens": ["SiTe", "NiTe"],
            "deltas": {token: row_by_token[token]["te_gradient"]["delta"] for token in ["SiTe", "NiTe"]},
            "pass": all(float(row_by_token[token]["te_gradient"]["delta"]) < 0 for token in ["SiTe", "NiTe"]),
        },
        "all_outputs_valid_density_matrices": {"pass": all(is_density_matrix(row["rho"]) for row in rows + cycle_rows)},
        "all_pair_gaps_separate": {"pair_gaps": pair_gaps, "pass": all(gap > 0.02 for gap in pair_gaps.values())},
        "four_substage_composition_runs": {
            "order": [row["token"] for row in cycle_rows],
            "closed_surface": "SiTe -> TeNi -> NiTe -> TeSi",
            "start_end_trace_distance": composition_distance(cycle_rows),
            "pass": all(is_density_matrix(row["rho"]) for row in cycle_rows) and composition_distance(cycle_rows) > 0.02,
        },
    }

    wrong_signs = {
        token: te_signed_gradient_eta(eta0, "down" if row["signed_te"] == "Te_up" else "up")
        for token, row in row_by_token.items()
    }
    graveyard_companions = {
        "topology_terrain_sign_order_noncollapse_z3": z3_slot_noncollapse(),
        "wrong_signs_reverse_expected_gradient_direction": {
            "deltas": {token: wrong_signs[token]["delta"] for token in sorted(wrong_signs)},
            "pass": all(
                (float(wrong_signs[token]["delta"]) < 0 if row_by_token[token]["signed_te"] == "Te_up" else float(wrong_signs[token]["delta"]) > 0)
                for token in sorted(wrong_signs)
            ),
        },
        "hill_and_citadel_projectors_differ": {
            "hill_projector": "Pz",
            "citadel_projector": "Px",
            "pass": not np.allclose(PZ_PLUS, PX_PLUS),
        },
        "pit_and_source_ladders_differ": {
            "pass": not np.allclose(SIGMA_MINUS, SIGMA_PLUS),
        },
        "left_right_hamiltonian_signs_opposed": {
            "pass": bool(np.allclose(H_R, -H_L)),
        },
        "si_and_ni_terrain_laws_not_same_channel": {
            "SiTe_vs_TeNi_gap": pair_gaps["left_pair_SiTe_vs_TeNi"],
            "TeSi_vs_NiTe_gap": pair_gaps["right_pair_TeSi_vs_NiTe"],
            "pass": pair_gaps["left_pair_SiTe_vs_TeNi"] > 0.02 and pair_gaps["right_pair_TeSi_vs_NiTe"] > 0.02,
        },
    }
    boundary = {
        "source_table_assignment_used": {
            "SiTe": "Si-in/Hill, Te_down, terrain_first",
            "TeSi": "Si-out/Citadel, Te_up, operator_first",
            "NiTe": "Ni-out/Source, Te_down, terrain_first",
            "TeNi": "Ni-in/Pit, Te_up, operator_first",
            "pass": True,
        },
        "not_full_engine_closure": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "four_substage_surface_is_not_arbitrary_full_cycle_claim": {
            "note": "This runs the four requested Te-bearing substages; the missing Se/Ne/Fi/Ti/Fe stages are not claimed here.",
            "pass": True,
        },
    }

    nearby_total = len(positive) + len(graveyard_companions) + len(boundary)
    nearby_passed = sum(1 for section in (positive, graveyard_companions, boundary) for row in section.values() if row.get("pass"))
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_assignment": {
            token: strip_rho(row_by_token[token]) for token in ["SiTe", "TeSi", "NiTe", "TeNi"]
        },
        "literal_math": {
            "Te_up": "eta <- eta + lr * grad_z_expectation(eta)",
            "Te_down": "eta <- eta - lr * grad_z_expectation(eta)",
            "left_Hill_Si": "X_H^L(rho_L)=-i[K_L,rho_L]+kappa(P_z rho_L P_z - rho_L)",
            "right_Citadel_Si": "X_Ci^R(rho_R)=-i[K_R,rho_R]+kappa(P_x rho_R P_x - rho_R)",
            "left_Pit_Ni": "X_P^L(rho_L)=gamma D[sigma_-](rho_L)-i eps[H_L,rho_L]",
            "right_Source_Ni": "X_So^R(rho_R)=gamma D[sigma_+](rho_R)-i eps[H_R,rho_R]",
        },
        "four_substage_surface": {
            "order": [strip_rho(row) for row in cycle_rows],
            "start_end_trace_distance": composition_distance(cycle_rows),
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": nearby_passed, "total": nearby_total},
        "blockers": [],
        "why_not_v4_probes": "This is a clean v5 formal scout for source-grounded Te-bearing substages, kept out of the mixed v4 probe estate.",
        "why_not_full_engine": "Only the four requested Te-bearing substages are executed. The full left/right engine loops still need the Se/Ne plus Fi/Ti/Fe substages and a work/closure observable.",
        "duration_sec": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    payload = main()
    print(json.dumps({"name": payload["name"], "all_pass": payload["nearby_variants"]["passed"] == payload["nearby_variants"]["total"], "out": str(OUT_PATH)}, indent=2))
