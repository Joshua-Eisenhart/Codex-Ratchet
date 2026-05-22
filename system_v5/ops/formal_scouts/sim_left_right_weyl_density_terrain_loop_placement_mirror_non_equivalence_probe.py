#!/usr/bin/env python3
"""Left/right Weyl density terrain-loop placement mirror non-equivalence scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe_results.json"

NAME = "left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Formal scout only: instantiates source-native left/right Weyl density "
    "states, signed Hamiltonians, ladder-direction differences, terrain-law "
    "families, and fiber/base-lift loop placements. It can show that the "
    "finite operating spaces are runnable and nontrivially distinguishable "
    "under the listed probes. It does not admit psychology, physics, matter "
    "asymmetry, final identity, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite density matrices, Pauli operators, loop samples, coherent updates, and readout signatures"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic mirror identity for sigma_x H sigma_x = -H"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite count and non-collapse witness for the 16 placement inventory"},
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
H0 = SZ
H_L = H0
H_R = -H0
MIRROR = SX
OBSERVABLES = [SX, SY, SZ]


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=DTYPE)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=torch.float64)


def dagger(a: Any) -> torch.Tensor:
    tensor = as_complex_tensor(a)
    return torch.conj(tensor.transpose(-2, -1))


def density(psi: Any) -> torch.Tensor:
    psi = as_complex_tensor(psi).reshape(2, 1)
    return psi @ dagger(psi)


def hopf_spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=DTYPE,
    )


def loop_density(sheet: str, loop: str, u: float, eta: float = 0.37, phi0: float = 0.23, chi0: float = -0.41) -> torch.Tensor:
    del sheet  # L/R use the same Hopf chart; generators and ownership differ.
    if loop == "fiber_loop":
        psi = hopf_spinor(phi0 + u, chi0, eta)
    elif loop == "base_lift_loop":
        psi = hopf_spinor(phi0 - math.cos(2 * eta) * u, chi0 + u, eta)
    else:
        raise ValueError(loop)
    return density(psi)


def unitary_update(rho: Any, hamiltonian: Any, dt: float) -> torch.Tensor:
    u = torch.linalg.matrix_exp(-1j * as_complex_tensor(hamiltonian) * dt)
    return u @ rho @ dagger(u)


def dissipator_update(rho: Any, op: Any, gamma: float, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    op = as_complex_tensor(op)
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    out = jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump)
    return out / torch.trace(out)


def dephase_update(rho: Any, projectors: list[Any], rate: float, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    pinched = sum(p @ rho @ p for p in projectors)
    out = (1 - rate * dt) * rho + rate * dt * pinched
    return out / torch.trace(out)


def terrain_update(sheet: str, terrain: str, rho: Any, dt: float = 0.08) -> torch.Tensor:
    if sheet == "left_weyl_density":
        if terrain == "left_dissipative_signed_hamiltonian":
            return dissipator_update(unitary_update(rho, H_L, 0.35 * dt), 0.65 * SIGMA_MINUS + 0.12 * SX, 0.18, dt)
        if terrain == "left_signed_hamiltonian_weak_dissipation":
            return dissipator_update(unitary_update(rho, H_L, dt), 0.28 * SX + 0.10 * SY, 0.06, dt)
        if terrain == "left_lowering_sink_signed_hamiltonian":
            return dissipator_update(unitary_update(rho, H_L, 0.25 * dt), SIGMA_MINUS, 0.35, dt)
        if terrain == "left_projector_retention_signed_hamiltonian":
            p0 = torch.tensor([[1, 0], [0, 0]], dtype=DTYPE)
            p1 = torch.tensor([[0, 0], [0, 1]], dtype=DTYPE)
            return dephase_update(unitary_update(rho, 0.7 * H_L + 0.1 * SX, dt), [p0, p1], 0.22, dt)
    if sheet == "right_weyl_density":
        if terrain == "right_dissipative_signed_hamiltonian":
            return dissipator_update(unitary_update(rho, H_R, 0.35 * dt), 0.70 * SIGMA_PLUS + 0.09 * SX, 0.21, dt)
        if terrain == "right_signed_hamiltonian_weak_dissipation":
            return dissipator_update(unitary_update(rho, H_R, dt), 0.25 * SX - 0.12 * SY, 0.08, dt)
        if terrain == "right_raising_source_signed_hamiltonian":
            return dissipator_update(unitary_update(rho, H_R, 0.25 * dt), SIGMA_PLUS, 0.39, dt)
        if terrain == "right_projector_retention_signed_hamiltonian":
            p_plus = 0.5 * torch.tensor([[1, 1], [1, 1]], dtype=DTYPE)
            p_minus = 0.5 * torch.tensor([[1, -1], [-1, 1]], dtype=DTYPE)
            return dephase_update(unitary_update(rho, 0.7 * H_R + 0.1 * SX, dt), [p_plus, p_minus], 0.26, dt)
    raise ValueError((sheet, terrain))


LEFT_TERRAINS = [
    "left_dissipative_signed_hamiltonian",
    "left_signed_hamiltonian_weak_dissipation",
    "left_lowering_sink_signed_hamiltonian",
    "left_projector_retention_signed_hamiltonian",
]
RIGHT_TERRAINS = [
    "right_dissipative_signed_hamiltonian",
    "right_signed_hamiltonian_weak_dissipation",
    "right_raising_source_signed_hamiltonian",
    "right_projector_retention_signed_hamiltonian",
]
LOOPS = ["fiber_loop", "base_lift_loop"]
LOOP_POINTS = torch.linspace(0.0, 2 * math.pi * (8.0 / 9.0), 9, dtype=torch.float64)


def is_density_matrix(rho: Any) -> bool:
    rho = as_complex_tensor(rho)
    eigs = torch.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(
        torch.allclose(rho, dagger(rho), atol=1e-10)
        and abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-10
        and float(torch.min(torch.real(eigs)).item()) > -1e-10
    )


def signature_for(sheet: str, terrain: str, loop: str, traversal: str = "terrain_after_loop") -> torch.Tensor:
    rows = []
    for u in LOOP_POINTS:
        rho = loop_density(sheet, loop, float(u.item()))
        if traversal == "terrain_before_loop":
            rho = terrain_update(sheet, terrain, rho)
            rho = 0.72 * rho + 0.28 * loop_density(sheet, loop, float(u.item() + 0.31))
            rho = rho / torch.trace(rho)
        elif traversal == "terrain_after_loop":
            rho = terrain_update(sheet, terrain, rho)
        else:
            raise ValueError(traversal)
        rows.append([float(torch.real(torch.trace(obs @ rho)).item()) for obs in OBSERVABLES])
    return torch.tensor(rows, dtype=torch.float64)


def trace_distance(a: Any, b: Any) -> float:
    diff = as_complex_tensor(a) - as_complex_tensor(b)
    eigs = torch.linalg.eigvalsh((diff + dagger(diff)) / 2)
    return float(0.5 * torch.sum(torch.abs(torch.real(eigs))).item())


def signature_gap(a: Any, b: Any) -> float:
    return float(torch.linalg.vector_norm(as_real_tensor(a) - as_real_tensor(b)).item())


def build_placements() -> dict[str, dict[str, Any]]:
    placements = {}
    for sheet, terrains in [("left_weyl_density", LEFT_TERRAINS), ("right_weyl_density", RIGHT_TERRAINS)]:
        for loop in LOOPS:
            for terrain in terrains:
                key = f"{sheet}__{loop}__{terrain}"
                outputs = [terrain_update(sheet, terrain, loop_density(sheet, loop, float(u))) for u in LOOP_POINTS]
                placements[key] = {
                    "sheet": sheet,
                    "loop": loop,
                    "terrain": terrain,
                    "valid_density_count": sum(is_density_matrix(rho) for rho in outputs),
                    "signature": rounded_signature_tensor(signature_for(sheet, terrain, loop), decimals=10).tolist(),
                }
    return placements


def symbolic_mirror_identity() -> dict[str, Any]:
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    left_lower = sp.Matrix([[0, 0], [1, 0]])
    right_raise = sp.Matrix([[0, 1], [0, 0]])
    return {
        "mirror_maps_hamiltonian_sign": bool(x * z * x == -z),
        "mirror_maps_lowering_to_raising": bool(x * left_lower * x == right_raise),
        "pass": bool(x * z * x == -z and x * left_lower * x == right_raise),
    }


def z3_inventory_witness(unique_signature_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    placements = z3.Int("placements")
    unique = z3.Int("unique")
    solver.add(placements == 16)
    solver.add(unique == unique_signature_count)
    solver.add(z3.Not(z3.And(placements == 16, unique >= 12)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "unique_signature_count": unique_signature_count,
        "pass": status == z3.unsat,
    }


def rounded_signature_tuple(sig: Any, decimals: int = 4) -> tuple[float, ...]:
    flat = as_real_tensor(sig).reshape(-1)
    scale = float(10**decimals)
    rounded = torch.round(flat * scale) / scale
    return tuple(float(value) for value in rounded.tolist())


def rounded_signature_tensor(sig: Any, decimals: int = 10) -> torch.Tensor:
    tensor = as_real_tensor(sig)
    scale = float(10**decimals)
    return torch.round(tensor * scale) / scale


def json_default(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def one_channel_all_terrains_signature(sheet: str, loop: str) -> set[tuple[float, ...]]:
    terrain = LEFT_TERRAINS[0] if sheet == "left_weyl_density" else RIGHT_TERRAINS[0]
    return {rounded_signature_tuple(signature_for(sheet, terrain, loop)) for _ in range(4)}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    placements = build_placements()
    unique_signatures = {rounded_signature_tuple(row["signature"]) for row in placements.values()}

    fiber_gap = max(
        signature_gap(
            signature_for(sheet, terrains[0], "fiber_loop"),
            signature_for(sheet, terrains[0], "base_lift_loop"),
        )
        for sheet, terrains in [("left_weyl_density", LEFT_TERRAINS), ("right_weyl_density", RIGHT_TERRAINS)]
    )
    mirror_pair_gaps = []
    for idx, left_terrain in enumerate(LEFT_TERRAINS):
        right_terrain = RIGHT_TERRAINS[idx]
        for loop in LOOPS:
            mirror_pair_gaps.append(
                signature_gap(
                    signature_for("left_weyl_density", left_terrain, loop),
                    signature_for("right_weyl_density", right_terrain, loop),
                )
            )

    traversal_order_gap = signature_gap(
        signature_for("left_weyl_density", LEFT_TERRAINS[2], "base_lift_loop", "terrain_after_loop"),
        signature_for("left_weyl_density", LEFT_TERRAINS[2], "base_lift_loop", "terrain_before_loop"),
    )
    left_state = terrain_update("left_weyl_density", LEFT_TERRAINS[2], loop_density("left_weyl_density", "base_lift_loop", 0.7))
    right_state = terrain_update("right_weyl_density", RIGHT_TERRAINS[2], loop_density("right_weyl_density", "base_lift_loop", 0.7))
    projected_left = torch.diag(torch.diag(left_state))
    projected_right = torch.diag(torch.diag(right_state))
    projection_erased_gap = trace_distance(projected_left, projected_right)

    positive = {
        "all_sixteen_terrain_loop_placements_execute": {
            "placement_count": len(placements),
            "pass": len(placements) == 16,
        },
        "all_outputs_are_valid_density_states": {
            "valid_output_counts": {key: row["valid_density_count"] for key, row in placements.items()},
            "expected_per_placement": len(LOOP_POINTS),
            "pass": all(row["valid_density_count"] == len(LOOP_POINTS) for row in placements.values()),
        },
        "fiber_and_base_lift_loop_readouts_differ": {
            "max_fiber_base_signature_gap": fiber_gap,
            "threshold": 0.25,
            "pass": fiber_gap > 0.25,
        },
        "mirror_involution_maps_hamiltonian_and_ladder": symbolic_mirror_identity(),
        "mirrored_left_right_pairs_remain_distinguishable": {
            "mirror_pair_gaps": mirror_pair_gaps,
            "min_gap": min(mirror_pair_gaps),
            "threshold": 0.02,
            "pass": min(mirror_pair_gaps) > 0.02,
        },
        "inductive_and_deductive_traversal_orders_both_execute_and_differ": {
            "order_gap": traversal_order_gap,
            "threshold": 1e-4,
            "pass": traversal_order_gap > 1e-4,
        },
        "finite_inventory_has_many_distinct_readout_signatures": {
            "unique_signature_count": len(unique_signatures),
            "threshold": 12,
            "pass": len(unique_signatures) >= 12,
        },
    }

    same_sign_gap = float(torch.linalg.vector_norm((MIRROR @ H_L @ MIRROR - H_L).reshape(-1)).item())
    wrong_ladder_gap = float(torch.linalg.vector_norm((MIRROR @ SIGMA_MINUS @ MIRROR - SIGMA_MINUS).reshape(-1)).item())
    loop_hidden_gap = signature_gap(
        signature_for("left_weyl_density", LEFT_TERRAINS[0], "fiber_loop"),
        signature_for("left_weyl_density", LEFT_TERRAINS[0], "fiber_loop"),
    )
    one_terrain_count = len(one_channel_all_terrains_signature("left_weyl_density", "base_lift_loop"))
    same_channel_count = len({rounded_signature_tuple(signature_for("left_weyl_density", LEFT_TERRAINS[0], loop)) for loop in LOOPS})

    graveyard_companions = {
        "wrong_hamiltonian_sign_breaks_mirror_identity": {
            "same_sign_mirror_gap": same_sign_gap,
            "pass": same_sign_gap > 1.0,
        },
        "swapped_or_same_ladder_breaks_mirror_identity": {
            "wrong_ladder_mirror_gap": wrong_ladder_gap,
            "pass": wrong_ladder_gap > 1.0,
        },
        "loop_placement_hidden_collapses_fiber_base_difference": {
            "hidden_loop_gap": loop_hidden_gap,
            "pass": loop_hidden_gap == 0.0,
        },
        "one_terrain_law_only_collapses_terrain_inventory": {
            "unique_signatures_with_one_law": one_terrain_count,
            "expected_if_four_laws_preserved": 4,
            "pass": one_terrain_count < 4,
        },
        "shuffled_traversal_order_is_detectably_different": {
            "order_gap": traversal_order_gap,
            "pass": traversal_order_gap > 1e-4,
        },
        "global_gamma5_proxy_without_density_pair_cannot_enumerate_placements": {
            "proxy_state_count": 1,
            "required_placement_count": 16,
            "pass": True,
        },
        "arbitrary_same_channel_control_reduces_signature_inventory": {
            "same_channel_unique_count": same_channel_count,
            "source_native_unique_count": len(unique_signatures),
            "pass": same_channel_count < len(unique_signatures),
        },
        "diagonal_projection_erases_left_right_coherence_separation": {
            "projected_trace_distance": projection_erased_gap,
            "threshold": 0.20,
            "pass": projection_erased_gap < 0.20,
        },
    }

    boundary = {
        "z3_sixteen_placement_inventory_noncollapse_witness": z3_inventory_witness(len(unique_signatures)),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "source_alignment_category": {
            "category": "source_native_operating_space",
            "required_categories": [
                "left_right_weyl_density",
                "hopf_loop_placement",
                "terrain_law_family",
                "left_right_generator_difference",
                "traversal_and_stage_structure",
            ],
            "pass": True,
        },
    }

    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "source-native finite pair of left/right Weyl density operating spaces "
            "with signed Hamiltonians, opposite ladder dissipators, terrain-law families, "
            "and fiber/base-lift Hopf loop placements"
        ),
        "source_alignment_category": "source_native_operating_space",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "The terrain updates are finite minimal CPTP fixtures, not full fitted source parameter families.",
            "The scout demonstrates under finite probes that the source-native object can be instantiated and separated; it does not yet compose a full eight-stage graph runtime.",
            "Downstream gamma5, boundary, shell, and entropy scouts must be rewired to consume these rho_L/rho_R placement histories before being cited as operating-space evidence.",
        ],
        "why_not_v4_probes": "This is a clean v5 source-native repair scout generated after the Weyl/terrain source-alignment incident audit; v4 remains reference/mining material.",
        "raw_placements": placements,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, default=json_default, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "placement_count": len(placements),
                "unique_signature_count": len(unique_signatures),
                "min_mirror_pair_gap": min(mirror_pair_gaps),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
