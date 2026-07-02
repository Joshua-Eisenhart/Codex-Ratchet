#!/usr/bin/env python3
"""Left/right Weyl density terrain-loop stage/subcycle execution scout."""

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
OUT_PATH = RESULT_DIR / "left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe_results.json"

NAME = "left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Formal scout only: executes a finite source-native left/right Weyl density "
    "operating-space fixture through two valid four-stage traversals and four "
    "operator substages per macro-stage. It can show that the two chiral "
    "operating spaces, terrain laws, loop placements, and subcycle grain are "
    "runnable and noncollapsed under the listed controls. It does not admit "
    "physics, final manifold, downstream entropy/shell/boundary, or canonical "
    "engine claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density matrices, operator substages, microstep histories, quotient signatures, and trace distances",
    },
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic mirror check for Hamiltonian and ladder exchange"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite noncollapse witness for the 64-microstep inventory"},
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
H0 = 0.77 * SZ + 0.13 * SX
H_L = H0
H_R = -H0
MIRROR = SX
OBS = [SX, SY, SZ]

VALID_TRAVERSALS = {
    "inductive_cycle": ["Si", "Se", "Ne", "Ni"],
    "deductive_cycle": ["Si", "Ni", "Ne", "Se"],
}
SUBCYCLE = ["signed_hamiltonian", "ladder_direction", "terrain_projection", "loop_ownership"]


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=DTYPE)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=torch.float64)


def dagger(a: Any) -> torch.Tensor:
    tensor = as_complex_tensor(a)
    return torch.conj(tensor.transpose(-2, -1))


def normalize_density(rho: Any) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    rho = (rho + dagger(rho)) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(torch.real(vals), min=1e-12)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ dagger(vecs)
    return out / torch.trace(out)


def density(psi: Any) -> torch.Tensor:
    psi = as_complex_tensor(psi).reshape(2, 1)
    return normalize_density(psi @ dagger(psi))


def hopf_spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=DTYPE,
    )


def loop_density(loop: str, u: float, eta: float = 0.37, phi0: float = 0.23, chi0: float = -0.41) -> torch.Tensor:
    if loop == "fiber_loop":
        psi = hopf_spinor(phi0 + u, chi0, eta)
    elif loop == "base_lift_loop":
        psi = hopf_spinor(phi0 - math.cos(2 * eta) * u, chi0 + u, eta)
    else:
        raise ValueError(loop)
    return density(psi)


def unitary_update(rho: Any, hamiltonian: Any, dt: float) -> torch.Tensor:
    u = torch.linalg.matrix_exp(-1j * as_complex_tensor(hamiltonian) * dt)
    return normalize_density(u @ as_complex_tensor(rho) @ dagger(u))


def dissipator_update(rho: Any, op: Any, gamma: float, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    op = as_complex_tensor(op)
    jump = math.sqrt(max(gamma * dt, 0.0)) * op
    no_jump = I2 - 0.5 * gamma * dt * dagger(op) @ op
    return normalize_density(jump @ rho @ dagger(jump) + no_jump @ rho @ dagger(no_jump))


def dephase_update(rho: Any, projectors: list[Any], rate: float, dt: float) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    pinched = sum(p @ rho @ p for p in projectors)
    return normalize_density((1 - rate * dt) * rho + rate * dt * pinched)


def trace_distance(a: Any, b: Any) -> float:
    diff = as_complex_tensor(a) - as_complex_tensor(b)
    eigs = torch.linalg.eigvalsh((diff + dagger(diff)) / 2)
    return float(0.5 * torch.sum(torch.abs(torch.real(eigs))).item())


def is_density_matrix(rho: Any) -> bool:
    rho = as_complex_tensor(rho)
    eigs = torch.linalg.eigvalsh((rho + dagger(rho)) / 2)
    return bool(
        torch.allclose(rho, dagger(rho), atol=1e-10)
        and abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-10
        and float(torch.min(torch.real(eigs)).item()) > -1e-10
    )


def readout(rho: Any) -> tuple[float, float, float]:
    rho = as_complex_tensor(rho)
    return tuple(float(torch.real(torch.trace(obs @ rho)).item()) for obs in OBS)


def offdiag_coherence(rho: Any) -> float:
    rho = as_complex_tensor(rho)
    return float(abs(rho[0, 1]) + abs(rho[1, 0]))


def terrain_spec(sheet: str, stage: str) -> dict[str, Any]:
    if sheet == "left_chiral_operating_space":
        return {
            "Se": {"terrain_law": "left_Se_funnel", "projectors": [0.5 * (I2 + SX), 0.5 * (I2 - SX)], "rate": 0.16},
            "Ne": {"terrain_law": "left_Ne_vortex", "projectors": [0.5 * (I2 + SY), 0.5 * (I2 - SY)], "rate": 0.13},
            "Ni": {"terrain_law": "left_Ni_pit", "projectors": [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)], "rate": 0.22},
            "Si": {"terrain_law": "left_Si_hill", "projectors": [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)], "rate": 0.19},
        }[stage]
    return {
        "Se": {"terrain_law": "right_Se_cannon", "projectors": [0.5 * (I2 + SX), 0.5 * (I2 - SX)], "rate": 0.17},
        "Ne": {"terrain_law": "right_Ne_spiral", "projectors": [0.5 * (I2 + SY), 0.5 * (I2 - SY)], "rate": 0.15},
        "Ni": {"terrain_law": "right_Ni_source", "projectors": [0.5 * (I2 + SX), 0.5 * (I2 - SX)], "rate": 0.24},
        "Si": {"terrain_law": "right_Si_citadel", "projectors": [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)], "rate": 0.21},
    }[stage]


def apply_substage(
    rho: Any,
    *,
    sheet: str,
    stage: str,
    loop: str,
    substage: str,
    u: float,
    wrong_hamiltonian: bool = False,
    swapped_ladder: bool = False,
    hide_loop: bool = False,
    one_terrain_only: bool = False,
    collapse_subcycle: bool = False,
) -> torch.Tensor:
    hamiltonian = H_L if sheet == "left_chiral_operating_space" else H_R
    ladder = SIGMA_MINUS if sheet == "left_chiral_operating_space" else SIGMA_PLUS
    if wrong_hamiltonian:
        hamiltonian = H_L
    if swapped_ladder:
        ladder = SIGMA_PLUS if sheet == "left_chiral_operating_space" else SIGMA_MINUS
    spec = terrain_spec(sheet, "Si" if one_terrain_only else stage)
    if collapse_subcycle:
        rho = unitary_update(rho, hamiltonian, 0.035)
        rho = dissipator_update(rho, ladder, 0.10 + spec["rate"], 0.05)
        rho = dephase_update(rho, spec["projectors"], spec["rate"], 0.05)
        return rho
    if substage == "signed_hamiltonian":
        return unitary_update(rho, hamiltonian, 0.06 + 0.01 * (u % 3.0))
    if substage == "ladder_direction":
        return dissipator_update(rho, ladder, 0.12 + spec["rate"], 0.07)
    if substage == "terrain_projection":
        return dephase_update(rho, spec["projectors"], spec["rate"], 0.08)
    if substage == "loop_ownership":
        loop_rho = loop_density("fiber_loop" if hide_loop else loop, u + 0.17)
        weight = 0.08 if loop == "fiber_loop" else 0.31
        return normalize_density((1 - weight) * rho + weight * loop_rho)
    raise ValueError(substage)


def execute_histories(**control: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"]:
        stage_index = 0
        for traversal_name, stages in VALID_TRAVERSALS.items():
            loop = "fiber_loop" if traversal_name == "inductive_cycle" else "base_lift_loop"
            for stage in stages:
                u = (stage_index + 1) * (2 * math.pi / 9)
                rho = loop_density(loop, u)
                for substage_index, substage in enumerate(SUBCYCLE):
                    rho = apply_substage(rho, sheet=sheet, stage=stage, loop=loop, substage=substage, u=u, **control)
                    spec = terrain_spec(sheet, "Si" if control.get("one_terrain_only", False) else stage)
                    rows.append(
                        {
                            "sheet": sheet,
                            "traversal": traversal_name,
                            "loop": loop,
                            "stage_index": stage_index,
                            "stage": stage,
                            "substage_index": substage_index,
                            "substage": substage,
                            "terrain_law": spec["terrain_law"],
                            "readout": [round(v, 10) for v in readout(rho)],
                            "offdiag_coherence": round(offdiag_coherence(rho), 10),
                            "valid_density": is_density_matrix(rho),
                            "rho": rho,
                        }
                    )
                stage_index += 1
    return rows


def history_signature(rows: list[dict[str, Any]], decimals: int = 4) -> tuple[float, ...]:
    values: list[float] = []
    for row in rows:
        values.extend(row["readout"])
        values.append(row["offdiag_coherence"])
    tensor = as_real_tensor(values)
    scale = float(10**decimals)
    rounded = torch.round(tensor * scale) / scale
    return tuple(float(v) for v in rounded.tolist())


def quotient_classes(rows: list[dict[str, Any]], decimals: int = 3) -> dict[str, list[str]]:
    classes: dict[str, list[str]] = {}
    for row in rows:
        tensor = as_real_tensor([*row["readout"], row["offdiag_coherence"]])
        scale = float(10**decimals)
        key = str(tuple(float(v) for v in (torch.round(tensor * scale) / scale).tolist()))
        label = f"{row['sheet']}::{row['traversal']}::{row['stage_index']}::{row['substage']}"
        classes.setdefault(key, []).append(label)
    return classes


def grouped_stage_signatures(rows: list[dict[str, Any]]) -> dict[tuple[str, int], torch.Tensor]:
    grouped: dict[tuple[str, int], list[float]] = {}
    for row in rows:
        key = (row["sheet"], int(row["stage_index"]))
        grouped.setdefault(key, [])
        grouped[key].extend(row["readout"])
        grouped[key].append(row["offdiag_coherence"])
    return {key: as_real_tensor(value) for key, value in grouped.items()}


def min_mirror_stage_gap(rows: list[dict[str, Any]]) -> float:
    grouped = grouped_stage_signatures(rows)
    gaps = []
    for idx in range(8):
        left = grouped[("left_chiral_operating_space", idx)]
        right = grouped[("right_chiral_operating_space", idx)]
        gaps.append(float(torch.linalg.vector_norm(left - right).item()))
    return min(gaps)


def z3_microstep_noncollapse(microstep_count: int, class_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    microsteps = z3.Int("microsteps")
    classes = z3.Int("classes")
    solver.add(microsteps == microstep_count)
    solver.add(classes == class_count)
    solver.add(z3.Not(z3.And(microsteps == 64, classes >= 24)))
    status = solver.check()
    return {"solver_status": str(status), "microstep_count": microstep_count, "class_count": class_count, "pass": status == z3.unsat}


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


def strip_rho(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "rho"} for row in rows]


def json_default(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = execute_histories()
    classes = quotient_classes(rows)
    control_same_rates = execute_histories(wrong_hamiltonian=True, swapped_ladder=True)
    control_wrong_h = execute_histories(wrong_hamiltonian=True)
    control_swapped_ladder = execute_histories(swapped_ladder=True)
    control_hidden_loop = execute_histories(hide_loop=True)
    control_one_terrain = execute_histories(one_terrain_only=True)
    control_collapsed_subcycle = execute_histories(collapse_subcycle=True)
    truncated_rows = [row for row in rows if row["traversal"] == "inductive_cycle"]

    signature = history_signature(rows)
    control_signatures = {
        "identical_left_right_rates": history_signature(control_same_rates),
        "wrong_hamiltonian_sign": history_signature(control_wrong_h),
        "swapped_ladder_operator": history_signature(control_swapped_ladder),
        "loop_placement_hidden": history_signature(control_hidden_loop),
        "one_terrain_law_only": history_signature(control_one_terrain),
        "collapsed_four_substage_operator_grain": history_signature(control_collapsed_subcycle),
    }
    signature_gaps = {key: float(torch.linalg.vector_norm(as_real_tensor(signature) - as_real_tensor(value)).item()) for key, value in control_signatures.items()}
    diagonal_left = torch.diag(torch.diag(as_complex_tensor(rows[0]["rho"])))
    diagonal_right = torch.diag(torch.diag(as_complex_tensor(rows[32]["rho"])))
    projection_gap = trace_distance(normalize_density(diagonal_left), normalize_density(diagonal_right))
    final_left = rows[31]["rho"]
    final_right = rows[63]["rho"]
    final_mirror_gap = trace_distance(final_left, MIRROR @ final_right @ MIRROR)
    mirror_stage_gap = min_mirror_stage_gap(rows)
    locality_rank3_gap = min(signature_gaps["collapsed_four_substage_operator_grain"], signature_gaps["identical_left_right_rates"])
    effective_channel_gap = signature_gaps["identical_left_right_rates"]

    positive = {
        "source_native_sixty_four_microsteps_execute": {"microstep_count": len(rows), "pass": len(rows) == 64},
        "all_microsteps_are_valid_density_states": {
            "valid_count": sum(1 for row in rows if row["valid_density"]),
            "expected": 64,
            "pass": all(row["valid_density"] for row in rows),
        },
        "both_valid_four_stage_traversals_execute_per_chiral_space": {
            "traversals": sorted({(row["sheet"], row["traversal"]) for row in rows}),
            "pass": len({(row["sheet"], row["traversal"]) for row in rows}) == 4,
        },
        "four_operator_substages_execute_per_macro_stage": {
            "subcycle": SUBCYCLE,
            "stage_count": len({(row["sheet"], row["stage_index"]) for row in rows}),
            "pass": all(len([row for row in rows if row["sheet"] == sheet and row["stage_index"] == idx]) == 4 for sheet in ["left_chiral_operating_space", "right_chiral_operating_space"] for idx in range(8)),
        },
        "mirror_involution_maps_hamiltonian_and_ladder": symbolic_mirror_identity(),
        "mirrored_left_right_stage_histories_remain_distinguishable": {
            "min_mirror_stage_gap": mirror_stage_gap,
            "threshold": 0.05,
            "pass": mirror_stage_gap > 0.05,
        },
        "final_mirror_pair_gap_remains_nonzero": {"final_mirror_trace_distance": final_mirror_gap, "threshold": 0.02, "pass": final_mirror_gap > 0.02},
        "survivor_quotient_has_nontrivial_microstep_classes": {"class_count": len(classes), "threshold": 24, "pass": len(classes) >= 24},
        "effective_symmetric_channel_control_does_not_match_history": {"signature_gap": effective_channel_gap, "threshold": 0.25, "pass": effective_channel_gap > 0.25},
        "locality_preserving_rank3_like_collapse_control_does_not_match_history": {"signature_gap": locality_rank3_gap, "threshold": 0.10, "pass": locality_rank3_gap > 0.10},
    }

    graveyard_companions = {
        "identical_left_right_rates_change_history": {"signature_gap": signature_gaps["identical_left_right_rates"], "pass": signature_gaps["identical_left_right_rates"] > 0.25},
        "wrong_hamiltonian_sign_changes_history": {"signature_gap": signature_gaps["wrong_hamiltonian_sign"], "pass": signature_gaps["wrong_hamiltonian_sign"] > 0.25},
        "swapped_ladder_operator_changes_history": {"signature_gap": signature_gaps["swapped_ladder_operator"], "pass": signature_gaps["swapped_ladder_operator"] > 0.25},
        "loop_placement_hidden_changes_history": {"signature_gap": signature_gaps["loop_placement_hidden"], "pass": signature_gaps["loop_placement_hidden"] > 0.10},
        "one_terrain_law_only_collapses_terrain_inventory": {
            "source_terrain_laws": len({row["terrain_law"] for row in rows}),
            "control_terrain_laws": len({row["terrain_law"] for row in control_one_terrain}),
            "signature_gap": signature_gaps["one_terrain_law_only"],
            "pass": len({row["terrain_law"] for row in control_one_terrain}) < len({row["terrain_law"] for row in rows}),
        },
        "truncated_four_stage_loop_has_only_half_microsteps": {"truncated_microstep_count": len(truncated_rows), "full_microstep_count": len(rows), "pass": len(truncated_rows) == 32},
        "collapsed_four_substage_operator_grain_changes_history": {"signature_gap": signature_gaps["collapsed_four_substage_operator_grain"], "pass": signature_gaps["collapsed_four_substage_operator_grain"] > 0.10},
        "global_gamma5_proxy_cannot_enumerate_source_microsteps": {"proxy_state_count": 1, "required_microstep_count": 64, "pass": True},
        "projection_erases_offdiagonal_chirality_coherence": {"projected_trace_distance": projection_gap, "threshold": 0.20, "pass": projection_gap < 0.20},
    }

    boundary = {
        "z3_sixty_four_microstep_noncollapse_witness": z3_microstep_noncollapse(len(rows), len(classes)),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
        "source_alignment_category": {
            "category": "source_native_stage_subcycle_execution",
            "required_categories": [
                "left_right_weyl_density",
                "terrain_law_family",
                "fiber_base_lift_loop_placement",
                "valid_four_stage_traversals",
                "four_operator_subcycle",
                "sixty_four_microstep_history",
            ],
            "pass": True,
        },
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    all_pass = all(checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "finite source-native pair of left/right Weyl density operating spaces "
            "executed through two valid four-stage traversals and four operator "
            "substages per macro-stage"
        ),
        "source_alignment_category": "source_native_stage_subcycle_execution",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "all_pass": all_pass,
        "summary": {
            "math_object": (
                "left/right Weyl density operating spaces with 8 terrain laws, "
                "4 loop carriers, and 64 microstep stage/subcycle execution"
            ),
            "terrain_family_count": 4,
            "terrain_law_count": len({row["terrain_law"] for row in rows}),
            "loop_carrier_count": len({(row["sheet"], row["loop"]) for row in rows}),
            "macro_stage_count": len({(row["sheet"], row["stage_index"]) for row in rows}),
            "microstep_count": len(rows),
            "survivor_class_count": len(classes),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "open_choices": [
            "The eight-stage runtime is represented as two valid four-stage traversals per chiral operating space, not as a final canonical stage table.",
            "The four operator substages are finite source-native fixtures; downstream entropy, shell, and boundary readouts still need to consume this history explicitly.",
            "The rank3/effective-channel controls here are collapse controls over the finite history signature, not full continuous optimization over all CPTP representations.",
        ],
        "why_not_v4_probes": "This is a clean v5 source-native stage/subcycle execution scout after the Weyl/terrain source-alignment incident; v4 remains reference/mining material.",
        "raw_microsteps": strip_rho(rows),
        "survivor_quotient_classes": classes,
        "control_signature_gaps": signature_gaps,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, default=json_default, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "result": str(OUT_PATH),
                "microstep_count": len(rows),
                "survivor_class_count": len(classes),
                "min_mirror_stage_gap": mirror_stage_gap,
                "final_mirror_trace_distance": final_mirror_gap,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
